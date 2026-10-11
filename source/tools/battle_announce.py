"""Battle chip-name announcement (support chips such as AreaGrab) in Hangul.

0x08021BF8 (red; 0x08021BC0 blue) draws the announced chip's name with the tile
renderer (native style 0x0868E224, whose F9 slot routes Hangul) from a
two-word root table [archive41, archive42] that only this routine reads
(its literal points at the table placed right after it). The table is pointed
at the library extension's translated private clones of 41 and 42.
"""
import json
from analyze_project import sha

SPEC='tools/specs/exe4_battle_announce_v1.json'


def writes(p,key,rom,library):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if sha(rom)!=prof['source_sha256']:raise ValueError('battle announce source drift')
    new=[0x08000000+library['archive_offsets']['41'],0x08000000+library['archive_offsets']['42']];out=[]
    for t in prof['tables']:
        if int.from_bytes(rom[t-4:t],'little')!=0x08000000+t:raise ValueError('battle announce table literal drift')
        if [int.from_bytes(rom[t+4*i:t+4*i+4],'little') for i in range(2)]!=prof['source_roots']:raise ValueError('battle announce roots drift')
        out.append((t,b''.join(x.to_bytes(4,'little') for x in new),'battle chip-name root table -> translated library clones'))
    ni=prof['name_insert']
    pairs=list(zip(ni['offsets'],ni['source_values'],new))+list(zip(prof['comm_names']['offsets'],prof['comm_names']['source_values'],new))
    for at,old,value in pairs:
        if int.from_bytes(rom[at:at+4],'little')!=old:raise ValueError('dialogue name insert table drift')
        out.append((at,value.to_bytes(4,'little'),'chip-name literal -> translated library clone'))
    return out,{'tables':prof['tables'],'roots':[hex(x) for x in new],'name_insert':ni['offsets']}
