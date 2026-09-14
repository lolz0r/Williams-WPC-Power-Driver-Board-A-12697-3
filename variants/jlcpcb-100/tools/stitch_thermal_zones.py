"""Connect top/bottom rectifier heat-spreading pours with clearance-screened vias.
Uses saved zone fills to restrict candidates to actual top copper. Native DRC remains mandatory.
"""
import math
import pcbnew

b=pcbnew.LoadBoard('wpc_power_driver_cost.kicad_pcb');tracks=list(b.GetTracks());pads=[p for f in b.GetFootprints() for p in f.Pads()]
mm=lambda x:round(x*1e6)
def distance(px,py,a,c):
 ax,ay=a.x/1e6,a.y/1e6;dx,dy=(c.x-a.x)/1e6,(c.y-a.y)/1e6;l=dx*dx+dy*dy
 u=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/l)) if l else 0
 return math.hypot(px-ax-u*dx,py-ay-u*dy)
added=[]
for z in list(b.Zones()):
 if not z.GetZoneName().startswith('BR') or z.GetLayer()!=pcbnew.F_Cu:continue
 net=z.GetNet();code=net.GetNetCode();poly=z.GetFilledPolysList(pcbnew.F_Cu);box=z.GetBoundingBox()
 chosen=[]
 for y in range(math.ceil(box.GetY()/1e6)+1,math.floor((box.GetY()+box.GetHeight())/1e6),4):
  for x in range(math.ceil(box.GetX()/1e6)+1,math.floor((box.GetX()+box.GetWidth())/1e6),4):
   if not all(poly.Contains(pcbnew.VECTOR2I(mm(x+dx),mm(y+dy))) for dx,dy in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]):continue
   if any(math.hypot(x-a,y-c)<7 for a,c in chosen):continue
   blocked=False
   for t in tracks:
    d=distance(x,y,t.GetStart(),t.GetEnd())
    if (t.GetClass()=='PCB_VIA' and d<2) or (t.GetClass()!='PCB_VIA' and t.GetNetCode()!=code and d<t.GetWidth()/2e6+1.1):blocked=True;break
   if blocked:continue
   if any(p.HitTest(pcbnew.VECTOR2I(mm(x),mm(y)),mm(1.1)) for p in pads if p.GetNetCode()!=code or p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH):continue
   v=pcbnew.PCB_VIA(b);v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetWidth(mm(1.2));v.SetDrill(mm(.6));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(net);b.Add(v);tracks.append(v);chosen.append((x,y));added.append((z.GetZoneName(),x,y))
pcbnew.SaveBoard('wpc_power_driver_cost.kicad_pcb',b)
print('Thermal stitching added:',added)
