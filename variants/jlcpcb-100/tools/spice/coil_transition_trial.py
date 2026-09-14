"""Bounded, short ROM-pulse study to isolate coil loss integration trouble.

Two exact initial pulses from the selected gameplay window, without shortening
their ON/OFF intervals. Does not substitute for the complete worst-duty replay.
"""
import argparse
import hashlib
import json
from pathlib import Path

from bounded_run import run_bounded
from replay_rom import read_edges, worst_window

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'output/verification/continuation/coil-transitions'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--step-us', type=float, required=True)
parser.add_argument('--method', choices=['trap', 'gear'], default='trap')
parser.add_argument('--wall-seconds', type=float, default=120)
parser.add_argument('--vendor-diode', action='store_true')
args = parser.parse_args()
OUT.mkdir(parents=True, exist_ok=True)
trace = ROOT / 'output/verification/pinmame/gameplay-prespin/bus.csv'
edges, last = read_edges(trace)
start, end, duty = worst_window(edges[1], last)
selected = [(t, s) for t, s in edges[1] if start <= t <= end][:4]
assert [s for t, s in selected] == [1, 0, 1, 0]
prefix = .0001
stop = prefix + selected[-1][0] - start + .02
points = [(0, 0)]
previous = 0
for t, state in selected:
    relative = prefix + t - start
    points += [(relative - 20e-9, 4.5*previous), (relative, 4.5*state)]
    previous = state
points.append((stop, 0))
name = f'two_pulses_{args.method}_{args.step_us:g}us' + ('_vendor' if args.vendor_diode else '')
path = OUT / (name + '.cir')
vendor = ROOT / '.scratch/vendor-models/S3M.spice.txt'
source = f'''Exact two initial ROM pulses; short convergence investigation {name}
.include {HERE/'models.lib'}
'''
if args.vendor_diode:
    source += f'.include {vendor}\n'
source += 'Vcmd cmd 0 PWL(\n' + ''.join(f'+ {t:.12f} {v:g}\n' for t, v in points) + '+ )\n'
source += f'''Vrail rail 0 86
Ro cmd a 40
Rg a gate 100
Rpd gate 0 10k
Vsense drain dq 0
XQ dq gate 0 IPD90N10S4L06
Lcoil drain cl 12m
Rcoil cl rail 3.78
Dfly drain rail {'DI_S3M' if args.vendor_diode else 'DS3M'}
.save v(dq) v(gate) i(Vsense) i(Lcoil) @m.xq.m1[id] @d.xq.db[id] @d.xq.db[capcur]
.options method={args.method} klu reltol=.0001 trtol=1 chgtol=1e-16 itl4=500
.tran 1u {stop:.12g} 0 {args.step_us:g}u
.control
run
let loss_channel=v(dq)*@m.xq.m1[id]
let loss_body=-v(dq)*(@d.xq.db[id]-@d.xq.db[capcur])
let loss_total=loss_channel+loss_body
let terminal_power=v(dq)*i(Vsense)
let icoil=abs(i(Lcoil))
let sim_end=time[length(time)-1]
print sim_end
meas tran e_dissipation INTEG loss_total
meas tran e_terminal INTEG terminal_power
meas tran vds_peak MAX v(dq)
meas tran coil_peak MAX icoil
.endc
.end
'''
if path.exists():
    raise FileExistsError(path)
path.write_text(source)
result = run_bounded(path, args.wall_seconds)
values = result['measurements']
limits = dict(sim_end=(stop-1e-8, stop+1e-8), vds_peak=(0, 90),
              coil_peak=(0, 86/3.78*1.02), e_dissipation=(0, 1), e_terminal=(0, 1))
checks = {k: dict(value=values.get(k), min=lo, max=hi,
                  passed=k in values and lo <= values[k] <= hi)
          for k, (lo, hi) in limits.items()}
result.update(checks=checks,
              passed=result['execution_completed'] and not result['errors'] and all(x['passed'] for x in checks.values()),
              trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),
              models_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest(),
              vendor_model_sha256=hashlib.sha256(vendor.read_bytes()).hexdigest() if args.vendor_diode else None,
              pulse_edges=selected, method=args.method, step_us=args.step_us,
              limitations=['Two initial pulses only; not the maximum-current transitions or full-window thermal qualification',
                           'Tighter integration tolerances and KLU; device models, gate resistance and command edges unchanged',
                           'Approximate MOSFET model; selected manufacturer S3M model used only with --vendor-diode'])
path.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2), flush=True)
raise SystemExit(0 if result['passed'] else 1)
