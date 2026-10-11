"""Manual record after direct inspection of the six diagnostic contact images."""
import json
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1];profiles=[]
for key in ['blue_moon','red_sun']:
 root=p/'analysis/runtime'/f'{key}_folder_chip_inventory_01'
 checks=[]
 for step in [1,12,24]:
  f=root/f'step_{step:03d}.png'
  checks.append({'capture':f.relative_to(p).as_posix(),'sha256':sha(f.read_bytes()),'observation':'original Japanese chip names, chip codes, icons, size numbers and purple/red profile styling remain visible; translated folder1 heading remains visible'})
 profiles.append({'profile':key,'runtime_receipt_sha256':sha((root/'result.json').read_bytes()),'checks':checks})
sheet=p/'analysis/visual_qa/chip_consumer_two_versions.png'
record={'schema':1,'status':'manual bounded diagnostic inspection recorded','reviewer':'Codex direct image inspection, 2026-09-16',
 'scope':'six source-chip screenshots at steps1/12/24, both revisions; no Korean chip raster is present or approved',
 'sheet_sha256':sha(sheet.read_bytes()),'profiles':profiles,
 'not_claimed':['all10names visually inspected','actual battle-screen QA','actual name-input or save QA','independent language review or final Hangul font approval']}
(p/'analysis/CHIP_CONSUMER_RUNTIME_QA.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print('six diagnostic images: manual preservation observations recorded')
