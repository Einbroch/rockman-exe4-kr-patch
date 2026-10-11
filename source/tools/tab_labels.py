"""Folder-tab captions (ロックバスター, フォルダ, プログラム) redrawn in Hangul.

They are pixels in the shared UI tile set (tile 0 at 0x086DAE4C red /
0x086DA988 blue), which ten-odd PET screens load. Each caption is a run of
tiles between the tab's left edge (263) and its right end (66, 270); only the
caption tiles are rewritten, in place. The kana are grey (colour 9) with a
lower-right shadow (colour 4) and dark accents (colour 3) on the tab fill
(colour 5); the Hangul is Galmuri7 in colour 9 with the same shadow.
"""
import json
from analyze_project import sha
from pet_labels import glyphs

SPEC='tools/specs/exe4_tab_labels_v1.json'


def build(p,key,rom,font_path):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if sha(rom)!=prof['source_sha256'] or sha(font_path.read_bytes())!=s['font_sha256']:raise ValueError('tab label source drift')
    base=prof['tile0'];font=glyphs(font_path);writes=[];done=[]
    for tab in s['tabs']:
        tiles=tab['tiles']
        old=b''.join(rom[base+t*32:base+t*32+32] for t in tiles)
        if sha(old)!=tab['tiles_sha256']:raise ValueError('tab caption art drift '+tab['source'])
        px={}
        for c,t in enumerate(tiles):
            for i in range(64):
                b=rom[base+t*32+i//2];px[(c*8+i%8,i//8)]=b>>4 if i%2 else b&15
        for q,v in px.items():
            if v in s['erase_colours']:px[q]=s['fill_colour']
        pen=tab.get('left',s['left']);ink=set()
        for ch in tab['text']:
            dw,g=font[ch];ink|={(pen+x,y) for x,y in g};pen+=dw
        top=min(y for _,y in ink);ink={(x,y-top+s['top']) for x,y in ink}
        if max(x for x,_ in ink)>=len(tiles)*8 or max(y for _,y in ink)>7:raise ValueError('tab caption does not fit: '+tab['text'])
        for x,y in ink:
            if (x+1,y+1) not in ink and (x+1,y+1) in px:px[(x+1,y+1)]=s['shadow_colour']
        for q in ink:px[q]=s['ink_colour']
        for c,t in enumerate(tiles):
            data=bytes(px[(c*8+(i%4)*2,i//4)]|px[(c*8+(i%4)*2+1,i//4)]<<4 for i in range(32))
            writes.append((base+t*32,data,f"tab caption tile {t} ({tab['text']})"))
        done.append(tab['text'])
    return writes,{'tabs':done,'spec_sha256':sha((p/SPEC).read_bytes())}
