"""Decode the PET label art from the final ROMs and check it against the wording.

Written apart from tools/pet_labels.py: the map and tiles are decoded fresh, the
Hangul is rasterised again from the BDF, and each row's colour must hold exactly
that text and nothing of the katakana.
"""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'tools'))
from analyze_project import PROFILES,sha,check_dependencies
check_dependencies(p)
spec=json.loads((p/'tools/specs/exe4_pet_labels_v1.json').read_text(encoding='utf-8'))
wording=json.loads((p/'translations/pet_labels_korean.json').read_text(encoding='utf-8'))['entries']
FONT=Path('D:/Games/Kor Patch/CLude/폰트/Galmuri-v2.24.29/Galmuri9.bdf')

def source(key):
    return next(f.read_bytes() for f in p.parents[1].glob('*.gba') if sha(f.read_bytes())==PROFILES[key]['sha256'])

def product(key):
    path=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
    r=path.read_bytes();assert sha(r)==json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))['output_sha256'];return r

def picture(rom,prof):
    px={}
    for cell in range(640):
        e=int.from_bytes(rom[prof['map_offset']+cell*2:prof['map_offset']+cell*2+2],'little');t=(e&1023)-spec['tile_first']
        if not 0<=t<spec['tile_count']:continue
        for i in range(64):
            b=rom[prof['tiles_offset']+t*32+i//2]
            px[(cell%32*8+i%8,cell//32*8+i//8)]=b>>4 if i%2 else b&15
    return px

def raster(text):
    glyph={}
    for block in FONT.read_text(encoding='ascii').split('STARTCHAR ')[1:]:
        lines=block.splitlines();cp=int(next(x for x in lines if x.startswith('ENCODING ')).split()[1])
        if chr(cp) not in text:continue
        bbx=[int(v) for v in next(x for x in lines if x.startswith('BBX ')).split()[1:]]
        dw=int(next(x for x in lines if x.startswith('DWIDTH ')).split()[1]);bits=lines[lines.index('BITMAP')+1:][:bbx[1]]
        glyph[chr(cp)]=(dw,bbx,[bin(int(r,16))[2:].zfill(len(r)*4) for r in bits])
    out=set();pen=0
    for c in text:
        dw,(w,h,xo,yo),rows=glyph[c]
        for y,r in enumerate(rows):
            for x in range(w):
                if r[x]=='1':out.add((pen+xo+x,y-h-yo))
        pen+=dw
    lx=min(a for a,_ in out);ty=min(b for _,b in out)
    return {(a-lx,b-ty) for a,b in out}

class PetLabels(unittest.TestCase):
    def test_each_row_colour_holds_exactly_its_hangul(self):
        for key in PROFILES:
            prof=spec['profiles'][key];old=picture(source(key),prof);new=picture(product(key),prof)
            for x in wording:
                colour=spec['label_colour_base']+x['row']
                after={q for q,v in new.items() if v==colour}
                ax=min(a for a,_ in after);ay=min(b for _,b in after)
                self.assertEqual({(a-ax,b-ay) for a,b in after},raster(x['text']),(key,x['text']))
                # Ink and shadow stay on the label's dark box, centred within a pixel.
                box=spec['box_colours'][0]
                for a,b in after|{(a+1,b+1) for a,b in after}:
                    self.assertIn(old.get((a,b)),{box,colour}|set(spec['shadow_colours']),(key,x['text'],a,b))
                rows=[r for r in range(ay-6,ay+16) if sum(old.get((c,r))==box for c in range(ax,ax+40))>=20]
                run=[r for r in rows if ay-3<=r<=ay+12]
                bottom=max(b for _,b in after)+1
                self.assertLessEqual(abs((ay-min(run))-(max(run)-bottom)),2,(key,x['text']))
    def test_cells_outside_the_label_region_are_untouched(self):
        (c0,c1),(r0,r1)=spec['region']['columns'],spec['region']['rows']
        for key in PROFILES:
            prof=spec['profiles'][key];a=source(key);b=product(key);m=prof['map_offset']
            # The map is re-tiled by content, so an outside cell may point at a
            # different tile index; its flip/palette bits and pixels may not change.
            for cell in range(640):
                if c0<=cell%32<c1 and r0<=cell//32<r1:continue
                self.assertEqual(int.from_bytes(a[m+cell*2:m+cell*2+2],'little')&~1023,int.from_bytes(b[m+cell*2:m+cell*2+2],'little')&~1023,(key,cell))
            old=picture(a,prof);new=picture(b,prof)
            outside=[q for q in old if not (c0*8<=q[0]<c1*8 and r0*8<=q[1]<r1*8)]
            self.assertTrue(all(old[q]==new[q] for q in outside),key)

if __name__=='__main__':unittest.main(verbosity=2)
