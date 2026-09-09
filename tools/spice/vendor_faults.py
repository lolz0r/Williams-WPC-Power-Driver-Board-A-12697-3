"""TI transient-model UVLO/restart, prebias and short/recovery sensitivities.
Uses exact already-qualified high-line decks; preserves separate evidence.
"""
import hashlib,json,re
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'output/verification/revision/vendor-buck';out=ROOT/'output/verification/revision/vendor-faults';out.mkdir(exist_ok=True)
ng=NgSpice();ng.cmd('set ngbehavior=ps');results=[]
for rail,vin in [('5v',15.34),('12v',20.69)]:
 for scenario in ('uvlo','prebias','short'):
  source=(base/f'{rail}_vin{vin}.cir').read_text();vout=5.105 if rail=='5v' else 12.;name=f'{rail}_{scenario}'
  source=re.sub(r'^Istep.*$', 'Istep vout 0 0',source,flags=re.M)
  if scenario=='uvlo':
   source=source.replace(f'PWL(0 0 100u {vin})',f'PWL(0 0 100u {vin} 4m {vin} 4.1m 3 5m 3 5.1m {vin})')
  elif scenario=='prebias':
   # Precharge capacitor to half nominal output, then remove source at 10 us.
   source=source.replace('Rload vout',f'Vpre pre 0 {vout/2}\nVprectl prectl 0 PWL(0 1 10u 1 10.1u 0)\nSpre pre vout prectl 0 PRE\n.model PRE SW(Ron=.02 Roff=1e12 Vt=.5 Vh=.1)\nRload vout')
  else:
   source=source.replace('Rload vout','Vshort shortctl 0 PWL(0 0 4m 0 4.001m 1 5m 1 5.001m 0)\nSshort vout 0 shortctl 0 SHORT\n.model SHORT SW(Ron=.02 Roff=1e12 Vt=.5 Vh=.1)\nRload vout')
  source=source[:source.index('.control')]+'.control\nrun\nmeas tran output_peak MAX v(vout)\nmeas tran output_min MIN v(vout) from=20u to=8m\nmeas tran recovery AVG v(vout) from=7.5m to=8m\nmeas tran inductor_peak MAX i(L1)\nmeas tran inductor_min MIN i(L1)\n.endc\n.end\n'
  path=out/(name+'.cir');logpath=out/(name+'.log')
  if path.exists() and path.read_text()==source and logpath.exists():log=logpath.read_text().splitlines()
  else:path.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(path));logpath.write_text('\n'.join(log)+'\n')
  v=measurements(log);limits={'output_peak':(0,5.25 if rail=='5v' else 12.6),'output_min':(-.3,13),'recovery':(4.95,5.2) if rail=='5v' else (11.4,12.6),'inductor_peak':(0,10),'inductor_min':(-1,10)}
  checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()};errors=[l for l in log if l.startswith('stderr') and 'Warning' not in l]
  results.append(dict(name=name,checks=checks,errors=errors,deck_sha256=hashlib.sha256(source.encode()).hexdigest(),passed=not errors and all(c['passed'] for c in checks.values())))
  report=dict(cases=results,complete=len(results)==6,passed=len(results)==6 and all(c['passed'] for c in results),limits='Short-circuit transient 10 A bound equals the selected inductor thermal rating at 25 C; not a converter current-limit accuracy test. Model overshoot does not qualify switch SOA.',limitations=['Typical TI behavioral model, no PCB parasitics or thermal feedback','Shorts last 1 ms; no claim of repeated/continuous fault survival','Prebias source is an artificial isolated charging fixture, not proof of tolerance to arbitrary backfeeding'])
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(results[-1],flush=True)
raise SystemExit(0 if report['passed'] else 1)
