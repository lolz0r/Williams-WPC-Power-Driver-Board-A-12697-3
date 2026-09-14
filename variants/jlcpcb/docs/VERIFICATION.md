> Current revision: JLC-3. See [prototype changes and current evidence](PROTOTYPE_JLC3.md); historical regulator results below describe the superseded JLC-2 circuit. Use the current exported BOM.

# JLC-2 verification

Fresh Linux verification uses KiCad 10.0.6, ngspice 47, the supplied STTNG L7 ROM and the final routed JLC-2 native source. Exact inputs and report hashes are bound by `output/release-candidate/reports/verification-manifest.json`. No previous Mac run is presented as fresh evidence.

The additional pre-spin review found and corrected disconnected flasher-clamp returns, producing JLC-2. See [continued verification](PRESPIN_VERIFICATION.md) for fresh PinMAME gameplay, netlist-driven ROM logic, auxiliary outputs and regulator-sequence investigations. The earlier failed fixtures are retained.

The [subsequent analog-review addendum](CONTINUED_ANALOG_REVIEW.md) establishes convergence of the selected coil replay and adds an energy balance, 72 source-headroom cases and 16 CPU switch-margin cases. Its input-isolation proposal is unbuilt; the native board and the original JLC-2 archives are unchanged.

## Results and limits

| Check | Result | Scope |
|---|---|---|
| Native ERC / PCB DRC / schematic parity | No errors, no unconnected items, no parity issues | Full final board and fresh hierarchical netlist. |
| DRC warnings | 77 retained and individually reviewed | 45 free-ended tracks, 17 one-layer/free-ended vias, 13 offset via junctions and the 2 intentional BR3/H9 mounting warnings. Same-net annular overlap and independent copper connectivity checked. Rules remain enabled. |
| Native source audit | 10,997 checks pass | Original files preserved; existing component positions and pad geometry retained; JLC-2 flasher cathode nets explicitly merged to +20 V; all sixteen pull-ups correctly migrated. |
| Independent copper topology | 1,393 pad checks and 363 net checks pass | Connectivity of native filled geometry; not an independent etch-tolerance or high-frequency analysis. |
| Interface logic | 2,188 checks pass | Includes 1,792 exhaustive register-byte patterns and connector/lamp/GI topology and nine connected flasher clamps. |
| Independent manufacturing parsing | Pass | Gerbonara checks copper-layer inventory, attributed pad coordinates/nets, drilled holes, BOM and placements against native source. The actual checks/counts are in `reports/manufacturing-check.json`. |
| Mechanical CAD | 425 model instances; no missing model files or solid intersections | Nominal library bodies and simplified/conservative envelopes. Model-free mounting holes/test points/fiducials are listed. Actual tolerance, cabinet and harness fit remain untested. |
| Base SPICE | 21 decks / 211 checks pass | Rails, rectification, startup/brownout, drivers, lamp matrix, GI and interface timing. These are engineering subcircuits, not an automatically extracted transistor-level model of the entire PCB. |
| Electrical corners | 66 cases pass | The selected design's voltage/load/component assumptions are recorded in each deck. |
| Reservoir ripple | 24 cases pass | 50/60 Hz, nominal/+10% line, ESR and unequal capacitance. Local ambient must stay ≤60 °C for the selected TDK ripple rating. Fuse-limit loads remain informational. |
| Ripple convergence | 16 comparisons pass | High-line/low-ESR cases at 10 µs and 5 µs differ by less than 0.0004%. Electrical models unchanged. |
| Analytical buck loops | 576 cases pass | Minimum modeled phase margin 61.87°, gain margin 18.12 dB. Averaged approximation; hardware loop injection remains required. |
| TI transient model | 6 startup/load-step cases pass | Includes two modified minimum-current-limit sensitivities; these are engineering perturbations, not manufacturer process corners. |
| Powered-input prebiased startup | Both rails pass | VIN already present, half-charged output, EN held low for 200 µs then released. |
| TI fault sweep | **2 pass; 4 failed/inconclusive** | Both 1 ms short/recovery tests pass. Both forced input-collapse cases fail recovery/reverse-current checks. Both output-powered, initially unpowered-input cases abort numerically and fail checks. |
| TI HCT timing | 6 cases pass | 120/200 pF ribbon, HCT240 delay sensitivity up to 53 ns, HCT574 propagation up to 66 ns, 25 ns setup and 5 ns hold requirements. Gate/load model still requires scope correlation. |
| Additional JLC substitutions | 26 cases pass | LED4 current/power corners and M7 flasher-clamp temperature, storage-time and wiring-inductance sensitivity; pull-up static-current bound also checked. |
| MAME ROM audit | `sttng_l7` good | SHA-256 `7c9657fbd4e5eb2e7d4f70ab3eed01c59b30e3af41a0443d626d77ec876e83cc`. ROM is not redistributed. |
| Fresh MAME diagnostics | 320 s complete | All seven power-driver register addresses exercised; 27 used outputs, unused channel 19 excluded; at most 3 simultaneous commands and no multi-column lamp writes. |
| ROM-driven SPICE | 16 coil channels at both 5 µs and 2.5 µs pass | Worst 10 s command windows, 86 V rail, cold coil resistance, hot MOSFET fit and 4.5 V command. Fresh gameplay and auxiliary-output replays are documented in the continued review. |
| Replay convergence / independent R–L bound | 96 / 16 checks pass | Drain peak remains about 87.71 V. Explicit end-time checks reject incomplete transients. |
| +5 V copper drop | About 30.34 mV at 3 A / 75 °C | Final 0.25 mm mesh; approximately 1.1% change from 0.5 mm. Excludes connector and harness resistance. |
| Simultaneous bridge thermal screening | Eight boundary-condition cases below 125 °C target | Approximate 2 mm copper/dielectric/barrel mesh at 50 °C ambient; worst estimate about 121.15 °C. Small margin and uncalibrated convection/lead models require physical measurements. |

## Open regulator findings

The failed UVLO fixture forces the raw input from normal voltage down to 3 V in 100 µs using an ideal voltage source that can sink current. The prebias fixture drives the output while VIN initially starts at zero. These reveal the unresolved reverse-power/shutdown area of the retained regulator topology. They are not complete models of transformer, bridge, reservoir and harness discharge, and the aborted cases cannot establish a real peak current.

For comparison, startup with VIN already present passes on both rails. That result does **not** close the failed shutdown/backfeed cases. The [continued review](PRESPIN_VERIFICATION.md) now adds full AC/bridge/reservoir switching-model fixtures, including completed precharged-output failures and a +12 V light-load restart overshoot. Physical correlation remains required. No unvalidated protection circuit has been inserted into the board to conceal these findings.

## Numerical investigations retained

The original replay metric rectified the entire diode terminal current, including stored-charge current. Its average varied with timestep. The final rating comparison subtracts ngspice `capcur` and measures positive carrier-conduction current. Original positive terminal-current averages are also retained and remain below the 3 A diode average-current limit. This separation changes the measurement, not the electrical device model. Original coarse/fine results and failed Gear/tighter-tolerance trials remain under `output/verification/`.

Two original reservoir cases aborted with the SPARSE/trapezoidal configuration. The full final sweep uses Gear integration at 10 µs. Both difficult cases were checked at 5 µs; the imbalanced fine case required KLU and 100 Newton iterations. It agrees with the coarse result without changes to the electrical model. The failed original and fine-SPARSE runs remain available.

## Model applicability

SPICE subcircuits use representative device fits, lumped ESR/DCR and assumed load/wiring parameters. The model name `DS1M` in the retained generic flasher deck is an engineering SMA rectifier fit; M7-specific sensitivities are separate. D33/D34 use a generic 1N4148 fit in low-voltage reference circuits; its model breakdown parameter is not a qualification of the selected part above its 75 V rating. TI timing limits apply over the cited voltage/load/temperature conditions. M7 recovery time is swept rather than claimed as a manufacturer guarantee.

The upstream MAME driver has incomplete emulation and is not a full physical playfield. Its service-diagnostic run is supplemented by the fresh 240-second PinMAME six-ball simulation in the continued review. Neither provides exhaustive ball-state coverage. Firmware commands are replayed into circuit models; MAME does not emulate this replacement PCB's analog behavior or its physical watchdog.

The STEP review cannot certify tolerance stack-up, screw passage/engagement, fuse service access, capacitor vents, mating connectors, the backbox or rear standoffs. Library footprint snapshots preserve the native land patterns; matching the snapshot is a consistency check, not independent manufacturer approval. The four 330 µF capacitor envelopes are nominal 8 × 11.5 mm bodies at factory-formed 5 mm pitch. The larger conservative courtyards remain.

See the [first-article procedure](ASSEMBLY_AND_FIRST_ARTICLE.md) for actual cabinet, voltage/current, waveform, thermal and fault measurements. No physical board, load or harness was tested during this work.

Primary model references: [TI TPS54360 model archive](https://www.ti.com/lit/zip/SLVMCT7), [TI reverse-power discussion](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1308507/tps54360b-power-output-without-input-in-test-environment), [ngspice manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf), [ngspice diode capacitor-current explanation](https://sourceforge.net/p/ngspice/discussion/127605/thread/54ae7420/), [TDK B41252](https://www.tdk-electronics.tdk.com/inf/20/30/db/aec/B41252.pdf).
