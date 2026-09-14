"""STTNG flashers and gun motors: ROM duty with explicitly bounded loads.
Uses clamped flasher candidate; source parity is checked by verify_rom_logic.py.
"""
import argparse,json,hashlib,itertools
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
from replay_rom import read_edges,worst_window,command_points
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--kind',choices=['flasher','motor'],required=True);p.add_argument('--max-step-us',type=float,default=5);p.add_argument('--channels',nargs='+',type=int);a=p.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
edges,last=read_edges(a.trace);ng=NgSpice();cases=[]
counts={20:1,21:2,22:2,23:4,24:1,25:2,26:3,27:3,28:3}
requests=[(ch,{}) for ch in counts] if a.kind=='flasher' else [(ch,dict(resistance=ohm,emi_H=emi,bemf=emf)) for ch,ohm,emi,emf in itertools.product([17,18],[8,16],[4.7e-6,4.7e-3],[0,8])]
if a.channels:requests=[(ch,par) for ch,par in requests if ch in a.channels]
assert requests,'No applicable channels selected'
for ch,params in requests:
 seq=edges[ch]
 if len(seq)==1:continue
 start,end,duty=worst_window(seq,last);history=max(0,start-.2);duration=end-history+.03;pts=command_points(seq,history,end,duration)
 name=f'sol{ch:02}' if a.kind=='flasher' else f'sol{ch:02}_r{params["resistance"]}_l{params["emi_H"]:g}_emf{params["bemf"]}'
 source=f'''ROM {a.kind} channel {ch}; {name}
.include {HERE/'models.lib'}
Vcmd cmd 0 PWL(
'''+''.join(f'+ {t:.12f} {v:.2f}\n' for t,v in pts)+'''+ )
Ro cmd a 40
Rg a gate 100
Rpd gate 0 10k
Vsense drain dq 0
XQ dq gate 0 J100_AOD66923
Vclamp clamprail 0 30
Vdiode drain da 0
'''
 source+='Dfly da clamprail '+('DS3M' if ch>=25 else 'DS1M')+'\n'
 if a.kind=='flasher':
  # Per-lamp lower-bound hot resistance 18 ohm, 10:1 cold ratio, 8 ms
  # thermal state normalized to 13 V operation. Nonlinear heating/cooling.
  n=counts[ch];source+=f'''Vlamp clamprail feed 0
Rwire feed wire .1
Lwire wire lp 100u
Blamp lp drain I={n}*v(lp,drain)/(1.8+16.2*max(v(theta),0))
Bheat 0 theta I=(v(lp,drain)^2/(1.8+16.2*max(v(theta),0)))/(169/18)
Ctheta theta 0 8m
Rtheta theta 0 1
'''
 else:
  source+=f'''Vraw raw 0 20
Rwire raw feed .1
Lplus feed motp {params['emi_H']}
Lmotor motp m1 10m
Rmotor m1 m2 {params['resistance']}
Vbemf m2 m3 {params['bemf']}
Lminus m3 m4 {params['emi_H']}
Dseries m4 drain D1N4004
'''
 source+=f'''.save v(drain) v(gate) i(Vsense) i(Vdiode) @dfly[capcur]
.options reltol=.002 method=gear
.tran 100u {duration:.9f} 0 {a.max_step_us:g}u
.control
run
let pfet=v(drain)*i(Vsense)
let carrier=i(Vdiode)-@dfly[capcur]
let forward=(abs(carrier)+carrier)/2
let sim_end=time[length(time)-1]
print sim_end
meas tran vds_peak MAX v(drain)
meas tran vgs_peak MAX v(gate)
meas tran current_peak MAX i(Vsense)
meas tran current_avg AVG i(Vsense) from={start-history:.9f} to={end-history:.9f}
meas tran diode_average AVG forward from={start-history:.9f} to={end-history:.9f}
meas tran power_average AVG pfet from={start-history:.9f} to={end-history:.9f}
let tj=50+power_average*62
print tj
.endc
.end
'''
 path=out/(name+'.cir');path.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(path));(out/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
 limits={'sim_end':(duration-1e-7,duration+1e-7),'vds_peak':(0,90),'vgs_peak':(0,15),'current_peak':(0,80),'diode_average':(0,3 if ch>=25 else 1),'tj':(0,125)}
 checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
 errors=[l for l in log if l.startswith('stderr') and not l.startswith('stderr Note:') and 'Warning' not in l]
 c=dict(name=name,channel=ch,load=params if params else dict(lamps=counts[ch],hot_ohm=18,cold_ohm=1.8,thermal_tau_s=.008,wire_uH=100),window_s=[start,end],duty=duty,measurements=v,checks=checks,errors=errors,passed=not errors and all(x['passed'] for x in checks.values()),deck_sha256=hashlib.sha256(source.encode()).hexdigest());cases.append(c);print(name,c['passed'],v,flush=True)
 report=dict(passed=len(cases)==len(requests) and all(x['passed'] for x in cases),complete=len(cases)==len(requests),trace_sha256=hashlib.sha256(a.trace.read_bytes()).hexdigest(),model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest(),max_step_us=a.max_step_us,cases=cases,limitations=['Worst 10 s commanded duty; latch output enabled, separate logic/blanking checks','Flashers: actual bulb counts from Williams printed 2-44, both #89 and #906 approximated by the same lower-resistance thermal envelope; not measured filament data','Flashers require proposed SOL21..28 cathode connection to +20 V on the PCB; original open-tieback board is not represented','Motors: manual 3-22 EMI series diode and two chokes included; 4.7 uH and 4.7 mH cover ambiguous drawing units, 10 mH motor and 8/16 ohm 0/8 V back EMF are sensitivities, not measured A-17562 values','8 ohm simultaneous stalled motors can exceed the shared 3 A rail fuse; passing device stress does not imply indefinite stall operation or prove fuse clearing','TI logic and MOSFET/M7 are approximate device fits; no avalanche/SOA/fuse-clearing or physical thermal claim'])
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)
