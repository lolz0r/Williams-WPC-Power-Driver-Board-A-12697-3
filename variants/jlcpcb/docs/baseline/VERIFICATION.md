# Verification and reproduction

Run commands from the repository root. The authoritative hardware input is the
routed `wpc_power_driver_cost.kicad_pcb` plus its root/child schematics and project
libraries. Do not run the historical placement generator to reproduce this routing.
Its missing sibling dependency and overwrite guards are intentional limitations.

## Installed environment

KiCad 10.0.6 native macOS app, Homebrew ngspice/libngspice 47, MAME 0.289, CMake,
Clang, Tesseract and Python 3.14 are installed. `.venv` contains NumPy, SciPy,
Shapely, Matplotlib, Pillow, PyMuPDF, Gerbonara 1.6.3 and cadquery-ocp 7.9.3.1.1.
KiCad's `pcbnew` requires its bundled Python 3.9; use `tools/kicad_env.py` to locate
it and set library paths. `NGSPICE_LIBRARY` can override the shared library.

```sh
python3 -m venv .venv
.venv/bin/pip install numpy scipy shapely matplotlib pillow pymupdf gerbonara==1.6.3 cadquery-ocp==7.9.3.1.1
brew install ngspice libngspice mame cmake tesseract
```

The commands above describe environment setup; already installed dependencies do
not need reinstalling. Native KiCad must also be installed. Numerical dependencies
are frozen in `tools/verification-requirements.txt` for this run.

## Hardware exports and independent checks

```sh
python3 tools/export_release.py
python3 tools/verify_interface.py output/release-candidate/reports/netlist.xml
python3 -m unittest discover -s tools -p test_verification.py
.venv/bin/python tools/verify_manufacturing.py
```

The exporter stops on native errors, opens or schematic parity differences. It
also independently compares PCB/netlist pad nets, values, footprints, MPNs and
manufacturers. Exports include 11 Gerber layers, drills/maps, BOM and placements,
IPC-D-356, schematic/assembly PDFs, STEP and top/bottom/perspective PNGs.

Export the saved filled copper and mechanical model placements with native Python:

```sh
python3 - <<'PY'
import subprocess,sys
sys.path.insert(0,'tools')
from kicad_env import python,environment
for script in ('tools/export_geometry.py','tools/export_mechanical.py'):
    subprocess.run([python(),script],env=environment(),check=True)
PY
.venv/bin/python tools/verify_copper_topology.py
.venv/bin/python tools/review_drc_warnings.py
.venv/bin/python tools/verify_mechanical.py
.venv/bin/python tools/copper_dc.py
.venv/bin/python tools/thermal_mesh.py --gap-aware
```

`make_mechanical_models.py` regenerates project nominal STEP envelopes. It is
separate from copper generation. The thermal model uses actual copper geometry,
maximum bridge losses from the corner run, conservative Schottky leakage and
explicit heatsink/lead boundary sensitivities. Its 8 W distributed background is
an assumption, not a complete component-by-component simultaneous-load model.
Nominal solid intersection does not prove cabinet fit or assembly tolerance.

The old `thermal_mesh.json`, `copper_dc-before-plane.json`, rejected-pour reports
and intermediate DRC files are historical evidence. Current thermal evidence is
`thermal_mesh_gap.json`. Experimental migration scripts are not the release pipeline.

## SPICE

```sh
python3 tools/spice/run_all.py --help
python3 tools/spice/corners.py
python3 tools/spice/capacitor_ripple.py
.venv/bin/python tools/spice/loop_corners.py
python3 tools/spice/vendor_buck.py --reuse
python3 tools/spice/vendor_faults.py
python3 tools/spice/vendor_prebiased_start.py
```

Use `run_all.py --output output/verification/revision/spice` for the current base
suite. Vendor models are cached locally under `.scratch/vendor-models`; they are
not redistributed. `vendor_buck.py` downloads TI's unencrypted transient model
when missing. It tests the exact schematic compensation and output capacitors.
The 4.5 A minimum-limit edit is an engineering sensitivity, not a vendor process
corner. `vendor_faults.py` intentionally returns failure for unresolved hard raw
clamp/backfeed cases; those results must remain visible. `vendor_reverse_protection.py`
is a rejected bypass experiment and does not modify the PCB. Prebias with VIN
already present is a separate fixture. Successful solver gmin stepping is recorded
as a diagnostic, not a simulation failure; aborted or missing measurements fail.

## Emulator and replay

ROMs are user supplied in `/Users/mc/Downloads/sttng_l7`. Do not redistribute them.

```sh
mame -rompath /Users/mc/Downloads -verifyroms sttng_l7
python3 tools/mame/run_trace.py --rompath /Users/mc/Downloads --scenario diagnostics --seconds 320
```

MAME marks STTNG as not working/no sound upstream; its service trace is useful,
but game scoring/launch coverage came from PinMAME. The latter's exact source
commit and passive observer patch are in `output/verification/pinmame/provenance.json`
and `record_bus.patch`. Current checkout commit: `2e64cfa9f92955952489854a60ec23397294417e`.

```sh
git clone https://github.com/vpinball/pinmame .scratch/pinmame
git -C .scratch/pinmame checkout 2e64cfa9f92955952489854a60ec23397294417e
python3 tools/pinmame/prepare.py
cmake -S .scratch/pinmame -B .scratch/pinmame/build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED=ON -DBUILD_STATIC=OFF
cmake --build .scratch/pinmame/build -j 4
python3 tools/pinmame/run_gameplay.py --rom-parent /Users/mc/Downloads --seconds 240
```

Skip clone/checkout on the existing patched checkout. The runner builds the C++
harness and records source/library/ROM/trace hashes; `--build-only` checks its
build without replaying the unchanged game. `analyze_trace.py` reads raw CPU bus
writes, not smoothed output states. Replay uses the worst 10 s command-duty window
for each supported coil and preserves the raw trace hash:

```sh
python3 tools/mame/analyze_trace.py PATH_TO_RAW_BUS_CSV
python3 tools/spice/replay_rom.py PATH_TO_RAW_BUS_CSV --output output/verification/revision/replay-reproduced
```

No emulator tests PCB copper, real CPU electrical timing, lamps, coils or motors.
The behavioral load models require actual-machine correlation.

## Package integrity

After the native export, run `python3 tools/verify_release.py` to refresh and
bind independent checks to the saved PCB. It reruns copper DC or thermal analysis
if the geometry hash changed, then writes `final-inputs.json`.
Run `python3 tools/package_review.py` after all checks to copy current review
summaries, assembly instructions, provenance and hashes into the candidate. It
retains failed experiments and explicit physical qualification gates. The script
must not turn missing reports into passes. See `READINESS.json` and
[RELEASE_STATUS.md](RELEASE_STATUS.md) for the current disposition.

Current mechanical reports hash both model-placement inputs and every STEP model
used in the solid-intersection calculation. The copper DC and thermal reports
hash the exact filled geometry. The package gate rejects stale PCB/netlist/DRC,
copper or mechanical input reports. After nominal model regeneration, run
`tools/connector_keys.py --models` with `.venv` Python before exporting, to restore
the explicit keyed-header variants; normal release export does not alter models.

ROM replay uses a 5 µs maximum trapezoidal timestep. A completion measurement
must equal the intended stop time; partial simulations cannot pass. PWL event
times are strictly increasing, including a command edge exactly at a window
endpoint. Forward diode current excludes reverse leakage. To reproduce the
additional integration sensitivity:

```sh
python3 tools/spice/replay_rom.py output/verification/pinmame/gameplay/bus.csv --channels 1 2 16 --max-step-us 2.5 --output output/verification/revision/replay-step-sensitivity
```

`python3 tools/spice/replay_rl_bound.py` performs an independent closed-form
RL segment calculation on all 30 replay windows. It checks conduction-only
MOSFET heating, forward diode average and the coil current bound. It omits
switching/reverse-recovery losses and does not supersede transient failures.
