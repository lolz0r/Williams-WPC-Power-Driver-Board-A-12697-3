"""Engineering experiment: bypass reverse current around the buck power switch.
NOT a PCB change unless explicitly promoted after electrical/layout checks.
"""
import hashlib,json,re
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'output/verification/revision/vendor-faults';out=ROOT/'output/verification/revision/reverse-protection-trial';out.mkdir(exist_ok=True)
ng=NgSpice();ng.cmd('set ngbehavior=ps');results=[]
for name in ('5v_uvlo','5v_prebias'):
 source=(base/(name+'.cir')).read_text().replace('Rin vin vinf .02','Rin vin vinf .02\nVreverse vout reverse 0\nDreverse reverse vinf DB560C')
 source=source.replace('.tran 100n 8m','.tran 100n 12m').replace('from=7.5m to=8m','from=11.5m to=12m')
 source=source.replace('.save v(vout) v(sw) v(comp) i(L1)','.save v(vout) v(sw) v(comp) i(L1) i(Vreverse)')
 source=source.replace('.endc','meas tran bypass_peak MAX i(Vreverse)\n.endc')
 p=out/(name+'.cir');p.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(p));(out/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
 errors=[l for l in log if l.startswith('stderr') and 'Warning' not in l];limits={'output_peak':(0,5.25),'recovery':(4.95,5.2),'inductor_min':(-1,10),'bypass_peak':(0,150)}
 checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
 results.append(dict(name=name,checks=checks,errors=errors,passed=not errors and all(c['passed'] for c in checks.values())))
 (out/'results.json').write_text(json.dumps({'cases':results,'complete':len(results)==2,'pcb_changed':False,'limitations':'Approximate bypass-diode model; IFSM comparison alone is not surge qualification.'},indent=2)+'\n');print(results[-1],flush=True)
