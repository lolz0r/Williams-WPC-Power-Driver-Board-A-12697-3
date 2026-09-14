"""Bind continued investigations to unchanged JLC-2 and retain every failed run."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/verification/continuation'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def path(relative):
    return OUT / relative


def normalized_circuit(text):
    # Compare physical devices and command points, allowing additional saved
    # vectors/measurements in energy-balance investigations.
    return '\n'.join(line for line in text.split('.save')[0].splitlines()[1:]
                     if not line.lower().startswith(('.options', '.tran ')))


native = ROOT / 'wpc_power_driver_cost.kicad_pcb'
netlist = ROOT / 'output/release-candidate/reports/netlist.xml'
assert digest(native) == '5afdf84d9bd267220aaa867f964622771d14b582d7a94e0bdca882a5982d7bc4'
assert digest(netlist) == 'd83a480ec2a1782bdbb1d6bddb01961f0359066e7ad5f34efe142b34f2f3b568'
prespin = ROOT / 'output/verification/prespin'
original_coil = prespin / 'replay-loss-segments/coil1_0.15625us_vendor_diode.cir'
original_matrix = prespin / 'replay-matrix/matrix_20.69V.cir'
trials = []
for result_path in sorted(OUT.rglob('*.run.json')):
    report = read(result_path)
    deck = result_path.with_name(result_path.name.removesuffix('.run.json') + '.cir')
    assert digest(deck) == report['deck_sha256'], deck
    measurements = report['measurements']
    # Parser failure or runtime completion is not a completed transient.
    match = re.search(r'^\.tran\s+\S+\s+(\S+)', deck.read_text(), re.M | re.I)
    stop = float(match[1])  # Generated bounded fixtures use seconds here.
    complete = (report['execution_completed'] and not report['errors']
                and abs(measurements.get('sim_end', -1) - stop) <= 1e-7)
    same_circuit = None
    if 'coil-full-window' in str(deck):
        same_circuit = normalized_circuit(deck.read_text()) == normalized_circuit(original_coil.read_text())
    elif '/matrix/' in str(deck):
        same_circuit = normalized_circuit(deck.read_text()) == normalized_circuit(original_matrix.read_text())
    if same_circuit is not None:
        assert same_circuit, deck
    shunt = re.search(r'\brshunt=([^\s]+)', deck.read_text(), re.I)
    trials.append(dict(path=str(result_path.relative_to(OUT)), complete=complete,
                       timed_out=report['timed_out'], elapsed_s=report['elapsed_s'],
                       unchanged_device_values_and_command_points=same_circuit,
                       numerical_shunt_ohms=float(shunt[1]) if shunt else None,
                       measurements=measurements,
                       errors=report['errors']))

by_path = {x['path']: x for x in trials}
comparisons = []


def compare(a, b, keys):
    first, second = by_path.get(a), by_path.get(b)
    complete = bool(first and second and first['complete'] and second['complete'])
    for key, relative, absolute in keys:
        x = first['measurements'].get(key) if first else None
        y = second['measurements'].get(key) if second else None
        difference = abs(x-y) if x is not None and y is not None else None
        limit = max(absolute, relative*max(abs(x), abs(y))) if difference is not None else None
        comparisons.append(dict(a=a, b=b, metric=key, both_complete=complete,
                                coarse=x, fine=y, difference=difference, limit=limit,
                                passed=bool(complete and difference is not None and difference <= limit)))


compare('coil-full-window/coil1_vendor_strict_klu_0.625us.run.json',
        'coil-full-window/extended-runtime/coil1_vendor_strict_klu_0.3125us.run.json',
        [('dissipation_w', .05, .001), ('terminal_w', .05, .001),
         ('vds_peak', .02, .001), ('coil_peak', .02, .001)])
compare('matrix/extended-runtime/matrix_trap_1us.run.json',
        'matrix/extended-runtime/matrix_trap_0.5us.run.json',
        [(f'{kind}{i}_{metric}', .05, .001) for kind in ('row','col')
         for i in range(8) for metric in ('peak','power')])
compare('matrix/matrix_trap_rshunt1G_1us.run.json',
        'matrix/matrix_trap_rshunt1G_0.5us.run.json',
        [(f'{kind}{i}_{metric}', .05, .001) for kind in ('row','col')
         for i in range(8) for metric in ('peak','power')])
matrix_reference = read(original_matrix.with_suffix('.json'))
for case in trials:
    values = case['measurements']
    if case['path'].startswith('coil-full-window/'):
        limits = {'vds_peak': (0,90), 'coil_peak': (0,86/3.78*1.02),
                  'tj_dissipation': (0,125), 'tj_terminal': (0,125)}
    elif case['path'].startswith('matrix/'):
        limits = {k: (v['min'],v['max']) for k,v in matrix_reference['checks'].items() if k != 'sim_end'}
    else:
        continue
    case['screens_passed'] = case['complete'] and all(k in values and lo <= values[k] <= hi
                                                    for k,(lo,hi) in limits.items())

headroom = read(path('reservoir-headroom/results.json'))
cpu = read(path('cpu-switch-margin/results.json'))
isolation = []
for p in sorted(path('isolated-buck').rglob('*.json')):
    if p.name.endswith('.run.json'):
        continue
    r = read(p)
    isolation.append(dict(path=str(p.relative_to(OUT)), passed=r['passed'],
                          timed_out=r['timed_out'], measurements=r['measurements'], checks=r['checks']))
# Keep the original ripple screening convention, including its conservative
# 100 Hz factor. A promising headroom result must not silently waive it.
ripple = []
for case in headroom['cases']:
    if case['topology'] != 'isolated' or case['nominal_reservoir_uF'] != 20000:
        continue
    rating = 7.89 * (.9 if case['frequency_Hz'] == 50 else 1)
    value = case['measurements']['capacitor_rms']
    ripple.append(dict(name=case['name'], measured_A=value, retained_limit_A=rating,
                       passed=value <= rating))
energy_trial = by_path.get('coil-full-window/coil1_vendor_energy_balance_0.625us.run.json')
energy_values = energy_trial['measurements'] if energy_trial else {}
energy_limit = max(.001, .01*abs(energy_values.get('e_terminal', 0)))
energy_check = dict(measurements=energy_values, residual_limit_J=energy_limit,
                    passed=bool(energy_trial and energy_trial['complete']
                                and 'energy_residual' in energy_values
                                and abs(energy_values['energy_residual']) <= energy_limit))
report = dict(pcb_sha256=digest(native), netlist_sha256=digest(netlist), pcb_changed=False,
              prior_release_readiness_changed=False, fab_ready=False,
              reservoir_cases_completed=sum(x['completed'] for x in headroom['cases']),
              cpu_switch_cases_passed=sum(x['passed'] for x in cpu['cases']),
              isolated_C6_ripple_screens=ripple, isolation_trials=isolation,
              simulation_trials=trials, convergence_comparisons=comparisons,
              coil_energy_balance=energy_check,
              coil_vendor_model_convergence=all(x['passed'] for x in comparisons[:4]),
              matrix_convergence=all(x['passed'] for x in comparisons[4:36]),
              matrix_shunt_sensitivity_convergence=all(x['passed'] for x in comparisons[36:]),
              limitations=[
                  'Converged model results do not qualify semiconductor SOA, physical harness clearance or loaded-board temperature',
                  'Source-only and CPU consumer screens supplement, and do not replace, the original full-input voltage failures',
                  'Diode-isolated C7 arrangement is unpromoted; native CAD and release archives remain JLC-2',
                  'Runtime limits are explicit incomplete runs, distinct from solver failures',
                  '1 Gohm rshunt cases deliberately perturb every analog node to ground; reported separately from the original matrix model',
              ])
report['pending_bounded_runs'] = [str(p.relative_to(OUT)) for folder in
    ('isolated-buck', 'coil-transitions', 'coil-full-window', 'matrix')
    for p in path(folder).rglob('*.cir') if not p.with_suffix('.run.json').exists()]
report['model_files_sha256'] = {str(p.relative_to(ROOT)): digest(p) for p in [
    ROOT/'tools/spice/models.lib', ROOT/'.scratch/vendor-models/S3M.spice.txt',
    ROOT/'.scratch/vendor-models/SLVMCT7/TPS54360_PSPICE_TRANS/TPS54360_TRANS.LIB']}
report['evidence_sha256'] = {str(p.relative_to(ROOT)): digest(p) for p in sorted(OUT.rglob('*'))
                             if p.is_file() and p.name != 'summary.json'}
report['sources_sha256'] = {str(ROOT.joinpath(s).relative_to(ROOT)): digest(ROOT/s) for s in [
    'tools/continuation_summary.py', 'tools/plot_continuation.py', 'tools/spice/bounded_run.py', 'tools/spice/reservoir_headroom.py',
    'tools/spice/isolated_buck_trial.py', 'tools/spice/coil_transition_trial.py',
    'tools/spice/cpu_switch_margin.py', 'tools/spice/models.lib', 'research/vendor-model-sources.json']}
path('summary.json').write_text(json.dumps(report, indent=2)+'\n')
print('Continuation evidence:',len(trials),'runs; coil convergence',report['coil_vendor_model_convergence'],
      'matrix convergence',report['matrix_convergence'],'fabrication ready',report['fab_ready'])
