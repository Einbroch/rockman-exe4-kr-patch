#!/usr/bin/env python3
"""Check that gated story lines keep the glossary's wording for the terms they name.

The story gate resolves wording per Japanese source line -- one source, one
Korean -- so it cannot see a name that recurs inside *different* source lines,
and those drift. The story-data puzzle named the sun spirit 해님 in its blank
and 오텐코 님 in the very next chapter; twelve lines called the PET menu's
데이터 도감 and 배틀칩 by other names, so a player told to open the one could
not find it on the menu.

The rule comes from translations/glossary.tsv alone: when a gated line's
Japanese contains a glossary term, that line's Korean must contain the
glossary's Korean. Every row is enforced whatever its state, because a
provisional menu term is still what the player sees in the menu.

A longer word can contain a term without being it (アメロッパン is a bread, not
the continent). Those are listed below per term, each with its reason, and
removed from the Japanese before the term is looked for; nothing else is
exempt.

Battle chip names are terms too, taken from the chip catalogue the chip folder
and library draw: a line that tells the player to use a chip has to call it
what the folder calls it. The dialogue had 메트가드 where the folder says
메톨가드 (a trade asks for 「메톨가드1 A」), 흡입 as 빨아들이다, and a dozen
names spaced differently (버블 샷 for 버블샷). The name is the catalogue name
without its number or suffix (キャノン for キャノン1..3), three characters or
longer; where the glossary lists the same source, the glossary row wins.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from analyze_project import sha
from survey_dialogue_layout import ESCAPED_BREAK

p = Path(__file__).resolve().parents[1]
BATCH_DIR = p / 'translations/story_korean'
GLOSSARY = p / 'translations/glossary.tsv'
CHIP_CATALOG = p / 'translations/chip_catalog_korean_draft.json'
BREAK = chr(10)
CHIP_SUFFIX = re.compile(r'(\d+|EX|SP|DS|V\d)$')

# term -> {longer word containing it: why that word is not the term}
NOT_THE_TERM = {
    'アメロッパ': {'アメロッパン': 'a bread sold in the story (아메로팡), not the continent'},
    'ナビカス': {'ナビカスタマイザー': 'the device named in full (내비 커스터마이저, its own row), not the short '
                                   'menu word'},
    'ロール': {'パトロール': 'a patrol (순찰), not Roll or her navi chip'},
}


def glossary(path: Path = GLOSSARY) -> list[dict]:
    with path.open(encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def chip_terms(path: Path = CHIP_CATALOG) -> list[dict]:
    """The chip folder's names as terms: キャノン1..3 give キャノン -> 캐논."""
    rows: dict[str, dict] = {}
    for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
        source = CHIP_SUFFIX.sub('', entry['source'].strip())
        korean = CHIP_SUFFIX.sub('', entry['text'].strip())
        if len(source) >= 3 and source not in rows:
            rows[source] = {'decision_id': f"chip-catalog:{entry['chip_id']}", 'source': source, 'korean': korean}
    return list(rows.values())


def flat(text: str) -> str:
    """One line of text, so a term is found wherever the window breaks it."""
    return text.replace(ESCAPED_BREAK, ' ').replace(BREAK, ' ')


def names(japanese: str, term: str) -> bool:
    for longer in NOT_THE_TERM.get(term, {}):
        japanese = japanese.replace(longer, '')
    return term in japanese


def check(batches: list[Path], terms: list[dict]) -> tuple[list[dict], dict[str, int]]:
    problems: list[dict] = []
    usage = {t['source']: 0 for t in terms}
    for batch in batches:
        for entry in json.loads(batch.read_text(encoding='utf-8'))['entries']:
            japanese = flat(entry['ja'])
            # A record whose source differs between revisions is held to each
            # revision's own source: Red Sun names Gutsman where Blue Moon names
            # Aquaman, and the Red Sun Korean has to follow the Red Sun line.
            red_japanese = flat(entry['ja_red_sun']) if 'ja_red_sun' in entry else japanese
            for term in terms:
                named = False
                for revision, source, korean in (('both', japanese, entry['ko']),
                                                 ('red_sun', red_japanese, entry.get('ko_red_sun'))):
                    if korean is None or not names(source, term['source']):
                        continue
                    named = True
                    if term['korean'] in flat(korean):
                        continue
                    problems.append({'batch': batch.name, 'id': entry['id'], 'revision': revision,
                                     'term': term['source'], 'expected': term['korean'],
                                     'decision_id': term['decision_id'], 'ko': korean})
                usage[term['source']] += named
    return problems, usage


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', action='append', type=Path,
                    help='one batch file; omit to check every batch in translations/story_korean')
    ap.add_argument('--glossary', type=Path, default=GLOSSARY)
    ap.add_argument('--output', type=Path, default=p / 'analysis/story_glossary_terms.json')
    a = ap.parse_args()

    listed = glossary(a.glossary)
    chips = [t for t in chip_terms() if t['source'] not in {g['source'] for g in listed}]
    terms = listed + chips
    batches = a.batch or sorted(BATCH_DIR.glob('*.json'))
    problems, usage = check(batches, terms)
    report = {
        'schema': 1,
        'status': 'PASS' if not problems else 'FAIL',
        'scope': 'every gated story line whose Japanese names a glossary term or a battle chip',
        'rule': 'a line whose Japanese contains a glossary source term or a chip name must contain that '
                'term\'s Korean',
        'not_claimed': ['a term the glossary does not list is consistent',
                        'a term split across a line break in the Japanese was checked',
                        'a chip name shorter than three characters was checked'],
        'glossary': a.glossary.resolve().relative_to(p).as_posix()
        if a.glossary.resolve().is_relative_to(p) else str(a.glossary),
        'glossary_sha256': sha(a.glossary.read_bytes()),
        'chip_catalog': CHIP_CATALOG.relative_to(p).as_posix(),
        'chip_catalog_sha256': sha(CHIP_CATALOG.read_bytes()),
        'glossary_terms': len(listed),
        'chip_terms': len(chips),
        'batches': [{'path': b.resolve().relative_to(p).as_posix() if b.resolve().is_relative_to(p) else str(b),
                     'sha256': sha(b.read_bytes())} for b in batches],
        'not_the_term': NOT_THE_TERM,
        'lines_checked': sum(usage.values()),
        'usage': usage,
        'problems': problems,
    }
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + BREAK, encoding='utf-8')
    for problem in problems:
        print(f"{problem['id']} {problem['revision']}: {problem['term']} should read {problem['expected']} "
              f"({problem['decision_id']}) :: {flat(problem['ko'])}")
    print(f"{report['status']} {report['lines_checked']} term uses over {len(listed)} glossary terms and "
          f"{len(chips)} chip names, {len(problems)} problems")
    return 0 if not problems else 1


if __name__ == '__main__':
    raise SystemExit(main())
