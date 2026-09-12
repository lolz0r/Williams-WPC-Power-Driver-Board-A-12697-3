"""First-order integration diagnostic; retain circuit and acceptance screens.

Backward Euler adds numerical damping. Completion alone is insufficient: compare
finer timesteps and report original-model failures alongside any new result.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from bounded_run import run_bounded

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/verification/followup/matrix-euler'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--step-us', type=float, required=True)
p.add_argument('--wall-seconds', type=float, default=180)
a = p.parse_args()
assert a.step_us > 0
OUT.mkdir(parents=True, exist_ok=True)
base = ROOT / 'output/verification/prespin/replay-matrix/matrix_20.69V.cir'
original = base.read_text()
s = re.sub(r'^\.options.*$', '.options method=trap maxord=1 klu reltol=.001 itl4=500', original, flags=re.M)
s = re.sub(r'^(\.tran 5u \S+ 0) .*$', rf'\g<1> {a.step_us:g}u', s, flags=re.M)
assert s.split('.save')[0] == original.split('.save')[0]
deck = OUT / f'matrix_backward_euler_{a.step_us:g}us.cir'
if deck.exists():
    raise FileExistsError(deck)
deck.write_text(s)
r = run_bounded(deck, a.wall_seconds)
prior = json.loads(base.with_suffix('.json').read_text())
v = r['measurements']
checks = {k: dict(min=c['min'], max=c['max'], value=v.get(k),
                  passed=k in v and c['min'] <= v[k] <= c['max'])
          for k, c in prior['checks'].items()}
r.update(checks=checks,
         passed=r['execution_completed'] and not r['errors'] and all(c['passed'] for c in checks.values()),
         method='backward Euler: method=trap maxord=1', step_us=a.step_us,
         pcb_changed=False, device_values_and_command_points_unchanged=True,
         base_deck_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
         model_sha256=hashlib.sha256((ROOT/'tools/spice/models.lib').read_bytes()).hexdigest(),
         pcb_sha256=hashlib.sha256((ROOT/'wpc_power_driver_cost.kicad_pcb').read_bytes()).hexdigest(),
         source='https://ngspice.sourceforge.io/docs/ngspice-44-manual.pdf',
         limitations=['First-order numerical damping can suppress transients; timestep convergence and cross-method agreement must be assessed',
                      'No device, command-edge, leakage-shunt or board change; original generic device models retained',
                      'Completion and screening do not qualify the real assembly or erase previous failed simulations'])
deck.with_suffix('.json').write_text(json.dumps(r, indent=2)+'\n')
print(json.dumps(r, indent=2), flush=True)
raise SystemExit(0 if r['passed'] else 1)
