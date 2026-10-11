"""Add two data-only menu consumers to an authenticated immutable development baseline."""
import copy,json
from pathlib import Path
from analyze_project import sha,PROFILES
p=Path(__file__).resolve().parents[1]
sp=p/'tools/specs/exe4_menu_descriptions_v2.json';spec=json.loads(sp.read_text())
rp=p/'analysis/menu_chip_description_analysis.json';report=json.loads(rp.read_text(encoding='utf-8'))
draft=p/'translations/menu_chip_descriptions_korean_draft.json'
if sha(draft.read_bytes())!=spec['draft_sha256'] or report['draft_sha256']!=spec['draft_sha256']:raise ValueError('menu description draft drift')
if report['tool_sha256']!=sha((p/'tools/prepare_menu_chip_descriptions.py').read_bytes()) or report['authoring_sha256']!=sha((p/'translations/menu_chip_description_authored.json').read_bytes()):raise ValueError('menu preparation input drift')
verified=json.loads((p/'analysis/descriptions_verification.json').read_text())
for key,pr in PROFILES.items():
 source=next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes())==pr['sha256']);s=spec['profiles'][key]
 baseline=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
 base=baseline.read_bytes();bm=json.loads(baseline.with_suffix('.json').read_text(encoding='utf-8'))
 if sha(source)!=s['source_sha256'] or sha(base)!=s['baseline_sha256'] or bm['output_sha256']!=sha(base) or verified['profiles'][key]['rom_sha256']!=sha(base):raise ValueError('baseline identity drift')
 data=(p/report['profiles'][key]['compiled']).read_bytes()
 if sha(data)!=s['compiled_sha256'] or data!=(p/report['profiles'][key]['compiled']).with_name('descriptions_back.msg').read_bytes():raise ValueError('menu compilation drift')
 if any(len(x['line_cells'])>3 or max(x['line_cells'])>9 for x in report['profiles'][key]['details']):raise ValueError('menu text bounds')
 demand={c for x in json.loads(draft.read_text(encoding='utf-8'))['entries'] for c in x['text'] if 0xac00<=ord(c)<=0xd7a3}
 if not demand<=set(bm['extension']['menu']['characters']):raise ValueError('menu missing glyph')
 end=max(x['offset']+x['size'] for x in bm['extension']['layout']);clone=(end+3)&~3
 if clone+len(data)>len(base) or base[clone:]!=b'\xff'*(len(base)-clone):raise ValueError('menu clone space not proven free')
 writes=[]
 for name,c in s['consumers'].items():
  at=c['pointer_offset'];start=c['start']
  if sha(source[start:at])!=c['context_sha256'] or base[start:at]!=source[start:at]:raise ValueError('menu executable context drift')
  if c['font']!=bm['extension']['menu']['styles'][1]['source_address']:raise ValueError('menu font style unclassified')
  if source[at:at+4]!=s['source_pointer'].to_bytes(4,'little') or base[at:at+4]!=source[at:at+4]:raise ValueError('menu pointer drift')
  writes.append({'offset':at,'size':4,'writer':name+' private menu description pointer','expected_sha256':sha(source[at:at+4]),'final_sha256':sha((0x08000000+clone).to_bytes(4,'little'))})
 target=bytearray(base)
 for w in writes:target[w['offset']:w['offset']+4]=(0x08000000+clone).to_bytes(4,'little')
 target[clone:clone+len(data)]=data
 m=copy.deepcopy(bm);m['expected_writes']=[x for x in m['expected_writes'] if x['offset']<len(source)]+writes
 m['expected_writes'].append({'offset':len(source),'size':len(target)-len(source),'writer':'inherited development payload plus private menu description clone','final_sha256':sha(target[len(source):])})
 covered=bytearray(len(source));ranges=[]
 for w in m['expected_writes']:
  at=w['offset'];stop=at+w['size'];ranges.append((at,stop))
  if sha(target[at:stop])!=w['final_sha256']:raise ValueError('final writer drift')
  if at<len(source):
   if stop>len(source) or sha(source[at:stop])!=w['expected_sha256']:raise ValueError('source preimage drift')
   covered[at:stop]=b'\1'*(stop-at)
 ranges.sort()
 if any(a[1]>b[0] for a,b in zip(ranges,ranges[1:])) or any(x!=y and not covered[i] for i,(x,y) in enumerate(zip(source,target))):raise ValueError('overlap or unexplained source difference')
 allowed=[(x['offset'],x['offset']+4) for x in writes]+[(clone,clone+len(data))]
 if any(x!=y and not any(lo<=i<hi for lo,hi in allowed) for i,(x,y) in enumerate(zip(base,target))):raise ValueError('unexplained baseline difference')
 layout={'name':'private ten menu descriptions archive54 clone','offset':clone,'size':len(data),'sha256':sha(data)}
 m['extension']['layout'].append(layout)
 m['extension']['menu_descriptions']={'contract_sha256':sha(sp.read_bytes()),'translation_asset_sha256':sha(draft.read_bytes()),
  'archive_offset':clone,'archive_size':len(data),'layout':[layout],'new_executable_code':False,'new_VRAM_allocation':False,
  'cells':10,'visible_cells':9,'lines':3,'selected_ids':[1,4,15,29,48,49,91,107,117,149],'unselected_scripts_preserved':246,
  'development_consumer_opt_in':'build_menu_descriptions.py exact ten menu drafts; no release eligibility','review_state':'needs_review'}
 m['baseline_sha256']=sha(base);m['output_sha256']=sha(target);m['runtime']='pending';m['known_limit']='adds folder-edit and library ten menu descriptions; third menu claim, independent review and whole-game/device QA remain open'
 m['menu_description_inputs']={name:sha((p/name).read_bytes()) for name in ['tools/build_menu_descriptions.py','tools/specs/exe4_menu_descriptions_v2.json','tools/prepare_menu_chip_descriptions.py','translations/menu_chip_description_authored.json','translations/menu_chip_descriptions_korean_draft.json','analysis/menu_chip_description_analysis.json']}
 out=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_v2_korean_development.gba'
 out.write_bytes(target);out.with_suffix('.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
 print(key,m['output_sha256'])
