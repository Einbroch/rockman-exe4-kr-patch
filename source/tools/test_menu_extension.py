"""ARMv4T fixture executes the actual revision-bound native tile renderer."""
import argparse,json,sys,unittest,tempfile
from pathlib import Path
from analyze_project import sha,PROFILES,check_dependencies
from menu_extension import font_ink,extend,pack,prepare
from extended_dialogue import assemble_verified
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);ap.add_argument('--font',type=Path,required=True)
args=ap.parse_args();p=Path(__file__).resolve().parents[1];check_dependencies(p)
specs=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))
if sha(args.font.read_bytes())!=specs['font_sha256']:raise ValueError('font identity drift')
ink=font_ink(args.font);rs={sha(f.read_bytes()):f.read_bytes() for f in args.rom_dir.glob('*.gba')}

class MenuExtension(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.fixtures=[]
  for key,profile in PROFILES.items():
   r=rs[profile['sha256']];spec=specs['profiles'][key];blob,patches,meta=extend(r,spec,b'',ink)
   u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
   u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,r+blob)
   u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x8000)
   u.mem_write(0x03005800,r[0x212700:0x213ecc])
   u.mem_write(0x03006750,(meta['machine_code']['address']|1).to_bytes(4,'little'))
   # Only the final DMA helper is stubbed; parser, newline, end-padding and
   # glyph drawing execute the original copied source and new dispatch slot.
   dma,_=assemble_verified('mov pc, lr',0x08000874,{})
   u.mem_write(0x08000874,dma)
   cls.fixtures.append((key,u,spec,meta))
 def reset(self,u,index,style,tint=0,subcommand=252):
  u.mem_write(0x02002000,bytes([249,subcommand])+index.to_bytes(2,'little'))
  u.mem_write(0x02001038,(0x02001200).to_bytes(4,'little'));u.mem_write(0x02001202,bytes([tint]))
  u.mem_write(0x02004000,b'\xaa'*128)
  for reg,value in [(UC_ARM_REG_R0,0x02002000),(UC_ARM_REG_R2,0x02004000),(UC_ARM_REG_R3,1),(UC_ARM_REG_R4,2),(UC_ARM_REG_R5,3),(UC_ARM_REG_R6,style),(UC_ARM_REG_R8,0x12345678),(UC_ARM_REG_R9,7),(UC_ARM_REG_R10,0x02001000),(UC_ARM_REG_R11,0x456789ab),(UC_ARM_REG_R12,0x56789abc),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,0x03001000)]:u.reg_write(reg,value)
  u.reg_write(UC_ARM_REG_CPSR,0x1f3)
 def test_all_available_syllables_both_styles_both_revisions(self):
  for key,u,spec,meta in self.fixtures:
   for style in spec['fonts']:
    for c in sorted(ink):
     self.reset(u,ord(c)-0xac00,style['source_address']);u.emu_start(meta['machine_code']['address']|1,0x03001000,count=200)
     self.assertEqual(bytes(u.mem_read(0x02004000,64)),pack(ink[c],style))
     for reg,value in [(UC_ARM_REG_R0,0x02002004),(UC_ARM_REG_R2,0x02004040),(UC_ARM_REG_R3,1),(UC_ARM_REG_R4,3),(UC_ARM_REG_R5,4),(UC_ARM_REG_R6,style['source_address']),(UC_ARM_REG_R8,0x12345678),(UC_ARM_REG_R9,8),(UC_ARM_REG_R10,0x02001000),(UC_ARM_REG_R11,0x456789ab),(UC_ARM_REG_R12,0x56789abc),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_PC,0x03001000)]:self.assertEqual(u.reg_read(reg),value,(key,c,reg))
     self.assertTrue(u.reg_read(UC_ARM_REG_CPSR)&32);self.assertEqual(bytes(u.mem_read(0x02004040,64)),b'\xaa'*64)
 def test_native_tint_word_addition(self):
  for key,u,spec,meta in self.fixtures:
   for style in spec['fonts']:
    for c in [sorted(ink)[0],sorted(ink)[255],sorted(ink)[-1]]:
     raw=pack(ink[c],style)
     for tint in [0,4,8,12]:
      self.reset(u,ord(c)-0xac00,style['source_address'],tint);u.emu_start(meta['machine_code']['address']|1,0x03001000,count=200)
      bias=(tint//4)*0x44444444
      expected=b''.join(((int.from_bytes(raw[i:i+4],'little')+bias)&0xffffffff).to_bytes(4,'little') for i in range(0,64,4))
      self.assertEqual(bytes(u.mem_read(0x02004000,64)),expected)
 def test_unsupported_codes_and_fonts_stop_before_reading_font(self):
  missing=next(i for i in range(11172) if chr(0xac00+i) not in ink)
  for key,u,spec,meta in self.fixtures:
   for code,font in [(missing,spec['fonts'][0]['source_address']),(11172,spec['fonts'][0]['source_address']),(65535,spec['fonts'][0]['source_address']),(0,spec['fonts'][0]['source_address']+4)]:
    self.reset(u,code,font);u.emu_start(meta['machine_code']['address']|1,0x03001000,count=200)
    self.assertEqual(u.reg_read(UC_ARM_REG_PC),meta['machine_code']['instructions'][-1]['address'])
    self.assertEqual(bytes(u.mem_read(0x02004000,128)),b'\xaa'*128)
    self.assertEqual(u.reg_read(UC_ARM_REG_R0),0x02002000)
 def test_all_native_f9_following_bytes_except_fc_tail_call(self):
  for key,u,spec,meta in self.fixtures:
   for sub in range(256):
    if sub==252:continue
    self.reset(u,0,spec['fonts'][0]['source_address'],subcommand=sub)
    u.emu_start(meta['machine_code']['address']|1,spec['slot']['legacy_handler']&~1,count=30)
    self.assertEqual(u.reg_read(UC_ARM_REG_PC),spec['slot']['legacy_handler']&~1)
    self.assertEqual(u.reg_read(UC_ARM_REG_R0),0x02002000);self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x03007000)
    self.assertEqual(bytes(u.mem_read(0x02004000,128)),b'\xaa'*128)
 def test_missing_translation_glyph_rejects_before_compiler_or_output(self):
  missing=next(chr(i) for i in range(0xac00,0xd7a4) if chr(i) not in ink)
  with tempfile.TemporaryDirectory(prefix='exe4-menu-gate-') as temporary:
   tp=Path(temporary);(tp/'tools/specs').mkdir(parents=True);(tp/'translations').mkdir()
   (tp/'tools/specs/exe4_menu_extension_v1.json').write_text(json.dumps({'font_sha256':sha(args.font.read_bytes())}),encoding='utf-8')
   (tp/'translations/menu_korean.json').write_text(json.dumps({'schema':1,'state':'needs_review','entries':[{'id':'synthetic-missing-glyph','text':missing}]}),encoding='utf-8')
   with self.assertRaisesRegex(ValueError,'menu font missing'):
    prepare(tp,'blue_moon',b'',args.font,tp/'unused_plugins',tp/'output',tp/'unused_index')
   self.assertFalse((tp/'output').exists())
 def test_copied_dispatch_parser_newline_padding_and_control_byte_arguments(self):
  c=next(c for c in sorted(ink) if (ord(c)-0xac00)&255 in (0xe5,0xe8,0xff))
  stream=b'\xf9\xfc\0\0\xe8\xf9\xfc'+(ord(c)-0xac00).to_bytes(2,'little')+b'\xe5'
  for key,u,spec,meta in self.fixtures:
   for style in spec['fonts']:
    self.reset(u,0,style['source_address']);u.mem_write(0x02002000,stream)
    u.mem_write(0x02004000,b'\xaa'*704)
    u.reg_write(UC_ARM_REG_R4,5);u.reg_write(UC_ARM_REG_R5,2);u.reg_write(UC_ARM_REG_R7,0)
    u.emu_start(0x0300677d,0x03001000,count=2500)
    blank=bytes([style['background']*17])*64
    expected=pack(ink['가'],style)+blank*4+pack(ink[c],style)+blank*4
    self.assertEqual(bytes(u.mem_read(0x02004000,640)),expected)
    self.assertEqual(bytes(u.mem_read(0x02004280,64)),b'\xaa'*64)
    self.assertEqual(u.reg_read(UC_ARM_REG_R0),2)
    self.assertEqual(u.reg_read(UC_ARM_REG_R2),640)
    self.assertEqual(u.reg_read(UC_ARM_REG_R6),style['source_address'])
    self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x03007000);self.assertTrue(u.reg_read(UC_ARM_REG_CPSR)&32)
 def test_dynamic_folder_transfer_and_width_scan_use_encoded_name_buffer(self):
  dialogue=json.loads((p/'tools/specs/exe4_dialogue_extension_v1.json').read_text(encoding='utf-8'))['profiles']
  for key in PROFILES:
   path=p/'poc/output'/f'{key}_opening_menu_korean_development.gba';rom=path.read_bytes();m=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
   self.assertEqual(sha(rom),m['output_sha256']);self.assertEqual(m['source_sha256'],PROFILES[key]['sha256'])
   part=next(x for x in m['extension']['menu']['archives'] if x['name']=='raw menu archive 5')
   u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
   u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,rom)
   u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x8000)
   # Native F9 root and folder selection execute the actual product. Only
   # its 64-byte copy helper is stubbed with a CPU byte-copy fixture.
   copy,_=assemble_verified('push {r3, lr}\nloop:\nldrb r3, [r0]\nstrb r3, [r1]\nadds r0, #1\nadds r1, #1\nsubs r2, #1\nbne loop\npop {r3, pc}',0x08000970,{})
   u.mem_write(0x08000970,copy)
   for entry in [0,1]:
    u.mem_write(0x02001000,bytes(0x100));u.mem_write(0x02002000,bytes([249,0,entry,4]))
    for reg,val in [(UC_ARM_REG_R4,0x02002000),(UC_ARM_REG_R5,0x02001000),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,0x03001000)]:u.reg_write(reg,val)
    u.reg_write(UC_ARM_REG_CPSR,0x1f3)
    u.emu_start(m['extension']['machine_code'][0]['address']|1,0x03001000,count=1000)
    buf=u.reg_read(UC_ARM_REG_R4);off=part['offset']+int.from_bytes(rom[part['offset']+entry*2:part['offset']+entry*2+2],'little')
    self.assertEqual(bytes(u.mem_read(buf,64)),rom[off:off+64])
    expected=b'\xf9\xfc'+(ord('폴')-0xac00).to_bytes(2,'little')+b'\xf9\xfc'+(ord('더')-0xac00).to_bytes(2,'little')+bytes([entry+2,229])
    self.assertEqual(bytes(u.mem_read(buf,len(expected))),expected)
    self.assertEqual(int.from_bytes(u.mem_read(0x02001044,4),'little'),0x02002004)
    self.assertEqual(bytes(u.mem_read(0x02001005,1)),b'\x01')
    self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x03007000);self.assertTrue(u.reg_read(UC_ARM_REG_CPSR)&32)
    u.reg_write(UC_ARM_REG_R4,0x02002000);u.reg_write(UC_ARM_REG_LR,0x03001000)
    u.emu_start(m['extension']['machine_code'][1]['address']|1,0x03001000,count=200)
    self.assertEqual(u.reg_read(UC_ARM_REG_R4),buf)
    self.assertEqual(int.from_bytes(u.mem_read(0x02001048,4),'little'),0x02002004)
    self.assertEqual(u.reg_read(UC_ARM_REG_SP),0x03007000);self.assertTrue(u.reg_read(UC_ARM_REG_CPSR)&32)

if __name__=='__main__':unittest.main(argv=[sys.argv[0]])
