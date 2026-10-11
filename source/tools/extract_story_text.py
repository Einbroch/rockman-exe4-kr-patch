#!/usr/bin/env python3
"""Write the story-text working sheet: one record per translatable literal, with
a stable id, the source line, and everything a translator needs to decide the
Korean without opening the ROM.

Two things the sheet carries that a plain dump would not:

  * A per-record binding to the exact source payload and TPL block, so a later
    build can refuse a translation that was written against different source.
  * The native pixel width of each source line, measured with the game's own
    advance table, next to the Korean budget.  A line that was already near the
    window edge in Japanese has no room to grow.

Records for archives a named consumer contract owns are not written: those
strings go through their own contract, and mixing them into the story pass is
how a chip name ends up in a dialogue encoder.
"""
from __future__ import annotations

import json
from pathlib import Path

from analyze_project import PROFILES, sha, scripts
from verify_tpi_index import lz77_decompress
from survey_dialogue_layout import ESCAPED_BREAK, HANGUL_ADVANCE, LEGACY_INDICES, ADVANCE_OFFSET, load_table, advances

p = Path(__file__).resolve().parents[1]
OUT = p / 'translations/story_source.jsonl'
# Story-candidate archives whose widest line proves another window: five BBS
# list pages, a mystery-data list and the ending credit line.
OTHER_WINDOWS = {'6E43CC.tpl', '6FA82C.tpl', '6FB194.tpl', '6FBB68.tpl', '6FC5CC.tpl', '6FCF58.tpl', '6FD768.tpl'}
DIALOGUE_BUDGET = 180


def budget(lines_pixels: list[int]) -> int:
    """The dialogue box fits 180px. A record whose own source line is already
    wider than that is drawn somewhere wider, and the game itself is the proof,
    so that record is allowed the width it already has.

    Doing this per record rather than per archive matters because archives mix
    windows: archive 008 holds both ordinary speech and the 447px ending credit
    line, and an archive-wide budget would license 447px speech."""
    return max(DIALOGUE_BUDGET, max(lines_pixels))


def collect(key: str, table: dict[str, int], width: list[int]) -> dict[str, dict]:
    analysis = json.loads((p / f'analysis/{key}_analysis.json').read_text(encoding='utf-8'))
    rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes()) == PROFILES[key]['sha256'])
    by_offset = {int(row['offset']): row for row in analysis['archives_detail']}
    out: dict[str, dict] = {}
    for f in sorted((p / f'analysis/{key}_tpl').glob('*.tpl')):
        row = by_offset[int(f.stem, 16)]
        index = int(row['index'])
        # Bind to the file's bytes, not to a newline-normalised copy of them:
        # the build edits this file in place and has to see the same bytes.
        block_sha = sha(f.read_bytes())
        text = f.read_text(encoding='utf-8')
        # Re-derive the payload from the ROM rather than trusting the recorded
        # digest, so a binding written here is bound to bytes, not to a report.
        if row['compressed']:
            data, consumed = lz77_decompress(rom, row['offset'])
            if consumed != row['size']:
                raise ValueError('compressed length mismatch')
        else:
            data = rom[row['offset']:row['offset'] + row['size']]
        payload_sha = sha(data)
        if payload_sha != row['payload_sha256']:
            raise ValueError('archive payload no longer matches the recorded analysis')
        for number, language, values, _ in scripts(text):
            for k, value in enumerate(values):
                lines = value.replace(ESCAPED_BREAK, '\n').split('\n')
                if not any(0x3040 <= ord(c) <= 0x30FF or 0x4E00 <= ord(c) <= 0x9FFF or 0xFF66 <= ord(c) <= 0xFF9D
                           for c in value):
                    continue
                out[f'archive/{index:03d}/script/{number}/literal/{k}'] = {
                    'archive': index, 'archive_file': f.name, 'script': number, 'literal': k,
                    'language': language, 'ja': value, 'ja_lines': lines,
                    'ja_line_pixels': [sum(width[table[c]] for c in line if c in table) for line in lines],
                    'source_payload_sha256': payload_sha, 'source_tpl_sha256': block_sha,
                    'other_window': f.name in OTHER_WINDOWS,
                }
    return out


table = load_table()
roms = {}
collected = {}
for key in PROFILES:
    rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes()) == PROFILES[key]['sha256'])
    roms[key] = rom
    collected[key] = collect(key, table, advances(rom, ADVANCE_OFFSET[key]))

population = json.loads((p / 'analysis/dialogue_population.json').read_text(encoding='utf-8'))
owned = set(population['profiles']['blue_moon']['owned_archives'])
# Archives 1 and 2 are owned for four save-screen labels each (mmbn4s), but they
# also hold 143 message-box scripts each -- the navigator's folder menu, PET
# messages -- that the normal dialogue renderer draws. Those go through the
# story pass; build_story_batch.py starts from the menu stage's moved copy.
owned -= {1, 2}
# Archive 418 is owned only for script 11, the NAME input options (packed
# three-byte indexes the four-byte Hangul stream cannot replace). Its other
# scripts are Town Area net-navi speech in the message box; excluding the whole
# archive left that speech Japanese (user report, 2026-10-10).
owned -= {418}
OWNED_SCRIPTS = {418: {11}}
blue, red = collected['blue_moon'], collected['red_sun']

records = []
for key_id in sorted(set(blue) | set(red)):
    b, r = blue.get(key_id), red.get(key_id)
    base = b or r
    if base['archive'] in owned:
        continue
    if base['script'] in OWNED_SCRIPTS.get(base['archive'], ()):
        continue
    if b and r and b['ja'] == r['ja']:
        revision = 'both'
    elif b and r:
        revision = 'differs'
    else:
        revision = 'blue_moon' if b else 'red_sun'
    # The source itself separates two script languages, and they behave like two
    # different jobs: mmbn4 is speech in a message box, mmbn4s is short labels
    # (menu items, staff credits) whose consumers are classified one at a time.
    # Translating a short label as if it were dialogue is how a label ends up in
    # a renderer that terminates on the dialogue encoder's lead byte.
    text_class = 'story' if base['language'] == 'mmbn4' else 'short'
    record = {'id': key_id, 'revision': revision, 'text_class': text_class, **{k: base[k] for k in
              ('archive', 'archive_file', 'script', 'literal', 'language', 'ja', 'ja_lines', 'ja_line_pixels',
               'other_window')},
              'line_budget_pixels': budget(base['ja_line_pixels']),
              'line_budget_syllables': budget(base['ja_line_pixels']) // HANGUL_ADVANCE,
              'page_line_budget': 3,
              'source_bindings': {k: {'payload_sha256': collected[k][key_id]['source_payload_sha256'],
                                      'tpl_sha256': collected[k][key_id]['source_tpl_sha256']}
                                  for k in PROFILES if key_id in collected[k]},
              'state': 'untranslated'}
    if revision == 'differs':
        record['ja_red_sun'] = r['ja']
    records.append(record)

OUT.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in records), encoding='utf-8')
summary = {
    'schema': 1,
    'status': 'PASS extraction only; every record is untranslated',
    'scope': 'story literals of both revisions, excluding archives a named consumer contract owns',
    'sheet': OUT.relative_to(p).as_posix(),
    'sheet_sha256': sha(OUT.read_bytes()),
    'records': len(records),
    'records_by_revision': {r: sum(1 for x in records if x['revision'] == r) for r in ('both', 'differs', 'blue_moon', 'red_sun')},
    'records_by_class': {c: sum(1 for x in records if x['text_class'] == c) for c in ('story', 'short')},
    'story_class': {
        'records': sum(1 for x in records if x['text_class'] == 'story'),
        'archives': len({x['archive'] for x in records if x['text_class'] == 'story'}),
        'distinct_japanese_lines': len({x['ja'] for x in records if x['text_class'] == 'story'}),
        'japanese_characters': sum(len(x['ja']) for x in records if x['text_class'] == 'story'),
        'over_budget_records': sum(1 for x in records if x['text_class'] == 'story' and max(x['ja_line_pixels']) > x['line_budget_pixels']),
    },
    'short_class_archives': sorted({x['archive'] for x in records if x['text_class'] == 'short'}),
    'records_in_other_windows': sum(1 for x in records if x['other_window']),
    'distinct_japanese_lines': len({x['ja'] for x in records}),
    'japanese_characters': sum(len(x['ja']) for x in records),
    'archives': len({x['archive'] for x in records}),
    'excluded_owned_archives': sorted(owned),
    'widest_source_line_pixels': max(max(x['ja_line_pixels']) for x in records),
    'records_whose_source_already_exceeds_its_budget': sum(1 for x in records if max(x['ja_line_pixels']) > x['line_budget_pixels']),
    'not_claimed': ['these archives were observed in the normal dialogue renderer',
                    'the indexed archives are all the text in the ROM',
                    'literals without a Japanese character are covered: a line like the ASCII ending credit '
                    'is skipped here and needs its own decision'],
    'tool_sha256': sha(Path(__file__).read_bytes()),
}
(p / 'analysis/story_extraction.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(summary['records'], 'records,', summary['distinct_japanese_lines'], 'distinct lines,',
      summary['archives'], 'archives;', summary['records_by_revision'],
      '| source already over budget:', summary['records_whose_source_already_exceeds_its_budget'])
