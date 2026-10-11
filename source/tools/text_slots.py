"""Keep every text archive inside the fixed RAM slot the game decodes it to.

The field decodes three archives per area, one after another (0x0804DF5C):
main -> 0x02030000 (next slot 0x3800 on), sub -> 0x02033800 (0x1000), and
extra -> 0x02034800 (0x2000, then the buffer at 0x02036800). A Korean
syllable takes four bytes where a kana took one, so translated archives grow
past their slot; a later decode then overwrites the tail, and a script read
from that tail runs garbage as commands (mGBA: "Jumped to invalid address").
A few other archives have the same kind of fixed buffer (mail bodies end
before 0x0202A000 in the source; see SPEC).

An archive over its cap keeps its whole payload uncompressed in ROM and, in
the decoded copy, its largest scripts are replaced by `F9 FD a0 a1 a2 a3`,
which every text interpreter now reads as "continue at this ROM address"
(extended_dialogue.JUMP). The jump targets the same script inside the ROM
copy, so a script that falls through into the next one still does; script
numbers are unchanged because the offset table keeps every entry.
"""
import json

SPEC='tools/specs/exe4_text_slots_v1.json'
JUMP_LEN=6


def _w(rom,a):return int.from_bytes(rom[a:a+4],'little')


def _arr(rom,a,maxn=64):
    out=[]
    for k in range(maxn):
        v=_w(rom,a+4*k)
        if not 0x08000000<=(v&0x9ffffff)<0x09400000:break
        out.append(v&0x1ffffff)
    return out


def caps(p,key,source):
    """Source archive offset -> the largest decoded size it may have."""
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if source[prof['selector_offset']:prof['selector_offset']+len(bytes.fromhex(s['selector_hex']))].hex()!=s['selector_hex']:raise ValueError('area text selector drift')
    out={}
    def put(off,limit):
        out[off]=min(out.get(off,1<<30),limit)
    for slot in s['area_slots']:
        root=prof['roots'][slot['name']]
        for half in (0,4):
            level=[_w(source,root+half)&0x1ffffff]
            for _ in range(slot['depth']):level=[x for a in level for x in _arr(source,a)]
            for off in level:put(off,slot['limit'])
    for item in s['fixed']:put(prof['fixed'][str(item['archive'])],item['limit'])
    return out,s


def cap_for(caps_map,source_offset,source_size):
    limit=caps_map.get(source_offset)
    if limit is None:return None
    # An archive the source already let run past the slot keeps its own size.
    return max(limit,source_size)


def scripts_of(data):
    n=int.from_bytes(data[0:2],'little')//2
    offs=[int.from_bytes(data[2*i:2*i+2],'little') for i in range(n)]
    starts=sorted(set(offs))
    if not starts or starts[0]!=2*n:raise ValueError('archive offset table is not followed by its scripts')
    bounds={a:b for a,b in zip(starts,starts[1:]+[len(data)])}
    return n,offs,starts,bounds


def externalize(data,cap,rom_address):
    """Return data shrunk to cap, with jumps into a whole copy at rom_address."""
    if len(data)<=cap:return data,[]
    n,offs,starts,bounds=scripts_of(data)
    size={a:bounds[a]-a for a in starts}
    out_set=set();total=len(data)
    for a in sorted(starts,key=lambda a:-size[a]):
        if total<=cap:break
        if size[a]<=JUMP_LEN:break
        out_set.add(a);total-=size[a]-JUMP_LEN
    if total>cap:raise ValueError(f'archive cannot be brought under its {cap}-byte slot')
    body=bytearray();moved={}
    for a in starts:
        moved[a]=2*n+len(body)
        if a in out_set:body+=b'\xf9\xfd'+(rom_address+a).to_bytes(4,'little')
        else:body+=data[a:bounds[a]]
    table=b''.join(moved[o].to_bytes(2,'little') for o in offs)
    new=table+bytes(body)
    if len(new)!=total:raise ValueError('externalized size bookkeeping')
    return new,sorted(starts.index(a) for a in out_set)


def check_stub(stub,full,full_address):
    """A decoded archive is the whole payload or the same with some scripts
    replaced by a jump to that script inside the ROM copy at full_address."""
    if stub==full:return 0
    n,offs,starts,bounds=scripts_of(stub)
    fn,foffs,fstarts,fbounds=scripts_of(full)
    if n!=fn:raise ValueError('externalized archive changed its script count')
    jumps=0
    for i in range(n):
        a,b=offs[i],bounds[offs[i]];fa,fb=foffs[i],fbounds[foffs[i]]
        got=stub[a:b]
        if got==full[fa:fb]:continue
        if got!=bytes([0xf9,0xfd])+(full_address+fa).to_bytes(4,'little'):raise ValueError(f'script {i} is neither kept nor a jump to its ROM copy')
        jumps+=1
    return jumps
