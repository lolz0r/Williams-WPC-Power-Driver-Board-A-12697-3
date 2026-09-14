"""Additional bounded electrical checks for the JLCPCB substitutions.
M7 uses an approximate diode fit, not a manufacturer SPICE model. Wiring
inductance and temperature sweeps do not qualify arbitrary inductive loads.
"""
import hashlib,itertools,json
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/verification/revision/jlc-substitutions';OUT.mkdir(parents=True,exist_ok=True)
ng=NgSpice();cases=[]
def run(name,source,limits):
    p=OUT/(name+'.cir');p.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(p));(OUT/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
    errors=[s for s in log if s.startswith('stderr') and 'Warning' not in s]
    checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
    cases.append(dict(name=name,checks=checks,errors=errors,deck_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),passed=not errors and all(c['passed'] for c in checks.values())))

for supply,vf,tolerance in itertools.product([4.95,5.2],[1.6,2.6],[.99,1.01]):
    run(f'led4_v{supply}_vf{vf}_r{tolerance}',f'''LED4 worst-case constant forward voltage; selected NCD0805R1 and 470R
Vcc vcc 0 {supply}
R192 vcc led {470*tolerance}
Vled led 0 {vf}
.tran 1u 10u
.control
run
let current=i(Vled)
let rp=(v(vcc)-v(led))*current
meas tran led_current AVG current
meas tran resistor_power AVG rp
.endc
.end
''',dict(led_current=(0,.025),resistor_power=(0,.125)))

for temp,wire_uH,tt_us in itertools.product([25,125],[1,10,100],[.1,2,10]):
    run(f'm7_t{temp}_l{wire_uH}_tt{tt_us}',f'''M7 flasher clamp, 30 V rail, hot #89 lamp 18 ohms, wiring inductance sensitivity
Vrail rail 0 30
Rlamp rail load 18
Lwire load drain {wire_uH}u
Vgate ctl 0 PULSE(0 5 100u 100n 100n 1m 100m)
Sdriver drain 0 ctl 0 DRIVER
.model DRIVER SW(Ron=.02 Roff=1e10 Vt=2.5 Vh=.1)
Vmeasure drain da 0
Dfly da rail M7FIT
.model M7FIT D(Is=5e-9 n=1.8 Rs=.08 Cjo=15p Tt={tt_us}u Bv=1000 Ibv=5u)
.temp {temp}
.save v(drain) v(rail) i(Vmeasure) @dfly[capcur]
.options method=gear reltol=.001
.tran .1u 4m
.control
run
let carrier=i(Vmeasure)-@dfly[capcur]
let forward=(abs(carrier)+carrier)/2
let terminal=(abs(i(Vmeasure))+i(Vmeasure))/2
let reverse=v(rail)-v(drain)
meas tran carrier_average AVG forward
meas tran terminal_average AVG terminal
meas tran clamp_peak MAX v(drain)
meas tran reverse_peak MAX reverse
.endc
.end
''',dict(carrier_average=(0,1),terminal_average=(0,1),clamp_peak=(0,35),reverse_peak=(0,1000)))

pullup_current=5.2/(4700*.99);pullup_power=5.2*pullup_current
report=dict(cases=cases,passed=all(c['passed'] for c in cases) and pullup_current<.006 and pullup_power<.125,pullup_static_bound=dict(supply_V=5.2,resistance_min_ohms=4653,current_A=pullup_current,power_W=pullup_power),sources=['https://www.microdiode.com/uploadfiles/PDF/M1-THRU-M7-SMA.pdf','https://jlcpcb.com/partdetail/C84256','https://jlcpcb.com/partdetail/C17673'],limitations=['LED modeled as its specified forward-voltage limits; reduced +5V LED current reduces brightness','M7 approximate fit, not vendor model; reverse recovery is a 0.1..10 us engineering sensitivity because the MDD datasheet does not guarantee it','30 V, hot 18 ohm flasher and 1..100 uH wiring; not a model of a replacement solenoid connected to a flasher output','1 A is average forward rating; 35 V clamp bound protects the 100 V MOSFET with margin under these assumptions','Pull-up low-output current bound applies to 4.7k resistors; HCT TTL input thresholds retained'])
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(len(cases),'cases',sum(c['passed'] for c in cases),'passed');print([c for c in cases if not c['passed']]);raise SystemExit(0 if report['passed'] else 1)
