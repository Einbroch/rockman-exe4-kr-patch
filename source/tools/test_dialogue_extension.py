"""Controlled CPU fixtures for the adopted extended-character ABI.

No game ROM, translation or current generated product is a test input.
Unicorn TI925T supplies an ARMv4T execution model. Dummy native helpers have
declared effects; real game rendering/pacing remains separate runtime QA.
"""
import unittest
from extended_dialogue import construct,sha,Ks,KS_ARCH_ARM,KS_MODE_THUMB
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *

def asm(code,address):
    return bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm('.cpu arm7tdmi\n.thumb\n'+code,address)[0])

class ABI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=bytearray(0x10000)
        funcs={'flag_test':0x08000300,'flag_set':0x08000310,'glyph_bookkeeping':0x08000320}
        for address,code in [(funcs['flag_test'],'push {r1}\nldrh r1,[r5,#0x3e]\nands r0,r1\npop {r1}\nmov pc,lr'),(funcs['flag_set'],'push {r1}\nldrh r1,[r5,#0x3e]\norrs r1,r0\nstrh r1,[r5,#0x3e]\npop {r1}\nmov pc,lr'),(funcs['glyph_bookkeeping'],'mov pc,lr'),(0x08000330,'mov pc,lr')]:
            code=asm(code,address);at=address-0x08000000;source[at:at+len(code)]=code
        spec={'main_dispatch_offset':0x200,'main_dispatch_expected_sha256':sha(source[0x200:0x38a]),'normal_f9_slot':{'offset':0x100,'expected_hex':'01050008','handler_address':0x08000501},'width_f9_slot':{'offset':0x104,'expected_hex':'01060008','handler_address':0x08000601},'font_literal':{'offset':0x108,'expected_address':0x08001000},'advance_literal':{'offset':0x10c,'expected_address':0x0800d000},'main_continuation_address':0x08000400,'functions':funcs,'sound_address':0x08000330,'renderer_runtime_address':0x03001000}
        for slot in ['normal_f9_slot','width_f9_slot']:source[spec[slot]['offset']:spec[slot]['offset']+4]=bytes.fromhex(spec[slot]['expected_hex'])
        for slot in ['font_literal','advance_literal']:source[spec[slot]['offset']:spec[slot]['offset']+4]=spec[slot]['expected_address'].to_bytes(4,'little')
        spec['source_sha256']=sha(source)
        glyphs={chr(0xac00+i):bytes([0x13])*96 for i in range(11172)}
        tail,patches,ext=construct(bytes(source),spec,b'\x10\0\0\0',glyphs)
        cls.ext=ext;cls.spec=spec
        cls.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);cls.u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
        cls.u.mem_map(0x08000000,0x400000);cls.u.mem_write(0x08000000,bytes(source)+tail)
        cls.u.mem_map(0x02000000,0x40000);cls.u.mem_map(0x03000000,0x8000)
        cls.u.mem_write(0x03001000,asm('ldr r2,[r5,#0x7c]\nadds r2,#48\nstr r2,[r5,#0x7c]\nmov pc,lr',0x03001000))

    def reset(self,stream,flags=0x800,delay=0,printing=0):
        u=self.u;u.mem_write(0x02002000,stream)
        u.mem_write(0x02001000,bytes(0x100))
        u.mem_write(0x0200103e,flags.to_bytes(2,'little'))
        u.mem_write(0x02001009,bytes([delay]));u.mem_write(0x02001011,bytes([printing]))
        for reg,value in [(UC_ARM_REG_R4,0x02002000),(UC_ARM_REG_R5,0x02001000),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,0x08000404),(UC_ARM_REG_R8,0x12345678),(UC_ARM_REG_R9,0x23456789),(UC_ARM_REG_R10,0x3456789a),(UC_ARM_REG_R11,0x456789ab),(UC_ARM_REG_R12,0x56789abc)]:u.reg_write(reg,value)
        u.reg_write(UC_ARM_REG_CPSR,0x1f3)

    def test_all_11172_syllables_execute_to_same_character_continuation(self):
        u=self.u;start=self.ext['machine_code'][0]['address'];end=self.spec['main_continuation_address']
        for index in range(11172):
            self.reset(b'\xf9\xfc'+index.to_bytes(2,'little'))
            u.emu_start(start|1,end,count=300)
            self.assertEqual(u.reg_read(UC_ARM_REG_PC),end)
            self.assertEqual(u.reg_read(UC_ARM_REG_R1),442+index)
            self.assertEqual(u.reg_read(UC_ARM_REG_R4),0x02002004)
            self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x03007000)
            self.assertEqual(int.from_bytes(u.mem_read(0x0200107c,4),'little'),48)
            self.assertTrue(u.reg_read(UC_ARM_REG_CPSR)&32)
            for reg,value in [(UC_ARM_REG_R8,0x12345678),(UC_ARM_REG_R9,0x23456789),(UC_ARM_REG_R10,0x3456789a),(UC_ARM_REG_R11,0x456789ab),(UC_ARM_REG_R12,0x56789abc)]:self.assertEqual(u.reg_read(reg),value)

    def test_delayed_character_leaves_stream_and_pixels_unchanged(self):
        self.reset(b'\xf9\xfc\0\0',flags=0,delay=2,printing=1)
        self.u.emu_start(self.ext['machine_code'][0]['address']|1,self.spec['main_continuation_address'],count=300)
        self.assertEqual(self.u.reg_read(UC_ARM_REG_R4),0x02002000)
        self.assertEqual(bytes(self.u.mem_read(0x02001009,1)),b'\1')
        self.assertEqual(bytes(self.u.mem_read(0x0200107c,4)),bytes(4))
        self.assertEqual(self.u.reg_read(UC_ARM_REG_SP),0x03007000)

    def test_paced_draw_uses_native_flag_helpers_and_restores_stack(self):
        self.reset(b'\xf9\xfc\xff\0',flags=0,delay=0,printing=1)
        self.u.emu_start(self.ext['machine_code'][0]['address']|1,self.spec['main_continuation_address'],count=300)
        self.assertEqual(self.u.reg_read(UC_ARM_REG_R4),0x02002004)
        self.assertEqual(self.u.reg_read(UC_ARM_REG_SP),0x03007000)

    def test_width_return_keeps_thumb_with_even_native_link_register(self):
        for index in [0,255,256,11171]:
            self.reset(b'\xf9\xfc'+index.to_bytes(2,'little'))
            self.u.reg_write(UC_ARM_REG_LR,0x08000400)
            self.u.emu_start(self.ext['machine_code'][1]['address']|1,0x08000400,count=30)
            self.assertEqual(int.from_bytes(self.u.mem_read(0x02001070,4),'little'),12)
            self.assertEqual(self.u.reg_read(UC_ARM_REG_R4),0x02002004)
            self.assertTrue(self.u.reg_read(UC_ARM_REG_CPSR)&32)

    def test_legacy_f9_subcommands_tail_call_original_handler(self):
        for segment,target in zip(self.ext['machine_code'],[0x08000500,0x08000600]):
            for subcommand in range(256):
                if subcommand==252:continue
                self.reset(bytes([249,subcommand,0,0]))
                self.u.emu_start(segment['address']|1,target,count=30)
                self.assertEqual(self.u.reg_read(UC_ARM_REG_R4),0x02002000)
                self.assertEqual(self.u.reg_read(UC_ARM_REG_SP),0x03007000)
                self.assertEqual(self.u.reg_read(UC_ARM_REG_PC),target)
                self.assertTrue(self.u.reg_read(UC_ARM_REG_CPSR)&32)

    def test_rejected_bx_lr_reproduces_arm_state_switch(self):
        self.u.mem_write(0x03002000,asm('bx lr',0x03002000));self.reset(b'')
        self.u.reg_write(UC_ARM_REG_LR,0x08000400)
        self.u.emu_start(0x03002001,0x08000400,count=1)
        self.assertFalse(self.u.reg_read(UC_ARM_REG_CPSR)&32)

if __name__=='__main__':unittest.main()
