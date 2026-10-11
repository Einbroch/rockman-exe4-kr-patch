"""Verify title-local file inventory and its byte/hash records without writes."""
import csv,json
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1];ledger=p/'ARTIFACT_MANIFEST.tsv'
with ledger.open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream,delimiter='\t'))
seen=set();total=0
for row in rows:
 key=row['artifact_key'];path=p/key
 if key in seen or not path.resolve().is_relative_to(p):raise ValueError('duplicate or external artifact')
 seen.add(key);data=path.read_bytes()
 if len(data)!=int(row['bytes']) or sha(data)!=row['sha256']:raise ValueError('artifact drift '+key)
 total+=len(data)
actual={f.relative_to(p).as_posix() for f in p.rglob('*') if f.is_file() and f!=ledger and '__pycache__' not in f.parts}
if actual!=seen:raise ValueError('inventory mismatch '+str(actual^seen))
for report,suffix in [('extended_verification.json','opening_korean_extended_development'),('boundary_verification.json','hangul_boundary_visibility'),('menu_verification.json','opening_menu_korean_development'),('chip_verification.json','opening_menu_chip_folder_korean_development'),('library_verification.json','opening_menu_chip_folder_library_korean_development')]:
 r=json.loads((p/'analysis'/report).read_text(encoding='utf-8'))
 if len(r['profiles'])!=2:raise ValueError('missing source profile')
 for item in r['profiles']:
  path=p/'poc/output'/f"{item['profile']}_{suffix}.gba"
  if item['static_status']!='PASS' or not item['runtime_status'].startswith('completed') or sha(path.read_bytes())!=item['rom_sha256']:raise ValueError('unverified current product '+str(path))
consumer=json.loads((p/'analysis/remaining_consumer_survey.json').read_text(encoding='utf-8'))
if consumer['contract_sha256']!=sha((p/'tools/specs/exe4_consumer_contracts_v1.json').read_bytes()) or consumer['draft_sha256']!=sha((p/'translations/chip_names_korean_draft.json').read_bytes()):raise ValueError('consumer report input drift')
if set(consumer['profiles'])!={'blue_moon','red_sun'}:raise ValueError('consumer profiles incomplete')
for key,item in consumer['profiles'].items():
 product=p/'poc/output'/f'{key}_opening_menu_korean_development.gba'
 meta=json.loads(product.with_suffix('.json').read_text(encoding='utf-8'))['extension']['menu']
 if not meta['consumer_selection_verified'] or meta['consumer_contract_sha256']!=consumer['contract_sha256']:raise ValueError('product consumer scope attribution drift')
 for proof,steps in [(item['runtime'],31),(item['native_VRAM_copies']['runtime'],1),(consumer['name_display_actual'][key]['runtime'],2)]:
  receipt=p/proof['receipt'];r=json.loads(receipt.read_text(encoding='utf-8'))
  if sha(receipt.read_bytes())!=proof['sha256'] or not r['complete'] or r['return_code'] or r['steps_captured']!=r['steps_expected'] or r['steps_captured']!=steps or r['rom_sha256']!=sha(product.read_bytes()):raise ValueError('consumer completed runtime attribution drift')
visual=json.loads((p/'analysis/CHIP_CONSUMER_RUNTIME_QA.json').read_text(encoding='utf-8'))
if visual['sheet_sha256']!=sha((p/'analysis/visual_qa/chip_consumer_two_versions.png').read_bytes()):raise ValueError('chip visual sheet drift')
for profile in visual['profiles']:
 if profile['runtime_receipt_sha256']!=consumer['profiles'][profile['profile']]['runtime']['sha256']:raise ValueError('chip manual visual runtime drift')
 for capture in profile['checks']:
  if sha((p/capture['capture']).read_bytes())!=capture['sha256']:raise ValueError('chip manual visual capture drift')
chip_v=p/'analysis/chip_verification.json';chip_visual=json.loads((p/'analysis/CHIP_FOLDER_RUNTIME_QA.json').read_text(encoding='utf-8'))
if chip_visual['verification_sha256']!=sha(chip_v.read_bytes()) or len(chip_visual['profiles'])!=2:raise ValueError('new chip visual verification attribution drift')
for name,digest in chip_visual['sheets'].items():
 if sha((p/name).read_bytes())!=digest:raise ValueError('new chip visual sheet drift')
for profile in chip_visual['profiles']:
 product=p/'poc/output'/f"{profile['profile']}_opening_menu_chip_folder_korean_development.gba"
 if profile['rom_sha256']!=sha(product.read_bytes()) or len(profile['checks'])!=9 or len(profile['distinct_chip_script_ids_visually_inspected'])!=10:raise ValueError('new chip manual scope drift')
 for capture in profile['checks']:
  if sha((p/capture['capture']).read_bytes())!=capture['sha256'] or sha((p/capture['runtime_receipt']).read_bytes())!=capture['runtime_receipt_sha256']:raise ValueError('new chip manual capture/receipt drift')
catalog=json.loads((p/'analysis/chip_catalog_analysis.json').read_text(encoding='utf-8'));asset=p/'translations/chip_catalog_korean_draft.json';cw=json.loads(asset.read_text(encoding='utf-8'))
if catalog['source_entries']!=391 or catalog['translated_non_reserve_entries']!=294 or len(cw['entries'])!=294 or not catalog['no_ROM_produced'] or catalog['asset_sha256']!=sha(asset.read_bytes()) or catalog['authoring_sha256']!=sha((p/'translations/chip_catalog_authored.tsv').read_bytes()):raise ValueError('research catalog scope/input drift')
if sha(Path(catalog['glossary']['path']).read_bytes())!=catalog['glossary']['sha256']:raise ValueError('EXE2 glossary reference drift')
for name,digest in catalog['tool_inputs'].items():
 if sha((p/name).read_bytes())!=digest:raise ValueError('research catalog tool drift')
for key,item in catalog['compilation'].items():
 if not item['no_ROM_produced'] or item['metadata']['consumer_selection_verified'] or item['metadata']['translation_asset_sha256']!=sha(asset.read_bytes()):raise ValueError('research compile falsely credited as runtime support')
 for part in item['payloads']:
  off=catalog['profiles'][key]['archives'][str(part['archive'])]['offset'];root=p/'analysis/chip_catalog_compilation'/key/'menu';msg=root/f'{off:06X}.msg';back=root/f'{off:06X}_back.msg'
  if sha(msg.read_bytes())!=part['sha256'] or msg.read_bytes()!=back.read_bytes():raise ValueError('research MSG byte roundtrip drift')
libpath=p/'analysis/library_consumer_analysis.json';library=json.loads(libpath.read_text(encoding='utf-8'));bench=library['bench']
if bench['return_code'] or sha((p/bench['log']).read_bytes())!=bench['log_sha256'] or sha(Path(bench['command'][1]).read_bytes())!=bench['test_sha256']:raise ValueError('native library CPU evidence drift')
for key,item in library['profiles'].items():
 for label,proof in item['runtime'].items():
  receipt=p/proof['receipt'];r=json.loads(receipt.read_text(encoding='utf-8'))
  if sha(receipt.read_bytes())!=proof['sha256'] or not r['complete'] or r['return_code'] or r['steps_captured']!=proof['steps'] or r['rom_sha256']!=sha((p/'poc/output'/f'{key}_opening_menu_korean_development.gba').read_bytes()):raise ValueError('native library runtime drift')
lib_visual=json.loads((p/'analysis/LIBRARY_SOURCE_RUNTIME_QA.json').read_text(encoding='utf-8'))
if lib_visual['analysis_sha256']!=sha(libpath.read_bytes()) or lib_visual['sheet_sha256']!=sha((p/'analysis/visual_qa/library_source_two_versions.png').read_bytes()):raise ValueError('native library visual binding drift')
for capture in lib_visual['checks']:
 if sha((p/capture['capture']).read_bytes())!=capture['sha256'] or sha((p/capture['receipt']).read_bytes())!=capture['receipt_sha256']:raise ValueError('native library capture drift')
implemented=p/'analysis/LIBRARY_RUNTIME_QA.json';libqa=json.loads(implemented.read_text(encoding='utf-8'));libv=p/'analysis/library_verification.json'
if not libqa['status'].startswith('PASS') or libqa['sheet_sha256']!=sha((p/libqa['sheet']).read_bytes()):raise ValueError('implemented library QA drift')
for key,item in libqa['profiles'].items():
 product=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_korean_development.gba'
 if item['rom_sha256']!=sha(product.read_bytes()) or item['actual_registered_source_ids']!=[1,4,15]:raise ValueError('implemented library product attribution drift')
 for proof in item['receipts']:
  if sha((p/proof['path']).read_bytes())!=proof['sha256']:raise ValueError('implemented library receipt drift')
 for shot in item['screenshots']:
  if sha((p/shot['path']).read_bytes())!=shot['sha256']:raise ValueError('implemented library screenshot drift')
bp=p/'analysis/battle_caption_verification.json';battle=json.loads(bp.read_text(encoding='utf-8'))
bq=json.loads((p/'analysis/BATTLE_CAPTION_RUNTIME_QA.json').read_text(encoding='utf-8'))
if not battle['status'].startswith('PASS') or not bq['status'].startswith('PASS') or bq['verification']['sha256']!=sha(bp.read_bytes()):raise ValueError('battle caption verification drift')
if set(battle['profiles'])!={'blue_moon','red_sun'} or set(bq['profiles'])!=set(battle['profiles']):raise ValueError('battle caption profile coverage drift')
for name,digest in battle['inputs'].items():
 if sha((p/name).read_bytes())!=digest:raise ValueError('battle caption input drift '+name)
if battle['bench']['return_code'] or sha((p/battle['bench']['log']).read_bytes())!=battle['bench']['log_sha256']:raise ValueError('battle caption CPU bench drift')
def check_proof(proof):
 if sha((p/proof['path']).read_bytes())!=proof['sha256']:raise ValueError('battle proof drift '+proof['path'])
check_proof(bq['sheet'])
for key,q in bq['profiles'].items():
 product=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_caption_korean_development.gba'
 if sha(product.read_bytes())!=q['rom_sha256'] or q['rom_sha256']!=battle['profiles'][key]['rom_sha256'] or q['natural_source_ids']!=[1,29,48,107]:raise ValueError('battle caption product/scope drift')
 for proof in q['receipts']+q['route_lineage']:
  check_proof(proof);r=json.loads((p/proof['path']).read_text(encoding='utf-8'))
  if not r['complete'] or r['return_code'] or r['rom_sha256']!=q['rom_sha256'] or r['steps_expected']!=r['steps_captured']:raise ValueError('incomplete battle route')
 if len(q['checks'])!=6:raise ValueError('battle caption checks missing')
 for capture in q['checks']:
  for kind in ['screenshot','RAM','VRAM']:check_proof(capture[kind])
  ram=(p/capture['RAM']['path']).read_bytes()[0x3e590:0x3e790]
  vram=(p/capture['VRAM']['path']).read_bytes()[0x9380:0x9580]
  if ram!=vram or sha(ram)!=capture['caption_sha256']:raise ValueError('battle caption RAM/VRAM drift')
av=p/'analysis/battle_active_verification.json';active=json.loads(av.read_text(encoding='utf-8'))
aq=json.loads((p/'analysis/BATTLE_ACTIVE_RUNTIME_QA.json').read_text(encoding='utf-8'))
if not active['status'].startswith('PASS') or not aq['status'].startswith('PASS') or aq['verification']['sha256']!=sha(av.read_bytes()):raise ValueError('queued battle name verification drift')
if set(active['profiles'])!={'blue_moon','red_sun'} or set(aq['profiles'])!=set(active['profiles']):raise ValueError('queued battle profile coverage drift')
for name,digest in active['inputs'].items():
 if sha((p/name).read_bytes())!=digest:raise ValueError('queued battle input drift '+name)
if active['bench']['return_code'] or sha((p/active['bench']['log']).read_bytes())!=active['bench']['log_sha256']:raise ValueError('queued battle CPU evidence drift')
if aq['tool_sha256']!=sha((p/'tools/record_battle_active_qa.py').read_bytes()):raise ValueError('queued battle runtime checker drift')
check_proof(aq['sheet'])
for key,q in aq['profiles'].items():
 product=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba'
 if sha(product.read_bytes())!=q['rom_sha256'] or q['rom_sha256']!=active['profiles'][key]['rom_sha256'] or q['natural_source_ids']!=[1,29]:raise ValueError('queued battle product/scope drift')
 for proof in q['receipts']+q['lineage']:
  check_proof(proof);r=json.loads((p/proof['path']).read_text(encoding='utf-8'))
  if not r['complete'] or r['return_code'] or r['rom_sha256']!=q['rom_sha256'] or r['steps_expected']!=r['steps_captured']:raise ValueError('incomplete queued battle route')
 for capture in q['checks']:
  for kind in ['screenshot','RAM','VRAM','PPU']:check_proof(capture[kind])
  ram=(p/capture['RAM']['path']).read_bytes()[0x3e590:0x3e790];vram=(p/capture['VRAM']['path']).read_bytes()[0x9380:0x9580]
  if ram!=vram or sha(ram)!=capture['caption_sha256'] or not capture['glyph_count_and_damage_position_verified']:raise ValueError('queued name RAM/VRAM drift')
 for capture in q['clearing']:
  check_proof(capture['VRAM']);check_proof(capture['screenshot']);vram=(p/capture['VRAM']['path']).read_bytes()
  if any(vram[0xf800+row*64:0xf800+row*64+32]!=b'\0'*32 for row in (18,19)):raise ValueError('queued name clearing drift')
description=json.loads((p/'analysis/chip_description_analysis.json').read_text(encoding='utf-8'))
if description['selected_entries']!=10 or description['authoring_sha256']!=sha((p/'translations/chip_description_authored.json').read_bytes()) or description['draft_sha256']!=sha((p/'translations/chip_descriptions_korean_draft.json').read_bytes()) or description['tool_sha256']!=sha((p/'tools/prepare_chip_descriptions.py').read_bytes()):raise ValueError('description research input drift')
for key,item in description['profiles'].items():
 compiled=p/item['compiled']
 if not item['roundtrip_exact'] or item['unselected_scripts_preserved']!=246 or sha(compiled.read_bytes())!=item['compiled_sha256'] or compiled.read_bytes()!=compiled.with_name('descriptions_back.msg').read_bytes():raise ValueError('description research compilation drift')
nr=description['native_runtime'];rp=p/nr['receipt'];r=json.loads(rp.read_text(encoding='utf-8'))
if sha(rp.read_bytes())!=nr['receipt_sha256'] or not r['complete'] or r['return_code'] or r['rom_sha256']!=nr['rom_sha256']:raise ValueError('native description runtime attribution drift')
dv=p/'analysis/descriptions_verification.json';descriptions=json.loads(dv.read_text(encoding='utf-8'))
dq=json.loads((p/'analysis/DESCRIPTIONS_RUNTIME_QA.json').read_text(encoding='utf-8'))
if not descriptions['status'].startswith('PASS') or not dq['status'].startswith('PASS') or dq['verification']['sha256']!=sha(dv.read_bytes()):raise ValueError('description product QA drift')
if set(descriptions['profiles'])!={'blue_moon','red_sun'} or set(dq['profiles'])!=set(descriptions['profiles']):raise ValueError('description profile coverage drift')
for name,digest in descriptions['inputs'].items():
 if sha((p/name).read_bytes())!=digest:raise ValueError('description build input drift '+name)
if descriptions['bench']['return_code'] or sha((p/descriptions['bench']['log']).read_bytes())!=descriptions['bench']['log_sha256']:raise ValueError('description CPU proof drift')
if dq['tool_sha256']!=sha((p/'tools/record_descriptions_qa.py').read_bytes()):raise ValueError('description runtime checker drift')
check_proof(dq['sheet'])
for key,q in dq['profiles'].items():
 product=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
 if sha(product.read_bytes())!=q['rom_sha256'] or q['rom_sha256']!=descriptions['profiles'][key]['rom_sha256'] or q['natural_source_ids']!=[1,29,48,107]:raise ValueError('description product/scope attribution drift')
 for proof in q['lineage']+q['receipts']:
  check_proof(proof);r=json.loads((p/proof['path']).read_text(encoding='utf-8'))
  if not r['complete'] or r['return_code'] or r['rom_sha256']!=q['rom_sha256'] or r['steps_expected']!=r['steps_captured']:raise ValueError('incomplete description runtime')
 for capture in q['checks']:
  for field in ['screenshot','closed_screenshot','fontread_before','fontread_open']:check_proof(capture[field])
  for proof in capture['VRAM_before_open_closed']:check_proof(proof)
  segments=[(p/x['path']).read_bytes()[0x9380:0x9580] for x in capture['VRAM_before_open_closed']]
  if segments[0]!=segments[1] or segments[1]!=segments[2]:raise ValueError('description overwrites caption')
mv=p/'analysis/menu_descriptions_verification.json';menudesc=json.loads(mv.read_text(encoding='utf-8'))
mq=json.loads((p/'analysis/MENU_DESCRIPTIONS_RUNTIME_QA.json').read_text(encoding='utf-8'))
if not menudesc['status'].startswith('PASS') or not mq['status'].startswith('PASS') or mq['verification']['sha256']!=sha(mv.read_bytes()):raise ValueError('menu description product QA drift')
if set(menudesc['profiles'])!={'blue_moon','red_sun'} or set(mq['profiles'])!=set(menudesc['profiles']):raise ValueError('menu description profile coverage drift')
for name,digest in menudesc['inputs'].items():
 if sha((p/name).read_bytes())!=digest:raise ValueError('menu description build input drift '+name)
if menudesc['bench']['return_code'] or sha((p/menudesc['bench']['log']).read_bytes())!=menudesc['bench']['log_sha256']:raise ValueError('menu description CPU proof drift')
if mq['tool_sha256']!=sha((p/'tools/record_menu_descriptions_qa.py').read_bytes()):raise ValueError('menu description runtime checker drift')
for proof in mq['sheets']:check_proof(proof)
# The ten-cell predecessor stays on record as rejected, and its ROM must never
# be the one the nine-cell claim is attributed to.
rejection=json.loads((p/mq['rejected_predecessor']).read_text(encoding='utf-8'))
if not rejection['status'].startswith('REJECTED'):raise ValueError('ten-cell predecessor no longer recorded as rejected')
for key,q in mq['profiles'].items():
 product=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_v2_korean_development.gba'
 if sha(product.read_bytes())!=q['rom_sha256'] or q['rom_sha256']!=menudesc['profiles'][key]['rom_sha256'] or q['natural_library_ids']!=[1,4,15]:raise ValueError('menu description product/scope attribution drift')
 if q['rom_sha256']==rejection['products'][key]['sha256']:raise ValueError('rejected ten-cell product credited as the nine-cell build')
 if len(q['checks'])!=15 or len(q['hidden'])!=3:raise ValueError('menu description coverage drift')
 for proof in q['lineage']:
  check_proof(proof);r=json.loads((p/proof['path']).read_text(encoding='utf-8'))
  if not r['complete'] or r['return_code'] or r['rom_sha256']!=q['rom_sha256'] or r['steps_expected']!=r['steps_captured']:raise ValueError('incomplete menu description runtime')
 for capture in q['checks']:
  for field in ['RAM','VRAM','OAM','palette','screenshot']:check_proof(capture[field])
  if not capture['tenth_column_blank'] or capture['visible_OBJ_cells']!=27:raise ValueError('menu description visible-cell attribution drift')
  if any(len(line)>9 for line in capture['text'].splitlines()):raise ValueError('recorded wording exceeds the visible ninth column')
 for capture in q['hidden']:
  check_proof(capture['screenshot'])
  if not capture['description_rectangle_uniform']:raise ValueError('unregistered entry retains description ink')
sv=p/'analysis/story_verification.json';story=json.loads(sv.read_text(encoding='utf-8'))
sq=json.loads((p/'analysis/STORY_RUNTIME_QA.json').read_text(encoding='utf-8'))
sg=json.loads((p/'analysis/story_translation_gate.json').read_text(encoding='utf-8'))
sx=json.loads((p/'analysis/story_extraction.json').read_text(encoding='utf-8'))
# Five archives carry no pointer claim, so a batch covering one would build text
# the ROM never loads. The refusal lives in prepare; this checks it stayed on.
unreachable={int(r['index']) for r in json.loads((p/'analysis/blue_moon_analysis.json').read_text(encoding='utf-8'))['archives_detail'] if not r['pointers']}
for item in sg['batches']:
 covered={e['id'].split('/')[1] for e in json.loads((p/item['path']).read_text(encoding='utf-8'))['entries']}
 if {int(x) for x in covered}&unreachable:raise ValueError('gated batch covers an archive with no pointer claim: '+item['path'])
sb=json.loads((p/'analysis/story_bench.json').read_text(encoding='utf-8'))
if not story['status'].startswith('PASS') or not sq['status'].startswith('PASS') or sg['status']!='PASS':raise ValueError('story stage is not PASS')
if sq['verification']['sha256']!=sha(sv.read_bytes()) or story['gate_sha256']!=sha((p/'analysis/story_translation_gate.json').read_bytes()):raise ValueError('story verification/gate binding drift')
if sg['sheet_sha256']!=sx['sheet_sha256'] or sx['sheet_sha256']!=sha((p/sx['sheet']).read_bytes()):raise ValueError('story sheet drift')
if sg['problem_count'] or sg['entries_checked']!=sg['story_ids_translated']:raise ValueError('story gate did not pass cleanly')
# The dialogue gate measures the 180px window, which a menu option does not get:
# it shares its row. Nothing was measuring that until a Hangul syllable at 12px
# started overrunning the kana at 11px it replaced, so the option gate is part
# of the attribution too, bound to the same batch files the dialogue gate saw.
ow=json.loads((p/'analysis/story_option_widths.json').read_text(encoding='utf-8'))
if ow['status']!='PASS' or ow['problems']:raise ValueError('story option-width gate did not pass')
if not ow['budgets'] or ow['translated_rows']<1:raise ValueError('story option-width gate checked nothing')
gated={item['path'] for item in sg['batches']}
if {b.relative_to(p).as_posix() for b in sorted((p/'translations/story_korean').glob('*.json'))}!=gated:
 raise ValueError('story option-width gate and dialogue gate saw different batch sets')
for item in sg['batches']:
 if sha((p/item['path']).read_bytes())!=item['sha256']:raise ValueError('story batch drift '+item['path'])
# The dialogue gate keeps one Korean per Japanese source line, so a name that recurs
# across different lines can drift without any line failing: the story-data puzzle
# named one spirit 해님 and 오텐코 님 a chapter apart, and dialogue called the PET
# menu's 데이터 도감 by another name. The glossary-term gate checks those names
# against translations/glossary.tsv, bound to the same batch files.
gt=json.loads((p/'analysis/story_glossary_terms.json').read_text(encoding='utf-8'))
if gt['status']!='PASS' or gt['problems']:raise ValueError('story glossary-term gate did not pass')
if gt['lines_checked']<1000:raise ValueError('story glossary-term gate checked almost nothing')
if gt['glossary_sha256']!=sha((p/'translations/glossary.tsv').read_bytes()):raise ValueError('story glossary drift')
if {gb['path'] for gb in gt['batches']}!=gated:raise ValueError('story glossary-term gate and dialogue gate saw different batch sets')
for gb in gt['batches']:
 if sha((p/gb['path']).read_bytes())!=gb['sha256']:raise ValueError('story glossary-term batch drift '+gb['path'])
if sb['status']!='PASS':raise ValueError('story gate bench did not pass')
if sha((p/sb['log']).read_bytes())!=sb['log_sha256'] or sb['tests']<16:raise ValueError('story gate bench drift')
for name,digest in sb['inputs'].items():
 if sha((p/name).read_bytes())!=digest:raise ValueError('story bench input drift '+name)
if sq['tool_sha256']!=sha((p/'tools/record_story_qa.py').read_bytes()):raise ValueError('story runtime checker drift')
for proof in sq['sheets']:check_proof(proof)
if set(story['profiles'])!={'blue_moon','red_sun'} or set(sq['profiles'])!=set(story['profiles']):raise ValueError('story profile coverage drift')
for key,q in sq['profiles'].items():
 product=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_story_korean_development.gba'
 if sha(product.read_bytes())!=q['rom_sha256'] or q['rom_sha256']!=story['profiles'][key]['rom_sha256']:raise ValueError('story product attribution drift')
 receipt=p/q['route']/'result.json';r=json.loads(receipt.read_text(encoding='utf-8'))
 if sha(receipt.read_bytes())!=q['receipt_sha256'] or not r['complete'] or r['return_code'] or r['rom_sha256']!=q['rom_sha256'] or r['steps_expected']!=r['steps_captured']:raise ValueError('story runtime receipt drift')
 # A capture only counts when its bytes are the ones the report measured.
 for capture in q['checks']:
  if sha((p/q['route']/capture['screenshot']).read_bytes())!=capture['screenshot_sha256']:raise ValueError('story capture drift')
  if not capture['pixel_matched_lines']:raise ValueError('story message recorded with no matched line')
  for line in capture['pixel_matched_lines']:
   if line['origin'][1] not in q['baselines']:raise ValueError('story line recorded off the baseline grid')
 if q['lines_pixel_matched']<18 or q['text_left_margin']!=51:raise ValueError('story runtime coverage drift')
 # Derive the count from the gated batches instead of pinning a number: a
 # literal belongs to a revision only when its record exists there, and a
 # hard-coded total just breaks on the next batch without checking anything.
 expected=sum(1 for item in sg['batches'] for e in json.loads((p/item['path']).read_text(encoding='utf-8'))['entries'] if key in e['source_bindings'])
 if story['profiles'][key]['selected_literals']!=expected or not story['profiles'][key]['no_executable_changes']:raise ValueError('story static scope drift')
 # A raw archive wrapped in an LZ77 header passed every static check and
 # still left the screen black, so the cheap boot check is part of the
 # attribution now, bound to this exact ROM.
 boot=json.loads((p/'analysis/story_boot_check.json').read_text(encoding='utf-8'))
 if boot['status']!='PASS':raise ValueError('story boot check did not pass')
 entry=next((x for x in boot['products'] if x['rom_sha256']==q['rom_sha256']),None)
 if entry is None or not entry['draws']:raise ValueError('no passing boot check for this story product')
 for item in story['profiles'][key]['checks']:
  if 'stored_compressed' not in item:raise ValueError('story archive storage form not recorded')
print('PASS',len(rows),'artifact byte/hash records;',total,'bytes; battle products and private ten-description builds attributed')
