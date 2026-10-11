#!/usr/bin/env python3
"""List every per-glyph reveal in the story text and how its Korean reads.

Some scenes spell a word out one piece at a time -- だ・ け・ ど、 -- with each
piece its own literal so the script can pause between them. The story gate
keeps one Korean per Japanese source line, and the pieces are short enough to
recur: だ・ opens だけど, だから and だれかさん, イ・ sits in both アイスクリーム
and キタイ. Deciding a piece for the word in front of you silently decides it
for every other word that uses it; batch 033 had made イ・ into 하. for
기.대.하., which would have spelled the ice-cream vendor's 아.하.스...

So the reveals are planned together (batch 072 notes): a shared piece carries a
syllable only when every word it opens can start with it (だ・ = 그.), and
otherwise keeps only its pause mark (.), its syllable moved to an unshared
neighbour. An empty piece would be a cleaner silent beat, but TextPet cannot
compile an empty literal and the story gate refuses one. This survey finds the
reveals, marks the shared pieces, and prints
the Korean each reveal currently reads as, so a revision to any piece can be
checked against every word it belongs to.

A reveal is a run of two or more consecutive literals in one script whose
Japanese is one or two kana, optionally followed by ・ or 、. The run shows the
pieces only; a piece embedded at the end of a longer line (ア・ in
アマクテ~ / ツメタイ~ / ア・) is outside it.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from analyze_project import sha

p = Path(__file__).resolve().parents[1]
BATCH_DIR = p / 'translations/story_korean'
SOURCE = p / 'translations/story_source.jsonl'
BREAK = chr(10)
# kana letters and ー, but not ・ (U+30FB sits in the katakana block): runs of bare dots are pauses, not words
PIECE = re.compile(r'^[ぁ-ゖァ-ヺー]{1,2}[・、]?$')


def reveals(records: list[dict]) -> list[list[dict]]:
    by_script = defaultdict(list)
    for r in records:
        by_script[(r['archive'], r['script'])].append(r)
    runs = []
    for rs in by_script.values():
        rs.sort(key=lambda r: r['literal'])
        run: list[dict] = []
        for r in rs + [None]:
            if r is not None and PIECE.match(r['ja']) and (not run or r['literal'] == run[-1]['literal'] + 1):
                run.append(r)
                continue
            if len(run) >= 2:
                runs.append(run)
            run = [r] if r is not None and PIECE.match(r['ja']) else []
    return sorted(runs, key=lambda run: (run[0]['archive'], run[0]['script'], run[0]['literal']))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, default=p / 'analysis/story_glyph_reveals.json')
    a = ap.parse_args()

    records = [r for r in (json.loads(line) for line in SOURCE.read_text(encoding='utf-8').splitlines())
               if r['text_class'] == 'story']
    batches = sorted(BATCH_DIR.glob('*.json'))
    korean: dict[str, str] = {}
    for batch in batches:
        for entry in json.loads(batch.read_text(encoding='utf-8'))['entries']:
            korean[entry['id']] = entry['ko']

    runs = reveals(records)
    words = defaultdict(set)
    for run in runs:
        word = ''.join(r['ja'] for r in run)
        for r in run:
            words[r['ja']].add(word)
    shared = {piece: sorted(ws) for piece, ws in sorted(words.items()) if len(ws) > 1}

    rows = []
    for run in runs:
        first = run[0]
        pieces = [{'id': r['id'], 'ja': r['ja'], 'ko': korean.get(r['id'])} for r in run]
        decided = all(piece['ko'] is not None for piece in pieces)
        rows.append({
            'reveal': f"{first['archive']}/{first['script']}/{first['literal']}-{run[-1]['literal']}",
            'japanese': ''.join(r['ja'] for r in run),
            'korean': ''.join(piece['ko'] for piece in pieces) if decided else None,
            'shared_pieces': [r['ja'] for r in run if r['ja'] in shared],
            'pieces': pieces,
        })
    report = {
        'schema': 1,
        'scope': 'every run of two or more one-or-two-kana literals in one story script',
        'not_claimed': ['that a decided reading is good Korean; the rows are for review',
                        'pieces embedded at the end of a longer line'],
        'source_sha256': sha(SOURCE.read_bytes()),
        'batches': [{'path': b.relative_to(p).as_posix(), 'sha256': sha(b.read_bytes())} for b in batches],
        'shared_pieces': shared,
        'reveals': rows,
    }
    a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + BREAK, encoding='utf-8')
    for row in rows:
        reading = row['korean'] if row['korean'] is not None else 'pending'
        mark = ' shared=' + ','.join(row['shared_pieces']) if row['shared_pieces'] else ''
        print(f"{row['reveal']}: {row['japanese']} -> {reading}{mark}")
    pending = sum(row['korean'] is None for row in rows)
    print(f'{len(rows)} reveals, {len(shared)} shared pieces, {pending} not yet decided')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
