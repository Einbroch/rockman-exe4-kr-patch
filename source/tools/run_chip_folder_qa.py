"""Owned muted Mesen cold boot and same-product folder inventory/edit regression."""
import argparse,ast,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True);a=ap.parse_args()
# Reuse the established ordinary-input route, without importing its run loop.
tree=ast.parse((p/'tools/run_menu_qa.py').read_text(encoding='utf-8'));nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 if isinstance(n,(ast.Assign,ast.AugAssign)) and isinstance(n.targets[0] if isinstance(n,ast.Assign) else n.target,ast.Name) and (n.targets[0] if isinstance(n,ast.Assign) else n.target).id=='actions':nodes.append(n)
scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'established_menu_actions','exec'),scope);actions=scope['actions']
rom=p/'poc/output'/f'{a.key}_opening_menu_chip_folder_korean_development.gba';data=rom.read_bytes();m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'))
chip=m['extension']['chip_folder'];pc=chip['machine_code'][1]['address']+6
def run(out,actions,probe,origin=None):
 c=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),'--mesen','C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe','--out',str(out),'--expect-rom-sha256',m['output_sha256'],'--actions',','.join(actions),'--probe',probe,'--trace-pc',hex(pc),'--timeout','360']
 if origin:c+=['--state',str(origin.parent/'checkpoint.mss'),'--state-origin',str(origin),'--watch-start','0x06006b80','--watch-end','0x060077ff']
 for at,size in [(0xa0,32),(0x800000,16)]+[(w['offset'],min(w['size'],10)) for w in m['expected_writes'] if w['offset']<0x800000]:c+=['--guard',f'{at}:'+data[at:at+size].hex()]
 print(a.key,out.name,'actions',len(actions),flush=True);subprocess.run(c,check=True)
cold=p/'analysis/runtime'/f'{a.key}_chip_folder_cold_01'
run(cold,actions,'chipcalls')
folder=['a:6:120']+['down:6:30']*30+['a:6:120','a:6:120','b:6:60','b:6:60','start:6:120','start:6:120','a:6:120']
run(p/'analysis/runtime'/f'{a.key}_chip_folder_final_01',folder,'chipqa',cold/'result.json')
