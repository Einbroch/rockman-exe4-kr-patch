"""Bind manually inspected caption captures to real RAM/VRAM and private streams."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from analyze_project import sha

p = Path(__file__).resolve().parents[1]
spec = json.loads((p/'tools/specs/exe4_battle_caption_v1.json').read_text(encoding='utf-8'))
catalog = json.loads((p/'translations/chip_catalog_korean_draft.json').read_text(encoding='utf-8'))
names = {x['chip_id']: x['text'] for x in catalog['entries']}
ids = [1, 29, 1, 48, 107, 48]
table = {}
for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
    code, sep, char = line.partition('=')
    if sep and len(char) == 1:
        table.setdefault(char, bytes.fromhex(code))

def proof(path):
    return {'path': path.relative_to(p).as_posix(), 'sha256': sha(path.read_bytes())}

def receipt(path, digest, count):
    r = json.loads(path.read_text(encoding='utf-8'))
    if (not r['complete'] or r['return_code'] or r['rom_sha256'] != digest
            or r['steps_captured'] != count or r['steps_expected'] != count):
        raise ValueError('incomplete or wrong-product receipt: '+str(path))
    for name, digest in r['artifacts'].items():
        if sha((path.parent/name).read_bytes()) != digest:
            raise ValueError('runtime artifact drift: '+name)
    return r

verification = p/'analysis/battle_caption_verification.json'
v = json.loads(verification.read_text(encoding='utf-8'))
report = {'schema': 1, 'status': 'PASS; bounded runtime and direct visual inspection',
          'scope': spec['scope'], 'verification': proof(verification),
          'reviewer': 'Codex native-resolution screenshots directly inspected, 2026-09-17',
          'profiles': {}, 'not_claimed': v['not_claimed']}
shots = []
for key, s in spec['profiles'].items():
    target = p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_caption_korean_development.gba'
    data = target.read_bytes()
    m = json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
    digest = sha(data)
    if digest != m['output_sha256'] or digest != v['profiles'][key]['rom_sha256']:
        raise ValueError('product hash drift')
    roots = {kind: p/'analysis/runtime'/f'{key}_battle_caption_{kind}_01'
             for kind in ('cold', 'ready', 'final', 'calls')}
    cr = receipt(roots['cold']/'result.json', digest, 17)
    if cr['state_origin'] is not None or cr['actions_total'] != 263:
        raise ValueError('cold-route provenance drift')
    ready = receipt(roots['ready']/'result.json', digest, 35)
    lineage = []
    origin = roots['ready']/'result.json'
    while True:
        r = json.loads(origin.read_text(encoding='utf-8'))
        receipt(origin, digest, r['steps_expected'])
        lineage.append(proof(origin))
        if r['state_origin'] is None:
            if origin != roots['cold']/'result.json': raise ValueError('unexpected cold origin')
            break
        parent = Path(r['state_origin'])
        if r['state_sha256'] != sha((parent.parent/'checkpoint.mss').read_bytes()):
            raise ValueError('route checkpoint provenance drift')
        origin = parent
    hit = json.loads((roots['ready']/'exectrace_final.json').read_text())['sites']
    if not any(int(x['pc'], 16) == 0x08000000+s['hook']['offset'] and x['hits'] > 0 for x in hit):
        raise ValueError('caption hook not reached')
    for kind in ('final', 'calls'):
        r = receipt(roots[kind]/'result.json', digest, 6)
        if Path(r['state_origin']) != roots['ready']/'result.json' or r['state_sha256'] != sha((roots['ready']/'checkpoint.mss').read_bytes()):
            raise ValueError('continuation does not derive from exact cold product')
    chars = {c: i for i, c in enumerate(m['extension']['menu']['characters'])}
    checks = []
    for step, chip_id in enumerate(ids, 1):
        expected = b''
        for c in names[chip_id]:
            if c in chars:
                at = m['extension']['menu']['fonts'][0]+chars[c]*64
            else:
                code = table[c]
                if len(code) != 1: raise ValueError('unexpected native character')
                at = s['font']-0x08000000+code[0]*64
            raw = data[at:at+64]
            expected += b''.join(((int.from_bytes(raw[j:j+4], 'little')+0x88888888)&0xffffffff).to_bytes(4, 'little') for j in range(0, 64, 4))
        expected += b'\x88'*(512-len(expected))
        stem = roots['final']/f'step_{step:03d}'
        ram_path = Path(str(stem)+'_gbaExtWorkRam.bin')
        vram_path = Path(str(stem)+'_gbaVideoRam.bin')
        at = s['destination']-0x02000000
        va = s['vram']-0x06000000
        if ram_path.read_bytes()[at:at+512] != expected or vram_path.read_bytes()[va:va+512] != expected:
            raise ValueError(f'actual caption RAM/VRAM mismatch: {key} step {step}')
        shot = Path(str(stem)+'.png')
        shots.append((key, chip_id, shot))
        checks.append({'step': step, 'source_id': chip_id, 'text': names[chip_id],
                       'caption_sha256': sha(expected), 'screenshot': proof(shot),
                       'RAM': proof(ram_path), 'VRAM': proof(vram_path), 'bytes_verified': 512})
    calls = json.loads((roots['calls']/'tilecalls_final.json').read_text())['calls']
    captions = [x for x in calls if x['destination'] == s['destination']]
    observed = set()
    for call in captions:
        if (call['font'], call['width'], call['height'], call['tint']) != (s['font'], 8, 1, 8):
            raise ValueError('native caption renderer contract drift')
        for chip_id in set(ids):
            base = m['extension']['battle_caption']['archive_offsets']['41']
            ptr = base+int.from_bytes(data[base+chip_id*2:base+chip_id*2+2], 'little')
            if call['stream'] == 0x08000000+ptr and call['stream_prefix_hex'] == data[ptr:ptr+32].hex().upper():
                observed.add(chip_id)
    # The initial Cannon is inherited from the checkpoint and need not redraw.
    if observed != set(ids):
        raise ValueError('private caption streams not all observed: '+str(observed))
    report['profiles'][key] = {'rom_sha256': digest, 'cold_actions': 263,
        'cold_captures': 17, 'natural_source_ids': sorted(set(ids)), 'checks': checks,
        'private_stream_source_ids_observed': sorted(observed),
        'route_lineage': lineage,
        'receipts': [proof(roots[k]/'result.json') for k in roots]}

sheet = Image.new('RGB', (240*6, 180*2), 'white')
draw = ImageDraw.Draw(sheet)
for i, (key, chip_id, shot) in enumerate(shots):
    x, y = i%6*240, i//6*180
    draw.text((x+3, y+3), f'{key} ID {chip_id}', fill='black')
    sheet.paste(Image.open(shot).convert('RGB'), (x, y+20))
dest = p/'analysis/visual_qa/battle_caption_two_versions_01.png'
sheet.save(dest)
report['sheet'] = proof(dest)
(p/'analysis/BATTLE_CAPTION_RUNTIME_QA.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('PASS both products, four natural names, 12 RAM/VRAM captions, private stream matches')
