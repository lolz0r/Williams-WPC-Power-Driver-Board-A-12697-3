"""Selected onsemi rectifier cold-start bounds, including crest energization."""
import hashlib,itertools,json,re
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'output/verification/inventory-rectifier-startup';OUT.mkdir(exist_ok=True,parents=True)
# Generated final bridge fixture: +10% mains and +20% bank capacitance.
base=(ROOT/'output/verification/inventory-bridge-final/bridge_60_1.1_1.2.cir').read_text().split('.options')[0]
def split_legs(m):
 name,a,k=m.groups();return f'{name}a {a} xa{name} J100ONLEG_A\nV{name}a xa{name} {k} 0\n{name}b {a} xb{name} J100ONLEG_B\nV{name}b xb{name} {k} 0'
base=re.sub(r'(?m)^(D\S+)\s+(\S+)\s+(\S+)\s+J100ON20H$',split_legs,base)
base+='\n.model J100ONLEG_A D(Is=1e-7 N=1.05 Rs=.0072 Cjo=700p Bv=100 Ibv=1m)\n.model J100ONLEG_B D(Is=1e-8 N=1.05 Rs=.0108 Cjo=700p Bv=100 Ibv=1m)\n'
ng=NgSpice();cases=[]
for hz,phase,rscale in itertools.product([50,60],[0,90],[1,.5]):
 src=re.sub(r'SIN\(0 ([\d.]+) 60\)',lambda m:f'SIN(0 {m[1]} {hz} 0 0 {phase})',base)
 src=re.sub(r'(?m)^(R[pq](?:5a|20a|12b)\s+\S+\s+\S+\s+)([\d.]+)$',lambda m:m[1]+str(float(m[2])*rscale),src)
 commands=['let sim_end=time[length(time)-1]','print sim_end'];checks={}
 for k in ['5a','20a','12b']:
  commands += [f'let ia_{k}=abs(i(Vs{k}))',f'let i2_{k}=ia_{k}*ia_{k}',f'meas tran peak_{k} MAX ia_{k} from=0 to=50m',f'meas tran i2t_{k} INTEG i2_{k} from=0 to=50m']
 for k in ['5a','20a','12b']:
  for leg in ['a','b']:
   commands += [f'let il_{k}_{leg}=abs(i(VD1{k}{leg}))',f'let il2_{k}_{leg}=il_{k}_{leg}*il_{k}_{leg}',f'meas tran legpeak_{k}_{leg} MAX il_{k}_{leg} from=0 to=50m',f'meas tran legi2t_{k}_{leg} INTEG il2_{k}_{leg} from=0 to=50m']
 src+='\n.options method=gear reltol=.001 minbreak=1p klu\n.tran 1u 50m 0 1u uic\n.control\nrun\n'+'\n'.join(commands)+'\n.endc\n.end\n'
 p=OUT/f'f{hz}_phase{phase}_r{rscale}.cir';p.write_text(src);ng.cmd('destroy all');log=ng.run_deck(str(p));p.with_suffix('.log').write_text('\n'.join(log)+'\n');v=measurements(log)
 for k in ['5a','20a','12b']:
  for leg in ['a','b']:
   tag=k+'_'+leg;checks[tag]=dict(peak_A=v.get('legpeak_'+tag),integrated_50ms_A2s=v.get('legi2t_'+tag),passed=0<v.get('legpeak_'+tag,1e9)<250 and 0<v.get('legi2t_'+tag,1e9)<250**2*.0083/2)
 errors=[x for x in log if x.startswith('stderr') and 'Note:' not in x];passed=not errors and abs(v.get('sim_end',0)-.05)<1e-8 and all(c['passed'] for c in checks.values());cases.append(dict(name=p.stem,passed=passed,checks=checks,errors=errors,deck_sha256=hashlib.sha256(src.encode()).hexdigest()));print(p.stem,passed,flush=True)
report=dict(passed=len(cases)==8 and all(c['passed'] for c in cases),cases=cases,model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest(),limits='250A per leg surge; explicitly simulated both parallel legs with opposite20% series-resistance mismatch and10:1 saturation-current mismatch (about62mV forward offset). Outer legs connect to the same native anode net. Integrated50ms current squared screened below single-leg250A8.3ms half-sine equivalent259.375A2s; waveform comparison is engineering screening, not a vendor repetitive/fault guarantee.',limitations=['Unmeasured transformer resistance:5/20V bridges0.05..0.1ohm loop,12VU0.25..0.5ohm. +10% line, +20% bulk capacitance;0/90degree energization.','Mismatch is engineering sensitivity, not manufacturer distribution. Hot repeated starts and measured winding impedance/leg current sharing remain required. No mains fault/transformer/fuse coordination qualification.'],datasheet='research/datasheets/C235758.pdf')
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(0 if report['passed'] else 1)
