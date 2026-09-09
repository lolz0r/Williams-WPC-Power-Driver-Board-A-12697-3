"""Export native KiCad model transforms; run with KiCad Python."""
import json,pcbnew
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--pcb',default='wpc_power_driver_cost.kicad_pcb');p.add_argument('--output',default='output/verification/revision/mechanical-inputs.json');a=p.parse_args()
b=pcbnew.LoadBoard(a.pcb);out=[]
for f in b.GetFootprints():
 models=[]
 for m in f.Models():
  models.append({'path':m.m_Filename,'offset':[m.m_Offset.x,m.m_Offset.y,m.m_Offset.z],'rotation':[m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z],'scale':[m.m_Scale.x,m.m_Scale.y,m.m_Scale.z]})
 out.append({'ref':f.GetReference(),'value':f.GetValue(),'x':f.GetPosition().x/1e6,'y':f.GetPosition().y/1e6,'angle':f.GetOrientationDegrees(),'bottom':f.IsFlipped(),'dnp':f.IsDNP(),'models':models})
open(a.output,'w').write(json.dumps(out,indent=2))
