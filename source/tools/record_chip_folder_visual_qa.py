"""Manual observations: run only after directly inspecting both contact sheets."""
import json
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1];verification=p/'analysis/chip_verification.json';v=json.loads(verification.read_text(encoding='utf-8'))
groups={1:[1,4],5:[4,15,29],12:[29,48],17:[48,49,91],24:[107,117,149]};profiles=[]
for item in v['profiles']:
 if not item['runtime_status'].startswith('completed'):raise ValueError('bounded runtime incomplete')
 key=item['profile'];checks=[]
 for kind,step in [('final',i) for i in groups]+[('cold',107),('final',33),('final',35),('final',38)]:
  root=p/'analysis/runtime'/f'{key}_chip_folder_{kind}_01';receipt=root/'result.json';r=json.loads(receipt.read_text(encoding='utf-8'));f=root/f'step_{step:03d}.png'
  if not r['complete'] or r['return_code'] or r['rom_sha256']!=item['rom_sha256'] or sha(f.read_bytes())!=r['artifacts'][f.name]:raise ValueError('visual capture attribution drift')
  observation='listed Korean draft chip names are visible within the eight-cell row; native chip icons, codes, capacity digits, folder1 heading and profile colors remain visible'
  if kind=='cold' or step==35:observation='PET returns with native NAME/digits/menu icons and translated place label visible; no obvious raster corruption in this capture'
  elif step==33:observation='folder edit shows Korean chip list/folder1 heading, original enlarged chip image and Japanese chip description, and native count/code digits'
  elif step==38:observation='folder reentry shows Korean cannon/air-shot rows and original chip icons, codes and capacity digits'
  checks.append({'capture':f.relative_to(p).as_posix(),'sha256':sha(f.read_bytes()),'runtime_receipt':receipt.relative_to(p).as_posix(),'runtime_receipt_sha256':sha(receipt.read_bytes()),'chip_script_ids':groups.get(step,[]),'observation':observation})
 profiles.append({'profile':key,'rom_sha256':item['rom_sha256'],'checks':checks,'distinct_chip_script_ids_visually_inspected':sorted({id for x in groups.values() for id in x})})
names=['chip_folder_two_versions','chip_folder_regression_two_versions'];sheets={f'analysis/visual_qa/{name}.png':sha((p/'analysis/visual_qa'/(name+'.png')).read_bytes()) for name in names}
record={'schema':1,'status':'manual bounded development inspection recorded','reviewer':'Codex direct native-resolution image inspection, 2026-09-16','scope':'ten draft chip names in both folder lists, edit screen, PET return and reentry; 18 captures','verification_sha256':sha(verification.read_bytes()),'sheets':sheets,'profiles':profiles,'not_claimed':['human final font/style approval','independent Japanese-to-Korean language review','all chip names or all folder states','battle/library chip consumers','NAME input/save/communication/device QA','whole-game translation or release']}
(p/'analysis/CHIP_FOLDER_RUNTIME_QA.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print('18 captures, both revisions, 10 draft names: bounded manual observations recorded')
