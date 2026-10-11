#!/usr/bin/env python3
"""Enumerate every 8x16 4bpp glyph bank in an EXE3 ROM.

Patching one copy of a font while the game reads another is a known way to get
a half-translated screen, so the bank count has to be established before any
glyph work, not after.

A bank is recognised by the layout the confirmed dialogue bank uses: record 0 is
an all-zero blank (the space character at table index 0x00), and records 1..N
are valid glyph records -- 64 bytes whose nibbles all fall in the bank's small
palette set.  Candidates are reported with their record count so a partial
lookalike cannot pass as a full bank.

The palette set is derived from the ROM rather than assumed: the confirmed
dialogue bank uses nibbles {0,1,2}, but a bank drawn with different indices
would still be found because the check is "few distinct nibbles", not "these
nibbles".
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

RECORD_BYTES = 64
MIN_RECORDS = 64


def record_nibbles(rom: bytes, off: int) -> set:
    values = set()
    for b in rom[off : off + RECORD_BYTES]:
        values.add(b & 0x0F)
        values.add(b >> 4)
    return values


def bank_at(rom: bytes, base: int, max_nibbles: int):
    """Return (record_count, palette) if a glyph bank starts at base, else None."""
    if base + RECORD_BYTES > len(rom):
        return None
    if any(b != 0 for b in rom[base : base + RECORD_BYTES]):
        return None  # record 0 must be the blank space glyph
    palette = set()
    count = 0
    inked = 0
    while base + (count + 1) * RECORD_BYTES <= len(rom):
        nib = record_nibbles(rom, base + count * RECORD_BYTES)
        merged = palette | nib
        if len(merged) > max_nibbles:
            break
        palette = merged
        if nib != {0}:
            inked += 1
        count += 1
    if count < MIN_RECORDS or inked < MIN_RECORDS // 2:
        return None
    return count, palette, inked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--max-nibbles", type=int, default=4)
    ap.add_argument("--output")
    args = ap.parse_args()

    rom_path = Path(args.rom)
    rom = rom_path.read_bytes()

    banks = []
    off = 0
    step = 4
    while off + RECORD_BYTES <= len(rom):
        # cheap pre-filter: 64 zero bytes
        if rom[off] == 0 and rom[off : off + RECORD_BYTES].count(0) == RECORD_BYTES:
            found = bank_at(rom, off, args.max_nibbles)
            if found:
                count, palette, inked = found
                banks.append(
                    {
                        "base": off,
                        "base_hex": "0x%X" % off,
                        "records": count,
                        "inked_records": inked,
                        "end_hex": "0x%X" % (off + count * RECORD_BYTES),
                        "palette_nibbles": sorted(palette),
                        "sha256": hashlib.sha256(
                            rom[off : off + count * RECORD_BYTES]
                        ).hexdigest(),
                    }
                )
                off += count * RECORD_BYTES
                continue
        off += step

    # Drop banks fully contained in a larger one already listed.
    banks.sort(key=lambda b: b["base"])
    report = {
        "rom": rom_path.name,
        "rom_sha256": hashlib.sha256(rom).hexdigest(),
        "max_nibbles": args.max_nibbles,
        "min_records": MIN_RECORDS,
        "bank_count": len(banks),
        "banks": banks,
    }
    print("%s: %d glyph bank(s)" % (rom_path.name, len(banks)))
    for b in banks:
        print("  base %-10s records %4d (inked %4d) end %-10s palette %s"
              % (b["base_hex"], b["records"], b["inked_records"], b["end_hex"],
                 b["palette_nibbles"]))
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
