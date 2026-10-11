"""Execute the actual selector tail and verify every clone script independently."""
import json,unittest,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'external/arm_debug_python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
spec=json.loads((p/'tools/specs/exe4_description_v1.json').read_text())
draft=json.loads((p/'translations/chip_descriptions_korean_draft.json').read_text(encoding='utf-8'))
def machine(data):
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
 u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,data);u.mem_map(0x03000000,0x8000);return u
def select(u,s,chip_id):
 u.mem_write(0x03007e00,b'\xaa'*64+(0x03001001).to_bytes(4,'little')+b'\xaa'*64)
 for r,v in [(UC_ARM_REG_CPSR,0x1f3),(UC_ARM_REG_R0,chip_id),(UC_ARM_REG_SP,0x03007e40),(UC_ARM_REG_R5,0x5555),(UC_ARM_REG_R10,0x12345678)]:u.reg_write(r,v)
 u.emu_start((0x08000000+s['selector_start'])|1,0x03001000,count=100)
 if u.reg_read(UC_ARM_REG_PC)!=0x03001000 or u.reg_read(UC_ARM_REG_SP)!=0x03007e44 or u.reg_read(UC_ARM_REG_R5)!=0x5555 or u.reg_read(UC_ARM_REG_R10)!=0x12345678:raise AssertionError('selector ABI/return failure')
 if bytes(u.mem_read(0x03007e00,64))!=b'\xaa'*64 or bytes(u.mem_read(0x03007e44,64))!=b'\xaa'*64:raise AssertionError('selector stack canary')
 return u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
def spans(d):
 offsets=[int.from_bytes(d[i:i+2],'little') for i in range(0,int.from_bytes(d[:2],'little'),2)]
 valid=sorted(set(x for x in offsets if x!=65535));ends={v:valid[i+1] if i+1<len(valid) else len(d) for i,v in enumerate(valid)}
 return [None if x==65535 else d[x:ends[x]] for x in offsets]
class Descriptions(unittest.TestCase):
 def test_514_selector_inputs_both_revisions(self):
  for key,s in spec['profiles'].items():
   base=(p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba').read_bytes()
   target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
   data=target.read_bytes();m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
   u,native=machine(data),machine(base)
   for chip_id in list(range(512))+[0x3784,0xffff]:
    old_root,old_id=select(native,s,chip_id);root,idx=select(u,s,chip_id)
    self.assertEqual(idx,old_id)
    self.assertEqual(root,0x08000000+m['extension']['descriptions']['archive_offset'] if old_root==s['source_pointer'] else old_root)
 def test_all_256_scripts_controls_and_exact_wording(self):
  table={}
  for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
   code,sep,ch=line.partition('=')
   if sep and len(ch)==1:table.setdefault(ch,bytes.fromhex(code))
  def encode(text):return b''.join(b'\xe8' if c=='\n' else b'\xf9\xfc'+(ord(c)-0xac00).to_bytes(2,'little') if 0xac00<=ord(c)<=0xd7a3 else table[c] for c in text)
  for key,s in spec['profiles'].items():
   target=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
   d=target.read_bytes();m=json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))['extension']['descriptions']
   old=spans(d[s['source_archive_offset']:s['source_archive_offset']+s['source_archive_size']])
   new=spans(d[m['archive_offset']:m['archive_offset']+m['archive_size']]);self.assertEqual(len(new),256)
   selected={int(x['id'].split('/')[-1]):x for x in draft['entries']}
   for i in range(256):
    if i in selected:
     x=selected[i];original=encode(x['source']);self.assertEqual(old[i].count(original),1)
     self.assertEqual(new[i],old[i].replace(original,encode(x['text']),1))
    else:self.assertEqual(new[i],old[i])
if __name__=='__main__':unittest.main()
