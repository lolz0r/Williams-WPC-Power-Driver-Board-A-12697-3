"""STTNG flasher harness inductance, including intentionally open tieback pins.
Read-only design screen; model avalanche is diagnostic, never proof of safe SOA.
"""
from pathlib import Path
import itertools,json,hashlib
from ngspice_lib import NgSpice
from corners import measurements
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
out=ROOT/'output/verification/prespin/flasher-unclamped';out.mkdir(parents=True,exist_ok=True);ng=NgSpice();cases=[]
for lamps,wire,clamp in itertools.product([1,4],[1,10,100],[False,True]):
 name=f'n{lamps}_l{wire}u_clamp{int(clamp)}'
 source=f'''Four maximum STTNG #906 flashers, hot-lamp switch-off, {name}
.include {HERE/'models.lib'}
Vrail rail 0 30
Rlamps rail lp {18/lamps}
Lwire lp drain {wire}u
Vcmd cmd 0 PULSE(0 4.5 100u 20n 20n 1m 5m)
Ro cmd a 40
Rg a gate 100
Rpd gate 0 10k
Vs drain dq 0
XQ dq gate 0 IPD90N10S4L06
'''
 if clamp:source+='Dfly drain rail DS1M\n'
 source+='''.save v(drain) v(gate) i(Vs) i(Lwire)
.options method=gear reltol=.001
.tran 50n 2m 0 100n
.control
run
let absload=abs(i(Lwire))
let pfet=v(drain)*i(Vs)
let sim_end=time[length(time)-1]
print sim_end
meas tran vds_peak MAX v(drain)
meas tran vgs_peak MAX v(gate)
meas tran load_peak MAX absload
meas tran e_turnoff INTEG pfet from=1.099m to=1.2m
.endc
.end
'''
 path=out/(name+'.cir');path.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(path));(out/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
 limits={'sim_end':(.00199999,.00200001),'vds_peak':(0,90),'vgs_peak':(0,15),'load_peak':(0,30/(18/lamps)*1.02)}
 checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
 errors=[l for l in log if l.startswith('stderr') and not l.startswith('stderr Note:') and 'Warning' not in l]
 c=dict(name=name,lamps=lamps,wire_uH=wire,clamp=clamp,checks=checks,measurements=v,errors=errors,passed=not errors and all(x['passed'] for x in checks.values()),deck_sha256=hashlib.sha256(source.encode()).hexdigest());cases.append(c);print(name,c['passed'],v,flush=True)
 result=dict(passed=len(cases)==12 and all(x['passed'] for x in cases),complete=len(cases)==12,cases=cases,limitations=['100 V MOSFET avalanche macro is not an SOA or avalanche-energy qualification','Constant hot 18 ohm filaments isolate turn-off; cold inrush tested separately','1..100 uH is engineering sensitivity, actual harness inductance unknown','On STTNG cathodes for SOL21..28 are open in the existing native board/harness; clamped cases are a comparison, not current hardware'])
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
raise SystemExit(0 if result['passed'] else 1)
