"""Bind native library consumer, residency and CPU counterproof to owned runs."""
import argparse,json,subprocess,sys
from pathlib import Path
from analyze_project import PROFILES,sha,check_dependencies,payload
from verify_tpi_index import parse_tpi
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'external/arm_debug_python'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
p=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);a=ap.parse_args();check_dependencies(p)
rs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')};records={};bodies=[]
c=[sys.executable,str(p/'tools/test_library_consumer.py')];r=subprocess.run(c,capture_output=True);log=p/'analysis/library_consumer_bench.log';log.write_bytes(r.stdout+r.stderr)
if r.returncode:raise SystemExit('native library CPU counterproof failed')
for key,pr in PROFILES.items():
 source=rs[pr['sha256']];rows=parse_tpi(p/'external/textpet-indexes'/pr['index']);parser=0x08038030 if key=='blue_moon' else 0x08038064;at=parser-0x08000000;body=source[at:at+52];bodies.append(body)
 instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(body,parser))
 if len(instructions)!=26 or any(x.size!=2 for x in instructions):raise ValueError('native library whole-function boundaries drift')
 receipts={};product=p/'poc/output'/f'{key}_opening_menu_korean_development.gba';data=product.read_bytes()
 for label,steps in [('source',6),('bg',8),('ppu',2)]:
  root=p/'analysis/runtime'/f'{key}_library_{label}_survey_01';receipt=root/'result.json';rt=json.loads(receipt.read_text(encoding='utf-8'))
  if not rt['complete'] or rt['return_code'] or rt['steps_captured']!=rt['steps_expected'] or rt['steps_captured']!=steps or rt['rom_sha256']!=sha(data) or rt['audio_enabled']:raise ValueError('library receipt attribution drift')
  for name,digest in rt['artifacts'].items():
   if sha((root/name).read_bytes())!=digest:raise ValueError('library runtime artifact drift')
  receipts[label]={'receipt':receipt.relative_to(p).as_posix(),'sha256':sha(receipt.read_bytes()),'steps':steps,'rom_sha256':sha(data)}
 root=p/'analysis/runtime'/f'{key}_library_bg_survey_01';calls=json.loads((root/'bgcalls_final.json').read_text(encoding='utf-8'))['calls'];jobs=json.loads((root/'final_vramwrites.json').read_text(encoding='utf-8'))['copies']
 if not calls or {x['pc'] for x in calls}!={parser} or any(x['lower_row']-x['destination']!=16 for x in calls):raise ValueError('actual library ABI drift')
 if {x['tile_base_palette'] for x in calls}!={0xe200}:raise ValueError('actual library palette/base drift')
 if any(x['stream_prefix_hex']!=data[x['stream']-0x08000000:x['stream']-0x08000000+32].hex().upper() for x in calls):raise ValueError('actual library stream bytes drift')
 original=payload(source,rows[41]);offsets=[int.from_bytes(original[i*2:i*2+2],'little') for i in range(256)];seen={}
 for x in calls:
  ids=[i for i,o in enumerate(offsets) if x['stream']==0x08000000+rows[41]['offset']+o]
  for id in ids:seen[str(id)]=x
 if set(seen)!={'1','4','15'}:raise ValueError('library registered names observation differs')
 font=0x0868e004 if key=='blue_moon' else 0x0868e224
 font_jobs=[x for x in jobs if x['source']==font and x['destination']==0x06004000 and x['bytes']==8704]
 if not font_jobs:raise ValueError('library native136-glyph upload absent')
 entry_frame=min(x['first_frame'] for x in font_jobs)
 # Consumer-specific candidate only, not a global allocation. No source or
 # transfer observed on this route overlaps its 58 glyph slots. The seven
 # 128-byte icon slots end at6580, even if unknown rows skip their copies.
 lo,hi=0x06006580,0x06007400
 active_jobs=[x for x in jobs if x['first_frame']>=entry_frame]
 if any(x['destination']<hi and x['destination']+x['bytes']>lo for x in active_jobs):raise ValueError('library proposed working region overlaps active transfer')
 for step in (2,3,4,5,6,7):
  vram=(root/f'step_{step:03d}_gbaVideoRam.bin').read_bytes();off=font-0x08000000
  if vram[0x4000:0x6200]!=source[off:off+8704]:raise ValueError('library native font residency mismatch')
 labels=[x for x in active_jobs if x['destination']==0x06007400 and x['bytes']==864]
 if not labels:raise ValueError('library label boundary unobserved')
 ppuroot=p/'analysis/runtime'/f'{key}_library_ppu_survey_01';state=json.loads((ppuroot/'final_state.json').read_text(encoding='utf-8'))['state'];vram=(ppuroot/'final_gbaVideoRam.bin').read_bytes();bg_references=[]
 if state['ppu.bgMode']!=0:raise ValueError('PPU snapshot is not regular tile mode0')
 for bg in range(4):
  prefix=f'ppu.bgLayers[{bg}].';control=state[prefix+'control'];base=state[prefix+'tilesetAddr'];mp=state[prefix+'tilemapAddr']
  if control&128 or state[prefix+'screenSize']!=0 or base!=((control>>2)&3)*0x4000 or mp!=((control>>8)&31)*0x800:raise ValueError('PPU map/character/bitdepth contract differs')
  references=[]
  for i in range(1024):
   tile=int.from_bytes(vram[mp+i*2:mp+i*2+2],'little')&1023;address=0x06000000+base+tile*32
   if address<hi and address+32>lo:references.append(i)
  if references:raise ValueError('candidate cache is referenced by the original full BG map')
  bg_references.append({'BG':bg,'control':control,'tileset_offset':base,'tilemap_offset':mp,'entries_checked':1024,'candidate_tile_references':0})
 textroot=p/'analysis/runtime'/f'{key}_library_source_survey_01';reads=json.loads((textroot/'textread_final.json').read_text(encoding='utf-8'))
 expected_table_read=0x08037f5e if key=='blue_moon' else 0x08037f92
 if {x['pc'] for x in reads['sites']}!={f'0x{expected_table_read:08X}',f'0x{parser+8:08X}'}:raise ValueError('library pipeline-attributed read sites drift')
 icon=parser+100;icon_at=icon-0x08000000;icon_body=source[icon_at:icon_at+84];icon_ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(icon_body,icon))
 if not any(x.mnemonic=='cmp' and x.op_str=='r7, #7' for x in icon_ins) or not any(x.mnemonic=='adds' and x.op_str=='r6, #0x80' for x in icon_ins):raise ValueError('seven-icon reservation loop drift')
 records[key]={'source_sha256':sha(source),'native_parser_entry':parser,'native_parser_bytes':52,'native_parser_sha256':sha(body),'instructions':[{'address':x.address,'hex':x.bytes.hex(),'mnemonic':x.mnemonic,'operands':x.op_str} for x in instructions],'runtime':receipts,'source_read_sites':reads['sites'],'actual_calls':calls,'actual_archive41_registered_script_ids':[1,4,15],'actual_native_tile_base_palette_hex':'E200','native_font_residency':{'source':font,'destination':0x06004000,'glyphs':136,'bytes':8704,'snapshots_verified':6},'native_dynamic_icons_region':[0x06006200,0x06006580],'native_icon_loop':{'address':icon,'bytes':84,'sha256':sha(icon_body),'slots':7,'stride':128},'native_label_jobs':labels,'rejected_cache_start':{'address':0x06006380,'reason':'registered rows3/4 copy icons into6380..647F; unknown rows skipping copies do not free their slots'},'proposed_working_region':{'start':lo,'end_exclusive':hi,'glyph_capacity':58,'observed_active_transfer_overlap':False,'original_BG_reference_audit':bg_references,'PPU_snapshot_policy':'actual emu.getState numeric PPU fields; no raw IO byte interpretation','not_adopted':'standard-tab snapshot proves no original BG refs; other states, update timing and cross-menu transitions required before new ROM writes'},'read_pc_policy':'CPU r15 callback is pipeline PC; source table and byte load instructions are four bytes earlier'}
if bodies[0]!=bodies[1]:raise ValueError('library revision function bodies differ')
report={'schema':1,'status':'native_library_consumer_classified; new_Hangul_support_not_implemented','scope':'actual standard/mega tab and registered names1/4/15; all library/PA/battle paths not closed','hardware_format_reference':'https://gbadev.net/tonc/regbg.html','profiles':records,'bench':{'command':c,'return_code':r.returncode,'log':log.relative_to(p).as_posix(),'log_sha256':sha(log.read_bytes()),'test_sha256':sha(Path(c[1]).read_bytes()),'scope':'whole original/current development-ROM parser; native tint, zero padding, F9FC empty/prefix loss; no helper stubs'},'open':['dynamic glyph supply and explicit cache lifetime','source private selection for seven-row consumer without changing other archive41 claims','pixel-transfer timing and VRAM/BG reference exclusion beyond standard-tab snapshot','remaining library tabs/other five-row caller','battle and name-input/save/device QA']}
(p/'analysis/library_consumer_analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('two native library consumers:136glyph residency, registered1/4/15, F9FC counterproof PASS;new support pending')
