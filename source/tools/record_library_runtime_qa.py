"""Bind adopted library runtime receipts, pixels, palettes and manual images."""
import json
from pathlib import Path
from analyze_project import PROFILES,sha
p=Path(__file__).resolve().parents[1];spec=json.loads((p/'tools/specs/exe4_chip_library_v1.json').read_text(encoding='utf-8'));draft=json.loads((p/'translations/chip_catalog_korean_draft.json').read_text(encoding='utf-8'));wording={x['chip_id']:x['text'] for x in draft['entries']};profiles={}
for key in PROFILES:
 rom_path=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_korean_development.gba';rom=rom_path.read_bytes();m=json.loads(rom_path.with_suffix('.json').read_text(encoding='utf-8'));library=m['extension']['chip_library'];menu=m['extension']['menu'];s=spec['profiles'][key]
 receipts=[]
 for kind,steps in [('cold',107),('final',25)]:
  root=p/'analysis/runtime'/f'{key}_library_{kind}_02';receipt=root/'result.json';r=json.loads(receipt.read_text(encoding='utf-8'))
  if not r['complete'] or r['return_code'] or r['steps_captured']!=r['steps_expected'] or r['steps_captured']!=steps or r['rom_sha256']!=sha(rom) or r['audio_enabled']:raise ValueError('library runtime receipt drift')
  for name,digest in r['artifacts'].items():
   if sha((root/name).read_bytes())!=digest:raise ValueError('library runtime artifact drift')
  receipts.append({'kind':kind,'path':receipt.relative_to(p).as_posix(),'sha256':sha(receipt.read_bytes()),'steps':steps})
 root=p/'analysis/runtime'/f'{key}_library_final_02';calls=json.loads((root/'chipcalls_final.json').read_text(encoding='utf-8'))['calls'];copies=json.loads((root/'final_vramwrites.json').read_text(encoding='utf-8'))['copies'];root41=s['roots']['41']['address'];actual={c['script_id'] for c in calls if c['archive']==root41}
 if not {1,4,15}<=actual:raise ValueError('all registered translated library IDs not reached')
 expected_jobs=set()
 for c in calls:
  if c['archive']!=root41 or c['script_id'] not in (1,4,15):continue
  row=(c['destination']-spec['upper_row_base'])//spec['row_stride']
  if not 0<=row<7 or c['destination']!=spec['upper_row_base']+row*32 or c['lower_row']!=c['destination']+16 or c['tile_base']!=spec['palette_tile_base']:raise ValueError('actual library ABI drift')
  for col,char in enumerate(wording[c['script_id']]):
   if not 0xac00<=ord(char)<=0xd7a3:continue
   cp=ord(char)-0xac00;ordinal=int.from_bytes(rom[menu['map_offset']+cp*2:menu['map_offset']+cp*2+2],'little')
   expected_jobs.add((0x08000000+menu['fonts'][0]+ordinal*64,spec['cache']['start']+(row*8+col)*64,64))
 observed={(x['source'],x['destination'],x['bytes']) for x in copies}
 if not expected_jobs<=observed:raise ValueError('actual library glyph copy jobs incomplete')
 chars=menu['characters'];bank=menu['fonts'][0];glyphs={rom[bank+i*64:bank+(i+1)*64]:c for i,c in enumerate(chars)}
 reconstructed={}
 for step in (4,8,13,25):
  ram=(root/f'step_{step:03d}_gbaExtWorkRam.bin').read_bytes();vram=(root/f'step_{step:03d}_gbaVideoRam.bin').read_bytes();rows=[]
  for row in range(7):
   text='';korean=0
   for col in range(8):
    tile=int.from_bytes(ram[0x16600+row*32+col*2:0x16602+row*32+col*2],'little');expected=spec['cache']['top_tile_first']+(row*8+col)*2
    if tile&0x3ff==expected:
     if tile&0xfc00!=spec['palette_tile_base']&0xfc00:raise ValueError('actual Korean palette bits lost')
     glyph=vram[spec['cache']['start']-0x06000000+(row*8+col)*64:spec['cache']['start']-0x06000000+(row*8+col+1)*64]
     if glyph not in glyphs:raise ValueError('actual cache glyph not in adopted menu bank')
     text+=glyphs[glyph];korean+=1
   rows.append(text)
  reconstructed[str(step)]=rows
 if reconstructed['4'][3]!='에어슛' or reconstructed['4'][4]!='발칸' or reconstructed['25'][3]!='에어슛' or reconstructed['25'][4]!='발칸':raise ValueError('visible/reentry library Korean rows drift')
 for step in (4,25):
  ram=(root/f'step_{step:03d}_gbaExtWorkRam.bin').read_bytes()
  if int.from_bytes(ram[0x16600+4*32+4:0x16600+4*32+6],'little')!=0xe204:raise ValueError('visible native digit palette/tile drift')
 screenshots=[]
 for step,observation in [(4,'standard tab displays Korean registered names including Cannon, AirShoot and Vulcan1;10/150 visible'),(13,'standard list scroll reached numbers4-10 without corruption'),(14,'mega tab0/60 and unknown rows remain intact'),(20,'folder screen retains its Korean ten-name cache after library use'),(25,'standard library reentry restores Korean per-cell glyph cache')]:
  f=root/f'step_{step:03d}.png';screenshots.append({'path':f.relative_to(p).as_posix(),'sha256':sha(f.read_bytes()),'observation':observation})
 profiles[key]={'rom_sha256':sha(rom),'receipts':receipts,'actual_registered_source_ids':sorted(actual&{1,4,15}),'expected_glyph_copy_jobs_observed':len(expected_jobs),'reconstructed_Korean_rows':reconstructed,'screenshots':screenshots}
sheet=p/'analysis/visual_qa/library_korean_two_versions_02.png'
report={'schema':1,'status':'PASS; bounded runtime and direct native-resolution visual inspection','scope':'two exact development ROMs; cold boot, standard/mega library, registered IDs1/4/15, scroll, folder collision and library reentry; CPU bench separately covers IDs0..310 and all294 drafts','reviewer':'Codex direct native-resolution image inspection,2026-09-16','sheet':sheet.relative_to(p).as_posix(),'sheet_sha256':sha(sheet.read_bytes()),'profiles':profiles,'not_claimed':['all294 names naturally visible in this save','independent Korean language approval','final font styling approval','RAM-special IDs >=311','battle/name-input/whole-game/device QA']}
(p/'analysis/LIBRARY_RUNTIME_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('library bounded runtime QA PASS; two revisions; cold107+final25 each')
