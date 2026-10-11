"""One-time explicit scope adoption; does not construct a ROM or translate text."""
import argparse,json
from pathlib import Path
from analyze_project import PROFILES,sha,check_dependencies
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);a=ap.parse_args()
out=p/'tools/specs/exe4_consumer_contracts_v1.json'
if out.exists():raise SystemExit('consumer contract already adopted; do not auto-promote translation input')
check_dependencies(p)
rs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
# Explicit finite allowlist. Other scripts in these same archives are NOT
# approved merely because their neighbor has an adopted renderer.
approved=[(ai,si,'shared-tile-save',None) for ai in (1,2) for si in range(6,10)]
approved += [(5,0,'shared-tile-and-normal-folder',64),(5,1,'shared-tile-and-normal-folder',64),(13,3,'shared-tile-place',None)]
rows=[];profiles={}
for key,pr in PROFILES.items():
 r=rs[pr['sha256']]
 es={e['id']:e for e in (json.loads(x) for x in (p/'analysis'/f'{key}_source_entries.jsonl').read_text(encoding='utf-8').splitlines())}
 current=[]
 for ai,si,consumer,cap in approved:
  identity=f'archive/{ai:03}/script/{si}';e=es[identity]
  if e['source_rom_sha256']!=sha(r) or e['language']!='mmbn4s' or len(e['source_literals'])!=1:raise ValueError('adoption source drift')
  current.append({'id':identity,'source':e['source_literals'][0],'consumer':consumer,'max_cells':len(e['source_literals'][0]),'max_encoded_bytes':cap})
 if rows and current!=rows:raise ValueError('supported entries differ by revision')
 rows=current
 start=0x2f4ac if key=='blue_moon' else 0x2f4e4
 anchors=[]
 for at,size,role in [(0x21367c,0x29a,'shared tile parser'),(start,0x36,'unsupported folder chip tilemap parser'),(0x21382c,0x28,'native three-byte NAME consumer')]:
  anchors.append({'offset':at,'size':size,'sha256':sha(r[at:at+size]),'role':role})
 profiles[key]={'source_sha256':sha(r),'anchors':anchors,'unsupported_chip_parser_entry':0x08000000+start}
contract={'schema':1,'scope':'11 adopted short scripts only; whole-game decoder closure pending',
 'supported_entries':rows,'profiles':profiles,
 'unsupported_consumers':{
  'archive/041':'folder chip names use a BG tilemap parser, not the shared raster parser; F9 >= E5 terminates; VRAM glyph allocation/other callers remain open',
  'NAME':'three single-byte glyph indexes from a 32-bit packed value; four-byte F9FC stream is not supported; save producer and menu name input remain to be extended',
  'all_other_short_scripts':'requires explicit producer/decoder/buffer/font evidence before adoption'},
 'evidence':['analysis/menu_bench.json','analysis/MENU_RUNTIME_QA.json','analysis/runtime/blue_moon_chip_textread_01/result.json','analysis/runtime/red_sun_chip_textread_01/result.json','analysis/runtime/blue_moon_name_trace_01/result.json'],
 'policy':'fail before compiler or ROM output for unclassified selection; no silent partial name'}
out.write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding='utf-8')
deps=p/'analysis/dependencies.json';d=json.loads(deps.read_text(encoding='utf-8'));d['files'].append({'path':out.relative_to(p).as_posix(),'sha256':sha(out.read_bytes())});deps.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('adopted 11 explicit entries; chip and NAME consumers remain unsupported')
