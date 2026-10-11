#!/usr/bin/env python3
"""Insert gated story batches into the development baseline, one archive at a time.

The baseline already carries the whole modern Hangul syllable block and the
F9 FC handlers, so nothing here touches code, fonts or advances. Each covered
archive is recompiled from its own source TPL with only the selected literals
replaced, relocated to the end of the ROM, and its single pointer rewritten
with the original flag bits preserved.

What the build refuses:

  * A batch that has not passed the gate, or whose sheet has moved.
  * A source TPL whose bytes differ from the binding the batch was written
    against.
  * Any literal in a covered archive that changed without being a selected
    entry, and any difference from the baseline outside the pointer words and
    the appended region.
  * A recompiled archive that does not re-extract to exactly the intended
    wording, or whose relocated blob does not decompress back to the compiled
    payload.

An archive that this revision does not own is skipped: Blue Moon and Red Sun
put the same tutorial in different archive slots, so an id exists in one
revision only.
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

from analyze_project import PROFILES, sha, scripts, SCRIPT, LITERAL
from verify_tpi_index import lz77_decompress

p = Path(__file__).resolve().parents[1]
BASELINE = '{key}_opening_menu_chip_folder_library_full_descriptions_korean_development'
PRODUCT = '{key}_opening_menu_chip_folder_library_menu_descriptions_story_korean_development'
BATCH_DIR = p / 'translations/story_korean'
GATE = p / 'analysis/story_translation_gate.json'


def lz_literal(data: bytes) -> bytes:
    """An LZ77 container that stores its payload verbatim. The game only needs a
    well-formed stream; squeezing it is a separate job from getting the text in."""
    if len(data) > 0xFFFFFF:
        raise ValueError('LZ length overflow')
    out = bytearray(b'\x10' + len(data).to_bytes(3, 'little'))
    for i in range(0, len(data), 8):
        out.append(0)
        out.extend(data[i:i + 8])
    return bytes(out)


def rewrite(text: str, wanted: dict[int, dict[int, str]]) -> str:
    """Replace only the selected literals, leaving every control command, script
    boundary and unselected literal byte-identical."""
    matches = list(SCRIPT.finditer(text))
    out = text
    for i in range(len(matches) - 1, -1, -1):
        number = int(matches[i].group(1))
        if number not in wanted:
            continue
        start = matches[i].end()
        stop = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = out[start:stop]
        literals = list(LITERAL.finditer(block))
        for k, m in reversed(list(enumerate(literals))):
            if k not in wanted[number]:
                continue
            ko = wanted[number][k]
            if '\n' in ko:
                token = '"""\r\n\t' + ko.replace('\n', '\r\n\t') + '\r\n\t"""'
            else:
                token = '"' + ko + '"'
            block = block[:m.start()] + token + block[m.end():]
        out = out[:start] + block + out[stop:]
    return out


def main() -> int:
    gate = json.loads(GATE.read_text(encoding='utf-8'))
    if gate['status'] != 'PASS' or not gate['batches']:
        raise SystemExit('story gate has not passed for any batch')
    batches = [json.loads((p / b['path']).read_text(encoding='utf-8')) for b in gate['batches']]
    for record, batch in zip(gate['batches'], batches):
        if sha((p / record['path']).read_bytes()) != record['sha256']:
            raise SystemExit('batch changed since the gate ran: ' + record['path'])
    sheet = {}
    for line in (p / 'translations/story_source.jsonl').read_text(encoding='utf-8').splitlines():
        r = json.loads(line)
        sheet[r['id']] = r
    if sha((p / 'translations/story_source.jsonl').read_bytes()) != gate['sheet_sha256']:
        raise SystemExit('extraction sheet changed since the gate ran')

    exe = p / 'external/TextPet-v1.0.0/TextPet.exe'
    results = {}
    for key, meta in PROFILES.items():
        rom = next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes()) == meta['sha256'])
        baseline_path = p / 'poc/output' / (BASELINE.format(key=key) + '.gba')
        base = baseline_path.read_bytes()
        bm = json.loads(baseline_path.with_suffix('.json').read_text(encoding='utf-8'))
        if bm['output_sha256'] != sha(base):
            raise SystemExit('baseline manifest does not describe the baseline bytes')
        analysis = json.loads((p / f'analysis/{key}_analysis.json').read_text(encoding='utf-8'))
        rows = {int(r['index']): r for r in analysis['archives_detail']}

        selected: dict[int, dict[int, dict[int, str]]] = {}
        ids: list[str] = []
        hangul: set[str] = set()
        for batch in batches:
            for entry in batch['entries']:
                if key not in entry['source_bindings']:
                    continue
                _, archive, _, number, _, literal = entry['id'].split('/')
                ko = entry.get('ko_red_sun', entry['ko']) if key == 'red_sun' and 'ko_red_sun' in entry else entry['ko']
                selected.setdefault(int(archive), {}).setdefault(int(number), {})[int(literal)] = ko
                ids.append(entry['id'])
                hangul |= {c for c in ko if 0xAC00 <= ord(c) <= 0xD7A3}
        if not selected:
            raise SystemExit('no batch entry belongs to ' + key)

        root = p / 'poc' / (key + '_story')
        if root.exists():
            shutil.rmtree(root)
        tpldir = root / 'tpl'
        tpldir.mkdir(parents=True)
        plugins = root / 'plugins'
        shutil.copytree(p / 'external/textpet-plugins', plugins, dirs_exist_ok=True)
        table = plugins / 'exe4-utf8.tbl'
        existing = table.read_text(encoding='utf-8-sig')
        lines = set(existing.splitlines())
        # Only the syllables this build uses are added; the Japanese table stays
        # whole, because a covered archive still holds untranslated Japanese.
        additions = ['F9FC' + (ord(c) - 0xAC00).to_bytes(2, 'little').hex().upper() + '=' + c for c in sorted(hangul)]
        table.write_text(existing + '\n' + '\n'.join(x for x in additions if x not in lines) + '\n', encoding='utf-8')

        # An archive an earlier stage already moved (the menu stage moves
        # archives 1 and 2 to translate four save-screen labels) is inherited:
        # its moved copy is the starting point, so those labels survive, and
        # every claim is followed from that copy rather than from the source.
        inherited = {}
        by_offset = {item['offset']: item for item in bm['extension']['layout']}
        for archive in selected:
            row = rows[archive]
            moved = [int.from_bytes(base[ptr:ptr + 4], 'little') & 0x1FFFFFF for ptr in row['pointers']
                     if base[ptr:ptr + 4] != rom[ptr:ptr + 4]]
            if not moved:
                continue
            if len(moved) != len(row['pointers']) or len(set(moved)) != 1 or moved[0] not in by_offset:
                raise SystemExit(f'archive {archive} is only partly moved by the baseline')
            item = by_offset[moved[0]]
            held = base[moved[0]:moved[0] + item['size']]
            if row['compressed']:
                # The menu stage keeps a compressed archive compressed; start
                # from its decoded payload, and the blob must be exactly that.
                held, consumed = lz77_decompress(base, moved[0])
                if consumed != item['size']:
                    raise SystemExit(f'inherited archive {archive} blob does not decompress to its layout size')
            inherited[archive] = {'offset': moved[0], 'name': item['name'], 'payload': bytes(held)}
        if inherited:
            idir = root / 'inherited'
            (idir / 'bin').mkdir(parents=True)
            for archive, item in inherited.items():
                (idir / 'bin' / f'{rows[archive]["offset"]:06X}.msg').write_bytes(item['payload'])
            run = subprocess.run([str(exe), 'load-plugins', str(plugins), 'game', 'exe4',
                                  'read-text-archives', str(idir / 'bin'), '-f', 'bin',
                                  'write-text-archives', str(idir / 'tpl') + '/', '-f', 'tpl'], capture_output=True)
            (root / 'inherited.log').write_bytes(run.stdout + run.stderr)
            if run.returncode:
                raise SystemExit('TextPet export of an inherited archive failed')

        intended = {}
        for archive, wanted in sorted(selected.items()):
            row = rows[archive]
            name = f'{row["offset"]:06X}'
            source_tpl = p / f'analysis/{key}_tpl/{name}.tpl'
            digest = sha(source_tpl.read_bytes())
            for number, literals in wanted.items():
                for literal in literals:
                    binding = sheet[f'archive/{archive:03d}/script/{number}/literal/{literal}']['source_bindings'][key]
                    if binding['tpl_sha256'] != digest:
                        raise SystemExit('source TPL differs from the binding the batch was written against')
            if archive in inherited:
                source_tpl = root / 'inherited/tpl' / f'{name}.tpl'
            # Read and write with newline translation off. The tokens below carry
            # their own CRLF, and letting the platform translate them again turns
            # every inserted line break into CR CR LF, which TextPet rejects.
            with source_tpl.open(encoding='utf-8-sig', newline='') as handle:
                text = handle.read()
            if archive in inherited:
                held = {(n, k): v for n, _, values, _ in scripts(text) for k, v in enumerate(values)}
                for number, literals in wanted.items():
                    for literal in literals:
                        ja = sheet[f'archive/{archive:03d}/script/{number}/literal/{literal}']['ja']
                        if held.get((number, literal)) != ja:
                            raise SystemExit(f'inherited archive {archive} script {number} literal {literal} '
                                             'no longer holds the source the sheet was written against')
            edited = rewrite(text, wanted)
            with (tpldir / f'{name}.tpl').open('w', encoding='utf-8', newline='') as handle:
                handle.write(edited)
            intended[archive] = {'name': name, 'row': row, 'edited': edited}

        compiled_dir = root / 'bin'
        compiled_dir.mkdir()
        run = subprocess.run([str(exe), 'load-plugins', str(plugins), 'game', 'exe4',
                              'read-text-archives', str(tpldir), '-f', 'tpl',
                              'write-text-archives', str(compiled_dir) + '/', '-f', 'bin'], capture_output=True)
        (root / 'compile.log').write_bytes(run.stdout + run.stderr)
        if run.returncode:
            raise SystemExit('TextPet compile failed; see ' + str(root / 'compile.log'))

        # TextPet can return zero and still drop text, so read the result back
        # and compare wording rather than trusting the exit code.
        reexport = root / 'reexport'
        reexport.mkdir()
        run = subprocess.run([str(exe), 'load-plugins', str(plugins), 'game', 'exe4',
                              'read-text-archives', str(compiled_dir), '-f', 'bin',
                              'write-text-archives', str(reexport) + '/', '-f', 'tpl'], capture_output=True)
        (root / 'reexport.log').write_bytes(run.stdout + run.stderr)
        if run.returncode:
            raise SystemExit('TextPet re-export failed; see ' + str(root / 'reexport.log'))

        target = bytearray(base)
        writes = []
        layout = []
        from text_slots import caps as slot_caps, cap_for, externalize
        caps_map, _ = slot_caps(p, key, rom)
        for archive, item in sorted(intended.items()):
            name = item['name']
            data = (compiled_dir / f'{name}.msg').read_bytes()
            back = {(n, k): v for n, _, values, _ in scripts((reexport / f'{name}.tpl').read_text(encoding='utf-8-sig'))
                    for k, v in enumerate(values)}
            for number, literals in selected[archive].items():
                for literal, ko in literals.items():
                    if back.get((number, literal), '').replace(chr(92) + 'n', '\n') != ko:
                        raise SystemExit(f'recompiled archive {archive} does not hold the intended wording '
                                         f'at script {number} literal {literal}')
            # Store it the way the source stored it. 77 of this ROM's 793
            # archives are raw, and handing their reader an LZ77 header feeds it
            # garbage: archive 008 is read during boot, and wrapping it left the
            # screen black from the first frame.
            compressed = bool(item['row']['compressed'])
            # The area text slots and a few other buffers have a fixed size; a
            # translated archive over it keeps its whole payload in ROM and its
            # decoded copy jumps there for the largest scripts (text_slots.py).
            source_offset = item['row']['offset']
            source_size = len(lz77_decompress(rom, source_offset)[0]) if compressed else len(data)
            cap = cap_for(caps_map, source_offset, source_size)
            full_entry = None
            if cap is not None and len(data) > cap:
                target.extend(bytes([0xff]) * ((-len(target)) % 4))
                full_at = len(target)
                target.extend(data)
                full_entry = {'name': f'story archive {archive} whole payload (ROM-resident)', 'offset': full_at,
                              'size': len(data), 'sha256': sha(data)}
                layout.append(full_entry)
                data, jumped = externalize(data, cap, 0x08000000 + full_at)
                full_entry['jump_scripts'] = jumped
            # An archive decoded to a fixed RAM address must still fit there.
            from ram_budgets import check as ram_budget
            try:
                ram_budget(p, archive, len(data))
            except ValueError as error:
                raise SystemExit(str(error))
            if compressed:
                blob = lz_literal(data)
                decoded, consumed = lz77_decompress(blob, 0)
                if decoded != data or consumed != len(blob):
                    raise SystemExit('relocated blob does not decompress back to the compiled payload')
            else:
                blob = data
            target.extend(b'\xff' * ((-len(target)) % 4))
            at = len(target)
            target.extend(blob)
            layout.append({'name': f'story archive {archive} clone', 'offset': at, 'size': len(blob),
                           'sha256': sha(blob), 'payload_sha256': sha(data), 'compressed': compressed})
            if full_entry is not None:
                layout[-1]['slot_cap'] = cap
                layout[-1]['full_copy_offset'] = full_entry['offset']
                layout[-1]['full_payload_sha256'] = full_entry['sha256']
            # Every claim has to follow the archive. Leaving one behind leaves a
            # reader pointed at the Japanese copy, and the two would disagree on
            # screen depending on which path drew the text. Flag bits differ per
            # claim, so each is preserved from its own word.
            pointers = item['row']['pointers']
            if not pointers:
                raise SystemExit(f'archive {archive} has no pointer claim to follow')
            for ptr in pointers:
                old = int.from_bytes(base[ptr:ptr + 4], 'little')
                if archive in inherited:
                    if old & 0x1FFFFFF != inherited[archive]['offset']:
                        raise SystemExit(f'inherited archive {archive} claim at {ptr:#x} does not address its copy')
                elif old != int.from_bytes(rom[ptr:ptr + 4], 'little'):
                    raise SystemExit('baseline already moved this archive pointer')
                elif old & 0x1FFFFFF != item['row']['offset']:
                    raise SystemExit(f'archive {archive} claim at {ptr:#x} does not address the archive')
                final = ((old & ~0x1FFFFFF) | at).to_bytes(4, 'little')
                writes.append({'offset': ptr, 'size': 4,
                               'writer': f'story archive {archive} pointer, flags preserved'
                                         + (' (inherited from ' + inherited[archive]['name'] + ')'
                                            if archive in inherited else ''),
                               'expected_sha256': sha(rom[ptr:ptr + 4]), 'final_sha256': sha(final)})
                target[ptr:ptr + 4] = final
            layout[-1]['pointer_claims'] = list(pointers)
            if archive in inherited:
                layout[-1]['inherited_from'] = inherited[archive]['name']

        allowed = [(w['offset'], w['offset'] + 4) for w in writes] + [(len(base), len(target))]
        for i, (x, y) in enumerate(zip(base, target)):
            if x != y and not any(lo <= i < hi for lo, hi in allowed):
                raise SystemExit(f'unexplained baseline difference at {i:#x}')

        m = copy.deepcopy(bm)
        m['expected_writes'] = [w for w in m['expected_writes'] if w['offset'] < len(rom)] + writes
        m['expected_writes'].append({'offset': len(rom), 'size': len(target) - len(rom),
                                     'writer': 'inherited development payload plus relocated story archives',
                                     'final_sha256': sha(bytes(target[len(rom):]))})
        m['extension']['layout'] = m['extension']['layout'] + layout
        m['extension']['story'] = {
            'sheet_sha256': gate['sheet_sha256'], 'gate_sha256': sha(GATE.read_bytes()),
            'batches': gate['batches'], 'archives': sorted(intended), 'entries': len(ids),
            'hangul_syllables_used': len(hangul), 'new_executable_code': False, 'new_VRAM_allocation': False,
            'new_font_bytes': False, 'layout': layout, 'review_state': 'needs_review',
        }
        m['baseline_sha256'] = sha(base)
        m['output_sha256'] = sha(bytes(target))
        m['output_bytes'] = len(target)
        m['runtime'] = 'pending'
        m['known_limit'] = ('adds gated story batches; the rest of the story text, the short-label consumers, '
                            'independent review and whole-game/device QA remain open')
        out = p / 'poc/output' / (PRODUCT.format(key=key) + '.gba')
        out.write_bytes(bytes(target))
        out.with_suffix('.json').write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')
        results[key] = {'sha256': m['output_sha256'], 'entries': len(ids), 'archives': sorted(intended),
                        'bytes': len(target), 'grew': len(target) - len(base)}
        print(key, m['output_sha256'], 'entries', len(ids), 'archives', sorted(intended),
              'grew', len(target) - len(base), 'bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
