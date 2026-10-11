"""Freeze two runtime-observed tile-description consumers; leave third claim native."""
import json
from pathlib import Path
from analyze_project import sha, PROFILES
p=Path(__file__).resolve().parents[1]
report=json.loads((p/'analysis/menu_chip_description_analysis.json').read_text(encoding='utf-8'))
spec={'schema':1,'scope':'folder edit and seven-row library ten descriptions; NON-DISTRIBUTION needs_review',
      'cells':10,'visible_cells':9,'lines':3,'draft_sha256':report['draft_sha256'],'profiles':{}}
for key,folder,library,trace in [('blue_moon',0x106a54,0x10987c,'blue_moon_menu_description_trace_01'),
                                ('red_sun',0x106ac4,0x1098ec,'red_sun_menu_description_trace_01')]:
 source=next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes())==PROFILES[key]['sha256'])
 rp=p/'analysis/runtime'/trace/'result.json';r=json.loads(rp.read_text(encoding='utf-8'))
 baseline=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
 if not r['complete'] or r['return_code'] or r['rom_sha256']!=sha(baseline.read_bytes()):raise ValueError('native menu trace attribution')
 tp=rp.with_name('exectrace_final.json');sites={int(x['pc'],16):x for x in json.loads(tp.read_text())['sites']}
 root=0x08000000+report['profiles'][key]['archive_offset'];consumers={}
 for label,start,call,ptr,vram in [('folder',folder,folder+0x2e,folder+0x70,0x06011600),('library',library,library+0x24,library+0x2c,0x06011800)]:
  site=sites[0x08000000+call];regs=site['first_regs']
  expected={'cpu.r0':root,'cpu.r1':1,'cpu.r2':0x02017800,'cpu.r3':vram,'cpu.r4':10,'cpu.r5':3,'cpu.r7':0}
  if site['hits']<1 or any(regs[k]!=v for k,v in expected.items()):raise ValueError('observed menu ABI differs')
  if int.from_bytes(source[ptr:ptr+4],'little')!=root:raise ValueError('menu pointer preimage differs')
  consumers[label]={'start':start,'call':call,'pointer_offset':ptr,'context_size':ptr-start,'context_sha256':sha(source[start:ptr]),
    'destination':regs['cpu.r2'],'vram':vram,'font':regs['cpu.r6'],'observed_hits':site['hits']}
 spec['profiles'][key]={'source_sha256':sha(source),'baseline_sha256':sha(baseline.read_bytes()),'source_pointer':root,
  'compiled_sha256':report['profiles'][key]['compiled_sha256'],'consumers':consumers,
  'preserved_other_menu_claim':0x106dac if key=='blue_moon' else 0x106e1c,
  'native_trace':{'receipt':rp.relative_to(p).as_posix(),'receipt_sha256':sha(rp.read_bytes()),
                  'trace':tp.relative_to(p).as_posix(),'trace_sha256':sha(tp.read_bytes())}}
(p/'tools/specs/exe4_menu_descriptions_v2.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('PASS source-bound folder and library contracts, both revisions')
