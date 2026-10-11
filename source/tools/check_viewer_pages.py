#!/usr/bin/env python3
"""Match every translated story line against the pages the dialogue viewer drew.

run_story_viewer.py draws each translated script through the game's field
renderer and captures its pages. This lays each Korean line of that script out
of the product ROM's own glyph bitmaps (record_story_qa.line_mask) and looks for
that exact ink pattern on the script's pages, on the page's three-line baseline
grid. A line found is drawn in full, uncut and at its place; a line not found
is listed for a person to look at, with the page it should be on.

A line can go unfound for reasons that are not defects: text the engine inserts
at run time (names, chip names, numbers) changes the pixels around it, a choice
row is drawn by another routine, and a per-glyph reveal piece is a fragment of
a line. Those are reported, not failed.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from analyze_project import sha
from build_story_batch import PRODUCT
from record_story_qa import BASELINES, LEFT_MARGIN, line_mask
from survey_dialogue_layout import load_table, advances

p = Path(__file__).resolve().parents[1]
BOX_LEFT, BOX_RIGHT = 40, 240


def find(arr: np.ndarray, mask: set[tuple[int, int]], width: int, height: int, xs) -> tuple[int, int] | None:
    ys = np.array([y for _, y in mask]); xm = np.array([x for x, _ in mask])
    fx, fy = min(mask)
    ink = np.zeros((height, width), bool)
    ink[ys, xm] = True
    for oy in BASELINES:
        if oy + height > arr.shape[0]:
            continue
        for ox in xs:
            if ox + width > arr.shape[1]:
                continue
            box = arr[oy:oy + height, ox:ox + width]
            colour = box[fy, fx]
            same = (box == colour).all(axis=2)
            if same[ink].all() and not same[~ink].any():
                return ox, oy
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--key', required=True, choices=['blue_moon', 'red_sun'])
    ap.add_argument('--run', required=True, help='viewer output folder name under analysis/runtime')
    a = ap.parse_args()
    run = p / 'analysis/runtime' / a.run
    result = json.loads((run / 'result.json').read_text(encoding='utf-8'))
    product = p / 'poc/output' / (PRODUCT.format(key=a.key) + '.gba')
    rom = product.read_bytes()
    m = json.loads(product.with_suffix('.json').read_text(encoding='utf-8'))
    if result['rom_sha256'] != sha(rom):
        raise SystemExit('viewer run is of another ROM')
    font_at = m['extension']['layout'][0]['offset']
    width_table = advances(rom, m['extension']['advance_offset'] & 0x1FFFFFF)
    table = load_table()

    lines: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for b in sorted((p / 'translations/story_korean').glob('*.json')):
        for e in json.loads(b.read_text(encoding='utf-8'))['entries']:
            ko = e['ko'] if a.key == 'blue_moon' or 'ko_red_sun' not in e else e['ko_red_sun']
            _, arc, _, script, _, literal = e['id'].split('/')
            for n, line in enumerate(ko.split('\n')):
                if line.strip():
                    lines[f'a{int(arc):03d}_s{int(script):03d}'].append((e['id'], n, line))
    ended = {r['job']: r for r in result['results']}
    matched, unmatched, no_glyph, not_run = 0, [], 0, []
    for job, items in sorted(lines.items()):
        pages = sorted(run.glob(job + '_p*.png'))
        if job not in ended:
            not_run.append(job)
            continue
        arrays = [np.asarray(Image.open(f).convert('RGB')) for f in pages]
        for key_id, n, line in items:
            mask, width, height = line_mask(rom, font_at, line.rstrip(), table, width_table)
            if not mask:
                no_glyph += 1
                continue
            indent = len(line) - len(line.lstrip(' '))
            first = [LEFT_MARGIN + 8 * indent] if indent else [LEFT_MARGIN]
            hit = None
            for i, arr in enumerate(arrays):
                where = find(arr, mask, width, height, first) or find(arr, mask, width, height, range(BOX_LEFT, BOX_RIGHT))
                if where:
                    hit = (i + 1, where)
                    break
            if hit:
                matched += 1
            else:
                unmatched.append({'job': job, 'id': key_id, 'line': n, 'text': line, 'pages': len(pages),
                                  'end': ended[job]['end']})
    report = {'schema': 1, 'key': a.key, 'run': a.run, 'rom_sha256': result['rom_sha256'],
              'lines_matched': matched, 'lines_unmatched': len(unmatched), 'lines_without_glyphs': no_glyph,
              'jobs_not_run': not_run, 'job_endings': {},
              'unmatched': unmatched, 'tool_sha256': sha(Path(__file__).read_bytes())}
    for r in result['results']:
        report['job_endings'][r['end']] = report['job_endings'].get(r['end'], 0) + 1
    (run / 'line_check.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{a.key}: {matched} lines matched pixel-exactly, {len(unmatched)} not found, {no_glyph} without glyphs, "
          f"{len(not_run)} scripts not run; endings {report['job_endings']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
