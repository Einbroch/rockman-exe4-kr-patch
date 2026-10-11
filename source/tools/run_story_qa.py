#!/usr/bin/env python3
"""Cold-boot the story product and walk to the link-battle explanation, which is
where batch 001 is drawn.

The route is short on purpose: the Operation Battle menu sits behind the title
screen, so this text can be reached without a save, without a link cable and
without replaying the prologue. Stage 'probe' is an exploratory walk that
captures every step so the menu layout can be read off the screen; stage
'final' replays a route that has already been read and captures it as evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

p = Path(__file__).resolve().parents[1]
MESEN = 'C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe'
PRODUCT = '{key}_opening_menu_chip_folder_library_menu_descriptions_story_korean_development'


def run(key: str, out: str, actions: list[str], timeout: int, capture: str | None = None) -> None:
    rom = p / 'poc/output' / (PRODUCT.format(key=key) + '.gba')
    data = rom.read_bytes()
    m = json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'))
    # Name the directory after the build it came from. Reusing one name across
    # rebuilds silently mixes captures of two different ROMs in one folder.
    out = f"{out}_{m['output_sha256'][:8]}"
    command = [sys.executable, str(p / 'tools/run_mesen_segment.py'), '--rom', str(rom), '--mesen', MESEN,
               '--out', str(p / 'analysis/runtime' / out), '--expect-rom-sha256', m['output_sha256'],
               '--actions', ','.join(actions), '--probe', 'none', '--timeout', str(timeout)]
    if capture:
        command += ['--capture-steps', capture]
    guards = []
    for w in m['expected_writes']:
        if w['offset'] < 0x800000:
            guards += ['--guard', str(w['offset']) + ':' + data[w['offset']:w['offset'] + w['size']].hex()]
    guards += ['--guard', '160:' + data[160:192].hex()]
    for item in m['extension']['story']['layout']:
        at = item['offset']
        guards += ['--guard', str(at) + ':' + data[at:at + 16].hex()]
    # One guard per relocated archive and pointer word: the list grows with every
    # batch and passed the Windows command-line limit at batch 106, so it goes
    # through an argument file (run_mesen_segment.py reads '@file'). The segment
    # still records every guard in its result.json.
    with tempfile.NamedTemporaryFile('w', suffix='.args', delete=False, encoding='utf-8') as f:
        f.write('\n'.join(guards) + '\n')
    try:
        subprocess.run(command + ['@' + f.name], check=True)
    finally:
        Path(f.name).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--key', required=True, choices=['blue_moon', 'red_sun'])
    ap.add_argument('--stage', required=True, choices=['probe', 'cold', 'final'])
    a = ap.parse_args()
    if a.stage == 'probe':
        # Boot, let the title settle, then press through whatever it offers,
        # capturing every step so the menu can be read rather than guessed.
        actions = ['none:1:900', 'start:1:180'] + ['none:1:120'] * 2
        actions += ['down:6:60', 'none:1:60', 'down:6:60', 'none:1:60', 'up:6:60', 'none:1:60']
        actions += ['a:6:180', 'none:1:120', 'none:1:120']
        run(a.key, f'{a.key}_story_probe_01', actions, 420)
    elif a.stage == 'cold':
        # The established menu route for this ROM lineage, replayed on the story
        # product with every step captured, so the field dialogue it passes through
        # can be read off the screen and matched to an archive.
        import ast
        tree = ast.parse((p / 'tools/run_menu_qa.py').read_text(encoding='utf-8'))
        nodes = []
        for n in tree.body:
            if isinstance(n, ast.For):
                break
            if isinstance(n, (ast.Assign, ast.AugAssign)):
                target = n.targets[0] if isinstance(n, ast.Assign) else n.target
                if isinstance(target, ast.Name) and target.id == 'actions':
                    nodes.append(n)
        scope = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'established_menu_actions', 'exec'), scope)
        run(a.key, f'{a.key}_story_cold_01', scope['actions'], 600)
    else:
        actions = json.loads((p / 'analysis/story_route.json').read_text(encoding='utf-8'))[a.key]
        run(a.key, f'{a.key}_story_final_01', actions, 480)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
