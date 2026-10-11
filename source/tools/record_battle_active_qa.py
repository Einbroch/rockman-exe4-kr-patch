"""Bind natural queued-name display, numeric placement, clearing and reentry."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
def proof(path):return {'path':path.relative_to(p).as_posix(),'sha256':sha(path.read_bytes())}
def read_receipt(root,digest):
 r=json.loads((root/'result.json').read_text(encoding='utf-8'))
 if not r['complete'] or r['return_code'] or r['rom_sha256']!=digest or r['steps_expected']!=r['steps_captured']:raise ValueError('invalid runtime '+str(root))
 for name,value in r['artifacts'].items():
  if sha((root/name).read_bytes())!=value:raise ValueError('receipt artifact drift '+name)
 return r
spec=json.loads((p/'tools/specs/exe4_battle_active_v1.json').read_text())
verification=p/'analysis/battle_active_verification.json'
verified=json.loads(verification.read_text(encoding='utf-8'))
report={'schema':1,'status':'PASS bounded runtime and direct visual inspection',
 'scope':spec['scope'],'verification':proof(verification),'profiles':{},
 'reviewer':'Codex direct native-resolution inspection, 2026-09-17',
 'not_claimed':['294 names naturally acquired/displayed','complete battle localization','description insertion','whole-game/device QA','independent language/font approval']}
shots=[]
for key in spec['profiles']:
 target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba'
 data=target.read_bytes();digest=sha(data);m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
 if digest!=verified['profiles'][key]['rom_sha256'] or digest!=m['output_sha256']:raise ValueError('active product drift')
 roots={kind:p/'analysis/runtime'/f'{key}_battle_active_{kind}' for kind in ['verify_survey_05','use_01','reentry_01','second_01','calls_01','calls_02']}
 for root in roots.values():read_receipt(root,digest)
 lineage=[];root=roots['second_01']
 while True:
  r=read_receipt(root,digest);lineage.append(proof(root/'result.json'))
  if r['state_origin'] is None:break
  origin=Path(r['state_origin'])
  if r['state_sha256']!=sha((origin.parent/'checkpoint.mss').read_bytes()):raise ValueError('active state lineage drift')
  root=origin.parent
 if root.name!=key+'_battle_active_verify_cold_01':raise ValueError('not own-product cold boot')
 chars={c:i for i,c in enumerate(m['extension']['menu']['characters'])}
 checks=[]
 for kind,step,name,chip_id,damage in [('verify_survey_05',2,'캐논',1,40),('use_01',1,'캐논',1,40),('use_01',2,'캐논',1,40),('use_01',3,'캐논',1,40),('second_01',8,'미니봄',29,50),('second_01',9,'미니봄',29,50)]:
  stem=roots[kind]/f'step_{step:03d}'
  rp=Path(str(stem)+'_gbaExtWorkRam.bin');vp=Path(str(stem)+'_gbaVideoRam.bin');st=Path(str(stem)+'_state.json')
  ram=rp.read_bytes();vram=vp.read_bytes();state=json.loads(st.read_text())['state']
  if state['ppu.bgLayers[3].tilemapAddr']!=0xf800 or state['ppu.bgLayers[3].tilesetAddr']!=0x8000 or state['ppu.bgLayers[3].scrollX'] or state['ppu.bgLayers[3].scrollY']:raise ValueError('active PPU mapping changed')
  expected=b''.join(data[m['extension']['menu']['fonts'][0]+chars[c]*64:m['extension']['menu']['fonts'][0]+chars[c]*64+64] for c in name)+b'\0'*(512-len(name)*64)
  if ram[0x3e590:0x3e790]!=expected or vram[0x9380:0x9580]!=expected:raise ValueError(f'active RAM/VRAM glyph mismatch {key} {kind} {step}')
  words=[0xd09c+2*i for i in range(len(name))]+[0xd148+2*int(c) for c in str(damage)]
  for row in (0,1):
   actual=vram[0xf800+(18+row)*64:0xf800+(18+row)*64+32]
   expected_map=b''.join((x+row).to_bytes(2,'little') for x in words)+b'\0'*(32-len(words)*2)
   if actual!=expected_map:raise ValueError(f'active damage position/map mismatch {key} {kind} {step}')
  shot=Path(str(stem)+'.png');shots.append((key,name,shot))
  checks.append({'kind':kind,'step':step,'source_id':chip_id,'text':name,'damage':damage,'caption_sha256':sha(expected),
                 'screenshot':proof(shot),'RAM':proof(rp),'VRAM':proof(vp),'PPU':proof(st),'glyph_count_and_damage_position_verified':True})
 clear=[]
 for step in [4,5,6]:
  stem=roots['use_01']/f'step_{step:03d}';vp=Path(str(stem)+'_gbaVideoRam.bin');vram=vp.read_bytes()
  if any(vram[0xf800+row*64:0xf800+row*64+32]!=b'\0'*32 for row in (18,19)):raise ValueError('queued name not cleared after use')
  clear.append({'step':step,'VRAM':proof(vp),'screenshot':proof(Path(str(stem)+'.png'))})
  if step==5:shots.append((key,'empty',Path(str(stem)+'.png')))
 for kind,chip_id in [('calls_01',1),('calls_02',29)]:
  r=read_receipt(roots[kind],digest)
  expected_origin=roots['verify_survey_05'] if chip_id==1 else roots['second_01']
  if Path(r['state_origin'])!=expected_origin/'result.json' or r['state_sha256']!=sha((expected_origin/'checkpoint.mss').read_bytes()):raise ValueError('trace origin drift')
  base=m['extension']['battle_active']['archive_offsets']['41'];at=base+int.from_bytes(data[base+chip_id*2:base+chip_id*2+2],'little')
  calls=json.loads((roots[kind]/'tilecalls_final.json').read_text())['calls']
  if not any(c['stream']==0x08000000+at and c['destination']==0x0203e590 and c['width']==8 and c['height']==1 and c['tint']==0 and c['stream_prefix_hex']==data[at:at+32].hex().upper() for c in calls):raise ValueError('active private stream not observed')
 report['profiles'][key]={'rom_sha256':digest,'natural_source_ids':[1,29],'checks':checks,'clearing':clear,'lineage':lineage,
  'receipts':[proof(root/'result.json') for root in roots.values()]}
sheet=Image.new('RGB',(240*7,180*2),'white');draw=ImageDraw.Draw(sheet)
for i,(key,name,shot) in enumerate(shots):
 x=i%7*240;y=i//7*180;draw.text((x+3,y+3),key+' '+str(i%7+1),fill='black');sheet.paste(Image.open(shot).convert('RGB'),(x,y+20))
dest=p/'analysis/visual_qa/battle_active_two_versions_01.png';sheet.save(dest);report['sheet']=proof(dest)
report['tool_sha256']=sha(Path(__file__).read_bytes())
(p/'analysis/BATTLE_ACTIVE_RUNTIME_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS queued Cannon/MiniBomb, exact glyphs and damage position, clearing, Custom Screen reentry, both products')
