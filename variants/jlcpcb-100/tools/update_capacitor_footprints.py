"""Update capacitor body graphics/models while preserving all routed pad UUIDs."""
import copy
from pathlib import Path
import uuid
from sexp import parse,dump,find,find_all,S

p=Path('wpc_power_driver_cost.kicad_pcb');root=parse(p.read_text())[0]
name='CP_Radial_D26.0mm_P10.00mm_SnapIn'
lib=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Capacitor_THT.pretty')/(name+'.kicad_mod')
template=parse(lib.read_text())[0]
for fp in find_all(root,'footprint'):
 props={n[1]:n for n in find_all(fp,'property')}
 if props['Reference'][2] not in ('C5','C6','C7','C11','C30'):continue
 if fp[1]=='Capacitor_THT:'+name:continue
 expected={n[1]:n for n in find_all(template,'pad')}
 for pad in find_all(fp,'pad'):
  for key in ('size','drill'):
   assert find(pad,key)==find(expected[pad[1]],key),(props['Reference'][2],key)
 fp[1]='Capacitor_THT:'+name
 fp[:]=[n for n in fp if not (isinstance(n,list) and n[0] in ('fp_line','fp_arc','fp_circle','fp_poly','model'))]
 for item in template:
  if isinstance(item,list) and item[0] in ('fp_line','fp_arc','fp_circle','fp_poly'):
   item=copy.deepcopy(item);uid=find(item,'uuid')
   if uid:uid[1]=str(uuid.uuid4())
   else:item.append(S('uuid',str(uuid.uuid4())))
   fp.append(item)
 fp.append(S('model','${KIPRJMOD}/models/TDK_B41252_25p4x45_envelope.step',S('offset',S('xyz',0,0,0)),S('scale',S('xyz',1,1,1)),S('rotate',S('xyz',0,0,0))))
p.write_text(dump(root)+'\n')
