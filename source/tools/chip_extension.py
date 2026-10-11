"""Folder chooser chip names through a least-recently-used Hangul tile cache.

v1 uploaded the syllables of ten chip names as a fixed bank at 0x06006B80.
With every chip name translated the demand is 204 syllables, more than the
folder screen's character block can hold at once, and the fixed bank also sat
under the chip image the game uploads to 0x06006C00 only while a chip is being
moved (a user's save showed 크랙아웃 losing its middle syllable).

v2 keeps the folder screen's own font only where the screen still draws it --
space, digits, chip codes and the few signs (codes 0..10 and 94..127) -- and
turns the rest of that font's tiles, plus the free tiles of the block, into
151 cache slots. The row renderer looks each syllable up in a RAM table; a
miss takes the least recently drawn slot and copies the 64-byte glyph into
VRAM with the CPU, so nothing waits on the frame's DMA queue. The table is
cleared, and the reduced font enqueued, at each folder initialization.
"""
import json
from analyze_project import sha
from menu_extension import prepare as prepare_short,pack
from extended_dialogue import assemble_verified

SPEC='tools/specs/exe4_chip_folder_v2.json'


def selection(p,key,source,wording):
 path=p/SPEC;s=json.loads(path.read_text(encoding='utf-8'))
 profile=s['profiles'][key]
 if wording.get('build_status')!='folder_chooser_archive41_and_archive42_chip_names':raise ValueError('chip folder policy drift')
 if profile['source_sha256']!=sha(source):raise ValueError('chip source identity drift')
 for a in profile['anchors']:
  if sha(source[a['offset']:a['offset']+a['size']])!=a['sha256']:raise ValueError('chip native anchor drift')
 # 0x0802F068 takes ids 0..255 from archive41 and 256..310 from archive42.
 if any(not (x['id'].startswith('archive/041/script/') or x['id'].startswith('archive/042/script/') and int(x['id'].split('/')[-1])<=54) for x in wording['entries']):raise ValueError('chip folder scope drift')
 if any(len(x['text'])>s['max_hangul_cells'] for x in wording['entries']):raise ValueError('chip name cell capacity exceeded')
 keep=[c for a,b in s['native_keep'] for c in range(a,b)]
 for x in wording['entries']:
  for ch in x['text']:
   if not 0xac00<=ord(ch)<=0xd7a3 and ch not in NATIVE_KEEP_CHARS:raise ValueError('chip name uses a native glyph the folder no longer loads: '+ch)
 return {'consumer_contract_sha256':sha(path.read_bytes()),'consumer_selection_verified':True,
         'scope':'folder chooser clone; all other archive41 claims retain source','native_codes_kept':len(keep)}


def folder_characters(p,spec):
 """Syllables the folder glyph set holds: every chip name, plus the menu labels
 the link-screen row renderer copy draws (their wording lives in the menu asset)."""
 chips=json.loads((p/'translations/chip_folder_korean.json').read_text(encoding='utf-8'))['entries']
 labels=[x for x in json.loads((p/spec['row_parser_label_source']).read_text(encoding='utf-8'))['entries'] if x['id'] in spec['row_parser_label_ids']]
 if len(labels)!=len(spec['row_parser_label_ids']):raise ValueError('row parser label missing from the menu asset')
 return sorted({c for x in chips+labels for c in x['text'] if 0xac00<=ord(c)<=0xd7a3})


# Characters of codes 0..10 and 94..127 in exe4-utf8.tbl.
NATIVE_KEEP_CHARS=set(' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ*-+')


def prepare(p,key,source,font,index,root):
 return prepare_short(p,key,source,font,None,root/'chip_compilation',index,
  translation_asset=p/'translations/chip_folder_korean.json',selection_validator=selection)


def extend(p,key,source,append,prepared):
 spec=json.loads((p/SPEC).read_text(encoding='utf-8'));s=spec['profiles'][key]
 ink,artifacts,metadata=prepared
 if [a[0] for a in artifacts]!=[41,42]:raise ValueError('chip clone population drift')
 chars=folder_characters(p,spec);blob=bytearray(append);layout=[]
 def alloc(data,name):
  blob.extend(b'\xff'*((-len(blob))%4));at=len(source)+len(blob);blob.extend(data)
  layout.append({'name':name,'offset':at,'size':len(data),'sha256':sha(data)});return at
 clone=alloc(artifacts[0][2],'folder chip archive41 clone');clone42=alloc(artifacts[1][2],'folder chip archive42 clone')
 style=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))['profiles'][key]['fonts'][0]
 font=alloc(b''.join(pack(ink[c],style) for c in chars),'folder Hangul glyphs, one 64-byte record per syllable')
 ordinals=bytearray(b'\xff\xff'*11172)
 for i,c in enumerate(chars):ordinals[(ord(c)-0xac00)*2:(ord(c)-0xac00)*2+2]=i.to_bytes(2,'little')
 ord_at=alloc(bytes(ordinals),'folder syllable-to-glyph-record table')
 tiles=spec['slot_tiles'];n=len(tiles)
 tiles_at=alloc(b''.join(t.to_bytes(2,'little') for t in tiles),'folder cache slot tile numbers')
 cache=spec['cache_ram'];stamps=cache+((4+2*n+3)&~3)
 codes=[]
 def add_code(code,literals,name):
  at=len(source)+((len(blob)+3)&~3);data,isa=assemble_verified(code,0x08000000+at,literals)
  alloc(data,name);codes.append(isa);return 0x08000001+at
 call='ldr r4, queue\nmov lr, pc\nbx r4\n'
 (k0,k1),(k2,k3)=spec['native_keep']
 upload=('push {r4, lr}\n'
         'ldr r0, cache\nmovs r1, #0\nstr r1, [r0]\nadds r1, r0, #4\nldr r2, empty\nldr r3, slots\n'
         'cpclear:\nstrh r2, [r1]\nadds r1, #2\nsubs r3, #1\nbne cpclear\n'
         'ldr r1, stamps\nmovs r2, #0\nldr r3, slots\n'
         'stclear:\nstr r2, [r1]\nadds r1, #4\nsubs r3, #1\nbne stclear\n'
         'ldr r0, keep0\nldr r1, dest0\nldr r2, bytes0\n'+call+
         'ldr r0, keep1\nldr r1, dest1\nldr r2, bytes1\n'+call+
         'pop {r4}\npop {r3}\nldr r0, keep0\nldr r1, dest0\nldr r2, bytes0\nldr r3, continuation\nmov lr, r3\nbx r3')
 nf=s['native_font_address']
 literals={'cache':cache,'empty':0xffff,'slots':n,'stamps':stamps,'queue':spec['queue_helper'],
           'keep0':nf+64*k0,'dest0':0x06004000+64*k0,'bytes0':64*(k1-k0),
           'keep1':nf+64*k2,'dest1':0x06004000+64*k2,'bytes1':64*(k3-k2),
           'continuation':s['upload_patch']['continuation']}
 upload_address=add_code(upload,literals,'folder cache reset and reduced native font enqueue hook')
 # In: r1 = syllable index. Out: r4 = top tile of its slot. r1 is scratch;
 # every other low register comes back as it went in.
 lookup='''push {r0, r2, r3, r5, r6, r7, lr}
adds r0, r1, #0
ldr r7, cache
ldr r6, [r7]
adds r6, #1
str r6, [r7]
mov r12, r6
movs r5, #0
ldr r4, slots
ldr r3, maxstamp
movs r2, #0
scan:
cmp r5, r4
bge miss
lsls r1, r5, #1
adds r1, #4
ldrh r1, [r7, r1]
cmp r1, r0
beq hit
lsls r1, r5, #2
ldr r6, stampoff
adds r1, r1, r6
ldr r1, [r7, r1]
cmp r1, r3
bhs next
adds r3, r1, #0
adds r2, r5, #0
next:
adds r5, #1
b scan
hit:
lsls r1, r5, #2
ldr r6, stampoff
adds r1, r1, r6
mov r6, r12
str r6, [r7, r1]
b tile
miss:
adds r5, r2, #0
lsls r1, r5, #1
adds r1, #4
strh r0, [r7, r1]
lsls r1, r5, #2
ldr r6, stampoff
adds r1, r1, r6
mov r6, r12
str r6, [r7, r1]
lsls r1, r0, #1
ldr r6, ordinals
ldrh r1, [r6, r1]
lsls r1, r1, #6
ldr r6, glyphs
adds r6, r6, r1
lsls r1, r5, #1
ldr r3, tiles
ldrh r1, [r3, r1]
lsls r1, r1, #5
ldr r3, vram
adds r3, r3, r1
movs r2, #16
copy:
ldmia r6!, {r1}
stmia r3!, {r1}
subs r2, #1
bne copy
tile:
lsls r1, r5, #1
ldr r3, tiles
ldrh r4, [r3, r1]
pop {r0, r2, r3, r5, r6, r7, pc}'''
 lookup_address=add_code(lookup,{'cache':cache,'slots':n,'maxstamp':0xffffffff,'stampoff':stamps-cache,
   'ordinals':0x08000000+ord_at,'glyphs':0x08000000+font,'tiles':0x08000000+tiles_at,'vram':0x06000000},
   'folder least-recently-used Hangul slot lookup')
 parser='''push {r5, r7, lr}
movs r6, #0x20
lsls r6, r6, #4
push {r2, r3}
subs r3, r3, r2
lsls r3, r3, #1
adds r3, r3, r2
clear:
strh r6, [r2]
adds r2, #2
cmp r2, r3
blt clear
pop {r2, r3}
lsls r1, r1, #1
ldrh r4, [r0, r1]
adds r0, r0, r4
movs r5, #0
loop:
ldrb r1, [r0]
cmp r1, #0xf9
bne native
ldrb r7, [r0, #1]
cmp r7, #0xfc
bne done
cmp r5, #8
bge unsupported
ldrb r1, [r0, #3]
lsls r1, r1, #8
ldrb r7, [r0, #2]
adds r1, r1, r7
ldr r7, limit
cmp r1, r7
bge unsupported
lsls r7, r1, #1
ldr r4, ordinals
ldrh r4, [r4, r7]
ldr r7, sentinel
cmp r4, r7
beq unsupported
ldr r7, lookup
mov lr, pc
bx r7
adds r0, #4
b draw
native:
cmp r1, #0xe5
bge done
lsls r1, r1, #1
adds r4, r6, r1
adds r0, #1
draw:
strh r4, [r2]
adds r4, #1
strh r4, [r3]
adds r2, #2
adds r3, #2
adds r5, #1
b loop
done:
pop {r5, r7}
pop {r4}
ldr r4, continuation
mov lr, r4
bx r4
unsupported:
b unsupported'''
 parser_address=add_code(parser,{'limit':11172,'ordinals':0x08000000+ord_at,'sentinel':65535,'lookup':lookup_address,
   'continuation':s['parser_patch']['continuation']},'folder F9FC BG tilemap row renderer')
 # Link-cable screens (0x0803CFA6, 0x0804C42E/0x0804C526) call the same chooser
 # but upload the whole native font themselves; give each upload the same
 # cache reset, then run the original copy and come back after it.
 clear=('ldr r0, cache\nmovs r1, #0\nstr r1, [r0]\nadds r1, r0, #4\nldr r2, empty\nldr r3, slots\n'
        'cpclear:\nstrh r2, [r1]\nadds r1, #2\nsubs r3, #1\nbne cpclear\n'
        'ldr r1, stamps\nmovs r2, #0\nldr r3, slots\n'
        'stclear:\nstr r2, [r1]\nadds r1, #4\nsubs r3, #1\nbne stclear\n')
 windows=[('upload_patch',s['upload_patch'],upload_address,'r0'),('parser_patch',s['parser_patch'],parser_address,'r6')]
 for point in s['link_upload_patches']:
  link=clear+'ldr r0, font\nldr r1, dest\nldr r2, size\nldr r3, continuation\nmov lr, r3\nldr r3, copier\nbx r3'
  address=add_code(link,{'cache':cache,'empty':0xffff,'slots':n,'stamps':stamps,'font':nf,'dest':0x06004000,
    'size':point['font_bytes'],'continuation':point['continuation'],'copier':point['copier']},'link screen cache reset and native font copy')
  windows.append(('link_upload_patch',point,address,'r0'))
 for point in s['extra_row_parser_patches']:
  epilogue=add_code(point['epilogue'],{},'link screen row caller epilogue')
  extra=parser.replace('push {r5, r7, lr}',point['prologue']+'\npush {r5, r7, lr}',1)
  address=add_code(extra,{'limit':11172,'ordinals':0x08000000+ord_at,'sentinel':65535,'lookup':lookup_address,
    'continuation':epilogue},'link screen F9FC BG tilemap row renderer')
  windows.append(('extra_row_parser_patch',point,address,'r6'))
 patches=[];jumps=[]
 for kind,point,address,reg in windows:
  at=point['offset'];expected=bytes.fromhex(point['expected_hex'])
  if source[at:at+len(expected)]!=expected:raise ValueError('chip expected source write drift')
  code,isa=assemble_verified(f'ldr {reg}, target\nbx {reg}',0x08000000+at,{'target':address})
  for pad in range(8,len(expected),2):
   nop,nop_isa=assemble_verified('mov r8, r8',0x08000000+at+pad,{})
   code+=nop[:2];jumps.append(nop_isa)
  if len(code)!=len(expected):raise ValueError('chip patch window size drift')
  patches.append((at,code,'folder '+kind));jumps.append(isa)
 at=s['clone_pointer']
 if int.from_bytes(source[at:at+4],'little')!=0x08000000+s['original_archive_offset']:raise ValueError('chip source clone pointer drift')
 patches.append((at,(0x08000000+clone).to_bytes(4,'little'),'folder chip clone literal'))
 second=s['second_clone'];at=second['pointer']
 if int.from_bytes(source[at:at+4],'little')!=0x08000000+second['original_archive_offset']:raise ValueError('chip source archive42 pointer drift')
 patches.append((at,(0x08000000+clone42).to_bytes(4,'little'),'folder chip archive42 clone literal'))
 return bytes(blob),patches,{**metadata,'layout':layout,'machine_code':codes,'jump_code':jumps,'archive_offset':clone,
   'archive_size':len(artifacts[0][2]),'archive42_offset':clone42,'archive42_size':len(artifacts[1][2]),'font_offset':font,'ordinal_offset':ord_at,'slot_tiles_offset':tiles_at,
   'cache_ram':cache,'stamp_ram':stamps,'slots':n,'characters':chars,'native_keep':spec['native_keep'],'styles':[style],
   'other_archive_claims_preserved':s['other_archive_claims_preserved'],'other_archive42_claims_preserved':second['other_archive_claims_preserved'],'native_parser_preserved':True,
   'whole_game_chip_localization':False}
