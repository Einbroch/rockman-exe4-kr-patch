import argparse
import json
from pathlib import Path
from analyze_project import payload, PROFILES
from verify_tpi_index import parse_tpi
ap=argparse.ArgumentParser()
ap.add_argument('--rom',type=Path,required=True)
ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
args=ap.parse_args()
p=args.project
rom=args.rom.read_bytes()
rows=parse_tpi(p/'external/textpet-indexes'/PROFILES['blue_moon']['index'])
result=[]
for row in rows:
    name=f"{row['offset']:06X}"
    source=payload(rom,row)
    back=(p/'analysis/blue_moon_roundtrip_bin'/(name+'.msg')).read_bytes()
    diffs=[{'at':i,'source':a,'rebuilt':b,'context':source[max(0,i-5):i+6].hex()} for i,(a,b) in enumerate(zip(source,back)) if a!=b]
    if diffs:
        print(name,len(diffs),diffs[:12])
        result.append({'archive':name,'differences':diffs})
(p/'analysis/roundtrip_differences.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
