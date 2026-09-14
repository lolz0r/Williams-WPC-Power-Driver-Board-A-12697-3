"""Fast source-only sensitivity study for U21; not a switching-regulator pass.

Keep the four-diode bridge and actual 20 mF nominal reservoir as the baseline.
Larger capacitors are explicitly hypothetical, with the same -20% tolerance.
"""
import hashlib
import itertools
import json
from pathlib import Path

from corners import measurements
from ngspice_lib import NgSpice

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/verification/continuation/reservoir-headroom'
MODELS = ROOT / 'tools/spice/models.lib'
OUT.mkdir(parents=True, exist_ok=True)
ng = NgSpice()
cases = []
for topology, nominal_uF, frequency, line, lamp_ohms in itertools.product(
        ('shared', 'isolated'), (20000, 30000, 40000), (50, 60), (.9, 1., 1.1), (2.5, 5.)):
    name = f'{topology}_c{nominal_uF}_f{frequency}_line{line:g}_lamp{lamp_ohms:g}'
    raw_cap = nominal_uF * .8 * (.5 if topology == 'isolated' else 1)
    buck_node = 'dedicated' if topology == 'isolated' else 'vinf'
    # Split the total capacitance equally, retaining 50 mOhm ESR for each
    # branch (sensitivity assumption, not a selected capacitor's guarantee).
    isolation = (f'Disolate vinf dedicated DB560C\n'
                 f'Rdedicated dedicated isolated_stored .05\n'
                 f'Cdedicated isolated_stored 0 {raw_cap:g}u\n'
                 if topology == 'isolated' else '')
    # 12 V * 0.75 A / 90% efficiency = 10 W; not a controller model.
    # Smooth enabling affects startup only; steady-state power is 10 W.
    source = f'''U21 source headroom; hypothetical reservoir sensitivity {name}
.include {MODELS}
Vsecondary secp secn SIN(0 {18.8*line:.12g} {frequency})
Rsec1 secp acp .05
Rsec2 secn acn .05
Dbridge1 acp vinf DSCH20100
Dbridge2 acn vinf DSCH20100
Dbridge3 0 acp DSCH20100
Dbridge4 0 acn DSCH20100
Creservoir stored 0 {raw_cap:g}u
Rreservoir stored vinf .05
Rrawbleed vinf 0 5000
Rlamps vinf 0 {lamp_ohms:g}
{isolation}Bbuck {buck_node} 0 I=10/max(v({buck_node}),4.5)*min(max((time-20m)/10m,0),1)
.save v(vinf) v({buck_node}) i(Vsecondary) @dbridge1[id] @dbridge2[id] @creservoir[i]
.options method=gear reltol=.0001 abstol=100n vntol=10u
.tran 10u 500m 0 10u
.control
run
let sim_end=time[length(time)-1]
print sim_end
meas tran raw_min MIN v(vinf) from=400m to=500m
meas tran raw_max MAX v(vinf) from=400m to=500m
meas tran raw_mean AVG v(vinf) from=400m to=500m
meas tran buck_input_min MIN v({buck_node}) from=400m to=500m
meas tran buck_input_max MAX v({buck_node}) from=400m to=500m
meas tran secondary_rms RMS i(Vsecondary) from=400m to=500m
meas tran capacitor_rms RMS @creservoir[i] from=400m to=500m
meas tran diode_peak MAX @dbridge1[id] from=400m to=500m
meas tran inrush_peak MAX @dbridge1[id] from=0 to=30m
.endc
.end
'''
    path = OUT / (name + '.cir')
    path.write_text(source)
    ng.cmd('destroy all')
    log = ng.run_deck(str(path))
    (OUT / (name + '.log')).write_text('\n'.join(log) + '\n')
    values = measurements(log)
    errors = [x for x in log if x.startswith('stderr')
              and not x.startswith('stderr Note:') and 'Warning' not in x]
    required = {'raw_min', 'raw_max', 'raw_mean', 'buck_input_min', 'buck_input_max',
                'secondary_rms', 'capacitor_rms', 'diode_peak', 'inrush_peak', 'sim_end'}
    complete = not errors and required <= values.keys() and abs(values.get('sim_end', 0) - .5) < 1e-8
    case = dict(name=name, topology=topology, nominal_reservoir_uF=nominal_uF,
                simulated_reservoir_uF=nominal_uF*.8, frequency_Hz=frequency,
                line_scale=line, lamp_ohms=lamp_ohms, measurements=values,
                completed=complete, errors=errors,
                raw_above_12V=complete and values['raw_min'] > 12,
                buck_above_12_3V_screen=complete and values['buck_input_min'] >= 12.3,
                deck_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    cases.append(case)
    print(name, values, flush=True)
report = dict(cases=cases, completed=all(x['completed'] for x in cases),
              pcb_changed=False, regulator_verified=False,
              model_sha256=hashlib.sha256(MODELS.read_bytes()).hexdigest(),
              assumptions=dict(secondary_peak_V=18.8, resistance_per_leg_ohm=.05,
                               reservoir_ESR_ohm=.05, buck_input_power_W=10),
              limitations=[
                  '10 W constant-power input approximates 0.75 A output at 90% efficiency; no controller, startup, dropout or overshoot qualification',
                  '12.3 V is a headroom screening value, not a guaranteed TPS54360B operating boundary',
                  'Transformer impedance, lamp loading, capacitor ESR and aging require measurement',
                  '30 mF and 40 mF nominal are hypothetical alternatives, not JLCPCB selections or CAD changes',
                  'Isolated topology splits total capacitance equally between the lamp rail and diode-isolated regulator input; no native PCB change or protection qualification',
                  'Reported inrush starts at an AC zero crossing; other phases and fuse I2t remain unqualified for hypothetical capacitors',
              ])
(OUT / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
raise SystemExit(0 if report['completed'] else 1)
