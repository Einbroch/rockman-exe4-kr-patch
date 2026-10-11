"""Recheck immutable preimages, complete final differences, and CPU evidence."""
import json,subprocess,sys
from pathlib import Path
from analyze_project import PROFILES,sha
p=Path(__file__).resolve().parents[1]
sp=p/'tools/specs/exe4_menu_descriptions_v2.json';spec=json.loads(sp.read_text())
report={'schema':1,'status':'PASS static and CPU; natural runtime recorded separately','scope':spec['scope'],'profiles':{}}
for key,pr in PROFILES.items():
 source=next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes())==pr['sha256']);s=spec['profiles'][key]
 baseline=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
 target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_v2_korean_development.gba'
 base=baseline.read_bytes();data=target.read_bytes();m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'));bm=json.loads(baseline.with_suffix('.json').read_text(encoding='utf-8'))
 if sha(base)!=s['baseline_sha256'] or sha(data)!=m['output_sha256'] or sha(source)!=m['source_sha256'] or m['baseline_sha256']!=sha(base) or len(data)!=len(base):raise ValueError('menu product identity')
 if m['policy']!='development/PoC; NON-DISTRIBUTION':raise ValueError('development policy drift')
 for name,digest in m['menu_description_inputs'].items():
  if sha((p/name).read_bytes())!=digest:raise ValueError('menu build input drift '+name)
 for name in ['menu','chip_folder','chip_library','battle_caption','battle_active','descriptions']:
  if m['extension'][name]!=bm['extension'][name]:raise ValueError('inherited feature changed')
 t=m['extension']['menu_descriptions'];clone=t['archive_offset'];end=clone+t['archive_size']
 if t['contract_sha256']!=sha(sp.read_bytes()) or t['translation_asset_sha256']!=spec['draft_sha256'] or sha(data[clone:end])!=s['compiled_sha256']:raise ValueError('menu clone inputs')
 allowed=[(clone,end)];covered=bytearray(len(source));ranges=[]
 for w in m['expected_writes']:
  lo=w['offset'];hi=lo+w['size'];ranges.append((lo,hi))
  if sha(data[lo:hi])!=w['final_sha256']:raise ValueError('menu final writer hash')
  if lo<len(source):
   if hi>len(source) or sha(source[lo:hi])!=w['expected_sha256']:raise ValueError('menu preimage hash')
   covered[lo:hi]=b'\1'*(hi-lo)
 ranges.sort()
 if any(a[1]>b[0] for a,b in zip(ranges,ranges[1:])) or any(x!=y and not covered[i] for i,(x,y) in enumerate(zip(source,data))):raise ValueError('unplanned source difference')
 for c in s['consumers'].values():
  at=c['pointer_offset'];allowed.append((at,at+4))
  if data[at:at+4]!=(0x08000000+clone).to_bytes(4,'little') or sha(data[c['start']:at])!=c['context_sha256']:raise ValueError('menu pointer or executable context')
 diffs=[i for i,(x,y) in enumerate(zip(base,data)) if x!=y]
 if any(not any(lo<=i<hi for lo,hi in allowed) for i in diffs) or base[clone:end]!=b'\xff'*(end-clone):raise ValueError('unexplained baseline difference')
 third=s['preserved_other_menu_claim']
 if data[third:third+4]!=source[third:third+4]:raise ValueError('unclassified menu claim changed')
 for file,hashname in [('receipt','receipt_sha256'),('trace','trace_sha256')]:
  if sha((p/s['native_trace'][file]).read_bytes())!=s['native_trace'][hashname]:raise ValueError('menu source evidence drift')
 report['profiles'][key]={'rom_sha256':sha(data),'baseline_sha256':sha(base),'source_sha256':sha(source),'delta_bytes':len(diffs),
  'allowed_delta_ranges':allowed,'no_executable_changes':True,'unclassified_menu_claim_preserved':True,
  'source_preimages_verified':True,'inherited_custom_screen_description_preserved':True,'selected_scripts':10,'unselected_scripts_preserved':246}
run=subprocess.run([sys.executable,str(p/'tools/test_menu_descriptions.py')],capture_output=True)
log=p/'analysis/menu_descriptions_bench.log';log.write_bytes(run.stdout+run.stderr)
if run.returncode:raise ValueError('menu description CPU tests failed')
report['bench']={'return_code':0,'log':log.relative_to(p).as_posix(),'log_sha256':sha(log.read_bytes()),
 'scope':'both revisions: full 256-script byte preservation; 10 descriptions exact 1920-byte native parser output with bounds; two actual selectors x 311 IDs',
 'limitation':'final DMA helper stubbed in CPU fixture; actual VRAM requires emulator evidence; special IDs beyond310 not exercised'}
report['inputs']={name:sha((p/name).read_bytes()) for name in ['tools/build_menu_descriptions.py','tools/prepare_menu_chip_descriptions.py','tools/test_menu_descriptions.py','tools/verify_menu_descriptions.py','tools/specs/exe4_menu_descriptions_v2.json','translations/menu_chip_description_authored.json','translations/menu_chip_descriptions_korean_draft.json']}
(p/'analysis/menu_descriptions_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS both products: only two pointers + clone changed; 10 descriptions render within 1920 bytes')
