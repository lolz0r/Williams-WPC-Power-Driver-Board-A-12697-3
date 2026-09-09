"""Reconcile reported track endpoints with via centres, moving their endpoint junctions together.
Requires native DRC afterwards; original geometry retained for rollback.
"""
import json,math,shutil
from pathlib import Path
from sexp import *
p=Path('wpc_power_driver_cost.kicad_pcb');backup=Path('.scratch/release-baseline/before-centering.kicad_pcb')
assert not backup.exists();shutil.copy2(p,backup)
r=parse(p.read_text())[0];items={find(x,'uuid')[1]:x for x in r if isinstance(x,list) and find(x,'uuid')};changes={};report=json.load(open('output/verification/revision/drc-current.json'))
for v in report['violations']:
 if v['type']!='track_not_centered_on_via':continue
 objects=[items[i['uuid']] for i in v['items']]
 track=next((x for x in objects if x[0]=='segment'),None);via=next((x for x in objects if x[0]=='via'),None)
 if not track or not via:continue
 target=tuple(map(float,find(via,'at')[1:3]));ends=[find(track,n) for n in ('start','end')]
 near=min(ends,key=lambda e:math.hypot(float(e[1])-target[0],float(e[2])-target[1]))
 if math.hypot(float(near[1])-target[0],float(near[2])-target[1])>float(find(via,'size')[1])/2+float(find(track,'width')[1])/2:continue
 key=(find(track,'net')[1],find(track,'layer')[1],float(near[1]),float(near[2]));changes[key]=target
n=0
for t in find_all(r,'segment'):
 for end in ('start','end'):
  point=find(t,end);key=(find(t,'net')[1],find(t,'layer')[1],float(point[1]),float(point[2]))
  if key in changes:point[1:3]=changes[key];n+=1
p.write_text(dump(r)+'\n');print('Centred',n,'endpoints at',len(changes),'junctions')
