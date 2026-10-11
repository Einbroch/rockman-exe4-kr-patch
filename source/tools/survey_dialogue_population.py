#!/usr/bin/env python3
"""Size and identify the story-text population before any of it is translated.

Every literal gets a stable id of the form archive/<index>/script/<n>/literal/<k>
so a translation asset can name a string without depending on file order, and
so the same id means the same string in both revisions wherever the payloads
agree.

Three things this survey deliberately does not do:

  * It does not adopt anything.  The consumer contract stays default-deny; an
    archive counted here as a dialogue candidate is a candidate because nothing
    has classified it yet, not because the normal renderer was observed drawing
    it.
  * It does not claim the indexed population is all the text.  The archive
    index is a lower bound; strings the index does not reach are still text.
  * It does not deduplicate the workload by itself.  Identical Japanese lines
    are reported so a translator can reuse a decision, but two ids that share a
    source line can still need different Korean.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from analyze_project import PROFILES, sha, scripts

p = Path(__file__).resolve().parents[1]
# The whole modern Hangul syllable block, which is exactly what the normal
# dialogue extension supplies, so the story path has no glyph budget to spend.
HANGUL_BLOCK = 0xD7A3 - 0xAC00 + 1


def japanese(text: str) -> int:
    return sum(1 for ch in text
               if 0x3040 <= ord(ch) <= 0x30FF or 0x4E00 <= ord(ch) <= 0x9FFF or 0xFF66 <= ord(ch) <= 0xFF9D)


def contracted_archives() -> dict[int, str]:
    """Archives a named contract already owns, so the story pass must not touch
    them without going through that contract."""
    owned: dict[int, str] = {}
    contract = json.loads((p / 'tools/specs/exe4_consumer_contracts_v1.json').read_text(encoding='utf-8'))
    for entry in contract['supported_entries']:
        owned.setdefault(int(entry['id'].split('/')[1]), 'adopted short-script menu contract')
    owned[41] = 'folder/library/battle chip names, BG tilemap parser'
    owned[42] = 'folder/library/battle chip names, BG tilemap parser'
    owned[54] = 'chip descriptions, four pointer claims'
    owned[55] = 'chip descriptions, second table'
    owned[418] = 'NAME input options, packed three-byte indexes'
    owned[442] = 'opening; already translated and runtime-verified'
    return owned


report = {
    'schema': 1,
    'status': 'PASS inventory only; nothing adopted, nothing translated',
    'scope': 'indexed archive population of both revisions, per-literal stable ids, and the story-text workload that remains',
    'hangul_supply': {'normal_dialogue_glyphs': 11172, 'modern_syllable_block': HANGUL_BLOCK,
                      'covers_whole_block': 11172 == HANGUL_BLOCK,
                      'note': 'the F9FC extension supplies every modern syllable, so the story path has no glyph budget'},
    'not_claimed': [
        'dialogue candidates were observed in the normal renderer',
        'the indexed archives are all the text in the ROM',
        'identical Japanese lines may share one Korean line',
    ],
    'profiles': {},
}

owned = contracted_archives()
per_profile_texts = {}

for key, meta in PROFILES.items():
    analysis = json.loads((p / f'analysis/{key}_analysis.json').read_text(encoding='utf-8'))
    if analysis['source']['sha256'] != meta['sha256']:
        raise ValueError('archive analysis is not the pinned source revision')
    by_offset = {int(row['offset']): row for row in analysis['archives_detail']}
    tpl_dir = p / f'analysis/{key}_tpl'
    files = sorted(tpl_dir.glob('*.tpl'))
    if len(files) != analysis['archives']:
        raise ValueError('extracted TPL count does not match the indexed archive count')
    archives = []
    texts: dict[str, str] = {}
    for f in files:
        offset = int(f.stem, 16)
        row = by_offset.get(offset)
        if row is None:
            raise ValueError('extracted archive is not in the index: ' + f.name)
        index = int(row['index'])
        text = f.read_text(encoding='utf-8')
        languages = Counter()
        literals = 0
        jp = 0
        for number, language, values, _ in scripts(text):
            languages[language] += 1
            for k, value in enumerate(values):
                count = japanese(value)
                literals += 1
                jp += count
                if count:
                    texts[f'archive/{index:03d}/script/{number}/literal/{k}'] = value
        archives.append({
            'index': index, 'offset': offset, 'file': f.name, 'compressed': row['compressed'],
            'pointer_claims': len(row['pointers']), 'scripts': sum(languages.values()),
            'languages': dict(languages), 'literals': literals, 'japanese_characters': jp,
            'owner': owned.get(index), 'story_candidate': index not in owned and jp > 0,
        })
    per_profile_texts[key] = texts
    candidates = [a for a in archives if a['story_candidate']]
    report['profiles'][key] = {
        'source_sha256': meta['sha256'],
        'tpl_dir': tpl_dir.relative_to(p).as_posix(),
        'tpl_dir_sha256': sha(b''.join(sha(f.read_bytes()).encode() for f in files)),
        'archives': len(archives),
        'owned_archives': sorted(owned),
        'story_candidate_archives': len(candidates),
        'story_candidate_literals': sum(a['literals'] for a in candidates),
        'story_candidate_japanese_characters': sum(a['japanese_characters'] for a in candidates),
        'translatable_ids': len(texts),
        'largest_story_archives': [
            {k: a[k] for k in ('index', 'file', 'scripts', 'literals', 'japanese_characters')}
            for a in sorted(candidates, key=lambda a: -a['japanese_characters'])[:20]],
        'archive_detail': archives,
    }

blue, red = per_profile_texts['blue_moon'], per_profile_texts['red_sun']
shared = {i for i in blue if i in red and blue[i] == red[i]}
lines = Counter(blue[i] for i in blue)
report['cross_revision'] = {
    'ids_in_both_with_identical_source': len(shared),
    'ids_only_in_blue_moon': len(set(blue) - set(red)),
    'ids_only_in_red_sun': len(set(red) - set(blue)),
    'ids_present_in_both_but_differing': len([i for i in blue if i in red and blue[i] != red[i]]),
    'note': 'an id whose source line is identical in both revisions can carry one Korean line; the rest need per-revision wording',
}
report['deduplication'] = {
    'blue_moon_ids_with_japanese': len(blue),
    'distinct_japanese_lines': len(lines),
    'ids_per_distinct_line': round(len(blue) / len(lines), 3) if lines else 0,
    'most_repeated': [{'occurrences': n, 'line': line} for line, n in lines.most_common(10)],
}
report['tool_sha256'] = sha(Path(__file__).read_bytes())
(p / 'analysis/dialogue_population.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

for key, item in report['profiles'].items():
    print(f"{key}: {item['story_candidate_archives']} story-candidate archives, "
          f"{item['story_candidate_literals']} literals, "
          f"{item['story_candidate_japanese_characters']} Japanese characters, "
          f"{item['translatable_ids']} ids carrying Japanese")
print('cross-revision identical ids:', report['cross_revision']['ids_in_both_with_identical_source'],
      '| distinct Japanese lines:', report['deduplication']['distinct_japanese_lines'])
