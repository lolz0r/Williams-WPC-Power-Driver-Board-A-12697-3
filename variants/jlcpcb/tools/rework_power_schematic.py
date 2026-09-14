"""One-time JLC-2 -> JLC-3 regulator schematic/land-pattern migration.

Preserves the routed project's remaining sheets and all connector connections.
Never invokes the historical whole-board generator.
"""
import copy
import hashlib
import json
import uuid
from sexp import parse, dump, find, find_all, S, Sym
from prototype_power_spec import ROOT, RAILS, PIN_NAMES, IC_FOOTPRINT, components


def uid(): return str(uuid.uuid4())
def props(n): return {p[1]:p[2] for p in find_all(n,'property')}
def field(n,key,value):
    p = next((p for p in find_all(n,'property') if p[1]==key), None)
    if p is None:
        p=copy.deepcopy(next(p for p in find_all(n,'property') if p[1]=='MPN'))
        p[1]=key;n.append(p)
    p[2]=str(value)


def footprint():
    """TI drawing 4228792/A (RYQ0021B), recommended land and stencil.

    Pin 9 is 0.33 mm wide over its central 2.35 mm, narrowing to 0.25 mm
    at both ends. Overlapping same-number rectangles preserve that profile.
    Separate paste-only apertures split the five long power terminals.
    """
    name=IC_FOOTPRINT.split(':')[1]
    f=S('footprint',name,S('version',20241229),S('generator',Sym('pcbnew')),
        S('layer','F.Cu'),S('descr','TI RYQ0021B, 4228792/A 07/2022, recommended land/stencil'),S('attr',Sym('smd')))
    for key,val,y in [('Reference','REF**',-2.5),('Value',name,2.5)]:
        f.append(S('property',key,val,S('at',0,y,0),S('layer','F.SilkS' if key=='Reference' else 'F.Fab'),
                   S('effects',S('font',S('size',.8,.8),S('thickness',.12)))))
    def rect(layer,x0,y0,x1,y1,width):
        f.append(S('fp_rect',S('start',x0,y0),S('end',x1,y1),S('stroke',S('width',width),S('type',Sym('default'))),S('fill',Sym('none')),S('layer',layer)))
    rect('F.Fab',-2.5,-1.5,2.5,1.5,.1);rect('F.CrtYd',-3.,-2.,3.,2.,.05)
    f.append(S('fp_circle',S('center',-3.,-.75),S('end',-2.85,-.75),S('stroke',S('width',.1),S('type',Sym('default'))),S('fill',Sym('solid')),S('layer','F.SilkS')))
    def pad(num,x,y,w,h,paste=True,mask=True):
        ls=['F.Cu'] + (['F.Paste'] if paste else []) + (['F.Mask'] if mask else [])
        f.append(S('pad',str(num),Sym('smd'),Sym('roundrect'),S('at',x,y),S('size',w,h),
                   S('layers',*ls),S('roundrect_rratio',min(.05/min(w,h),.25)),S('clearance',.16),S('solder_mask_margin',.05)))
    for i in range(4):
        pad(i+1,-2.4,-.75+.5*i,.6,.25)
        pad(17-i,2.4,-.75+.5*i,.6,.25)
    for num,x,y,h in [(5,-2.04,1.375,.65),(6,-1.54,1.4,.6),(12,1.54,1.4,.6),(13,2.04,1.375,.65),
                      (18,2.04,-1.375,.65),(19,1.54,-1.4,.6),(20,-1.54,-1.4,.6),(21,-2.04,-1.375,.65)]:
        pad(num,x,y,.25,h)
    for num,x in [(7,-1.04),(8,-.54),(9,0),(10,.54),(11,1.04)]:
        pad(num,x,0,.25,3.4,paste=False)
        if num==9: pad(num,x,0,.33,2.35,paste=False)
        for y in [-1.2,0,1.2]:
            f.append(S('pad','',Sym('smd'),Sym('roundrect'),S('at',x,y),S('size',.25,1.),
                       S('layers','F.Paste'),S('roundrect_rratio',.2)))
    f.append(S('model','${KIPRJMOD}/models/TI_RYQ0021B_envelope.step',S('offset',S('xyz',0,0,0)),S('scale',S('xyz',1,1,1)),S('rotate',S('xyz',0,0,0))))
    p=ROOT/'footprints/wpc_cost.pretty'/f'{name}.kicad_mod';p.write_text(dump(f)+'\n')


def main():
    path=ROOT/'power_supply.kicad_sch';doc=parse(path.read_text())[0]
    old={props(s)['Reference']:s for s in find_all(doc,'symbol')}
    assert props(old['U20'])['MPN']=='TPS54360BDDAR', 'Migration already applied'
    originals={ref:props(s) for ref,s in old.items()}
    allparts={ref:p for r in RAILS for ref,p in components(r,originals).items()}
    expected={ref for r in RAILS for ref in [r['ref'],*r['old_caps'],*r['bulk'],*r['resistors'],r['inductor'],r['diode']]}
    boxes=[(345,30,518,129),(345,130,518,220)]
    def inside(x,y): return any(x0<=x<=x1 and y0<=y<=y1 for x0,y0,x1,y1 in boxes)
    removed=[];kept=[]
    for n in doc:
        if not isinstance(n,list) or n[0]=='lib_symbols': kept.append(n);continue
        at=find(n,'at')
        pts=[]
        if at:pts=[tuple(map(float,at[1:3]))]
        elif n[0]=='wire':pts=[tuple(map(float,p[1:3])) for p in find(n,'pts')[1:]]
        if pts and all(inside(*p) for p in pts):
            if n[0]=='symbol' and not props(n)['Reference'].startswith('#'):
                removed.append(props(n)['Reference'])
        else:
            assert not (n[0]=='wire' and any(inside(*p) for p in pts)), 'Unexpected wire crossing migration boundary'
            kept.append(n)
    assert set(removed)==expected,(set(removed)-expected,expected-set(removed))
    doc=kept
    name='TPS552892RYQR';libid='wpc_symbols:'+name
    lib=S('symbol',libid,S('pin_names',S('offset',.8)),S('in_bom',Sym('yes')),S('on_board',Sym('yes')),
          S('property','Reference','U',S('at',0,18,0),S('effects',S('font',S('size',1.27,1.27)))),
          S('property','Value',name,S('at',0,16,0),S('effects',S('font',S('size',1.27,1.27)))),
          S('property','ki_fp_filters','TI_RYQ0021B*',S('at',0,0,0),S('effects',S('font',S('size',1.27,1.27)),S('hide',Sym('yes')))),
          S('symbol',name+'_0_1',S('rectangle',S('start',-10.16,15.24),S('end',10.16,-15.24),S('stroke',S('width',.254),S('type',Sym('default'))),S('fill',S('type',Sym('background'))))))
    sub=S('symbol',name+'_1_1');pinpos={}
    for number,pname in enumerate(PIN_NAMES,1):
        left=number<=11;x=-15.24 if left else 15.24;y=12.7-2.54*((number-1) if left else number-12);a=0 if left else 180
        typ='power_in' if number in [7,9,17] else 'power_out' if number in [11,18] else 'open_collector' if number in [3,4] else 'passive' if number in [8,10,19,20] else 'output' if number in [15,16] else 'input'
        pinpos[str(number)]=(x,-y,a)
        sub.append(S('pin',Sym(typ),Sym('line'),S('at',x,y,a),S('length',5.08),
                     S('name',pname,S('effects',S('font',S('size',1.,1.)))),S('number',str(number),S('effects',S('font',S('size',1.,1.))))))
    lib.append(sub);find(doc,'lib_symbols').append(lib)
    # Clone and preserve UUIDs of surviving references. New refs get fresh UUIDs.
    def place(ref,x,y,is_ic=False):
        p=allparts[ref];s=copy.deepcopy(old[p['template']]);oldat=find(s,'at');dx=x-float(oldat[1]);dy=y-float(oldat[2]);oldat[1:]=[x,y,0]
        if ref not in old:
            find(s,'uuid')[1]=uid()
        for prop in find_all(s,'property'):
            at=find(prop,'at');at[1]=float(at[1])+dx;at[2]=float(at[2])+dy
        for key,value in p['properties'].items():field(s,key,value)
        for key,off in [('Reference',(1.5,-1.8)),('Value',(1.5,.2))]:
            prop=next(z for z in find_all(s,'property') if z[1]==key);find(prop,'at')[1:]=[x+off[0],y+off[1],0]
            font=find(find(prop,'effects'),'font');find(font,'size')[1:]=[.9,.9]
        def fix_instance(n):
            for c in n:
                if isinstance(c,list):
                    if c[0]=='reference':c[1]=ref
                    else:fix_instance(c)
        fix_instance(find(s,'instances'))
        if is_ic:
            find(s,'lib_id')[1]=libid
            s[:]=[z for z in s if not(isinstance(z,list) and z[0]=='pin')]
            s.extend(S('pin',str(i),S('uuid',uid())) for i in range(1,22))
            positions=pinpos
        else:
            # All two-terminal templates in this block are vertical at 0 degrees.
            symid=find(s,'lib_id')[1];emb=next(z for z in find_all(find(doc,'lib_symbols'),'symbol') if z[1]==symid)
            positions={}
            for unit in find_all(emb,'symbol'):
                for pin in find_all(unit,'pin'):
                    at=find(pin,'at');positions[find(pin,'number')[1]]=(float(at[1]),-float(at[2]),float(at[3]))
        doc.append(s);p['uuid']=find(s,'uuid')[1]
        for num,net in p['nets'].items():
            px,py,angle=positions[num];a=(round(x+px,4),round(y+py,4))
            if net is None:
                doc.append(S('no_connect',S('at',*a),S('uuid',uid())));continue
            import math
            end=(round(a[0]-2.54*math.cos(math.radians(angle)),4),round(a[1]+2.54*math.sin(math.radians(angle)),4))
            doc.append(S('wire',S('pts',S('xy',*a),S('xy',*end)),S('stroke',S('width',0),S('type',Sym('default'))),S('uuid',uid())))
            local=net.startswith('/Power_Supply/');text=net.split('/')[-1] if local else net
            rotation={0:180,180:0,90:270,270:90}[int(angle)%360]
            label=S('label' if local else 'global_label',text)
            if not local:label.append(S('shape',Sym('passive')))
            label.extend([S('at',*end,rotation),S('effects',S('font',S('size',.8,.8)),S('justify',Sym('left' if rotation in [0,90] else 'right'),Sym('bottom'))),S('uuid',uid())])
            doc.append(label)
    for r in RAILS:
        base=0 if r['ref']=='U20' else 90.17
        place(r['ref'],375.92,60.96+base,True)
        refs=[ref for ref in components(r,originals) if ref!=r['ref']]
        for i,ref in enumerate(refs):place(ref,round(350.52+13.97*(i%12),4),round(99.06+20.32*(i//12)+base,4))
        title=f"{r['ref']}: TPS552892 buck-boost / 395 kHz / PFM / {r['out']} / current limit {0.05/r['shunt_ohm']:.2f} A nominal"
        doc.append(S('text',title,S('at',350.52,34.29+base,0),S('effects',S('font',S('size',1.2,1.2)),S('justify',Sym('left'))),S('uuid',uid())))
        doc.append(S('text','Local output ceramics precede the sense resistor; bulk capacitors and feedback follow it. EXTVCC open selects internal VCC.',
                     S('at',350.52,81.28+base,0),S('effects',S('font',S('size',1.,1.)),S('justify',Sym('left'))),S('uuid',uid())))
    path.write_text(dump(doc)+'\n')
    library_path=ROOT/'wpc_symbols.kicad_sym';library=parse(library_path.read_text())[0]
    external=copy.deepcopy(lib);external[1]=name;library.append(external);library_path.write_text(dump(library)+'\n')
    footprint()
    (ROOT/'research/prototype-power-migration.json').write_text(json.dumps(dict(
        revision='JLC-3',removed_refs=[r['diode'] for r in RAILS],parts=allparts,
        pin_source='https://www.ti.com/lit/ds/symlink/tps552892.pdf',
        land_source='TI RYQ0021B 4228792/A, land pattern and stencil; center pin 9 has 0.33 mm central width'),indent=2)+'\n')
    print('Replaced both supply schematics and wrote verified RYQ land-pattern source')


if __name__=='__main__':main()
