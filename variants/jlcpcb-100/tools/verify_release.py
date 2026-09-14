"""Verify the saved native export and bind independent reports to its exact inputs.
Run after tools/export_release.py, then tools/package_review.py.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
from kicad_env import python as native_python,environment
ROOT=Path(__file__).resolve().parents[1]
REV=ROOT/'output/verification/revision';OUT=ROOT/'output/release-candidate'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';initial=sha(pcb)
 assert read(OUT/'reports/artifact-parity.json')['inputs'][str(pcb)]==initial,'Export current PCB first'
 venv=ROOT/'.venv/bin/python'
 def run(interpreter,script,*args,native=False):
  subprocess.run([str(interpreter),str(ROOT/script),*map(str,args)],cwd=ROOT,env=environment() if native else None,check=True)
 for script in ('tools/export_geometry.py','tools/export_mechanical.py'):run(native_python(),script,native=True)
 run(sys.executable,'tools/verify_interface.py',OUT/'reports/netlist.xml')
 run(sys.executable,'tools/connector_keys.py')
 for script in ('tools/verify_copper_topology.py','tools/review_drc_warnings.py','tools/verify_mechanical.py','tools/verify_manufacturing.py'):run(venv,script)
 geom_hash=sha(REV/'copper_geometry.json')
 for report,script,args in [('copper_dc.json','tools/copper_dc.py',[]),('thermal_mesh_gap.json','tools/thermal_mesh.py',['--gap-aware'])]:
  path=REV/report
  if not path.exists() or read(path).get('geometry_sha256')!=geom_hash:run(venv,script,*args)
 assert sha(pcb)==initial,'PCB changed during verification'
 final=dict(pcb_sha256=initial,mechanical_inputs_sha256=sha(REV/'mechanical-inputs.json'),geometry_sha256=geom_hash)
 (REV/'final-inputs.json').write_text(json.dumps(final,indent=2)+'\n')
 print('Independent release input checks completed; package gate is next.',flush=True)
if __name__=='__main__':main()
