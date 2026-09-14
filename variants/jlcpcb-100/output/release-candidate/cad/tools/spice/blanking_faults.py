"""Assert external BLANKING while representative coil/lamp/GI loads are on.
Sweep guaranteed TTL recognition range and ribbon capacitance. No watchdog model.
"""
import hashlib,json
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
out=ROOT/'output/verification/prespin/blanking';out.mkdir(parents=True,exist_ok=True)
original=(HERE/'decks/powerup.cir').read_text();ng=NgSpice();cases=[]
for vcc in [4.5,5.2]:
 for threshold in [.8,2.0]:
  for hz in [50,60]:
   name=f'blank_{vcc:g}V_{threshold:g}Vth_{hz}Hz'
   source=original[:original.index('.tran')]
   source=source[source.index('.include'):].replace('.include ../models.lib',f'.include {HERE/"models.lib"}')
   source=f'Assert BLANKING at 15 ms under active loads; {name}\n'+source
   source=source.replace('V50 v50 0 70','V50 v50 0 86').replace('V18 v18 0 18','V18 v18 0 30').replace('Vac ac 0 SIN(0 9.6 60)',f'Vac ac 0 SIN(0 11.1 {hz})')
   source=source.replace('Bvcc vcc 0 V = (time < 30m) ? 0 : min(5, (time - 30m) / 2m * 5)',f'Vvcc vcc 0 {vcc}')
   source=source.replace('Vcpu cpu 0 PULSE(0 5 200m 1u 1u 1 2)','Vcpu cpu 0 PWL(0 5 15m 5 15.00002m 0 30m 0 30.00002m 5)\nCblank blank 0 280p')
   source=source.replace('Bdat dat 0 V = (time < 240m) ? 1 : 0','Bdat dat 0 V = (time < 25m) ? 1 : 0')
   source=source.replace('((v(vcc) > 2.0) && (v(blank) < 0.5*v(vcc)))',f'(v(blank) < {threshold})')
   source=source.replace('Sq q lq en 0 SWL','Sq q lq en 0 SWL')
   source=source.replace('Scpu blank 0 cpu 0 SWL','Scpu blank 0 cpu 0 SWCPU\n.model SWCPU SW(Ron=25 Roff=1e9 Vt=.5 Vh=.1)')
   source=source.replace('XQ out g 0 IPD90N10S4L06','Vsense out drainq 0\nXQ drainq g 0 IPD90N10S4L06')
   source=source.replace('IPD90N10S4L06','J100_AOD66923').replace('QMMBT4401','J100Q2222').replace('/ 0.025','/ 0.05')
   source+='''
.save v(blank) v(g) v(cg) v(out) i(Vsense) i(Vcol) i(Vstr)
.options method=gear reltol=.002 minbreak=1p
.tran 1u 40m 0 500n
.control
run
let ifet=abs(i(Vsense))
let icol=abs(i(Vcol))
let igi=abs(i(Vstr))
let sim_end=time[length(time)-1]
print sim_end
meas tran fet_on MAX ifet from=10m to=14m
meas tran col_on MAX icol from=10m to=14m
meas tran gi_on MAX igi from=1m to=14m
meas tran gate_off MAX v(g) from=15.5m to=29m
meas tran fet_off MAX ifet from=15.5m to=29m
meas tran col_off MAX icol from=15.5m to=29m
meas tran gi_off MAX igi from=27m to=29m
meas tran fet_restart MAX ifet from=31m to=40m
meas tran col_restart MAX icol from=31m to=40m
meas tran gi_restart MAX igi from=31m to=40m
meas tran blank_high MIN v(blank) from=15.01m to=29m
.endc
.end
'''
   path=out/(name+'.cir');path.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(path));(out/(name+'.log')).write_text('\n'.join(log)+'\n');values=measurements(log)
   limits={'sim_end':(.03999999,.04000001),'fet_on':(1,80),'col_on':(1,20),'gi_on':(1,15),'gate_off':(0,.8),'fet_off':(0,.01),'col_off':(0,.01),'gi_off':(0,.001),'fet_restart':(0,.01),'col_restart':(0,.01),'gi_restart':(0,.001),'blank_high':(4.4,5.3)}
   checks={k:dict(value=values.get(k),min=lo,max=hi,passed=k in values and lo<=values[k]<=hi) for k,(lo,hi) in limits.items()}
   errors=[l for l in log if l.startswith('stderr') and not l.startswith('stderr Note:') and 'Warning' not in l]
   case=dict(name=name,checks=checks,errors=errors,passed=all(x['passed'] for x in checks.values()) and not errors,deck_sha256=hashlib.sha256(source.encode()).hexdigest());cases.append(case);print(name,case['passed'],values,flush=True)
   report=dict(passed=len(cases)==8 and all(x['passed'] for x in cases),complete=len(cases)==8,cases=cases,model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest(),limitations=['External BLANKING asserted by fixture, does not verify CPU watchdog generation','Full 4.5 or 5.2 V supply; HCT partial-power or power-off behavior remains unqualified','280 pF lumped BLANKING load: 200 pF ribbon plus 80 pF input allowance','Threshold extremes .8 and 2 V model guaranteed TTL bands; not measured threshold distribution','Gate-driver/triac models are approximate; GI may continue to next AC current zero','Writes of zero at 25 ms and release of BLANKING at 30 ms are explicit firmware-order assumptions'])
   (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)
