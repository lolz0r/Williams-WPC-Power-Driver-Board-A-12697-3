"""STTNG manual 3-2/3-3 CPU switch-interface voltage-margin screen.

This is a simplified downstream consumer test, not a CPU-board qualification
or justification for silently changing the retained +12 V regulation screen.
"""
import hashlib
import itertools
import json
from pathlib import Path
from corners import measurements
from ngspice_lib import NgSpice

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/verification/continuation/cpu-switch-margin'
MODELS = ROOT / 'tools/spice/models.lib'
OUT.mkdir(parents=True, exist_ok=True)
ng = NgSpice()
cases = []
for v12, v5, contact in itertools.product((9.5, 10.9175196, 12.8187381, 13.5), (4.75, 5.25), (.1, 100)):
    name = f'rail{v12:g}_logic{v5:g}_contact{contact:g}'
    source = f'''STTNG CPU switch voltage margin {name}; manual printed 3-2 and 3-3
.include {MODELS}
V12 twelve 0 {v12:.12g}
V5 five 0 {v5:g}
Vcolumncmd ccmd 0 PULSE(0 5 1m 20n 20n 1m 3m)
Rcdriver ccmd cin 30
Xcolumn cin column ULN2803CH
Rcolumn twelve column 1k
Ccolumn column 0 470p
Rpull twelve row 1.2k
Crow row 0 470p
Rsense row sense 1k
Dcpu row switch_wire D1N4148
Rcontact switch_wire sw {contact:g}
Dplayfield sw column D1N4148
* Harness capacitance is a sensitivity assumption in addition to the manual.
Charness switch_wire 0 2n
Xcomparator sense five out LM339
Routput five out 10k
.save v(row) v(sense) v(out) v(column)
.options method=gear reltol=.0001
.tran 100n 3m 0 100n
.control
run
let sim_end=time[length(time)-1]
print sim_end
let margin_open=v(sense)-{v5:g}
let margin_closed={v5:g}-v(sense)
meas tran input_open_margin MIN margin_open from=500u to=900u
meas tran input_closed_margin MIN margin_closed from=1100u to=1900u
meas tran output_high MIN v(out) from=500u to=900u
meas tran output_low MAX v(out) from=1100u to=1900u
meas tran return_high MIN v(out) from=2100u to=2900u
.endc
.end
'''
    path = OUT / (name + '.cir')
    path.write_text(source)
    ng.cmd('destroy all')
    log = ng.run_deck(str(path))
    path.with_suffix('.log').write_text('\n'.join(log) + '\n')
    v = measurements(log)
    limits = dict(sim_end=(.003-1e-9,.003+1e-9), input_open_margin=(.1,20),
                  input_closed_margin=(.1,20), output_high=(2,v5+.1),
                  output_low=(0,.8), return_high=(2,v5+.1))
    checks = {k: dict(value=v.get(k), min=lo, max=hi, passed=k in v and lo <= v[k] <= hi)
              for k,(lo,hi) in limits.items()}
    errors = [s for s in log if s.startswith('stderr') and not s.startswith('stderr Note:') and 'Warning' not in s]
    cases.append(dict(name=name, rail_V=v12, logic_V=v5, contact_ohms=contact,
                      measurements=v, checks=checks, errors=errors,
                      passed=not errors and all(c['passed'] for c in checks.values()),
                      deck_sha256=hashlib.sha256(source.encode()).hexdigest()))
report = dict(cases=cases, passed=all(c['passed'] for c in cases),
              model_sha256=hashlib.sha256(MODELS.read_bytes()).hexdigest(),
              manual_sha256=hashlib.sha256((ROOT/'.scratch/sttng-manual.pdf').read_bytes()).hexdigest(),
              sources=['https://archive.org/download/arcademanual_Star_Trek_TNG_OPS/Star_Trek_TNG_OPS.pdf',
                       'https://www.ti.com/lit/ds/symlink/lm339.pdf'],
              limitations=[
                  'Manual printed 3-2/3-3 functional circuits; no actual CPU-board netlist or complete CPU power-domain model',
                  'Generic ULN2803/diode and ideal hysteretic comparator models; no manufacturer offset/delay/process model',
                  '0.1 V minimum comparator-input margin is a screening guard band; TTL 0.8/2.0 V output screens',
                  'The fixed 5 V comparison input is within the legacy LM339 common-mode range when powered by these 12 V cases; no startup/partial-power claim',
                  'Matrix path adds a second series diode/column sink relative to the directly grounded dedicated-switch example',
                  '9.5-13.5 V brackets observed normal-run extrema but is not a replacement rail requirement or complete peripheral acceptance range',
                  '100 ohm contact and 2 nF harness capacitance are explicit sensitivity assumptions; measurements sampled 100 us after each command edge',
              ])
(OUT/'results.json').write_text(json.dumps(report, indent=2)+'\n')
print('CPU switch-margin cases:',len(cases),'passed:',sum(c['passed'] for c in cases))
raise SystemExit(0 if report['passed'] else 1)
