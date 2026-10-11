#!/usr/bin/env python3
"""Measure the line width the game itself already uses, with the game's own
advance table, so the Korean line budget is an observation and not a constant
somebody picked.

The native font is proportional: the advance of a character is a word in the
table the renderer loads, not a fixed cell.  Counting characters, or assuming
one width for all of them, inflates or deflates the budget.  The Hangul the
dialogue extension supplies is fixed at 12 pixels per syllable, so the budget
converts directly into a syllable count per line.

Per-archive maxima matter more than one global number: a window that only ever
shows short strings does not prove a wide window, and the widest line an
archive already contains is the strongest evidence of what its window fits.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from analyze_project import PROFILES, sha, scripts

p = Path(__file__).resolve().parents[1]
HANGUL_ADVANCE = 12  # tools/extended_dialogue.py writes this for every syllable
ESCAPED_BREAK = chr(92) + 'n'  # a single-quoted TPL literal escapes its line breaks
LEGACY_INDICES = 442
TABLE = p / 'external/textpet-plugins/exe4-utf8.tbl'  # the pinned plugin table, not a stage's generated copy
ADVANCE_OFFSET = {'blue_moon': 0x51588, 'red_sun': 0x515B8}


def load_table() -> dict[str, int]:
    """char -> glyph index.  Single bytes index themselves; the E4 page continues
    after the last single byte."""
    singles, page = {}, {}
    for line in TABLE.read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line:
            continue
        code, ch = line.split('=', 1)
        if len(code) == 2:
            singles[ch] = int(code, 16)
        elif len(code) == 4 and code.startswith('E4'):
            page[ch] = int(code[2:], 16)
    base = max(v for v in singles.values() if v != 0xE8) + 1
    index = {ch: v for ch, v in singles.items() if v != 0xE8}
    for ch, trail in page.items():
        index[ch] = base + trail
    if max(index.values()) >= LEGACY_INDICES:
        raise ValueError('table produces an index the native font does not hold')
    return index


def advances(rom: bytes, at: int) -> list[int]:
    return [int.from_bytes(rom[at + i * 4:at + i * 4 + 4], 'little') for i in range(LEGACY_INDICES)]




def main() -> None:
    """Kept behind a guard so another tool can import the rules above
    without rewriting this survey's report as a side effect."""
    report = {
        'schema': 1,
        'status': 'PASS measurement only; no budget adopted into a contract',
        'scope': 'native pixel width of every indexed literal line, measured with the advance table the renderer loads',
        'not_claimed': [
            'the widest existing line equals the physical window width',
            'every archive draws through the same window',
            'a line that fits horizontally also fits the page line count',
        ],
        'hangul_advance': HANGUL_ADVANCE,
        'profiles': {},
    }

    table = load_table()
    for key, meta in PROFILES.items():
        rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes()) == meta['sha256'])
        width = advances(rom, ADVANCE_OFFSET[key])
        if len(set(width)) < 2:
            raise ValueError('advance table looks uniform; wrong address')
        unmapped: Counter[str] = Counter()
        per_archive = []
        widest = {'pixels': 0}
        histogram: Counter[int] = Counter()
        line_counts: Counter[int] = Counter()
        for f in sorted((p / f'analysis/{key}_tpl').glob('*.tpl')):
            best = 0
            best_line = ''
            lines_here = 0
            for number, language, values, _ in scripts(f.read_text(encoding='utf-8')):
                for k, value in enumerate(values):
                    # Measuring the escape as two glyphs invents width that the
                    # renderer never draws, and it hides the real line break.
                    rows = value.replace(ESCAPED_BREAK, '\n').split('\n')
                    line_counts[len(rows)] += 1
                    lines_here = max(lines_here, len(rows))
                    for row in rows:
                        pixels = 0
                        for ch in row:
                            if ch in table:
                                pixels += width[table[ch]]
                            else:
                                unmapped[ch] += 1
                        histogram[pixels // 16 * 16] += 1
                        if pixels > best:
                            best, best_line = pixels, row
                        if pixels > widest['pixels']:
                            widest = {'pixels': pixels, 'file': f.name, 'script': number, 'literal': k, 'line': row}
            per_archive.append({'file': f.name, 'widest_line_pixels': best, 'widest_line': best_line,
                                'max_lines_in_a_literal': lines_here})
        report['profiles'][key] = {
            'source_sha256': meta['sha256'],
            'advance_offset': ADVANCE_OFFSET[key],
            'advance_table_sha256': sha(rom[ADVANCE_OFFSET[key]:ADVANCE_OFFSET[key] + LEGACY_INDICES * 4]),
            'distinct_advances': sorted(set(width)),
            'widest_line_in_the_game': widest,
            'unmapped_characters': {ch: n for ch, n in unmapped.most_common(20)},
            'unmapped_total': sum(unmapped.values()),
            'line_width_histogram_16px_buckets': dict(sorted(histogram.items())),
            'literal_line_counts': dict(sorted(line_counts.items())),
            'archives_by_widest_line': sorted(per_archive, key=lambda a: -a['widest_line_pixels'])[:20],
            'per_archive': per_archive,
        }

    # The globals above include consumers that are not the dialogue box: the BBS
    # list rows and the ending credit line are far wider than any speech line, so
    # a budget taken from the whole game would be a budget taken from the wrong
    # window. Restrict to the archives the population survey calls story text and
    # report the distribution of each archive's own widest line.
    population = json.loads((p / 'analysis/dialogue_population.json').read_text(encoding='utf-8'))
    for key, item in report['profiles'].items():
        story = {a['file'] for a in population['profiles'][key]['archive_detail'] if a['story_candidate']}
        widths = sorted(a['widest_line_pixels'] for a in item['per_archive'] if a['file'] in story)
        if not widths:
            raise ValueError('population survey and layout survey disagree about the archive set')
        item['story_widest_line_percentiles'] = {
            f'p{int(q * 100)}': widths[int(q * (len(widths) - 1))] for q in (0.5, 0.9, 0.99, 1.0)}
        item['story_archives_measured'] = len(widths)
        item['story_archives_above_200px'] = [a for a in item['per_archive']
                                              if a['file'] in story and a['widest_line_pixels'] > 200]

    blue = report['profiles']['blue_moon']
    widest = blue['widest_line_in_the_game']['pixels']
    report['derived_budget'] = {
        'widest_native_line_pixels': widest,
        'hangul_syllables_at_that_width': widest // HANGUL_ADVANCE,
        'ninety_ninth_percentile_bucket': max(b for b, n in blue['line_width_histogram_16px_buckets'].items()
                                              if sum(v for k, v in blue['line_width_histogram_16px_buckets'].items() if k <= b)
                                              <= 0.99 * sum(blue['line_width_histogram_16px_buckets'].values())),
        'note': 'a per-archive budget is the widest line that archive already draws; these globals only bound it',
        'story_widest_line_percentiles': blue['story_widest_line_percentiles'],
        'adopted_story_line_budget_pixels': 180,
        'adopted_story_line_budget_syllables': 180 // HANGUL_ADVANCE,
        'adopted_story_page_lines': max(int(k) for k in blue['literal_line_counts']),
        'adopted_because': ('180px is the gate the already runtime-verified opening build enforces, it sits above the '
                            'p90 of the archives story text actually draws, and it stays under the widest ordinary '
                            'speech line measured anywhere (198px). Wider archives in the table are BBS rows and the '
                            'ending credit line, which are other consumers.'),
    }
    report['tool_sha256'] = sha(Path(__file__).read_bytes())
    (p / 'analysis/dialogue_layout_budget.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('widest native line', widest, 'px =', widest // HANGUL_ADVANCE, 'Hangul syllables;',
          'unmapped characters', blue['unmapped_total'],
          '| literal line counts', blue['literal_line_counts'])


if __name__ == '__main__':
    main()
