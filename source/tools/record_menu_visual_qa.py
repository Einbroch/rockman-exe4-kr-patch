"""Manually inspected fixed route; never infer visual PASS from file existence."""
import json
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
report={'schema':1,'scope':'PET room label, folder1 and four save headings in both revisions',
 'inspection':'Codex directly inspected native screenshots and source-capture contact sheet; 2026-09-16',
 'language_review':'needs_review; no independent review',
 'font_direction':'functional Galmuri7 candidate with vertical shadow; human final approval pending',
 'not_claimed':['folder2 visibly reached','second save variant visibly reached','all menu scripts translated','all 4363 syllables game-screen verified','all font/width/count/name/battle consumers supported','whole-game or device QA'],
 'profiles':[]}
for key in ['blue_moon','red_sun']:
 root=p/'analysis/runtime'/f'{key}_menu_final_02';receipt=root/'result.json';r=json.loads(receipt.read_text(encoding='utf-8'))
 product=p/'poc/output'/f'{key}_opening_menu_korean_development.gba'
 if not r['complete'] or r['return_code']!=0 or r['rom_sha256']!=sha(product.read_bytes()) or r['steps_captured']!=107:raise ValueError('menu visual attribution failed')
 checks=[]
 for step,expected in [(92,['넷토의 방']),(93,['폴더1']),(102,['플레이 시간','데이터 도감','배틀칩','소지금'])]:
  f=root/f'step_{step:03d}.png'
  if sha(f.read_bytes())!=r['artifacts'][f.name]:raise ValueError('capture drift')
  checks.append({'capture':f.relative_to(p).as_posix(),'capture_sha256':sha(f.read_bytes()),'expected':expected,'manual_display_result':'PASS; visible with no clipping or colour blocks in this route'})
 report['profiles'].append({'profile':key,'rom_sha256':r['rom_sha256'],'runtime_receipt_sha256':sha(receipt.read_bytes()),'checks':checks,'native_compatibility':'Japanese chip names, status numbers, short NAME buffer, save prompt and icons remained visible'})
(p/'analysis/MENU_RUNTIME_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('manual menu route record written')
