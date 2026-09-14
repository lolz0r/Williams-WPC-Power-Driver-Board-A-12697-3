"""Place JLC-3 supply cells and route their primary current loops.

Consumes the reviewed schematic migration. Removes obsolete regulator
copper and clips crossing tracks inside the two documented work areas.
Remaining connections are closed separately and checked by KiCad.
"""
import copy
import json
import math
import uuid
from pathlib import Path
from shapely.geometry import LineString, Point, box
from sexp import parse, dump, find, find_all, S
from kicad_pcb import Board as Writer
from prototype_power_spec import ROOT, RAILS, PIN_NAMES

def uid():return str(uuid.uuid4())
def props(n):return {p[1]:p[2] for p in find_all(n,'property')}
def xy(n,key):return tuple(map(float,find(n,key)[1:3]))


def main():
    path=ROOT/'wpc_power_driver_cost.kicad_pcb';doc=parse(path.read_text())[0]
    old={props(f)['Reference']:f for f in find_all(doc,'footprint')}
    assert props(old['U20'])['MPN']=='TPS54360BDDAR', 'Migration already applied'
    migration=json.loads((ROOT/'research/prototype-power-migration.json').read_text());parts=migration['parts']
    sch=parse((ROOT/'power_supply.kicad_sch').read_text())[0]
    ic_symbol=next(s for s in find_all(sch,'symbol') if props(s)['Reference']=='U20')
    parent=str(find(find(find(ic_symbol,'instances'),'project'),'path')[1])
    writer=Writer('JLC-3 supply cells');fps={};log={'removed_copper':{},'placements':{}}
    windows=[box(255,39,287,81),box(131,49,161,93)]
    for r,window in zip(RAILS,windows):
        private='/Power_Supply/'+r['ref']+'_'
        kept=[];removed=0
        for item in doc:
            if not isinstance(item,list) or item[0] not in ['segment','via','zone']:
                kept.append(item);continue
            net=find(item,'net');net=str(net[-1]) if net else ''
            if net.startswith(private):removed+=1;continue
            # The dense new cell requires moving the crossing tracks as well.
            # Keep their stubs at the work-area boundary for width-aware closure.
            if item[0]=='zone':kept.append(item);continue
            if item[0]=='via' and window.contains(Point(xy(item,'at'))):removed+=1;continue
            if item[0]=='segment':
                line=LineString([xy(item,'start'),xy(item,'end')])
                if line.intersects(window):
                    remaining=line.difference(window);removed+=1
                    geoms=list(remaining.geoms) if hasattr(remaining,'geoms') else [remaining]
                    for g in geoms:
                        if g.is_empty or g.length<.001:continue
                        n=copy.deepcopy(item);find(n,'start')[1:]=list(g.coords[0]);find(n,'end')[1:]=list(g.coords[-1]);find(n,'uuid')[1]=uid();kept.append(n)
                    continue
            kept.append(item)
        doc=kept;log['removed_copper'][r['ref']]=removed
    for r in RAILS:
        cx,cy=r['center'];ci1,ci2,cb1,cc,cp,co1=r['old_caps'];cb2,cv,chi,cho,ci3,ci4,co2=r['new_caps']
        en1,en2,rt,fb1,fb2,rc=r['resistors']
        positions={r['ref']:(0,0,0),r['inductor']:(0,11,0),
            ci1:(-2.8,-6.5,180),ci2:(-2.8,-11.5,180),ci3:(-8,-6.5,180),ci4:(-8,-11.5,180),
            co1:(2.8,-6.5,0),co2:(2.8,-11.5,0),cv:(7,0,0),
            cb1:(-2.6,3.2,0),cb2:(2.6,3.2,180),chi:(-.52,-2.55,0),cho:(.52,-3.65,180),
            en1:(-6,2.5,0),en2:(-10,2.5,0),rt:(-11,7,0),fb1:(7,3,0),fb2:(11,3,0),
            rc:(10,7,0),cc:(10,11,0),cp:(14,7,0),r['shunt']:(9,-14,0)}
        for ref in [ref for ref in parts if ref in positions]:
            p=parts[ref];prop=p['properties'];dx,dy,angle=positions[ref]
            nets={num:(net if net is not None else f"unconnected-({ref}-{PIN_NAMES[int(num)-1]}-Pad{num})") for num,net in p['nets'].items()}
            pathid=parent+'/'+p['uuid']
            fp=writer.footprint(ref,prop['Footprint'],cx+dx,cy+dy,angle,prop['Value'],nets,
                path=pathid,sheetname='Power_Supply',sheetfile='power_supply.kicad_sch',center_on_pads=False,
                extra_fields={k:v for k,v in prop.items() if k not in ['Reference','Value','Footprint','Datasheet','Description']},ref_size=.8)
            next(z for z in find_all(fp,'property') if z[1]=='Description')[2]=prop.get('Description','')
            # Preserve exact existing inductor body models, including the reviewed height.
            if ref==r['inductor']:
                fp[:]=[z for z in fp if not(isinstance(z,list) and z[0]=='model')]
                fp.extend(copy.deepcopy(find_all(old[ref],'model')))
            for m in find_all(fp,'model'):m[1]=m[1].replace('${KICAD10_3DMODEL_DIR}','${KIPRJMOD}/models/kicad')
            if ref==r['ref']:
                for pad in find_all(fp,'pad'):
                    if pad[1]:pad.append(S('pinfunction',PIN_NAMES[int(pad[1])-1]))
            fps[ref]=fp;log['placements'][ref]=[cx+dx,cy+dy,angle]
        # Bulk output capacitors retain their footprints; C2 moves clear of the
        # new U21 input bank. Its two nets are routed to the existing distribution.
        for ref in r['bulk']:
            fp=copy.deepcopy(old[ref]);fps[ref]=fp
            if ref=='C2':
                find(fp,'at')[1:]=[122.5,58.7,0]
                for item in find_all(fp,'pad')+find_all(fp,'property')+find_all(fp,'fp_text'):
                    at=find(item,'at')
                    if at and len(at)>3:at[3]=(float(at[3])+90)%360
            for key,value in parts[ref]['properties'].items():
                v=next((z for z in find_all(fp,'property') if z[1]==key),None)
                if v is not None:v[2]=value
            log['placements'][ref]=find(fp,'at')[1:]
    replace=set(parts)|set(migration['removed_refs'])
    doc[:]=[n for n in doc if not(isinstance(n,list) and n[0]=='footprint' and props(n)['Reference'] in replace)]
    doc.extend(fps.values())
    def pad(ref,num):
        f=fps[ref];a=find(f,'at');x,y=map(float,a[1:3]);angle=math.radians(float(a[3]) if len(a)>3 else 0)
        p=next(p for p in find_all(f,'pad') if p[1]==str(num));px,py=xy(p,'at')
        return (round(x+px*math.cos(angle)+py*math.sin(angle),6),round(y-px*math.sin(angle)+py*math.cos(angle),6))
    def track(net,points,w=.4,layer='F.Cu'):
        for a,b in zip(points,points[1:]):
            if math.dist(a,b)<.00001:continue
            doc.append(S('segment',S('start',*a),S('end',*b),S('width',w),S('layer',layer),S('net',net),S('uuid',uid())))
    def via(net,p,size=.8,drill=.4):
        doc.append(S('via',S('at',*p),S('size',size),S('drill',drill),S('layers','F.Cu','B.Cu'),S('net',net),S('uuid',uid())))
    for r in RAILS:
        u=r['ref'];x,y=r['center'];n=lambda suffix:'/Power_Supply/'+u+'_'+suffix
        at=lambda dx,dy:(round(x+dx,6),round(y+dy,6))
        ci1,ci2,cb1,cc,cp,co1=r['old_caps'];cb2,cv,chi,cho,ci3,ci4,co2=r['new_caps']
        # Both switch nodes leave the bottom; VIN/VOUT feed local ceramics
        # from the top. This keeps the high-frequency paths on the top layer.
        for sign,sw,cb,lpin in [(-1,'SW1',cb1,1),(1,'SW2',cb2,2)]:
            track(n(sw),[at(sign*.54,1.55),at(sign*.54,2.05),at(sign*1.3,3.6)],.25)
            track(n(sw),[at(sign*1.3,3.6),at(sign*3.,5.),pad(r['inductor'],lpin)],1.2)
            track(n(sw),[pad(cb,2),at(sign*1.3,3.6)],.25)
        for net,dx,first,second,hf in [(r['vin'],-1.04,ci1,ci2,chi),(n('REG'),1.04,co1,co2,cho)]:
            track(net,[at(dx,-1.55),pad(hf,1),pad(first,1)],.25)
            track(net,[pad(first,1),pad(second,1)],.9)
        pa,pb=pad(ci2,1),pad(ci4,1);yy=pa[1]-2.5
        track(r['vin'],[pa,(pa[0],yy),(pb[0],yy),pb],.8)
        track(r['vin'],[pad(ci3,1),pad(ci4,1)],.8)
        # Central PGND connects both HF bypasses and a short, broad thermal
        # return beneath the device. No via is placed in a paste aperture.
        track('GND',[at(0,-1.55),pad(chi,2),pad(cho,2),at(0,-9.)],.25)
        via('GND',at(0,-9.),.6,.3)
        track('GND',[at(0,1.55),at(0,3.5)],.25)
        track('GND',[at(0,3.5),at(0,6.8)],.8)
        for dy in [4.4,5.6,6.8]:via('GND',at(0,dy))
        for ref in [ci1,ci2,ci3,ci4,co1,co2,cv]:
            a=pad(ref,2);v=(a[0],a[1]+(-2.5 if ref==cv else 2.5))
            track('GND',[a,v],.6);via('GND',v,.6,.3)
        # Current shunt power path. ISP and ISN signal connections are routed
        # separately to the two pad centers, not along the load tracks.
        target=pad(r['shunt'],1);source=pad(co2,1)
        track(n('REG'),[source,(source[0],target[1]),target],1.)
    find(find(doc,'title_block'),'rev')[1]='JLC-3'
    for t in find_all(doc,'gr_text'):
        if isinstance(t[1],str):t[1]=t[1].replace('JLC-2','JLC-3')
    path.write_text(dump(doc)+'\n')
    (ROOT/'research/prototype-power-layout.json').write_text(json.dumps(log,indent=2)+'\n')
    print('Placed supply cells and primary loops; signal/distribution closure and DRC still required')


if __name__=='__main__':main()
