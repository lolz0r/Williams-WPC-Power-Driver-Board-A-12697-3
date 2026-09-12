# Williams WPC power/driver replacement

The separate [JLC-2 electronics redesign](variants/jlcpcb/README.md) includes JLCPCB sourcing, revised native CAD and fresh Linux SPICE/MAME verification. Its status and exports are maintained independently from the parent revision below.

This project develops a modern replacement for the Williams **A-12697-3** power
and driver board, with **Star Trek: The Next Generation L7** as the current
compatibility and emulation target. It provides rectified supplies, 5 V and 12 V
buck regulators, 28 coil/flasher outputs, an 8×8 lamp matrix and five general
illumination triac channels. The board has no firmware.

**Current disposition: engineering candidate; not production released.**
Manufacturing exports are available, but finer-timestep ROM replay convergence,
regulator shutdown/backfeed, physical thermal/fault qualification, cabinet/harness
fit and fabricator DFM remain open.
J106/J111 differences prevent a universal A-12697 drop-in claim. See the
[release status](docs/RELEASE_STATUS.md) for evidence and exact limitations.

## Latest deliverables

- [Perspective render](output/release-candidate/3d/perspective.png),
  [top](output/release-candidate/3d/top.png), [bottom](output/release-candidate/3d/bottom.png)
  and [STEP model](output/release-candidate/3d/board.step).
- Complete engineering review archive: pending the replay convergence gate.
- [Gerbers and drills](output/release-candidate/gerbers-and-drills.zip),
  [purchase BOM](output/release-candidate/bom/purchase-bom.csv),
  [schematic PDF](output/release-candidate/schematic/schematic.pdf) and
  [fabrication specification](output/release-candidate/FABRICATION.txt).
- [Verification and reproduction](docs/VERIFICATION.md),
  [component sourcing](docs/SOURCING_REVIEW.md),
  [assembly and first-article procedure](docs/ASSEMBLY_AND_FIRST_ARTICLE.md).

The four-layer board is 449.152 × 272.910 mm, nominally 1.6 mm thick, with
**2 oz FINISHED outer / 1 oz inner copper**: 70/35/35/70 µm. Minimum finished
plated-barrel copper is 20 µm. Use only `output/release-candidate/`; older exports
directly under `output/` are superseded.

## Source and tooling

The routed `wpc_power_driver_cost.kicad_pcb`, root/child KiCad schematics, project
symbol library, `footprints/` and `models/` are the hardware source. The routed
PCB is authoritative. Historical placement generation depends on a missing
sibling project and **cannot reproduce the current routing**; overwrite guards
protect the PCB and derived schematic.

`tools/design_cost.py` and `tools/sourcing.py` describe circuit choices and parts.
`tools/spice/` contains electrical models and sweeps; `tools/mame/` and
`tools/pinmame/` capture and analyze user-supplied ROM activity. Independent
geometry, manufacturing and mechanical checks are in `tools/verify_*.py`.

```sh
python3 tools/export_release.py
python3 tools/verify_release.py
python3 tools/package_review.py
```

Install the dependencies and generate the prerequisite simulation reports as
specified in [VERIFICATION.md](docs/VERIFICATION.md). The package gate rejects
missing, failed or stale required reports; retained failed fault experiments
and physical qualification gates remain explicit in `READINESS.json`.

The [historical design narrative](docs/HISTORICAL_DESIGN.md) records earlier
component selections and estimates. It does not describe the current build.
