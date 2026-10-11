"""F9 FC Hangul for the ROM proportional tile renderer (0x08053A30/0x08053A28).

That renderer draws the mail SUBJECT line and the staff credits. Its command
table (one word per code from E5) sends F9 to printShortString; this hook keeps
that for every F9 not followed by FC. For F9 FC it draws one syllable with the
renderer's own glyph routine: the routine reads glyph font[ctx+0x14] + code*0x60
and the advance of that code from the style's width table, so the hook points
the font base at the dialogue extension's Hangul bank shifted back by one glyph
and draws code 1, whose advance is 11 in both styles (441 of 442 native codes
are 11). The Hangul glyphs keep their ink in columns 0..10, so only the last
shadow column is trimmed. The font base is saved and restored by the hook.

The command table calls its handlers with `mov lr, pc`, so lr has no Thumb bit
and a handler must return with `pop {pc}` (no interworking), never `bx`.
"""
import json
from analyze_project import sha
from extended_dialogue import assemble_verified

SPEC='tools/specs/exe4_rom_renderer_hangul_v1.json'

from extended_dialogue import JUMP
CODE='''ldrb r1, [r0, #1]
cmp r1, #0xfc
beq hangul
cmp r1, #0xfd
beq jump
ldr r7, legacy
bx r7
jump:
'''+JUMP('r0','r1')+'''mov pc, lr
hangul:
push {r0, r3, lr}
ldrb r1, [r0, #3]
lsls r1, r1, #8
ldrb r2, [r0, #2]
adds r1, r1, r2
ldr r2, limit
cmp r1, r2
bge stop
movs r2, #0x60
muls r1, r2, r1
ldr r2, bank
adds r1, r1, r2
ldr r5, ctx
ldr r6, [r5, #0x14]
push {r6}
str r1, [r5, #0x14]
movs r1, #1
ldr r7, draw
mov lr, pc
bx r7
pop {r6}
ldr r5, ctx
str r6, [r5, #0x14]
pop {r0, r3}
adds r0, #4
pop {pc}
stop:
b stop'''


def extend(p,key,source,append,normal_font_offset):
    s=json.loads((p/SPEC).read_text(encoding='utf-8'));prof=s['profiles'][key]
    if sha(source)!=prof['source_sha256']:raise ValueError('ROM renderer source drift')
    slot=prof['slot']
    if int.from_bytes(source[slot:slot+4],'little')!=prof['legacy_handler']:raise ValueError('ROM renderer F9 slot drift')
    if source[prof['draw']&0x1fffffe:(prof['draw']&0x1fffffe)+4].hex()!=s['draw_head_hex']:raise ValueError('ROM renderer glyph routine drift')
    for at in prof['width_tables']:
        if int.from_bytes(source[(at&0x1ffffff)+4:(at&0x1ffffff)+8],'little')!=s['borrowed_code_advance']:raise ValueError('borrowed code advance drift')
    hangul=0x08000000+normal_font_offset+s['legacy_glyphs']*0x60
    blob=bytearray(append);blob.extend(b'\xff'*((-len(blob))%4));at=len(source)+len(blob)
    code,isa=assemble_verified(CODE,0x08000000+at,{'legacy':prof['legacy_handler'],'limit':11172,'bank':hangul-0x60,
                                                   'ctx':prof['context'],'draw':prof['draw']})
    blob.extend(code)
    return bytes(blob),[(slot,(0x08000001+at).to_bytes(4,'little'),'ROM renderer F9 slot -> Hangul hook')],{
        'layout':[{'name':'ROM renderer F9 FC Hangul hook','offset':at,'size':len(code),'sha256':sha(code)}],
        'machine_code':isa,'hangul_bank':hangul,'borrowed_code':1}
