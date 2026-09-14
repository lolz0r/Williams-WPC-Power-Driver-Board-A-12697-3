"""Select the stock-qualified onsemi rectifier without changing its compatible pads."""
import json
from pathlib import Path
from sexp import parse,dump,find_all
ROOT=Path(__file__).resolve().parents[1]
code='C235758';cat=json.loads((ROOT/'research/jlcpcb/catalog'/(code+'.json')).read_text())
props={'Value':'MBRB20H100CTT4G','MPN':cat['componentModelEn'],'Manufacturer':cat['componentBrandEn'],'JLCPCB Part':code,'JLCPCB Library':'Extended','Link':cat['url'],'Description':'onsemi100V dual10A Schottky175C,250A surge per leg; 6mA max reverse leakage/leg at125C. Physical A-K-A; anodes paralleled, cathode tab.','Datasheet':'https://www.onsemi.com/download/data-sheet/pdf/mbr20h100ct-d.pdf','Price':'','Price100':''}
refs={f'D{i}' for i in range(105,117)}
for path in [ROOT/'wpc_power_driver_cost.kicad_pcb',ROOT/'power_supply.kicad_sch']:
 doc=parse(path.read_text())[0];seen=set()
 for obj in find_all(doc,'footprint' if path.suffix=='.kicad_pcb' else 'symbol'):
  pr={p[1]:p for p in find_all(obj,'property')};ref=pr.get('Reference',[0,0,''])[2]
  if ref not in refs:continue
  for key,val in props.items():
   assert key in pr,(ref,key)
   pr[key][2]=val
  seen.add(ref)
 assert seen==refs,seen
 if path.suffix=='.kicad_sch':
  for t in find_all(doc,'text'):
   t[1]=t[1].replace('STPS20M100SG','MBRB20H100CTT4G').replace('MBRB30100CT','MBRB20H100CTT4G')
 path.write_text(dump(doc)+'\n')
plan=json.loads((ROOT/'research/selection.json').read_text())
for ref in refs:plan[ref].update(code=code,value=props['Value'],reason=props['Description'])
(ROOT/'research/selection.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Selected onsemi C235758 at all12 SMT rectifier positions; native pad geometry preserved')
