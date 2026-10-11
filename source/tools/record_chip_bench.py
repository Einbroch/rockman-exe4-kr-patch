"""Bind final-product complete chooser and real queue CPU tests."""
import json,subprocess,sys
from pathlib import Path
from analyze_project import sha,PROFILES
p=Path(__file__).resolve().parents[1];c=[sys.executable,str(p/'tools/test_chip_extension.py')];r=subprocess.run(c,capture_output=True)
log=p/'analysis/chip_bench.log';log.write_bytes(r.stdout+r.stderr)
if r.returncode:raise SystemExit('chip CPU tests failed; see '+str(log))
report={'schema':1,'status':'PASS','scope':'both revisions; 256 complete native chooser entries, ten translations, real queue helper; explicit missing/range/ninth-cell stops; not GPU proof','command':c,'log':log.relative_to(p).as_posix(),'log_sha256':sha(log.read_bytes()),'tests':3,'inputs':{name:sha((p/name).read_bytes()) for name in ['tools/test_chip_extension.py','tools/chip_extension.py','tools/menu_extension.py','tools/extended_dialogue.py','tools/build_opening_poc.py','tools/specs/exe4_chip_folder_v1.json','translations/chip_names_korean_draft.json']},'products':{key:sha((p/'poc/output'/f'{key}_opening_menu_chip_folder_korean_development.gba').read_bytes()) for key in PROFILES}}
(p/'analysis/chip_bench.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('chip CPU bench PASS; 3 tests, two revisions')
