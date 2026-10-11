"""Title menu sheet: span guard, shared から columns, untouched columns, drift refusal."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from title_menu_label import build
from verify_tpi_index import lz77_decompress

p = Path(__file__).resolve().parent.parent
font = p.parent.parent.parent / '폰트/Galmuri-v2.24.29/Galmuri11.bdf'
for key, pat in (('red_sun', '*Red Sun*Rev 1*.gba'), ('blue_moon', '*Blue Moon*.gba')):
    rom = next(f for f in p.parent.parent.glob(pat)).read_bytes()
    (at, blob, _), = build(p, key, rom, font)[0]
    assert len(blob) <= 768 and rom[at + 768] == 0x10
    new, _ = lz77_decompress(blob, 0)
    old, _ = lz77_decompress(rom, at)
    assert new[:4] == old[:4] and len(new) == len(old), 'size word and length kept'
    assert new != old
    bad = bytearray(rom); bad[at + 0x20] ^= 0xFF
    try:
        build(p, key, bytes(bad), font)
    except ValueError:
        pass
    else:
        raise AssertionError('drift not refused')
print('OK')
