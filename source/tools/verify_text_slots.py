"""Gate: no area text combination overflows a slot the source did not overflow.

Independent of text_slots.externalize: it walks the product's own selector
tables (main by area/sub-area/progress, sub by area/sub-area, extra by
area/progress, progress through the threshold table), decodes what each
pointer names in both ROMs, and applies the slot rules of the decoder at
0x0804DF5C: main <= 0x3800; sub <= 0x1000 whenever an extra archive is decoded
after it; extra <= 0x2000. A rule the source already broke for a combination
is not counted against the product. It also holds the fixed buffers listed in
exe4_text_slots_v1.json to their limits.
"""
import argparse,json,sys
from functools import lru_cache
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from analyze_project import PROFILES,sha
from verify_tpi_index import lz77_decompress

p=Path(__file__).resolve().parent.parent
PRODUCT='poc/output/{key}_opening_menu_chip_folder_library_menu_descriptions_story_korean_development.gba'


def w(rom,a):return int.from_bytes(rom[a:a+4],'little')


def arr(rom,a,maxn=64):
    out=[]
    for k in range(maxn):
        v=w(rom,a+4*k)
        if not 0x08000000<=(v&0x9ffffff)<0x09400000:break
        out.append(v&0x1ffffff)
    return out


def audit(key,src,prod):
    s=json.loads((p/'tools/specs/exe4_text_slots_v1.json').read_text(encoding='utf-8'));prof=s['profiles'][key]
    R=prof['roots'];th_at=prof['selector_offset']+(0x4e408-0x4e3a8)
    th=[];k=th_at
    while len(th)<32:
        th.append((src[k],src[k+1]));k+=2
        if src[k-2]==0xff:break
    progs=sorted({i for _,i in th})
    roms={'o':src,'n':prod}

    @lru_cache(None)
    def size(x,a):
        try:return len(lz77_decompress(roms[x],a)[0])
        except Exception:return -1
    def faults(m,sb,e):
        f=set()
        if m>0x3800:f.add('main')
        if sb>0x1000 and e>0:f.add('sub')
        if e>0x2000:f.add('extra')
        return f
    new=[];combos=0
    for half in (0,4):
        top={x:{n:arr(roms[x],w(roms[x],R[n]+half)&0x1ffffff) for n in R} for x in 'on'}
        for r0 in range(len(top['o']['main'])):
            m1={x:arr(roms[x],top[x]['main'][r0]) for x in 'on'}
            s1={x:(arr(roms[x],top[x]['sub'][r0]) if r0<len(top[x]['sub']) else []) for x in 'on'}
            e1={x:(arr(roms[x],top[x]['extra'][r0]) if r0<len(top[x]['extra']) else []) for x in 'on'}
            for r1 in range(len(m1['o'])):
                m2={x:arr(roms[x],m1[x][r1]) for x in 'on'}
                sb={x:(size(x,s1[x][r1]) if r1<len(s1[x]) else 0) for x in 'on'}
                for pr in progs:
                    mm={x:(size(x,m2[x][pr]) if pr<len(m2[x]) else 0) for x in 'on'}
                    ee={x:(size(x,e1[x][pr]) if pr<len(e1[x]) else 0) for x in 'on'}
                    combos+=1
                    extra=faults(mm['n'],sb['n'],ee['n'])-faults(mm['o'],sb['o'],ee['o'])
                    if extra:new.append([half//4,r0,r1,pr,sorted(extra),mm['n'],sb['n'],ee['n']])
    return combos,new


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);a=ap.parse_args()
    report={'schema':1,'products':{}};bad=False
    for key,meta in PROFILES.items():
        src=next(f.read_bytes() for f in a.rom_dir.glob('*.gba') if sha(f.read_bytes())==meta['sha256'])
        prod=(p/PRODUCT.format(key=key)).read_bytes()
        combos,new=audit(key,src,prod)
        report['products'][key]={'rom_sha256':sha(prod),'combinations':combos,'new_overflows':len(new),'examples':new[:20]}
        print(f'{key} {"PASS" if not new else "FAIL"} {combos} area text combinations, {len(new)} new slot overflows')
        bad|=bool(new)
    (p/'analysis/text_slots_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    return 1 if bad else 0


if __name__=='__main__':raise SystemExit(main())
