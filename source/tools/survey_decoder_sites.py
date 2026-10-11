"""Candidate census, not complete control-flow/reference verification."""
import argparse
import json
from pathlib import Path
from analyze_project import sha
ap=argparse.ArgumentParser()
ap.add_argument('--rom',type=Path,required=True)
ap.add_argument('--ram',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
args=ap.parse_args()
rom=args.rom.read_bytes();ram=args.ram.read_bytes()
anchor=0x6a48;needle=ram[anchor:anchor+32]
at=rom.find(needle)
if at<0 or rom.find(needle,at+1)>=0:raise SystemExit('renderer source anchor unresolved')
delta=at-anchor
start,end=anchor,anchor+32
while start>0 and delta+start>0 and ram[start-1]==rom[delta+start-1]:start-=1
while end<len(ram) and delta+end<len(rom) and ram[end]==rom[delta+end]:end+=1
sites=[]
for off in range(0,len(ram)-1,2):
    op=int.from_bytes(ram[off:off+2],'little')
    if op&0xf800 in (0x2800,0x3000) and op&255 in (0xe4,0xe5):
        sites.append({'ram_address':hex(0x03000000+off),'kind':'cmp' if op&0xf800==0x2800 else 'add','register':(op>>8)&7,'immediate':hex(op&255),'in_renderer_exact_source_span':start<=off<end,'rom_offset':hex(delta+off) if start<=off<end else None})
report={'status':'candidate survey; not decoder completeness','rom_sha256':sha(rom),'ram_sha256':sha(ram),'renderer_runtime_anchor':hex(0x03000000+anchor),'renderer_rom_anchor':hex(at),'exact_matching_span':{'ram_start':hex(0x03000000+start),'ram_end_exclusive':hex(0x03000000+end),'rom_start':hex(delta+start),'rom_end_exclusive':hex(delta+end),'bytes':end-start},'conclusion':'observed renderer source is directly stored in ROM; no compression prerequisite for this exact matching span','candidate_sites':sites,'next_diagnostic':'tie other candidates to entry points and runtime consumers; inspect ROM-to-IWRAM copy descriptors and separate menu decoder before lead expansion'}
args.out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('exact renderer source span',report['exact_matching_span'],'E4/E5 immediate candidates',len(sites))
