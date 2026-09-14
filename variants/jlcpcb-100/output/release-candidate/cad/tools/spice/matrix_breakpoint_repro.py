"""Short A/B reproduction of the matrix breakpoint failure; no rating claim."""
import hashlib
import argparse
import json
import re
from pathlib import Path

from bounded_run import run_bounded

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'output/verification/prototype-readiness'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gear', action='store_true', help='First 150 ms using original Gear settings')
    args = parser.parse_args()
    tag = '_gear' if args.gear else ''
    stop = .15 if args.gear else .03
    options = 'method=gear klu reltol=.002 itl4=500' if args.gear else 'method=trap maxord=1 klu reltol=.001 itl4=500'
    base = ROOT/'output/verification/prespin/replay-matrix/matrix_20.69V.cir'
    original = base.read_text()
    circuit = original.split('.save')[0]
    cases = []
    for name, option in [('default', ''), ('minbreak1p', ' minbreak=1p')]:
        source = circuit + f'''
.save v(row0q) v(row0g) v(col0drain)
.options {options}{option}
.tran 5u {stop:g} 0 .5u
.control
set numdgt=12
run
let sim_end=time[length(time)-1]
print sim_end
.endc
.end
'''
        path = OUT/f'matrix_breakpoint_repro{tag}_{name}.cir'
        if path.exists():
            raise FileExistsError(path)
        path.write_text(source)
        r = run_bounded(path, 300)
        r['requested_window_completed'] = r['execution_completed'] and not r['errors'] and abs(r['measurements'].get('sim_end',0)-stop)<1e-10
        r['name'] = name
        cases.append(r)
        print(name, r['requested_window_completed'], r['measurements'], flush=True)
    times = sorted({float(t) for t in re.findall(r'^\+ ([0-9.]+) [0-9.]+$', circuit, re.M)})
    report = dict(cases=cases, diagnostic_only=True, pcb_changed=False,
                  command_points_and_circuit_unchanged=True,
                  original_minimum_distinct_breakpoint_interval_s=min(b-a for a,b in zip(times,times[1:])),
                  requested_minbreak_s=1e-12,
                  base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
                  scope=f'First {stop:g} seconds of full matrix, {options}, 0.5 us maxstep; only minbreak differs between runs. No component rating acceptance asserted.',
                  source='https://raw.githubusercontent.com/ngspice/ngspice/master/src/spicelib/analysis/cktsopt.c')
    (OUT/f'matrix-breakpoint-reproduction{tag}.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
