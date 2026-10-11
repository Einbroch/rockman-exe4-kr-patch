"""Arrange accepted captures for visual inspection; never alter game assets."""
from pathlib import Path
from PIL import Image, ImageDraw
import argparse,math
ap=argparse.ArgumentParser();ap.add_argument('--run-suffix',choices=['opening_final','extended_v2_final'],default='opening_final')
args=ap.parse_args()
p=Path(__file__).resolve().parents[1]
out=p/'analysis/visual_qa';out.mkdir(exist_ok=True)
for key in ['blue_moon','red_sun']:
    root=p/'analysis/runtime'/f'{key}_{args.run_suffix}'
    files=sorted(root.glob('step_*.png'))
    if len(files)!=(70 if args.run_suffix=='extended_v2_final' else 64):raise ValueError('incomplete final capture set')
    for page in range(math.ceil(len(files)/32)):
        canvas=Image.new('RGB',(4*240,8*180),'#333333')
        draw=ImageDraw.Draw(canvas)
        for i,f in enumerate(files[page*32:(page+1)*32]):
            x,y=(i%4)*240,(i//4)*180
            with Image.open(f) as im:
                if im.size!=(240,160):raise ValueError('unexpected GBA screenshot size')
                canvas.paste(im,(x,y+20))
            draw.text((x+4,y+3),f'{key} {f.stem}',fill='white')
        label='opening' if args.run_suffix=='opening_final' else 'extended'
        canvas.save(out/f'{key}_{label}_{page+1}.png')
print('source-capture contact sheets created for',args.run_suffix)
