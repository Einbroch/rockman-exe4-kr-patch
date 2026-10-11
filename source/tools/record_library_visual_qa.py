"""Manual source survey observations after inspecting library contact sheet."""
import json
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1];report=p/'analysis/library_consumer_analysis.json';r=json.loads(report.read_text(encoding='utf-8'));checks=[]
for key in r['profiles']:
 for kind,step in [('source',3),('source',6),('bg',7)]:
  root=p/'analysis/runtime'/f'{key}_library_{kind}_survey_01';f=root/f'step_{step:03d}.png'
  checks.append({'profile':key,'capture':f.relative_to(p).as_posix(),'sha256':sha(f.read_bytes()),'receipt':(root/'result.json').relative_to(p).as_posix(),'receipt_sha256':sha((root/'result.json').read_bytes()),'observation':'native standard names cannon/air-shot/vulcan1 and question-mark rows, chip image/description and10/150 count visible' if kind=='source' and step==3 else 'native mega tab shows question-mark rows,0/60 count and empty chip panel' if kind=='source' else 'standard tab return preserves Japanese names/question marks/digits; selected unregistered row has an empty image panel'})
sheet=p/'analysis/visual_qa/library_source_two_versions.png';record={'schema':1,'status':'manual bounded native-library survey inspection recorded','reviewer':'Codex direct native-resolution image inspection,2026-09-16','analysis_sha256':sha(report.read_bytes()),'sheet_sha256':sha(sheet.read_bytes()),'checks':checks,'not_claimed':['Korean library rendering','all chip names/PA/battle/name-input QA','font or independent language approval']}
(p/'analysis/LIBRARY_SOURCE_RUNTIME_QA.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print('six native library screenshots: manual source observations recorded')
