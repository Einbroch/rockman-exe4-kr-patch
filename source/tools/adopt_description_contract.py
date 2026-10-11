"""Freeze the observed Custom Screen description table, leaving other claims native."""
import json
from pathlib import Path
from analyze_project import sha,PROFILES
from verify_tpi_index import parse_tpi
p=Path(__file__).resolve().parents[1]
draft=p/'translations/chip_descriptions_korean_draft.json'
analysis=json.loads((p/'analysis/chip_description_analysis.json').read_text(encoding='utf-8'))
spec={'schema':1,'scope':'Custom Screen R description; ten drafts, NON-DISTRIBUTION needs_review',
 'draft_sha256':sha(draft.read_bytes()),'selected_ids':[1,4,15,29,48,49,91,107,117,149],
 'max_lines':3,'provisional_line_pixels':132,'profiles':{}}
for key,at in [('blue_moon',0x1fce4),('red_sun',0x1fd20)]:
 pr=PROFILES[key];source=next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes())==pr['sha256'])
 rows=parse_tpi(p/'external/textpet-indexes'/pr['index']);row=rows[54]
 if at not in row['pointers'] or int.from_bytes(source[at:at+4],'little')!=0x08000000+row['offset']:raise ValueError('description pointer not indexed')
 if int.from_bytes(source[at-4:at],'little')!=0x08000000+at:raise ValueError('description table loader drift')
 if int.from_bytes(source[at+4:at+8],'little')!=0x08000000+rows[55]['offset']:raise ValueError('description adjacent table drift')
 spec['profiles'][key]={'source_sha256':sha(source),'pointer_offset':at,'source_archive_offset':row['offset'],
  'source_archive_size':row['size'],'source_pointer':0x08000000+row['offset'],
  'other_pointer_claims':[x for x in row['pointers'] if x!=at],
  'selector_start':at-0x24,'selector_return':at-8,'selector_context_offset':at-0x3c,
  'selector_context_size':0x3c,'selector_context_sha256':sha(source[at-0x3c:at]),
  'compiled_sha256':analysis['profiles'][key]['compiled_sha256']}
(p/'tools/specs/exe4_description_v1.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
