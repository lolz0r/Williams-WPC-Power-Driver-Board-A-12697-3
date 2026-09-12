# Historical design narrative — superseded

Use [RELEASE_STATUS.md](RELEASE_STATUS.md) for current parts, limits and verification.
The following narrative is retained as development history, not build instructions.

# WPC Power Driver Board - cost-optimised modern version

**Current revision (2026-09-08): [release status and verification evidence](RELEASE_STATUS.md).**
The schematic/PCB mismatches have been repaired and the board now specifies **2 oz finished outer / 1 oz inner copper**.
Updated manufacturing files and native 3D renders are in `output/release-candidate/`.
**This is an unreleased engineering candidate:** regulator reverse-current, thermal and physical qualification gates remain open.
The complete review archive is `output/wpc-sttng-engineering-candidate.zip`; see
[reproduction instructions](VERIFICATION.md) and [component sourcing](SOURCING_REVIEW.md).
J106 and J111 differences prevent a universal drop-in compatibility claim.

The remaining sections document the original cost-reduction design and earlier revisions;
component choices, dimensions and verification claims below are superseded where the current release status differs.

A cost-reduced variant of `../wpc_power_driver_modern/` (the modern-component functional replacement for the Williams WPC Power Driver
Board **A-12697-3**).  Same 449.2 x 272.9 mm outline, every connector, fuse, bridge rectifier, big capacitor and mounting hole in its
original position and with the original pin-outs, so it still drops into a WPC cabinet with the original harness.  The design goal was a
**quantity-100 parts cost of about 105-115 USD** with **no Chinese-brand parts** (DigiKey/Mouser-stocked Infineon, TI, Nexperia, Vishay,
Diodes Inc, Toshiba, ST, Rubycon, Nichicon, Panasonic, Molex, 3M, Littelfuse, Keystone, Bourns, Yageo, Samsung, Lite-On) and **robust
margins kept** (SPICE-verified, see below).

**Machine-level review (2026-09-06)**: the board was then checked against the real WPC interface of a *Star Trek: The Next Generation*
machine - the WPC schematic manual 16-9834.2, the STTNG operations manual, pinwiki, PinMAME and FreeWPC (`docs/WPC_INTERFACE_FINDINGS.md`,
every fact with its source).  Four of the design's interface assumptions were wrong and have been corrected: the ribbon data bus is
**active low**, the **J113 pin-out** was invented, the **"+50 V" rail is ~70 V DC**, and the **+12 V topology** (regulated from +20 V through the
3/4 A fuse to everything) did not match the machine.  See "Interface findings and corrections" below.

Everything is script-generated with the same tool-chain as the modern board: `python3 tools/gen_project.py` (schematics, `.kicad_pro`,
netlist), `NO_ZONES=1 python3 tools/gen_pcb.py` (placed board), `python3 tools/bom_report.py` (BOM + cost roll-up),
`flatpak run --command=python3 org.kicad.KiCad tools/spice/run_all.py` and `python3 tools/spice/compare.py` (SPICE suite + comparison).
Design: `tools/design_cost.py`, sourcing table: `tools/sourcing.py`, placement: `tools/placement_cost.py`.

## What changed versus the modern board, and why

| block | modern board | cost board | why / effect |
|---|---|---|---|
| solenoid / flasher MOSFETs (28) | IRLB4030PBF TO-220 (100 V, 4.3 mOhm) | **Infineon IRLR3110ZTRPBF** DPAK (100 V, 14 mOhm @10 V / 16 mOhm @4.5 V, logic level), same 100 R gate / 10 k pull-down / SMA-SMC tie-back | reel-priced SMD part, ~40 % of the modern MOSFET cost; drop 0.23 V instead of 0.07 V at 12 A (still 7x better than the 1993 TIP36C) |
| lamp rows (8) | IRLZ44NPBF TO-220 (22 mOhm) | **Infineon IRLR024NTRPBF** DPAK (55 V, 65 mOhm @10 V / 78 mOhm @5 V) | cheapest logic-level DPAK from an allowed brand that is in stock; row drop 0.62 V incl. the 0.22 R sense (was 0.51 V) |
| lamp columns (8) | IRF9Z34NPBF TO-220 (100 mOhm) | **Infineon IRFR5305TRPBF** P-DPAK (-55 V, 65 mOhm @-10 V) | cheaper and lower Rds(on): column drop 0.12 V (was 0.20 V) |
| bridges | 4 x GBPC3510 (35 A block) + GBU4J-BP (MCC) | BR3 +50 V: **GBPC3510W-E4/51** (wire leads) under a Boyd 6224BG basket heatsink; the +18 V, +20 V, +5 V raw and +12 V power bridges are **discrete Schottky bridges of four ST STPS20M100SG-TR** (100 V, 20 A, D2PAK) each: D101-D104, D109-D112, D105-D108, D113-D116 (2026-09-07 thermal review, `docs/THERMAL_AND_PROTECTION.md`) | a GBJ1510 block dissipated 15 W at full lamp load with no way to heat-sink it on the board; the Schottky bridge halves the loss and spreads it over four D2PAK tabs cooled by 2-10 cm2 pours; +0.5 V on every low-voltage rail |
| big electrolytics | 4 x 15000 uF / 35 V (Rubycon 25 x 45 mm) | C5, C6, C7, C11: **Rubycon 25USC10000MEFCSN25X25** (10000 uF / 25 V, 25 x 25 mm); C8/C32 2 x 2200 uF / 100 V kept | rails are 9-20 V so 25 V parts have the same 20-25 % margin the 35 V parts had at 20 V; one part number for all four |
| +5 V / +12 V bucks | 2 x TPS54560BDDAR (5 A) | 2 x **TI TPS54360BDDAR** (60 V, 3.5 A, same HSOP-8 pin-out); +5 V rated 3 A, +12 V 2 A; same SRP1265A-100M / B560C | the CPU/DMD/sound loads are < 3 A; feedback (10.5 k / 28 k over 2 k, Vref 0.8 V), RT (240 k -> 405 kHz) and compensation recomputed from the TPS54360B datasheet (below) |
| fuses | 3AG (6.3 x 32 mm), Littelfuse 313/312 + 102071 clips | **5 x 20 mm**: Littelfuse **239 series Slo-Blo** 0239007 / 0239005 / 0239003 / 0239.750 and **0217008** (8 A fast) in **Keystone 3517** clips; each fuse centred on the original 3AG position (see below) | clip + fuse cost roughly halves |
| test points TP1-TP9 | Keystone 5000 | plain 2.0 mm plated pads (`TestPoint_THTPad_D2.0mm_Drill1.0mm`), no purchased part | -9 parts |
| **interface corrections (machine-level review, see below)** | true data bus, invented J113 map, 36 VAC solenoid winding, +12 V buck from +20 V feeding J114-J118 via F115, active-low zero cross, triac MT1 grounded | **U9 74HCT240** data inverter + **SR2** pull-ups, real J113 map, 51 VAC / ~70 V decks with 2 x 15 k bleeder and S3M tie-backs on the coil groups, **+12 V digital buck from +18 V -> F115 -> J114 only**, **+12 V power (BR5 GBU8J, C30 10000 uF) -> J116/J117/J118**, active-high zero cross, **GI_RET** return bus with W1, J111 GPIO, TP6/TP8 names | +3.4 USD at qty 100; without them the board would have fired every coil on a 0x00 write, clocked the wrong groups and lost the switch matrix with the coin door open |
| everything else | | unchanged: 74HCT574 / 74HCT74 / LM339 logic, TBD62083A column driver, BTA16-600CRG triacs with MMBT4401 emitter-follower drive, all connectors and pin-outs, 0805 / 2512 passives, SMA / SMC / SOD-123 diodes, LEDs, relay option (DNP), 4-layer stack, netclasses | |

## Interface findings and corrections (machine-level review)

Full record with sources: `docs/WPC_INTERFACE_FINDINGS.md`.  Summary of what the machine really does and what changed:

| item | what the machine does (source) | design before | now |
|---|---|---|---|
| BLANKING (J113-31) | HIGH = every 74LS374 tri-stated (OC pin 1), pulled up on the driver board (R227 4.7 k), driven low by an open-collector 2N3904 on the CPU board only while the ASIC watchdog is kicked; on for ~1-3 s at power-up (LED D19) - pinwiki, schematic 16-9834.2 | HIGH = disabled on the 74HCT574 /OE, 470 R pull-up | unchanged polarity, SR1 = 4.7 k |
| J113 ribbon | 7 /LMP ROW, 8 /LMP COL, **9 /SOL 2 = sol 17-24, 10 /SOL 4 = sol 1-8, 11 /SOL 3 = sol 9-16, 12 /SOL 1 = sol 25-28**, 13 /TRIAC, 15-29 odd = D7-D0, 31 BLANKING, 34 ZERO CROSS; 1/3/5/32/33 = flipper-opto sense of the -1 board (N/C on -3), 2 N/C, other even = GND - schematic sheet 1 + 3 (wire-traced) | strobes on odd 1-13 in a guessed order, ZC on 33 | real map |
| data polarity | the CPU board drives the ribbon data through a 74LS240 (U12): **active low**; the driver latches take it directly (LOW = on through the PNP pre-drivers), only the column latch U18 re-inverts it (U9 74LS240 + ULN2803); firmware writes 1 = on (PinMAME, FreeWPC) | true bus into 74HCT574 (a 0x00 write would have turned all 28 MOSFETs on) | U9 = 74HCT240 inverts /D0-/D7 into the board's true bus, SR2 4.7 k pull-ups (OEM: SR1 470 R on the data lines) |
| zero cross (J113-34) | the D38 half-wave sample of the F113-fused 9 VAC leg on U6A pin 7 (+) against a 0.45 V reference (sheet 1 at 600 dpi; U6C on the other leg is redundant): **a 60 Hz square wave, HIGH while that leg is positive (~8 ms), one edge per crossing** - a real TP4 measures ~8.1 ms pulses (Pinside topic 22018); PinMAME's 120/s flag = both edges | active-low 1.3 ms pulse, then (wrongly) an active-high 120 Hz pulse | corrected 2026-09-06: R197 samples the fused 9 VAC leg (AC9_AF) into U6A + with the 0.26 V reference on -, R198 DNP -> 60 Hz square wave, 7.3 ms high, edges 0.5 ms after / before the crossing |
| solenoid supply | 51.4 VAC winding (STTNG measured 55.2 VAC unloaded): **"+50 V" is 70-75 V DC** (pinwiki TP6) | 36 VAC / 50 V in every deck | decks at 72.7 V peak: AE-23-800 draws 16.6 A, IRLR3110Z 0.31 V / 5.2 W per pulse (+2.8 C per pulse, +52 C at 20 % duty); bleeder 2 x 15 k 2512 (0.7 W); S3M tie-backs on sol 9-16 / 25-28 (PWM-held coils freewheel 1.3 A average); 100 V MOSFETs / diodes / capacitors keep >= 17 V of margin at the 83 V high-line peak; TP6 = +50 V, TP8 = +18 V as on the factory schematic |
| +12 V | regulated "+12 V digital" comes from the **+18 V lamp rail** (7812, F115 3/4 A) and feeds only J114 (CPU switch matrix, Fliptronic, 8-driver); **J116/J117/J118 pin 2 carry the unregulated "+12 V power"** (BR5, C30 15000 uF, F116) for motors, optos, coin door and DMD - STTNG's two gun motors sit on J118 - pinwiki, schematic, manual wire colours; the coin-door interlock kills +20 V and +50 V | buck from +20 V -> F115 -> J114 + J116/J117/J118 (the gun motors through a 3/4 A fuse; switch matrix dead with the coin door open) | U21 from +18 V -> F115 -> J114 only; BR5 = GBU8J, C30 = 10000 uF/25 V, +12VU -> J116/J117/J118 pin 2 (pin 4 = +5 V as on the original) |
| G.I. | hot ends J115-2..6 -> one fuse each -> strings; returns -> triac MT2, **MT1 -> J115-7/8/10/11/12 (winding return), J115-1 = GND REF** | MT1 and all return pins on the ground plane | GI_RET bus (5 x MT1 + 5 return pins) tied to logic ground by the 0 R link W1: the 25 A of string return current stays off the ground plane |
| lamp matrix timing | one column at a time, **2 ms per column, 16 ms frame** (FreeWPC lamp.c); bit = 1 selects the column / lights the row | 2 ms / 16 ms already used in the trip deck | new `lamp_strobe` deck (thermal #555 filaments): column DPAK 8 A peak / 0.23 W, row 1 A peak / 0.08 W, lamps see 6.17 V RMS (original Darlington board: 5.53 V, rating 6.3 V) |
| G.I. dimming | IRQ (976 Hz) writes the triac latch on and immediately off N ms after the crossing, level = 7 - N, the triac conducts to the next crossing (FreeWPC triac.c, PinMAME) | continuous gate drive only | new `gi_dim` deck: 5 us latch pulse -> 78 mA gate current -> string RMS 96 / 84 / 34 % at levels 6 / 4 / 1, both half-cycles (quadrant IV), no DC component |
| solenoid timing | 4 ms refresh slots, pulses of n x 4 ms, PWM holds 1/8..8/8 (FreeWPC sol.c); "most solenoids don't have a holding coil so the software simulates it by pulsing" (PinMAME) | 40 ms pulses | `sol_hold` deck: 100 % hold 4.8 A / 0.43 W (+21 C), 50 % PWM 3.2 A average / 0.27 W, diode 1.3 A average |
| J111 | G.I. latch bits T5-T7 on pins 1-3, key 4, GND 5 (GPIO, shot-clock drive on later games) | N/C | wired |
| +5 V load | CPU + DCS sound (J114) + DMD controller/display (J117) + Fliptronic + 8-driver: 2.2-2.6 A estimated, original LM323K rated 3 A behind a 5 A fuse | 3 A buck (4.5 A minimum current limit) | unchanged, 15-35 % margin over the estimate |

Agreement with the modern-board review: same conclusion on the active-low data bus (implemented there with 74HCT564 latches, here with one
74HCT240), on ZERO CROSS = pin 34, BLANKING = 31, data on 15-29, on the strobe map (7 / 8 / 9 / 10 / 11 / 12 / 13 - both generators agree since the
coordinator's re-read of J211) and on the data-line pull-ups.  The one disagreement that survived - the zero-cross waveform - was settled
2026-09-06 in favour of the modern board's reading (60 Hz square wave; see `docs/VERIFICATION_MATRIX.md` section 16) and this board was changed.

Still unverified / open before a first article: the J115 pin-to-string order (hot pins 2-6 / return pins 7-12 are certain, the order is
not - the manual's colour table is inconsistent), the 239-series 7 A melting I2t (313 value as stand-in; every inrush result is < 5 % of it),
the real +5 V and +12 V power currents of a given machine, the J111 GPIO polarity (N/C on STTNG), the D2PAK Rth on 2 oz copper (the ST curve
is for 35 um; the +18 V bridge diodes are estimated at ~120 C with all 64 incandescent lamps lit and ~75 C on an LED machine), and the
solenoid MOSFET drain copper (rated for <= 10 % duty of an AE-23-800; larger drain pours do not fit the 2 mm component spacing).

### Buck converter values (TPS54360B, datasheet SNVSB93 section 8.2.2)

gm(ea) = 350 uA/V, gm(ps) = 12 A/V (TPS54560B: 17 A/V), Vref = 0.8 V, current limit 4.5 A minimum / 5.5 A typical, fsw = 405 kHz with
RT = 240 k (Rt = 101756 x fsw^-1.008).  Output filter 2 x 330 uF Panasonic FR (45 mOhm each) + 10 uF = 670 uF / 22 mOhm.

| | fp_mod = Iout / (2 pi Vout Cout) | fz_mod = 1 / (2 pi Resr Cout) | fco = sqrt(fp_mod x fsw/2) (eq. 47) | Rc (eq. 48) | Cc (eq. 49) | Cp (eq. 50) | EN/UVLO divider |
|---|---|---|---|---|---|---|---|
| +5 V, 3 A (U20) | 142 Hz | 10.7 kHz | 5.3 kHz | 33.2 k | 33 nF | 470 pF | 118 k / 29.4 k: start 5.9 V, stop 5.5 V nominal (see "UVLO thresholds" below) |
| +12 V, 2 A (U21, input = +18 V lamp rail) | 40 Hz | 10.7 kHz | 2.8 kHz | 42.2 k | 100 nF | 390 pF | 130 k / 20 k: start 8.8 V, stop 8.4 V nominal |

The datasheet's other crossover option (eq. 46, geometric mean of modulator pole and ESR zero: 1.2 kHz / 650 Hz) was simulated first: with the
large electrolytic output filter it gave Rc 7.68 k / Cc 150 nF and 10 k / 470 nF, a 4.69 V dip on a 1 -> 3 A step and a +12 V rail that
needed > 10 ms to reach its set point after soft-start.  Eq. 47 keeps the crossover below fsw/10 and between the modulator pole and the ESR
zero, as the method requires, and gives 4.90 V / 11.80 V on the load steps (U21 now simulated from 13.5 V, the +18 V rail at full lamp load).

### UVLO thresholds (brownout analysis)

TPS54360B EN pin: threshold Vena = 1.2 V (1.1-1.3 V), the pin *sources* 1.2 uA below and 4.6 uA above the threshold, so
Vstart = Vena + R1 (Vena/R2 - 1.2 uA) and Vstop = Vena + R1 (Vena/R2 - 4.6 uA) (datasheet eq. 40/41).  The raw +5 V rail (9 VAC winding,
GBU8J, C5 = 10000 uF) was swept with the averaged buck model (`tools/spice/uvlo_sweep.py`, table in `output/spice/uvlo_sweep.md`):

| mains | 100 % | 90 % | 88 % | 85 % |
|---|---|---|---|---|
| raw minimum at 2 A (V) | 9.10 | 7.67 | 7.38 | 6.93 |
| raw minimum at 3 A (V) | 8.34 | 6.80 | 6.48 | 5.98 |
| raw ripple p-p at 3 A (V) | 1.03 | 1.17 | 1.20 | 1.26 |

The converter regulates 5.0 V down to Vin = 5.6 V.  A divider like the modern board's first attempt (start 7.2 V) would switch the +5 V
off in any brownout below ~92 % at 3 A; even the modern board's final 82 k / 20 k (stop 5.74 V nominal, 6.25 V at Vena = 1.3 V) leaves
only 0.23 V worst-case margin at 88 % / 3 A because the cost board's raw rail is ~0.6 V lower (10000 uF, higher-Rs GBU8J).  Chosen: **118 k /
29.4 k -> start 5.9 V / stop 5.5 V nominal (6.4 / 6.0 V at Vena = 1.3 V, 5.4 / 5.0 V at 1.1 V)**: the stop level sits just below the
5.6 V regulation limit, so in a deep brownout the converter droops (Vout = 0.97 Vin - 0.5) instead of shutting down, and at 88 % / 3 A the raw
minimum (6.48 V) is 1.0 V above the nominal and 0.5 V above the worst-case stop level; at 85 % / 3 A (5.98 V) it reaches the regulation
limit anyway.  +12 V: **130 k / 20 k -> start 8.8 V / stop 8.4 V** (9.5 / 9.1 V worst case), well under the 10.3 V that the +18 V rail keeps at
88 % mains with all 64 lamps lit; the +12 V digital then droops to 9.5 V rather than dropping out (the original 7812 would have delivered ~7 V
there).  The stress decks model both stop levels with a smooth 0.5 (1 + tanh((Vin - Vstop) 40)) factor (5.6 V / 8.5 V, i.e. the Vena = 1.22 V values).

### Fuse position check

`tools/gen_pcb.py` places every footprint by its pad centroid.  The Keystone 3517 footprint (pads at 0 / 6.76 / 16.35 / 23.11 mm, centroid
11.555 mm) and the 3AG 102 clip footprint (0 / 7.62 / 26.59 / 34.21 mm, centroid 17.105 mm) both have their centroid at the fuse centre, so
every 5 x 20 mm fuse sits centred on the original 3AG position; `.scratch/placed.json` of both projects agrees to <= 0.12 mm for all
sixteen positions (F106-F108 moved 0.12 mm during the courtyard relaxation).  Fuses, bridges, connectors and the C5/C6/C7/C11/C30
capacitors are now anchored (`fixed`) in the relaxation so they cannot drift.

## Cost

`output/bom/BOM-cost.md` (one DigiKey link per line item, qty-1 and qty-100 columns, cost by group) and `output/bom/bom_*.csv`
(`kicad-cli sch export bom` with Reference, Value, Footprint, Manufacturer, MPN, Link, Price, Price100, Description).  Qty-1 prices are the
DigiKey/Mouser single-unit prices seen during sourcing where they were visible (a `~` marks the 266 small parts - mostly 0805 passives -
that carry an estimate so the roll-up is complete).  Qty-100 prices are estimates for buying 100 boards' worth (reel / 1000-piece breaks
for the parts used 8-32 times per board, 100-piece breaks otherwise; where no break was visible: 0.55-0.7x qty-1 for semiconductors,
0.3x passives, 0.6x connectors / electromechanical).  Fuse clips (32) and the five triac heatsinks are included as synthetic lines.

| group | parts | per board, qty 1 (USD) | per board, qty 100 (USD) |
|---|---|---|---|
| MOSFETs (44 DPAK) | 44 | 77.20 | 32.48 |
| Connectors (KK-396 / KK-254 / box header) | 38 | 30.96 | 20.04 |
| Electrolytic capacitors | 7 | 21.70 | 13.65 |
| Fuses + clips (16 positions) | 46 | 27.67 | 10.00 |
| Buck converters (IC, inductor, diode) | 6 | 14.48 | 9.30 |
| Bridge rectifiers (BR3 GBPC3510W + 16 x STPS20M100S) | 17 | 32.28 | 13.02 |
| Triacs + gate transistors + heatsinks (5 x 7019BG, 6224BG + M3 / M4 hardware) | 28 | 26.10 | 17.33 |
| Logic / comparators / driver (incl. U9) | 15 | 9.42 | 5.25 |
| SMD passives (incl. SR1/SR2, 0.1 % +5 V feedback divider) | 195 | 26.10 | 4.73 |
| Diodes + LEDs (S3M on the coil groups) | 37 | 13.82 | 5.11 |
| Misc (test points) | 15 | 2.98 | 1.32 |
| **components per board** | **448** | **282.71** | **132.23** |

The qty-100 total (**~132 USD**: 115 USD before the 2026-09-07 thermal review, which replaced the four low-voltage bridges by 16 STPS20M100S Schottky
diodes (+8.3 USD net of the GBJ / GBU parts) and added real Boyd heatsinks and hardware for the triacs and BR3 (+7.9 USD net of the 1.75 USD of clip-on
sinks, `docs/THERMAL_AND_PROTECTION.md`) - the chassis heatsink of the original board was never in the cost target; 112 USD before the interface corrections: +0.42 U9, +0.35 SR2, +1.2 C30 10000 uF, -0.2 BR5 GBU8J, +1.56 S3M x 12,
+0.16 bleeder/link) sits at the top of the 105-115 USD target of `../wpc_power_driver_modern/output/bom/COST-ESTIMATE-Q100.md`.
The biggest uncertainties are the 28 IRLR3110Z (0.78 USD assumed at reel quantity; every 0.10 USD moves the board by 2.80 USD) and the
connectors (18 USD; the five N/C spare headers J108/J109/J110/J111/J123 could be omitted for another ~2.5 USD).  Not included: the bare
4-layer PCB, assembly, thermal compound, M4 hardware for the mounting holes.

## SPICE verification

`flatpak run --command=python3 org.kicad.KiCad tools/spice/run_all.py` runs twenty-one ngspice decks (`tools/spice/decks/`) and writes
`output/spice/RESULTS.md` (**211 / 211 checks pass** after the 2026-09-07 thermal review `docs/THERMAL_AND_PROTECTION.md`, which turned the
four low-voltage bridges into STPS20M100S Schottky bridges and raised the +5 V set point to 5.10 V; see the table and `docs/VERIFICATION_MATRIX.md`,
which maps every machine integration point to its evidence and check) plus waveform CSVs; `python3 tools/spice/compare.py` writes `output/spice/COMPARISON.md`
(modern vs cost).  Model notes: level-1 MOSFET fits to the DPAK datasheets (IRLR3110Z ~18 mOhm at the 4.6 V HCT gate drive, IRLR024N ~80 mOhm
at 4.6 V, IRFR5305 65 mOhm at -10 V), a TPS54360B behavioural peak-current-mode model (12 A/V, 4.5 A minimum current limit, 400 kHz), bridge
elements with a higher series resistance than the 35 A block (GBJ15 60 mOhm, GBU8 80 mOhm, Vf ~1.3 V modelled at rated current - pessimistic),
and - since the machine-level review - the real WPC interface: the 51.4 VAC solenoid winding (72.7 V peak, 0.6 ohm per leg; the STTNG transformer
measured 55.2 VAC unloaded), the "9.8 VAC" +12 V power winding at its measured 12.47 VAC unloaded (0.25 ohm per leg), 2 ms lamp column strobes
with thermal #555 filaments, IRQ-timed 5 us triac writes, 4 ms PWM coil holds, the +12 V digital buck on the +18 V rail, the active-high zero
cross, BLANKING as the CPU drives it, and switch-on inrush against the Littelfuse melting I2t.  Every limit in `run_all.py` carries its
justification.  Machine-level decks and their key numbers:

| deck | what it proves | key numbers (limit) |
|---|---|---|
| `powerup` | +5 V soft-start with random latch contents, BLANKING high for 200 ms as the CPU holds reset, then released with the latches holding 1, then written 0 | coil / G.I. / column current while blanked 13 nA / 10 uA / 0.1 nA (<= 10 / 50 / 10 mA), BLANKING never below 5.0 V (>= 4 V), then 16.6 A coil / 6.6 A string / 5.3 A column when released, 0 after the write |
| `sol_high` | AE-23-800 (4.2 ohm) 40 ms pulse on the 70 V rail | 16.6 A, Vds 0.31 V (<= 0.45), 5.2 W during the pulse (<= 7.5), 0.185 J (<= 0.3), +2.8 C per pulse (<= 6, Zth 0.6 C/W), +52 C at 20 % duty (<= 75 on 1 sq. in. copper) |
| `sol_low` | AE-26-1200 (10.8 ohm) pulse | 6.5 A, 0.12 V, 0.77 W (<= 1.5) |
| `sol_hold` | 100 % hold of a 14.5 ohm coil for 3 s; FreeWPC 50 % PWM hold (4 ms / 4 ms) of an AE-26-1200 | 4.8 A / 0.43 W / +21 C (<= 40); PWM 3.2 A average, 5.5 A peak, 0.9 A minimum (continuous), 0.27 W, S3M freewheel 1.28 A average (<= 2, IF(AV) 3 A), 7.6 A peak |
| `lamp_strobe` | 8 columns x 2 ms, 8 lamps per column, thermal filaments; row with all 8 lamps lit; the original Darlington path for comparison | column IRFR5305 8.0 A peak / 0.67 A average / 0.43 V / 0.23 W (+12 C), row IRLR024N 1.0 A peak / 0.51 A average / 0.08 W, sense 0.19 V (no false trip), cold first strobe 2.3 A, lamp RMS 6.17 V (5.5-6.6; original board 5.53 V) |
| `gi_dim` | the board's own zero-cross detector + an ASIC edge model + firmware timing (levels 0 / 3 / 7, gate held vs 8 us pulse), both half-cycles, BTA16-600C Q IV | level 0 4.68 A rms; level 7 pulsed 0.69 A rms (1.35 / -3.70 A peaks), no DC component; a bit held through the crossing re-fires (as on the OEM) |
| `zero_cross` | the corrected detector on the F113-fused 9 VAC leg (GBU8J + 10000 uF at 3 A) | 60 Hz square wave, 7.3 ms high, edges +0.53 / -0.50 ms from the true crossings, 5.0 V / 0.16 V, 4 us rise |
| `gi_gate` (checks added) | gate drive, triac on-state (Vt0 0.85 V / 25 mOhm) dissipation and junction temperature with the Boyd 7019BG bolt-on heatsink (thermal review 2026-09-07) | 78 mA gate, 3.3 W; junction rise 51 C (61 C at the 4.5 A string of `gi_string`) with the 11 C/W 7019BG - the earlier 577002 clip is a 32 C/W part and would have given 114 C |
| `bridge_loss` (new, 2026-09-07) | conduction loss and junction temperature of the bridges: four STPS20M100S Schottky diodes per low-voltage rail on 2-15 cm2 pours (per-diode loss 0.425 IF(AV) + 0.0088 IF(RMS)^2), BR3 GBPC3510W under a 6224BG basket, at the sustained design loads and the fuse-limit loads | +18 V diodes 1.92 W each / 107 C with all 64 incandescent lamps lit (a GBJ1510 block was 15 W / 208 C), +20 V 73 C, +5 V raw 67 C, +12 V power 75 C, BR3 117 C at 3 A; DPAK checks re-based on the as-routed 110 C/W (tab pad only): 20 % duty machine-gun 163 C (< 175 C absolute) |
| `gi_string` (new) | 18 x #44 cold start through F106 (239 5 A) and the triac, fired at the peak | 39 A peak, 9.2 A2s = 3 % of the 302.8 A2s melting I2t, 4.54 A rms steady |
| `ribbon` (new) | 6809E write -> ASIC 375 ns strobe -> 74LS240 (active-low) -> ribbon (4.7 k pull-ups) -> U9 74HCT240 -> 74HCT574 (XSPICE) -> IRLR3110Z; unplugged; BLANKING high | setup 145 ns / hold 154 ns (needs 20 / 5), write 1 -> ON, write 0 -> OFF, latch tri-stated (< 2 nA) when unplugged or blanked |
| `psu` | rails with the real windings (Schottky bridges) | "+50 V" idle 69.2 V (66-74), 41.6 V average / 35.5 V minimum during the 16 A pulse; +18 V 15.3 V; +5 V raw 10.0 V minimum, +5 V 5.10 V (4.86 V at the CPU with 3 A through 80 mOhm); +12 V digital 12.00 V from +18 V; +20 V 17.8 V minimum under a 4 A flasher burst |
| `psu_maxload` | everything on | +18 V 11.9 V minimum with 64 lamps -> +12 V digital 11.0 V (>= 10.5; original 7812 ~10 V); +12 V power 10.5 V at 2.5 A (>= 10); +20 V 12.1 V during the 54 A flasher inrush; six coils at once 37.8 A, rail 14.1 V, bridge 37 A (400 A surge); BR5 GBU8J 7.2 A peaks |
| `psu_brownout` | 88 % mains | +5 V raw 6.48 V (>= 6.0), +5 V 5.00 V; +18 V 10.3 V -> +12 V digital 9.5 V (>= 9); +12 V power 9.1 V (>= 8.5) |
| `psu_12vu` | +12 V power rail | 10.5 V minimum / 11.1 V average / 1.06 V ripple at 2.5 A; 15.9 V unloaded maximum (25 V capacitor); 9.3 V with the manual's nominal 9.8 VAC (pessimistic) |
| `inrush` | switch-on at the mains peak into every capacitor | fuse peaks F113 33 A, F114 52 A, F111 47 A, F116 25 A, F112 53 A; I2t 1.5 / 7.1 / 4.1 / 1.2 / 6.7 A2s = 0.5 / 3.6 / 1.3 / 0.6 / 1.9 % of the melting I2t (239 5 A 302.8 A2s, 217 8 A 198 A2s, 313 3 A / 7 A 200 / 347 A2s as stand-ins) - all <= 20 %; bridge peaks far below GBU8J 200 A / GBJ1510 240 A / GBPC3510 400 A |
| `buck_5v`, `buck_12v` | switching-model loops | 4.90 V undershoot on 1 -> 3 A, 3.65 A peak inductor current (< 4.5 A limit); +12 V from 13.5 V: 11.80 V on 1 -> 2 A, 3.23 A peak |
| `flasher`, `lamp_matrix`, `lamp_matrix_trip`, `gi_gate` | block-level checks from the modern suite | unchanged: 6.6 A cold flasher inrush, 0.12 V column / 0.62 V row drop, 8.4 A row fault cleared 0.16 ms after the strobe, 78 mA triac gate |

What the interface corrections cost in margin: the 70 V rail triples the pulse dissipation of the high-power DPAKs (5.2 W for 40 ms instead of
2.9 W; still +2.8 C per pulse, and +52 C for a coil machine-gunning at 20 % duty on 1 sq. in. of copper), the +12 V digital rail follows the
+18 V lamp rail down to 11.0 V with all lamps lit (original: ~10 V) and 9.5 V at 88 % mains, and the +12 V power rail sits at 10.5-11 V with
2.5 A of motors and optos on 10000 uF (a 15000 uF C30 like the original would add ~0.4 V).  Lamps run brighter than on the 1993 board
(6.17 V RMS vs 5.53 V, rating 6.3 V), so incandescent #555 life is roughly a third - irrelevant with LEDs.

## Sourcing notes

* **IRLR024NPBF** (tube) is out of stock at DigiKey with no back-orders; the tape-and-reel **IRLR024NTRPBF** (DigiKey 812549, "ships today";
  Mouser 1.02 USD) is used.  Alternatives checked and rejected: IRLR2905 (3000-piece minimum / back-order), onsemi NTD/NVD5867NL (obsolete).
* **IRFR5305PBF** (tube) is out of stock; **IRFR5305TRPBF** (DigiKey 811407, Mouser 1.98 USD) is used.
* **Nichicon LGN1E682MELZ** does not exist at DigiKey; the 6800 uF / 25 V candidates that do (Nichicon LLS1E682MELZ 22 x 30 mm, Rubycon
  25USC6800MEFCSN22X25) are both out of stock / back-order, so C5 uses the same in-stock **Rubycon 25USC10000MEFCSN25X25** as C6/C7/C11
  (more capacitance on the buck input, one part number for four positions).
* **VS-KBPC2510 / GBPC2510** for BR3: the Vishay GBPC2510-E4/51 is more expensive (8.35 USD) than the GBPC3510-E4/51 (6.36 USD, 4.26 USD at
  100), the Diodes GBPC2510 is obsolete and the stocked KBPC2510 alternatives are Chinese brands (Comchip, SMC), so BR3 keeps the 35 A Vishay
  block - as the **wire-lead GBPC3510W-E4/51** (DigiKey 605926; the lug-terminal GBPC3510-E4/51 listed until 2026-09-07 does not fit the wire-lead footprint).
  The GBJ1510-F / GBU8J-E3/51 entries below are no longer used: since the thermal review the +18 V / +20 V / +5 V raw / +12 V power bridges are four
  **ST STPS20M100SG-TR** (100 V, 20 A Schottky, D2PAK, DigiKey 2122461: 1.58 USD @1, 0.52 @1000) each - a GBJ1510 at 15 W could not be cooled on the board.  Diodes Inc **GBJ1510-F** (1.22 USD at 100) is used for BR1/BR4; the GBJ package has no KiCad library footprint, so
  `footprints/wpc_cost.pretty/Diode_Bridge_GBJ.kicad_mod` was written from the Diodes DS21221 outline (30 x 20 x 4 mm, leads `+ ~ ~ -` at
  10.0 / 7.5 / 7.5 mm, 1.3 mm drills) and registered in `fp-lib-table`.
* **GBU4J-BP** (MCC) was first replaced by Vishay GBU4J-E3/51 (Chinese-brand rule); after the machine-level review BR5 became a **GBU8J-E3/51** (the +12 V power rail feeds motors and optos, up to the 3 A of F116).
* **Fuses**: the Littelfuse 218 series (IEC, 250 V) has no 7 A, 3 A or 3/4 A ratings (6.3 / 3.15 / 0.8 A only), so the UL **239 Slo-Blo**
  series with the exact original ratings is used: 0239007.MXP (7 A, 125 V), 0239005.MXP (5 A, 125 V), 0239003.MXP (3 A, 250 V),
  0239.750MXP (3/4 A, 250 V); the 8 A fast fuse is 0217008.MXP (217 series, 250 V).  125 V is ample for the <= 36 VAC / 50 VDC secondaries;
  the 239 series is rated 10 kA interrupting at 125 V.  Clips: Keystone **3517** (0.32 USD at 1, 0.18 at 100, 0.13 at 5000) instead of the
  Littelfuse 520-series clip (no PCB-clip part number could be verified).
* **TPS54360BDDAR**: DigiKey 10434703, 4.52 USD at 1.
* DigiKey product pages block automated fetches, so prices come from search-result snippets and distributor listings; qty-100 prices are
  estimates (see `tools/sourcing.py` for the rule used per part).  Nothing on the BOM is from a Chinese brand.

## Board

* Same outline, stack-up (4-layer, In1.Cu GND plane), mounting holes and keep-out drawings as the modern board; **2 oz outer copper** is now a
  requirement (`docs/FABRICATION_NOTES.md`).
* `DEOVERLAP_MARGIN=2.0 PLANE_ONLY=1 python3 tools/gen_pcb.py` writes the placed board; `wpc_power_driver_cost.kicad_pcb` as delivered is
  **fully routed and production-finished (2026-09-07)**: `kicad-cli pcb drc` with the project net classes reports **0 violations,
  0 unconnected items** (`output/reports/drc.rpt`; the remaining warnings are short dangling pad-entry stubs, seven small isolated pour
  islands, six hole-to-hole spacings and the intended bolt hole H9 inside BR3's courtyard); ERC: 0 errors (`output/reports/erc.rpt`).
* **Power distribution copper (2026-09-07 rework)**: a copper audit of the first routed board found the +5 V, +18 V, "+50 V", G.I. and
  return paths on 1.6 mm / 1.0 mm tracks partly on the 1 oz inner layer (+5 V buck-to-J114 78 mOhm, +50 V bridge-to-capacitor 42 mOhm,
  the whole G.I. return on one 1.6 mm track and a single via).  The router (`../wpc_power_driver_modern/tools/fastroute.py`) got two new
  classes that are confined to the 2 oz outer layers - **Bus** 3.0 mm (+18V, +50V, +20V, +5V, +5V raw, +12V power, all AC legs, G.I.
  strings) and **Heavy** 5.0 mm (G.I. return) with a 1.6 / 0.8 / 0.4 mm neck-down chain at 0.4 mm clearance - plus a 1.6 mm outer-layer
  **Coil** class for the 28 solenoid outputs, a board-edge keep-out and a per-cell width rule (a wide track may not end inside another
  net's clearance zone).  Measured on the finished board (`copper_resistance.py`, DC, 20 C): +5 V C4 -> J114 **52 mOhm** (was 78),
  +18 V bridge -> column MOSFET sources **14.8 mOhm** (27), bridge -> C6 8.4 mOhm, +20 V bridge -> J107/J106 5.1 mOhm, +12 V power
  bridge -> J116/J117/J118 21 mOhm (67), G.I. string J115 -> fuse 2.8 mOhm (17), G.I. return J115 -> triac MT1 4.0 mOhm.
* **Discrete Schottky bridges**: BR1/BR2/BR4/BR5 are four D2PAK STPS20M100SG each (`docs/THERMAL_AND_PROTECTION.md` section 8), on the old
  bridge spots (BR1 quad at x 350/363 y 40/61, BR2 quad below C8 at x 290/311 y 114/128, BR4 at x 281/302 y 12/26, BR5 at x 17/30 y 19/40;
  `tools/placement_cost.py` POS_MM).  Project footprint `wpc_cost:D2PAK_Schottky_AKA` (tab = pad 1 = cathode, both leads = pad 2 = anode
  as in the ST drawing "A K A").  Each tab sits on a 2 oz heat-spreading pour on F.Cu and B.Cu joined by a 3 x 3 via array
  (`tools/rail_pours.py`; filled area F+B: +18 V 9.6 cm2 shared by D101/D102, AC13 legs 7.8 / 8.7 cm2, +20 V 4.5, AC16 legs 3.8 / 10.3,
  +5 V raw 3.3, AC9 legs 2.4 / 2.3, +12 V power 6.4, AC98 legs 3.4 / 3.4).  With the ST Rth(j-a) curve (35 um copper, 2 oz taken as
  0.9x) the +18 V diodes reach about 120 C at the full 64-incandescent-lamp load (1.9 W each) and 75 C with 3 A (LED machine, or half
  the lamps); the other three bridges stay below 90 C at their fuse ratings.  BR3 (+50 V) keeps the GBPC3510W block with the Boyd 6224BG
  basket heatsink and the new 5.5 mm bolt hole H9.
* Placement changes versus the A-12697-3 drawing, all connectors kept: **U1 rotated 180 deg** (see below), **J129 2.5 mm left** (its housing sat inside mounting hole H6's courtyard), **B13** (U13 bypass) moved left of U13, **C21** (10 nF zero-cross
  filter, had no drawing position and was missing from the first board) next to U6, three SMT **fiducials** FID1-FID3, silkscreen legend
  with fuse ratings and connector functions (`tools/legend.py`).
* Interface corrections from `docs/INTERFACE_PARITY.md` applied to the copper: J125 key at pin 4, J128/J129/J131/J132 added at their
  drawing positions, J105 = copy of J104, J120/J121 carry all five G.I. strings, J123 = sol 25-28, J126-10..13 = SOL21..24_TB,
  J103-3/4 grounded, J107-5 = +20V, J108 = fused +50V.  Net-list changes are applied to the routed board with
  `../wpc_power_driver_modern/tools/update_nets.py` (rename-aware, strips only the changed nets' copper) and re-routed incrementally.
* U1 (the G.I. / triac latch) is rotated 180 deg relative to the original board: with GI_BIT5 / GI_BIT6 -> J111 its pins 13/14 had to
  cross GI5_L inside the U1 channel, where the CPU data-bus lines on In2.Cu leave no via slot and D7 / BLANKING occupy B.Cu.
* Hand-routed links (after the router gave up): the U21 buck EN pin, D6 into U1, the U13 clock/D0/ROWCLR1 knot (clock fed through pin 3
  and an under-body link to pin 11), D4 into U11, SOL21_L, the +12 V power link into R250, two GND stitches at J103.
* Flow: `tools/pipeline.sh` (generate, stitch, route, repair, finish, export) or, for a routed board, `tools/finalize.sh` (GND stitch vias,
  rail pours + thermal vias, `finish_board.py`: dedupe, PowerPAD via arrays, outer GND pours, refill, dangling-stub trimming, legend,
  final DRC) followed by `bash tools/export.sh`.

## Renders (`output/3d/`)

`kicad-cli pcb render --quality high` of the placed board: `wpc_power_driver_cost-top-4k.png` (3840 x 2160, zoom 1.05),
`wpc_power_driver_cost-perspective-4k.png` (`--perspective --rotate "-35,0,20" --zoom 1.15 --floor`), `wpc_power_driver_cost-bottom-4k.png`
and `wpc_power_driver_cost-top-1080p.png`.  3D models: the project GBJ footprint carries the KiCad Diotec 32 x 17 mm bridge model scaled to the
GBJ body (30 x 20 x 4 mm); four library footprints reference STEP files that are not shipped in this KiCad 3D package and get stand-ins in
`tools/kicad_pcb.py` (render only): Keystone 3517 clips -> Schurter 0031.8201 open 5 x 20 mm holder (with fuse), SRP1245A -> Bourns SRR1260
(scaled 1.04), Texas HSOP-8 -> generic HSOP-8-1EP, Omron G2RL-2 (DNP) -> G2RL.  The KK-396 headers use the KK-254 model scaled 1.56 as on the
modern board.  Only the eight M4 mounting holes and the nine plated test pads have no model (nothing to show).

Renders and Gerbers were regenerated from the routed board on 2026-09-06.  Also not verified: live DigiKey prices (see above), the GBJ footprint against a physical part (the coordinator's note quoted a 21.5 x 20 mm / 5 mm-pitch GBJ; Diodes DS21221, read directly, gives 30 x 20 x 4 mm with 10 / 7.5 / 7.5 mm lead gaps - the footprint follows the datasheet), the thermal behaviour of the DPAK
solenoid drivers on the final copper (the SPICE limits assume ~1 sq. in. of copper per DPAK tab), and the TPS54360B loop on a first article.

## Verification audit (2026-09-06)

`docs/VERIFICATION_MATRIX.md` lists every integration point with the rest of the machine with its evidence and check (211 / 211 checks after
the Schottky-bridge change of `docs/THERMAL_AND_PROTECTION.md`, which also flags the 1.6 mm GI_RET return bus and the +18 V winding tracks as
layout items for the re-route).  Two real design errors were found on this board and corrected in `tools/design_cost.py` (schematic regenerated,
ERC 0; no footprint added or removed - R198 is now DNP - so the placed board only needs its rat's nest refreshed):

* the zero-cross detector produced a 120 Hz active-high pulse; it now reproduces the OEM 60 Hz square wave
  (`R197-1: AC98_A -> AC9_AF`, `R198-1: AC98_B -> AC9_B` + DNP, `U6-4 <-> U6-5` swapped so the sample is on +);
* J104 carried the unfused 51 VAC winding; it now carries the F112-fused leg on pin 1 and the F111-fused 16 VAC leg on pin 4
  (`J104-1 ACSOL_A_F, -2 ACSOL_B, -4 AC16_A_F, -5 AC16_B`; F113-2 / BR2-3 = `AC9_AF`, F112-2 / BR3-3 = `ACSOL_A_F`, F111-2 / BR4-3 = `AC16_A_F`
  are now global nets, same copper).
