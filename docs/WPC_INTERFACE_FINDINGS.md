> Earlier design/review record. See [current release status](RELEASE_STATUS.md) for superseding component choices, copper stackup, results and unresolved gates.

# WPC power driver board (A-12697-3) - interface facts for a drop-in replacement

Research record for the cost-optimised board, written while checking whether it will work inside a *Star Trek: The Next Generation*
(Williams, 1993, WPC-DCS, Fliptronic II, 8-driver board) machine.  Every fact carries its source; where the sources disagree or are silent it
says so.  "Assumed" = what the design assumed before this review; "Found" = what the sources say; "Status" = right / wrong / changed.

## Sources

| tag | source |
|---|---|
| **[SCH]** | Williams *WPC Schematic Manual* 16-9834.2 (January 1995), scanned PDF (22 pages, 436 dpi JBIG2) at `https://o.pinside.com/4/78/20/47820bf780b80c8b60dfa1a05b4be5626e784d91.pdf`; pages used: 3-4 power wiring, 5 CPU board (16-9060), 7-9 power driver board "16-9057, PWB 5763-12405-01, sub-assembly A-12697, assembly A-12698", sheets 1-3.  The strobe-to-latch wiring on sheet 3 was traced numerically on the bitmap (`tools/spice/../.scratch` scripts, not shipped) because the line spacing is 13 px. |
| **[MAN]** | STTNG operations manual 16-50023-101 (`/home/lolz0r/tng/Star_Trek_TNG_OPS.pdf`, scan without text): p.1-38 LED list, p.1-39 fuse list, p.2-8 driver-board parts list, p.2-44 solenoid/flasher table, p.3-4 lamp circuit, p.3-8/3-9 solenoid & flashlamp circuits, p.3-10 G.I. circuit and block diagram, p.3-23 gun circuit, p.3-24 8-driver board, p.3-29 CPU board connectors, p.3-30 audio board, p.3-31 DMD controller, p.3-32 Fliptronic II, p.3-33..3-35 driver-board connector tables. |
| **[PW]** | pinwiki.com *Williams WPC* page (wikitext fetched 2026-09-05): sections "LEDs on the MPU", "LEDs and test points on WPC-089 Power/Driver Boards", "WPC and WPC-S Games With No Solenoid, Flasher or Feature Lamps, A Blanking Signal Issue", "Controlled Lamp Operational Description", "General Illumination Problems", "GI Lamps Not Dimming", "Check fuses F114 and F115 message", "Low Coil Voltage", "Failed Capacitors" (MC34064). |
| **[PWX]** | pinwiki.com *WPC Transformers* page (winding table). |
| **[PWB]** | pinwiki.com *Leon Borre WPC CPU board repairs* (blanking LED timing, U21/U5). |
| **[PM]** | PinMAME `src/wpc/wpc.h` and `src/wpc/wpc.c` (github.com/vpinball/pinmame, master, fetched 2026-09-05). |
| **[FW]** | FreeWPC (github.com/bcd/freewpc, master): `include/platform/wpc.h`, `include/platform/wpc-mmap.h`, `kernel/lamp.c`, `kernel/triac.c`, `kernel/ac.c`, `kernel/sol.c`, `include/system/sol.h`, `kernel/flip.c`, `kernel/init.c`, `platform/wpc/start.s`. |
| **[TH]** | forums.tomshardware.com thread "TECH: Williams Transformer Voltages - ST:TNG" (unloaded secondary voltages measured on an STTNG at 120.5 V line). |
| **[TOS]** | Toshiba "TBD62083A series, TBD62084A series usage considerations" (docget did=30610). |
| **[LF]** | Littelfuse 239 datasheet values as published on the LCSC product page C3158794 (0239005: 302.836 A2s); 217 8 A: 198 A2s (Littelfuse 217 datasheet, via search snippet); OEM 3AG 313 values from the Littelfuse 313/315 datasheet (octopart copy). |
| **[IR]** | Infineon IRLR3110Z datasheet (RthJC 1.05 K/W, 63 A, Qg 34 nC). |

## 1. BLANKING

* **Found**: the CPU board's ASIC pin 34 originates the blanking signal; "it is inverted 3 times by U21 and U5 before being distributed to
  J204, J211, J202 and the blanking LED" [PW].  On the CPU sheet the last stage is U5F (74LS14) whose output drives the blanking LED D19
  through R8 (470 R, LED lit when the output is low) and Q1 (2N3904) through R69 (1 k) [SCH p.5].  At the ribbon the signal is BLANK on
  J211-31 = J113-31 [SCH p.5, p.7].  On the driver board "the blanking signal from the MPU is connected to pin 1 of each of the 74LS374
  buffers (U1 thru U5 and U18)... Normally, this signal is pulled low by the MPU board, indicating that no faults have been detected and the
  system is running as expected. Without a low blanking signal, none of the game features implemented by the driver board will be enabled"
  [PW]; "pin 1 of the LS374 should always test low" [PW, G.I. section].  Sheet 3 [SCH] shows the OC (pin 1) inputs of U2/U3/U4/U5 bussed
  with a 4.7 k pull-up (R227) to VCC.  Timing: D19 "should light when power is applied, then after about 1 second, go off and stay off"
  [PW] ("appx 3 seconds" [PWB]); the manual: "At game turn-on = D19 & D21 on, D20 off; during normal operation = D19 off" [MAN p.1-38].
  The ASIC's watchdog / blanking is kicked by writing 0x3FFF (PinMAME: bit 1 "reset watchdog", bit 2 IRQ enable, bit 7 IRQ ack [PM wpc.h])
  = FreeWPC `WPC_ZEROCROSS_IRQ_CLEAR` with `WPC_CTRL_BLANK_RESET 0x2 | WPC_CTRL_WATCHDOG_RESET 0x4` "always set when writing this
  register" [FW wpc.h]; FreeWPC's start-up code kicks it during the ROM/RAM tests ("Writing a 6 here does not turn off blanking" [FW start.s]),
  i.e. blanking is released by the ASIC only after the firmware runs and keeps kicking the watchdog.
* **Polarity**: HIGH on J113-31 = every latch tri-stated (74LS374 OC is active low) = "blanked"; LOW = running.  The line is pulled up on the
  driver board (R227 4.7 k) and driven low by an open-collector 2N3904 on the CPU board, so an unplugged ribbon or a dead CPU leaves the
  board blanked.
* **Assumed**: BLANKING HIGH = outputs disabled, tied to the 74HCT574 /OE pins, pulled up by SR1.  **Status: right.**  Changed only in
  detail: SR1 is now 4.7 k like R227 (it was 470 R, which would have loaded the 2N3904 with 10 mA).
* Lamp rows are not blanked on the original either (the 74LS74s have no enable); the columns are, which is enough - verified by the
  `powerup` deck.  The extra U6B path that pulls the 1.4 V reference low while blanked is kept (harmless).

## 2. J113 / J211 ribbon pin-out

**Found** [SCH p.7 J113 table, p.5 J211 table, p.9 wire trace] - identical on both ends (straight 34-way cable):

| pin | signal | pin | signal |
|---|---|---|---|
| 1 | SW COL 1 (flipper-opto sense, -1 boards; N/C on -3) | 2 | N/C |
| 3 | SW ROW 1 (idem) | 4 | GND |
| 5 | SW ROW 2 (idem) | 6 | GND |
| 7 | /LMP ROW -> U10-U13 (74LS74 clocks) | 8 | /LMP COL -> U18 |
| 9 | /SOL 2 -> **U3 = solenoids 17-24** (flashers) | 10 | /SOL 4 -> **U5 = solenoids 1-8** (high power) |
| 11 | /SOL 3 -> **U4 = solenoids 9-16** (low power) | 12 | /SOL 1 -> **U2 = solenoids 25-28** (general purpose) |
| 13 | /TRIAC -> U1 (G.I.) | 14 | GND |
| 15 | D7 | 16 | GND |
| 17 | D6 | 18 | GND |
| 19 | D5 | 20 | GND |
| 21 | D4 | 22 | GND |
| 23 | D3 | 24 | GND |
| 25 | D2 | 26 | GND |
| 27 | D1 | 28 | GND |
| 29 | D0 | 30 | GND |
| 31 | BLANKING | 32 | SW J2 (N/C on -3) |
| 33 | SW J1 (N/C on -3) | 34 | ZERO CROSS (driver -> CPU) |

The latch identities were confirmed through their output transistors and the manual's solenoid table (U5-Q7 -> Q59 -> Q69/Q70 = sol 8,
U4-Q7 -> Q43/Q44 = sol 16, U3-Q7 -> Q31/Q32 = sol 24, U2 -> Q20/Q22 = sol 28/27) [SCH p.9, MAN p.2-44].  Register order [PM wpc.h / FW
wpc-mmap.h]: 0x3FE0 = sol 25-28, 0x3FE1 = sol 1-8, 0x3FE2 = sol 17-24, 0x3FE3 = sol 9-16 - i.e. the ASIC's "/SOL n" names do **not**
follow the register order (/SOL 1 = 0x3FE0, /SOL 2 = 0x3FE2, /SOL 3 = 0x3FE3, /SOL 4 = 0x3FE1).  **Note for the modern-board agent**: a
pin map that assigns the strobes "per the CPU register map" (/SOL 2 -> 1-8, /SOL 3 -> 17-24, /SOL 4 -> 9-16) contradicts the traced wiring;
we agree on pin 34 = ZERO CROSS, 31 = BLANKING, 15-29 = data, 7/8 = lamp row/column, 13 = triac and on the pull-ups on the data lines.

* **Assumed**: strobes on odd pins 1-13 (LAMP_COL, LAMP_ROW, SOL_GEN, SOL_HIGH, SOL_FLASH, SOL_LOW, GI), ZERO_CROSS on pin 33, all even
  pins ground.  **Status: wrong - changed** to the table above (`design_cost.py` sheet_cpu).

## 3. Data polarity

* **Found**: on the CPU board the ribbon data lines D0-D7 are driven by U12, a **74LS240** (inverting) gated by DREN [SCH p.5]; the
  display ribbon by a 74LS244 (non-inverting).  On the driver board U2/U3/U4/U5/U1 take the ribbon data directly [SCH p.7, p.9]; only U18
  (lamp columns) takes it through U9, a second 74LS240 ("U9... buffers the column bit pattern for U18" [PW]).  The latch output turns a
  2N5401 PNP on when LOW ("When point A drops low... the coil turns on" [MAN p.3-8]), the 74LS74 rows drive the TIP102 from /Q with D
  from the ribbon ("the processor drives the input of the 74LS74 low, causing a high at output F" [MAN p.3-4]), U18's true data drives the
  ULN2803 (inverting) into the PNP TIP107.  The firmware writes 1 = on (PinMAME solenoid handlers, `core_setLamp` column bit = 1 [PM
  wpc.c/core.c]; FreeWPC `sol_req_on` non-inverted for the 28 board solenoids, `lamp_strobe_mask = 0x1` [FW]).  All of that is consistent
  only if the **ribbon data is active low** (register 1 -> ribbon LOW -> latch Q LOW -> PNP on; columns get two inversions).  The OEM
  SR1 (9 x 470 R) pulls the eight data lines up [SCH p.7], i.e. "no data" reads as 0.
* **Assumed**: true data on the ribbon, bit = 1 -> 74HCT574 Q = 1 -> MOSFET on.  **Status: wrong - changed**: with the real CPU every
  0x00 write would have turned all 28 MOSFETs ON.  Fix: U9 = 74HCT240 inverts /D0-/D7 into the board's true bus; every latch / flip-flop
  stays as it was; SR2 (4.7 k) pulls the ribbon data lines up.  (The modern-board agent chose inverting-output 74HCT564 latches instead -
  the same conclusion, a different implementation; both are correct.)

## 4. Register map and software timing

* Map [PM wpc.h, FW wpc-mmap.h]: 0x3FE0 sol 25-28, 0x3FE1 sol 1-8, 0x3FE2 sol 17-24, 0x3FE3 sol 9-16, 0x3FE4 lamp row, 0x3FE5 lamp
  column, 0x3FE6 G.I. triacs (bits 0-4 strings 1-5, bits 5-7 = T5-T7 on J111 / flipper relay on -1 boards) , 0x3FD4 Fliptronic port A
  (coils written inverted, `~val` [FW]), 0x3FFF zero cross (R bit 7) / IRQ ack / watchdog.  IRQ = 8 MHz / 8192 = 976.6 Hz [PM wpc.c].
* Lamp matrix: "At IRQ time, the column strobe is repeatedly switched among the 8 columns, at a rate of every 2 ms. Thus, the effective
  time to redraw the entire lamp matrix is 16 ms" [FW lamp.c]; PinMAME reads columns every 2 vblanks.  One column (one-hot, bit = 1)
  at a time, 12.5 % duty per lamp -> deck `lamp_strobe`.
* Solenoids: the hardware is refreshed "at IRQ time... every 4 ms"; pulses are `time x 4 ms` with a duty mask 1/8..8/8 applied per 4 ms
  slot; "only one of these can be pulsed at a time" through the shared pulse driver (queue of 8); default `SOL_TIME_DEFAULT 64` (x 4 ms),
  `FLASHER_TIME_DEFAULT 24` [FW sol.c, sol.h].  PinMAME: "Most solenoids don't have a holding coil so the software simulates it by pulsing
  the power" [PM wpc.c].  So: 30-260 ms pulses, PWM holds with 4 ms granularity (125 Hz at 50 %), and several coils on at once only across
  groups -> decks `sol_high`, `sol_low`, `sol_hold`, `psu_maxload` (6 coils at once as the bounding case).
* G.I. dimming: `gi_dim(triac, brightness)` puts the string into `gi_dimming[7 - brightness]`; `triac_rtt` runs every IRQ and, when
  `zc_timer` (ms since the last zero cross) equals that index, writes the latch with the string ON and immediately OFF again ("The triac
  is enabled from the point of the first write to the next zerocross point") [FW triac.c, ac.c]; level 7 "doesn't work because the GI
  string would have to be turned on and off very shortly before the next zerocross".  PinMAME: 8 or 9 IRQs per half cycle, level = on-time
  ratio since the last crossing, "Triac that were turned on before will continue to conduct until next zero cross" [PM wpc.c].  -> deck
  `gi_dim` (5 us latch pulse 1 / 3 / 6 ms after each crossing, both half cycles).
* Zero cross: read as bit 7 of 0x3FFF, "latched value reseted on read" with a FIXME "it seems that the zero cross should just be the live
  zc state" [PM wpc.c]; FreeWPC polls it every IRQ and resets `zc_timer` when the bit is set ("we are currently at a zero crossing"),
  `ZC_MAX_PERIOD 11` ms [FW ac.c].  Expected: a short HIGH pulse at every crossing (120 Hz) - see 5.
* Flippers: Fliptronic II (A-15472-1) handles the flipper coils itself (0x3FD4, EOS and button switches), gets its ~51 VAC from J104 and
  rectifies it on-board [MAN p.3-32, PW "FlipTronics"]; the driver board's relay/opto flipper circuit (U7/U8 4N25, R210/R211, relay) is
  "NOT USED IN A-12697-3" [SCH p.7] -> the DNP relay option is the right call; J105 stays empty.

## 5. Zero-cross circuit

* **Found** [SCH p.7 U6A/U6C, PW]: "keyed from the AC that feeds the 5V circuit, diodes D3 and D38, and the LM339 at U6" [PW].  Each leg
  of the 9 VAC winding is half-wave rectified (D38 after F113, D3 on J101-2) into a 270 R / 270 R divider with 1 nF (R203/R204/C1,
  R202/R205/C12).  **Corrected 2026-09-06 (verification audit, docs/VERIFICATION_MATRIX.md):** re-read at 600 dpi, the D38 sample goes
  to **U6A pin 7 (+)** with the reference on pin 6 (-), and the D3 sample to **U6C pin 8 (-)** with the reference on pin 9 (+) - the pin
  numbers are legible, and they match the LM339 pinout (7 = IN2+, 6 = IN2-, 8 = IN3-, 9 = IN3+).  The reference node is R198 10 k /
  R199 1 k (0.45 V) with R206 27 k from the output (positive feedback for U6C, negative for U6A), both open-collector outputs are wired
  together with R197 10 k to +5 V and go to J113-34 and TP4.  Output: HIGH only while the fused leg is positive by more than ~2 V, i.e.
  a **60 Hz SQUARE WAVE, ~7.4-8.1 ms high, with one edge per mains zero crossing** (U6C is logically redundant).  Field confirmation: a
  Pinside owner timed TP4 with an Arduino pulse timer and got **~8100 us pulses, "close enough to 8.33 ms for a 60 Hz signal"** on the
  healthy board, and dimming failed once a degraded detector's high pulse fell below ~90 us (Pinside topic 22018, "WPC Zero Cross point
  not working - Solved").  PinMAME's 120-per-second latched flag is therefore the ASIC reacting to **both edges** of this square wave (its
  own FIXME says it may simply be the live state); a 120 Hz pulse train would give the ASIC 240 edges per second.  The earlier reading of
  this document ("both samples on inverting inputs, active-HIGH ~1 ms pulse at 120 Hz") was wrong; the pinwiki D3-trace note only says
  both traces must be intact, which does not discriminate.
* **Assumed**: an active-LOW ~1.3 ms pulse (summing both legs through 10 k / 10 k into U6A, threshold 0.26 V); then, wrongly, an
  active-HIGH 120 Hz pulse.  **Status: wrong twice - changed 2026-09-06** to reproduce the OEM waveform with the existing parts: R197 10 k
  now samples the **F113-fused leg of the 9 VAC winding** (net AC9_AF, half-wave through R254 1.5 k / C21 10 n), **R198 is DNP**, the
  sample goes to U6A **pin 5 (+)** and the 0.26 V reference to pin 4 (-).  Deck `zero_cross`: 60 Hz, 7.3 ms high, edges 0.5 ms after /
  before the true crossing, 5.0 V / 0.16 V levels; `gi_dim` now runs the modern suite's machine-level model (real detector + ASIC edge
  model, held vs pulsed gate bit) on this detector.

## 6. Transformer windings, fuses, bridges, capacitors

Winding table [PWX] with the STTNG measurements (unloaded, 120.5 V line) [TH] and the driver-board connector [MAN p.3-33/34]:

| winding (nominal) | colour | connector | measured unloaded | makes | fuse [MAN p.1-39] |
|---|---|---|---|---|---|
| 9 VAC | red | J101-1,2 | 9.86 VAC | +5 V raw (BR2, C5) | F113 5 A S.B. |
| 13.3 VAC | blue-white | J101-4..7 | - | +18 V lamps (BR1, C6/C7) and, on the original, the 7812 +12 V digital [PW] | F114 8 A fast |
| 16 VAC | white-red | J102-1..4 | 17.07 VAC | +20 V flashers (BR4, C11) | F111 5 A S.B. |
| **51.4 VAC** | black-yellow | J102-5,6,8,9 (and J104 to the Fliptronic board) | **55.2 VAC** | "+50V" = **70-75 V DC** ("TP6... will actually measure 70 - 75VDC" [PW]; "Coil power for WPC games is nominally about 70VDC" [PW]) | F112 7 A S.B. |
| 9.8 VAC | white-green | J112-1,2 / 3,5 | 12.47 VAC | +12 V power, unregulated (BR5, C30) - "used to power motors, optos, and other game features" [PW] | F116 3 A S.B. |
| 6.8 VAC | yellow / yellow-white ... | J115 | 7.87 VAC | G.I. strings (F106-F110 5 A S.B.) | - |

The manual's "Black-Yellow, 16VAC" for J102-5..9 is a typo (J104 says "50VAC" for the same wires) [MAN p.3-33].  The +50 V DC rail was
designed for 36 VAC; **status: wrong - changed** (decks, bleeder 2 x 15 k 2512, S3M tie-backs on the coil groups, TP6/TP8 names; the
100 V MOSFETs, S1M/S3M and 100 V capacitors are fine at the 78-83 V unloaded peak).  The regulated +12 V comes from the +18 V rail on the
original ("AC voltage is rectified to about 18VDC by BR1... D1 and D2 drop... then the LM7812 at Q2... +12V Digital... fused by F114... path
through F115 to the 12V power header at J114" [PW]) and J116/J117/J118 pin 2 carry the unregulated "+12V POWER" [SCH p.7, PW LED7-TP1];
the manual's wire colours confirm two nets (gray-green to J114 / CPU J210-6,7 / Fliptronic J904-2 / 8-driver J2-6, gray-yellow to the
coin door J2-4, DMD J606-7 and the playfield boards, where the STTNG gun motors sit: "Gray-Yellow +12V" into the motor EMI boards, switched by
sol. 17/18 [MAN p.3-23]).  **Assumed**: +12 V buck from +20 V feeding everything through the 3/4 A F115; +12VU only for an LED.
**Status: wrong - changed**: U21 now runs from +18 V (not interlocked by the coin door, unlike +20 V / +50 V [PW]) and feeds only J114
through F115; BR5 became a GBU8J and C30 a 10000 uF/25 V, and J116/J117/J118 pin 2 are on +12VU (pin 4 = +5 V as on the original).
Fuse choices: ratings and speeds match the manual; the 5 x 20 mm 239 5 A has a nominal melting I2t of 302.8 A2s [LF] (OEM 3AG 313 series,
Littelfuse 313/315 datasheet read 2026-09-06: 3 A 200, 5 A 140, 7 A 347, 3/4 A 7.16 A2s; 312 8 A fast 166 A2s), the 217 8 A 198 A2s [LF]; the switch-on inrush (deck `inrush`) is < 8 A2s on every rail, so the fuses never age from
switch-on, and the bridge surge currents (33-53 A) are far below the GBU8J 200 A / GBJ1510 240 A / GBPC3510 400 A ratings.  The 239 3 A
and 7 A I2t values were not retrieved (Littelfuse blocks automated fetches); the OEM 313 values (200 / 347 A2s) stand in.
G.I.: the triacs sit in the return leg with MT1 on the winding's return pins J115-7/8/10/11/12 and J115-1 = "GND REF" [SCH p.7], the
hot ends J115-2..6 each feed one fuse [SCH p.7]; the block diagram shows the fuse on the hot side and the triac on the return [MAN p.3-10].
**Assumed**: MT1 grounded, J115 returns grounded.  **Status: functionally right, changed** to the OEM topology (GI_RET bus + W1 link) so
that the 5 x 5 A return current stays off the logic ground plane; the pin-to-string order of J115 is still unverified (the manual's colour
table is inconsistent, the scan's lines could not be followed).

## 7. +5 V / +12 V loads

* +5 V consumers on J114/J117 [MAN p.3-29..3-32]: CPU board (J210-4,5), DCS audio board (J3-1,3 - the DCS board takes its +5 V from the
  driver board), DMD controller (J606-5) and through it the display, Fliptronic II (J904-1), 8-driver board (J2-3).  Measured: "the MPU on
  the bench... about 0.3 - 0.5 amps" [pinside via search]; the original LM323K is a 3 A regulator behind a 5 A fuse [MAN, PW].  Estimate:
  CPU 0.5 A, DCS 0.7-0.9 A, DMD controller + display 0.8-1 A, Fliptronic + 8-driver 0.15 A = 2.2-2.6 A.  The 3 A TPS54360B design
  therefore carries 15-35 % margin over the estimate and equals the original regulator's rating; its hard limit is the 4.5 A minimum
  current limit (peak inductor current 3.65 A at 3 A).  Not verified by measurement.
* +12 V digital (J114): CPU switch matrix (LM339 supply, ULN2803 +12 V pin, 1 k pull-ups [SCH p.5]), Fliptronic and 8-driver logic; the
  original 7812 sat behind the 3/4 A F115, so the load is < 0.75 A - the 2 A buck is ample.
* +12 V power (J116/J117/J118): gun motors (2), 16-opto and 7-opto boards, proximity sensors, DMD display +12 V, coin door; bounded by
  F116 (3 A on the 9.8 VAC side) - 2.5 A DC assumed in the decks.

## 8. Other machine-level items

* Coin-door interlock (TZ 1993 onwards): opens +20 V and +50 V [PW] - the +12 V digital must not depend on +20 V (fixed, see 6).
* 8-driver board (A-16100) on STTNG: its coils use J107-1 (+50 V "continuous duty" branch, F103) and +20 V, its logic +5 V / +12 V from
  J114 and ground from J103 [MAN p.3-24] - all present.
* J111: T5/T6/T7 of the G.I. latch on pins 1-3, key 4, ground 5 [SCH p.7] (GPIO used by e.g. the NBA Fastbreak shot clock [PW]) - now
  wired (N/C on STTNG).
* **J104 / J105** [SCH p.7, 600 dpi 2026-09-06]: both 5-pin headers carry pin 1 = 51 VAC **after F112**, pin 2 = the other 51 VAC leg,
  pin 3 key, pin 4 = 16 VAC **after F111**, pin 5 = the other 16 VAC leg (J104 "B.B." -> Fliptronic II J901, J105 "PLFD").  **Assumed**:
  J104-1/2 = the raw winding (unfused).  **Status: wrong - changed** to ACSOL_A_F / ACSOL_B / AC16_A_F / AC16_B (the fuse output legs are
  now global nets); a shorted Fliptronic bridge is again protected by F112 as on the original.
* **J113 pins 2/4/6** [SCH p.7]: pin 2 is labelled "NC", pins 4 and 6 are looped together (not on the ground bus of the sheet), pins
  14-30 even are the ground bus.  The cost board grounds 4 and 6 and leaves 2 open - consistent.
* **J116 / J117 / J118** [SCH p.7]: pin 1 key, pin 2 "+12 V POWER" (unregulated), pin 3 ground, pin 4 "+5 V DIGITAL" - as wired.
* TBD62083A inputs: "Output is off in the open state because input pin has pull down processing" [TOS] - a tri-stated U18 leaves the
  columns off, like the original ULN2803.
* CPU reset: MC34064 at U10 on the MPU (4.6 V threshold) [PW "Failed Capacitors"]; the +5 V buck keeps 5.00 V down to 88 % mains.
* Lamp voltage: with the MOSFET drops the #555 lamps see 6.2 V RMS instead of 5.5 V on the original (rated 6.3 V): brighter, roughly 3x
  shorter incandescent life; irrelevant with LEDs (deck `lamp_strobe`).

## Undetermined

* J115 pin-to-string order (hot pins 2-6, return pins 7/8/10/11/12 established; which pin is which string is not).
* The 239-series 3 A / 7 A / 0.75 A melting I2t values (datasheet not reachable); the inrush margins are large enough that this does not
  change the conclusion.
* The exact +5 V current of a DCS + DMD machine (estimate 2.2-2.6 A) and the +12 V power load (assumed 2.5 A).
* Whether the WPC ASIC latches the zero-cross edge or samples the level (PinMAME's own FIXME); the board now produces the OEM waveform
  either way.


## Verification audit 2026-09-06

Row-by-row verification of every integration point against the scan and the decks: `docs/VERIFICATION_MATRIX.md`.  Findings that changed
this document: the zero-cross waveform (section 5, corrected above - a 60 Hz square wave, the design was changed), J104 (fused legs),
J113 pins 2/4/6, the 313/312 fuse I2t values.  New decks: `gi_gate` (triac dissipation - the specified 25 C/W clip heatsink fails the
Tj check with a full incandescent string, ~20 C/W or better is needed), `gi_string` (cold-start I2t through F106: 9.2 A2s = 3 % of the
239 5 A melting I2t), `ribbon` (end-to-end 74LS240 -> ribbon -> 74HCT240 -> 74HCT574 -> DPAK with the 6809E/ASIC timing: 145 ns setup,
150 ns hold against 20 / 5 ns), and the machine-level `gi_dim`.  Still unverified: the 239 3 A / 7 A / 0.75 A melting I2t (313 values as
stand-ins; all inrush results are < 5 % of them), the J115 pin-to-string order, the real +5 V / +12 V power currents.
