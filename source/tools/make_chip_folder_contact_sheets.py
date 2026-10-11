"""Preserve native screenshot pixels in bounded review contact sheets."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
for name,steps in [('chip_folder_two_versions',[('final',1),('final',5),('final',12),('final',17),('final',24)]),('chip_folder_regression_two_versions',[('cold',107),('final',33),('final',35),('final',38)])]:
 canvas=Image.new('RGB',(240*len(steps),360),'#333333');draw=ImageDraw.Draw(canvas)
 for row,key in enumerate(['blue_moon','red_sun']):
  for col,(kind,step) in enumerate(steps):
   root=p/'analysis/runtime'/f'{key}_chip_folder_{kind}_01';r=json.loads((root/'result.json').read_text(encoding='utf-8'));f=root/f'step_{step:03d}.png'
   if not r['complete'] or r['return_code'] or sha(f.read_bytes())!=r['artifacts'][f.name]:raise ValueError('unverified capture')
   im=Image.open(f)
   if im.size!=(240,160):raise ValueError('not native GBA resolution')
   canvas.paste(im,(col*240,row*180+20));draw.text((col*240+4,row*180+3),f'{key} {kind} step {step}',fill='white')
 out=p/'analysis/visual_qa'/(name+'.png');canvas.save(out);print(out)
