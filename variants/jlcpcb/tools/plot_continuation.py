"""Export source-headroom/ripple tradeoffs; all curves are simulations."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/verification/continuation'
cases = json.loads((OUT/'reservoir-headroom/results.json').read_text())['cases']
fig, axes = plt.subplots(1, 2, figsize=(11, 4.7), layout='constrained')
colors = {'shared': '#b65235', 'isolated': '#21739b'}
for topology in ('shared', 'isolated'):
    selected = sorted((c for c in cases if c['topology'] == topology and c['frequency_Hz'] == 60
                       and c['line_scale'] == .9 and c['lamp_ohms'] == 2.5),
                      key=lambda c:c['nominal_reservoir_uF'])
    axes[0].plot([c['nominal_reservoir_uF']/1000 for c in selected],
                 [c['measurements']['buck_input_min'] for c in selected],
                 'o-', color=colors[topology], label='Shared reservoir' if topology == 'shared' else 'Half isolated for U21')
axes[0].axhline(12.3, color='#555555', ls='--', label='12.3 V headroom screen')
axes[0].set(title='Input minimum at 90% line, 60 Hz',
            xlabel='Total nominal reservoir capacitance (mF)', ylabel='Regulator input minimum (V)')
axes[0].set_xticks([20,30,40]);axes[0].legend(fontsize=8, loc='lower right')
for frequency, color in ((50, '#8856a7'), (60, '#21739b')):
    selected = sorted((c for c in cases if c['topology'] == 'isolated' and c['frequency_Hz'] == frequency
                       and c['nominal_reservoir_uF'] == 20000 and c['lamp_ohms'] == 2.5),
                      key=lambda c:c['line_scale'])
    axes[1].plot([100*c['line_scale'] for c in selected],
                 [c['measurements']['capacitor_rms'] for c in selected], 'o-', color=color,
                 label=f'{frequency} Hz, single lamp capacitor')
    axes[1].axhline(7.89*(.9 if frequency == 50 else 1), color=color, ls='--',
                   label=f'Retained {frequency} Hz ripple screen')
axes[1].set(title='Ripple tradeoff: split two 10 mF capacitors',
            xlabel='Secondary amplitude (% of nominal)', ylabel='Lamp-capacitor ripple current (A RMS)')
axes[1].set_xticks([90,100,110]);axes[1].legend(fontsize=8, loc='lower right')
for ax in axes:
    ax.grid(alpha=.2)
fig.suptitle('Unbuilt U21 input-isolation candidate — source-only SPICE\n'
             '2.5 Ω lamp load, 10 W regulator input, −20% capacitance; assumed transformer and ESR', fontsize=11)
fig.savefig(OUT/'reservoir-tradeoff.png', dpi=180)
fig.savefig(OUT/'reservoir-tradeoff.pdf')
print(OUT/'reservoir-tradeoff.png')
