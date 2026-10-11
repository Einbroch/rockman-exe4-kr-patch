"""Private description clone at one source-bound table entry; no executable edits."""
import json
from analyze_project import sha

def extend(p,key,source,append):
 path=p/'tools/specs/exe4_description_v1.json';spec=json.loads(path.read_text())
 s=spec['profiles'][key];draft=p/'translations/chip_descriptions_korean_draft.json'
 report=json.loads((p/'analysis/chip_description_analysis.json').read_text(encoding='utf-8'))
 if sha(source)!=s['source_sha256'] or sha(draft.read_bytes())!=spec['draft_sha256'] or report['draft_sha256']!=spec['draft_sha256']:raise ValueError('description identity drift')
 if report['tool_sha256']!=sha((p/'tools/prepare_chip_descriptions.py').read_bytes()) or report['authoring_sha256']!=sha((p/'translations/chip_description_authored.json').read_bytes()):raise ValueError('description preparation input drift')
 at=s['selector_context_offset'];end=at+s['selector_context_size']
 if sha(source[at:end])!=s['selector_context_sha256']:raise ValueError('description consumer context drift')
 at=s['pointer_offset']
 if source[at:at+4]!=s['source_pointer'].to_bytes(4,'little'):raise ValueError('description source pointer drift')
 compiled=p/report['profiles'][key]['compiled'];data=compiled.read_bytes()
 if sha(data)!=s['compiled_sha256'] or data!=compiled.with_name('descriptions_back.msg').read_bytes():raise ValueError('description compiler proof drift')
 if any(len(d['line_widths'])>spec['max_lines'] or max(d['line_widths'])>spec['provisional_line_pixels'] for d in report['profiles'][key]['details']):raise ValueError('description line budget drift')
 blob=bytearray(append);blob.extend(b'\xff'*(-len(blob)%4));offset=len(source)+len(blob);blob.extend(data)
 layout=[{'name':'private Custom Screen ten-description archive54 clone','offset':offset,'size':len(data),'sha256':sha(data)}]
 return bytes(blob),[(at,(0x08000000+offset).to_bytes(4,'little'),'Custom Screen private description table')],{
  'scope':spec['scope'],'contract_sha256':sha(path.read_bytes()),'translation_asset_sha256':sha(draft.read_bytes()),
  'development_consumer_opt_in':'--chip-descriptions; exact existing drafts, not release eligible',
  'selected_ids':spec['selected_ids'],'archive_offset':offset,'archive_size':len(data),'layout':layout,
  'other_original_claims_preserved':3,'unselected_scripts_preserved':246,'new_executable_code':False,
  'runtime':'pending','review_state':'needs_review'}
