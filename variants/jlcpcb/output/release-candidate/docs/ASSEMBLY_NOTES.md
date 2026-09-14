> Current revision: JLC-3. See [prototype changes and current evidence](PROTOTYPE_JLC3.md); historical regulator results below describe the superseded JLC-2 circuit. Use the current exported BOM.

> JLC-2 retains this mechanical and connector assembly scheme. Use the current [JLC-2 report](../README.md) and `output/release-candidate/bom/` for electronic part numbers and readiness. Physical first-article qualification remains open.
**JLC-2 electrical change — STTNG only:** flasher diode cathodes for SOL21–SOL28 now return to +20 V on the PCB. J122 pins 5/6/8/9 and J126 pins 10/11/12/13 are therefore +20 V; J126 pin 9 remains the key. These cathode contacts are unused in STTNG. Verify the actual harness before mating; another game may use a different tieback voltage.

# Assembly notes - cost-optimised WPC Power Driver Board (A-12697-3 replacement)

Current fabrication/assembly status: [RELEASE_STATUS.md](RELEASE_STATUS.md).

## Connector key pins

The Williams harness plugs (Molex KK 396 / KK 254 housings) carry a blocked position; the matching header pin must be **omitted** (pull
the pin out of the header before soldering, or use a header ordered with that position removed).  The positions below were taken from the
A-12697-1 silkscreen film (STTNG manual p.2-9), cross-checked with the manual's connector map (p.3-33, whose printed pin numbers are
mirrored on J104/J105/J106/J113) and with a photographed board (pinwiki `WPC_Power_-Driver_Board.jpg`, blocked slot visible on every header).
"Pin 1 end" is the physical end of the header on this PCB, which matches the original board (verified against the photo).  Board orientation
as in the manual's connector map: transformer connectors J101-J103 on the right edge, J113/J114/J115 on the left edge, J116-J138 along the bottom.

| connector | header | pins | omit pin (key) | pin 1 end | note |
|---|---|---|---|---|---|
| J101 | KK 396 | 7 | 3 | top | 9 VAC (1, 2) / 13 VAC (4-7) |
| J102 | KK 396 | 9 | 7 | top | 16 VAC (1-4) / 51 VAC (5, 6, 8, 9) |
| J103 | KK 396 | 4 | none | top | all four pins GND, plug has no key |
| J104 | KK 396 | 5 | 3 | left | fused 51 VAC to the Fliptronic II board |
| J105 | KK 396 | 5 | 3 | left | copy of J104, empty on STTNG |
| J106 | KK 396 | 5 | **4** | left | the 16-9057 symbol says 2; film, map and photo say 4 - follow 4 (pins 1-4 are open on this board) |
| J107 | KK 396 | 6 | 4 | left | +50 V branches 1-3, +20 V on 5 and 6 |
| J108 | KK 396 | 3 | none | left | +50 V branches, empty on STTNG |
| J109 | KK 396 | 7 | 6 | left | option header, all pins open |
| J110 | KK 396 | 9 | 5 | left | option header, all pins open |
| J111 | KK 254 (0.100") | 5 | 4 | left | T5-T7 GPIO, empty on STTNG |
| J112 | KK 396 | 5 | 4 | left | 9.8 VAC |
| J113 | 2 x 17 0.100" | 34 | none | bottom end, inner column | see below |
| J114 | KK 396 | 7 | 6 | bottom | +12 V digital (1, 2), +5 V (3, 4), GND (5, 7) -> CPU J210 |
| J115 | KK 396 | 12 | 9 | bottom | G.I. secondary: 1 GND REF, 2-6 hot, 7/8/10/11/12 returns |
| J116 | KK 396 | 4 | 1 | right | +12 V power / GND / +5 V (coin door) |
| J117 | KK 396 | 4 | 1 | right | idem (DMD controller) |
| J118 | KK 396 | 4 | 1 | right | idem (playfield) |
| J119 | KK 396 | 3 | 2 | right | G.I. string 5 to the coin door |
| J120 | KK 396 | 11 | 4 | right | G.I. (all five strings; STTNG uses 2, 3, 8, 9) |
| J121 | KK 396 | 11 | 4 | right | G.I. (all five strings; STTNG uses 1, 5, 6, 7, 10, 11) |
| J122 | KK 396 | 9 | 7 | right | sol 25-28 + tie-back cathodes 5, 6, 8, 9 |
| J123 | KK 396 | 5 | 2 | right | sol 25-28 (backbox), empty on STTNG |
| J124 | KK 396 | 5 | 4 | right | sol 25-28 (cabinet) |
| J125 | KK 396 | 9 | **4** | right | backbox flashers; the 16-9057 symbol draws the key at 5, the film/map/photo show 4 - the board is wired for 4 (sol 20 on pin 5) |
| J126 | KK 396 | 13 | 9 | right | playfield flashers; 10-13 = sol 21-24 tie-back cathodes |
| J127 | KK 396 | 9 | 2 | right | sol 9-16 |
| J128 | KK 396 | 5 | 4 | right | sol 13-16 (cabinet), empty on STTNG |
| J129 | KK 396 | 5 | 3 | right | sol 9-12 (backbox), empty on STTNG |
| J130 | KK 396 | 9 | 3 | right | sol 1-8 |
| J131 | KK 396 | 5 | 2 | right | sol 5-8 (cabinet), empty on STTNG |
| J132 | KK 396 | 5 | 4 | right | sol 1-4 (backbox), empty on STTNG |
| J133 | KK 254 (0.100") | 9 | 3 | right | lamp rows (cabinet) |
| J134 | KK 254 (0.100") | 9 | 3 | right | lamp rows (spare) |
| J135 | KK 254 (0.100") | 9 | 3 | right | lamp rows (playfield) |
| J136 | KK 396 | 3 | 1 | right | lamp column 8 (cabinet) |
| J137 | KK 396 | 9 | 8 | right | lamp columns (playfield) |
| J138 | KK 396 | 9 | 8 | right | lamp columns (playfield/backbox) |

J121 key 4 was rechecked directly against the manufacturer manual, PDF page 61
(printed 2-9), on 2026-09-08; the earlier key-3 entry was a transcription error.

Header pins that are electrically open but not key positions (J106-1..3, J109, J110, J111-1..3 on STTNG, ...) stay in place - the plug
expects a pin there or has no plug at all.

### J113 ribbon header - orientation

* Pin 1 is at the **bottom end of the header (the end nearest J114), in the inner column** (toward the board centre); pin 2 is beside it in
  the outer column, pins 33/34 are at the top end.  This is the position printed on the original board ("2 1" at the bottom, "34 33" at the
  top - the connector map on manual p.3-33 prints it upside down).  The ribbon's red stripe (pin 1) therefore goes to the bottom end, exactly
  as on the original board; the CPU end (J211) is unchanged.
* The footprint is a **shrouded IDC box header** (`wpc_cost:3M_N2534_6002_RB`): the polarising notch faces the board interior, i.e. the
  odd-pin row, which is the DIN 41651 convention that keyed IDC sockets follow - a standard keyed ribbon socket can only go on pin 1 to pin 1.
  The original used an unshrouded 2 x 17 header (Williams 5791-12516-00).  If a game's ribbon socket has its key bump on the other side (it
  will not seat in the shroud), fit an unshrouded 2 x 17 0.100" header instead - the pad layout is the same - and mind the stripe.
* Never plug the ribbon rotated: with the stripe at the top end, BLANKING lands on a ground pin and the strobes on data lines, which turns
  outputs on at random.

### Fuses

All positions take **5 x 20 mm** fuses in Keystone 3517 clips (not the original 3AG): F103/F104/F105 3 A S.B., F106-F110 5 A S.B.,
F111 5 A S.B., F112 7 A S.B., F113 5 A S.B., F114 8 A fast, F115 0.75 A S.B., F116 3 A S.B.; F101/F102 are empty clips (not used on
Fliptronic games).  Label the board so the operator does not fit 3AG spares.
