#!/usr/bin/env python3
"""Ask one question about a product: does it draw anything at all?

A blank screen from the first capture is not a route problem, it is a dead
boot, and the 107-step route is a very slow way to learn that. This runs three
captures per product and reports whether any of them holds more than one
colour, which takes about a minute.

It exists because a build that wrapped a raw archive in an LZ77 header left the
screen black from frame one, and the only thing that noticed was a route that
took forty minutes to say so.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

p = Path(__file__).resolve().parents[1]
MESEN = 'C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe'


def check(rom: Path) -> dict:
    rom = rom if rom.is_absolute() else (p / rom)
    m = json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'))
    out = p / 'analysis/runtime' / f"boot_check_{m['output_sha256'][:8]}"
    if not out.exists():
        subprocess.run([sys.executable, str(p / 'tools/run_mesen_segment.py'), '--rom', str(rom),
                        '--mesen', MESEN, '--out', str(out), '--expect-rom-sha256', m['output_sha256'],
                        '--actions', 'none:1:900,none:1:300,start:1:300', '--probe', 'none',
                        '--timeout', '180'], check=True)
    shots = sorted(out.glob('step_*.png'))
    colours = [len(set(Image.open(f).convert('RGB').getdata())) for f in shots]
    return {'product': rom.relative_to(p).as_posix(), 'rom_sha256': m['output_sha256'],
            'route': out.relative_to(p).as_posix(), 'colours_per_capture': colours,
            'draws': any(c > 1 for c in colours)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', type=Path, action='append', required=True)
    ap.add_argument('--record', type=Path, help='write a report here; exit non-zero unless every ROM draws')
    a = ap.parse_args()
    results = [check(rom) for rom in a.rom]
    for r in results:
        state = 'DRAWS' if r['draws'] else 'BLANK'
        print(f"{Path(r['product']).name}  sha {r['rom_sha256'][:12]}  "
              f"colours per capture {r['colours_per_capture']}  {state}")
    if a.record:
        report = {
            'schema': 1,
            'status': 'PASS' if all(r['draws'] for r in results) else 'FAIL',
            'scope': 'three captures from a cold boot; a single colour everywhere means the ROM never drew',
            'not_claimed': ['the game is playable', 'any particular screen is correct'],
            'products': results,
        }
        a.record.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if all(r['draws'] for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
