"""Select stocked KEMET 0805 compensation capacitors; electrical values unchanged."""
from pathlib import Path
from sexp import parse,dump,find_all
changes={'CL21B333KBANNNC':('C0805C333K5RACTU','411440'),
         'CL21C471JBANNNC':('C0805C471J5GACTU','411132'),
         'CL21C391JBANNNC':('C0805C391J5GACTU',None),
         'CL21B103KBANNNC':('C0805C103K5RACTU','411157')}
def update(node):
 if not isinstance(node,list):return
 props={p[1]:p for p in find_all(node,'property')}
 mpn=props.get('MPN',[None,None,None])[2]
 if mpn in changes:
  new,pid=changes[mpn];props['MPN'][2]=new;props['Manufacturer'][2]='KEMET'
  props['Link'][2]='https://search.kemet.com/download/specsheet/'+new
 for n in node:update(n)
for p in [*Path('.').glob('*.kicad_sch'),Path('wpc_power_driver_cost.kicad_pcb')]:
 original=p.read_text()
 if not any(m in original for m in changes):continue
 b=parse(original)[0];update(b);p.write_text(dump(b)+'\n')
p=Path('tools/sourcing.py');lines=p.read_text().splitlines()
for i,line in enumerate(lines):
 for old,(new,pid) in changes.items():
  if old in line:lines[i]=line.replace(old,new).replace("mfr='Samsung'","mfr='KEMET'")
p.write_text('\n'.join(lines)+'\n')
