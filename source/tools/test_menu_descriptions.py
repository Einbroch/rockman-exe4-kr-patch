"""Real ARM7 tile parser, full clone preservation, and actual consumer selectors."""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'external/arm_debug_python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
from menu_extension import font_ink,pack
from test_descriptions import spans
spec=json.loads((p/'tools/specs/exe4_menu_descriptions_v2.json').read_text())
draft=json.loads((p/'translations/menu_chip_descriptions_korean_draft.json').read_text(encoding='utf-8'))
table={}
for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
 code,sep,ch=line.partition('=')
 if sep and len(ch)==1:table.setdefault(ch,bytes.fromhex(code))
def encode(text):return b''.join(b'\xe8' if c=='\n' else b'\xf9\xfc'+(ord(c)-0xac00).to_bytes(2,'little') if 0xac00<=ord(c)<=0xd7a3 else table[c] for c in text)
def fixture(data):
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
 u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,data)
 u.mem_map(0x03000000,0x8000);u.mem_map(0x02000000,0x40000)
 u.mem_write(0x03005800,data[0x212700:0x213ecc]);return u
def load(key):
 target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_v2_korean_development.gba'
 return target.read_bytes(),json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
def render(u,stream,font):
 u.mem_write(0x02001038,(0x02001200).to_bytes(4,'little'));u.mem_write(0x02001202,b'\0')
 u.mem_write(0x020177c0,b'\xaa'*(1920+128))
 for r,v in [(UC_ARM_REG_CPSR,0x1f3),(UC_ARM_REG_R0,stream),(UC_ARM_REG_R2,0x02017800),(UC_ARM_REG_R3,0x06011600),(UC_ARM_REG_R4,10),(UC_ARM_REG_R5,3),(UC_ARM_REG_R6,font),(UC_ARM_REG_R7,0),(UC_ARM_REG_R8,0x12345678),(UC_ARM_REG_R10,0x02001000),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03001001)]:u.reg_write(r,v)
 # Only final DMA queue helper is stubbed. Real snapshot proof covers VRAM.
 u.mem_write(0x08000874,bytes.fromhex('f746'))
 u.emu_start(0x0300677d,0x03001000,count=20000)
 # Native parser uses r8 for the 30-cell extent; it is not preserved here.
 if u.reg_read(UC_ARM_REG_PC)!=0x03001000 or u.reg_read(UC_ARM_REG_SP)!=0x03007e00 or u.reg_read(UC_ARM_REG_R8)!=30:raise AssertionError('parser return/extent')
 if bytes(u.mem_read(0x020177c0,64))!=b'\xaa'*64 or bytes(u.mem_read(0x02017f80,64))!=b'\xaa'*64:raise AssertionError('description exceeds 1920-byte window')
 return bytes(u.mem_read(0x02017800,1920))
def expected(data,m,text):
 ink=font_ink(Path(r'D:\Games\Kor Patch\CLude\폰트\Galmuri-v2.24.29\Galmuri7.bdf'))
 style=m['extension']['menu']['styles'][1];at=style['source_address']-0x08000000;blank=bytes([style['background']*17])*64
 lines=[]
 for line in text.split('\n'):
  raw=b''
  for ch in line:
   if ch in ink:raw+=pack(ink[ch],style)
   else:
    code=table[ch]
    if len(code)!=1:raise AssertionError('native cell unclassified')
    raw+=data[at+code[0]*64:at+(code[0]+1)*64]
  lines.append(raw+blank*(10-len(line)))
 return b''.join(lines)+blank*10*(3-len(lines))
class MenuDescriptions(unittest.TestCase):
 def test_every_script_exact_and_unselected_preserved(self):
  for key,s in spec['profiles'].items():
   data,m=load(key);t=m['extension']['menu_descriptions'];original=json.loads((p/'tools/specs/exe4_description_v1.json').read_text())['profiles'][key]
   old=spans(data[original['source_archive_offset']:original['source_archive_offset']+original['source_archive_size']]);new=spans(data[t['archive_offset']:t['archive_offset']+t['archive_size']])
   self.assertEqual(len(new),256);selected={int(x['id'].split('/')[-1]):x for x in draft['entries']}
   for i in range(256):
    if i in selected:
     x=selected[i];self.assertEqual(old[i].count(encode(x['source'])),1);self.assertEqual(new[i],old[i].replace(encode(x['source']),encode(x['text']),1))
    else:self.assertEqual(new[i],old[i])
 def test_all_ten_exact_1920_byte_tiles_and_canaries(self):
  for key,s in spec['profiles'].items():
   data,m=load(key);u=fixture(data);at=m['extension']['menu_descriptions']['archive_offset']
   for x in draft['entries']:
    idx=int(x['id'].split('/')[-1]);stream=0x08000000+at+int.from_bytes(data[at+idx*2:at+idx*2+2],'little')
    self.assertEqual(render(u,stream,s['consumers']['folder']['font']),expected(data,m,x['text']),(key,idx))
 def test_actual_selectors_311_ids_both_consumers(self):
  for key,s in spec['profiles'].items():
   data,m=load(key);base=(p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba').read_bytes()
   old,new=fixture(base),fixture(data)
   for c in s['consumers'].values():
    for idx in range(311):
     outputs=[]
     for u in [old,new]:
      for reg,val in [(UC_ARM_REG_CPSR,0x1f3),(UC_ARM_REG_R0,idx),(UC_ARM_REG_R8,0),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03001001)]:u.reg_write(reg,val)
      u.emu_start(0x08000001+c['start'],0x08000000+c['call'],count=100)
      self.assertEqual(u.reg_read(UC_ARM_REG_PC),0x08000000+c['call'])
      outputs.append([u.reg_read(r) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_SP]])
     wanted=outputs[0][:]
     if wanted[0]==s['source_pointer']:wanted[0]=0x08000000+m['extension']['menu_descriptions']['archive_offset']
     self.assertEqual(outputs[1],wanted,(key,idx))
if __name__=='__main__':unittest.main()
