# Assembly quote counts

Counts for the current populated engineering candidate, excluding DNP parts,
test points, mounting holes and fiducials. These are quotation quantities;
the release limitations in [RELEASE_STATUS.md](RELEASE_STATUS.md) still apply.

| Form field | Count | Interpretation |
| --- | ---: | --- |
| Unique electronic parts | 70 | Distinct electronic MPNs, including fuse cartridges and clips |
| Unique full purchase BOM parts | 79 | Also includes mounting hardware and thermal paste |
| SMD components | 314 | Populated surface-mount component instances |
| SMT pads | 929 | Numbered copper pads, including exposed pads; excludes paste-only apertures |
| BGA/QFP components or pads | 0 | No BGA or QFP packages |
| Through-hole components | 93 | Individual physical soldered parts |
| Populated through-hole solder pins | 389 | Excludes 35 removed connector key pins |

Use **929** when the SMD field's unit is “total SMT pads,” and **314** when
it asks for components. Use **93** for through-hole parts or **389** for
through-hole solder pins.

The 77 through-hole footprint groups represent 93 physical parts because
16 fuseholder footprints each contain two separate clips. The through-hole
parts comprise 38 headers, 32 clips, 11 capacitors, five triacs, four TO-220
diodes, one bridge and two SIP resistor arrays. There are 424 numbered
through-hole PCB pads before subtracting the 35 connector key pins.

The 14 plug-in fuse cartridges are additional assembly items and are not
included in the soldered through-hole component count.

Sources: the routed PCB, `output/release-candidate/bom/purchase-bom.csv`,
and `output/verification/revision/connector-keys.csv`.
