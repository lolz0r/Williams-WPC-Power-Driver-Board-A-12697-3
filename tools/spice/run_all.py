"""Run all SPICE verification decks through native libngspice and summarize measurements.
Usage: python3 tools/spice/run_all.py --output output/verification/revision/spice"""
import os, sys, json, glob, argparse, tempfile, shutil, re, hashlib
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ngspice_lib import NgSpice
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', 'output', 'spice'))
os.makedirs(OUT, exist_ok=True)
CHECKS = {  # deck -> list of (measurement, lo, hi, description)   [cost board in the STTNG machine: real "+50V" = ~70 V (51 VAC winding), real strobe timing, real +12 V topology]
    'sol_low': [('icoil_max', 5.5, 7.5, 'AE-26-1200 (10.8 ohm) coil current on the 70 V rail (A)'),
                ('vce_on', 0.0, 0.25, 'IPD90N10S4L06 drain voltage during conduction at 4.6 V command; approximate hot-resistance fit, 8.1 mOhm maximum specified at 4.5 V and 25 C.'),
                ('vcol_peak', 68.0, 80.0, 'Drain voltage clamped by S3M tie-back in this 70 V case; separate high-line and parasitic checks are required.'),
                ('i_latch', -0.001, 0.001, 'steady current drawn from the 74HCT574 output (A)'),
                ('icoil_off', -0.01, 0.05, 'coil current 15 ms after turn-off (A)'),
                ('p_fet', 0.0, 1.5, 'MOSFET conduction loss during the commanded pulse, using the approximate hot-resistance fit.')],
    'sol_high': [('icoil_max', 14.0, 18.5, 'AE-23-800 (4.2 ohm, 12 mH) coil current on the 70 V rail (A): 70 / 4.2 = 16.7 A'),
                 ('vout_on', 0.0, 0.45, 'IPD90N10S4L06 drain voltage during conduction; approximate hot-resistance fit.'),
                 ('vout_peak', 68.0, 80.0, 'output clamped by the S3M tie-back diode (V)'),
                 ('p_fet', 0.0, 7.5, 'MOSFET conduction loss during the commanded pulse, using the approximate hot-resistance fit.'),
                 ('e_pulse', 0.0, 0.3, 'energy dissipated in the MOSFET per 40 ms pulse (J)'),
                 ('tj_rise_pulse', 0.0, 6.0, 'Illustrative single-pulse rise from energy and assumed 0.6 C/W transient impedance; not package/board thermal qualification.'),
                 ('tj_rise_10pct', 0.0, 75.0, 'Junction rise at 10% repeating duty using 62 C/W minimum-footprint datasheet RthJA; 125 C target at 50 C local ambient.'),
                 ('tj_rise_20pct', 0.0, 75.0, 'Junction rise at 20% repeating duty using 62 C/W minimum-footprint datasheet RthJA; 125 C target at 50 C local ambient.'),
                 ('tj_rise_20pct_pour', 0.0, 75.0, 'Sensitivity only: same 20% duty at an assumed 60 C/W. No claim that this layout achieves that resistance.')],
    'sol_hold': [('ia_hold', 4.0, 5.5, '100 % hold of a 14.5 ohm coil on 70 V (A)'),
                 ('pa_hold', 0.0, 0.8, 'MOSFET conduction loss during continuous hold using the approximate hot-resistance fit.'),
                 ('vds_hold', 0.0, 0.15, 'Vds during the hold (V)'),
                 ('tj_rise_hold', 0.0, 75.0, 'Continuous-hold junction rise using 62 C/W minimum-footprint datasheet RthJA; excludes neighboring heat.'),
                 ('ib_avg', 2.5, 4.0, 'average current of an AE-26-1200 PWM-held at 50 % (FreeWPC SOL_DUTY_50: 4 ms on / 4 ms off) (A)'),
                 ('ib_max', 4.0, 7.0, 'peak coil current during the PWM hold (A)'), ('ib_min', 0.3, 3.0, 'coil current stays continuous through the 4 ms off slot (A)'),
                 ('pb_avg', 0.0, 0.8, 'MOSFET dissipation during the PWM hold (W): conduction + the 125 Hz switching is negligible'),
                 ('tj_rise_pwm', 0.0, 75.0, 'PWM-hold junction rise using 62 C/W minimum-footprint datasheet RthJA; excludes neighboring heat.'),
                 ('idb_avg', 0.0, 2.0, 'average freewheel current in the S3M tie-back (A): S3M IF(AV) = 3 A (this is why the coil groups got S3M instead of S1M)'),
                 ('idb_max', 0.0, 30.0, 'peak diode current (A): S3M IFSM 100 A')],
    'flasher': [('ilamp_inrush', 3.0, 8.0, 'cold-lamp inrush (A)'), ('ilamp_hot', 0.7, 1.4, 'hot lamp current (A)'), ('vsat', 0.0, 0.1, 'IPD90N10S4L06 drain voltage with hot filament load.')],
    'lamp_matrix': [('irow_normal', 0.3, 3.5, 'row current, normal lamp incl. cold inrush (A)'), ('vsense_normal', 0.0, 1.3, 'sense voltage stays below the 1.4 V trip (V)'),
                    ('vref', 1.2, 1.6, '1.4 V reference (V)'), ('vcol_drop', 0.0, 0.3, 'column IRFR5305 drop with one lamp on (V): ~2 A x 65 mOhm = 0.13 V; 0.3 V = 150 mOhm (hot, low Vgs)'),
                    ('vrow_on', 0.0, 0.8, 'row driver drop incl. the 0.22 R sense resistor (V): 2 A x (0.22 + 0.08) = 0.6 V; 0.8 V keeps > 17 V on the 18 V lamp string'),
                    ('clr_min', 3.0, 5.5, 'comparator never clears the row flip-flop in normal operation (V)'),
                    ('vgs_col', -13.0, -7.0, 'column MOSFET Vgs from the 1k/1.5k divider (V): IRFR5305 needs <= -7 V for its rated 65 mOhm')],
    'lamp_matrix_trip': [('irow_fault', 6.4, 80.0, 'shorted lamp: row current exceeds the 6.4 A trip (A)'),
                    ('t_trip', 0.0330, 0.0332, 'row flip-flop cleared (s): short applied at 32.5 ms, column strobe (fault current) starts at 33.0 ms -> cleared within 0.2 ms'),
                    ('irow_after', 0.0, 0.5, 'row current after shutdown until the next strobe (A)'), ('irow_next', 2.0, 80.0, 'fault current returns at the next strobe and trips again (A) - per-strobe shutdown as in the original')],
    'lamp_strobe': [('icol_peak', 4.0, 12.0, 'column IRFR5305 current at the start of a 2 ms strobe with 8 warm #555 lamps (A): ~1 A per lamp, 0.7 A once hot'),
                    ('icol_avg', 0.4, 1.0, 'average column current over the 16 ms frame (A): x 8 columns = the ~5 A +18V load with every lamp lit'),
                    ('vcol_drop', 0.0, 0.8, 'column MOSFET drop at the 8 A strobe peak (V): 65-100 mOhm'),
                    ('pcol_avg', 0.0, 0.6, 'average column MOSFET dissipation, all 8 lamps lit (W): 2 ms of 8 A every 16 ms'),
                    ('tj_rise_col', 0.0, 75.0, 'column DPAK junction rise (C): P x 110 C/W (IRFR5305 datasheet minimum footprint; the as-routed drain copper is the tab pad only)'),
                    ('irow_peak', 0.5, 2.5, 'row IRLR024N current: one warm lamp per strobe (A)'), ('irow_avg', 0.2, 1.0, 'average row current with all 8 lamps of the row lit (A)'),
                    ('prow_avg', 0.0, 0.3, 'row MOSFET average dissipation (W)'), ('tj_rise_row', 0.0, 75.0, 'row DPAK junction rise (C): P x 110 C/W (IRLR024N minimum footprint, as routed)'),
                    ('vsense_max', 0.0, 1.2, 'sense voltage over 400 ms of strobing incl. the cold first strobes (V): stays below the 1.4 V trip'),
                    ('clr_min', 3.0, 5.5, 'no false over-current trip during normal strobing (V)'),
                    ('ilamp_first', 1.5, 3.5, 'cold-filament current at the very first strobe (A): 7 ohm filament on 18 V'),
                    ('vlamp_rms', 5.5, 6.6, 'RMS voltage across a #555 lamp over the 16 ms frame (V): rated 6.3 V; the MOSFET drops are 0.5 V instead of the 2.2 V of the 1993 Darlingtons, so the lamps run at ~98 % of their rating (brighter, about 3x shorter life than on the original board - irrelevant for LEDs)'),
                    ('vlamp_old_rms', 5.0, 6.0, 'the same lamp behind the original TIP107/TIP102 drops (V) - reference for the comparison')],
    'gi_dim': [('zc_period', 0.0163, 0.0170, 'ZERO CROSS period from the board detector inside this deck (s)'), ('zc_rise_offset', 0.0, 0.001, 'ZC rising edge after the true crossing (s)'), ('zc_fall_offset', -0.001, 0.0, 'ZC falling edge before the true crossing (s)'),
               ('ig_pk', 0.06, 0.13, 'triac gate current (A) - above the 50 mA quadrant-IV Igt of the BTA16-600C'),
               ('l0_max', 5.0, 8.0, 'level 0 (full): positive half-cycle peak string current (A)'), ('l0_min', -8.0, -5.0, 'level 0: negative half-cycle peak (A) - fires in both half-cycles'),
               ('l0_asym', 0.0, 0.02, 'level 0: |average| / rms of the string current - symmetric, no transformer DC'),
               ('l3h_max', 5.0, 8.0, 'level 3, gate held to the next ZC edge: positive peak (A)'), ('l3h_min', -8.0, -5.0, 'level 3 held: negative peak (A) - both half-cycles fire'),
               ('l3h_asym', 0.0, 0.25, 'level 3 held: |avg|/rms - asymmetry from the +/-0.3 ms edge offsets of the detector (same behaviour as the original board)'),
               ('l3p_max', 5.0, 8.0, 'level 3, 8 us gate pulse (FreeWPC style): positive peak (A)'), ('l3p_min', -8.0, -5.0, 'level 3 pulsed: negative peak (A) - the 50 mA-gate BTA16-600C latches on a few-us pulse in both quadrants'),
               ('l7h_max', 1.0, 8.0, 'level 7 (dimmest) with the bit HELD until the next ZC edge: positive peak (A) - informational: because the ZC edge comes after the crossing, a held gate re-fires the triac at the crossing and that half-cycle runs at full brightness; the firmware must pulse the bit or clear it before the crossing, exactly as with the original detector'),
               ('l7h_min', -8.0, -1.0, 'level 7 held: negative peak (A)'),
               ('l7p_max', 1.0, 8.0, 'level 7 pulsed: positive peak (A)'), ('l7p_min', -8.0, -1.0, 'level 7 pulsed: negative peak (A)'),
               ('l7p_rms', 0.3, 1.5, 'level 7 pulsed: string rms current (A) - dimmest level'), ('l0_rms', 4.0, 5.5, 'level 0: string rms current (A) - full (18 x #44 = 4.5 A)')],
    'zero_cross': [('zc_high', 4.5, 5.1, 'ZERO CROSS high level (V) - 1.5 k pull-up, no divider'), ('zc_low', 0.0, 0.5, 'ZERO CROSS low level (V)'),
                   ('za_min', -0.35, 0.3, 'sample node minimum (V, must stay > -0.3 V for the LM339): the fused leg sits at about -1 V while the other leg conducts, divided by 10k/1.5k'),
                   ('zc_period', 0.0163, 0.0170, 'ZERO CROSS period (s) - 60 Hz square wave as on the A-12697 (sheet 1: D38 sample on U6A pin 7 (+), reference on pin 6 (-); a real TP4 measures ~8.1 ms high pulses at 60 Hz - Pinside, Arduino pulse timer), one edge per mains zero crossing; the earlier 120 Hz active-high pulse of this board was wrong'),
                   ('zc_high_time', 0.0065, 0.0085, 'time HIGH per cycle (s) - 8.33 ms minus twice the threshold delay (~2 V on the leg); the OEM detector gives the same shape'),
                   ('zc_rise_offset', 0.0, 0.001, 'rising edge after the true zero crossing (s)'), ('zc_fall_offset', -0.001, 0.0, 'falling edge before the true zero crossing (s)'),
                   ('zc_rise_time', 0.0, 0.0003, '10-90 % rise time of the edge (s) - no hysteresis feedback here, the comparator switches cleanly; the ASIC squares it anyway'),
                   ('i_r197_pk', 0.0, 0.005, 'peak current into the 10 k sample resistor (A) - 0805 1/8 W is fine')],
    'psu': [('v18_avg', 13.0, 20.0, '+18V lamp rail average at 2.8 A / 5 ohm plus the 1 A +12V digital buck (V): the lamp matrix needs >= 13 V for full brightness'),
            ('v18_ripple', 0.0, 3.0, '+18V ripple p-p with 2 x 10000 uF (V): 3 V = 20 % of the rail, the largest brightness flicker acceptable at 120 Hz'),
            ('vin5_min', 6.5, 14.0, '+5V buck input minimum at 3 A output with 10000 uF (V): TPS54360B needs 5.6 V for 5 V out, the 6.0 V UVLO start + 0.5 V'),
            ('vin5_ripple', 0.0, 3.5, '+5V raw ripple p-p (V)'), ('v5_min', 5.05, 5.15, '+5V minimum at 3 A load (V): set point 5.10 V (11.3 k / 2.1 k, 0.1 %) since the 2026-09-07 review'),
            ('v5_cpu_worst', 4.70, 5.2, '+5V at the CPU board with 3 A through 80 mOhm of board copper + harness (V): must stay above the 4.70 V maximum MC34064 reset threshold (with 5.00 V and 1 % feedback parts the worst case was 4.61 V)'),
            ('v50_idle', 66.0, 74.0, '"+50V" idle (V): 51.4 VAC nominal winding -> 72.7 V peak minus two diode drops; pinwiki: TP6 measures 70-75 V'),
            ('v50_max', 66.0, 80.0, '"+50V" maximum at idle (V): the STTNG transformer measured 55.2 VAC unloaded = 78 V peak (83 V at +6 % line); 100 V capacitors and 100 V MOSFETs keep >= 17 V'),
            ('v50_avg_pulse', 35.0, 60.0, '"+50V" average during a 40 ms AE-23-800 pulse with 4400 uF (V): the original 100 uF board fell to the rectified sine'),
            ('v50_min_pulse', 28.0, 60.0, '"+50V" minimum during the pulse (V)'), ('icoil_max', 11.0, 18.0, 'peak AE-23-800 coil current with the sagging rail (A)'),
            ('v20_min', 13.0, 24.0, '+20V minimum during a 4 A flasher burst with 10000 uF (V): flashers only on this rail now'),
            ('v20_ripple', 0.0, 3.0, '+20V ripple p-p during the burst (V)'),
            ('v12_min', 11.95, 12.05, '+12V digital minimum, buck fed from the +18V lamp rail at 2.8 A of lamps (V)'), ('v12_max', 11.95, 12.05, '+12V digital maximum (V)')],
    'psu_maxload': [('v18_min', 10.0, 20.0, '+18V minimum with all 64 lamps lit (2.5 ohm, ~5 A) plus the +12V digital buck, 2 x 10000 uF (V): lamps stay usable above ~10 V'),
                    ('vin5_min', 6.0, 14.0, '+5V buck input minimum with everything on (V): converter needs 5.6 V, worst-case UVLO stop 6.0 V'),
                    ('v5_min', 5.05, 5.15, '+5V minimum at 3 A with everything on (V): 5.10 V set point'),
                    ('v20_min', 9.0, 24.0, '+20V minimum during the 8-flasher cold inrush with 10000 uF (V): only flashers hang on this rail (interlocked with the coin door)'),
                    ('iflash_peak', 20.0, 60.0, 'combined cold inrush of 8 flashers (A) - within the F111 5 A slow-blow 40 ms envelope'),
                    ('v12_min', 10.5, 12.05, '+12V digital minimum with all lamps lit (V): the buck droops (0.97 Vin - 0.5) while +18V sags to 11.9 V; the original 7812 (needs 14 V in) dropped to ~10 V in the same case; the CPU switch matrix (LM339 + 1 k pull-ups) works far below that'),
                    ('v12u_min', 10.0, 16.0, '+12V power (unregulated) minimum with 2.5 A of gun motors / optos / DMD / coin door on 10000 uF (V): pinwiki reports jittery optos around 10 V; a 15000 uF C30 (OEM) would add ~0.4 V'),
                    ('v50_avg_pulse', 15.0, 60.0, '"+50V" average with 2 AE-23-800 + 4 AE-26-1200 fired together (V) - informational, an unrealistic firmware case bounding the rail'),
                    ('itot50_max', 25.0, 45.0, 'total coil current, six coils at once (A)'),
                    ('ibr50_peak', 0.0, 400.0, 'peak current through the +50V bridge (A): GBPC3510 surge rating 400 A (this is a single 40 ms event)'),
                    ('ibr18_peak', 0.0, 60.0, 'repetitive peak current in the +18V GBJ1510 with all lamps lit (A): capacitor-input rectifiers run at 3-5 x Io, limit 4 x the 15 A rating; surge rating 240 A'),
                    ('ibr20_peak', 0.0, 60.0, 'peak current in the +20V GBJ1510 during the flasher inrush (A): 4 x the 15 A rating for the repetitive part; the 240 A surge rating covers the first cycles'),
                    ('ibr5_peak', 0.0, 32.0, 'repetitive peak current in the +5V-raw GBU8J at 3 A output (A): 4 x the 8 A rating; surge rating 200 A'),
                    ('ibr12_peak', 0.0, 32.0, 'repetitive peak current in the +12V-power GBU8J (BR5) at 2.5 A (A): 4 x the 8 A rating')],
    'psu_brownout': [('vraw_min', 6.0, 12.0, '+5V buck input minimum at 88 % mains and the rated 3 A (V): must stay above the UVLO stop level - 5.5 V nominal, 6.0 V worst case (Vena 1.3 V) - so the converter keeps regulating (sweep: output/spice/uvlo_sweep.md)'),
                     ('v5_min', 5.05, 5.15, '+5V holds through an 88 % brownout at 3 A (V) - the CPU reset chip (MC34064, 4.6 V) never trips; 5.10 V set point'),
                     ('v18_min', 9.5, 16.0, '+18V minimum at 88 % mains with all lamps lit (V)'),
                     ('v12_min', 9.0, 12.05, '+12V digital at 88 % mains with all lamps lit (V): droops with the +18V rail; 9 V still runs the CPU switch-matrix comparators; the original 7812 would have delivered ~7 V here'),
                     ('v12u_min', 8.5, 16.0, '+12V power at 88 % mains with 2.5 A of motors / optos (V)')],
    'psu_12vu': [('v12u_min', 10.0, 16.0, '+12V power minimum at 2.5 A, measured STTNG winding (12.47 VAC unloaded, 0.25 ohm/leg) (V)'),
                 ('v12u_avg', 10.5, 16.0, '+12V power average at 2.5 A (V)'), ('v12u_ripple', 0.0, 2.0, 'ripple p-p at 2.5 A with 10000 uF (V)'),
                 ('ibr5_peak', 0.0, 32.0, 'BR5 GBU8J repetitive peak current (A): 4 x 8 A'), ('ibr5_rms', 0.0, 8.0, 'BR5 RMS current (A): GBU8J average rating 8 A'),
                 ('v12u_max_unloaded', 0.0, 20.0, 'maximum +12V power with only the LED load (V): C30 is a 25 V part - 20 V keeps 20 % margin (unloaded winding 17.6 V peak)'),
                 ('v12u_min_nominal', 8.5, 16.0, 'pessimistic bound: the manual\'s nominal 9.8 VAC winding at 2.5 A (V) - the real transformer is ~2 V higher')],
    'buck_5v': [('vout_ss', 5.0, 5.2, 'steady-state output at 1 A (V): 5.10 V set point (11.3 k / 2.1 k, Vref 0.8 V)'), ('vout_ripple', 0.0, 0.08, 'output ripple p-p at 1 A (V)'),
                ('vout_step_min', 4.75, 5.2, 'undershoot on a 1 -> 3 A load step (V): with the 5.10 V set point the dip stays >= 4.75 V at the board, i.e. > 4.70 V (MC34064 maximum threshold) at the CPU even through 80 mOhm... see docs/THERMAL_AND_PROTECTION.md section 9'),
                ('vout_step_max', 5.0, 5.5, 'overshoot on the 3 -> 1 A step (V): stays below the 5.20 V no-load maximum at the connector'),
                ('il_peak', 3.0, 4.3, 'peak inductor current at 3 A (A): must stay below the 4.5 A minimum current limit of the TPS54360B (SRP1265A-100M rated 10 A)'),
                ('vout_3a', 5.0, 5.2, 'output at 3 A (V)'), ('iin_3a', -3.0, -1.5, 'input current at 3 A out from 8 V (A, negative = drawn from Vin)')],
    'buck_12v': [('vout_ss', 11.8, 12.2, 'steady-state output at 1 A from the +18V rail at 13.5 V (V)'), ('vout_ripple', 0.0, 0.1, 'output ripple p-p at 1 A (V)'),
                 ('vout_step_min', 11.4, 12.2, 'undershoot on a 1 -> 2 A load step (V): the real load behind F115 is <= 0.75 A; 11.4 V keeps the switch matrix / CPU +12V loads happy'),
                 ('vout_step_max', 11.8, 12.6, 'overshoot on the 2 -> 1 A step (V)'),
                 ('il_peak', 2.0, 4.3, 'peak inductor current at 2 A from 13.5 V (A): below the 4.5 A minimum current limit'),
                 ('vout_2a', 11.8, 12.2, 'output at 2 A (V)'), ('iin_2a', -2.6, -1.0, 'input current at 2 A out from 13.5 V (A)')],
    'powerup': [('icoil_blank', 0.0, 0.01, 'coil current while BLANKING is high (reset, +5V ramp, undefined latch content = 1) (A): the tri-stated 74HCT574 and the 10 k gate pull-down keep the IPD90N10S4L06 off'),
                ('istr_blank', 0.0, 0.05, 'G.I. string current while blanked (A): 10 k base pull-down keeps the MMBT4401 / triac off'),
                ('icol_blank', 0.0, 0.01, 'lamp column current while blanked with a row MOSFET randomly ON (A): the TBD62083A input pull-down keeps the column P-MOSFET off'),
                ('vgate_blank', 0.0, 0.5, 'solenoid gate voltage while blanked (V)'),
                ('blank_min', 4.0, 5.5, 'BLANKING never drops below 4 V while the CPU holds reset (V): SR1 pulls it up, the CPU 2N3904 is off'),
                ('icoil_on', 10.0, 20.0, 'coil current after the CPU releases BLANKING with the latch holding 1 (A): the path works'),
                ('istr_on', 4.0, 8.0, 'G.I. string current after release (A peak)'), ('icol_on', 3.0, 8.0, 'lamp column current after release (A)'),
                ('icoil_after', 0.0, 0.01, 'coil current after the CPU writes 0 (A)'), ('icol_after', 0.0, 0.01, 'column current after the CPU writes 0 (A)')],
    'gi_gate': [('ig_peak', 0.06, 0.13, 'triac gate current (A) - above the 50 mA worst-case Q IV Igt of the BTA16-600C'), ('istr_off', 0.0, 0.05, 'string current before trigger (A)'),
                ('istr_on', 4.0, 8.0, 'string current while enabled (A peak)'), ('istr_rms', 3.0, 5.0, 'string rms current while enabled (A) - 18 x #44 on 6.3 VAC, F106 is 5 A S.B.'),
                ('istr_after', 0.0, 0.3, 'string current after latch released (A)'),
                ('p_npn', 0.0, 0.25, 'MMBT4401 dissipation (W, SOT-23 limit 0.31 W)'), ('i_latch', -0.004, -0.0001, 'base current sourced by the 74HCT574 (A, negative = out of the latch)'),
                ('p_triac', 0.0, 5.0, 'BTA16-600C conduction loss with the datasheet on-state (Vt0 0.85 V, Rd 25 mOhm) at this string current (W) - the datasheet gives <= 5 W at 4.5 A rms'),
                ('tj_rise_sink', 0.0, 75.0, 'junction rise above ambient with the Boyd 7020BG bolt-on channel heatsink (8.7 C/W catalogue value at a 75 C rise, x1.25 for the ~50 C rise here) + Rth(j-c) 2.5 (BTA16 insulated TO-220) + 0.5 C/W interface = 13.875 C/W (C): limit Tj <= 125 C in a 50 C cabinet. The 7020BG (33.02 x 11.94 x 36.83 mm, M3 bolt-on, no PCB holes) fits all five triac positions on the tab side (docs/THERMAL_AND_PROTECTION.md section 2)'),
                ('tj_rise_clip', 0.0, 200.0, 'informational: the rise the previously specified Aavid 577002B00000G clip-on would give - it is a 32 C/W part per the Boyd catalogue (35 C/W junction-to-ambient), i.e. Tj ~165 C with an incandescent string; replaced by the 7020BG (C)'),
                ('rth_sa_needed', 0.0, 100.0, 'maximum sink-to-ambient thermal resistance that keeps Tj <= 125 C at 50 C ambient with this string (C/W) - informational, compare with the 10.875 C/W of the 7020BG in this cabinet')],
    'gi_string': [('ipk', 0.0, 160.0, 'cold-start peak current of an 18 x #44 string fired at the voltage peak (A) - BTA16-600C ITSM 160 A (8.3 ms)'),
                  ('i2t_f106', 0.0, 60.0, 'I2t through F106 (239 5 A S.B., 302.8 A2s nominal melting) during the whole cold start (A2s): <= 20 %, and far below the BTA16 I2t of 128 A2s'),
                  ('i2t_30ms', 0.0, 60.0, 'I2t in the first 30 ms (A2s) - the part the fuse sees as a surge'),
                  ('irms_ss', 3.5, 5.0, 'steady string rms current (A) - 18 x #44 = 4.5 A on the 5 A slow-blow F106 (rated to carry 110 % continuously)'),
                  ('p_triac', 0.0, 5.0, 'steady triac dissipation with the datasheet on-state (W) - see gi_gate for the heatsink requirement'),
                  ('istr_pre', 0.0, 0.05, 'string current before the gate is driven (A)'),
                  ('tj_rise_sink', 0.0, 75.0, 'junction rise with the Boyd 7020BG heatsink at the steady 4.5 A rms string (C): P x 13.875 C/W (2.5 j-c + 0.5 interface + 10.875 sink) - the worst of the two G.I. decks; Tj <= 125 C at 50 C ambient')],
    'ribbon': [('g_w1', 4.0, 5.0, 'MOSFET gate after the CPU writes bit = 1 (V): 74LS240 drives the ribbon LOW, U9 74HCT240 re-inverts it, the 74HCT574 latches it on the strobe rising edge -> ON'),
               ('out_w1', 0.0, 1.0, 'drain voltage with the output ON (V)'),
               ('g_w0', 0.0, 0.3, 'gate after the CPU writes bit = 0 (ribbon HIGH) (V) - OFF'), ('out_w0', 60.0, 80.0, 'drain at the 70 V rail with the output OFF (V)'),
               ('g_w1b', 4.0, 5.0, 'gate after a second write of 1 (V) - ON again'),
               ('ioe_on', 1e-5, 0.2, 'current the 74HCT574 output drives into the gate network while enabled (A) - proves the output is active (charging Cgs through 100 R)'),
               ('ioe_unplug', 0.0, 1e-6, '74HCT574 output current with the ribbon unplugged (A): SR2 pulls the data HIGH (bit 0), SR1 holds the strobes HIGH (no clock) and BLANKING HIGH -> every latch tri-stated (/OE) - the 10 k pull-down then discharges the gate in ~150 us (powerup.cir)'),
               ('g_unplug', 0.0, 5.0, 'gate 10 us after the unplug (V) - informational: still decaying through the 10 k / Cgs (tau ~40 us), see powerup for the settled state'),
               ('blank_unplug', 4.0, 5.5, 'BLANKING level with the ribbon unplugged (V) - pulled to Vcc by SR1'),
               ('ioe_blank', 0.0, 1e-6, '74HCT574 output current while the CPU holds BLANKING high (reset / watchdog) with the latch holding 1 (A) - tri-stated, OFF'),
               ('g_blank', 0.0, 5.0, 'gate 10 us after BLANKING went high (V) - informational (see ioe_blank and powerup.cir)'),
               ('g_w0b', 0.0, 0.3, 'gate after the final write of 0 (V)'),
               ('rib_low', 0.0, 0.8, 'ribbon data line LOW level during the strobe with the 4.7 k pull-up sinking into the 74LS240 (V) - HCT VIL 0.8 V'),
               ('rib_high', 2.0, 5.5, 'ribbon data line HIGH level from the 74LS240 totem pole (V) - HCT VIH 2.0 V'),
               ('t_setup', 20e-9, 1e-6, 'data setup at the 74HCT574 D input (after the 25 ns 74HCT240) before the strobe rising edge (s): 6809E tDDQ 200 ns max after Q rise vs the strobe ending at E fall (375 ns); 74HCT574 tsu 20 ns at 4.5 V'),
               ('t_hold', 5e-9, 1e-6, 'data hold at the 74HCT574 after the strobe rising edge (s): 6809E tDHW 30 ns min plus the 74HCT240 delay and the 4.7 k / 120 pF ribbon rise (~0.5 us); 74HCT574 th 5 ns')],
    'bridge_loss': [('iavg_18a', 5.0, 8.0, 'BR1 +18V DC output current with all 64 lamps lit + the +12V digital buck at 0.75 A (A) - the everything-on case of psu_maxload'),
                    ('irms_18a', 5.0, 16.0, 'BR1 leg RMS current in that case (A): capacitor-input rectifier, crest factor ~1.6-2'),
                    ('pd_18a', 0.0, 5.0, 'per-diode loss of the +18V Schottky bridge (4 x STPS20M100S) with all lamps lit, datasheet equation 0.425 IF(AV) + 0.0088 IF(RMS)^2 (W) - the whole bridge is 4x this (was 15.2 W with the GBJ1510)'),
                    ('rthreq_18a', 25.0, 200.0, 'Conduction-only required thermal resistance for 110 C; informational legacy metric (C/W)'),
                    ('tj_18a', 0.0, 125.0, 'BR1 TO220 with individual Boyd 5772: 32.2 C/W including 25% sink derating, plus worst 70 V/125 C leakage at 20.69 V; target 125 C at 50 C ambient'),
                    ('tj_18b', 0.0, 125.0, 'BR1 TO220/sink junction estimate at 3 A DC, including leakage (C)'),
                    ('pd_18c', 0.0, 5.0, 'per-diode loss at the F114 rating 8 A DC (W) - informational: needs ~30 cm2 of 2 oz copper per diode for 110 C, i.e. the 8 A fuse limit is a short-term rating'),
                    ('tj_18c', 0.0, 150.0, 'BR1 fuse-rating load is informational only; not qualified for continuous operation (C)'),
                    ('tj_20a', 0.0, 110.0, 'BR4 +20V diode junction temperature at 2.5 A DC sustained on 4 cm2 of 2 oz copper per diode (36 C/W) (C)'),
                    ('tj_20b', 0.0, 150.0, 'BR4 diode junction temperature at the F111 rating 5 A DC on 4 cm2 (C): informational, limit = Tj max 150 C; 110 C needs ~10 cm2 per diode'),
                    ('tj_50a', 0.0, 125.0, 'BR3 +50V GBPC3510W junction temperature at 3.0 A DC sustained (a held 14.5 ohm coil half the time plus play; flippers are rectified on the Fliptronic board) with the Boyd 6223BG basket heatsink bolted on the (upward-facing) metal base: 1.4 j-c + 0.5 + 9.4 x 1.05 = 11.8 C/W (C)'),
                    ('pds_50b', 0.0, 60.0, 'BR3 dissipation at the F112 rating 7 A DC (W) - informational: sustained limit with the 6223BG is 3.4 A'),
                    ('tj_5a', 0.0, 110.0, 'BR2 +5V raw diode junction temperature with the +5V buck at its rated 3 A output (~1.9 A DC in) on 2 cm2 of 2 oz copper per diode (41 C/W) (C)'),
                    ('tj_5b', 0.0, 110.0, 'BR2 diode junction temperature at the estimated real +5V load 2.4 A (C)'),
                    ('tj_12a', 0.0, 110.0, 'BR5 +12V power diode junction temperature at 2.5 A DC sustained on 2 cm2 of 2 oz copper per diode (41 C/W) (C)'),
                    ('tj_12b', 0.0, 110.0, 'BR5 diode junction temperature at the F116 rating 3 A DC on 2 cm2 (C) - the 239 fuse carries 110 % for 4 h, so a sustained case'),
                    ('pmodel_18a', 0.0, 40.0, 'cross-check: whole-bridge dissipation of BR1 with all lamps lit from the SPICE model power balance (AC-side minus DC-side power) (W) - the model is fitted to the 25 C typical Vf and so runs above the 125 C datasheet equation'),
                    ('vdc_18a', 12.0, 20.0, '+18V rail average with all lamps lit and the Schottky bridge (V): was 12.6 V with the GBJ1510'),
                    ('irms_12a', 0.0, 8.0, 'BR5 leg RMS current at 2.5 A DC (A): each diode carries Irms/sqrt(2) = 2.8 A rms (IF(RMS) rating 30 A)')],
    'inrush': [('ipk_f113', 0.0, 60.0, 'peak inrush through F113 / BR2 (GBU8J, IFSM 200 A) into C5 at switch-on on the mains peak (A)'),
               ('i2t_f113', 0.0, 60.5, 'I2t through F113 in the first 250 ms (A2s): <= 20 % of the 302.836 A2s nominal melting I2t of the Littelfuse 239 5 A (239 datasheet / distributor specification, docs/THERMAL_AND_PROTECTION.md section 4) so the fuse never ages from switch-on'),
               ('ipk_f114', 0.0, 120.0, 'peak inrush through F114 / BR1 (GBJ1510, IFSM 240 A) into C6 + C7 (A)'),
               ('i2t_f114', 0.0, 39.6, 'I2t through the FAST 8 A F114 (A2s): <= 20 % of the 198.16 A2s of the Littelfuse 217 8 A (217 datasheet table, read directly)'),
               ('ipk_f111', 0.0, 120.0, 'peak inrush through F111 / BR4 (GBJ1510) into C11 (A)'),
               ('i2t_f111', 0.0, 60.5, 'I2t through F111 (239 5 A, 302.836 A2s) (A2s): <= 20 %'),
               ('ipk_f116', 0.0, 100.0, 'peak inrush through F116 / BR5 (GBU8J) into the 10000 uF C30 (A)'),
               ('i2t_f116', 0.0, 25.9, 'I2t through F116 (239 3 A) (A2s): <= 20 % of the real 239 3 A nominal melting I2t, 129.51 A2s (replaces the 313 3 A 200 A2s stand-in)'),
               ('ipk_f112', 0.0, 200.0, 'peak inrush through F112 / BR3 (GBPC3510, IFSM 400 A) into 2 x 2200 uF at 72.7 V peak (A)'),
               ('i2t_f112', 0.0, 69.4, 'I2t through F112 (239 7 A) (A2s): the 239 7 A row could not be retrieved (every host of the 239 datasheet blocks automated access; the 3 A / 5 A values 129.5 / 302.8 A2s extrapolate to ~530 A2s) - the limit stays at 20 % of the OEM 313 7 A (347 A2s), which is the more conservative reference'),
               ('v50_final', 66.0, 74.0, '"+50V" reached after 250 ms (V)'), ('v18_final', 14.0, 20.0, '+18V reached after 250 ms (V)')],
}

def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=OUT, help='Directory for fresh reports and waveforms')
    args = parser.parse_args()
    OUT = os.path.abspath(args.output)
    os.makedirs(OUT, exist_ok=True)
    Path(OUT, 'RESULTS.md').write_text('# SPICE verification\n\nINCOMPLETE: run in progress or interrupted.\n')
    ng = NgSpice()
    summary = []
    source_decks = sorted(glob.glob(os.path.join(HERE, 'decks', '*.cir')))
    names = {Path(p).stem for p in source_decks}
    if names != set(CHECKS):
        raise RuntimeError(f'Deck/check coverage mismatch: {names ^ set(CHECKS)}')
    # Stage unchanged electrical circuits with portable waveform destinations.
    # Keep the checked-in reference results and source decks intact.
    stage = tempfile.TemporaryDirectory(prefix='wpc-spice-')
    staged = Path(stage.name)
    shutil.copytree(Path(HERE) / 'decks', staged / 'decks')
    shutil.copyfile(Path(HERE) / 'models.lib', staged / 'models.lib')
    manifest = {}
    for original in source_decks + [os.path.join(HERE, 'models.lib'), __file__,
                                   os.path.join(os.path.dirname(__file__), 'ngspice_lib.py')]:
        manifest[os.path.relpath(original, HERE)] = hashlib.sha256(Path(original).read_bytes()).hexdigest()
    Path(OUT, 'inputs.json').write_text(json.dumps(manifest, indent=2) + '\n')
    for deck in sorted(glob.glob(str(staged / 'decks' / '*.cir'))):
        source = Path(deck).read_text()
        source = re.sub(r'(?m)^(\s*wrdata\s+)\S+',
                        lambda m: m[1] + Path(m[0].split()[-1]).name, source)
        Path(deck).write_text(source)
        name = os.path.basename(deck)[:-4]
        os.chdir(staged / 'decks')
        ng.cmd('destroy all')
        log = ng.run_deck(deck)
        Path(OUT, name + '.log').write_text('\n'.join(log) + '\n')
        for waveform in (staged / 'decks').glob('*.csv'):
            shutil.move(str(waveform), str(Path(OUT) / waveform.name))
        csv = os.path.join(OUT, name + '.csv')     # the 20 ns switching-model runs write > 100 MB: keep every 10th sample (measurements were taken on the full run)
        if os.path.exists(csv) and os.path.getsize(csv) > 20e6:
            rows = Path(csv).read_text().split('\n'); Path(csv).write_text('\n'.join(rows[::10]) + '\n')
        meas = {}
        errs = [l for l in log if 'stderr' in l and 'Warning' not in l]
        for l in log:
            if 'stdout' in l and '=' in l and ' at' not in l.split('=')[0] and 'Data Rows' not in l:
                parts = l.replace('stdout', '').strip().split('=')
                key = parts[0].strip()
                try: meas[key] = float(parts[1].split()[0])
                except Exception: pass
        for k in list(meas):
            if k.endswith('_rms_sq') and meas[k] >= 0: meas[k[:-3]] = meas[k] ** 0.5
        if 'zc_r1' in meas and 'zc_f1' in meas and 'tz1' in meas and 'tz2' in meas:
            meas['zc_high_time'] = meas['zc_f1'] - meas['zc_r1']
            meas['zc_rise_offset'] = meas['zc_r1'] - meas['tz1']
            meas['zc_fall_offset'] = meas['zc_f1'] - meas['tz2']
            if 'zc_r2' in meas: meas['zc_period'] = meas['zc_r2'] - meas['zc_r1']
            if 'zc_r1_10' in meas and 'zc_r1_90' in meas: meas['zc_rise_time'] = meas['zc_r1_90'] - meas['zc_r1_10']
        for nm in ('l0', 'l3h', 'l3p', 'l7h', 'l7p'):
            if nm + '_avg' in meas and nm + '_rms' in meas and meas[nm + '_rms'] > 0:
                meas[nm + '_asym'] = abs(meas[nm + '_avg']) / meas[nm + '_rms']
        results = []
        for m, lo, hi, desc in CHECKS.get(name, []):
            v = meas.get(m)
            ok = v is not None and lo <= v <= hi
            results.append((m, v, lo, hi, ok, desc))
        summary.append((name, results, errs[:5]))
        print(f'== {name}: ' + ', '.join(f'{k}={v:.4g}' for k, v in meas.items() if k != 'time'))
        for e in errs[:5]: print('   ERR', e[:160])
    lines = ['# SPICE verification results - cost-optimised board in the STTNG machine', '', 'ngspice shared-library transient runs of each circuit block; MOSFET/diode models in `tools/spice/models.lib` are level-1 fits to datasheet Rds(on)/Qg',
             '(functional fidelity, not vendor-exact); the TPS54360B is a behavioural peak-current-mode model (12 A/V, 4.5 A minimum current limit, 400 kHz). Machine-level decks use the real WPC',
             'interface: 51 VAC solenoid winding (~70 V rail), 2 ms lamp column strobes, IRQ-timed triac firing, PWM-held coils, the +12 V digital / +12 V power split, the zero-cross square wave,',
             'BLANKING as the CPU drives it at reset, and switch-on inrush against the Littelfuse 239/217 melting I2t (docs/WPC_INTERFACE_FINDINGS.md). Waveform CSVs are next to this file.',
             'Each limit is explained in its description column (see also README.md).', '']
    allok = True
    for name, results, errs in summary:
        allok &= bool(results) and not errs
        lines.append(f'## {name}'); lines.append('')
        lines.append('| measurement | value | expected | result |'); lines.append('|---|---|---|---|')
        for m, v, lo, hi, ok, desc in results:
            allok &= ok
            lines.append(f'| {desc} (`{m}`) | {"n/a" if v is None else f"{v:.4g}"} | {lo:g} … {hi:g} | {"PASS" if ok else "FAIL"} |')
        for e in errs: lines.append(f'* ngspice error: `{e.strip()[:160]}`')
        lines.append('')
    lines.append(f'**Overall: {"ALL CHECKS PASS" if allok else "SOME CHECKS FAILED"}**')
    Path(OUT, 'RESULTS.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    os.chdir(HERE)
    stage.cleanup()
    return 0 if allok else 1
if __name__ == '__main__':
    sys.exit(main())
