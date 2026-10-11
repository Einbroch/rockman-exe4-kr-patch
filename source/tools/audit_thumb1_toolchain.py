"""ARMv4T Thumb toolchain audit; does not claim complete game control flow.

Enumerates all defined 16-bit encoding families (excluding unpredictable empty
lists/low-low high-register forms), plus each BL half-field value against
zero and extreme opposite halves. Full external assembler/disassembler own
instruction semantics; this enumeration is an analysis audit, not a decoder.
"""
import json
from pathlib import Path
from extended_dialogue import Ks,KS_ARCH_ARM,KS_MODE_THUMB,Cs,CS_ARCH_ARM,CS_MODE_THUMB
p=Path(__file__).resolve().parents[1]
ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB);cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
address=0x08800000;header='.cpu arm7tdmi\n.thumb\n'
counts={};failures=[];rejected=0
def family(w):
    if w<0x1800:return 'shift-immediate'
    if w<0x2000:return 'add-subtract'
    if w<0x4000:return 'immediate-alu'
    if w<0x4400:return 'register-alu'
    if w<0x4700:
        if w&0xc0==0:return None  # low-low high-register encoding unpredictable
        return 'high-register-alu'
    if w<0x4800:return 'branch-exchange' if w&0x87==0 else None
    if w<0x5000:return 'pc-relative-load'
    if w<0x6000:return 'register-load-store'
    if w<0x8000:return 'immediate-load-store'
    if w<0x9000:return 'halfword-load-store'
    if w<0xa000:return 'sp-relative-load-store'
    if w<0xb000:return 'load-address'
    if w<0xb100:return 'sp-adjust'
    if w&0xfe00 in (0xb400,0xbc00):return 'push-pop' if w&0x1ff else None
    if 0xc000<=w<0xd000:return 'load-store-multiple' if w&0xff else None
    if 0xd000<=w<0xde00:return 'conditional-branch'
    if 0xdf00<=w<0xe000:return 'software-interrupt'
    if 0xe000<=w<0xe800:return 'unconditional-branch'
    return None
def audit(blob,name):
    ins=list(cs.disasm(blob,address))
    if len(ins)!=1 or ins[0].size!=len(blob):failures.append({'hex':blob.hex(),'family':name,'failure':'decode boundary'});return
    i=ins[0];statement=i.mnemonic+' '+i.op_str
    # Both engines use ADR's relative immediate. At the last two forward
    # branch encodings, Keystone's numeric-target path rejects a valid branch;
    # its symbolic-label fixup path encodes the same ARMv4T target correctly.
    if name in ('conditional-branch','unconditional-branch'):
        target=int(i.op_str.lstrip('#'),0);delta=target-address
        limit=256 if name=='conditional-branch' else 2048
        if delta>=limit:statement=i.mnemonic+' target\n.space '+str(delta-2)+',0\ntarget:'
    try:rebuilt=bytes(ks.asm(header+statement,address)[0])[:len(blob)]
    except Exception as ex:failures.append({'hex':blob.hex(),'family':name,'statement':statement,'failure':str(ex)});return
    if rebuilt!=blob:failures.append({'hex':blob.hex(),'family':name,'statement':statement,'rebuilt':rebuilt.hex()});return
    counts[name]=counts.get(name,0)+1
for w in range(65536):
    f=family(w)
    if f:audit(w.to_bytes(2,'little'),f)
    else:rejected+=1
for hi in range(2048):
    for lo in [0,1023,2047]:audit((0xf000|hi).to_bytes(2,'little')+(0xf800|lo).to_bytes(2,'little'),'long-branch-link')
for lo in range(2048):
    for hi in [0,1023,2047]:audit((0xf000|hi).to_bytes(2,'little')+(0xf800|lo).to_bytes(2,'little'),'long-branch-link')
report={'isa':'ARM7TDMI ARMv4T little-endian Thumb-1','primary_reference':'ARM7TDMI Technical Reference Manual https://documentation-service.arm.com/static/5e8e1323fd977155116a3129','scope':'full declared instruction families and addressing modes; all defined 16-bit opcodes enumerated; BL field-wise boundaries, not every 22-bit combination','assembly_grammar':'ADR relative immediates; internal symbolic branch labels, including forward branch boundaries; numeric-target Keystone bug not accepted as ISA support loss','passed_by_family':counts,'not_standalone_valid_16bit_words':rejected,'failure_count':len(failures),'failures':failures,'status':'PASS' if not failures else 'FAIL'}
(p/'analysis/thumb1_toolchain_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(report['status'],sum(counts.values()),'encodings;',len(failures),'failures')
if failures:print(json.dumps(failures[:12],indent=2));raise SystemExit(1)
