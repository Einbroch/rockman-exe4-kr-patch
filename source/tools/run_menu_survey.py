"""Read-only menu investigation, with guards derived from the selected ROM."""
import argparse,json,subprocess,sys
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--rom',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--origin',type=Path,required=True)
ap.add_argument('--actions',required=True)
ap.add_argument('--probe',choices=['exectrace','ramdump','fontread','tilecalls'],default='exectrace')
ap.add_argument('--font-base',type=lambda x:int(x,0),default=0x0868e004)
ap.add_argument('--font-end',type=lambda x:int(x,0),default=0x08695004)
args=ap.parse_args();p=Path(__file__).resolve().parents[1]
rom=args.rom.resolve();data=rom.read_bytes()
m=json.loads(rom.with_suffix('.json').read_text(encoding='utf-8'))
origin=args.origin.resolve()
command=[sys.executable,str(p/'tools/run_mesen_segment.py'),'--rom',str(rom),
 '--mesen','C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe',
 '--out',str(args.out.resolve()),'--expect-rom-sha256',m['output_sha256'],
 '--state',str(origin.parent/'checkpoint.mss'),'--state-origin',str(origin),
 '--actions',args.actions,'--probe',args.probe,'--timeout','120']
guards=[(0xa0,32),(0x800000,16)]
guards += [(w['offset'],w['size']) for w in m['expected_writes'] if w['size']==4]
for at,size in guards:command.extend(['--guard',f'{at}:'+data[at:at+size].hex()])
if args.probe=='exectrace':
 for pc in (0x0300677c,0x0300679c,0x030067f0,0x0300692c):
  command.extend(['--trace-pc',hex(pc)])
if args.probe in ('fontread','tilecalls'):
 command.extend(['--font-base',hex(args.font_base),'--font-end',hex(args.font_end),'--font-stride','64'])
subprocess.run(command,check=True)
