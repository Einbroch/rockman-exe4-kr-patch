"""Display actual accepted menu captures at native resolution."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
p=Path(__file__).resolve().parents[1];out=p/'analysis/visual_qa/menu_two_versions.png'
canvas=Image.new('RGB',(720,360),'#333333');draw=ImageDraw.Draw(canvas)
for row,key in enumerate(['blue_moon','red_sun']):
 root=p/'analysis/runtime'/f'{key}_menu_final_02';r=json.loads((root/'result.json').read_text(encoding='utf-8'))
 if not r['complete'] or r['return_code']!=0 or r['steps_captured']!=107:raise ValueError('unaccepted menu run')
 for col,(step,label) in enumerate([(92,'PET room label'),(93,'folder 1'),(102,'save labels')]):
  f=root/f'step_{step:03d}.png';im=Image.open(f)
  if im.size!=(240,160):raise ValueError('not native GBA size')
  canvas.paste(im,(col*240,row*180+20));draw.text((col*240+4,row*180+3),f'{key} {label}',fill='white')
out.parent.mkdir(exist_ok=True);canvas.save(out);print(out)
