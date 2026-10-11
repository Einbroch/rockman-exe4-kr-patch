"""Actual native consumer fixtures and pre-compiler unsupported-selection gate."""
import argparse,json,sys,tempfile,unittest
from pathlib import Path
from analyze_project import PROFILES,sha,check_dependencies
from consumer_contracts import check_selection
from menu_extension import prepare
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);a=ap.parse_args()
p=Path(__file__).resolve().parents[1];check_dependencies(p)
rs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
contracts=json.loads((p/'tools/specs/exe4_consumer_contracts_v1.json').read_text(encoding='utf-8'))
styles=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))['profiles']

def fixture(key):
 r=rs[PROFILES[key]['sha256']];u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
 u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,r)
 u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x8000)
 u.mem_write(0x03005800,r[0x212700:0x213ecc])
 u.reg_write(UC_ARM_REG_SP,0x03007000);u.reg_write(UC_ARM_REG_LR,0x03001000);u.reg_write(UC_ARM_REG_CPSR,0x1f3)
 return r,u

class ConsumerContracts(unittest.TestCase):
 def test_native_folder_chip_parser_terminates_on_new_lead_in_both_revisions(self):
  for key in PROFILES:
   # Native single-byte rendering, then two representative unsupported F9FC
   # streams. Executes the whole original function, without helper stubs.
   for stream,indexes in [(b'\x11\x30\x2b\x3a\xe5',[0x11,0x30,0x2b,0x3a]),(b'\xf9\xfc\0\0\xe5',[]),(b'\x11\xf9\xfc\0\0\xe5',[0x11])]:
    r,u=fixture(key);u.mem_write(0x02002000,b'\x02\0'+stream);u.mem_write(0x02004000,b'\xaa'*48)
    for reg,value in [(UC_ARM_REG_R0,0x02002000),(UC_ARM_REG_R1,0),(UC_ARM_REG_R2,0x02004000),(UC_ARM_REG_R3,0x02004010),(UC_ARM_REG_R6,0x200)]:u.reg_write(reg,value)
    u.emu_start(contracts['profiles'][key]['unsupported_chip_parser_entry']|1,0x03001000,count=300)
    upper=[0x200+2*i for i in indexes]+[0x200]*(8-len(indexes))
    lower=[0x201+2*i for i in indexes]+[0x200]*(8-len(indexes))
    self.assertEqual(bytes(u.mem_read(0x02004000,32)),b''.join(x.to_bytes(2,'little') for x in upper+lower))
    self.assertEqual(bytes(u.mem_read(0x02004020,16)),b'\xaa'*16)
    self.assertEqual(u.reg_read(UC_ARM_REG_R0),0x02002002+len(indexes))
    self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x03007000);self.assertTrue(u.reg_read(UC_ARM_REG_CPSR)&32)
 def test_native_name_is_three_byte_indexes_not_an_extended_stream(self):
  for key in PROFILES:
   for style in styles[key]['fonts']:
    for value,indexes in [(0xaa030201,[1,2,3]),(0xbb030201,[1,2,3]),(0x0000fcf9,[249,252,0])]:
     r,u=fixture(key)
     u.mem_write(0x02001044,(0x02001200).to_bytes(4,'little'));u.mem_write(0x02001270,value.to_bytes(4,'little'))
     u.mem_write(0x02001038,(0x02001400).to_bytes(4,'little'));u.mem_write(0x02001402,b'\0')
     u.mem_write(0x02002000,b'\xf9\xe5');u.mem_write(0x02004000,b'\xaa'*256)
     for reg,v in [(UC_ARM_REG_R0,0x02002000),(UC_ARM_REG_R2,0x02004000),(UC_ARM_REG_R3,1),(UC_ARM_REG_R4,5),(UC_ARM_REG_R5,5),(UC_ARM_REG_R6,style['source_address']),(UC_ARM_REG_R10,0x02001000)]:u.reg_write(reg,v)
     u.emu_start(0x0300692d,0x03001000,count=600)
     expected=b''.join(r[(style['source_address']&0x1ffffff)+i*64:(style['source_address']&0x1ffffff)+(i+1)*64] for i in indexes)
     self.assertEqual(bytes(u.mem_read(0x02004000,192)),expected)
     self.assertEqual(bytes(u.mem_read(0x020040c0,64)),b'\xaa'*64)
     self.assertEqual(u.reg_read(UC_ARM_REG_R0),0x02002001);self.assertEqual(u.reg_read(UC_ARM_REG_R2),0x020040c0)
     self.assertEqual(u.reg_read(UC_ARM_REG_R4),8);self.assertEqual(u.reg_read(UC_ARM_REG_R5),8)
     self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x03007000);self.assertTrue(u.reg_read(UC_ARM_REG_CPSR)&32)
 def test_unclassified_chip_translation_rejected_before_compiler_or_output(self):
  for key in PROFILES:
   with tempfile.TemporaryDirectory(prefix='exe4-consumer-gate-') as temp:
    tp=Path(temp)
    for rel in ['tools/specs/exe4_menu_extension_v1.json','tools/specs/exe4_consumer_contracts_v1.json','external/textpet-plugins/exe4-utf8.tbl']:
     target=tp/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((p/rel).read_bytes())
    (tp/'translations').mkdir()
    (tp/'translations/menu_korean.json').write_text(json.dumps({'schema':1,'state':'needs_review','entries':[{'id':'archive/041/script/1','source':'キャノン','text':'캐논'}]}),encoding='utf-8')
    with self.assertRaisesRegex(ValueError,'unclassified short-text consumer'):
     prepare(tp,key,rs[PROFILES[key]['sha256']],a.font,tp/'absent-compiler',tp/'output',tp/'absent-index')
    self.assertFalse((tp/'output').exists())
 def test_byte_capacity_is_separate_from_cell_count(self):
  # A controlled future 17-cell producer with the real native 64-byte copy
  # ceiling. 17 Hangul cells occupy 69 encoded bytes including end marker.
  c={'schema':1,'profiles':{'blue_moon':{'source_sha256':sha(b''),'anchors':[]}},'supported_entries':[{'id':'controlled-capacity','source':'_'*17,'max_cells':17,'max_encoded_bytes':64}]}
  w={'entries':[{'id':'controlled-capacity','source':'_'*17,'text':'가'*17}]}
  with self.assertRaisesRegex(ValueError,'encoded buffer budget exceeded'):check_selection(c,'blue_moon',b'',w,{'_':b'\0'})
  w['entries'][0]['text']='가'*15
  self.assertTrue(check_selection(c,'blue_moon',b'',w,{'_':b'\0'}))

if __name__=='__main__':unittest.main(argv=[sys.argv[0]])
