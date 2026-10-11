"""Check actual RAM, VRAM, all nine visible OBJ cells, and screenshot ink masks."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from analyze_project import sha
from test_menu_descriptions import expected,load,draft
p=Path(__file__).resolve().parents[1]
def proof(f):return {'path':f.relative_to(p).as_posix(),'sha256':sha(f.read_bytes())}
def receipt(root,digest):
 r=json.loads((root/'result.json').read_text(encoding='utf-8'))
 if not r['complete'] or r['return_code'] or r['rom_sha256']!=digest or r['steps_expected']!=r['steps_captured']:raise ValueError('menu runtime identity/completion')
 for name,h in r['artifacts'].items():
  if sha((root/name).read_bytes())!=h:raise ValueError('menu runtime artifact drift '+name)
 return r
texts={int(x['id'].split('/')[-1]):x['text'] for x in draft['entries']}
vp=p/'analysis/menu_descriptions_verification.json';v=json.loads(vp.read_text(encoding='utf-8'))
report={'schema':1,'status':'PASS bounded runtime, actual nine-cell display and direct visual inspection',
 'scope':'folder ten natural descriptions; library three registered IDs, unknown entries/category hiding, folder reentry',
 'verification':proof(vp),'reviewer':'Claude direct native-resolution contact sheets of both revisions, 2026-09-20','profiles':{},'sheets':[],
 'not_claimed':['third menu pointer consumer','all catalog descriptions translated','all ten library entries naturally selected','whole-game/device QA','independent language/font review'],
 'rejected_predecessor':'analysis/rejected/menu_descriptions_10cell/REJECTION.json'}
folder=[(4,1),(8,4),(11,15),(14,29),(18,48),(22,49),(24,91),(27,107),(31,117),(32,149)]
library=[(39,1),(42,4),(43,15),(45,15)]
for key in ['blue_moon','red_sun']:
 data,m=load(key);digest=sha(data)
 if digest!=v['profiles'][key]['rom_sha256']:raise ValueError('menu verified product mismatch')
 root=p/'analysis/runtime'/f'{key}_menu_descriptions_final_02';r=receipt(root,digest)
 cold=p/'analysis/runtime'/f'{key}_menu_descriptions_cold_02';cr=receipt(cold,digest)
 if cr['state_origin'] is not None or Path(r['state_origin'])!=cold/'result.json' or r['state_sha256']!=sha((cold/'checkpoint.mss').read_bytes()) or r['steps_captured']!=51:raise ValueError('menu cold lineage mismatch')
 checks=[]
 for consumer,cases in [('folder',folder+[(51,1)]),('library',library)]:
  at=0x11600 if consumer=='folder' else 0x11800;xorigin=18 if consumer=='folder' else 10;first=(at-0x10000)//32
  for step,chip in cases:
   paths={kind:root/f'step_{step:03d}{suffix}' for kind,suffix in [('RAM','_gbaExtWorkRam.bin'),('VRAM','_gbaVideoRam.bin'),('OAM','_gbaSpriteRam.bin'),('palette','_gbaPaletteRam.bin'),('screenshot','.png')]}
   want=expected(data,m,texts[chip]);ram=paths['RAM'].read_bytes()[0x17800:0x17f80];vr=paths['VRAM'].read_bytes()[at:at+1920]
   if want!=ram or ram!=vr:raise ValueError(f'menu exact tile data mismatch {key} {step}')
   if any(len(line)>9 for line in texts[chip].splitlines()):raise ValueError('visible ninth-column limit exceeded')
   oam=paths['OAM'].read_bytes();im=Image.open(paths['screenshot']).convert('RGB');colors={};inkmask=[]
   for row in range(3):
    # The native buffer has ten columns but only nine are drawn. Its unused
    # tenth cell must be blank, not a hidden character credited as rendered.
    if want[(row*10+9)*64:(row*10+10)*64]!=bytes([0x11])*64:raise ValueError('hidden tenth glyph')
    for col in range(9):
     tile=first+row*20+col*2;found=[]
     for i in range(128):
      a0=int.from_bytes(oam[i*8:i*8+2],'little');a1=int.from_bytes(oam[i*8+2:i*8+4],'little');a2=int.from_bytes(oam[i*8+4:i*8+6],'little')
      if a2&1023==tile and a1&511==xorigin+col*8 and a0&255==96+row*16 and a0&0x300==0:found.append((a0,a1,a2))
     if len(found)!=1:raise ValueError('missing/duplicate actual description OBJ cell')
     a0,a1,a2=found[0]
     if a0&0xfc00!=0x8000 or a1&0xfe00 or a2>>12!=2:raise ValueError('description OBJ geometry/palette drift')
     glyph=want[(row*10+col)*64:(row*10+col+1)*64]
     for y in range(16):
      for x in range(8):
       index=(glyph[y*4+x//2]>>(4*(x%2)))&15
       if index not in [1,3,4]:raise ValueError('unclassified description pixel palette')
       rgb=im.getpixel((xorigin+col*8+x,96+row*16+y));colors.setdefault(index,set()).add(rgb);inkmask.append((index==3,rgb))
   # Mesen applies a GBA color profile, so compare exact binary ink geometry
   # against the screenshot instead of assuming an uncorrected RGB555 mapping.
   if any(len(c)!=1 for c in colors.values()) or next(iter(colors[3]))==next(iter(colors[1])):raise ValueError('screenshot differs from expected ink geometry')
   ink=next(iter(colors[3]))
   if any(isink!=(rgb==ink) for isink,rgb in inkmask):raise ValueError('clipped or residual description ink')
   checks.append({'consumer':consumer,'step':step,'source_id':chip,'text':texts[chip],
    'exact_tile_bytes':1920,'visible_OBJ_cells':27,'screenshot_pixels_checked':3456,'tenth_column_blank':True,
    **{kind:proof(f) for kind,f in paths.items()}})
 hidden=[]
 for step in [40,41,44]:
  f=root/f'step_{step:03d}.png';im=Image.open(f).convert('RGB');pixels=set(im.crop((10,96,82,144)).getdata())
  if len(pixels)!=1:raise ValueError('unregistered entry retains visible description ink')
  hidden.append({'step':step,'screenshot':proof(f),'description_rectangle_uniform':True})
 for label,cases in [('folder',folder),('library',[(39,1),(40,None),(41,None),(42,4),(43,15),(44,None),(45,15),(51,1)])]:
  sheet=Image.new('RGB',(960,180*((len(cases)+3)//4)),'white');draw=ImageDraw.Draw(sheet)
  for i,(step,chip) in enumerate(cases):
   x=i%4*240;y=i//4*180;draw.text((x+3,y+3),key+' step '+str(step)+' ID '+str(chip),fill='black');sheet.paste(Image.open(root/f'step_{step:03d}.png'),(x,y+20))
  f=p/'analysis/visual_qa'/f'{key}_menu_descriptions_{label}_02.png';sheet.save(f);report['sheets'].append(proof(f))
 report['profiles'][key]={'rom_sha256':digest,'natural_folder_ids':sorted(texts),'natural_library_ids':[1,4,15],
  'checks':checks,'hidden':hidden,'lineage':[proof(cold/'result.json'),proof(root/'result.json')]}
report['tool_sha256']=sha(Path(__file__).read_bytes())
(p/'analysis/MENU_DESCRIPTIONS_RUNTIME_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS both versions: ten folder + three library descriptions, 30 snapshots x 3456 visible pixels, 27 OBJ cells each')
