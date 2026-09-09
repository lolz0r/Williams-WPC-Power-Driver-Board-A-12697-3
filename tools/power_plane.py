"""Add the +5 V distribution plane on In2.Cu; retain existing signal routing.
KiCad's zone refill enforces clearances. Always run saved native DRC afterwards.
"""
import pcbnew
b=pcbnew.LoadBoard('wpc_power_driver_cost.kicad_pcb')
if not any(z.GetZoneName()=='5V_INNER_DISTRIBUTION' for z in b.Zones()):
 z=pcbnew.ZONE(b);z.SetLayer(pcbnew.In2_Cu);z.SetNet(b.FindNet('+5V'));z.SetZoneName('5V_INNER_DISTRIBUTION')
 o=z.Outline();o.NewOutline()
 for x,y in ((1,1),(448,1),(448,271.7),(1,271.7)):o.Append(round(x*1e6),round(y*1e6))
 z.SetLocalClearance(400000);z.SetMinThickness(500000);z.SetThermalReliefGap(400000);z.SetThermalReliefSpokeWidth(600000)
 z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL);z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS);z.SetAssignedPriority(0);z.SetIsFilled(False);b.Add(z)
pcbnew.SaveBoard('wpc_power_driver_cost.kicad_pcb',b)
print('Inner +5V distribution plane present')
