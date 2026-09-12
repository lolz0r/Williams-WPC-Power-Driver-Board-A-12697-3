"""Refine the sixteen Basic pull-up placements without touching original routes."""
from pathlib import Path
import json,pcbnew
ROOT=Path(__file__).resolve().parents[1]
b=pcbnew.LoadBoard(str(ROOT/'wpc_power_driver_cost.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
def vec(x,y):return pcbnew.VECTOR2I(round(x*1e6),round(y*1e6))
def track(a,z,net,layer=pcbnew.F_Cu,w=.4):
 t=pcbnew.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetWidth(round(w*1e6));t.SetLayer(layer);t.SetNetCode(net);b.Add(t)
def via(x,y,net):
 v=pcbnew.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetWidth(1000000);v.SetDrill(500000);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNetCode(net);b.Add(v)
items=json.loads((ROOT/'pullup-migration.json').read_text())
for name in ['SR1','SR2']:
 cx,cy=(20.65,112.443) if name=='SR1' else (15.48,102.803);net=b.GetNetcodeFromNetname('+5V');via(cx,cy,net)
 busx=cx-3.4
 track((cx,cy),(busx,cy),net,pcbnew.B_Cu)
 track((busx,cy),(busx,min(p['y'] for p in items if p['array']==name)),net,pcbnew.B_Cu)
 for item in [i for i in items if i['array']==name]:
  fp=fps[item['ref']];fp.SetOrientationDegrees(0);fp.SetPosition(vec(item['x']-2.2,item['y']))
  fp.GetField('Description').SetText('4.7 kohm 1% 125 mW 0805 discrete CPU-interface pull-up')
  fp.Reference().SetTextSize(vec(.8,.8));fp.Reference().SetPosition(vec(item['x']-2.2,item['y']-1.0))
  for p in fp.Pads():
   x,y=p.GetPosition().x/1e6,p.GetPosition().y/1e6
   if p.GetNumber()=='1':
    via(busx,y,net);track((x,y),(busx,y),net)
   else:
    pn=p.GetNetCode();via(item['x'],item['y'],pn);track((item['x'],item['y']),(x,y),pn)
pcbnew.SaveBoard(str(ROOT/'wpc_power_driver_cost.kicad_pcb'),b)
