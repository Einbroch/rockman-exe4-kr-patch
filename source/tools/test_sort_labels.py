"""The folder SORT window in the final ROMs: each translated item's ink equals
the EXE 1 [K] glyphs decoded here independently, and every pixel outside the
translated item areas is unchanged from the source window."""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'tools'))
from analyze_project import PROFILES,sha
spec=json.loads((p/'tools/specs/exe4_sort_labels_v1.json').read_text(encoding='utf-8'))
G=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))['hangul_glyph_source']

def picture(rom,prof):
    w,h=spec['map_cells'];px={}
    for c in range(w*h):
        t=(int.from_bytes(rom[prof['map_offset']+c*2:prof['map_offset']+c*2+2],'little')&1023)-spec['tile_first']
        for i in range(64):
            b=rom[prof['tiles_offset']+t*32+i//2];px[((c%w)*8+i%8,(c//w)*8+i//8)]=b>>4 if i%2 else b&15
    return px

def glyph(k1,ch):
    """Rows as strings: drop row 0 and column 0, then fold one inked repeated row
    (else clear a row-0 stroke top, else fold a blank repeated row)."""
    e=ch.encode('euc_kr');n=(e[0]-0xB0)*94+(e[1]-0xA1);rec=k1[0x80016C+(512+n)*64:0x80016C+(513+n)*64]
    rows=[''.join('1' if ((rec[y*4+x//2]>>(4*(x%2)))&15)==3 else '0' for x in range(8)) for y in range(16)]
    rows=[r[1:]+'0' for r in rows[1:]]+['0'*8]
    if '1' in rows[0]:
        d=next((i for i in range(1,16) if rows[i]==rows[i-1] and '1' in rows[i]),None)
        if d is None and all(rows[1][x]=='1'==rows[2][x] for x in range(8) if rows[0][x]=='1'):rows=['0'*8]+rows[1:]
        else:
            d=d if d is not None else next(i for i in range(1,16) if rows[i]==rows[i-1])
            rows=['0'*8]+rows[:d]+rows[d+1:]
    return {(x,y) for y,r in enumerate(rows) for x,v in enumerate(r) if v=='1'}

class SortLabels(unittest.TestCase):
    def test_items_and_untouched_window(self):
        k1=Path(G['path']).read_bytes();self.assertEqual(sha(k1),G['sha256'])
        for key in PROFILES:
            prof=spec['profiles'][key]
            src=next(f.read_bytes() for f in p.parents[1].glob('*.gba') if sha(f.read_bytes())==PROFILES[key]['sha256'])
            rom=(p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_story_korean_development.gba').read_bytes()
            old=picture(src,prof);new=picture(rom,prof);areas=set()
            for item in spec['items']:
                if item['text']==item['source']:continue
                x0,x1=item['columns'][0]*8,item['columns'][1]*8;y0=item['row']*8
                area={q for q in new if x0<=q[0]<x1 and y0<=q[1]<y0+16};areas|=area
                want=set()
                for k,ch in enumerate(item['text']):
                    if ch!=' ':want|={(x0+8*k+x,y0+y) for x,y in glyph(k1,ch)}
                self.assertEqual({q for q in area if new[q]==spec['ink']},want,(key,item['text']))
            self.assertTrue(all(old[q]==new[q] for q in old if q not in areas),key)

if __name__=='__main__':unittest.main(verbosity=2)
