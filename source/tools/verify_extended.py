"""Verify exact extension artifacts, packed BDF pixels and runtime attribution."""
import argparse,json
from pathlib import Path
from analyze_project import PROFILES,sha,check_dependencies
from extended_dialogue import assemble_verified,HANGUL_COUNT,LEGACY_INDICES
from verify_tpi_index import lz77_decompress

def read_ink(font):
    result={}
    for block in font.read_text(encoding='utf-8').split('STARTCHAR ')[1:]:
        lines=block.splitlines();cp=int(next(x.split()[1] for x in lines if x.startswith('ENCODING ')))
        if not 0xac00<=cp<=0xd7a3:continue
        w,h,xoff,yoff=map(int,next(x for x in lines if x.startswith('BBX ')).split()[1:])
        start=lines.index('BITMAP')+1;rows=[bytes.fromhex(x) for x in lines[start:start+h]]
        result[cp]={(x+xoff,y+11-h-yoff) for y,row in enumerate(rows) for x in range(w) if row[x//8]&(0x80>>(x%8))}
    if set(result)!=set(range(0xac00,0xd7a4)):raise ValueError('font repertoire missing')
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True);ap.add_argument('--font',type=Path,required=True);ap.add_argument('--font-probe',action='store_true');ap.add_argument('--menu-font',type=Path);ap.add_argument('--chip-folder',action='store_true');ap.add_argument('--library-chips',action='store_true')
    args=ap.parse_args();p=Path(__file__).resolve().parents[1];check_dependencies(p,args.font)
    if args.chip_folder and not args.menu_font:raise ValueError('chip verification requires menu font')
    if args.library_chips and not args.chip_folder:raise ValueError('library verification requires chip folder')
    spec=json.loads((p/'tools/specs/exe4_dialogue_extension_v1.json').read_text(encoding='utf-8'))['profiles']
    sources={sha(f.read_bytes()):f.read_bytes() for f in args.rom_dir.glob('*.gba')}
    inks=read_ink(args.font)
    report={'schema':1,'claim':'normal dialogue extension development only; no release','status':'bench_verified','open_conditions':['unindexed and external F9 FC collision population','tile-menu font representation/decoder','other width/count/bypass consumers','whole-game translation and QA','device QA'],'profiles':[]}
    if args.menu_font:
        report['claim']='normal dialogue and two observed shared tile styles; bounded source-bound menu draft; no release'
        report['open_conditions'][1]='remaining menu/battle/name-entry font, decoder and buffer consumers'
    if args.chip_folder:report['claim']='normal/menu plus private folder clone of ten draft chip names and 24 active syllables; bounded development, no release'
    if args.library_chips:report['claim']='normal/menu/folder plus private seven-row library clones for 294 draft chip names and 56 active per-cell slots; bounded development, no release'
    for key,profile in PROFILES.items():
        source=sources[profile['sha256']];s=spec[key]
        suffix='opening_menu_chip_folder_library_korean_development' if args.library_chips else 'opening_menu_chip_folder_korean_development' if args.chip_folder else 'opening_menu_korean_development' if args.menu_font else 'hangul_boundary_visibility' if args.font_probe else 'opening_korean_extended_development'
        path=p/'poc/output'/f'{key}_{suffix}.gba'
        data=path.read_bytes();m=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'));ext=m['extension']
        if not m.get('extended_codec_byte_roundtrip') or not m.get('wording_reextracted_exactly'):raise ValueError('missing extended archive roundtrip gate')
        if m['source_sha256']!=sha(source) or m['output_sha256']!=sha(data) or m['policy']!='development/PoC; NON-DISTRIBUTION' or len(data)!=0x1000000:raise ValueError('identity/policy drift')
        allowed=bytearray(len(source));intervals=[]
        for w in m['expected_writes']:
            a,b=w['offset'],w['offset']+w['size'];intervals.append((a,b))
            if sha(data[a:b])!=w['final_sha256']:raise ValueError('final write drift')
            if a<len(source):
                if b>len(source) or sha(source[a:b])!=w['expected_sha256']:raise ValueError('expected write drift')
                allowed[a:b]=b'\1'*(b-a)
        intervals.sort()
        if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):raise ValueError('overlapping writes')
        if any(x!=y and not allowed[i] for i,(x,y) in enumerate(zip(source,data))):raise ValueError('unexplained source diff')
        decoded,consumed=lz77_decompress(data,len(source))
        if sha(decoded)!=m['archive_payload_sha256']:raise ValueError('compressed opening drift')
        parts=ext['layout'];last=len(source)+consumed
        for part in parts:
            a,b=part['offset'],part['offset']+part['size']
            if a<last or a%4 or sha(data[a:b])!=part['sha256'] or any(x!=255 for x in data[last:a]):raise ValueError('append layout drift')
            last=b
        if any(x!=255 for x in data[last:]):raise ValueError('unexplained append tail')
        native_font=s['font_literal']['expected_address']&0x1ffffff
        native_width=s['advance_literal']['expected_address']&0x1ffffff
        font_at,width_at=ext['normal_font_offset'],ext['advance_offset']
        if LEGACY_INDICES!=ext['legacy_index_view'] or HANGUL_COUNT!=ext['hangul_syllables']:raise ValueError('font repertoire drift')
        if data[native_font:native_font+442*96]!=source[native_font:native_font+442*96] or data[native_width:native_width+442*4]!=source[native_width:native_width+442*4]:raise ValueError('native provider changed')
        if data[font_at:font_at+442*96]!=source[native_font:native_font+442*96] or data[width_at:width_at+442*4]!=source[native_width:native_width+442*4]:raise ValueError('legacy compatibility view drift')
        if data[native_font+441*96:native_font+441*96+0x100]!=source[native_font+441*96:native_font+441*96+0x100]:raise ValueError('protected source palette changed')
        for index in range(HANGUL_COUNT):
            record=data[font_at+(442+index)*96:font_at+(443+index)*96]
            pixels={(i*2%16,i*2//16):b&15 for i,b in enumerate(record)}
            pixels.update({((i*2+1)%16,(i*2+1)//16):b>>4 for i,b in enumerate(record)})
            ink=inks[0xac00+index];shadow={(x+1,y+1) for x,y in ink if x+1<12 and y+1<12}-ink
            if not ink or any(not 0<=x<12 or not 0<=y<12 for x,y in ink):raise ValueError('source glyph clipping')
            if {pos for pos,v in pixels.items() if v==3}!=ink or {pos for pos,v in pixels.items() if v==2}!=shadow or set(pixels.values())-{1,2,3}:raise ValueError('packed BDF pixel mismatch '+hex(0xac00+index))
            if int.from_bytes(data[width_at+(442+index)*4:width_at+(443+index)*4],'little')!=12:raise ValueError('Hangul advance mismatch')
        for name,at in [('font_literal',font_at),('advance_literal',width_at)]:
            off=s[name]['offset']
            if int.from_bytes(data[off:off+4],'little')!=0x08000000+at:raise ValueError('IWRAM provider literal drift')
        for name,code in zip(['normal_f9_slot','width_f9_slot'],ext['machine_code']):
            off=s[name]['offset'];base=code['address'];a=base-0x08000000
            if int.from_bytes(data[off:off+4],'little')!=base|1:raise ValueError('handler pointer drift')
            instructions='\n'.join(i['mnemonic']+' '+i['operands'] for i in code['instructions'])
            rebuilt,_=assemble_verified(instructions,base,code['literal_values'])
            if data[a:a+len(rebuilt)]!=rebuilt:raise ValueError('final placed machine-code mismatch')
        item={'profile':key,'rom_sha256':sha(data),'static_status':'PASS','hangul_glyphs_pixel_verified':11172,'legacy_indices_pixel_bytes_preserved':442,'source_font_width_palette_preserved':True,'source_offset_diff_bytes':sum(x!=y for x,y in zip(source,data)),'runtime_status':'pending'}
        if args.menu_font:
            from verify_menu import check
            item.update(check(p,key,source,data,m,args.menu_font,static_only=args.chip_folder))
            if args.chip_folder:
                from verify_chip import check as check_chip
                item.update(check_chip(p,key,source,data,m,args.menu_font,static_only=args.library_chips))
                if args.library_chips:
                    from verify_library import check as check_library
                    item.update(check_library(p,key,source,data,m,args.menu_font))
            report['profiles'].append(item)
            print(key,'PASS normal 11172 and tile 4363 x two styles;',item['runtime_status'])
            continue
        run='boundary_final' if args.font_probe else 'extended_v2_final'
        root=p/'analysis/runtime'/f'{key}_{run}';receipt=root/'result.json'
        if receipt.exists():
            r=json.loads(receipt.read_text(encoding='utf-8'))
            for name,digest in r['artifacts'].items():
                if sha((root/name).read_bytes())!=digest:raise ValueError('runtime evidence drift')
            if r['rom_sha256']!=sha(data) or len(r['loaded_rom_guards'])<7 or r['audio_enabled']:raise ValueError('runtime attribution drift')
            if r['complete'] and r['return_code']==0 and r['steps_captured']==r['steps_expected']==(9 if args.font_probe else 70):
                reads=json.loads((root/'fontread_final.json').read_text(encoding='utf-8'))
                expected={ord(c)-0xac00 for c in m['mapping']}
                if {e['index'] for e in reads['records']}!=expected:raise ValueError('actual extended glyph selection differs from opening demand')
                if {e['pc'] for e in reads['sites']}!={'0x03006A92','0x03006A94'}:raise ValueError('unexpected extended provider consumer')
                item.update(runtime_status='completed diagnostic; visual QA separate',runtime_receipt_sha256=sha(receipt.read_bytes()),actual_glyphs_read=len(expected),font_read_sites=reads['sites'])
            else:item['runtime_status']='PARTIAL_RUNTIME'
        report['profiles'].append(item)
        print(key,item['static_status'],'11172 glyphs pixel verified; Japanese source preserved;',item['runtime_status'])
    name='library_verification.json' if args.library_chips else 'chip_verification.json' if args.chip_folder else 'menu_verification.json' if args.menu_font else 'boundary_verification.json' if args.font_probe else 'extended_verification.json'
    if args.menu_font and all(x['runtime_status'].startswith('completed') for x in report['profiles']):report['status']='bench_and_bounded_runtime_verified'
    (p/'analysis'/name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
