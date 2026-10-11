"""One-time adoption of the bounded seven-row chip-library consumer."""
import json,sys
from pathlib import Path

p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'tools'))
from analyze_project import PROFILES,sha
from verify_tpi_index import parse_tpi

report_path=p/'analysis/library_consumer_analysis.json'
catalog_path=p/'analysis/chip_catalog_analysis.json'
report=json.loads(report_path.read_text(encoding='utf-8'))
catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
roms={sha(f.read_bytes()):f.read_bytes() for f in p.parents[1].glob('*.gba')}
fixed={
 'blue_moon':{'patch_offset':0x37f58,'continuation':0x08037f7b,'loop_anchor_offset':0x37efc,'loop_anchor_size':0x92},
 'red_sun':{'patch_offset':0x37f8c,'continuation':0x08037faf,'loop_anchor_offset':0x37f30,'loop_anchor_size':0x92},
}
profiles={}
for key,pr in PROFILES.items():
 source=roms[pr['sha256']];observed=report['profiles'][key];cat=catalog['profiles'][key]
 if observed['source_sha256']!=sha(source) or cat['source_sha256']!=sha(source):raise ValueError('source evidence drift')
 index=parse_tpi(p/'external/textpet-indexes'/pr['index']);f=fixed[key]
 patch=source[f['patch_offset']:f['patch_offset']+12]
 if patch.hex()!='4900415a401800f067f80ae0':raise ValueError('library hook window drift')
 roots={str(ai):{'offset':index[ai]['offset'],'address':0x08000000+index[ai]['offset'],'size':index[ai]['size'],'sha256':sha(source[index[ai]['offset']:index[ai]['offset']+index[ai]['size']])} for ai in (41,42)}
 profiles[key]={
  'source_sha256':sha(source),
  'loop_anchor':{'offset':f['loop_anchor_offset'],'size':f['loop_anchor_size'],'sha256':sha(source[f['loop_anchor_offset']:f['loop_anchor_offset']+f['loop_anchor_size']])},
  'hook':{'offset':f['patch_offset'],'expected_hex':patch.hex(),'continuation':f['continuation']},
  'native_parser_entry':observed['native_parser_entry']|1,
  'native_parser_size':observed['native_parser_bytes'],'native_parser_sha256':observed['native_parser_sha256'],
  'native_icon_loop':observed['native_icon_loop'],
  'native_font_residency':observed['native_font_residency'],
  'copy_helper_sha256':sha(source[0x98c:0x99a]),
  'roots':roots,
 }
spec={
 'schema':1,
 'scope':'private translated archive41/42 clones selected only by the standard seven-row library name loop; other consumers retain source roots',
 'font_sha256':'26321b2d780b859bfee7ca6cc561b50268efed139a852b470a589c0ba9901b24',
 'translation_asset_sha256':sha((p/'translations/chip_catalog_korean_draft.json').read_bytes()),
 'analysis_inputs':{'library_consumer_analysis':sha(report_path.read_bytes()),'chip_catalog_analysis':sha(catalog_path.read_bytes())},
 'profiles':profiles,
 'copy_helper':{'entry':0x0800098d,'offset':0x98c,'size':14,'abi':'r0 source,r1 destination,r2 bytes; wrapper preserves r0-r3 and returns; SVC 0x0B performs CpuSet'},
 'upper_row_base':0x02016600,'row_stride':32,'lower_row_gap':16,'rows':7,'cells':8,
 'cache':{'start':0x06006580,'end_exclusive':0x06007380,'reserved_end':0x06007400,'glyph_slots':56,'glyph_bytes':64,'top_tile_first':0x32c},
 'palette_tile_base':0xe200,'hangul_code_limit':11172,'missing_glyph_policy':'explicit self-stop; no replacement or blank fallback',
 'catalog_chip_ids':list(range(1,195))+list(range(201,291))+list(range(301,311)),
 'open':['294 Korean names need independent language review','font styling needs human approval','bounded runtime and device QA','RAM-special IDs >=311 and non-library consumers'],
}
out=p/'tools/specs/exe4_chip_library_v1.json'
out.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
print(out,sha(out.read_bytes()))
