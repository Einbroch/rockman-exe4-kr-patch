#!/usr/bin/env python3
"""Measure the translatable text corpus in a directory of extracted TPL files.

This sizes the job and, just as importantly, records which archives hold no
text at all so they can be excluded from the translation denominator instead of
being silently counted as "remaining".

A TPL string literal is the quoted run inside a script block.  Escaped quotes
are respected so a literal containing one is not split.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
SCRIPT_RE = re.compile(r"^script\s+(\d+)\s+(\S+)\s*\{", re.MULTILINE)
# Characters that do not by themselves make a line worth translating.
NON_TEXT = set(" \t0123456789")


def japanese_chars(s: str) -> int:
    n = 0
    for ch in s:
        o = ord(ch)
        if (0x3040 <= o <= 0x30FF) or (0x4E00 <= o <= 0x9FFF) or (0xFF66 <= o <= 0xFF9D):
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tpl-dir", required=True)
    ap.add_argument("--output")
    args = ap.parse_args()

    files = sorted(Path(args.tpl_dir).glob("*.tpl"))
    per_archive = []
    total_scripts = 0
    total_strings = 0
    total_chars = 0
    total_jp = 0
    empty_archives = 0
    script_langs = Counter()
    unique = set()

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        scripts = SCRIPT_RE.findall(text)
        strings = [m.group(1) for m in STRING_RE.finditer(text)]
        chars = sum(len(s) for s in strings)
        jp = sum(japanese_chars(s) for s in strings)
        for _, lang in scripts:
            script_langs[lang] += 1
        for s in strings:
            if s.strip() and any(c not in NON_TEXT for c in s):
                unique.add(s)
        total_scripts += len(scripts)
        total_strings += len(strings)
        total_chars += chars
        total_jp += jp
        if jp == 0:
            empty_archives += 1
        per_archive.append(
            {
                "archive": path.stem,
                "scripts": len(scripts),
                "strings": len(strings),
                "chars": chars,
                "japanese_chars": jp,
            }
        )

    per_archive.sort(key=lambda a: -a["japanese_chars"])
    report = {
        "tpl_dir": str(Path(args.tpl_dir)),
        "archives": len(files),
        "archives_without_japanese": empty_archives,
        "scripts_total": total_scripts,
        "script_languages": dict(script_langs),
        "strings_total": total_strings,
        "string_chars_total": total_chars,
        "japanese_chars_total": total_jp,
        "unique_nontrivial_strings": len(unique),
        "largest_archives": per_archive[:25],
    }
    print("archives                 %d  (without Japanese: %d)"
          % (len(files), empty_archives))
    print("scripts                  %d   %s" % (total_scripts, dict(script_langs)))
    print("string literals          %d" % total_strings)
    print("string characters        %d" % total_chars)
    print("Japanese characters      %d" % total_jp)
    print("unique non-trivial lines %d" % len(unique))
    print("largest archives by Japanese char count:")
    for a in per_archive[:12]:
        print("  %-8s scripts=%-5d strings=%-5d jp=%d"
              % (a["archive"], a["scripts"], a["strings"], a["japanese_chars"]))
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
