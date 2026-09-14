# JLC-100 inventory variant

> **WARNING: These are unverified, experimental boards. Use at your own risk.**
> No physical board has been validated or qualified for production. Passing
> simulation and CAD checks do not establish safe or reliable operation. Errors
> can damage connected equipment; independently review and test a first article.

See the [repository overview](../../README.md) for the preserved parent project,
the earlier [JLC-3 prototype](../jlcpcb/README.md), and the separate
[one-board DigiKey sourcing proposal](output/digikey-1/README.md).

An independent KiCad variant of JLC-3, with electronics selected from public JLCPCB stock for **100 boards plus spares**. The original source files are preserved. Gerbers, drills, BOMs, centroids, schematic/assembly PDFs and a STEP assembly are generated from the updated native design.

**Status: software-checked engineering prototype.** The electronics stock audit passes; required heatsinks, fasteners and thermal paste are external purchases. These items are included in the complete assembly BOM, with heatsinks and fasteners represented in the assembly models. No stock is reserved, and no order has been placed. Physical first-article qualification remains necessary before committing the full run.

- [Complete package](output/wpc-sttng-JLC-100-prototype.zip)
- [Gerbers and drills](output/release-candidate/gerbers-and-drills.zip)
- **[JLCPCB combined SMT + through-hole BOM](output/release-candidate/jlcpcb-assembly/BOM.csv)** and **[matching CPL](output/release-candidate/jlcpcb-assembly/CPL.csv)**
- [BOM/CPL download bundle](output/wpc-JLC-100-BOM-CPL.zip) and [upload/manual assembly instructions](docs/JLCPCB_UPLOAD.md)
- [Complete procurement and hardware record](output/release-candidate/bom/all-components.csv)
- [100-board electronics purchasing BOM](output/release-candidate/bom/jlc-electronics-purchase.csv)
- [Optional SMT-only BOM](output/release-candidate/bom/jlc-smt-bom.csv) and [SMT centroids](output/release-candidate/assembly/jlc-smt-cpl.csv)
- [Through-hole/manual BOM](output/release-candidate/bom/jlc-through-hole-manual.csv) and [engineering placement details](output/release-candidate/assembly/electronics-placement-details.csv)
- [Native board](wpc_power_driver_cost.kicad_pcb), [schematic](wpc_power_driver_cost.kicad_sch) and [assembly preview](output/release-candidate/3d/perspective.png)

For the requested complete electronics assembly, use the combined BOM/CPL pair above. It describes one board and contains 440 matching references, including both J115 headers and separate fuse cartridges/holders. Select 100 boards in the assembly order; procurement spares are not extra placements. Copy [PCBA-remark.txt](output/release-candidate/jlcpcb-assembly/PCBA-remark.txt) into the order remarks: the cartridge CPL entries have a documented 0.3 mm selection offset for stacked assembly. The prior `all-electronics-positions.csv` filename now aliases the valid combined CPL; it must be paired with the new combined BOM. The [local upload audit](output/release-candidate/reports/jlc-assembly-check.json) checks file coverage, centers and library orientation evidence; live JLCPCB import and assembly acceptance have not been tested.

The design has **426 populated electronic references: 345 SMT and 81 through-hole**. Purchasing includes **440 electronic pieces per board**, accounting for separate fuse holders and the two-piece J115 header. Of the SMT placements, **204 are Basic**. All 69 electronic catalog codes pass a quantity check of 100 times per-board usage plus the larger of 10 pieces or 5% spares. The September 13, 2026 Pacific / September 14 UTC snapshots use the smaller of public stock and orderable quantity. The estimated electronics cost including spares is **US$8,524.49**; PCB fabrication, assembly, external hardware, shipping and tax are additional.

In assembly terms, those 440 purchased pieces are **345 SMT, 82 soldered
through-hole pieces and 13 inserted fuse cartridges**. The 81 native through-hole
references combine some holders/cartridges and represent J115 as one reference.
The [external hardware BOM](output/release-candidate/bom/external-hardware.csv)
adds heatsinks, fasteners and thermal paste; these require separate procurement
and agreement on fitting them.

The [connector orientation guide](output/release-candidate/jlcpcb-assembly/connector-orientation-guide.pdf)
and [preview review notes](docs/CONNECTOR_PREVIEW_REVIEW.md) explain the remaining
supplier-library/manual assembly gates. Current CPL rotations include U1 = 90°,
U2/U3 = 270°, J110 = 180° and J113 = 90°. The subsequent
[native connector-tab audit](output/verification/revision/native-connector-tabs.json)
checks 37 single-row headers in nominal CAD; J113 and physical cable fit retain
the documented limitations. This later audit is in the repository, outside the
existing complete prototype ZIP.

## Separate DigiKey estimate: one board

- [DigiKey BOM.csv](output/digikey-1/DigiKey-BOM.csv)
- [Itemized prices and total rows.csv](output/digikey-1/DigiKey-pricing.csv)
- [Cost breakdown.csv](output/digikey-1/DigiKey-totals.csv)
- [DigiKey ZIP](output/DigiKey-one-board.zip) and [scope/limitations](output/digikey-1/README.md)

This procurement proposal assumes **one board with no production spares**. Its
priced purchase subtotal is **$405.60 USD**, including minimum hardware order
quantities. It prices 78 of 79 required lines; F115's 0.75 A ceramic time-delay
fuse remains unresolved and unpriced. Proposed substitutes are flagged for
engineering review and are not qualified by the JLC-100 simulations. The proposal
does not change this variant's PCB, Gerbers or JLCPCB BOM/CPL.

## Recorded verification

The accepted verification contains **230 passing ngspice engineering cases**, covering supply startup/load/restart/prebias and tolerances, replayed drivers, GI, blanking, capacitor ripple and rectifier startup. Native ERC has zero violations. PCB DRC has zero errors, zero unconnected items and zero schematic parity issues; 178 warnings have documented dispositions. Independent Gerber/drill/BOM checks pass 7,909 checks; the inventory design audit passes 219 and the controller land-pattern audit passes 152. The mechanical review reports no collisions or missing models. Eight simultaneous rectifier thermal sensitivity cases pass their stated screening targets (SMT maximum 119.4°C; through-hole maximum 141.2°C at 50°C ambient).

The stiffest simulated crest-start case reaches **244.8 A in one rectifier leg against its 250 A single-pulse rating**. Real winding impedance, hot/cold starts, current sharing, loaded supply waveforms, thermal boundaries and harness fit require measurement. The SPICE models are engineering fits, including an averaged supply controller; they do not establish production qualification. Several stocked connectors need documented trimming/key preparation, and F112 is a soldered time-lag fuse.

Read [inventory and assembly instructions](docs/INVENTORY_AND_ASSEMBLY.md), [simulation scope](docs/SPICE_SCOPE.md), [first-article procedure](docs/FIRST_ARTICLE.md), [DRC warning review](docs/DRC_WARNING_REVIEW.md) and [original project audit](docs/ORIGINAL_PROJECT_AUDIT.md). The package contains dated stock evidence, exact model/deck/log files and checksums. `output/release-candidate/reports/verification-manifest.json` identifies accepted evidence; earlier rejected trials in the working tree are not accepted results.
