"""Extend BR1 heat-spreading polygons; refill and DRC are mandatory afterwards."""
raise SystemExit('Rejected historical experiment: enlarged pours introduced opens and did not solve BR1 heat. Current board uses TO-220 sinks; see docs/RELEASE_STATUS.md.')
from pathlib import Path
import pcbnew
from rail_pours import POURS

path=Path('wpc_power_driver_cost.kicad_pcb')
backup=Path('.scratch/release-baseline/before-br1-expansion.kicad_pcb')
if not backup.exists():backup.write_bytes(path.read_bytes())
b=pcbnew.LoadBoard(str(path))
limits={'BR1_18V':(335,57,438,114),'BR1_AC13A':(331,3,359.3,53),'BR1_AC13B':(359.3,3,438,53)}
for zone in b.Zones():
 for prefix,(x0,y0,x1,y1) in limits.items():
  if zone.GetZoneName().startswith(prefix+'_'):
   poly=zone.Outline();poly.RemoveAllContours();poly.NewOutline()
   for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):poly.Append(round(x*1e6),round(y*1e6))
   zone.SetIsFilled(False)
existing={z.GetZoneName() for z in b.Zones()}
nets={'BR1_18V':'+18V','BR1_AC13A':'/Power_Supply/AC13_A_F','BR1_AC13B':'AC13_B'}
for prefix,(x0,y0,x1,y1) in limits.items():
 for layer in (pcbnew.In1_Cu,pcbnew.In2_Cu):
  name=prefix+'_'+b.GetLayerName(layer)
  if name in existing:continue
  z=pcbnew.ZONE(b);z.SetLayer(layer);z.SetNet(b.GetNetInfo().GetNetItem(nets[prefix]));z.SetZoneName(name)
  z.SetLocalClearance(400000);z.SetMinThickness(500000);z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL);z.SetAssignedPriority(2)
  poly=z.Outline();poly.NewOutline()
  for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):poly.Append(round(x*1e6),round(y*1e6))
  b.Add(z)
pcbnew.SaveBoard(str(path),b)
