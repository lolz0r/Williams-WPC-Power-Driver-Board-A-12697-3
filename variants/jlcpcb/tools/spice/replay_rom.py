"""Replay worst 10 s commanded-duty windows into actual driver-topology SPICE.
Uses raw CPU bus writes. Coil R/L are explicit approximations, not measured parts.
"""
import argparse
import bisect
import csv
import hashlib
import json
from pathlib import Path
import sys
from ngspice_lib import NgSpice
from corners import measurements

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'mame'))
from analyze_trace import REGS

def read_edges(path):
 edges={n:[(0.,0)] for n in range(1,29)};last=0.
 with path.open() as f:
  for row in csv.DictReader(f):
   t=float(row['time']);assert t>=last,'Non-monotonic emulator timestamps';last=t
   address=int(row['address'],16)
   if row['kind']!='W' or address not in REGS:continue
   base,bits=REGS[address];value=int(row['data'],16)
   for bit in range(bits):
    sequence=edges[base+bit];state=(value>>bit)&1
    if state!=sequence[-1][1]:sequence.append((t,state))
 return edges,last

def worst_window(sequence,last,width=10.):
 times=[t for t,s in sequence];area=[0.]
 for (t,state),(end,_) in zip(sequence,sequence[1:]):area.append(area[-1]+(end-t)*state)
 def integral(t):
  if t<=0:return 0.
  i=bisect.bisect_right(times,t)-1
  return area[i]+(t-times[i])*sequence[i][1]
 ends={min(last,max(width,t+shift)) for t in times for shift in (0,width)}
 end=max(ends,key=lambda t:integral(t)-integral(t-width))
 return max(0.,end-width),end,(integral(end)-integral(end-width))/width

def command_points(sequence, history, end, duration, slew=20e-9):
 """Finite command edges with strictly increasing PWL times, including end events."""
 state=sequence[bisect.bisect_right([t for t,s in sequence],history)-1][1]
 points=[(0.,4.5*state)]
 for timestamp,new in sequence:
  if not history<timestamp<=end:continue
  at=timestamp-history
  # A bus trace can contain multiple writes at one timestamp: last write wins.
  if at==points[-1][0]:points[-1]=(at,4.5*new);state=new;continue
  assert at>points[-1][0]
  before=max(at-slew,(at+points[-1][0])/2)
  points.extend([(before,4.5*state),(at,4.5*new)]);state=new
 stop=end-history
 if stop>points[-1][0]:points.append((stop,4.5*state))
 points.extend([(stop+slew,0.),(duration,0.)])
 assert all(b[0]>a[0] for a,b in zip(points,points[1:])), 'Non-increasing PWL points'
 return points

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--channels',nargs='+',type=int,choices=range(1,17),default=list(range(1,17)));p.add_argument('--max-step-us',type=float,default=5.);p.add_argument('--method',choices=['trap','gear'],default='trap');p.add_argument('--reltol',type=float,default=.002);p.add_argument('--klu',action='store_true');p.add_argument('--channel-loss',action='store_true');a=p.parse_args();assert 0<a.max_step_us<=100
 a.output.mkdir(parents=True,exist_ok=True);edges,last=read_edges(a.trace);ng=NgSpice();results=[]
 for channel in a.channels:
  seq=edges[channel]
  if len(seq)==1:continue
  start,end,duty=worst_window(seq,last);history=max(0,start-.2);duration=end-history+.03
  points=command_points(seq,history,end,duration)
  resistance=4.2 if channel<=8 or channel==16 else 14.5 if channel==11 else 9.6 if channel==15 else 10.8
  inductance=.012 if channel<=8 or channel==16 else .03 if channel==11 else .025
  resistance*=.9 # cold tolerance bound at 20 C, independently applied hot MOSFET fit
  source=f'''ROM raw-write replay channel {channel}; {a.trace.name}
.include {HERE/'models.lib'}
Vrail rail 0 86
Vcmd cmd 0 PWL(
'''+''.join(f'+ {t:.12f} {v:.2f}\n' for t,v in points)+f'''+ )
Rout cmd gateinput 40
Rg gateinput gate 100
Rpd gate 0 10k
Vsense drain drainq 0
XQ drainq gate 0 IPD90N10S4L06
Lcoil drain coil {inductance}
Rcoil coil rail {resistance}
Vdiode drain diode 0
Dfly diode rail DS3M
.save v(drainq) v(gate) i(Vsense) i(Vdiode) i(Lcoil) @dfly[capcur]{' @m.xq.m1[id] @d.xq.db[id] @d.xq.db[capcur]' if a.channel_loss else ''}
.options reltol={a.reltol:g} method={a.method} maxord=2{' klu itl4=100' if a.klu else ''}
.tran 100u {duration:.9f} 0 {a.max_step_us:g}u
.control
set numdgt=12
run
let pfet=v(drainq)*i(Vsense)
* Separate carrier conduction from the diode stored-charge current.
* Rectifying numerical capacitor ringing otherwise biases the forward average.
* Keep the original terminal-current metric for independent review.
let id_terminal=(abs(i(Vdiode))+i(Vdiode))/2
let diode_conduction=i(Vdiode)-@dfly[capcur]
let id=(abs(diode_conduction)+diode_conduction)/2
let icoil=abs(i(Lcoil))
let sim_end=time[length(time)-1]
print sim_end
meas tran vds_peak MAX v(drainq)
meas tran vgs_peak MAX v(gate)
meas tran p_avg AVG pfet from={start-history:.9f} to={end-history:.9f}
meas tran id_avg AVG id from={start-history:.9f} to={end-history:.9f}
meas tran id_terminal_avg AVG id_terminal from={start-history:.9f} to={end-history:.9f}
meas tran i_peak MAX i(Vsense)
meas tran coil_peak MAX icoil
let tj_repeating=50+p_avg*62
print tj_repeating
.endc
.end
'''
  if a.channel_loss:
   extra=f'''* Channel + body carrier loss excludes reactive displacement current.
let loss_channel=v(drainq)*@m.xq.m1[id]
let loss_body=-v(drainq)*(@d.xq.db[id]-@d.xq.db[capcur])
let loss_total=loss_channel+loss_body
meas tran p_dissipation AVG loss_total from={start-history:.9f} to={end-history:.9f}
let tj_dissipation=50+p_dissipation*62
print tj_dissipation
'''
   source=source.replace('.endc',extra+'.endc')
  path=a.output/f'sol{channel:02d}.cir';path.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(path));values=measurements(log)
  (a.output/f'sol{channel:02d}.log').write_text('\n'.join(log)+'\n')
  limits={'vds_peak':(0,90),'vgs_peak':(0,15),'tj_repeating':(0,125),'id_avg':(0,3),'i_peak':(0,80),'coil_peak':(0,86/resistance*1.02),'sim_end':(duration-1e-7,duration+1e-7)}
  if a.channel_loss:limits.update(p_dissipation=(0,75/62),tj_dissipation=(0,125))
  checks={k:dict(value=values.get(k),min=lo,max=hi,passed=k in values and lo<=values[k]<=hi) for k,(lo,hi) in limits.items()}
  errors=[l for l in log if l.startswith('stderr') and not l.startswith('stderr Note:') and ('Warning' not in l or 'non-increasing' in l)]
  result=dict(dissipation_W=values.get('p_dissipation'),dissipation_tj_C=values.get('tj_dissipation'),diode_terminal_forward_average_A=values.get('id_terminal_avg'),deck_sha256=hashlib.sha256(source.encode()).hexdigest(),channel=channel,window_s=[start,end],commanded_duty=duty,coil_ohm=resistance,coil_H=inductance,rail_V=86,checks=checks,errors=errors,passed=not errors and all(c['passed'] for c in checks.values()))
  results.append(result);print(channel,'PASS' if result['passed'] else 'FAIL',values,flush=True)
 report=dict(solver='KLU/itl4=100' if a.klu else 'SPARSE/default iterations',method=a.method,reltol=a.reltol,max_step_us=a.max_step_us,requested_channels=a.channels,trace_sha256=hashlib.sha256(a.trace.read_bytes()).hexdigest(),model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest(),cases=results,passed=bool(results) and all(r['passed'] for r in results),limitations=['Integration method and maximum step recorded in report, 20 ns command transitions, strict PWL times and explicit end-time completion; no partial transient may pass','Forward diode rating uses carrier-conduction current after subtracting ngspice capcur; original positive terminal-current average is also reported. Electrical device and stored-charge model unchanged', 'Coil R/L approximations; 86 V high-line bound with 4.5 V gate and hot MOSFET fit','Commands assumed enabled; no credit for physical blanking','Temperature is steady repetition of worst 10 s window at 50 C ambient and 62 C/W, excludes mutual heating','Channels 17-28 motors/flashers excluded here; covered by generic decks only','No harness parasitics, avalanche SOA, fuse clearing or physical thermal correlation'])
 (a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
