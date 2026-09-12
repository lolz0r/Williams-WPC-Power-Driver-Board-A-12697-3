# Verification still possible before hardware

Further useful software verification is possible. JLC-2 remains unchanged and the prototype hold remains in effect. The priority is to resolve the open analog findings; the existing ROM/logic and manufacturing results remain applicable.

| Priority | Work possible now | What would constitute useful evidence |
|---|---|---|
| 1 | Finish the diode-isolated U21 startup transient with a longer runtime allowance and saved waveforms | Complete the requested 30 ms and evaluate the whole final rectified cycle, startup peak and reverse current. Earlier 300/900-second runtime stops were incomplete, not solver failures. |
| 2 | Isolate the matrix switching edges that repeatedly cause solver failure | Reproduce a failing transition in a smaller fixture, identify the responsible numerical/model behavior, and then complete the original full matrix at two sufficiently fine timesteps. Preserve device values, command timing and the original failures. |
| 3 | Test reverse-current protection candidates with the actual bridge/reservoir topology | Compare internal regulator current, external diode current, transferred energy, output excursion and subsequent recovery. A protection proposal must be checked for inrush and component stress before being applied to CAD. |
| 4 | Examine simultaneous MOSFET voltage/current and transient losses at the worst recorded edges | Relate the modeled approximately 114 A terminal-current spike to pulse duration, voltage and applicable device limits. The coil's approximately 22.7 A peak does not describe recovery/displacement current. More accurate manufacturer models would improve this assessment. |
| 5 | Extend targeted ROM scenarios for tilt, door changes, ball search and resets | Capture new bus traces, demonstrate the intended ROM state occurred, and pass the actual-netlist logic comparison. This adds scenario coverage; PinMAME's absent physical-watchdog model remains a limitation. |

The supply candidate also needs a consistent per-capacitor ESR/tolerance sweep, ripple/inrush checks and circuit/layout review. The earlier source-only study used 50 mΩ aggregate ESR for the shared reservoir and 50 mΩ per isolated branch; that assumption must remain visible when comparing arrangements. Its high-line single-capacitor ripple screens already identify a tradeoff to resolve.

## New matrix diagnostic

`tools/spice/matrix_euler_trial.py` adds a bounded first-order integration comparison at 1 and 0.5 µs. The device values, ROM command points and acceptance limits are retained. [ngspice documents](https://ngspice.sourceforge.io/docs/ngspice-44-manual.pdf) backward Euler through `method=trap maxord=1`. Its numerical damping means a completed run alone would not establish convergence or physical stability.

Both runs aborted before the required 370 ms: 1 µs steps at 8.06098 ms and 0.5 µs steps at 24.38948 ms. Neither establishes convergence; partial-window power readings are not accepted. Results are retained in [the follow-up report](../output/verification/followup/matrix-euler/results.json). They supplement the [existing addendum](CONTINUED_ANALOG_REVIEW.md); the previously packaged ZIP files remain historical snapshots.

## Requires physical hardware

Cabinet/harness clearance, actual transformer impedance and lamp/coil characteristics, real switching waveforms, fuse operation, loaded temperatures, CPU-generated BLANKING and partial-power behavior still require measurements. These are separate from the software checks above. No simulator result can establish mechanical fit or measured first-article performance.
