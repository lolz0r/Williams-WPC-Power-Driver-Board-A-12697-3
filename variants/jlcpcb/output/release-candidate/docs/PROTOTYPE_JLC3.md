# JLC-3 prototype build

JLC-3 replaces both supplies with TPS552892RYQR four-switch buck-boost converters.
Use the three files from the same `output/release-candidate` export:

- `gerbers-and-drills.zip` — bare PCB fabrication.
- `bom/jlc-smt-bom.csv` — JLCPCB SMT BOM with exact LCSC codes.
- `assembly/jlc-smt-cpl.csv` — top-side SMT package centers, millimetres, native rotations.

`READINESS.json` records whether all checks have passed for the exact PCB hash.
The intended use is a controlled first prototype, followed by the measurements in
[ASSEMBLY_AND_FIRST_ARTICLE.md](ASSEMBLY_AND_FIRST_ARTICLE.md). No physical board
has been qualified. Older JLC-1/JLC-2 archives and their supply simulations are
historical and do not describe this regulator revision.

## Electrical and layout changes

The earlier 12 V buck lost regulation as its lamp-supply input dipped below the
required headroom. The asynchronous converters also provided an uncontrolled
output-to-input body-diode path with a precharged output and an empty input.
TPS552892 supports buck and boost operation, shutdown load disconnect and
PFM diode-emulation operation. Both regulators retain their original transformer
feeds; the revision adds no load to the F111 flasher supply.

| Circuit | Selected parts and settings |
|---|---|
| U20, U21 | TI TPS552892RYQR, JLCPCB C19272254; internal VCC, PFM, nominal 395 kHz |
| +5 V feedback | R264 6.65 kΩ / R265 2.1 kΩ, both 0.1%; nominal 5.000 V |
| +12 V feedback | R270 18 kΩ / R271 2 kΩ, both 0.1%; nominal 12.000 V |
| U20 compensation | R266 33.2 kΩ, C36 100 nF, C37 680 pF C0G |
| U21 compensation | R272 42.2 kΩ, C42 330 nF, C43 1 nF C0G |
| Output current limits | R326 13 mΩ / R327 33 mΩ, 1 W 1%; nominal 3.85 A / 1.52 A |
| Intended regulated loads | +5 V: 3 A; +12 V: 0.75 A, retaining F115 |
| L1, L2 | Existing Bourns SRP1265A-100M 10 µH; 15.5 A saturation rating |
| Bypass | Four 10 µF input ceramics, two 10 µF local output ceramics per IC; separate bootstrap and VCC bypasses |

D36/D37 are removed. The IC land pattern and split paste apertures follow TI's
RYQ0021B drawing. Separate ISP/ISN branches reach the output shunt pads. Power
feeds have separate wider connections, and the ground returns use multiple vias.
The two regulator work areas and the crossing tracks were rerouted; C2 moved to
clear the U21 input bank. The rest of the board's component positions, connector
geometry and documented STTNG flasher-clamp wiring are checked against the
preserved source. The detailed migration is in `research/prototype-power-migration.json`.

## Verification and its limits

The final averaged supply fixtures run startup, 20 mA-to-full-load steps,
loss/restart and prebiased-output cases at 50/60 Hz and ±10% line. The 96 cases
include bulk capacitance −20%/+20%, ESR sensitivity, ±20% error-amplifier gain,
and ±1.5% combined reference/divider/temperature sensitivity. The CCM loop
sweep additionally varies compensation capacitance and resistance.

| Model result | +5 V | +12 V |
|---|---:|---:|
| Largest output peak | 5.226 V | 12.570 V |
| Lowest load-step output | 4.828 V | 11.825 V |
| Minimum modeled phase margin | 68.37° | 70.16° |
| Minimum modeled gain margin | 20.04 dB | 24.63 dB |

These are engineering average-model results. TI's public switching model is
encrypted and was not run in ngspice. The model cannot establish switching
overshoot, PFM burst ripple, reverse-current commutation, short-circuit recovery,
EMI or physical stability. Those are first-article scope measurements, not claims
made by the software tests. The current-limit loop is an approximation.

The ROM-driven lamp-matrix fixture now completes its 370 ms window using
`minbreak=1p`. Gear at 1 µs and 0.5 µs and trapezoidal integration at 0.5 µs all
pass 41 checks. The updated replay generator also passes. The largest modeled
column junction temperature is 75.54 °C at 50 °C ambient. This fixes numerical
breakpoint handling without changing circuit parameters or drive waveforms.

Bridge stress cases were rerun with the new regulated 12 V load and reservoir
tolerance. Their constant 2.5 Ω lamp load and sustained flasher load are stress
bounds, not measured gameplay. Some continuous stress cases exceed the AC RMS
fuse ratings. **Keep the specified fuse values.** Measure transformer/fuse RMS
currents under actual diagnostics and gameplay before prolonged full-load use.
The thermal model uses explicit assumed cooling and is not a cabinet measurement.

Failed and superseded candidate experiments remain in
`output/verification/prototype-readiness/`; only `summary.json` and the fixture
audit select evidence for this revision. Earlier averaged trials measured current
in the undriven reference voltage source; their zero RMS values are invalid.
Final fixtures measure the actual behavioral AC drive source.

## Fabrication and assembly

Order 4 layers, 1.6 mm FR-4, Tg ≥150 °C, ENIG, 2 oz **finished** outer copper and
1 oz inner copper (70/35/35/70 µm). Require ≥20 µm finished plated-hole barrel
copper and bare-board electrical test. The routed outline is
449.152 × 272.910 mm. Check the quoted stack and large-board service with JLCPCB.

The local QFN land pattern needs 0.16 mm minimum clearance capability; signal
fanouts use 0.20 mm traces and 0.30 mm drills. Wider power routing retains the
applicable net-class widths. The package's narrow power-pad escapes are short.
The project contains a local courtyard rule for these fanouts; it does not lower
clearances on the rest of the board.

SMT upload files omit through-hole parts and mechanical hardware. Use
`bom/jlc-through-hole-manual.csv`, `bom/external-hardware.csv` and
`assembly/fuse-clip-centers.csv` to complete assembly. There are 32 fuse clips
and 14 fuse cartridges. Confirm QFN pin 1, diode polarity, electrolytic polarity
and all JLCPCB placement rotations in the assembly preview against the included
assembly drawing. Stock snapshots are not reservations.

This remains an **STTNG-specific** reproduction. The JLC-2 flasher return change
is retained: verify J122/J126 contacts and the actual harness before mating.
Follow the connector-key schedule; a no-connect pin is not automatically a key.

Begin with isolated, current-limited supplies and dummy loads. Verify both rails,
startup/shutdown, prebias handling and load steps before connecting a CPU or
machine harness. Measure at the receiving CPU connector as well as the board;
the nominal 5.0 V setting leaves less allowance for resistive harness contacts.

Sources: [TI TPS552892 datasheet](https://www.ti.com/lit/ds/symlink/tps552892.pdf),
[Bourns inductor](https://www.bourns.com/docs/product-datasheets/srp1265a.pdf),
[JLCPCB copper rules](https://jlcpcb.com/help/article/jlcpcb-copper-weight),
[JLCPCB capabilities](https://jlcpcb.com/capabilities/Capabilities).
