"""Bind selected components, complete BOM, schematic nets and model assumptions."""
import csv,hashlib,json,math,re
from pathlib import Path
import xml.etree.ElementTree as ET
from sexp import parse,find,find_all
from verify_artifacts import audit
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/release-candidate';pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';net=OUT/'reports/netlist.xml';checks=[]
def check(ok,description):checks.append(dict(passed=bool(ok),description=description))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=parse(pcb.read_text())[0];fps={next(p[2] for p in find_all(f,'property') if p[1]=='Reference'):f for f in find_all(b,'footprint')};props={r:{p[1]:p[2] for p in find_all(f,'property')} for r,f in fps.items()}
sel=json.loads((ROOT/'research/selection.json').read_text())
for ref,s in sel.items():check(props[ref]['JLCPCB Part']==s['code'],ref+' matches selected catalog code')
check(audit(pcb,net)['passed'],'Every native component field and pad net agrees with fresh schematic netlist')
for ref in ['U20','U21']:check(props[ref]['MPN']=='TPS552872QWRYQRQ1',ref+' exact RYQ21 TI controller')
check(props['R266']['Value']=='33K','5V compensation R266=33k, as simulated')
for ref in ['C5','C59','C6','C60','C7','C61','C11','C62','C30','C63']:check(props[ref]['JLCPCB Part']=='C443892' and props[ref]['Value']=='4700uF 35V',ref+' GPD 4700uF35V')
for ref in ['C8','C32','C64','C65']:check(props[ref]['JLCPCB Part']=='C3445915' and props[ref]['Value']=='1000uF 100V',ref+' NHA 1000uF100V')
for group,expected in [(['C5','C59'],'/Power_Supply/+5V_RAW'),(['C6','C60','C7','C61'],'+18V'),(['C11','C62'],'+20V'),(['C30','C63'],'+12VU'),(['C8','C32','C64','C65'],'+50V')]:
 for r in group:
  nets={p[1]:str(find(p,'net')[-1]) for p in find_all(fps[r],'pad')};check(nets=={'1':expected,'2':'GND'},r+' bank polarity and rail')
check(sum(p.get('JLCPCB Part')=='C485687' for p in props.values())==28,'All 28 replaced power drivers use the replayed AOD66923')
for r in ['Q9','Q11','Q13','Q15','Q17']:check(props[r]['JLCPCB Part']=='C8512',r+' MMBT2222A gate source')
for r in ['Q10','Q12','Q14','Q16','Q18']:check(props[r]['JLCPCB Part']=='C9102',r+' four-quadrant BTA08-600CRG')
for r in [f'D{i}' for i in range(105,117)]:check(props[r]['JLCPCB Part']=='C235758' and props[r]['MPN']=='MBRB20H100CTT4G',r+' selected onsemi rectifier, final conduction/leakage fixture')
check(props['J115']['Purchased Quantity']=='2','J115 two-piece assembly quantity native to design')
check(sum('Holder JLCPCB Part' in p for p in props.values())==13,'All 13 cartridge assemblies specify separate holders in the native design')
check(props['F112']['JLCPCB Part']=='C3014110','F112 remains 7 A time-lag, changed to stocked SMT TA7')
for p in find_all(fps['F112'],'pad'):check(tuple(map(float,find(p,'size')[1:]))==(2.5,3.0) and abs(float(find(p,'at')[1]))==2.75,'TLC recommended 2410 fuse land spacing/size')
for p in find_all(fps['BR3'],'pad'):
 expected={'1':(0,-6.4),'2':(18,11.6),'3':(0,11.6),'4':(18,-6.4)}[p[1]];check(tuple(map(float,find(p,'at')[1:3]))==expected,'BR3 formed lead pattern pad '+p[1])
models=[];missing=[]
for ref,fp in fps.items():
 for m in find_all(fp,'model'):
  raw=m[1].replace('${KIPRJMOD}',str(ROOT));p=Path(raw)
  if not p.exists():missing.append(dict(ref=ref,path=raw))
  else:models.append(p)
check(not missing,'All referenced assembly models are local and present')
source=json.loads((OUT/'reports/jlc-sourcing.json').read_text());check(source['passed'] and not source['shortfalls'],'Complete 100-board electronics purchasing inventory with reserve')
check(source['native_populated_electronic_references']==426 and source['purchased_electronic_units']==440,'426 populated electronic references / 440 purchased units')
check(source['smt_placements']==345 and source['through_hole_native_references']==81,'345 SMT and 81 THT native placements')
# Preserve all original files recorded before this independent variant was created.
baseline=json.loads((ROOT/'research/baseline-sources.json').read_text());unchanged={p:Path(p).exists() and sha(Path(p))==h for p,h in baseline.items()};check(all(unchanged.values()),'Original JLC-3 source files match pre-variant hashes')
report=dict(passed=all(c['passed'] for c in checks),checks=len(checks),failures=[c for c in checks if not c['passed']],pcb_sha256=sha(pcb),netlist_sha256=sha(net),missing_models=missing,model_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(models))},original_sources_unchanged=all(unchanged.values()),original_sources_checked=len(unchanged),limitations=['Electrical simulations are engineering fixtures with stated loads and model bounds, not an extracted whole-board simulation. Native component/net parity and this audit bind their assumptions to the selected design.','Passive fit, gate-drive, commutation, thermal boundaries, cable fit, fuses and actual JLC assembly orientation require physical qualification.'])
(OUT/'reports/inventory-design.json').write_text(json.dumps(report,indent=2)+'\n');print('Inventory design:',report['passed'],report['checks'],report['failures']);raise SystemExit(0 if report['passed'] else 1)
