"""Independent menu pixel/table/script/pointer and runtime attribution checks."""
import json,re
from pathlib import Path
from analyze_project import sha,payload
from verify_tpi_index import parse_tpi,lz77_decompress
from extended_dialogue import assemble_verified

def check(p,key,source,data,m,font,static_only=False):
 spec=json.loads((p/'tools/specs/exe4_menu_extension_v1.json').read_text(encoding='utf-8'))
 s=spec['profiles'][key];t=m['extension']['menu']
 if sha(font.read_bytes())!=spec['font_sha256'] or sha(font.read_bytes())!=t['font_source_sha256']:raise ValueError('menu font identity mismatch')
 ink={}
 for block in font.read_text(encoding='ascii').split('STARTCHAR ')[1:]:
  lines=block.splitlines();cp=int(next(x.split()[1] for x in lines if x.startswith('ENCODING ')))
  if not 0xac00<=cp<=0xd7a3:continue
  w,h,xo,yo=map(int,next(x for x in lines if x.startswith('BBX ')).split()[1:]);start=lines.index('BITMAP')+1
  rows=[bytes.fromhex(x) for x in lines[start:start+h]]
  ink[chr(cp)]={(x+xo,y+14-h-yo) for y,row in enumerate(rows) for x in range(w) if row[x//8]&(0x80>>(x%8))}
 chars=sorted(ink)
 # KS X 1001 syllables come from EXE 1 [K] (rows as strings, written apart from
 # tools/exe1k_hangul.py): drop the first row and column, then delete the first
 # repeated inked row (else clear row 0 under a continuing stroke, else the
 # first repeated row) with everything above sliding down one.
 g=spec['hangul_glyph_source'];k1=Path(g['path']).read_bytes()
 if sha(k1)!=g['sha256']:raise ValueError('EXE 1 [K] glyph source drift')
 for c in chars:
  try:e=c.encode('euc_kr')
  except UnicodeEncodeError:continue
  n=(e[0]-0xB0)*94+(e[1]-0xA1)
  if not (0xB0<=e[0]<=0xC8 and 0<=n<2350):continue
  rec=k1[0x80016C+(512+n)*64:0x80016C+(513+n)*64]
  rows=[''.join('1' if ((rec[y*4+x//2]>>(4*(x%2)))&15)==3 else '0' for x in range(8)) for y in range(16)]
  rows=[r[1:]+'0' for r in rows[1:]]+['0'*8]
  if '1' in rows[0]:
   d=next((i for i in range(1,16) if rows[i]==rows[i-1] and '1' in rows[i]),None)
   if d is None and all(rows[1][x]=='1'==rows[2][x] for x in range(8) if rows[0][x]=='1'):rows=['0'*8]+rows[1:]
   else:
    d=d if d is not None else next(i for i in range(1,16) if rows[i]==rows[i-1])
    rows=['0'*8]+rows[:d]+rows[d+1:]
  ink[c]={(x,y) for y,r in enumerate(rows) for x,v in enumerate(r) if v=='1'}
 if len(chars)!=4363 or t['characters']!=chars or t['styles']!=s['fonts']:raise ValueError('tile font supply drift')
 for style,base in zip(s['fonts'],t['fonts']):
  at=style['source_address']&0x1ffffff
  if data[at:at+style['size']]!=source[at:at+style['size']]:raise ValueError('native tile font changed')
  for i,c in enumerate(chars):
   record=data[base+i*64:base+(i+1)*64]
   pixels={(j*2%8,j*2//8):b&15 for j,b in enumerate(record)};pixels.update({((j*2+1)%8,(j*2+1)//8):b>>4 for j,b in enumerate(record)})
   right=int(max(x for x,_ in ink[c])<7)
   shadow={(x+right,y+1) for x,y in ink[c]}-ink[c]
   if {pos for pos,v in pixels.items() if v==style['ink']}!=ink[c] or {pos for pos,v in pixels.items() if v==style['shadow']}!=shadow or any(v!=style['background'] for pos,v in pixels.items() if pos not in ink[c]|shadow):raise ValueError('tile glyph pixel mismatch '+c)
 for i in range(11172):
  at=t['map_offset']+i*2;actual=int.from_bytes(data[at:at+2],'little')
  expected=chars.index(chr(0xac00+i)) if chr(0xac00+i) in ink else 65535
  if actual!=expected:raise ValueError('tile map drift')
 code=t['machine_code'];a=code['address']-0x08000000
 rebuilt,_=assemble_verified('\n'.join(x['mnemonic']+' '+x['operands'] for x in code['instructions']),code['address'],code['literal_values'])
 if data[a:a+len(rebuilt)]!=rebuilt or int.from_bytes(data[s['slot']['offset']:s['slot']['offset']+4],'little')!=code['address']|1:raise ValueError('tile code/dispatch drift')
 asset=p/'translations/menu_korean.json';wording=json.loads(asset.read_text(encoding='utf-8'))
 if any(x.get('revision') not in (None,'blue_moon','red_sun') for x in wording['entries']):raise ValueError('menu revision tag unknown')
 wording={**wording,'entries':[x for x in wording['entries'] if x.get('revision',key)==key]}
 if wording['state']!='needs_review' or sha(asset.read_bytes())!=t['translation_asset_sha256'] or wording['entries']!=t['selected_entries']:raise ValueError('menu asset drift')
 from consumer_contracts import validate_selection
 consumer=validate_selection(p,key,source,wording)
 if not t.get('consumer_selection_verified') or t.get('consumer_contract_sha256')!=consumer['consumer_contract_sha256']:raise ValueError('menu consumer contract not attributed')
 if not all(t[x] for x in ['source_bound','control_skeleton_preserved','unselected_script_bytes_preserved','codec_byte_roundtrip','wording_reextracted_exactly']):raise ValueError('menu build gates absent')
 rows=parse_tpi(p/'external/textpet-indexes'/('exe4bm-v10.tpi' if key=='blue_moon' else 'exe4rs-v11.tpi'))
 table={}
 for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
  code,sep,text=line.partition('=')
  if sep and len(text)==1:table.setdefault(text,bytes.fromhex(code))
  elif sep and text[:1]=='[' and text[-1:]==']':table.setdefault(text,bytes.fromhex(code))
 def encode(text):
  parts=re.split(r'(\[[^\]]+\])',text)
  return b''.join(table[x] if x.startswith('[') else b''.join(b'\xe8' if c=='\n' else b'\xf9\xfc'+(ord(c)-0xac00).to_bytes(2,'little') if c in ink else table[c] for c in x) for x in parts if x)
 def literals(x,field):return x[field] if isinstance(x[field],list) else [x[field]]
 def substitute(span,sources,texts,encode):
  rest=span;out=b''
  for s,t in zip(sources,texts):
   head,sep,rest=rest.partition(encode(s))
   if not sep:raise ValueError('menu source literal absent from its script')
   out+=head+encode(t)
  return out+rest
 def spans(d):
  f=int.from_bytes(d[:2],'little');o=[int.from_bytes(d[i:i+2],'little') for i in range(0,f,2)];v=sorted(set(o))
  if any(not f<=x<=len(d) for x in o):raise ValueError('unproved menu table value')
  ends={x:v[i+1] if i+1<len(v) else len(d) for i,x in enumerate(v)}
  return o,[d[x:ends[x]] for x in o]
 translated_addresses={};required={f'archive/001/script/{i}' for i in range(6,10)}|{'archive/005/script/0','archive/013/script/3'}
 for part in t['archives']:
  ai=int(part['name'].split()[-1]);row=rows[ai];old=payload(source,row);new=data[part['offset']:part['offset']+part['size']]
  if bool(row['compressed'])!=bool(part.get('compressed')):raise ValueError('menu archive storage form changed')
  if row['compressed']:
   new,used=lz77_decompress(data,part['offset'])
   if used!=part['size']:raise ValueError('menu LZ blob length mismatch')
  oo,os=spans(old);no,ns=spans(new);selected={int(x['id'].split('/')[-1]):x for x in wording['entries'] if int(x['id'].split('/')[1])==ai}
  # A slot sharing a selected script's original offset is its alias and must
  # hold that script's new bytes; every other unselected slot keeps the old.
  aliases={i:next(s for s in selected if oo[s]==oo[i]) for i in range(len(oo)) if i not in selected and any(oo[s]==oo[i] for s in selected)}
  if any(ns[i]!=ns[s] for i,s in aliases.items()):raise ValueError('menu alias does not follow its script')
  if len(oo)!=len(no) or any(x!=y for i,(x,y) in enumerate(zip(os,ns)) if i not in selected and i not in aliases):raise ValueError('unselected menu bytes differ')
  for si,x in selected.items():
   sources,texts=literals(x,'source'),literals(x,'text')
   if len(sources)!=len(texts) or (x.get('budget')!='bytes' and any(len(t)>len(s) for s,t in zip(sources,texts))):raise ValueError('menu exceeds source cells')
   # A plain label is exactly its literal; a command-bearing one keeps every
   # byte between its literals.
   if not isinstance(x['source'],list) and os[si]!=encode(x['source'])+b'\xe5':raise ValueError('menu exact encoded source mismatch')
   if ns[si]!=substitute(os[si],sources,texts,encode):raise ValueError('menu exact encoded wording mismatch')
   if not row['compressed']:translated_addresses[0x08000000+part['offset']+no[si]]=(x,ns[si])
  claims=json.loads((p/'tools/specs/exe4_consumer_contracts_v1.json').read_text(encoding='utf-8')).get('archive_claims',{}).get(str(ai),{}).get(key)
  for ptr in row['pointers']:
   if claims is not None and ptr not in claims:
    if data[ptr:ptr+4]!=source[ptr:ptr+4]:raise ValueError('unlisted claim of a private menu clone moved')
    continue
   was,now=int.from_bytes(source[ptr:ptr+4],'little'),int.from_bytes(data[ptr:ptr+4],'little')
   if was&0x1FFFFFF!=row['offset'] or now&0x1FFFFFF!=part['offset'] or was&~0x1FFFFFF!=now&~0x1FFFFFF:raise ValueError('menu archive relocation mismatch')
 result={'tile_glyphs_pixel_verified_per_style':4363,'tile_styles':2,'menu_code_roundtrip':True,'menu_selected_scripts':len(wording['entries']),'menu_unselected_bytes_preserved':True,'consumer_selection_verified':True,'consumer_contract_sha256':consumer['consumer_contract_sha256'],'runtime_status':'pending'}
 if static_only:return result
 bench_path=p/'analysis/menu_bench.json';bench=json.loads(bench_path.read_text(encoding='utf-8'))
 if bench['status']!='PASS' or bench['products'][key]!=sha(data) or bench['font_sha256']!=sha(font.read_bytes()):raise ValueError('CPU bench attribution drift')
 for name,digest in bench['inputs'].items():
  if sha((p/name).read_bytes())!=digest:raise ValueError('CPU bench input drift')
 for case in bench['records']:
  if case['return_code'] or sha((p/case['log']).read_bytes())!=case['log_sha256'] or sha(Path(case['command'][1]).read_bytes())!=case['test_script_sha256']:raise ValueError('CPU bench case drift')
 result['cpu_bench_sha256']=sha(bench_path.read_bytes())
 root=p/'analysis/runtime'/f'{key}_menu_final_02';receipt=root/'result.json'
 if receipt.exists():
  r=json.loads(receipt.read_text(encoding='utf-8'))
  for name,digest in r['artifacts'].items():
   if sha((root/name).read_bytes())!=digest:raise ValueError('menu runtime artifact drift')
  if r['rom_sha256']!=sha(data) or len(r['loaded_rom_guards'])<7 or r['audio_enabled']:raise ValueError('menu runtime attribution mismatch')
  if r['complete'] and r['return_code']==0 and r['steps_captured']==r['steps_expected']==107:
   calls=json.loads((root/'tilecalls_final.json').read_text(encoding='utf-8'))['calls'];seen={};expected=set()
   for c in calls:
    hit=translated_addresses.get(c['stream'])
    if hit:
     x,stream=hit
     if c['stream_prefix_hex'][:min(64,len(stream)*2)]!=stream.hex().upper()[:64]:raise ValueError('actual menu stream bytes mismatch')
     style=next((i for i,sf in enumerate(s['fonts']) if sf['source_address']==c['font']),None)
     if style is None:raise ValueError('unproved actual native tile style')
     seen[x['id']]={'call':c,'text':x['text']}
     expected|={chars.index(ch)+style*4363 for ch in ''.join(literals(x,'text')) if ch in ink}
   if required-set(seen):raise ValueError('menu route did not reach all required labels: '+str(required-set(seen)))
   reads=json.loads((root/'fontread_final.json').read_text(encoding='utf-8'))
   if {x['index'] for x in reads['records']}!=expected or {x['pc'] for x in reads['sites']}!={'0x0300680A'}:raise ValueError('actual tile glyph consumption mismatch')
   result.update(runtime_status='completed diagnostic; visual QA separate',actual_menu_entries=seen,actual_tile_records_read=len(expected),runtime_receipt_sha256=sha(receipt.read_bytes()))
  else:result['runtime_status']='PARTIAL_RUNTIME'
 visual_path=p/'analysis/MENU_RUNTIME_QA.json'
 if visual_path.exists():
  visual=json.loads(visual_path.read_text(encoding='utf-8'));v=next(x for x in visual['profiles'] if x['profile']==key)
  if v['rom_sha256']!=sha(data) or v['runtime_receipt_sha256']!=sha(receipt.read_bytes()):raise ValueError('manual visual attribution drift')
  for capture in v['checks']:
   if sha((p/capture['capture']).read_bytes())!=capture['capture_sha256']:raise ValueError('manual visual capture drift')
  result.update(visual_status='manual bounded-route inspection recorded; final font and language approval pending',visual_qa_sha256=sha(visual_path.read_bytes()))
 return result
