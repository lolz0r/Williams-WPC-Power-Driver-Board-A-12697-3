"""Record every DRC warning with geometry-specific evidence; fail on unknown classes.
Accepted geometry warnings remain visible in KiCad. No rules are disabled.
"""
import argparse,hashlib,json,math
from pathlib import Path
from shapely.geometry import Point,LineString
from sexp import parse,find,find_all
p=argparse.ArgumentParser();p.add_argument('--report',type=Path,default=Path('output/release-candidate/reports/drc.json'));a=p.parse_args()
out=Path('output/verification/revision');drc=json.loads(a.report.read_text());pcb=Path('wpc_power_driver_cost.kicad_pcb');board=parse(pcb.read_text())[0]
items={find(t,'uuid')[1]:t for t in board if isinstance(t,list) and find(t,'uuid')}
topo=json.loads((out/'copper-topology.json').read_text());assert topo['passed']
assert not drc['unconnected_items'] and not drc['schematic_parity']
records=[]
for v in drc['violations']:
 r={'type':v['type'],'items':v['items'],'accepted':False}
 if v['severity']=='error':r['reason']='Error cannot be dispositioned by this tool'
 elif v['type'] in ('track_dangling','via_dangling'):
  r.update(accepted=True,reason='Retained routed copper. Native pad connectivity and independent filled-copper topology both pass. Free-ended copper/one-layer vias do not create an open circuit; deleting whole reported segments previously broke necessary intermediate junctions. Physical signal integrity is a first-article check.')
  t=items[v['items'][0]['uuid']];r['net']=find(t,'net')[-1];r['geometry']=t[:]
 elif v['type']=='track_not_centered_on_via':
  objects=[items[i['uuid']] for i in v['items']];t=next(t for t in objects if t[0]=='segment');via=next(t for t in objects if t[0]=='via')
  start,end=[tuple(map(float,find(t,k)[1:3])) for k in ('start','end')];xy=tuple(map(float,find(via,'at')[1:3]));width=float(find(t,'width')[1]);radius=float(find(via,'size')[1])/2;drill=float(find(via,'drill')[1])/2
  annulus=Point(*xy).buffer(radius,quad_segs=64).difference(Point(*xy).buffer(drill,quad_segs=64));track=LineString([start,end]).buffer(width/2,quad_segs=64)
  area=annulus.intersection(track).area
  r.update(accepted=area>.01 and find(t,'net')[1]==find(via,'net')[1],copper_overlap_excluding_drill_mm2=area,reason='Offset junction retains positive copper overlap with plated annulus, same net; native clearance and independent continuity pass. Centre alignment is a routing style warning.')
 elif v['type']=='missing_courtyard' and 'Footprint H9' in v['items'][0]['description']:
  r.update(accepted=True,reason='H9 is the separate NPTH passage for the BR3/6223BG mounting bolt; its mechanical envelope is reviewed with BR3, not a separately populated component.')
 elif v['type']=='npth_inside_courtyard' and {i['description'] for i in v['items']}=={'NPTH pad of H9','Footprint BR3'}:
  r.update(accepted=True,reason='Intentional BR3 central mounting bolt passage. The NPTH belongs inside the bridge body courtyard and clears electrical copper; verify fastener engagement during assembly.')
 records.append(r)
report={'passed':all(r['accepted'] for r in records),'warnings':len(records),'board_sha256':hashlib.sha256(pcb.read_bytes()).hexdigest(),'drc_sha256':hashlib.sha256(a.report.read_bytes()).hexdigest(),'records':records,'limitation':'Engineering disposition based on geometry, not physical EMC or mechanical qualification.'}
(out/'drc-warning-review.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['# Item-specific DRC warning review','',f'{len(records)} warnings; {sum(r["accepted"] for r in records)} accepted under the stated geometry checks. Rules remain enabled.','']
for n,r in enumerate(records,1):
 lines += [f'## {n}. {r["type"]}', '',r.get('reason','UNREVIEWED'), '']
 for i in r['items']:lines.append(f'* `{i["uuid"]}` — {i["description"]}; {i.get("pos")}')
 if 'copper_overlap_excluding_drill_mm2' in r:lines.append(f'* Track/annulus overlap excluding hole: {r["copper_overlap_excluding_drill_mm2"]:.4f} mm².')
 lines.append('')
(out/'DRC_WARNING_REVIEW.md').write_text('\n'.join(lines));print('Warnings',len(records),'accepted',sum(r['accepted'] for r in records));print([r for r in records if not r['accepted']])
raise SystemExit(0 if report['passed'] else 1)
