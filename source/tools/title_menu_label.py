"""Title menu words (はじめから / つづきから / N周目のつづきから / オペレーションバトル) redrawn.

The title menu is built from sprites cut from one 25x2-tile sheet, an LZ77
stream with a 4-byte size word in front. The words share parts: から (two tile
columns) closes both はじめから and つづきから, and the N-th-cycle line is
[digit][周目の][つづき][から]. The Korean words are chosen so the shared part
stays shared: 새로하기 / 이어하기 drawn at a 12-pixel pitch put the end of 하 and
all of 기 in the から columns, identical for both. Ink 1 with a shadow of 2 one
pixel right and down, as the source. The sheet is recompressed in place.
"""
import json
from analyze_project import sha
from pet_labels import glyphs
from verify_tpi_index import lz77_decompress
from library_pa_label import lz77_compress

SPEC='tools/specs/exe4_title_menu_label_v1.json'


def word_image(font,text,pitch,width,align,top,bold=False):
    """Ink pixels of text, one syllable every pitch pixels, placed in width."""
    ink=set();pen=0
    for c in text:
        if c==' ':pen+=pitch//2;continue
        dw,px=font[c];x0=min(x for x,_ in px) if px else 0
        ink|={(pen+x-x0+(pitch-1-(max(x for x,_ in px)-x0+1))//2,y) for x,y in px};pen+=pitch
    if bold:ink|={(x+1,y) for x,y in ink}
    w=max(x for x,_ in ink)+2
    if w>width:raise ValueError(f'title word too wide: {text} ({w} > {width})')
    left={'left':0,'center':(width-w)//2}[align]
    y0=min(y for _,y in ink)
    ink={(x+left,y-y0+top) for x,y in ink}
    img={}
    for x,y in ink:
        if (x+1,y+1) not in ink:img[(x+1,y+1)]=2
    for q in ink:img[q]=1
    return img


def build(p,key,rom,font_path):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if sha(rom)!=prof['source_sha256'] or sha(font_path.read_bytes())!=s['font_sha256']:raise ValueError('title menu source drift')
    at=prof['sheet_offset']
    if int.from_bytes(rom[prof['pointer']:prof['pointer']+4],'little')!=0x08000000+at:raise ValueError('title sheet pointer drift')
    sheet,used=lz77_decompress(rom,at)
    if used!=s['compressed_size'] or sha(sheet)!=s['sheet_sha256']:raise ValueError('title sheet drift')
    font=glyphs(font_path);cols=s['columns'];new=bytearray(sheet)
    painted={}
    for w in s['words']:
        width=8*sum(b-a for a,b in w['parts'])
        img=word_image(font,w['text'],s['pitch'],width,w['align'],s['top'],s.get('bold',False))
        x=0
        for a,b in w['parts']:
            for col in range(a,b):
                tile={}
                for yy in range(16):
                    for xx in range(8):tile[(xx,yy)]=img.get((x+xx,yy),0)
                if col in painted and painted[col]!=tile:raise ValueError(f'shared column {col} differs between words')
                painted[col]=tile;x+=8
    for col,tile in painted.items():
        for row in (0,1):
            t=col+row*cols;base=s['tile_base']+t*32
            for i in range(32):
                a=(2*i%8,row*8+2*i//8);b=((2*i+1)%8,row*8+(2*i+1)//8)
                new[base+i]=tile[a]|tile[b]<<4
    blob=lz77_compress(bytes(new))
    back,consumed=lz77_decompress(blob,0)
    if back!=bytes(new) or not len(blob)-3<=consumed<=len(blob):raise ValueError('title sheet recompression does not round-trip')
    span=s['span_bytes']
    if rom[at+span]!=0x10 or len(blob)>span:raise ValueError(f'title sheet is {len(blob)} bytes, over its {span}-byte span')
    return [(at,blob,'title menu words (sheet recompressed in place)')],{
        'words':[w['text'] for w in s['words']],'compressed_bytes':len(blob),'span_bytes':span,
        'sheet_sha256':sha(bytes(new)),'spec_sha256':sha((p/SPEC).read_bytes())}
