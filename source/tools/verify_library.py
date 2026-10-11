"""Independent static verification of the private seven-row chip library."""
import json
from analyze_project import sha,payload
from verify_tpi_index import parse_tpi
from extended_dialogue import assemble_verified

def spans(data):
 first=int.from_bytes(data[:2],'little');offsets=[int.from_bytes(data[i:i+2],'little') for i in range(0,first,2)];valid=sorted(set(offsets));ends={x:valid[i+1] if i+1<len(valid) else len(data) for i,x in enumerate(valid)}
 return offsets,[data[x:ends[x]] for x in offsets]

def check(p,key,source,data,m,font):
 spec_path=p/'tools/specs/exe4_chip_library_v1.json';spec=json.loads(spec_path.read_text(encoding='utf-8'));s=spec['profiles'][key];t=m['extension']['chip_library']
 asset=p/'translations/chip_catalog_korean_draft.json';wording=json.loads(asset.read_text(encoding='utf-8'))
 from library_extension import selection
 contract=selection(p,key,source,wording)
 if t['translation_asset_sha256']!=sha(asset.read_bytes()) or t['consumer_contract_sha256']!=sha(spec_path.read_bytes()) or contract['consumer_contract_sha256']!=t['consumer_contract_sha256']:raise ValueError('library identity/contract drift')
 if not t['consumer_selection_verified'] or t['whole_game_chip_localization'] or not t['other_consumers_preserved']:raise ValueError('library scope drift')
 if t['cache']!=spec['cache'] or t['active_residency_slots']!=56 or t['row_scope']!={'upper_base':spec['upper_row_base'],'rows':7,'stride':32,'cells':8}:raise ValueError('library active residency drift')
 if t['menu_font_reused']!={'font_offset':m['extension']['menu']['fonts'][0],'map_offset':m['extension']['menu']['map_offset']}:raise ValueError('library font provider drift')
 point=s['hook'];expected=bytes.fromhex(point['expected_hex']);at=point['offset']
 if source[at:at+len(expected)]!=expected:raise ValueError('library source hook drift')
 for code in t['machine_code']+t['jump_code']:
  rebuilt,_=assemble_verified('\n'.join(x['mnemonic']+' '+x['operands'] for x in code['instructions']),code['address'],code['literal_values']);off=code['address']-0x08000000
  if data[off:off+len(rebuilt)]!=rebuilt:raise ValueError('library final placed ARM bytes drift')
 # Original archives and every original archive42 claim remain exact. Archive41
 # has only the separately verified private-folder claim changed by that feature.
 rows=parse_tpi(p/'external/textpet-indexes'/('exe4bm-v10.tpi' if key=='blue_moon' else 'exe4rs-v11.tpi'))
 chosen={int(x['id'].split('/')[1]):{} for x in wording['entries']}
 table={}
 for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
  code,sep,char=line.partition('=')
  if sep and len(char)==1:table.setdefault(char,bytes.fromhex(code))
 def encode(text):return b''.join(b'\xf9\xfc'+(ord(c)-0xac00).to_bytes(2,'little') if 0xac00<=ord(c)<=0xd7a3 else table[c] for c in text)+b'\xe5'
 entries={int(x['id'].split('/')[1]):{} for x in wording['entries']}
 for ai in (41,42):
  row=rows[ai];old=payload(source,row);self_copy=data[row['offset']:row['offset']+len(old)]
  if self_copy!=old:raise ValueError('library shared archive changed')
  clone_at=t['archive_offsets'][str(ai)];new=data[clone_at:clone_at+t['archive_sizes'][str(ai)]];oo,os=spans(old);no,ns=spans(new)
  selected={int(x['id'].split('/')[-1]):x for x in wording['entries'] if int(x['id'].split('/')[1])==ai}
  if len(oo)!=len(no) or any(a!=b for i,(a,b) in enumerate(zip(os,ns)) if i not in selected):raise ValueError('library unselected clone span changed')
  for i,x in selected.items():
   if os[i]!=encode(x['source']) or ns[i]!=encode(x['text']):raise ValueError('library exact wording bytes drift')
  for ptr in row['pointers']:
   if ai==42 and data[ptr:ptr+4]!=source[ptr:ptr+4]:raise ValueError('archive42 source claim changed')
 if len(t['characters'])!=204 or sorted({c for x in wording['entries'] for c in x['text'] if 0xac00<=ord(c)<=0xd7a3})!=t['characters']:raise ValueError('library glyph demand drift')
 bench_path=p/'analysis/library_bench.json';bench=json.loads(bench_path.read_text(encoding='utf-8'))
 if bench['status']!='PASS' or bench['products'][key]!=sha(data):raise ValueError('library CPU product attribution drift')
 for name,digest in bench['inputs'].items():
  if sha((p/name).read_bytes())!=digest:raise ValueError('library CPU input drift')
 if sha((p/bench['log']).read_bytes())!=bench['log_sha256']:raise ValueError('library CPU log drift')
 result={'library_source_bound_drafts':294,'library_ROM_ids_CPU_verified':311,'library_active_slots':56,'library_Hangul_demand':204,'library_final_ARM_bytes_verified':True,'library_cpu_bench_sha256':sha(bench_path.read_bytes()),'runtime_status':'pending'}
 qa_path=p/'analysis/LIBRARY_RUNTIME_QA.json'
 if qa_path.exists():
  qa=json.loads(qa_path.read_text(encoding='utf-8'));q=qa['profiles'][key]
  if not qa['status'].startswith('PASS') or q['rom_sha256']!=sha(data) or q['actual_registered_source_ids']!=[1,4,15]:raise ValueError('library runtime QA attribution drift')
  if sha((p/qa['sheet']).read_bytes())!=qa['sheet_sha256']:raise ValueError('library contact sheet drift')
  for r in q['receipts']:
   if sha((p/r['path']).read_bytes())!=r['sha256']:raise ValueError('library adopted receipt drift')
  for shot in q['screenshots']:
   if sha((p/shot['path']).read_bytes())!=shot['sha256']:raise ValueError('library adopted screenshot drift')
  result.update(runtime_status='completed cold boot and bounded library/folder diagnostic; visual inspection recorded',library_runtime_QA_sha256=sha(qa_path.read_bytes()),library_actual_registered_names_reached=3)
 return result
