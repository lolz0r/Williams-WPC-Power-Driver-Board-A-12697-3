"""TI's unencrypted TPS54360 transient model: startup and load steps for U20/U21.
Runs in ngspice PSpice compatibility mode. Vendor average model is encrypted.
Downloaded vendor files stay in ignored .scratch; hashes identify the exact model.
"""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile
import argparse
from ngspice_lib import NgSpice
from corners import measurements

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/verification/revision/vendor-buck';OUT.mkdir(parents=True,exist_ok=True)
folder=ROOT/'.scratch/vendor-models';folder.mkdir(parents=True,exist_ok=True)
archive=folder/'SLVMCT7.zip';lib=folder/'SLVMCT7/TPS54360_PSPICE_TRANS/TPS54360_TRANS.LIB'
if not lib.exists():
 urllib.request.urlretrieve('https://www.ti.com/lit/zip/SLVMCT7',archive)
 with zipfile.ZipFile(archive) as z:z.extractall(folder/'SLVMCT7')
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reuse',action='store_true',help='Reuse a log only when its exact generated input deck matches');parser.add_argument('--case');args=parser.parse_args()
# Engineering sensitivity: lower the model control-current ceiling from
# 61.2 uA * 91.4 kohm = 5.59368 A to 4.5 A. This is a modified vendor model,
# not a manufacturer-provided process corner. Preserve the original model.
minimum_lib=folder/'TPS54360_TRANS_minimum_limit_sensitivity.lib'
original=lib.read_text(encoding='latin1');assert original.count('-1.22u,61.2u)')==1
minimum_source=original.replace('-1.22u,61.2u)',f'-1.22u,{4.5/91400:.12g})')
if not minimum_lib.exists() or minimum_lib.read_text(encoding='latin1')!=minimum_source:minimum_lib.write_text(minimum_source,encoding='latin1')
ng=NgSpice();ng.cmd('set ngbehavior=ps');results=[]
cases=[('5v',8.,False),('5v',15.34,False),('12v',13.,False),('12v',20.69,False),('12v',13.,True),('12v',20.69,True)]
for rail,vin,minimum in cases:
 is5=rail=='5v';vout=5.105 if is5 else 12.;lowload=1. if is5 else .75;highload=3. if is5 else 2.
 ren1,ren2,fb1,fb2,rc,cc,cp=('118k','29.4k','11.3k','2.1k','33.2k','33n','470p') if is5 else ('130k','20k','28k','2k','42.2k','100n','390p')
 name=f'{rail}_vin{vin}'+('_minimum_limit' if minimum else '')
 if args.case and args.case!=name:continue
 p=OUT/(name+'.cir')
 source=f'''TI TPS54360 transient model, {rail} actual compensation, Vin={vin}
.include {minimum_lib if minimum else lib}
.include {ROOT/'tools/spice/models.lib'}
Vin vin 0 PWL(0 0 100u {vin})
Rin vin vinf .02
Cin vinf 0 20u
XU boot comp en 0 sw rt vinf fb 0 TPS54360_TRANS
Ren1 vinf en {ren1}
Ren2 en 0 {ren2}
Rrt rt 0 240k
Cboot boot sw 100n
Rfb1 vout fb {fb1}
Rfb2 fb 0 {fb2}
Rc comp cc {rc}
Cc cc 0 {cc}
Cp comp 0 {cp}
Dcatch 0 sw DB560C
L1 sw linductor 10u
Rdcr linductor vout .025
Cout1 vout c1 330u
Resr1 c1 0 .045
Cout2 vout c2 330u
Resr2 c2 0 .045
Cc3 vout 0 10u
Rload vout 0 {vout/lowload}
Istep vout 0 PWL(0 0 4.5m 0 4.501m {highload-lowload} 6m {highload-lowload} 6.001m 0)
.save v(vout) v(sw) v(comp) i(L1)
.options reltol=.005 abstol=1u vntol=1m method=gear
.tran 100n 8m
.control
run
meas tran output_ss AVG v(vout) from=4m to=4.5m
meas tran output_peak MAX v(vout)
meas tran step_min MIN v(vout) from=4.5m to=5m
meas tran removal_peak MAX v(vout) from=6m to=7m
meas tran highload_ss AVG v(vout) from=5.5m to=6m
meas tran inductor_peak MAX i(L1)
meas tran inductor_running_peak MAX i(L1) from=4m to=8m
.endc
.end
'''
 logpath=OUT/(name+'.log')
 if args.reuse and p.exists() and p.read_text()==source and logpath.exists():log=logpath.read_text().splitlines()
 else:
  p.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(p));logpath.write_text('\n'.join(log)+'\n')
 v=measurements(log)
 limits={'output_ss':(4.95,5.2) if is5 else (11.4,12.6),'output_peak':(0,5.25 if is5 else 12.6),
         'step_min':(4.75,5.25) if is5 else (10.8,12.6),'removal_peak':(0,5.25 if is5 else 12.6),
         'highload_ss':(4.95,5.2) if is5 else (11.4,12.6),'inductor_peak':(0,6.8),'inductor_running_peak':(0,4.5)}
 checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
 errors=[l for l in log if l.startswith('stderr') and 'Warning' not in l]
 results.append(dict(name=name,checks=checks,errors=errors,minimum_current_limit_sensitivity=minimum,deck_sha256=hashlib.sha256(source.encode()).hexdigest(),passed=not errors and all(c['passed'] for c in checks.values())))
 report=dict(source='https://www.ti.com/lit/zip/SLVMCT7',model_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),minimum_limit_model_sha256=hashlib.sha256(minimum_lib.read_bytes()).hexdigest(),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),compatibility='ngspice 47 ngbehavior=ps; TI model v1.10, originally PSpice 16.2; TI SLVAEA1 documents TPS54360B coating change',cases=results,complete=len(results)==len(cases),passed=len(results)==len(cases) and all(r['passed'] for r in results),current_limits='4.5 A is the guaranteed MINIMUM regulator current-limit threshold, not a component absolute maximum. 6.8 A is the maximum threshold. SRP1265A-100M has 10 A thermal / 15.5 A saturation ratings at 25 C. Running peaks must stay below 4.5 A; startup is separately tested with a lowered model ceiling.',limitations='Typical vendor behavioral model; two explicitly modified minimum-current-limit sensitivity cases are not vendor process corners. Catch-diode fit and lumped output ESR/DCR. Does not validate PCB parasitics, physical loop stability, all faults, SOA or thermal shutdown accuracy.')
 (OUT/(name+'.result.json')).write_text(json.dumps(results[-1],indent=2)+'\n')
 if not args.case:(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
 print(name,results[-1],flush=True)
raise SystemExit(0 if (bool(results) and all(r['passed'] for r in results)) else 1)
