"""Compile source-bound 9-visible-cell menu descriptions; never writes a ROM."""
import json,re,shutil,subprocess
from pathlib import Path
from analyze_project import PROFILES,sha,payload,scripts,SCRIPT,LITERAL
from verify_tpi_index import parse_tpi
from menu_extension import font_ink
p=Path(__file__).resolve().parents[1]
author=p/'translations/menu_chip_description_authored.json'
auth=json.loads(author.read_text(encoding='utf-8'))
selected={int(k):v for k,v in auth['scripts'].items()}
if set(selected)!={1,4,15,29,48,49,91,107,117,149} or auth['state']!='needs_review':raise ValueError('description scope drift')
font=Path(r'D:\Games\Kor Patch\CLude\폰트\Galmuri-v2.24.29\Galmuri7.bdf')
wanted={c for text in selected.values() for c in text if 0xac00<=ord(c)<=0xd7a3}
ink=font_ink(font)
if wanted-set(ink):raise ValueError('missing menu Hangul glyph')
report={'schema':1,'status':'PASS research compilation only; no ROM insertion or Hangul description runtime claim',
 'authoring_sha256':sha(author.read_bytes()),'font_sha256':sha(font.read_bytes()),'Hangul_syllables':len(wanted),
 'selected_entries':10,'profiles':{},'consumer_scope':'observed folder edit and seven-row library description calls; third menu claim unclassified',
 'runtime_native_reference':'analysis/runtime/blue_moon_battle_description_survey_01/result.json'}
bindings={};reference=None
def spans(data):
 first=int.from_bytes(data[:2],'little');offsets=[int.from_bytes(data[i:i+2],'little') for i in range(0,first,2)]
 valid=sorted(set(x for x in offsets if x!=65535));ends={v:valid[i+1] if i+1<len(valid) else len(data) for i,v in enumerate(valid)}
 return [None if x==65535 else data[x:ends[x]] for x in offsets]
for key,pr in PROFILES.items():
 source=next(f.read_bytes() for f in p.parent.parent.glob('*.gba') if sha(f.read_bytes())==pr['sha256'])
 row=parse_tpi(p/'external/textpet-indexes'/pr['index'])[54];old=payload(source,row)
 es={e['script_id']:e for e in map(json.loads,(p/'analysis'/f'{key}_source_entries.jsonl').read_text(encoding='utf-8').splitlines()) if e['archive_index']==54}
 original=(p/'analysis'/f'{key}_tpl'/f"{row['offset']:06X}.tpl").read_text(encoding='utf-8-sig')
 parsed={si:(lang,values,block) for si,lang,values,block in scripts(original)}
 if len(parsed)!=256 or len(es)!=256:raise ValueError('archive54 population drift')
 if reference is not None and [parsed[i][1] for i in selected]!=reference:raise ValueError('version-specific description wording')
 reference=[parsed[i][1] for i in selected]
 root=p/'analysis/menu_chip_description_compilation'/key;plugins=root/'plugins'
 shutil.copytree(p/'external/textpet-plugins',plugins,dirs_exist_ok=True)
 table=plugins/'exe4-utf8.tbl';native=table.read_text(encoding='utf-8-sig');mapping={}
 for line in native.splitlines():
  code,sep,ch=line.partition('=')
  if sep and len(ch)==1:mapping.setdefault(ch,bytes.fromhex(code))
 table.write_text(native+'\n'+'\n'.join('F9FC'+(ord(c)-0xac00).to_bytes(2,'little').hex().upper()+'='+c for c in sorted(wanted))+'\n',encoding='utf-8')
 ds=json.loads((p/'tools/specs/exe4_dialogue_extension_v1.json').read_text())['profiles'][key]
 widths=ds['advance_literal']['expected_address']-0x08000000
 def measure(text):
  for c in text:
   if c not in wanted and (c not in mapping or len(mapping[c])!=1):raise ValueError('unclassified native menu cell')
  return len(text)
 text=original;details=[]
 for si,translated in selected.items():
  e=es[si];lang,values,_=parsed[si]
  if lang!='mmbn4' or len(values)!=1 or e['source_literals']!=values or e['source_rom_sha256']!=sha(source) or e['source_payload_sha256']!=sha(old):raise ValueError('description source binding drift')
  lines=translated.split('\n');line_cells=list(map(measure,lines))
  if len(lines)>3 or max(line_cells)>9:raise ValueError('menu 9-visible-cell by 3-line budget exceeded')
  matches=list(SCRIPT.finditer(text));m=next(m for m in matches if int(m.group(1))==si)
  end=next((n.start() for n in matches if n.start()>m.start()),len(text))
  block=text[m.end():end];literals=list(LITERAL.finditer(block))
  if len(literals)!=1:raise ValueError('unexpected description controls')
  token='"""\n'+'\n'.join('\t'+line for line in lines)+'\n\t"""'
  lit=literals[0];new=block[:lit.start()]+token+block[lit.end():]
  if LITERAL.sub('TEXT',block)!=LITERAL.sub('TEXT',new):raise ValueError('description control mutation')
  text=text[:m.end()]+new+text[end:]
  details.append({'id':e['id'],'source':values[0],'text':translated,'line_cells':line_cells,
                  'source_binding':{f:e[f] for f in ['source_rom_sha256','source_payload_sha256','source_tpl_block_sha256']}})
 tpl=root/'descriptions.tpl';msg=root/'descriptions.msg';back=root/'descriptions_back.tpl';again=root/'descriptions_back.msg'
 tpl.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
 common=[str(p/'external/TextPet-v1.0.0/TextPet.exe'),'load-plugins',str(plugins),'game','exe4']
 for i,(src,fmt,dest,outfmt) in enumerate([(tpl,'tpl',msg,'bin'),(msg,'bin',back,'tpl'),(back,'tpl',again,'bin')]):
  run=subprocess.run(common+['read-text-archives',str(src),'-f',fmt,'write-text-archives',str(dest),'-f',outfmt],capture_output=True,timeout=60)
  (root/f'compile_{i}.log').write_bytes(run.stdout+run.stderr)
  if run.returncode or b'FATAL:' in run.stdout+run.stderr:raise ValueError('description compiler failure')
 data=msg.read_bytes();observed={si:vs for si,lang,vs,block in scripts(back.read_text(encoding='utf-8-sig'))}
 if data!=again.read_bytes() or any(observed[si]!=[text] for si,text in selected.items()):raise ValueError('description text/byte roundtrip failure')
 before,after=spans(old),spans(data)
 if len(before)!=len(after) or any(x!=y for i,(x,y) in enumerate(zip(before,after)) if i not in selected):raise ValueError('unselected description byte drift')
 bindings[key]=details
 report['profiles'][key]={'source_sha256':sha(source),'archive_offset':row['offset'],'source_population':256,
  'pointer_claims':row['pointers'],'compiled':msg.relative_to(p).as_posix(),'compiled_sha256':sha(data),
  'roundtrip_exact':True,'unselected_scripts_preserved':246,'details':details}
asset=p/'translations/menu_chip_descriptions_korean_draft.json'
asset.write_text(json.dumps({'schema':1,'state':'needs_review','build_status':'research-only; no consumer insertion approved by technical contract',
 'authoring_sha256':sha(author.read_bytes()),'entries':[{'id':d['id'],'source':d['source'],'text':d['text'],
 'source_bindings':{k:next(x['source_binding'] for x in entries if x['id']==d['id']) for k,entries in bindings.items()}} for d in bindings['blue_moon']]},ensure_ascii=False,indent=2),encoding='utf-8')
report['draft_sha256']=sha(asset.read_bytes());report['tool_sha256']=sha(Path(__file__).read_bytes())
(p/'analysis/menu_chip_description_analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS ten 9-visible-cell menu drafts, Galmuri7 coverage, both roundtrips, controls and 246 unselected scripts')
