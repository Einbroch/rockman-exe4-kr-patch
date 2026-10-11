#!/usr/bin/env python3
"""Build the story product from a chosen subset of batches and boot-check it.

Used to find which batch stops the game from drawing. The prepared batches are
moved aside rather than deleted, so the set is restored exactly afterwards.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

p = Path(__file__).resolve().parents[1]
BATCHES = p / 'translations/story_korean'
HOLD = p / 'poc/bisect_hold'
PRODUCT = 'blue_moon_opening_menu_chip_folder_library_menu_descriptions_story_korean_development'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', required=True, help='comma-separated batch numbers to keep, e.g. 001,002')
    a = ap.parse_args()
    keep = {x.strip() for x in a.keep.split(',') if x.strip()}
    HOLD.mkdir(parents=True, exist_ok=True)
    moved = []
    try:
        for f in sorted(BATCHES.glob('batch_*.json')):
            if f.stem.split('_')[1] not in keep:
                shutil.move(str(f), HOLD / f.name)
                moved.append(f.name)
        present = sorted(x.stem.split('_')[1] for x in BATCHES.glob('batch_*.json'))
        print('building with batches', present)
        for step in ('tools/check_story_translation.py', 'tools/build_story_batch.py'):
            r = subprocess.run([sys.executable, str(p / step)], capture_output=True, text=True,
                               encoding='utf-8', errors='replace')
            print(' ', step, r.returncode, (r.stdout or r.stderr).strip().splitlines()[-1][:120])
            if r.returncode:
                return 1
        rom = p / 'poc/output' / (PRODUCT + '.gba')
        r = subprocess.run([sys.executable, str(p / 'tools/boot_check.py'), '--rom', str(rom)],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(r.stdout.strip())
        return r.returncode
    finally:
        for name in moved:
            shutil.move(str(HOLD / name), BATCHES / name)


if __name__ == '__main__':
    raise SystemExit(main())
