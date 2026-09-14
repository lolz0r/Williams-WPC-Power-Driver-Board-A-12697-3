"""Compare native and added-reservoir U21 input circuits with per-capacitor ESR.

The extra capacitor/diode are simulation candidates, not native parts. This is
an input-headroom/ripple/inrush screen; it does not simulate the buck controller.
"""
import hashlib
import argparse
import itertools
import json
from pathlib import Path

from corners import measurements
from ngspice_lib import NgSpice

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/verification/prototype-readiness/reservoir'
MODEL = ROOT / 'tools/spice/models.lib'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flasher', action='store_true', help='Existing flasher rail before/after moving U21')
    args = parser.parse_args()
    out = OUT.parent/'flasher-source' if args.flasher else OUT
    out.mkdir(parents=True, exist_ok=True)
    if (out/'results.json').exists():
        raise FileExistsError('Preserve prior reservoir experiment')
    ng = NgSpice()
    cases = []
    topologies = ['flasher_only', 'flasher_with_u21'] if args.flasher else ['native', 'added']
    for topology, frequency, line, esr, imbalance, phase in itertools.product(
            topologies, [50, 60], [.9, 1.1], [.02, .05, .1], [False, True], [0, 90]):
        name = f'{topology}_f{frequency}_line{line:g}_esr{esr:g}_imb{int(imbalance)}_phase{phase}'
        caps = [('c6', 8000, esr), ('c7', 12000 if imbalance else 8000, esr*2 if imbalance else esr)]
        if args.flasher:
            caps = [('c11', 12000 if imbalance else 8000, esr)]
        if topology == 'added':
            caps.append(('dedicated', 8000, esr))
        nodes = {ref: ('buckin' if ref == 'dedicated' else 'raw') for ref, _, _ in caps}
        captext = ''.join(f'R{ref} {nodes[ref]} {ref}_stored {r:g}\nC{ref} {ref}_stored 0 {c:g}u\n'
                          for ref, c, r in caps)
        buckin = 'buckin' if topology == 'added' else 'raw'
        isolation = 'Disolate raw buckin DB560C\n' if topology == 'added' else ''
        measures = ['sim_end', 'input_min', 'input_max', 'bridge_peak', 'bridge_i2t_start', 'bridge_power', 'secondary_rms']
        commands = ''
        for ref, _, _ in caps:
            commands += f'meas tran rms_{ref} RMS @c{ref}[i] from=.4 to=.5\n'
            measures.append('rms_'+ref)
        if topology == 'added':
            commands += 'let isolate_power=v(raw,buckin)*@disolate[id]\nmeas tran isolate_peak MAX @disolate[id]\nmeas tran isolate_power_avg AVG isolate_power from=.4 to=.5\n'
            measures += ['isolate_peak', 'isolate_power_avg']
        source = f'''U21 reservoir candidate: {name}; 10 W constant-power regulator approximation
.include {MODEL}
Vsecondary secp secn SIN(0 {(22.6 if args.flasher else 18.8)*line:g} {frequency} 0 0 {phase})
Rsec1 secp acp .05
Rsec2 secn acn .05
Dbridge1 acp raw DSCH20100
Dbridge2 acn raw DSCH20100
Dbridge3 0 acp DSCH20100
Dbridge4 0 acn DSCH20100
{captext}{isolation}{'Bflashers raw 0 I=2.5*tanh(v(raw)/1)' if args.flasher else 'Rlamps raw 0 2.5'}
Rbleed raw 0 5000
Bbuck {buckin} 0 I={0 if topology == 'flasher_only' else 10}/max(v({buckin}),4.5)*min(max((time-20m)/10m,0),1)
.save v(raw) v({buckin}) v(acp) i(Vsecondary) @dbridge1[id] @dbridge2[id] {'@disolate[id]' if topology == 'added' else ''} {' '.join('@c'+r+'[i]' for r,_,_ in caps)}
.options method=gear reltol=.0001 abstol=100n vntol=10u klu itl4=100
.tran 10u .5 0 10u uic
.control
set numdgt=12
run
let sim_end=time[length(time)-1]
print sim_end
meas tran input_min MIN v({buckin}) from=.4 to=.5
meas tran input_max MAX v({buckin}) from=.4 to=.5
meas tran bridge_peak MAX @dbridge1[id]
meas tran secondary_rms RMS i(Vsecondary) from=.4 to=.5
let bridge_i2=@dbridge1[id]^2
meas tran bridge_i2t_start INTEG bridge_i2 from=0 to=.03
let bridge_p=v(acp,raw)*@dbridge1[id]
meas tran bridge_power AVG bridge_p from=.4 to=.5
{commands}.endc
.end
'''
        deck = out/(name+'.cir')
        if deck.exists():
            raise FileExistsError(deck)
        deck.write_text(source)
        ng.cmd('destroy all')
        log = ng.run_deck(str(deck))
        deck.with_suffix('.log').write_text('\n'.join(log)+'\n')
        v = measurements(log)
        errors = [s for s in log if s.startswith('stderr') and not s.startswith('stderr Note:') and 'Warning' not in s]
        completed = not errors and all(k in v for k in measures) and abs(v.get('sim_end', 0)-.5) < 1e-8
        rating = 7.89*(.9 if frequency == 50 else 1)
        checks = {'headroom': completed and v['input_min'] >= 12.3,
                  'capacitor_ripple': completed and all(v['rms_'+r] <= rating for r,_,_ in caps)}
        if args.flasher:
            checks['secondary_below_5A_fuse_rating'] = completed and v['secondary_rms'] <= 5
        case = dict(name=name, topology=topology, frequency_Hz=frequency, line_scale=line,
                    ESR_ohm=esr, capacitance_ESR_imbalance=imbalance, start_phase_deg=phase,
                    measurements=v, completed=completed, checks=checks, errors=errors,
                    capacitor_ripple_limit_A=rating, deck_sha256=hashlib.sha256(source.encode()).hexdigest())
        cases.append(case)
        print(name, checks, flush=True)
    report = dict(cases=cases, completed=all(c['completed'] for c in cases),
                  pcb_changed=False, models_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),
                  pcb_sha256=hashlib.sha256((ROOT/'wpc_power_driver_cost.kicad_pcb').read_bytes()).hexdigest(),
                  limitations=['Source-only constant-power load, not a controller or voltage-regulation pass',
                               'ESR/winding resistance/lamp load are explicit assumptions; no measured transformer model',
                               'Extra 10000 uF nominal reservoir and B560C isolation diode are unbuilt candidates',
                               '12.3 V is an engineering headroom screen, not a guaranteed dropout specification',
                               'Inrush and bridge power are reported without claiming fuse or transient SOA qualification',
                               'Ripple limits retain local capacitor ambient at or below 60 C'])
    if args.flasher:
        report['limitations'] = ['Source-only comparison of native +20 V supply and unbuilt U21 reassignment',
                                'One C11 capacitor at +/-20 percent, not two-capacitor imbalance',
                                '2.5 A passive bounded flasher-current envelope and 10 W approximate regulator input',
                                'A 5 A RMS fuse-rating check alone does not qualify fuse derating, inrush, clearing or thermal behavior',
                                'No new component or native CAD change; transformer and ESR remain assumptions']
    (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
