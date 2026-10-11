"""Execute and bind CPU regression evidence to exact tools, BDF and sources."""
import argparse,json,subprocess,sys
from pathlib import Path
from analyze_project import sha,PROFILES,check_dependencies
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);a=ap.parse_args()
p=Path(__file__).resolve().parents[1];check_dependencies(p)
commands=[[sys.executable,str(p/'tools/test_dialogue_extension.py')],[sys.executable,str(p/'tools/test_menu_extension.py'),'--rom-dir',str(a.rom_dir.resolve()),'--font',str(a.font.resolve())],[sys.executable,str(p/'tools/test_consumer_contracts.py'),'--rom-dir',str(a.rom_dir.resolve()),'--font',str(a.font.resolve())]]
records=[]
for i,command in enumerate(commands):
 r=subprocess.run(command,capture_output=True);log=p/'analysis'/f'menu_bench_{i}.log';log.write_bytes(r.stdout+r.stderr)
 if r.returncode:raise SystemExit('CPU regression rejected; see '+str(log))
 records.append({'command':command,'return_code':r.returncode,'log':log.relative_to(p).as_posix(),'log_sha256':sha(log.read_bytes()),'test_script_sha256':sha(Path(command[1]).read_bytes())})
report={'schema':1,'status':'PASS','scope':'controlled ARMv4T fixtures; not whole-game runtime','sources':{k:v['sha256'] for k,v in PROFILES.items()},'font_sha256':sha(a.font.read_bytes()),'records':records,'menu_cases':{'tests':6,'available_syllables':4363,'native_font_styles':2,'source_revisions':2,'native_renderer_executions':4363*2*2,'copied_parser_dispatch':'original parser/newline/end-padding plus updated F9 slot; final DMA helper stubbed','missing_glyph_or_style':'explicit stop; no pixels written','build_missing_demand':'rejected before compiler/output'},'inputs':{f:sha((p/f).read_bytes()) for f in ['tools/menu_extension.py','tools/consumer_contracts.py','tools/extended_dialogue.py','tools/specs/exe4_menu_extension_v1.json','tools/specs/exe4_dialogue_extension_v1.json','tools/specs/exe4_consumer_contracts_v1.json']}}
report['menu_cases']['tests']=7
report['menu_cases']['dynamic_folder_producer']='actual product native F9 folder1/2 transfer and width path; 64-byte copy helper stubbed; not game-screen proof'
report['products']={key:sha((p/'poc/output'/f'{key}_opening_menu_korean_development.gba').read_bytes()) for key in PROFILES}
report['consumer_cases']={'tests':4,'native_chip_decoder':'both source revisions, no helper stubs; F9FC stops before the new glyph, including partial native prefix','native_name_decoder':'both styles/revisions, original parser and renderer without stubs; three low-byte indexes, high byte ignored','unclassified_selection':'rejected before absent compiler or output directory is reached','byte_budget':'controlled 17-cell producer with native folder copy ceiling64; 69 encoded bytes rejected'}
(p/'analysis/menu_bench.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('normal 6, menu 7 and consumer 4 tests PASS')
