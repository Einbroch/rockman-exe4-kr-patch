"""Cold replay through the inspected caption and first-battle input checkpoints."""
import argparse,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True);a=ap.parse_args()
key=a.key
rom=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba'
m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'));data=rom.read_bytes()
s=json.loads((p/'tools/specs/exe4_battle_active_v1.json').read_text())['profiles'][key]
templates=[('cold_01','blue_moon_battle_caption_cold_01')]
templates += [(name,'blue_moon_battle_caption_'+name) for name in ['route_02','route_03','route_04','ready_01']]
templates += [('survey_'+n,'blue_moon_battle_active_survey_'+n) for n in ['01','02','03','04','05']]
previous=None
for name,template in templates:
 r=json.loads((p/'analysis/runtime'/template/'result.json').read_text(encoding='utf-8'))
 if not r['complete'] or r['return_code']:raise ValueError('invalid route template')
 out=p/'analysis/runtime'/f'{key}_battle_active_verify_{name}'
 c=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),'--mesen',r['emulator_path'],
    '--out',str(out),'--expect-rom-sha256',m['output_sha256'],'--actions',r['actions'],
    '--probe','snapshot' if name.startswith('survey_') else 'exectrace','--timeout','900']
 if not name.startswith('survey_'):c+=['--trace-pc',hex(0x08000000+s['hook']['offset'])]
 if name=='cold_01':c+=['--capture-steps',','.join(map(str,r['capture_steps']))]
 if previous:c+=['--state',str(previous/'checkpoint.mss'),'--state-origin',str(previous/'result.json')]
 for w in m['expected_writes']:
  if w['offset']<0x800000:c+=['--guard',str(w['offset'])+':'+data[w['offset']:w['offset']+w['size']].hex()]
 c+=['--guard','160:'+data[160:192].hex(),'--guard','8388608:'+data[0x800000:0x800010].hex()]
 print(key,name,flush=True)
 subprocess.run(c,check=True);previous=out
