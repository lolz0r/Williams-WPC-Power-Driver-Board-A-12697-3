"""Explicit short fanouts for the crowded RYQ right-hand signal pins."""
import uuid
from sexp import parse,dump,find,find_all,S
from prototype_power_spec import ROOT,RAILS

def main():
    path=ROOT/'wpc_power_driver_cost.kicad_pcb';d=parse(path.read_text())[0]
    remove={f'/Power_Supply/{r["ref"]}_{suffix}' for r in RAILS for suffix in ['BOOT2','FB']}
    d[:]=[n for n in d if not(isinstance(n,list) and n[0] in ['segment','via'] and find(n,'net')[-1] in remove)]
    # Drop the broad +18 V fill-redundant routes added by the first closure
    # attempt. Subsequent distribution closure uses only exact DRC pairs.
    last_primary=max(i for i,n in enumerate(d) if isinstance(n,list) and n[0]=='segment' and find(n,'net')[-1]=='/Power_Supply/U21_REG' and float(find(n,'width')[1])==1.)
    d[:]=[n for i,n in enumerate(d) if not(i>last_primary and isinstance(n,list) and n[0] in ['segment','via'] and find(n,'net')[-1]=='+18V')]
    def track(net,pts,width=.2):
        for a,b in zip(pts,pts[1:]):d.append(S('segment',S('start',*a),S('end',*b),S('width',width),S('layer','F.Cu'),S('net',net),S('uuid',str(uuid.uuid4()))))
    def via(net,p):d.append(S('via',S('at',*p),S('size',.7),S('drill',.3),S('layers','F.Cu','B.Cu'),S('net',net),S('uuid',str(uuid.uuid4()))))
    for r in RAILS:
        x,y=r['center'];at=lambda dx,dy:(round(x+dx,5),round(y+dy,5));net=lambda name:'/Power_Supply/'+r['ref']+'_'+name
        for name,pts in [('VCC',[(2.04,-1.375),(2.1,-1.9),(3.6,-2.6)]),
                         ('COMP',[(2.4,.25),(4.3,.25)]),
                         ('FB',[(2.4,.75),(3.5,1.5)]),
                         ('BOOT2',[(1.54,-1.4),(1.54,-2.3),(2.5,-3.4)])]:
            track(net(name),[at(*p) for p in pts]);via(net(name),at(*pts[-1]))
        track('GND',[at(2.4,-.75),at(3.5,-1.)]);via('GND',at(3.5,-1.))
    path.write_text(dump(d)+'\n')
    print('Routed separate VCC, COMP, FB, AGND, and BOOT2 escapes')

if __name__=='__main__':main()
