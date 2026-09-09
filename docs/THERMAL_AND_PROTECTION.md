> Earlier design/review record. See [current release status](RELEASE_STATUS.md) for superseding component choices, copper stackup, results and unresolved gates.

# Thermal and protection design - cost-optimised WPC Power Driver Board (A-12697-3 replacement)

Review of 2026-09-07 closing the open thermal / protection items of `VERIFICATION_MATRIX.md` (rows 9.6, 14, 15): bridge rectifier and triac
heatsinks, the real copper under the DPAK MOSFETs, the real fuse I2t values and the connector / track currents.  **Follow-up design change
(same day, section 8): the four low-voltage bridges BR1 / BR2 / BR4 / BR5 are now discrete Schottky bridges of four ST STPS20M100SG-TR each
(D101-D116), because the GBJ1510 of BR1 could not be cooled on the board; the +5 V set point was raised to 5.10 V (section 9).**  Sections 1
and 5 keep the block-bridge analysis that led to the change; the numbers that still apply to the board as designed are in sections 8 and 9.  Every number is either
measured on the routed board (`wpc_power_driver_cost.kicad_pcb`, read with pcbnew - `.scratch/thermal/board_thermal.py`,
`copper_audit2.py`, `.scratch/nettracks.py`), simulated (`tools/spice/decks/*.cir`, suite result `output/spice/RESULTS.md`:
**211 of 211 checks pass** with the Schottky bridges - the block-bridge FAIL of item 1.6 is gone) or quoted from a datasheet / catalogue named in section 7.

Design limits used throughout: **50 C ambient inside the backbox, Tj <= 125 C** (design target; absolute maxima: GBJ / GBU / GBPC 150 C,
BTA16 125 C, IRLR3110Z / IRLR024N / IRFR5305 175 C).  Heatsink catalogue values are natural-convection figures at a 75 C sink rise
(Boyd board-level catalogue, "n" column); they are multiplied by 1.05 (bridges, 55-65 C rise) or 1.15 (triacs, ~50 C rise) because
natural convection is weaker at a smaller rise (Rth ~ dT^-0.25).  Interface resistance 0.5 C/W (thermal compound, bolted).

## 0. Summary

| device | realistic sustained load | dissipation | thermal part (Boyd / Aavid) | Rth j-a (C/W) | Tj at 50 C | status |
|---|---|---|---|---|---|---|
| **+18 V bridge D101-D104** (4 x STPS20M100S, was BR1 GBJ1510) | **all 64 incandescent lamps + buck = 6.4 A DC / 11.2 A rms** | **1.92 W per diode** (7.7 W per bridge; was 15.2 W) | **15 cm2 of 2 oz copper per diode** (D101/D102 share a 30 cm2 +18V pour, D103 / D104 15 cm2 on the AC legs), 29.7 C/W | 29.7 | **107 C** | PASS (Tj <= 110 C) |
| +18 V bridge | 3.0 A DC (half the lamps + the buck; LED machine) | 0.79 W per diode | same | 29.7 | 74 C | PASS |
| +20 V bridge D109-D112 (was BR4) | 2.5 A DC (flasher shows at half the F111 rating); 5 A fuse rating | 0.65 / 1.44 W per diode | 4 cm2 of 2 oz copper per diode, 36 C/W | 36 | 73 / 102 C | PASS |
| BR3 GBPC3510W-E4/51, "+50 V" | 3.0 A DC (a held 14.5 R coil half the time + play) | 5.7 W | **6224BG** basket, 9.4 C/W, 26.9 mm sq x 31.75 mm, ~6.20 USD, M4 through the block | 11.8 | 117 C | PASS (limit 3.3 A sustained) |
| +5 V raw bridge D105-D108 (was BR2) | +5 V buck at 3 A out = 1.7 A DC in | 0.41 W per diode | 2 cm2 of 2 oz copper per diode, 41 C/W | 41 | 67 C | PASS |
| +12 V power bridge D113-D116 (was BR5) | 2.5 A DC (gun motors, optos, DMD, coin door); 3 A fuse rating | 0.60 / 0.73 W per diode | 2 cm2 of 2 oz copper per diode, 41 C/W | 41 | 75 / 80 C | PASS |
| (superseded) BR1 GBJ1510-F on a Boyd 7020BG | all lamps + buck 5.8 A DC | 15.2 W | 7020BG 8.7 C/W | 10.4 | 208 C | FAIL - the reason for the Schottky bridges (section 1.6) |
| Q10/Q12/Q14/Q16/Q18 BTA16-600CRG | 4.54 A rms incandescent string | 3.9 W (gi_string), 3.3 W (gi_gate) | **7019BG** bolt-on channel, 11.0 C/W, 39.4 x 9.5 x 25.4 mm, ~1.15 USD | 15.65 | 111 C | PASS (was FAIL with the 32 C/W 577002 clip) |
| IRLR3110Z DPAK, sol 1-8 | AE-23-800 40 ms pulses, <= 10 % duty | 0.52 W avg | tab pad only (38-64 mm2 of 1 oz copper, no pour): 110 C/W | 110 | 107 C | PASS |
| IRLR3110Z | machine-gunning at 20 % duty | 1.03 W avg | same | 110 | **163 C** | above the 125 C target, below Tjmax 175 C - open item 3.4 |
| IRLR3110Z, sol 9-16 / 25-28 | 14.5 R coil held 100 % (4.8 A) / PWM 50 % | 0.43 / 0.27 W | same | 110 | 97 / 79 C | PASS |
| IRFR5305 / IRLR024N lamp columns / rows | all lamps lit | 0.23 / 0.08 W | same | 110 | 76 / 59 C | PASS |

BOM effect (`output/bom/BOM-cost.md`, qty-100): 16 x STPS20M100SG-TR 8.32 USD minus the GBJ1510 / GBU8J parts 4.44 USD = +3.88 USD; heatsinks
5 x 7019BG 5.75 + 6224BG 6.20 + M3 / M4 hardware 0.38 = 12.33 USD minus the 1.75 USD of the five 577002 clips = +10.58 USD; BR3 wire-lead part
+0.44 USD; 0.1 % feedback divider +0.10 USD = **+15.0 USD per board from the thermal review (115.4 -> 130.4 USD; the report total of 132.23 USD
includes the +1.8 USD of the parallel connector review)**.  Qty-1: +35.6 USD (16 diodes at 1.58 USD).

Production blockers found on the way (section 6): the +18 V rail at full incandescent lamp load - the bridge part is solved by the Schottky
bridge (section 8), the 1.6 mm winding tracks AC13_A / AC13_B (11.2 A rms now) must be widened in the re-route - and the **G.I. return bus
GI_RET, which carries up to 22.7 A rms through one 1.6 mm track and one via** (item 5.3).  Both are layout items for the re-route the
coordinator is doing from this netlist.

## 1. Bridge rectifiers

### 1.1 Loads

The average bridge current is the DC output current of its rail; the loss is set by the DC average and the RMS of the peaky
capacitor-input current (crest factor 1.55-1.9 measured).  Sustained (minutes) design loads, all justified from the machine:

| bridge | rail | sustained design load | source | everything-on / fuse-limit case |
|---|---|---|---|---|
| BR1 | +18 V | 3.0 A DC: ~half the 64 lamps lit (lamp_strobe: 0.67 A per column with 8 lamps) + the +12 V digital buck (0.75 A / 0.88 eff) | `lamp_strobe`, `psu` | all 64 lamps (2.5 ohm) + buck = 5.81 A DC (`psu_maxload` case); F114 8 A |
| BR4 | +20 V | 2.5 A DC: flasher shows at half the F111 rating (a hot flasher is 1.1 A, `flasher`) | `psu` (4 A burst at 33 % duty = 1.3 A average) | F111 5 A (8 hot flashers would draw 8.9 A and blow F111) |
| BR3 | "+50 V" (70 V) | 3.0 A DC: a 14.5 ohm continuous-duty coil (4.8 A, `sol_hold`) held half the time plus play; the flippers are rectified on the Fliptronic II board from J104 and do not load BR3 | `sol_hold`, `psu_maxload` (six coils 40 ms / 400 ms = 3.8 A average) | F112 7 A |
| BR2 | +5 V raw | the +5 V buck at its rated 3 A output = 1.93 A DC in (eff 0.88, 8.9 V raw); the real load is 2.2-2.6 A (README) = 1.5 A in | `psu`, `buck_5v` | none - the converter limits the rail (F113 5 A is never reached) |
| BR5 | +12 V power | 2.5 A DC (two gun motors, optos, coin door, DMD; `psu_12vu`) | `psu_12vu` | F116 3 A (the 239 fuse carries 110 % for 4 h) |

### 1.2 Dissipation (SPICE deck `bridge_loss.cir`, new)

Each rail is rectified with the real winding, the SPICE bridge model and its filter capacitor, then loaded as above; the deck measures the
DC average and RMS of the leg current, the model dissipation by power balance (AC-side minus DC-side power = the four diodes; the level-1
model has Vf ~1.3 V at rated current, so this is pessimistic) and the datasheet dissipation

P = 2 (V0 Iavg + Rd Irms^2), V0 / Rd through the datasheet **maximum** Vf point: GBJ1510 1.05 V @ 7.5 A -> 0.80 V / 33 mOhm;
GBU8J 1.0 V @ 8 A -> 0.75 V / 31 mOhm; GBPC35 1.1 V @ 17.5 A -> 0.80 V / 17 mOhm.

| case | Iavg (A) | Irms (A) | Vdc (V) | P datasheet (W) | P model (W) | Rth j-a (C/W) | Tj (C) | check |
|---|---|---|---|---|---|---|---|---|
| BR1 all 64 lamps + buck | 5.81 | 9.48 | 12.6 | **15.2** | 21.2 | 10.4 | **208** | `tj_18a` FAIL |
| BR1 3.0 A design | 3.00 | 5.46 | 14.2 | 6.8 | 8.8 | 10.4 | 120 | `tj_18b` PASS |
| BR1 8 A (F114) | 8.00 | 12.4 | 11.6 | 22.9 | 32.9 | 10.4 | 288 | informational |
| BR4 2.5 A | 2.50 | 4.83 | 18.2 | 5.5 | 7.2 | 10.4 | 108 | `tj_20a` PASS |
| BR4 5 A (F111) | 5.00 | 8.61 | 16.5 | 12.9 | 17.9 | 10.4 | 184 | informational |
| BR3 3.0 A | 3.01 | 5.15 | 56.2 | 5.7 | 8.7 | 11.8 | 117 | `tj_50a` PASS |
| BR3 7 A (F112) | 7.01 | 10.4 | 45.2 | 14.9 | 25.2 | 11.8 | 226 | informational |
| BR2 buck 3 A out | 1.93 | 3.42 | 8.9 | 3.6 | 5.3 | 13.6 | 99 | `tj_5a` PASS |
| BR2 buck 2.4 A out | 1.48 | 2.74 | 9.2 | 2.7 | 3.8 | 13.6 | 87 | `tj_5b` PASS |
| BR5 2.5 A | 2.50 | 3.87 | 10.8 | 4.7 | 6.8 | 13.6 | 114 | `tj_12a` PASS |
| BR5 3 A (F116) | 3.00 | 4.51 | 10.2 | 5.8 | 8.6 | 13.6 | 128 | `tj_12b` (limit 150 C absolute; 3 C over the design target with worst-case Vf, ~110 C with typical Vf) |

### 1.3 Datasheet thermal data

| part | Rth j-c | Rth j-a (no sink) | mounting | Tj max | IF(AV) | IFSM | source |
|---|---|---|---|---|---|---|---|
| Diodes GBJ1510-F | 0.8 C/W typ per element (on a 300 x 300 x 1.6 mm copper plate) | not given | through hole for #6 screw, 5.0 in-lb max; hole 3.4-3.8 mm, body 3.8-4.2 mm thick | 150 C | 15 A "with heatsink" | 240 A | DS21219 Rev 8-2 (May 2025) |
| Vishay GBU8J-E3/51 | 4.0 C/W (bolted to an aluminium plate) | 20 C/W (PCB, 12 x 12 mm pads, free air) | #6 screw, 8.8 in-lb max; recommended: bolt down with silicone thermal compound | 150 C | 8 A at Tc 60 C bolted / 3.9 A at Ta 40 C on a PCB | 200 A | doc 88616 rev 10-Jul-2020 |
| Vishay GBPC3510W-E4/51 | 1.4 C/W (with heatsink) | not given (a 28.6 mm block in free air is ~30-40 C/W) | #10 screw, 20 in-lb, hole 5.08-5.59 mm; block 28.3-28.8 mm sq, 7.36-7.87 mm thick; W = wire leads 0.97-1.07 mm, >= 31.8 mm long | 150 C | 35 A (Fig. 1, on a heatsink) | 400 A | doc 88612 rev 30-Nov-2021 |

Required sink-to-ambient resistance for Tj <= 125 C at 50 C (Rth s-a = 75 / P - Rth j-c - 0.5, before the 1.05 derating):

| case | P (W) | Rth j-a needed | Rth s-a needed | catalogue value needed (/1.05) |
|---|---|---|---|---|
| BR1 3 A | 6.8 | 11.1 | 9.8 | <= 9.3 -> 7020BG (8.7) |
| BR1 all lamps | 15.2 | 4.9 | 3.6 | <= 3.4 -> chassis-class heatsink (the OEM bracket); no device-mounted part |
| BR4 2.5 A | 5.5 | 13.5 | 12.2 | <= 11.6 -> 7020BG (7019BG at 11.0 is marginal) |
| BR3 3 A | 5.7 | 13.1 | 11.2 | <= 10.7 -> 6224BG (9.4) |
| BR2 3 A out | 3.6 | 20.8 | 16.3 | <= 15.5 -> 7020BG |
| BR5 2.5 A | 4.7 | 16.0 | 11.5 | <= 11.0 -> 7020BG |

Sustained current limits with the chosen sinks (Tj = 125 C, measured crest factors): BR1 / BR4 **3.1 A**, BR3 **3.3 A**, BR2 / BR5 **2.9 A DC**.

### 1.4 Heatsink parts

* **Boyd (Aavid) 7020BG** - narrow channel style heat sink with folded-back fins, 1.27 mm black-anodised aluminium, 8.7 C/W, 33.02 wide x
  11.94 deep x 36.83 mm high, two 3.81 mm device holes 7.87 and 14.48 mm above the bottom edge, **no solderable tabs** (mounted by the
  device screw only - no PCB hole needed).  Boyd board-level catalogue p. 27; DigiKey 1625705 ("8.0 W @ 70 C").  The channel is 17.8 mm
  wide inside, i.e. it cannot wrap a 30 mm GBJ / 22 mm GBU body: it is bolted **back-to-back**, its flat back plate against the metal face
  of the bridge, fins pointing away.  With the bridge's #6 hole ~11 mm (GBJ) / ~15 mm (GBU) above the board and the sink's upper hole the
  sink bottom sits 0.5-3.5 mm above the PCB, top ~37-40 mm.  M3 x 12 pan-head screw + M3 nut (an M3 in the 3.4-3.8 mm hole with the
  sink's 3.81 mm hole is the standard TO-220 fit), thermal compound, thread-lock.
* **Boyd 6224BG** - "square basket style heat sink for bridge rectifiers, uses no additional board space": 26.92 mm square, 1.27 mm
  aluminium base plate with four 31.75 mm walls, 4.77 mm centre hole (6222BG 3.61 / 6223BG 4.14 mm), 9.4 C/W (catalogue p. 77; DigiKey
  lists the 6223BG at 8.87 USD @1 / 6.14 @1000; Future 6224BG 6.42).  It sits on the exposed metal base of the GBPC block, bolted through
  the block's 5.1-5.6 mm hole with an M4 x 16 screw + nut.
* **Boyd 7019BG** - narrow channel style heat sink with folded-back fins, 1.02 mm aluminium, 11.0 C/W, 39.37 wide x 9.52 deep x 25.40 mm
  high, 11.94 mm channel (a TO-220 is 10.2 mm), 3.81 mm device hole 14.48 mm above the bottom, no tabs (catalogue p. 27; Mouser hosts the
  7019 data sheet "Board-Level-Cooling-Narrow-Channel-7019.pdf").  Alternative without a screw: **584000B00000G** louvered clip-on,
  10.0 C/W, 31.75 x 9.91 x 43.18 mm (catalogue p. 67).
* The previously specified **Aavid 577002B00000G** clip ("25 C/W" in the old sourcing table) is a **32 C/W** part (catalogue p. 34,
  Jameco listing "32 deg C/W", 13.2 x 6.4 x 19 mm): with a 3.9 W incandescent string it would have run the triac at ~165 C.
* Prices: 7019BG / 7020BG are estimates (1.75 / 2.40 USD @1, 1.15 / 1.55 @100 - no distributor page could be fetched; DigiKey and
  Mouser block automated access, Farnell timed out); 6224BG from the 6223BG DigiKey price.  Hardware: B&F Fastener Supply MPMS 003 0012 PH
  / MHNZ 003 (M3) and MPMS 004 0016 PH / MHNZ 004 (M4), ~0.05 USD each at 100 (estimate).

### 1.5 Physical fit (courtyards from the routed board, all bridges at rot -90: leads along y, faces normal to x)

Metal-face side: for the GBJ the lead order "+ ~ ~ -" reads left-to-right on the marking (front) face with the bevel at the top-left;
with pad 1 (+) at the smaller y and the board viewed from +x that order reads left-to-right, so the marking face points **+x and the metal
back -x** for BR1 and BR4; the Vishay GBU ("polarity shown on front side of case, positive lead by beveled corner") gives the same for
BR2 and BR5.  Should an assembled part face the other way, the +x sides are also free (BR1 24 mm to the fuse clips, BR4 21 mm to C11,
BR2 25 mm to F111, BR5 15 mm to J112).

| bridge | body (x, y) | sink footprint on the metal side (x, y) | nearest neighbours (courtyard) | clearance |
|---|---|---|---|---|
| BR1 GBJ (358.3-363.8, 68.1-99.6), hole y 83.8 | 7020BG x 346.6-358.5, y 67.3-100.3 | C8 x <= 339.3; R196 x <= 344.7 (y 92-94); LED6 x <= 343.3; C7 y >= 105.1; C5 x <= 337.4 | 7.3 / 1.9 / 3.3 / 4.8 mm - fits |
| BR4 GBJ (285.4-291.0, 7.3-38.8), hole y 23.1 | 7020BG x 273.8-285.7, y 6.5-39.5 | BR3 courtyard x <= 266.8 (the 6224BG basket stays inside x 238.5-265.5); board edge y = 0 | 7.0 / 6.5 mm - fits |
| BR2 GBU (358.7-363.2, 15.0-37.7), hole y ~26.3 | 7020BG x 347.1-359.0, y 9.8-42.8 | LED5 x <= 341.8 (y 37-41); R194 x <= 342.8 (y 42.7-44.6); C11 x <= 337.5 | 5.3 / 4.3 / 9.6 mm - fits |
| BR5 GBU (29.5-34.0, 16.0-38.6), hole y ~27.2 | 7020BG x 17.9-29.8, y 10.7-43.7 | C30 y >= 48.5; H3 hole x, y <= 11.1; board edge x = 0 | 4.8 / 6.8 / 17.9 mm - fits |
| BR3 GBPC (237.2-266.8, 8.5-38.1), centre (252.0, 23.3) | 6224BG 26.9 mm sq on the block (x 238.5-265.5, y 9.8-36.8), walls up to ~40 mm above the board | J106 4.6 mm, J107 7.0 mm (both lower than the block), BR4 sink 8.3 mm | fits |

Vertical clearance: the 25 x 40 mm snap-in capacitors C8 / C32 already reach 40 mm; nothing in the backbox is closer than the OEM bracket.

### 1.6 Open item: BR1 at full incandescent lamp load, and the BR3 mounting hole

* **BR1 (+18 V)**: with all 64 incandescent lamps lit plus the +12 V digital buck the GBJ1510 dissipates 15 W (21 W with the pessimistic
  SPICE model) - the same ~15 W the OEM's aluminium bracket sinks from its 35 A block, and the reason the OEM +18 V bridge joints crack.
  A bracket-class sink (<= 3.4 C/W catalogue) cannot be attached to a GBJ on this PCB: the metal face points at C8 (19 mm free), the
  next-best pin-mounted extrusion that fits nowhere near (Boyd 6398B-P2G, 4.4 C/W, 42 x 38 x 25 mm) would still give Tj ~140 C, and the
  1.6 mm winding tracks AC13_A / AC13_B (67 / 106 mm, F.Cu) carry the 9.5 A rms leg current at ~100 C rise (IPC-2221, item 5.3).  The
  check `bridge_loss / tj_18a` therefore stays a **FAIL**.  Options, in order of cost: (a) specify the board for LED-converted lamp
  matrices (<= 2 A on +18 V: Tj < 100 C with the 7020BG) or a firmware / attract-mode lamp-count limit that keeps the average below the
  **3.1 A** sustained limit; (b) next PCB revision: mirror BR1 so its metal face points +x (fuse-clip side, 24 mm free), add two 2.9 mm
  holes for a tabbed 7020B-MTG / 7022B-MTG (6.5 C/W, 50 x 9.5 x 50 mm) and widen AC13_A/B to >= 4 mm - Tj ~125-140 C at 15 W, still
  marginal; (c) OEM solution: 35 A block on a chassis bracket (2-3 C/W).  Recommended: (a) now, (c) or an off-board bracket for the
  incandescent variant.
* **BR3 mounting**: the GBPC-W block stands on its lead face (straight leads through the 1.4 mm holes at 18.0 x 11.6 mm), metal base up,
  7.4-7.9 mm above the board; the footprint has **no centre hole**.  On this revision the M4 x 16 screw is inserted from the lead side
  before the block is soldered (head captive between block and board, the block then stands 2.7 mm - the pan-head height - off the board
  on its >= 31.8 mm leads) and the nut goes on top of the basket.  Next revision: a 5.5 mm NPTH at the block centre (251.99, 23.30) -
  the board audit finds no pad, via or track within 4.5 mm of that point on any layer (only the outer GND pours, which need a clearance
  ring) - so that a screw + nut from the solder side, or a threaded standoff, can be used.

## 2. G.I. triacs

Q10 / Q12 / Q14 / Q16 / Q18 = BTA16-600CRG, insulated TO-220AB, at (117.4, 207.5), (38.4, 156.7), (78.0, 129.9), (78.0, 182.3),
(128.3, 155.1), all rot -90 (leads along y).  They are 40-50 mm apart, so no shared bar - one sink each.  The 3D render
(`output/3d/wpc_power_driver_cost-top-4k.png`) shows the metal tab on the **-x** side of every TO-220 (the TO-220-3_Vertical footprint
puts the tab behind the pin row).

Data (ST BTA16 / BTB16 data sheet, Doc ID 7471; the ST, RS and alldatasheet copies all refused automated access during this review, so
the values are the ones already used in the decks): Rth j-c 2.5 C/W DC for the insulated BTA (a distributor listing of the current ST
revision quotes 2.1 C/W - 2.5 kept as the conservative figure), Rth j-a 60 C/W, Vt0 0.85 V / Rd 25 mOhm, Tj max 125 C, IT(RMS) 16 A,
ITSM 160 A, I2t 128 A2s, IGT 50 mA max in quadrant IV (C suffix).

Dissipation: `gi_gate` 3.27 W (3.89 A rms, 1.4 R hot string on 8.9 V peak), `gi_string` **3.91 W at 4.54 A rms** (18 x #44 steady,
the worst case).  Required Rth s-a for a 75 C rise: 75 / 3.91 - 2.5 - 0.5 = **16.2 C/W** (`rth_sa_needed` 20.0 C/W with the gi_gate
current).

Chosen: **Boyd 7019BG**, 11.0 C/W catalogue x 1.15 = 12.65 C/W -> Rth j-a 15.65 C/W -> rise **61 C (Tj 111 C)** at 3.91 W,
51 C (Tj 101 C) at 3.27 W: checks `gi_gate / tj_rise_sink` 51.1 C and `gi_string / tj_rise_sink` 61.2 C, limit 75 C, PASS (14 C
margin to the triac's 125 C absolute maximum; with LED strings < 1 A the rise is < 10 C).  The old 577002 clip: `tj_rise_clip`
114 C (informational).

Fit (7019BG: back plate 39.4 mm wide along y, 9.5 mm channel depth toward +x of which ~4 mm past the device front, 25.4 mm high;
hole 14.48 mm above its bottom, the TO-220 hole ~17 mm above the board -> sink bottom ~2.5 mm above the PCB):

| triac | sink extent (x, y) | nearest neighbours on the tab (-x) side | clearance |
|---|---|---|---|
| Q10 | x 106.5-121.5 (channel legs to ~125), y 187.8-227.1 | R16 (95.6-103.3, 186.8-190.7); F109 x <= 91; R7 / Q9 / R9 x >= 136.6 (+x side) | 3.2 mm - fits |
| Q12 | x 27.5-42, y 137.0-176.4 | J114 x <= 13.0; H8 hole x <= 11.1; R10 x >= 56.3 (+x) | 14.5 mm - fits |
| Q14 | x 67.0-82, y 110.2-149.6 | R12 (58.5-61.9, 152.7-154.6); R13 / Q13 / R15 x >= 93.9 (+x) | 3.1 mm - fits |
| Q16 | x 67.0-82, y 162.6-202.0 | R10 (56.3-64.0, 162.5-166.4); Q11 (58.5-61.9, 156.6-160.5); F109 y >= 215.2 | 3.0 mm - fits |
| Q18 | x 117.3-132 (legs to ~135.5 at the channel ends y 135.4 / 174.7 only), y 135.4-174.7 | R20 / R17 / R14 (118.7-122.1, y <= 131.6); R19 (136.6-144.4, 160.8-164.7), Q17, R21 x >= 136.6 on the +x side | 3.8 mm (-x), 1.1 mm from the leg tips to R19 which is not in the leg path - fits |

Hardware: M3 x 12 + nut through the insulated tab (2500 V isolation, no washer needed), thermal compound.

## 3. DPAK MOSFETs (28 x IRLR3110Z, 8 x IRLR024N, 8 x IRFR5305)

### 3.1 Copper audit (`.scratch/thermal/board_thermal.py`, all 44 DPAKs on F.Cu, tab pad 37.1 mm2, stack-up 35 um on every layer)

Copper of the drain net on the tab layer inside a window centred on the tab (pads + tracks + zone fills, union): 12.7 mm box: 38-45 mm2
(all 44 parts: the tab pad plus a 1.0 mm track); 25.4 mm box (1 in2): IRLR3110Z 44-64 mm2 (median 55), IRLR024N 38-54, IRFR5305 40-62;
no zone exists on any drain net; other layers 0-15 mm2 within 25.4 mm, 0-2 vias.  That is the data sheets' **minimum-footprint**
condition, not the 1 in2 pad:

| part | Rth j-a "PCB mount" (1 in2 square PCB, FR-4) | Rth j-a minimum footprint | Rth j-c | source |
|---|---|---|---|---|
| IRLR3110Z | 40 C/W | 110 C/W | 1.05 | Infineon / IR data sheet 11/09, notes i, j |
| IRLR024N | 50 C/W | 110 C/W | 3.3 | IR data sheet 12/6/04, note ** |
| IRFR5305 | 50 C/W | 110 C/W | 1.4 | IR data sheet v01_01, note * |

The 0.2 mm dielectric between the tab pad and the In1.Cu ground plane probably brings the real value to 60-80 C/W (a 37 mm2 pad conducts
~18 C/W into the plane), but that is unverified, so **110 C/W** is used in the checks (the decks assumed 50 C/W before this review).

Per-part table for the solenoid drivers (mm2 of F.Cu on the drain net): Q20-Q26 (sol 25-28) 40.5 / 57-64 (12.7 / 25.4 mm box), Q28-Q36
(sol 20-24) 38-41 / 44-61, Q38-Q44 (sol 16-19) 40.5 / 52-61, Q46-Q58 (sol 9-15) 38-41 / 50-54, Q64-Q70 (sol 5-8) 39-41 / 52-60,
Q76-Q82 (sol 1-4) 40.5 / 52-58; rows Q83-Q90 38-43 / 38-54; columns Q91-Q98 40-43 / 40-62.

### 3.2 Re-evaluated checks (110 C/W)

| deck / check | dissipation | rise | Tj at 50 C | limit | result |
|---|---|---|---|---|---|
| sol_high `tj_rise_10pct` - AE-23-800 40 ms pulses at the normal <= 10 % firmware duty | 5.15 W x 0.1 | 57 C | 107 C | 75 C | PASS |
| sol_high `tj_rise_20pct` - a coil machine-gunning at 20 % duty (stuck ball on a pop bumper) | 1.03 W | **113 C** | **163 C** | 125 C (= Tjmax 175 - 50) | passes the absolute limit, **exceeds the 125 C design target** |
| sol_high `tj_rise_20pct_pour` - the same with the recommended >= 300 mm2 pour (60 C/W) | 1.03 W | 62 C | 112 C | 75 C | PASS |
| sol_high `tj_rise_pulse` - single 40 ms pulse (Zth) | 0.185 J | 2.8 C | - | 6 C | PASS (unchanged) |
| sol_hold `tj_rise_hold` - 14.5 R coil held for seconds, 4.8 A | 0.43 W | 47 C | 97 C | 75 C | PASS |
| sol_hold `tj_rise_pwm` - 50 % PWM hold | 0.27 W | 29 C | 79 C | 75 C | PASS |
| lamp_strobe `tj_rise_col` - IRFR5305 column, 8 lamps | 0.235 W | 26 C | 76 C | 75 C | PASS |
| lamp_strobe `tj_rise_row` - IRLR024N row | 0.082 W | 9 C | 59 C | 75 C | PASS |
| sol_low `p_fet` - AE-26-1200 pulse, 6.5 A | 0.77 W (<= 10 % duty: 0.08 W avg) | 8 C | 58 C | - | PASS |

### 3.3 Conclusion

No DPAK exceeds 125 C at 50 C ambient in normal operation; the only case above the target is a high-power coil at 20 % duty for longer
than the ~20 s thermal time constant of a minimum-footprint DPAK, which reaches ~163 C (below the 175 C absolute maximum, so no failure,
but outside the design margin).

### 3.4 Mitigation (next PCB revision, no change to parts)

Per high-power output (Q64, Q66, Q68, Q70, Q76, Q78, Q80, Q82 = sol 1-8; the same is cheap for all 28) attach **>= 300 mm2 of F.Cu on the
drain net** to the tab (e.g. a 25 x 12 mm pour beside the tab; the DPAKs sit on a 26.4 mm pitch in y with the S3M tie-back diode between
them, so the pour extends sideways in x) plus 9-12 thermal vias into a B.Cu pour of the same size.  The IR AN-1057 curve (110 C/W at the
minimum footprint, 40 C/W at 1 in2 of 2 oz) gives ~60 C/W for that - `tj_rise_20pct_pour` 62 C, Tj 112 C at 20 % duty.  A full 1 in2
(645 mm2, 25 x 25 mm) per part (40 C/W) is possible for sol 1-8 but not needed.  No different part is required (a D2PAK would also need a
footprint change).

## 4. Fuses

Nominal melting I2t (Littelfuse data sheets; the 239 series data sheet itself is served only through hosts that block automated access -
the 239 values were taken from distributor specification listings that reproduce the data-sheet table; the 217 table was read directly):

| fuse | positions | type | nominal melting I2t | cold R | previously used | source |
|---|---|---|---|---|---|---|
| 0217008.MXP 8 A fast | F114 (+18 V) | 217 | **198.16 A2s** | 6.8 mOhm | 198 | Littelfuse 217 data sheet table (8 A row: 80 A @ 250 VAC interrupting, 130 mV drop) |
| 0239007.MXP 7 A Slo-Blo | F112 (+50 V) | 239 | **not retrievable** (the 3 A / 5 A trend, I2t ~ I^1.67, extrapolates to ~530 A2s) | - | 347 (313 7 A) | the 313 7 A value (347 A2s) is kept as the conservative reference |
| 0239005.MXP 5 A Slo-Blo | F111, F113, F106-F110 | 239 | **302.836 A2s** | 19.9 mOhm | 302.8 | Littelfuse 239 data sheet via distributor listing (10 kA interrupting @ 125 V) |
| 0239003.MXP 3 A Slo-Blo | F116, F103-F105 | 239 | **129.51 A2s** | - | 200 (313 3 A) | distributor listing of the 239 table |
| 0239.750MXP 0.75 A Slo-Blo | F115 (+12 V digital) | 239 | **5.425 A2s** | - | 7.16 (313 3/4 A) | distributor listing of the 239 table |

Time-current requirements: 239 (UL 248-14): 110 % 4 h minimum, 135 % 1 h maximum, 200 % 5 s minimum / 2 min maximum; 217 (data-sheet
table, 8-15 A): 150 % 30 min minimum, 210 % 30 min maximum, 275 % 0.05-2 s, 400 % 0.01-0.4 s, 1000 % <= 0.04 s.

Results (`inrush`, switch-on at the mains peak into every capacitor; `gi_string`, cold #44 string fired at the peak) against 20 % of the
melting I2t (the level below which a fuse does not age):

| fuse | event | I2t (A2s) | melting I2t | ratio | peak current | bridge IFSM | result |
|---|---|---|---|---|---|---|---|
| F113 5 A | +5 V raw inrush, 250 ms | 1.49 | 302.8 | 0.5 % | 33 A | GBU8J 200 A | PASS |
| F114 8 A fast | +18 V inrush | 7.07 | 198.2 | 3.6 % | 52 A | GBJ1510 240 A | PASS |
| F111 5 A | +20 V inrush | 4.07 | 302.8 | 1.3 % | 47 A | GBJ1510 240 A | PASS |
| F116 3 A | +12 V power inrush | 1.25 | 129.5 | 1.0 % (was quoted against 200) | 25 A | GBU8J 200 A | PASS |
| F112 7 A | +50 V inrush | 6.66 | 347 (313 stand-in) / ~530 | 1.9 % / 1.3 % | 53 A | GBPC35 400 A | PASS |
| F106-F110 5 A | G.I. cold start (18 x #44, fired at the peak) | 9.19 (3.16 in the first 30 ms) | 302.8 | 3.0 % | 38.8 A | BTA16 ITSM 160 A, I2t 128 A2s | PASS |
| F103-F105 3 A | one AE-23-800 40 ms pulse, 16.6 A | 11.0 (16.6^2 x 0.04) | 129.5 | 8.5 % per pulse | 16.6 A | - | PASS (was quoted as ~8 vs ~200) |
| F115 0.75 A | +12 V digital: buck soft-start, no capacitor inrush through the fuse; steady 0.75 A max (CPU switch matrix, Fliptronic, 8-driver) | - | 5.4 | - | - | - | N/S (no inrush path) |

All margins are kept: the largest is 8.5 % (per coil pulse on the 3 A branch fuses, which is what the OEM 3 A branch fuses also see).

## 5. Connector and track currents

Ratings: **Molex KK 396** (26-60-4xxx / 6410, 3.96 mm, tin) **7.0 A maximum per circuit** with 18 AWG (Molex KK 396 product
specification PS-08-50-001; derate for multi-circuit loading); **Molex KK 254** (22-23-20xx / 6410-05A, 2.54 mm) **4.0 A maximum**
(PS-10-07-001).  Currents below are RMS for AC and switched loads (bridge leg currents from `bridge_loss.cir`), average for DC rails.

| connector / pins | net | load carried (sustained design case; bound) | per pin | of 7 A | note |
|---|---|---|---|---|---|
| J101-1, -2 | AC9_A / AC9_B (9 VAC -> F113 -> BR2) | 3.4 A rms at 3 A +5 V output | 3.4 A | 49 % | single pins |
| J101-4+5, -6+7 | AC13_A / AC13_B (13.3 VAC -> F114 -> BR1) | 5.5 A rms at the 3 A design load; **9.5 A rms with all incandescent lamps**; 12.4 A at the 8 A fuse limit | 2.7 / 4.7 / 6.2 A | 39 / 68 / 89 % | two pins per leg, as the OEM harness |
| J102-1+2, -3+4 | AC16_A / AC16_B (16 VAC -> F111 -> BR4) | 4.8 A rms at 2.5 A DC; 8.6 A at the 5 A fuse limit | 2.4 / 4.3 A | 34 / 61 % | two pins per leg |
| J102-5+6, -8+9 | ACSOL_A / ACSOL_B (51 VAC -> F112 -> BR3) | 5.1 A rms at 3 A DC; 10.4 A at 7 A | 2.6 / 5.2 A | 37 / 74 % | two pins per leg |
| J112-1+2, -3+5 | AC98_A / AC98_B (9.8 VAC -> F116 -> BR5) | 3.9 A rms at 2.5 A; 4.5 A at 3 A | 1.9 / 2.3 A | 28 / 32 % | two pins per leg |
| J104-1, -2 | ACSOL_A_F / ACSOL_B (fused 51 VAC to Fliptronic II J901) | flipper power: 4 ohm coil pulses of ~16 A for ~50 ms per flip, then the hold winding; <= ~5 A rms during hard play, the same duty the OEM J104 carried | <= 5 A | <= 71 % | single pins, pulsed |
| J104-4, -5 | AC16_A_F / AC16_B (fused 16 VAC) | <= F111 5 A | <= 5 A | <= 71 % | single pins |
| J107-1, -2, -3 | +50V_F103 / F104 / F105 | <= 3 A S.B. each (branch fuses); 16.6 A / 40 ms pulses | 3 A | 43 % | |
| J107-6, J106-5 | +20 V | <= F111 5 A total (flashers) | <= 5 A | 71 % | |
| J114-1+2 | +12V_F | <= F115 0.75 A | 0.4 A | 5 % | |
| J114-3+4 | +5 V | 3 A (buck rating) | 1.5 A | 21 % | |
| J114-5+7 | GND | 3.75 A return | 1.9 A | 27 % | |
| J116/J117/J118-2 | +12VU | <= F116 3 A shared; STTNG gun motors on J118 ~2 A | <= 3 A | <= 43 % | |
| J116/J117/J118-3, -4 | GND, +5 V | return of the above + the +5 V share (<= 3 A total over four connectors) | <= 3 A | <= 43 % | |
| J130-1..9, J127 | SOL01-SOL16 (IRLR3110Z drains) | high-power: 16.6 A x 40 ms at <= 10 % duty = 5.2 A rms (20 %: 7.4 A rms); low-power: 6.5 A pulses, 4.8 A held 100 % | 4.8-5.2 A | 69-74 % | the 20 % machine-gun case exceeds 7 A rms briefly (same on the OEM) |
| J126, J125 | SOL17-SOL24 (flashers) | 6.6 A cold inrush, 1.1 A hot | 1.1 A | 16 % | |
| J122-1..4, J124 | SOL25-SOL28 | as low-power: 6.5 A pulses / 4.8 A held | 4.8 A | 69 % | |
| J122-5, -6, -8, -9 | SOL25_TB..SOL28_TB (tie-back cathodes) | freewheel current, 1.3 A average on a 50 % PWM hold, 7.6 A peaks | 1.3 A | 19 % | |
| J115-2..6 | GI1_IN..GI5_IN (string hot, one 5 A fuse each) | 4.54 A rms per incandescent string | 4.5 A | 65 % | |
| J115-7, -8, -10, -11, -12 | GI_RET (winding return) | 5 x 4.54 A = 22.7 A over five pins (all five wired in the OEM harness) | 4.5 A | 65 % | **board bus: item 5.3** |
| J120-8, -9; J121-7, -10, -11; J119-1 | GI2/GI3/GI1/GI4/GI5_OUT (string hot to the playfield / backbox / coin door) | 4.54 A rms per string (J119 carries only the coin-door share of string 5) | 4.5 A | 65 % | |
| J120-2, -3; J121-1, -5, -6; J119-3 | GIx_RET (string return to MT2) | 4.54 A rms | 4.5 A | 65 % | |
| J133/J134/J135-1..9 | ROW1-ROW8 | 1.0 A x 2 ms strobes, 0.5 A average | 0.5 A | 7 % | |
| J137/J138-1..9, J136-3 | COL1-COL8 | 8 A x 2 ms per 16 ms = 2.8 A rms | 2.8 A | 40 % | |
| J103-1, -2 | GND to the 8-driver board | return of the F103 branch, <= 3 A | 1.5 A | 21 % | |
| J111-1, -2, -3, -5 (KK 254, 4 A) | GI_BIT5 / GI_BIT6 / FLIP_RLY_L / GND | logic (< 20 mA) | - | < 1 % | |
| J113 (IDC 34, 1 A/contact) | data / strobes / BLANKING / ZC / GND | logic | - | - | |
| J105 (DNP) | flipper relay option | - | - | - | not fitted |

### 5.3 Tracks (`copper_audit2.py`: minimum width per layer; 35 um copper on all four layers)

IPC-2221 external 35 um: 1.0 mm carries 2.4 / 3.2 / 3.9 A at 10 / 20 / 30 C rise, 1.6 mm carries 3.4 / 4.6 / 5.5 A (internal layers
per IPC-2221 half of that; IPC-2152 with the adjacent GND plane is between the two).

| net(s) | width | layers (mm of track) | current | rise (external IPC-2221) | result |
|---|---|---|---|---|---|
| AC9_A / AC9_AF / AC9_B (+5 V raw legs) | 1.6 mm | F.Cu 67 + 208, In2 233 + 334, B.Cu 86 | 3.4 A rms | 10 C (In2: ~40 C by IPC-2221, less with the plane) | OK |
| AC16_A / AC16_A_F / AC16_B (+20 V legs) | 1.6 mm | F.Cu 49 + 177, In2 204 | 4.8 A rms (2.5 A DC) | 22 C | OK at the design load; 83 C at the 5 A fuse limit |
| ACSOL_A / ACSOL_A_F / ACSOL_B (+50 V legs) | 1.6 mm | F.Cu 57 + 177, B.Cu 314 + 65 + 181, In2 66 | 5.1 A rms (3 A DC) | 25 C | OK at the design load; 130 C at the 7 A fuse limit |
| AC13_A / AC13_A_F / AC13_B (+18 V legs) | 1.6 mm | F.Cu 67 + 61 + 106 | 5.5 A rms at 3 A DC; **9.5 A rms all lamps** | 30 C; **~100 C** | OK at 3 A; **not at full incandescent load** (item 1.6) |
| +18 V, +20 V, +50 V DC distribution | 1.6 mm (one 1.0 mm F.Cu segment on +18 V) | F.Cu 260-419, In2 151-281, B.Cu 180 | 3 / 2.5 / 3 A DC (5.8 A on +18 V with all lamps) | 8 / 5 / 8 C (34 C at 5.8 A) | OK |
| +50V_F103..F105 | 1.6 mm | F.Cu 47-53 | <= 3 A (16.6 A / 40 ms pulses: 11 A2s, adiabatic rise < 1 C) | 8 C | OK |
| +5 V | 1.0 mm (0.4 mm stubs at the ICs) | F.Cu 910, In2 399, B.Cu 299 | 3 A total, split to J114 / J116-J118 | <= 17 C | OK |
| +12VU / +12V / +12V_F | 1.0 mm | F.Cu 112-333, B.Cu 13-369 | 2.5 / 2 / 0.75 A | 12 / 8 / 1 C | OK |
| SOL01-SOL28 (DPAK drain to the KK pins) | 1.0 mm | F.Cu 24-27 (+ In2 on a few) | 4.8 A held (low-power), 16.6 A / 40 ms pulses | 48 C for a coil held 100 % (4.8 A); pulses adiabatic | marginal for the 14.5 R continuous-duty coils - widen to 1.6 mm in the next revision |
| GI1-5_IN / _OUT / _RET (string hot and return, one string each) | 1.6 mm | F.Cu / In2 / B.Cu 7-164 | 4.54 A rms | 20 C (In2 / B.Cu: 40 C IPC-2221) | OK |
| **GI_RET (return bus of all five strings)** | **1.6 mm, one via** | F.Cu 113, In2 205 | **22.7 A rms** through the trunk J115 -> (18.2, 201.4) (~10 mm), 18 A through (18.2, 201.4) -> (30, 181.8) -> one via -> In2 (30 -> 77.4, 181.8) (~80 mm), 9 A on In2 (78.8 -> 117, 182.4) | far beyond any IPC limit (a 1.6 mm track at 22.7 A would exceed 300 C; a single via carries ~3 A) | **DEFECT - next PCB revision** |

The GI_RET routing is a daisy chain: J115-7/8/10/11/12 -> W1 -> (18.2, 201.4) -> Q12 (F.Cu) and -> via (30.0, 181.8) -> In2.Cu ->
Q16 -> Q14 -> Q18 -> Q10.  The OEM board carries this current on a wide bus along J115 and five harness wires.  Fix: route the bus as a
>= 8 mm wide F.Cu + B.Cu pour along J115 with the five return pins and W1 on it and a via array (>= 12 vias per 5 A), and take each
triac's MT1 to it on >= 3 mm (4.5 A, 20 C rise); or give each triac its own return pin (J115-7, -8, -10, -11, -12 are five pins for
five triacs).  Until then the board must not drive incandescent G.I. strings.

## 6. Production status after this review

| item | status |
|---|---|
| G.I. triac heatsink (matrix 9.6) | **closed** - 7019BG, Tj 111 C |
| bridge heatsinks (matrix 14 / 15) | **closed**: BR3 GBPC3510W + 6224BG; the four low-voltage bridges are Schottky bridges cooled by 2-15 cm2 pours (section 8) - the 7020BG heatsinks are no longer needed |
| DPAK thermal (matrix 14) | closed for normal duty; the 20 % machine-gun case documented, pour recommended (3.4) |
| fuse I2t (matrix 4 / 15) | closed for the 3 A / 5 A / 0.75 A / 8 A fuses; the 7 A value stays a conservative stand-in |
| connector currents (5) | closed - every pin <= 74 % of the KK 396 rating in the sustained design cases |
| **GI_RET bus** (5.3) | **open - PCB revision required before incandescent G.I. use** |
| +18 V winding tracks at full lamp load (5.3) | layout item for the re-route: AC13_A / AC13_B >= 4 mm (11.2 A rms with the Schottky bridge) |
| solenoid output tracks (1.0 mm) for 100 %-held coils | recommendation: 1.6 mm |
| BR3 centre hole | recommendation for the re-route: 5.5 mm NPTH at the block centre |
| +5 V set point | **raised to 5.10 V** (11.3 k / 2.1 k, 0.1 %) - section 9 |

## 7. Sources

* Board: `wpc_power_driver_cost.kicad_pcb` (routed 2026-09-06) read with pcbnew (KiCad 10 flatpak): `.scratch/thermal/board_thermal.py`
  (placement, courtyards, DPAK copper -> `.scratch/thermal/board_thermal.json`), `.scratch/thermal/copper_audit2.py` (track widths),
  `.scratch/nettracks.py GI_RET`, `.scratch/region2.py` (copper at the BR3 centre); 3D render `output/3d/wpc_power_driver_cost-top-4k.png`.
* SPICE: `tools/spice/decks/bridge_loss.cir` (new), `sol_high.cir`, `sol_hold.cir`, `lamp_strobe.cir`, `gi_gate.cir`, `gi_string.cir`,
  `inrush.cir` (edited), limits in `tools/spice/run_all.py`, results `output/spice/RESULTS.md`.
* Diodes Inc GBJ15005-GBJ1510 data sheet DS21219 Rev 8-2, May 2025 (diodes.com/assets/Datasheets/ds21219.pdf).
* Vishay GBU8A-GBU8M data sheet, document 88616, rev 10-Jul-2020 (vishay.com/docs/88616/gbu8a.pdf).
* Vishay GBPC12/15/25/35 data sheet, document 88612, rev 30-Nov-2021 (vishay.com/docs/88612/gbpc12.pdf).
* Infineon / IR IRLR3110Z data sheet (infineon.com, IR 11/09), IRLR024N (12/6/04), IRFR5305 (v01_01, DigiKey mirror).
* STMicroelectronics BTA16 / BTB16 data sheet Doc ID 7471 (values as used since the 2026-09-06 review; the PDF hosts refused access).
* Littelfuse 217 series data sheet (5 x 20 mm fast-acting, table "Electrical characteristic specifications by item"; b-cdn mirror of the
  Littelfuse PDF), Littelfuse 239 series data sheet values via distributor specification listings (Newark / RS / Littelfuse product
  pages: 3 A 129.51, 5 A 302.836 (0.0199 ohm), 0.75 A 5.425 A2s).
* Boyd (Aavid) Board Level Heatsinks Catalog (info.boydcorp.com / mouser.com "Aavid-Board-Level-Heatsinks-Catalog.pdf"): index by device
  and thermal resistance ("natural convection thermal resistance based on a 75 C heat sink temperature rise"), pages 27 (7019, 7020, 7025),
  29 (7022), 34 (5770 clip), 67 (5840 clip-on), 77 (6222 / 6223 / 6224 bridge-rectifier baskets).  DigiKey 7020BG 1625705; 6223BG
  1625608 (8.87 USD @1, 6.14 @1000); Future Electronics 6224BG 6.42 USD; Jameco 577002B00000G "32 deg C/W".
* Ohmite W series (WA-T220-101E 12 C/W at 10 W) and Fischer SK 104 (25.4 STS 14 C/W, 38.1 STS 11 C/W), Wakefield 637 series (637-10ABPE
  12.7 C/W) were evaluated and rejected: they need PCB holes for their solder pins / tabs.
* Molex KK 396 product specification PS-08-50-001 (7 A per circuit), KK 254 PS-10-07-001 (4 A); IPC-2221 track current formula.
* Vishay GBPC3510W-E4/51: DigiKey 605926 (wire-lead version; the -E4/51 without W has 0.25 in faston lugs and cannot be fitted to the
  wire-lead footprint - corrected in `tools/sourcing.py`).

## 8. Not verified

* Live distributor prices of the heatsinks and hardware (estimates in `tools/sourcing.py`); the B&F Fastener Supply part numbers.
* The 239 7 A melting I2t (F112); the ST BTA16 Rth j-c revision (2.1 vs 2.5 C/W); the metal-face side of the GBJ / GBU as assembled
  (both sides are free); the real Rth j-a of the DPAKs with the inner ground plane (110 C/W assumed); the natural-convection derating of
  the Boyd values at the smaller temperature rise (1.05 / 1.15 assumed); the backbox air temperature (50 C assumed).
* Nothing was changed on the PCB; every fit statement is from courtyards and catalogue drawings, not from a physical trial.

## 8. Discrete Schottky bridges for the low-voltage rails (design change, 2026-09-07)

Decision (coordinator, from item 1.6): BR1, BR4, BR2 and BR5 become discrete bridges of four identical D2PAK Schottky diodes; BR3 keeps the
GBPC3510W block under the 6224BG basket.  Implemented in `tools/design_cost.py` (`rect_block(kind='sch', diodes=...)`): **D101-D104**
(+18 V, 13.3 VAC), **D105-D108** (+5 V raw, 9 VAC), **D109-D112** (+20 V, 16 VAC), **D113-D116** (+12 V power, 9.8 VAC), footprint
`Package_TO_SOT_SMD:TO-263-2` (pad 1 = tab = cathode).  Net names are exactly the ones the block pads carried: D101 AC13_A_F -> +18V,
D102 AC13_B -> +18V, D103 GND -> AC13_A_F, D104 GND -> AC13_B, and likewise (AC9_AF / AC9_B -> +5V_RAW, AC16_A_F / AC16_B -> +20V,
AC98_A_F / AC98_B -> +12VU); ERC 0, the rest of the netlist is unchanged (`.scratch/nets.json`).  The four 7020BG heatsinks and eight M3
screws / nuts of section 1.4 are removed from the BOM; the GBJ1510 / GBU8J sourcing entries stay for reference only.

### 8.1 Part

**STMicroelectronics STPS20M100SG-TR** - 100 V, 20 A power Schottky rectifier, D2PAK, tape and reel (ST DS6169 Rev 5, February 2019;
IHS mirror of the ST PDF).  DigiKey 2122461 (in stock, 1878 pcs at the time of the review): 1.58 USD @1, 0.782 @100, 0.519 @1000
(reel; 16 per board = 1600 for 100 boards, so 0.52 USD used) - `tools/sourcing.py` key `SCH20100`.  Candidates rejected: onsemi
FSV20100V (TO-277, not D2PAK), Vishay VS-20TQ100SPBF (no reachable datasheet / stock data), onsemi MBRB20100CT and ST STPS20H100CG
(dual common-cathode, TO-263-3).

| parameter | value | condition |
|---|---|---|
| VRRM | 100 V | |
| IF(AV) | 20 A | D2PAK, Tc = 130 C, delta 0.5 |
| IFSM | 350 A | 10 ms sinusoidal, non-repetitive |
| Tj max | 150 C | |
| Rth(j-c) | 1.2 C/W | D2PAK |
| VF max (typ) | 0.73 (0.66) V @ 10 A, 0.85 (0.775) V @ 20 A, Tj = 25 C; 0.60 (0.53) V @ 10 A, 0.69 (0.61) V @ 20 A, Tj = 125 C; 0.55 / 0.455 V typ @ 5 A, 25 / 125 C | pulse 380 us |
| conduction loss (data sheet) | **P = 0.425 IF(AV) + 0.0088 IF(RMS)^2** per diode | Tj = 125 C |
| IR max | 40 uA @ 25 C, 40 mA (10 typ) @ 125 C | VR = 100 V - at the 13-26 V the bridges see and Tj <= 110 C the leakage is ~1-3 mA per diode, i.e. < 50 mW |
| Rth(j-a) vs copper under the tab (Fig. 9, FR4, 35 um) | 70 / 55 / 46 / 39 / 35 / 33 / 31 / 30 C/W at 0.5 / 1 / 2 / 5 / 10 / 15 / 20 / 40 cm2 | 2 oz outer copper taken as 10 % better (assumption, section 8.5) |

Reverse voltage: each diode blocks the DC rail voltage (the AC node swings between the rails, not to -Vpk): +18 V 18.8 V peak (21.6 V at
+15 % mains unloaded), +20 V 22.6 (26.0) V, +5 V raw 12.7 (14.6) V, +12 V power 17.6 (20.3) V -> >= 3.8x margin to 100 V.
Surge: `inrush` peaks with the Schottky bridges F114 71 A, F111 60 A, F113 55 A, F116 36 A (all up from 25-52 A because the Schottky
drops less) against IFSM 350 A; the I2t stays at 0.9-5.3 % of the fuses' melting values (section 8.4).

SPICE: `models.lib` `DSCH20100 D(Is=2.3e-7 n=1.05 Rs=0.0182 ...)`, fitted to the 25 C typical VF (0.55 V @ 5 A, 0.66 V @ 10 A, 0.86 V
at 20 A - slightly above the 0.775 V typical, i.e. pessimistic for the rails); every bridge element of `psu`, `psu_maxload`,
`psu_brownout`, `psu_12vu`, `inrush`, `zero_cross`, `gi_dim` and `bridge_loss` uses it.  Dissipation is taken from the data-sheet
equation (Tj = 125 C), not from the model.

### 8.2 Per-diode dissipation and copper (`bridge_loss.cir`; IF(AV) = Iavg / 2, IF(RMS) = Irms / sqrt 2 per diode)

| bridge, case | Iavg (A) | Irms leg (A) | Vdc (V) | P per diode (W) | bridge total (W) | Rth(j-a) for Tj <= 110 C at 50 C (C/W) | copper specified per diode, 2 oz | Rth assumed | Tj (C) |
|---|---|---|---|---|---|---|---|---|---|
| +18 V, all 64 lamps + buck | 6.45 | 11.2 | 14.3 | **1.92** | 7.7 | 31.2 | **15 cm2** (D101 + D102 share a 30 cm2 +18V pour; D103 on AC13_A_F, D104 on AC13_B 15 cm2 each) | 29.7 | **107** |
| +18 V, 3 A design point | 3.00 | 5.9 | 15.8 | 0.79 | 3.2 | 76 | same | 29.7 | 74 |
| +18 V, 8 A (F114 rating) | 8.00 | 13.4 | 13.8 | 2.49 | 10.0 | 24 (~30 cm2) | same | 29.7 | 124 (informational, < 150 C) |
| +20 V, 2.5 A | 2.50 | 5.2 | 19.6 | 0.65 | 2.6 | 92 | **4 cm2** (D109 + D110: 8 cm2 +20V pour; D111 / D112 4 cm2) | 36 | 73 |
| +20 V, 5 A (F111 rating) | 5.00 | 9.3 | 18.3 | 1.44 | 5.8 | 42 | same | 36 | 102 |
| +5 V raw, buck 3 A out | 1.69 | 3.4 | 10.5 | 0.41 | 1.6 | 146 | **2 cm2** (D105 + D106: 4 cm2 +5V_RAW pour; D107 / D108 2 cm2) | 41 | 67 |
| +5 V raw, 2.4 A out | 1.33 | 2.8 | 10.7 | 0.32 | 1.3 | 190 | same | 41 | 63 |
| +12 V power, 2.5 A | 2.50 | 4.0 | 12.3 | 0.60 | 2.4 | 100 | **2 cm2** (D113 + D114: 4 cm2 +12VU pour; D115 / D116 2 cm2) | 41 | 75 |
| +12 V power, 3 A (F116 rating) | 3.00 | 4.7 | 11.7 | 0.73 | 2.9 | 82 | same | 41 | 80 |
| BR3 GBPC3510W, 3 A (unchanged) | 3.01 | 5.1 | 56.2 | 5.7 (block) | 5.7 | 13.1 (block, Tj 125) | 6224BG basket | 11.8 | 117 |

Whole-bridge model power balance (25 C Vf model): +18 V all lamps 11.0 W, 3 A 4.2 W; +20 V 3.4 W; +5 V raw 2.0 W; +12 V 2.9 W - 20-40 %
above the data-sheet figures, as expected for the cold-Vf fit.  Total copper for the four bridges: 60 + 16 + 8 + 8 = **92 cm2** (7.5 % of
the 1226 cm2 board); every pour is on a net that exists anyway (rail or AC leg).  The AC-leg pours double as the wide tracks the legs need
(item 5.3): AC13_A_F / AC13_B carry 11.2 A rms with all lamps lit.

### 8.3 Rail numbers with the Schottky bridges (block bridges in brackets)

| rail / case | deck, check | Schottky | (GBJ / GBU) |
|---|---|---|---|
| +18 V, 2.8 A lamps + 1 A buck, average | psu `v18_avg` | **15.3 V** | 13.8 |
| +18 V, all 64 lamps + buck, minimum | psu_maxload `v18_min` | **13.5 V** | 11.9 |
| +18 V, all lamps, 88 % mains | psu_brownout `v18_min` | 11.7 V | 10.3 |
| +12 V digital (from +18 V), all lamps / 88 % mains | psu_maxload / psu_brownout `v12_min` | 12.0 / 10.9 V | 11.0 / 9.5 |
| +5 V raw minimum at 3 A | psu `vin5_min` | **10.0 V** | 8.3 |
| +5 V raw minimum at 3 A, **88 % mains** | psu_brownout `vraw_min` | **8.3 V** (UVLO stop 5.5 / 6.0 V worst; 5.10 V needs >= 5.8 V) | 6.5 |
| +12 V power at 2.5 A, minimum / average / ripple | psu_12vu `v12u_min` / `v12u_avg` / `v12u_ripple` | **11.6 / 12.2 V / 1.2 V** | 10.5 / 11.1 / 1.1 |
| +12 V power, 88 % mains | psu_brownout `v12u_min` | 10.1 V | 9.1 |
| +12 V power unloaded maximum (25 V capacitor) | psu_12vu `v12u_max_unloaded` | 16.7 V | 15.9 |
| +20 V minimum, 4 A flasher burst / 8-flasher cold inrush | psu / psu_maxload `v20_min` | 17.8 / 12.8 V | 16.5 / 12.1 |
| inrush peaks F113 / F114 / F111 / F116 | inrush `ipk_*` | 55 / 71 / 60 / 36 A | 33 / 52 / 47 / 25 |
| inrush I2t F113 / F114 / F111 / F116 (A2s, % of melting) | inrush `i2t_*` | 2.8 (0.9 %) / 10.5 (5.3 %) / 5.5 (1.8 %) / 1.9 (1.5 %) | 1.5 / 7.1 / 4.1 / 1.2 |
| zero-cross detector (fused 9 VAC leg) | zero_cross | 60 Hz, 7.4 ms high, sample node min -0.10 V | 7.3 ms, -0.23 V |

Suite: **211 of 211 checks pass** (`output/spice/RESULTS.md`).

### 8.4 Fuses with the Schottky bridges

The lower forward drop raises the switch-on peaks by 40-50 % (the winding resistance now limits alone); all I2t ratios stay far below
the 20 % ageing limit: F113 0.9 %, F114 5.3 %, F111 1.8 %, F116 1.5 % of the melting values of section 4.  The G.I. and +50 V
results are unchanged.

### 8.5 Assumptions to verify on the first article

* Rth(j-a) of a D2PAK on 2 oz copper taken as 0.9 x the ST 35 um curve; the pours are on the same layer as the tabs, uninterrupted,
  and not shared with other heat sources.  If the layouter can only give 10 cm2 to the +18 V diodes, Tj rises to ~111 C at full lamp
  load (still far below 150 C); with 20 cm2 it drops to ~104 C.
* The 2.5 ohm all-lamps load model draws 6.45 A from the higher Schottky rail; real filaments (resistance rising with voltage) draw
  ~5.9 A, so the 1.92 W per diode is slightly pessimistic.
* Diode Vf at the operating Tj (~100 C) is ~0.1 V below the 25 C model: the real rails sit 0.1-0.2 V above the simulated values.

## 9. +5 V set point: 5.10 V

Inputs (coordinator): board copper from the buck output to J114 ~15-20 mOhm after the re-route, CPU harness 30-60 mOhm, load up to 3 A,
MC34064 reset threshold 4.65 V typical (4.70 V maximum), no-load maximum at the board connector 5.20 V.

| | 5.00 V, 1 % divider (before) | **5.10 V, 0.1 % divider (implemented)** |
|---|---|---|
| divider R264 / R265 | 10.5 k / 2.0 k | **11.3 k / 2.10 k** (E96), Yageo RT0805BRD07 0.1 % 25 ppm thin film |
| nominal Vout = 0.8 V (1 + R264 / R265) | 5.000 V | 5.105 V (`buck_5v` 5.105 V at 1 A, 5.091 V at 3 A) |
| tolerance (TPS54360B Vref 0.792-0.808 V = +-1 %, resistor ratio) | +-1 % + 0.84 x 2 % = +-2.7 % | +-1 % + 0.84 x 0.2 % = **+-1.2 %** |
| Vout range at the board | 4.865-5.135 V | 5.044-5.166 V |
| maximum at the connector, no load | 5.135 V | **5.17 V** (< 5.20); SPICE 3 -> 1 A overshoot 5.19 V |
| worst-case at the CPU, 3 A, 80 mOhm, load regulation -14 mV | **4.61 V - below the 4.70 V reset threshold** | **4.79 V** (`psu` `v5_cpu_worst` 4.86 V with the nominal set point) |
| worst-case at the real 2.6 A load | 4.64 V | 4.82 V |
| 1 -> 3 A load-step dip at the board | 4.90 V | 5.00 V (`buck_5v` `vout_step_min`; 4.90 V at the CPU through 80 mOhm - the dip is 0.5 ms, the stacked worst case reaches 4.69 V only with the worst-tolerance part AND the worst harness AND a full step at once) |
| raw input needed (Vout = 0.97 Vin - 0.5) | 5.67 V | 5.77 V - the raw rail minimum at 88 % mains is now 8.3 V (Schottky bridge), UVLO 5.9 / 5.5 V unchanged |

A 5.15 V set point would exceed 5.20 V at the connector (5.21 V worst case) and was not chosen; 5.10 V with 1 % resistors would give
5.24 V worst case, hence the 0.1 % parts (+0.10 USD per board).  The `buck_5v` / `psu` / `psu_maxload` / `psu_brownout` / `bridge_loss`
decks and their checks run at 5.10 V (`v5_min` 5.05-5.15 V, `v5_cpu_worst` >= 4.70 V, `vout_step_min` >= 4.75 V, `vout_step_max` <= 5.5 V),
`uvlo_sweep.py` too.  The +5 V loads (74HCT logic, CPU board, DMD controller) are 5 V +-5 % parts (4.75-5.25 V): 5.17 V maximum is inside.

## 10. As built (2026-09-07, routed board v8)

Pour areas actually filled around the D2PAK tabs (`tools/rail_pours.py`, F.Cu + B.Cu, 3 x 3 via arrays where no other net runs under
the tab; 97 of 144 via positions could be used):

| bridge | tab net | filled copper (F+B) | diodes on it | per diode | P at the design maximum | Rth(j-a) est. (ST curve, 2 oz x 0.9) | Tj at 50 C ambient |
|---|---|---|---|---|---|---|---|
| BR1 +18 V | +18V | 9.6 cm2 | D101, D102 | 4.8 cm2 | 1.92 W (64 incandescent lamps + buck, 6.45 A) | ~37 C/W | ~121 C (LED machine / 3 A: ~76 C) |
| BR1 | AC13_A_F / AC13_B | 7.8 / 8.7 cm2 | D103 / D104 | 7.8 / 8.7 cm2 | 1.92 W | ~34 C/W | ~115 C (3 A: ~74 C) |
| BR4 +20 V | +20V | 4.5 cm2 | D109, D110 | 2.2 cm2 | 1.44 W (5 A) / 0.65 W (2.5 A) | ~45 C/W | ~115 C / ~79 C |
| BR4 | AC16_A_F / AC16_B | 3.8 / 10.3 cm2 | D111 / D112 | 3.8 / 10.3 | 1.44 / 0.65 W | ~38 / ~33 | ~105 / ~72 C |
| BR2 +5 V raw | +5V_RAW | 3.3 cm2 | D105, D106 | 1.7 cm2 | 0.41 W | ~50 C/W | ~71 C |
| BR2 | AC9_AF / AC9_B | 2.4 / 2.3 cm2 | D107 / D108 | 2.4 / 2.3 | 0.41 W | ~46 C/W | ~69 C |
| BR5 +12 V power | +12VU | 6.4 cm2 | D113, D114 | 3.2 cm2 | 0.73 W (3 A fuse) | ~42 C/W | ~81 C |
| BR5 | AC98_A_F / AC98_B | 3.4 / 3.4 cm2 | D115 / D116 | 3.4 | 0.73 W | ~41 C/W | ~80 C |

The +18 V bridge therefore meets the 125 C junction target at the full incandescent load (the 15 cm2 / 110 C goal of section 8 did not fit
between C5, C8 and the fuse column) and runs ~75 C on an LED-equipped machine; all other bridges stay under 90 C at their fuse ratings.
BR3 keeps the GBPC3510W block + 6224BG basket (M4 through the new 5.5 mm hole H9).  Bus copper on the finished board (DC, 20 C, from
`copper_resistance.py`): +5 V C4 -> J114 52 mOhm (the SPICE margin analysis in section 9 assumed 80), +18 V bridge -> column MOSFET
sources 14.8 mOhm, +20 V 5.1 mOhm, +12 V power 21 mOhm, G.I. string J115 -> fuse 2.8 mOhm, G.I. return J115 -> triac MT1 4.0 mOhm
(the section 6 defect is fixed: 5 mm outer-layer track).  Solenoid outputs are 1.6 mm outer-layer tracks (Coil class).  Open: the DPAK
drain pours (>= 300 mm2 per solenoid MOSFET for the 20 %-duty machine-gun case) do not fit the 2 mm component spacing and are not
implemented; the devices are rated for <= 10 % duty of an AE-23-800 (section 4).
