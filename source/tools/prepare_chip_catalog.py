"""Source-bound chip name authoring and research roundtrip; NEVER builds ROM."""
import argparse,csv,json
from pathlib import Path
from analyze_project import PROFILES,sha,check_dependencies,payload
from verify_tpi_index import parse_tpi
from menu_extension import font_ink,prepare
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--glossary',type=Path,default=p.parents[2]/'록맨 에그제 2/translations/glossary.tsv');a=ap.parse_args()
check_dependencies(p);rs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
author=p/'translations/chip_catalog_authored.tsv';rows=list(csv.DictReader(author.open(encoding='utf-8'),delimiter='\t'));proposals={int(x['chip_id']):x['korean'] for x in rows}
approved=set(range(1,195))|set(range(201,291))|set(range(301,311))
if len(rows)!=294 or set(proposals)!=approved:raise ValueError('authored chip catalog scope drift')
glossary=list(csv.DictReader(a.glossary.open(encoding='utf-8-sig'),delimiter='\t'));terms={}
for x in glossary:terms.setdefault(x['source'],[]).append(x)
source_entries={};indexes={};profiles={};catalog=[]
spec=json.loads((p/'tools/specs/exe4_chip_folder_v1.json').read_text(encoding='utf-8'))
for key,pr in PROFILES.items():
 source=rs[pr['sha256']];index=p/'external/textpet-indexes'/pr['index'];indexes[key]=index;tp=parse_tpi(index)
 es={x['id']:x for x in map(json.loads,(p/'analysis'/f'{key}_source_entries.jsonl').read_text(encoding='utf-8').splitlines()) if x['archive_index'] in (41,42,43,44)}
 if len(es)!=391:raise ValueError('source catalog denominator drift')
 for e in es.values():
  if e['source_rom_sha256']!=sha(source) or e['source_payload_sha256']!=sha(payload(source,tp[e['archive_index']])):raise ValueError('source entry profile/payload drift')
 source_entries[key]=es;s=spec['profiles'][key];literal=s['clone_pointer']
 values=[int.from_bytes(source[literal+i*4:literal+i*4+4],'little') for i in range(7)]
 expected=[0x08000000+tp[41]['offset'],0x08000000+tp[42]['offset'],0x137,0x08000000+literal+16,0x02001770,0x02001780,0x100]
 if values!=expected:raise ValueError('folder ROM/RAM branch boundary drift')
 profiles[key]={'source_sha256':sha(source),'index_sha256':sha(index.read_bytes()),'selector_literals':values,'normal_ROM_chip_ids':[0,310],'RAM_special_first_id':311,'RAM_first_two_pointer_targets':[0x02001770,0x02001780],'RAM_valid_last_id':'not proven by the selector; caller/external provider contract required','archives':{str(ai):{'offset':tp[ai]['offset'],'size':tp[ai]['size'],'entries':sum(e['archive_index']==ai for e in es.values()),'sha256':sha(payload(source,tp[ai])),'claims':tp[ai]['pointers']} for ai in (41,42,43,44)}}
left=source_entries['blue_moon'];right=source_entries['red_sun']
if set(left)!=set(right) or any(left[id]['source_literals']!=right[id]['source_literals'] for id in left):raise ValueError('version-specific chip wording requires separate draft')
entries=[];reference_count=0
for id,text in sorted(proposals.items()):
 stable=f'archive/{41 if id<256 else 42:03d}/script/{id if id<256 else id-256}';es=left[stable]
 if len(es['source_literals'])!=1:raise ValueError('chip source literal structure drift')
 wording=es['source_literals'][0];matches=terms.get(wording,[])
 if any(x['korean']!=text for x in matches):raise ValueError('EXE2 exact glossary differs: '+wording)
 reference_count+=bool(matches)
 entries.append({'id':stable,'chip_id':id,'source':wording,'text':text,'review_state':'needs_review','source_bindings':{key:{field:source_entries[key][stable][field] for field in ['source_rom_sha256','source_payload_sha256','source_tpl_block_sha256']} for key in PROFILES},'EXE2_exact_glossary':matches})
initial=json.loads((p/'translations/chip_names_korean_draft.json').read_text(encoding='utf-8'))
for x in initial['entries']:
 if next(e['text'] for e in entries if e['id']==x['id'])!=x['text']:raise ValueError('adopted initial chip wording drift')
for stable,e in sorted(left.items(),key=lambda pair:(pair[1]['archive_index'],pair[1]['script_id'])):
 ai=e['archive_index'];si=e['script_id'];logical=si if ai==41 else 256+si if ai==42 and si<55 else None
 state='authored draft; not runtime-inserted' if logical in proposals else 'native reserve/empty; preserved' if logical is not None else 'other chip/PA/soul/special source; consumer not classified'
 catalog.append({'id':stable,'source':''.join(e['source_literals']),'ordinary_selector_ROM_id':logical,'status':state,'gameplay_equip_eligibility':'not proven by source selector reachability'})
asset=p/'translations/chip_catalog_korean_draft.json'
wording={'schema':1,'state':'needs_review','build_status':'development seven-row library insertion only; other consumers excluded','scope':'294 non-reserve names in the native selector ROM branch; does not prove gameplay equip eligibility','authoring_sha256':sha(author.read_bytes()),'EXE2_glossary_sha256':sha(a.glossary.read_bytes()),'entries':entries}
asset.write_text(json.dumps(wording,ensure_ascii=False,indent=2),encoding='utf-8')
ink=font_ink(a.font);sets={e['chip_id']:{c for c in e['text'] if 0xac00<=ord(c)<=0xd7a3} for e in entries};demand=set.union(*sets.values())
if demand-set(ink):raise ValueError('catalog glyph missing: '+''.join(sorted(demand-set(ink))))
if any(len(e['text'])>8 for e in entries):raise ValueError('catalog exceeds native eight-cell row')
def witness(population):
 selected=[];active=set()
 for _ in range(7):
  best=max((i for i in population if i not in selected),key=lambda i:(len(sets[i]-active),len(sets[i]),-i));selected.append(best);active|=sets[best]
 while True:
  score=len(set.union(*(sets[i] for i in selected)));best=(score,None,None)
  for slot in range(7):
   other=set.union(*(sets[i] for n,i in enumerate(selected) if n!=slot))
   for i in population:
    if i not in selected and len(other|sets[i])>best[0]:best=(len(other|sets[i]),slot,i)
  if best[1] is None:break
  selected[best[1]]=best[2]
 return {'chip_ids':selected,'texts':[proposals[i] for i in selected],'Hangul_syllables':len(set.union(*(sets[i] for i in selected))),'scope':'hypothetical seven-name working set; no gameplay equip or actual screen claim','conservative_seven_name_upper_bound':sum(sorted((len(sets[i]) for i in population),reverse=True)[:7])}
def validator(project,key,source,w):
 if sha(source)!=PROFILES[key]['sha256'] or w!=wording:raise ValueError('research source/wording drift')
 return {'consumer_selection_verified':False,'consumer_contract_sha256':None,'scope':'source-bound research compile; native F9FC rendering remains unsupported for the full catalog'}
compilation={}
for key in PROFILES:
 _,artifacts,meta=prepare(p,key,rs[PROFILES[key]['sha256']],a.font,None,p/'analysis/chip_catalog_compilation'/key,indexes[key],translation_asset=asset,selection_validator=validator)
 compilation[key]={'no_ROM_produced':True,'metadata':meta,'payloads':[{'archive':ai,'size':len(data),'sha256':sha(data),'original_size':len(payload(rs[PROFILES[key]['sha256']],row))} for ai,row,data in artifacts]}
report={'schema':1,'status':'source-bound research roundtrip verified; bounded library insertion verified separately','no_ROM_produced':True,'source_entries':391,'translated_non_reserve_entries':294,'EXE2_exact_glossary_matches':reference_count,'initial_ten_wordings_preserved':True,'asset_sha256':sha(asset.read_bytes()),'authoring_sha256':sha(author.read_bytes()),'glossary':{'path':str(a.glossary.resolve()),'sha256':sha(a.glossary.read_bytes())},'font_sha256':sha(a.font.read_bytes()),'Hangul_syllables':len(demand),'missing_glyphs':[],'max_cells':max(len(e['text']) for e in entries),'current_fixed_cache_syllables':24,'hypothetical_first150_witness':witness([i for i in sets if i<=150]),'hypothetical_full_ROM_branch_witness':witness(list(sets)),'profiles':profiles,'catalog':catalog,'compilation':compilation,'tool_inputs':{name:sha((p/name).read_bytes()) for name in ['tools/prepare_chip_catalog.py','tools/menu_extension.py','tools/specs/exe4_chip_folder_v1.json']}}
(p/'analysis/chip_catalog_analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(f'391 source names;294 drafts;{len(demand)} Hangul;both research byte roundtrips PASS;NO ROM produced')
