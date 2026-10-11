"""Owned muted cold boot and same-product library/folder cache regression."""
import argparse,ast,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True);a=ap.parse_args()
tree=ast.parse((p/'tools/run_menu_qa.py').read_text(encoding='utf-8'));nodes=[]
for n in tree.body:
 if isinstance(n,ast.For):break
 if isinstance(n,(ast.Assign,ast.AugAssign)) and isinstance(n.targets[0] if isinstance(n,ast.Assign) else n.target,ast.Name) and (n.targets[0] if isinstance(n,ast.Assign) else n.target).id=='actions':nodes.append(n)
scope={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'established_menu_actions','exec'),scope);cold_actions=scope['actions']
rom=p/'poc/output'/f'{a.key}_opening_menu_chip_folder_library_korean_development.gba';data=rom.read_bytes();m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'));library=m['extension']['chip_library'];pc=library['machine_code'][0]['address']
def run(out,actions,probe,origin=None):
 c=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),'--mesen','C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe','--out',str(out),'--expect-rom-sha256',m['output_sha256'],'--actions',','.join(actions),'--probe',probe,'--trace-pc',hex(pc),'--timeout','360']
 if origin:c+=['--state',str(origin.parent/'checkpoint.mss'),'--state-origin',str(origin),'--watch-start',hex(library['cache']['start']),'--watch-end',hex(library['cache']['reserved_end']-1)]
 guards=[(0xa0,32),(0x800000,16),(library['archive_offsets']['41'],16),(library['archive_offsets']['42'],16),(library['machine_code'][0]['address']-0x08000000,16)]
 guards += [(w['offset'],min(w['size'],12)) for w in m['expected_writes'] if w['offset']<0x800000]
 for at,size in guards:c+=['--guard',f'{at}:'+data[at:at+size].hex()]
 print(a.key,out.name,'actions',len(actions),flush=True);subprocess.run(c,check=True)
cold=p/'analysis/runtime'/f'{a.key}_library_cold_02';run(cold,cold_actions,'chipcalls')
actions=['down:6:30','down:6:30','a:6:120','none:1:60']+['down:6:30']*9+['right:6:60','left:6:60','b:6:60','up:6:30','up:6:30','a:6:120','none:1:60','b:6:60','down:6:30','down:6:30','a:6:120','none:1:60']
run(p/'analysis/runtime'/f'{a.key}_library_final_02',actions,'chipqa',cold/'result.json')
