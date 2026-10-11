"""Observe Hangul font-record reads while opening the exact same descriptions."""
import argparse,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True);a=ap.parse_args()
origin=p/'analysis/runtime'/f'{a.key}_descriptions_ready_01';r=json.loads((origin/'result.json').read_text(encoding='utf-8'))
steps=json.loads((p/'analysis/runtime'/f'{a.key}_descriptions_final_01/result.json').read_text(encoding='utf-8'))
m=json.loads(Path(r['rom_path']).with_suffix('.json').read_text(encoding='utf-8'))
base=0x08000000+m['extension']['normal_font_offset']+442*96
c=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',r['rom_path'],'--mesen',r['emulator_path'],
 '--out',str(p/'analysis/runtime'/f'{a.key}_descriptions_reads_01'),'--expect-rom-sha256',r['rom_sha256'],
 '--state',str(origin/'checkpoint.mss'),'--state-origin',str(origin/'result.json'),'--actions',steps['actions'],
 '--probe','fontread','--font-base',hex(base),'--font-end',hex(base+11172*96-1),'--font-stride','96','--timeout','300']
for guard in r['loaded_rom_guards']:c+=['--guard',guard]
subprocess.run(c,check=True)
