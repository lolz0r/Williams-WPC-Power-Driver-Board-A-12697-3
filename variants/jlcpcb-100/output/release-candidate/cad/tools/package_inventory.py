"""Package only current, independently checked JLC-100 outputs and accepted evidence."""
import csv,hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/release-candidate';V=ROOT/'output/verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
# Never permit a package to imply success from copied historical reports.
for name in ['artifact-parity','manufacturing-check','jlc-sourcing','inventory-design','ryq-land-pattern','jlc-assembly-check','connector-model-check','placement-regression-check','orientation-electrical-parity']:
 d=read(OUT/'reports'/(name+'.json'));assert d['passed'],name
 if 'pcb_sha256' in d:assert d['pcb_sha256']==sha(ROOT/'wpc_power_driver_cost.kicad_pcb'),name+' stale PCB hash'
assembly_check=read(OUT/'reports/jlc-assembly-check.json')
for name,h in assembly_check['file_sha256'].items():assert sha(OUT/name)==h,'Assembly upload changed since validation: '+name
for name,h in assembly_check['connector_library_source_sha256'].items():assert sha(ROOT/name)==h,'Connector library evidence changed since validation: '+name
for name,h in read(OUT/'reports/orientation-electrical-parity.json')['files'].items():assert sha(ROOT/name)==h['before']==h['after'],'Electrical/manufacturing change: '+name
drc=read(OUT/'reports/drc.json');erc=read(OUT/'reports/erc.json');assert not drc['unconnected_items'] and not drc['schematic_parity'];assert not any(v['severity']=='error' for v in drc['violations']);assert not any(v['severity']=='error' for s in erc['sheets'] for v in s['violations'])
geometry=read(V/'revision/copper_geometry.json');assert geometry['pcb_sha256']==sha(ROOT/'wpc_power_driver_cost.kicad_pcb'),'Stale thermal geometry'
thermal=read(V/'revision/thermal_mesh.json');assert all(c['within_device_derated_targets'] for c in thermal['cases']),'Thermal screening failed'
assert thermal['geometry_sha256']==sha(V/'revision/copper_geometry.json'),'Thermal geometry mismatch'
assert thermal['bridge_results_sha256']==sha(V/'inventory-bridge-final/results.json'),'Thermal bridge input mismatch'
mechanical=read(V/'revision/mechanical.json');assert not mechanical['collisions'] and not mechanical['missing_models'],'Mechanical review failed'
assert sha(V/'revision/mechanical-inputs.json')==mechanical['mechanical_inputs_sha256']
for name,h in mechanical['model_file_sha256'].items():assert sha(Path(name))==h,'Stale mechanical model: '+name
for name,h in read(OUT/'reports/connector-model-check.json')['model_sha256'].items():assert sha(ROOT/name)==h,'Stale connector post check: '+name
keys=read(V/'revision/connector-keys.json');assert keys['passed'] and keys['pcb_sha256']==sha(ROOT/'wpc_power_driver_cost.kicad_pcb')
suites=['prototype-readiness/final-supply-min-current','prototype-readiness/supply-high-tolerance','prototype-readiness/supply-low-tolerance','coil-replay-minbreak','flasher-replay','motor-replay','prespin/replay-gi','capacitor-ripple-final','inventory-safety-final','inventory-bridge-final','inventory-rectifier-startup','revision/ribbon-ti','prespin/blanking']
evidence=[]
for name in suites:
 src=V/name;d=read(src/'results.json');assert d['passed'],name
 cases=d.get('cases',[]);assert cases and all(c.get('passed',True) for c in cases),name
 if 'model_sha256' in d:assert d['model_sha256']==sha(ROOT/'tools/spice/models.lib'),name+' model file changed'
 # Retain the report's original simulation-time PCB hash. Electrical source audit
 # connects pre-routing fixtures to this PCB; never rewrite a simulation hash.
 dest=OUT/'reports/verification'/name;shutil.copytree(src,dest,dirs_exist_ok=True)
 evidence.append(dict(suite=name,cases=len(cases),passed=True,report_sha256=sha(src/'results.json'),simulation_pcb_sha256=d.get('pcb_sha256'),scope='Engineering electrical fixture; native component/net audit binds assumptions to final design.'))
for name in ['mechanical-inputs.json','mechanical.json','thermal_mesh.json','copper_geometry.json','connector-keys.json','connector-keys.csv','connector-models.json']:
 dest=OUT/'reports/verification/revision'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(V/'revision'/name,dest)
shutil.copy2(V/'revision/connector-keys.csv',OUT/'assembly/connector-keys.csv')
for folder in ['docs','footprints','models']:shutil.copytree(ROOT/folder,OUT/('cad/'+folder if folder!='docs' else 'docs'),dirs_exist_ok=True)
for p in ROOT.iterdir():
 if p.suffix in ['.kicad_pcb','.kicad_sch','.kicad_sym','.kicad_pro','.kicad_dru'] or p.name in ['fp-lib-table','sym-lib-table']:shutil.copy2(p,OUT/'cad'/p.name)
# Include only supported verification/export scripts, not one-shot historical migrations.
for name in ['export_release.py','export_jlc_bom.py','export_jlc_assembly.py','verify_jlc_assembly.py','placement_rules.py','audit_placement_libraries.py','placement_guide.py','connector_models.py','verify_connector_models.py','verify_placement_regressions.py','fetch_placement_libraries.py','verify_inventory_design.py','verify_manufacturing.py','verify_artifacts.py','verify_ryq.py','connector_keys.py','export_geometry.py','thermal_mesh.py','export_mechanical.py','verify_mechanical.py','package_inventory.py','sexp.py','sourcing.py','kicad_env.py','kicad-cli','kicad-python']:
 dest=OUT/'cad/tools'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'tools'/name,dest)
shutil.copytree(ROOT/'tools/spice',OUT/'cad/tools/spice',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
for name in ['selection.json','baseline-sources.json','search-hardware-results.json']:
 dest=OUT/'cad/research'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'research'/name,dest)
for src in sorted((ROOT/'research/jlc-preview').iterdir()):
 dest=OUT/'cad/research/jlc-preview'/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
shutil.copytree(ROOT/'research/jlc-placement-libraries',OUT/'cad/research/jlc-placement-libraries',dirs_exist_ok=True)
shutil.copy2(ROOT/'research/orientation-baseline-CPL.csv',OUT/'cad/research/orientation-baseline-CPL.csv')
for name in ['search-connector-replacement.json','search-connector-replacement-results.json','search-te-header-replacement.json','search-te-header-replacement-results.json']:
 shutil.copy2(ROOT/'research'/name,OUT/'cad/research'/name)
sourcing=read(OUT/'reports/jlc-sourcing.json')
for code in sourcing['catalog_archives']:
 for suffix in ['.json','.html']:
  src=ROOT/'research/jlcpcb/catalog'/(code+suffix)
  if src.exists():dest=OUT/'cad/research/jlcpcb/catalog'/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
for src in (ROOT/'research/datasheets').glob('*.pdf'):
 if src.stem in sourcing['catalog_archives'] or src.stem in ['TPS552872_Q1','ChemiCon_GPD','Samyoung_NHA']:
  dest=OUT/'cad/research/datasheets'/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
trace=ROOT.parent/'jlcpcb/output/verification/pinmame/gameplay-prespin/bus.csv';dest=OUT/'reports/verification/input-trace/bus.csv';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(trace,dest)
for name in ['coil-replay-minbreak','flasher-replay','motor-replay','prespin/replay-gi']:assert read(V/name/'results.json')['trace_sha256']==sha(trace)
# Every BOM-listed electronic reference has a PCB placement, and all multipart
# quantities are included in the inventory report checked above.
manifest=dict(revision='JLC-100',pcb_sha256=sha(ROOT/'wpc_power_driver_cost.kicad_pcb'),netlist_sha256=sha(OUT/'reports/netlist.xml'),spice_suites=evidence,spice_cases=sum(e['cases'] for e in evidence),trace_sha256=sha(trace),original_sources_unchanged=read(OUT/'reports/inventory-design.json')['original_sources_unchanged'],electronics_inventory_for_100_boards=True,external_hardware_inventory_qualified=False,physical_qualification_performed=False)
manifest['mixed_assembly_upload']={'bom':'jlcpcb-assembly/BOM.csv','cpl':'jlcpcb-assembly/CPL.csv','entries':assembly_check['cpl_entries'],'checks':assembly_check['checks'],'live_jlcpcb_upload_tested':False,'file_sha256':assembly_check['file_sha256']}
manifest['mixed_assembly_upload']['connector_library_entries_checked']=assembly_check['connector_library_entries_checked']
manifest['mixed_assembly_upload']['connector_entries_without_library']=assembly_check['connector_entries_without_library']
manifest['mixed_assembly_upload']['placement_library_audit']=assembly_check['placement_library_audit']
(OUT/'reports/verification-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
readiness=dict(revision='JLC-100',status='SOFTWARE_CHECKED_ENGINEERING_PROTOTYPE',native_manufacturing_exports_complete=True,electrical_errors=0,unconnected_items=0,schematic_parity_issues=0,erc_warnings=sum(len(s['violations']) for s in erc['sheets']),drc_warnings=len(drc['violations']),spice_engineering_cases=manifest['spice_cases'],inventory_board_count=100,electronics_stock_with_spares_passed=True,stock_reserved=False,all_mechanical_hardware_from_JLCPCB=False,production_qualified=False,fab_ready=False,remaining_gates=['Procure external heatsinks, fasteners and paste; all appear in complete BOM; heatsinks/fasteners also in assembly models','JLCPCB DFM, orientation previews and agreement on THT/manual assembly, prepared connectors and soldered F112 service method','First-article connector/key/cabinet fit, loaded supplies and scope measurements, thermal correlation, cold/hot starts and real fault coordination; worst modeled rectifier leg surge244.752A is close to250A rating'])
readiness['mixed_smt_tht_upload_entries']=assembly_check['cpl_entries']
readiness['assembly_upload_format_and_coverage_passed']=True
readiness['live_jlcpcb_upload_tested']=False
readiness['manual_orientation_review_references']=assembly_check['placement_library_audit']['manual_references']
(OUT/'READINESS.json').write_text(json.dumps(readiness,indent=2)+'\n')
(OUT/'README.md').write_text('''# JLC-100 engineering prototype package

For complete SMT and through-hole electronics assembly, upload `jlcpcb-assembly/BOM.csv` and `jlcpcb-assembly/CPL.csv` with `gerbers-and-drills.zip`. The matching pair contains all 440 electronic pieces per board (345 SMT plus 95 THT/inserted parts). Use `jlcpcb-assembly/PCBA-remark.txt` and `placement-map.csv` for separate fuse holders/cartridges and prepared connectors. Read `docs/JLCPCB_UPLOAD.md` before confirming the assembly preview. JLCPCB live import/assembly acceptance has not been tested here.

The complete September 14 orientation audit changes 76 SMT and 18 further connector angles relative to the last uploaded CPL. U1=90°, U2/U3=270°, J110=180° (inward friction wall), J113 remains 90°. `jlcpcb-assembly/connector-orientation-guide.pdf` shows all 39 purchased headers, physical pin 1, tab/notch direction and removed key posts. `component-orientation-check.csv` covers all 440 entries / 69 purchased codes. `orientation-change-log.csv` records the exact delta. The corrected native connector models retain unused posts and remove only the explicit key post.

Unresolved supplier data is explicitly flagged: 15 headers have conflicting pad/model orientations, ten C505166 headers lack 3D housings, three C592598 headers have no public library, D101–D104 have invalid supplier 3D frames, and BR3 requires native polarity/formed-lead placement. The assembler must resolve these against the native guide before manufacture. J120/J121/J126 also require selection of the matched C592598 row and manual preparation. See `docs/CONNECTOR_PREVIEW_REVIEW.md`.

`bom/all-components.csv` is the human-readable complete assembly record, including external heatsinks/fasteners/paste. The 100-board purchasing list is `bom/jlc-electronics-purchase.csv`. These procurement records are not the upload BOM. Heatsinks and fasteners also appear in CAD assembly models; their procurement and fitting require a manual quotation. SMT-only exports remain available under `bom/jlc-smt-bom.csv` and `assembly/jlc-smt-cpl.csv`.

Read `READINESS.json`, `docs/INVENTORY_AND_ASSEMBLY.md`, `docs/SPICE_SCOPE.md` and `reports/verification-manifest.json`. This package passes the recorded software checks; it is not qualified for an untested 100-board production run. Stock is a public dated snapshot, not a reservation. No order has been placed.

The `cad/` project contains the actual selected parts, including all through-hole parts, individually annotated parallel capacitors, fuseholder fields and the two-piece J115. Library footprints/models are local. The accepted simulation reports retain their original run hashes and explicit engineering-model limitations.
''')
# Rebuild gerber archive after final readiness, then hash all delivered files.
with zipfile.ZipFile(OUT/'gerbers-and-drills.zip','w',zipfile.ZIP_DEFLATED) as z:
 for folder in ['gerbers','drill']:
  for p in sorted((OUT/folder).iterdir()):z.write(p,p.relative_to(OUT))
 for name in ['FABRICATION.txt','READINESS.json']:z.write(OUT/name,name)
hashes={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256.json'};(OUT/'SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
archive=ROOT/'output/wpc-sttng-JLC-100-prototype.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,strict_timestamps=False) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(OUT))
archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n');print('Packaged',archive,'cases',manifest['spice_cases'],'bytes',archive.stat().st_size)
small=ROOT/'output/wpc-JLC-100-BOM-CPL.zip'
with zipfile.ZipFile(small,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((OUT/'jlcpcb-assembly').iterdir()):
  if p.is_file():z.write(p,p.name)
 for source,dest in [('assembly/connector-keys.csv','connector-keys.csv'),('docs/INVENTORY_AND_ASSEMBLY.md','INVENTORY_AND_ASSEMBLY.md'),('reports/jlc-assembly-check.json','validation.json')]:z.write(OUT/source,dest)
small.with_suffix('.zip.sha256').write_text(sha(small)+'  '+small.name+'\n');print('BOM/CPL bundle:',small)
