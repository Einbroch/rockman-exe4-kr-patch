"""Source-specific adoption survey; not whole-game decoder completeness."""
import argparse,json
from pathlib import Path
from analyze_project import PROFILES,sha
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True)
args=ap.parse_args();p=Path(__file__).resolve().parents[1]
inputs={sha(f.read_bytes()):f.read_bytes() for f in args.rom_dir.glob('*.gba')}
blue=inputs[PROFILES['blue_moon']['sha256']]
def unique(data,needle):
    at=data.find(needle)
    if at<0 or data.find(needle,at+1)>=0:raise ValueError('source anchor not unique')
    return at
def ldr_literal(data,at):
    op=int.from_bytes(data[at:at+2],'little')
    if op&0xf800!=0x4800:raise ValueError('not Thumb PC-relative LDR')
    pool=((at+4)&~3)+(op&255)*4
    return pool,int.from_bytes(data[pool:pool+4],'little')
report={'schema':1,'scope':'normal dialogue draw, cumulative-width scan and observed shared tile renderer only','encoding_candidate':'F9 FC + uint16 little endian Hangul syllable index (U+AC00 base); NON-DISTRIBUTION until consumer/collision population closed','profiles':{}}
for key,profile in PROFILES.items():
    r=inputs[profile['sha256']]
    main=unique(r,blue[0x4df90:0x4dfa0])
    normal_pool,normal_table=ldr_literal(r,main+0x6c)
    width_pool,width_table=ldr_literal(r,main+0x12a)
    renderer=unique(r,blue[0x213948:0x213974])
    font_pool,font_address=ldr_literal(r,renderer+0x22)
    advance_pool,advance_address=ldr_literal(r,renderer+0x2a)
    tile=unique(r,blue[0x21367c:0x213694])
    tile_pool,tile_table=ldr_literal(r,tile+0x2a)
    def slot(table):
        at=(table&0x1ffffff)+(0xf9-0xe5)*4
        # Tile table points inside the copied source bank, not directly into ROM.
        if table<0x08000000:at=tile+(table-(0x0300677c))+(0xf9-0xe5)*4
        return {'offset':at,'expected_hex':r[at:at+4].hex(),'handler_address':int.from_bytes(r[at:at+4],'little')}
    functions={name:0x08000000+unique(r,blue[at:at+12]) for name,at in {'flag_test':0x4e534,'flag_set':0x4e51c,'glyph_bookkeeping':0x4e770}.items()}
    report['profiles'][key]={'source_sha256':sha(r),'main_dispatch_offset':main,'main_dispatch_expected_sha256':sha(r[main:main+0x18a]),'normal_f9_slot':slot(normal_table),'width_f9_slot':slot(width_table),'tile_f9_slot':slot(tile_table),'renderer_offset':renderer,'renderer_runtime_address':0x03006a48,'font_literal':{'offset':font_pool,'expected_address':font_address},'advance_literal':{'offset':advance_pool,'expected_address':advance_address},'main_continuation_address':0x08000000+main+0xde,'functions':functions,'sound_address':0x08000558}
    # The dispatch routines and helpers are identified, not just a global delta.
    for name,addr in report['profiles'][key]['functions'].items():
        at=addr-0x08000000
        blueat={'flag_test':0x4e534,'flag_set':0x4e51c,'glyph_bookkeeping':0x4e770}[name]
        if r[at:at+12]!=blue[blueat:blueat+12]:raise ValueError('helper source anchor drift '+name)
report['rejected_candidates']=['IWRAM 0x03002A66 and 0x0300488A E4/E5 immediate matches are image/palette data in the captured state, not decoder evidence.','Galmuri9 has 9-pixel Hangul ink and cannot be losslessly fitted to the observed 8-pixel tile cell.','Galmuri7 supplies 4363 Hangul syllables, so it cannot provide the full 11172 repertoire without a separate declared representation.']
(p/'analysis/expansion_site_survey.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report['profiles'],indent=2))
