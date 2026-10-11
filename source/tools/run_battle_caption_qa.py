"""Cold replay on each product; flattened route ends in kitchen, not battle QA.

Use run_battle_caption_followup.py afterwards to correct the movement route and
reach the actual Custom Screen. Complete here means input replay only.
"""
import argparse,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True)
a=ap.parse_args()
origin=p/'analysis/runtime/blue_moon_battle_route_48/result.json'
chain=[]
while True:
    r=json.loads(origin.read_text(encoding='utf-8'))
    if not r['complete']:raise ValueError('partial route source')
    chain.append((origin,r))
    if not r.get('state_origin'):break
    origin=Path(r['state_origin'])
chain.reverse()
actions=[];landmarks=[]
for path,r in chain:
    actions+=r['actions'].split(',')
    landmarks.append({'source_receipt':path.relative_to(p).as_posix(),'last_action':len(actions)})
rom=p/'poc/output'/f'{a.key}_opening_menu_chip_folder_library_battle_caption_korean_development.gba'
m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'));data=rom.read_bytes()
out=p/'analysis/runtime'/f'{a.key}_battle_caption_cold_01'
spec=json.loads((p/'tools/specs/exe4_battle_caption_v1.json').read_text(encoding='utf-8'))['profiles'][a.key]
c=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),'--mesen',r['emulator_path'],
   '--out',str(out),'--expect-rom-sha256',m['output_sha256'],'--actions',','.join(actions),
   '--capture-steps',','.join(str(x['last_action']) for x in landmarks),'--probe','exectrace',
   '--trace-pc',hex(0x08000000+spec['hook']['offset']), '--timeout','600']
for w in m['expected_writes']:
    if w['offset']<0x800000:c+=['--guard',str(w['offset'])+':'+data[w['offset']:w['offset']+w['size']].hex()]
c+=['--guard','160:'+data[160:192].hex(),'--guard','8388608:'+data[0x800000:0x800010].hex()]
print(a.key,'cold replay',len(actions),'actions',len(landmarks),'captures',flush=True)
subprocess.run(c,check=True)
(out/'route_lineage.json').write_text(json.dumps(landmarks,indent=2),encoding='utf-8')
