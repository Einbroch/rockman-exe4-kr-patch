#!/usr/bin/env python3
"""Check menu-option rows against the width the game itself draws at.

A dialogue line has the whole 180px window; a menu option shares its row.
`positionOptionHorizontal` / `positionOptionVertical` carry a `width` the
TextPet plugin describes as "the horizontal distance, in increments of a single
character width, between the right edge of the text area and the left edge of
the menu option", but that character width is not written down anywhere this
project can read, and every whole-pixel value tried against it is contradicted
by some row of the ROM.  So the budget here is not derived from a model of the
renderer at all.

The rule is: a Korean option row may not be wider than the widest Japanese
option row the ROM already draws at the same placement and the same declared
width.  Whatever `width` means, the game demonstrably draws that many pixels
there, so a Korean row that stays inside it asks for no space the Japanese did
not already take.  The dialogue window is a second, independent cap.

This matters because Korean syllables advance 12px against 11px for kana: a
rule of "no wider than the line it replaces" would forbid translating a
two-character option as two syllables, which is most of them.

Row grouping follows the literals: a row ends at the option carrying the line
break, or where a new position command starts the next one.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from analyze_project import PROFILES, sha, scripts, LITERAL
from check_story_translation import measure
from survey_dialogue_layout import ESCAPED_BREAK, ADVANCE_OFFSET, load_table, advances

p = Path(__file__).resolve().parents[1]
BATCH_DIR = p / 'translations/story_korean'
WINDOW_PIXELS = 180

# A command in a TextPet dump is a bare name on its own line; its parameters are
# indented `name = value` lines, which this deliberately does not match.
COMMAND = re.compile(r'(?m)^[\t ]*([A-Za-z][A-Za-z0-9]*)[\t ]*(?:\r?\n|$)')
POSITION = re.compile(r'positionOption(Horizontal|Vertical)\s*\n\s*width = (\d+)')


def rows_of(key: str):
    """Yield (archive, script, placement, [(record id, literal), ...]) per option row."""
    analysis = json.loads((p / f'analysis/{key}_analysis.json').read_text(encoding='utf-8'))
    by_offset = {int(row['offset']): int(row['index']) for row in analysis['archives_detail']}
    for f in sorted((p / f'analysis/{key}_tpl').glob('*.tpl')):
        archive = by_offset[int(f.stem, 16)]
        for number, _language, values, block in scripts(f.read_text(encoding='utf-8')):
            spans = list(LITERAL.finditer(block))
            if len(spans) != len(values):
                raise ValueError(f'literal enumeration drifted in {f.name} script {number}')
            end, positions, row, place = 0, 0, [], None
            for k, m in enumerate(spans):
                gap, end = block[end:m.start()], m.end()
                # `space` sits between `option` and its label; anything else
                # between them means this literal is not that option's label.
                commands = [c for c in COMMAND.findall(gap) if c != 'space']
                if not commands or commands[-1] != 'option':
                    if row:
                        yield archive, number, place, row
                        row = []
                    continue
                seen = POSITION.findall(block[:m.start()])
                if len(seen) != positions:
                    if row:
                        yield archive, number, place, row
                        row = []
                    positions = len(seen)
                place = (seen[-1][0], int(seen[-1][1])) if seen else None
                row.append((f'archive/{archive:03d}/script/{number}/literal/{k}', values[k]))
                if ESCAPED_BREAK in values[k]:
                    yield archive, number, place, row
                    row = []
            if row:
                yield archive, number, place, row


def label(text: str) -> str:
    """The part of an option literal drawn on its row.

    The extraction sheet writes the break as the two characters TextPet uses;
    the Korean batches write a real newline. Both end the row."""
    return text.replace(ESCAPED_BREAK, '\n').split('\n')[0]


def row_pixels(texts, table, width) -> tuple[int, list[str]]:
    total, unencodable = 0, []
    for text in texts:
        pixels, bad = measure(label(text), table, width)
        total += pixels
        unencodable += bad
    return total, unencodable


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', action='append', type=Path,
                    help='one batch file; omit to check every batch in translations/story_korean')
    ap.add_argument('--output', type=Path, default=p / 'analysis/story_option_widths.json')
    a = ap.parse_args()

    table = load_table()
    rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba')
               if sha(f.read_bytes()) == PROFILES['blue_moon']['sha256'])
    width = advances(rom, ADVANCE_OFFSET['blue_moon'])

    korean: dict[str, dict] = {}
    batches = a.batch or (sorted(BATCH_DIR.glob('*.json')) if BATCH_DIR.exists() else [])
    for batch in batches:
        for entry in json.loads(batch.read_text(encoding='utf-8'))['entries']:
            korean[entry['id']] = {'batch': batch.name, 'ko': entry['ko'],
                                   'ko_red_sun': entry.get('ko_red_sun')}

    # First pass: what the Japanese already occupies at each declared width.
    everything = list(rows_of('blue_moon'))
    budget: dict[tuple[str, int], dict] = {}
    for archive, script, place, members in everything:
        if place is None:
            continue
        pixels, _ = row_pixels([text for _id, text in members], table, width)
        best = budget.get(place)
        if best is None or pixels > best['pixels']:
            budget[place] = {'pixels': pixels, 'archive': archive, 'script': script,
                             'literals': [label(t) for _i, t in members]}

    problems, translated = [], 0
    for archive, script, place, members in everything:
        if not any(_id in korean for _id, _ in members):
            continue
        translated += 1
        allowed = WINDOW_PIXELS if place is None else min(budget[place]['pixels'], WINDOW_PIXELS)
        for revision in ('ko', 'ko_red_sun'):
            texts = []
            for _id, text in members:
                entry = korean.get(_id) or {}
                texts.append(entry.get(revision) or entry.get('ko') or text)
            pixels, unencodable = row_pixels(texts, table, width)
            item = {'archive': archive, 'script': script, 'revision': revision,
                    'placement': None if place is None else place[0],
                    'declared_width': None if place is None else place[1],
                    'allowed_pixels': allowed, 'ko_pixels': pixels,
                    'ja': [label(t) for _i, t in members],
                    'ko': [label(t) for t in texts],
                    'ids': [i for i, _t in members]}
            if unencodable:
                problems.append(dict(item, problem=f'unencodable {sorted(set(unencodable))}'))
            elif pixels > allowed:
                where = 'the dialogue window' if place is None else \
                    (f"the widest row the ROM draws at {place[0].lower()} width {place[1]} "
                     f"(archive {budget[place]['archive']} script {budget[place]['script']})")
                problems.append(dict(item, problem=f'{pixels}px exceeds the {allowed}px of {where}'))

    report = {
        'schema': 1,
        'status': 'PASS' if not problems else 'FAIL',
        'scope': 'menu-option rows of the gated story batches, measured with the product advance table',
        'rule': 'a Korean option row may not be wider than the widest Japanese option row the ROM '
                'draws at the same placement and declared width, nor wider than the dialogue window',
        'not_claimed': ['an option row that fits this budget was seen on screen',
                        'the meaning of the declared width in pixels is known',
                        'a row with no position command is bounded by anything but the window'],
        'window_pixels': WINDOW_PIXELS,
        'option_rows_in_rom': len(everything),
        'translated_rows': translated,
        'budgets': [{'placement': k[0], 'declared_width': k[1], **v}
                    for k, v in sorted(budget.items())],
        'problems': problems,
    }
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for problem in problems:
        print(f"archive {problem['archive']} script {problem['script']} {problem['revision']}: "
              f"{problem['problem']} :: {problem['ko']}")
    print(f"{report['status']} {translated} translated option rows of {len(everything)} in the ROM, "
          f"{len(problems)} problems")
    return 0 if not problems else 1


if __name__ == '__main__':
    raise SystemExit(main())
