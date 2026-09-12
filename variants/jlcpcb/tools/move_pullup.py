"""Place Basic pull-ups in free front-side area, preserving all original routing."""
import copy,json,math,uuid,shapely,argparse
from pathlib import Path
from shapely.geometry import box,Point
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
from close_routes import Board,LAYERS
from sexp import parse,dump,find,find_all,S
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'wpc_power_driver_cost.kicad_pcb'
ap=argparse.ArgumentParser();ap.add_argument('--ref',default='R314');args=ap.parse_args()
new=parse(p.read_text())[0]
def ref(fp):return next(v[2] for v in find_all(fp,'property') if v[1]=='Reference')
fps={ref(f):f for f in find_all(new,'footprint')};items=[i for i in json.loads((ROOT/'pullup-migration.json').read_text()) if i['ref']==args.ref]
b=Board(p);b.items=[v for v in b.items if not v.get('pin','').startswith(args.ref+'.')];new.remove(fps[args.ref])
# Existing courtyards reserve physical space for bodies and assembly access.
bodies=[]
for f in find_all(new,'footprint'):
 a=find(f,'at');fx,fy=map(float,a[1:3]);angle=float(a[3]) if len(a)>3 else 0;pts=[]
 for g in f:
  if isinstance(g,list) and g[0] in ('fp_line','fp_rect','fp_circle','fp_poly') and find(g,'layer') and find(g,'layer')[1]=='F.CrtYd':
   if g[0]=='fp_circle':
    cx,cy=map(float,find(g,'center')[1:3]);ex,ey=map(float,find(g,'end')[1:3]);r=math.hypot(ex-cx,ey-cy);pts.extend([(cx-r,cy-r),(cx+r,cy+r)]);continue
   for k in ['start','end','center']:
    v=find(g,k)
    if v:pts.append(tuple(map(float,v[1:3])))
   v=find(g,'pts')
   if v:pts.extend(tuple(map(float,q[1:3])) for q in v[1:])
 if pts:
  body=box(min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts))
  bodies.append(translate(rotate(body,-angle,origin=(0,0)),fx,fy))
mechanical=ROOT/'output/verification/revision/mechanical.json'
if mechanical.exists():
 for component in json.loads(mechanical.read_text())['components']:
  if component['ref']==args.ref:continue
  x1,y1,z1,x2,y2,z2=component['bounds']
  if z2>1.6 and z1<2.2:bodies.append(box(x1,-y2,x2,-y1).buffer(.4))
occupied=unary_union(bodies);front=[i for i in b.items if 0 in i['layers']]
placed=[]
for item in items:
 sig=item['net'];snet=unary_union([i['poly'] for i in front if i['net']==sig]);power=unary_union([i['poly'] for i in front if i['net']=='+5V'])
 obs={n:unary_union([i['poly'].buffer(max(.4,b.params(i['net'])['clearance'])+.03) for i in front if i['net']!=n]) for n in [sig,'+5V']}
 shapely.prepare(occupied)
 for o in obs.values():shapely.prepare(o)
 candidates=[]
 locations=sorted(((Point(x,y).distance(snet)+Point(x,y).distance(power)+.025*math.hypot(x-item['x'],y-item['y']),x,y) for x in range(16,100) for y in range(65,146)))
 for score,x,y in locations:
  for angle in [0,90,180,270]:
   footprint=translate(rotate(box(-1.9,-1.1,1.9,1.1),-angle,origin=(0,0)),x,y)
   if occupied.intersects(footprint):continue
   pads=[translate(rotate(box(xx-.52,-.78,xx+.52,.78),-angle,origin=(0,0)),x,y) for xx in [-.9125,.9125]]
   if obs['+5V'].intersects(pads[0]) or obs[sig].intersects(pads[1]):continue
   candidates.append((score,x,y,angle,footprint));break
  if candidates:break
 assert candidates,f'No free location for {item}'
 _,x,y,angle,footprint=min(candidates,key=lambda v:v[0]);occupied=unary_union([occupied,footprint]);f=fps[item['ref']];a=find(f,'at');a[1:]=[x,y,angle]
 # Existing local primitives stay local; field positions and pad rotations are board angles.
 for prop in find_all(f,'property'):
  at=find(prop,'at');at[1:]=[0,-1.65 if prop[1]=='Reference' else 1.65 if prop[1]=='Value' else 0,angle]
  if prop[1]=='Description':prop[2]='4.7 kohm 1% 125 mW 0805 discrete CPU-interface pull-up'
 for pad in find_all(f,'pad'):find(pad,'at')[3:]=[angle]
 new.append(f);placed.append(dict(ref=item['ref'],net=sig,x=x,y=y,angle=angle))
 print(placed[-1],flush=True)
p.write_text(dump(new)+'\n');(ROOT/f'pullup-placement-adjustment-{args.ref}.json').write_text(json.dumps(placed,indent=2)+'\n')
