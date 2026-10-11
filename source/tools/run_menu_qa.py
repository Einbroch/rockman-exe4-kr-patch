"""Sequential muted cold boot, ordinary inputs, shared tile calls and reads."""
import json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
actions=['none:1:900','start:1:120','a:1:360','none:1:300']+['a:1:240']*60+['a:1:240','a:1:240','none:1:300','a:1:600','a:1:300','none:1:600']
actions+=['a:6:180']*10
actions+=['right+down:22:60','right+up:25:60','down:25:30','right:35:30','up:15:30']
actions+=['a:6:180']*6+['start:6:120','a:6:120','b:6:60']
actions+=['down:6:30']*7+['a:6:180','right:6:30','a:6:120','b:6:60','b:6:60','start:6:120']
for key in ['blue_moon','red_sun']:
 rom=p/'poc/output'/f'{key}_opening_menu_korean_development.gba'
 m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'));data=rom.read_bytes();tile=m['extension']['menu']
 command=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),
  '--mesen','C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe',
  '--out',str(p/'analysis/runtime'/f'{key}_menu_final_02'),'--expect-rom-sha256',m['output_sha256'],
  '--actions',','.join(actions),'--probe','tilecalls','--font-base',hex(0x08000000+tile['fonts'][0]),
  '--font-end',hex(0x08000000+tile['fonts'][1]+4363*64),'--font-stride','64','--timeout','360']
 guards=[(0xa0,32),(0x800000,16),(tile['fonts'][0],64),(tile['fonts'][1],64)]
 guards += [(w['offset'],4) for w in m['expected_writes'] if w['size']==4]
 for at,size in guards:command.extend(['--guard',f'{at}:'+data[at:at+size].hex()])
 print(key,'steps',len(actions),flush=True);subprocess.run(command,check=True)
