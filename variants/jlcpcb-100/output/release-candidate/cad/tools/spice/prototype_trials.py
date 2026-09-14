"""Preserved, bounded prototype-readiness experiments; never modifies native CAD.

Each case gets a new directory entry, its original-input hashes, an explicit end
time check and the unchanged electrical acceptance screens. Candidate circuitry
is identified separately from solver-only experiments.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from bounded_run import run_bounded

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/verification/prototype-readiness'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=['matrix', 'isolated', 'reverse'])
    p.add_argument('--name', required=True)
    p.add_argument('--wall-seconds', type=float, default=600)
    p.add_argument('--step-us', type=float, default=1)
    p.add_argument('--options', default='method=gear reltol=.002 abstol=1n vntol=10u klu itl4=500')
    p.add_argument('--rail', choices=['5v', '12v'], default='12v')
    p.add_argument('--bypass', choices=['none', 'output', 'switch'], default='output')
    p.add_argument('--stop-ms', type=float)
    p.add_argument('--lamp-form', choices=['current', 'resistor'], default='current')
    p.add_argument('--gate-series-collapse', action='store_true')
    p.add_argument('--raw-reservoir-uf', type=float)
    p.add_argument('--compensation-nf', type=float)
    p.add_argument('--flasher-input', action='store_true')
    p.add_argument('--direct-input', action='store_true')
    p.add_argument('--scenario', choices=['startup', 'loss_restart'], default='startup')
    p.add_argument('--load', type=float, default=.75)
    p.add_argument('--stress-only', action='store_true', help='Short precharge screen; no startup/recovery acceptance')
    p.add_argument('--isolate-input', action='store_true')
    p.add_argument('--protection-model', choices=['DB560C', 'DSCH20100'], default='DB560C')
    a = p.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_.-]+', a.name):
        p.error('name must be a simple filename')
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (a.name + '.cir')
    if path.exists():
        raise FileExistsError(path)
    changes = []
    if a.kind == 'matrix':
        base = ROOT / 'output/verification/prespin/replay-matrix/matrix_20.69V.cir'
        source = base.read_text()
        limits = {k: (c['min'], c['max']) for k, c in json.loads(base.with_suffix('.json').read_text())['checks'].items()}
        source = re.sub(r'^\.options.*$', '.options ' + a.options, source, flags=re.M)
        source = re.sub(r'^(\.tran 5u \S+ 0) .*$', rf'\g<1> {a.step_us:g}u', source, flags=re.M)
        assert source.split('.save')[0] == base.read_text().split('.save')[0]
        changes.append('Solver options/maxstep only; identical circuit and ROM PWL points')
        if a.lamp_form == 'resistor':
            source, count = re.subn(r'^Blamp(\d+) (\S+) (\S+) I=v\([^\n]+?\)/\((7\+18\*max\(v\(t\d+\),0\))\)$',
                                    r'Rlamp\1 \2 \3 R={\4}', source, flags=re.M)
            assert count == 64, count
            changes.append('Same lamp I-V law restamped as a behavioral resistor')
        if a.gate_series_collapse:
            for i in range(8):
                old = f'Routr{i} row{i}cmd row{i}q 40\nRg{i} row{i}q row{i}g 100'
                assert old in source
                source = source.replace(old, f'Rg{i} row{i}cmd row{i}g 140')
            changes.append('Algebraically collapse unloaded 40+100 ohm gate series resistors to 140 ohms')
        end = .37
    elif a.kind == 'isolated':
        base = ROOT / 'output/verification/continuation/isolated-buck/startup_0.75A_f60_cc100n_stop30m.cir'
        source = base.read_text()
        limits = {k: (c['min'], c['max']) for k, c in json.loads(base.with_suffix('.json').read_text())['checks'].items()}
        changes.extend(['Unbuilt candidate: move C7 behind added B560C input diode',
                        'U21 input divider and local input capacitors follow isolated input',
                        'Native board remains unchanged; original TI model retained'])
        end = .03
        source = source.replace('Rload vout 0 16', f'Rload vout 0 {12/a.load:.12g}')
        if a.flasher_input:
            source = source.replace('V=16.92*sin', 'V=20.34*sin')
            # Bound current at 2.5 A in operation; retain passive I-V behavior
            # around zero during supply interruption (no ideal current sink
            # can force a discharged reservoir negative).
            source = source.replace('Rlamps vinf 0 2.5', 'Bflashers vinf 0 I=2.5*tanh(v(vinf)/1)')
            changes = ['Unbuilt candidate: feed U21 through B560C from +20 V flasher rail',
                       'Keep C11 on flasher rail; add dedicated 10000 uF nominal regulator reservoir',
                       'Retain both C6/C7 on lamp rail; 2.5 A sustained flasher load assumption',
                       '16 V secondary at minus 10 percent, existing four-diode bridge, 0.1 ohm winding resistance']
            changes.append('Passive bounded-current flasher envelope I=2.5*tanh(V/1 V), approaching 2.5 A at operating voltage')
        if a.direct_input:
            assert a.flasher_input
            source = re.sub(r'^(Disolate|Rdedicated|Cdedicated) .*\n', '', source, flags=re.M)
            source = source.replace('buck_input', 'vinf').replace(' @disolate[id]', '')
            source = re.sub(r'^meas tran isolation_diode_peak .*\n', '', source, flags=re.M)
            changes = ['Unbuilt candidate: move U21 input/divider/local ceramics from +18 V to existing +20 V flasher rail',
                       'No new diode or capacitor; C11 remains the 10000 uF nominal raw reservoir',
                       'Retain C6/C7 on lamp rail; 2.5 A sustained flasher load assumption',
                       '16 V secondary at minus 10 percent, existing four-diode bridge, 0.1 ohm winding resistance']
        if a.scenario == 'loss_restart':
            source = re.sub(r'^(Bsecondary.*)$', r'\1*((time<25m)?1:((time<85m)?0:min((time-85m)/100u,1)))', source, flags=re.M)
            changes.append('AC off at 25 ms, restored at 85 ms with 100 us ramp')
    else:
        base = ROOT / f'output/verification/prespin/power-sequence/{a.rail}_precharged_output_{"1" if a.rail == "5v" else "0.75"}A_250n.cir'
        source = base.read_text()
        original = json.loads(base.with_suffix('.json').read_text())
        limits = {k: (c['min'], c['max']) for k, c in original['checks'].items()}
        if a.bypass != 'none':
            node = 'vout' if a.bypass == 'output' else 'sw'
            source = source.replace('.save ', f'Vbypass {node} bypass 0\nDbypass bypass vinf {a.protection_model}\n.save i(Vbypass) v(bypass) ')
            source = source.replace('set wr_singlescale', 'meas tran bypass_peak MAX i(Vbypass)\nlet bypass_power=v(bypass,vinf)*i(Vbypass)\nmeas tran bypass_energy INTEG bypass_power\nlet bypass_i2=i(Vbypass)^2\nmeas tran bypass_i2t INTEG bypass_i2\nset wr_singlescale')
            changes.append(f'Unbuilt candidate: {a.protection_model} from {node} to input rail; measure bypass current and energy')
        else:
            changes.append('Unmodified native regulator topology, precharged outputs')
        end = .12
        if a.isolate_input:
            source = source.replace('Cin vinf 0 20u', 'Cin local_input 0 20u')
            source = source.replace('sw rt vinf fb', 'sw rt local_input fb')
            source = source.replace('Ren1 vinf en', 'Ren1 local_input en')
            source = source.replace('Dbypass bypass vinf', 'Dbypass bypass local_input')
            source = source.replace('v(bypass,vinf)', 'v(bypass,local_input)')
            source = source.replace('.save ', f'Dinput vinf local_input {a.protection_model}\n.save v(local_input) ')
            changes.append('Added input blocking diode after the raw reservoir, before local 20 uF and U20/U21')
    if a.raw_reservoir_uf is not None:
        assert a.kind != 'matrix' and a.raw_reservoir_uf > 0
        source, count = re.subn(r'^Creservoir stored 0 \S+',
                               f'Creservoir stored 0 {a.raw_reservoir_uf:g}u', source, flags=re.M)
        assert count == 1
        changes.append(f'Candidate raw-rail capacitance {a.raw_reservoir_uf:g} uF after tolerance')
    if a.compensation_nf is not None:
        assert a.kind != 'matrix' and a.compensation_nf > 0
        source, count = re.subn(r'^Cc cc 0 \S+', f'Cc cc 0 {a.compensation_nf:g}n', source, flags=re.M)
        assert count == 1
        changes.append(f'Candidate compensation capacitor {a.compensation_nf:g} nF')
    if a.stop_ms is not None:
        end = a.stop_ms / 1000
        source = re.sub(r'^(\.tran \S+) \S+', rf'\g<1> {end:.12g}', source, flags=re.M)
        limits['sim_end'] = (end - 1e-8, end + 1e-8)
        if a.kind == 'reverse':
            source = re.sub(r'^meas tran recovery .*$', f'meas tran recovery AVG v(vout) from={end-.005:g} to={end:g}', source, flags=re.M)
        if a.kind == 'isolated':
            source = re.sub(r'from=0\.0216666666667 to=0\.03', f'from={end-1/120:.12g} to={end:.12g}', source)
        changes.append(f'Transient ends at {end:g} seconds')
    if a.stress_only:
        assert a.kind == 'reverse' and a.stop_ms is not None
        source = re.sub(r'^meas tran (before_loss|recovery) .*\n', '', source, flags=re.M)
        limits.pop('recovery', None)
        limits.pop('before_loss', None)
        changes.append('Initial reverse-stress screen only; no recovery or complete-sequence claim')
    source = source.replace('.control\n', '.control\nset numdgt=12\n')
    source = re.sub(r'^(wrdata) \S+', rf'\g<1> {path.with_suffix(".csv")}', source, flags=re.M)
    path.write_text(source)
    r = run_bounded(path, a.wall_seconds, pspice=a.kind != 'matrix')
    values = r['measurements']
    checks = {k: dict(value=values.get(k), min=lo, max=hi,
                      passed=k in values and math.isfinite(values[k]) and lo <= values[k] <= hi)
              for k, (lo, hi) in limits.items()}
    r.update(checks=checks, passed=r['execution_completed'] and not r['errors'] and all(c['passed'] for c in checks.values()),
             kind=a.kind, pcb_changed=False, candidate_only=a.kind != 'matrix' and a.bypass != 'none',
             changes=changes, arguments=vars(a), required_end_s=end,
             base_deck_sha256=sha(base), pcb_sha256=sha(ROOT/'wpc_power_driver_cost.kicad_pcb'),
             models_sha256=sha(ROOT/'tools/spice/models.lib'),
             limitations=['Typical/approximate device models; no hardware, SOA, thermal or assembly qualification',
                          'A failed or partial transient cannot establish full-window convergence',
                          'Candidate circuitry is not present in current CAD or purchasing/manufacturing files'])
    path.with_suffix('.json').write_text(json.dumps(r, indent=2) + '\n')
    print(json.dumps({k: r[k] for k in ['kind', 'passed', 'elapsed_s', 'timed_out', 'measurements', 'errors']}, indent=2), flush=True)
    return 0 if r['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
