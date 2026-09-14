"""Relocate DRC-reported silk texts into nearby free space; never hide references.
Long board legends move to the back. Pad, text and silk-line bounding boxes provide
conservative candidate screening; native DRC checks the actual glyph strokes afterwards.
"""
import json
import math
import pcbnew
import argparse
p=argparse.ArgumentParser();p.add_argument("--report",default="output/verification/revision/drc-current.json");a=p.parse_args()
b=pcbnew.LoadBoard('wpc_power_driver_cost.kicad_pcb')
report=json.load(open(a.report))
ids={i['uuid'] for v in report['violations'] if v['type'] in ('silk_overlap','silk_over_copper') for i in v['items']}
items=list(b.Drawings());pads=[]
for f in b.GetFootprints():
 items.extend(f.GraphicalItems());items.extend(x for x in f.GetFields() if x.IsVisible());pads.extend(f.Pads())
movable=[x for x in items if x.m_Uuid.AsString() in ids and x.GetClass() in ('PCB_TEXT','PCB_FIELD') and x.GetLayer() in (pcbnew.F_SilkS,pcbnew.B_SilkS)]
def bounds(item):
 r=item.GetBoundingBox();return [r.GetX()/1e6,r.GetY()/1e6,(r.GetX()+r.GetWidth())/1e6,(r.GetY()+r.GetHeight())/1e6]
def overlaps(a,c,margin=.2):return a[0]<c[2]+margin and c[0]<a[2]+margin and a[1]<c[3]+margin and c[1]<a[3]+margin
long_index=0;moved=[];unplaced=[]
for t in sorted(movable,key=lambda t:-(bounds(t)[2]-bounds(t)[0])*(bounds(t)[3]-bounds(t)[1])):
 original=t.GetPosition();text=t.GetText()
 if len(text)>65 and t.GetLayer()==pcbnew.F_SilkS:
  t.SetLayer(pcbnew.B_SilkS);t.SetMirrored(True);t.SetPosition(pcbnew.VECTOR2I(224600000,round((125+long_index*5)*1e6)));long_index+=1;moved.append((text,'B.SilkS'));continue
 obstacles=[bounds(x) for x in items if x is not t and x.GetLayer()==t.GetLayer()]
 obstacles.extend(bounds(p) for p in pads if p.IsOnLayer(pcbnew.F_Mask if t.GetLayer()==pcbnew.F_SilkS else pcbnew.B_Mask))
 offsets=sorted([(dx*.5,dy*.5) for dx in range(-24,25) for dy in range(-24,25)],key=lambda p:p[0]*p[0]+p[1]*p[1])
 found=False
 for scale in (1.,.85):
  size=t.GetTextSize();t.SetTextSize(pcbnew.VECTOR2I(max(900000,round(size.x*scale)),max(900000,round(size.y*scale))))
  for dx,dy in offsets:
   t.SetPosition(pcbnew.VECTOR2I(original.x+round(dx*1e6),original.y+round(dy*1e6)));bb=bounds(t)
   if bb[0]<.6 or bb[1]<.6 or bb[2]>448.6 or bb[3]>272.3:continue
   if not any(overlaps(bb,o) for o in obstacles):found=True;break
  if found:break
 if found:moved.append((text,t.GetPosition().x/1e6,t.GetPosition().y/1e6))
 else:t.SetPosition(original);unplaced.append(text)
pcbnew.SaveBoard('wpc_power_driver_cost.kicad_pcb',b)
print('Moved',len(moved),moved);print('Need manual placement:',unplaced)
