#!/usr/bin/env python3
"""Verify a TextPet .tpi archive index against an actual EXE3 ROM.

The .tpi file is a third-party hypothesis about where message archives live and
which ROM words hold pointers to them.  Nothing in it is treated as fact until
the bytes in this exact ROM agree.  For every index row we check:

  * the archive offset is in range and 4-byte aligned;
  * a '&' row (compressed) starts with a GBA LZ77 header (0x10) and decompresses
    while consuming exactly the stated compressed length;
  * a '%' row (size header) stores the stated size as a leading 32-bit word;
  * every listed pointer word actually holds 0x08000000 + offset.

Rows whose pointer list is the single placeholder 0x00 carry no pointer claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROM_BASE = 0x08000000


def parse_tpi(path: Path) -> list:
    rows = []
    text = path.read_text(encoding="utf-8-sig")
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        head, _, ptr_part = line.partition("=")
        off_str, _, size_str = head.partition(":")
        compressed = "&" in size_str
        size_header = "%" in size_str
        size_str = size_str.replace("&", "").replace("%", "").strip()
        pointers = []
        for tok in ptr_part.split(","):
            tok = tok.strip()
            if tok:
                pointers.append(int(tok, 16))
        rows.append(
            {
                "line": lineno,
                "offset": int(off_str, 16),
                "size": int(size_str, 16) if size_str else None,
                "compressed": compressed,
                "size_header": size_header,
                "pointers": pointers,
            }
        )
    return rows


def lz77_decompress(data: bytes, start: int):
    """GBA BIOS LZ77 (type 0x10).  Returns (output, bytes consumed)."""
    if start + 4 > len(data) or data[start] != 0x10:
        raise ValueError("not an LZ77 0x10 stream")
    out_size = int.from_bytes(data[start + 1 : start + 4], "little")
    pos = start + 4
    out = bytearray()
    while len(out) < out_size:
        if pos >= len(data):
            raise ValueError("truncated LZ77 stream")
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(out) >= out_size:
                break
            if flags & (0x80 >> bit):
                if pos + 1 >= len(data):
                    raise ValueError("truncated LZ77 match")
                b0, b1 = data[pos], data[pos + 1]
                pos += 2
                length = (b0 >> 4) + 3
                disp = (((b0 & 0x0F) << 8) | b1) + 1
                if disp > len(out):
                    raise ValueError("LZ77 back-reference before start")
                for _ in range(length):
                    out.append(out[-disp])
            else:
                if pos >= len(data):
                    raise ValueError("truncated LZ77 literal")
                out.append(data[pos])
                pos += 1
    return bytes(out), pos - start


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--tpi", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    rom_path = Path(args.rom)
    rom = rom_path.read_bytes()
    tpi_path = Path(args.tpi)
    rows = parse_tpi(tpi_path)

    report = {
        "rom": rom_path.name,
        "rom_sha256": hashlib.sha256(rom).hexdigest(),
        "rom_size": len(rom),
        "tpi": tpi_path.name,
        "tpi_sha256": hashlib.sha256(tpi_path.read_bytes()).hexdigest(),
        "label": args.label,
        "archives_total": len(rows),
        "archives_compressed": 0,
        "archives_size_header": 0,
        "archives_raw": 0,
        "offset_ok": 0,
        "offset_bad": [],
        "lz77_ok": 0,
        "lz77_bad": [],
        "lz77_length_mismatch": [],
        "size_header_ok": 0,
        "size_header_bad": [],
        "pointers_total": 0,
        "pointers_ok": 0,
        "pointers_bad": [],
        "rows_without_pointer_claim": 0,
        "decoded_bytes_total": 0,
    }

    for row in rows:
        off = row["offset"]
        size = row["size"]
        if row["compressed"]:
            report["archives_compressed"] += 1
        elif row["size_header"]:
            report["archives_size_header"] += 1
        else:
            report["archives_raw"] += 1

        if 0 <= off < len(rom) and off % 4 == 0:
            report["offset_ok"] += 1
        else:
            report["offset_bad"].append({"line": row["line"], "offset": off})
            continue

        if row["compressed"]:
            try:
                decoded, consumed = lz77_decompress(rom, off)
                report["lz77_ok"] += 1
                report["decoded_bytes_total"] += len(decoded)
                if size is not None and consumed != size:
                    report["lz77_length_mismatch"].append(
                        {
                            "line": row["line"],
                            "offset": off,
                            "declared": size,
                            "consumed": consumed,
                            "decoded_size": len(decoded),
                        }
                    )
            except Exception as exc:  # recorded as evidence, not raised
                report["lz77_bad"].append(
                    {"line": row["line"], "offset": off, "error": str(exc)}
                )
        elif row["size_header"]:
            stored = int.from_bytes(rom[off : off + 4], "little")
            if size is not None and stored == size:
                report["size_header_ok"] += 1
            else:
                report["size_header_bad"].append(
                    {
                        "line": row["line"],
                        "offset": off,
                        "declared": size,
                        "stored": stored,
                    }
                )

        expected = ROM_BASE + off
        claims = [p for p in row["pointers"] if p != 0]
        if not claims:
            report["rows_without_pointer_claim"] += 1
        for ptr in claims:
            report["pointers_total"] += 1
            if ptr + 4 > len(rom):
                report["pointers_bad"].append(
                    {"line": row["line"], "ptr_at": ptr, "error": "out of range"}
                )
                continue
            stored = int.from_bytes(rom[ptr : ptr + 4], "little")
            # EXE4 has flagged ROM pointers. Keep the original value and flag
            # explicit; accept bit 31 only for an indexed compressed archive.
            flagged = row["compressed"] and stored == (expected | 0x80000000)
            if stored == expected or flagged:
                report["pointers_ok"] += 1
                if flagged:
                    report.setdefault("compressed_flagged_pointers", []).append(
                        {"line": row["line"], "ptr_at": ptr, "stored": stored,
                         "address": expected, "flag": "0x80000000"})
            else:
                report["pointers_bad"].append(
                    {
                        "line": row["line"],
                        "ptr_at": ptr,
                        "expected": expected,
                        "stored": stored,
                    }
                )

    report["verdict"] = (
        "MATCH"
        if not report["offset_bad"]
        and not report["lz77_bad"]
        and not report["size_header_bad"]
        and not report["pointers_bad"]
        and not report["lz77_length_mismatch"]
        else "MISMATCH"
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("%s: %s" % (args.label or rom_path.name, report["verdict"]))
    print("  archives          %d (compressed %d, size-header %d, raw %d)"
          % (report["archives_total"], report["archives_compressed"],
             report["archives_size_header"], report["archives_raw"]))
    print("  offsets ok        %d/%d" % (report["offset_ok"], report["archives_total"]))
    print("  LZ77 decoded ok   %d/%d   length mismatches %d"
          % (report["lz77_ok"], report["archives_compressed"],
             len(report["lz77_length_mismatch"])))
    print("  size-header ok    %d/%d" % (report["size_header_ok"],
                                         report["archives_size_header"]))
    print("  pointers verified %d/%d   bad %d"
          % (report["pointers_ok"], report["pointers_total"],
             len(report["pointers_bad"])))
    print("  rows w/o pointer claim %d" % report["rows_without_pointer_claim"])
    print("  decoded bytes total    %d" % report["decoded_bytes_total"])
    return 0 if report["verdict"] == "MATCH" else 1


if __name__ == "__main__":
    sys.exit(main())
