# Verification matrix - cost-optimised WPC Power Driver Board (A-12697-3 replacement)

Audit of every functional integration point between this board and the rest of a WPC machine (STTNG as the reference machine), done
2026-09-06 together with the modern board (`../wpc_power_driver_modern/docs/VERIFICATION_MATRIX.md`; the two matrices share the evidence
and the contradiction table).  Each row names the evidence, the SPICE deck / check (or the netlist check) and the result.
Suite: `flatpak run --command=python3 org.kicad.KiCad tools/spice/run_all.py` -> `output/spice/RESULTS.md` (**211 of 211 checks pass**
- see `docs/THERMAL_AND_PROTECTION.md`, the 2026-09-07 thermal / protection review that closed rows 9.6, 14 and 15, added the `bridge_loss`
deck, replaced the +18 V / +20 V / +5 V raw / +12 V power bridges by discrete STPS20M100S Schottky bridges D101-D116 and raised the +5 V set
point to 5.10 V).  Schematic regenerated from `tools/design_cost.py` with **ERC 0** after the
corrections in section 17.

Evidence tags: **[SCH1/2/3]** = WPC Schematic Manual 16-9834.2, power driver board 16-9057 rev 6 sheets 1-3 (PDF pages 7-9 of
`../wpc_power_driver_modern/.scratch/wpc_sch.pdf`, read at 600 dpi); **[SCH-CPU]** CPU board 16-9060 (page 5); **[SCH-PW]** power wiring
sheet 2 (page 4, interlock); **[OPS]** STTNG manual; **[PM]** PinMAME; **[FW]** FreeWPC; **[PW]** pinwiki; **[PS-ZC]** Pinside topic 22018
(Arduino pulse-timer measurement of TP4); **[LF]** Littelfuse datasheets (239 5 A 302.836, 3 A 129.51, 0.75 A 5.425 A2s; 217 8 A 198.16 A2s; the 239 7 A row not
retrievable - 313 7 A 347 A2s kept as the stand-in; `docs/THERMAL_AND_PROTECTION.md` section 4); **[NET]** `.scratch/nets.json`.  Result: **PASS / FAIL / NET** (netlist inspection) / **N/S** (not simulated, reason given).

## 1. J113 ribbon (CPU J211, 34-way 1:1)

Netlist dump [NET]: `J113 1:nc 2:nc 3:nc 4:GND 5:nc 6:GND 7:CLK_LAMP_ROW 8:CLK_LAMP_COL 9:CLK_SOL_FLASH 10:CLK_SOL_HIGH 11:CLK_SOL_LOW
12:CLK_SOL_GEN 13:CLK_GI 14:GND 15:D7_N 17:D6_N ... 29:D0_N 16-30 even GND 31:BLANKING 32:nc 33:nc 34:ZERO_CROSS`; strobes -> `U10-U13
pins 3/11, U18-11, U3-11, U5-11, U4-11, U2-11, U1-11` with SR1 4.7 k pull-ups; `BLANKING -> /OE of U1-U5, U18, SR1-9, R6`; data `D0_N..D7_N ->
U9 74HCT240 -> D0..D7` with SR2 4.7 k pull-ups.  Timing deck `ribbon.cir` (XSPICE): 6809E 2 MHz write, strobe LOW Q-rise .. E-fall
(375 ns), CPU data valid 200-405 ns, 74LS240 25 R / 3.4 V, ribbon 1 R / 120 pF, SR2 4.7 k, 74HCT240 25 ns, 74HCT574 20 ns.

| pin | function / direction / polarity / timing | evidence | deck / check | result |
|---|---|---|---|---|
| 1 | SW COL 1 (relay-option switch strobe), N/C on the -3 board | [SCH1] "NOT USED IN A-12697-3" | NET nc | NET |
| 2 | "NC" on sheet 1 | [SCH1] | NET nc | NET |
| 3 | SW ROW 1, N/C | [SCH1] | NET nc | NET |
| 4 | looped to 6 on the OEM; ground here | [SCH1] | NET GND | NET |
| 5 | SW ROW 2, N/C | [SCH1] | NET nc | NET |
| 6 | ground | [SCH1] | NET GND | NET |
| 7 | /LMP ROW -> CLK of U10-U13 (74HCT74), ~370 ns LOW, latch on the rising edge | [SCH2], [FW] lamp.c | ribbon `t_setup` 145 ns >= 20, `t_hold` 154 ns >= 5 (the 74HCT240 delay and the 4.7 k ribbon pull-up lengthen the hold) | PASS |
| 8 | /LMP COL -> U18 | [SCH2], [SCH-CPU] | ribbon; lamp_strobe | PASS |
| 9 | /SOL 2 -> U3 = sol 17-24 (0x3FE2) | [SCH3] traced, [PM] | NET U3-11; flasher | PASS |
| 10 | /SOL 4 -> U5 = sol 1-8 (0x3FE1) | [SCH3], [SCH-CPU] | NET U5-11; sol_high | PASS |
| 11 | /SOL 3 -> U4 = sol 9-16 (0x3FE3) | [SCH3] | NET U4-11; sol_low, sol_hold | PASS |
| 12 | /SOL 1 -> U2 = sol 25-28 (0x3FE0) | [SCH3], [SCH-CPU] | NET U2-11 | PASS |
| 13 | /TRIAC -> U1 (0x3FE6) | [SCH1] | NET U1-11; gi_gate, gi_dim | PASS |
| 14 | ground bus | [SCH1] | NET GND | NET |
| 15-29 odd | D7..D0 **ACTIVE LOW** (CPU 74LS240 U12) -> SR2 pull-ups -> U9 74HCT240 -> true bus -> 74HCT574 / 74HCT74 D inputs; register bit 1 = output on | [SCH-CPU], [SCH1-3], [OPS], [PM]/[FW] | ribbon `rib_low` 0.03 V, `rib_high` 3.44 V, `g_w1` 4.54 V ON, `g_w0` 0.012 V OFF, `out_w0` 71.1 V | PASS |
| 16-30 even | ground bus | [SCH1] | NET GND | NET |
| 31 | BLANKING, open-collector from the CPU, HIGH = every latch tri-stated, SR1 4.7 k (OEM R227 4.7 k) | [SCH1-3], [PW], [SCH-CPU] | powerup; ribbon `ioe_blank` 1.8 nA, `blank_unplug` 5.0 V | PASS |
| 32 / 33 | SW J2 / SW J1, N/C | [SCH1] | NET nc | NET |
| 34 | ZERO CROSS, board -> CPU (ASIC pin 71), 60 Hz square wave | [SCH1], [PS-ZC] | zero_cross, gi_dim - section 3 | PASS |

## 2. BLANKING behaviour

| case | expected | evidence | deck / check | result |
|---|---|---|---|---|
| power-up with random latch content, +5 V soft-start, BLANKING high for 200 ms | no coil / string / column current | [FW], [PW] D19 | powerup `icoil_blank` 13 nA, `istr_blank` 10 uA, `icol_blank` 0.1 nA, `vgate_blank` 0.1 mV, `blank_min` 5.0 V | PASS |
| release with the latches holding 1, then a write of 0 | outputs follow | [FW] | powerup `icoil_on` 16.6 A, `istr_on` 6.6 A, `icol_on` 5.3 A, `icoil_after` 2.5 nA, `icol_after` 0.1 mA | PASS |
| reset / watchdog re-assertion during a coil pulse | coil cut, decays through the tie-back | [PW-RST], [FW] | modelled in the modern suite (powerup brownout case, same MOSFET class, 37 uA after 13 ms); this board's tie-backs are S3M | PASS (by the modern deck) |
| BLANKING high with a latch holding 1 | tri-state wins | [SCH] | ribbon `ioe_blank` 1.8 nA | PASS |
| ribbon unplugged | BLANKING to Vcc via SR1, data read 0 via SR2, strobes held high via SR1 | [SCH1] | ribbon `blank_unplug` 5.0 V, `ioe_unplug` 1.1 nA | PASS |
| rows during blanking | columns off + REF_1V4 pulled low (U6B) | [SCH2] | powerup `icol_blank` with a row randomly ON | PASS |

## 3. ZERO CROSS (J113-34)

| item | expected by the CPU | evidence | deck / check | result |
|---|---|---|---|---|
| waveform | **60 Hz square wave, HIGH while the F113-fused 9 VAC leg is positive, one edge per zero crossing** (the ASIC/PinMAME count 120/s = both edges) | [SCH1] 600 dpi: D38 sample -> U6A **pin 7 (+)**, reference pin 6 (-); D3 -> U6C pin 8 (-), reference pin 9 (+); **[PS-ZC]** TP4 "~8100 uS, close enough to 8.33 ms for 60 Hz", dimming lost below ~90 us; [PM] latched flag 120/s | zero_cross (corrected detector): `zc_period` 16.67 ms, `zc_high_time` 7.31 ms, `zc_rise_offset` +0.53 ms, `zc_fall_offset` -0.50 ms, `zc_rise_time` 4 us, `zc_high` 5.0 V, `zc_low` 0.16 V, `za_min` -0.23 V (LM339 range), `i_r197_pk` 0.9 mA | PASS |
| firmware use | delay N x 1.024 ms after each edge, held or pulsed triac bit | [FW], [PM] | gi_dim (section 9) | PASS |
| missing ZERO CROSS | firmware flags it / G.I. runs undimmed; board side safe | [FW] ac.c, [PW] | N/S - firmware behaviour | N/S |
| earlier design (120 Hz active-high pulse, samples summed from the 9.8 VAC winding) | wrong: 240 edges/s for an edge-counting ASIC | [PS-ZC] | **corrected 2026-09-06** (section 17) | - |

## 4. Power rails

Fuse I2t [LF]: 239 5 A 302.836 A2s (F111, F113, F106-F110), 217 8 A 198.16 A2s (F114), 239 3 A 129.51 A2s (F116, F103-F105), 239 0.75 A
5.425 A2s (F115); only the 239 7 A (F112) could not be retrieved - the 3AG 313 7 A value 347 A2s stands in (the inrush result is 1.9 % of it).
Limits 20 % of melting (`docs/THERMAL_AND_PROTECTION.md` section 4).

| rail | winding -> fuse -> bridge -> filter | load case | deck / check | result |
|---|---|---|---|---|
| "+50V" (~70 V) | 51.4 VAC -> F112 7 A -> BR3 GBPC3510 -> 2 x 2200 uF/100 V, bleeder 2 x 15 k | AE-23-800 40 ms; six coils; hold; high line | psu `v50_idle` 69.2 V, `v50_max` 69.4 V, pulse 41.6 avg / 35.5 min V, `icoil_max` 13.1 A; psu_maxload 37.8 A -> 22.4 V, `ibr50_peak` 37 A; sol_hold 4.8 A 100 % / 3.2 A PWM; inrush `ipk_f112` 53 A, `i2t_f112` 6.7 A2s (limit 70), `v50_final` 70.4 V | PASS |
| +20 V flashers (interlocked winding) | 16 VAC -> F111 5 A -> **D109-D112 Schottky bridge** -> C11 10000 uF | 4 A burst; 8 cold flashers; 88 % | psu `v20_min` 17.8 V; psu_maxload `v20_min` 12.8 V, `ibr20_peak` 38 A; inrush 60 A / 5.5 A2s (1.8 %) | PASS |
| +18 V lamps + the +12 V digital buck | 13.3 VAC -> F114 8 A fast (217) -> **D101-D104 STPS20M100S Schottky bridge** -> 2 x 10000 uF | 2.8 A + 1 A; all lamps + 0.75 A; 88 % | psu `v18_avg` 15.3 V, ripple 1.1 V; psu_maxload `v18_min` 13.5 V, `ibr18_peak` 24.6 A; psu_brownout `v18_min` 11.7 V; inrush 71 A / 10.5 A2s (5.3 % of 198.2) | PASS |
| +5 V raw -> +5 V (**set point 5.10 V**, 11.3 k / 2.1 k 0.1 %) | 9 VAC -> F113 5 A -> **D105-D108 Schottky bridge** -> C5 10000 uF -> TPS54360B (118 k / 29.4 k: 5.9 / 5.5 V) | 3 A; 88 % at 3 A; 1 -> 3 A step | psu `vin5_min` 9.97 V, `v5_min` 5.10 V, `v5_cpu_worst` 4.86 V (3 A through 80 mOhm, > 4.70 V MC34064 max); psu_brownout `vraw_min` 8.28 V (> 6.0), `v5_min` 5.10 V; buck_5v 5.105 V, 5.00 V undershoot, 5.19 V overshoot (< 5.20), `il_peak` 3.66 A (< 4.5 A limit); inrush 55 A / 2.8 A2s | PASS |
| +12 V digital (J114) | +18 V -> TPS54360B U21 (130 k / 20 k: 8.8 / 8.4 V) -> F115 3/4 A -> J114-1,2 (OEM 7812 from +18 V) | 1 A / 0.75 A; all lamps; 88 % | psu 12.00 V; psu_maxload `v12_min` 11.0 V; psu_brownout 9.51 V; buck_12v 11.80 V undershoot on 1 -> 2 A from 13.5 V | PASS |
| +12 V power (J116/J117/J118) | 9.8 VAC (12.47 measured) -> F116 3 A -> **D113-D116 Schottky bridge** -> C30 10000 uF, unregulated | 2.5 A; 88 %; unloaded; nominal winding | psu_12vu `v12u_min` 11.6 / avg 12.2 V / ripple 1.2 V, `ibr5_rms` 4.1 A, `v12u_max_unloaded` 16.7 V (25 V part), nominal-winding bound 10.6 V; psu_brownout 10.1 V; psu_maxload `ibr12_peak` 8.2 A; inrush 36 A / 1.9 A2s (1.5 % of 129.5) | PASS |
| G.I. strings | J115-2..6 -> F106-F110 239 5 A -> strings -> triacs (MT1 on the GI_RET bus -> J115-7..12, W1 to GND) | cold start; 4.5 A rms | gi_string `ipk` 38.8 A, `i2t_f106` 9.2 A2s (limit 60), `irms_ss` 4.54 A, `p_triac` 3.9 W | PASS (thermal: 9.6) |
| CPU reset threshold | +5 V > 4.6 V (MC34064) always | [PW] | psu_brownout `v5_min` 5.00 V, buck_5v `vout_step_min` 4.90 V | PASS |

## 5. Output connectors

| connector | pins (NET) | expected | deck / check | result |
|---|---|---|---|---|
| J107 | 1-3 +50V_F103/F104/F105, 6 +20V | 3 A S.B. per branch (239 3 A), ~70 V | psu / sol decks; per-branch fuse N/S (pulse I2t ~8 A2s vs ~200 A2s melting) | PASS / N/S |
| J106-5 | +20V backbox flashers | | psu_maxload | PASS |
| J114 | 1,2 +12V_F; 3,4 +5V; 5,7 GND | CPU, Fliptronic, 8-driver | psu, buck decks | PASS |
| J116 / J117 / J118 | 2 +12VU, 3 GND, 4 +5V | [SCH1] +12 V POWER / +5 V DIGITAL | psu_12vu | PASS |
| J130 / J127 / J126+J125 / J122+J124 | solenoid / flasher / GP outputs, J122-5,6,8,9 tie-back cathodes | 70 V, 16.6 A HP / 6.5 A LP / 6.6 A flasher inrush | sol_high, sol_low, sol_hold, flasher | PASS |
| J115 | 1 GND, 2-6 GI1/GI4/GI2/GI3/GI5 hot, 7/8/10/11/12 GI_RET | [SCH1]; pin-to-string order not readable | gi_gate / gi_string; order N/S | PASS / N/S |
| J104 | 1 ACSOL_A_F, 2 ACSOL_B, 4 AC16_A_F, 5 AC16_B | [SCH1] fused legs (corrected) | NET | NET |
| J105 | relay-switched flipper AC (DNP) / ACSOL_B | OEM J105 = J104; N/C on Fliptronic games | N/S (DNP) | N/S |
| J103 | 1,2 GND | 8-driver ground | NET | NET |
| J111 | 1 GI_BIT5, 2 GI_BIT6, 3 FLIP_RLY_L, 5 GND | OEM T5-T7 GPIO (N/C on STTNG) | NET | NET |
| J108/J109/J110/J123 | N/C | relay-option / spares | N/S | N/S |

## 6. Lamp matrix

| item | expected | deck / check | result |
|---|---|---|---|
| strobe timing 2 ms / 16 ms | [FW] lamp.c | lamp_strobe (thermal #555 filaments, 400 ms) | PASS |
| column IRFR5305 | 8 A peak / 0.67 A avg, 0.43 V, 0.23 W, +12 C | lamp_strobe `icol_peak`, `vcol_drop`, `pcol_avg`, `tj_rise_col` | PASS |
| row IRLR024N + 0.22 R | 1.0 A peak / 0.51 A avg, 0.08 W, +4 C; drop 0.62 V | lamp_strobe, lamp_matrix `vrow_on` | PASS |
| lamp voltage | 6.17 V rms on an 18 V stiff rail (OEM Darlington path 5.53 V) - the modern suite's loaded-rail case gives 4.93 V | lamp_strobe `vlamp_rms`, `vlamp_old_rms` | PASS |
| over-current shutdown | fault 8.4 A, cleared 0.16 ms after the strobe, 2.5 mA after, trips again next strobe | lamp_matrix_trip | PASS |
| no false trips | `vsense_max` 0.19 V, `clr_min` 5.0 V, cold first strobe 2.3 A | lamp_strobe | PASS |
| blanking of rows / columns | TBD62083A input pull-down keeps the columns off while U18 is tri-stated | powerup `icol_blank` | PASS |
| polarity chain | ribbon LOW -> U9 HIGH -> U18 Q HIGH -> TBD62083A -> P-MOSFET on | ribbon (same latch/inverter), lamp_matrix `vgs_col` -10.8 V | PASS |

## 7. Solenoid groups

| group | register -> strobe -> latch -> switch -> connector | pattern | tie-back | deck / check | result |
|---|---|---|---|---|---|
| sol 1-8 | 0x3FE1 -> J113-10 -> U5 -> IRLR3110Z -> J130; F105 | AE-23-800 40 ms | S3M | sol_high 16.6 A, 0.31 V, 5.2 W / 0.185 J, +2.8 C per pulse, +52 C at 20 % duty | PASS |
| sol 9-16 | 0x3FE3 -> J113-11 -> U4 -> IRLR3110Z -> J127; F104 | AE-26-1200 pulse; 100 % hold; 50 % PWM | S3M | sol_low 6.5 A, 0.12 V, 0.77 W; sol_hold 4.8 A / 0.43 W / +21 C, PWM 3.2 A avg, diode 1.28 A avg (S3M 3 A) | PASS |
| sol 17-24 flashers | 0x3FE2 -> J113-9 -> U3 -> IRLR3110Z -> J126/J125; +20 V | 60 ms | S1M to +20V | flasher 6.6 A inrush, 1.1 A, 20 mV; psu_maxload | PASS |
| sol 25-28 | 0x3FE0 -> J113-12 -> U2 -> IRLR3110Z -> J122/J124; F103 | as LP | S3M, cathodes on J122 | sol_low / sol_hold; NET | PASS |
| +50 V sag | 41.6 V avg / 35.5 V min during the 40 ms pulse (0.6 R winding model) | psu | | PASS |
| six coils at once | 22.4 V avg, bridge 37 A (informational) | psu_maxload | | PASS |

## 8. Flashers - see 7.3 and the +20 V rows.

## 9. G.I. strings

| item | deck / check | result |
|---|---|---|
| 9.1 gate drive >= 50 mA (Q IV) | gi_gate `ig_peak` 78 mA, `i_latch` -3.7 mA, `p_npn` 0.12 W | PASS |
| 9.2 dimming levels (real detector + ASIC edge model) | gi_dim: level 0 `l0_rms` 4.68 A; level 3 pulsed +-6.62 A; level 7 pulsed `l7p_max` 1.35 / `l7p_min` -3.70 A, `l7p_rms` 0.69 A | PASS |
| 9.3 both half-cycles, no DC | `l0_asym` 2e-9, `l3h_asym` 0.11 (edge offsets, same as the OEM) | PASS |
| 9.4 held bit re-fires at the crossing (OEM identical) | `l7h_max` 6.62 A - informational | PASS |
| 9.5 fuse F106 | gi_string 9.2 A2s = 3 % of 302.8 A2s; 4.54 A rms steady | PASS |
| 9.6 triac thermal | gi_gate `p_triac` 3.27 W, gi_string 3.91 W at 4.54 A rms; **Boyd 7019BG** bolt-on heatsink (11.0 C/W catalogue, 12.65 derated + 2.5 j-c + 0.5) -> `tj_rise_sink` 51 / 61 C (Tj 101 / 111 C at 50 C), `rth_sa_needed` 20 C/W; the old 577002 clip is a 32 C/W part (`tj_rise_clip` 114 C, informational); fits all five positions on the tab side (`docs/THERMAL_AND_PROTECTION.md` section 2) | PASS |
| 9.7 return path | GI_RET bus -> J115-7..12, W1 0 R to logic ground (OEM J115-1 "GND REF") | NET | NET |

## 10. Flipper relay option / Fliptronic pass-through

J104-1/2 = 51 VAC after F112 / return, J104-4/5 = 16 VAC after F111 / return (corrected, [SCH1]); relay K1 / U7 / U8 / J105 / J109 / J110
DNP ("NOT USED IN A-12697-3"); flipper coils on the Fliptronic board (0x3FD4, F901-F904).  Result: NET / N/S.

## 11. Coin door / DMD / playfield +12 V (J116-J118)

Rows 4.6 / 5.4: 10.5 V min at 2.5 A, 9.1 V at 88 % mains, 15.9 V unloaded, +5 V on pin 4; the coin-door interlock [SCH-PW] cuts only the
16 VAC and 51 VAC windings, so the switch matrix (+12 V digital from +18 V) and the +12 V power loads stay alive with the door open.

## 12. 8-driver board (J107-1, J103, J114)

+50 V continuous-duty branch F103, ground J103, +5 V / +12 V digital from J114 [OPS] p.3-24: NET.

## 13. CPU +5 V supply and reset threshold

**5.10 V set point** (11.3 k / 2.1 k, 0.1 %; thermal doc section 9): 5.09 V at 3 A (`buck_5v`), 5.00 V minimum on a 1 -> 3 A step, 4.86 V at
the CPU with 3 A through 80 mOhm of board + harness (4.79 V worst case, above the 4.70 V MC34064 maximum), 5.17 V maximum at no load (< 5.20 V),
holds at 88 % mains at 3 A (raw 8.28 V > 6.0 V worst-case UVLO stop).  Real +5 V budget (estimate 2.2-2.6 A) unpublished: N/S.

## 14. Thermal limits

| part | deck / check | result |
|---|---|---|
| IRLR3110Z DPAK solenoid switches - as routed: tab pad only, 38-64 mm2 of 1 oz copper, no pour -> datasheet minimum-footprint **110 C/W** (the 50 C/W / 1 sq. in. assumption was wrong) | sol_high `tj_rise_pulse` 2.8 C, `tj_rise_10pct` 57 C (Tj 107 C), `tj_rise_20pct` **113 C** (Tj 163 C: above the 125 C target, below Tjmax 175 - limit 125), `tj_rise_20pct_pour` 62 C with the recommended >= 300 mm2 drain pour; sol_low 0.77 W; sol_hold `tj_rise_hold` 47 C, `tj_rise_pwm` 29 C | PASS (20 % duty pour = next-revision item, `docs/THERMAL_AND_PROTECTION.md` 3.4) |
| IRFR5305 columns / IRLR024N rows (110 C/W as routed) | lamp_strobe `tj_rise_col` 26 C, `tj_rise_row` 9 C | PASS |
| BTA16-600C triacs | gi_gate / gi_string `tj_rise_sink` 51 / 61 C with the 7019BG | PASS (9.6) |
| TPS54360B bucks | `il_peak` 3.65 / 3.23 A < 4.5 A current limit; dissipation ~1 W (datasheet) | PASS / N/S |
| **Schottky bridges D101-D116** (4 x STPS20M100S 100 V / 20 A D2PAK per rail, cooled by 2-15 cm2 of 2 oz copper per diode: +18 V 15 cm2, +20 V 4 cm2, +5 V raw / +12 V power 2 cm2 - thermal doc section 8) | bridge_loss: per-diode loss 0.425 IF(AV) + 0.0088 IF(RMS)^2 (ST DS6169); `tj_18a` **107 C** with all 64 lamps lit (1.92 W per diode, was 208 C with the GBJ1510), `tj_18b` 74 C, `tj_20a` 73 C (102 C at the 5 A fuse rating), `tj_5a` 67 C, `tj_12a` 75 C (80 C at 3 A); IFSM 350 A vs inrush peaks <= 71 A; reverse voltage <= 26 V vs 100 V | PASS (Tj <= 110 C) |
| GBPC3510W BR3 under a **Boyd 6224BG** basket (9.4 C/W) | bridge_loss `tj_50a` 117 C at 3 A (sustained limit 3.4 A); psu_maxload `ibr50_peak` 37 A vs 400 A | PASS |
| **GI_RET return bus** (found during the track audit) | 22.7 A rms of string return through one 1.6 mm track and one via between J115 and the triacs (`docs/THERMAL_AND_PROTECTION.md` 5.3) | **DEFECT - PCB revision before incandescent G.I. use** |

## 15. Fuse / bridge surge ratings

`inrush` (Schottky bridges): F113 2.82 / 302.8, F114 10.5 / 198.2, F111 5.46 / 302.8, F116 1.94 / 129.5, F112 6.66 / (347 stand-in) A2s = 0.9-5.3 % of melting; peaks
55 / 71 / 60 / 36 / 53 A vs STPS20M100S IFSM 350 A and GBPC3510 400 A.  `gi_string`: F106 9.19 / 302.8 A2s (3.0 %); F103-F105 3 A: 11 A2s per AE-23-800 pulse = 8.5 % of 129.5.
Connector pins: every KK 396 pin <= 74 % of its 7 A rating in the sustained design cases (thermal doc section 5); the wire-lead
**GBPC3510W-E4/51** replaces the faston-lug GBPC3510-E4/51 that could not have been fitted to the BR3 footprint.

## 16. Contradictions between the projects and their resolution

See section 16 of the modern matrix (identical table).  For this board the consequences were: the ZERO CROSS detector was wrong (rewired),
J104 was unfused (rewired), `gi_gate` had no registered checks (added), `gi_dim` used an ideal 120 Hz reference (replaced by the real
detector + ASIC edge model), and the 313-series I2t values quoted here for the OEM fuses are now the datasheet ones (3 A 200, 5 A 140,
7 A 347, 3/4 A 7.16; 312 8 A 166 A2s - the 198 A2s belongs to the 217 8 A used on this board).

## 17. Design errors found and changes made (schematic regenerated, ERC 0)

| error | evidence | change in `tools/design_cost.py` | netlist effect |
|---|---|---|---|
| ZERO CROSS produced a 120 Hz active-high pulse (both legs of the 9.8 VAC winding summed into the inverting input) instead of the OEM 60 Hz square wave | [SCH1] pin numbers 7(+)/6(-), [PS-ZC] TP4 8.1 ms pulses | R197 now samples the F113-fused 9 VAC leg (new global net `AC9_AF` from the +5 V rect_block), **R198 DNP** (its other end stays on AC9_B), sample on U6A **pin 5 (+)**, reference on pin 4 (-) | `AC9_AF`: BR2-3, F113-2, R197-1; `ZC_SAMPLE`: R197-2, R198-2, R254-1, C21-1, U6-5; `ZC_REF`: R206-2, R255-1, U6-4 |
| J104 fed from the unfused 51 VAC winding | [SCH1] | J104-1 `ACSOL_A_F`, 2 `ACSOL_B`, 4 `AC16_A_F`, 5 `AC16_B` (fuse outputs as global nets, `fused_gl` parameter in rect_block) | J104-1 joins F112-2 / BR3-3; J104-4 joins F111-2 / BR4-3 |

No footprint was added or removed (R198 keeps its 0805 pad, DNP); the placed, unrouted PCB only needs the rat's nest refreshed for the
changed nets (R197-1, J104-1/4/5, U6-4/5 swap).  `.scratch/nets.json` was backed up to `.scratch/verif/nets_before.json`.

## 18. Copper and routing (2026-09-07)

| item | evidence | check | result |
|---|---|---|---|
| 18.1 bus resistance | `copper_resistance.py` on the finished board | +5 V C4 -> J114 52 mOhm (3 A: 0.16 V; SPICE section 13 margin assumed 80 mOhm), +18 V 14.8 mOhm (8 A: 0.12 V), +12 V power 21 mOhm, +20 V 5 mOhm, G.I. string 2.8 mOhm, G.I. return 4.0 mOhm | PASS |
| 18.2 current density | 2 oz outer copper, Bus 3.0 mm (IPC-2221 ext. ~12 A at 20 C rise), Heavy 5.0 mm (~22 A), Coil 1.6 mm (~7.5 A), no high-current net on the 1 oz inner layer (router classes confined to F.Cu/B.Cu) | audit `copper_audit.py`: +18V/+50V/+20V/+5V/+12VU/AC*/GI* have 0 mm on In2.Cu except necked pad entries | PASS |
| 18.3 DRC | `kicad-cli pcb drc --severity-all` with the project net classes (Bus/Heavy/HV 0.4 mm, Drive/Coil 0.3, Default 0.2) | 0 violations, 0 unconnected (`output/reports/drc.rpt`) | PASS |
| 18.4 ERC / net-list parity | `output/reports/erc.rpt`; `update_nets.py` diff of the routed board against the schematic net-list | 0 ERC errors; 0 pad-net differences, no footprint missing on either side | PASS |
