# SPICE verification results - cost-optimised board

ngspice (KiCad 10 bundled libngspice) transient runs of each circuit block; MOSFET/diode models in `tools/spice/models.lib` are level-1 fits to datasheet Rds(on)/Qg
(functional fidelity, not vendor-exact); the TPS54360B is a behavioural peak-current-mode model (12 A/V, 4.5 A minimum current limit, 400 kHz). Waveform CSVs are next to this file.
Each limit is explained in its description column (see also README.md).

## buck_12v

| measurement | value | expected | result |
|---|---|---|---|
| steady-state output at 1 A (V) (`vout_ss`) | 11.93 | 11.8 … 12.2 | PASS |
| output ripple p-p at 1 A (V) (`vout_ripple`) | 0.04351 | 0 … 0.1 | PASS |
| undershoot on a 1 -> 2 A load step (V): 11.4 V keeps the switch matrix / CPU +12V loads (LM7805 pre-regulators, opto emitters) happy (`vout_step_min`) | 11.82 | 11.4 … 12.2 | PASS |
| overshoot on the 2 -> 1 A step (V) (`vout_step_max`) | 12.03 | 11.8 … 12.6 | PASS |
| peak inductor current at 2 A from 15.7 V (A): below the 4.5 A minimum current limit (`il_peak`) | 3.282 | 2 … 4.3 | PASS |
| output at 2 A (V) (`vout_2a`) | 11.92 | 11.8 … 12.2 | PASS |
| input current at 2 A out from 15.7 V (A) (`iin_2a`) | -1.549 | -2.2 … -1 | PASS |

## buck_5v

| measurement | value | expected | result |
|---|---|---|---|
| steady-state output at 1 A (V) (`vout_ss`) | 5 | 4.9 … 5.1 | PASS |
| output ripple p-p at 1 A (V) (`vout_ripple`) | 0.02705 | 0 … 0.08 | PASS |
| undershoot on a 1 -> 3 A load step (V): 4.6 V is the 74HCT / CPU-board minimum with margin (`vout_step_min`) | 4.898 | 4.6 … 5.1 | PASS |
| overshoot on the 3 -> 1 A step (V) (`vout_step_max`) | 5.092 | 4.9 … 5.4 | PASS |
| peak inductor current at 3 A (A): must stay below the 4.5 A minimum current limit of the TPS54360B (SRP1265A-100M rated 10 A) (`il_peak`) | 3.65 | 3 … 4.3 | PASS |
| output at 3 A (V) (`vout_3a`) | 4.986 | 4.9 … 5.1 | PASS |
| input current at 3 A out from 8 V (A, negative = drawn from Vin) (`iin_3a`) | -2.026 | -3 … -1.5 | PASS |

## flasher

| measurement | value | expected | result |
|---|---|---|---|
| cold-lamp inrush (A) (`ilamp_inrush`) | 6.615 | 3 … 8 | PASS |
| hot lamp current (A) (`ilamp_hot`) | 1.111 | 0.7 … 1.4 | PASS |
| IRLR3110Z Vds with the lamp on (V): 1.1 A x 18 mOhm = 0.02 V (`vsat`) | 0.02035 | 0 … 0.1 | PASS |

## gi_gate

| measurement | value | expected | result |
|---|---|---|---|
| triac gate current (A) - above the 50 mA worst-case Q IV Igt of the BTA16-600C (`ig_peak`) | 0.07841 | 0.06 … 0.13 | PASS |
| string current before trigger (A) (`istr_off`) | 6.092e-06 | 0 … 0.05 | PASS |
| string current while enabled (A peak) (`istr_on`) | 6.138 | 4 … 8 | PASS |
| string current after latch released (A) (`istr_after`) | 8.9e-06 | 0 … 0.3 | PASS |
| MMBT4401 dissipation (W, SOT-23 limit 0.31 W) (`p_npn`) | 0.1245 | 0 … 0.25 | PASS |
| base current sourced by the 74HCT574 (A, negative = out of the latch) (`i_latch`) | -0.003665 | -0.004 … -0.0001 | PASS |

## lamp_matrix

| measurement | value | expected | result |
|---|---|---|---|
| row current, normal lamp incl. cold inrush (A) (`irow_normal`) | 2.438 | 0.3 … 3.5 | PASS |
| sense voltage stays below the 1.4 V trip (V) (`vsense_normal`) | 0.5026 | 0 … 1.3 | PASS |
| 1.4 V reference (V) (`vref`) | 1.29 | 1.2 … 1.6 | PASS |
| column IRFR5305 drop with the lamp on (V): ~2 A x 65 mOhm = 0.13 V; 0.3 V = 150 mOhm (hot, low Vgs) (`vcol_drop`) | 0.1205 | 0 … 0.3 | PASS |
| row driver drop incl. the 0.22 R sense resistor (V): 2 A x (0.22 + 0.08) = 0.6 V; 0.8 V keeps > 17 V on the 18 V lamp string (`vrow_on`) | 0.6228 | 0 … 0.8 | PASS |
| comparator never clears the row flip-flop in normal operation (V) (`clr_min`) | 4.999 | 3 … 5.5 | PASS |
| column MOSFET Vgs from the 1k/1.5k divider (V): IRFR5305 needs <= -7 V for its rated 65 mOhm (`vgs_col`) | -10.8 | -13 … -7 | PASS |

## lamp_matrix_trip

| measurement | value | expected | result |
|---|---|---|---|
| shorted lamp: row current exceeds the 6.4 A trip (A) (`irow_fault`) | 8.365 | 6.4 … 80 | PASS |
| row flip-flop cleared (s): short applied at 32.5 ms, column strobe (fault current) starts at 33.0 ms -> cleared within 0.2 ms (`t_trip`) | 0.03316 | 0.033 … 0.0332 | PASS |
| row current after shutdown until the next strobe (A) (`irow_after`) | 0.002529 | 0 … 0.5 | PASS |
| fault current returns at the next strobe and trips again (A) - per-strobe shutdown as in the original (`irow_next`) | 8.365 | 2 … 80 | PASS |

## psu

| measurement | value | expected | result |
|---|---|---|---|
| +18V lamp rail average at 2.8 A / 5 ohm (V): the lamp matrix needs >= 13 V for full brightness (`v18_avg`) | 13.98 | 13 … 20 | PASS |
| +18V ripple p-p with 2 x 10000 uF (V): 3 V = 20 % of the rail, the largest brightness flicker acceptable at 120 Hz (`v18_ripple`) | 0.7756 | 0 … 3 | PASS |
| +5V buck input minimum at 3 A output with 10000 uF (V): TPS54360B needs 5.6 V for 5 V out, the 6.0 V UVLO start + 0.5 V (`vin5_min`) | 8.336 | 6.5 … 14 | PASS |
| +5V raw ripple p-p (V): 10000 uF at ~3.9 A input current -> ~2.5 V; must stay below vin5_min - 5.6 V headroom (`vin5_ripple`) | 1.027 | 0 … 3.5 | PASS |
| +5V minimum at 3 A load (V) (`v5_min`) | 5 | 4.95 … 5.05 | PASS |
| +50V idle (V) (`v50_idle`) | 48.82 | 45 … 55 | PASS |
| +50V average during a 12 A coil pulse with 4400 uF (V) - unchanged from the modern board (`v50_avg_pulse`) | 38.05 | 38 … 50 | PASS |
| +50V minimum during the pulse (V) (`v50_min_pulse`) | 31.96 | 30 … 50 | PASS |
| peak coil current (A) (`icoil_max`) | 9.912 | 9 … 14 | PASS |
| +20V minimum during a 4 A flasher burst with 10000 uF (V): the +12V buck needs >= 12.9 V (Vout + Vf + Rds Iout) to stay in regulation (`v20_min`) | 15.22 | 13 … 22 | PASS |
| +20V ripple p-p during the burst (V) (`v20_ripple`) | 2.557 | 0 … 3 | PASS |
| +12V minimum during the flasher burst (V) (`v12_min`) | 12 | 11.95 … 12.05 | PASS |
| +12V maximum (V) (`v12_max`) | 12 | 11.95 … 12.05 | PASS |

## psu_brownout

| measurement | value | expected | result |
|---|---|---|---|
| +5V buck input minimum at 88 % mains and the rated 3 A (V): must stay above the UVLO stop level - 5.5 V nominal, 6.0 V worst case (Vena 1.3 V) - so the converter keeps regulating (sweep: output/spice/uvlo_sweep.md) (`vraw_min`) | 6.482 | 6 … 12 | PASS |
| +5V holds through an 88 % brownout at 3 A (V) - the LM323K needed 7.5 V raw and would have dropped out (`v5_min`) | 5 | 4.95 … 5.05 | PASS |
| +20V minimum at 88 % mains with 8 flashers hot and 10000 uF (V): above the 9.1 V worst-case UVLO stop of the +12V buck (`v20_min`) | 11.35 | 9.5 … 22 | PASS |
| +12V at 88 % mains with flashers hot (V): droops (0.97 Vin - 0.5) when +20V is under 12.9 V; 10 V still runs the switch-matrix / opto loads and the CPU-board 5 V pre-regulators (`v12_min`) | 10.51 | 10 … 12.05 | PASS |

## psu_maxload

| measurement | value | expected | result |
|---|---|---|---|
| +18V minimum with all 64 lamps lit (2.5 ohm, ~5.5 A) and 2 x 10000 uF (V): lamps stay usable above ~10 V (`v18_min`) | 12.01 | 10 … 20 | PASS |
| +5V buck input minimum with everything on (V): converter needs 5.6 V, worst-case UVLO stop 6.0 V (`vin5_min`) | 8.336 | 6 … 14 | PASS |
| +5V minimum at 3 A with everything on (V) (`v5_min`) | 5 | 4.95 … 5.05 | PASS |
| +20V minimum during the 8-flasher cold inrush with 10000 uF (V): must stay above the 8.5 V UVLO stop of the +12V buck (9.1 V worst case) (`v20_min`) | 10.95 | 9 … 22 | PASS |
| combined cold inrush of 8 flashers (A) - within the F111 5 A slow-blow 40 ms envelope (`iflash_peak`) | 50.89 | 20 … 60 | PASS |
| +12V minimum during the flasher inrush (V): the buck droops (never shuts down) when +20V is below 12.9 V; 8 V keeps the CPU-board 5 V pre-regulators alive (`v12_min`) | 10.12 | 8 … 12.05 | PASS |
| +50V average with 2 HP + 4 LP coils fired together (V) - informational, an unrealistic firmware case; parts unchanged from the modern board (`v50_avg_pulse`) | 27.68 | 20 … 50 | PASS |
| total coil current, six coils at once (A) (`itot50_max`) | 31.21 | 20 … 60 | PASS |
| peak current through the +50V bridge (A): GBPC3510 surge rating 400 A (this is a single 40 ms event) (`ibr50_peak`) | 60.89 | 0 … 400 | PASS |
| repetitive peak current in the +18V GBJ1510 with all lamps lit (A): capacitor-input rectifiers run at 3-5 x Io, limit 4 x the 15 A rating; surge rating 240 A (`ibr18_peak`) | 17.66 | 0 … 60 | PASS |
| peak current in the +20V GBJ1510 during the flasher inrush (A): 4 x the 15 A rating for the repetitive part; the 240 A surge rating covers the first cycles (`ibr20_peak`) | 32.01 | 0 … 60 | PASS |
| repetitive peak current in the +5V-raw GBU8J at 3 A output (A): 4 x the 8 A rating; surge rating 200 A (`ibr5_peak`) | 7.681 | 0 … 32 | PASS |

## sol_high

| measurement | value | expected | result |
|---|---|---|---|
| coil current with 4 ohm coil on 50 V (A) (`icoil_max`) | 12.44 | 9 … 13.5 | PASS |
| IRLR3110Z Vds while ON (V): 12 A x 18 mOhm = 0.22 V; 0.3 V = 25 mOhm, above the 4.5 V datasheet max incl. heating (`vout_on`) | 0.2315 | 0 … 0.3 | PASS |
| output clamped by the S3M tie-back diode (V) (`vout_peak`) | 51.35 | 49 … 53 | PASS |
| MOSFET dissipation during the pulse (W): 2.6 W for 40 ms is 0.1 J into the DPAK die/tab (~0.2 C/J x 40 ms ... < 5 C rise); pulsed at <= 10 % duty the average stays < 0.4 W (`p_fet`) | 2.88 | 0 … 3.5 | PASS |

## sol_low

| measurement | value | expected | result |
|---|---|---|---|
| coil current with 9 ohm coil on 50 V (A) (`icoil_max`) | 5.544 | 3.5 … 6 | PASS |
| IRLR3110Z Vds while ON at 4.6 V gate drive (V): 5.5 A x 18 mOhm = 0.1 V, limit = 2x model (36 mOhm, the datasheet max at 4.5 V is 16 mOhm) (`vce_on`) | 0.1022 | 0 … 0.2 | PASS |
| drain voltage clamped by the S1M tie-back diode at turn-off (V) (`vcol_peak`) | 51.41 | 49 … 53 | PASS |
| steady current drawn from the 74HCT574 output (A) (`i_latch`) | 0.0004536 | -0.001 … 0.001 | PASS |
| coil current 15 ms after turn-off (A) (`icoil_off`) | 1.882e-07 | -0.01 … 0.05 | PASS |
| MOSFET dissipation while ON (W): 1 W continuous is what a DPAK on 1 sq. in. of copper (~50 C/W) can hold at 50 C rise (`p_fet`) | 0.5664 | 0 … 1 | PASS |

## zero_cross

| measurement | value | expected | result |
|---|---|---|---|
| +12VU average (V) - only feeds the LED/test point (`vu_avg`) | 11.81 | 10 … 16 | PASS |
| +12VU ripple p-p (V) (`vu_ripple`) | 0.3082 | 0 … 2 | PASS |
| ZC output low level (V) (`zc_low`) | 0.09804 | 0 … 0.5 | PASS |
| sample node minimum (V, must stay > -0.3 for LM339) (`smp_min`) | 1.226e-05 | -0.35 … 0.3 | PASS |
| ZC low-pulse width (s) (`zc_width`) | 0.001272 | 0.0003 … 0.002 | PASS |
| pulse centre vs true zero crossing (s) (`zc_center_err`) | 2.115e-05 | -0.0005 … 0.0005 | PASS |

**Overall: ALL CHECKS PASS**
