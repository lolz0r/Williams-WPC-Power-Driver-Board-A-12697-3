# Original project audit

The original JLC-3 project already had native KiCad sources and a manufacturing package: four-layer Gerbers, plated/non-plated drills, an SMT BOM and centroid file, a complete purchasing BOM, assembly drawings and STEP/renders. A coherent export did not mean that all selected parts were in JLCPCB inventory. The pre-variant procurement audit recorded shortages in the following parts; it was not suitable for an all-JLC electronics100-board order.

| Part | JLC code | Quantity per board | Recorded public stock |
|---|---|---:|---:|
| LLS2A222MELA | C1582025 | 2 | 0 |
| 26604110 | C17541501 | 2 | 0 |
| 0026604060 | C17656945 | 1 | 0 |
| STPS20M100ST | C222114 | 4 | 0 |
| 3517 | C3029536 | 32 | 0 |
| 0239.750MXP | C3157012 | 1 | 0 |
| IPD90N10S4L06ATMA1 | C5440942 | 28 | 1 |
| 26604070 | C587091 | 3 | 0 |
| B41252A7109M000 | C6130373 | 5 | 0 |
| STPS20M100SG-TR | C969989 | 12 | 2 |

JLC-100 is an independent variant. The original source files recorded in `research/baseline-sources.json` remain unchanged, as checked by `reports/inventory-design.json`. The new BOM includes all populated through-hole electronics, separate fuse holders and multipart connectors, plus separately sourced mechanical hardware. Public stock is not reserved.
