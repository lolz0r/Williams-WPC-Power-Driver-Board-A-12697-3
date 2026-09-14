# JLC-3 prototype status

The JLC-3 board is ready for **controlled prototype fabrication and assembly
planning** once the matching export's `READINESS.json` reports
`READY_FOR_CONTROLLED_PROTOTYPE_BUILD`. Use the current Gerber ZIP, SMT BOM and
CPL together. No physical board has been tested or ordered.

The revised supplies and routed board pass the electrical and geometry checks:
zero ERC/DRC errors, zero unconnected nets, zero schematic mismatches, 8,023
independent manufacturing checks, 10,801 source checks, 1,012 supply-fixture
checks and 152 QFN land-pattern checks. The 105 remaining DRC warnings have
item-specific dispositions; rules remain enabled. Mechanical checks cover 439
model instances with no collisions or missing referenced models.

All 96 final averaged supply cases pass. Four complete lamp-matrix replay runs
pass 41 checks each. Updated bridge-loss simulations feed eight passing thermal
sensitivity cases; the largest estimated rectifier junction temperature is
121.32 °C at 50 °C ambient. The independent +5 V copper model estimates 42.5 mV
drop at 3 A and 75 °C, from R326's load pad to J114, excluding harness contacts.
These are numerical estimates, not hardware measurements.

**JLCPCB assembly procurement remains open.** The current BOM has 344 top-side
SMT placements and 419 populated electronic references. JLCPCB's public stock
is insufficient for two retained SMT types: 28 IPD90N10S4L06ATMA1 MOSFETs and
12 STPS20M100SG-TR rectifiers per board. Keep the validated exact parts and use
JLCPCB Global Sourcing or consignment. Source the whole quantity of each part
plus assembly attrition through one permitted inventory channel. Several
through-hole/manual types also require procurement; see
`bom/procurement-shortfalls.csv`. Public stock was not reserved.

JLCPCB describes these options in its
[parts sourcing instructions](https://jlcpcb.com/help/article/pcba-parts-sourcing-instruction).
Exact-part distributor options include
[Mouser's MOSFET listing](https://www.mouser.com/ProductDetail/Infineon-Technologies/IPD90N10S4L06ATMA1?qs=LxJ0xX%2FWJR62lwU%2FrihEDA%3D%3D)
and [DigiKey's rectifier listing](https://www.digikey.com/en/products/detail/stmicroelectronics/STPS20M100SG-TR/2122461).
Confirm availability and JLCPCB acceptance in the actual quote.

Build details, selected values, model limitations and fabrication settings are
in [PROTOTYPE_JLC3.md](PROTOTYPE_JLC3.md). Follow
[ASSEMBLY_AND_FIRST_ARTICLE.md](ASSEMBLY_AND_FIRST_ARTICLE.md) before connecting
an expensive CPU or the STTNG harness. First-article scope, fuse/transformer RMS,
thermal and cabinet-fit measurements remain necessary. The continuous all-lamps
stress envelope is not certified against the installed fuses; retain their
specified values and measure real operation before prolonged full-load use.

The original root project is preserved. JLC-1/JLC-2 archives and earlier supply
experiments are historical. The current hash manifest selects evidence for JLC-3
and does not turn superseded failures into passing results.
