"""Summarize current supply and unchanged matrix evidence without promoting old trials."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/prototype-readiness'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rails={};evidence={}
for u in ['U20','U21']:
 cases=[];loops=[]
 for folder in ['buckboost-qualified-nominal','buckboost-qualified-high','buckboost-qualified-low']:
  p=OUT/folder/'results.json';d=json.loads(p.read_text());assert d['passed'],folder
  evidence[str(p.relative_to(ROOT))]=sha(p);cases += [c for c in d['cases'] if c['name'].startswith(u+'_')];loops+=d['loops'][u]['cases']
 rails[u]=dict(transient_cases=len(cases),all_passed=all(c['passed'] for c in cases),peak_output_V=max(c['measurements']['output_peak'] for c in cases),
  settled_min_V=min(c['measurements']['settled_min'] for c in cases),settled_max_V=max(c['measurements']['settled_max'] for c in cases),
  load_step_min_V=min(c['measurements']['step_min'] for c in cases if 'load_step' in c['name']),
  minimum_phase_margin_deg=min(c['phase_margin_deg'] for c in loops),minimum_gain_margin_dB=min(c['gain_margin_dB'] for c in loops if c['gain_margin_dB'] is not None))
matrices=[]
for name in ['matrix_minbreak1p_1us.json','matrix_minbreak1p_0.5us.json','matrix_minbreak1p_trap_0.5us.json','replay-matrix/matrix_20.69V_1us.json']:
 p=OUT/name;d=json.loads(p.read_text());assert d['passed'],name
 matrices.append(dict(report=str(p.relative_to(ROOT)),sha256=sha(p),checks=len(d['checks']),completed_s=d['measurements']['sim_end'],peak_column_junction_C=max(v for k,v in d['measurements'].items() if k.startswith('col') and k.endswith('_tj'))))
report=dict(passed=True,rails=rails,matrix=matrices,evidence_sha256=evidence,
 scope='96 averaged supply transient screens, CCM loop sensitivities, and four completed 370 ms ROM-trace matrix runs. Native topology/value audits bind current hardware separately.',
 limitations=['No physical qualification has been performed','Supply model is averaged and the public TI switching model is encrypted','The matrix driver circuit is unchanged; its prior PCB hash identifies the time of the run, not an extracted whole-board simulation','Fuses/transformer, harness losses, cabinet thermal conditions, PFM and backfeed behavior require prototype measurements'])
(OUT/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rails,indent=2))
