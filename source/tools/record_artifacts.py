"""Hash title-local artifacts, retaining current/historical evidence separately."""
import csv
from pathlib import Path
from analyze_project import sha
p=Path(__file__).resolve().parents[1]
out=p/'ARTIFACT_MANIFEST.tsv'
rows=[]
for f in sorted(p.rglob('*')):
    if not f.is_file() or f==out or '__pycache__' in f.parts:continue
    if not f.resolve().is_relative_to(p):raise SystemExit('artifact outside title project')
    rel=f.relative_to(p).as_posix()
    if rel.startswith('tools/'):
        role,producer,reproduce='authored-tool','Codex authored source; dates in WORK_LOG','authored source; retain exact file'
    elif rel.startswith('translations/'):
        role,producer,reproduce='translation-input','Codex Japanese-to-Korean; dates in WORK_LOG','translator-authored; source IDs in analysis source_entries'
    elif rel.startswith('external/'):
        role,producer,reproduce='external-input','EXE2/EXE3 local TextPet copy; pinned upstream','README dependency record and upstream commit'
    elif rel.startswith('poc/output/') and '_story_korean_development' in rel:
        role,producer,reproduce='non-distribution-product','tools/build_story_batch.py','gated story batches applied to the recorded baseline product'
    elif rel.startswith(('poc/blue_moon_story','poc/red_sun_story')):
        role,producer,reproduce='story-build-intermediate','tools/build_story_batch.py or tools/verify_story_batch.py','gated batch plus the source TPL it was written against'
    elif rel.startswith('poc/'):
        role,producer,reproduce='non-distribution-product','tools/build_opening_poc.py','README build command; exact source profiles and pinned BDF'
    elif rel.startswith('analysis/runtime/'):
        role,producer,reproduce='runtime-evidence','tools/run_mesen_segment.py','result.json command, frame inputs, build and core hashes'
    elif rel.startswith(('analysis/chip_description_compilation/','analysis/menu_chip_description_compilation/')):
        role,producer,reproduce='description-compiler-output','tools/prepare_chip_descriptions.py or tools/prepare_menu_chip_descriptions.py; consumer insertion separately verified','authored JSON plus source-bound sheet, original profiles, TextPet and Galmuri11'
    elif rel.startswith('analysis/chip_catalog_compilation/'):
        role,producer,reproduce='research-text-roundtrip','tools/prepare_chip_catalog.py; NO ROM produced','authored TSV plus source-bound sheet, original profiles, TextPet and Galmuri7'
    elif rel.startswith('analysis/'):
        role,producer,reproduce='analysis-evidence','tools/analyze_project.py or named survey','README commands and named tools'
    else:
        role,producer,reproduce='project-record','Codex 2026-09-15','authored current facts and append-only handoff'
    rejected='rejected' in rel or any(x in rel for x in ('korean_anSA','opening_qa/','opening_palette_fixed/','opening_isolated/','faulty_dialogue','blue_moon_extended_final/','library_cold_01/','library_final_01/','all_descriptions_korean_development','menu_descriptions_cold_01/','menu_descriptions_final_01/','menu_descriptions_folder_01.png','menu_descriptions_library_01.png'))
    partial=any(x in rel for x in ('blue_moon_menu_survey_01/','blue_moon_menu_final_01/','blue_moon_chip_vram_writes_01/'))
    research=rel.startswith('analysis/chip_catalog_compilation/')
    description_input=rel.startswith(('analysis/chip_description_compilation/','analysis/menu_chip_description_compilation/'))
    rows.append({'artifact_key':rel,'role':role,'producer':producer,'reproduce':reproduce,'status':'private-description-development-input' if description_input else 'research-only-not-runtime-inserted' if research else 'partial-or-rejected-menu-diagnostic' if partial else 'historical-rejected-or-unowned-diagnostic' if rejected else 'current-or-source-evidence','bytes':f.stat().st_size,'sha256':sha(f.read_bytes())})
with out.open('w',encoding='utf-8',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=['artifact_key','role','producer','reproduce','status','bytes','sha256'],delimiter='\t')
    writer.writeheader();writer.writerows(rows)
print('artifact records',len(rows),'bytes',sum(r['bytes'] for r in rows))
