"""Library P.A memo panel caption (パターン ?/?) redrawn as 패턴.

The word is a 32x8 sprite (tiles 0xBC..0xBF, OBJ palette 2) taken from the
library sprite sheet, an LZ77 stream the library decodes to 0x02031000; the
"?/?" after it are separate sprites and stay. The four tiles are redrawn
(ink 14 on fill 11, right-aligned so the word still meets the "?/?"), the sheet
is recompressed with an optimal LZ77 parse and written back in place, so the
pointer and the decoded size do not change.
"""
import json
from analyze_project import sha
from pet_labels import glyphs, text_pixels
from verify_tpi_index import lz77_decompress

SPEC='tools/specs/exe4_library_pa_label_v1.json'


def lz77_compress(data):
    """GBA LZ77 (type 0x10), optimal parse. The sheet is decoded by BIOS LZ77UnCompWram
    (svc 0x11 at 0x08111700) into work RAM, so distance 1 is allowed."""
    n=len(data);INF=1<<60
    cost=[INF]*(n+1);cost[n]=0;choice=[None]*(n+1)
    heads={}
    pos_by_key=[[] for _ in range(n)]
    for i in range(n-2):
        k=data[i:i+3];pos_by_key[i]=heads.setdefault(k,[]);heads[k].append(i)
    for i in range(n-1,-1,-1):
        # a literal costs 8 bits plus its flag bit
        cost[i]=cost[i+1]+9;choice[i]=(0,0)
        if i+3>n:continue
        best={}
        for j in reversed(pos_by_key[i]):
            if j>=i:continue
            d=i-j
            if d>4096:break
            m=0
            while m<18 and i+m<n and data[j+m]==data[i+m]:m+=1
            for L in range(3,m+1):
                if L not in best:best[L]=d
        for L,d in best.items():
            c=cost[i+L]+17
            if c<cost[i]:cost[i]=c;choice[i]=(L,d)
    out=bytearray([0x10])+n.to_bytes(3,'little');i=0
    while i<n:
        flag_at=len(out);out.append(0);flags=0
        for b in range(8):
            if i>=n:break
            L,d=choice[i]
            if L:
                v=((L-3)<<12)|(d-1);out+=bytes([v>>8,v&0xff]);flags|=0x80>>b;i+=L
            else:
                out.append(data[i]);i+=1
        out[flag_at]=flags
    while len(out)%4:out.append(0)
    return bytes(out)


def build(p,key,rom,font_path):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if sha(rom)!=prof['source_sha256'] or sha(font_path.read_bytes())!=s['font_sha256']:raise ValueError('P.A label source drift')
    at=prof['sheet_offset']
    if int.from_bytes(rom[prof['pointer']:prof['pointer']+4],'little')!=0x08000000+at:raise ValueError('P.A sheet pointer drift')
    sheet,used=lz77_decompress(rom,at)
    if used!=s['compressed_size'] or sha(sheet)!=s['sheet_sha256']:raise ValueError('P.A sheet drift')
    base=s['tile_offset'];tiles=s['tiles'];w=tiles*8
    img={}
    for t in range(tiles):
        for i in range(64):
            b=sheet[base+t*32+i//2];img[(t*8+i%8,i//8)]=b>>4 if i%2 else b&15
    for q,v in img.items():
        if v!=s['fill'] and v not in s['keep']:img[q]=s['fill']
    px=text_pixels(glyphs(font_path),s['text'])
    tw=max(x for x,_ in px)+1;th=max(y for _,y in px)+1
    if tw+s['right_margin']>w or th>8:raise ValueError('P.A caption does not fit')
    left=w-s['right_margin']-tw;top=(8-th+1)//2
    for x,y in px:img[(left+x,top+y)]=s['ink']
    new=bytearray(sheet)
    # The handakuten of パ is its own 8x8 sprite above the word; its ink goes to
    # the fill, its transparent rows stay transparent.
    for t in s['erase_tiles']:
        for i in range(32):
            b=new[t+i];lo,hi=b&15,b>>4
            lo=lo if lo in (0,s['fill']) else s['fill'];hi=hi if hi in (0,s['fill']) else s['fill']
            new[t+i]=lo|hi<<4
    for t in range(tiles):
        for i in range(32):
            a=(t*8+(i*2)%8,(i*2)//8);b=(t*8+(i*2+1)%8,(i*2+1)//8)
            new[base+t*32+i]=img[a]|img[b]<<4
    blob=lz77_compress(bytes(new))
    back,consumed=lz77_decompress(blob,0)
    # The stream is padded to a word; the decoder stops at the declared size.
    if back!=bytes(new) or not len(blob)-3<=consumed<=len(blob):raise ValueError('P.A sheet recompression does not round-trip')
    # The stream may use its word padding; the next stream (an LZ77 header) starts there.
    span=s['span_bytes']
    if rom[at+span]!=0x10 or len(blob)>span:raise ValueError(f'P.A sheet is {len(blob)} bytes, over its {span}-byte span')
    return [(at,blob,'library P.A caption 패턴 (sheet recompressed in place)')],{
        'text':s['text'],'compressed_bytes':len(blob),'source_compressed_bytes':used,
        'sheet_sha256':sha(bytes(new)),'spec_sha256':sha((p/SPEC).read_bytes())}
