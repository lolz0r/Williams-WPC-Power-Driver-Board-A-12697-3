# SPICE verification results - cost-optimised board in the STTNG machine

ngspice shared-library transient runs of each circuit block; MOSFET/diode models in `tools/spice/models.lib` are level-1 fits to datasheet Rds(on)/Qg
(functional fidelity, not vendor-exact); the TPS54360B is a behavioural peak-current-mode model (12 A/V, 4.5 A minimum current limit, 400 kHz). Machine-level decks use the real WPC
interface: 51 VAC solenoid winding (~70 V rail), 2 ms lamp column strobes, IRQ-timed triac firing, PWM-held coils, the +12 V digital / +12 V power split, the zero-cross square wave,
BLANKING as the CPU drives it at reset, and switch-on inrush against the Littelfuse 239/217 melting I2t (docs/WPC_INTERFACE_FINDINGS.md). Waveform CSVs are next to this file.
Each limit is explained in its description column (see also README.md).

## bridge_loss

| measurement | value | expected | result |
|---|---|---|---|
| BR1 +18V DC output current with all 64 lamps lit + the +12V digital buck at 0.75 A (A) - the everything-on case of psu_maxload (`iavg_18a`) | 6.447 | 5 … 8 | PASS |
| BR1 leg RMS current in that case (A): capacitor-input rectifier, crest factor ~1.6-2 (`irms_18a`) | 11.22 | 5 … 16 | PASS |
| per-diode loss of the +18V Schottky bridge (4 x STPS20M100S) with all lamps lit, datasheet equation 0.425 IF(AV) + 0.0088 IF(RMS)^2 (W) - the whole bridge is 4x this (was 15.2 W with the GBJ1510) (`pd_18a`) | 1.923 | 0 … 5 | PASS |
| Conduction-only required thermal resistance for 110 C; informational legacy metric (C/W) (`rthreq_18a`) | 31.19 | 25 … 200 | PASS |
| BR1 TO220 with individual Boyd 5772: 32.2 C/W including 25% sink derating, plus worst 70 V/125 C leakage at 20.69 V; target 125 C at 50 C ambient (`tj_18a`) | 115.3 | 0 … 125 | PASS |
| BR1 TO220/sink junction estimate at 3 A DC, including leakage (C) (`tj_18b`) | 78.84 | 0 … 125 | PASS |
| per-diode loss at the F114 rating 8 A DC (W) - informational: needs ~30 cm2 of 2 oz copper per diode for 110 C, i.e. the 8 A fuse limit is a short-term rating (`pd_18c`) | 2.494 | 0 … 5 | PASS |
| BR1 fuse-rating load is informational only; not qualified for continuous operation (C) (`tj_18c`) | 133.6 | 0 … 150 | PASS |
| BR4 +20V diode junction temperature at 2.5 A DC sustained on 4 cm2 of 2 oz copper per diode (36 C/W) (C) (`tj_20a`) | 73.46 | 0 … 110 | PASS |
| BR4 diode junction temperature at the F111 rating 5 A DC on 4 cm2 (C): informational, limit = Tj max 150 C; 110 C needs ~10 cm2 per diode (`tj_20b`) | 102 | 0 … 150 | PASS |
| BR3 +50V GBPC3510W junction temperature at 3.0 A DC sustained (a held 14.5 ohm coil half the time plus play; flippers are rectified on the Fliptronic board) with the Boyd 6223BG basket heatsink bolted on the (upward-facing) metal base: 1.4 j-c + 0.5 + 9.4 x 1.05 = 11.8 C/W (C) (`tj_50a`) | 117.5 | 0 … 125 | PASS |
| BR3 dissipation at the F112 rating 7 A DC (W) - informational: sustained limit with the 6223BG is 3.4 A (`pds_50b`) | 14.88 | 0 … 60 | PASS |
| BR2 +5V raw diode junction temperature with the +5V buck at its rated 3 A output (~1.9 A DC in) on 2 cm2 of 2 oz copper per diode (41 C/W) (C) (`tj_5a`) | 66.83 | 0 … 110 | PASS |
| BR2 diode junction temperature at the estimated real +5V load 2.4 A (C) (`tj_5b`) | 62.96 | 0 … 110 | PASS |
| BR5 +12V power diode junction temperature at 2.5 A DC sustained on 2 cm2 of 2 oz copper per diode (41 C/W) (C) (`tj_12a`) | 74.7 | 0 … 110 | PASS |
| BR5 diode junction temperature at the F116 rating 3 A DC on 2 cm2 (C) - the 239 fuse carries 110 % for 4 h, so a sustained case (`tj_12b`) | 80.09 | 0 … 110 | PASS |
| cross-check: whole-bridge dissipation of BR1 with all lamps lit from the SPICE model power balance (AC-side minus DC-side power) (W) - the model is fitted to the 25 C typical Vf and so runs above the 125 C datasheet equation (`pmodel_18a`) | 10.95 | 0 … 40 | PASS |
| +18V rail average with all lamps lit and the Schottky bridge (V): was 12.6 V with the GBJ1510 (`vdc_18a`) | 14.33 | 12 … 20 | PASS |
| BR5 leg RMS current at 2.5 A DC (A): each diode carries Irms/sqrt(2) = 2.8 A rms (IF(RMS) rating 30 A) (`irms_12a`) | 4.021 | 0 … 8 | PASS |

## buck_12v

| measurement | value | expected | result |
|---|---|---|---|
| steady-state output at 1 A from the +18V rail at 13.5 V (V) (`vout_ss`) | 11.94 | 11.8 … 12.2 | PASS |
| output ripple p-p at 1 A (V) (`vout_ripple`) | 0.04068 | 0 … 0.1 | PASS |
| undershoot on a 1 -> 2 A load step (V): the real load behind F115 is <= 0.75 A; 11.4 V keeps the switch matrix / CPU +12V loads happy (`vout_step_min`) | 11.8 | 11.4 … 12.2 | PASS |
| overshoot on the 2 -> 1 A step (V) (`vout_step_max`) | 12.04 | 11.8 … 12.6 | PASS |
| peak inductor current at 2 A from 13.5 V (A): below the 4.5 A minimum current limit (`il_peak`) | 3.233 | 2 … 4.3 | PASS |
| output at 2 A (V) (`vout_2a`) | 11.9 | 11.8 … 12.2 | PASS |
| input current at 2 A out from 13.5 V (A) (`iin_2a`) | -1.812 | -2.6 … -1 | PASS |

## buck_5v

| measurement | value | expected | result |
|---|---|---|---|
| steady-state output at 1 A (V): 5.10 V set point (11.3 k / 2.1 k, Vref 0.8 V) (`vout_ss`) | 5.105 | 5 … 5.2 | PASS |
| output ripple p-p at 1 A (V) (`vout_ripple`) | 0.02824 | 0 … 0.08 | PASS |
| undershoot on a 1 -> 3 A load step (V): with the 5.10 V set point the dip stays >= 4.75 V at the board, i.e. > 4.70 V (MC34064 maximum threshold) at the CPU even through 80 mOhm... see docs/THERMAL_AND_PROTECTION.md section 9 (`vout_step_min`) | 5.004 | 4.75 … 5.2 | PASS |
| overshoot on the 3 -> 1 A step (V): stays below the 5.20 V no-load maximum at the connector (`vout_step_max`) | 5.194 | 5 … 5.5 | PASS |
| peak inductor current at 3 A (A): must stay below the 4.5 A minimum current limit of the TPS54360B (SRP1265A-100M rated 10 A) (`il_peak`) | 3.66 | 3 … 4.3 | PASS |
| output at 3 A (V) (`vout_3a`) | 5.091 | 5 … 5.2 | PASS |
| input current at 3 A out from 8 V (A, negative = drawn from Vin) (`iin_3a`) | -2.103 | -3 … -1.5 | PASS |

## flasher

| measurement | value | expected | result |
|---|---|---|---|
| cold-lamp inrush (A) (`ilamp_inrush`) | 6.628 | 3 … 8 | PASS |
| hot lamp current (A) (`ilamp_hot`) | 1.112 | 0.7 … 1.4 | PASS |
| IPD90N10S4L06 drain voltage with hot filament load. (`vsat`) | 0.01363 | 0 … 0.1 | PASS |

## gi_dim

| measurement | value | expected | result |
|---|---|---|---|
| ZERO CROSS period from the board detector inside this deck (s) (`zc_period`) | 0.01667 | 0.0163 … 0.017 | PASS |
| ZC rising edge after the true crossing (s) (`zc_rise_offset`) | 0.0004759 | 0 … 0.001 | PASS |
| ZC falling edge before the true crossing (s) (`zc_fall_offset`) | -0.0004456 | -0.001 … 0 | PASS |
| triac gate current (A) - above the 50 mA quadrant-IV Igt of the BTA16-600C (`ig_pk`) | 0.08003 | 0.06 … 0.13 | PASS |
| level 0 (full): positive half-cycle peak string current (A) (`l0_max`) | 6.621 | 5 … 8 | PASS |
| level 0: negative half-cycle peak (A) - fires in both half-cycles (`l0_min`) | -6.621 | -8 … -5 | PASS |
| level 0: |average| / rms of the string current - symmetric, no transformer DC (`l0_asym`) | 2.796e-08 | 0 … 0.02 | PASS |
| level 3, gate held to the next ZC edge: positive peak (A) (`l3h_max`) | 6.621 | 5 … 8 | PASS |
| level 3 held: negative peak (A) - both half-cycles fire (`l3h_min`) | -6.621 | -8 … -5 | PASS |
| level 3 held: |avg|/rms - asymmetry from the +/-0.3 ms edge offsets of the detector (same behaviour as the original board) (`l3h_asym`) | 0.1133 | 0 … 0.25 | PASS |
| level 3, 8 us gate pulse (FreeWPC style): positive peak (A) (`l3p_max`) | 6.621 | 5 … 8 | PASS |
| level 3 pulsed: negative peak (A) - the 50 mA-gate BTA16-600C latches on a few-us pulse in both quadrants (`l3p_min`) | -6.621 | -8 … -5 | PASS |
| level 7 (dimmest) with the bit HELD until the next ZC edge: positive peak (A) - informational: because the ZC edge comes after the crossing, a held gate re-fires the triac at the crossing and that half-cycle runs at full brightness; the firmware must pulse the bit or clear it before the crossing, exactly as with the original detector (`l7h_max`) | 6.621 | 1 … 8 | PASS |
| level 7 held: negative peak (A) (`l7h_min`) | -3.593 | -8 … -1 | PASS |
| level 7 pulsed: positive peak (A) (`l7p_max`) | 1.477 | 1 … 8 | PASS |
| level 7 pulsed: negative peak (A) (`l7p_min`) | -3.593 | -8 … -1 | PASS |
| level 7 pulsed: string rms current (A) - dimmest level (`l7p_rms`) | 0.6617 | 0.3 … 1.5 | PASS |
| level 0: string rms current (A) - full (18 x #44 = 4.5 A) (`l0_rms`) | 4.682 | 4 … 5.5 | PASS |

## gi_gate

| measurement | value | expected | result |
|---|---|---|---|
| triac gate current (A) - above the 50 mA worst-case Q IV Igt of the BTA16-600C (`ig_peak`) | 0.07841 | 0.06 … 0.13 | PASS |
| string current before trigger (A) (`istr_off`) | 6.092e-06 | 0 … 0.05 | PASS |
| string current while enabled (A peak) (`istr_on`) | 5.649 | 4 … 8 | PASS |
| string rms current while enabled (A) - 18 x #44 on 6.3 VAC, F106 is 5 A S.B. (`istr_rms`) | 3.887 | 3 … 5 | PASS |
| string current after latch released (A) (`istr_after`) | 8.9e-06 | 0 … 0.3 | PASS |
| MMBT4401 dissipation (W, SOT-23 limit 0.31 W) (`p_npn`) | 0.1245 | 0 … 0.25 | PASS |
| base current sourced by the 74HCT574 (A, negative = out of the latch) (`i_latch`) | -0.003665 | -0.004 … -0.0001 | PASS |
| BTA16-600C conduction loss with the datasheet on-state (Vt0 0.85 V, Rd 25 mOhm) at this string current (W) - the datasheet gives <= 5 W at 4.5 A rms (`p_triac`) | 3.265 | 0 … 5 | PASS |
| junction rise above ambient with the Boyd 7020BG bolt-on channel heatsink (8.7 C/W catalogue value at a 75 C rise, x1.25 for the ~50 C rise here) + Rth(j-c) 2.5 (BTA16 insulated TO-220) + 0.5 C/W interface = 13.875 C/W (C): limit Tj <= 125 C in a 50 C cabinet. The 7020BG (33.02 x 11.94 x 36.83 mm, M3 bolt-on, no PCB holes) fits all five triac positions on the tab side (docs/THERMAL_AND_PROTECTION.md section 2) (`tj_rise_sink`) | 45.3 | 0 … 75 | PASS |
| informational: the rise the previously specified Aavid 577002B00000G clip-on would give - it is a 32 C/W part per the Boyd catalogue (35 C/W junction-to-ambient), i.e. Tj ~165 C with an incandescent string; replaced by the 7020BG (C) (`tj_rise_clip`) | 114.3 | 0 … 200 | PASS |
| maximum sink-to-ambient thermal resistance that keeps Tj <= 125 C at 50 C ambient with this string (C/W) - informational, compare with the 10.875 C/W of the 7020BG in this cabinet (`rth_sa_needed`) | 19.97 | 0 … 100 | PASS |

## gi_string

| measurement | value | expected | result |
|---|---|---|---|
| cold-start peak current of an 18 x #44 string fired at the voltage peak (A) - BTA16-600C ITSM 160 A (8.3 ms) (`ipk`) | 38.84 | 0 … 160 | PASS |
| I2t through F106 (239 5 A S.B., 302.8 A2s nominal melting) during the whole cold start (A2s): <= 20 %, and far below the BTA16 I2t of 128 A2s (`i2t_f106`) | 9.188 | 0 … 60 | PASS |
| I2t in the first 30 ms (A2s) - the part the fuse sees as a surge (`i2t_30ms`) | 3.155 | 0 … 60 | PASS |
| steady string rms current (A) - 18 x #44 = 4.5 A on the 5 A slow-blow F106 (rated to carry 110 % continuously) (`irms_ss`) | 4.544 | 3.5 … 5 | PASS |
| steady triac dissipation with the datasheet on-state (W) - see gi_gate for the heatsink requirement (`p_triac`) | 3.913 | 0 … 5 | PASS |
| string current before the gate is driven (A) (`istr_pre`) | 1.107e-05 | 0 … 0.05 | PASS |
| junction rise with the Boyd 7020BG heatsink at the steady 4.5 A rms string (C): P x 13.875 C/W (2.5 j-c + 0.5 interface + 10.875 sink) - the worst of the two G.I. decks; Tj <= 125 C at 50 C ambient (`tj_rise_sink`) | 54.29 | 0 … 75 | PASS |

## inrush

| measurement | value | expected | result |
|---|---|---|---|
| peak inrush through F113 / BR2 (GBU8J, IFSM 200 A) into C5 at switch-on on the mains peak (A) (`ipk_f113`) | 55.12 | 0 … 60 | PASS |
| I2t through F113 in the first 250 ms (A2s): <= 20 % of the 302.836 A2s nominal melting I2t of the Littelfuse 239 5 A (239 datasheet / distributor specification, docs/THERMAL_AND_PROTECTION.md section 4) so the fuse never ages from switch-on (`i2t_f113`) | 2.824 | 0 … 60.5 | PASS |
| peak inrush through F114 / BR1 (GBJ1510, IFSM 240 A) into C6 + C7 (A) (`ipk_f114`) | 71.27 | 0 … 120 | PASS |
| I2t through the FAST 8 A F114 (A2s): <= 20 % of the 198.16 A2s of the Littelfuse 217 8 A (217 datasheet table, read directly) (`i2t_f114`) | 10.46 | 0 … 39.6 | PASS |
| peak inrush through F111 / BR4 (GBJ1510) into C11 (A) (`ipk_f111`) | 59.63 | 0 … 120 | PASS |
| I2t through F111 (239 5 A, 302.836 A2s) (A2s): <= 20 % (`i2t_f111`) | 5.458 | 0 … 60.5 | PASS |
| peak inrush through F116 / BR5 (GBU8J) into the 10000 uF C30 (A) (`ipk_f116`) | 35.52 | 0 … 100 | PASS |
| I2t through F116 (239 3 A) (A2s): <= 20 % of the real 239 3 A nominal melting I2t, 129.51 A2s (replaces the 313 3 A 200 A2s stand-in) (`i2t_f116`) | 1.94 | 0 … 25.9 | PASS |
| peak inrush through F112 / BR3 (GBPC3510, IFSM 400 A) into 2 x 2200 uF at 72.7 V peak (A) (`ipk_f112`) | 53.27 | 0 … 200 | PASS |
| I2t through F112 (239 7 A) (A2s): the 239 7 A row could not be retrieved (every host of the 239 datasheet blocks automated access; the 3 A / 5 A values 129.5 / 302.8 A2s extrapolate to ~530 A2s) - the limit stays at 20 % of the OEM 313 7 A (347 A2s), which is the more conservative reference (`i2t_f112`) | 6.663 | 0 … 69.4 | PASS |
| "+50V" reached after 250 ms (V) (`v50_final`) | 70.37 | 66 … 74 | PASS |
| +18V reached after 250 ms (V) (`v18_final`) | 17.5 | 14 … 20 | PASS |

## lamp_matrix

| measurement | value | expected | result |
|---|---|---|---|
| row current, normal lamp incl. cold inrush (A) (`irow_normal`) | 2.438 | 0.3 … 3.5 | PASS |
| sense voltage stays below the 1.4 V trip (V) (`vsense_normal`) | 0.5026 | 0 … 1.3 | PASS |
| 1.4 V reference (V) (`vref`) | 1.29 | 1.2 … 1.6 | PASS |
| column IRFR5305 drop with one lamp on (V): ~2 A x 65 mOhm = 0.13 V; 0.3 V = 150 mOhm (hot, low Vgs) (`vcol_drop`) | 0.1205 | 0 … 0.3 | PASS |
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

## lamp_strobe

| measurement | value | expected | result |
|---|---|---|---|
| column IRFR5305 current at the start of a 2 ms strobe with 8 warm #555 lamps (A): ~1 A per lamp, 0.7 A once hot (`icol_peak`) | 8.022 | 4 … 12 | PASS |
| average column current over the 16 ms frame (A): x 8 columns = the ~5 A +18V load with every lamp lit (`icol_avg`) | 0.666 | 0.4 … 1 | PASS |
| column MOSFET drop at the 8 A strobe peak (V): 65-100 mOhm (`vcol_drop`) | 0.4342 | 0 … 0.8 | PASS |
| average column MOSFET dissipation, all 8 lamps lit (W): 2 ms of 8 A every 16 ms (`pcol_avg`) | 0.2349 | 0 … 0.6 | PASS |
| column DPAK junction rise (C): P x 110 C/W (IRFR5305 datasheet minimum footprint; the as-routed drain copper is the tab pad only) (`tj_rise_col`) | 25.84 | 0 … 75 | PASS |
| row IRLR024N current: one warm lamp per strobe (A) (`irow_peak`) | 1.023 | 0.5 … 2.5 | PASS |
| average row current with all 8 lamps of the row lit (A) (`irow_avg`) | 0.5139 | 0.2 … 1 | PASS |
| row MOSFET average dissipation (W) (`prow_avg`) | 0.08207 | 0 … 0.3 | PASS |
| row DPAK junction rise (C): P x 110 C/W (IRLR024N minimum footprint, as routed) (`tj_rise_row`) | 9.027 | 0 … 75 | PASS |
| sense voltage over 400 ms of strobing incl. the cold first strobes (V): stays below the 1.4 V trip (`vsense_max`) | 0.1917 | 0 … 1.2 | PASS |
| no false over-current trip during normal strobing (V) (`clr_min`) | 5 | 3 … 5.5 | PASS |
| cold-filament current at the very first strobe (A): 7 ohm filament on 18 V (`ilamp_first`) | 2.28 | 1.5 … 3.5 | PASS |
| RMS voltage across a #555 lamp over the 16 ms frame (V): rated 6.3 V; the MOSFET drops are 0.5 V instead of the 2.2 V of the 1993 Darlingtons, so the lamps run at ~98 % of their rating (brighter, about 3x shorter life than on the original board - irrelevant for LEDs) (`vlamp_rms`) | 6.174 | 5.5 … 6.6 | PASS |
| the same lamp behind the original TIP107/TIP102 drops (V) - reference for the comparison (`vlamp_old_rms`) | 5.531 | 5 … 6 | PASS |

## powerup

| measurement | value | expected | result |
|---|---|---|---|
| coil current while BLANKING is high (reset, +5V ramp, undefined latch content = 1) (A): the tri-stated 74HCT574 and the 10 k gate pull-down keep the IPD90N10S4L06 off (`icoil_blank`) | 2.375e-08 | 0 … 0.01 | PASS |
| G.I. string current while blanked (A): 10 k base pull-down keeps the MMBT4401 / triac off (`istr_blank`) | 9.6e-06 | 0 … 0.05 | PASS |
| lamp column current while blanked with a row MOSFET randomly ON (A): the TBD62083A input pull-down keeps the column P-MOSFET off (`icol_blank`) | 1.36e-10 | 0 … 0.01 | PASS |
| solenoid gate voltage while blanked (V) (`vgate_blank`) | 0.0001295 | 0 … 0.5 | PASS |
| BLANKING never drops below 4 V while the CPU holds reset (V): SR1 pulls it up, the CPU 2N3904 is off (`blank_min`) | 5 | 4 … 5.5 | PASS |
| coil current after the CPU releases BLANKING with the latch holding 1 (A): the path works (`icoil_on`) | 16.62 | 10 … 20 | PASS |
| G.I. string current after release (A peak) (`istr_on`) | 6.621 | 4 … 8 | PASS |
| lamp column current after release (A) (`icol_on`) | 5.284 | 3 … 8 | PASS |
| coil current after the CPU writes 0 (A) (`icoil_after`) | 2.533e-09 | 0 … 0.01 | PASS |
| column current after the CPU writes 0 (A) (`icol_after`) | 3.111e-05 | 0 … 0.01 | PASS |

## psu

| measurement | value | expected | result |
|---|---|---|---|
| +18V lamp rail average at 2.8 A / 5 ohm plus the 1 A +12V digital buck (V): the lamp matrix needs >= 13 V for full brightness (`v18_avg`) | 15.33 | 13 … 20 | PASS |
| +18V ripple p-p with 2 x 10000 uF (V): 3 V = 20 % of the rail, the largest brightness flicker acceptable at 120 Hz (`v18_ripple`) | 1.121 | 0 … 3 | PASS |
| +5V buck input minimum at 3 A output with 10000 uF (V): TPS54360B needs 5.6 V for 5 V out, the 6.0 V UVLO start + 0.5 V (`vin5_min`) | 9.974 | 6.5 … 14 | PASS |
| +5V raw ripple p-p (V) (`vin5_ripple`) | 1.008 | 0 … 3.5 | PASS |
| +5V minimum at 3 A load (V): set point 5.10 V (11.3 k / 2.1 k, 0.1 %) since the 2026-09-07 review (`v5_min`) | 5.1 | 5.05 … 5.15 | PASS |
| +5V at the CPU board with 3 A through 80 mOhm of board copper + harness (V): must stay above the 4.70 V maximum MC34064 reset threshold (with 5.00 V and 1 % feedback parts the worst case was 4.61 V) (`v5_cpu_worst`) | 4.86 | 4.7 … 5.2 | PASS |
| "+50V" idle (V): 51.4 VAC nominal winding -> 72.7 V peak minus two diode drops; pinwiki: TP6 measures 70-75 V (`v50_idle`) | 69.22 | 66 … 74 | PASS |
| "+50V" maximum at idle (V): the STTNG transformer measured 55.2 VAC unloaded = 78 V peak (83 V at +6 % line); 100 V capacitors and 100 V MOSFETs keep >= 17 V (`v50_max`) | 69.39 | 66 … 80 | PASS |
| "+50V" average during a 40 ms AE-23-800 pulse with 4400 uF (V): the original 100 uF board fell to the rectified sine (`v50_avg_pulse`) | 41.64 | 35 … 60 | PASS |
| "+50V" minimum during the pulse (V) (`v50_min_pulse`) | 35.53 | 28 … 60 | PASS |
| peak AE-23-800 coil current with the sagging rail (A) (`icoil_max`) | 13.07 | 11 … 18 | PASS |
| +20V minimum during a 4 A flasher burst with 10000 uF (V): flashers only on this rail now (`v20_min`) | 17.81 | 13 … 24 | PASS |
| +20V ripple p-p during the burst (V) (`v20_ripple`) | 2.194 | 0 … 3 | PASS |
| +12V digital minimum, buck fed from the +18V lamp rail at 2.8 A of lamps (V) (`v12_min`) | 12 | 11.95 … 12.05 | PASS |
| +12V digital maximum (V) (`v12_max`) | 12 | 11.95 … 12.05 | PASS |

## psu_12vu

| measurement | value | expected | result |
|---|---|---|---|
| +12V power minimum at 2.5 A, measured STTNG winding (12.47 VAC unloaded, 0.25 ohm/leg) (V) (`v12u_min`) | 11.61 | 10 … 16 | PASS |
| +12V power average at 2.5 A (V) (`v12u_avg`) | 12.22 | 10.5 … 16 | PASS |
| ripple p-p at 2.5 A with 10000 uF (V) (`v12u_ripple`) | 1.207 | 0 … 2 | PASS |
| BR5 GBU8J repetitive peak current (A): 4 x 8 A (`ibr5_peak`) | 8.227 | 0 … 32 | PASS |
| BR5 RMS current (A): GBU8J average rating 8 A (`ibr5_rms`) | 4.079 | 0 … 8 | PASS |
| maximum +12V power with only the LED load (V): C30 is a 25 V part - 20 V keeps 20 % margin (unloaded winding 17.6 V peak) (`v12u_max_unloaded`) | 16.7 | 0 … 20 | PASS |
| pessimistic bound: the manual's nominal 9.8 VAC winding at 2.5 A (V) - the real transformer is ~2 V higher (`v12u_min_nominal`) | 10.56 | 8.5 … 16 | PASS |

## psu_brownout

| measurement | value | expected | result |
|---|---|---|---|
| +5V buck input minimum at 88 % mains and the rated 3 A (V): must stay above the UVLO stop level - 5.5 V nominal, 6.0 V worst case (Vena 1.3 V) - so the converter keeps regulating (sweep: output/spice/uvlo_sweep.md) (`vraw_min`) | 8.275 | 6 … 12 | PASS |
| +5V holds through an 88 % brownout at 3 A (V) - the CPU reset chip (MC34064, 4.6 V) never trips; 5.10 V set point (`v5_min`) | 5.1 | 5.05 … 5.15 | PASS |
| +18V minimum at 88 % mains with all lamps lit (V) (`v18_min`) | 11.71 | 9.5 … 16 | PASS |
| +12V digital at 88 % mains with all lamps lit (V): droops with the +18V rail; 9 V still runs the CPU switch-matrix comparators; the original 7812 would have delivered ~7 V here (`v12_min`) | 10.86 | 9 … 12.05 | PASS |
| +12V power at 88 % mains with 2.5 A of motors / optos (V) (`v12u_min`) | 10.13 | 8.5 … 16 | PASS |

## psu_maxload

| measurement | value | expected | result |
|---|---|---|---|
| +18V minimum with all 64 lamps lit (2.5 ohm, ~5 A) plus the +12V digital buck, 2 x 10000 uF (V): lamps stay usable above ~10 V (`v18_min`) | 13.48 | 10 … 20 | PASS |
| +5V buck input minimum with everything on (V): converter needs 5.6 V, worst-case UVLO stop 6.0 V (`vin5_min`) | 9.974 | 6 … 14 | PASS |
| +5V minimum at 3 A with everything on (V): 5.10 V set point (`v5_min`) | 5.1 | 5.05 … 5.15 | PASS |
| +20V minimum during the 8-flasher cold inrush with 10000 uF (V): only flashers hang on this rail (interlocked with the coin door) (`v20_min`) | 12.81 | 9 … 24 | PASS |
| combined cold inrush of 8 flashers (A) - within the F111 5 A slow-blow 40 ms envelope (`iflash_peak`) | 56.72 | 20 … 60 | PASS |
| +12V digital minimum with all lamps lit (V): the buck droops (0.97 Vin - 0.5) while +18V sags to 11.9 V; the original 7812 (needs 14 V in) dropped to ~10 V in the same case; the CPU switch matrix (LM339 + 1 k pull-ups) works far below that (`v12_min`) | 12 | 10.5 … 12.05 | PASS |
| +12V power (unregulated) minimum with 2.5 A of gun motors / optos / DMD / coin door on 10000 uF (V): pinwiki reports jittery optos around 10 V; a 15000 uF C30 (OEM) would add ~0.4 V (`v12u_min`) | 11.61 | 10 … 16 | PASS |
| "+50V" average with 2 AE-23-800 + 4 AE-26-1200 fired together (V) - informational, an unrealistic firmware case bounding the rail (`v50_avg_pulse`) | 22.4 | 15 … 60 | PASS |
| total coil current, six coils at once (A) (`itot50_max`) | 37.82 | 25 … 45 | PASS |
| peak current through the +50V bridge (A): GBPC3510 surge rating 400 A (this is a single 40 ms event) (`ibr50_peak`) | 37 | 0 … 400 | PASS |
| repetitive peak current in the +18V GBJ1510 with all lamps lit (A): capacitor-input rectifiers run at 3-5 x Io, limit 4 x the 15 A rating; surge rating 240 A (`ibr18_peak`) | 24.57 | 0 … 60 | PASS |
| peak current in the +20V GBJ1510 during the flasher inrush (A): 4 x the 15 A rating for the repetitive part; the 240 A surge rating covers the first cycles (`ibr20_peak`) | 38.26 | 0 … 60 | PASS |
| repetitive peak current in the +5V-raw GBU8J at 3 A output (A): 4 x the 8 A rating; surge rating 200 A (`ibr5_peak`) | 8.705 | 0 … 32 | PASS |
| repetitive peak current in the +12V-power GBU8J (BR5) at 2.5 A (A): 4 x the 8 A rating (`ibr12_peak`) | 8.228 | 0 … 32 | PASS |

## ribbon

| measurement | value | expected | result |
|---|---|---|---|
| MOSFET gate after the CPU writes bit = 1 (V): 74LS240 drives the ribbon LOW, U9 74HCT240 re-inverts it, the 74HCT574 latches it on the strobe rising edge -> ON (`g_w1`) | 4.536 | 4 … 5 | PASS |
| drain voltage with the output ON (V) (`out_w1`) | 0.07961 | 0 … 1 | PASS |
| gate after the CPU writes bit = 0 (ribbon HIGH) (V) - OFF (`g_w0`) | 0.0913 | 0 … 0.3 | PASS |
| drain at the 70 V rail with the output OFF (V) (`out_w0`) | 71.12 | 60 … 80 | PASS |
| gate after a second write of 1 (V) - ON again (`g_w1b`) | 4.475 | 4 … 5 | PASS |
| current the 74HCT574 output drives into the gate network while enabled (A) - proves the output is active (charging Cgs through 100 R) (`ioe_on`) | 0.0004536 | 1e-05 … 0.2 | PASS |
| 74HCT574 output current with the ribbon unplugged (A): SR2 pulls the data HIGH (bit 0), SR1 holds the strobes HIGH (no clock) and BLANKING HIGH -> every latch tri-stated (/OE) - the 10 k pull-down then discharges the gate in ~150 us (powerup.cir) (`ioe_unplug`) | 7.113e-10 | 0 … 1e-06 | PASS |
| gate 10 us after the unplug (V) - informational: still decaying through the 10 k / Cgs (tau ~40 us), see powerup for the settled state (`g_unplug`) | 4.132 | 0 … 5 | PASS |
| BLANKING level with the ribbon unplugged (V) - pulled to Vcc by SR1 (`blank_unplug`) | 5 | 4 … 5.5 | PASS |
| 74HCT574 output current while the CPU holds BLANKING high (reset / watchdog) with the latch holding 1 (A) - tri-stated, OFF (`ioe_blank`) | 1.271e-09 | 0 … 1e-06 | PASS |
| gate 10 us after BLANKING went high (V) - informational (see ioe_blank and powerup.cir) (`g_blank`) | 3.537 | 0 … 5 | PASS |
| gate after the final write of 0 (V) (`g_w0b`) | 0.07675 | 0 … 0.3 | PASS |
| ribbon data line LOW level during the strobe with the 4.7 k pull-up sinking into the 74LS240 (V) - HCT VIL 0.8 V (`rib_low`) | 0.02751 | 0 … 0.8 | PASS |
| ribbon data line HIGH level from the 74LS240 totem pole (V) - HCT VIH 2.0 V (`rib_high`) | 3.443 | 2 … 5.5 | PASS |
| data setup at the 74HCT574 D input (after the 53 ns TI HCT240 bound) before the strobe rising edge (s): 6809E tDDQ 200 ns max after Q rise vs the strobe ending at E fall (375 ns); TI SN74HCT574 tsu 25 ns at 4.5 V over -40..85 C (`t_setup`) | 1.158e-07 | 2.5e-08 … 1e-06 | PASS |
| data hold at the 74HCT574 after the strobe rising edge (s): 6809E tDHW 30 ns min plus the 74HCT240 delay and the 4.7 k / 120 pF ribbon rise (~0.5 us); 74HCT574 th 5 ns (`t_hold`) | 1.824e-07 | 5e-09 … 1e-06 | PASS |

## sol_high

| measurement | value | expected | result |
|---|---|---|---|
| AE-23-800 (4.2 ohm, 12 mH) coil current on the 70 V rail (A): 70 / 4.2 = 16.7 A (`icoil_max`) | 16.62 | 14 … 18.5 | PASS |
| IPD90N10S4L06 drain voltage during conduction; approximate hot-resistance fit. (`vout_on`) | 0.2054 | 0 … 0.45 | PASS |
| output clamped by the S3M tie-back diode (V) (`vout_peak`) | 71.49 | 68 … 80 | PASS |
| MOSFET conduction loss during the commanded pulse, using the approximate hot-resistance fit. (`p_fet`) | 3.413 | 0 … 7.5 | PASS |
| energy dissipated in the MOSFET per 40 ms pulse (J) (`e_pulse`) | 0.123 | 0 … 0.3 | PASS |
| Illustrative single-pulse rise from energy and assumed 0.6 C/W transient impedance; not package/board thermal qualification. (`tj_rise_pulse`) | 1.846 | 0 … 6 | PASS |
| Junction rise at 10% repeating duty using 62 C/W minimum-footprint datasheet RthJA; 125 C target at 50 C local ambient. (`tj_rise_10pct`) | 21.16 | 0 … 75 | PASS |
| Junction rise at 20% repeating duty using 62 C/W minimum-footprint datasheet RthJA; 125 C target at 50 C local ambient. (`tj_rise_20pct`) | 42.32 | 0 … 75 | PASS |
| Sensitivity only: same 20% duty at an assumed 60 C/W. No claim that this layout achieves that resistance. (`tj_rise_20pct_pour`) | 40.96 | 0 … 75 | PASS |

## sol_hold

| measurement | value | expected | result |
|---|---|---|---|
| 100 % hold of a 14.5 ohm coil on 70 V (A) (`ia_hold`) | 4.824 | 4 … 5.5 | PASS |
| MOSFET conduction loss during continuous hold using the approximate hot-resistance fit. (`pa_hold`) | 0.2858 | 0 … 0.8 | PASS |
| Vds during the hold (V) (`vds_hold`) | 0.05926 | 0 … 0.15 | PASS |
| Continuous-hold junction rise using 62 C/W minimum-footprint datasheet RthJA; excludes neighboring heat. (`tj_rise_hold`) | 17.72 | 0 … 75 | PASS |
| average current of an AE-26-1200 PWM-held at 50 % (FreeWPC SOL_DUTY_50: 4 ms on / 4 ms off) (A) (`ib_avg`) | 3.194 | 2.5 … 4 | PASS |
| peak coil current during the PWM hold (A) (`ib_max`) | 5.486 | 4 … 7 | PASS |
| coil current stays continuous through the 4 ms off slot (A) (`ib_min`) | 0.9033 | 0.3 … 3 | PASS |
| MOSFET dissipation during the PWM hold (W): conduction + the 125 Hz switching is negligible (`pb_avg`) | 0.2345 | 0 … 0.8 | PASS |
| PWM-hold junction rise using 62 C/W minimum-footprint datasheet RthJA; excludes neighboring heat. (`tj_rise_pwm`) | 14.54 | 0 … 75 | PASS |
| average freewheel current in the S3M tie-back (A): S3M IF(AV) = 3 A (this is why the coil groups got S3M instead of S1M) (`idb_avg`) | 1.28 | 0 … 2 | PASS |
| peak diode current (A): S3M IFSM 100 A (`idb_max`) | 12.33 | 0 … 30 | PASS |

## sol_low

| measurement | value | expected | result |
|---|---|---|---|
| AE-26-1200 (10.8 ohm) coil current on the 70 V rail (A) (`icoil_max`) | 6.474 | 5.5 … 7.5 | PASS |
| IPD90N10S4L06 drain voltage during conduction at 4.6 V command; approximate hot-resistance fit, 8.1 mOhm maximum specified at 4.5 V and 25 C. (`vce_on`) | 0.07961 | 0 … 0.25 | PASS |
| Drain voltage clamped by S3M tie-back in this 70 V case; separate high-line and parasitic checks are required. (`vcol_peak`) | 71.14 | 68 … 80 | PASS |
| steady current drawn from the 74HCT574 output (A) (`i_latch`) | 0.0004536 | -0.001 … 0.001 | PASS |
| coil current 15 ms after turn-off (A) (`icoil_off`) | 3.071e-07 | -0.01 … 0.05 | PASS |
| MOSFET conduction loss during the commanded pulse, using the approximate hot-resistance fit. (`p_fet`) | 0.5154 | 0 … 1.5 | PASS |

## zero_cross

| measurement | value | expected | result |
|---|---|---|---|
| ZERO CROSS high level (V) - 1.5 k pull-up, no divider (`zc_high`) | 5 | 4.5 … 5.1 | PASS |
| ZERO CROSS low level (V) (`zc_low`) | 0.1607 | 0 … 0.5 | PASS |
| sample node minimum (V, must stay > -0.3 V for the LM339): the fused leg sits at about -1 V while the other leg conducts, divided by 10k/1.5k (`za_min`) | -0.09706 | -0.35 … 0.3 | PASS |
| ZERO CROSS period (s) - 60 Hz square wave as on the A-12697 (sheet 1: D38 sample on U6A pin 7 (+), reference on pin 6 (-); a real TP4 measures ~8.1 ms high pulses at 60 Hz - Pinside, Arduino pulse timer), one edge per mains zero crossing; the earlier 120 Hz active-high pulse of this board was wrong (`zc_period`) | 0.01667 | 0.0163 … 0.017 | PASS |
| time HIGH per cycle (s) - 8.33 ms minus twice the threshold delay (~2 V on the leg); the OEM detector gives the same shape (`zc_high_time`) | 0.007411 | 0.0065 … 0.0085 | PASS |
| rising edge after the true zero crossing (s) (`zc_rise_offset`) | 0.0004746 | 0 … 0.001 | PASS |
| falling edge before the true zero crossing (s) (`zc_fall_offset`) | -0.0004475 | -0.001 … 0 | PASS |
| 10-90 % rise time of the edge (s) - no hysteresis feedback here, the comparator switches cleanly; the ASIC squares it anyway (`zc_rise_time`) | 4.2e-06 | 0 … 0.0003 | PASS |
| peak current into the 10 k sample resistor (A) - 0805 1/8 W is fine (`i_r197_pk`) | 0.0009606 | 0 … 0.005 | PASS |

**Overall: ALL CHECKS PASS**
