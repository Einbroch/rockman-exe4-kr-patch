"""Cold boot and inspect four naturally offered Custom Screen descriptions."""
import argparse,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True);a=ap.parse_args()
key=a.key
rom=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'));data=rom.read_bytes();previous=None
for name in ['cold_01','route_02','route_03','route_04','ready_01']:
 template=p/'analysis/runtime'/f'blue_moon_battle_caption_{name}/result.json'
 r=json.loads(template.read_text(encoding='utf-8'));out=p/'analysis/runtime'/f'{key}_descriptions_{name}'
 if not r['complete'] or r['return_code']:raise ValueError('incomplete source route')
 c=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),'--mesen',r['emulator_path'],
    '--out',str(out),'--expect-rom-sha256',m['output_sha256'],'--actions',r['actions'],'--probe','none','--timeout','900']
 if name=='cold_01':c+=['--capture-steps',','.join(map(str,r['capture_steps']))]
 if previous:c+=['--state',str(previous/'checkpoint.mss'),'--state-origin',str(previous/'result.json')]
 for w in m['expected_writes']:
  if w['offset']<0x800000:c+=['--guard',str(w['offset'])+':'+data[w['offset']:w['offset']+w['size']].hex()]
 c+=['--guard','160:'+data[160:192].hex(),'--guard','8388608:'+data[0x800000:0x800010].hex()]
 print(key,name,flush=True);subprocess.run(c,check=True);previous=out
actions='none:1:30,r:6:60,b:6:30,right:6:30,r:6:60,b:6:30,right:6:30,right:6:30,r:6:60,b:6:30,right:6:30,r:6:60,b:6:30,left:6:30,r:6:60,b:6:30'
subprocess.run([sys.executable,str(p/'tools/continue_battle_route.py'),previous.name,key+'_descriptions_final_01',actions,'--probe','snapshot'],check=True)
