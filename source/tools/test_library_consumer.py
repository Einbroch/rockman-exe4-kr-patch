"""Whole original library tilemap function; source and current-ROM counterproof."""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'external/arm_debug_python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
from analyze_project import PROFILES,sha
entries={'blue_moon':0x08038030,'red_sun':0x08038064}
class LibraryConsumer(unittest.TestCase):
 def test_native_palette_padding_and_F9FC_rejection_in_both_versions(self):
  bodies=[]
  for key,pr in PROFILES.items():
   source=next(f.read_bytes() for f in p.parents[1].glob('*.gba') if sha(f.read_bytes())==pr['sha256']);at=entries[key]-0x08000000
   bodies.append(source[at:at+52]);product=(p/'poc/output'/f'{key}_opening_menu_chip_folder_korean_development.gba').read_bytes()
   self.assertEqual(source[at:at+52],product[at:at+52])
   for r in [source,product]:
    for stream,indexes in [(b'\x11\x30\x2b\x3a\xe5',[17,48,43,58]),(bytes(range(1,9))+b'\xe5',list(range(1,9))),(b'\xf9\xfc\0\0\xe5',[]),(b'\x11\xf9\xfc\0\0\xe5',[17])]:
     for palette in (0x2200,0xe200):
      u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T);u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,r);u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x8000)
      u.mem_write(0x02002000,stream);u.mem_write(0x02004000,b'\xaa'*48)
      for reg,v in [(UC_ARM_REG_CPSR,0x1f3),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,0x03001001),(UC_ARM_REG_R0,0x02002000),(UC_ARM_REG_R2,0x02004000),(UC_ARM_REG_R3,0x02004010),(UC_ARM_REG_R4,0x4444),(UC_ARM_REG_R6,palette),(UC_ARM_REG_R7,0x7777)]:u.reg_write(reg,v)
      u.emu_start(entries[key]|1,0x03001000,count=300)
      expected=[palette+2*i for i in indexes]+[0]*(8-len(indexes))+[palette+2*i+1 for i in indexes]+[0]*(8-len(indexes))
      self.assertEqual(bytes(u.mem_read(0x02004000,32)),b''.join(i.to_bytes(2,'little') for i in expected))
      self.assertEqual(bytes(u.mem_read(0x02004020,16)),b'\xaa'*16)
      self.assertEqual(u.reg_read(UC_ARM_REG_R0),0x02002000+len(indexes))
      self.assertEqual([u.reg_read(x) for x in (UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_SP)],[0x02004010,0x02004020,0x4444,palette,0x7777,0x03007000])
  self.assertEqual(*bodies)
if __name__=='__main__':unittest.main()
