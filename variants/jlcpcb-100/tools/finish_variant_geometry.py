"""Finalize project model paths, corrected capacitor bodies and pull-up metadata."""
import math,uuid,copy
from pathlib import Path
from sexp import parse,find,find_all,dump,S
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'wpc_power_driver_cost.kicad_pcb';b=parse(p.read_text())[0]
for f in find_all(b,'footprint'):
 props={v[1]:v for v in find_all(f,'property')};ref=props['Reference'][2]
 for m in find_all(f,'model'):m[1]=m[1].replace('${KICAD10_3DMODEL_DIR}','${KIPRJMOD}/models/kicad')
 if ref in {f'R{i}' for i in range(310,326)}:
  props['Link'][2]='https://jlcpcb.com/partdetail/UNIROYAL-UniroyalElec-0805W8F4701T5E/C17673'
  def renew(n):
   for v in n:
    if isinstance(v,list):
     if v[0]=='uuid':v[1]=str(uuid.uuid4())
     else:renew(v)
  renew(f)
 if ref in ['C2','C4','C9','C12']:
  f[1]='wpc_cost:CP_Radial_D8.0mm_P5.00mm'
  # Preserve proven pad/hole positions and conservative 10 mm courtyard.
  # Smaller nominal 8 x 11.5 mm body model corresponds to the factory-formed part.
  for m in find_all(f,'model'):m[1]='${KIPRJMOD}/models/Panasonic_EEUFR1E331B_envelope.step'
p.write_text(dump(b)+'\n')
for p in ROOT.glob('*.kicad_sch'):
 b=parse(p.read_text())[0]
 for s in find_all(b,'symbol'):
  props={v[1]:v for v in find_all(s,'property')}
  if props.get('Reference',[None,None,None])[2] in ['C2','C4','C9','C12']:props['Footprint'][2]='wpc_cost:CP_Radial_D8.0mm_P5.00mm'
 p.write_text(dump(b)+'\n')
