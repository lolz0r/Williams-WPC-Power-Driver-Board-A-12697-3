"""Prebiased startup with VIN present and EN initially held low.
Separate from the deliberately abusive output-powered/VIN-clamped-low fixture.
"""
import json,re
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'output/verification/revision/vendor-faults';out=ROOT/'output/verification/revision/vendor-prebiased-start';out.mkdir(exist_ok=True)
ng=NgSpice();ng.cmd('set ngbehavior=ps');results=[]
for rail,vin in [('5v',15.34),('12v',20.69)]:
 source=(base/(rail+'_prebias.cir')).read_text();source=re.sub(r'^Vin vin 0 .*$',f'Vin vin 0 {vin}',source,flags=re.M)
 source=source.replace('Rin vin vinf .02','Rin vin vinf .02\nVenctl enctl 0 PWL(0 1 200u 1 201u 0)\nSen en 0 enctl 0 PRE')
 source=source.replace('10u 1 10.1u 0','200u 1 201u 0')
 p=out/(rail+'.cir');lp=out/(rail+'.log')
 if p.exists() and p.read_text()==source and lp.exists():log=lp.read_text().splitlines()
 else:
  p.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(p));lp.write_text('\n'.join(log)+'\n')
 v=measurements(log)
 errors=[l for l in log if l.startswith('stderr') and 'Warning' not in l and not l.startswith('stderr Note:')];limits={'output_peak':(0,5.25 if rail=='5v' else 12.6),'recovery':(4.95,5.2) if rail=='5v' else (11.4,12.6),'inductor_min':(-1,10)}
 checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
 results.append(dict(name=rail,checks=checks,errors=errors,passed=not errors and all(c['passed'] for c in checks.values())))
 report=dict(cases=results,complete=len(results)==2,passed=len(results)==2 and all(c['passed'] for c in results),scope='VIN already present; output half prebiased, EN held low for 200 us then released. Does not qualify external backfeed into an unpowered raw rail.')
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(results[-1],flush=True)

raise SystemExit(0 if report['passed'] else 1)
