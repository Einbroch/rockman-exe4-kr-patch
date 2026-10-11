"""Execute the folder chooser, its row renderer and the cache on the final ROMs.

Each chip name is drawn by the real chooser into a tilemap with VRAM mapped, so
a Hangul cell is checked twice: its tile number belongs to a cache slot, and
the VRAM at that tile holds that syllable's glyph record. Native cells keep the
native tile rule, and the native glyphs the folder still loads are the ones its
names use.
"""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'external/arm_debug_python'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
from unicorn.arm_const import *
from analyze_project import PROFILES,sha,check_dependencies
check_dependencies(p)
s=json.loads((p/'tools/specs/exe4_chip_folder_v2.json').read_text(encoding='utf-8'))
wording=json.loads((p/'translations/chip_folder_korean.json').read_text(encoding='utf-8'))
# Chip id = script for archive41, 256 + script for archive42 (0x0802F068).
selected={int(x['id'].split('/')[-1])+(256 if x['id'].startswith('archive/042/') else 0):x['text'] for x in wording['entries']}
UNUSED={256+i for i in range(35,45)}  # archive42 ミテイ placeholders
IDS=range(311)
KEEP={c for a,b in s['native_keep'] for c in range(a,b)}
def product(key):
 path=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
 r=path.read_bytes();m=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
 assert sha(r)==m['output_sha256'];return r,m['extension']['chip_folder']
def fixture(r):
 u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(UC_CPU_ARM_TI925T)
 u.mem_map(0x08000000,0x1000000);u.mem_write(0x08000000,r)
 u.mem_map(0x02000000,0x40000);u.mem_map(0x03000000,0x8000);u.mem_map(0x06000000,0x18000)
 u.reg_write(UC_ARM_REG_CPSR,0x1f3)
 return u
def reset(u,meta):
 u.mem_write(meta['cache_ram'],b'\0'*4+b'\xff\xff'*meta['slots'])
 u.mem_write(meta['stamp_ram'],b'\0'*4*meta['slots'])
def call(u,entry,id,row=2):
 regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7]
 values=[0x02004000,id,0x4444,0x5555,0x6666,row]
 for reg,value in zip(regs,values):u.reg_write(reg,value)
 u.mem_write(0x02004000,b'\xaa'*320)
 u.reg_write(UC_ARM_REG_SP,0x03007000);u.reg_write(UC_ARM_REG_LR,0x03001001)
 u.emu_start(entry|1,0x03001000,count=40000)
 if u.reg_read(UC_ARM_REG_PC)!=0x03001000:raise AssertionError('chooser did not return')
 if [u.reg_read(x) for x in regs]!=values:raise AssertionError('native callee state drift')
 if u.reg_read(UC_ARM_REG_SP)!=0x03007000:raise AssertionError('stack drift')
 return bytes(u.mem_read(0x02004000,320))
def cells(r,meta,id):
 archive,id=(meta['archive42_offset'],id-256) if id>=256 else (meta['archive_offset'],id)
 at=archive+int.from_bytes(r[archive+id*2:archive+id*2+2],'little');out=[]
 while r[at]<0xe5 or r[at:at+2]==b'\xf9\xfc':
  if r[at:at+2]==b'\xf9\xfc':out.append(('k',int.from_bytes(r[at+2:at+4],'little')));at+=4
  else:out.append(('n',r[at]));at+=1
 return out
def glyph(r,meta,cp):
 o=int.from_bytes(r[meta['ordinal_offset']+cp*2:meta['ordinal_offset']+cp*2+2],'little')
 return r[meta['font_offset']+o*64:meta['font_offset']+o*64+64]
class ChipExtension(unittest.TestCase):
 def test_every_name_draws_its_glyphs_through_the_cache(self):
  for key in PROFILES:
   r,meta=product(key);profile=s['profiles'][key];u=fixture(r);reset(u,meta)
   slot_tiles=set(s['slot_tiles'])
   for id in IDS:
    after=call(u,profile['chooser_entry'],id)
    if id not in selected:continue
    tiles=[]
    for kind,v in cells(r,meta,id):
     row=after[64+2*len(tiles):66+2*len(tiles)];tile=int.from_bytes(row,'little')
     if kind=='k':
      self.assertIn(tile,slot_tiles,(key,id))
      self.assertEqual(bytes(u.mem_read(0x06000000+tile*32,64)),glyph(r,meta,v),(key,id,v))
     else:
      self.assertIn(v,KEEP,(key,id,v));self.assertEqual(tile,512+2*v)
     tiles.append(tile)
    self.assertEqual(len(tiles),len(selected[id]))
    expected=tiles+[512]*(8-len(tiles))+[x+1 for x in tiles]+[512]*(8-len(tiles))
    self.assertEqual(after[64:96],b''.join(x.to_bytes(2,'little') for x in expected),(key,id))
    self.assertEqual(after[:64]+after[96:],b'\xaa'*288)
   # The battle chip-name announcement table is moved on purpose by tools/battle_announce.py.
   announce=json.loads((p/'tools/specs/exe4_battle_announce_v1.json').read_text(encoding='utf-8'))['profiles'][key]
   moved=announce['tables']
   # ...and so is the dialogue name insert's chip-name pair.
   for at in profile['other_archive_claims_preserved']+profile['second_clone']['other_archive_claims_preserved']:
    if any(at in (m,m+4) for m in moved) or at in announce['name_insert']['offsets']+announce['comm_names']['offsets']:continue
    source=next(f.read_bytes() for f in p.parents[1].glob('*.gba') if sha(f.read_bytes())==PROFILES[key]['sha256'])
    self.assertEqual(r[at:at+4],source[at:at+4])
 def test_a_repeated_syllable_reuses_its_slot_and_the_oldest_slot_is_evicted(self):
  for key in PROFILES:
   r,meta=product(key);u=fixture(r);reset(u,meta);n=meta['slots']
   lookup=meta['machine_code'][1]['address']
   def look(cp):
    u.reg_write(UC_ARM_REG_R1,cp);u.reg_write(UC_ARM_REG_SP,0x03007000);u.reg_write(UC_ARM_REG_LR,0x03001000)
    u.emu_start(lookup|1,0x03001000,count=20000);return u.reg_read(UC_ARM_REG_R4)
   cps=[ord(c)-0xac00 for c in meta['characters']]
   first=[look(cp) for cp in cps[:n]]
   self.assertEqual(sorted(first),sorted(s['slot_tiles']))
   self.assertEqual(look(cps[0]),first[0])            # hit refreshes the oldest
   evicted=look(cps[n]);self.assertEqual(evicted,first[1])   # so the second-oldest goes
   self.assertEqual(bytes(u.mem_read(0x06000000+evicted*32,64)),glyph(r,meta,cps[n]))
 def test_every_folder_chip_name_is_translated(self):
  for key in PROFILES:
   r,meta=product(key);untranslated=[]
   for id in IDS:
    if id in UNUSED:continue
    c=cells(r,meta,id)
    if any(k=='n' and v not in KEEP for k,v in c):untranslated.append(id)
   self.assertEqual(untranslated,[],key)
 def test_reset_hook_clears_the_cache_and_enqueues_only_the_kept_font(self):
  for key in PROFILES:
   r,meta=product(key);profile=s['profiles'][key];u=fixture(r)
   u.mem_write(meta['cache_ram'],b'\x55'*(4+2*meta['slots']));u.mem_write(meta['stamp_ram'],b'\x55'*4*meta['slots'])
   for reg,v in [(UC_ARM_REG_R4,0x4444),(UC_ARM_REG_R5,0x5555),(UC_ARM_REG_R6,0x6666),(UC_ARM_REG_R7,0x7777),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,0x03001001)]:u.reg_write(reg,v)
   u.emu_start((0x08000000+profile['upload_patch']['offset'])|1,profile['upload_patch']['continuation']&~1,count=5000)
   self.assertEqual(u.reg_read(UC_ARM_REG_PC),profile['upload_patch']['continuation']&~1)
   self.assertEqual(bytes(u.mem_read(meta['cache_ram'],4+2*meta['slots'])),b'\0'*4+b'\xff\xff'*meta['slots'])
   self.assertEqual(bytes(u.mem_read(meta['stamp_ram'],4*meta['slots'])),b'\0'*4*meta['slots'])
   self.assertEqual(int.from_bytes(u.mem_read(0x0200b134,4),'little'),2)
   nf=profile['native_font_address'];jobs=[(nf+64*a,0x06004000+64*a,64*(b-a)) for a,b in s['native_keep']]
   for i,job in enumerate(jobs):
    desc=bytes(u.mem_read(0x0200d120+i*20,20));self.assertEqual(tuple(int.from_bytes(desc[j:j+4],'little') for j in (0,4,8)),job)
   self.assertEqual([u.reg_read(x) for x in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_SP)],[0x4444,0x5555,0x6666,0x7777,0x03007000])
 def test_link_screen_uploads_reset_the_cache_then_copy_the_whole_font(self):
  for key in PROFILES:
   r,meta=product(key);profile=s['profiles'][key]
   for point in profile['link_upload_patches']:
    u=fixture(r)
    u.mem_write(meta['cache_ram'],b'\x55'*(4+2*meta['slots']));u.mem_write(meta['stamp_ram'],b'\x55'*4*meta['slots'])
    for reg,v in [(UC_ARM_REG_R4,0x4444),(UC_ARM_REG_R5,0x5555),(UC_ARM_REG_R6,0x6666),(UC_ARM_REG_R7,0x7777),(UC_ARM_REG_SP,0x03007000)]:u.reg_write(reg,v)
    u.emu_start((0x08000000+point['offset'])|1,point['copier']&~1,count=5000)
    self.assertEqual(u.reg_read(UC_ARM_REG_PC),point['copier']&~1)
    self.assertEqual(bytes(u.mem_read(meta['cache_ram'],4+2*meta['slots'])),b'\0'*4+b'\xff\xff'*meta['slots'])
    self.assertEqual(bytes(u.mem_read(meta['stamp_ram'],4*meta['slots'])),b'\0'*4*meta['slots'])
    # The copier sees exactly the original call: same font, place and size,
    # and returns to the instruction after the replaced bl.
    self.assertEqual([u.reg_read(x) for x in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_LR)],
                     [profile['native_font_address'],0x06004000,point['font_bytes'],point['continuation']])
    self.assertEqual([u.reg_read(x) for x in (UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_SP)],[0x4444,0x5555,0x6666,0x7777,0x03007000])
 def test_link_screen_none_label_draws_through_the_cache(self):
  wording=json.loads((p/'translations/menu_korean.json').read_text(encoding='utf-8'))
  text=next(x['text'] for x in wording['entries'] if x['id']=='archive/001/script/177')
  for key in PROFILES:
   r,meta=product(key);profile=s['profiles'][key]
   for point in profile['extra_row_parser_patches']:
    entry=0x08000000+point['offset']-0x10
    self.assertEqual(r[entry-0x08000000+1],0xb5)   # push {..., lr}
    u=fixture(r);reset(u,meta)
    for reg,v in [(UC_ARM_REG_R0,0x02004000),(UC_ARM_REG_R1,0x1111),(UC_ARM_REG_R4,0x4444),(UC_ARM_REG_R5,0x5555),(UC_ARM_REG_R6,0x6666),(UC_ARM_REG_R7,1),(UC_ARM_REG_SP,0x03007000),(UC_ARM_REG_LR,0x03001001)]:u.reg_write(reg,v)
    u.mem_write(0x02004000,b'\xaa'*128)
    u.emu_start(entry|1,0x03001000,count=40000)
    self.assertEqual(u.reg_read(UC_ARM_REG_PC),0x03001000)
    self.assertEqual([u.reg_read(x) for x in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_SP)],
                     [0x02004000,0x1111,0x4444,0x5555,0x6666,1,0x03007000])
    row=bytes(u.mem_read(0x02004020,32));top=[int.from_bytes(row[i:i+2],'little') for i in range(0,16,2)]
    for i,ch in enumerate(text):
     self.assertIn(top[i],s['slot_tiles'])
     self.assertEqual(bytes(u.mem_read(0x06000000+top[i]*32,64)),glyph(r,meta,ord(ch)-0xac00),(key,ch))
    self.assertEqual(top[len(text):],[512]*(8-len(text)))
    self.assertEqual(bytes(u.mem_read(0x02004000,32))+bytes(u.mem_read(0x02004040,64)),b'\xaa'*96)
if __name__=='__main__':unittest.main(verbosity=2)
