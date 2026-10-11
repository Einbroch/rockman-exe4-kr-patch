"""Bind native chip/NAME findings and blocked drafts to source and actual runs."""
import argparse,json,sys
from pathlib import Path
from analyze_project import PROFILES,sha,check_dependencies,payload,scripts
from verify_tpi_index import parse_tpi
from menu_extension import font_ink
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'external/arm_debug_python'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);a=ap.parse_args()
check_dependencies(p);rs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
contract_path=p/'tools/specs/exe4_consumer_contracts_v1.json';contract=json.loads(contract_path.read_text(encoding='utf-8'))
draft_path=p/'translations/chip_names_korean_draft.json';draft=json.loads(draft_path.read_text(encoding='utf-8'))
if draft['schema']!=1 or draft['state']!='needs_review' or draft['build_status']!='private_folder_development_only; all other consumers excluded':raise ValueError('draft policy drift')
ink=font_ink(a.font);wanted={ch for e in draft['entries'] for ch in e['text'] if 0xac00<=ord(ch)<=0xd7a3}
report={'schema':1,'status':'baseline native consumers classified; private folder extension has separate chip_verification evidence',
 'scope':'initial folder BG tilemap decoder and existing PET three-byte NAME display; not battle-screen, name-input/save, or whole-game closure',
 'contract_sha256':sha(contract_path.read_bytes()),'draft_sha256':sha(draft_path.read_bytes()),
 'draft_font_demand':{'syllables':len(wanted),'font_sha256':sha(a.font.read_bytes()),'missing':sorted(wanted-set(ink)),'does_not_prove_VRAM_allocation':True},'profiles':{}}
def receipt(rel,key,steps):
 root=p/rel;r=json.loads((root/'result.json').read_text(encoding='utf-8'))
 product=p/'poc/output'/f'{key}_opening_menu_korean_development.gba'
 if not r['complete'] or r['return_code'] or r['steps_captured']!=r['steps_expected'] or (steps and r['steps_captured']!=steps) or r['rom_sha256']!=sha(product.read_bytes()) or r['audio_enabled']:
  raise ValueError('incomplete or foreign consumer receipt')
 if len(r['loaded_rom_guards'])<7:raise ValueError('consumer loaded-byte guards missing')
 for name,digest in r['artifacts'].items():
  if sha((root/name).read_bytes())!=digest:raise ValueError('consumer artifact drift '+name)
 return root,r,{'receipt':str((root/'result.json').relative_to(p).as_posix()),'sha256':sha((root/'result.json').read_bytes()),'rom_sha256':r['rom_sha256'],'steps':r['steps_captured']}
for key,pr in PROFILES.items():
 source=rs[pr['sha256']];rows=parse_tpi(p/'external/textpet-indexes'/pr['index']);row=rows[41];original=payload(source,row)
 es={e['id']:e for e in (json.loads(x) for x in (p/'analysis'/f'{key}_source_entries.jsonl').read_text(encoding='utf-8').splitlines())}
 root,r,proof=receipt(f'analysis/runtime/{key}_folder_chip_inventory_01',key,31)
 calls=json.loads((root/'chipcalls_final.json').read_text(encoding='utf-8'))['calls'];seen={};start=contract['profiles'][key]['unsupported_chip_parser_entry']
 for c in calls:
  if c['pc']!=start or c['archive']!=0x08000000+row['offset'] or c['tile_base']!=0x200 or c['lower_row']-c['destination']!=16:raise ValueError('chip native ABI drift')
  si=c['script_id'];offset=int.from_bytes(original[si*2:si*2+2],'little');stream=0x08000000+row['offset']+offset
  if c['stream']!=stream or c['stream_prefix_hex']!=source[stream&0x1ffffff:(stream&0x1ffffff)+32].hex().upper():raise ValueError('chip stream identity drift')
  e=es[f'archive/041/script/{si}']
  if e['language']!='mmbn4s' or e['source_rom_sha256']!=sha(source) or e['source_payload_sha256']!=sha(original):raise ValueError('chip source binding drift')
  seen[e['id']]={'source':e['source_literals'][0],'native_call':c,'source_payload_sha256':e['source_payload_sha256'],'source_tpl_block_sha256':e['source_tpl_block_sha256']}
 if set(seen)!={e['id'] for e in draft['entries']}:raise ValueError('draft and actual initial folder population differ')
 for e in draft['entries']:
  if seen[e['id']]['source']!=e['source'] or len(e['text'])>8:raise ValueError('chip draft wording/cell drift')
 instructions=[]
 for at,size in [(start&0x1ffffff,0x36),(0x21382c,0x28)]:
  addr=0x0300692c if at==0x21382c else 0x08000000+at
  decoded=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(source[at:at+size],addr))
  if sum(len(i.bytes) for i in decoded)!=size:raise ValueError('native instruction census incomplete')
  instructions += [{'address':i.address,'hex':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in decoded]
 report['profiles'][key]={'source_sha256':sha(source),'chip_archive':41,'chip_source_offset':row['offset'],'chip_parser_entry':start,'chip_unique_calls':len(calls),'chip_entries':seen,'cell_count_observed':8,'tilemap_upper_lower_row_gap':16,'tile_base_observed':512,'runtime':proof,'native_instructions':instructions}
 vram_rel='analysis/runtime/blue_moon_chip_survey_03' if key=='blue_moon' else 'analysis/runtime/red_sun_chip_vram_survey_01'
 vr,_,vp=receipt(vram_rel,key,1);vram=(vr/'final_gbaVideoRam.bin').read_bytes()
 style=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))['profiles'][key]['fonts'][0]
 copies=[]
 for first,count,dest in [(0,160,0x06004000),(416,32,0x0600d800)]:
  at=(style['source_address']&0x1ffffff)+first*64;chunk=source[at:at+count*64];off=vram.find(chunk)
  if off<0 or vram.find(chunk,off+1)>=0 or off+0x06000000!=dest:raise ValueError('native font VRAM copy not uniquely matched')
  copies.append({'source_offset':at,'bytes':len(chunk),'source_sha256':sha(chunk),'VRAM_address':dest,'exact_unique_copy':True,'scope':'native characters0..159' if first==0 else 'observed copy includes seven records beyond adopted 441-font supply; their purpose is unclassified'})
 report['profiles'][key]['native_VRAM_copies']={'runtime':vp,'copies':copies,'other_VRAM_allocations_closed':False}
 # Static name-input source evidence. This is not an actual name-entry GUI run.
 matches=[]
 for e in es.values():
  if e['script_id']!=11:continue
  path=p/'analysis'/f'{key}_tpl'/f"{e['archive_offset']:06X}.tpl"
  parsed=next((b for si,lang,vs,b in scripts(path.read_text(encoding='utf-8-sig')) if si==11),None)
  if parsed and 'menuSelectName' in parsed and 'ナマエをトウロクしてください' in parsed:
   if parsed.count('menuOptionName')!=3:raise ValueError('name option census drift')
   matches.append({'id':e['id'],'source_tpl_block_sha256':e['source_tpl_block_sha256'],'options':3,'scope':'source-only; input/save producer not runtime-verified'})
 if len(matches)!=1:raise ValueError('ambiguous name-entry source')
 report['profiles'][key]['name_entry_source']=matches[0]
report['name_display_actual']={}
for key in PROFILES:
 root,r,proof=receipt(f'analysis/runtime/{key}_name_trace_01',key,2)
 trace={c['pc']:c for c in json.loads((root/'step_002_exectrace.json').read_text(encoding='utf-8'))['sites']}
 if trace['0x0300692C']['hits']!=1 or trace['0x0300693A']['hits']!=3 or trace['0x0300693A']['first_regs']['cpu.r0']!=0x00828282:raise ValueError('actual default NAME census drift')
 report['name_display_actual'][key]={'runtime':proof,'native_calls':trace,'packed_name_value_hex':'00828282','three_default_dash_glyphs':True}
report['open_requirements']=['folder demand and residency beyond the observed ten chip names; see chip_verification for bounded private extension','chip all other callers including battle/library/compressed/external consumers','name input character-selection engine and save producer/layout/checksum/communication consumers','entire short-text/font demand beyond the observed ten chip names']
(p/'analysis/remaining_consumer_survey.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('two revisions: baseline initial folder 10 chip names, 58 unique calls, 8 cells; native NAME 3 byte indexes; private extension is separate')
