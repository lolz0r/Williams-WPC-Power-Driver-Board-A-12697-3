"""JLC-100 GI trigger/load and high-rail capacitor/fuse screening in ngspice.
Unknown harness, transformer and external Fliptronic load are explicit sensitivities.
"""
import hashlib,itertools,json,math
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'output/verification/inventory-safety-final';OUT.mkdir(parents=True,exist_ok=True);ng=NgSpice();cases=[]
def run(name,src,limits):
 p=OUT/(name+'.cir');p.write_text(src);ng.cmd('destroy all');log=ng.run_deck(str(p));p.with_suffix('.log').write_text('\n'.join(log)+'\n');v=measurements(log);errors=[x for x in log if x.startswith('stderr') and 'Note:' not in x];checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()};case=dict(name=name,measurements=v,checks=checks,errors=errors,passed=not errors and all(c['passed'] for c in checks.values()),deck_sha256=hashlib.sha256(src.encode()).hexdigest());cases.append(case);print(name,case['passed'],v,flush=True)
base=(HERE/'decks/gi_string.cir').read_text().split('.options')[0].replace('.include ../models.lib',f'.include {HERE/"models.lib"}').replace('QMMBT4401','J100Q2222').replace('/ 0.025','/ 0.05')
for hz,line in itertools.product([50,60],[.9,1.1]):
 src=base.replace('SIN(0 11.1 60)',f'SIN(0 {11.1*line} {hz})')+'''
.options method=gear reltol=.001 minbreak=1p klu
.tran 5u 1 0 5u
.control
run
let sim_end=time[length(time)-1]
print sim_end
let iabs=abs(i(Vf106))
let ptri=v(mt2i)*i(Vmt)
let isq=iabs*iabs
meas tran rms RMS i(Vf106) from=.8 to=1
meas tran peak MAX iabs
meas tran power AVG ptri from=.8 to=1
meas tran i2t INTEG isq from=0 to=.03
let tj=50+power*13.875
print tj
.endc
.end
'''
 run(f'gi_{hz}_{line}',src,dict(sim_end=(.99999,1.00001),peak=(0,80),i2t=(0,32),rms=(0,5),tj=(0,125)))
# Gate corner derived from actual Rb470/Rg27, HCT output resistance40 ohm,
# +5% resistors, VBE=.95, Vgate=1.3, conservative beta75. Voltage clamps in SPICE
# make this a worst-case algebraic drive check independent from nominal diode fit.
src='''GI low-drive trigger bound
Vout out 0 4.4
Rhct out bsrc 40
Rb bsrc b 493.5
Rpd b 0 10000
Bbe b e V=.95
Bgain 0 e I=75*i(Bbe)
Rg e gate 28.35
Vgate gate 0 1.3
.op
.control
run
let gate_current=i(Vgate)
print gate_current
.endc
.end
'''
run('gate_low_drive',src,dict(gate_current=(.05,.2)))
for hz,line,imbalance in itertools.product([50,60],[.9,1.1],[False,True]):
 # Own BR3 four 1000uF100V NHA capacitors, 3 A sustained load; independent capacitor tolerance and ESR sharing.
 ca,cb=(1200,800) if imbalance else (1000,1000);ra,rb=(.08,.16) if imbalance else (.08,.08)
 src=f'''High rail {hz} Hz {line} line, 3 A continuous engineering load
.include {HERE/'models.lib'}
.model J100GBPC25 D(Is=3e-9 N=1.5 Rs=.0192 Cjo=180p Tt=4u BV=600 Ibv=10u)
Vsec a b SIN(0 {72.7*line} {hz})
Ra a aa .6
Rb b bb .6
Vf aa ab 0
D1 ab dc J100GBPC25
D2 bb dc J100GBPC25
D3 0 ab J100GBPC25
D4 0 bb J100GBPC25
Resra dc ca {ra}
Resrb dc cb {rb}
C8 ca 0 {ca}u
C32 cb 0 {cb}u
Resrc dc cc {rb}
Resrd dc cd {rb}
C64 cc 0 {cb}u
C65 cd 0 {cb}u
Bload dc 0 I=ternary_fcn(time>.1,3,0)*tanh(v(dc))
.save all @c8[i] @c32[i] @c64[i] @c65[i]
.options method=gear reltol=.001 minbreak=1p klu
.tran 10u 1 0 10u uic
.control
run
let sim_end=time[length(time)-1]
print sim_end
meas tran ripple_c8 RMS @c8[i] from=.8 to=1
meas tran ripple_c32 RMS @c32[i] from=.8 to=1
meas tran ripple_c64 RMS @c64[i] from=.8 to=1
meas tran ripple_c65 RMS @c65[i] from=.8 to=1
meas tran fuse_rms RMS i(Vf) from=.8 to=1
meas tran cap_peak MAX v(dc)
.endc
.end
'''
 run(f'highrail_{hz}_{line}_{imbalance}',src,dict(sim_end=(.99999,1.00001),ripple_c8=(0,2.02*(.9 if hz==50 else 1)),ripple_c32=(0,2.02*(.9 if hz==50 else 1)),ripple_c64=(0,2.02*(.9 if hz==50 else 1)),ripple_c65=(0,2.02*(.9 if hz==50 else 1)),fuse_rms=(0,7),cap_peak=(0,90)))
# F112 feeds BR3 AND J104 external Fliptronic AC. Bound an additional 4400 uF
# external capacitance, 20% high tolerance, no load during worst-phase power-on.
for resistance,phase in itertools.product([.6,1.2],[0,90]):
 src=f'''F112 combined capacitor cold inrush bound; external 4400uF assumed
.include {HERE/'models.lib'}
.model J100GBPC25 D(Is=3e-9 N=1.5 Rs=.0192 Cjo=180p Tt=4u BV=600 Ibv=10u)
Vsec a b SIN(0 {72.7*1.1} 50 0 0 {phase})
Rwind a aa {resistance}
Vf aa ab 0
D1 ab dc J100GBPC25
D2 b dc J100GBPC25
D3 0 ab J100GBPC25
D4 0 b J100GBPC25
Csum dc 0 10080u
.options method=gear reltol=.001 minbreak=1p klu
.tran 2u .1 0 2u uic
.control
run
let sim_end=time[length(time)-1]
print sim_end
let isq=i(Vf)*i(Vf)
let iabs=abs(i(Vf))
meas tran i2t INTEG isq from=0 to=.1
meas tran peak MAX iabs
.endc
.end
'''
 run(f'f112_inrush_{resistance}_{phase}',src,dict(sim_end=(.09999,.10001),i2t=(0,139.419),peak=(0,300)))
report=dict(passed=all(c['passed'] for c in cases),cases=cases,limitations=['F112 139.419 A2s is TYPICAL pre-arcing, not a guaranteed repetitive endurance allowance; physical cold/hot/fault tests remain required.','External Fliptronic reservoir 4400uF and winding0.6..1.2ohm are assumptions. Prospective symmetrical current at worst56.55Vrms/.6ohm=94.3A is below200A fuse interruption rating only within this assumed bound.','Highrail 3A sustained DC and all-GI lamp envelopes are engineering load bounds. Actual duty/population/transformer regulation unknown.','BTA08 gate model does not validate real commutation or quadrant timing. 50mA IGT maximum is screened at low drive.'],model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest())
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(0 if report['passed'] else 1)
