"""Record Codex's inspected route and literal-to-capture attribution.

This documents visual inspection performed on 2026-09-15, rather than claiming
that file presence automatically proves appearance or independent review.
"""
import json
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
translation=p/'translations/opening_korean.json'
source=json.loads(translation.read_text(encoding='utf-8'))
literals=[(int(script),i,text) for script,values in sorted(source['scripts'].items(),key=lambda kv:int(kv[0])) for i,text in enumerate(values)]
steps=[('opening_final',i) for i in [3,5,6,7,8]+list(range(11,33))+list(range(34,65))]+[('opening_end',2)]
if len(literals)!=59 or len(steps)!=59:raise ValueError('opening route map drift; inspect again')
report={'schema':1,'reviewer':'Codex visual inspection 2026-09-15','scope':'two exact-hash NON-DISTRIBUTION opening development ROMs only','translation_sha256':sha(translation.read_bytes()),'independent_language_review':'pending; translations remain needs_review','full_game_qa':'not performed','findings':['All 59 opening literal pages inspected in four native-resolution capture contact sheets plus the final response captures.','Korean ink, shadows and line breaks are visible; no clipped Korean or palette color-block failure seen in this route.','Final response is followed by a natural scene transition to Netto bedroom; next dialogue remains Japanese.','This establishes opening display and event progression only; temporary Japanese glyph reuse prevents whole-game acceptance.'],'profiles':[]}
for key in ['blue_moon','red_sun']:
    entry={'profile':key,'runs':[],'pages':[]}
    for suffix,count in [('opening_final',64),('opening_end',3),('opening_exit',3)]:
        root=p/'analysis/runtime'/f'{key}_{suffix}'
        receipt=root/'result.json';r=json.loads(receipt.read_text(encoding='utf-8'))
        if not r['complete'] or r['steps_captured']!=count or r['return_code']!=0:raise ValueError('incomplete route')
        entry['runs'].append({'receipt':receipt.relative_to(p).as_posix(),'receipt_sha256':sha(receipt.read_bytes()),'rom_sha256':r['rom_sha256'],'captures':count,'scope':r['scope']})
    for (script,i,text),(suffix,step) in zip(literals,steps):
        f=p/'analysis/runtime'/f'{key}_{suffix}'/f'step_{step:03}.png'
        entry['pages'].append({'entry_id':f'archive/442/script/{script}','literal_index':i,'expected_text':text,'capture':f.relative_to(p).as_posix(),'capture_sha256':sha(f.read_bytes()),'visual_assessment':'visible; no clipping or palette failure observed'})
    f=p/'analysis/runtime'/f'{key}_opening_exit/step_003.png'
    entry['transition']={'capture':f.relative_to(p).as_posix(),'sha256':sha(f.read_bytes()),'observation':'Netto bedroom, original Japanese dialogue; no field progression beyond this accepted'}
    report['profiles'].append(entry)
(p/'analysis/OPENING_RUNTIME_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('recorded inspected opening route: 59 pages per version; whole-game QA remains open')
