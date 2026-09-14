"""Extend existing signal fanout ends into the new SO-20 pads.
Only reported track-to-logic-pad gaps shorter than two millimetres are bridged;
all additions must pass fresh native DRC.
"""
import json,math,uuid
from pathlib import Path
from sexp import parse,dump,find,find_all,S
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'wpc_power_driver_cost.kicad_pcb';b=parse(path.read_text())[0];d=json.loads((ROOT/'output/verification/native-reroute4/drc.json').read_text());ids={str(find(n,'uuid')[1]):n for n in b[1:] if isinstance(n,list) and find(n,'uuid')};record=[]
for gap in d['unconnected_items']:
 items=gap['items'];pads=[i for i in items if i['description'].startswith('Pad ') and ' of U' in i['description']];tracks=[i for i in items if i['description'].startswith('Track ')]
 if len(pads)!=1 or len(tracks)!=1:continue
 tr=ids[tracks[0]['uuid']];n=str(find(tr,'net')[-1]);p=pads[0]['pos'];target=(p['x'],p['y']);ends=[tuple(map(float,find(tr,k)[1:3])) for k in ['start','end']];point=min(ends,key=lambda q:math.dist(q,target));dist=math.dist(point,target)
 if dist>2:raise ValueError((n,dist))
 b.append(S('segment',S('start',*point),S('end',*target),S('width',.2),S('layer',str(find(tr,'layer')[1])),S('net',n),S('uuid',str(uuid.uuid4()))));record.append(dict(net=n,start=point,end=target,length=dist))
# Local model paths for new standard library copies.
import re
text=dump(b)+'\n';text=re.sub(r'\$\{KICAD\d+_3DMODEL_DIR\}/','${KIPRJMOD}/models/kicad/',text);path.write_text(text)
for p in ROOT.glob('footprints/*/*.kicad_mod'):p.write_text(re.sub(r'\$\{KICAD\d+_3DMODEL_DIR\}/','${KIPRJMOD}/models/kicad/',p.read_text()))
(ROOT/'research/logic-microgaps.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
