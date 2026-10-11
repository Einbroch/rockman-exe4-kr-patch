"""Continue exact-ROM natural-input research; preserve receipts and captures."""
import argparse, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw

p = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('origin')
ap.add_argument('output')
ap.add_argument('actions')
ap.add_argument('--probe', default='exectrace')
ap.add_argument('--pc', action='append')
a = ap.parse_args()
origin = p / 'analysis/runtime' / a.origin / 'result.json'
r = json.loads(origin.read_text(encoding='utf-8'))
out = p / 'analysis/runtime' / a.output
c = [sys.executable, str(p/'tools/run_mesen_segment.py'), '--rom', r['rom_path'],
     '--mesen', r['emulator_path'], '--out', str(out), '--expect-rom-sha256', r['rom_sha256'],
     '--state', str(origin.parent/'checkpoint.mss'), '--state-origin', str(origin),
     '--actions', a.actions, '--probe', a.probe, '--timeout', '300']
for guard in r['loaded_rom_guards']:
    c += ['--guard', guard]
if a.probe == 'exectrace':
    for pc in a.pc or r.get('trace_pc', []):
        c += ['--trace-pc', pc]
subprocess.run(c, check=True)
fs = sorted(out.glob('step_*.png'))
ims = [Image.open(f).convert('RGB') for f in fs]
w, h = ims[0].size
cols = min(4, len(ims))
sheet = Image.new('RGB', (cols*w, ((len(ims)+cols-1)//cols)*(h+20)), 'white')
d = ImageDraw.Draw(sheet)
for i, im in enumerate(ims):
    x, y = (i%cols)*w, (i//cols)*(h+20)
    sheet.paste(im, (x, y+20))
    d.text((x+4, y+3), fs[i].stem, fill='black')
sheet.save(out/'contact.png')
