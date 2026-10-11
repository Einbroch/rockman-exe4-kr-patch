"""Sequential cold-boot ordinary-input QA of the dialogue extension."""
import argparse,json,subprocess,sys
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--mesen',type=Path,required=True);ap.add_argument('--font-probe',action='store_true')
args=ap.parse_args();p=Path(__file__).resolve().parents[1]
actions=','.join(['none:1:900','start:1:120','a:1:360','none:1:300']+['a:1:240']*60+['a:1:240','a:1:240','none:1:300','a:1:600','a:1:300','none:1:600'])
if args.font_probe:actions=','.join(['none:1:900','start:1:120','a:1:360','none:1:300']+['a:1:240']*5)
for key in ['blue_moon','red_sun']:
    suffix='hangul_boundary_visibility' if args.font_probe else 'opening_korean_extended_development'
    run='boundary_final' if args.font_probe else 'extended_v2_final'
    rom=p/'poc/output'/f'{key}_{suffix}.gba'
    m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'));ext=m['extension'];data=rom.read_bytes()
    at=ext['normal_font_offset']+ext['legacy_index_view']*96
    guards=['0xA0:'+data[0xa0:0xc0].hex(),'0x800000:'+data[0x800000:0x800010].hex(),f'{at}:'+data[at:at+96].hex()]
    for w in m['expected_writes']:
        if w['writer'] in ('normal_f9_slot','width_f9_slot','font_literal','advance_literal'):
            off=w['offset'];guards.append(f'{off}:'+data[off:off+4].hex())
    command=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),'--mesen',str(args.mesen),'--out',str(p/'analysis/runtime'/f'{key}_{run}'),'--expect-rom-sha256',m['output_sha256'],'--actions',actions,'--probe','fontread','--font-base',hex(0x08000000+at),'--font-end',hex(0x08000000+at+11172*96),'--font-stride','96','--timeout','240']
    for g in guards:command.extend(['--guard',g])
    subprocess.run(command,check=True)
print('both extended dialogue routes completed separately')
