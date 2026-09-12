"""Integration sensitivity of ROM replays, with declared engineering tolerances."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'output/verification/revision'
def main():
 coarse=json.loads((REV/'replay-diagnostics/results.json').read_text())
 fine=json.loads((REV/'replay-step-sensitivity/results.json').read_text())
 assert coarse['passed'] and fine['passed'],'Transient checks must pass first'
 assert coarse['trace_sha256']==fine['trace_sha256'] and coarse['model_sha256']==fine['model_sha256']
 assert coarse['max_step_us']==5 and fine['max_step_us']==2.5
 assert fine['requested_channels']==coarse['requested_channels']==list(range(1,17))
 base={c['channel']:c for c in coarse['cases']};checks=[]
 # Voltage and coil maxima within 1%; FET transient peak within 5%.
 # Average forward current and thermal rise within 5%; absolute floor for leakage.
 for c in fine['cases']:
  b=base[c['channel']]
  for key,relative,absolute in [('vds_peak',.01,.01),('vgs_peak',.01,.001),('coil_peak',.01,.001),('i_peak',.05,.01),('id_avg',.05,.0001),('tj_repeating',.05,.1)]:
   v0=b['checks'][key]['value'];v1=c['checks'][key]['value'];difference=abs(v1-v0)
   scale=abs(v1-50) if key=='tj_repeating' else abs(v1)
   bound=max(absolute,relative*scale)
   checks.append(dict(channel=c['channel'],metric=key,coarse=v0,fine=v1,absolute_difference=difference,allowed_difference=bound,passed=difference<=bound))
 report=dict(passed=all(c['passed'] for c in checks),checks=checks,trace_sha256=coarse['trace_sha256'],model_sha256=coarse['model_sha256'],limitations='Engineering numerical-sensitivity limits; not accuracy against measured hardware or a device SOA qualification.')
 (REV/'replay-step-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Replay convergence:',len(checks),'checks,',sum(c['passed'] for c in checks),'passed');return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
