"""Rerun retained bridge stress fixtures with JLC-3's regulated 12 V load.

The 2.5-ohm lamp stress and winding impedances are explicit unmeasured bounds.
Fuse ratings are AC RMS ratings, never interchangeable with DC reservoir loads.
"""
import json,hashlib,re
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/verification/prototype-readiness/bridge-corners'
OUT.mkdir(exist_ok=True);assert not (OUT/'results.json').exists();ng=NgSpice();cases=[]
for original in sorted((ROOT/'output/verification/revision/corners').glob('bridge_*.cir')):
 for scale in [.8,1.2]:
  src=original.read_text().replace('the +12V digital buck','the JLC-3 +12V digital buck-boost')
  src=src.replace('min(12.0, max(0.97*v(dc18a) - 0.5, 0))','12.0')
  # Vary all low-voltage 10/20 mF reservoirs together to cover ripple loading.
  src=re.sub(r'(?m)^(C(?:18|20|5|12)\w*\s+\S+\s+\S+\s+)([\d.]+)u$',lambda m:m[1]+str(float(m[2])*scale)+'u',src)
  p=OUT/(original.stem+f'_cap{scale}.cir');p.write_text(src);ng.cmd('destroy all');log=ng.run_deck(str(p));p.with_suffix('.log').write_text('\n'.join(log)+'\n')
  v=measurements(log);errors=[s for s in log if s.startswith('stderr') and not s.startswith('stderr Note:')]
  completed=not errors and all('pd_'+k in v for k in ['18a','5a','20a','12b'])
  cases.append(dict(name=p.stem,completed=completed,capacitance_scale=scale,measurements=v,errors=errors,deck_sha256=hashlib.sha256(src.encode()).hexdigest(),source_fixture_sha256=hashlib.sha256(original.read_bytes()).hexdigest()))
  print(p.stem,'complete',completed,flush=True)
report=dict(passed=all(c['completed'] for c in cases) and len(cases)==12,cases=cases,
 scope='Updated bridge-conduction thermal inputs, not fuse or transformer qualification',
 limitations=['All-lamps constant load and sustained flasher load are stress bounds, not measured gameplay','Retained fitted diode model and winding impedances need measurement','AC RMS fuse loading can exceed fuse ratings at continuous stress loads; do not raise OEM fuse values to satisfy a model'])
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report['passed'])
