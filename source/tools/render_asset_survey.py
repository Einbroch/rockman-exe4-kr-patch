"""Render source bytes for investigation; produces no replacement assets."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw
ap=argparse.ArgumentParser()
ap.add_argument('--rom',type=Path,required=True)
ap.add_argument('--offset',type=lambda x:int(x,0),required=True)
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
rom=args.rom.read_bytes()
panels=[]
for depth,width,height in [(4,16,12),(4,8,16),(2,8,16),(1,8,16),(1,16,16),(2,8,12),(1,16,12)]:
    count,cols=256,32
    cellbytes=width*height*depth//8
    im=Image.new('RGB',(cols*width,8*height+20),'white')
    draw=ImageDraw.Draw(im)
    draw.text((0,0),f'{depth}bpp {width}x{height} at {args.offset:06X}',fill='black')
    for index in range(count):
        data=rom[args.offset+index*cellbytes:args.offset+(index+1)*cellbytes]
        for y in range(height):
            for x in range(width):
                bit=(y*width+x)*depth
                value=(data[bit//8]>>(bit%8))&((1<<depth)-1)
                # Generic packed view. Tile ordering is a separate hypothesis.
                col=255-value*255//((1<<depth)-1)
                im.putpixel(((index%cols)*width+x,20+(index//cols)*height+y),(col,col,col))
    panels.append(im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST))
out=Image.new('RGB',(max(p.width for p in panels),sum(p.height for p in panels)), 'gray')
cursor=0
for panel in panels:
    out.paste(panel,(0,cursor));cursor+=panel.height
args.out.parent.mkdir(parents=True,exist_ok=True)
out.save(args.out)
