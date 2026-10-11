#!/usr/bin/env python3
"""Expand an authored story batch into a source-bound batch the gate can check.

The authored file carries only wording, keyed by script/literal path, because
the archives it covers hold identical source.  This tool attaches each record's
id and source bindings from the extraction sheet, refuses to leave any story
record of a covered archive untranslated, and writes the Japanese next to the
Korean so a review reads as a pair rather than as a list of Korean lines.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyze_project import sha
from check_story_translation import spacing_only
from survey_dialogue_layout import ESCAPED_BREAK

p = Path(__file__).resolve().parents[1]

def red_sun_wording(record: dict, path: str, scripts_red_sun: dict, by_source: dict, blue_moon: str):
    """Pick the Red Sun Korean of a record whose source differs between revisions.

    Archive 504 names Aquaman in Blue Moon and Gutsman in Red Sun. The Red Sun
    wording used to fall back to the Blue Moon one whenever none was authored,
    so Red Sun showed 아쿠아맨 over the Gutsman scene and gave Saloma's words to
    Hinoken. It is looked up by the Red Sun source like any other line, and may
    borrow the Blue Moon wording only when the two sources differ in spacing.
    """
    if path in scripts_red_sun:
        return scripts_red_sun[path], 'path'
    source = record['ja_red_sun'].replace(ESCAPED_BREAK, '\n')
    if source in by_source:
        return by_source[source], 'source'
    if spacing_only(record['ja'], record['ja_red_sun']):
        return blue_moon, 'spacing'
    return None, None


def wording(record: dict, path: str, scripts: dict, by_source: dict):
    """Pick the Korean for one record, and say which rule supplied it.

    Keyed by the record, never by the path alone: archives covered together can
    hold different lines at the same script/literal path, and resolving by path
    would hand them all the first archive's wording.
    """
    if path in scripts:
        return scripts[path], 'path'
    source = record['ja'].replace(ESCAPED_BREAK, '\n')
    if source in by_source:
        return by_source[source], 'source'
    return None, None


SHEET = p / 'translations/story_source.jsonl'
AUTHORED = p / 'translations/story_authored'
OUT_DIR = p / 'translations/story_korean'


def no_pointer_claim() -> set[int]:
    """Archives nothing in the pointer table points at.

    The build relocates a rewritten archive to the end of the ROM and rewrites
    the pointer that claimed it. Five archives have no such claim, so there is
    nothing to repoint and the Korean would sit in the ROM unread. Catching it
    here rather than at build time means the wording is never written.
    """
    analysis = json.loads((p / 'analysis/blue_moon_analysis.json').read_text(encoding='utf-8'))
    return {int(row['index']) for row in analysis['archives_detail'] if not row['pointers']}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', required=True, help='batch number, e.g. 001')
    args = ap.parse_args()

    authored = json.loads((AUTHORED / f'batch_{args.batch}.json').read_text(encoding='utf-8'))
    sheet = {}
    for line in SHEET.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        sheet[record['id']] = record

    covered = set(authored['archives'])
    unreachable = sorted(covered & no_pointer_claim())
    if unreachable and not authored.get('accept_unrelocatable'):
        raise SystemExit(f'archives {unreachable} carry no pointer claim, so the build cannot relocate '
                         'them; translating one produces text the ROM would never load')
    wanted = {k for k, v in sheet.items() if v['archive'] in covered and v['text_class'] == 'story'}
    # A batch may leave named records in Japanese, but only by saying so and why.
    # Some lines are puzzles whose scrambling is the puzzle; inventing a Korean
    # one without knowing the intended answer would ship a broken riddle.
    deferred = []
    for path, reason in authored.get('deferred', {}).items():
        for archive in sorted(covered):
            key = f'archive/{archive:03d}/{path}'
            if key in wanted:
                deferred.append({'id': key, 'reason': reason})
    # Some archives repeat one system message dozens of times. Authoring those
    # by source line keeps the wording in one place; the batch still lists every
    # id with its own Japanese and Korean, so nothing is hidden. A per-path entry
    # always wins, which is how a line that needs different Korean in one place
    # gets it.
    #
    # Resolution is per archive, not per path: four archives can hold four
    # different lines at script/18/literal/0, and keying by path alone silently
    # gives them all the first archive's wording.
    by_source = {k.replace(ESCAPED_BREAK, '\n'): v for k, v in authored.get('by_source', {}).items()}
    scripts = authored.get('scripts', {})
    scripts_red_sun = authored.get('scripts_red_sun', {})
    deferred_ids = {d['id'] for d in deferred}
    entries, no_red_sun = [], []
    used_paths, used_red_paths, used_sources = set(), set(), set()
    for key in sorted(wanted):
        if key in deferred_ids:
            continue
        record = sheet[key]
        path = key.split('/', 2)[2]
        ko, rule = wording(record, path, scripts, by_source)
        if rule is None:
            continue
        (used_paths if rule == 'path' else used_sources).add(
            path if rule == 'path' else record['ja'].replace(ESCAPED_BREAK, '\n'))
        entry = {'id': key, 'ja': record['ja'], 'ko': ko, 'source_bindings': record['source_bindings']}
        if record['revision'] == 'differs':
            red, red_rule = red_sun_wording(record, path, scripts_red_sun, by_source, ko)
            if red_rule is None:
                no_red_sun.append(key)
                continue
            if red_rule == 'path':
                used_red_paths.add(path)
            elif red_rule == 'source':
                used_sources.add(record['ja_red_sun'].replace(ESCAPED_BREAK, '\n'))
            entry['ja_red_sun'] = record['ja_red_sun']
            entry['ko_red_sun'] = red
        entries.append(entry)

    if no_red_sun:
        first = sheet[no_red_sun[0]]
        raise SystemExit(f'{len(no_red_sun)} records say something else in Red Sun and have no Red Sun wording, '
                         f"first: {no_red_sun[0]} {first['ja']!r} / Red Sun {first['ja_red_sun']!r}")
    # An authored line that reaches nothing is a typo in the source text, and a
    # typo here means some record is about to be reported as untranslated for
    # the wrong reason.
    stray = sorted(set(scripts) - used_paths) + sorted(set(scripts_red_sun) - used_red_paths)
    if stray:
        raise SystemExit('authored path matches no record: ' + stray[0])
    unused = sorted(set(by_source) - used_sources)
    if unused:
        raise SystemExit('by_source line matches no record: ' + repr(unused[0]))

    missing = sorted(wanted - {e['id'] for e in entries} - {d['id'] for d in deferred})
    if missing:
        raise SystemExit(f'{len(missing)} story records of the covered archives are neither translated '
                         f'nor deferred, first: {missing[0]}')
    overlap = sorted({e['id'] for e in entries} & {d['id'] for d in deferred})
    if overlap:
        raise SystemExit('id is both translated and deferred: ' + overlap[0])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f'batch_{args.batch}.json'
    out.write_text(json.dumps({
        'schema': 1,
        'batch': args.batch,
        'state': authored['state'],
        'scope': authored['scope'],
        'provenance': authored['provenance'],
        'authored': (AUTHORED / f'batch_{args.batch}.json').relative_to(p).as_posix(),
        'authored_sha256': sha((AUTHORED / f'batch_{args.batch}.json').read_bytes()),
        'sheet_sha256': sha(SHEET.read_bytes()),
        'archives': sorted(covered),
        'deferred': deferred,
        'entries': entries,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'batch {args.batch}: {len(entries)} entries over archives {sorted(covered)}'
          + (f', {len(deferred)} deferred' if deferred else '')
          + f' -> {out.relative_to(p).as_posix()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
