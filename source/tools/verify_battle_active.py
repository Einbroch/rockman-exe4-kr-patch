"""Verify exact source writes, inherited bytes, final ISA and bounded CPU evidence."""
import argparse,json,subprocess,sys
from pathlib import Path
from analyze_project import PROFILES,sha
from extended_dialogue import assemble_verified
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);a=ap.parse_args()
sources={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
sp=p/'tools/specs/exe4_battle_active_v1.json';spec=json.loads(sp.read_text(encoding='utf-8'))
report={'schema':1,'status':'PASS static and CPU; runtime recorded separately',
        'scope':spec['scope'],'profiles':{},'not_claimed':['all names acquired in natural play','whole-battle localization','whole-game QA','independent language/font approval','device QA']}
for key,profile in PROFILES.items():
    source=sources[profile['sha256']];s=spec['profiles'][key]
    baseline=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_caption_korean_development.gba'
    target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba'
    base=baseline.read_bytes();bm=json.loads(baseline.with_suffix('.json').read_text(encoding='utf-8'))
    data=target.read_bytes();m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
    t=m['extension']['battle_active']
    if sha(base)!=bm['output_sha256'] or sha(data)!=m['output_sha256'] or m['source_sha256']!=sha(source):raise ValueError('product identity drift')
    if m['policy']!='development/PoC; NON-DISTRIBUTION' or len(data)!=0x1000000:raise ValueError('product scope drift')
    if t['contract_sha256']!=sha(sp.read_bytes()) or t['translation_asset_sha256']!=spec['catalog_sha256']:raise ValueError('caption contract drift')
    if t['archive_offsets']!=m['extension']['chip_library']['archive_offsets'] or t['new_VRAM_allocation']:raise ValueError('caption residency contract drift')
    for name in ['menu','chip_folder','chip_library','battle_caption']:
        if m['extension'][name]!=bm['extension'][name]:raise ValueError('inherited feature manifest changed')
    intervals=[];covered=bytearray(len(data))
    for w in m['expected_writes']:
        start=w['offset'];end=start+w['size'];intervals.append((start,end))
        if sha(data[start:end])!=w['final_sha256']:raise ValueError('final write drift')
        if start<len(source) and (end>len(source) or sha(source[start:end])!=w['expected_sha256']):raise ValueError('source preimage drift')
        covered[start:end]=b'\1'*(end-start)
    intervals.sort()
    if any(x[1]>y[0] for x,y in zip(intervals,intervals[1:])):raise ValueError('overlapping final writers')
    if any(x!=y and not covered[i] for i,(x,y) in enumerate(zip(source,data))):raise ValueError('unplanned source diff')
    ranges=[(s['hook']['offset'],s['hook']['offset']+8)]
    for part in t['layout']:
        start=part['offset'];end=start+part['size'];ranges.append((start,end))
        if sha(data[start:end])!=part['sha256'] or base[start:end]!=b'\xff'*(end-start):raise ValueError('new allocation overlaps inherited bytes')
    differences=[i for i,(x,y) in enumerate(zip(base,data)) if x!=y]
    if any(not any(lo<=i<hi for lo,hi in ranges) for i in differences):raise ValueError('unexpected delta from inherited library product')
    for code in t['machine_code']+t['jump_code']:
        rebuilt,_=assemble_verified('\n'.join(x['mnemonic']+' '+x['operands'] for x in code['instructions']),code['address'],code['literal_values'])
        off=code['address']-0x08000000
        if data[off:off+len(rebuilt)]!=rebuilt:raise ValueError('final ARM byte verification failed')
    report['profiles'][key]={'rom_sha256':sha(data),'baseline_sha256':sha(base),'source_sha256':sha(source),
        'delta_bytes':len(differences),'allowed_delta_ranges':ranges,'source_preimages_verified':True,
        'inherited_code_fonts_archives_bytes_unchanged':True,'final_ARM_verified':True,
        'caption_buffer':hex(s['destination']),'caption_VRAM':hex(s['vram']),'caption_bytes':512}
run=subprocess.run([sys.executable,str(p/'tools/test_battle_active.py')],capture_output=True)
log=p/'analysis/battle_active_bench.log';log.write_bytes(run.stdout+run.stderr)
if run.returncode:raise ValueError('battle caption CPU tests failed: '+str(log))
report['bench']={'log':log.relative_to(p).as_posix(),'log_sha256':sha(log.read_bytes()),'return_code':run.returncode,
    'scope':'both revisions IDs0..310, 294 exact names with tint0 and native padding, canaries, ABI; root42>=55 and unknown root fallback',
    'limitation':'native final DMA queue transport stubbed; real transfer separately requires emulator evidence',
    'test_sha256':sha((p/'tools/test_battle_active.py').read_bytes())}
report['inputs']={name:sha((p/name).read_bytes()) for name in [
    'tools/battle_active_extension.py','tools/build_opening_poc.py',
    'tools/test_battle_active.py','tools/verify_battle_active.py',
    'tools/extended_dialogue.py','tools/specs/exe4_battle_active_v1.json',
    'translations/chip_catalog_korean_draft.json']}
(p/'analysis/battle_active_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS two products; only 8-byte caller hook and appended selector differ; 622 ID executions')
