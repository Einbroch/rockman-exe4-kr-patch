"""Preserve an isolated reproduction of source comma loss; never writes a ROM."""
import json,subprocess
from pathlib import Path
from analyze_project import sha,check_dependencies
p=Path(__file__).resolve().parents[1];check_dependencies(p)
source=p/'analysis/blue_moon_tpl/6DE180.tpl';original=p/'analysis/blue_moon_roundtrip_bin/6DE180.msg'
plugins=p/'poc/blue_moon_menu/plugins';table=plugins/'exe4-utf8.tbl'
if '87=,' not in table.read_text(encoding='utf-8').splitlines():raise ValueError('expected rejected comma condition absent')
root=p/'analysis/rejected_menu_comma_reproduction';root.mkdir(exist_ok=True);out=root/'6DE180.msg'
command=[str(p/'external/TextPet-v1.0.0/TextPet.exe'),'load-plugins',str(plugins),'game','exe4','read-text-archives',str(source),'-f','tpl','write-text-archives',str(out),'-f','bin']
r=subprocess.run(command,capture_output=True);log=root/'compile.log';log.write_bytes(r.stdout+r.stderr)
if r.returncode or not out.exists() or out.read_bytes()==original.read_bytes():raise ValueError('isolated failure not reproduced')
d=original.read_bytes();n=out.read_bytes()
def spans(data):
 first=int.from_bytes(data[:2],'little');o=[int.from_bytes(data[i:i+2],'little') for i in range(0,first,2)];v=sorted(set(o));ends={x:v[i+1] if i+1<len(v) else len(data) for i,x in enumerate(v)}
 return [data[x:ends[x]] for x in o]
diff=[i for i,(a,b) in enumerate(zip(spans(d),spans(n))) if a!=b]
report={'schema':1,'status':'REJECTED; isolated reproduced diagnostic, not original failed-build artifact',
 'cause':'opening ASCII-comma compatibility table cannot encode source Japanese comma; TextPet writes an incomplete archive despite return code 0',
 'scope':'unmodified blue source archive1, rejected table only; no selected translation and no ROM writes',
 'command':command,'return_code':r.returncode,'original_payload_sha256':sha(d),'reproduced_payload_sha256':sha(n),'original_bytes':len(d),'reproduced_bytes':len(n),'changed_script_ids':diff,'table_sha256':sha(table.read_bytes()),'source_tpl_sha256':sha(source.read_bytes()),'compile_log_sha256':sha(log.read_bytes())}
(root/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('rejected source-copy reproduction:',len(d)-len(n),'bytes lost,',len(diff),'script spans differ')
