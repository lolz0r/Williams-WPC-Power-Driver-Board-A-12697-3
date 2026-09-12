"""Full 8x8 thermal lamp matrix, driven by the ROM's actual row/column writes.
Comparator clear is monitored; a trip is failure rather than silently suppressing it.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
from replay_rom import command_points,worst_window
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--rail',type=float,default=20.69);p.add_argument('--max-step-us',type=float,default=2);p.add_argument('--strict',action='store_true');a=p.parse_args()
out=ROOT/'output/verification/prespin/replay-matrix';out.mkdir(exist_ok=True,parents=True)
sequences={f'{kind}{i}':[(0.,0)] for kind in ['row','col'] for i in range(8)};last=0;rows=cols=0;weight=[(0.,0)]
for r in csv.DictReader(a.trace.open()):
 last=float(r['time']);addr=int(r['address'],16)
 if r['kind']!='W' or addr not in [0x3fe4,0x3fe5]:continue
 word=int(r['data'],16);kind='row' if addr==0x3fe4 else 'col'
 if kind=='row':rows=word
 else:cols=word
 w=rows.bit_count()*cols.bit_count()
 if w!=weight[-1][1]:weight.append((last,w))
 for bit in range(8):
  val=(word>>bit)&1;seq=sequences[f'{kind}{bit}']
  if val!=seq[-1][1]:seq.append((last,val))
start,end,score=worst_window(weight,last,.25);history=max(0,start-.1);duration=end-history+.02
source=f'''All 64 lamp paths, raw ROM row/column strobes, {a.rail} V
.include {HERE/'models.lib'}
Vrail rail 0 {a.rail}
Vcc vcc 0 5
Rref vcc ref 1k
Dref1 ref mid D1N4148
Dref2 mid 0 D1N4148
'''
for name,seq in sequences.items():
 pts=command_points(seq,history,end,duration)
 source+=f'Vdrive{name} {name}cmd 0 PWL(\n'+''.join(f'+ {t:.12f} {v:.2f}\n' for t,v in pts)+'+ )\n'
for i in range(8):
 source+=f'''Routc{i} col{i}cmd col{i}in 40
Xdriver{i} col{i}in col{i}sink TBD62083CH
Rserc{i} col{i}sink col{i}g 1k
Rgsc{i} col{i}g rail 1.5k
Xcol{i} col{i}drain col{i}g rail IRFR5305
Vcol{i} col{i}drain col{i} 0
Routr{i} row{i}cmd row{i}q 40
Rg{i} row{i}q row{i}g 100
Rpd{i} row{i}g 0 10k
Xrow{i} row{i} row{i}g row{i}s IRLR024N
Vrow{i} row{i}s row{i}sh 0
Rsh{i} row{i}sh 0 .22
Rsense{i} row{i}s row{i}sense 1k
Csense{i} row{i}sense 0 100n
Xcmp{i} ref row{i}sense clr{i} LM339
Rclr{i} clr{i} vcc 10k
'''
for col in range(8):
 for row in range(8):
  n=f'{col}{row}'
  source+=f'''Blamp{n} col{col} a{n} I=v(col{col},a{n})/(7+18*max(v(t{n}),0))
Dlamp{n} a{n} row{row} D1N4004
Bheat{n} 0 t{n} I=(v(col{col},a{n})^2/(7+18*max(v(t{n}),0)))/1.6
Cthermal{n} t{n} 0 15m
Rthermal{n} t{n} 0 1
'''
source+='.save '+ ' '.join(f'v(clr{i}) v(row{i}) v(row{i}s) v(col{i}drain) i(Vrow{i}) i(Vcol{i})' for i in range(8))+'\n'
source+=f'''.options method=gear reltol={'.0001 trtol=1 chgtol=1e-16' if a.strict else '.002'} klu itl4=500
.tran 5u {duration:.9f} 0 {a.max_step_us:g}u
.control
run
let sim_end=time[length(time)-1]
print sim_end
'''
limits={'sim_end':(duration-1e-7,duration+1e-7)}
for i in range(8):
 source+=f'''let pc{i}=({a.rail}-v(col{i}drain))*i(Vcol{i})
let pr{i}=(v(row{i})-v(row{i}s))*i(Vrow{i})
let ir{i}=abs(i(Vrow{i}))
let ic{i}=abs(i(Vcol{i}))
meas tran col{i}_peak MAX ic{i}
meas tran row{i}_peak MAX ir{i}
meas tran row{i}_clear MIN v(clr{i})
meas tran col{i}_power AVG pc{i} from={start-history:.9f} to={end-history:.9f}
meas tran row{i}_power AVG pr{i} from={start-history:.9f} to={end-history:.9f}
let col{i}_tj=50+col{i}_power*110
let row{i}_tj=50+row{i}_power*110
print col{i}_tj
print row{i}_tj
'''
 limits.update({f'col{i}_peak':(0,31),f'row{i}_peak':(0,8),f'row{i}_clear':(2.4,5.1),f'col{i}_tj':(0,125),f'row{i}_tj':(0,125)})
source+='.endc\n.end\n';name=f'matrix_{a.rail:g}V'+(f'_{a.max_step_us:g}us' if a.max_step_us!=2 else '')+('_strict' if a.strict else '');path=out/(name+'.cir');path.write_text(source)
ng=NgSpice();log=ng.run_deck(str(path));(out/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
errors=[l for l in log if l.startswith('stderr') and not l.startswith('stderr Note:') and 'Warning' not in l]
report=dict(passed=not errors and all(x['passed'] for x in checks.values()),checks=checks,measurements=v,errors=errors,window_s=[start,end],average_selected_lamps=score,deck_sha256=hashlib.sha256(source.encode()).hexdigest(),trace_sha256=hashlib.sha256(a.trace.read_bytes()).hexdigest(),model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest(),limitations=['Full 64 series-diode/thermal-filament paths, eight column and eight row MOSFETs; lumped comparator model','Selected 250 ms window maximizes average selected lamp count, with 100 ms history; no claim of every lamp animation or thermal steady state','ROM latch outputs drive circuit directly; separate netlist logic and ribbon timing checks bind mapping/edge requirements','A comparator trip is rejected; no asynchronous row-clear feedback in this replay','Constant 20.69 V default is high-line envelope; actual transformer/filament/contact characteristics require measurements'])
(out/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
