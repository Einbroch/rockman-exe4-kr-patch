"""Replay the inspected kitchen correction, tutorial and caption probes."""
import argparse, subprocess, sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--key',choices=['blue_moon','red_sun'],required=True)
a=ap.parse_args()
origin=a.key+'_battle_caption_cold_01'
route=[
 ('route_02','none:1:30,r:6:180,'+','.join(['a:6:180']*6)),
 ('route_03','none:1:30,right:12:30,up:18:30,left:6:30,r:6:180,'+','.join(['a:6:180']*6)),
 ('route_04','none:1:30,right:24:30,up:26:30,left:20:30,r:6:180,'+','.join(['a:6:180']*6)),
 ('ready_01','none:1:30,'+','.join(['a:6:180']*34))]
def run(source,target,actions,probe):
 subprocess.run([sys.executable,str(p/'tools/continue_battle_route.py'),source,target,actions,'--probe',probe],check=True)
for name,actions in route:
 target=a.key+'_battle_caption_'+name
 run(origin,target,actions,'exectrace');origin=target
actions='none:1:30,right:6:45,right:6:45,right:6:45,right:6:45,left:6:45'
for name,probe in [('final_01','snapshot'),('calls_01','tilecalls')]:
 run(origin,a.key+'_battle_caption_'+name,actions,probe)
