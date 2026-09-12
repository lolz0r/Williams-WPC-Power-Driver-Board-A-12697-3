"""Independent GEOS union/connectivity of saved copper polygons and plated barrels.
Every populated/schematic pad on each net must share a conductive component.
Does not evaluate RF/SI, etch tolerances or contact resistance.
"""
import hashlib,json
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
OUT=Path('output/verification/revision');path=OUT/'copper_geometry.json';data=json.loads(path.read_text())
checks=0;failures=[];results=[]
for net,layers in sorted(data['copper'].items()):
 polygons=[];layer_ids={}
 for layer,raw in layers.items():
  geom=unary_union([Polygon(p['outer'],p['holes']) for p in raw])
  pp=[] if geom.is_empty else [geom] if geom.geom_type=='Polygon' else list(geom.geoms)
  layer_ids[layer]=list(range(len(polygons),len(polygons)+len(pp)));polygons.extend(pp)
 parent=list(range(len(polygons)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(ids):
  for i in ids[1:]:parent[root(i)]=root(ids[0])
 def hits(t,ls):
  # Plated pads/vias are represented as full outer copper in the native export.
  # 1 um query tolerance absorbs polygon rounding, not physical clearances.
  point=Point(t['x'],t['y']).buffer(.001)
  return [i for l in ls for i in layer_ids[l] if polygons[i].intersects(point)]
 for via in (v for v in data['vias'] if v['net']==net):union(hits(via,layers))
 terminals=[t for t in data['terminals'] if t['net']==net]
 for t in terminals:
  if t['drill_mm']:union(hits(t,t['layers']))
 groups={};missing=[]
 for t in terminals:
  ids=hits(t,t['layers']);checks+=1
  if not ids:missing.append(t['ref']+'-'+t['pad']);continue
  groups.setdefault(root(ids[0]),[]).append(t['ref']+'-'+t['pad'])
 ok=len(groups)<=1 and not missing
 if not ok:failures.append({'net':net,'groups':list(groups.values()),'missing':missing})
 results.append({'net':net,'pads':len(terminals),'conductive_pad_groups':len(groups),'passed':ok})
report={'passed':not failures,'pad_checks':checks,'net_checks':len(results),'geometry_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'failures':failures,'nets':results,'limitations':['Native exported copper is the input; this is independent topology analysis, not an independent Gerber geometry extraction','Round pads exported as solid copper; plated holes connect via annulus by construction','No etch tolerance or high-frequency integrity qualification']}
(OUT/'copper-topology.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='nets'},indent=2))
raise SystemExit(0 if report['passed'] else 1)
