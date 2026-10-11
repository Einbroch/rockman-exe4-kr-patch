"""8x16 Hangul ink masks from the local EXE 1 [K] Korean ROM, for the tile font.

The EXE3 project established this source and its placement (see that project's
tools/exe1k_glyphs.py).  EXE4's own tile font uses the same band -- ink in rows
1..13 and columns 0..6 of the 8x16 cell, measured over its kana records in both
styles -- so the same transform applies: decode the record (ink is palette
index 3 on index 1), move it by (-1,-1), and fold its fourteen rows into the
thirteen-row band by deleting one repeated row.

The ROM is a local-only reference.  It is never copied into this project, and
reading glyphs from it grants no distribution right.
"""
import hashlib
from pathlib import Path

EXPECTED_SHA256 = 'c0753c1d3170f69e1eb8b03a02875ec63c5622185ac4afbb2b8688c53209d865'
FONT_BASE_OFFSET = 0x80016C
HANGUL_BASE_INDEX = 512
KS_COUNT = 2350
INK, BACKGROUND = 3, 1


def load(path):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError('unexpected EXE 1 [K] ROM')
    if data[0xAC:0xB0] != b'AREJ':
        raise ValueError('EXE 1 [K] header identity differs')
    return data


def ordinal(ch):
    """KS X 1001 Hangul ordinal, or None for a syllable outside it."""
    try:
        e = ch.encode('euc_kr')
    except UnicodeEncodeError:
        return None
    if len(e) != 2 or not (0xB0 <= e[0] <= 0xC8 and 0xA1 <= e[1] <= 0xFE):
        return None
    n = (e[0] - 0xB0) * 94 + (e[1] - 0xA1)
    return n if n < KS_COUNT else None


def _mask(source, n):
    at = FONT_BASE_OFFSET + (HANGUL_BASE_INDEX + n) * 64
    record = source[at:at + 64]
    mask = [[0] * 8 for _ in range(16)]
    for i, byte in enumerate(record):
        y, x = i // 4, (i % 4) * 2
        for k, v in ((0, byte & 15), (1, byte >> 4)):
            if v not in (INK, BACKGROUND):
                raise ValueError('EXE 1 [K] record uses an unexpected palette index')
            mask[y][x + k] = int(v == INK)
    return mask


def _fold(mask, ch):
    if not any(mask[0]):
        return mask
    # Only a repeated row with ink is a stroke; folding two blank rows would
    # just slide the whole glyph down onto row 14.
    for d in range(1, 16):
        if mask[d] == mask[d - 1] and any(mask[d]):
            return [[0] * 8] + [row[:] for row in mask[:d]] + [row[:] for row in mask[d + 1:]]
    if all(mask[1][x] and mask[2][x] for x in range(8) if mask[0][x]):
        return [[0] * 8] + [row[:] for row in mask[1:]]
    # 68 glyphs (o/u vowels over a final ㄹ/ㅇ, e.g. 올 용 줄) have neither; as in
    # EXE3 they fold a blank row and sit one row lower, ink on rows 1..14.
    for d in range(1, 16):
        if mask[d] == mask[d - 1]:
            return [[0] * 8] + [row[:] for row in mask[:d]] + [row[:] for row in mask[d + 1:]]
    raise ValueError('glyph %r cannot be folded into the band' % ch)


def ink(source, ch):
    """Ink pixels {(x, y)} of ch in EXE4's band, or None outside KS X 1001."""
    n = ordinal(ch)
    if n is None:
        return None
    m = _mask(source, n)
    if any(m[y][0] for y in range(16)) or any(m[0]) or any(m[15]):
        raise ValueError('EXE 1 [K] glyph %r is not inside rows 1..14, columns 1..7' % ch)
    moved = [m[y + 1][1:] + [0] for y in range(15)] + [[0] * 8]
    out = _fold(moved, ch)
    pixels = {(x, y) for y in range(16) for x in range(8) if out[y][x]}
    if not pixels or min(y for _, y in pixels) < 1 or max(y for _, y in pixels) > 14 or max(x for x, _ in pixels) > 6:
        raise ValueError('glyph %r falls outside the native band' % ch)
    return pixels
