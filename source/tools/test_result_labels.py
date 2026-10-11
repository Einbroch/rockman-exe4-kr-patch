"""Result window labels: only label bands and border dakuten cells change, pool guard, drift refusal."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from result_labels import build

p = Path(__file__).resolve().parent.parent
font = p.parent.parent.parent / '폰트/Galmuri-v2.24.29/Galmuri9.bdf'
for key, pat in (('red_sun', '*Red Sun*Rev 1*.gba'), ('blue_moon', '*Blue Moon*.gba')):
    rom = next(f for f in p.parent.parent.glob(pat)).read_bytes()
    writes, meta = build(p, key, rom, font)
    (ta, tiles, _), (ma, mp, _) = writes
    assert len(mp) == 24 * 17 * 2 and len(tiles) == 0x57 * 32
    changed = {i // 2 for i in range(len(mp)) if mp[i] != rom[ma + i]}
    allowed = {r * 24 + c for r in (3, 4) for c in range(3, 14)} | {r * 24 + c for r in (6, 7) for c in range(3, 16)} \
        | {2 * 24 + 3, 5 * 24 + 3, 5 * 24 + 8, 5 * 24 + 10}
    assert changed <= allowed, sorted(changed - allowed)
    for i in range(0, len(mp), 2):
        assert mp[i + 1] & 0xF0 == rom[ma + i + 1] & 0xF0, 'palette bits kept'
    bad = bytearray(rom); bad[ta + 0x1A * 32] ^= 0xFF
    try:
        build(p, key, bytes(bad), font)
    except ValueError:
        pass
    else:
        raise AssertionError('drift not refused')
print('OK')
