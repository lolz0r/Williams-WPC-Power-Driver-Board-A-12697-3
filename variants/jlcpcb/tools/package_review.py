"""Assemble a traceable review archive; never infer production readiness from files."""
import csv,hashlib,json,shutil,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/release-candidate';REV=ROOT/'output/verification/revision'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';board_hash=sha(pcb)
 checks={}
 for name,path in [('artifact_parity',OUT/'reports/artifact-parity.json'),('manufacturing',OUT/'reports/manufacturing-check.json'),('interface',REV/'interface.json'),('copper_topology',REV/'copper-topology.json'),('drc_warning_review',REV/'drc-warning-review.json'),('connector_keys',REV/'connector-keys.json'),('corners',REV/'corners/results.json'),('capacitor_ripple',REV/'capacitor-ripple/results.json'),('loop_sensitivity',REV/'loop/results.json'),('vendor_buck',REV/'vendor-buck/results.json'),('vin_present_prebias',REV/'vendor-prebiased-start/results.json')]:
  j=read(path);assert j['passed'],f'{name} did not pass'
  checks[name]={'passed':True,'report':str(path.relative_to(ROOT)),'sha256':sha(path)}
  for field in ('pcb_sha256','board_sha256'):
   if field in j:assert j[field]==board_hash,f'{name} is for an older PCB'
 parity=read(OUT/'reports/artifact-parity.json');assert parity['inputs'][str(pcb)]==board_hash
 assert read(REV/'interface.json')['netlist_sha256']==sha(OUT/'reports/netlist.xml')
 assert read(REV/'drc-warning-review.json')['drc_sha256']==sha(OUT/'reports/drc.json')
 assert read(REV/'copper-topology.json')['geometry_sha256']==sha(REV/'copper_geometry.json')
 mechanical=read(REV/'mechanical.json');assert not mechanical['collisions'] and not mechanical['missing_models']
 assert mechanical['mechanical_inputs_sha256']==sha(REV/'mechanical-inputs.json'), 'Mechanical input report is stale'
 for path,digest in mechanical['model_file_sha256'].items():assert sha(Path(path))==digest, 'Mechanical model changed: '+path
 final=read(REV/'final-inputs.json');assert final['pcb_sha256']==board_hash
 assert final['mechanical_inputs_sha256']==sha(REV/'mechanical-inputs.json') and final['geometry_sha256']==sha(REV/'copper_geometry.json')
 assert read(REV/'copper_dc.json')['geometry_sha256']==sha(REV/'copper_geometry.json'), 'Copper DC report is stale'
 checks['nominal_mechanical']={'models':mechanical['models'],'collisions':0,'missing_referenced_models':0,'sha256':sha(REV/'mechanical.json')}
 drc=read(OUT/'reports/drc.json');erc=read(OUT/'reports/erc.json')
 assert not drc['unconnected_items'] and not drc['schematic_parity']
 ev=[v for s in erc['sheets'] for v in s['violations']];assert not ev
 assert not any(v['severity']=='error' for v in drc['violations'])
 thermal=read(REV/'thermal_mesh_gap.json')
 assert thermal['geometry_sha256']==sha(REV/'copper_geometry.json'), 'Thermal report is stale'
 assert len(thermal['cases'])==8 and all(c['within_125C_target'] for c in thermal['cases']), 'Thermal boundary check failed'
 assert '**Overall: ALL CHECKS PASS**' in (REV/'spice/RESULTS.md').read_text()
 for folder in ('replay-diagnostics','replay-gameplay'):
  replay=read(REV/folder/'results.json');assert replay['passed'], f'{folder} did not pass'
  assert replay['model_sha256']==sha(ROOT/'tools/spice/models.lib'), 'Replay model changed'
  assert replay['requested_channels']==list(range(1,17)), 'Incomplete replay request'
  assert len(replay['cases'])==(16 if folder=='replay-diagnostics' else 14), 'Replay coverage changed'
  assert all('sim_end' in c['checks'] and c['checks']['sim_end']['passed'] for c in replay['cases']), 'Replay did not finish'
 assert read(REV/'replay-step-sensitivity/results.json')['passed'], 'Replay step sensitivity failed'
 assert read(REV/'replay-step-comparison.json')['passed'], 'Replay timestep comparison failed'
 readiness=dict(status='ENGINEERING_CANDIDATE_NOT_PRODUCTION_RELEASED',fab_ready=False,board_sha256=board_hash,
  stackup_finished_copper_um=[70,35,35,70],outline_mm=[449.152,272.910],electrical_errors=0,unconnected_items=0,schematic_parity_issues=0,erc_warnings=0,drc_warnings=len(drc['violations']),drc_warnings_dispositioned=True,checks=checks,
  retained_unresolved_experiments=['vendor-faults: hard raw-rail collapse / external output power with dead input','reverse-protection-trial: bypass did not establish reverse-current qualification; PCB unchanged'],
  remaining_gates=['Real regulator shutdown/backfeed and switch SOA; hard-clamp vendor model is not a characterized body-diode model','Simultaneous-load thermal correlation, actual load/harness data and fuse/fault coordination','OEM cabinet/harness fit and tolerances; J106/J111 prevent a universal drop-in claim','Fabricator DFM acceptance, finished stack/drill certification and bare-board electrical test','Complete procurement stock confirmation at order time and first-article/EMC/ESD/vibration qualification'],
  physical_qualification_performed=False,details='docs/RELEASE_STATUS.md')
 (OUT/'READINESS.json').write_text(json.dumps(readiness,indent=2)+'\n')
 # Procurement view: one line per exact manufacturer/MPN, including all 32 clips.
 grouped={}
 for row in csv.DictReader((OUT/'bom/purchase-bom.csv').open()):
  key=(row['Manufacturer'],row['MPN']);g=grouped.setdefault(key,dict(Manufacturer=key[0],MPN=key[1],Qty=0,References=[],Links=[]))
  g['Qty']+=int(row['Qty']);g['References'].append(row['Refs'])
  if row['Link'] and row['Link'] not in g['Links']:g['Links'].append(row['Link'])
 with (OUT/'bom/order-bom.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,['Manufacturer','MPN','Qty','References','Links']);writer.writeheader()
  for key,g in sorted(grouped.items()):writer.writerow(dict(g,References='; '.join(g['References']),Links='; '.join(g['Links'])))
 (OUT/'README.md').write_text('''# WPC STTNG engineering candidate

This archive is not a production release. Read [READINESS.json](READINESS.json)
and [release status](docs/RELEASE_STATUS.md) before ordering or assembly.

- [Perspective render](3d/perspective.png), [top](3d/top.png), [bottom](3d/bottom.png), [STEP](3d/board.step).
- [Gerbers and drills](gerbers-and-drills.zip), [fabrication specification](FABRICATION.txt), [order BOM](bom/order-bom.csv).
- [Schematic](schematic/schematic.pdf), assembly drawings and placements in `assembly/`.
- Editable KiCad sources and project libraries in `cad/`; standard KiCad 10 libraries are also required.
- [Assembly procedure](docs/ASSEMBLY_AND_FIRST_ARTICLE.md), [sourcing observations](docs/SOURCING_REVIEW.md), verification summaries in `reports/`.
- [SHA-256 file manifest](SHA256.json) and [source provenance](reports/source-provenance.json).

Copper: 2 oz FINISHED outer / 1 oz inner. The reproduction instructions refer
to the original repository workspace, which contains the verification tools,
raw simulation/emulator traces and local dependency caches. ROMs and downloaded
third-party models/manuals are not redistributed in this archive.
''')
 docs=OUT/'docs';docs.mkdir(exist_ok=True)
 for name in ('RELEASE_STATUS.md','VERIFICATION.md','SOURCING_REVIEW.md','ASSEMBLY_AND_FIRST_ARTICLE.md','ASSEMBLY_NOTES.md'):
  shutil.copy2(ROOT/'docs'/name,docs/name)
 review=OUT/'reports/verification';review.mkdir(exist_ok=True)
 for name in ('final-inputs.json','mechanical-inputs.json','capacitor-ripple-before-c5-upgrade.json','replay-diagnostics-before-pwl-fix.json','replay-gameplay-before-pwl-fix.json','replay-step-comparison.json','interface.json','copper-topology.json','drc-warning-review.json','DRC_WARNING_REVIEW.md','connector-keys.json','connector-keys.csv','mechanical.json','copper_dc.json','thermal_mesh_gap.json'):
  shutil.copy2(REV/name,review/name)
 for folder in ('corners','capacitor-ripple','loop','vendor-buck','vendor-faults','vendor-prebiased-start','reverse-protection-trial','replay-diagnostics','replay-gameplay','replay-step-sensitivity'):
  shutil.copy2(REV/folder/'results.json',review/(folder+'.json'))
 shutil.copy2(REV/'spice/RESULTS.md',review/'SPICE_RESULTS.md');shutil.copy2(REV/'spice/inputs.json',review/'spice-inputs.json')
 shutil.copy2(ROOT/'output/verification/pinmame/provenance.json',review/'pinmame-provenance.json')
 cad=OUT/'cad';cad.mkdir(exist_ok=True)
 for pattern in ('*.kicad_sch','*.kicad_sym'):
  for p in ROOT.glob(pattern):shutil.copy2(p,cad/p.name)
 for name in ('wpc_power_driver_cost.kicad_pcb','wpc_power_driver_cost.kicad_pro','fp-lib-table','sym-lib-table'):
  shutil.copy2(ROOT/name,cad/name)
 for name in ('footprints','models'):shutil.copytree(ROOT/name,cad/name,dirs_exist_ok=True)
 source_files=[pcb,*ROOT.glob('*.kicad_sch'),*ROOT.glob('*.kicad_sym'),ROOT/'wpc_power_driver_cost.kicad_pro',*ROOT.glob('tools/**/*.py'),*ROOT.glob('tools/spice/**/*.cir'),ROOT/'tools/spice/models.lib']
 provenance={'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'working_tree_modified':True,'sources':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(source_files))},'note':'Uncommitted engineering revision; hashes identify inputs. ROMs, downloaded vendor models and OEM manual scans are not distributed.'}
 (OUT/'reports/source-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
 with zipfile.ZipFile(OUT/'gerbers-and-drills.zip','w',zipfile.ZIP_DEFLATED) as z:
  for directory in ('gerbers','drill'):
   for f in sorted((OUT/directory).iterdir()):z.write(f,f.relative_to(OUT))
  for name in ('FABRICATION.txt','READINESS.json'):z.write(OUT/name,name)
 hashes={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256.json'}
 (OUT/'SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n')
 archive=OUT.parent/'wpc-sttng-engineering-candidate.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(OUT))
 archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n')
 print('Verified review archive:',archive)
 print('Production release gates remain open:',len(readiness['remaining_gates']))
if __name__=='__main__':main()
