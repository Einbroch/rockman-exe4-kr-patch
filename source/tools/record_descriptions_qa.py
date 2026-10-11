"""Bind inspected description windows to exact drafts, font reads and cold lineage."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
def proof(path):return {'path':path.relative_to(p).as_posix(),'sha256':sha(path.read_bytes())}
def receipt(root,digest,steps=None):
 r=json.loads((root/'result.json').read_text(encoding='utf-8'))
 if not r['complete'] or r['return_code'] or r['rom_sha256']!=digest or r['steps_expected']!=r['steps_captured'] or steps is not None and r['steps_captured']!=steps:raise ValueError('description receipt invalid')
 for name,d in r['artifacts'].items():
  if sha((root/name).read_bytes())!=d:raise ValueError('description runtime artifact drift '+name)
 return r
draft=json.loads((p/'translations/chip_descriptions_korean_draft.json').read_text(encoding='utf-8'))
names={int(x['id'].split('/')[-1]):x['text'] for x in draft['entries']}
vp=p/'analysis/descriptions_verification.json';v=json.loads(vp.read_text(encoding='utf-8'))
report={'schema':1,'status':'PASS bounded runtime and direct visual inspection',
 'scope':'four natural chip descriptions, repeated opening/closing, existing caption preservation; ten drafts compiled',
 'verification':proof(vp),'reviewer':'Codex native-resolution screenshot inspection, 2026-09-19','profiles':{},
 'not_claimed':['all ten descriptions naturally shown','other description consumers localized','whole-game/device QA','independent language/font approval']}
shots=[]
for key in ['blue_moon','red_sun']:
 target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
 digest=sha(target.read_bytes());m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
 if digest!=m['output_sha256'] or digest!=v['profiles'][key]['rom_sha256']:raise ValueError('description runtime product drift')
 final=p/'analysis/runtime'/f'{key}_descriptions_final_01';reads=p/'analysis/runtime'/f'{key}_descriptions_reads_01'
 fr=receipt(final,digest,16);rr=receipt(reads,digest,16)
 if fr['state_origin']!=rr['state_origin'] or fr['state_sha256']!=rr['state_sha256'] or fr['actions']!=rr['actions']:raise ValueError('description probes not from same state/actions')
 lineage=[];root=final
 while True:
  r=receipt(root,digest);lineage.append(proof(root/'result.json'))
  if r['state_origin'] is None:break
  origin=Path(r['state_origin'])
  if r['state_sha256']!=sha((origin.parent/'checkpoint.mss').read_bytes()):raise ValueError('description checkpoint lineage drift')
  root=origin.parent
 if root.name!=key+'_descriptions_cold_01':raise ValueError('description lineage not cold')
 checks=[];observed=set()
 for before,opened,closed,chip_id in [(1,2,3,1),(4,5,6,29),(8,9,10,48),(11,12,13,107),(14,15,16,48)]:
  def counts(step):return {x['index']:x['reads'] for x in json.loads((reads/f'step_{step:03d}_fontread.json').read_text())['records']}
  a,b=counts(before),counts(opened)
  seen={chr(i+0xac00) for i,n in b.items() if n>a.get(i,0)}
  wanted={c for c in names[chip_id] if 0xac00<=ord(c)<=0xd7a3}
  if seen!=wanted:raise ValueError(f'actual Hangul reads differ {key} {chip_id}: {seen^wanted}')
  observed|=seen
  captions=[];evidence=[]
  for step in [before,opened,closed]:
   vr=final/f'step_{step:03d}_gbaVideoRam.bin';captions.append(vr.read_bytes()[0x9380:0x9580]);evidence.append(proof(vr))
  if captions[0]!=captions[1] or captions[1]!=captions[2]:raise ValueError('description window overwrites highlighted chip caption')
  shot=final/f'step_{opened:03d}.png';close_shot=final/f'step_{closed:03d}.png'
  shots.append((key,chip_id,shot))
  checks.append({'source_id':chip_id,'text':names[chip_id],'open_step':opened,'close_step':closed,
   'Hangul_read_set':sorted(seen),'screenshot':proof(shot),'closed_screenshot':proof(close_shot),
   'VRAM_before_open_closed':evidence,'fontread_before':proof(reads/f'step_{before:03d}_fontread.json'),
   'fontread_open':proof(reads/f'step_{opened:03d}_fontread.json'),'caption_preserved_bytes':512})
 report['profiles'][key]={'rom_sha256':digest,'natural_source_ids':[1,29,48,107],
  'Hangul_syllables_actually_read':len(observed),'checks':checks,'lineage':lineage,
  'receipts':[proof(final/'result.json'),proof(reads/'result.json')]}
sheet=Image.new('RGB',(240*5,180*2),'white');draw=ImageDraw.Draw(sheet)
for i,(key,chip_id,shot) in enumerate(shots):
 x=i%5*240;y=i//5*180;draw.text((x+3,y+3),key+' ID '+str(chip_id),fill='black');sheet.paste(Image.open(shot).convert('RGB'),(x,y+20))
dest=p/'analysis/visual_qa/descriptions_two_versions_01.png';sheet.save(dest);report['sheet']=proof(dest)
report['tool_sha256']=sha(Path(__file__).read_bytes())
(p/'analysis/DESCRIPTIONS_RUNTIME_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS both versions: four natural descriptions, exact Hangul read sets, ten open/close cases, caption preservation')
