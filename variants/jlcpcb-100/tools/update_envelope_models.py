"""Attach project nominal mechanical envelopes, preserving placement and routing."""
import re
from pathlib import Path
from sexp import parse,dump,find,find_all,S
p=Path('wpc_power_driver_cost.kicad_pcb');b=parse(p.read_text())[0]
for f in find_all(b,'footprint'):
 props={p[1]:p[2] for p in find_all(f,'property')};ref=props['Reference'];model=None
 if ref in ('C8','C32'):model='Nichicon_LLS_25x40_envelope'
 if ref in ('L1','L2'):model='Bourns_SRP1265A_envelope'
 match=re.search(r'Molex_KK-396_A-41791-00(\d\d)_',f[1])
 if match:model=f'Molex_KK396_{match[1]}_envelope'
 if model:
  f[:]=[n for n in f if not(isinstance(n,list) and n[0]=='model')]
  f.append(S('model','${KIPRJMOD}/models/'+model+'.step',S('offset',S('xyz',0,0,0)),S('scale',S('xyz',1,1,1)),S('rotate',S('xyz',0,0,0))))
p.write_text(dump(b)+'\n')
