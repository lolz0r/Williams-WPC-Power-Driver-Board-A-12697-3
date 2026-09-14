"""Deterministic supplemental SPICE corners; explicitly bounded, not hardware certification."""
import itertools
import json
import math
import os
from pathlib import Path
import re
import tempfile

from ngspice_lib import NgSpice

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / 'output/verification/revision/corners'


def measurements(log):
    values = {}
    for line in log:
        match = re.match(r'stdout\s+(\w+)\s*=\s*([-+\d.eE]+)', line)
        if match:
            values[match[1]] = float(match[2])
    return values


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ng = NgSpice()
    results = []
    def run(name, source, limits, parameters, category='normal'):
        source = re.sub(r'^wrdata.*$', '', source, flags=re.M)
        source = source.replace('.include ../models.lib', '.include ' + str(HERE / 'models.lib'))
        path = OUT / (name + '.cir')
        path.write_text(source)
        ng.cmd('destroy all')
        log = ng.run_deck(str(path))
        (OUT / (name + '.log')).write_text('\n'.join(log) + '\n')
        values = measurements(log)
        errors = [s for s in log if s.startswith('stderr') and 'Warning' not in s]
        checks = {key: {'value': values.get(key), 'min': lo, 'max': hi,
                        'passed': key in values and math.isfinite(values[key]) and lo <= values[key] <= hi}
                  for key, lo, hi in limits}
        passed = bool(checks) and not errors and all(c['passed'] for c in checks.values())
        results.append(dict(name=name, category=category, parameters=parameters, checks=checks, passed=passed, errors=errors))
        print(name, 'PASS' if passed else 'FAIL', flush=True)
        return values

    # Worst hot-RDS fit is retained even at low ambient: conservative conduction.
    # Coil copper resistance is correlated with ambient, with +/-10% production tolerance.
    base = (HERE / 'decks/sol_high.cir').read_text()
    for ambient, rail, tolerance, gate in itertools.product((0, 25, 50), (63, 70, 86), (.9, 1.1), (4.5, 5.15)):
        resistance = 4.2 * tolerance * (1 + .00393 * (ambient - 20))
        source = base.replace('V50 v50 0 70', f'V50 v50 0 {rail}').replace('Rc cl v50c 4.2', f'Rc cl v50c {resistance}')
        source = source.replace('PULSE(0 4.6 ', f'PULSE(0 {gate} ')
        name = f'sol_t{ambient}_v{rail}_r{tolerance}_g{gate}'
        run(name, source, [('vout_peak', 0, 90), ('tj_rise_20pct', 0, 125 - ambient),
                           ('tj_rise_pulse', 0, 10), ('icoil_off', -.01, .1)],
            dict(ambient_C=ambient, rail_V=rail, coil_ohm=resistance, gate_V=gate, duty=.2, rth_C_W=62))

    # Zero-cross edges must follow the supplied mains frequency. Measurement
    # windows start away from an exact boundary to avoid coincident-edge ambiguity.
    base = (HERE / 'decks/zero_cross.cir').read_text()
    for frequency, scale, logic in itertools.product((50, 60), (.85, 1., 1.1), (4.75, 5.2)):
        source = base.replace('SIN(0 12.7 60)', f'SIN(0 {12.7*scale} {frequency})').replace('VCC vcc 0 5', f'VCC vcc 0 {logic}')
        source = source.replace('from=60m', 'from=61m').replace('.tran 5u 100m', '.tran 5u 140m')
        source = source.replace('.endc', 'let period = zc_r2-zc_r1\nprint period\n.endc')
        run(f'zc_f{frequency}_v{scale}_logic{logic}', source,
            [('period', .999 / frequency, 1.001 / frequency), ('zc_low', 0, .8), ('zc_high', 4., 5.3)],
            dict(frequency_Hz=frequency, line_scale=scale, logic_V=logic))

    # Full rectifier and averaged regulator load model: capacitor aging/tolerance,
    # line and frequency. Does not substitute for switching-regulator loop testing.
    base = (HERE / 'decks/psu_brownout.cir').read_text()
    for frequency, scale, capacitance in itertools.product((50, 60), (.88, 1., 1.1), (.8, 1.2)):
        source = base
        for old, nominal in [(11.18, 12.7), (16.54, 18.8), (15.5, 17.63)]:
            source = source.replace(f'SIN(0 {old} 60)', f'SIN(0 {nominal*scale} {frequency})')
        source = source.replace('10000u', f'{10000*capacitance}u')
        run(f'psu_f{frequency}_line{scale}_cap{capacitance}', source,
            [('v5_min', 4.75, 5.25), ('v12_min', 9., 12.6), ('v12u_min', 8., 20.)],
            dict(frequency_Hz=frequency, line_scale=scale, capacitor_scale=capacitance))

    # Bridge losses are measured electrically, then checked against the conservative
    # individual BR1 heatsinks, 25% catalog derating and maximum leakage allowance.
    base = (HERE / 'decks/bridge_loss.cir').read_text()
    for frequency, scale in itertools.product((50, 60), (.9, 1., 1.1)):
        source = re.sub(r'SIN\(0 ([\d.]+) 60\)', lambda m: f'SIN(0 {float(m[1])*scale} {frequency})', base)
        source = source.replace('from=233.33m', 'from=240m' if frequency==50 else 'from=250m')
        run(f'bridge_f{frequency}_line{scale}', source, [('tj_18a', 0, 125), ('tj_50a', 0, 125)],
            dict(frequency_Hz=frequency, line_scale=scale, ambient_C=50, BR1_rth_C_W=32.2))

    # Absolute capacitor voltage bound uses measured unloaded winding values,
    # +10% line, and zero diode drop. This is conservative and independent of SPICE.
    cap_bounds = {'C5': (9.86, 35), 'C6/C7': (13.3, 35), 'C11': (17.07, 35),
                  'C30': (12.47, 35), 'C8/C32': (55.2, 100)}
    capacitor_checks = {ref: {'peak_bound_V': rms*1.1*math.sqrt(2), 'rating_V': rating,
                              'passed': rms*1.1*math.sqrt(2) <= rating}
                        for ref, (rms, rating) in cap_bounds.items()}
    report = {'model_limitations': 'Approximate semiconductor/control models. No measured transformer impedance, thermal correlation, SOA or EMC certification.',
              'cases': results, 'capacitor_voltage_bounds': capacitor_checks,
              'passed': all(r['passed'] for r in results) and all(c['passed'] for c in capacitor_checks.values())}
    (OUT / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Passed', sum(r['passed'] for r in results), '/', len(results), 'SPICE cases')
    print('Capacitor bounds:', capacitor_checks)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
