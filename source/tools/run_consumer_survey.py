"""Read-only consumer probes, continuing only an exact same-ROM checkpoint."""
import argparse,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--origin',type=Path,required=True)
ap.add_argument('--actions',required=True)
ap.add_argument('--probe',choices=['textread','exectrace','fontread','tilecalls','ramdump','chipcalls','vramwrites','bgqa','snapshot'],required=True)
ap.add_argument('--start',type=lambda x:int(x,0),default=0)
ap.add_argument('--end',type=lambda x:int(x,0),default=0)
ap.add_argument('--pc',type=lambda x:int(x,0),action='append',default=[])
a=ap.parse_args()
rom=p/'poc/output'/f'{a.key}_opening_menu_korean_development.gba'
m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'));data=rom.read_bytes()
origin=a.origin.resolve()
c=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),
 '--mesen','C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe',
 '--out',str(a.out.resolve()),'--expect-rom-sha256',m['output_sha256'],
 '--state',str(origin.parent/'checkpoint.mss'),'--state-origin',str(origin),
 '--actions',a.actions,'--probe',a.probe,'--timeout','120']
for at,size in [(0xa0,32),(0x800000,16)]+[(w['offset'],4) for w in m['expected_writes'] if w['size']==4]:
 c+=['--guard',f'{at}:'+data[at:at+size].hex()]
if a.probe in ('textread','vramwrites','bgqa'):
 if not a.start or a.end<a.start:raise ValueError('explicit bus range required')
 c+=['--watch-start',hex(a.start),'--watch-end',hex(a.end)]
if a.probe in ('fontread','tilecalls'):
 if not a.start or a.end<=a.start:raise ValueError('explicit font range required')
 c+=['--font-base',hex(a.start),'--font-end',hex(a.end),'--font-stride','64']
if a.probe in ('exectrace','chipcalls','bgqa'):
 if not a.pc:raise ValueError('explicit instruction sites required')
 for pc in a.pc:c+=['--trace-pc',hex(pc)]
subprocess.run(c,check=True)
