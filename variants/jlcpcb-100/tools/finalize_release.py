"""Validate/refill the existing routed design with native KiCad; no absent sibling scripts."""
import json
from pathlib import Path
import subprocess
from kicad_env import cli,environment
from verify_artifacts import audit

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/revision';OUT.mkdir(parents=True,exist_ok=True)
def run(args):subprocess.run([cli(),*map(str,args)],env=environment(),cwd=ROOT,check=True)
run(['sch','export','netlist','--format','kicadxml','-o',OUT/'netlist.xml',ROOT/'wpc_power_driver_cost.kicad_sch'])
run(['sch','erc','--severity-all','--format','json','-o',OUT/'erc-current.json',ROOT/'wpc_power_driver_cost.kicad_sch'])
run(['pcb','drc','--refill-zones','--save-board','--schematic-parity','--severity-all','--format','json','-o',OUT/'drc-current.json',ROOT/'wpc_power_driver_cost.kicad_pcb'])
d=json.loads((OUT/'drc-current.json').read_text());e=json.loads((OUT/'erc-current.json').read_text())
parity=audit(ROOT/'wpc_power_driver_cost.kicad_pcb',OUT/'netlist.xml');(OUT/'artifact-parity.json').write_text(json.dumps(parity,indent=2)+'\n')
errors=[v for v in d['violations'] if v['severity']=='error']+[v for s in e['sheets'] for v in s['violations'] if v['severity']=='error']
if errors or d['unconnected_items'] or d['schematic_parity'] or not parity['passed']:raise SystemExit('FAILED: inspect verification/revision reports')
print('Electrical/PCB gates passed. DRC warnings:',len(d['violations']),'; see docs/RELEASE_STATUS.md for other release gates.')
