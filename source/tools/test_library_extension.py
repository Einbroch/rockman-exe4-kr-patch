"""Execute every ROM-backed chip ID through the final seven-row library hook."""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(p/'external/arm_debug_python'),str(p/'tools')]
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_INTR
from unicorn.arm_const import *
from analyze_project import PROFILES,sha

spec=json.loads((p/'tools/specs/exe4_chip_library_v1.json').read_text(encoding='utf-8'))
draft=json.loads((p/'translations/chip_catalog_korean_draft.json').read_text(encoding='utf-8'))
selected={x['chip_id']:x for x in draft['entries']}

def fixture(rom):
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
 u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,rom)
 u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x8000);u.mem_map(0x06000000,0x20000)
 copies=[]
 def intr(uc,number,user):
  if number!=2:raise AssertionError('unexpected ARM interrupt '+str(number))
  source=uc.reg_read(UC_ARM_REG_R0);destination=uc.reg_read(UC_ARM_REG_R1);control=uc.reg_read(UC_ARM_REG_R2)
  if control&0x01000000:raise AssertionError('unexpected CpuSet fill')
  size=(control&0x1fffff)*(4 if control&0x04000000 else 2)
  uc.mem_write(destination,bytes(uc.mem_read(source,size)));copies.append((source,destination,size))
 u.hook_add(UC_HOOK_INTR,intr)
 return u,copies

def setup(u):
 u.reg_write(UC_ARM_REG_SP,0x03007000);u.reg_write(UC_ARM_REG_LR,0x03001001);u.reg_write(UC_ARM_REG_CPSR,0x1f3)

def source_stream(rom,root,id):
 off=int.from_bytes(rom[root+id*2:root+id*2+2],'little');return 0x08000000+root+off

def call_native(rom,entry,stream,row=0):
 u,_=fixture(rom);setup(u);upper=spec['upper_row_base']+row*spec['row_stride'];u.mem_write(spec['upper_row_base'],b'\xaa'*(spec['rows']*spec['row_stride']))
 for reg,value in [(UC_ARM_REG_R0,stream),(UC_ARM_REG_R2,upper),(UC_ARM_REG_R3,upper+16),(UC_ARM_REG_R6,spec['palette_tile_base'])]:u.reg_write(reg,value)
 u.reg_write(UC_ARM_REG_LR,0x03001001);u.emu_start(entry,0x03001000,count=1000)
 return bytes(u.mem_read(upper,32))

def call_hook(u,s,root,id,row=0,count=5000):
 upper=spec['upper_row_base']+row*spec['row_stride'];u.mem_write(spec['upper_row_base'],b'\xaa'*(spec['rows']*spec['row_stride']))
 values=(0x4444,0x5555,spec['palette_tile_base'],0x7777)
 for reg,value in [(UC_ARM_REG_R0,root),(UC_ARM_REG_R1,id),(UC_ARM_REG_R2,upper),(UC_ARM_REG_R3,upper+16),(UC_ARM_REG_R4,values[0]),(UC_ARM_REG_R5,values[1]),(UC_ARM_REG_R6,values[2]),(UC_ARM_REG_R7,values[3])]:u.reg_write(reg,value)
 setup(u);u.emu_start((0x08000000+s['hook']['offset'])|1,s['hook']['continuation']&~1,count=count)
 return bytes(u.mem_read(upper,32)),values

class LibraryExtension(unittest.TestCase):
 def test_all_311_ROM_ids_and_all_seven_cache_rows(self):
  for key in PROFILES:
   path=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_korean_development.gba';rom=path.read_bytes();m=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'));self.assertEqual(sha(rom),m['output_sha256'])
   t=m['extension']['chip_library'];s=spec['profiles'][key];u,copies=fixture(rom);setup(u)
   menu=m['extension']['menu'];clone={int(ai):at for ai,at in t['archive_offsets'].items()}
   for chip_id in range(311):
    ai=41 if chip_id<256 else 42;local=chip_id if ai==41 else chip_id-256;root=s['roots'][str(ai)]['address'];before=len(copies)
    got,registers=call_hook(u,s,root,local)
    self.assertEqual([u.reg_read(x) for x in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7)],list(registers),(key,chip_id))
    self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x03007000,(key,chip_id));self.assertEqual(u.reg_read(UC_ARM_REG_PC),s['hook']['continuation']&~1,(key,chip_id))
    if chip_id not in selected:
     stream=source_stream(rom,s['roots'][str(ai)]['offset'],local);self.assertEqual(got,call_native(rom,s['native_parser_entry'],stream),(key,chip_id));self.assertEqual(len(copies),before,(key,chip_id));continue
    at=clone[ai]+int.from_bytes(rom[clone[ai]+local*2:clone[ai]+local*2+2],'little');tiles=[];hangul=[]
    while True:
     b=rom[at]
     if rom[at:at+2]==b'\xf9\xfc':
      cp=int.from_bytes(rom[at+2:at+4],'little');ordinal=int.from_bytes(rom[menu['map_offset']+cp*2:menu['map_offset']+cp*2+2],'little');self.assertNotEqual(ordinal,65535)
      slot=len(tiles);tile=(spec['palette_tile_base']&0xfc00)|((spec['cache']['top_tile_first']+slot*2)&0x3ff);glyph=rom[menu['fonts'][0]+ordinal*64:menu['fonts'][0]+(ordinal+1)*64];hangul.append((slot,glyph));at+=4
     elif b<0xe5:tile=spec['palette_tile_base']+b*2;at+=1
     else:break
     tiles.append(tile)
    expected=tiles+[0]*(8-len(tiles))+[x+1 for x in tiles]+[0]*(8-len(tiles));self.assertEqual(got,b''.join(x.to_bytes(2,'little') for x in expected),(key,chip_id))
    self.assertEqual(len(copies)-before,len(hangul),(key,chip_id))
    for slot,glyph in hangul:self.assertEqual(bytes(u.mem_read(spec['cache']['start']+slot*64,64)),glyph,(key,chip_id,slot))
   for row in range(7):
    got,_=call_hook(u,s,s['roots']['41']['address'],1,row);self.assertNotEqual(got[:4],b'\0'*4)
    base=spec['cache']['start']+row*8*64
    for source,destination,size in copies[-2:]:self.assertTrue(base<=destination<base+8*64 and size==64,(key,row,hex(destination)))

 def test_native_fallback_and_explicit_unsupported_stops(self):
  for key in PROFILES:
   path=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_korean_development.gba';rom=path.read_bytes();m=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'));t=m['extension']['chip_library'];s=spec['profiles'][key]
   # A non-seven-row destination must stay on the native source archive/parser.
   u,copies=fixture(rom);setup(u);bad=spec['upper_row_base']+2
   for reg,value in [(UC_ARM_REG_R0,s['roots']['41']['address']),(UC_ARM_REG_R1,1),(UC_ARM_REG_R2,bad),(UC_ARM_REG_R3,bad+16),(UC_ARM_REG_R6,spec['palette_tile_base']),(UC_ARM_REG_R7,0x7777)]:u.reg_write(reg,value)
   u.mem_write(bad,b'\xaa'*32);u.emu_start((0x08000000+s['hook']['offset'])|1,s['hook']['continuation']&~1,count=2000)
   stream=source_stream(rom,s['roots']['41']['offset'],1);self.assertEqual(bytes(u.mem_read(bad,32)),call_native(rom,s['native_parser_entry'],stream));self.assertFalse(copies);self.assertEqual(u.reg_read(UC_ARM_REG_R7),0x7777)
   # Mutate only an emulated clone fixture to exercise absent, range, and ninth-cell stops.
   code=t['machine_code'][0];stop=code['instructions'][-1]['address'];clone=t['archive_offsets']['41'];present=ord(t['characters'][0])-0xac00
   lookup=bytearray(rom[m['extension']['menu']['map_offset']:m['extension']['menu']['map_offset']+11172*2]);absent=next(i for i in range(11172) if int.from_bytes(lookup[i*2:i*2+2],'little')==65535)
   for indexes in ([absent],[11172],[present]*9):
    u,copies=fixture(rom);setup(u);offset=2200;u.mem_write(0x08000000+clone,(offset).to_bytes(2,'little'));u.mem_write(0x08000000+clone+offset,b''.join(b'\xf9\xfc'+i.to_bytes(2,'little') for i in indexes)+b'\xe5')
    u.mem_write(spec['upper_row_base'],b'\xaa'*224)
    for reg,value in [(UC_ARM_REG_R0,s['roots']['41']['address']),(UC_ARM_REG_R1,0),(UC_ARM_REG_R2,spec['upper_row_base']),(UC_ARM_REG_R3,spec['upper_row_base']+16),(UC_ARM_REG_R6,spec['palette_tile_base']),(UC_ARM_REG_R7,0x7777)]:u.reg_write(reg,value)
    u.emu_start((0x08000000+s['hook']['offset'])|1,0,count=1000)
    self.assertEqual(u.reg_read(UC_ARM_REG_PC),stop,(key,indexes));self.assertEqual(bytes(u.mem_read(spec['upper_row_base']+32,16)),b'\xaa'*16)

if __name__=='__main__':unittest.main()
