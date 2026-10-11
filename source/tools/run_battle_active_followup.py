"""Test queued-chip consumption, clearing, Custom Screen reentry and second name."""
import argparse,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True);a=ap.parse_args()
key=a.key;origin=key+'_battle_active_verify_survey_05'
def run(source,target,actions,probe):
 subprocess.run([sys.executable,str(p/'tools/continue_battle_route.py'),source,target,actions,'--probe',probe],check=True)
run(origin,key+'_battle_active_calls_01','none:1:30','tilecalls')
for kind in ['use','reentry','second']:
 template=p/'analysis/runtime'/f'blue_moon_battle_active_{kind}_survey_01/result.json'
 r=json.loads(template.read_text(encoding='utf-8'))
 if not r['complete'] or r['return_code']:raise ValueError('invalid normal-input template')
 target=key+'_battle_active_'+kind+'_01';run(origin,target,r['actions'],'snapshot');origin=target
run(origin,key+'_battle_active_calls_02','none:1:30','tilecalls')
