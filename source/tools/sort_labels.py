"""Folder SORT window items redrawn in Hangul (EXE 1 [K] 8x16 glyphs).

The window is a raw 8x17-cell map with its own 61-tile block (both raw in
ROM, the map right after the tiles); three screens load it (folder edit and
two link screens). Each item is a 16-pixel row of 8x16 glyphs in palette 6:
ink colour 1 with a lower-right shadow in colour 2 on the window grey 6.
The items are erased and redrawn, then the whole map is re-tiled by content
inside its block, keeping every cell's palette and flip bits.
"""
import json
from analyze_project import sha
from exe1k_hangul import load,ink as exe1k_ink

SPEC='tools/specs/exe4_sort_labels_v1.json'


def build(p,key,rom):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if sha(rom)!=prof['source_sha256']:raise ValueError('sort label source drift')
    to,mo=prof['tiles_offset'],prof['map_offset'];first,count=s['tile_first'],s['tile_count'];w,h=s['map_cells']
    tiles=rom[to:to+count*32];mp=rom[mo:mo+w*h*2]
    if sha(tiles)!=s['tiles_sha256'] or sha(mp)!=s['map_sha256']:raise ValueError('sort window art drift')
    g=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))['hangul_glyph_source']
    k1=load(g['path'])
    entry=lambda c:int.from_bytes(mp[c*2:c*2+2],'little')
    def tile(t):return tiles[(t-first)*32:(t-first+1)*32]
    img={}
    for c in range(w*h):
        e=entry(c)
        if e>>10&3 or not first<=e&1023<first+count:raise ValueError('sort window cell outside the plain block')
        for i,b in enumerate(tile(e&1023)):
            img[((c%w)*8+(i%4)*2,(c//w)*8+i//4)]=b&15
            img[((c%w)*8+(i%4)*2+1,(c//w)*8+i//4)]=b>>4
    old=dict(img)
    for item in s['items']:
        if item['text']==item['source']:continue
        x0,x1=item['columns'][0]*8,item['columns'][1]*8;y0=item['row']*8
        for q,v in old.items():
            if x0<=q[0]<x1 and y0<=q[1]<y0+16 and v in (s['ink'],s['shadow']):img[q]=s['background']
        pen=x0
        for ch in item['text']:
            if ch!=' ':
                for x,y in exe1k_ink(k1,ch):
                    if (pen+x+1,y0+y+1) in img and img[(pen+x+1,y0+y+1)]==s['background']:img[(pen+x+1,y0+y+1)]=s['shadow']
            pen+=8
        if pen>x1:raise ValueError('sort item does not fit: '+item['text'])
        pen=x0
        for ch in item['text']:
            if ch!=' ':
                for x,y in exe1k_ink(k1,ch):img[(pen+x,y0+y)]=s['ink']
            pen+=8
    def cell(c,src):
        cx,cy=(c%w)*8,(c//w)*8
        return bytes(src[(cx+(i%4)*2,cy+i//4)]|src[(cx+(i%4)*2+1,cy+i//4)]<<4 for i in range(32))
    cells={c:cell(c,img) for c in range(w*h)}
    assigned={}
    for c,data in cells.items():
        t=entry(c)&1023
        if data==tile(t) and data not in assigned and t not in assigned.values():assigned[data]=t
    pool=[t for t in range(first,first+count) if t not in assigned.values()]
    for c,data in cells.items():
        if data not in assigned:
            if not pool:raise ValueError('sort window tile budget exceeded: %d distinct cells' % len(set(cells.values())))
            assigned[data]=pool.pop(0)
    newtiles=bytearray(tiles);newmap=bytearray(mp)
    for data,t in assigned.items():newtiles[(t-first)*32:(t-first+1)*32]=data
    for c,data in cells.items():newmap[c*2:c*2+2]=(entry(c)&~1023|assigned[data]).to_bytes(2,'little')
    return [(to,bytes(newtiles),'SORT window tiles (Hangul items)'),(mo,bytes(newmap),'SORT window map')],{
        'items':[x['text'] for x in s['items']],'slots_left':len(pool),'spec_sha256':sha((p/SPEC).read_bytes())}
