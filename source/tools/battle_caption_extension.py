"""Select existing private chip clones only at the Custom Screen caption call."""
import json
from analyze_project import sha
from extended_dialogue import assemble_verified

def extend(p, key, source, append, library, menu):
    path = p/'tools/specs/exe4_battle_caption_v1.json'
    spec = json.loads(path.read_text(encoding='utf-8'))
    s = spec['profiles'][key]
    catalog = p/'translations/chip_catalog_korean_draft.json'
    if sha(catalog.read_bytes()) != spec['catalog_sha256'] or sha(source) != s['source_sha256']:
        raise ValueError('battle caption input identity drift')
    anchor = s['context']
    if sha(source[anchor['offset']:anchor['offset']+anchor['size']]) != anchor['sha256']:
        raise ValueError('battle caption caller context drift')
    point = s['hook']
    if source[point['offset']:point['offset']+8].hex() != point['expected_hex']:
        raise ValueError('battle caption hook drift')
    if s['font'] != menu['styles'][0]['source_address']:
        raise ValueError('battle caption font not supported')
    if not set(library['characters']) <= set(menu['characters']):
        raise ValueError('battle caption missing glyph')
    # This explicit opt-in expands only the consumer scope, never prose or
    # review state. The original library input contract remains unchanged.
    code = '''ldr r4, root41
cmp r0, r4
beq use41
ldr r4, root42
cmp r0, r4
bne resume
cmp r1, #54
bhi resume
ldr r0, clone42
b resume
use41:
ldr r0, clone41
resume:
ldr r3, destination
movs r4, #8
movs r5, #1
ldr r6, font
ldr r7, continuation
bx r7
'''
    blob = bytearray(append)
    blob.extend(b'\xff'*(-len(blob)%4))
    at = len(source)+len(blob)
    literals = {'root41':s['roots']['41'], 'root42':s['roots']['42'],
                'clone42':0x08000000+library['archive_offsets']['42'],
                'clone41':0x08000000+library['archive_offsets']['41'],
                'destination':s['vram'], 'font':s['font'], 'continuation':point['continuation']}
    machine, isa = assemble_verified(code, 0x08000000+at, literals)
    blob.extend(machine)
    jump, jisa = assemble_verified('ldr r3, target\nbx r3',0x08000000+point['offset'],{'target':0x08000001+at})
    if len(jump)!=8: raise ValueError('battle jump window drift')
    layout = [{'name':'private Custom Screen chip caption selector','offset':at,'size':len(machine),'sha256':sha(machine)}]
    return bytes(blob), [(point['offset'],jump,'private battle Custom Screen caption selector')], {
        'scope':spec['scope'], 'contract_sha256':sha(path.read_bytes()),
        'translation_asset_sha256':sha(catalog.read_bytes()), 'translation_review_state':'needs_review',
        'development_consumer_opt_in':'--battle-caption; exact existing wording, no release eligibility',
        'layout':layout,'machine_code':[isa],'jump_code':[jisa],
        'archive_offsets':library['archive_offsets'],'cells':8,'tint':8,
        'destination':s['destination'],'vram':s['vram'],'font':s['font'],
        'active_glyph_bytes':512,'new_VRAM_allocation':False,
        'other_archive_claims_unchanged':True,'runtime':'pending'}
