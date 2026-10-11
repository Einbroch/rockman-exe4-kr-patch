#!/usr/bin/env python3
"""Re-derive every ROM word that names the chip-description archive and ask, for
each one, which instruction could load it.

Three of the four words are already classified consumers.  This survey exists
for the fourth, which the description contract deliberately leaves pointing at
the original archive.  A static sweep can only say "no addressing form I know
reaches this word"; it cannot say the word is never read.  So the sweep carries
its own positive controls: the two classified direct references must each be
reached by exactly one PC-relative load, and the two routines already observed
at runtime must each be reached by at least one BL.  If a control fails the
method is broken and the survey refuses to record its negative result.
"""
from __future__ import annotations

import json
from pathlib import Path

from analyze_project import PROFILES, sha

p = Path(__file__).resolve().parents[1]
ROM_BASE = 0x08000000
# Contract-fixed reference offsets, per tools/specs/exe4_menu_descriptions_v2.json
# and tools/specs/exe4_description_v1.json.
CLASSIFIED = {
    'blue_moon': {'battle': 0x01FCE4, 'folder': 0x106AC4, 'library': 0x1098A8},
    'red_sun': {'battle': 0x01FD20, 'folder': 0x106B34, 'library': 0x109918},
}
UNCLASSIFIED = {'blue_moon': 0x106DAC, 'red_sun': 0x106E1C}
# Routines whose runtime hits are already recorded in exe4_menu_descriptions_v2.json.
OBSERVED_ROUTINES = {'blue_moon': [0x106A54, 0x10987C], 'red_sun': [0x106AC4, 0x1098EC]}
TWINS = {'blue_moon': [0x106A9C, 0x106D84], 'red_sun': [0x106B0C, 0x106DF4]}


def thumb_literal_loaders(rom: bytes, literal: int) -> list[dict]:
    """LDR Rd,[PC,#imm8*4] can only reach 1020 bytes forward, so the loader of a
    literal is always just behind it."""
    out = []
    for at in range(max(0, literal - 1024), literal, 2):
        half = int.from_bytes(rom[at:at + 2], 'little')
        if 0x4800 <= half < 0x5000 and (((at + 4) & ~3) + (half & 0xFF) * 4) == literal:
            out.append({'at': at, 'register': (half >> 8) & 7, 'form': 'thumb ldr literal'})
    return out


def arm_literal_loaders(rom: bytes, literal: int) -> list[dict]:
    out = []
    for at in range(max(0, literal - 4096), min(len(rom) - 3, literal + 4096), 4):
        word = int.from_bytes(rom[at:at + 4], 'little')
        if (word & 0x0F7F0000) not in (0x051F0000, 0x059F0000):
            continue
        imm = word & 0xFFF
        target = at + 8 + (imm if (word >> 23) & 1 else -imm)
        if target == literal:
            out.append({'at': at, 'register': (word >> 12) & 15, 'form': 'arm ldr literal'})
    return out


def thumb_adr(rom: bytes, literal: int) -> list[dict]:
    out = []
    for at in range(max(0, literal - 1024), literal, 2):
        half = int.from_bytes(rom[at:at + 2], 'little')
        if 0xA000 <= half < 0xA800 and (((at + 4) & ~3) + (half & 0xFF) * 4) == literal:
            out.append({'at': at, 'register': (half >> 8) & 7, 'form': 'thumb adr'})
    return out


def word_references(rom: bytes, address: int) -> list[int]:
    needle = address.to_bytes(4, 'little')
    return [i for i in range(0, len(rom) - 3, 4) if rom[i:i + 4] == needle]


def bl_targets(rom: bytes) -> dict[int, list[int]]:
    found: dict[int, list[int]] = {}
    for at in range(0, len(rom) - 4, 2):
        high = int.from_bytes(rom[at:at + 2], 'little')
        if (high & 0xF800) != 0xF000:
            continue
        low = int.from_bytes(rom[at + 2:at + 4], 'little')
        if (low & 0xF800) != 0xF800:
            continue
        offset = ((high & 0x7FF) << 12) | ((low & 0x7FF) << 1)
        if offset & 0x400000:
            offset -= 0x800000
        found.setdefault(ROM_BASE + at + 4 + offset, []).append(at)
    return found


report = {
    'schema': 1,
    'status': 'PASS static sweep with positive controls; fourth reference left unclassified',
    'scope': 'aligned ROM words naming the chip-description archive, and the addressing forms that could load them',
    'not_claimed': [
        'the fourth word is never read at runtime',
        'the routine ahead of it is dead code',
        'the addressing forms swept here are every form the ROM uses',
    ],
    'method': 'thumb ldr literal, arm ldr literal, thumb adr, aligned word pointing at the reference, and BL callers',
    'profiles': {},
}

for key, meta in PROFILES.items():
    rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes()) == meta['sha256'])
    archive = int.from_bytes(rom[CLASSIFIED[key]['folder']:CLASSIFIED[key]['folder'] + 4], 'little')
    census = word_references(rom, archive)
    if sorted(census) != sorted(list(CLASSIFIED[key].values()) + [UNCLASSIFIED[key]]):
        raise ValueError('archive reference census no longer matches the pinned contract offsets')
    calls = bl_targets(rom)
    controls = []
    for name in ('folder', 'library'):
        at = CLASSIFIED[key][name]
        loaders = thumb_literal_loaders(rom, at)
        if len(loaders) != 1:
            raise ValueError('positive control lost: classified direct reference has no single loader')
        controls.append({'control': name + ' direct load', 'literal': at, 'loaders': loaders})
    for routine in OBSERVED_ROUTINES[key]:
        callers = calls.get(ROM_BASE + routine, [])
        if not callers:
            raise ValueError('positive control lost: observed routine has no BL caller')
        controls.append({'control': 'observed routine BL', 'routine': routine, 'callers': callers})
    references = {}
    for name, at in list(CLASSIFIED[key].items()) + [('unclassified', UNCLASSIFIED[key])]:
        references[name] = {
            'offset': at,
            'value': int.from_bytes(rom[at:at + 4], 'little'),
            'thumb_literal_loaders': thumb_literal_loaders(rom, at),
            'arm_literal_loaders': arm_literal_loaders(rom, at),
            'thumb_adr': thumb_adr(rom, at),
            'words_pointing_here': word_references(rom, ROM_BASE + at),
        }
    unread = UNCLASSIFIED[key]
    pool = [{'offset': unread + i * 4, 'value': int.from_bytes(rom[unread + i * 4:unread + i * 4 + 4], 'little'),
             'thumb_literal_loaders': thumb_literal_loaders(rom, unread + i * 4)} for i in range(6)]
    folder_pool = [int.from_bytes(rom[CLASSIFIED[key]['folder'] + i * 4:CLASSIFIED[key]['folder'] + i * 4 + 4], 'little')
                   for i in range(5)]
    twin_a, twin_b = TWINS[key]
    report['profiles'][key] = {
        'source_sha256': meta['sha256'],
        'archive_address': archive,
        'positive_controls': controls,
        'references': references,
        'unclassified_pool': pool,
        'folder_pool_words': folder_pool,
        'pool_shape_matches_folder': [x['value'] for x in pool[:5]][:3] == folder_pool[:3]
                                      and pool[4]['value'] == folder_pool[4],
        'pool_font_word_differs': pool[3]['value'] != folder_pool[3],
        'twin_routines': {
            'folder_side': {'at': twin_a, 'bl_callers': calls.get(ROM_BASE + twin_a, [])},
            'unclassified_side': {'at': twin_b, 'bl_callers': calls.get(ROM_BASE + twin_b, [])},
            'bytes_identical_except': [i for i, (x, y) in enumerate(zip(rom[twin_a:twin_a + 40], rom[twin_b:twin_b + 40])) if x != y],
        },
    }

report['tool_sha256'] = sha(Path(__file__).read_bytes())
(p / 'analysis/fourth_description_reference_survey.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
for key, item in report['profiles'].items():
    unread = [x['offset'] for x in item['unclassified_pool'][:5] if not x['thumb_literal_loaders']]
    print(key, 'unclassified pool words with no loader:', len(unread), 'of 5;',
          'twin BL callers:', len(item['twin_routines']['unclassified_side']['bl_callers']))
