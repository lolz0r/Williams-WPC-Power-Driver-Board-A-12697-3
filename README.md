# Williams WPC power/driver replacement

> **WARNING: These are unverified, experimental boards. Use at your own risk.**
> No variant has been physically validated or qualified for production. Simulation
> results, CAD checks and manufacturing files do not establish safe or reliable
> operation. Errors may damage the board, connected equipment or pinball machine.
> Independently review the design and complete first-article testing before use.

This project develops a modern replacement for the Williams **A-12697-3 WPC
Power/Driver Board**, with **Star Trek: The Next Generation L7** as the documented
compatibility and emulation target. It provides rectified supplies, regulated
5 V and 12 V rails, 28 coil/flasher outputs, an 8×8 lamp matrix and five general
illumination triac channels. The board has no firmware. Compatibility with every
A-12697 installation has not been established.

## Variants and sourcing options

| Location | What it contains | Quantity and status |
| --- | --- | --- |
| [JLC-100](variants/jlcpcb-100/README.md) | Latest separate native KiCad variant, derived from JLC-3 with stocked alternative parts, mixed SMT/through-hole assembly files and connector-orientation guides. | Electronics selected for **100 boards plus spares**, using dated JLCPCB inventory snapshots. Experimental; software checks pass, physical and assembler acceptance gates remain open. |
| [JLC-3](variants/jlcpcb/README.md) | Earlier JLCPCB prototype with TPS552892 buck-boost supplies. Its CAD and exports are independent of JLC-100. | Prototype revision with procurement shortfalls. Its standard upload pair covers SMT; through-hole/manual parts and hardware use separate lists. |
| [DigiKey one-board sourcing proposal](variants/jlcpcb-100/output/digikey-1/README.md) | Alternative procurement BOM and itemized USD pricing based on the JLC-100 design. **This is not another released PCB or CPL.** | **One board, no production spares.** Some parts are proposed substitutes requiring engineering review; F115 remains unresolved and unpriced. |
| [Original cost-reduced project](docs/RELEASE_STATUS.md) at the repository root | Preserved parent CAD, earlier regulator design, simulation work and release-candidate exports. | Earlier engineering candidate with its own unresolved verification gates. Root `output/` does not contain the JLC-100 variant. |

Choose the variant first, then use its matching CAD, Gerbers, BOM and CPL.
Substitutions, packages and placement rotations differ between variants.
JLC-1/JLC-2 archives under `variants/jlcpcb/output/` are historical snapshots.

## JLC-100: Gerbers, BOM and centroids

For the latest JLCPCB variant, start with these files:

| File | Purpose |
| --- | --- |
| [Gerbers and drills ZIP](variants/jlcpcb-100/output/release-candidate/gerbers-and-drills.zip) | Bare-board fabrication layers and plated/non-plated drills. |
| [Combined electronics BOM.csv](variants/jlcpcb-100/output/release-candidate/jlcpcb-assembly/BOM.csv) | JLCPCB upload BOM covering all SMT and through-hole electronics, holders and fuse cartridges. |
| [Matching CPL.csv](variants/jlcpcb-100/output/release-candidate/jlcpcb-assembly/CPL.csv) | Matching component centers and corrected supplier placement rotations. Use with the combined BOM above. |
| [BOM/CPL bundle ZIP](variants/jlcpcb-100/output/wpc-JLC-100-BOM-CPL.zip) | Combined upload pair with assembly reference material. |
| [Complete prototype package ZIP](variants/jlcpcb-100/output/wpc-sttng-JLC-100-prototype.zip) | Native CAD, fabrication and assembly outputs, sourcing and recorded verification evidence. |
| [Complete components BOM](variants/jlcpcb-100/output/release-candidate/bom/all-components.csv) | Human-readable assembly/procurement record, including external hardware and zero-quantity DNP/board features. |
| [100-board electronics purchase BOM](variants/jlcpcb-100/output/release-candidate/bom/jlc-electronics-purchase.csv) | Order quantities and stock evidence, including procurement spares. This is not the upload BOM. |
| [External hardware BOM](variants/jlcpcb-100/output/release-candidate/bom/external-hardware.csv) | Heatsinks, screws, nuts and thermal paste for separate procurement and manual fitting. |
| [Native KiCad PCB](variants/jlcpcb-100/wpc_power_driver_cost.kicad_pcb), [schematic](variants/jlcpcb-100/wpc_power_driver_cost.kicad_sch) and [assembly preview](variants/jlcpcb-100/output/release-candidate/3d/perspective.png) | Source design and nominal assembled geometry. |

The combined upload pair describes **one board**. Select the production quantity
in the assembly order; do not multiply CPL entries or include purchasing spares
as placements. There are **440 electronic pieces per board: 345 SMT, 82 soldered
through-hole pieces and 13 inserted fuse cartridges**, grouped into 69 catalog
parts. J115 is purchased as two six-position headers. Separate fuse holders and
cartridges account for the other expanded references.

Read the [upload and manual-assembly instructions](variants/jlcpcb-100/docs/JLCPCB_UPLOAD.md)
and provide the [PCBA remarks](variants/jlcpcb-100/output/release-candidate/jlcpcb-assembly/PCBA-remark.txt).
The cartridge CPL entries use a documented 0.3 mm selection offset for stacked
parts; their physical centers remain at the holders. Heatsinks, fasteners and
paste are in the complete BOM but require separate sourcing and assembly
agreement. An accepted electronics upload alone does not establish complete
mechanical assembly.

Use the [connector orientation guide](variants/jlcpcb-100/output/release-candidate/jlcpcb-assembly/connector-orientation-guide.pdf)
and [preview review notes](variants/jlcpcb-100/docs/CONNECTOR_PREVIEW_REVIEW.md)
to resolve supplier-library discrepancies. The current CPL includes U1 = 90°,
U2/U3 = 270°, J110 = 180° and J113 = 90°; do not apply those offsets again.
J120/J121/J126 are present as C592598 / TE 1-640445-3 and need explicit part
selection and the documented header preparation. Several connector and rectifier
orientations still require assembler review.

For SMT-only work, use the separate [SMT BOM](variants/jlcpcb-100/output/release-candidate/bom/jlc-smt-bom.csv)
and [SMT CPL](variants/jlcpcb-100/output/release-candidate/assembly/jlc-smt-cpl.csv),
with the [through-hole/manual BOM](variants/jlcpcb-100/output/release-candidate/bom/jlc-through-hole-manual.csv)
for the remaining electronics. Generic engineering position reports are not the
assembly upload pair.

The JLC-100 fabrication specification is **four layers, 1.6 mm nominal FR-4,
2 oz finished outer copper / 1 oz inner copper** (70/35/35/70 µm), ENIG and at
least 20 µm finished plated-hole barrel copper. The outline is
449.152 × 272.910 mm. See [FABRICATION.txt](variants/jlcpcb-100/output/release-candidate/FABRICATION.txt)
and [READINESS.json](variants/jlcpcb-100/output/release-candidate/READINESS.json)
for the exact requirements and outstanding gates.

## DigiKey: one-board BOM and pricing

- [DigiKey BOM.csv](variants/jlcpcb-100/output/digikey-1/DigiKey-BOM.csv): original
  and proposed parts, order numbers, references, required/purchase quantities,
  through-hole parts, hardware and substitution notes.
- [Itemized pricing.csv](variants/jlcpcb-100/output/digikey-1/DigiKey-pricing.csv):
  per-part USD prices, quantity breaks, stock snapshots, product source links,
  extended costs and subtotal/complete-total rows.
- [Totals.csv](variants/jlcpcb-100/output/digikey-1/DigiKey-totals.csv): category
  subtotals, minimum-purchase overhead and missing-cost status.
- [DigiKey package ZIP](variants/jlcpcb-100/output/DigiKey-one-board.zip) and
  [sourcing explanation](variants/jlcpcb-100/output/digikey-1/README.md).

The September 14, 2026 estimate has a **$405.60 USD priced purchase subtotal**,
including minimum hardware purchase quantities. Parts allocated to one board
account for $363.30, including one complete thermal-paste syringe; $42.30 is
minimum-purchase excess. Freight, taxes, tariffs, PCB fabrication and assembly
are additional.

**This is a partial estimate: 78 of 79 required procurement lines are priced.**
F115's 0.75 A ceramic time-delay fuse remains required and unpriced, so the final
complete-BOM total is blank. The 28 priced candidate/accessory lines require
engineering review; the JLC-100 SPICE results do not qualify these substitutions.
No DigiKey-specific PCB, Gerbers or CPL has been released.

## Verification and reproduction

JLC-100 retains 230 passing ngspice engineering cases and recorded CAD,
manufacturing, inventory and assembly-file checks. These use engineering models,
including an averaged supply controller. They do not establish physical thermal,
fault, startup, harness-fit or production performance. Stock snapshots are not
reservations. Supplier part selection and manual operations remain review items.

See the variant's [simulation scope](variants/jlcpcb-100/docs/SPICE_SCOPE.md),
[inventory and assembly notes](variants/jlcpcb-100/docs/INVENTORY_AND_ASSEMBLY.md),
[first-article procedure](variants/jlcpcb-100/docs/FIRST_ARTICLE.md), and
[accepted verification manifest](variants/jlcpcb-100/output/release-candidate/reports/verification-manifest.json).
The later [native connector-tab audit](variants/jlcpcb-100/output/verification/revision/native-connector-tabs.json)
checks 37 single-row connector wall directions in nominal CAD; J113 and physical
cable compatibility retain the documented limitations. That audit and the
DigiKey proposal are additional repository records outside the existing complete
prototype ZIP.

Each variant's routed native PCB is authoritative. Open it with its adjacent
schematics, local symbols, footprints and models. Historical placement generators
and one-time migrations must not overwrite the routed source. Follow the chosen
variant's README and verification instructions when regenerating exports.

The large catalog-search cache is retained as lossless gzip; see the
[research storage notes](variants/jlcpcb-100/research/README.md) to unpack it.

The DigiKey CSVs can be regenerated from their saved pricing facts at the
repository root:

```sh
python3 variants/jlcpcb-100/tools/build_digikey_one_board.py
```

For the preserved parent project, use its [release status](docs/RELEASE_STATUS.md),
[verification instructions](docs/VERIFICATION.md), [Gerbers](output/release-candidate/gerbers-and-drills.zip),
[purchase BOM](output/release-candidate/bom/purchase-bom.csv),
[schematic PDF](output/release-candidate/schematic/schematic.pdf) and
[fabrication specification](output/release-candidate/FABRICATION.txt).
Older root exports directly under `output/` are superseded by the parent's
`output/release-candidate/`. The [historical design narrative](docs/HISTORICAL_DESIGN.md)
records earlier selections and estimates.
