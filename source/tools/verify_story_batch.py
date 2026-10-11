#!/usr/bin/env python3
"""Recheck the story product from the ROM it produced, not from the build's notes.

The archive is pulled back out of the product, decompressed, re-extracted with
TextPet and compared literal by literal: every selected literal must hold the
batch wording, and every unselected literal must still hold the original
Japanese. A build that quietly dropped a string would pass a size check and
fail this one.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from analyze_project import PROFILES, sha, scripts
from verify_tpi_index import lz77_decompress
from build_story_batch import BASELINE, PRODUCT, GATE

p = Path(__file__).resolve().parents[1]
ESCAPED_BREAK = chr(92) + 'n'


def main() -> int:
    gate = json.loads(GATE.read_text(encoding='utf-8'))
    if gate['status'] != 'PASS':
        raise SystemExit('story gate is not PASS')
    batches = [json.loads((p / b['path']).read_text(encoding='utf-8')) for b in gate['batches']]
    exe = p / 'external/TextPet-v1.0.0/TextPet.exe'
    report = {'schema': 1, 'status': 'PASS static; runtime recorded separately',
              'scope': 'story batches re-read out of the product archive by archive',
              'not_claimed': ['the wording was seen on screen', 'the covered archives are drawn by the normal renderer'],
              'gate_sha256': sha(GATE.read_bytes()), 'profiles': {}}

    for key, meta in PROFILES.items():
        rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes()) == meta['sha256'])
        base = (p / 'poc/output' / (BASELINE.format(key=key) + '.gba')).read_bytes()
        product_path = p / 'poc/output' / (PRODUCT.format(key=key) + '.gba')
        data = product_path.read_bytes()
        m = json.loads(product_path.with_suffix('.json').read_text(encoding='utf-8'))
        if m['output_sha256'] != sha(data) or m['baseline_sha256'] != sha(base):
            raise SystemExit('product identity drift')

        wanted: dict[int, dict[tuple[int, int], str]] = {}
        for batch in batches:
            for entry in batch['entries']:
                if key not in entry['source_bindings']:
                    continue
                _, archive, _, number, _, literal = entry['id'].split('/')
                ko = entry.get('ko_red_sun', entry['ko']) if key == 'red_sun' and 'ko_red_sun' in entry else entry['ko']
                wanted.setdefault(int(archive), {})[(int(number), int(literal))] = ko

        pointer_offsets = {w['offset'] for w in m['expected_writes']
                           if w['writer'].startswith('story archive') and w['size'] == 4}
        allowed = [(at, at + 4) for at in pointer_offsets] + [(len(base), len(data))]
        differences = [i for i, (x, y) in enumerate(zip(base, data))
                       if x != y and not any(lo <= i < hi for lo, hi in allowed)]
        if differences:
            raise SystemExit(f'{len(differences)} unexplained differences from the baseline')

        analysis = json.loads((p / f'analysis/{key}_analysis.json').read_text(encoding='utf-8'))
        rows = {int(r['index']): r for r in analysis['archives_detail']}
        root = p / 'poc' / (key + '_story_verify')
        if root.exists():
            shutil.rmtree(root)
        binroot = root / 'bin'
        binroot.mkdir(parents=True)
        plugins = root / 'plugins'
        shutil.copytree(p / 'external/textpet-plugins', plugins, dirs_exist_ok=True)
        table = plugins / 'exe4-utf8.tbl'
        existing = table.read_text(encoding='utf-8-sig')
        syllables = sorted({c for entries in wanted.values() for ko in entries.values()
                            for c in ko if 0xAC00 <= ord(c) <= 0xD7A3})
        table.write_text(existing + '\n' + '\n'.join(
            'F9FC' + (ord(c) - 0xAC00).to_bytes(2, 'little').hex().upper() + '=' + c for c in syllables) + '\n',
            encoding='utf-8')

        checks = []
        for archive, entries in sorted(wanted.items()):
            row = rows[archive]
            name = f'{row["offset"]:06X}'
            # Every claim must point at the same relocated copy; one left behind
            # would still read the Japanese archive.
            landed = set()
            for ptr in row['pointers']:
                old = int.from_bytes(rom[ptr:ptr + 4], 'little')
                new = int.from_bytes(data[ptr:ptr + 4], 'little')
                if new & ~0x1FFFFFF != old & ~0x1FFFFFF:
                    raise SystemExit(f'archive {archive} claim at {ptr:#x} lost its original flag bits')
                landed.add(new & 0x1FFFFFF)
            if len(landed) != 1:
                raise SystemExit(f'archive {archive} claims disagree about where the archive is')
            at = landed.pop()
            if not len(base) <= at < len(data):
                raise SystemExit(f'archive {archive} pointer does not land in the appended region')
            # Read it back the way the source stored it, and refuse a product
            # that changed the storage form: a raw archive handed an LZ77 header
            # is garbage to its reader.
            entry = next(x for x in m['extension']['story']['layout'] if x['offset'] == at)
            if bool(entry['compressed']) != bool(row['compressed']):
                raise SystemExit(f'archive {archive} changed storage form')
            if row['compressed']:
                payload, consumed = lz77_decompress(data, at)
            else:
                consumed = entry['size']
                payload = data[at:at + consumed]
            if sha(payload) != entry['payload_sha256']:
                raise SystemExit(f'archive {archive} payload does not match what the build recorded')
            jumps = 0
            if 'full_copy_offset' in entry:
                # A capped archive: the decoded copy must fit its slot, and every
                # script it does not hold must jump to that script in the ROM copy.
                from text_slots import check_stub
                fo = entry['full_copy_offset']
                fe = next(x for x in m['extension']['story']['layout'] if x['offset'] == fo)
                full = data[fo:fo + fe['size']]
                if sha(full) != entry['full_payload_sha256'] or len(payload) > entry['slot_cap']:
                    raise SystemExit(f'archive {archive} ROM copy or slot size does not match the build')
                try:
                    jumps = check_stub(payload, full, 0x08000000 + fo)
                except ValueError as error:
                    raise SystemExit(f'archive {archive}: {error}')
                payload = full
            (binroot / f'{name}.msg').write_bytes(payload)
            # An inherited archive (one an earlier stage already moved) is
            # compared against that stage's copy, read here from the baseline
            # ROM itself, so its earlier translations count as the source.
            if entry.get('inherited_from'):
                bm = json.loads((p / 'poc/output' / (BASELINE.format(key=key) + '.json')).read_text(encoding='utf-8'))
                held = next(x for x in bm['extension']['layout'] if x['name'] == entry['inherited_from'])
                (root / 'inherited_bin').mkdir(exist_ok=True)
                blob = base[held['offset']:held['offset'] + held['size']]
                if row['compressed']:
                    blob, used = lz77_decompress(base, held['offset'])
                    if used != held['size']:
                        raise SystemExit('inherited compressed archive does not decompress to its layout size')
                (root / 'inherited_bin' / f'{name}.msg').write_bytes(bytes(blob))
            checks.append({'archive': archive, 'name': name, 'pointer_offsets': list(row['pointers']),
                           'pointer_claims': len(row['pointers']), 'relocated_to': at,
                           'stored_compressed': bool(row['compressed']),
                           'stored_bytes': consumed, 'payload_bytes': len(payload),
                           'payload_sha256': sha(payload), 'rom_jump_scripts': jumps})
        out = root / 'tpl'
        out.mkdir()
        run = subprocess.run([str(exe), 'load-plugins', str(plugins), 'game', 'exe4',
                              'read-text-archives', str(binroot), '-f', 'bin',
                              'write-text-archives', str(out) + '/', '-f', 'tpl'], capture_output=True)
        (root / 'reextract.log').write_bytes(run.stdout + run.stderr)
        if run.returncode:
            raise SystemExit('re-extraction of the product archive failed; see ' + str(root / 'reextract.log'))

        if (root / 'inherited_bin').exists():
            run = subprocess.run([str(exe), 'load-plugins', str(plugins), 'game', 'exe4',
                                  'read-text-archives', str(root / 'inherited_bin'), '-f', 'bin',
                                  'write-text-archives', str(root / 'inherited_tpl') + '/', '-f', 'tpl'],
                                 capture_output=True)
            if run.returncode:
                raise SystemExit('re-extraction of an inherited baseline archive failed')
        for check in checks:
            archive = check['archive']
            origin = root / 'inherited_tpl' / f'{check["name"]}.tpl'
            if not origin.exists():
                origin = p / f'analysis/{key}_tpl/{check["name"]}.tpl'
            source = {(n, k): v for n, _, values, _ in scripts(origin.read_text(encoding='utf-8-sig'))
                      for k, v in enumerate(values)}
            got = {(n, k): v for n, _, values, _ in
                   scripts((out / f'{check["name"]}.tpl').read_text(encoding='utf-8-sig'))
                   for k, v in enumerate(values)}
            if set(got) != set(source):
                raise SystemExit(f'archive {archive} lost or gained literals')
            translated = 0
            for place, value in source.items():
                expected = wanted[archive].get(place)
                actual = got[place].replace(ESCAPED_BREAK, '\n')
                if expected is None:
                    if actual != value.replace(ESCAPED_BREAK, '\n'):
                        raise SystemExit(f'archive {archive} changed an unselected literal at {place}')
                else:
                    if actual != expected:
                        raise SystemExit(f'archive {archive} does not hold the batch wording at {place}')
                    translated += 1
            check['literals'] = len(source)
            check['translated_literals'] = translated
            check['unselected_literals_preserved'] = len(source) - translated
            if translated != len(wanted[archive]):
                raise SystemExit(f'archive {archive} translated {translated} of {len(wanted[archive])} selected literals')

        font = m['extension']['layout'][0]
        advance = m['extension']['layout'][1]
        for item in (font, advance):
            if sha(data[item['offset']:item['offset'] + item['size']]) != item['sha256']:
                raise SystemExit('the Hangul font or advance region moved')
        report['profiles'][key] = {
            'rom_sha256': m['output_sha256'], 'baseline_sha256': m['baseline_sha256'],
            'source_sha256': meta['sha256'], 'grew_bytes': len(data) - len(base),
            'pointer_words_changed': len(pointer_offsets), 'no_executable_changes': True,
            'font_and_advance_unchanged': True, 'checks': checks,
            'selected_literals': sum(c['translated_literals'] for c in checks),
            'unselected_literals_preserved': sum(c['unselected_literals_preserved'] for c in checks),
        }
    report['tool_sha256'] = sha(Path(__file__).read_bytes())
    (p / 'analysis/story_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                        encoding='utf-8')
    for key, item in report['profiles'].items():
        print(key, 'PASS', item['selected_literals'], 'translated,',
              item['unselected_literals_preserved'], 'unselected preserved,',
              item['pointer_words_changed'], 'pointer words, grew', item['grew_bytes'], 'bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
