"""Demand-gated F9 FC tile extension; source/native palettes remain intact."""
import json,subprocess,shutil
from pathlib import Path
from analyze_project import sha,scripts,SCRIPT,LITERAL,payload
from verify_tpi_index import parse_tpi
from extended_dialogue import assemble_verified

def font_ink(path):
    found={}
    for block in path.read_text(encoding='ascii').split('STARTCHAR ')[1:]:
        lines=block.splitlines();cp=int(next(x.split()[1] for x in lines if x.startswith('ENCODING ')))
        if not 0xac00<=cp<=0xd7a3:continue
        w,h,xo,yo=map(int,next(x for x in lines if x.startswith('BBX ')).split()[1:])
        top=14-h-yo;start=lines.index('BITMAP')+1
        ink={(x+xo,y+top) for y,row in enumerate(lines[start:start+h]) for x in range(w) if int(row,16)&(1<<(((w+7)//8)*8-1-x))}
        if not ink or any(not (0<=x<8 and 0<=y<15) for x,y in ink):raise ValueError('menu ink cannot fit '+chr(cp))
        found[chr(cp)]=ink
    if len(found)!=4363:raise ValueError('menu font repertoire drift')
    # The user preferred EXE3's 8x16 lettering: every KS X 1001 syllable takes
    # the EXE 1 [K] glyph; the Galmuri7 repertoire still decides which exist.
    from exe1k_hangul import load,ink as exe1k_ink
    source=json.loads((Path(__file__).resolve().parent/'specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))['hangul_glyph_source']
    rom=load(source['path'])
    if sha(rom)!=source['sha256']:raise ValueError('EXE 1 [K] glyph source drift')
    for c in found:
        pixels=exe1k_ink(rom,c)
        if pixels is not None:found[c]=pixels
    return found

def pack(ink,style):
    grid=[[style['background']]*8 for _ in range(16)]
    # The native font drops its shadow one pixel right and down. A glyph that
    # leaves column 7 free (every EXE 1 [K] glyph) does the same; a width-eight
    # Galmuri7 syllable keeps a vertical shadow so no ink pixel is lost.
    dx=1 if all(x<=6 for x,_ in ink) else 0
    for x,y in ink:grid[y+1][x+dx]=style['shadow']
    for x,y in ink:grid[y][x]=style['ink']
    return bytes(grid[y][x]|grid[y][x+1]<<4 for y in range(16) for x in range(0,8,2))

def literals(entry,field):
    """An entry's literals in script order. A plain string is a one-literal
    label; a list is a script whose literals sit between commands (a number
    printed before or between them) and is replaced literal by literal."""
    value=entry[field]
    return value if isinstance(value,list) else [value]

def encoder(p):
    table={}
    for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
        code,sep,text=line.partition('=')
        if sep and (len(text)==1 or text.startswith('[')):table.setdefault(text,bytes.fromhex(code))
    def encode(text):
        out=b''
        while text:
            if text[0]=='\n':out+=b'\xe8';text=text[1:];continue
            # A bracketed table token such as [MB] is one byte, not four letters.
            token=next((k for k in table if k.startswith('[') and text.startswith(k)),text[0])
            out+=b'\xf9\xfc'+(ord(token)-0xac00).to_bytes(2,'little') if len(token)==1 and 0xac00<=ord(token)<=0xd7a3 else table[token]
            text=text[len(token):]
        return out
    return encode

def substitute(span,sources,texts,encode):
    """Swap each source literal's bytes for its translation in order; every
    byte between them (commands and their parameters) stays as it was."""
    out=bytearray();at=0
    for s,t in zip(sources,texts,strict=True):
        old=encode(s);found=span.find(old,at)
        if found<0:raise ValueError('menu source literal not in its script bytes')
        out+=span[at:found]+encode(t);at=found+len(old)
    return bytes(out+span[at:])

def prepare(p,key,rom,font,plugins,root,index,translation_asset=None,selection_validator=None):
    spec=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))
    if sha(font.read_bytes())!=spec['font_sha256']:raise ValueError('menu font identity drift')
    ink=font_ink(font)
    asset=translation_asset or p/'translations/menu_korean.json';wording=json.loads(asset.read_text(encoding='utf-8'))
    if wording['schema']!=1 or wording['state']!='needs_review':raise ValueError('menu translation policy changed')
    if len({(x['id'],x.get('revision')) for x in wording['entries']})!=len(wording['entries']):raise ValueError('duplicate menu input')
    # Archive numbers differ between the revisions for a few archives (the
    # training menu is red 4 / blue 3), so an entry may name its revision.
    wording={**wording,'entries':[x for x in wording['entries'] if x.get('revision',key)==key]}
    wanted={c for x in wording['entries'] for c in ''.join(literals(x,'text')) if 0xac00<=ord(c)<=0xd7a3}
    if wanted-set(ink):raise ValueError('menu font missing: '+''.join(sorted(wanted-set(ink))))
    from consumer_contracts import validate_selection
    consumer_metadata=(selection_validator or validate_selection)(p,key,rom,wording)
    # Menu archives contain unselected Japanese prose. Keep its complete
    # source table, including the Japanese comma; the opening's authored
    # ASCII-comma compatibility table is unsuitable for that prose.
    plugins=root/'menu_plugins'
    shutil.copytree(p/'external/textpet-plugins',plugins,dirs_exist_ok=True)
    table=plugins/'exe4-utf8.tbl'
    existing=table.read_text(encoding='utf-8');lines=set(existing.splitlines())
    additions=['F9FC'+(ord(c)-0xac00).to_bytes(2,'little').hex().upper()+'='+c for c in sorted(wanted)]
    table.write_text(existing+'\n'+'\n'.join(x for x in additions if x not in lines)+'\n',encoding='utf-8')
    rows=parse_tpi(index);groups={};artifacts=[]
    entries={x['id']:x for x in (json.loads(line) for line in (p/'analysis'/f'{key}_source_entries.jsonl').read_text(encoding='utf-8').splitlines())}
    for x in wording['entries']:groups.setdefault(int(x['id'].split('/')[1]),[]).append(x)
    exe=p/'external/TextPet-v1.0.0/TextPet.exe'
    common=[str(exe),'load-plugins',str(plugins),'game','exe4']
    root=root/'menu';root.mkdir(parents=True,exist_ok=True)
    for ai,selected in sorted(groups.items()):
        row=rows[ai];name=f"{row['offset']:06X}";original=payload(rom,row)
        src=(p/'analysis'/f'{key}_tpl'/(name+'.tpl')).read_text(encoding='utf-8-sig')
        parsed={si:(language,values,block) for si,language,values,block in scripts(src)}
        before=src
        for x in selected:
            si=int(x['id'].split('/')[-1]);protected=entries[x['id']]
            if protected['source_rom_sha256']!=sha(rom) or protected['source_payload_sha256']!=sha(original):raise ValueError('menu source identity drift')
            sources,texts=literals(x,'source'),literals(x,'text')
            if protected['source_literals']!=sources or parsed[si][0]!='mmbn4s' or parsed[si][1]!=sources:raise ValueError('menu source wording drift')
            # A line break is allowed only where the source has the same number
            # of breaks (multi-line descriptions drawn by the message box). A word
            # inserted into dialogue (budget: bytes) is held to its buffer by the
            # consumer contract instead of the source's cell count.
            if len(texts)!=len(sources) or any(c in t for t in texts for c in '"\\') or any(s.count('\n')!=t.count('\n') for s,t in zip(sources,texts)) or (x.get('budget')!='bytes' and any(len(t)>len(s) for s,t in zip(sources,texts))):raise ValueError('menu exceeds source cell budget')
            matches=list(SCRIPT.finditer(src));m=next(m for m in matches if int(m.group(1))==si)
            end=next((n.start() for n in matches if n.start()>m.start()),len(src))
            block=src[m.end():end];ls=list(LITERAL.finditer(block))
            if len(ls)!=len(sources):raise ValueError('menu literal count drift')
            newblock=block
            for l,t in reversed(list(zip(ls,texts))):newblock=newblock[:l.start()]+'"'+t.replace('\n','\\n')+'"'+newblock[l.end():]
            if LITERAL.sub('TEXT',block)!=LITERAL.sub('TEXT',newblock):raise ValueError('menu control mutation')
            src=src[:m.end()]+newblock+src[end:]
        tpl=root/(name+'.tpl');msg=root/(name+'.msg');back=root/(name+'_back.tpl');again=root/(name+'_back.msg')
        tpl.write_bytes(src.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
        stages=[['read-text-archives',str(tpl),'-f','tpl','write-text-archives',str(msg),'-f','bin'],['read-text-archives',str(msg),'-f','bin','write-text-archives',str(back),'-f','tpl'],['read-text-archives',str(back),'-f','tpl','write-text-archives',str(again),'-f','bin']]
        for number,stage in enumerate(stages):
            r=subprocess.run(common+stage,capture_output=True);(root/f'{name}_{number}.log').write_bytes(r.stdout+r.stderr)
            if r.returncode or b'FATAL:' in r.stdout+r.stderr:raise ValueError('menu TextPet failure')
        data=msg.read_bytes()
        if data!=again.read_bytes():raise ValueError('menu roundtrip mismatch')
        # TextPet guesses each script's language when it reads binary back, and
        # a script that opens with a number command (F1) reads as mmbn4. Plain
        # labels are still re-extracted; every label is also checked by bytes.
        observed={si:vs for si,lang,vs,b in scripts(back.read_text(encoding='utf-8-sig'))}
        lost=[(x['id'],x['text'],observed[int(x['id'].split('/')[-1])]) for x in selected if not isinstance(x['text'],list) and observed[int(x['id'].split('/')[-1])]!=[x['text']]]
        if lost:raise ValueError('menu wording lost '+repr(lost[:5]))
        def spans(d):
            first=int.from_bytes(d[:2],'little');offsets=[int.from_bytes(d[i:i+2],'little') for i in range(0,first,2)]
            valid=sorted(set(x for x in offsets if first<=x<=len(d)))
            if any(x!=65535 and x not in valid for x in offsets):raise ValueError('unsupported archive table')
            ends={v:(valid[i+1] if i+1<len(valid) else len(d)) for i,v in enumerate(valid)}
            return [None if x==65535 else d[x:ends[x]] for x in offsets]
        oldsp,newsp=spans(original),spans(data);selected_ids={int(x['id'].split('/')[-1]) for x in selected}
        encode=encoder(p)
        for x in selected:
            si=int(x['id'].split('/')[-1])
            if newsp[si]!=substitute(oldsp[si],literals(x,'source'),literals(x,'text'),encode):raise ValueError('menu label bytes differ from literal substitution '+x['id'])
        # A slot that points at the same bytes as a selected script is an alias
        # of it (archive 62 parks twenty unused slots on one item name), so it
        # follows that script's new wording rather than keeping the old bytes.
        old_offsets=[int.from_bytes(original[i:i+2],'little') for i in range(0,int.from_bytes(original[:2],'little'),2)]
        aliases={i for i,o in enumerate(old_offsets) if o!=65535 and any(old_offsets[s]==o for s in selected_ids)}
        if any(newsp[i]!=newsp[next(s for s in selected_ids if old_offsets[s]==old_offsets[i])] for i in aliases-selected_ids):raise ValueError('alias does not follow its selected script')
        if len(oldsp)!=len(newsp) or any(a!=b for i,(a,b) in enumerate(zip(oldsp,newsp)) if i not in selected_ids|aliases):raise ValueError('unselected menu script changed')
        artifacts.append((ai,row,data))
    return ink,artifacts,{**consumer_metadata,'translation_asset_sha256':sha(asset.read_bytes()),'selected_entries':wording['entries'],'glyph_demand':sorted(wanted),'source_bound':True,'control_skeleton_preserved':True,'unselected_script_bytes_preserved':True,'codec_byte_roundtrip':True,'wording_reextracted_exactly':True,'font_source_sha256':sha(font.read_bytes())}

def extend(source,spec,append,ink):
    if sha(source)!=spec['source_sha256'] or sha(source[spec['source_code_offset']:spec['source_code_offset']+spec['source_code_size']])!=spec['source_code_sha256']:raise ValueError('tile source drift')
    if source[spec['slot']['offset']:spec['slot']['offset']+4].hex()!=spec['slot']['expected_hex']:raise ValueError('tile F9 slot drift')
    blob=bytearray(append);layout=[]
    def alloc(data,name):
        blob.extend(b'\xff'*((-len(blob))%4));at=len(source)+len(blob);blob.extend(data)
        layout.append({'name':name,'offset':at,'size':len(data),'sha256':sha(data)});return at
    chars=sorted(ink);banks=[]
    for style in spec['fonts']:
        at=style['source_address']&0x1ffffff
        if sha(source[at:at+style['size']])!=style['sha256']:raise ValueError('tile font source drift')
        banks.append(alloc(b''.join(pack(ink[c],style) for c in chars),'Galmuri7 tile bank '+hex(style['source_address'])))
    lookup=bytearray(b'\xff\xff'*11172)
    for i,c in enumerate(chars):lookup[(ord(c)-0xac00)*2:(ord(c)-0xac00)*2+2]=i.to_bytes(2,'little')
    map_at=alloc(lookup,'4363-syllable map; FFFF unsupported sentinel')
    from extended_dialogue import JUMP
    code='''ldrb r7, [r0, #1]
cmp r7, #0xfc
beq hangul
cmp r7, #0xfd
beq jump
ldr r7, legacy
bx r7
jump:
'''+JUMP('r0','r1')+'''mov pc, lr
hangul:
push {r6, lr}
ldrb r1, [r0, #3]
lsls r1, r1, #8
ldrb r7, [r0, #2]
adds r1, r1, r7
ldr r7, limit
cmp r1, r7
bge unsupported
lsls r1, r1, #1
ldr r7, lookup
ldrh r1, [r7, r1]
ldr r7, sentinel
cmp r1, r7
beq unsupported
ldr r7, native0
cmp r6, r7
beq style0
ldr r7, native1
cmp r6, r7
bne unsupported
ldr r6, font1
b draw
style0:
ldr r6, font0
draw:
ldr r7, renderer
mov lr, pc
bx r7
adds r0, #4
mov r7, r9
adds r7, #1
mov r9, r7
pop {r6, pc}
unsupported:
b unsupported
'''
    literals={'legacy':spec['slot']['legacy_handler'],'limit':11172,'lookup':0x08000000+map_at,'sentinel':65535,'native0':spec['fonts'][0]['source_address'],'native1':spec['fonts'][1]['source_address'],'font1':0x08000000+banks[1],'font0':0x08000000+banks[0],'renderer':spec['renderer_runtime']}
    at=len(source)+((len(blob)+3)&~3);code,isa=assemble_verified(code,0x08000000+at,literals)
    hook=alloc(code,'tile F9 FC handler')
    return bytes(blob),[(spec['slot']['offset'],(0x08000001+hook).to_bytes(4,'little'),'tile_f9_slot')],{'layout':layout,'machine_code':isa,'fonts':banks,'map_offset':map_at,'syllables':4363,'characters':chars,'styles':spec['fonts'],'unsupported_policy':'explicit stop loop for absent glyph, invalid code or unclassified native font; build rejects missing glyph demand; no blank fallback','all_consumers_closed':False}
