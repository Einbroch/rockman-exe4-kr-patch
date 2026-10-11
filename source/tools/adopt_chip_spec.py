"""Adopt one bounded folder clone and split VRAM cache; no ROM writes."""
import argparse,json
from pathlib import Path
from analyze_project import PROFILES,sha,check_dependencies
from verify_tpi_index import parse_tpi
p=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);a=ap.parse_args()
out=p/'tools/specs/exe4_chip_folder_v1.json'
if out.exists():raise SystemExit('chip spec already adopted')
check_dependencies(p);rs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
profiles={};segments=[{'address':0x06006b80,'glyphs':18},{'address':0x06007360,'glyphs':6}]
for key,pr in PROFILES.items():
 r=rs[pr['sha256']];rows=parse_tpi(p/'external/textpet-indexes'/pr['index']);row=rows[41]
 root=p/'analysis/runtime'/f'{key}_chip_vram_writes_02';receipt=json.loads((root/'result.json').read_text(encoding='utf-8'))
 if not receipt['complete'] or receipt['return_code'] or receipt['steps_captured']!=8:raise ValueError('VRAM survey incomplete')
 for name,digest in receipt['artifacts'].items():
  if sha((root/name).read_bytes())!=digest:raise ValueError('VRAM survey artifact drift')
 events=json.loads((root/'final_vramwrites.json').read_text(encoding='utf-8'))
 for s in segments:
  lo=s['address'];hi=lo+s['glyphs']*64
  if any(lo<=0x06000000+x['tile']*32<hi for x in events['tiles']):raise ValueError('cache candidate has observed native writes')
  if any(c['destination']<hi and c['destination']+c['bytes']>lo for c in events['copies']):raise ValueError('cache candidate overlaps observed transfer')
 upload,parser,pointer,chooser,init=(0x2e9ac,0x2f084,0x2f090,0x2f030,0x2e994) if key=='blue_moon' else (0x2e9e4,0x2f0bc,0x2f0c8,0x2f068,0x2e9cc)
 if pointer not in row['pointers'] or int.from_bytes(r[pointer:pointer+4],'little')!=0x08000000+row['offset']:raise ValueError('folder clone literal is not claimed')
 anchors=[{'offset':at,'size':size,'sha256':sha(r[at:at+size])} for at,size in [(chooser,0x5c),(init,0xf0),(0x870,0x48)]]
 profiles[key]={'source_sha256':sha(r),'anchors':anchors,'chooser_entry':0x08000000+chooser,
  'upload_patch':{'offset':upload,'expected_hex':r[upload:upload+10].hex(),'continuation':0x08000000+upload+11},
  'parser_patch':{'offset':parser,'expected_hex':r[parser:parser+8].hex(),'continuation':0x08000000+parser+9},
  'clone_pointer':pointer,'original_archive_offset':row['offset'],'other_archive_claims_preserved':[x for x in row['pointers'] if x!=pointer],
  'native_font_address':0x0868e004 if key=='blue_moon' else 0x0868e224,
  'bounded_VRAM_receipt_sha256':sha((root/'result.json').read_bytes())}
spec={'schema':1,'scope':'initial ten chip names in private folder chooser clone only; other consumers retain original archive41',
 'font_sha256':'26321b2d780b859bfee7ca6cc561b50268efed139a852b470a589c0ba9901b24','profiles':profiles,'segments':segments,
 'queue_helper':0x08000871,'glyph_bytes':64,'native_tile_base':512,'max_hangul_cells':8,
 'cache_lifetime':'upload after native160-glyph enqueue at each folder initialization; survives observed edit and scrolling; runtime regression still required',
 'open':['other menu/battle/name consumers','whole-game and physical device QA','font and language approval'],
 'rejected_candidate':'06006800 begins seven dynamic128-byte chip images; never allocate a Hangul bank there',
 'IO_evidence_policy':'raw Lua byte reads of display IO are not adopted as PPU register evidence; use actual tilemap/pixel consumption'}
out.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
deps=p/'analysis/dependencies.json';d=json.loads(deps.read_text(encoding='utf-8'));d['files'].append({'path':out.relative_to(p).as_posix(),'sha256':sha(out.read_bytes())});deps.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print('adopted two split cache segments; only one folder archive literal per revision')
