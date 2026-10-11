"""Source-bound ARMv4T Thumb dialogue extension; no tile-menu claim.

Normal F9 dispatch: r4 stream, r5 text context, r10 global context; r0/r1/r2/
r3/r6/r7 are native scratch. Legacy F9 subcommands tail-call unchanged.
New F9 FC is one syllable, keeps native pacing/sound/mouth bookkeeping and
resumes the verified normal-character continuation (not control bookkeeping).
Width F9 dispatch: r4 stream, r5 context; new syllable advances four bytes and
adds 12 to context+0x70; legacy subcommands tail-call unchanged.
"""
import json,sys
from pathlib import Path
from analyze_project import sha
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'external/arm_debug_python'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB,__version__ as KS_VERSION
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,__version__ as CS_VERSION
LEGACY_INDICES=442  # index 441 is a source palette alias; preserve its bytes.
HANGUL_COUNT=11172

def assemble_verified(code,address,literals):
    if KS_VERSION!='0.9.2' or CS_VERSION!='5.0.7':raise ValueError('ARM toolchain version drift')
    header='.syntax unified\n.cpu arm7tdmi\n.thumb\n'
    declarations='\n'.join(f'{name}: .word {value}' for name,value in literals.items())
    blob=bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(header+code+'\n.balign 4\n'+declarations,address)[0])
    count=sum(bool(line.strip()) and not line.strip().endswith(':') for line in code.splitlines())
    length=count*2
    instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob[:length],address))
    if len(instructions)!=count or any(i.size!=2 for i in instructions):raise ValueError('not complete Thumb-1 instruction boundaries')
    assembler=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
    for i in instructions:
        # Full external ARM assembler enforces CPU features; no partial encoder.
        if bytes(assembler.asm(header+i.mnemonic+' '+i.op_str,i.address)[0])!=i.bytes:raise ValueError('ARM assemble/disassemble disagreement '+hex(i.address))
        if i.mnemonic in ('b','beq','bne','bgt','bge','blt','ble','bmi','bpl'):
            target=int(i.op_str.lstrip('#'),0)
            if not address<=target<address+length or (target-address)%2:raise ValueError('bad final branch target')
        if i.mnemonic=='ldr' and '[pc,' in i.op_str:
            op=int.from_bytes(i.bytes,'little');pool=((i.address+4)&~3)+(op&255)*4
            if not address+length<=pool<address+len(blob) or pool%4:raise ValueError('bad final literal load')
    start=(length+3)&~3
    values=[int.from_bytes(blob[i:i+4],'little') for i in range(start,len(blob),4)]
    if values!=list(literals.values()):raise ValueError('literal-pool mismatch')
    return blob,{'isa':'ARM7TDMI ARMv4T little-endian Thumb-1; ARM and Thumb-2 generation excluded','assembler':'keystone-engine '+KS_VERSION,'disassembler':'capstone '+CS_VERSION,'address':address,'code_bytes':length,'literal_offset':start,'literal_values':literals,'final_placement_roundtrip':True,'instructions':[{'address':i.address,'hex':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in instructions]}

def JUMP(stream,tmp):
    """F9 FD a0 a1 a2 a3: continue the script stream at the little-endian
    address a0..a3 (an archive kept whole in ROM; see text_slots.py). The
    address is read byte by byte because the command has no alignment."""
    t='r7' if stream!='r7' and tmp!='r7' else 'r6'
    lines=[f'ldrb {tmp}, [{stream}, #5]',f'lsls {tmp}, {tmp}, #8',f'ldrb {t}, [{stream}, #4]',f'orrs {tmp}, {t}',
           f'lsls {tmp}, {tmp}, #8',f'ldrb {t}, [{stream}, #3]',f'orrs {tmp}, {t}',f'lsls {tmp}, {tmp}, #8',
           f'ldrb {t}, [{stream}, #2]',f'orrs {tmp}, {t}',f'movs {stream}, {tmp}']
    return ''.join(x+chr(10) for x in lines)

def construct(source,spec,compressed,glyphs):
    if spec['source_sha256']!=sha(source):raise ValueError('wrong expansion source')
    main=spec['main_dispatch_offset']
    if sha(source[main:main+0x18a])!=spec['main_dispatch_expected_sha256']:raise ValueError('dispatch scope drift')
    if set(glyphs)!={chr(0xac00+i) for i in range(HANGUL_COUNT)}:raise ValueError('full Hangul font supply missing')
    append=bytearray(compressed);layout=[]
    def alloc(blob,name):
        append.extend(b'\xff'*((-len(append))%4));at=len(source)+len(append)
        append.extend(blob);layout.append({'name':name,'offset':at,'size':len(blob),'sha256':sha(blob)})
        return at
    native_font=spec['font_literal']['expected_address']&0x1ffffff
    native_width=spec['advance_literal']['expected_address']&0x1ffffff
    font=source[native_font:native_font+LEGACY_INDICES*96]+b''.join(glyphs[chr(0xac00+i)] for i in range(HANGUL_COUNT))
    widths=source[native_width:native_width+LEGACY_INDICES*4]+(12).to_bytes(4,'little')*HANGUL_COUNT
    font_at=alloc(font,'source-compatible legacy view and 11172 Hangul glyphs')
    width_at=alloc(widths,'source-compatible legacy advances and Hangul advances')
    call=lambda label:f'ldr r7, {label}\nmov lr, pc\nbx r7\n'
    code='''ldrb r1, [r4, #1]
cmp r1, #0xfc
beq hangul
cmp r1, #0xfd
beq jump
ldr r7, legacy
bx r7
jump:
'''+JUMP('r4','r1')+'''movs r0, #0
mov pc, lr
hangul:
push {lr}
ldrb r1, [r4, #3]
lsls r1, r1, #8
ldrb r7, [r4, #2]
adds r1, r1, r7
ldr r7, bias
adds r1, r1, r7
ldrb r0, [r5, #0x11]
tst r0, r0
bne pacing
ldr r0, mode_mask
'''+call('flag_test')+'''bne draw
ldr r0, mode_mask
'''+call('flag_set')+'''pacing:
movs r0, #0
ldrb r2, [r5, #9]
cmp r2, #0
bgt delay
ldrb r2, [r5, #8]
strb r2, [r5, #9]
movs r0, #0x40
'''+call('flag_test')+'''bne draw
movs r2, #0x68
ldrh r0, [r5, r2]
'''+call('sound')+'''draw:
movs r0, #0
ldr r6, [r5, #0x7c]
'''+call('renderer')+call('bookkeeping')+'''adds r4, #4
movs r0, #0
b resume
delay:
subs r2, #1
strb r2, [r5, #9]
resume:
pop {r7}
ldr r7, continuation
bx r7
'''
    literals={'legacy':spec['normal_f9_slot']['handler_address'],'bias':LEGACY_INDICES,'mode_mask':0x800,'flag_test':spec['functions']['flag_test']|1,'flag_set':spec['functions']['flag_set']|1,'sound':spec['sound_address']|1,'renderer':spec['renderer_runtime_address']|1,'bookkeeping':spec['functions']['glyph_bookkeeping']|1,'continuation':spec['main_continuation_address']|1}
    next_at=len(source)+((len(append)+3)&~3)
    normal,normal_isa=assemble_verified(code,0x08000000+next_at,literals)
    normal_at=alloc(normal,'normal dialogue F9 FC handler')
    code='''ldrb r1, [r4, #1]
cmp r1, #0xfc
beq hangul
cmp r1, #0xfd
beq jump
ldr r7, legacy
bx r7
jump:
'''+JUMP('r4','r1')+'''mov pc, lr
hangul:
ldr r0, [r5, #0x70]
adds r0, #12
str r0, [r5, #0x70]
adds r4, #4
mov pc, lr
'''
    next_at=len(source)+((len(append)+3)&~3)
    width,width_isa=assemble_verified(code,0x08000000+next_at,{'legacy':spec['width_f9_slot']['handler_address']})
    width_hook_at=alloc(width,'cumulative-width F9 FC handler')
    patches=[]
    for name,value in [('normal_f9_slot',0x08000001+normal_at),('width_f9_slot',0x08000001+width_hook_at)]:
        slot=spec[name];at=slot['offset']
        if source[at:at+4].hex()!=slot['expected_hex']:raise ValueError('F9 dispatch slot drift')
        patches.append((at,value.to_bytes(4,'little'),name))
    for name,value in [('font_literal',0x08000000+font_at),('advance_literal',0x08000000+width_at)]:
        slot=spec[name];at=slot['offset']
        if int.from_bytes(source[at:at+4],'little')!=slot['expected_address']:raise ValueError('font pointer drift')
        patches.append((at,value.to_bytes(4,'little'),name))
    return bytes(append),patches,{'encoding':'F9 FC + uint16 LE Hangul syllable offset from U+AC00','hangul_syllables':HANGUL_COUNT,'legacy_index_view':LEGACY_INDICES,'legacy_palette_alias_index':441,'normal_font_offset':font_at,'advance_offset':width_at,'layout':layout,'machine_code':[normal_isa,width_isa],'native_font_and_width_bytes_unchanged':True,'tile_menu_hangul':'not implemented; native path unchanged','collision_population':'open; development only'}
