"""Bind the full 311-ID library CPU test to the exact two products."""
import json,subprocess,sys
from pathlib import Path
from analyze_project import sha,PROFILES
p=Path(__file__).resolve().parents[1];command=[sys.executable,str(p/'tools/test_library_extension.py')];run=subprocess.run(command,capture_output=True)
log=p/'analysis/library_bench.log';log.write_bytes(run.stdout+run.stderr)
if run.returncode:raise SystemExit('library CPU tests failed; see '+str(log))
report={'schema':1,'status':'PASS','scope':'both revisions; all ROM-backed IDs0..310, all294 Korean drafts, all seven rows, native fallback, actual copy wrapper with CpuSet semantics, explicit missing/range/ninth-cell stops; not GPU proof','command':command,'log':log.relative_to(p).as_posix(),'log_sha256':sha(log.read_bytes()),'tests':2,'inputs':{name:sha((p/name).read_bytes()) for name in ['tools/test_library_extension.py','tools/library_extension.py','tools/menu_extension.py','tools/extended_dialogue.py','tools/build_opening_poc.py','tools/specs/exe4_chip_library_v1.json','translations/chip_catalog_korean_draft.json']},'products':{key:sha((p/'poc/output'/f'{key}_opening_menu_chip_folder_library_korean_development.gba').read_bytes()) for key in PROFILES}}
(p/'analysis/library_bench.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('library CPU bench PASS; 2 tests, 311 IDs x two revisions')
