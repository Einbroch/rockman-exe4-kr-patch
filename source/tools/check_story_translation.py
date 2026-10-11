#!/usr/bin/env python3
"""Gate a story translation batch before it can reach a compiler.

What it refuses, and why each one is a real failure mode this project has
already met somewhere:

  * An id that is not in the extraction sheet, or whose source binding has
    moved.  A translation written against different source is not a
    translation of this ROM.
  * A record that is not story class.  Short labels have their own consumers
    and their own contracts; the dialogue encoder's lead byte terminates some
    of them.
  * More than three lines on a page, or a line wider than the adopted budget.
    Width is measured with the game's advance table, not by counting
    characters: Hangul is a fixed 12-pixel advance and the native glyphs are
    proportional, so a mixed line is neither.
  * A character the build cannot encode: anything that is neither a modern
    Hangul syllable the dialogue extension supplies nor a glyph the native
    table already holds.
  * Korean that still contains kana or CJK, which means the line was copied
    rather than translated.
  * An empty literal.  TextPet cannot parse "" and one of them stops the
    compile for every archive in the build; a per-glyph reveal piece that
    shows no syllable keeps its pause mark instead.
  * A source line with words on it that the Korean leaves empty.  The page
    still draws, so nothing looks broken, but the words are gone: batch 018
    emptied `・・・ですよ` and nine records lost their second line.  Only a
    line that is a lone particle may be emptied, where Korean folds it into
    its neighbour (archive 214, ` を` before an inserted name).
  * A record whose Red Sun source says something else, given the Blue Moon
    Korean again.  Archive 504 names Aquaman in Blue Moon and Gutsman in Red
    Sun, and Red Sun showed 아쿠아맨 over the Gutsman scene because a missing
    Red Sun wording fell back to the Blue Moon one.  Only sources that differ
    in spacing alone may share a wording.  Every check above runs on the Red
    Sun Korean as well, against the Red Sun source lines.
  * A scrambled riddle that no longer reads.  The kidnapper's mail (archives
    7 and 560) reads down the columns from the right, the memo of archives 9
    and 10 reads backwards and their hint data reads as a spiral.  The order
    of the letters is the content, so a Korean line that looks fine can still
    be a riddle with no answer.  Each riddle is registered with its reading
    and the message it gives back: the Japanese has to give back its message,
    which shows the reading is the one the game means, and the Korean its own.

It reports coverage against the whole sheet so progress is a number, not an
impression.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

from analyze_project import PROFILES, sha
from survey_dialogue_layout import ESCAPED_BREAK, HANGUL_ADVANCE, ADVANCE_OFFSET, load_table, advances

p = Path(__file__).resolve().parents[1]
SHEET = p / 'translations/story_source.jsonl'
BATCH_DIR = p / 'translations/story_korean'
HANGUL_FIRST, HANGUL_LAST = 0xAC00, 0xD7A3
# A Japanese line holding only one of these may be emptied in Korean, whose
# particle attaches to the word before it rather than standing on its own line.
LONE_PARTICLES = frozenset('をがはにのとへでもや')
# Scrambled riddles: id -> (reading, message the source gives back, message the
# Korean gives back). Each Japanese message uses every letter of its grid.
KIDNAPPER = ('columns_from_right', 'ひろばにいるおじいさんにききな', '광장에있는할아버지께물어보아라')
MEMO = ('backwards', 'みどりのなび\nたうんえりあさん', '초록 내비\n타운 에리어3')
HINT = ('spiral', 'はなたばのなかをさがしてみるんだな!', '꽃다발속을찾아보는거야!')
RIDDLES = {
    'archive/007/script/1/literal/8': KIDNAPPER,
    'archive/560/script/17/literal/2': KIDNAPPER,
    'archive/560/script/18/literal/0': KIDNAPPER,
    'archive/009/script/10/literal/0': MEMO,
    'archive/010/script/10/literal/0': MEMO,
    'archive/009/script/11/literal/0': HINT,
    'archive/010/script/11/literal/0': HINT,
}


def is_hangul(ch: str) -> bool:
    return HANGUL_FIRST <= ord(ch) <= HANGUL_LAST


def japanese(ch: str) -> bool:
    o = ord(ch)
    return 0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF or 0xFF66 <= o <= 0xFF9D


def source_lines(source: str) -> list[str]:
    """A source text split into the lines the window draws."""
    return source.replace(ESCAPED_BREAK, '\n').split('\n')


def spacing_only(first: str, second: str) -> bool:
    """True when two source texts differ in spaces and line breaks alone."""
    def squeeze(text: str) -> str:
        return ''.join(text.replace(ESCAPED_BREAK, ' ').split())
    return squeeze(first) == squeeze(second)


def unscramble(lines: list[str], reading: str) -> str | None:
    """What a riddle says once its reading is undone; None if the lines are not the grid it needs.

    A quoted riddle keeps the indent of its continued lines, so each row is
    stripped first."""
    rows = [line.strip() for line in lines]
    if reading == 'backwards':
        return '\n'.join(row[::-1] for row in rows)
    if not rows or len({len(row) for row in rows}) != 1:
        return None
    height, width = len(rows), len(rows[0])
    if reading == 'columns_from_right':
        return ''.join(rows[r][c] for c in reversed(range(width)) for r in range(height))
    if reading == 'spiral':
        # Clockwise from the top-right corner, going down first.
        top, bottom, left, right, out = 0, height - 1, 0, width - 1, []
        while True:
            if top > bottom or left > right:
                break
            out += [rows[r][right] for r in range(top, bottom + 1)]
            right -= 1
            if top > bottom or left > right:
                break
            out += [rows[bottom][c] for c in range(right, left - 1, -1)]
            bottom -= 1
            if top > bottom or left > right:
                break
            out += [rows[r][left] for r in range(bottom, top - 1, -1)]
            left += 1
            if top > bottom or left > right:
                break
            out += [rows[top][c] for c in range(left, right + 1)]
            top += 1
        return ''.join(out)
    raise ValueError('unknown riddle reading: ' + reading)


def measure(line: str, table: dict[str, int], width: list[int]) -> tuple[int, list[str]]:
    pixels, unencodable = 0, []
    for ch in line:
        if is_hangul(ch):
            pixels += HANGUL_ADVANCE
        elif ch in table:
            pixels += width[table[ch]]
        else:
            unencodable.append(ch)
    return pixels, unencodable


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', action='append', type=Path,
                    help='one batch file; omit to check every batch in translations/story_korean')
    ap.add_argument('--output', type=Path, default=p / 'analysis/story_translation_gate.json')
    args = ap.parse_args()

    sheet = {}
    for line in SHEET.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        sheet[record['id']] = record
    table = load_table()
    rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba')
               if sha(f.read_bytes()) == PROFILES['blue_moon']['sha256'])
    width = advances(rom, ADVANCE_OFFSET['blue_moon'])

    batches = args.batch or (sorted(BATCH_DIR.glob('*.json')) if BATCH_DIR.exists() else [])
    problems, checked, seen = [], 0, {}
    for f in batches:
        asset = json.loads(f.read_text(encoding='utf-8'))
        for entry in asset['entries']:
            checked += 1
            key = entry['id']
            where = f'{f.name}:{key}'
            record = sheet.get(key)
            if record is None:
                problems.append({'where': where, 'problem': 'id is not in the extraction sheet'})
                continue
            if key in seen:
                problems.append({'where': where, 'problem': 'id already translated in ' + seen[key]})
            seen[key] = f.name
            if record['text_class'] != 'story':
                problems.append({'where': where, 'problem': 'not story class: ' + record['text_class']})
            for profile, binding in entry.get('source_bindings', {}).items():
                if binding != record['source_bindings'].get(profile):
                    problems.append({'where': where, 'problem': 'source binding drift for ' + profile})
            if not entry.get('source_bindings'):
                problems.append({'where': where, 'problem': 'no source binding recorded'})
            ko = entry['ko']
            # TextPet cannot parse an empty string literal, and a single "" stops
            # the compile for every archive in the build. A reveal piece that
            # shows no syllable keeps its pause mark (tools/survey_glyph_reveals.py).
            if ko == '' or entry.get('ko_red_sun') == '':
                problems.append({'where': where, 'problem': 'empty literal; TextPet cannot compile "" '
                                 '(keep at least the pause mark)'})
            # Each wording is checked against the source it is drawn over: the
            # Red Sun Korean of a record whose source differs, against the Red
            # Sun lines.
            differs = record['revision'] == 'differs'
            red_source = record.get('ja_red_sun') if differs else None
            wordings = [('ko', ko, record['ja_lines'])]
            if 'ko_red_sun' in entry:
                wordings.append(('ko_red_sun', entry['ko_red_sun'],
                                 source_lines(red_source) if red_source is not None else record['ja_lines']))
            for field, korean, ja_lines in wordings:
                label = '' if field == 'ko' else field + ': '
                lines = korean.split('\n')
                if len(lines) > record['page_line_budget']:
                    problems.append({'where': where, 'problem': f'{label}{len(lines)} lines exceeds the page budget'})
                for n, line in enumerate(lines):
                    pixels, unencodable = measure(line, table, width)
                    if pixels > record['line_budget_pixels']:
                        problems.append({'where': where, 'problem': f'{label}line {n} is {pixels}px over the '
                                         f"{record['line_budget_pixels']}px budget", 'line': line})
                    if unencodable:
                        problems.append({'where': where, 'problem': f'{label}characters the build cannot encode: '
                                         + ' '.join(f'{c!r} ({unicodedata.name(c, "?")})'
                                                    for c in dict.fromkeys(unencodable))})
                if any(japanese(c) for c in korean):
                    problems.append({'where': where, 'problem': f'{label}Korean still contains kana or CJK'})
                # The opening build could spend the Japanese comma's table entry on
                # an ASCII comma because it retranslated its whole archive. A story
                # archive keeps untranslated Japanese beside the Korean, so that
                # entry has to stay Japanese and an ASCII comma has nothing to
                # encode to. Use the Japanese comma, or no comma.
                if ',' in korean:
                    problems.append({'where': where, 'problem': f"{label}ASCII comma has no glyph; use the "
                                     "Japanese comma U+3001 or drop it", 'ko': korean})
                # The source line breaks were authored for this game's box, and a
                # translation that lands on the wrong record usually has a different
                # shape. Changing the shape can be right, but it has to be meant.
                if len(lines) != len(ja_lines) and not entry.get('line_count_change_ok'):
                    problems.append({'where': where, 'problem': f"{label}{len(lines)} Korean lines against "
                                     f"{len(ja_lines)} source lines; set line_count_change_ok if intended",
                                     'ja': '\n'.join(ja_lines), 'ko': korean})
                # A blank Korean line under a Japanese line with words on it draws a
                # clean page with the words missing. Checked line by line only where
                # the shapes agree; a deliberate reshape is judged as a whole above.
                if len(lines) == len(ja_lines):
                    for n, (ja_line, ko_line) in enumerate(zip(ja_lines, lines)):
                        source = ja_line.strip()
                        if not ko_line.strip() and source and source not in LONE_PARTICLES:
                            problems.append({'where': where, 'problem': f'{field} line {n} is empty under source '
                                             f'line {source!r}; only a lone particle line may be emptied'})
            if key in RIDDLES:
                reading, _, message = RIDDLES[key]
                if unscramble(ko.split('\n'), reading) != message:
                    problems.append({'where': where, 'problem': f'the riddle no longer reads: read {reading} it '
                                     f'must give back {message!r}', 'ko': ko})
            if differs and 'ko_red_sun' not in entry:
                problems.append({'where': where, 'problem': 'source differs between revisions but only one Korean line given'})
            elif differs:
                if entry.get('ja_red_sun') != red_source:
                    problems.append({'where': where, 'problem': 'the batch does not show the Red Sun source the '
                                     'sheet holds; prepare the batch again'})
                if not spacing_only(record['ja'], red_source) and entry['ko_red_sun'] == ko:
                    problems.append({'where': where, 'problem': 'the Red Sun source says something else but its '
                                     'Korean repeats the Blue Moon line', 'ja': record['ja'],
                                     'ja_red_sun': red_source, 'ko': ko})

    # The registry itself is held to the sheet: a reading that does not give
    # back the registered message from the Japanese is a misread riddle.
    for key, (reading, message, _) in RIDDLES.items():
        record = sheet.get(key)
        if record is None or unscramble(record['ja_lines'], reading) != message:
            problems.append({'where': key, 'problem': f'the source does not read {reading} as {message!r}; '
                             'the riddle registry is wrong'})

    story_ids = {k for k, v in sheet.items() if v['text_class'] == 'story'}
    report = {
        'schema': 1,
        'status': 'PASS' if not problems else 'FAIL',
        'scope': 'story translation batches against the extraction sheet, the adopted line budget and the encodable character set',
        'sheet_sha256': sha(SHEET.read_bytes()),
        # A batch under test can live outside the project; record it as given
        # rather than refusing to report on it.
        'batches': [{'path': f.relative_to(p).as_posix() if f.resolve().is_relative_to(p) else str(f),
                     'sha256': sha(f.read_bytes())} for f in batches],
        'entries_checked': checked,
        'story_ids_total': len(story_ids),
        'story_ids_translated': len(set(seen) & story_ids),
        'coverage': round(len(set(seen) & story_ids) / len(story_ids), 5) if story_ids else 0,
        'problems': problems[:200],
        'problem_count': len(problems),
        'not_claimed': ['a line that fits the budget was seen on screen',
                        'these archives were observed in the normal dialogue renderer'],
        'tool_sha256': sha(Path(__file__).read_bytes()),
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(report['status'], report['entries_checked'], 'entries,', report['problem_count'], 'problems, coverage',
          f"{report['story_ids_translated']}/{report['story_ids_total']}")
    for x in problems[:10]:
        print('  ', x)
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
