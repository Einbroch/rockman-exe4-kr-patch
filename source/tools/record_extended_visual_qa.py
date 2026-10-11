"""Record inspected exact-hash extension routes; no independent review claim."""
import json
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
translation=p/'translations/opening_korean.json';probe=p/'poc/font_probe_wording.json'
words=json.loads(translation.read_text(encoding='utf-8'))['scripts'];probe_words=json.loads(probe.read_text(encoding='utf-8'))['scripts']['0']
pages=[(int(s),i,text) for s,values in sorted(words.items(),key=lambda kv:int(kv[0])) for i,text in enumerate(values)]
steps=[3,5,6,7,8]+list(range(11,33))+list(range(34,65))+[65]
if len(pages)!=59 or len(steps)!=59:raise ValueError('inspect route map again')
report={'schema':1,'reviewer':'Codex visual inspection 2026-09-15','claim':'normal-dialogue extension development only','independent_language_review':'pending; opening wording remains needs_review','translation_sha256':sha(translation.read_bytes()),'font_probe_wording_sha256':sha(probe.read_bytes()),'evidence_roles':{'full_11172_glyph_supply':'analysis/extended_verification.json: static independent BDF ink/shadow pixel comparison','full_11172_code_decoding':'controlled CPU fixture execution, tools/test_dialogue_extension.py; dummy native helpers; not whole-game runtime','ISA_model':'analysis/thumb1_toolchain_audit.json: defined 16-bit encodings and each instruction family; BL field-wise boundaries','actual_game_runtime':'cold boot and ordinary input; 59 opening pages and 25 boundary glyphs in two versions'},'findings':['All 59 opening literal pages inspected in native-size contact sheets and final response captures; Korean ink/shadow/line breaks visible, no clipping seen.','Both versions reach Netto bedroom; original Japanese first dialogue remains readable.','Both versions display U+AC00 and U+D7A3 boundary syllables, dense consonants/vowels, spaces/Latin/digits, and glyph codes containing E5/E8/FF/00 argument bytes without early termination.','Full-game menu, battle, name-entry, imported strings, layout and device QA remain open.'],'profiles':[]}
for key in ['blue_moon','red_sun']:
    entry={'profile':key,'opening_pages':[],'font_probe_pages':[],'receipts':[]}
    for run,count in [('extended_v2_final',70),('boundary_final',9)]:
        f=p/'analysis/runtime'/f'{key}_{run}/result.json';r=json.loads(f.read_text(encoding='utf-8'))
        if not r['complete'] or r['return_code']!=0 or r['steps_captured']!=count:raise ValueError('incomplete route')
        entry['receipts'].append({'file':f.relative_to(p).as_posix(),'sha256':sha(f.read_bytes()),'rom_sha256':r['rom_sha256'],'captures':count})
    def capture(run,step):
        f=p/'analysis/runtime'/f'{key}_{run}'/f'step_{step:03}.png'
        return {'file':f.relative_to(p).as_posix(),'sha256':sha(f.read_bytes())}
    for (script,i,text),step in zip(pages,steps):entry['opening_pages'].append({'entry_id':f'archive/442/script/{script}','literal_index':i,'expected_text':text,'capture':capture('extended_v2_final',step),'observation':'visible; no clipping or palette-block failure seen'})
    for text,step in zip(probe_words,[3,5,6,7,8]):entry['font_probe_pages'].append({'expected_text':text,'hangul_indices':[ord(c)-0xac00 for c in text if 0xac00<=ord(c)<=0xd7a3],'capture':capture('boundary_final',step),'observation':'visible; dense/edge syllables remain distinct; Latin and line break also displayed'})
    entry['original_japanese_transition']={'capture':capture('extended_v2_final',68),'expected_text':'熱斗くん、あさだよ！','observation':'Netto bedroom; Japanese glyphs preserved and readable'}
    report['profiles'].append(entry)
(p/'analysis/EXTENDED_RUNTIME_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('recorded inspected extended opening + boundary routes; whole-game claim withheld')
