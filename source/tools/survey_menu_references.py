"""Read-only literal/interior-pointer candidates; not control-flow closure."""
import argparse,json,struct
from pathlib import Path
from analyze_project import sha,PROFILES,check_dependencies
from verify_tpi_index import parse_tpi
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);a=ap.parse_args()
p=Path(__file__).resolve().parents[1];check_dependencies(p)
inputs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
spec=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))
report={'schema':1,'status':'source reference candidates; runtime classification required',
 'scope':'aligned native font/entry literals and aligned words into four selected raw archives; not all computed pointers/callers',
 'profiles':{}}
for key,profile in PROFILES.items():
 r=inputs[profile['sha256']];s=spec['profiles'][key];rows=parse_tpi(p/'external/textpet-indexes'/profile['index'])
 targets=[f['source_address'] for f in s['fonts']]+[0x0300677d,0x030067f1]
 literal_refs={target:[] for target in targets};archives={ai:{'claimed_base':rows[ai]['pointers'],'unclaimed_base_candidates':[],'interior_candidates':[]} for ai in [1,2,5,13]}
 for i,(word,) in enumerate(struct.iter_unpack('<I',r)):
  at=i*4
  if word in literal_refs:literal_refs[word].append(at)
  if not 0x08000000<=word<0x08000000+len(r):continue
  off=word-0x08000000
  for ai,item in archives.items():
   row=rows[ai]
   if off==row['offset'] and at not in row['pointers']:item['unclaimed_base_candidates'].append({'offset':at,'word':word})
   elif row['offset']<off<row['offset']+row['size']:item['interior_candidates'].append({'offset':at,'word':word,'within_archive_offset':off-row['offset']})
 literal_sites={at for refs in literal_refs.values() for at in refs};ldr_candidates=[]
 for at in range(0,len(r)-2,2):
  op=int.from_bytes(r[at:at+2],'little')
  if op&0xf800!=0x4800:continue
  pool=((at+4)&~3)+(op&255)*4
  if pool in literal_sites:ldr_candidates.append({'offset':at,'literal_offset':pool,'register':(op>>8)&7,'target':int.from_bytes(r[pool:pool+4],'little'),'classification':'opcode-shaped candidate; data can match'})
 report['profiles'][key]={'source_sha256':sha(r),'literal_references':{hex(t):refs for t,refs in literal_refs.items()},'thumb_ldr_candidates':ldr_candidates,'relocated_raw_archive_pointer_candidates':archives}
 print(key,'font/entry literal counts',{hex(t):len(v) for t,v in literal_refs.items()},'interior candidates',{ai:len(v['interior_candidates']) for ai,v in archives.items()})
(p/'analysis/menu_reference_census.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
