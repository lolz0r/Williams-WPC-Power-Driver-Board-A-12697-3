"""Candidate U21 input isolation using C7; no PCB or approved BOM mutation."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from bounded_run import run_bounded

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/verification/continuation/isolated-buck'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--load', type=float, default=.75)
parser.add_argument('--frequency', type=int, default=60)
parser.add_argument('--scenario', choices=['startup', 'loss_restart'], default='startup')
parser.add_argument('--stop-ms', type=float, default=30)
parser.add_argument('--wall-seconds', type=float, default=300)
parser.add_argument('--cc-nf', type=float, default=100)
args = parser.parse_args()
OUT.mkdir(parents=True, exist_ok=True)
base = ROOT / 'output/verification/prespin/power-sequence/12v_loss_restart_0.75A_250n.cir'
source = base.read_text().split('.save')[0]
# U21, its divider, and local ceramic input capacitance move behind the diode.
# The original bridge/raw lamp rail stays on vinf. C6 and C7 are each 8 mF
# after tolerance; C7 is moved to the isolated side, retaining its ground.
source = source.replace('Cin vinf 0 20u', 'Cin buck_input 0 20u')
source = source.replace('sw rt vinf fb', 'sw rt buck_input fb')
source = source.replace('Ren1 vinf en', 'Ren1 buck_input en')
source = source.replace('Creservoir stored 0 16000u', 'Creservoir stored 0 8000u')
source = re.sub(r'^Rload vout 0 .*$', f'Rload vout 0 {12/args.load:.12g}', source, flags=re.M)
source = source.replace('Cc cc 0 100n', f'Cc cc 0 {args.cc_nf:g}n')
waveform = f'{18.8*.9:g}*sin(2*3.141592653589793*{args.frequency}*time)'
if args.scenario == 'loss_restart':
    waveform += '*((time<25m)?1:((time<85m)?0:min((time-85m)/100u,1)))'
source = re.sub(r'^Bsecondary .*$', f'Bsecondary secp secn V={waveform}', source, flags=re.M)
source += '''
* Hypothetical C7 input hold-up; B560C is already a selected board part.
Disolate vinf buck_input DB560C
Rdedicated buck_input dedicated_stored .05
Cdedicated dedicated_stored 0 8000u
'''
stop = args.stop_ms / 1000
period = 1 / (2 * args.frequency)
assert stop >= 2 * period
name = f'{args.scenario}_{args.load:g}A_f{args.frequency}_cc{args.cc_nf:g}n_stop{args.stop_ms:g}m'
path = OUT / (name + '.cir')
source += f'''
.save v(vout) v(vinf) v(buck_input) v(en) v(comp) i(L1) @disolate[id]
.options reltol=.005 abstol=1u vntol=1m method=gear klu itl4=100
.tran 1u {stop:.12g} 0 250n
.control
run
let sim_end=time[length(time)-1]
print sim_end
meas tran output_peak MAX v(vout)
meas tran output_min MIN v(vout)
meas tran inductor_peak MAX i(L1)
meas tran inductor_min MIN i(L1)
meas tran isolation_diode_peak MAX @disolate[id]
meas tran recovery_min MIN v(vout) from={stop-period:.12g} to={stop:.12g}
meas tran recovery_max MAX v(vout) from={stop-period:.12g} to={stop:.12g}
meas tran recovery_avg AVG v(vout) from={stop-period:.12g} to={stop:.12g}
meas tran headroom_min MIN v(buck_input) from={stop-period:.12g} to={stop:.12g}
set wr_singlescale
set wr_vecnames
linearize v(vout) v(vinf) v(buck_input) v(comp) i(L1)
wrdata {OUT/(name+'.csv')} v(vout) v(vinf) v(buck_input) v(comp) i(L1)
.endc
.end
'''
if path.exists():
    raise FileExistsError(f'Preserve previous candidate before re-running: {path}')
path.write_text(source)
result = run_bounded(path, args.wall_seconds, pspice=True)
values = result['measurements']
limits = {'sim_end': (stop-1e-8, stop+1e-8), 'output_peak': (0, 12.6),
          'output_min': (-.3, 13), 'inductor_peak': (0, 10), 'inductor_min': (-1, 10),
          'recovery_min': (11.4, 12.6), 'recovery_max': (11.4, 12.6)}
checks = {k: dict(value=values.get(k), min=lo, max=hi,
                  passed=k in values and lo <= values[k] <= hi)
          for k, (lo, hi) in limits.items()}
result.update(checks=checks,
              passed=result['execution_completed'] and not result['errors'] and all(x['passed'] for x in checks.values()),
              candidate_only=True, pcb_changed=False, scenario=args.scenario,
              load_A=args.load, frequency_Hz=args.frequency, compensation_C_nF=args.cc_nf,
              base_deck_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
              deviations=['C7 moved from lamp rail to diode-isolated U21 input',
                          'Added B560C diode between +18 V and U21 input',
                          'U21 input divider/local ceramics follow isolated input',
                          f'C42 modeled at {args.cc_nf:g} nF (native 100 nF)'],
              limitations=['Typical vendor model; no PCB layout or component SOA qualification',
                           'Last complete rectified cycle checked, not merely a partial-cycle average',
                           'Ripple, fuse inrush, brownout, reverse power, thermal and source corners still needed before promotion'])
path.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2), flush=True)
raise SystemExit(0 if result['passed'] else 1)
