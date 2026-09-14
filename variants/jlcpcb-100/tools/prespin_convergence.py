"""Summarize convergence honestly: retain failing refinements and comparisons."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/prespin'
def read(p):return json.loads(p.read_text())
comparisons=[];inputs={}
def compare(a,b,keys,rel=.05,absolute=.001):
 for path in [a,b]:inputs[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
 x,y=read(a),read(b)
 # A partial transient is never accepted as a convergence comparison.
 valid=x['passed'] and y['passed']
 for key in keys:
  u=x['measurements'].get(key);v=y['measurements'].get(key)
  delta=abs(u-v) if u is not None and v is not None else None
  bound=max(absolute,rel*max(abs(u),abs(v))) if delta is not None else None
  comparisons.append(dict(a=str(a.relative_to(OUT)),b=str(b.relative_to(OUT)),metric=key,both_runs_passed=valid,a_value=u,b_value=v,difference=delta,limit=bound,passed=bool(valid and delta is not None and delta<=bound)))
segments=OUT/'replay-loss-segments'
a=segments/'coil1_0.15625us.json';b=segments/'coil1_0.078125us.json'
if a.exists() and b.exists():compare(a,b,['dissipation_w','terminal_w','vds_peak','coil_peak'])
matrix=OUT/'replay-matrix';a=matrix/'matrix_20.69V.json';b=matrix/'matrix_20.69V_1us.json'
if a.exists() and b.exists():compare(a,b,[f'{kind}{i}_{metric}' for kind in ['col','row'] for i in range(8) for metric in ['peak','power']])
# Completed full-window outputs remain useful screening bounds even if their
# convergence criterion is not met. Do not relabel those bounds as convergence.
coil=[]
for folder in ['replay-gameplay','replay-gameplay-fine','replay-gameplay-1p25us','replay-gameplay-0p625us','replay-gameplay-loss5us','replay-gameplay-loss0p625us','replay-gameplay-loss0p3125us','replay-gameplay-gear2p5us','replay-gameplay-gear1p25us']:
 p=OUT/folder/'results.json'
 if not p.exists():continue
 d=read(p)
 for c in d['cases']:
  if c['channel']!=1:continue
  coil.append(dict(run=folder,complete=c['checks']['sim_end']['passed'],passed=c['passed'],max_step_us=d['max_step_us'],method=d['method'],terminal_temperature_C=c['checks']['tj_repeating']['value'],carrier_dissipation_W=c.get('dissipation_W'),errors=c['errors']))
trials=[]
for path in sorted(list(segments.glob('coil*.json'))+list(matrix.glob('matrix*.json'))):
 d=read(path);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
 trials.append(dict(run=str(path.relative_to(OUT)),complete=d['checks']['sim_end']['passed'],passed=d['passed'],measurements=d['measurements'],errors=d['errors']))
initial=read(OUT/'replay-convergence-initial.json')
report=dict(passed=bool(comparisons) and all(c['passed'] for c in comparisons),initial_comparison_passed=initial['passed'],initial_failed_checks=[c for c in initial['checks'] if not c['passed']],comparisons=comparisons,coil_refinements=coil,additional_trials=trials,inputs=inputs,limitations=['Convergence must be distinguished from all completed runs remaining below an engineering screen','Failed or aborted finer-step runs cannot establish a physical maximum; retained for audit','Channel/body loss and terminal-energy estimates are separately recorded; no unvalidated model alteration made to force agreement','Physical scope/current/thermal correlation remains required'])
report['pending_refinements']=[str(p.relative_to(OUT)) for folder in [segments,matrix] for p in sorted(folder.glob('*.cir')) if not p.with_suffix('.json').exists()]
report['passed']=report['passed'] and not report['pending_refinements']
report['manual_interruptions']=read(segments/'runtime-stops.json')
(OUT/'convergence-review.json').write_text(json.dumps(report,indent=2)+'\n');print('Convergence established:',report['passed'],'comparisons:',len(comparisons))
