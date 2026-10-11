"""Bounded seven-row chip-library Hangul renderer with per-cell VRAM slots."""
import json
from analyze_project import sha
from menu_extension import prepare as prepare_short
from extended_dialogue import assemble_verified

def selection(p,key,source,wording):
 spec_path=p/'tools/specs/exe4_chip_library_v1.json';spec=json.loads(spec_path.read_text(encoding='utf-8'));s=spec['profiles'][key]
 if sha(source)!=s['source_sha256'] or sha(wording_path(p).read_bytes())!=spec['translation_asset_sha256']:raise ValueError('library source/translation identity drift')
 if wording.get('build_status')!='development seven-row library insertion only; other consumers excluded':raise ValueError('library translation policy drift')
 ids={x['chip_id'] for x in wording['entries']}
 if ids!=set(spec['catalog_chip_ids']) or len(wording['entries'])!=294:raise ValueError('library catalog scope drift')
 if any(x['id']!=f"archive/{41 if x['chip_id']<256 else 42:03d}/script/{x['chip_id'] if x['chip_id']<256 else x['chip_id']-256}" for x in wording['entries']):raise ValueError('library stable ID drift')
 if any(len(x['text'])>spec['cells'] for x in wording['entries']):raise ValueError('library row cell capacity exceeded')
 return {'consumer_contract_sha256':sha(spec_path.read_bytes()),'consumer_selection_verified':True,'scope':spec['scope'],'translation_review_state':'needs_review; development insertion authorized; not release wording'}

def wording_path(p):return p/'translations/chip_catalog_korean_draft.json'

def prepare(p,key,source,font,index,root):
 return prepare_short(p,key,source,font,None,root/'library_compilation',index,translation_asset=wording_path(p),selection_validator=selection)

def extend(p,key,source,append,prepared,menu):
 spec=json.loads((p/'tools/specs/exe4_chip_library_v1.json').read_text(encoding='utf-8'));s=spec['profiles'][key]
 ink,artifacts,metadata=prepared
 if [x[0] for x in artifacts]!=[41,42]:raise ValueError('library clone population drift')
 if sha(source)!=s['source_sha256']:raise ValueError('library source drift')
 anchor=s['loop_anchor'];
 if sha(source[anchor['offset']:anchor['offset']+anchor['size']])!=anchor['sha256']:raise ValueError('library loop anchor drift')
 parser=s['native_parser_entry']&~1
 if sha(source[parser-0x08000000:parser-0x08000000+s['native_parser_size']])!=s['native_parser_sha256']:raise ValueError('library native parser drift')
 copy=spec['copy_helper']
 if sha(source[copy['offset']:copy['offset']+copy['size']])!=s['copy_helper_sha256']:raise ValueError('library copy helper drift')
 if menu['syllables']!=4363 or len(menu['characters'])!=4363:raise ValueError('library menu font supply drift')
 blob=bytearray(append);layout=[]
 def alloc(data,name):
  blob.extend(b'\xff'*((-len(blob))%4));at=len(source)+len(blob);blob.extend(data)
  layout.append({'name':name,'offset':at,'size':len(data),'sha256':sha(data)});return at
 clones={ai:alloc(data,f'private library chip archive{ai} clone') for ai,row,data in artifacts}
 roots=alloc(b''.join((0x08000000+clones[ai]).to_bytes(4,'little') for ai in (41,42)),'private library archive41/42 root pair')
 code='''pop {r7}
push {r4, r5, r6, r7, lr}
ldr r7, upper_base
adds r5, r2, #0
subs r5, r5, r7
bmi native_gate
cmp r5, #0xc0
bgt native_gate
movs r7, #0x1f
tst r5, r7
bne native_gate
ldr r7, original41
cmp r0, r7
beq use41
ldr r7, original42
cmp r0, r7
bne native_gate
use42:
ldr r0, clone42
b selected
native_gate:
b native
use41:
ldr r0, clone41
selected:
lsls r1, r1, #1
ldrh r1, [r0, r1]
adds r0, r0, r1
push {r6}
push {r2}
adds r4, r0, #0
adds r5, r2, #0
adds r6, r3, #0
adds r7, r2, #0
ldr r1, upper_base
subs r7, r7, r1
lsrs r7, r7, #5
lsls r7, r7, #4
ldr r1, first_tile
adds r7, r7, r1
loop:
ldrb r0, [r4]
cmp r0, #0xf9
bne native_char
ldrb r1, [r4, #1]
cmp r1, #0xfc
bne done
ldr r1, [sp, #0]
adds r1, #0x10
cmp r5, r1
bge unsupported
ldrb r1, [r4, #3]
lsls r1, r1, #8
ldrb r0, [r4, #2]
adds r1, r1, r0
ldr r0, limit
cmp r1, r0
bge unsupported
lsls r1, r1, #1
ldr r0, lookup
ldrh r0, [r0, r1]
ldr r1, sentinel
cmp r0, r1
beq unsupported
lsls r0, r0, #6
ldr r1, font
adds r0, r0, r1
adds r1, r7, #0
lsls r1, r1, #5
ldr r3, vram
adds r1, r1, r3
movs r2, #0x40
ldr r3, copy
mov lr, pc
bx r3
adds r0, r7, #0
ldr r1, [sp, #4]
lsrs r1, r1, #10
lsls r1, r1, #10
orrs r0, r1
adds r4, #4
b draw
native_char:
cmp r0, #0xe5
bge done
ldr r1, [sp, #0]
adds r1, #0x10
cmp r5, r1
bge unsupported
lsls r0, r0, #1
ldr r1, [sp, #4]
adds r0, r0, r1
adds r4, #1
draw:
strh r0, [r5]
adds r0, #1
strh r0, [r6]
adds r5, #2
adds r6, #2
adds r7, #2
b loop
done:
ldr r1, [sp, #0]
adds r1, #0x10
pad:
cmp r5, r1
bge finish
movs r0, #0
strh r0, [r5]
strh r0, [r6]
adds r5, #2
adds r6, #2
b pad
finish:
adds r0, r4, #0
adds r2, r5, #0
adds r3, r6, #0
pop {r1}
pop {r1}
pop {r4, r5, r6, r7}
pop {r1}
ldr r1, continuation
bx r1
native:
lsls r1, r1, #1
ldrh r1, [r0, r1]
adds r0, r0, r1
ldr r7, native_parser
mov lr, pc
bx r7
pop {r4, r5, r6, r7}
pop {r1}
ldr r1, continuation
bx r1
unsupported:
b unsupported
'''
 at=len(source)+((len(blob)+3)&~3)
 literals={'upper_base':spec['upper_row_base'],'original41':s['roots']['41']['address'],'original42':s['roots']['42']['address'],'clone42':0x08000000+clones[42],'clone41':0x08000000+clones[41],'first_tile':spec['cache']['top_tile_first'],'limit':spec['hangul_code_limit'],'lookup':0x08000000+menu['map_offset'],'sentinel':65535,'font':0x08000000+menu['fonts'][0],'vram':0x06000000,'copy':copy['entry'],'continuation':s['hook']['continuation'],'native_parser':s['native_parser_entry']}
 machine,isa=assemble_verified(code,0x08000000+at,literals);hook=alloc(machine,'seven-row library private selector and F9FC renderer')
 point=s['hook'];expected=bytes.fromhex(point['expected_hex'])
 if source[point['offset']:point['offset']+len(expected)]!=expected:raise ValueError('library expected source write drift')
 jump,jisa=assemble_verified('push {r7}\nldr r7, target\nbx r7',0x08000000+point['offset'],{'target':0x08000001+hook})
 if len(jump)!=len(expected):raise ValueError('library hook window size drift')
 demand=sorted(metadata['glyph_demand'])
 return bytes(blob),[(point['offset'],jump,'private seven-row chip library selector')],{**metadata,'layout':layout,'machine_code':[isa],'jump_code':[jisa],'archive_offsets':{str(k):v for k,v in clones.items()},'archive_sizes':{str(ai):len(data) for ai,row,data in artifacts},'private_roots_offset':roots,'characters':demand,'active_residency_slots':spec['cache']['glyph_slots'],'cache':spec['cache'],'row_scope':{'upper_base':spec['upper_row_base'],'rows':spec['rows'],'stride':spec['row_stride'],'cells':spec['cells']},'menu_font_reused':{'font_offset':menu['fonts'][0],'map_offset':menu['map_offset']},'other_consumers_preserved':True,'whole_game_chip_localization':False}
