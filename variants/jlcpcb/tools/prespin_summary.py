"""Bind additional pre-spin evidence and expose failures without changing limits."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/prespin';REL=ROOT/'output/release-candidate'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
primary={}
for folder,count in {'blanking':8,'replay-gameplay':14,'replay-flashers':9,'replay-motors':16,'replay-gi':20}.items():
 p=OUT/folder/'results.json';d=read(p);assert d['passed'] and len(d['cases'])==count,folder
 primary[folder]={'passed':True,'cases':count,'sha256':sha(p)}
for name in ['rom-logic.json','gameplay-evidence.json','replay-matrix/matrix_20.69V.json','replay-rl-bound.json','regulator-fixture-audit.json']:
 p=OUT/name;d=read(p);assert d.get('passed',d.get('gameplay_verified')) is True,name
 primary[name]={'passed':True,'sha256':sha(p)}
assert read(OUT/'rom-logic.json')['netlist_sha256']==sha(REL/'reports/netlist.xml')
assert read(OUT/'regulator-fixture-audit.json')['netlist_sha256']==sha(REL/'reports/netlist.xml')
trace=ROOT/'output/verification/pinmame/gameplay-prespin/bus.csv'
for folder in ['replay-gameplay','replay-flashers','replay-motors','replay-gi']:
 d=read(OUT/folder/'results.json');assert d['trace_sha256']==sha(trace)
 assert d['model_sha256']==sha(ROOT/'tools/spice/models.lib')
 for c in d['cases']:assert c['deck_sha256'] in {sha(p) for p in (OUT/folder).glob('*.cir')}
normal=['5v_loss_restart_3A_250n','12v_loss_restart_0.75A_250n','12v_loss_restart_0.02A_250n']
extra=['12v_loss_restart_2A_250n','5v_precharged_output_1A_250n','12v_precharged_output_0.75A_250n']
power=[]
for name in normal+extra:
 p=OUT/'power-sequence'/(name+'.json');assert p.exists(),f'Power-sequence run still pending: {name}'
 d=read(p);assert d['deck_sha256']==sha(p.with_suffix('.cir'))
 power.append(dict(name=name,intended_load_loss_restart=name in normal,simulation_completed=d['checks']['sim_end']['passed'],passed=d['passed'],measurements=d['measurements'],failed_checks={k:v for k,v in d['checks'].items() if not v['passed']},report_sha256=sha(p)))
convergence=read(OUT/'convergence-review.json')
vendor=read(ROOT/'research/vendor-model-sources.json')
for model in vendor.values():assert sha(ROOT/model['local_path'])==model['sha256']
reports=[p for p in OUT.rglob('*.json') if p.name!='summary.json']
result=dict(revision='JLC-2',expanded_checks_executed=True,all_primary_logic_and_output_screens_passed=True,all_simulation_checks_passed=all(p['passed'] for p in power) and convergence['passed'],normal_power_sequence_passed=all(p['passed'] for p in power if p['intended_load_loss_restart']),numerical_convergence_established=convergence['passed'],pcb_sha256=sha(ROOT/'wpc_power_driver_cost.kicad_pcb'),netlist_sha256=sha(REL/'reports/netlist.xml'),primary_checks=primary,power_sequence=power,clamp_change=read(ROOT/'clamp-migration.json'),reports={str(p.relative_to(ROOT)):sha(p) for p in reports},physical_test_completed=False,limitations=['Software-only verification; incomplete numerical refinements are not passes','Watchdog assertion, partial-power behavior, real circuit loss/SOA/fuse coordination, actual transformer/harness, thermal and fit need hardware measurements','Power-sequence body_reverse_peak records instantaneous terminal current including displacement; it is not a separate carrier-current SOA qualification','12 V 2 A case exceeds the rail fuse rating; precharged-output cases exercise an unqualified backfeed condition','The manufacturer S3M model comparison is distinct from the unchanged engineering diode fit used for prior screening'])
result['vendor_model_sources']=vendor
result['pending_refinements']=convergence['pending_refinements']
(OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['revision','expanded_checks_executed','all_simulation_checks_passed','normal_power_sequence_passed','numerical_convergence_established']},indent=2))
