"""Battle result window labels (デリートタイム / バスティングレベル) redrawn.

The result window is a raw 24x17 BG map over raw 4bpp tiles (palette 9). Each
label is a two-row band (top row on fill tile 0x19, bottom row on fill 0x24,
whose lower half is the box's bottom line); the two labels share bottom-row
tiles and their dakuten stick up into the border rows. The bands are redrawn
whole (ink 1, shadow 8 one pixel right and down, as the source), every 8x8
cell is matched to a fill tile or given a tile from the pool of tiles only the
labels used, and the dakuten cells of the border rows go back to the plain
border tile. Tiles and map are rewritten in place.
"""
import json
from analyze_project import sha
from pet_labels import glyphs, text_pixels

SPEC='tools/specs/exe4_result_labels_v1.json'


def build(p,key,rom,font_path):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if sha(rom)!=prof['source_sha256'] or sha(font_path.read_bytes())!=s['font_sha256']:raise ValueError('result label source drift')
    tb,mb,W,H=prof['tiles'],prof['map'],s['map_width'],s['map_height']
    tiles=bytearray(rom[tb:tb+s['tile_count']*32]);mp=bytearray(rom[mb:mb+W*H*2])
    if sha(bytes(tiles))!=s['tiles_sha256'] or sha(bytes(mp))!=s['map_sha256']:raise ValueError('result window art drift')
    def tile_px(t):return [[(tiles[t*32+y*4+x//2]>>4) if x&1 else tiles[t*32+y*4+x//2]&15 for x in range(8)] for y in range(8)]
    def entry(r,c):return int.from_bytes(mp[(r*W+c)*2:(r*W+c)*2+2],'little')
    def set_entry(r,c,t):
        e=entry(r,c);mp[(r*W+c)*2:(r*W+c)*2+2]=((e&~0x3ff)|t).to_bytes(2,'little')
    pool=list(s['pool']);used={}
    # The pool must be the label tiles only: nothing outside the bands may use them.
    band={(l['row']+d,c) for l in s['labels'] for d in (0,1) for c in range(l['first'],l['last']+1)}
    for r in range(H):
        for c in range(W):
            if (entry(r,c)&0x3ff) in pool and (r,c) not in band and [r,c] not in s['border_cells']:raise ValueError('pool tile used outside the label bands')
    font=glyphs(font_path);fills=s['fills'];cells={}
    for l in s['labels']:
        width=(l['last']-l['first']+1)*8
        img=[[0]*width for _ in range(16)]
        for half,fill in enumerate(fills):
            px=tile_px(fill)
            for y in range(8):
                for x in range(width):img[half*8+y][x]=px[y][x%8]
        ink=text_pixels(font,l['text'],s.get('bold',False))
        tw=max(x for x,_ in ink)+2;th=max(y for _,y in ink)+2
        if tw+l['left']>width or th+s['top']>s['ink_rows']:raise ValueError('result label does not fit: '+l['text'])
        q={(x+l['left'],y+s['top']) for x,y in ink}
        for x,y in q:
            if (x+1,y+1) not in q:img[y+1][x+1]=s['shadow']
        for x,y in q:img[y][x]=s['ink']
        for half in (0,1):
            for k in range(l['last']-l['first']+1):
                cell=tuple(tuple(img[half*8+y][k*8:k*8+8]) for y in range(8))
                cells[(l['row']+half,l['first']+k)]=(cell,fills[half])
    for (r,c),(cell,fill) in sorted(cells.items()):
        if cell==tuple(tuple(row) for row in tile_px(fill)):set_entry(r,c,fill);continue
        if cell not in used:
            if not pool:raise ValueError('result label tile pool exhausted')
            t=pool.pop(0);used[cell]=t
            for y in range(8):
                for x in range(0,8,2):tiles[t*32+y*4+x//2]=cell[y][x]|cell[y][x+1]<<4
        set_entry(r,c,used[cell])
    for r,c in s['border_cells']:set_entry(r,c,s['border_tile'])
    for t in pool:
        for i in range(32):tiles[t*32+i]=tiles[fills[0]*32+i]
    return [(tb,bytes(tiles),'result window label tiles'),(mb,bytes(mp),'result window label map')],{
        'labels':[l['text'] for l in s['labels']],'tiles_used':len(used),'pool_left':len(pool),'spec_sha256':sha((p/SPEC).read_bytes())}
