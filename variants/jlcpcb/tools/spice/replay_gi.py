"""Actual ROM GI gate commands and approximate triac/filament response.
Sweep relative AC phase because emulator ZC timing is not a measured detector.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
from replay_rom import worst_window,command_points
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('trace',type=Path);a=p.parse_args();out=ROOT/'output/verification/prespin/replay-gi';out.mkdir(exist_ok=True,parents=True)
edges={i:[(0.,0)] for i in range(5)};last=0
for row in csv.DictReader(a.trace.open()):
 last=float(row['time'])
 if row['kind']=='W' and int(row['address'],16)==0x3fe6:
  word=int(row['data'],16)
  for bit,seq in edges.items():
   val=(word>>bit)&1
   if val!=seq[-1][1]:seq.append((last,val))
ng=NgSpice();cases=[]
base=(HERE/'decks/gi_string.cir').read_text()
for channel,sequence in edges.items():
 start,end,duty=worst_window(sequence,last,.4);history=max(0,start-.1);duration=end-history+.02
 for phase in [0,90,180,270]:
  name=f'gi{channel+1}_phase{phase}';pts=command_points(sequence,history,end,duration)
  source=base[:base.index('.tran')];source=source[source.index('.include'):].replace('.include ../models.lib',f'.include {HERE/"models.lib"}')
  source=f'ROM GI {channel+1}, AC relative phase {phase}; 18 #44 envelope\n'+source
  source=source.replace('Vac ac0 0 SIN(0 11.1 60)',f'Vac ac0 0 SIN(0 11.1 60 0 0 {phase})')
  source=source.replace('VL latch 0 PULSE(0 4.6 4.17m 20n 20n 1 2)','VL latch 0 PWL(\n'+''.join(f'+ {t:.12f} {v:.2f}\n' for t,v in pts)+'+ )')
  source+=f'''.save i(Vf106) i(Vmt) v(mt2i) i(Vg)
.tran 5u {duration:.9f} 0 2u
.control
run
let istr=i(Vf106)
let iabs=abs(istr)
let isq=istr*istr
let ptri=v(mt2i)*i(Vmt)
let sim_end=time[length(time)-1]
print sim_end
meas tran peak_current MAX iabs
meas tran rms_current RMS istr from={start-history:.9f} to={end-history:.9f}
meas tran avg_power AVG ptri from={start-history:.9f} to={end-history:.9f}
meas tran inrush_i2t INTEG isq from=0 to=.03
let tj=50+avg_power*13.875
print tj
.endc
.end
'''
  path=out/(name+'.cir');path.write_text(source);ng.cmd('destroy all');log=ng.run_deck(str(path));(out/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
  limits={'sim_end':(duration-1e-7,duration+1e-7),'peak_current':(0,160),'rms_current':(0,5),'inrush_i2t':(0,128),'tj':(0,125)}
  checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
  errors=[l for l in log if l.startswith('stderr') and not l.startswith('stderr Note:') and 'Warning' not in l]
  c=dict(name=name,channel=channel+1,phase_degrees=phase,window_s=[start,end],gate_command_duty=duty,measurements=v,checks=checks,errors=errors,passed=not errors and all(x['passed'] for x in checks.values()),deck_sha256=hashlib.sha256(source.encode()).hexdigest());cases.append(c);print(name,c['passed'],v,flush=True)
  report=dict(passed=len(cases)==20 and all(x['passed'] for x in cases),complete=len(cases)==20,cases=cases,trace_sha256=hashlib.sha256(a.trace.read_bytes()).hexdigest(),model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest(),limitations=['Worst 400 ms gate-command-duty window with 100 ms history; highest gate duty does not prove the hottest possible dimmer phase','All five strings use 18 #44 lamps as the existing engineering envelope; STTNG insert strings use #555, actual populations and thermal data must be measured','60 Hz ROM trace; four phase offsets sample emulator/physical zero-cross uncertainty, not exhaustive phase/timing corners','Approximate triac latch/holding-current model; real commutation, trigger quadrant, EMI and heatsink contact require bench testing','128 A2s is a device surge-screen bound over the initial 30 ms; no repetitive surge/fuse coordination qualification'])
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)
