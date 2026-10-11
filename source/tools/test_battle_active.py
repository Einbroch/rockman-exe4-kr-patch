"""Execute placed caption hook and native tile parser; DMA transport stub only."""
import json, sys, unittest
from pathlib import Path
from analyze_project import sha
from extended_dialogue import assemble_verified
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import *
p=Path(__file__).resolve().parents[1]
spec=json.loads((p/'tools/specs/exe4_battle_active_v1.json').read_text(encoding='utf-8'))
wording=json.loads((p/'translations/chip_catalog_korean_draft.json').read_text(encoding='utf-8'))
names={x['chip_id']:x['text'] for x in wording['entries']}

def machine(data):
    u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
    u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,data)
    u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x8000)
    u.mem_write(0x03005800,data[0x212700:0x213ecc])
    stub,_=assemble_verified('mov pc, lr',0x08000874,{})
    u.mem_write(0x08000874,stub)
    return u

def run(u,s,chip_id):
    root=s['roots']['41' if chip_id<256 else '42'];idx=chip_id&255
    u.mem_write(s['destination']-64,b'\xaa'*640)
    u.mem_write(0x02009e70+0x38,(0x02001000).to_bytes(4,'little'))
    u.mem_write(0x02001002,b'\x08')
    for reg,v in [(UC_ARM_REG_CPSR,0x1f3),(UC_ARM_REG_R0,root),(UC_ARM_REG_R1,idx),
        (UC_ARM_REG_R2,s['destination']),(UC_ARM_REG_R3,0x3333),(UC_ARM_REG_R4,0x4444),
        (UC_ARM_REG_R5,0x5555),(UC_ARM_REG_R6,0x6666),(UC_ARM_REG_R7,0x7777),
        (UC_ARM_REG_R8,0x8888),(UC_ARM_REG_R9,0x9999),(UC_ARM_REG_R10,0x02009e70),
        (UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,0x03001001)]:u.reg_write(reg,v)
    start=0x08000000+s['hook']['offset'];end=start+14
    u.emu_start(start|1,end,count=30000)
    if u.reg_read(UC_ARM_REG_PC)!=end:raise AssertionError('caption parser did not return')
    if bytes(u.mem_read(s['destination']-64,64))!=b'\xaa'*64 or bytes(u.mem_read(s['destination']+512,64))!=b'\xaa'*64:raise AssertionError('caption buffer overrun')
    if u.reg_read(UC_ARM_REG_SP)!=0x03007000 or u.reg_read(UC_ARM_REG_R8)!=0x8888 or u.reg_read(UC_ARM_REG_R9)!=0x9999:raise AssertionError('caption ABI corruption')
    return bytes(u.mem_read(s['destination'],512))

class Caption(unittest.TestCase):
    def test_all_311_ids_actual_parser_both_revisions(self):
        table={}
        for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
            code,sep,ch=line.partition('=')
            if sep and len(ch)==1:table.setdefault(ch,bytes.fromhex(code))
        for key,s in spec['profiles'].items():
            base=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_caption_korean_development.gba'
            target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba'
            data=target.read_bytes();m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
            self.assertEqual(sha(data),m['output_sha256'])
            u=machine(data);native=machine(base.read_bytes());menu=m['extension']['menu']
            chars={c:i for i,c in enumerate(menu['characters'])}
            for chip_id in range(311):
                got=run(u,s,chip_id)
                if chip_id not in names:self.assertEqual(got,run(native,s,chip_id));continue
                expected=b''
                for c in names[chip_id]:
                    if c in chars:at=menu['fonts'][0]+chars[c]*64
                    else:
                        code=table[c];self.assertEqual(len(code),1);at=s['font']-0x08000000+code[0]*64
                    raw=data[at:at+64]
                    expected+=b''.join(((int.from_bytes(raw[j:j+4],'little')+0x00000000)&0xffffffff).to_bytes(4,'little') for j in range(0,64,4))
                expected+=b'\x00'*(512-len(expected))
                self.assertEqual(got,expected,(key,chip_id,names[chip_id]))
                # The caller uses this count to place the damage number next
                # to the queued name; byte count must not replace glyph count.
                self.assertEqual(u.reg_read(UC_ARM_REG_R0),len(names[chip_id]))
    def test_selector_fallback_boundaries(self):
        for key,s in spec['profiles'].items():
            target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba'
            data=target.read_bytes();m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
            t=m['extension']['battle_active'];u=machine(data)
            for root,idx in [(s['roots']['42'],55),(s['roots']['42'],132),(0x02001234,1)]:
                for reg,v in [(UC_ARM_REG_CPSR,0x1f3),(UC_ARM_REG_R0,root),(UC_ARM_REG_R1,idx),(UC_ARM_REG_R2,s['destination']),(UC_ARM_REG_SP,0x03007000)]:u.reg_write(reg,v)
                u.emu_start((0x08000000+s['hook']['offset'])|1,s['hook']['continuation']&~1,count=100)
                self.assertEqual(u.reg_read(UC_ARM_REG_R0),root)
                self.assertEqual(u.reg_read(UC_ARM_REG_R1),idx)
                self.assertEqual(u.reg_read(UC_ARM_REG_R2),s['destination'])
                self.assertEqual(u.reg_read(UC_ARM_REG_R3),s['vram'])
                self.assertEqual(u.reg_read(UC_ARM_REG_R6),s['font'])

if __name__=='__main__':unittest.main()
