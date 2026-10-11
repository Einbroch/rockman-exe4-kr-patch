"""Own a cold boot of each exact product, then inspect folder/library descriptions."""
import argparse,ast,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',required=True,choices=['blue_moon','red_sun']);ap.add_argument('--stage',choices=['cold','final'],required=True);a=ap.parse_args()
key=a.key
if a.stage=='cold':
 tree=ast.parse((p/'tools/run_menu_qa.py').read_text(encoding='utf-8'));nodes=[]
 for n in tree.body:
  if isinstance(n,ast.For):break
  if isinstance(n,(ast.Assign,ast.AugAssign)):
   target=n.targets[0] if isinstance(n,ast.Assign) else n.target
   if isinstance(target,ast.Name) and target.id=='actions':nodes.append(n)
 scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'established_menu_actions','exec'),scope)
 rom=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_v2_korean_development.gba'
 data=rom.read_bytes();m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'))
 out=p/'analysis/runtime'/f'{key}_menu_descriptions_cold_02'
 c=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),'--mesen','C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe',
    '--out',str(out),'--expect-rom-sha256',m['output_sha256'],'--actions',','.join(scope['actions']),'--probe','none','--timeout','600','--capture-steps',str(len(scope['actions']))]
 for w in m['expected_writes']:
  if w['offset']<0x800000:c+=['--guard',str(w['offset'])+':'+data[w['offset']:w['offset']+w['size']].hex()]
 clone=m['extension']['menu_descriptions']['archive_offset']
 c+=['--guard','160:'+data[160:192].hex(),'--guard',str(clone)+':'+data[clone:clone+16].hex()]
 subprocess.run(c,check=True)
else:
 actions=['none:1:30','a:6:90','a:6:60','a:6:90']+['down:6:30']*30+['b:6:60','b:6:60','down:6:30','down:6:30','a:6:90']+['down:6:30']*4+['right:6:60','left:6:60','b:6:60','up:6:30','up:6:30','a:6:90','a:6:60','a:6:90']
 subprocess.run([sys.executable,str(p/'tools/continue_battle_route.py'),key+'_menu_descriptions_cold_02',key+'_menu_descriptions_final_02',','.join(actions),'--probe','snapshot'],check=True)
