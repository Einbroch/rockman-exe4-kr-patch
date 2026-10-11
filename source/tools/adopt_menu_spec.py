"""One-time source survey/adoption, not invoked by product builds."""
import argparse,json
from pathlib import Path
from analyze_project import PROFILES,sha,check_dependencies
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);a=ap.parse_args()
p=Path(__file__).resolve().parents[1];check_dependencies(p)
rs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
b=rs[PROFILES['blue_moon']['sha256']]
spec={'schema':1,'scope':'two observed shared tile font styles; not all menu/battle/name consumers',
 'evidence':['runtime/blue_moon_menu_survey_09/step_008_exectrace.json','runtime/blue_moon_menu_survey_10/step_008_exectrace.json'],
 'font_sha256':'26321b2d780b859bfee7ca6cc561b50268efed139a852b470a589c0ba9901b24',
 'font_direction':'functional Galmuri7 with vertical shadow; human visual approval pending','profiles':{}}
for key,pr in PROFILES.items():
 r=rs[pr['sha256']];fonts=[]
 for at,bg,ink,shadow in [(0x68e004,0,1,2),(0x6c699c,1,3,4)]:
  blob=b[at:at+441*64];found=r.find(blob)
  if found<0 or r.find(blob,found+1)>=0:raise ValueError('font source not unique')
  fonts.append({'source_address':0x08000000+found,'size':len(blob),'sha256':sha(blob),'background':bg,'ink':ink,'shadow':shadow})
 spec['profiles'][key]={'source_sha256':sha(r),'slot':{'offset':0x213650,'expected_hex':r[0x213650:0x213654].hex(),'legacy_handler':0x0300692d},
  'renderer_runtime':0x030067f1,'source_code_offset':0x21367c,'source_code_size':0x29a,
  'source_code_sha256':sha(r[0x21367c:0x213916]),'fonts':fonts}
out=p/'tools/specs/exe4_menu_extension_v1.json';out.write_text(json.dumps(spec,indent=2),encoding='utf-8')
deps=json.loads((p/'analysis/dependencies.json').read_text(encoding='utf-8'))
entry={'path':out.relative_to(p).as_posix(),'sha256':sha(out.read_bytes())}
if any(x['path']==entry['path'] for x in deps['files']):raise ValueError('already adopted; reassess explicitly')
deps['files'].append(entry);deps['menu_font']={'name':'Galmuri7.bdf','sha256':spec['font_sha256'],'version':'2.24.29','license':'SIL OFL 1.1'}
(p/'analysis/dependencies.json').write_text(json.dumps(deps,indent=2),encoding='utf-8')
print({k:[hex(f['source_address']) for f in v['fonts']] for k,v in spec['profiles'].items()})
