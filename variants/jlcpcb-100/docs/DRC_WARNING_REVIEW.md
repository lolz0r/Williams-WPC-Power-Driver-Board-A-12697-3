# Native DRC warning review

Reviewed 178 warnings from native-final3; zero errors, zero opens, zero schematic parity issues.

| Warning | Count | Disposition |
|---|---:|---|
| lib_footprint_mismatch | 6 | Intentional local silkscreen clipping on six footprints after pad/package changes. Native pad geometry and net parity checked; embedded PCB is manufacturing authority. |
| missing_courtyard | 1 | Inherited non-purchased board feature; independent complete 3D assembly has no missing models or inter-component collisions. |
| npth_inside_courtyard | 1 | Intentional BR3/H9 mounting axis and bridge/basket hardware assembly; physically review stack and torque. |
| silk_over_copper | 11 | Some native body/polarity outlines intersect mask openings. Manufacturing exporter subtracts solder mask from silk; assembly Fab outlines remain complete. Reference labels remain visible. |
| track_dangling | 75 | Existing/local fanout tails remain after package rerouting. Native final connectivity and clearances pass. Retained copper tails are not assembly parts; do not remove entire reported tracks blindly, because mid-track branches may carry functional connections. |
| track_not_centered_on_via | 74 | Copper overlaps plated via land away from its center. Native geometric connection/clearance checks pass. Manufacturing electrical test remains required. |
| via_dangling | 10 | Retained nonessential stitching/legacy drill sites. Connectivity does not depend on an unrouted item; final DRC reports zero opens. |

These are recorded dispositions, not suppressed rules. Independent Gerber/drill verification checks exported geometry. Production still requires fabricator DFM and first-article electrical, mechanical and thermal testing.
