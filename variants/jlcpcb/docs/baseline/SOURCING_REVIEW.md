# Sourcing review — observations retrieved 2026-09-08

The current purchase BOM is generated from fresh schematic XML, plus explicit
heatsinks, screws/nuts, fuse clips and thermal paste. No order has been placed.
Stock figures below are web-page observations, sometimes from cached pages, not
reserved inventory or a binding quote. Reconfirm exact MPN, packaging, quantity,
authorized channel and delivery before purchasing. The historical `price100`
fields in `tools/sourcing.py` are estimates, not current production pricing.

## Changed selections

| Selection | Reason and compatibility | Availability evidence |
|---|---|---|
| IPD90N10S4L06ATMA1 | 100 V logic-level DPAK; 8.1 mΩ maximum at 4.5 V; improved output-driver thermal margin | [DigiKey: 4,523](https://www.digikey.com/en/products/detail/infineon-technologies/IPD90N10S4L06ATMA1/5960270); [Infineon active/preferred](https://www.infineon.com/part/IPD90N10S4L-06) |
| B41252A7109M000 ×5 | 10,000 µF/35 V; high ripple at ≤60 °C local ambient; 25.4×45 mm, 10 mm pitch, 6±1 mm leads; replaces the shorter-lead M067 selection | [DigiKey: 1,463](https://www.digikey.com/en/products/detail/tdk/B41252A7109M000/3493689) |
| STPS20M100ST ×4 | BR1 TO-220 A-K-A; new project footprint, routing and four separate heatsinks | [DigiKey: 624](https://www.digikey.com/en/products/detail/stmicroelectronics/STPS20M100ST/2122463) |
| Boyd 577202B00000G ×4 | BR1 sink, 13.21×12.70×19.05 mm, 24.4 °C/W catalogue natural convection | [DigiKey: 58,431](https://www.digikey.com/en/products/detail/boyd-laconia-llc/577202B00000G/108322) |
| Boyd 7020BG ×5 | Replaces poorly stocked 7019BG; 33.02×11.94×36.83 mm, 8.7 °C/W; CAD and thermal model updated | [DigiKey: 2,256](https://www.digikey.com/en/products/detail/boyd-laconia-llc/7020BG/1625705) |
| Boyd 6223BG ×1 | Replaces poorly stocked 6224BG; same 26.92 mm square/31.75 mm high, 9.4 °C/W; 4.14 mm hole requires actual M4 fit check | [DigiKey: 2,212](https://www.digikey.com/en/products/detail/boyd-laconia-llc/6223BG/1625608) |
| 3M N2534-6002-RB | Active vertical 34-pin IDC; old 30334-5002HB was obsolete and right angle; 50.50×8.59 mm body, 0.90 mm finished PCB holes | [DigiKey: 2,137](https://www.digikey.com/en/products/detail/3m/N2534-6002-RB/755183); [3M drawing](https://multimedia.3m.com/mws/media/330367O/3m-four-wall-header-2500-series-ts-0770.pdf?fn=ts0770_R10.pdf) |
| C0805C333K5RACTU | KEMET 33 nF, ±10%, 50 V, X7R, 0805; replaces obsolete Samsung CL21B333KBANNNC | [DigiKey: 112,623](https://www.digikey.com/en/products/detail/kemet/C0805C333K5RACTU/411440); [manufacturer specification](https://search.kemet.com/download/specsheet/C0805C333K5RACTU) |
| C0805C471J5GACTU | KEMET 470 pF, ±5%, 50 V, C0G, 0805; replaces obsolete CL21C471JBANNNC | [DigiKey: 74,684](https://www.digikey.com/en/products/detail/kemet/C0805C471J5GACTU/411132); [manufacturer specification](https://search.kemet.com/download/specsheet/C0805C471J5GACTU) |
| C0805C391J5GACTU | KEMET 390 pF, ±5%, 50 V, C0G, 0805; same electrical specification, available replacement | [Mouser: 5,673](https://www.mouser.com/es/ProductDetail/KEMET/C0805C391J5GACTU?qs=Z8iU%252BYX8GzEXY6S0ID4LXw%3D%3D); [manufacturer specification](https://search.kemet.com/download/specsheet/C0805C391J5GACTU) |
| C0805C103K5RACTU | KEMET 10 nF, ±10%, 50 V, X7R, 0805; available replacement | [DigiKey: 1,532,160](https://www.digikey.pl/pl/products/detail/kemet/C0805C103K5RACTU/411157); [manufacturer specification](https://search.kemet.com/component-documentation/download/specsheet/C0805C103K5RACTU) |

KEMET nominal bodies are 2.0×1.25×0.78 mm, maximum thickness 0.88 mm;
standard 0805 pads remain appropriate. Capacitance, dielectric and tolerance
assumptions in the loop/transient tests are unchanged. Catalogue thermal resistance
requires the stated mounting/airflow; a stock check does not validate thermal performance.

## Connector ordering-code correction

All 33 KK396 fields used transposed ordering digits. The corrected family is
`0026604NN0`, where NN is the position count. This is a catalogue correction,
with unchanged pin pitch and routing. Full-pin stock requires key-pin removal
as documented in [ASSEMBLY_NOTES.md](ASSEMBLY_NOTES.md); an NC pin is not itself
a key designation. The native models now depict the specified removed pins.

| Ways / MPN | Distributor observation |
|---|---|
| 3 / 0026604030 | [DigiKey: 32,525](https://www.digikey.com/en/products/detail/molex/0026604030/96502) |
| 4 / 0026604040 | [DigiKey: 59,962](https://www.digikey.com.br/en/products/detail/molex/0026604040/197447) |
| 5 / 0026604050 | DigiKey related-product listing showed 9,556; reconfirm exact current stock |
| 6 / 0026604060 | [TTI: 4,297](https://www.tti.com/content/ttiinc/en/apps/part-detail.html?mfgShortname=MOL&partsNumber=0026604060) |
| 7 / 0026604070 | [DigiKey: 17,033](https://www.digikey.com/en/products/detail/molex/0026604070/97339) |
| 9 / 0026604090 | [DigiKey active listing](https://www.digikey.com/en/products/detail/molex/0026604090/79784); quantity not retained |
| 11 / 0026604110 | [DigiKey: 774](https://www.digikey.com.au/en/products/detail/molex/0026604110/193997) |
| 12 / 0026604120 | [DigiKey active listing](https://www.digikey.com/en/products/detail/molex/0026604120/193986); quantity not retained |
| 13 / 0026604130 | [DigiKey: 2,482](https://www.digikey.com/en/products/detail/molex/0026604130/3044429) |

## Retained parts checked

| Part | Evidence |
|---|---|
| TPS54360BDDAR | TI active; DigiKey search showed 963; vendor-model testing uses TI's compatible transient model |
| STPS20M100SG-TR | [Mouser: 1,847](https://www.mouser.com/en/ProductDetail/STMicroelectronics/STPS20M100SG-TR?qs=5HwTSiuA5HCdrjP2dKfpog%3D%3D) |
| GBPC3510W-E4/51 | [Mouser: 1,657](https://www.mouser.com/ProductDetail/Vishay-Semiconductors/GBPC3510W-E4-51?qs=AvlKB63p5SkfiLMdbYKoSQ%3D%3D) |
| BTA16-600CRG | [DigiKey: 5,836](https://www.digikey.com/en/products/detail/stmicroelectronics/BTA16-600CRG/669145) |
| IRFR5305TRPBF | [DigiKey: 35,543](https://www.digikey.com/en/products/detail/infineon-technologies/IRFR5305TRPBF/812554) |
| IRLR024NTRPBF | Infineon active; DigiKey search showed 52,569 |
| 74HCT574D,653 | Mouser search showed 20,221; DigiKey 1,750 |
| 74HCT240D,653 | [DigiKey: 1,359](https://www.digikey.com/en/products/detail/nexperia-usa-inc/74HCT240D-653/1230746) |
| SN74HCT74DR | [DigiKey: 5,161](https://www.digikey.com/en/products/detail/texas-instruments/SN74HCT74DR/276854) |
| LM339DR | [DigiKey: 23,050](https://www.digikey.com/en/products/detail/texas-instruments/LM339DR/276657); 0–70 °C ambient grade |
| TBD62083AFWG,EL | Avnet search showed 2,000; retain Toshiba DMOS array, not a Darlington pin-compatible assumption |
| B560C-13-F | [DigiKey: 140,710, active](https://www.digikey.com/en/products/detail/diodes-incorporated/B560C-13-F/768773) |
| S3M-13-F | [DigiKey: 3,895, active](https://www.digikey.com/en/products/base-product/diodes-incorporated/31/S3M/4379) |
| LLS2A222MELA | [DigiKey: 187](https://www.digikey.com/en/products/detail/nichicon/LLS2A222MELA/2548962) |
| EEU-FR1E331 | [DigiKey: 3,304, active](https://www.digikey.jp/ja/products/detail/panasonic-industry/EEU-FR1E331/2433549) |
| SRP1265A-100M | [DigiKey: 21,314](https://www.digikey.com/en/products/detail/bourns-inc/SRP1265A-100M/4876620) |
| CL32B106KBJNNWE | [DigiKey: 4,997, active](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL32B106KBJNNWE/3889046) |
| CL21B104KBCNNNC | [DigiKey: 5,413,821, active](https://www.digikey.com/en/products/detail/samsung-electro-mechanics/CL21B104KBCNNNC/3886661) |
| LTST-C170KRKT | [DigiKey: 489,785, active](https://www.digikey.com/en/products/detail/liteon/LTST-C170KRKT/386779) |
| RT0805BRD0711K3L | [DigiKey substitute table: 5,160](https://www.digikey.com/en/products/detail/panasonic-industry/ERA-6AEB1132V/2025757); retain exact part; Panasonic ERA-6AEB1132V is an available same-value alternative, not installed in this BOM |
| RT0805BRD072K1L | [DigiKey substitute table: 2,604](https://www.digikey.com/en/products/detail/yageo/AT0805DRD072K1L/5910684) |
| RC0805FR-0728KL | [DigiKey: 12,282, active](https://www.digikey.com/en/products/detail/yageo/RC0805FR-0728KL/730735) |
| RL2512FK-070R22L | [Mouser listing: 14,928](https://www.mouser.com/c/passive-components/resistors/current-sense-resistors-smd/?case+code+-+in=2512&resistance=220+mOhms); use exact 1% part, account for TCR |
| 4610X-101-472LF | [DigiKey: 24,276, active](https://www.digikey.ca/en/products/detail/bourns-inc/4610X-101-472LF/1089205) |
| 0022232091 | [DigiKey: 3,292](https://www.digikey.com/en/products/detail/molex/0022232091/26681) |
| 0022232051 | [TTI: 85,175](https://www.tti.com/content/ttiinc/en/apps/part-detail.html?mfgShortname=MOL&partsNumber=22-23-2051) |
| 0239005.MXP | [DigiKey: 2,238, active](https://www.digikey.com/en/products/detail/littelfuse-inc/0239005-MXP/778232) |
| MG 8616-3ML | [DigiKey: 83](https://www.digikey.com/en/products/detail/mg-chemicals/8616-3ML/4899944) |
| M3×8 MPMS 003 0008 PH | [DigiKey: 45,707](https://www.digikey.com/en/products/detail/bfirst-industrial/MPMS-003-0008-PH/274954) |

The remaining procurement task is an order-time quotation covering all quantities,
minimum pack sizes, exact packaging and delivery. Stock observations below close
additional catalogue checks; they do not reserve inventory. Fuse DC breaking
capacity and time-current coordination require application review independently
of availability. Any substitution requires a specification and footprint review.


Additional retained-value observations: [118 kΩ: 15,904](https://www.digikey.in/en/products/detail/yageo/RC0805FR-07118KL/727566),
[29.4 kΩ: 46,881](https://www.digikey.ca/en/products/detail/yageo/RC0805FR-0729K4L/727796),
[240 kΩ: in stock](https://uk.rs-online.com/web/p/surface-mount-resistors/2426949),
[33.2 kΩ: 11,066](https://www.mouser.com/ProductDetail/YAGEO/RC0805FR-0733K2L?qs=QrWOOBGzeCbCvHLaHT4sLQ%3D%3D),
[130 kΩ: 92,932](https://www.digikey.in/en/products/detail/yageo/RC0805FR-07130KL/727590),
[42.2 kΩ: 16,375](https://www.digikey.com/en/products/detail/yageo/RC0805FR-0742K2L/727949),
[27 Ω 2512: 4,201](https://www.digikey.com/en/products/detail/yageo/RC2512JK-0727RL/12708610),
[0 Ω 2512: 69,260](https://www.mouser.com/en/ProductDetail/YAGEO/RC2512JK-070RL?qs=Fz%2FrpjPuTcGb5uCYF3SHgw%3D%3D),
[Keystone 3517: 66,018](https://www.newark.com/keystone/3517/fuse-holder/dp/74R7981).
These are the exact YAGEO MPNs in the corresponding BOM rows, not generic value substitutions.

C5 also uses B41252A7109M000. Its previous Rubycon selection exceeded the
conservative 50 Hz ripple bound by 1.5% in one modeled corner. The common TDK
replacement preserves 10,000 µF and 10 mm lead pitch; the taller body is included
in the current nominal mechanical review.

## Further catalogue closure

| Exact MPN | Observed stock |
|---|---|
| RC0805FR-07100RL | [DigiKey: 893,630](https://www.digikey.com/en/products/detail/yageo/RC0805FR-07100RL/727543) |
| RC0805FR-0710KL | [DigiKey: 2,318,254](https://www.digikey.com/en/products/detail/yageo/RC0805FR-0710KL/727535) |
| RC0805FR-071K5L | [DigiKey: 622,689](https://www.digikey.com/en/products/detail/yageo/RC0805FR-071K5L/727496) |
| RC0805FR-071KL | [DigiKey: 895,275](https://www.digikey.com/en/products/detail/yageo/RC0805FR-071KL/730391) |
| RC0805FR-0720KL | [DigiKey: 22,085](https://www.digikey.com/en/products/detail/yageo/RC0805FR-0720KL/730667) |
| RC0805FR-07270RL | [DigiKey: 137,783](https://www.digikey.com/en/products/detail/yageo/RC0805FR-07270RL/727783) |
| RC0805FR-0727KL | [DigiKey: 46,879](https://www.digikey.com/en/products/detail/yageo/RC0805FR-0727KL/727780) |
| RC0805FR-072KL | [DigiKey: 785,611](https://www.digikey.com/en/products/detail/yageo/RC0805FR-072KL/727664) |
| RC0805FR-07240KL | [DigiKey: 31,229](https://www.digikey.com/en/products/detail/yageo/RC0805FR-07240KL/727762) |
| RC0805FR-07470RL | [DigiKey: 229,402](https://www.digikey.com/en/products/detail/yageo/RC0805FR-07470RL/727976) |
| RC2512JK-0715KL | [DigiKey: 1,933](https://www.digikey.com/en/products/detail/yageo/RC2512JK-0715KL/5922492) |
| 0239003.MXP | [DigiKey: 2,949](https://www.digikey.com/en/products/detail/littelfuse-inc/0239003-MXP/778224) |
| 0239007.MXP | [DigiKey: 3,891](https://www.digikey.com/en/products/detail/littelfuse-inc/0239007-MXP/778234) |
| 0239.750MXP | [DigiKey: 871](https://www.digikey.com/en/products/detail/littelfuse-inc/0239-750MXP/778208) |
| 0217008.MXP | [DigiKey: 6,063](https://www.digikey.com/en/products/detail/littelfuse-inc/0217008-MXP/777551) |
| S1M-13-F | [DigiKey: 2,671](https://www.digikey.com/en/products/detail/diodes-incorporated/S1M-13-F/804883) |
| 1N4148W-7-F | [DigiKey: 1,395,759](https://www.digikey.com/en/products/detail/diodes-incorporated/1N4148W-7-F/815280) |
| MPMS 003 0012 PH | [DigiKey: 2,122](https://www.digikey.com/en/products/detail/bfirst-industrial/MPMS-003-0012-PH/274955) |
| MHNZ 003 | [DigiKey: 43,616](https://www.digikey.com/en/products/detail/bfirst-industrial/MHNZ-003/274973) |
| MHNZ 004 | [DigiKey: 6,132](https://www.digikey.com/en/products/detail/bfirst-industrial/MHNZ-004/274974) |

MMBT4401-7-F is active; [DigiKey exact-part substitute listing](https://www.digikey.com/en/products/detail/diodes-incorporated/MMBT4401-7-F-W/27803722)
showed 98,504 of the exact -7-F part. The -W suffix is not substituted.
[KK396 nine-way stock](https://www.digikey.com/en/products/detail/molex/0026604090/79784)
was 1,145, and [12-way stock](https://www.digikey.com/en/products/detail/molex/0026604120/193986)
was 5,330.

The unconfirmed M4 screw ordering code has been replaced with **Kanebridge
MJ416MPP**, confirmed in the [manufacturer catalogue](https://legacy.kanebridge.com/kaneprls.asp?SellCode=MJ-MPP).
[DigiKey/Fix Supply](https://www.digikey.com/en/products/detail/kanebridge/MJ416MPP/21635726)
lists 60,000, but a 3,000-piece carton minimum: do not interpret the one-board BOM
quantity as the seller's minimum. Seek split packs from the manufacturer's
resellers when obtaining the procurement quotation. This is zinc steel, M4×16,
JIS-B1111 Phillips pan, 6.75 mm head diameter and 2.60 mm height. The existing
7.6×3.0 mm CAD head envelope conservatively bounds it; shaft and engagement remain
unchanged. The old MPMS 004 0016 PH catalogue entry is not qualified for ordering.
