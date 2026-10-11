import argparse
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
ap=argparse.ArgumentParser()
ap.add_argument('--ram',type=Path,required=True)
ap.add_argument('--start',type=lambda x:int(x,0),required=True)
ap.add_argument('--length',type=lambda x:int(x,0),default=0x100)
args=ap.parse_args()
data=args.ram.read_bytes()
offset=args.start-0x03000000
if offset<0 or offset+args.length>len(data):raise SystemExit('range outside IWRAM')
for inst in Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(data[offset:offset+args.length],args.start):
    print(f'{inst.address:08X} {inst.bytes.hex():12} {inst.mnemonic:8} {inst.op_str}')
