# Modern vs cost-optimised board - SPICE comparison

| quantity | modern board | cost board | note |
|---|---|---|---|
| +5V minimum under full load | 5 V | 5 V | modern: 5 A TPS54560B / cost: 3 A TPS54360B |
| +5V buck input minimum (headroom, buck needs ~5.6 V) | 7.541 V | 8.336 V | 15000 uF / 5 A -> 10000 uF / 3 A, GBU8J instead of GBPC3510 |
| +12V digital minimum (buck from the +18V lamp rail, 2.8 A of lamps) | 12 V | 12 V | both boards now feed U21 from +18V as the original 7812 does (the +20V rail is cut by the coin-door interlock); the modern board was corrected 2026-09-06 |
| +20V minimum during the flasher burst | 16.78 V | 16.47 V | 15000 uF -> 10000 uF, GBJ1510 instead of GBPC3510 |
| +18V lamp rail average (5 ohm load) | 13.48 V | 13.76 V | 2 x 15000 uF -> 2 x 10000 uF, GBJ1510 |
| +18V ripple p-p | 0.6483 V | 0.9925 V |  |
| "+50V" rail idle | 67.67 V | 69.21 V | both suites use the real 51.4 VAC winding (~70 V) |
| +50V average during a coil pulse | 45.43 V | 41.64 V | modern: 4 ohm coil, 0.35 R + 0.5 mH winding model; cost: AE-23-800 (4.2 ohm), 0.6 R winding model |
| +50V minimum during the pulse | 39.95 V | 35.53 V |  |
| peak 4-ohm coil current in the PSU sim | 13.45 A | 13.07 A |  |
| high-power driver drop while ON | 0.09988 V | 0.3106 V | IRLB4030 4.3 mOhm -> IRLR3110Z (18 mOhm modelled at 4.6 V), both on the 70 V rail |
| high-power driver dissipation while ON | 1.745 W | 5.154 W | TO-220 -> DPAK; pulsed duty keeps the average low |
| high-power coil current | 17.48 A | 16.59 A | modern: 4 ohm; cost: AE-23-800 4.2 ohm; both on 70 V |
| low-power driver drop while ON | 0.04434 V | 0.1194 V |  |
| low-power driver dissipation while ON | 0.3446 W | 0.7725 W |  |
| current the latch must sink/source per output | 0.0004536 A | 0.0004536 A | unchanged (MOSFET gate) |
| flasher driver drop | 0.006334 V | 0.02035 V |  |
| lamp column driver drop | 0.1994 V | 0.1205 V | IRF9Z34N 100 mOhm -> IRFR5305 65 mOhm (better) |
| lamp row driver drop incl. 0.22 R sense | 0.5104 V | 0.6228 V | IRLZ44N 22 mOhm -> IRLR024N 65-80 mOhm |
| column MOSFET Vgs | -10.79 V | -10.8 V | same 1k/1.5k divider |
| row over-current shutdown time | 0.03308 s | 0.03316 s |  |
| row fault current before shutdown | 15.09 A | 8.365 A | higher Rds(on) limits the fault current a little |
| row current after shutdown | 0.022 A | 0.002529 A |  |
| triac gate current | 0.07841 A | 0.07841 A | unchanged |
| ZERO CROSS period | 0.01667 s | 0.01667 s | both boards: 60 Hz square wave with one edge per crossing (A-12697 U6A pin 7 = D38 sample); the cost board earlier produced a 120 Hz pulse, corrected 2026-09-06 |
| ZERO CROSS time HIGH per cycle | 0.007392 s | 0.007306 s | real TP4: ~8.1 ms (Pinside Arduino measurement) |
| ZC edge delay after the true crossing | 0.0004704 s | 0.0005266 s | modern: two half-wave detectors, 27k feedback; cost: one half-wave sample, no feedback |
| +5V buck output ripple (switching model) | 0.02396 V | 0.02705 V | TPS54560B 17 A/V -> TPS54360B 12 A/V, recomputed compensation |
| +5V buck undershoot on a load step | 4.801 V | 4.898 V | modern: 1 -> 5 A step; cost: 1 -> 3 A step |
| +5V buck peak inductor current at full load | 6.499 A | 3.65 A | cost: must stay below the 4.5 A minimum current limit |
| +12V buck undershoot on a 1 -> 2 A step | n/a  | 11.8 V | cost: from 13.5 V (+18V rail at full lamp load) |
| coil current while BLANKING is high at power-up | n/a  | 1.312e-08 A | cost-board machine-level deck |
| RMS lamp voltage with 2 ms strobes | 4.932 V | 6.174 V | cost-board machine-level deck (original Darlington board: 5.53 V) |
| G.I. string RMS at level 7 (8 us gate pulse) - modern deck | 0.6801 A | n/a  | the cost deck gi_dim now runs the same machine-level model with its own detector (l7p_rms below) |
| G.I. string RMS at level 7 (8 us gate pulse) - cost deck | n/a  | 0.688 A |  |
| triac conduction loss at a full 18-lamp string | 3.265 W | 3.265 W | same BTA16-600C; the specified 25 C/W clip heatsink fails the Tj check on both boards (tj_rise_clip) |
| G.I. string cold-start I2t through F106 | 9.188 A2s | 9.188 A2s | modern: 313 5 A (140 A2s); cost: 239 5 A (302.8 A2s) |
| switch-on I2t through F112 (+50V, 4400 uF) | 9.911 A2s | 6.663 A2s | modern: 313 7 A (347 A2s) at 78 V peak; cost: 239 7 A (stand-in 347 A2s) at 72.7 V peak |
| switch-on I2t through the fast 8 A F114 | 10.88 A2s | 7.07 A2s | modern: 312 8 A (166 A2s, 2 x 15000 uF); cost: 217 8 A (198 A2s, 2 x 10000 uF) |
| data setup at the latch before the strobe edge | 1.702e-07 s | 1.438e-07 s | modern: 74HCT564 direct; cost: through the 25 ns 74HCT240 |
| data hold after the strobe edge | 3.529e-08 s | 1.544e-07 s | cost: the 74HCT240 delay and the 4.7 k ribbon pull-up lengthen it |
| +12V power (J116/J117/J118) minimum at 2.5 A | 10.68 V | n/a  | modern: C30 15000 uF; cost: 10000 uF - both GBU8J, both the OEM topology now |

Both suites: ngspice transient runs, generic functional models (see each project's `tools/spice/`).  Modern results: `../wpc_power_driver_modern/output/spice/RESULTS.md`; cost board: `output/spice/RESULTS.md`.
