> JLC-2 retains this mechanical and connector assembly scheme. Use the current [JLC-2 report](../README.md) and `output/release-candidate/bom/` for electronic part numbers and readiness. Physical first-article qualification remains open.
**JLC-2 electrical change — STTNG only:** flasher diode cathodes for SOL21–SOL28 now return to +20 V on the PCB. J122 pins 5/6/8/9 and J126 pins 10/11/12/13 are therefore +20 V; J126 pin 9 remains the key. These cathode contacts are unused in STTNG. Verify the actual harness before mating; another game may use a different tieback voltage.

# Assembly and first-article qualification

This is a prototype engineering procedure. No physical steps below have been performed.
Use the current `output/release-candidate` files together; older exports are obsolete.

## Assembly

1. Fabricate the saved four-layer design with **70/35/35/70 µm copper**: 2 oz
   finished outer layers, 1 oz inner layers. Nominal dielectric layers are
   0.200/0.990/0.200 mm, total finished board thickness 1.6 mm. Require at least
   20 µm finished plated-hole barrel copper and bare-board electrical testing
   against the included IPC-D-356 file. The Edge.Cuts centerline is
   **449.152 × 272.910 mm**; it controls dimensions over rounded prose labels.
2. Use the purchase BOM and placement file. F101/F102 are clip-only positions;
   each takes two Keystone 3517 clips. F103–F116 each require two clips plus the
   specified fuse. Total: **32 clips**, with 14 populated fuses. Do not substitute
   fast and slow fuse families based only on current rating. DNP parts remain DNP.
3. Fit four separate Boyd **577202B00000G** heatsinks to D101–D104. These
   STPS20M100ST devices have physical **A–K–A** leads; the project footprint
   numbers them **2–1–2**. Their tabs and heatsinks are electrically live cathodes.
   Keep all four heatsinks separate. Use M3×8 pan-head screws and M3 nuts.
4. Fit Boyd **7020BG** to Q10/Q12/Q14/Q16/Q18 with M3×12 screws and M3 nuts,
   using the lower mounting hole. BTA16-600CRG has an insulated tab; a non-insulated
   BTB variant is not an automatic substitute. Fit **6223BG** to BR3 with M4×16
   and M4 nut through H9. Its 4.14 mm hole is close clearance for M4: verify the
   actual screw passes freely before assembly. Do not drill the heatsink in place.
5. Apply a thin, continuous MG Chemicals **8616** thermal-paste film at each
   device/heatsink interface. The modeled 0.5 °C/W interface allowance must be
   validated with actual surface finish, clamping and torque. Set torque from
   the device mounting instructions and fastener specification; no unverified
   numerical torque has been assigned. Support devices while tightening to avoid
   bending leads or loading solder joints. Check retention under cabinet vibration.
6. Verify capacitor polarity and diode orientation against the assembly drawing
   and netlist. C5/C6/C7/C11/C30: TDK B41252A7109M000, nominal 25.4×45 mm,
   worst-case body 26.4×47 mm. C8/C32: Nichicon LLS2A222MELA, nominal 25×40 mm.
   Allow space above every pressure vent, following the capacitor instructions.
   Check maximum envelopes against the backbox, shields, wiring and service access.
   Native TO-220 models currently show untrimmed leads; cut soldered leads to the
   assembly process specification. The BR3 mounting screw also projects below the
   board; measure standoff clearance rather than relying on an unclipped CAD view.
7. Full-pin stock headers require removal of **only the OEM key pins**, as listed
   in the [connector-key schedule](ASSEMBLY_NOTES.md). A no-connect schematic pin is not automatically
   a key, especially on J113. Match friction-lock side, pin 1, key position and
   housing orientation to an OEM board/harness before inserting connectors.

## Acceptance records

Create a record for each serial number containing BOM revision, PCB hash, fabricator
stackup certificate, bare-board electrical-test result, assembly inspection, applied
loads, instrument settings, waveforms, thermal images, and pass/fail disposition.
A fabricated board is not a qualified replacement until these records exist.

| Stage | Exercise and required observations |
|---|---|
| Mechanical | Compare all mounting holes, outline, connector centers, lock directions and keys with an OEM A-12697-3. Trial fit with power disconnected; check mating access, maximum capacitor/vent envelope, heatsinks, fasteners and rear clearance. |
| Unpowered inspection | Inspect solder joints and thermal pads, polarity, fuse identities and clips. Measure isolation between unrelated supplies and live heatsinks; verify ground and intended GI-return jumper. Check for shorts with the reservoir capacitors discharged. |
| Supply bring-up | Use isolated, current-limited secondary sources and dummy loads, beginning with the raw-input paths. Observe +5 V, +12 V, raw rails, switch nodes and input/output currents. Do not inject power into regulated outputs while raw inputs are held low: reverse-power survival is not qualified. |
| Regulation | Sweep declared secondary voltages, ±10% high line, 50/60 Hz, capacitor tolerance and intended loads. Target +5 V at the receiving CPU connector, including harness/contact/ground drop; board-only DC analysis does not include those losses. Check startup, shutdown, short recovery, minimum load, load steps, UVLO and repeated interruptions. |
| Stability | Measure loop gain with a suitable injection fixture at low/high input and load. Compare with the analytical corner model; confirm phase/gain margin and time-domain damping including pulse-skipping operation. |
| CPU interface | Scope ribbon data/strobes, inversion, setup/hold, ZERO_CROSS and BLANKING at both boards. Verify reset/watchdog, disconnected ribbon, partial supplies and loss of ground do not leave unintended drivers active. |
| Output loads | Start with current-limited resistive/inductive loads. Check all 28 outputs, 64 lamp addresses and five GI strings, including cold-lamp inrush. Measure actual coil/motor R/L, flyback voltage, gate voltage, current and repeated pulse temperature. Verify external tie-back diodes and motor suppression in the real harness. |
| Thermal | Reach equilibrium at worst line/load and intended cabinet temperature with enclosure closed. Record rectifier/triac/MOSFET/regulator/inductor/connector temperatures and local capacitor ambient. TDK ripple qualification assumes local ambient ≤60 °C. Correlate board and heatsink models instead of treating modeled temperatures as measurements. |
| Faults | On appropriately contained sacrificial hardware, verify shorted rows, stuck outputs, missing flyback paths, repeated faults and fuse clearing. Record current, duration, energy and resulting damage. SPICE and a fuse rating alone do not establish containment or semiconductor SOA. |
| Cabinet validation | Run service diagnostics and gameplay with the actual STTNG harness, checking every mechanism. Include ball search, tilt/slam, multiball, gun motors, long service tests and power interruptions. Emulator coverage is not physical mechanism coverage. |
| Production | Establish fixture limits and coverage; retain golden-board waveforms. Perform appropriate EMC/ESD and vibration/temperature testing for the intended product/environment. |

Relevant manufacturer sources: [ST rectifier](https://www.st.com/resource/en/datasheet/stps20m100s.pdf),
[TI reverse-power guidance](https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1308507/tps54360b-power-output-without-input-in-test-environment),
[TDK B41252](https://www.tdk-electronics.tdk.com/inf/20/30/db/aec/B41252.pdf),
[Nichicon LLS](https://www.nichicon.com/en-us/part/lls2a222mela/13160/).
