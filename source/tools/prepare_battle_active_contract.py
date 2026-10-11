"""Freeze separately observed queued-chip caller coordinates for both sources."""
import json
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
base=json.loads((p/'tools/specs/exe4_battle_caption_v1.json').read_text(encoding='utf-8'))
base['scope']='in-battle queued chip name only; needs_review NON-DISTRIBUTION'
for key,at in [('blue_moon',0x15030),('red_sun',0x15064)]:
 s=base['profiles'][key]
 source=next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes())==s['source_sha256'])
 if source[at:at+8].hex()!='494b08240125494e':raise ValueError('active source caller drift')
 s['hook']={'offset':at,'expected_hex':'494b08240125494e','continuation':0x08000000+at+9}
 s['context']={'offset':at-6,'size':22,'sha256':sha(source[at-6:at+16])}
(p/'tools/specs/exe4_battle_active_v1.json').write_text(json.dumps(base,indent=2),encoding='utf-8')
