#!/usr/bin/env python3
"""Look a line up in the extraction sheet.

Matching a screenshot to an archive is the everyday question of this phase:
you can read the Japanese off the screen, but not which archive drew it. This
prints every id whose source contains the given text, with its archive, so a
route capture turns into a batch target.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

p = Path(__file__).resolve().parents[1]
SHEET = p / 'translations/story_source.jsonl'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('text', help='substring of the Japanese source line')
    ap.add_argument('--limit', type=int, default=20)
    a = ap.parse_args()
    hits = []
    for line in SHEET.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        if a.text in record['ja']:
            hits.append(record)
    archives = Counter(r['archive'] for r in hits)
    print(f'{len(hits)} matching ids in {len(archives)} archives: {archives.most_common(10)}')
    for record in hits[:a.limit]:
        print(f"  {record['id']}  [{record['text_class']}/{record['revision']}]  {record['ja']!r}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
