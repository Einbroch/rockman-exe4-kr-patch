"""Battle Custom Screen message panels redrawn with Korean lines.

ADD (CHIP DATA TRANSMISSION), NO DATA SELECTED and SHUFFLE are raw 7x6-tile
pictures shown in the chip-image window. Their English title stays; the
Japanese lines under it (ink colour 3, edge colour 2, on colour 1) are erased
and replaced, in place, by Galmuri9 lines centred in the panel.
"""
import json
from analyze_project import sha
from pet_labels import glyphs

SPEC='tools/specs/exe4_panel_labels_v1.json'


def line_pixels(font,text):
    pen=0;px=set()
    for c in text:
        dw,ink=font[c];px|={(pen+x,y) for x,y in ink};pen+=dw
    x0=min(x for x,_ in px);y0=min(y for _,y in px)
    return {(x-x0,y-y0) for x,y in px}


def build(p,key,rom,font_path):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'))
    if sha(rom)!=s['profiles'][key]['source_sha256'] or sha(font_path.read_bytes())!=s['font_sha256']:raise ValueError('panel label source drift')
    font=glyphs(font_path);writes=[]
    for panel in s['panels']:
        at=panel['offsets'][key];data=rom[at:at+1344]
        if sha(data)!=panel['sha256']:raise ValueError('panel art drift '+panel['name'])
        img={}
        for t in range(42):
            for i in range(64):
                b=data[t*32+i//2];img[((t%7)*8+i%8,(t//7)*8+i//8)]=b>>4 if i%2 else b&15
        y0,y1=panel['erase_rows']
        # Erased text becomes panel fill; on a frame row (a stroke that crossed
        # the bottom frame) it takes its nearest non-text neighbour's colour.
        text={(x,y) for (x,y),v in img.items() if y0<=y<y1 and x>=s['left_margin'] and v in (s['ink'],s['edge'])}
        fill_row={y:sum(img[(x,y)]==s['background'] for x in range(56))>=28 for y in range(48)}
        for x,y in sorted(text):
            img[(x,y)]=s['background'] if fill_row[y] else next(img[(x-d,y)] for d in range(1,x+1) if (x-d,y) not in text)
        top=panel['first_line_top']
        for line in panel['lines']:
            px=line_pixels(font,line);w=max(x for x,_ in px)+1;h=max(y for _,y in px)+1
            # Centre in the widest run of columns that are panel fill for the
            # whole line height (the frame cuts into the left edge on some rows).
            free=[all(img.get((x,top+y))==s['background'] for y in range(h)) for x in range(56)]
            runs=[];start=None
            for x in range(57):
                if x<56 and free[x]:start=x if start is None else start
                elif start is not None:runs.append((start,x));start=None
            a,b=max(runs,key=lambda r:r[1]-r[0])
            if b-a<w:raise ValueError('panel line too wide: '+line)
            left=a+(b-a-w)//2
            for x,y in px:
                q=(left+x,top+y)
                if img.get(q)!=s['background'] or not y0<=q[1]<y1:raise ValueError('panel line leaves the text area: %s at %s (%r)' % (line,q,img.get(q)))
                img[q]=s['ink']
            top+=panel['line_pitch']
        out=bytes(img[((t%7)*8+(i*2)%8,(t//7)*8+(i*2)//8)]|img[((t%7)*8+(i*2+1)%8,(t//7)*8+(i*2+1)//8)]<<4 for t in range(42) for i in range(32))
        writes.append((at,out,'Custom Screen panel '+panel['name']+' (Korean lines)'))
    return writes,{'panels':[x['name'] for x in s['panels']],'spec_sha256':sha((p/SPEC).read_bytes())}
