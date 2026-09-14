"""Export actual filled copper polygons and terminals for independent DC/thermal analysis.
Run with KiCad Python after a saved native zone refill.
"""
import collections
import hashlib
import json
from pathlib import Path
import pcbnew

b=pcbnew.LoadBoard('wpc_power_driver_cost.kicad_pcb')
nets={p.GetNetname() for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()}
layers={b.GetLayerName(i):i for i in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu)}
parts=collections.defaultdict(list)
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNetname() in nets:parts[p.GetNetname()].append(p)
for t in b.GetTracks():
 if t.GetNetname() in nets:parts[t.GetNetname()].append(t)
result={'pcb_sha256':hashlib.sha256(Path('wpc_power_driver_cost.kicad_pcb').read_bytes()).hexdigest(),'units':'mm','copper_thickness_mm':{'F.Cu':.07,'B.Cu':.07,'In1.Cu':.035,'In2.Cu':.035},'copper':{},'terminals':[]}
def points(line):return [[line.CPoint(i).x/1e6,line.CPoint(i).y/1e6] for i in range(line.PointCount())]
for net in sorted(nets):
 result['copper'][net]={}
 for name,layer in layers.items():
  acc=pcbnew.SHAPE_POLY_SET()
  for p in parts[net]:
   if not p.IsOnLayer(layer):continue
   poly=pcbnew.SHAPE_POLY_SET()
   p.TransformShapeToPolygon(poly,layer,0,5000,pcbnew.ERROR_INSIDE)
   acc.Append(poly)
  for z in b.Zones():
   if z.GetNetname()==net and z.IsOnLayer(layer):acc.Append(z.GetFilledPolysList(layer))
  acc.Simplify()
  result['copper'][net][name]=[{'outer':points(acc.COutline(i)),'holes':[points(acc.CHole(i,h)) for h in range(acc.HoleCount(i))]} for i in range(acc.OutlineCount())]
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNumber():
   result['terminals'].append({'ref':f.GetReference(),'pad':p.GetNumber(),'net':p.GetNetname(),'x':p.GetPosition().x/1e6,'y':p.GetPosition().y/1e6,'layers':[n for n,i in layers.items() if p.IsOnLayer(i)],'drill_mm':p.GetDrillSize().x/1e6})
result['vias']=[{'net':v.GetNetname(),'x':v.GetPosition().x/1e6,'y':v.GetPosition().y/1e6,'drill_mm':v.GetDrillValue()/1e6} for v in b.GetTracks() if v.GetClass()=='PCB_VIA' ]
p=Path('output/verification/revision/copper_geometry.json');p.write_text(json.dumps(result)+'\n');print(p)
