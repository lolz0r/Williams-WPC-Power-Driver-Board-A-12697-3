"""Reconnect native DRC-reported gaps with width-aware, obstacle-checked copper."""
import argparse,json,time
from pathlib import Path
from close_routes import Board
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('drc',type=Path);p.add_argument('--nets');p.add_argument('--name',required=True);a=p.parse_args()
b=Board(ROOT/'wpc_power_driver_cost.kicad_pcb');report=json.loads(a.drc.read_text());ids={v['id']:v for v in b.items};orig=b.groups;records=[]
for un in report['unconnected_items']:
 objects=[ids.get(i['uuid']) for i in un['items']]
 if len(objects)!=2 or not all(objects):continue
 n=objects[0]['net'];left,right=[o['id'] for o in objects]
 if n.startswith('unconnected-') or (a.nets and n not in a.nets.split(',')):continue
 def pair(net):
  groups=orig(net);aa=next((g for g in groups if any(v['id']==left for v in g)),None);zz=next((g for g in groups if any(v['id']==right for v in g)),None)
  assert aa and zz,(n,left,right)
  return [aa] if aa is zz else [aa,zz]
 b.groups=pair
 # Logic branches use the existing 0.2 mm signal rule. Reservoir/fuse power
 # branches retain at least the project net-class width (up to 5 mm).
 width=b.params(n)['track_width']
 if any(o.get('pin','').startswith(('U1.','U2.','U3.','U4.','U5.','U9.','U18.')) for o in objects):width=.2
 if n in ['D'+str(i) for i in range(8)]+['D'+str(i)+'_N' for i in range(8)] or n.endswith('_L') or n.startswith('CLK_') or n in ['BLANKING','GI_BIT5','GI_BIT6','FLIP_RLY_L']:width=.2
 b.routing_options=dict(width=width,clearance=.2,via_diameter=.7 if width<=.4 else 1.2,via_drill=.3 if width<=.4 else .6)
 t=time.monotonic();result=b.route(n,.05 if width<=.4 else .1,grid_margin=0)
 record=dict(net=n,result=result,width_mm=width,source=left,target=right,seconds=round(time.monotonic()-t,2));records.append(record);print(record,flush=True);b.save()
 b.groups=orig
(ROOT/'research'/(a.name+'.json')).write_text(json.dumps(records,indent=2)+'\n')
