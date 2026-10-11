"""Independent private chip clone, final ARM bytes and bounded runtime checks."""
import json
from analyze_project import sha,payload
from verify_tpi_index import parse_tpi
from extended_dialogue import assemble_verified
from chip_extension import selection,folder_characters
def check(p,key,source,data,m,font,static_only=False):
 t=m['extension']['chip_folder'];spec=json.loads((p/'tools/specs/exe4_chip_folder_v2.json').read_text(encoding='utf-8'));s=spec['profiles'][key]
 asset=p/'translations/chip_folder_korean.json';w=json.loads(asset.read_text(encoding='utf-8'));contract=selection(p,key,source,w)
 if t['translation_asset_sha256']!=sha(asset.read_bytes()) or t['consumer_contract_sha256']!=contract['consumer_contract_sha256'] or t['whole_game_chip_localization']:raise ValueError('chip identity/scope drift')
 if any(not t[x] for x in ['source_bound','control_skeleton_preserved','unselected_script_bytes_preserved','codec_byte_roundtrip','wording_reextracted_exactly','consumer_selection_verified']):raise ValueError('chip compilation gates absent')
 chars=folder_characters(p,spec)
 if chars!=t['characters']:raise ValueError('folder syllable demand drift')
 # Every glyph record must equal the menu bank's record for the same syllable,
 # a bank verify_menu.check derives from the BDF independently.
 menu=m['extension']['menu']
 for i,c in enumerate(chars):
  at=t['font_offset']+i*64;original=menu['fonts'][0]+menu['characters'].index(c)*64
  if data[at:at+64]!=data[original:original+64]:raise ValueError('folder glyph differs from the menu bank')
 for cp in range(11172):
  c=chr(0xac00+cp);at=t['ordinal_offset']+cp*2;want=chars.index(c) if c in chars else 65535
  if int.from_bytes(data[at:at+2],'little')!=want:raise ValueError('syllable-to-glyph table drift')
 tiles=spec['slot_tiles']
 if t['slots']!=len(tiles) or data[t['slot_tiles_offset']:t['slot_tiles_offset']+2*len(tiles)]!=b''.join(x.to_bytes(2,'little') for x in tiles):raise ValueError('cache slot table drift')
 keep={c for a,b in spec['native_keep'] for c in range(a,b)}
 if any(512+2*c in tiles or 513+2*c in tiles for c in keep):raise ValueError('a cache slot covers a native glyph the folder still loads')
 for code in t['machine_code']+t['jump_code']:
  rebuilt,_=assemble_verified('\n'.join(x['mnemonic']+' '+x['operands'] for x in code['instructions']),code['address'],code['literal_values']);at=code['address']-0x08000000
  size=len(rebuilt) if code['literal_values'] else code['code_bytes']
  if data[at:at+size]!=rebuilt[:size]:raise ValueError('chip final placed ARM bytes drift')
 rows=parse_tpi(p/'external/textpet-indexes'/('exe4bm-v10.tpi' if key=='blue_moon' else 'exe4rs-v11.tpi'))
 table={}
 for line in (p/'external/textpet-plugins/exe4-utf8.tbl').read_text(encoding='utf-8-sig').splitlines():
  code,sep,c=line.partition('=')
  if sep and len(c)==1:table.setdefault(c,bytes.fromhex(code))
 def encode(text):return b''.join(b'\xf9\xfc'+(ord(c)-0xac00).to_bytes(2,'little') if 0xac00<=ord(c)<=0xd7a3 else table[c] for c in text)+b'\xe5'
 def spans(d):
  count=int.from_bytes(d[:2],'little')//2;o=[int.from_bytes(d[i*2:i*2+2],'little') for i in range(count)];v=sorted(set(o));ends={x:v[i+1] if i+1<len(v) else len(d) for i,x in enumerate(v)}
  return o,[d[x:ends[x]] for x in o]
 # Both archives 0x0802F068 reads: archive41 (ids 0..255) and archive42 (256..310).
 for ai,pointer,clone_at,clone_size in [(41,s['clone_pointer'],t['archive_offset'],t['archive_size']),(42,s['second_clone']['pointer'],t['archive42_offset'],t['archive42_size'])]:
  row=rows[ai];old=payload(source,row);new=data[clone_at:clone_at+clone_size]
  if data[row['offset']:row['offset']+len(old)]!=old:raise ValueError('shared chip archive changed')
  for ptr in row['pointers']:
   expected=0x08000000+(clone_at if ptr==pointer else row['offset'])
   if int.from_bytes(data[ptr:ptr+4],'little')!=expected:raise ValueError('chip claim isolation drift')
  oo,os=spans(old);no,ns=spans(new);chosen={int(x['id'].split('/')[-1]):x for x in w['entries'] if int(x['id'].split('/')[1])==ai}
  if len(oo)!=len(no) or any(a!=b for i,(a,b) in enumerate(zip(os,ns)) if i not in chosen):raise ValueError('unselected private clone spans changed')
  for id,x in chosen.items():
   if os[id]!=encode(x['source']) or ns[id]!=encode(x['text']):raise ValueError('chip exact wording bytes mismatch')
 return {'chip_names_source_bound':len(w['entries']),'chip_glyphs_verified':len(chars),'chip_cache_slots':len(tiles),'chip_private_claims_relocated':2,'chip_other_claims_preserved':len(s['other_archive_claims_preserved']),'chip_arm_final_bytes_verified':True,'runtime_status':'pending; see analysis/runtime/user_save_folder_v2_*'}
