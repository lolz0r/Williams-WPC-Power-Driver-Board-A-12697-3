"""Close JLC-3 supply/control connections with width-aware conservative routing.

KiCad DRC and copper-current checks remain mandatory. Local IC fanout matches
the explicit project rule; all other obstacles retain their net-class clearance.
"""
import argparse
import json
import time
from shapely.geometry import box
from close_routes import Board
from prototype_power_spec import ROOT, RAILS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['private','distribution','ground'],default='private')
    p.add_argument('--drc',default='drc-layout2.json');p.add_argument('--nets')
    a=p.parse_args();b=Board(ROOT/'wpc_power_driver_cost.kicad_pcb')
    out=ROOT/'.scratch/prototype-rework';results=[]
    if a.mode=='private':
        nets=sorted({v['net'] for v in b.items if any(v['net'].startswith('/Power_Supply/'+r['ref']+'_') for r in RAILS)})
        areas=[box(x-3,y-2,x+3,y+2) for x,y in [r['center'] for r in RAILS]]
        for v in b.items:
            if 'pin' not in v and any(v['poly'].intersects(area) for area in areas):v['local_clearance']=.2
    elif a.mode=='distribution':
        report=json.loads((out/a.drc).read_text());ids={v['id']:v for v in b.items};nets=[]
        original_groups=b.groups
        for u in report['unconnected_items']:
            items=[ids.get(item['uuid']) for item in u['items']]
            if len(items)!=2 or not all(items):continue
            n=items[0]['net']
            if n=='GND' or n.startswith('unconnected-') or (a.nets and n not in a.nets.split(',')):continue
            left,right=[v['id'] for v in items]
            def pair_groups(net,left=left,right=right):
                gs=original_groups(net)
                aa=next((g for g in gs if any(v['id']==left for v in g)),None)
                zz=next((g for g in gs if any(v['id']==right for v in g)),None)
                return [aa] if aa is zz else [aa,zz]
            b.groups=pair_groups
            width=b.params(n)['track_width']
            # Resistor/IC sense branches carry little current. Main distribution
            # pairs retain their actual 1/3/5 mm net-class widths.
            controls={ref for r in RAILS for ref in r['resistors']}
            def small_branch(v):
                ref,_,pin=v.get('pin','').partition('.')
                return ref in controls or (ref in ['U20','U21'] and pin not in ['7','8','9','10','11'])
            if any(small_branch(v) for v in items):width=.2
            b.routing_options=dict(width=width,clearance=.2,via_diameter=.7 if width<=.4 else 1.,via_drill=.3 if width<=.4 else .5)
            result=b.route(n,.025 if width<=.2 else .05 if width<=.4 else .1,grid_margin=0 if width<=.2 else None)
            row=dict(net=n,width_mm=width,result=result,source_uuid=left,target_uuid=right)
            results.append(row);print(row,flush=True);b.save()
        b.groups=original_groups
        (out/f'route-distribution-pairs-{int(time.time())}.json').write_text(json.dumps(results,indent=2)+'\n')
        return
    else:
        partrefs=set(json.loads((ROOT/'research/prototype-power-migration.json').read_text())['parts'])
        nets=sorted({v['pin'] for v in b.items if v['net']=='GND' and v.get('pin','').split('.')[0] in partrefs})
    if a.nets:nets=a.nets.split(',')
    for n in nets:
        width=.2 if a.mode=='private' else .25 if a.mode=='ground' else b.params(n)['track_width']
        b.routing_options=dict(width=width,clearance=.2,via_diameter=.7 if width<=.4 else 1.,via_drill=.3 if width<=.4 else .5)
        start=time.monotonic()
        for iteration in range(20):
            result=b.route('GND' if a.mode=='ground' else n,.025 if a.mode=='private' else .05 if width<=.4 else .1,
                           grid_margin=0 if a.mode=='private' else None,
                           ground_pin=n if a.mode=='ground' else None)
            row=dict(net=n,width_mm=width,result=result,elapsed_s=round(time.monotonic()-start,2))
            results.append(row);print(row,flush=True);b.save()
            if not result.startswith('added'):break
    (out/f'route-{a.mode}-{int(time.time())}.json').write_text(json.dumps(results,indent=2)+'\n')


if __name__=='__main__':main()
