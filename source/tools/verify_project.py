"""Verify frozen artifacts and bind separate runtime evidence by exact hash."""
import argparse
import json
from pathlib import Path
from analyze_project import PROFILES, sha, check_dependencies
from verify_tpi_index import lz77_decompress

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rom-dir',type=Path,required=True)
    ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args()
    p=args.project.resolve()
    check_dependencies(p)
    sources={sha(f.read_bytes()):f for f in args.rom_dir.glob('*.gba')}
    result={'schema':1,'claim':'analysis and non-distribution opening development only','release_status':'not_ready','artifacts':[],'runtime':[],'open_conditions':['full Hangul code space','separate tile-font/menu consumers','unindexed text and continuation populations','whole-game translation/review/layout','whole-game and device QA']}
    for key,profile in PROFILES.items():
        source_path=sources[profile['sha256']]
        source=source_path.read_bytes()
        analysis=json.loads((p/'analysis'/f'{key}_analysis.json').read_text(encoding='utf-8'))
        if analysis['roundtrip_passed']!=793 or analysis['roundtrip_mismatches']:raise ValueError('roundtrip gate failed')
        for suffix in ['opening_visibility_poc','opening_korean_development']:
            out=p/'poc/output'/f'{key}_{suffix}.gba'
            target=out.read_bytes()
            manifest=json.loads(out.with_suffix('.json').read_text(encoding='utf-8'))
            if manifest['policy']!='development/PoC; NON-DISTRIBUTION' or manifest['source_sha256']!=sha(source) or manifest['output_sha256']!=sha(target):raise ValueError('artifact identity/policy drift')
            if len(target)!=0x1000000:raise ValueError('ROM size mismatch')
            allowed=bytearray(len(source));intervals=[]
            fontbase=int(manifest['font_base'],16);widthbase=int(manifest['width_base'],16)
            for write in manifest['expected_writes']:
                start,size=write['offset'],write['size'];end=start+size
                intervals.append((start,end))
                if sha(target[start:end])!=write['final_sha256']:raise ValueError('final write mismatch')
                if start<len(source):
                    if end>len(source) or sha(source[start:end])!=write['expected_sha256']:raise ValueError('expected source mismatch')
                    allowed[start:end]=b'\x01'*size
            intervals.sort()
            if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):raise ValueError('write overlap')
            if any(a!=b and not allowed[i] for i,(a,b) in enumerate(zip(source,target))):raise ValueError('unexplained final diff')
            palette_at=fontbase+441*96
            if target[palette_at:palette_at+0x100]!=source[palette_at:palette_at+0x100]:raise ValueError('protected palette changed')
            decoded,consumed=lz77_decompress(target,len(source))
            if sha(decoded)!=manifest['archive_payload_sha256']:raise ValueError('relocated payload mismatch')
            if any(b!=255 for b in target[len(source)+consumed:]):raise ValueError('unexplained ROM tail')
            for ch,index in manifest['mapping'].items():
                if index>=441:raise ValueError('font index invades protected palette')
                record=target[fontbase+index*96:fontbase+(index+1)*96]
                pixels=[v for b in record for v in (b&15,b>>4)]
                if set(pixels)-{1,2,3} or 3 not in pixels:raise ValueError('invalid/empty glyph '+ch)
                if int.from_bytes(target[widthbase+4*index:widthbase+4*index+4],'little')!=12:raise ValueError('advance mismatch')
            result['artifacts'].append({'profile':key,'file':out.relative_to(p).as_posix(),'sha256':sha(target),'status':'PASS (bench)','selected_scripts':len(manifest['selected_entries']),'glyphs':manifest['glyph_count'],'protected_palette_preserved':True})
        for name in [key+'_korean_opening',key+'_opening_final',key+'_opening_end',key+'_opening_exit']:
            root=p/'analysis/runtime'/name
            report_path=root/'result.json'
            if not report_path.exists():
                result['runtime'].append({'run':name,'status':'PENDING_RUNTIME'});continue
            runtime=json.loads(report_path.read_text(encoding='utf-8'))
            for file,digest in runtime['artifacts'].items():
                if sha((root/file).read_bytes())!=digest:raise ValueError('runtime artifact drift '+name+'/'+file)
            expected=next(a for a in result['artifacts'] if a['profile']==key and ('visibility' in a['file'])==(name.endswith('_korean_opening')))
            if runtime['rom_sha256']!=expected['sha256']:raise ValueError('runtime/build attribution mismatch')
            if runtime.get('state_origin'):
                origin_path=Path(runtime['state_origin']).resolve()
                if not origin_path.is_relative_to(p/'analysis/runtime'):raise ValueError('foreign state receipt')
                origin=json.loads(origin_path.read_text(encoding='utf-8'))
                if not origin['complete'] or origin['rom_sha256']!=runtime['rom_sha256'] or origin['emulator_components']!=runtime['emulator_components']:raise ValueError('state origin attribution mismatch')
                state_sha=runtime['state_sha256']
                if state_sha!=origin['artifacts']['checkpoint.mss'] or state_sha!=runtime['artifacts']['input.mss'] or state_sha!=sha((origin_path.parent/'checkpoint.mss').read_bytes()):raise ValueError('state lineage mismatch')
            status='completed diagnostic; visual QA recorded separately' if runtime['complete'] and runtime['return_code']==0 and not runtime['audio_enabled'] else 'PARTIAL_RUNTIME'
            if name.endswith(('_opening_final','_opening_end','_opening_exit')) and len(runtime.get('loaded_rom_guards',[]))<3:raise ValueError('missing actual loaded-ROM guards')
            result['runtime'].append({'run':name,'status':status,'rom_sha256':runtime['rom_sha256'],'captured':runtime['steps_captured'],'expected':runtime['steps_expected'],'audio_enabled':runtime['audio_enabled'],'state_origin':runtime.get('state_origin')})
    if any(sources[h].read_bytes() and sha(sources[h].read_bytes())!=h for h in sources):raise ValueError('source changed during verification')
    (p/'analysis/project_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS (bench):',len(result['artifacts']),'development ROMs; source hashes unchanged; palette preserved')
    for run in result['runtime']:print(run['run'],run['status'])
    return result
if __name__=='__main__':main()
