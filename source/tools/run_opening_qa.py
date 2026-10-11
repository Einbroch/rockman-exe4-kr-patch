"""Sequential cold-boot QA; no shared settings writes; loaded-ROM guards."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--mesen',type=Path,required=True)
ap.add_argument('--resume-only',action='store_true')
ap.add_argument('--exit-only',action='store_true')
ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
args=ap.parse_args();p=args.project.resolve()
actions=','.join(['none:1:900','start:1:120','a:1:360','none:1:300']+['a:1:240']*60)
for key in ['blue_moon','red_sun']:
    rom=p/'poc/output'/f'{key}_opening_korean_development.gba'
    manifest=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'))
    data=rom.read_bytes()
    first=min(manifest['mapping'].values())
    glyph_at=int(manifest['font_base'],16)+first*96
    guards=[f'0xA0:{data[0xA0:0xC0].hex()}',f'{glyph_at}:{data[glyph_at:glyph_at+96].hex()}','0x800000:'+data[0x800000:0x800010].hex()]
    command=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),'--mesen',str(args.mesen),'--out',str(p/'analysis/runtime'/f'{key}_opening_final'),'--expect-rom-sha256',manifest['output_sha256'],'--actions',actions,'--probe','none','--timeout','240']
    for guard in guards:command.extend(['--guard',guard])
    if not args.resume_only and not args.exit_only:subprocess.run(command,check=True)
    origin=p/'analysis/runtime'/f'{key}_opening_final'
    continuation=command.copy()
    continuation[continuation.index('--out')+1]=str(p/'analysis/runtime'/f'{key}_opening_end')
    continuation[continuation.index('--actions')+1]='a:1:240,a:1:240,none:1:300'
    continuation.extend(['--state',str(origin/'checkpoint.mss'),'--state-origin',str(origin/'result.json')])
    if not args.exit_only:subprocess.run(continuation,check=True)
    origin=p/'analysis/runtime'/f'{key}_opening_end'
    continuation[continuation.index('--out')+1]=str(p/'analysis/runtime'/f'{key}_opening_exit')
    continuation[continuation.index('--actions')+1]='a:1:600,a:1:300,none:1:600'
    continuation[continuation.index('--state')+1]=str(origin/'checkpoint.mss')
    continuation[continuation.index('--state-origin')+1]=str(origin/'result.json')
    subprocess.run(continuation,check=True)
print('both opening diagnostic runs completed separately')
