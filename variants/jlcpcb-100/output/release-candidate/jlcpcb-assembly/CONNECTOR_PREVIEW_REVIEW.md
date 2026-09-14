# Connector preview review — September 14, 2026

The reported JLCPCB preview showed J113 perpendicular to its PCB footprint, bare holes at J120/J121/J126, and gray blocks at several other headers. The user confirmed that the C592598 row was matched but unchecked with a warning; the exact warning was no longer available. The files contained all connectors. The selection state explains the three excluded headers; the specific reason for the warning is still unknown.

## Full orientation audit

The user confirmed the latest CPL (J113 = 90°), with no manual rotations. The earlier check preserved native SMT angles and checked connector pad numbers; it did not establish correct supplier orientation for all parts or validate friction walls. This audit supersedes that claim.

All **69 purchased codes / 440 placements** now have an entry in `component-orientation-check.csv`. Compared with that last CPL, **76 SMT and 18 connector rotations change**. The SMT-only CPL receives the same corrections. Raw native angles are kept separately in `assembly/native-smt-positions.csv`; they are not the JLC upload file.

| Parts | Offset from native KiCad angle |
| --- | ---: |
| SN74HCT574NSR C2878759 (U1–U5, U18), SN74HCT240NSR C6772 (U9) | −90° |
| SN74HCT74DR C352961, LM339DR C7948, TBD62083AFWG C165895 | −90° |
| AOD66923 C485687, IRFR5305 C2624, MMBT2222A C8512 | +180° |
| IRLR024N C3007 | +90° |
| MBRB20H100CT C235758 (D105–D116) | −90° |
| XFCN C5200275 (J113) | −90° (retained correction) |
| Molex C505166, TE C94118 | +180° (retained corrections) |
| TE C86500/C305801/C305802; Molex C588986 (J111) | +180° for inward tab; **manual model/pad conflict** |
| TE C592598 (J120/J121/J126) | +180° inferred from TE family; **manual placement, no public library** |

**U1 = 90°, U2/U3 = 270°, J110 = 180°, J113 = 90°.** J110's tab faces down/toward the board interior in the native board top view. Its key is post 5. Retain every other post, including unused posts. The same inward-tab rule applies to the single-row J headers; the PDF provides a separate top-view detail for all 39 purchased headers.

### Evidence and remaining manual gates

`connector-orientation-guide.pdf` shows native pin-1 coordinates, physical key-post locations and tab/notch directions. `placement-map.csv` records native angle, applied offset and final CPL angle. Functional pad comparisons account for the native rectifier symbol's duplicated anodes and C3007's library drain pin 4 versus native drain pin 2. U20/U21 retain 0° offset: all 21 RYQ lands match. Diodes, LEDs, polarized capacitors and remaining nonpolarized axes were included; 15 resistor positions have no public library and retain their electrically symmetric native orientation. Fuse cartridges are manual insertions into their separately placed holders.

**A supplier model is not always consistent with its own pad labels.** TE C86500/C305801/C305802 and Molex C588986 have a 180° disagreement between numbered pads and housing orientation. The CPL follows the inward friction wall; these 15 placements require the assembler to resolve the library conflict against the native pin/key guide. They are not counted as successfully verified numbered-pad placements. TE's drawing labels post 1 on the opposite end from the public 3.96 mm pad library when the locking wall is aligned. Never rewire the board to follow erroneous library labels.

C505166's numbered pads support its retained 180° correction, but its public library has no 3D housing; its ten inward tabs require manual confirmation. C592598's three placements have no public library. D101–D104 C5143116 have symmetric anodes and a supplier 3D model framed below the PCB; a CPL Z rotation cannot fix that model. Retain their native tab-to-heatsink direction and confirm manually. BR3 has no public placement library and requires its documented polarity/lead forming. These limitations remain explicit assembly gates.

The public library sources are exact-code LCSC-owned results from `https://lceda.cn/api/products/<C-code>/components`. JSON, retrieval metadata, supplier preview meshes and source hashes are archived in `cad/research/jlc-placement-libraries/` and `cad/research/jlc-preview/`. Public data does not prove the current private JLCPCB job uses the same model. [JLCPCB explains](https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2) that its red/pink dot is an orientation mark and is not necessarily pin 1.

The original Williams STTNG Operations Manual, PDF page 61 / printed 2-9, controls the inward friction walls and key schedule. [TE 640445 drawing](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Customer+Drawing%7F640445%7FAD7%7Fpdf%7FEnglish%7FENG_CD_640445_AD7.pdf%7F640445-9) and [TE 640456 drawing](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Customer+Drawing%7F640456%7FW3%7Fpdf%7FEnglish%7FENG_CD_640456_W3.pdf%7F1-640456-0) control the replacement header envelopes. Native TE/Molex generated models now put the wall on the inward side, use corrected housing centers, and remove only the explicit key post. The old TE generator incorrectly removed every unconnected post. Native PCB pads, electrical pin numbering and copper remain unchanged. Simplified envelopes do not certify molded detail or cable fit.

J113's 34 absolute library pin positions still coincide with the native drilled holes at 90°. Pin 1 is X=8.220, Y=−128.459 mm, bottom/right of the array in board top view. The notch faces right, toward the board interior. Other checks compare centered functional land patterns and separate physical housing centers; they do not claim all supplier body origins match the live placement job.

## C592598 selection and replacement search

J120/J121/J126 remain one BOM group containing three TE 1-640445-3 headers per board. The public stock recheck returned 371 physical and 371 orderable pieces, sufficient for 300 build pieces plus 15 spares. Stock is not reserved. The library endpoint returned `success:false, code:404` for C592598; this explains why a public footprint could not be checked, but does not establish the cause of the user's warning.

The user requested a replacement if possible. The same-day search found:

| Candidate | Available quantity | Decision |
| --- | ---: | --- |
| TE 1-640445-1, C592644, exact 11-position | 0 physical; negative orderable value | Insufficient for 200 build pieces plus spares |
| Molex 26604110, C17541501, exact 11-position | 0 | Insufficient |
| Molex 0026604130, C17226055, exact 13-position | 89 | Insufficient for 100 build pieces plus spares |
| TE 1-640445-2, C592597, 12-position for trimming | 28 orderable | Insufficient |
| Other longer TE 640445 headers | 0 | Insufficient |
| Stocked 11-/13-position VH-family headers | Some meet quantity | Matching 3.96 mm pitch does not establish compatibility with existing KK/MTA cable plugs; no mating-compatible substitute qualified |

The release retains the stocked C592598 and its existing preparation instructions. Search queries and results are archived with the full package.

On JLCPCB **Select Parts**, review the warning, confirm C592598 / 1-640445-3, then check the row. All three references must appear in the selected assembly list. [JLCPCB's matching instructions](https://jlcpcb.com/help/article/common-bom-and-cpl-matching-issues-and-explanations) explain that a matched but unchecked component is not selected for assembly. CSV content cannot acknowledge this existing order-page warning.

For manual assembly, trim J120/J121 from 13 to 11 positions by removing positions 12–13, preserve pin 1 and the friction wall, and remove key post 4. J126 stays 13 positions with key post 9 removed. Send `PCBA-remark.txt`, `placement-map.csv`, and `connector-keys.csv` with the quotation. Gray blocks in the screenshot appear to be placeholders; verify selected part codes and the final assembly drawing rather than inferring omission from the model appearance.

The PCB, schematic, nets, Gerbers, purchased part quantities and electrical simulation models are unchanged by these upload corrections. The previously accepted SPICE results remain applicable within their documented engineering-model scope; no new simulation run is claimed.
