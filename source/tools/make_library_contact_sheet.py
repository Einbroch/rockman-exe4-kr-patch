"""Native-resolution source-library survey captures; no Korean library claim."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from analyze_project import sha
p=Path(__file__).resolve().parents[1];im=Image.new('RGB',(720,360),'#333333');draw=ImageDraw.Draw(im)
for row,key in enumerate(['blue_moon','red_sun']):
 for col,(kind,step) in enumerate([('source',3),('source',6),('bg',7)]):
  root=p/'analysis/runtime'/f'{key}_library_{kind}_survey_01';r=json.loads((root/'result.json').read_text(encoding='utf-8'));f=root/f'step_{step:03d}.png'
  if not r['complete'] or r['return_code'] or sha(f.read_bytes())!=r['artifacts'][f.name]:raise ValueError('unverified library capture')
  shot=Image.open(f)
  if shot.size!=(240,160):raise ValueError('not native GBA size')
  im.paste(shot,(col*240,row*180+20));draw.text((col*240+4,row*180+3),f'{key} {kind} step {step}',fill='white')
out=p/'analysis/visual_qa/library_source_two_versions.png';im.save(out);print(out)
