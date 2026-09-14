"""Independent TI RYQ0021B land/stencil and native assembly-origin checks."""
import csv,hashlib,json,math
from pathlib import Path
from sexp import parse,find,find_all
ROOT=Path(__file__).resolve().parents[1];pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';b=parse(pcb.read_text())[0];checks=[];guide=[]
def check(ok,label):checks.append(dict(passed=bool(ok),description=label))
expected={str(i+1):(-2.4,-.75+.5*i,.6,.25) for i in range(4)}
expected.update({str(17-i):(2.4,-.75+.5*i,.6,.25) for i in range(4)})
expected.update({str(k):(x,y,.25,h) for k,x,y,h in [(5,-2.04,1.375,.65),(6,-1.54,1.4,.6),(12,1.54,1.4,.6),(13,2.04,1.375,.65),(18,2.04,-1.375,.65),(19,1.54,-1.4,.6),(20,-1.54,-1.4,.6),(21,-2.04,-1.375,.65)]})
expected.update({str(k):(x,0,.25,3.4) for k,x in [(7,-1.04),(8,-.54),(9,0),(10,.54),(11,1.04)]})
for fp in find_all(b,'footprint'):
 props={p[1]:p[2] for p in find_all(fp,'property')};ref=props['Reference']
 if ref not in ['U20','U21']:continue
 pads=find_all(fp,'pad');copper=[p for p in pads if 'F.Cu' in find(p,'layers')];paste=[p for p in pads if not p[1]]
 check(len(copper)==22 and len(paste)==15,ref+' 21 terminal numbers, overlapping PGND profile, 15 stencil apertures')
 for pin,want in expected.items():
  matches=[p for p in copper if p[1]==pin]
  shapes=[tuple(map(float,find(p,'at')[1:3]+find(p,'size')[1:3])) for p in matches]
  check(any(all(abs(a-z)<1e-6 for a,z in zip(shape,want)) for shape in shapes),ref+' TI land '+pin)
  for p in matches:check(float(find(p,'clearance')[1])==.16,ref+' pad '+pin+' local clearance')
 pg=[p for p in copper if p[1]=='9'];check(any(tuple(map(float,find(p,'size')[1:3]))==(.33,2.35) for p in pg),ref+' stepped PGND center')
 for p in paste:
  check(find(p,'layers')[1:]==['F.Paste'],ref+' paste-only aperture')
  check(tuple(map(float,find(p,'size')[1:3]))==(.25,1.),ref+' segmented power-pad stencil')
 at=list(map(float,find(fp,'at')[1:]));angle=at[2] if len(at)>2 else 0
 check(angle==0 and props['MPN']=='TPS552872QWRYQRQ1',ref+' selected package and orientation')
 guide.append(dict(Designator=ref,MPN=props['MPN'],Mid_X_mm=at[0],Mid_Y_mm=-at[1],Rotation_deg=angle,Pin1_X_mm=at[0]-2.4,Pin1_Y_mm=-(at[1]-.75),Pin1_function='EN/UVLO',Pin1_marker='Left edge, toward upper corner; see assembly PDF'))
report=dict(passed=all(c['passed'] for c in checks),checks=len(checks),failures=[c for c in checks if not c['passed']],pcb_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),source='TI RYQ0021B 4228792/A, recommended land and stencil; TPS552872-Q1 pin table (research/datasheets/TPS552872_Q1.pdf)',limitations='Checks native package geometry and orientation; JLCPCB library rotation mapping must be checked in the actual assembly preview')
OUT=ROOT/'output/release-candidate';(OUT/'reports/ryq-land-pattern.json').write_text(json.dumps(report,indent=2)+'\n')
with (OUT/'assembly/regulator-pin1-guide.csv').open('w') as f:w=csv.DictWriter(f,list(guide[0]));w.writeheader();w.writerows(guide)
print('RYQ geometry:',report['checks'],'checks; passed',report['passed']);raise SystemExit(0 if report['passed'] else 1)
