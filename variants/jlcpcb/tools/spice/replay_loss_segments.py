"""Refine loss of a ROM coil window, compressing only fully settled OFF gaps.
Electrical parameters are unchanged. Preserve at least 100 ms OFF (>30 RL tau)
where a long gap is shortened; scale total energy by original ten-second window.
"""
import argparse,json,hashlib
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
from replay_rom import read_edges,worst_window
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--step-us',type=float,required=True);p.add_argument('--vendor-diode',action='store_true');p.add_argument('--strict',action='store_true');a=p.parse_args()
trace=ROOT/'output/verification/pinmame/gameplay-prespin/bus.csv';edges,last=read_edges(trace);seq=edges[1];start,end,duty=worst_window(seq,last)
# This selected window starts with a rising edge and ends OFF, so no partial
# pulse energy crosses its boundaries. Check those prerequisites explicitly.
selected=[(t,s) for t,s in seq if start<=t<=end];assert selected[0]==(start,1) and selected[-1][1]==0
kept=[];shift=0.;last_t=start;state=0;removed=0.
for t,s in selected:
 gap=t-last_t
 if state==0 and gap>.1:shift+=gap-.1;removed+=gap-.1
 kept.append((.05+t-start-shift,s));last_t=t;state=s
stop=kept[-1][0]+.05
points=[(0.,0.)];state=0
for t,s in kept:points.extend([(t-20e-9,4.5*state),(t,4.5*s)]);state=s
points.append((stop,0.));assert all(x[0]<y[0] for x,y in zip(points,points[1:]))
out=ROOT/'output/verification/prespin/replay-loss-segments';out.mkdir(exist_ok=True,parents=True);name=f'coil1_{a.step_us:g}us'+('_vendor_diode' if a.vendor_diode else '')+('_strict' if a.strict else '')
source=f'''Actual coil-1 ROM pulses with only settled OFF time compressed; {name}
.include {HERE/'models.lib'}
'''
vendor=ROOT/'.scratch/vendor-models/S3M.spice.txt'
if a.vendor_diode:source+=f'.include {vendor}\n'
source+='Vcmd cmd 0 PWL(\n'+''.join(f'+ {t:.12f} {v:g}\n' for t,v in points)+'+ )\n'
source+=f'''Vrail rail 0 86
Ro cmd a 40
Rg a gate 100
Rpd gate 0 10k
Vsense drain dq 0
XQ dq gate 0 IPD90N10S4L06
Lcoil drain cl 12m
Rcoil cl rail 3.78
Dfly drain rail {'DI_S3M' if a.vendor_diode else 'DS3M'}
.save v(dq) v(gate) i(Vsense) i(Lcoil) @m.xq.m1[id] @d.xq.db[id] @d.xq.db[capcur]
.options method=trap reltol={'.0001 trtol=1 chgtol=1e-16 itl4=500' if a.strict else '.002'}
.tran 1u {stop:.12f} 0 {a.step_us:g}u
.control
run
let loss_channel=v(dq)*@m.xq.m1[id]
let loss_body=-v(dq)*(@d.xq.db[id]-@d.xq.db[capcur])
let loss_total=loss_channel+loss_body
let terminal_power=v(dq)*i(Vsense)
let icoil=abs(i(Lcoil))
let sim_end=time[length(time)-1]
print sim_end
meas tran e_dissipation INTEG loss_total
meas tran e_terminal INTEG terminal_power
meas tran vds_peak MAX v(dq)
meas tran coil_peak MAX icoil
meas tran fet_terminal_peak MAX i(Vsense)
let dissipation_W=e_dissipation/{end-start:g}
let terminal_W=e_terminal/{end-start:g}
let tj_dissipation=50+dissipation_W*62
let tj_terminal=50+terminal_W*62
print dissipation_W
print terminal_W
print tj_dissipation
print tj_terminal
.endc
.end
'''
path=out/(name+'.cir');path.write_text(source);ng=NgSpice();log=ng.run_deck(str(path));(out/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
limits={'sim_end':(stop-1e-7,stop+1e-7),'vds_peak':(0,90),'coil_peak':(0,86/3.78*1.02),'tj_dissipation':(0,125),'tj_terminal':(0,125)}
checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()};errors=[l for l in log if l.startswith('stderr') and not l.startswith('stderr Note:') and 'Warning' not in l]
report=dict(passed=not errors and all(x['passed'] for x in checks.values()),step_us=a.step_us,vendor_diode=a.vendor_diode,checks=checks,errors=errors,measurements=v,original_window_s=[start,end],simulated_s=stop,removed_idle_s=removed,trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),deck_sha256=hashlib.sha256(source.encode()).hexdigest(),model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest(),vendor_diode_sha256=hashlib.sha256(vendor.read_bytes()).hexdigest() if a.vendor_diode else None,limitations=['Only OFF gaps shortened; at least 100 ms OFF exceeds 30 coil L/R time constants. No physical thermal feedback in this lumped model, so energy can be averaged over the original duration','Initial 50 ms and final 50 ms allow electrical settling; their leakage/switching losses are included conservatively','Channel+body carrier loss excludes reactive MOSFET capacitance current; terminal-energy metric retained independently','Vendor diode comparison uses unmodified Diodes Inc S3M model; approximate hot MOSFET fit retained','Peak terminal current includes displacement/recovery and is reported separately, not treated as a continuous-current/SOA guarantee'])
(out/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
