"""TI HCT timing with worst 150 pF propagation and full-temperature setup/hold."""
from pathlib import Path
import json,re,hashlib
from ngspice_lib import NgSpice
from corners import measurements
from run_all import CHECKS
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[1]/'output/verification/revision/ribbon-ti';OUT.mkdir(parents=True,exist_ok=True)
source=(HERE/'decks/ribbon.cir').read_text().replace('.include ../models.lib',f'.include {HERE}/models.lib');source=re.sub(r'^wrdata.*$','',source,flags=re.M)
results=[];ng=NgSpice()
# 53 ns maximizes setup burden; 0 delay is a conservative lower bound for hold.
for delay in [.001,32,53]:
 for cap in [120,200]:
  text=source.replace('rise_delay=53n fall_delay=53n',f'rise_delay={delay}n fall_delay={delay}n').replace('120p',f'{cap}p');p=OUT/f'delay{delay}_c{cap}.cir';p.write_text(text)
  ng.cmd('destroy all');log=ng.run_deck(str(p));(p.with_suffix('.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
  checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,lo,hi,_ in CHECKS['ribbon']};errors=[l for l in log if l.startswith('stderr') and 'Warning' not in l]
  results.append(dict(delay_ns=delay,ribbon_pF=cap,checks=checks,errors=errors,passed=not errors and all(c['passed'] for c in checks.values()),deck_sha256=hashlib.sha256(text.encode()).hexdigest()))
report=dict(passed=all(r['passed'] for r in results),cases=results,sources=['https://www.ti.com/lit/ds/symlink/sn74hct240.pdf','https://www.ti.com/lit/ds/symlink/sn74hct574.pdf'],limitations='Behavioral output impedance and logic model; board/harness load and gate-drive waveforms need physical correlation. 150 pF timing rating bounds logic input bus; MOSFET gate load is modeled explicitly.')
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('TI ribbon timing',report['passed'],[(r['delay_ns'],r['ribbon_pF'],[(k,c['value']) for k,c in r['checks'].items() if not c['passed']]) for r in results]);raise SystemExit(0 if report['passed'] else 1)
