"""EXE4 revision-bound survey, binary round trip and protected source inventory.

TextPet indexes describe a finite lower bound, not all in-game consumers.
No output ROM is constructed by this analysis command.
"""
import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from verify_tpi_index import parse_tpi, lz77_decompress

PROFILES = {
    "blue_moon": {"sha256": "f976a84ef226e47d4a65695052da09b415867b01586dd74bbb1c289a6f607b63", "code": "B4BJ", "revision": 0, "index": "exe4bm-v10.tpi"},
    "red_sun": {"sha256": "1904692bc383fc2cb7e1d81e1c80bf2d8c616c0d1b1d396c689f71b49a2e3188", "code": "B4WJ", "revision": 1, "index": "exe4rs-v11.tpi"},
}
def sha(b):
    return hashlib.sha256(b).hexdigest()

def check_dependencies(project,font=None):
    deps=json.loads((project/'analysis/dependencies.json').read_text(encoding='utf-8-sig'))
    if deps['schema']!=1:raise ValueError('dependency schema changed')
    for entry in deps['files']:
        if sha((project/entry['path']).read_bytes())!=entry['sha256']:
            raise ValueError('dependency drift '+entry['path'])
    if font is not None and sha(font.read_bytes())!=deps['font']['sha256']:
        raise ValueError('font candidate identity changed')

def payload(rom, row):
    off, size = row['offset'], row['size']
    if size is None or off + size > len(rom):
        raise ValueError('missing size or out-of-range archive')
    if row['compressed']:
        data, consumed = lz77_decompress(rom, off)
        if consumed != size:
            raise ValueError('compressed length mismatch')
        return data
    if row['size_header']:
        raise ValueError('size-header mode not adopted for EXE4')
    return rom[off:off+size]

SCRIPT = re.compile(r'^script\s+(\d+)\s+(\S+)\s*\{', re.M)
LITERAL = re.compile(r'"""\r?\n(.*?)\r?\n[\t ]*"""|"((?:[^"\\]|\\.)*)"', re.S)
def scripts(text):
    matches = list(SCRIPT.finditer(text))
    for i, m in enumerate(matches):
        block = text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]
        literals = []
        for s in LITERAL.finditer(block):
            if s.group(1) is not None:
                value = '\n'.join(line[1:] if line.startswith('\t') else line for line in s.group(1).splitlines())
            else:
                value = s.group(2)
            literals.append(value)
        yield int(m.group(1)), m.group(2), literals, block

def run_textpet(project, args, log):
    exe = project/'external/TextPet-v1.0.0/TextPet.exe'
    command = [str(exe), 'load-plugins', str(project/'external/textpet-plugins'), 'game', 'exe4'] + [str(a) for a in args]
    result = subprocess.run(command, capture_output=True)
    (project/'analysis'/log).write_bytes(result.stdout + result.stderr)
    # TextPet sometimes exits zero on errors; artifacts are verified below.
    if result.returncode or b'FATAL:' in result.stdout+result.stderr:
        raise ValueError('TextPet failed; inspect '+log)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom-dir', type=Path, required=True)
    ap.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    p = args.project.resolve()
    check_dependencies(p)
    reports, populations = {}, {}
    inputs = {}
    for rom_path in args.rom_dir.glob('*.gba'):
        rom = rom_path.read_bytes()
        key = next((k for k,v in PROFILES.items() if sha(rom)==v['sha256']), None)
        if key:
            inputs[key] = (rom_path, rom)
    if set(inputs) != set(PROFILES):
        raise ValueError('both exact supported source hashes are required')
    for key, profile in PROFILES.items():
        rom_path, rom = inputs[key]
        rom_sha = sha(rom)
        if len(rom)!=8388608 or rom[0xAC:0xB0].decode('ascii')!=profile['code'] or rom[0xBC]!=profile['revision']:
            raise ValueError('header/profile mismatch '+key)
        index = p/'external/textpet-indexes'/profile['index']
        rows = parse_tpi(index)
        if len(rows)!=793:
            raise ValueError('index denominator changed')
        direct, flagged, no_claim = 0, 0, []
        for i,row in enumerate(rows):
            claims = [x for x in row['pointers'] if x]
            if not claims: no_claim.append(i)
            for at in claims:
                if at<0 or at+4>len(rom): raise ValueError('pointer location out of range')
                value = int.from_bytes(rom[at:at+4], 'little')
                expected = 0x08000000+row['offset']
                if value == expected: direct += 1
                elif row['compressed'] and value == expected|0x80000000: flagged += 1
                else: raise ValueError('pointer mismatch '+key+' '+hex(at))
        tpl_dir = p/'analysis'/f'{key}_tpl'
        bin_dir = p/'analysis'/f'{key}_roundtrip_bin'
        run_textpet(p, ['load-file-index',index,'read-text-archives',rom_path,'-f','rom','write-text-archives',str(tpl_dir)+'/', '-f','tpl'],f'{key}_extract.log')
        run_textpet(p, ['read-text-archives',tpl_dir,'-f','tpl','write-text-archives',str(bin_dir)+'/', '-f','bin'],f'{key}_roundtrip.log')
        if len(list(tpl_dir.glob('*.tpl')))!=len(rows) or len(list(bin_dir.glob('*.msg')))!=len(rows):
            raise ValueError('artifact count mismatch')
        entries, per_archive, mismatches = [], [], []
        declared_slots=0
        langs, glyphs = Counter(), Counter()
        for i,row in enumerate(rows):
            name = f"{row['offset']:06X}"
            data = payload(rom,row)
            data_sha = sha(data)
            back = (bin_dir/(name+'.msg')).read_bytes()
            if data != back:
                mismatches.append({'archive':name,'source_size':len(data),'rebuilt_size':len(back),'first_diff':next((j for j,(a,b) in enumerate(zip(data,back)) if a!=b),min(len(data),len(back)))})
            text = (tpl_dir/(name+'.tpl')).read_text(encoding='utf-8-sig')
            parsed = list(scripts(text))
            declared=int(re.search(r'^@size\s+(\d+)',text,re.M).group(1))
            declared_slots+=declared
            if len(data)<declared*2:raise ValueError('script table exceeds payload')
            table=[int.from_bytes(data[j:j+2],'little') for j in range(0,declared*2,2)]
            present_ids={s[0] for s in parsed}
            missing=[n for n in range(declared) if n not in present_ids]
            for num,lang,literals,block in parsed:
                langs[lang]+=1
                for literal in literals: glyphs.update(literal)
                entries.append({'id':f'archive/{i:03d}/script/{num}', 'archive_index':i,'archive_offset':row['offset'],'script_id':num,'language':lang,'source_literals':literals,'source_tpl_block_sha256':sha(block.encode()),'source_payload_sha256':data_sha,'source_rom_sha256':rom_sha})
            per_archive.append({'index':i,'offset':row['offset'],'size':row['size'],'compressed':row['compressed'],'pointers':row['pointers'],'payload_sha256':sha(data),'payload_bytes':len(data),'scripts_present':len(parsed),'text_scripts':sum(bool(x[2]) for x in parsed),'declared_script_slots':declared,'script_offsets_u16le':table,'unprinted_slots':missing,'slot_status':'offsets preserved; aliases/empty/continuation consumer classification pending'})
        populations[key] = [payload(rom,row) for row in rows]
        report = {'profile':key,'source':{'name':rom_path.name,'sha256':sha(rom),'bytes':len(rom),'title':rom[0xA0:0xAC].decode('ascii'),'game_code':profile['code'],'revision':profile['revision']},'index_sha256':sha(index.read_bytes()),'volume_status':'lower bound: indexed population; unindexed text and consumer coverage open','archives':len(rows),'compressed_archives':sum(r['compressed'] for r in rows),'direct_pointers':direct,'flagged_compressed_pointers':flagged,'archives_without_pointer_claim':no_claim,'scripts_present':len(entries),'text_scripts':sum(bool(e['source_literals']) for e in entries),'string_literals':sum(len(e['source_literals']) for e in entries),'literal_characters':sum(sum(map(len,e['source_literals'])) for e in entries),'script_languages':dict(langs),'roundtrip_equivalence':'decompressed payload byte identity, full indexed population','roundtrip_passed':len(rows)-len(mismatches),'roundtrip_mismatches':mismatches,'archives_detail':per_archive}
        reports[key] = report
        report['declared_script_slots']=declared_slots
        report['unprinted_script_slots']=declared_slots-len(entries)
        report['workload_note']='printed TPL scripts and literals are source units, not deduplicated translation workload; all unprinted slots remain in the protected archive table'
        (p/'analysis'/f'{key}_analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        (p/'analysis'/f'{key}_source_entries.jsonl').write_text('\n'.join(json.dumps(e,ensure_ascii=False) for e in entries)+'\n',encoding='utf-8')
        print(key, 'archives',len(rows),'scripts',len(entries),'roundtrip',report['roundtrip_passed'],'/',len(rows),'mismatches',mismatches[:4])
    same = [i for i,(a,b) in enumerate(zip(populations['blue_moon'],populations['red_sun'])) if a==b]
    difference = [i for i in range(793) if i not in same]
    (p/'analysis/version_comparison.json').write_text(json.dumps({'compared':793,'identical':len(same),'different':len(difference),'different_archive_indexes':difference,'translation_reuse':'only byte-identical entries; story/version differences must remain distinct'},indent=2),encoding='utf-8')
    print('version payloads identical',len(same),'different',len(difference))
    if any(r['roundtrip_mismatches'] for r in reports.values()):
        raise SystemExit('ROUNDTRIP FAILED: do not build translated ROM')
if __name__=='__main__':
    main()
