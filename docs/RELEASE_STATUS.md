# Engineering revision — 2026-09-08

**Manufacturing files generated; engineering candidate, not production qualified.**
Use only `output/release-candidate/`. Older files directly under `output/gerbers`,
`output/bom`, `output/3d` and historical review documents describe earlier revisions.

This is a proposed Williams WPC A-12697-3 power/driver replacement: rectified
supplies, 5 V and 12 V buck regulators, 28 coil/flasher outputs, an 8×8 lamp
matrix and five GI triacs. STTNG L7 is the emulation target. There is no firmware
on this board. The routed KiCad PCB is authoritative. The historical placement
generator depends on a missing sibling project and cannot recreate this routing;
explicit overwrite guards now protect the derived PCB and schematic.

## Current construction and parts

* 449.152 × 272.910 mm Edge.Cuts, four layers, nominal 1.6 mm FR-4, ENIG.
  **2 oz FINISHED outer / 1 oz inner copper**, 70/35/35/70 µm. Calculations
  assume at least 20 µm finished plated-barrel copper. Dielectrics: 0.200/0.990/0.200 mm.
* In1 is predominantly GND with an AC16_A trunk. In2 includes the +5 V plane.
  Actual filled copper predicts 30.7 mV board-only +5 V drop at 3 A, 75 °C copper;
  0.25/0.5 mm meshes differ by 0.9%. Contacts, harness and ground drop are additional.
* The +5 V divider is 11.3 kΩ / 2.1 kΩ, 0.1%, nominal 5.105 V.
* All 28 coil/flasher MOSFETs use Infineon IPD90N10S4L06ATMA1, 100 V,
  8.1 mΩ maximum at 4.5 V. DNP DQ3 uses the same part.
* BR1 uses four STPS20M100ST TO-220 rectifiers with individual Boyd
  577202B00000G sinks. D105–D116 retain STPS20M100SG-TR on stitched copper.
  GI sinks are 7020BG; BR3 sink is 6223BG. Fasteners and thermal paste are in the BOM.
* C5/C6/C7/C11/C30: TDK B41252A7109M000, 10,000 µF / 35 V, 25.4×45 mm
  nominal, 26.4×47 mm maximum body, 10 mm pitch, 6±1 mm leads. Ripple checks
  require **measured local ambient ≤60 °C**. The 100 Hz factor 0.9 conservatively
  bounds the manufacturer's frequency curve. C8/C32 are
  Nichicon LLS2A222MELA, 100 V, 25×40 mm nominal.
* Corrected all 33 KK396 connector ordering codes: e.g. seven ways is
  **0026604070**, not 0026604007. J113 uses active vertical **3M N2534-6002-RB**;
  the old 30334-5002HB entry was obsolete and right angle. Its 34 holes now
  specify 0.90 mm finished, within the manufacturer's 0.89±0.08 mm recommendation.
* Four small compensation capacitor MPNs now use stocked KEMET equivalents,
  including replacements for obsolete Samsung 33 nF and 470 pF selections.
* Large capacitor, inductor, connector, heatsink and mounting-hardware models
  use nominal manufacturer dimensions. Fin shapes and fasteners are simplified.
  Full mating harness, component tolerances and cabinet geometry are unavailable.

Sources and availability observations are recorded in [SOURCING_REVIEW.md](SOURCING_REVIEW.md).

## Verification evidence

Reports live under `output/verification/revision/`; native manufacturing checks
are under `output/release-candidate/reports/`. See [VERIFICATION.md](VERIFICATION.md)
for commands and scope. A pass means the stated model/check passed, not that an
unbuilt assembly has been tested.

| Check | Evidence | Limit |
|---|---|---|
| KiCad ERC / DRC / schematic parity | Zero electrical errors, zero opens, zero parity differences; 65 warnings individually dispositioned | Routing stubs retained after a removal experiment broke junctions; warnings remain enabled |
| Interface audit | 2,179 checks, including 1,792 exhaustive register byte patterns | Static mapping; analog timing is separate |
| Audit fault injection | 13 tests pass | Tests intentionally catch wrong nets, mappings, stack or connector MPN |
| Independent filled-copper connectivity | 1,381 pads / 373 nets pass | GEOS planar unions and barrel graph; not an independent full-Gerber connectivity solver |
| Gerber/drill/BOM reconciliation | Independent Gerbonara parsing and checks, X2 pad/net/position attributes, drill hits, outline and BOM fields | Does not replace fabricator DFM or electrical testing |
| Base SPICE | 21 decks / 211 checks pass | Approximate switch/load models |
| Deterministic corners | 66/66 pass; five capacitor voltage bounds pass | Assumed line/load and thermal boundaries |
| Reservoir ripple | 24 cases pass at modeled design loads | ESR, mains frequency, high line and C6/C7 imbalance; fuse-limit case informational |
| Buck loop sensitivity | 576 cases pass; minimum phase margin 61.9°, gain margin 18.1 dB | Averaged current-mode model; physical Bode measurement still needed |
| TI transient buck model | Six cases / 42 checks pass, startup and load steps | Typical vendor model; two 4.5 A limit edits are engineering sensitivities, not vendor process corners |
| VIN-present prebiased startup | Both rails pass; output peaks 5.121 V / 11.967 V | EN held low initially; does not qualify dead-input backfeed |
| TI short/recovery | Both rails recover after 1 ms shorts | Does not establish continuous/repeated short survival or switch SOA |
| Thermal geometry | Eight gap-aware boundary/lead cases below 125 °C; isolated BR1 bound 122.36 °C at 50 °C ambient | 8 W distributed background is assumed; no complete local simultaneous-load thermal qualification |
| Mechanical solids | 411 model instances, zero missing referenced models and zero detected nominal collisions; includes the final J113 and keyed headers | No cabinet/mating cable CAD, tolerance stack or tool-access qualification |
| MAME 0.289 | ROM audit and 320 s service trace; all 27 used outputs exercised | Upstream marks game MACHINE_NOT_WORKING/NO_SOUND; full gameplay uses PinMAME |
| PinMAME | 240 s gameplay, six-ball simulator, launch and scoring observed | Finite scripted gameplay; up to four simultaneous commands, long gun motor runs |
| ROM-to-SPICE | 16 service and 14 gameplay coil channels complete/pass at 5 µs | Finer-timestep verification remains unresolved; these results are not sufficient for transient qualification |
| ROM timestep sensitivity | Only 1 of 3 cases passes at 2.5 µs; two abort | This is an open numerical verification gate, not a PCB test pass |
| Independent RL replay | 30 conduction-only cases pass; maximum modeled junction temperature 67.2 °C | Excludes switching and reverse-recovery losses; does not close the transient gate |

## Open findings and physical release gates

**Open software finding:** the long ROM-driven SPICE transients remain sensitive
to timestep and solver conditioning. Full 5 µs runs pass, but the 2.5 µs check
aborts on channels 1 and 2. Alternative solver/conditioning trials do not yet
establish numerical convergence. The closed-form RL cross-check passes
conduction-only limits; it cannot validate switching peaks or reverse recovery.
No flyback-diode substitution has been applied to the PCB. The combined archive
gate remains blocked pending an explicit disposition of this finding.

1. **Regulator reverse current / power sequencing.** The hard-raw-rail-collapse
   fixture produces reverse inductor current; output-powered/dead-input prebias
   fixtures also encounter model convergence failure. These failed results are
   retained in `vendor-faults`. The TI model's internal D_D1 diode uses n=0.1 and
   is not a characterized power-MOSFET body diode, so the computed reverse-current
   magnitude is not a hardware rating. An output-to-input B560C bypass experiment
   did not close the problem; **no bypass diode was added to the PCB**. The separate
   VIN-present prebiased-start test must not be confused with dead-input backfeed.
   Measure actual reservoir decay and switch/inductor reverse current before
   release. TI confirms that external output power can stress the internal diode:
   [TI support response](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1308507/tps54360b-power-output-without-input-in-test-environment).
2. **Thermal and protection.** Establish simultaneous transformer/bridge/buck/
   MOSFET/GI/capacitor temperatures at high line and sustained representative
   gameplay. Correlate the model with real airflow. Verify actual load R/L,
   inrush, hot resistance, harness parasitics, avalanche/SOA, fuse clearing,
   repeated lamp-row faults, lost flyback paths, hot plugging and ground faults.
   Fuse rating alone is not a protection-coordination result.
3. **OEM interface and mechanics.** J106 pins 1–4 are deliberately open because
   OEM sources conflict on keyed positions; only pin 5 carries +20 V. This is
   not established as a universal A-12697 drop-in. J109/J110 are spare NC. J111 spare GPIO polarity is inverted relative to OEM
   on bits 5–7; STTNG leaves these unused. This also blocks a universal drop-in claim.
   Confirm STTNG harness continuity, connector key orientation, board mounting
   centres, all mating/vent clearances and underside fastener space on real hardware.
4. **Fabrication and assembly.** Obtain the chosen fabricator's DFM acceptance of
   this exact stack, drill/annulus/etch tolerances and electrical test data.
   Availability snapshots are not reserved stock or procurement acceptance.
5. **First article.** Execute [ASSEMBLY_AND_FIRST_ARTICLE.md](ASSEMBLY_AND_FIRST_ARTICLE.md):
   current-limited dummy-load bring-up, scope/Bode measurements, thermal equilibrium,
   controlled fault tests, cabinet service diagnostics and representative gameplay.
   EMC/ESD, vibration, aging and production fixture tests require physical facilities.

Software cannot deliver 100% certainty about an unbuilt board. The package includes
Gerbers, drills/maps, BOM, placement, IPC-D-356, schematic and assembly PDFs, STEP,
three native renders and hashes; **file completeness does not close these gates**.

C5 was also upgraded to the TDK reservoir after the release gate caught 2.905 A
RMS versus a conservative 2.862 A limit for the previous Rubycon part at 50 Hz.
The failed pre-upgrade ripple report is retained as historical evidence.

The final package gate also rejected the earlier ROM replay summaries: some
transients had aborted, and a tiny reverse diode leakage was incorrectly tested
as forward average current. Replay now uses strictly increasing PWL timestamps,
20 ns command transitions, a 5 µs maximum trapezoidal timestep, a measured
end-time gate, positive-only forward diode current and a coil-current physical
bound. Earlier failed reports are retained. Gameplay channels 1, 2 and 16 also
receive a 2.5 µs timestep sensitivity run. These are model checks, not measured
reverse recovery or switch SOA.
