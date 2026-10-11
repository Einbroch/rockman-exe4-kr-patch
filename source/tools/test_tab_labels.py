"""The ROCKMAN folder-tab captions in the final ROMs hold exactly their Hangul.

Written apart from tools/tab_labels.py: the caption tiles are decoded fresh and
the ink colour must equal the Galmuri7 text drawn again here; every tile of the
shared UI set outside the caption tiles is byte-identical to the source.
"""
import json,sys,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'tools'))
from analyze_project import PROFILES,sha
spec=json.loads((p/'tools/specs/exe4_tab_labels_v1.json').read_text(encoding='utf-8'))
FONT=Path('D:/Games/Kor Patch/CLude/폰트/Galmuri-v2.24.29/Galmuri7.bdf')

def raster(text,left):
    out=set();pen=left
    for c in text:
        block=next(b for b in FONT.read_text(encoding='ascii').split('STARTCHAR ')[1:] if '\nENCODING %d\n'%ord(c) in b)
        lines=block.splitlines();w,h,xo,yo=[int(v) for v in next(x for x in lines if x.startswith('BBX ')).split()[1:]]
        dw=int(next(x for x in lines if x.startswith('DWIDTH ')).split()[1])
        for y,r in enumerate(lines[lines.index('BITMAP')+1:][:h]):
            bits=bin(int(r,16))[2:].zfill(len(r)*4)
            out|={(pen+xo+x,y-h-yo) for x in range(w) if bits[x]=='1'}
        pen+=dw
    top=min(y for _,y in out);return {(x,y-top+spec['top']) for x,y in out}

class TabLabels(unittest.TestCase):
    def test_captions_and_untouched_neighbours(self):
        for key in PROFILES:
            src=next(f.read_bytes() for f in p.parents[1].glob('*.gba') if sha(f.read_bytes())==PROFILES[key]['sha256'])
            rom=(p/'poc/output'/f'{key}_opening_menu_chip_folder_library_menu_descriptions_story_korean_development.gba').read_bytes()
            base=spec['profiles'][key]['tile0'];caption=set()
            for tab in spec['tabs']:
                ink=set()
                for c,t in enumerate(tab['tiles']):
                    caption.add(t)
                    for i in range(64):
                        b=rom[base+t*32+i//2]
                        if (b>>4 if i%2 else b&15)==spec['ink_colour']:ink.add((c*8+i%8,i//8))
                self.assertEqual(ink,raster(tab['text'],tab.get('left',spec['left'])),(key,tab['text']))
            for t in range(0,0x2B40//32+1):
                if t not in caption:self.assertEqual(rom[base+t*32:base+t*32+32],src[base+t*32:base+t*32+32],(key,t))

if __name__=='__main__':unittest.main(verbosity=2)
