"""Every chip description in Korean: full clones of archives 54 and 55.

The earlier description stages each translated ten chips (the Custom Screen
clone and the folder/library clone), so the shop, folder and library showed
Japanese for the other chips (user report 2026-10-10). This stage compiles all
scripts of archive 54 (chips 0..255) and 55 (256..) from
translations/chip_descriptions_full_korean.json, appends both archives raw (the
source stores them raw, read in place from ROM) and points every consumer whose
renderer handles F9FC at them:

  Custom Screen 0x0801FD20/24 -> message box 0x0804E2A4 (dialogue font)
  folder edit   0x08106B34/38 -> tile renderer, native style 0x086C6E60
  library       0x08109918/1C -> tile renderer, native style 0x086C6E60
  library P.A   0x08109D08 (55) -> tile renderer, native style 0x086C6E60
The pair at 0x08106E1C/20 has no reader anywhere in the ROM and stays.

The tile renderer stops on a syllable outside its 4,363-syllable set, so every
syllable must be in that set; the window is 9 visible cells by 3 lines.
"""
import copy,json,shutil,subprocess,sys
from pathlib import Path
from analyze_project import PROFILES,sha,scripts,SCRIPT,LITERAL
from verify_tpi_index import parse_tpi

p=Path(__file__).resolve().parents[1]
SPEC=p/'tools/specs/exe4_full_descriptions_v1.json'
ASSET=p/'translations/chip_descriptions_full_korean.json'
BASE='{key}_opening_menu_chip_folder_library_menu_descriptions_v2_korean_development'
OUT='{key}_opening_menu_chip_folder_library_full_descriptions_korean_development'


def compile_archive(key,rows,archive,by_source,root):
    row=rows[archive];name=f"{row['offset']:06X}"
    text=(p/'analysis'/f'{key}_tpl'/f'{name}.tpl').read_text(encoding='utf-8-sig')
    wanted={}
    for si,lang,values,block in scripts(text):
        src=''.join(values)
        if not any(0x3040<=ord(c)<=0x30ff or 0x4e00<=ord(c)<=0x9fff for c in src):continue
        if len(values)!=1 or src not in by_source:raise ValueError(f'archive {archive} script {si} has no Korean description')
        wanted[si]=by_source[src]
    for si,ko in wanted.items():
        lines=ko.split('\n')
        if len(lines)>3 or max(map(len,lines))>9:raise ValueError(f'description over 9 cells x 3 lines: {archive}/{si}')
        matches=list(SCRIPT.finditer(text));m=next(m for m in matches if int(m.group(1))==si)
        end=next((n.start() for n in matches if n.start()>m.start()),len(text))
        block=text[m.end():end];lits=list(LITERAL.finditer(block))
        if len(lits)!=1:raise ValueError('unexpected description controls')
        token='"""\n'+'\n'.join('\t'+line for line in lines)+'\n\t"""'
        new=block[:lits[0].start()]+token+block[lits[0].end():]
        if LITERAL.sub('TEXT',block)!=LITERAL.sub('TEXT',new):raise ValueError('description control mutation')
        text=text[:m.end()]+new+text[end:]
    d=root/str(archive);d.mkdir(parents=True,exist_ok=True)
    tpl,msg,back,again=d/'d.tpl',d/'d.msg',d/'back.tpl',d/'back.msg'
    tpl.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
    common=[str(p/'external/TextPet-v1.0.0/TextPet.exe'),'load-plugins',str(root/'plugins'),'game','exe4']
    for i,(s,f,o,of) in enumerate([(tpl,'tpl',msg,'bin'),(msg,'bin',back,'tpl'),(back,'tpl',again,'bin')]):
        run=subprocess.run(common+['read-text-archives',str(s),'-f',f,'write-text-archives',str(o),'-f',of],capture_output=True,timeout=120)
        (d/f'compile_{i}.log').write_bytes(run.stdout+run.stderr)
        if run.returncode or b'FATAL:' in run.stdout+run.stderr:raise ValueError('description compiler failure')
    data=msg.read_bytes()
    seen={si:vs for si,lang,vs,b in scripts(back.read_text(encoding='utf-8-sig'))}
    if data!=again.read_bytes() or any(seen[si]!=[ko] for si,ko in wanted.items()):raise ValueError('description roundtrip failure')
    return data,len(wanted)


def main():
    spec=json.loads(SPEC.read_text(encoding='utf-8'));asset=json.loads(ASSET.read_text(encoding='utf-8'))
    by_source=asset['by_source']
    syll={c for v in by_source.values() for c in v if 0xac00<=ord(c)<=0xd7a3}
    for key,pr in PROFILES.items():
        s=spec['profiles'][key]
        source=next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes())==pr['sha256'])
        bpath=p/'poc/output'/(BASE.format(key=key)+'.gba');base=bpath.read_bytes()
        bm=json.loads(bpath.with_suffix('.json').read_text(encoding='utf-8'))
        if bm['output_sha256']!=sha(base):raise ValueError('baseline manifest drift')
        missing=syll-set(bm['extension']['menu']['characters'])
        if missing:raise ValueError('description syllables outside the tile set: '+''.join(sorted(missing)))
        rows=parse_tpi(p/'external/textpet-indexes'/pr['index'])
        root=p/'analysis/full_descriptions'/key
        if root.exists():shutil.rmtree(root)
        shutil.copytree(p/'external/textpet-plugins',root/'plugins')
        table=root/'plugins/exe4-utf8.tbl';native=table.read_text(encoding='utf-8-sig')
        table.write_text(native+'\n'+'\n'.join('F9FC'+(ord(c)-0xac00).to_bytes(2,'little').hex().upper()+'='+c for c in sorted(syll))+'\n',encoding='utf-8')
        known={x['offset'] for x in bm['extension']['layout']}
        target=bytearray(base);writes=[];layout=[];counts={}
        for archive in (54,55):
            row=rows[archive]
            if row['compressed']:raise ValueError('description archives are stored raw in the source')
            data,counts[archive]=compile_archive(key,rows,archive,by_source,root)
            target.extend(b'\xff'*((-len(target))%4));at=len(target);target.extend(data)
            layout.append({'name':f'full Korean archive {archive} clone (all chip descriptions)','offset':at,'size':len(data),'sha256':sha(data)})
            for ptr in s['claims'][str(archive)]:
                if ptr not in row['pointers']:raise ValueError('claim is not a source pointer of the archive')
                old=int.from_bytes(base[ptr:ptr+4],'little')
                if old!=int.from_bytes(source[ptr:ptr+4],'little') and (old&0x1ffffff) not in known:raise ValueError(f'claim {ptr:#x} holds an unknown pointer')
                target[ptr:ptr+4]=(0x08000000+at).to_bytes(4,'little')
                writes.append({'offset':ptr,'size':4,'writer':f'chip description archive {archive} pointer -> full Korean clone',
                               'expected_sha256':sha(source[ptr:ptr+4]),'final_sha256':sha(bytes(target[ptr:ptr+4]))})
            for ptr in s['unread'][str(archive)]:
                if base[ptr:ptr+4]!=source[ptr:ptr+4]:raise ValueError('unread description claim changed')
        m=copy.deepcopy(bm);mine={w['offset'] for w in writes}
        m['expected_writes']=[w for w in m['expected_writes'] if w['offset'] not in mine and w['offset']<len(source)]+writes
        m['expected_writes'].append({'offset':len(source),'size':len(target)-len(source),'writer':'inherited payload plus full description clones','final_sha256':sha(bytes(target[len(source):]))})
        covered=bytearray(len(source));ranges=[]
        for w in m['expected_writes']:
            lo=w['offset'];hi=lo+w['size'];ranges.append((lo,hi))
            if sha(bytes(target[lo:hi]))!=w['final_sha256']:raise ValueError('final writer drift')
            if lo<len(source):
                if sha(source[lo:hi])!=w['expected_sha256']:raise ValueError('source preimage drift')
                covered[lo:hi]=b'\1'*(hi-lo)
        ranges.sort()
        if any(a[1]>b[0] for a,b in zip(ranges,ranges[1:])) or any(x!=y and not covered[i] for i,(x,y) in enumerate(zip(source,target))):raise ValueError('overlap or unexplained source difference')
        m['extension']['layout']+=layout
        m['extension']['full_descriptions']={'spec_sha256':sha(SPEC.read_bytes()),'asset_sha256':sha(ASSET.read_bytes()),'translated_scripts':counts,
                                             'claims':s['claims'],'unread_claims_kept':s['unread'],'layout':layout,'syllables':len(syll)}
        m['baseline_sha256']=sha(base);m['output_sha256']=sha(bytes(target))
        out=p/'poc/output'/(OUT.format(key=key)+'.gba')
        out.write_bytes(bytes(target));out.with_suffix('.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
        print(key,m['output_sha256'],'descriptions',counts)
    return 0


if __name__=='__main__':raise SystemExit(main())
