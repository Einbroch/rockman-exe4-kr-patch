#!/usr/bin/env python3
"""Start an archive's authored batch from decisions already made elsewhere.

System messages recur across the whole game: the pickup line appears 174 times,
the yes/no pair 223 times each. Once a batch has settled on wording for a source
line, re-deciding it in the next archive is wasted effort and a chance to drift.

This prints, for a target archive, which of its source lines an existing batch
already translates, and emits a `by_source` block seeded with those decisions
plus an empty slot for every line still to write. It proposes; it does not
adopt. A reused line still has to read correctly in its new place, and a batch
that takes one is saying it does.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from survey_dialogue_layout import ESCAPED_BREAK

p = Path(__file__).resolve().parents[1]
SHEET = p / 'translations/story_source.jsonl'
BATCHES = p / 'translations/story_korean'


def unescape(text: str) -> str:
    return text.replace(ESCAPED_BREAK, '\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', type=int, action='append', required=True,
                    help='archive index to start; repeatable')
    ap.add_argument('--out', type=Path, help='write the starter JSON here instead of printing it')
    a = ap.parse_args()

    decided: dict[str, set[str]] = {}
    for batch in sorted(BATCHES.glob('*.json')):
        for entry in json.loads(batch.read_text(encoding='utf-8'))['entries']:
            decided.setdefault(unescape(entry['ja']), set()).add(entry['ko'])

    wanted: Counter[str] = Counter()
    for line in SHEET.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        if record['archive'] in a.archive and record['text_class'] == 'story':
            wanted[unescape(record['ja'])] += 1

    reused, fresh, conflicted = {}, {}, {}
    for source, count in wanted.most_common():
        known = decided.get(source)
        if not known:
            fresh[source] = ''
        elif len(known) == 1:
            reused[source] = next(iter(known))
        else:
            # The same Japanese already carries two different Korean lines, so
            # this one is a decision, not a lookup.
            conflicted[source] = sorted(known)

    starter = {
        'schema': 1,
        'batch': 'NNN',
        'state': 'needs_review',
        'scope': f'Archives {sorted(a.archive)}.',
        'provenance': 'Claude translator-authored Japanese to Korean; no independent review yet',
        'archives': sorted(a.archive),
        'tone': '',
        'by_source': {**reused, **{k: v[0] for k, v in conflicted.items()}, **fresh},
    }
    records = sum(wanted.values())
    print(f'archives {sorted(a.archive)}: {records} records, {len(wanted)} distinct lines')
    print(f'  reused from existing batches: {len(reused)}')
    print(f'  already translated two ways, pick one: {len(conflicted)}')
    for source, options in list(conflicted.items())[:10]:
        print(f'    {source!r} -> {options}')
    print(f'  still to write: {len(fresh)}')
    if a.out:
        a.out.write_text(json.dumps(starter, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('  starter ->', a.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
