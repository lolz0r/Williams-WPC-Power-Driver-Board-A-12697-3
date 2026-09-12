"""Replace obsolete right-angle BOM entry with dimension-checked 3M vertical header.
Retains routed pad centres; adjusts 34 finished holes to datasheet 0.89 +/-0.08 mm.
"""
from pathlib import Path
from copy import deepcopy
from sexp import parse,dump,find,find_all,S
new='wpc_cost:3M_N2534_6002_RB';old='Connector_IDC:IDC-Header_2x17_P2.54mm_Vertical'
p=Path('wpc_power_driver_cost.kicad_pcb');b=parse(p.read_text())[0]
f=next(f for f in find_all(b,'footprint') if any(p[1:3]==['Reference','J113'] for p in find_all(f,'property')))
f[1]=new
for prop in find_all(f,'property'):
 if prop[1]=='MPN':prop[2]='N2534-6002-RB'
 if prop[1]=='Link':prop[2]='https://www.digikey.com/en/products/detail/3m/N2534-6002-RB/755183'
for pad in find_all(f,'pad'):find(pad,'drill')[1]=.9
f[:]=[n for n in f if not(isinstance(n,list) and n[0]=='model')]
f.append(S('model','${KIPRJMOD}/models/3M_N2534_6002_RB_envelope.step',S('offset',S('xyz',0,0,0)),S('scale',S('xyz',1,1,1)),S('rotate',S('xyz',0,0,0))))
p.write_text(dump(b)+'\n')
# Library copy strips board-specific connectivity, UUID and global placement.
lib=deepcopy(f);lib[1]=new.split(':')[1]
lib[:]=[n for n in lib if not(isinstance(n,list) and n[0] in ('at','uuid','path','sheetname','sheetfile'))]
for pad in find_all(lib,'pad'):
 pad[:]=[n for n in pad if not(isinstance(n,list) and n[0] in ('net','uuid'))]
 at=find(pad,'at');at[:]=at[:3]
for prop in find_all(lib,'property'):
 if prop[1]=='Reference':prop[2]='REF**'
Path('footprints/wpc_cost.pretty/3M_N2534_6002_RB.kicad_mod').write_text(dump(lib)+'\n')
for p in [Path('cpu_interface.kicad_sch'),Path('tools/design_cost.py'),Path('tools/sourcing.py')]:
 s=p.read_text().replace(old,new).replace('30334-5002HB/1237402','N2534-6002-RB/755183').replace('30334-5002HB','N2534-6002-RB');p.write_text(s)
