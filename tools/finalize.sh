#!/bin/bash
# Final steps for the routed cost board: rail pours + thermal vias, stub cleanup / pours / DRC (finish_board), legend + fiducials,
# final DRC with the project rules, export.   Usage: bash tools/finalize.sh .scratch/flow.kicad_pcb
set -e -o pipefail
PCB="$1"; PROJ=/home/lolz0r/tng/wpc_power_driver_cost; MOD=/home/lolz0r/tng/wpc_power_driver_modern/tools; KC="flatpak run --command=kicad-cli org.kicad.KiCad"; KPY="flatpak run --command=python3 org.kicad.KiCad"
cd "$PROJ"
echo "== GND stitch vias";  python3 $MOD/gnd_stitch.py "$PCB" 2>&1 | tail -1
echo "== rail pours";      $KPY tools/rail_pours.py "$PCB" 2>&1 | grep -v "swig\|Debug\|memory"
echo "== finish (dedupe, thermal vias, GND pours, refill, stub cleanup)"; python3 -u $MOD/finish_board.py "$PCB" 2>&1 | grep -v "swig\|memory leak\|Debug"
echo "== legend";          $KPY tools/legend.py "$PCB" 2>&1 | grep -v "swig\|Debug\|memory"
echo "== final DRC";       $KC pcb drc --refill-zones --save-board --format json --severity-all -o "$PCB.final.json" "$PCB" >/dev/null 2>&1
python3 - "$PCB" <<'PY'
import json, sys, collections
d = json.load(open(sys.argv[1] + '.final.json')); skip = {'lib_footprint_issues', 'silk_overlap', 'silk_over_copper', 'footprint_type_mismatch', 'solder_mask_bridge'}
c = collections.Counter((v['severity'], v['type']) for v in d['violations'] if v['type'] not in skip)
print({k: v for k, v in c.items()}, 'unconnected', len(d['unconnected_items']))
for v in [v for v in d['violations'] if v['severity'] == 'error' and v['type'] not in skip][:12]: print('  ', v['type'], '|', ' / '.join(i.get('description', '')[:45] + ' @%.1f,%.1f' % (i['pos']['x'], i['pos']['y']) for i in v['items']))
for u in d['unconnected_items'][:8]: print('   open:', ' / '.join(i.get('description', '')[:45] for i in u['items']))
PY
