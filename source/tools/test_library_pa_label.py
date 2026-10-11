"""The P.A caption tool: compressor round-trip, span guard, and drift refusal."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from library_pa_label import lz77_compress, build
from verify_tpi_index import lz77_decompress

p = Path(__file__).resolve().parent.parent
font = p.parent.parent.parent / '폰트/Galmuri-v2.24.29/Galmuri7.bdf'
for data in (b'', b'a', b'abcabcabcabcabc' * 40, bytes(range(256)) * 3, b'\x00' * 5000):
    blob = lz77_compress(data)
    back, used = lz77_decompress(blob, 0)
    assert back == data and len(blob) % 4 == 0 and used <= len(blob), len(data)
for key, pat in (('red_sun', '*Red Sun*Rev 1*.gba'), ('blue_moon', '*Blue Moon*.gba')):
    rom = next(f for f in p.parent.parent.glob(pat)).read_bytes()
    writes, meta = build(p, key, rom, font)
    (at, blob, _), = writes
    assert len(blob) <= 1016 and rom[at + 1016] == 0x10
    sheet, _ = lz77_decompress(blob, 0)
    old, _ = lz77_decompress(rom, at)
    diff = [i for i in range(len(old)) if old[i] != sheet[i]]
    assert diff and 0x11A4 <= min(diff) and max(diff) < 0x11A4 + 160, 'only the caption tiles and the handakuten tile change'
    bad = bytearray(rom); bad[at + 0x40] ^= 0xFF
    try:
        build(p, key, bytes(bad), font)
    except ValueError:
        pass
    else:
        raise AssertionError('drift not refused')
print('OK')
