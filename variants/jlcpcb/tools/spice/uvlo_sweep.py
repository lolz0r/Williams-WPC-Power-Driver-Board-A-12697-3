"""+5V raw-rail sweep for the cost board's TPS54360B UVLO design: mains 100 / 90 / 88 / 85 % x buck load 2 / 3 A with the averaged buck
model (eta 0.88, dropout Vout = 0.97 Vin - 0.5), 9 VAC winding (12.7 V peak at 100 %), GBU8J bridge, C5 = 10000 uF.  The UVLO factor is
left out on purpose so that the raw-rail minimum can be compared with candidate stop levels.  Writes output/spice/uvlo_sweep.md.
Usage: flatpak run --command=python3 org.kicad.KiCad tools/spice/uvlo_sweep.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngspice_lib import NgSpice
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'output', 'spice'))
DECK = """uvlo sweep mains {mains} load {load}
.include {models}
V9 s1 s2 SIN(0 {vpk} 60)
Rs1 s1 sa 0.05
Rs2 s2 sb 0.05
DS1 sa vraw DGBU8
DS2 sb vraw DGBU8
DS3 0 sa DGBU8
DS4 0 sb DGBU8
C5 vraw 0 10000u
Bv5 v5 0 V = min(5.10, max(0.97*v(vraw) - 0.5, 0))
R5 v5 0 {rload}
Bin5 vraw 0 I = (v(v5)*v(v5)/{rload}) / (0.88*max(v(vraw),1))
.tran 50u 200m uic
.control
run
meas tran vraw_min MIN v(vraw) from=150m to=200m
meas tran vraw_avg AVG v(vraw) from=150m to=200m
meas tran vraw_pp PP v(vraw) from=150m to=200m
meas tran v5_min MIN v(v5) from=150m to=200m
.endc
.end
"""
def main():
    ng = NgSpice(); rows = []
    os.chdir(os.path.join(HERE, 'decks'))
    for mains in (1.00, 0.90, 0.88, 0.85):
        for load in (2.0, 3.0):
            deck = os.path.join(HERE, 'decks', '_uvlo_tmp.cir')
            open(deck, 'w').write(DECK.format(mains=mains, load=load, vpk=12.7 * mains, rload=5.1 / load, models=os.path.join(HERE, 'models.lib')))
            ng.cmd('destroy all'); log = ng.run_deck(deck)
            meas = {}
            for l in log:
                if 'stdout' in l and '=' in l:
                    k, _, v = l.replace('stdout', '').strip().partition('=')
                    try: meas[k.strip()] = float(v.split()[0])
                    except Exception: pass
            rows.append((mains, load, meas.get('vraw_min'), meas.get('vraw_avg'), meas.get('vraw_pp'), meas.get('v5_min')))
            print(f"mains {mains:.0%} load {load:.0f} A: vraw min {meas.get('vraw_min'):.2f} avg {meas.get('vraw_avg'):.2f} pp {meas.get('vraw_pp'):.2f}  v5 min {meas.get('v5_min'):.3f}")
    os.remove(deck)
    lines = ['# +5V raw rail vs mains and load (averaged TPS54360B model, C5 = 10000 uF, GBU8J)', '',
             '| mains | 9 VAC peak (V) | +5V load (A) | raw minimum (V) | raw average (V) | raw ripple p-p (V) | +5V minimum (V) |', '|---|---|---|---|---|---|---|']
    for mains, load, vmin, vavg, vpp, v5 in rows:
        lines.append(f'| {mains:.0%} | {12.7 * mains:.2f} | {load:.0f} | {vmin:.2f} | {vavg:.2f} | {vpp:.2f} | {v5:.3f} |')
    lines += ['', 'The buck regulates 5.0 V down to Vin = 5.6 V (0.97 Vin - 0.5 = 5.0); the UVLO stop level must sit below the raw-rail minimum of the',
              'worst case that the board has to survive (88 % mains, 3 A) with margin for the EN threshold spread (1.1-1.3 V, i.e. +/- 8 % on the stop level).']
    os.makedirs(OUT, exist_ok=True); open(os.path.join(OUT, 'uvlo_sweep.md'), 'w').write('\n'.join(lines) + '\n')
if __name__ == '__main__':
    main()
