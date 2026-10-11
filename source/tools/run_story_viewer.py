#!/usr/bin/env python3
"""Draw translated story scripts through the game's own field dialogue renderer.

A normal playthrough reaches each script only after hours of play, so this
takes the one scene the cold route does reach -- Netto's room with the first
message box open (a same-ROM checkpoint captured by the ramdump probe at step
68) -- and, for each job, writes a decompressed archive into the buffer that
scene's event command decompressed its own archive into (0x02036800), points
the text engine's read, script and archive words (0x0200A52C/34/30) at the
chosen script, and presses A page by page, capturing each page.  The state is
reloaded before every job so one script cannot disturb the next.

What this shows: every page of the script as the real renderer draws it --
glyphs, widths, line breaks, box overflow -- and whether the script reaches its
end or hangs.  What it does not show: the scene the script belongs to (actors,
camera, flags), or a hang that only that scene's event flow would cause.  It
writes RAM on purpose, unlike run_mesen_segment.py, and says so in its result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

p = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(p / 'tools'))
from verify_tpi_index import lz77_decompress  # noqa: E402

MESEN = 'C:/Users/<사용자>/AppData/Local/emucap/mesen2/47801/portable/Mesen.exe'
PRODUCT = '{key}_opening_menu_chip_folder_library_menu_descriptions_story_korean_development'
BUFFER, READ, ARCHIVE, SCRIPT = 0x02036800, 0x0200A52C, 0x0200A530, 0x0200A534
BUFFER_LIMIT = 0x5000 - 0x40  # the largest story archive decompresses to 18,211 bytes

LUA = r'''
local root=@ROOT@
local jobs=@JOBS@
local WAIT=@WAIT@
local MAXPAGES=@MAXPAGES@
local SETTLE=40
local stuck=0
local JOBFRAMES=4000
local BUF=@BUFFER@
local READ=@READ@
local BASE=BUF+0x40
local state=nil
local ji=0
local phase='load'
local t=0
local page=0
local press=0
local lastRead=-1
local still=0
local capturedAt=-1
local log={}
local function write(name,data) local f=assert(io.open(root..'/'..name,'wb'));f:write(data);f:close() end
local function read(name) local f=assert(io.open(root..'/'..name,'rb'));local d=f:read('*a');f:close();return d end
local function w32(a,v) for i=0,3 do emu.write(a+i,(v>>(8*i))&255,emu.memType.gbaMemory) end end
local function r32(a) local v=0 for i=0,3 do v=v|(emu.read(a+i,emu.memType.gbaMemory)<<(8*i)) end return v end
local function endJob(reason)
 local line=string.format('{"job":"%s","pages":%d,"end":"%s","read":%d}',jobs[ji].name,page,reason,r32(READ)-BASE)
 log[#log+1]=line
 local f=assert(io.open(root..'/jobs_log.txt','ab'));f:write(line..'\n');f:close()
 phase='load'
end
emu.addEventCallback(function()
 local keys={a=false,b=false,l=false,r=false,start=false,select=false,up=false,down=false,left=false,right=false}
 if press>0 then keys.a=true end
 emu.setInput(keys,0)
end,emu.eventType.inputPolled)
local function startJob()
 local j=jobs[ji]
 -- The checkpoint waits at BUF+0x30 on the key-wait that ends archive 443's
 -- first script, followed by clear-box and jump-to-script-1. Keep that
 -- sequence, point its jump at the job's script, and move the job's archive
 -- to BASE so the jump resolves against it.
 local data=read(j.file)
 for i=1,#data do emu.write(BASE+i-1,string.byte(data,i),emu.memType.gbaMemory) end
 local tramp={0xE6,0x00,0xF1,0xEF,0x00,j.script}
 for i=1,#tramp do emu.write(BUF+0x2F+i,tramp[i],emu.memType.gbaMemory) end
 w32(@ARCHIVE@,BASE);w32(0x0200AA50,BASE)
 page=0;t=0;lastRead=-1;still=0;capturedAt=-1;stuck=0
 write('current.txt',j.name)
end
emu.addEventCallback(function()
 if phase=='load' then
  ji=ji+1
  if ji>#jobs then
   write('jobs_result.json','['..table.concat(log,',')..']')
   write('complete.txt','done')
   emu.stop(0)
   return
  end
  phase='loading'
  local id
  id=emu.addMemoryCallback(function()
   emu.removeMemoryCallback(id,emu.callbackType.exec,0,0x0fffffff)
   local ok,err=pcall(function() assert(emu.loadSavestate(state),'state load failed') end)
   if not ok then write('error.txt',tostring(err));emu.stop(1) end
   phase='start'
  end,emu.callbackType.exec,0,0x0fffffff)
  return
 end
 if phase=='loading' then return end
 if phase=='start' then
  local ok,err=pcall(startJob)
  if not ok then write('error.txt',tostring(err));emu.stop(1);return end
  phase='run';press=1;return
 end
 if phase~='run' then return end
 if press>0 then press=press-1;return end
 local j=jobs[ji]
 local r=r32(READ)-BASE
 t=t+1
 -- A script often opens with a flag test that jumps to another script, so
 -- leaving the script's own bytes is not its end; the jumps are followed and
 -- the job ends when the stream stops, or at the page or frame cap.
 if r<-0x40 or r>=0x8000 then
  page=page+1
  write(string.format('%s_p%02d.png',j.name,page),emu.takeScreenshot())
  endJob('left_buffer');return
 end
 if r==lastRead then still=still+1 else still=0;lastRead=r end
 if still>=SETTLE then
  -- A pause command also holds the stream still, so a repeat is only the end
  -- when pressing A three times in a row has not moved it.
  if r==capturedAt then
   stuck=stuck+1
   if stuck>=3 then endJob('stopped');return end
   still=-WAIT;press=1;return
  end
  stuck=0
  capturedAt=r
  page=page+1
  write(string.format('%s_p%02d.png',j.name,page),emu.takeScreenshot())
  if page>=MAXPAGES then endJob('page_cap');return end
  still=-WAIT;press=1
 end
 if t>=JOBFRAMES then endJob('timeout');return end
end,emu.eventType.endFrame)
state=read('input.mss')
'''


def archive_bytes(rom: bytes, item: dict) -> bytes:
    if item['compressed']:
        r = lz77_decompress(rom, item['offset'])
        return r[0] if isinstance(r, tuple) else r
    return rom[item['offset']:item['offset'] + item['size']]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--key', required=True, choices=['blue_moon', 'red_sun'])
    ap.add_argument('--state', type=Path, required=True, help='checkpoint.mss with the first message box open')
    ap.add_argument('--out', required=True)
    ap.add_argument('--archives', default='', help='comma list of archive numbers; empty means every relocated story archive')
    ap.add_argument('--wait', type=int, default=100)
    ap.add_argument('--max-pages', type=int, default=40)
    ap.add_argument('--timeout', type=int, default=3600)
    ap.add_argument('--chunk', type=int, default=1500, help='jobs per Mesen process')
    a = ap.parse_args()

    rom_path = p / 'poc/output' / (PRODUCT.format(key=a.key) + '.gba')
    rom = rom_path.read_bytes()
    m = json.loads(rom_path.with_suffix('.json').read_text(encoding='utf-8'))
    out = p / 'analysis/runtime' / f"{a.out}_{m['output_sha256'][:8]}"
    out.mkdir(parents=True, exist_ok=True)
    wanted = {int(x) for x in a.archives.split(',') if x}
    scripts: dict[int, set[int]] = {}
    for b in sorted((p / 'translations/story_korean').glob('*.json')):
        for e in json.loads(b.read_text(encoding='utf-8'))['entries']:
            parts = e['id'].split('/')
            scripts.setdefault(int(parts[1]), set()).add(int(parts[3]))
    jobs, skipped = [], []
    for item in m['extension']['story']['layout']:
        if not item['name'].startswith('story archive '):
            continue
        number = int(item['name'].split()[2])
        if wanted and number not in wanted:
            continue
        data = archive_bytes(rom, item)
        if len(data) > BUFFER_LIMIT:
            skipped.append({'archive': number, 'reason': f'{len(data)} bytes over the buffer limit'})
            continue
        (out / f'a{number:03d}.bin').write_bytes(data)
        # Script s runs from its table offset to the next larger offset; the
        # table ends where the first script begins.
        table_end = int.from_bytes(data[0:2], 'little')
        offsets = sorted({int.from_bytes(data[2 * i:2 * i + 2], 'little') for i in range(table_end // 2)} | {len(data)})
        for s in sorted(scripts.get(number, ())):
            offset = int.from_bytes(data[2 * s:2 * s + 2], 'little')
            stop = next((o for o in offsets if o > offset), None)
            if stop is None:
                skipped.append({'archive': number, 'script': s, 'reason': 'script offset at or past the archive end'})
                continue
            if s > 255:
                skipped.append({'archive': number, 'script': s, 'reason': 'the jump operand is one byte'})
                continue
            jobs.append({'name': f'a{number:03d}_s{s:03d}', 'file': f'a{number:03d}.bin', 'script': s, 'offset': offset, 'stop': stop})
    (out / 'input.mss').write_bytes(a.state.read_bytes())
    root = out.as_posix()
    drive = None
    if os.name == 'nt' and not root.isascii():
        for letter in 'QRSTUVWXYZ':
            if not Path(letter + ':/').exists():
                subprocess.run(['subst', letter + ':', str(out)], check=True)
                drive = letter + ':'
                break
        root = drive + '/'
    # Mesen can die on a job; every finished job is logged as it ends, so a
    # restart runs only what is left, and a job that kills it twice is logged
    # as a crash and skipped.
    def logged() -> dict[str, dict]:
        f = out / 'jobs_log.txt'
        return {r['job']: r for r in (json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip())} if f.exists() else {}
    crashes: dict[str, int] = {}
    returncodes = []
    try:
        while True:
            done = logged()
            pending = [j for j in jobs if j['name'] not in done]
            if not pending:
                break
            # One Mesen process dies after several thousand jobs (both revisions
            # stopped near archive 600, while that range alone runs clean), so
            # each process gets a bounded slice and the next one resumes.
            pending = pending[:a.chunk]
            (out / 'complete.txt').unlink(missing_ok=True)
            (out / 'current.txt').unlink(missing_ok=True)
            lua_jobs = '{' + ','.join('{name="%s",file="%s",script=%d,offset=%d,stop=%d}' % (j['name'], j['file'], j['script'], j['offset'], j['stop']) for j in pending) + '}'
            lua = (LUA.replace('@ROOT@', json.dumps(root)).replace('@JOBS@', lua_jobs)
                   .replace('@WAIT@', str(a.wait)).replace('@MAXPAGES@', str(a.max_pages))
                   .replace('@BUFFER@', str(BUFFER)).replace('@ARCHIVE@', str(ARCHIVE))
                   .replace('@SCRIPT@', str(SCRIPT)).replace('@READ@', str(READ)))
            (out / 'viewer.lua').write_text(lua, encoding='utf-8')
            command = [MESEN, '--testRunner', '--noAudio', '--doNotSaveSettings', '--preferences.singleInstance=false',
                       '--emulation.emulationSpeed=0', '--enableStdout', f'--timeout={a.timeout}',
                       str((out / 'viewer.lua')), str(rom_path)]
            try:
                run = subprocess.run(command, cwd=out, capture_output=True, timeout=a.timeout + 60)
                returncodes.append(run.returncode)
            except subprocess.TimeoutExpired:
                returncodes.append('timeout')
            if (out / 'complete.txt').exists():
                continue
            current = (out / 'current.txt').read_text(encoding='utf-8').strip() if (out / 'current.txt').exists() else None
            if current is None or current in logged():
                raise SystemExit('the viewer stopped outside a job; see ' + str(out))
            crashes[current] = crashes.get(current, 0) + 1
            print('viewer restart after', current, 'crash', crashes[current], flush=True)
            if crashes[current] >= 2:
                with (out / 'jobs_log.txt').open('a', encoding='utf-8') as f:
                    f.write(json.dumps({'job': current, 'pages': 0, 'end': 'emulator_crash', 'read': -1}) + chr(10))
    finally:
        if drive:
            subprocess.run(['subst', drive, '/D'], check=True)
    results = list(logged().values())
    complete = len(results) == len(jobs)
    report = {
        'schema': 1,
        'scope': 'translated story scripts drawn by the field dialogue renderer from a same-ROM checkpoint with the '
                 'first message box open; the archive buffer and text-engine words are written for each job',
        'writes_ram': True,
        'rom_sha256': m['output_sha256'],
        'state_sha256': hashlib.sha256(a.state.read_bytes()).hexdigest(),
        'complete': complete,
        'returncodes': returncodes,
        'crashes': crashes,
        'jobs': len(jobs),
        'results': results,
        'skipped': skipped,
        'not_claimed': ['the script was seen in the scene it belongs to', 'scene-specific event flow does not hang'],
    }
    (out / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    ended = {}
    for r in results:
        ended[r['end']] = ended.get(r['end'], 0) + 1
    print(f"viewer {out.name} complete={report['complete']} restarts={len(returncodes) - 1} jobs {len(results)}/{len(jobs)} {ended} skipped {len(skipped)}")
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
