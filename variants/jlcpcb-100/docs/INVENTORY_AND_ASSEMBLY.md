# JLC-100 component and assembly decisions

This is a separate variant of JLC-3. The original variant is preserved. Public JLCPCB catalog snapshots were fetched on 2026-09-14 UTC (2026-09-13 in Los Angeles). Stock is not reserved. A 100-board build requires the per-board quantity times 100, plus 5% spares with a minimum of ten extra units per catalog code. The inventory test uses the smaller of warehouse stock and orderable stock. Pre-order MOQ is recorded separately: this design uses public stock for assembly, not an out-of-stock pre-order. JLCPCB explains that distinction in its [pre-order service documentation](https://jlcpcb.com/help/article/what-is-jlcpcb-parts-pre-order-service).

The complete `bom/all-components.csv` contains every purchased electronic component and the additional hardware. It also identifies unpopulated components and fabricated test/mounting features. `jlc-electronics-purchase.csv` aggregates shared codes across the whole board before applying the 100-board reserve. All through-hole electronic parts have JLCPCB catalog codes. Heatsinks, fasteners and thermal paste are separately identified external procurement items; their inventory is not covered by the JLCPCB stock check. The assembly models include these mechanical assemblies on their parent footprints.

**Use `jlcpcb-assembly/BOM.csv` and `jlcpcb-assembly/CPL.csv` for complete SMT and through-hole electronics assembly.** Both describe the same 440 individual purchased units. Follow [JLCPCB_UPLOAD.md](JLCPCB_UPLOAD.md) and include `PCBA-remark.txt` for fuse insertion, prepared headers and mechanical completion. `bom/all-components.csv` is the complete human-readable assembly/procurement record; the separate `jlc-smt-bom.csv` and `jlc-smt-cpl.csv` files cover SMT only. The old `all-electronics-positions.csv` filename now contains the valid combined CPL; the richer engineering table is `electronics-placement-details.csv`. Catalog availability does not guarantee acceptance for a particular JLCPCB assembly process: arrange THT/manual assembly and the connector preparations below in the assembly quotation. No orders or messages have been sent.

| Circuit | Selected substitution | Reason and consequence |
|---|---|---|
| U20/U21 | TPS552872QWRYQRQ1, C22397842 | Same RYQ21 pins; model uses guaranteed minimum 3.3 A average inductor limit. Output targets remain 5.1 V/3 A and 12 V/0.75 A. R266 becomes Basic 33 kΩ. |
| 28 solenoid/flasher/general power switches | AOD66923, C485687 | 100 V, 4.5 V specified logic drive, same DPAK pinout. Hot resistance and replayed load transients checked. |
| U1–U5/U18, U9 | SN74HCT574NSR C2878759, SN74HCT240NSR C6772 | Preserve HCT thresholds and functions; new 5.3 mm SO-20 body requires the changed routing. |
| Q9/Q11/Q13/Q15/Q17 | Basic MMBT2222A1P C8512 | Same B-E-C SOT-23 footprint; trigger-current low-drive corner checked. |
| Q10/Q12/Q14/Q16/Q18 | BTA08-600CRG C9102 | 8 A, four-quadrant triac with 50 mA worst-quadrant IGT. Rated current is lower than the old 16 A device; use the modeled 5 A GI-string envelope and original fuse values. Retain all five Boyd 7020BG sinks. |
| D101–D104 | MOT MBR40100A C5143116 | Dual 20 A legs in parallel, A-K-A physical leads. Retain separate electrically live Boyd 577202B00000G sinks and direct tab interfaces. |
| D105–D116 | onsemi MBRB20H100CTT4G C235758 | Dual10A,100V,175°C;250A surge per leg. Maximum6mA leakage/leg at125°C. Outer anodes parallel on A, tab/center cathode on K; same5.08mm outer lead spacing. Final thermal and startup fixtures use this part. |
| BR3 | onsemi GBPC2506W C906984 | Wire-lead version; new diagonal DC terminal pattern and thicker case. Follow the dedicated footprint and instructions below. |
| Five low-voltage reservoirs | Ten EGPD350ELL472MM30H C443892 | Each old 10,000 µF capacitor becomes two individually annotated 4,700 µF capacitors. Four on +18 V, two on +5V_RAW, two on +20 V, two on +12VU. |
| High-voltage reservoir | Four NHA100V1000M18*40 LO C3445915 | C8/C32/C64/C65 total 4,000 µF, replacing 4,400 µF. Each rated 2.02 A at 120 Hz. Unequal sharing and mains-frequency ripple checked. |
| C2/C4/C9/C12 | Rubycon 25ZLH330MEFC8X11.5 C109394 | Retain 330 µF/25 V; use the actual 3.5 mm lead spacing. |
| Small capacitors and shunts | C307331, C138687, C875839 | Basic 0402 100 nF/50 V X7R; 1210 10 µF/50 V X7R; eight 0.22 Ω 2512 1 W shunts. |

The Basic library was searched for suitable alternatives. The design retains higher voltage ratings, X7R input capacitors, appropriate power packages and HCT logic thresholds where a Basic substitute was unsuitable.

## Fuse assemblies

There are **15 HONGJU FH1-200CK-G holders, C268204**, each including its cover. F101 and F102 are empty holders as in the original variant; do not insert unspecified fuses. The other thirteen holders have separately listed cartridges. Holder metadata is present in both schematic and PCB fields, so the complete BOM is generated from the design rather than a handwritten count. Holder lead pitch is 22.6 mm, finished holes 1.7 mm. Former clip holes retained as plated vias are copper features, not additional purchased clips.

F106–F110, F111 and F113 use REOMAX 5.250.1500A, C5381754, 5 A time-lag ceramic 5×20 mm. F115 uses REOMAX 5.250.0750A, C5381743, 0.75 A time-lag. F103/F104/F105/F116 retain their specified 3 A time-lag cartridges; F114 retains its specified 8 A fast cartridge. Never increase a fuse rating to satisfy a simulated continuous overload.

**F112 changes service method:** it is a soldered TLC TA7, C3014110, 7 A time-lag 2410 fuse with 125 VAC/200 A interruption rating. It has no holder and requires desoldering for replacement. Manufacturer recommended lands are 2.5×3.0 mm, centers 5.5 mm apart. F112 feeds the coil AC supply and external Fliptronic AC branch at J104. The inrush simulation explicitly includes an assumed external reservoir; the 139.419 A²s figure is typical pre-arcing data, not guaranteed repetitive endurance or fault coordination. Qualify cold/hot starts and actual external loads before a production run.

## Prepared connectors

Maintain every original connector number, electrical pin number, friction-wall direction, pin-1 marking and removed key post. The CAD models omit keyed posts; PCB holes remain in place. Use `connector-keys.csv` with the assembly drawings. A cut-to-length or composite header is a prepared assembly, not an unmodified drop-in MPN.

- J107: one TE 640445-6 C86500. J101/J109/J114: 640445-7 C305801. Eight 9-position headers use 640445-9 C305802. J126 uses 1-640445-3 C592598.
- J120/J121: trim 13-position 1-640445-3 to 11 positions by removing positions 12–13 at the far end. Deburr and retain pin 1 and the friction wall. Purchase one 13-position header for each connector.
- **J115 purchases two 640445-6 headers.** J115A covers electrical pins 1–6; J115B covers 7–12. Align both walls and post rows; lightly dress the mating body ends if required. The complete BOM counts two pieces. Key position 9 means removing post 3 of J115B. Prove the combined header fits the actual 12-position housing without interference before preparing the batch.
- J133/J134/J135: trim TE 1-640456-0 C94118 from 10 to 9 positions, removing only position 10. Preserve the existing keyed post position and 2.54 mm pitch.
- J113: XFCN EH254V-12-34P C5200275, 34 positions, 2.54 mm pitch, with ejector latches. Match the notch and pin 1 to the assembly drawing. Closed body is 62.38 mm long and 16.9 mm high; allow 27.5 mm open-latch height and cable/tool access. This is longer than the old 3M body.

TE MTA-156 posts are 1.14 mm square and use 1.8 mm finished PCB holes. A nominal 3.96 mm CAD pitch approximates 0.156 inch (3.9624 mm); the small accumulated difference is within the supplied lead-hole clearance. Confirm connector mating, retention and gauge compatibility on a first article.

## BR3 and mechanical hardware

BR3 uses the **GBPC2506W wire-lead version**, not the Faston-lug version. The new footprint places DC positive at pad 1 and DC negative at diagonally opposite pad 2; pads 3 and 4 are AC. Check markings on every bridge. Form the flexible wire leads to the 18×18 mm pad pattern using a support fixture without loading the package seals. The onsemi outline allows lead-position variation; verify the forming fixture with received parts.

The body envelope is 29×29×11.23 mm maximum, with 0.12 mm nominal standoff. The Boyd 6223BG basket sits on the metal base. Use the listed **M4×20 screw**, replacing M4×16 to accommodate the thicker bridge. The native model includes the new bridge, raised basket, screw and nut. Preserve the H9 axis and check underside clearance.

Ten heatsinks, ten mounting screw/nut sets and thermal paste are included in the complete BOM and assembly models. Paste quantity is consumption based; a syringe is an initial batch provision, not a validated yield for 100 boards. All parent references and hardware counts are explicit in `external-hardware.csv`.

Mechanical models include simplified manufacturer-dimension envelopes. They do not establish cabinet fit, assembly tolerances, tool access, harness retention or thermal performance by themselves.

JLCPCB hardware catalog searches are retained in `research/search-hardware-results.json`: the exact 577202B00000G returned zero stock, and no exact 7020BG, 6223BG or MJ420MPP stock listing was found. Consequently this is an all-JLCPCB **electronics** selection, not an all-JLCPCB mechanical procurement package. The external hardware remains required and must not be omitted from the assembly.
