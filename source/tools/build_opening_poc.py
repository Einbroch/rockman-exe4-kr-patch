"""Non-distribution EXE4 opening visibility/end-to-end PoC.

The primary development mode appends Hangul and preserves Japanese glyphs.
Legacy temporary code reassignment is retained for historical reproduction.
Both modes are non-distribution development, never release builds.
All source changes are planned before applying to the immutable source.
"""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from analyze_project import PROFILES, sha, payload, SCRIPT, LITERAL, scripts, check_dependencies
from verify_tpi_index import parse_tpi, lz77_decompress

FONT_BASE_BLUE = 0x695004
WIDTH_BASE_BLUE = 0x51588
RECORD_BYTES=96
GLYPHS=441

def bdf_glyphs(path, wanted):
    found={}
    for block in path.read_text(encoding='utf-8').split('STARTCHAR ')[1:]:
        lines=block.splitlines()
        cp=int(next(x.split()[1] for x in lines if x.startswith('ENCODING ')))
        ch=chr(cp)
        if ch not in wanted:continue
        width,height,xoff,yoff=map(int,next(x for x in lines if x.startswith('BBX ')).split()[1:])
        start=lines.index('BITMAP')+1
        bits=[int(x,16) for x in lines[start:start+height]]
        top=11-height-yoff
        if width>11 or height>11 or xoff<0 or top<0 or top+height>11:
            raise ValueError('PoC glyph requires another placement '+repr(ch))
        ink={(x+xoff,y+top) for y,row in enumerate(bits) for x in range(width) if row & (1 << (((width+7)//8)*8-1-x))}
        if not ink:raise ValueError('empty glyph '+ch)
        grid=[[1]*16 for _ in range(12)]
        for x,y in ink:
            if x+1<12 and y+1<12:grid[y+1][x+1]=2
        for x,y in ink:grid[y][x]=3
        found[ch]=bytes(grid[y][x]|(grid[y][x+1]<<4) for y in range(12) for x in range(0,16,2))
    if set(found)!=wanted:raise ValueError('missing glyphs '+repr(wanted-set(found)))
    return found

def lz_literal(data):
    if len(data)>0xffffff:raise ValueError('LZ length overflow')
    out=bytearray(b'\x10'+len(data).to_bytes(3,'little'))
    for i in range(0,len(data),8):out.append(0);out.extend(data[i:i+8])
    return bytes(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rom-dir',type=Path,required=True)
    ap.add_argument('--font',type=Path,required=True)
    ap.add_argument('--selection',choices=['centered','opening'],default='opening')
    ap.add_argument('--encoding',choices=['temporary','extended'],default='extended')
    ap.add_argument('--font-probe',action='store_true')
    ap.add_argument('--menu-font',type=Path,help='optional Galmuri7 menu development extension')
    ap.add_argument('--chip-folder',action='store_true',help='private folder chip-name clone and demand VRAM cache; development only')
    ap.add_argument('--library-chips',action='store_true',help='294 draft names in the private seven-row library consumer; development only')
    ap.add_argument('--battle-caption',action='store_true',help='private Custom Screen chip caption; development only')
    ap.add_argument('--battle-active',action='store_true',help='private in-battle queued chip name; development only')
    ap.add_argument('--chip-descriptions',action='store_true',help='ten private Custom Screen descriptions; development only')
    ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args()
    if args.battle_caption and not args.library_chips:raise ValueError('battle caption requires library clones')
    if args.battle_active and not args.battle_caption:raise ValueError('active battle name requires caption baseline')
    if args.chip_descriptions and not args.battle_active:raise ValueError('descriptions require active-name baseline')
    if args.chip_folder and not args.menu_font:raise ValueError('chip folder extension requires menu font')
    if args.library_chips and (not args.menu_font or not args.chip_folder):raise ValueError('library chip extension requires menu font and chip folder extension')
    extended=args.encoding=='extended'
    if args.menu_font and (not extended or args.selection!='opening' or args.font_probe):raise ValueError('menu extension requires normal full opening extension')
    if extended and args.selection!='opening' and not args.font_probe:raise ValueError('extension currently adopts full opening or explicit font probe only')
    if args.font_probe and (not extended or args.selection!='centered'):raise ValueError('font probe requires extended encoding and centered selection')
    p=args.project.resolve()
    check_dependencies(p,args.font)
    wording_path=p/'poc/font_probe_wording.json' if args.font_probe else p/'translations/opening_korean.json'
    wording=json.loads(wording_path.read_text(encoding='utf-8'))
    if wording['state']!='needs_review' or wording['schema']!=1:raise ValueError('input policy/schema changed')
    selected_ids=[0] if args.selection=='centered' else list(range(26))
    selected=[s for i in selected_ids for s in wording['scripts'][str(i)]]
    wanted={c for s in selected for c in s if '\uac00'<=c<='\ud7a3'}
    glyphs=bdf_glyphs(args.font,{chr(i) for i in range(0xac00,0xd7a4)} if extended else wanted)
    temporary_slots=list(range(256,GLYPHS)) if args.selection=='centered' else list(range(228,GLYPHS))+list(range(144,228))
    mapping={c:442+ord(c)-0xac00 if extended else temporary_slots[i] for i,c in enumerate(sorted(wanted))}
    if not extended and max(mapping.values())>=GLYPHS:raise ValueError('temporary glyph slots overflow')
    for key,profile in PROFILES.items():
        rom_path=next((f for f in args.rom_dir.glob('*.gba') if sha(f.read_bytes())==profile['sha256']),None)
        if rom_path is None:raise ValueError('source not found '+key)
        rom=rom_path.read_bytes()
        report=json.loads((p/'analysis'/f'{key}_analysis.json').read_text(encoding='utf-8'))
        if report['roundtrip_passed']!=793 or report['roundtrip_mismatches'] or report['source']['sha256']!=sha(rom):raise ValueError('full source roundtrip gate failed')
        rows=parse_tpi(p/'external/textpet-indexes'/profile['index'])
        row=rows[442]
        name=f"{row['offset']:06X}"
        original=(p/'analysis'/f'{key}_tpl'/(name+'.tpl')).read_text(encoding='utf-8-sig')
        parsed=list(scripts(original))
        if len(parsed)!=26 or [x[0] for x in parsed]!=list(range(26)):raise ValueError('opening source boundary changed')
        source_entries=[json.loads(x) for x in (p/'analysis'/f'{key}_source_entries.jsonl').read_text(encoding='utf-8').splitlines()]
        for script_id in selected_ids:
            protected=next(e for e in source_entries if e['id']==f'archive/442/script/{script_id}')
            if protected['source_literals']!=parsed[script_id][2] or protected['source_payload_sha256']!=sha(payload(rom,row)):raise ValueError('protected baseline mismatch')
        # Only the selected script is edited; all event/control text is retained.
        matches=list(SCRIPT.finditer(original))
        blocks=[]
        for script_id in selected_ids:
            block=original[matches[script_id].end():matches[script_id+1].start() if script_id+1<len(matches) else len(original)]
            literals=list(LITERAL.finditer(block))
            translations=wording['scripts'][str(script_id)]
            if len(literals)!=len(translations):raise ValueError('literal count mismatch')
            for m,translation in reversed(list(zip(literals,translations))):
                if '\n' in translation:
                    token='"""\r\n\t'+translation.replace('\n','\r\n\t')+'\r\n\t"""'
                else:token='"'+translation+'"'
                block=block[:m.start()]+token+block[m.end():]
            blocks.append(block)
        # Centering uses a count of 11-pixel source cells; account for 12-pixel
        # Hangul advances. Each explicit centered page remains within 240x160.
        page_widths=[max(sum(12 if c in wanted else (8 if c==' ' else 11) for c in line) for line in s.split('\n')) for s in selected]
        if any(w>220 for w in page_widths) or any(len(s.split('\n'))>3 for s in selected):raise ValueError('PoC page exceeds observed screen budget')
        if args.selection=='opening' and any(w>180 for w in page_widths[5:]):raise ValueError('ordinary opening dialogue exceeds 180-pixel observed budget')
        widths=iter((w+10)//11 for w in page_widths[:5])
        blocks[0]=re.sub(r'(positionTextCenter\s+width = )\d+',lambda m:m.group(1)+str(next(widths)),blocks[0])
        # Compile only selected wording: the temporary font table deliberately
        # reassigns Japanese characters and cannot encode unselected prose.
        translated='@archive '+name+'\n@size '+str(len(selected_ids))+'\n\n'+''.join(f'script {i} mmbn4 {{'+block for i,block in zip(selected_ids,blocks))
        root=p/'poc'/(key+'_library_chips' if args.library_chips else key+'_chips' if args.chip_folder else key+'_menu' if args.menu_font else key+'_boundary' if args.font_probe else key+'_extended' if extended else key if args.selection=='centered' else key+'_opening')
        tpldir=root/'tpl';tpldir.mkdir(parents=True,exist_ok=True)
        # TextPet loads every file, including .orig; pristine files stay outside.
        plugins=root/'plugins';shutil.copytree(p/'external/textpet-plugins',plugins,dirs_exist_ok=True)
        table=p/'external/textpet-plugins/exe4-utf8.tbl'
        table_lines=table.read_text(encoding='utf-8-sig').splitlines()
        assigned={(f'E4{index-228:02X}' if index>=228 else f'{index:02X}'):ch for ch,index in mapping.items()}
        if extended:
            replaced='\n'.join(table_lines)+'\n'+''.join('F9FC'+(ord(c)-0xac00).to_bytes(2,'little').hex().upper()+'='+c+'\n' for c in sorted(wanted))
        else:replaced='\n'.join(code+'='+assigned[code] if code in assigned else line for line in table_lines for code in [line.partition('=')[0]])+'\n'
        # Authored comma punctuation uses the original Japanese comma glyph.
        replaced='\n'.join(line.partition('=')[0]+'=,' if line.partition('=')[2]=='、' else line for line in replaced.splitlines())+'\n'
        (plugins/'exe4-utf8.tbl').write_text(replaced,encoding='utf-8')
        menu_prepared=None
        if args.menu_font:
            from menu_extension import prepare
            menu_prepared=prepare(p,key,rom,args.menu_font,plugins,root,p/'external/textpet-indexes'/profile['index'])
        (tpldir/(name+'.tpl')).write_bytes(translated.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
        exe=p/'external/TextPet-v1.0.0/TextPet.exe'
        bindir=root/'compiled'
        bindir.mkdir(parents=True,exist_ok=True)
        compiled=bindir/(name+'.msg')
        run=subprocess.run([str(exe),'load-plugins',str(plugins),'game','exe4','read-text-archives',str(tpldir),'-f','tpl','write-text-archives',str(compiled), '-f','bin'],capture_output=True)
        (root/'compile.log').write_bytes(run.stdout+run.stderr)
        compiled=bindir/(name+'.msg')
        if run.returncode or b'FATAL:' in run.stdout+run.stderr or not compiled.exists():raise ValueError('compile failure')
        selected_archive=compiled.read_bytes()
        if extended:
            reexport=root/'roundtrip_tpl';rebuilt=root/'roundtrip_bin'
            reexport.mkdir(exist_ok=True);rebuilt.mkdir(exist_ok=True)
            common=[str(exe),'load-plugins',str(plugins),'game','exe4']
            stages=[['read-text-archives',str(compiled),'-f','bin','write-text-archives',str(reexport/(name+'.tpl')), '-f','tpl'],['read-text-archives',str(reexport/(name+'.tpl')),'-f','tpl','write-text-archives',str(rebuilt/(name+'.msg')), '-f','bin']]
            for number,stage in enumerate(stages):
                cycle=subprocess.run(common+stage,capture_output=True)
                (root/f'roundtrip_{number}.log').write_bytes(cycle.stdout+cycle.stderr)
                if cycle.returncode or b'FATAL:' in cycle.stdout+cycle.stderr:raise ValueError('extended codec TextPet roundtrip failure')
            if (rebuilt/(name+'.msg')).read_bytes()!=selected_archive:raise ValueError('extended encoded archive is not byte-reversible')
            observed={i:values for i,language,values,block in scripts((reexport/(name+'.tpl')).read_text(encoding='utf-8-sig'))}
            if observed!={i:wording['scripts'][str(i)] for i in selected_ids}:raise ValueError('extended re-extraction differs from exact authored wording')
        original_data=payload(rom,row)
        if args.selection=='centered':
            new_script=selected_archive[int.from_bytes(selected_archive[:2],'little'):]
            first=int.from_bytes(original_data[:2],'little')
            second=int.from_bytes(original_data[2:4],'little')
            delta=len(new_script)-(second-first)
            new_table=bytearray(original_data[:first])
            for table_at in range(2,first,2):
                old=int.from_bytes(original_data[table_at:table_at+2],'little')
                if old<second:raise ValueError('unexpected shared opening pointer')
                new_table[table_at:table_at+2]=(old+delta).to_bytes(2,'little')
            data=bytes(new_table)+new_script+original_data[second:]
        else:data=selected_archive
        # Verify encoded wording independently of TextPet, including line breaks.
        tablemap={}
        for line in replaced.splitlines():
            code,sep,text=line.partition('=')
            if sep and text and not text.startswith('['):tablemap.setdefault(text,bytes.fromhex(code))
        cursor=int.from_bytes(data[:2],'little')
        raw_script=data[cursor:]
        ordered=0
        for s in selected:
            encoded=b''.join(b'\xe8' if c=='\n' else tablemap[c] for c in s)
            at=raw_script.find(encoded,ordered)
            if at<0:raise ValueError('wording bytes absent in compiled script')
            ordered=at+len(encoded)
        # Locate version-specific font and width coordinates by complete frozen
        # source data; this is survey-derived, not an assumed global offset delta.
        blue_path=next(f for f in args.rom_dir.glob('*.gba') if sha(f.read_bytes())==PROFILES['blue_moon']['sha256'])
        blue=blue_path.read_bytes()
        font_source=blue[FONT_BASE_BLUE:FONT_BASE_BLUE+GLYPHS*RECORD_BYTES]
        width_source=blue[WIDTH_BASE_BLUE:WIDTH_BASE_BLUE+GLYPHS*4]
        def unique(blob):
            at=rom.find(blob)
            if at<0 or rom.find(blob,at+1)>=0:raise ValueError('source anchor not unique')
            return at
        fontbase=unique(font_source);widthbase=unique(width_source)
        writes=[]
        def plan(at,final,writer):
            if at<0 or at+len(final)>len(rom):raise ValueError('write out of source bounds')
            writes.append({'offset':at,'expected':rom[at:at+len(final)],'final':final,'writer':writer})
        if not extended:
            for c,index in mapping.items():
                plan(fontbase+index*96,glyphs[c],'temporary glyph '+c)
                plan(widthbase+index*4,(12).to_bytes(4,'little'),'temporary glyph advance '+c)
        palette_at=fontbase+GLYPHS*RECORD_BYTES
        if rom[palette_at:palette_at+4]!=bytes.fromhex('0000fe7b'):
            raise ValueError('expected protected palette boundary missing')
        appended=lz_literal(data)
        extension=None
        if extended:
            from extended_dialogue import construct
            spec=json.loads((p/'tools/specs/exe4_dialogue_extension_v1.json').read_text(encoding='utf-8'))['profiles'][key]
            appended,patches,extension=construct(rom,spec,appended,glyphs)
            for at,final,writer in patches:plan(at,final,writer)
            if menu_prepared:
                from menu_extension import extend
                menu_ink,menu_archives,menu_metadata=menu_prepared
                buf=bytearray(appended);menu_layout=[]
                from ram_budgets import check as ram_budget
                for ai,mrow,mdata in menu_archives:
                    if mrow['size_header']:raise ValueError('menu relocation does not adopt size-header archives')
                    # Keep the storage form: a compressed archive stays LZ77
                    # (verbatim stream) and must still fit its RAM buffer.
                    blob=mdata
                    if mrow['compressed']:
                        ram_budget(p,ai,len(mdata));blob=lz_literal(mdata)
                        if lz77_decompress(blob,0)!=(mdata,len(blob)):raise ValueError('menu LZ blob does not decode back')
                    buf.extend(b'\xff'*((-len(buf))%4));mat=len(rom)+len(buf);buf.extend(blob)
                    menu_layout.append({'name':f"{'compressed' if mrow['compressed'] else 'raw'} menu archive {ai}",'offset':mat,'size':len(blob),'sha256':sha(blob),'payload_sha256':sha(mdata),'compressed':bool(mrow['compressed'])})
                    # An archive with a claim list is a private clone: only the
                    # listed readers (those proven to draw Hangul) move to it.
                    claims=json.loads((p/'tools/specs/exe4_consumer_contracts_v1.json').read_text(encoding='utf-8')).get('archive_claims',{}).get(str(ai),{}).get(key)
                    if claims is not None and not set(claims)<=set(mrow['pointers']):raise ValueError('menu claim list drift')
                    for ptr in (claims if claims is not None else mrow['pointers']):
                        old=int.from_bytes(rom[ptr:ptr+4],'little')
                        if old&0x1FFFFFF!=mrow['offset']:raise ValueError('menu pointer drift')
                        plan(ptr,((old&~0x1FFFFFF)|mat).to_bytes(4,'little'),f'menu archive {ai} pointer, flags preserved')
                menu_spec=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))['profiles'][key]
                appended,mpatches,tile=extend(rom,menu_spec,bytes(buf),menu_ink)
                for at,final,writer in mpatches:plan(at,final,writer)
                from rom_renderer_hangul import extend as extend_rom_renderer
                appended,rpatches,rom_renderer=extend_rom_renderer(p,key,rom,appended,extension['normal_font_offset'])
                for at,final,writer in rpatches:plan(at,final,writer)
                extension['rom_renderer_hangul']=rom_renderer
                extension['layout']+=menu_layout+tile['layout']+rom_renderer['layout']
                extension['tile_menu_hangul']='two observed styles; 4363 syllables, source-bound menu draft only'
                extension['menu']={**menu_metadata,**tile,'archives':menu_layout}
                if args.chip_folder:
                    from chip_extension import prepare as prepare_chip,extend as extend_chip
                    chip_prepared=prepare_chip(p,key,rom,args.menu_font,p/'external/textpet-indexes'/profile['index'],root)
                    appended,chip_patches,chip=extend_chip(p,key,rom,appended,chip_prepared)
                    for at,final,writer in chip_patches:plan(at,final,writer)
                    extension['layout']+=chip['layout'];extension['chip_folder']=chip
                    from pet_labels import build as build_pet_labels
                    pet_writes,pet_meta,_=build_pet_labels(p,key,rom,args.menu_font.parent/'Galmuri9.bdf')
                    for at,final,writer in pet_writes:plan(at,final,writer)
                    extension['pet_labels']=pet_meta
                    from tab_labels import build as build_tab_labels
                    tab_writes,tab_meta=build_tab_labels(p,key,rom,args.menu_font)
                    for at,final,writer in tab_writes:plan(at,final,writer)
                    extension['tab_labels']=tab_meta
                    from sort_labels import build as build_sort_labels
                    sort_writes,sort_meta=build_sort_labels(p,key,rom)
                    for at,final,writer in sort_writes:plan(at,final,writer)
                    extension['sort_labels']=sort_meta
                    from panel_labels import build as build_panel_labels
                    panel_writes,panel_meta=build_panel_labels(p,key,rom,args.menu_font.parent/'Galmuri9.bdf')
                    for at,final,writer in panel_writes:plan(at,final,writer)
                    extension['panel_labels']=panel_meta
                    from library_pa_label import build as build_pa_label
                    pa_writes,pa_meta=build_pa_label(p,key,rom,args.menu_font)
                    for at,final,writer in pa_writes:plan(at,final,writer)
                    extension['library_pa_label']=pa_meta
                    from title_menu_label import build as build_title_menu
                    title_writes,title_meta=build_title_menu(p,key,rom,args.font)
                    for at,final,writer in title_writes:plan(at,final,writer)
                    extension['title_menu_label']=title_meta
                    from result_labels import build as build_result_labels
                    result_writes,result_meta=build_result_labels(p,key,rom,args.menu_font.parent/'Galmuri9.bdf')
                    for at,final,writer in result_writes:plan(at,final,writer)
                    extension['result_labels']=result_meta
                    from ram_budgets import header_move
                    for at,final,writer in header_move(p,key,rom):plan(at,final,writer)
                    extension['mail_header_buffer']='archive 6 decoded at 0x0202C800 (was 0x0202B000) so the Korean archive 7 fits before it'
                    if args.library_chips:
                        from library_extension import prepare as prepare_library,extend as extend_library
                        library_prepared=prepare_library(p,key,rom,args.menu_font,p/'external/textpet-indexes'/profile['index'],root)
                        appended,library_patches,library=extend_library(p,key,rom,appended,library_prepared,extension['menu'])
                        for at,final,writer in library_patches:plan(at,final,writer)
                        extension['layout']+=library['layout'];extension['chip_library']=library
                        from battle_announce import writes as announce_writes
                        aw,ameta=announce_writes(p,key,rom,library)
                        for at,final,writer in aw:plan(at,final,writer)
                        extension['battle_announce']=ameta
                        if args.battle_caption:
                            from battle_caption_extension import extend as extend_battle
                            appended,bpatches,battle=extend_battle(p,key,rom,appended,library,extension['menu'])
                            for at,final,writer in bpatches:plan(at,final,writer)
                            extension['layout']+=battle['layout'];extension['battle_caption']=battle
                            if args.battle_active:
                                from battle_active_extension import extend as extend_active
                                appended,apatches,active=extend_active(p,key,rom,appended,library,extension['menu'])
                                for at,final,writer in apatches:plan(at,final,writer)
                                extension['layout']+=active['layout'];extension['battle_active']=active
                                if args.chip_descriptions:
                                    from description_extension import extend as extend_descriptions
                                    appended,dpatches,descriptions=extend_descriptions(p,key,rom,appended)
                                    for at,final,writer in dpatches:plan(at,final,writer)
                                    extension['layout']+=descriptions['layout'];extension['descriptions']=descriptions
        append_at=len(rom)
        for at in row['pointers']:
            if at==0:raise ValueError('unresolved opening pointer')
            old=int.from_bytes(rom[at:at+4],'little')
            expected=0x08000000+row['offset']
            if old not in (expected,expected|0x80000000):raise ValueError('opening pointer drift')
            plan(at,((old&~0x1ffffff)|append_at).to_bytes(4,'little'),'opening archive pointer, flags preserved')
        intervals=sorted((w['offset'],w['offset']+len(w['final'])) for w in writes)
        if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):raise ValueError('overlapping writers')
        if any(a<palette_at+0x100 and b>palette_at for a,b in intervals):raise ValueError('protected palette write')
        target=bytearray(rom)
        for w in writes:
            if rom[w['offset']:w['offset']+len(w['expected'])]!=w['expected']:raise ValueError('source changed')
            target[w['offset']:w['offset']+len(w['final'])]=w['final']
        target.extend(appended);target.extend(b'\xff'*(0x1000000-len(target)))
        allowed=bytearray(len(rom))
        for w in writes:allowed[w['offset']:w['offset']+len(w['final'])]=b'\x01'*len(w['final'])
        if any(a!=b and not allowed[i] for i,(a,b) in enumerate(zip(rom,target))):raise ValueError('unexplained diff')
        if target[len(rom):len(rom)+len(appended)]!=appended or any(b!=255 for b in target[len(rom)+len(appended):]):raise ValueError('append plan drift')
        # All 25 unselected scripts must retain exactly the same binary slices.
        def slices(d):
            offsets=[int.from_bytes(d[i:i+2],'little') for i in range(0,int.from_bytes(d[:2],'little'),2)]
            return [d[a:(offsets[i+1] if i+1<len(offsets) else len(d))] for i,a in enumerate(offsets)]
        if args.selection=='centered' and slices(data)[1:]!=slices(original_data)[1:]:raise ValueError('unselected script bytes changed')
        # The non-text TPL skeleton (events, timers, jumps, waits, portraits)
        # must match source; only the 5 centering widths are allowed to change.
        def skeleton(t):
            return re.sub(r'(positionTextCenter\s+width = )\d+',r'\1WIDTH',LITERAL.sub('"TEXT"',t)).replace('\r\n','\n').strip()
        for i,block in zip(selected_ids,blocks):
            source_block=original[matches[i].end():matches[i+1].start() if i+1<len(matches) else len(original)]
            if skeleton(block)!=skeleton(source_block):raise ValueError('protected control structure changed')
        suffix='opening_menu_chip_folder_library_korean_development' if args.library_chips else 'opening_menu_chip_folder_korean_development' if args.chip_folder else 'opening_menu_korean_development' if args.menu_font else 'hangul_boundary_visibility' if args.font_probe else 'opening_korean_extended_development' if extended else 'opening_visibility_poc' if args.selection=='centered' else 'opening_korean_development'
        out=p/'poc/output'/f'{key}_{suffix}.gba'
        if args.battle_caption:out=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_caption_korean_development.gba'
        if args.battle_active:out=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_active_korean_development.gba'
        if args.chip_descriptions:out=p/'poc/output'/f'{key}_opening_menu_chip_folder_library_battle_descriptions_korean_development.gba'
        out.write_bytes(target)
        manifest={'policy':'development/PoC; NON-DISTRIBUTION','known_limit':'temporary glyph reassignment changes untranslated uses elsewhere; full Hangul encoding not implemented','selected_entries':[f'archive/442/script/{i}' for i in selected_ids],'translation_asset_sha256':sha((p/'translations/opening_korean.json').read_bytes()),'source_profile':key,'source_sha256':sha(rom),'output_sha256':sha(target),'output_bytes':len(target),'font_source':{'name':args.font.name,'sha256':sha(args.font.read_bytes()),'use':'functional PoC candidate; visual direction unapproved'},'font_base':hex(fontbase),'width_base':hex(widthbase),'glyph_count':len(mapping),'mapping':mapping,'page_pixel_budgets':page_widths,'archive_original_offset':row['offset'],'archive_new_offset':append_at,'archive_payload_sha256':sha(data),'unselected_script_bytes_preserved':26-len(selected_ids),'control_skeleton_preserved':True,'expected_writes':[{'offset':w['offset'],'size':len(w['final']),'writer':w['writer'],'expected_sha256':sha(w['expected']),'final_sha256':sha(w['final'])} for w in writes]+[{'offset':append_at,'size':len(target)-append_at,'writer':'relocated LZ archive and FF ROM growth','final_sha256':sha(target[append_at:])}],'final_diff_audited':True,'runtime':'pending'}
        if extended:
            manifest['known_limit']='normal dialogue extension only; tile consumers and F9 FC collision population remain open; no whole-game or device QA'
            if args.menu_font:manifest['known_limit']='normal dialogue plus two observed menu font styles; menu supply is 4363 syllables and demand-gated; other consumers, collision population, whole-game and device QA remain open'
            if args.chip_folder:manifest['known_limit']='development-only private folder clone for ten draft chip names and a 24-syllable split cache; battle, other chip consumers, NAME, whole-game and device QA remain open'
            if args.library_chips:manifest['known_limit']='development-only private seven-row library clones for 294 draft names with 56 per-cell VRAM slots; language/font approval, RAM-special IDs, other consumers, whole-game and device QA remain open'
            if args.battle_caption:manifest['known_limit']='development library plus Custom Screen highlighted-chip caption only; other battle consumers, language/font approval, whole-game and device QA remain open'
            if args.battle_active:manifest['known_limit']='development library, Custom Screen caption and queued in-battle name; descriptions, other battle consumers, independent review and whole-game/device QA remain open'
            if args.chip_descriptions:manifest['known_limit']='adds ten private Custom Screen descriptions; other description consumers, independent review and whole-game/device QA remain open'
            manifest['extension']=extension
            manifest['encoding_profile']='extended_dialogue_F9FC_v1'
            manifest['extended_codec_byte_roundtrip']=True
            manifest['wording_reextracted_exactly']=True
        manifest['translation_asset_sha256']=sha(wording_path.read_bytes())
        manifest['input_kind']='functional-font-probe; not story translation' if args.font_probe else 'translation draft; needs_review'
        out.with_suffix('.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        print(key,sha(target),'glyphs',len(mapping),'pages',len(selected),'font',hex(fontbase),'widths',hex(widthbase))
if __name__=='__main__':main()
