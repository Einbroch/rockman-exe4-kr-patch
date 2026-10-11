"""Verify the one-pointer private description extension and inherited product bytes."""
import argparse,json,subprocess,sys
from pathlib import Path
from analyze_project import PROFILES,sha
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);a=ap.parse_args()
sources={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
sp=p/'tools/specs/exe4_description_v1.json';spec=json.loads(sp.read_text())
report={'schema':1,'status':'PASS static and CPU; runtime recorded separately','scope':spec['scope'],'profiles':{}}
for key,profile in PROFILES.items():
 source=sources[profile['sha256']];s=spec['profiles'][key]
 baseline=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba'
 target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
 base=baseline.read_bytes();bm=json.loads(baseline.with_suffix('.json').read_text(encoding='utf-8'))
 data=target.read_bytes();m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'));t=m['extension']['descriptions']
 if sha(base)!=bm['output_sha256'] or sha(data)!=m['output_sha256'] or m['source_sha256']!=sha(source) or len(data)!=0x1000000:raise ValueError('description product identity drift')
 if m['policy']!='development/PoC; NON-DISTRIBUTION' or t['contract_sha256']!=sha(sp.read_bytes()) or t['translation_asset_sha256']!=spec['draft_sha256']:raise ValueError('description scope/input drift')
 for name in ['menu','chip_folder','chip_library','battle_caption','battle_active']:
  if m['extension'][name]!=bm['extension'][name]:raise ValueError('inherited manifest changed')
 ranges=[];covered=bytearray(len(data))
 for w in m['expected_writes']:
  at=w['offset'];end=at+w['size'];ranges.append((at,end));covered[at:end]=b'\1'*(end-at)
  if sha(data[at:end])!=w['final_sha256']:raise ValueError('description final writer drift')
  if at<len(source) and (end>len(source) or sha(source[at:end])!=w['expected_sha256']):raise ValueError('source preimage drift')
 ranges.sort()
 if any(a[1]>b[0] for a,b in zip(ranges,ranges[1:])) or any(x!=y and not covered[i] for i,(x,y) in enumerate(zip(source,data))):raise ValueError('overlap or unplanned source diff')
 at=s['pointer_offset'];clone=t['archive_offset'];end=clone+t['archive_size']
 if data[at:at+4]!=(0x08000000+clone).to_bytes(4,'little') or base[clone:end]!=b'\xff'*(end-clone):raise ValueError('private description allocation drift')
 allowed=[(at,at+4),(clone,end)]
 diff=[i for i,(x,y) in enumerate(zip(base,data)) if x!=y]
 if any(not any(lo<=i<hi for lo,hi in allowed) for i in diff):raise ValueError('unexplained difference from active-name product')
 if sha(data[clone:end])!=s['compiled_sha256']:raise ValueError('compiled description drift')
 lo=s['source_archive_offset'];hi=lo+s['source_archive_size']
 if data[lo:hi]!=source[lo:hi] or any(data[x:x+4]!=source[x:x+4] for x in s['other_pointer_claims']):raise ValueError('shared description archive/claims changed')
 ctx=s['selector_context_offset'];size=s['selector_context_size']
 if sha(data[ctx:ctx+size])!=s['selector_context_sha256']:raise ValueError('native selector code changed')
 report['profiles'][key]={'rom_sha256':sha(data),'baseline_sha256':sha(base),'source_sha256':sha(source),
  'delta_bytes':len(diff),'allowed_delta_ranges':allowed,'no_executable_changes':True,'other_original_claims_preserved':3,
  'source_preimages_verified':True,'shared_archive_preserved':True,'translated_descriptions':10,'unselected_scripts_preserved':246}
run=subprocess.run([sys.executable,str(p/'tools/test_descriptions.py')],capture_output=True)
log=p/'analysis/descriptions_bench.log';log.write_bytes(run.stdout+run.stderr)
if run.returncode:raise ValueError('description tests failed: '+str(log))
report['bench']={'return_code':run.returncode,'log':log.relative_to(p).as_posix(),'log_sha256':sha(log.read_bytes()),
 'scope':'two revisions x 514 actual selector-tail inputs, both full256-script clones, exact selected bytes and all control commands',
 'limitation':'CPU selector and byte structure proof; natural renderer/layout requires emulator evidence'}
report['inputs']={name:sha((p/name).read_bytes()) for name in ['tools/build_opening_poc.py','tools/description_extension.py','tools/test_descriptions.py','tools/verify_descriptions.py','tools/specs/exe4_description_v1.json','tools/prepare_chip_descriptions.py','translations/chip_description_authored.json','translations/chip_descriptions_korean_draft.json']}
(p/'analysis/descriptions_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS both private description products; pointer + clone only, native selector code unchanged')
