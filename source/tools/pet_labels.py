"""PET main menu labels redrawn in Hangul inside the raw BG tiles.

The eight katakana labels (チップフォルダ .. セーブ) are pixels in the PET
module's tile block, laid out by its 32x20 map. Each label is drawn in its own
palette-14 colour (8 + row): the game highlights the selected row by turning
that colour white, so a redrawn label must keep its row's colour. The katakana
and their drop shadow are erased back to the box fill, the Hangul is drawn at
the katakana's top-left in bold Galmuri9 with the same shadow, and the changed
map cells are re-tiled into the tile slots only those cells used.
"""
import json
from analyze_project import sha

SPEC='tools/specs/exe4_pet_labels_v1.json'


def glyphs(path):
    out={}
    for block in path.read_text(encoding='ascii').split('STARTCHAR ')[1:]:
        lines=block.splitlines();cp=int(next(x.split()[1] for x in lines if x.startswith('ENCODING ')))
        w,h,xo,yo=map(int,next(x for x in lines if x.startswith('BBX ')).split()[1:])
        dw=int(next(x.split()[1] for x in lines if x.startswith('DWIDTH ')))
        start=lines.index('BITMAP')+1;rows=[int(r,16) for r in lines[start:start+h]]
        pad=((w+7)//8)*8
        out[chr(cp)]=(dw,{(xo+x,-(h+yo)+y) for y,r in enumerate(rows) for x in range(w) if r&(1<<(pad-1-x))})
    return out


def text_pixels(font,text,bold=False):
    """Pixels of text relative to its top-left ink corner; bold adds a column."""
    pen=0;px=set()
    for c in text:
        dw,ink=font[c]
        for x,y in ink:px|={(pen+x,y),(pen+x+1,y)} if bold else {(pen+x,y)}
        pen+=dw+(1 if bold else 0)
    if not px:raise ValueError('empty PET label')
    x0=min(x for x,_ in px);y0=min(y for _,y in px)
    return {(x-x0,y-y0) for x,y in px}


def build(p,key,rom,font_path):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if sha(rom)!=prof['source_sha256']:raise ValueError('PET label source identity drift')
    if sha(font_path.read_bytes())!=s['font']['sha256']:raise ValueError('PET label font drift')
    to,mo=prof['tiles_offset'],prof['map_offset'];first,count=s['tile_first'],s['tile_count']
    tiles=rom[to:to+count*32];mp=rom[mo:mo+1280]
    if sha(tiles)!=prof['tiles_sha256'] or sha(mp)!=prof['map_sha256']:raise ValueError('PET label art drift')
    for lit,at in ((prof['tiles_literal'],to),(prof['map_literal'],mo)):
        if int.from_bytes(rom[lit:lit+4],'little')!=0x08000000+at:raise ValueError('PET label reference drift')
    (c0,c1),(r0,r1)=s['region']['columns'],s['region']['rows']
    entry=lambda tx,ty:int.from_bytes(mp[(ty*32+tx)*2:(ty*32+tx)*2+2],'little')
    def tile(t):return tiles[(t-first)*32:(t-first+1)*32]
    img={}
    for ty in range(r0,r1):
        for tx in range(c0,c1):
            e=entry(tx,ty)
            if e>>10&3 or e>>12!=s['palette'] or not first<=e&1023<first+count:raise ValueError('PET label cell outside the plain block')
            data=tile(e&1023)
            for i,b in enumerate(data):
                img[((tx-c0)*8+(i%4)*2,(ty-r0)*8+i//4)]=b&15
                img[((tx-c0)*8+(i%4)*2+1,(ty-r0)*8+i//4)]=b>>4
    old=dict(img);font=glyphs(font_path)
    wording=json.loads((p/'translations/pet_labels_korean.json').read_text(encoding='utf-8'))
    if [x['row'] for x in wording['entries']]!=list(range(8)):raise ValueError('PET label rows drift')
    box=set(s['box_colours']);shades=set(s['shadow_colours']);placements=[]
    for x in wording['entries']:
        colour=s['label_colour_base']+x['row']
        text={q for q,v in old.items() if v==colour}
        if not text:raise ValueError('PET label colour absent '+x['source'])
        # The shadow is mostly (+1,+1) but not only; inside a label's box the
        # shadow colours occur nowhere else, so take them around the text.
        x0,x1=min(a for a,_ in text)-2,max(a for a,_ in text)+2;y0,y1=min(b for _,b in text)-2,max(b for _,b in text)+2
        shadow={(a,b) for (a,b),v in old.items() if v in shades and x0<=a<=x1 and y0<=b<=y1}
        kind=max(shades,key=lambda c:sum(old[q]==c for q in shadow))
        for q in sorted(text|shadow):
            a,b=q;fill=next((old[(a-d,b)] for d in range(1,40) if (a-d,b) in old and (a-d,b) not in text|shadow),None)
            if fill not in box:raise ValueError('PET label fill is not the box colour: %s at %s got %r' % (x['source'],q,fill))
            img[q]=fill
        left=min(a for a,_ in text);top=min(b for _,b in text)
        # Centre the Hangul and its shadow in the box: the box is the run of
        # rows around the katakana whose pixel two columns in is box, text or
        # shadow (the user saw the bold labels sit high in the box).
        # The katakana stand over the box's top edge, so the box is measured on
        # the box colours alone: the run of rows around the text where most of
        # the label's width is box fill once the katakana are erased.
        span=range(left,left+40)
        def boxy(row):return sum(img.get((a,row)) in box for a in span)>=20
        mid=next(r for r in range(top,top+12) if boxy(r))
        box_top=mid
        while boxy(box_top-1):box_top-=1
        box_bot=mid
        while boxy(box_bot+1):box_bot+=1
        shape=text_pixels(font,x['text'],s.get('bold',False))
        height=max(b for _,b in shape)+2
        top=box_top+(box_bot-box_top+1-height+1)//2
        placements.append((x['text'],colour,kind,shape,left,top))
    def cell_bytes(tx,ty,src):
        return bytes(src[((tx-c0)*8+(i%4)*2,(ty-r0)*8+i//4)]|src[((tx-c0)*8+(i%4)*2+1,(ty-r0)*8+i//4)]<<4 for i in range(32))
    def drawn(choice):
        out=dict(img)
        for (text,colour,kind,shape,left,top),(dx,dy) in zip(placements,choice):
            new={(left+dx+a,top+dy+b) for a,b in shape}
            # Hangul and its shadow must land on the label's own box.
            for q in new|{(a+1,b+1) for a,b in new}:
                if old.get(q) not in box|{colour}|shades:return None
            for a,b in new:
                if (a+1,b+1) not in new:out[(a+1,b+1)]=kind
            for q in new:out[q]=colour
        return out
    def distinct(src):
        seen=set()
        for i in range(640):
            q=(i%32,i//32);e=entry(*q)
            if first<=e&1023<first+count:
                seen.add(cell_bytes(*q,src) if c0<=q[0]<c1 and r0<=q[1]<r1 else tile(e&1023))
        return len(seen)
    # Thin Hangul sits across tile rows differently from the katakana, so a
    # centred layout can need a few more distinct tiles than the block holds.
    # Each label may move one pixel from centre; the move that needs the
    # fewest tiles wins, centre first on ties.
    moves=[(0,0),(0,1),(0,-1),(1,0),(1,1),(1,-1)]
    choice=[(0,0)]*len(placements)
    for k in range(len(placements)):
        best=None
        for m in moves:
            trial=choice[:k]+[m]+choice[k+1:];out=drawn(trial)
            if out is None:continue
            n=distinct(out)
            if best is None or n<best[0]:best=(n,m)
        if best is None:raise ValueError('PET label overflows its box: '+placements[k][0])
        choice[k]=best[1]
    img=drawn(choice)
    # Re-tile the map by content (see below).
    changed={(tx,ty) for ty in range(r0,r1) for tx in range(c0,c1) if cell_bytes(tx,ty,img)!=cell_bytes(tx,ty,old)}
    region={(tx,ty) for ty in range(r0,r1) for tx in range(c0,c1)}
    # The block and its map belong to the PET screen alone (one ROM reference
    # each), so the whole map is re-tiled by content: identical tiles merge,
    # every cell outside the label region keeps exactly its pixels and flip
    # bits, and each tile keeps its own index while its content still lives.
    cells={}
    for i in range(640):
        q=(i%32,i//32);e=entry(*q)
        if first<=e&1023<first+count:cells[q]=cell_bytes(*q,img) if q in region else tile(e&1023)
    slots=count
    newtiles=bytearray(tiles);newmap=bytearray(mp);assigned={}
    for q,data in sorted(cells.items(),key=lambda kv:(kv[0][1],kv[0][0])):
        t=entry(*q)&1023
        if data==tile(t) and data not in assigned and t not in assigned.values():assigned[data]=t
    pool=[t for t in range(first,first+count) if t not in assigned.values()]
    for q,data in sorted(cells.items(),key=lambda kv:(kv[0][1],kv[0][0])):
        if data not in assigned:
            if not pool:raise ValueError('PET label tile budget exceeded: %d slots for %d distinct cells' % (count,len(set(cells.values()))))
            t=pool.pop(0);assigned[data]=t
    for data,t in assigned.items():newtiles[(t-first)*32:(t-first+1)*32]=data
    for q,data in cells.items():
        e=entry(*q)&~1023|assigned[data];newmap[(q[1]*32+q[0])*2:(q[1]*32+q[0])*2+2]=e.to_bytes(2,'little')
    writes=[(to,bytes(newtiles),'PET menu label tiles (Hangul redraw)'),(mo,bytes(newmap),'PET menu label map cells')]
    meta={'translation_asset_sha256':sha((p/'translations/pet_labels_korean.json').read_bytes()),'spec_sha256':sha((p/SPEC).read_bytes()),
          'labels':[x['text'] for x in wording['entries']],'changed_cells':len(changed),'slots_rewritten':sum(1 for t in assigned.values() if newtiles[(t-first)*32:(t-first+1)*32]!=tiles[(t-first)*32:(t-first+1)*32]),'slots_left':len(pool),'slots':slots,'moves':[list(m) for m in choice],
          'tiles_sha256':sha(bytes(newtiles)),'map_sha256':sha(bytes(newmap))}
    return writes,meta,img
