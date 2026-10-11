"""Revision-bound tile consumer inventory. Indexed scope is a lower bound."""
import argparse,json,sys
from pathlib import Path
from collections import Counter
from analyze_project import PROFILES,sha,check_dependencies
from verify_tpi_index import parse_tpi
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'external/arm_debug_python'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
ap=argparse.ArgumentParser();ap.add_argument('--rom-dir',type=Path,required=True)
ap.add_argument('--font',type=Path,required=True);a=ap.parse_args()
p=Path(__file__).resolve().parents[1];check_dependencies(p)
inputs={sha(f.read_bytes()):f.read_bytes() for f in a.rom_dir.glob('*.gba')}
font=a.font.read_text(encoding='ascii');supply={}
for block in font.split('STARTCHAR ')[1:]:
 lines=block.splitlines();cp=int(next(x.split()[1] for x in lines if x.startswith('ENCODING ')))
 if not 0xac00<=cp<=0xd7a3:continue
 box=list(map(int,next(x for x in lines if x.startswith('BBX ')).split()[1:]))
 if box[0]+box[2]>8 or box[2]<0:raise ValueError('8-pixel cell overflow')
 supply[chr(cp)]=box
result={'schema':1,'scope':'exact indexed mmbn4s population; lower bound for whole game',
 'font_candidate':{'path':str(a.font.resolve()),'sha256':sha(a.font.read_bytes()),'syllables':len(supply),'status':'functional candidate; visual direction unapproved'},'profiles':{}}
for key,pr in PROFILES.items():
 r=inputs[pr['sha256']]
 entries=[json.loads(x) for x in (p/'analysis'/f'{key}_source_entries.jsonl').read_text(encoding='utf-8').splitlines()]
 selected=[e for e in entries if e['language']=='mmbn4s']
 if any(e['source_rom_sha256']!=sha(r) for e in selected):raise ValueError('source identity drift')
 rows=parse_tpi(p/'external/textpet-indexes'/pr['index'])
 listing=[]
 for start,size in [(0x21367c,0x64),(0x2136f0,0x26),(0x21382c,0x2a)]:
  listing += [{'address':i.address,'hex':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(r[start:start+size],0x03000000+start-0x20cf00)]
 # Derive the font pointer from the source caller's literal later; the blue
 # bank survey alone does not establish all consumers or the red bank.
 result['profiles'][key]={'source_sha256':sha(r),'indexed_archives':len(rows),
  'short_scripts':len(selected),'short_text_scripts':sum(bool(e['source_literals']) for e in selected),
  'literal_count':sum(len(e['source_literals']) for e in selected),'archive_count':len({e['archive_index'] for e in selected}),
  'command_f9_source_slot':{'offset':0x213650,'hex':r[0x213650:0x213654].hex()},
  'native_tile_code_sha256':sha(r[0x21367c:0x213916]),'observed_tile_disassembly':listing}
 (p/'analysis'/f'{key}_menu_sources.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in selected),encoding='utf-8')
result['representation']={'native_cell':[8,16],'bytes_per_glyph':64,
 'Galmuri9':'9-pixel ink does not fit without geometry changes',
 'Galmuri7':'8-pixel maximum ink; demand must be a subset of the 4363 available syllables',
 'missing_glyph_policy':'reject build; no blank replacement',
 'open':['title and other graphics','unindexed/external text','caller buffer capacities','name input','battle consumers','physical font palette and baseline','all decoding/lookahead paths']}
(p/'analysis/menu_consumer_survey.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:{n:v for n,v in x.items() if n in ('short_scripts','short_text_scripts','literal_count','archive_count')} for k,x in result['profiles'].items()}))
