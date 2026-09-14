"""Package an exactly verified JLC-3 controlled-prototype release.

Physical qualification is recorded separately from prototype fabrication readiness.
No orders or external uploads are performed.
"""
import csv,hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/release-candidate';REV=ROOT/'output/verification/revision';PRO=ROOT/'output/verification/prototype-readiness'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';h=sha(pcb);net=OUT/'reports/netlist.xml';checks={}
 paths={'artifact_parity':OUT/'reports/artifact-parity.json','manufacturing':OUT/'reports/manufacturing-check.json','sourcing':OUT/'reports/jlc-sourcing.json','ryq_land_pattern':OUT/'reports/ryq-land-pattern.json',
 'source_audit':REV/'source-audit.json','interface':REV/'interface.json','connector_keys':REV/'connector-keys.json','copper_topology':REV/'copper-topology.json','drc_warning_review':REV/'drc-warning-review.json',
 'regulator_fixture_audit':PRO/'regulator-fixture-audit.json','simulation_summary':PRO/'summary.json','bridge_stress':PRO/'bridge-corners/results.json'}
 for name,p in paths.items():
  d=read(p);assert d['passed'],name
  for key in ['pcb_sha256','board_sha256']:
   if key in d:assert d[key]==h,name+' stale board'
  if 'netlist_sha256' in d:assert d['netlist_sha256']==sha(net),name+' stale netlist'
  checks[name]=dict(passed=True,report=str(p.relative_to(ROOT)),sha256=sha(p))
 parity=read(paths['artifact_parity']);assert parity['inputs'][str(pcb)]==h
 drc=read(OUT/'reports/drc.json');erc=read(OUT/'reports/erc.json')
 assert not drc['unconnected_items'] and not drc['schematic_parity']
 assert not any(v['severity']=='error' for v in drc['violations'])
 assert not [v for s in erc['sheets'] for v in s['violations']]
 assert read(paths['drc_warning_review'])['drc_sha256']==sha(OUT/'reports/drc.json')
 geometry=sha(REV/'copper_geometry.json');assert read(paths['copper_topology'])['geometry_sha256']==geometry
 final=read(REV/'final-inputs.json');assert final['pcb_sha256']==h and final['geometry_sha256']==geometry
 mech=read(REV/'mechanical.json');assert not mech['collisions'] and not mech['missing_models']
 assert mech['mechanical_inputs_sha256']==sha(REV/'mechanical-inputs.json')==final['mechanical_inputs_sha256']
 for p,digest in mech['model_file_sha256'].items():assert sha(Path(p))==digest,p
 thermal=read(REV/'thermal_mesh_gap.json');assert thermal['geometry_sha256']==geometry and all(c['within_125C_target'] for c in thermal['cases'])
 dc=read(REV/'copper_dc.json');assert dc['geometry_sha256']==geometry
 for name in ['mechanical','thermal_mesh_gap','copper_dc','final-inputs']:
  p=REV/(name+'.json');checks[name]=dict(report=str(p.relative_to(ROOT)),sha256=sha(p))
 # Supply reports must still be exactly those audited. Historical trials may fail.
 for row in read(paths['regulator_fixture_audit'])['evidence']:assert sha(ROOT/row['report'])==row['sha256']
 source=read(paths['sourcing']);assert source['smt_placements']==344
 assert read(ROOT/'research/prototype-procurement.json')['sourcing_report_sha256']==sha(paths['sourcing'])
 ready=dict(revision='JLC-3',status='READY_FOR_CONTROLLED_PROTOTYPE_BUILD',fab_ready=True,prototype_assembly_files_ready=True,assembly_stock_confirmed=False,production_qualified=False,physical_qualification_performed=False,
  pcb_sha256=h,netlist_sha256=sha(net),electrical_errors=0,unconnected_items=0,schematic_parity_issues=0,erc_warnings=0,drc_warnings=len(drc['violations']),drc_warnings_dispositioned=True,
  outline_mm=[449.152,272.910],stackup_finished_copper_um=[70,35,35,70],smt_placements=source['smt_placements'],checks=checks,
  order_time_checks=['JLCPCB DFM/stackup acceptance, component stock and actual library orientation preview','Through-hole parts, connector keys, fuse clips and external hardware are separate assembly operations'],
  first_article_required=['Current-limited dummy-load startup/shutdown and prebias tests before attaching CPU/harness','Scope switching/PFM ripple, transient overshoot, loop gain and backfeed currents','Measure AC RMS fuse/transformer loading in real diagnostics/gameplay; do not increase specified fuses','Confirm harness/CPU voltage drop, STTNG cabinet fit and simultaneous thermal behavior'],
  limitations='Engineering averaged supply simulations and geometry checks support building a test prototype. They do not establish silicon switching behavior, physical fuse/fault containment, production reliability or universal WPC compatibility.')
 (OUT/'READINESS.json').write_text(json.dumps(ready,indent=2)+'\n')
 docs=OUT/'docs';docs.mkdir(exist_ok=True)
 for name in ['PROTOTYPE_JLC3.md','RELEASE_STATUS.md','ASSEMBLY_AND_FIRST_ARTICLE.md','ASSEMBLY_NOTES.md']:
  shutil.copy2(ROOT/'docs'/name,docs/name)
 reports=OUT/'reports/verification';reports.mkdir(exist_ok=True)
 for name,p in paths.items():shutil.copy2(p,reports/(name+'.json'))
 for name in ['mechanical','thermal_mesh_gap','copper_dc','final-inputs']:
  shutil.copy2(REV/(name+'.json'),reports/(name+'.json'))
 shutil.copy2(REV/'DRC_WARNING_REVIEW.md',reports/'DRC_WARNING_REVIEW.md')
 cad=OUT/'cad';cad.mkdir(exist_ok=True)
 for pattern in ['*.kicad_sch','*.kicad_sym','*.kicad_pcb','*.kicad_pro','*.kicad_dru']:
  for p in ROOT.glob(pattern):shutil.copy2(p,cad/p.name)
 for name in ['fp-lib-table','sym-lib-table']:shutil.copy2(ROOT/name,cad/name)
 for name in ['footprints','models']:shutil.copytree(ROOT/name,cad/name,dirs_exist_ok=True)
 (OUT/'README.md').write_text('''# JLC-3 controlled prototype\n\nUpload the matching `gerbers-and-drills.zip`, `bom/jlc-smt-bom.csv` and\n`assembly/jlc-smt-cpl.csv` to JLCPCB. See `READINESS.json` and\n`docs/PROTOTYPE_JLC3.md` for build scope, settings and first-article checks.\nThrough-hole/manual parts and hardware are listed separately in `bom/`.\nEditable KiCad 10 sources, libraries and models are in `cad/`.\nThis package supports building a test prototype; physical qualification remains to be performed.\n''')
 (OUT/'FABRICATION.txt').write_text((OUT/'FABRICATION.txt').read_text().replace('JLC-3 PROTOTYPE EXPORT — consult READINESS.json before ordering.','JLC-3 — READY FOR CONTROLLED PROTOTYPE FABRICATION; see READINESS.json.'))
 shutil.copy2(ROOT/'research/prototype-procurement.json',OUT/'reports/procurement.json')
 sources=[*ROOT.glob('*.kicad_sch'),*ROOT.glob('*.kicad_sym'),pcb,ROOT/'wpc_power_driver_cost.kicad_pro',ROOT/'wpc_power_driver_cost.kicad_dru',*ROOT.glob('tools/**/*.py'),ROOT/'tools/spice/models.lib',*ROOT.glob('research/prototype-*.json')]
 manifest=dict(revision='JLC-3',pcb_sha256=h,git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),working_tree_modified=True,
  sources={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(sources))},evidence={name:row for name,row in checks.items()},
  note='Hashes identify the uncommitted revision. ROMs and downloaded TI/OEM proprietary models/manuals are not bundled. Older archives are historical.')
 (OUT/'reports/verification-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 with zipfile.ZipFile(OUT/'gerbers-and-drills.zip','w',zipfile.ZIP_DEFLATED,strict_timestamps=False) as z:
  for directory in ['gerbers','drill']:
   for p in sorted((OUT/directory).iterdir()):z.write(p,p.relative_to(OUT))
  for name in ['FABRICATION.txt','READINESS.json']:z.write(OUT/name,name)
 hashes={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256.json'}
 (OUT/'SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
 archive=OUT.parent/'wpc-sttng-JLC-3-prototype.zip';temporary=archive.with_suffix('.zip.tmp')
 with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,strict_timestamps=False) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(OUT))
 with zipfile.ZipFile(temporary) as z:
  assert z.testzip() is None
  for p,digest in hashes.items():assert hashlib.sha256(z.read(p)).hexdigest()==digest,p
 temporary.replace(archive)
 archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n')
 print('Verified JLC-3 prototype package:',archive,'files:',len(hashes),'PCB:',h)
if __name__=='__main__':main()
