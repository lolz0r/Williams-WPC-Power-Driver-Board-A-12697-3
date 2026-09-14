"""Bind review evidence to the final source and package it without declaring release."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,zipfile

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/release-candidate';V=ROOT/'output/verification';R=V/'revision'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')

pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';ph=sha(pcb);net=OUT/'reports/netlist.xml';nh=sha(net)
drc=read(OUT/'reports/drc.json');erc=read(OUT/'reports/erc.json')
assert not [v for v in drc['violations'] if v['severity']=='error']
assert not drc['unconnected_items'] and not drc['schematic_parity']
assert not [v for s in erc['sheets'] for v in s['violations'] if v['severity']=='error']
for name in ['source-audit.json','drc-warning-review.json','copper-topology.json','interface.json','replay-step-comparison.json','replay-rl-bound.json','capacitor-step-comparison.json']:
    d=read(R/name);assert d['passed'],name
    if 'pcb_sha256' in d:assert d['pcb_sha256']==ph,name
    if 'board_sha256' in d:assert d['board_sha256']==ph,name
    if 'netlist_sha256' in d:assert d['netlist_sha256']==nh,name
for name in ['jlc-sourcing.json','manufacturing-check.json']:
    d=read(OUT/'reports'/name);assert d['passed'] and d['pcb_sha256']==ph,name
assert read(OUT/'reports/artifact-parity.json')['passed']
assert read(R/'drc-warning-review.json')['drc_sha256']==sha(OUT/'reports/drc.json')
geometry=sha(R/'copper_geometry.json')
for name in ['copper-topology.json','copper_dc.json','thermal_mesh_gap.json']:
    assert read(R/name)['geometry_sha256']==geometry,name
mech=read(R/'mechanical.json');assert not mech['collisions'] and not mech['missing_models']
assert mech['mechanical_inputs_sha256']==sha(R/'mechanical-inputs.json')
for p,h in mech['model_file_sha256'].items():assert sha(Path(p))==h,p
base=(V/'spice/RESULTS.md').read_text();assert base.count('| PASS |')==211 and '| FAIL |' not in base
for p,h in read(V/'spice/inputs.json').items():assert sha(ROOT/'tools/spice'/p)==h,p
expected={'corners':66,'capacitor-ripple':24,'loop':576,'vendor-buck':6,'vendor-prebiased-start':2,'ribbon-ti':6,'jlc-substitutions':26,'replay-diagnostics':16,'replay-step-sensitivity':16}
for folder,n in expected.items():
    d=read(R/folder/'results.json');assert d['passed'] and len(d['cases'])==n,folder
    for c in d['cases']:
        if 'deck_sha256' not in c:continue
        # Each hashed deck must actually be present with exactly that digest.
        assert c['deck_sha256'] in {sha(p) for p in (R/folder).glob('*.cir')},(folder,c)
terminal=[]
for folder in ['replay-diagnostics','replay-step-sensitivity']:
    d=read(R/folder/'results.json');assert d['model_sha256']==sha(ROOT/'tools/spice/models.lib')
    assert d['trace_sha256']==sha(V/'mame/diagnostics/bus.csv')
    for c in d['cases']:
        val=c['diode_terminal_forward_average_A'];assert 0<=val<3
        terminal.append(dict(run=folder,channel=c['channel'],positive_terminal_average_A=val,limit_A=3,passed=True))
write(R/'replay-terminal-bound.json',dict(passed=True,checks=terminal,scope='Both the terminal-current bound and carrier-conduction metric remain below the 3 A average diode rating. Terminal rectification remains timestep-sensitive; no convergence claim for that diagnostic metric.'))
faults=read(R/'vendor-faults/results.json');assert faults['complete'] and len(faults['cases'])==6
failed=[c['name'] for c in faults['cases'] if not c['passed']]
assert len(failed)==4 and not faults['passed']
mame=read(V/'mame/diagnostics/manifest.json');assert '1 romsets found, 1 were OK.' in (V/'mame/diagnostics/rom-audit.log').read_text()
assert sha(Path(mame['command'][3]))==mame['binary_sha256']
rom=Path('/home/lolz0r/Downloads/sttng_l7.zip');assert sha(rom)==mame['rom_sha256']['sttng_l7.zip']
analysis=read(V/'mame/diagnostics/analysis.json')
assert analysis['last_event_s']-analysis['first_event_s']>=319 and analysis['multi_column_writes']==0
assert all(analysis['writes_by_register'].get(hex(a),0)>0 for a in range(0x3fe0,0x3fe7))

prespin=read(V/'prespin/summary.json');assert prespin['expanded_checks_executed'] and prespin['pcb_sha256']==ph and prespin['netlist_sha256']==nh
assert not prespin['pending_refinements'],prespin['pending_refinements']
readiness=dict(status='ENGINEERING_REVIEW_CANDIDATE_WITH_OPEN_ANALOG_FINDINGS',revision='JLC-2',electronic_redesign_complete=True,software_review_complete=False,expanded_checks_executed=True,all_simulation_checks_passed=prespin['all_simulation_checks_passed'],normal_power_sequence_passed=prespin['normal_power_sequence_passed'],numerical_convergence_established=prespin['numerical_convergence_established'],fabrication_files_verified=True,prototype_recommendation='Hold assembled prototype order pending disposition of the regulator and numerical findings in docs/PRESPIN_VERIFICATION.md',fab_ready=False,production_qualified=False,electrical_errors=0,unconnected_items=0,schematic_parity_issues=0,drc_warnings=len(drc['violations']),drc_warnings_reviewed=True,all_populated_electronics_jlcpcb_purchasable_snapshot=True,failed_or_inconclusive_regulator_cases=failed,remaining_gates=['Regulator full-input sequence/backfeed findings and incomplete fine-step loss/matrix convergence; see prespin summary and continued report','First-article cabinet/harness/fastener/tolerance clearance and actual component fit','Loaded power, simultaneous thermal, faults, fuse clearing and protection/SOA measurements','JLCPCB procurement including twelve short-stock/preorder types; assembly orientation and fabricator DFM confirmation'],physical_qualification='No physical prototype, load or cabinet/harness was tested. See docs/VERIFICATION.md and first-article procedure.')
readiness['prespin_failed_power_cases']=[c['name'] for c in prespin['power_sequence'] if not c['passed']]
readiness['prespin_summary_sha256']=sha(V/'prespin/summary.json')
write(OUT/'READINESS.json',readiness)
native=list(ROOT.glob('*.kicad_pcb'))+list(ROOT.glob('*.kicad_sch'))+list(ROOT.glob('*.kicad_pro'))+list(ROOT.glob('*.kicad_sym'))+[ROOT/'fp-lib-table',ROOT/'sym-lib-table']
native+=list((ROOT/'footprints').rglob('*.kicad_mod'))+list((ROOT/'models').rglob('*.step'))
evidence=[p for p in V.rglob('*') if p.is_file() and p.suffix in ['.json','.md','.log','.cir','.csv','.lua','.png','.pgm','.patch'] and not any(x in p.parts for x in ['cfg','nvram'])]
manifest=dict(revision='JLC-2',created_utc=datetime.now(timezone.utc).isoformat(),pcb_sha256=ph,netlist_sha256=nh,runtime=read(ROOT/'research/runtime-versions.json'),native_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(native)},verification_files={str(p.relative_to(ROOT)):sha(p) for p in sorted(evidence)},verification_tools={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'tools').rglob('*')) if p.is_file() and p.suffix in ['.py','.cir','.lib','.lua','.cpp']},manufacturing_check_sha256=sha(OUT/'reports/manufacturing-check.json'),sourcing_audit_sha256=sha(OUT/'reports/jlc-sourcing.json'),scope='Hashes bind documented model assumptions and all final verification reports to this source. They do not assert that SPICE or MAME physically simulates every PCB feature.',production_qualified=False,failed_regulator_cases=failed)
write(OUT/'reports/verification-manifest.json',manifest)
with zipfile.ZipFile(OUT/'gerbers-and-drills.zip','w',zipfile.ZIP_DEFLATED) as z:
    for directory in ['gerbers','drill']:
        for p in sorted((OUT/directory).iterdir()):z.write(p,p.relative_to(OUT))
    for n in ['FABRICATION.txt','READINESS.json']:z.write(OUT/n,n)
write(OUT/'SHA256.json',{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='SHA256.json'})
docs=[ROOT/'README.md']+list((ROOT/'docs').glob('*.md'))
native_extra=[ROOT/'baseline-sha256.json',ROOT/'pullup-migration.json',ROOT/'clamp-migration.json',ROOT/'research/sttng-manual-source.json',ROOT/'research/vendor-model-sources.json',ROOT/'research/footprint-sources.json',ROOT/'research/kicad-model-sources.json']
with zipfile.ZipFile(ROOT/'output/JLC-2-native-cad.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(native+docs+native_extra):z.write(p,Path('JLC-2')/p.relative_to(ROOT))
review_files=native+native_extra+docs+list(OUT.rglob('*'))+evidence
review_files+=list((ROOT/'research/jlcpcb/catalog').glob('*.json'))+[ROOT/'research/runtime-versions.json']
review_files+=[p for p in (ROOT/'tools').rglob('*') if p.is_file() and p.suffix in ['.py','.cir','.lib','.lua','.json','.txt','.cpp']]
review_files += [ROOT/'tools/kicad-cli',ROOT/'tools/kicad-python']
with zipfile.ZipFile(ROOT/'output/JLC-2-review.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(review_files)):
        if p.is_file():z.write(p,Path('JLC-2')/p.relative_to(ROOT))
archives={n:dict(sha256=sha(ROOT/'output'/n),bytes=(ROOT/'output'/n).stat().st_size) for n in ['JLC-2-native-cad.zip','JLC-2-review.zip']}
write(ROOT/'output/archives-sha256.json',archives)
print(json.dumps(dict(status=readiness['status'],pcb_sha256=ph,failed_regulator_cases=failed,archives=archives),indent=2))
