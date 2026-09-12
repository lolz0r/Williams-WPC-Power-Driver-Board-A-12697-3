"""Modern vs cost-optimised SPICE results side by side (reads both RESULTS.md files)."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'wpc_power_driver_modern', 'output', 'spice', 'RESULTS.md'))
MOD = os.path.abspath(os.path.join(HERE, '..', '..', 'output', 'spice', 'RESULTS.md'))
def load(p):
    vals = {}; deck = None
    for l in open(p):
        m = re.match(r'## (\w+)', l)
        if m: deck = m.group(1); continue
        m = re.match(r'\| (.*?) \(`(\w+)`\) \| ([-\d.e+na/]+) \|', l)
        if m and deck: vals[(deck, m.group(2))] = (m.group(3), m.group(1))
    return vals
o, m = load(ORIG), load(MOD)
ROWS = [  # (deck, key, label, unit, note)
    ('psu', 'v5_min', '+5V minimum under full load', 'V', 'modern: 5 A TPS54560B / cost: 3 A TPS54360B'),
    ('psu', 'vin5_min', '+5V buck input minimum (headroom, buck needs ~5.6 V)', 'V', '15000 uF / 5 A -> 10000 uF / 3 A, GBU8J instead of GBPC3510'),
    ('psu', 'v12_min', '+12V digital minimum (buck from the +18V lamp rail, 2.8 A of lamps)', 'V', 'both boards now feed U21 from +18V as the original 7812 does (the +20V rail is cut by the coin-door interlock); the modern board was corrected 2026-09-06'),
    ('psu', 'v20_min', '+20V minimum during the flasher burst', 'V', '15000 uF -> 10000 uF, GBJ1510 instead of GBPC3510'),
    ('psu', 'v18_avg', '+18V lamp rail average (5 ohm load)', 'V', '2 x 15000 uF -> 2 x 10000 uF, GBJ1510'),
    ('psu', 'v18_ripple', '+18V ripple p-p', 'V', ''),
    ('psu', 'v50_idle', '"+50V" rail idle', 'V', 'both suites use the real 51.4 VAC winding (~70 V)'),
    ('psu', 'v50_avg_pulse', '+50V average during a coil pulse', 'V', 'modern: 4 ohm coil, 0.35 R + 0.5 mH winding model; cost: AE-23-800 (4.2 ohm), 0.6 R winding model'),
    ('psu', 'v50_min_pulse', '+50V minimum during the pulse', 'V', ''),
    ('psu', 'icoil_max', 'peak 4-ohm coil current in the PSU sim', 'A', ''),
    ('sol_high', 'vout_on', 'high-power driver drop while ON', 'V', 'IRLB4030 4.3 mOhm -> IRLR3110Z (18 mOhm modelled at 4.6 V), both on the 70 V rail'),
    ('sol_high', 'p_fet', 'high-power driver dissipation while ON', 'W', 'TO-220 -> DPAK; pulsed duty keeps the average low'),
    ('sol_high', 'icoil_max', 'high-power coil current', 'A', 'modern: 4 ohm; cost: AE-23-800 4.2 ohm; both on 70 V'),
    ('sol_low', 'vce_on', 'low-power driver drop while ON', 'V', ''),
    ('sol_low', 'p_fet', 'low-power driver dissipation while ON', 'W', ''),
    ('sol_low', 'i_latch', 'current the latch must sink/source per output', 'A', 'unchanged (MOSFET gate)'),
    ('flasher', 'vsat', 'flasher driver drop', 'V', ''),
    ('lamp_matrix', 'vcol_drop', 'lamp column driver drop', 'V', 'IRF9Z34N 100 mOhm -> IRFR5305 65 mOhm (better)'),
    ('lamp_matrix', 'vrow_on', 'lamp row driver drop incl. 0.22 R sense', 'V', 'IRLZ44N 22 mOhm -> IRLR024N 65-80 mOhm'),
    ('lamp_matrix', 'vgs_col', 'column MOSFET Vgs', 'V', 'same 1k/1.5k divider'),
    ('lamp_matrix_trip', 't_trip', 'row over-current shutdown time', 's', ''),
    ('lamp_matrix_trip', 'irow_fault', 'row fault current before shutdown', 'A', 'higher Rds(on) limits the fault current a little'),
    ('lamp_matrix_trip', 'irow_after', 'row current after shutdown', 'A', ''),
    ('gi_gate', 'ig_peak', 'triac gate current', 'A', 'unchanged'),
    ('zero_cross', 'zc_period', 'ZERO CROSS period', 's', 'both boards: 60 Hz square wave with one edge per crossing (A-12697 U6A pin 7 = D38 sample); the cost board earlier produced a 120 Hz pulse, corrected 2026-09-06'),
    ('zero_cross', 'zc_high_time', 'ZERO CROSS time HIGH per cycle', 's', 'real TP4: ~8.1 ms (Pinside Arduino measurement)'),
    ('zero_cross', 'zc_rise_offset', 'ZC edge delay after the true crossing', 's', 'modern: two half-wave detectors, 27k feedback; cost: one half-wave sample, no feedback'),
    ('buck_5v', 'vout_ripple', '+5V buck output ripple (switching model)', 'V', 'TPS54560B 17 A/V -> TPS54360B 12 A/V, recomputed compensation'),
    ('buck_5v', 'vout_step_min', '+5V buck undershoot on a load step', 'V', 'modern: 1 -> 5 A step; cost: 1 -> 3 A step'),
    ('buck_5v', 'il_peak', '+5V buck peak inductor current at full load', 'A', 'cost: must stay below the 4.5 A minimum current limit'),
    ('buck_12v', 'vout_step_min', '+12V buck undershoot on a 1 -> 2 A step', 'V', 'cost: from 13.5 V (+18V rail at full lamp load)'),
    ('powerup', 'icoil_blank', 'coil current while BLANKING is high at power-up', 'A', 'cost-board machine-level deck'),
    ('lamp_strobe', 'vlamp_rms', 'RMS lamp voltage with 2 ms strobes', 'V', 'cost-board machine-level deck (original Darlington board: 5.53 V)'),
    ('gi_dimming', 'l7p_rms', 'G.I. string RMS at level 7 (8 us gate pulse) - modern deck', 'A', 'the cost deck gi_dim now runs the same machine-level model with its own detector (l7p_rms below)'),
    ('gi_dim', 'l7p_rms', 'G.I. string RMS at level 7 (8 us gate pulse) - cost deck', 'A', ''),
    ('gi_gate', 'p_triac', 'triac conduction loss at a full 18-lamp string', 'W', 'same BTA16-600C; the specified 25 C/W clip heatsink fails the Tj check on both boards (tj_rise_clip)'),
    ('gi_string', 'i2t_f106', 'G.I. string cold-start I2t through F106', 'A2s', 'modern: 313 5 A (140 A2s); cost: 239 5 A (302.8 A2s)'),
    ('inrush', 'i2t_f112', 'switch-on I2t through F112 (+50V, 4400 uF)', 'A2s', 'modern: 313 7 A (347 A2s) at 78 V peak; cost: 239 7 A (stand-in 347 A2s) at 72.7 V peak'),
    ('inrush', 'i2t_f114', 'switch-on I2t through the fast 8 A F114', 'A2s', 'modern: 312 8 A (166 A2s, 2 x 15000 uF); cost: 217 8 A (198 A2s, 2 x 10000 uF)'),
    ('ribbon', 't_setup', 'data setup at the latch before the strobe edge', 's', 'modern: 74HCT564 direct; cost: through the 25 ns 74HCT240'),
    ('ribbon', 't_hold', 'data hold after the strobe edge', 's', 'cost: the 74HCT240 delay and the 4.7 k ribbon pull-up lengthen it'),
    ('psu', 'v12u_min', '+12V power (J116/J117/J118) minimum at 2.5 A', 'V', 'modern: C30 15000 uF; cost: 10000 uF - both GBU8J, both the OEM topology now'),
]
lines = ['# Modern vs cost-optimised board - SPICE comparison', '', '| quantity | modern board | cost board | note |', '|---|---|---|---|']
for deck, key, label, unit, note in ROWS:
    ov = o.get((deck, key), ('n/a', ''))[0]; mv = m.get((deck, key), ('n/a', ''))[0]
    lines.append(f'| {label} | {ov} {unit if ov != "n/a" else ""} | {mv} {unit if mv != "n/a" else ""} | {note} |')
lines += ['', 'Both suites: ngspice transient runs, generic functional models (see each project\'s `tools/spice/`).  Modern results: '
          f'`{os.path.relpath(ORIG, os.path.join(HERE, "..", ".."))}`; cost board: `output/spice/RESULTS.md`.']
out = os.path.join(HERE, '..', '..', 'output', 'spice', 'COMPARISON.md')
open(out, 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
