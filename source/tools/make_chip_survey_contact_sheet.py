"""Native-resolution diagnostic evidence; preserves all screenshot pixels."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
canvas=Image.new('RGB',(720,360),'#333333');draw=ImageDraw.Draw(canvas)
for row,key in enumerate(['blue_moon','red_sun']):
 root=p/'analysis/runtime'/f'{key}_folder_chip_inventory_01';r=json.loads((root/'result.json').read_text(encoding='utf-8'))
 if not r['complete'] or r['return_code'] or r['steps_captured']!=31:raise ValueError('incomplete chip survey')
 for col,step in enumerate([1,12,24]):
  f=root/f'step_{step:03d}.png'
  if sha(f.read_bytes())!=r['artifacts'][f.name]:raise ValueError('capture hash drift')
  im=Image.open(f)
  if im.size!=(240,160):raise ValueError('not native GBA size')
  canvas.paste(im,(col*240,row*180+20));draw.text((col*240+4,row*180+3),f'{key} source chips, step {step}',fill='white')
out=p/'analysis/visual_qa/chip_consumer_two_versions.png';canvas.save(out);print(out)
