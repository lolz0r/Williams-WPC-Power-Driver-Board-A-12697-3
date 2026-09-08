# Interface parity: cost board vs. Williams A-12697-3 (pin by pin)

Audit date 2026-09-07.  Question answered here: does this board present **exactly the same interface** to the rest of the machine
(CPU board ribbon, wiring harness plugs, fuses the operator replaces) as the original WPC Power Driver Board A-12697-3?
Every connector pin, every fuse and every rail is compared; every difference is listed with a severity, and the ones that could be fixed
in the connector / fuse sections of `tools/design_cost.py` were fixed (section 6 lists the resulting net changes for the PCB).

## Sources

| tag | source |
|---|---|
| **[MAN]** | STTNG operations manual 16-50023-101 (`/home/lolz0r/tng/Star_Trek_TNG_OPS.pdf`): p.1-39 fuse list (PDF p.49), p.2-9 A-12697-1 assembly / silkscreen film (PDF p.61), p.3-33..3-35 connector map + harness wire list (PDF p.131-133). The wire list says what the **STTNG harness** connects; "N/C" there means "no wire in this game", not "no copper on the board". |
| **[SCH]** | WPC Schematic Manual 16-9834.2, power driver board 16-9057 rev 6 (`../wpc_power_driver_modern/.scratch/wpc_sch.pdf` p.7-9 = sheets 1-3, p.5 = CPU board 16-9060), read at 800 dpi. This is the copper: every connector symbol carries its KEY pin and its nets. |
| **[PHOTO]** | pinwiki.com `WPC_Power_-Driver_Board.jpg` (4290 x 2837 px, an A-12697-1 with the flipper relay stuffed - same PCB 5763-12405-01): silkscreen pin numbers and the physical key position (blocked slot / missing pin) of every header. |
| **[ORIG]** | `../wpc_power_driver/tools/design_sch.py` (reverse-engineered original, pin maps taken from [MAN]/[SCH]). |
| **[COST]** | `tools/design_cost.py` after this audit; netlist `.scratch/nets.json`; PCB `wpc_power_driver_cost.kicad_pcb` (pad positions read with pcbnew). |
| **[FIND]** | `docs/WPC_INTERFACE_FINDINGS.md`, `docs/VERIFICATION_MATRIX.md` (2026-09-06; not re-litigated: active-low data, J113 strobe map, BLANKING 31, ZERO CROSS 34, ~70 V "+50V", +12 V split). |

**A warning about the manual's connector map (p.3-33).**  The map prints the pin numbers of **J104, J105, J106 and J113 mirrored**
("5 ... 1" / "2 1" at the top).  The silkscreen film on p.2-9 and the photographed board both show pin 1 on the other end (J104/J105/J106:
pin 1 at the left, J113: pins 1/2 at the bottom end next to J114, pin 1 in the inner column).  The PCB follows the film and the photo
(section 4).  Where the p.3-33 key squares are quoted below, they were re-read with the true numbering.

Verdict legend: **=** identical, **~** electrically equivalent (differs only in something the machine cannot see), **X** discrepancy
(fixed unless marked "open"), **N/C** not used by the STTNG harness.

## 1. J113 ribbon (CPU J211, 34-way, straight cable)

Header: original = unshrouded 2 x 17 0.100" (5791-12516-00), pins 1/2 at the bottom end (next to J114), odd pins in the inner column
[PHOTO silkscreen "34 33" top, "2 1" bottom].  Cost board: `Connector_IDC:IDC-Header_2x17_P2.54mm_Vertical` at (8.22, 128.46) rot 180 -
pad 1 (8.22, 128.46) = bottom-inner, pad 2 (5.68, 128.46) = bottom-outer, pad 33 (8.22, 87.82), pad 34 (5.68, 87.82) = top-outer.
**Same pin-1 position and same column assignment as the real board**; the shroud notch is on the odd-pin (inner) side = DIN 41651
standard, so a standard keyed IDC socket mates pin 1 to pin 1.  CPU-side check [SCH p.5 J211]: pins 2, 4, 6 and 14-30 even are on the
CPU board's ground bus, so grounding 4/6 here (the original loops them together) is harmless.

| pin | original A-12697-3 [SCH sheet 1] | cost board net | verdict |
|---|---|---|---|
| 1 | SW COL 1 (relay option, "NOT USED IN A-12697-3") | N/C | = |
| 2 | NC | N/C | = |
| 3 | SW ROW 1 (option, unused) | N/C | = |
| 4 | looped to 6 (GND on the CPU end) | GND | ~ |
| 5 | SW ROW 2 (option, unused) | N/C | = |
| 6 | looped to 4 (GND on the CPU end) | GND | ~ |
| 7 | /LMP ROW -> 74LS74 clocks, R252 6.8 k pull-up | CLK_LAMP_ROW -> U10-U13 CLK, SR1 4.7 k | ~ (pull-up 6.8 k -> 4.7 k) |
| 8 | /LMP COL -> U18, R251 1.5 k | CLK_LAMP_COL -> U18-11, SR1 4.7 k | ~ (1.5 k -> 4.7 k, lighter load on the ASIC) |
| 9 | /SOL 2 -> U3 (sol 17-24), R255 1.5 k | CLK_SOL_FLASH -> U3-11 | ~ |
| 10 | /SOL 4 -> U5 (sol 1-8), R253 1.5 k | CLK_SOL_HIGH -> U5-11 | ~ |
| 11 | /SOL 3 -> U4 (sol 9-16), R254 1.5 k | CLK_SOL_LOW -> U4-11 | ~ |
| 12 | /SOL 1 -> U2 (sol 25-28), R256 1.5 k | CLK_SOL_GEN -> U2-11 | ~ |
| 13 | /TRIAC -> U1, R257 1.5 k | CLK_GI -> U1-11 | ~ |
| 14 | GND | GND | = |
| 15 | D7 (active low), SR1 470 R pull-up | D7_N -> U9 (74HCT240) -> D7, SR2 4.7 k | ~ (re-inverted on board, section 7) |
| 16 | GND | GND | = |
| 17 | D6 | D6_N | ~ |
| 18 | GND | GND | = |
| 19 | D5 | D5_N | ~ |
| 20 | GND | GND | = |
| 21 | D4 | D4_N | ~ |
| 22 | GND | GND | = |
| 23 | D3 | D3_N | ~ |
| 24 | GND | GND | = |
| 25 | D2 | D2_N | ~ |
| 26 | GND | GND | = |
| 27 | D1 | D1_N | ~ |
| 28 | GND | GND | = |
| 29 | D0 | D0_N | ~ |
| 30 | GND | GND | = |
| 31 | BLANKING (HIGH = latches tri-stated), R227 4.7 k | BLANKING -> /OE of U1-U5, U18; R6/U6B; SR1 4.7 k | = |
| 32 | SW J2 (line-level detector, unstuffed W2) | N/C | ~ |
| 33 | SW J1 (unstuffed W1) | N/C | ~ |
| 34 | ZERO CROSS, driver -> CPU, 60 Hz square wave, R197 10 k pull-up | ZERO_CROSS (U6A open collector, R256 1.5 k pull-up + LED3) | ~ (levels in section 7) |

Key position: none (dual-row header).  Ribbon pin 1 (red stripe) = bottom end, inner column - as on the original board.

## 2. Harness connectors J101 - J138

Key = the header pin that is omitted so the harness plug (with its blocked position) mates.  Every key below was read from the p.2-9
film and confirmed on the photographed board (blocked slot); where the 16-9057 symbol disagrees it is said so.
Pin-1 end = physical position on the PCB, verified against the photo (section 4).

### Transformer inputs and AC pass-through

| conn | pin | original [SCH]/[MAN] | cost board | verdict |
|---|---|---|---|---|
| J101 (7, key 3, pin 1 top) | 1 | 9 VAC red, **F113** side (D38 zero-cross sample) | AC9_A -> F113 | = |
| | 2 | 9 VAC red, other leg (D3) | AC9_B | = |
| | 3 | KEY | N/C | = |
| | 4, 5 | 13 VAC blu-wht, F114 side (loop) | AC13_A -> F114 | = |
| | 6, 7 | 13 VAC blu-wht, other leg (loop) | AC13_B | = |
| J102 (9, key 7, pin 1 top) | 1, 2 | 16 VAC wht-red, unfused leg | AC16_A -> **F111** | ~ (fuse in the other leg of the same winding; J104/J105-4 still get the fused leg) |
| | 3, 4 | 16 VAC wht-red, **F111** side | AC16_B (unfused) | ~ |
| | 5, 6 | 51 VAC blk-yel, unfused leg ("16VAC" in the manual is a misprint) | ACSOL_A -> **F112** | ~ (same remark) |
| | 7 | KEY | N/C | = |
| | 8, 9 | 51 VAC blk-yel, **F112** side | ACSOL_B (unfused) | ~ |
| J103 (4, no key, pin 1 top) | 1-4 | all four GND [SCH]; harness uses 1, 2 | GND, GND, **GND, GND** | **X fixed** (3/4 were open) |
| J104 (5, key 3, pin 1 left) | 1 | 51 VAC after F112 -> Fliptronic J901-3 | ACSOL_A_F | = |
| | 2 | 51 VAC other leg -> J901-1 | ACSOL_B | = |
| | 3 | KEY | N/C | = |
| | 4 | 16 VAC after F111 (N/C in harness) | AC16_A_F | = |
| | 5 | 16 VAC other leg (N/C in harness) | AC16_B | = |
| J105 (5, key 3, pin 1 left) | 1-5 | **parallel copy of J104** ("HDR5 PLFD") - all N/C on STTNG | was FLIP_L_AC / FLIP_R_AC / - / ACSOL_B / ACSOL_B (relay option); **now = J104** | **X fixed** |
| J112 (5, key 4, pin 1 left) | 1, 2 | 9.8 VAC wht-grn, F116 side (loop) | AC98_A -> F116 | = |
| | 3, 5 | 9.8 VAC wht-grn, other leg | AC98_B | = |
| | 4 | KEY | N/C | = |

### DC power outputs

| conn | pin | original | cost board | verdict |
|---|---|---|---|---|
| J106 (5, **key 4**, pin 1 left) | 1-4 | 16-9057 draws the KEY at pin 2 and the F103/F104/F105 +50 V branches on 1/3/4; film, map and photo put the plug key at **pin 4** (all N/C in the harness) | open | **X open (cosmetic)**: the two Williams sources contradict each other; pins left open rather than put +50 V on a keyed position. STTNG uses only pin 5. |
| | 5 | +20 V to backbox flashlamps | +20V | = |
| J107 (6, key 4, pin 1 left) | 1 | +50 V via F103 (continuous duty: sol 25-28, 8-driver) | +50V_F103 | = |
| | 2 | +50 V via F104 (sol 9-16) | +50V_F104 | = |
| | 3 | +50 V via F105 (sol 1-8) | +50V_F105 | = |
| | 4 | KEY | N/C | = |
| | 5 | +20 V (tied to 6) [SCH]; no wire in harness | **+20V** (was open) | **X fixed** |
| | 6 | +20 V to playfield flashlamps | +20V | = |
| J108 (3, no key, pin 1 left) | 1, 2, 3 | +50 V branches F103 / F104 / F105 ("HDR3 CAB") [SCH]; N/C in harness | **+50V_F103 / _F104 / _F105** (were open) | **X fixed** |
| J114 (7, key 6, pin 1 bottom) | 1 | +12 V digital (F115) -> CPU J210-6,7 / Fliptronic J904-2 | +12V_F | = |
| | 2 | +12 V digital -> 8-driver J2-6 | +12V_F | = |
| | 3 | +5 V -> 8-driver J2-3 | +5V | = |
| | 4 | +5 V -> CPU J210-4,5 / DCS J3-1,3 / J904-1 | +5V | = |
| | 5 | GND -> J210-1,3 / J3-4,5 / J904-4,5 | GND | = |
| | 6 | KEY | N/C | = |
| | 7 | GND -> 8-driver J2-1 | GND | = |
| J116 / J117 / J118 (4, key 1, pin 1 right) | 1 | KEY | N/C | = |
| | 2 | +12 V POWER (unregulated BR5/C30) | +12VU | = |
| | 3 | GND | GND | = |
| | 4 | +5 V digital (harness uses it on J117 only) | +5V | = |

### Solenoids and flashers

| conn | pin | original | cost board | verdict |
|---|---|---|---|---|
| J130 (9, key 3, pin 1 right) | 1, 2, 4-9 | sol 1, 2, 3-8 drives (TIP36C collectors) | SOL01, SOL02, SOL03..SOL08 (DPAK drains) | = |
| J132 (5, key 4) "B.B." | 1, 2, 3, 5 | sol 1, 2, 3, 4 (parallel to J130) [SCH sheet 3] | **new: SOL01, SOL02, SOL03, SOL04** | **X fixed** (connector was missing) |
| J131 (5, key 2) "CAB" | 1, 3, 4, 5 | sol 5, 6, 7, 8 | **new: SOL05, SOL06, SOL07, SOL08** | **X fixed** |
| J127 (9, key 2, pin 1 right) | 1, 3-9 | sol 9, 10-16 | SOL09, SOL10..SOL16 | = |
| J129 (5, key 3) "B.B." | 1, 2, 4, 5 | sol 9, 10, 11, 12 | **new** | **X fixed** |
| J128 (5, key 4) "CAB" | 1, 2, 3, 5 | sol 13, 14, 15, 16 | **new** | **X fixed** |
| J126 (13, key 9, pin 1 right) | 1-8 | sol 17-24 drives | SOL17..SOL24 | = |
| | 9 | KEY | N/C | = |
| | 10, 11, 12, 13 | cathodes of D9 (sol 21), D10 (sol 22), D12 (sol 23), D11 (sol 24) - nested non-crossing routing on sheet 3, medium confidence on the 10..13 order; N/C on STTNG | **SOL21_TB, SOL22_TB, SOL23_TB, SOL24_TB** (were open; the diodes were tied to +20V on the board) | **X fixed** - see 5.4 |
| J125 (9, **key 4**, pin 1 right) | 1, 2, 3 | sol 17, 18, 19 | SOL17, SOL18, SOL19 | = |
| | 4 | plug key (film + map + photo; the 16-9057 symbol draws it at 5) | **N/C** (was SOL20) | **X fixed** |
| | 5 | sol 20 | **SOL20** (was the key) | **X fixed** |
| | 6, 7, 8, 9 | sol 21, 22, 23, 24 (STTNG: 6 = sol 21 blue-green, 8 = sol 23 blue-violet) | SOL21..SOL24 | = |
| J122 (9, key 7, pin 1 right) | 1-4 | sol 25-28 | SOL25..SOL28 | = |
| | 5, 6, 8, 9 | D5-D8 cathodes (sol 25, 26, 27, 28 tie-backs; N/C on STTNG) | SOL25_TB, SOL26_TB, SOL27_TB, SOL28_TB | = |
| J123 (5, key 2, pin 1 right) "B.B." | 1, 3, 4, 5 | sol 25, 26, 27, 28 [SCH sheet 3, film key 2] | **SOL25, SOL26, SOL27, SOL28** (was "spare", all open) | **X fixed** |
| J124 (5, key 4, pin 1 right) "CAB" | 1, 2, 3, 5 | sol 25, 26, 27, 28 | SOL25, SOL26, SOL27, SOL28 | = |

### General illumination

| conn | pin | original | cost board | verdict |
|---|---|---|---|---|
| J115 (12, key 9, pin 1 bottom) | 1 | GND REF (yellow-white) | GND | = |
| | 2-6 | 6.8 VAC hot ends -> one fuse each (five parallel wires of one winding) | GI1_IN, GI4_IN, GI2_IN, GI3_IN, GI5_IN | ~ (pin-to-fuse order not readable on the scan; all five pins are the same harness node, any order is electrically identical) |
| | 7, 8, 10, 11, 12 | winding returns = triac MT1 bus | GI_RET (MT1 bus, W1 0 R to GND) | = |
| | 9 | KEY | N/C | = |
| J120 (11, key 4, pin 1 right) "PLFD" | 1, 2, 3, 5, 6 | returns strings 1, 2, 3, 4, 5 (all five wired; STTNG uses 2, 3) | GI1_RET, GI2_RET, GI3_RET, GI4_RET, GI5_RET (1/5/6 were open) | **X fixed** |
| | 7, 8, 9, 10, 11 | hot (fused) strings 1-5 (STTNG uses 8, 9) | GI1_OUT..GI5_OUT (7/10/11 were open) | **X fixed** |
| J121 (11, key 3, pin 1 right) "B.B." | same map as J120 (STTNG uses 1, 5, 6, 7, 10, 11) | same | GI*_RET / GI*_OUT (2/3/8/9 were open) | **X fixed** |
| J119 (3, key 2, pin 1 right) | 1 | string 5 hot (wht-vio) -> coin door | GI5_OUT | = |
| | 3 | string 5 return | GI5_RET | = |

### Lamp matrix

| conn | pin | original | cost board | verdict |
|---|---|---|---|---|
| J137 / J138 (9, key 8, pin 1 right) | 1-7, 9 | columns 1-7, 8 (+18 V high side) | COL1..COL7, COL8 | = |
| J136 (3, key 1, pin 1 right) | 3 | column 8 -> cabinet | COL8 | = |
| J133 / J134 / J135 (9 x 0.100", key 3, pin 1 right) | 1, 2, 4-9 | rows 1, 2, 3-8 (sink) | ROW1, ROW2, ROW3..ROW8 | = |

### Option headers and spares

| conn | pin | original | cost board | verdict |
|---|---|---|---|---|
| J109 (7, key 6, pin 1 left) "FLIPPER SWITCHES PLFD" | 1-5, 7 | wired to the unstuffed 4N25 / relay option ("NOT USED IN A-12697-3") -> floating | N/C | ~ |
| J110 (9, key 5, pin 1 left) "CAB" | 1-4, 6-9 | idem (W4/W5 jumpers, relay contacts, optos - all unstuffed) | N/C | ~ |
| J111 (5 x 0.100", key 4, pin 1 left) | 1, 2, 3 | T5, T6, T7 = 74LS374 U1 Q5-Q7 latching the **active-low** bus: LOW when the register bit is 1 | GI_BIT5, GI_BIT6, FLIP_RLY_L = 74HCT574 U1 Q5-Q7 latching the **true** bus: HIGH when the bit is 1 | **X open (cosmetic on STTNG - N/C)**: polarity inverted for games that use J111 (see 5.5) |
| | 5 | GND | GND | = |

## 3. Fuses and rails

### Fuses F101-F116 (ratings from [MAN] p.1-39, functions from [SCH])

| fuse | original (3AG 6.3 x 32 mm) | protects | cost board (5 x 20 mm, Littelfuse 239 Slo-Blo / 217 fast in Keystone 3517 clips) | verdict |
|---|---|---|---|---|
| F101 | 3 A S.B. "Left Flipper" - **Not Used** (clips empty) | +50 V branch to the pre-Fliptronic flipper (relay option) | clips only, in the DNP relay option; output now terminates at the clip (no J105 connection) | ~ (both open) |
| F102 | 3 A S.B. "Right Flipper" - Not Used | idem | idem | ~ |
| F103 | 3 A S.B. | +50 V sol 25-28 / 8-driver (J107-1, J108-1) | 3 A S.B. | = |
| F104 | 3 A S.B. | +50 V sol 9-16 (J107-2, J108-2) | 3 A S.B. | = |
| F105 | 3 A S.B. | +50 V sol 1-8 (J107-3, J108-3) | 3 A S.B. | = |
| F106 | 5 A S.B. | G.I. #5 wht-vio | 5 A S.B. (string 5) | = |
| F107 | 5 A S.B. | G.I. #4 wht-grn | 5 A S.B. (string 4) | = |
| F108 | 5 A S.B. | G.I. #3 wht-yel | 5 A S.B. (string 3) | = |
| F109 | 5 A S.B. | G.I. #2 wht-org | 5 A S.B. (string 2) | = |
| F110 | 5 A S.B. | G.I. #1 wht-brn | 5 A S.B. (string 1) | = |
| F111 | 5 A S.B. | 16 VAC flasher secondary (BR4) | 5 A S.B. | = |
| F112 | 7 A S.B. | 51 VAC solenoid secondary (BR3, J104/J105-1) | 7 A S.B. | = |
| F113 | 5 A S.B. | 9 VAC +5 V logic secondary (BR2) | 5 A S.B. | = |
| F114 | 8 A N.B. (fast) | 13 VAC +18 V lamp matrix secondary (BR1) | 8 A fast (217) | = |
| F115 | 3/4 A S.B. | +12 V digital to J114 | 3/4 A S.B. | = |
| F116 | 3 A S.B. | 9.8 VAC +12 V power secondary (BR5) | 3 A S.B. | = |

Physical difference (deliberate, cost): 5 x 20 mm instead of 3AG - the operator's spare-fuse kit changes; every fuse sits on the
original fuse's position and keeps its number and rating.  Severity: cosmetic / operational (label the board).

### Bridges and rails

| rail | original | cost board | verdict |
|---|---|---|---|
| "+50V" solenoid (51.4 VAC -> ~70 V DC) | BR3 KBPC35 35 A / 200 V, C8 100 uF 100 V (150 V on rev 6), bleeder 10 k | BR3 GBPC3510, 2 x 2200 uF 100 V, bleeder 2 x 15 k | ~ (stiffer rail: a coil pulse sags to 41 V avg instead of the OEM's exhausted 100 uF) |
| +20 V flashers (16 VAC) | BR4 KBPC35, C11 15000 uF 25 V | BR4 GBJ1510, C11 10000 uF 25 V | ~ |
| +18 V lamps (13.3 VAC) | BR1 KBPC35, C6 + C7 15000 uF 25 V | BR1 GBJ1510, C6 + C7 10000 uF 25 V | ~ |
| +5 V logic (9 VAC) | BR2 KBPC35, C5 15000 uF, R224 0.12 R, LM323K 3 A linear | BR2 GBU8J, C5 10000 uF, TPS54360B buck 3 A (5.00 V, 4.6 V CPU reset never reached) | ~ |
| +12 V digital (J114) | +18 V -> D1/D2 -> LM7812 -> F115 | +18 V -> TPS54360B U21 (2 A) -> F115 | ~ |
| +12 V power (J116-J118) | BR5 KBPC35, C30 15000 uF, unregulated | BR5 GBU8J, C30 10000 uF, unregulated | ~ |
| G.I. 6.8 VAC x 5 | fuse on the hot side, BT138E triac in the return, MT1 bus to J115 returns | fuse, BTA16-600C triac in the return, MT1 = GI_RET bus | = |
| Zero cross | D38 on the F113-fused leg (J101-1) -> U6A(+) -> 60 Hz square wave | R197 on the F113-fused leg (J101-1) -> U6A(+) -> 60 Hz square wave, same phase | = |

## 4. Physical placement and pin-1 orientation (PCB vs. the real board)

Read with pcbnew from `wpc_power_driver_cost.kicad_pcb` and compared with the photographed board (3-33 orientation: transformer
connectors on the right edge, J113 on the left edge, harness connectors along the bottom).

| edge | connectors | pin 1 on the PCB | real board [PHOTO] |
|---|---|---|---|
| right | J101, J102, J103 | top | top ("1" printed at the top end) |
| top | J104, J105, J106, J107, J108, J109, J110, J111, J112 | left | left |
| left | J113 | bottom end, inner column | bottom end, inner column ("2 1" at the bottom, "1" inner) |
| left | J114, J115 | bottom | bottom |
| bottom | J116-J138 | right | right |

Every connector sits on its original position (placement from the p.2-9 film), so the harness dressing is unchanged.  The four new
connectors are **not yet on the PCB** (section 6).

## 5. Discrepancies found (all of them)

| # | item | what differed | severity | status |
|---|---|---|---|---|
| 5.1 | J103-3/4 | open instead of GND | cosmetic (STTNG uses 1, 2) | fixed |
| 5.2 | J105 | carried the DNP relay option's switched AC instead of the J104 copy of the -3 board | blocks drop-in for a harness that uses J105 (none on STTNG) | fixed |
| 5.3 | J107-5, J108-1..3 | open instead of +20 V / +50 V branches | cosmetic | fixed |
| 5.4 | J126-10..13 and the sol 21-24 tie-back diodes | pins open, diodes clamped to +20 V on the board. A harness that feeds a sol 21-24 load from +50 V would have forward-biased that diode into the +20 V rail | blocks drop-in for games with +50 V loads on sol 21-24 (STTNG: flashers, N/C) | fixed: D9-D12 cathodes on J126-10..13 only (as A-12697) |
| 5.5 | sol 17-20 tie-back diodes | the board has S1M diodes to +20 V where the A-12697 has none (D1/D2/D3/D38 belong elsewhere) - same hazard as 5.4 for a harness feeding sol 17-20 from +50 V | blocks drop-in for such a harness (none known; STTNG: +12 V gun motors on 17/18, flashers on 19/20) | **open** - component change, outside the connector scope: mark D1/D2/D3/D38 DNP on such games |
| 5.6 | J120 / J121 | only the STTNG-used pins wired; the original has all five strings on both | cosmetic on STTNG | fixed |
| 5.7 | J123 | "spare, all N/C" instead of sol 25-28 with key 2 | blocks drop-in for a harness using J123 | fixed |
| 5.8 | J125 key | key on pin 5 (from the 16-9057 symbol); film, map and photo show the plug key at pin 4 | **blocks drop-in on STTNG** (the backbox flasher plug would not seat) | fixed: key 4, sol 20 on pin 5 |
| 5.9 | J128, J129, J131, J132 | connectors absent | blocks drop-in for games using them (N/C on STTNG) | fixed in the schematic; PCB footprints to be placed |
| 5.10 | J106-1..4 | open; the 16-9057 symbol has +50 V branches on 1/3/4 with key 2, but film/map/photo have the key at 4 | cosmetic (all N/C on STTNG) | **open** - contradictory sources, left open on purpose |
| 5.11 | J111-1..3 polarity | inverted vs. the original (true bus latched instead of the active-low bus) | cosmetic on STTNG (N/C); blocks drop-in for a game that uses T5-T7 (e.g. shot-clock drive) | **open** - fix would be `latch574(... in_nets=['D0'..'D4','D5_N','D6_N','D7_N'])` for U1 plus an inverting (or P-channel) driver for the DNP relay; outside the connector scope |
| 5.12 | J113 header type | shrouded box header instead of an unshrouded 2 x 17 | cosmetic (pin 1 position identical; notch on the standard side) - use an unshrouded header if the game's ribbon socket is keyed non-standard | note in ASSEMBLY_NOTES |
| 5.13 | ribbon pull-ups | 4.7 k everywhere instead of 470 R (data) / 1.5 k, 6.8 k (strobes) | equivalent (section 7) | none |
| 5.14 | ZERO CROSS pull-up | 1.5 k + LED branch instead of 10 k | equivalent (section 7); 10 k would restore the OEM low-level margin over temperature | none |
| 5.15 | fuse form factor | 5 x 20 mm instead of 3AG | operational | none (deliberate) |
| 5.16 | fused winding leg (J102) | F111 / F112 in the 1/2 and 5/6 leg instead of 3/4 and 8/9 | equivalent | none |
| 5.17 | J115 hot-pin to fuse order | not readable on the scan | equivalent (same node) | none |
| 5.18 | J109 / J110 | headers present, pins open (original: wired to unstuffed option parts) | equivalent | none |

Superseded statements in the earlier docs: `VERIFICATION_MATRIX.md` section 5 rows "J105 relay-switched flipper AC" and "J108/J109/J110/J123 N/C",
`WPC_INTERFACE_FINDINGS.md` "J123 stays empty" - this document is the current word on those connectors.

## 6. Net changes for the PCB (schematic regenerated, ERC 0 violations)

Pad-level diff of `.scratch/nets.json` (56 pins) - no footprint moved, no track edited here:

```
D9-1   +20V -> SOL21_TB        D10-1  +20V -> SOL22_TB        D11-1  +20V -> SOL24_TB        D12-1  +20V -> SOL23_TB
F101-1 FLIP_L_AC -> n/c        F102-1 FLIP_R_AC -> n/c
J103-3 n/c -> GND              J103-4 n/c -> GND
J105-1 FLIP_L_AC -> ACSOL_A_F  J105-2 FLIP_R_AC -> ACSOL_B    J105-4 ACSOL_B -> AC16_A_F     J105-5 ACSOL_B -> AC16_B
J107-5 n/c -> +20V
J108-1 n/c -> +50V_F103        J108-2 n/c -> +50V_F104        J108-3 n/c -> +50V_F105
J120-1 n/c -> GI1_RET   J120-5 n/c -> GI4_RET   J120-6 n/c -> GI5_RET   J120-7 n/c -> GI1_OUT   J120-10 n/c -> GI4_OUT   J120-11 n/c -> GI5_OUT
J121-2 n/c -> GI2_RET   J121-3 n/c -> GI3_RET   J121-8 n/c -> GI2_OUT   J121-9 n/c -> GI3_OUT
J123-1 n/c -> SOL25     J123-3 n/c -> SOL26     J123-4 n/c -> SOL27     J123-5 n/c -> SOL28
J125-4 SOL20 -> n/c (key)      J125-5 n/c -> SOL20
J126-10 n/c -> SOL21_TB  J126-11 n/c -> SOL22_TB  J126-12 n/c -> SOL23_TB  J126-13 n/c -> SOL24_TB
new J128 (KK 396 1x5): 1 SOL13, 2 SOL14, 3 SOL15, 4 key, 5 SOL16
new J129 (KK 396 1x5): 1 SOL09, 2 SOL10, 3 key, 4 SOL11, 5 SOL12
new J131 (KK 396 1x5): 1 SOL05, 2 key, 3 SOL06, 4 SOL07, 5 SOL08
new J132 (KK 396 1x5): 1 SOL01, 2 SOL02, 3 SOL03, 4 key, 5 SOL04
```

Nets removed: FLIP_L_AC, FLIP_R_AC.  Nets added: SOL21_TB, SOL22_TB, SOL23_TB, SOL24_TB.  Suggested positions for the four new
footprints (lower connector row, y = 265.3 mm, rot 180 like J126, pin 1 at the right; x scaled from the p.3-33 map with J127/J130 as
references): J128 pin 1 at x = 251.4, J129 278.0, J131 315.3, J132 341.0 (they fall in the free span between J126, which ends at
x = 222.9, and J133-J135 at x = 349-369).  The J125 change only swaps which pad is drilled-out/keyed: pad 4 becomes the omitted key
pin, pad 5 takes the SOL20 track.  D9-D12 lose their +20 V connection and get one track each to J126-10..13.

## 7. CPU integration (numbers)

* **Data D0-D7 (J113-15..29).**  CPU side: U12 74LS240 (inverting, enabled by DREN during the write): V_OH >= 2.4 V at I_OH = -15 mA
  (2.7 V at -3 mA; 3.4 V typical), V_OL <= 0.4 V at 12 mA (0.5 V at 24 mA).  Board side: U9 74HCT240, V_IH >= 2.0 V, V_IL <= 0.8 V at
  Vcc 4.5-5.5 V, input current +-1 uA, plus the SR2 4.7 k pull-up to +5 V.  Low state: the LS240 sinks 5 V / 4.7 k = 1.06 mA per line
  (OEM SR1 470 R: 10.6 mA) -> V_OL ~ 0.1-0.2 V, margin to V_IL >= 0.6 V.  High state: the pull-up lifts the node above the LS240's own
  V_OH (the output only sources below its ~3.4 V); worst-case margin 2.4 - 2.0 = 0.4 V at full datasheet load, ~1.4 V typical.  The
  OEM 74LS374 inputs needed the same 2.0 V, so any CPU board that drove the original drives this one.  Deck `ribbon` (XSPICE, 6809E
  2 MHz write, 74LS240 25 R / 3.4 V, ribbon 1 R / 120 pF): `rib_low` 0.03 V, `rib_high` 3.44 V, setup 145 ns (needs 20), hold 154 ns
  (needs 5) at the 74HCT574 / 74HCT74 clock edge.  Ribbon unplugged: SR2 holds every line high = data 0 = every output off.
* **Strobes (J113-7..13).**  ASIC outputs -> 74HCT574 CLK / 74HCT74 CLK (V_IH 2.0 V).  Pull-up 4.7 k (SR1) instead of the OEM 1.5 k
  (6.8 k on /LMP ROW): DC sink when low 1.06 mA instead of 3.3 mA - a lighter load on the ASIC; the strobe timing is set by the ASIC's
  totem-pole edges, not by the pull-up.  Unplugged: all strobes held high, no clock edges.
* **BLANKING (J113-31).**  CPU side: 2N3904 open collector (Q1, base R69 1 k from 74LS14 U5F, I_B ~ 2.7 mA).  Load on this board:
  SR1 4.7 k (1.06 mA) + R6 10 k into U6B (0.5 mA) + six 74HCT574 /OE inputs (1 uA each) ~ 1.6 mA (OEM: R227 4.7 k + six 74LS374 OC
  inputs, up to ~3.5 mA) -> V_CEsat ~ 0.1 V against V_IL 0.8 V.  Released (transistor off) the line sits at +5 V through SR1 -> every
  latch tri-stated and the gate pull-downs hold all 28 MOSFETs, the 8 columns and the 5 triacs off (`powerup` deck: 13 nA coil current,
  0.1 nA column current, `blank_unplug` 5.0 V).
* **ZERO CROSS (J113-34, board -> CPU ASIC).**  LM339 U6A open collector, pull-up R256 1.5 k to +5 V plus LED3 through R253 1.5 k
  (OEM: R197 10 k, no LED).  High = 5.0 V (deck `zc_high`).  Low: the LM339 sinks 3.2 mA (R256) + 2.1 mA (LED branch) = 5.3 mA;
  LM339 V_OL 250 mV typical / 400 mV max at 4 mA and 25 C, 700 mV max at 4 mA over the full temperature range; deck `zc_low` 0.16 V.
  Against a 5 V CMOS gate-array input (V_IL ~ 1.5 V) the margin is > 1 V in every case; against a TTL-level 0.8 V threshold it is
  0.4 V at the 25 C datasheet maximum.  Restoring the OEM 10 k (and dropping LED3) would cut the sink current to 0.5 mA and give the
  OEM margin; not changed here (component values are outside this audit's scope).  Waveform: 60 Hz square wave, 7.3 ms high, edges
  0.5 ms after / before the true crossing, same phase as the OEM because the same (F113-fused, J101-1) leg is sampled.
* **+5 V / +12 V feed to the CPU (J114).**  7 pins, key 6, pin 1 at the bottom - identical to the original; J114-4 (+5 V) -> CPU
  J210-4/5, J114-1 (+12 V digital) -> J210-6/7, J114-5 (GND) -> J210-1/3, exactly the STTNG harness wire list.  +5 V: 5.00 V at 3 A,
  4.90 V minimum on a 1 -> 3 A step, holds to 88 % mains (MC34064 reset at 4.6 V never reached); two KK 396 pins per rail (7 A each).
  +12 V digital: 12.0 V at 1 A, 11.0 V with the whole lamp matrix on, behind the same 3/4 A F115.

## 8. Not verified

* The order of the four tie-back cathodes on J126-10..13 (nested routing read on the 800 dpi scan; the harness leaves them open on STTNG).
* J115 hot-pin-to-fuse order (electrically irrelevant, all five pins are one node).
* J106 pins 1-4 and J125 pin 4/5: the 16-9057 symbols contradict the film, the connector map and the photographed board; the
  physical sources were followed for the key pins.  Confirm on a real board before a large production run.
* The CPU-side statement "red stripe at the bottom of J211" comes from a forum search snippet (Pinside, 2026-09-07); the pin-1
  position on the driver side is from the photographed board's silkscreen.
