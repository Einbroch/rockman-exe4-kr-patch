#!/usr/bin/env python3
"""Run one muted Mesen 2 segment against a pinned GBA ROM and capture evidence.

Only normal controller input is replayed; no game RAM, script, position or
progress flag is written.  The ROM and emulator are pinned by SHA-256 so a
result can never be attributed to a build it did not come from.
Validated same-ROM diagnostic checkpoints can continue a previous input run.

Probes are opt-in Lua fragments:

  none      just play and screenshot
  fontread  count CPU reads that land inside a declared glyph bank, bucketed by
            record index, so the byte-to-glyph mapping can be read off against
            text whose bytes are already known
  ramdump   dump IWRAM and EWRAM at every capture point, plus the emulator's
            memory-type table, so an encoded text string can be located in the
            buffer the renderer is actually parsing
  textread  record the program counter of every read of a chosen address range,
            bucketed by PC, to find the routine that parses the text stream
  statehash at every capture point, record the CPU registers and a hash of each
            memory region, so two runs can be compared on machine state
  snapshot  same, but dump every memory region in full so a difference can be
            located to the byte.  This is the deterministic regression capture:
            two runs of the same ROM produce identical dumps, while
            emu.takeScreenshot does not.
  exectrace put an execution breakpoint on each --trace-pc and record how often
            it fires, on which frame it first fired, and the registers at that
            first hit.  A routine that never fires across a route is not proof
            of dead code, but a routine that fires tells you which screen owns
            it and what it was handed.

--capture-pc anchors every capture to a chosen program counter instead of a
frame boundary.  A frame boundary catches the CPU wherever it happens to be, so
two builds whose code differs in length land a cycle apart and a scratch byte
can differ for reasons that are not behavioural.  Waiting for a fixed PC puts
both runs on the same instruction.  0x0800054C, the entry of the routine that
busy-waits on a hardware status bit, is a good anchor for EXE3.
"""

from __future__ import annotations

import argparse
import os
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

GBA_BUTTONS = {"a", "b", "l", "r", "start", "select", "up", "down", "left", "right"}

LUA_TEMPLATE = r'''
local root=ROOT
local actions=ACTIONS
local captureAt=CAPTUREAT
local capturePc=CAPTUREPC
local total=TOTAL
local frame=0
local final=false
local ready=STATEREADY
local function write(name,data)
 local f=assert(io.open(root..'/'..name,'wb'));f:write(data);f:close()
end
LOADGUARD
local fontHits={}
local fontTotal=0
local fontFirst={}
local fontPcs={}
local FONT_BASE=FONTBASE
local FONT_END=FONTEND
local FONT_STRIDE=FONTSTRIDE
local PROBE=PROBENAME
local WATCH_START=WATCHSTART
local WATCH_END=WATCHEND
local TRACE_PCS=TRACEPCS
local traceHits={}
local traceFirst={}
local traceRegs={}
local tileCalls={}
local chipCalls={}
local vramSites={}
local vramTiles={}
local copyCalls={}
if PROBE=='vramwrites' or PROBE=='chipqa' or PROBE=='bgqa' then
 emu.addMemoryCallback(function(address,value)
  local pc=emu.getState()['cpu.r15'];local key=string.format('%08X',pc)
  local s=vramSites[key]
  if s==nil then s={hits=0,min=address,max=address,first=frame};vramSites[key]=s end
  s.hits=s.hits+1;s.min=math.min(s.min,address);s.max=math.max(s.max,address)
  local tile=math.floor((address-0x06000000)/32);vramTiles[tile]=(vramTiles[tile] or 0)+1
 end,emu.callbackType.write,WATCH_START>0 and WATCH_START or 0x06000000,WATCH_END>0 and WATCH_END or 0x06017FFF)
 for _,pc in ipairs({0x08000876,0x0800098C,0x080009A0}) do
  emu.addMemoryCallback(function()
   local st=emu.getState();local src=st['cpu.r0'];local dest=st['cpu.r1'];local size=st['cpu.r2']
   if dest>=0x06000000 and dest<0x06018000 then
    local key=string.format('%08X:%08X:%08X:%08X',pc,src,dest,size)
    local c=copyCalls[key]
    if c then c.hits=c.hits+1 else copyCalls[key]={pc=pc,src=src,dest=dest,size=size,hits=1,first=frame,caller=st['cpu.r14']} end
   end
  end,emu.callbackType.exec,pc,pc)
 end
end
local function dumpVram(name)
 local sites={};local tiles={};local copies={}
 for pc,s in pairs(vramSites) do sites[#sites+1]=string.format('{"pc":"0x%s","hits":%d,"min":%d,"max":%d,"first_frame":%d}',pc,s.hits,s.min,s.max,s.first) end
 for tile,count in pairs(vramTiles) do tiles[#tiles+1]=string.format('{"tile":%d,"hits":%d}',tile,count) end
 for _,c in pairs(copyCalls) do copies[#copies+1]=string.format('{"pc":%d,"source":%d,"destination":%d,"bytes":%d,"hits":%d,"first_frame":%d,"caller_lr":%d}',c.pc,c.src,c.dest,c.size,c.hits,c.first,c.caller) end
 write(name..'_vramwrites.json','{"sites":['..table.concat(sites,',')..'],"tiles":['..table.concat(tiles,',')..'],"copies":['..table.concat(copies,',')..']}')
 local io={}
 for i=0,95 do io[#io+1]=string.char(emu.read(0x04000000+i,emu.memType.gbaMemory)) end
 write(name..'_display_io.bin',table.concat(io))
end
if PROBE=='chipcalls' or PROBE=='chipqa' then
 for _,pc in ipairs(TRACE_PCS) do
  emu.addMemoryCallback(function()
   local st=emu.getState()
   local archive=st['cpu.r0'];local id=st['cpu.r1']
   local dest=st['cpu.r2'];local lower=st['cpu.r3'];local base=st['cpu.r6']
   local key=string.format('%08X:%08X:%d:%08X:%08X:%d',pc,archive,id,dest,lower,base)
   local item=chipCalls[key]
   if item then item.hits=item.hits+1 else
    local offset=emu.read(archive+id*2,emu.memType.gbaMemory)+256*emu.read(archive+id*2+1,emu.memType.gbaMemory)
    local stream=archive+offset;local bytes={}
    for i=0,31 do bytes[#bytes+1]=string.format('%02X',emu.read(stream+i,emu.memType.gbaMemory)) end
    chipCalls[key]={hits=1,first=frame,pc=pc,archive=archive,id=id,dest=dest,lower=lower,base=base,stream=stream,caller=st['cpu.r14'],hex=table.concat(bytes)}
   end
  end,emu.callbackType.exec,pc,pc)
 end
end
local function dumpChip(name)
 local parts={}
 for _,s in pairs(chipCalls) do
  parts[#parts+1]=string.format('{"hits":%d,"first_frame":%d,"pc":%d,"archive":%d,"script_id":%d,"destination":%d,"lower_row":%d,"tile_base":%d,"stream":%d,"caller_lr":%d,"stream_prefix_hex":"%s"}',s.hits,s.first,s.pc,s.archive,s.id,s.dest,s.lower,s.base,s.stream,s.caller,s.hex)
 end
 write(name,'{"calls":['..table.concat(parts,',')..']}')
end
local bgCalls={}
if PROBE=='bgqa' then
 for _,pc in ipairs(TRACE_PCS) do
  emu.addMemoryCallback(function()
   local st=emu.getState();local stream=st['cpu.r0'];local dest=st['cpu.r2'];local lower=st['cpu.r3'];local base=st['cpu.r6']
   local key=string.format('%08X:%08X:%08X:%08X:%d',pc,stream,dest,lower,base)
   local item=bgCalls[key]
   if item then item.hits=item.hits+1 else
    local bytes={};for i=0,31 do bytes[#bytes+1]=string.format('%02X',emu.read(stream+i,emu.memType.gbaMemory)) end
    bgCalls[key]={hits=1,first=frame,pc=pc,stream=stream,dest=dest,lower=lower,base=base,caller=st['cpu.r14'],hex=table.concat(bytes)}
   end
  end,emu.callbackType.exec,pc,pc)
 end
end
local function dumpBg(name)
 local parts={}
 for _,s in pairs(bgCalls) do
  parts[#parts+1]=string.format('{"hits":%d,"first_frame":%d,"pc":%d,"stream":%d,"destination":%d,"lower_row":%d,"tile_base_palette":%d,"caller_lr":%d,"stream_prefix_hex":"%s"}',s.hits,s.first,s.pc,s.stream,s.dest,s.lower,s.base,s.caller,s.hex)
 end
 write(name,'{"calls":['..table.concat(parts,',')..']}')
end
if PROBE=='tilecalls' then
 emu.addMemoryCallback(function()
  local st=emu.getState()
  local stream=st['cpu.r0'];local dest=st['cpu.r2'];local font=st['cpu.r6']
  local width=st['cpu.r4'];local height=st['cpu.r5'];local tint=st['cpu.r7']
  local key=string.format('%08X:%08X:%08X:%d:%d:%d',stream,dest,font,width,height,tint)
  local item=tileCalls[key]
  if item then item.hits=item.hits+1 else
   local bytes={}
   for i=0,31 do bytes[#bytes+1]=string.format('%02X',emu.read(stream+i,emu.memType.gbaMemory)) end
   tileCalls[key]={hits=1,first=frame,stream=stream,dest=dest,font=font,width=width,height=height,tint=tint,caller=st['cpu.r14'],hex=table.concat(bytes)}
  end
 end,emu.callbackType.exec,0x0300677C,0x0300677C)
end
local function dumpTile(name)
 local parts={}
 for _,s in pairs(tileCalls) do
  parts[#parts+1]=string.format('{"hits":%d,"first_frame":%d,"stream":%d,"destination":%d,"font":%d,"width":%d,"height":%d,"tint":%d,"caller_lr":%d,"stream_prefix_hex":"%s"}',s.hits,s.first,s.stream,s.dest,s.font,s.width,s.height,s.tint,s.caller,s.hex)
 end
 write(name,'{"calls":['..table.concat(parts,',')..']}')
end
if PROBE=='exectrace' then
 for _,pc in ipairs(TRACE_PCS) do
  local key=string.format('%08X',pc)
  traceHits[key]=0
  emu.addMemoryCallback(function()
   traceHits[key]=traceHits[key]+1
   if traceFirst[key]==nil then
    traceFirst[key]=frame
    local st=emu.getState()
    local parts={}
    for _,rn in ipairs({'cpu.r0','cpu.r1','cpu.r2','cpu.r3','cpu.r4',
                        'cpu.r5','cpu.r6','cpu.r7','cpu.r8','cpu.r9',
                        'cpu.r10','cpu.r11','cpu.r12','cpu.r13','cpu.r14'}) do
     parts[#parts+1]=string.format('"%s":%d',rn,st[rn] or -1)
    end
    traceRegs[key]='{'..table.concat(parts,',')..'}'
   end
  end,emu.callbackType.exec,pc,pc)
 end
end
local function dumpTrace(name)
 local parts={}
 for key,count in pairs(traceHits) do
  parts[#parts+1]=string.format('{"pc":"0x%s","hits":%d,"first_frame":%d,"first_regs":%s}',
    key,count,traceFirst[key] or -1,traceRegs[key] or 'null')
 end
 write(name,'{"sites":['..table.concat(parts,',')..']}')
end
if PROBE=='fontread' or PROBE=='tilecalls' then
 emu.addMemoryCallback(function(address)
  local idx=math.floor((address-FONT_BASE)/FONT_STRIDE)
  fontHits[idx]=(fontHits[idx] or 0)+1
  if fontFirst[idx]==nil then fontFirst[idx]=frame end
  fontTotal=fontTotal+1
  local pc=emu.getState()['cpu.r15']
  local key=string.format('%08X',pc)
  local s=fontPcs[key]
  if s==nil then s={reads=0,first=address,min=address,max=address};fontPcs[key]=s end
  s.reads=s.reads+1;s.min=math.min(s.min,address);s.max=math.max(s.max,address)
 end,emu.callbackType.read,FONT_BASE,FONT_END-1)
end
local pcHits={}
local pcValue={}
local pcAddr={}
local pcTotal=0
if PROBE=='textread' then
 emu.addMemoryCallback(function(address,value)
  local pc=emu.getState()['cpu.r15']
  local key=string.format('%08X',pc)
  pcHits[key]=(pcHits[key] or 0)+1
  pcTotal=pcTotal+1
  if pcValue[key]==nil then
   pcValue[key]=value or -1
   pcAddr[key]=address
  end
 end,emu.callbackType.read,WATCH_START,WATCH_END)
end
local function dumpPc(name)
 local parts={}
 for key,count in pairs(pcHits) do
  parts[#parts+1]=string.format('{"pc":"0x%s","reads":%d,"first_value":%d,"first_address":%d}',
    key,count,pcValue[key],pcAddr[key])
 end
 write(name,string.format('{"total_reads":%d,"watch_start":%d,"watch_end":%d,"sites":[%s]}',
   pcTotal,WATCH_START,WATCH_END,table.concat(parts,',')))
end
local REGIONS={
 {'gbaIntWorkRam',0x8000},{'gbaExtWorkRam',0x40000},
 {'gbaVideoRam',0x18000},{'gbaPaletteRam',0x400},{'gbaSpriteRam',0x400}}
local function dumpRam(name)
 for _,r in ipairs(REGIONS) do
  local mt=emu.memType[r[1]]
  if mt~=nil then
   local data={}
   for i=0,r[2]-1 do data[#data+1]=string.char(emu.read(i,mt)) end
   write(name..'_'..r[1]..'.bin',table.concat(data))
  end
 end
end
local function fnv(data)
 local h=2166136261
 for i=1,#data do
  h=h ~ string.byte(data,i)
  h=(h*16777619) % 4294967296
 end
 return h
end
local function regionHash(kind,size)
 local mt=emu.memType[kind]
 if mt==nil then return -1 end
 local parts={}
 for i=0,size-1 do parts[#parts+1]=string.char(emu.read(i,mt)) end
 return fnv(table.concat(parts))
end
local function dumpState(name)
 local cpu=emu.getState()
 local keys={}
 for k,v in pairs(cpu) do
  if type(v)=='number' then keys[#keys+1]=string.format('"%s":%d',k,v) end
 end
 table.sort(keys)
 local regions={
  {'gbaIntWorkRam',0x8000},{'gbaExtWorkRam',0x40000},
  {'gbaVideoRam',0x18000},{'gbaPaletteRam',0x400},{'gbaSpriteRam',0x400}}
 local hashes={}
 for _,r in ipairs(regions) do
  hashes[#hashes+1]=string.format('"%s":%d',r[1],regionHash(r[1],r[2]))
 end
 write(name,string.format('{"frame":%d,"state":{%s},"hashes":{%s}}',
   frame,table.concat(keys,','),table.concat(hashes,',')))
end
local function dumpFont(name)
 local parts={}
 for idx,count in pairs(fontHits) do
  parts[#parts+1]=string.format('{"index":%d,"reads":%d,"first_frame":%d}',idx,count,fontFirst[idx])
 end
 local sites={}
 for pc,s in pairs(fontPcs) do
  sites[#sites+1]=string.format('{"pc":"0x%s","reads":%d,"first":%d,"min":%d,"max":%d}',pc,s.reads,s.first,s.min,s.max)
 end
 write(name,string.format('{"total_reads":%d,"records":[%s],"sites":[%s]}',fontTotal,table.concat(parts,','),table.concat(sites,',')))
end
local function capture(name)
 if not verifyLoadedRom() then return end
 write(name..'.png',emu.takeScreenshot())
 local cpu=emu.getState()
 write(name..'.json',string.format('{"frame":%d,"pc":%d}',frame,cpu['cpu.r15']))
 if PROBE=='fontread' then dumpFont(name..'_fontread.json') end
 if PROBE=='ramdump' then dumpRam(name) end
 if PROBE=='textread' then dumpPc(name..'_textread.json') end
 if PROBE=='statehash' then dumpState(name..'_state.json') end
 if PROBE=='snapshot' then dumpRam(name); dumpState(name..'_state.json') end
 if PROBE=='exectrace' then dumpTrace(name..'_exectrace.json') end
 if PROBE=='tilecalls' then dumpTile(name..'_tilecalls.json');dumpFont(name..'_fontread.json') end
 if PROBE=='chipcalls' or PROBE=='chipqa' then dumpChip(name..'_chipcalls.json') end
 if PROBE=='vramwrites' or PROBE=='chipqa' or PROBE=='bgqa' then dumpVram(name);dumpRam(name) end
 if PROBE=='bgqa' then dumpBg(name..'_bgcalls.json') end
end
if PROBE=='ramdump' then
 local names={}
 for k,v in pairs(emu.memType) do names[#names+1]=string.format('"%s":%d',k,v) end
 write('memtypes.json','{'..table.concat(names,',')..'}')
end
local pendingCapture=nil
local pendingFinal=false
local function finish()
 write('checkpoint.mss',emu.createSavestate())
 write('complete.txt',tostring(frame))
 emu.stop(0)
end
if capturePc~=nil then
 emu.addMemoryCallback(function()
  if pendingCapture~=nil then
   local n=pendingCapture
   pendingCapture=nil
   capture(n)
  end
  if pendingFinal then
   pendingFinal=false
   finish()
  end
 end,emu.callbackType.exec,capturePc,capturePc)
end
local function requestCapture(name)
 if capturePc==nil then capture(name) else pendingCapture=name end
end
local function onceExec(fn)
 local id
 id=emu.addMemoryCallback(function()
  emu.removeMemoryCallback(id,emu.callbackType.exec,0,0x0fffffff)
  fn()
 end,emu.callbackType.exec,0,0x0fffffff)
end
STATELOAD
emu.addEventCallback(function()
 local keys={a=false,b=false,l=false,r=false,start=false,select=false,
             up=false,down=false,left=false,right=false}
 if ready and not final then
  for _,act in ipairs(actions) do
   if frame>=act.start and frame<act.release then
    for _,k in ipairs(act.keys) do keys[k]=true end
   end
  end
 end
 emu.setInput(keys,0)
 if ready and not final then
  for _,pk in ipairs(POKES) do
   local act=actions[pk[1]]
   if frame>=act.start and frame<act.finish then
    for k,v in ipairs(pk[3]) do emu.write(pk[2]+k-1,v,emu.memType.gbaMemory) end
   end
  end
 end
end,emu.eventType.inputPolled)
emu.addEventCallback(function()
 if final or not ready then return end
 frame=frame+1
 for i,act in ipairs(actions) do
  if frame==act.finish and (captureAt==nil or captureAt[i]) then
   requestCapture(string.format('step_%03d',i))
  end
 end
 if frame>=total then
  final=true
  if capturePc~=nil then
   pendingCapture='final'
   pendingFinal=true
  else
   onceExec(function()
    if PROBE=='fontread' then dumpFont('fontread_final.json') end
    if PROBE=='textread' then dumpPc('textread_final.json') end
    if PROBE=='ramdump' then dumpRam('final') end
    if PROBE=='snapshot' then dumpRam('final'); dumpState('final_state.json') end
    if PROBE=='exectrace' then dumpTrace('exectrace_final.json') end
    if PROBE=='tilecalls' then dumpTile('tilecalls_final.json');dumpFont('fontread_final.json') end
    if PROBE=='chipcalls' or PROBE=='chipqa' then dumpChip('chipcalls_final.json') end
    if PROBE=='vramwrites' or PROBE=='chipqa' or PROBE=='bgqa' then dumpVram('final');dumpRam('final') end
    if PROBE=='bgqa' then dumpBg('bgcalls_final.json') end
    finish()
   end)
  end
 end
end,emu.eventType.endFrame)
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    # '@file' reads arguments one per line. The story build guards every
    # relocated archive, and that list outgrew the 32,767-character Windows
    # command line (WinError 206), so callers with long guard lists pass a file.
    ap = argparse.ArgumentParser(fromfile_prefix_chars='@')
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--mesen", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--expect-rom-sha256")
    ap.add_argument("--actions", default="none:1:599")
    ap.add_argument("--poke", action="append", default=[],
                    help="STEP:ADDR:HEX — write these bytes every frame while action STEP runs "
                         "(diagnostic runs only; the receipt records every poke)")
    ap.add_argument("--probe",
                    choices=("none", "fontread", "ramdump", "textread",
                            "statehash", "snapshot", "exectrace", "tilecalls", "chipcalls", "vramwrites", "chipqa", "bgqa"),
                    default="none")
    ap.add_argument("--trace-pc", type=lambda v: int(v, 0), action="append",
                    default=[],
                    help="bus address to put an execution breakpoint on; "
                         "repeatable, used by the exectrace probe")
    ap.add_argument("--watch-start", type=lambda v: int(v, 0), default=0)
    ap.add_argument("--watch-end", type=lambda v: int(v, 0), default=0)
    ap.add_argument("--font-base", type=lambda v: int(v, 0), default=0x0867A978)
    ap.add_argument("--font-end", type=lambda v: int(v, 0), default=0x08682978)
    ap.add_argument("--font-stride",type=int,default=64)
    ap.add_argument('--guard',action='append',default=[],help='ROM file offset:expected hex bytes')
    ap.add_argument('--state',type=Path)
    ap.add_argument('--state-origin',type=Path)
    ap.add_argument("--capture-steps", default="",
                    help="comma-separated 1-based action indices to capture at. "
                         "Every action still runs; only these produce a snapshot. "
                         "Empty means capture at every action.")
    ap.add_argument("--capture-pc", type=lambda v: int(v, 0), default=0,
                    help="anchor captures to this program counter instead of a "
                         "frame boundary; 0 disables")
    ap.add_argument("--timeout", type=int, default=90)
    args = ap.parse_args()
    if args.probe in ('chipcalls','chipqa','bgqa') and len(args.trace_pc)!=1:raise SystemExit('calls probe requires exactly one adopted parser entry')

    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit("refusing to overwrite an existing segment: %s" % args.out)

    rom_sha = digest(args.rom)
    if args.expect_rom_sha256 and rom_sha != args.expect_rom_sha256:
        raise SystemExit("ROM SHA-256 mismatch: %s" % rom_sha)
    if bool(args.state)!=bool(args.state_origin):raise SystemExit('state and exact origin receipt are both required')
    if args.state:
        origin=json.loads(args.state_origin.read_text(encoding='utf-8'))
        if not origin['complete'] or origin['rom_sha256']!=rom_sha or origin['artifacts']['checkpoint.mss']!=digest(args.state):raise SystemExit('foreign/incomplete/stale checkpoint rejected')

    actions = []
    for item in args.actions.split(","):
        keys, held, wait = item.split(":")
        buttons = [] if keys == "none" else keys.split("+")
        if not set(buttons) <= GBA_BUTTONS:
            raise SystemExit("unknown button in %r" % keys)
        held, wait = int(held), int(wait)
        if not (1 <= held <= 3600 and 0 <= wait <= 3600):
            raise SystemExit("action timing out of range in %r" % item)
        actions.append((buttons, held, wait))

    timeline = []
    cursor = 0
    for keys, held, wait in actions:
        timeline.append({"start": cursor, "release": cursor + held,
                         "finish": cursor + held + wait, "keys": keys})
        cursor += held + wait

    lua_actions = "{" + ",".join(
        "{start=%d,release=%d,finish=%d,keys={%s}}"
        % (t["start"], t["release"], t["finish"],
           ",".join(json.dumps(k) for k in t["keys"]))
        for t in timeline
    ) + "}"

    pokes = []
    for item in args.poke:
        step, addr, hexv = item.split(":")
        step = int(step); addr = int(addr, 16)
        if not 1 <= step <= len(actions): raise SystemExit("poke step out of range: %r" % item)
        pokes.append((step, addr, bytes.fromhex(hexv)))
    lua_pokes = "{" + ",".join("{%d,%d,{%s}}" % (st, ad, ",".join(str(b) for b in hv)) for st, ad, hv in pokes) + "}"

    if args.capture_steps.strip():
        wanted = sorted({int(t) for t in args.capture_steps.split(",") if t.strip()})
        bad = [i for i in wanted if not (1 <= i <= len(actions))]
        if bad:
            raise SystemExit("capture step out of range: %s" % bad)
        capture_at = "{" + ",".join("[%d]=true" % i for i in wanted) + "}"
    else:
        wanted = list(range(1, len(actions) + 1))
        capture_at = "nil"

    # Mesen changes its current directory on startup. Use an absolute root.
    args.out.mkdir(parents=True,exist_ok=True)
    runtime = args.out.resolve()
    if args.state:shutil.copy2(args.state,runtime/'input.mss')
    drive = None
    lua_root = runtime.as_posix()
    if os.name == 'nt' and not lua_root.isascii():
        # Lua's native fopen cannot open UTF-8 Korean Windows paths. A free
        # DOS drive is a temporary alias of this exact output folder, not a
        # different output location. Remove the alias after emulator exit.
        for c in 'ZYXWVUTSRQPONMLKJIHGFE':
            if Path(c+':/').exists():continue
            alias=subprocess.run(['subst',c+':',str(runtime)],capture_output=True)
            if alias.returncode==0:
                drive=c+':'
                break
        if drive is None:
            raise SystemExit('no free drive for project-local Lua output alias')
        lua_root = drive + '/'
    lua = (LUA_TEMPLATE
           .replace("ROOT", json.dumps(lua_root))
           .replace("ACTIONS", lua_actions)
           .replace("POKES", lua_pokes)
           .replace("TOTAL", str(cursor))
           .replace("FONTBASE", str(args.font_base))
           .replace("FONTEND", str(args.font_end))
           .replace("FONTSTRIDE",str(args.font_stride))
           .replace("PROBENAME", json.dumps(args.probe))
           .replace("TRACEPCS",
                    "{" + ",".join(str(pc) for pc in args.trace_pc) + "}")
           .replace("WATCHSTART", str(args.watch_start))
           .replace("WATCHEND", str(args.watch_end))
           .replace("CAPTUREAT", capture_at)
           .replace("CAPTUREPC", str(args.capture_pc) if args.capture_pc else "nil"))
    script = runtime / "segment.lua"
    guards=[]
    for guard in args.guard:
        offset,hexbytes=guard.split(':',1)
        start=int(offset,0)
        expected=bytes.fromhex(hexbytes)
        guards.append("for i,v in ipairs({%s}) do if emu.read(%d+i-1,emu.memType.gbaPrgRom)~=v then write('loaded_rom_guard_failed.txt','ROM identity mismatch');emu.stop(1);return false end end"%(','.join(str(b) for b in expected),start))
    lua=lua.replace('LOADGUARD','local function verifyLoadedRom()\n'+'\n'.join(guards)+'\nreturn true end\nif not verifyLoadedRom() then return end')
    lua=lua.replace('STATEREADY','false' if args.state else 'true')
    lua=lua.replace('STATELOAD',"onceExec(function() local f=assert(io.open(root..'/input.mss','rb'));local data=f:read('*a');f:close();assert(emu.loadSavestate(data),'State load failed');write('loaded.txt','true');ready=true end)" if args.state else '')
    script.write_text(lua, encoding="utf-8")

    command = [str(args.mesen.resolve()), "--testRunner", "--noAudio", "--doNotSaveSettings", "--preferences.singleInstance=false", "--emulation.emulationSpeed=0",
               "--enableStdout", "--timeout=%d" % args.timeout,
               str(script), str(args.rom.resolve())]
    try:
        run = subprocess.run(command, cwd=runtime, capture_output=True,
                             timeout=args.timeout + 30)
    finally:
        if drive:
            subprocess.run(['subst',drive,'/D'],check=True)

    (args.out / "stdout.txt").write_bytes(run.stdout)
    (args.out / "stderr.txt").write_bytes(run.stderr)

    complete = (run.returncode == 0
                and (args.out / "checkpoint.mss").exists()
                and (args.out / "complete.txt").exists())
    steps_present = sum(1 for i in wanted
                        if (args.out / ("step_%03d.png" % i)).exists())

    result = {
        "scope": "normal controller input from validated same-ROM diagnostic checkpoint; no RAM or progress injection" if args.state else "cold boot and normal controller input only; no RAM or progress injection",
        "rom_path": str(args.rom.resolve()),
        "rom_sha256": rom_sha,
        "emulator_path": str(args.mesen.resolve()),
        "emulator_sha256": digest(args.mesen),
        "audio_enabled": False,
        "probe": args.probe,
        "font_base": "0x%X" % args.font_base,
        "font_end": "0x%X" % args.font_end,
        "font_stride": args.font_stride,
        "loaded_rom_guards": args.guard,
        "state_origin": str(args.state_origin.resolve()) if args.state_origin else None,
        "state_sha256": digest(args.state) if args.state else None,
        "emulator_components": {name:digest(args.mesen.parent/name) for name in ('Mesen.exe','Mesen.dll','MesenCore.dll') if (args.mesen.parent/name).exists()},
        "capture_pc": "0x%X" % args.capture_pc,
        "trace_pc": ["0x%X" % pc for pc in args.trace_pc],
        "watch_start": "0x%X" % args.watch_start,
        "watch_end": "0x%X" % args.watch_end,
        "command": command,
        "actions": args.actions,
        "pokes": args.poke,
        "total_frames": cursor,
        "return_code": run.returncode,
        "actions_total": len(actions),
        "capture_steps": wanted,
        "steps_expected": len(wanted),
        "steps_captured": steps_present,
        "complete": complete,
        "artifacts": {p.name: digest(p) for p in sorted(args.out.iterdir())
                      if p.is_file()},
    }
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print("segment %s  complete=%s  rc=%d  captures %d/%d (actions %d)"
          % (args.out, complete, run.returncode, steps_present, len(wanted),
             len(actions)))
    if not complete:
        tail = run.stdout.decode("utf-8", "replace")[-1500:]
        print("--- stdout tail ---")
        print(tail)
        err = run.stderr.decode("utf-8", "replace")[-800:]
        if err.strip():
            print("--- stderr tail ---")
            print(err)
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
