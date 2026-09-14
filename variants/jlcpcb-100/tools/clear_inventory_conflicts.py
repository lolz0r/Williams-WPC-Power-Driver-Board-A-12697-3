"""Remove explicitly reported copper conflicts; retain a UUID audit trail."""
import argparse,json,math,uuid
from pathlib import Path
from sexp import parse,dump,find,find_all,S
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('report',type=Path);p.add_argument('--initial',action='store_true');a=p.parse_args()
f=ROOT/'wpc_power_driver_cost.kicad_pcb';b=parse(f.read_text())[0];d=json.loads(a.report.read_text());nodes={str(find(n,'uuid')[1]):n for n in b[1:] if isinstance(n,list) and n[0] in ['segment','via']}
victims={i['uuid'] for v in d['violations'] if v['severity']=='error' for i in v['items'] if i['uuid'] in nodes}
# F108 only needs a 0.15 mm positional correction, not removal of the long GI return.
if a.initial:
 for v in d['violations']:
  if any('F108' in i['description'] for i in v['items']):
   for i in v['items']:victims.discard(i['uuid'])
 for fp in find_all(b,'footprint'):
  ref=next(x[2] for x in find_all(fp,'property') if x[1]=='Reference')
  if ref=='F108':at=find(fp,'at');at[1]=float(at[1])+.15
record=[]
for u in sorted(victims):
 n=nodes[u];record.append(dict(uuid=u,type=str(n[0]),net=str(find(n,'net')[-1])));b.remove(n)
# Replaced clips supplied useful PTH inter-layer connections. Retain those
# native drill sites as plated vias; they are copper features, not BOM parts.
if a.initial:
 old=parse((ROOT.parent/'jlcpcb/wpc_power_driver_cost.kicad_pcb').read_text())[0]
 used={(round(float(find(v,'at')[1]),5),round(float(find(v,'at')[2]),5)) for v in find_all(b,'via')}
 for fp in find_all(old,'footprint'):
  ref=next(x[2] for x in find_all(fp,'property') if x[1]=='Reference')
  if not ref.startswith('F'):continue
  at=find(fp,'at');x,y=map(float,at[1:3]);angle=math.radians(float(at[3]) if len(at)>3 else 0)
  for p in find_all(fp,'pad'):
   pa=find(p,'at');px,py=map(float,pa[1:3]);gx=x+px*math.cos(angle)+py*math.sin(angle);gy=y-px*math.sin(angle)+py*math.cos(angle)
   # Restore only removed inner pads, or all four original F112 sites.
   if ref!='F112' and px not in [6.76,16.35]:continue
   if (round(gx,5),round(gy,5)) in used:continue
   b.append(S('via',S('at',round(gx,6),round(gy,6)),S('size',2.7),S('drill',1.7),S('layers','F.Cu','B.Cu'),S('net',str(find(p,'net')[-1])),S('uuid',str(uuid.uuid4()))))
f.write_text(dump(b)+'\n');out=ROOT/'research'/(a.report.parent.name+'-removed-conflicts.json');out.write_text(json.dumps(record,indent=2)+'\n');print('Removed',len(record),'conflicting copper items')
# Extend symbol-library footprint filters to the reviewed alternative packages.
for path in [*ROOT.glob('*.kicad_sch'),*ROOT.glob('*.kicad_sym')]:
 doc=parse(path.read_text())[0]
 def visit(n):
  if not isinstance(n,list):return
  if n and n[0]=='property' and len(n)>2 and n[1]=='ki_fp_filters':
   if '3M_N2534' in n[2] and 'XFCN*' not in n[2]:n[2]+=' XFCN*'
   if 'Fuse' in n[2] and 'HONGJU*' not in n[2]:n[2]+=' HONGJU* TLC_TA*'
   if '20' in n[2] and 'SOIC' in n[2] and 'SO-20*' not in n[2]:n[2]+=' SO-20*'
  for x in n:visit(x)
 visit(doc);path.write_text(dump(doc)+'\n')
