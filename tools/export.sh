#!/bin/bash
# Production outputs for the WPC Power Driver Board project (KiCad 10 via flatpak).
set -e
KC="flatpak run --command=kicad-cli org.kicad.KiCad"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="$ROOT/output"
for d in gerbers drill bom assembly schematic 3d reports; do rm -rf "$OUT/$d"; done; mkdir -p "$OUT/gerbers" "$OUT/drill" "$OUT/bom" "$OUT/assembly" "$OUT/schematic" "$OUT/3d" "$OUT/reports"
PCB="$ROOT/wpc_power_driver_cost.kicad_pcb"; SCH="$ROOT/wpc_power_driver_cost.kicad_sch"

echo "== ERC / DRC"
$KC sch erc --severity-error --format report -o "$OUT/reports/erc.rpt" "$SCH" | tail -1
$KC pcb drc --severity-error --format report -o "$OUT/reports/drc.rpt" "$PCB" | tail -2

echo "== Gerbers (RS-274X, Protel extensions)"
$KC pcb export gerbers --layers "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts,F.Fab,B.Fab,Dwgs.User" \
   --use-drill-file-origin --no-x2 --subtract-soldermask -o "$OUT/gerbers/" "$PCB" | tail -1
echo "== Drill (Excellon + map)"
$KC pcb export drill --format excellon --excellon-separate-th --excellon-units mm --drill-origin absolute \
   --generate-map --map-format gerberx2 -o "$OUT/drill/" "$PCB" | tail -1
echo "== Position / assembly"
$KC pcb export pos --format csv --units mm --side both --exclude-dnp -o "$OUT/assembly/wpc_power_driver_cost-pos.csv" "$PCB" | tail -1
$KC pcb export pos --format csv --units mm --side both -o "$OUT/assembly/wpc_power_driver_cost-pos-all-incl-dnp.csv" "$PCB" | tail -1
$KC pcb export ipcd356 -o "$OUT/assembly/wpc_power_driver_cost.d356" "$PCB" | tail -1
echo "== BOM"
$KC sch export bom --fields "Reference,Value,Footprint,Manufacturer,MPN,Link,Price,Description,${QUANTITY},${DNP}" --labels "Refs,Value,Footprint,Manufacturer,MPN,Distributor link,Unit price USD (DigiKey qty 1),Description,Qty,DNP" \
   --group-by "Value,Footprint,MPN,DNP" --sort-field Reference --exclude-dnp -o "$OUT/bom/wpc_power_driver_cost-bom-grouped.csv" "$SCH" | tail -1
$KC sch export bom --fields "Reference,Value,Footprint,Manufacturer,MPN,Link,Price,Description,${DNP}" --labels "Ref,Value,Footprint,Manufacturer,MPN,Distributor link,Unit price USD (DigiKey qty 1),Description,DNP" \
   --sort-field Reference -o "$OUT/bom/wpc_power_driver_cost-bom-flat.csv" "$SCH" | tail -1
python3 "$ROOT/tools/bom_report.py"
echo "== Schematic PDF / SVG"
$KC sch export pdf -o "$OUT/schematic/wpc_power_driver_cost-schematic.pdf" "$SCH" | tail -1
$KC sch export svg -o "$OUT/schematic/svg" "$SCH" | tail -1
echo "== Board PDFs"
$KC pcb export pdf --layers "In1.Cu,Edge.Cuts" --include-border-title -o "$OUT/assembly/wpc_power_driver_cost-in1-gndplane.pdf" "$PCB" | tail -1
$KC pcb export pdf --layers "In2.Cu,Edge.Cuts" --include-border-title -o "$OUT/assembly/wpc_power_driver_cost-in2.pdf" "$PCB" | tail -1
$KC pcb export pdf --layers "F.Cu,F.SilkS,Edge.Cuts,F.Fab" --include-border-title -o "$OUT/assembly/wpc_power_driver_cost-top.pdf" "$PCB" | tail -1
$KC pcb export pdf --layers "B.Cu,B.SilkS,Edge.Cuts" --mirror --include-border-title -o "$OUT/assembly/wpc_power_driver_cost-bottom.pdf" "$PCB" | tail -1
$KC pcb export pdf --layers "F.Fab,Edge.Cuts,Dwgs.User" --include-border-title -o "$OUT/assembly/wpc_power_driver_cost-assembly-drawing.pdf" "$PCB" | tail -1
$KC pcb export svg --layers "F.Cu,In2.Cu,B.Cu,F.SilkS,Edge.Cuts" --page-size-mode 2 -o "$OUT/assembly/wpc_power_driver_cost-board.svg" "$PCB" | tail -1
echo "== 3D"
$KC pcb export step --subst-models --no-dnp -o "$OUT/3d/wpc_power_driver_cost.step" "$PCB" | tail -1 || true
$KC pcb render --side top --quality high --zoom 1.05 --width 3840 --height 2160 --background opaque -o "$OUT/3d/wpc_power_driver_cost-top-4k.png" "$PCB" | tail -1 || true
$KC pcb render --side top --quality high --perspective --rotate "-35,0,20" --zoom 1.15 --floor --width 3840 --height 2160 --background opaque -o "$OUT/3d/wpc_power_driver_cost-perspective-4k.png" "$PCB" | tail -1 || true
$KC pcb render --side bottom --quality high --zoom 1.05 --width 3840 --height 2160 --background opaque -o "$OUT/3d/wpc_power_driver_cost-bottom-4k.png" "$PCB" | tail -1 || true
echo "== Netlist"
$KC sch export netlist --format kicadxml -o "$OUT/reports/wpc_power_driver_cost-netlist.xml" "$SCH" | tail -1
echo "== Gerber job / zip"
(cd "$OUT" && zip -qr wpc_power_driver_cost-gerbers.zip gerbers drill && ls -la wpc_power_driver_cost-gerbers.zip)
echo "done"
