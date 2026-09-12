"""Apply reviewed JLC part substitutions and replace the two SIP pull-up arrays.

Run once with KiCad's Python. Inputs are the isolated variant and the saved
catalog selection, never the original PCBWay board.
"""
import copy, json, uuid
from pathlib import Path
import pcbnew
from sexp import parse, dump, find, find_all, S, Sym

ROOT=Path(__file__).resolve().parents[1]
parts=json.loads((ROOT/'parts-selection-draft.json').read_text())
selected={ref:r for r in parts if r['JLCPCB_part'] and r['Footprint']!='Mechanical'
          for ref in r['Refs'].split()}
index=json.loads((ROOT/'research/catalog-index.json').read_text())
pcb=ROOT/'wpc_power_driver_cost.kicad_pcb'
b=pcbnew.LoadBoard(str(pcb))
fps={f.GetReference():f for f in b.GetFootprints()}
assert 'SR1' in fps, 'This migration has already run'
def uid():return str(uuid.uuid4())
def field(node,name,value):
    p=next((p for p in find_all(node,'property') if p[1]==name),None)
    if p is None:
        template=next(p for p in find_all(node,'property') if p[1]=='MPN')
        p=copy.deepcopy(template);p[1]=name;node.append(p)
    p[2]=str(value)
def bfield(fp,name,value):
    f=fp.GetField(name)
    if f:f.SetText(str(value))
    else:
        f=pcbnew.PCB_FIELD(fp,pcbnew.FIELD_T_USER,name);f.SetText(str(value));f.SetVisible(False);fp.Add(f)
def metadata(r):
    return {'MPN':r['Selected_MPN'],'Manufacturer':r['Selected_manufacturer'],
            'Link':r['JLCPCB_URL'],'JLCPCB Part':r['JLCPCB_part'],'JLCPCB Library':r['Library']}

pullups=[]
for name in ('SR1','SR2'):
    fp=fps[name]
    for p in sorted(fp.Pads(),key=lambda p:int(p.GetNumber())):
        n=int(p.GetNumber())
        if 2<=n<=9:
            pullups.append(dict(ref=f'R{310+len(pullups)}',array=name,pin=n,net=p.GetNetname(),
                x=p.GetPosition().x/1e6,y=p.GetPosition().y/1e6))

for path in ROOT.glob('*.kicad_sch'):
    sch=parse(path.read_text())[0]
    symbols=find_all(sch,'symbol')
    for sym in symbols:
        props={p[1]:p[2] for p in find_all(sym,'property')}
        ref=props.get('Reference')
        if ref in selected:
            for k,v in metadata(selected[ref]).items():field(sym,k,v)
    if path.name=='cpu_interface.kicad_sch':
        template=next(s for s in symbols if any(p[1:3]==['Reference','R3'] for p in find_all(s,'property')))
        original_array={next(p[2] for p in find_all(s,'property') if p[1]=='Reference'):s
                        for s in symbols if any(p[1]=='Reference' and p[2] in ['SR1','SR2'] for p in find_all(s,'property'))}
        sch[:]=[n for n in sch if n not in original_array.values()]
        for name,arr in original_array.items():
            ax,ay=map(float,find(arr,'at')[1:3]);nc=(round(ax+10.16,6),round(ay+5.08,6))
            sch[:]=[n for n in sch if not(isinstance(n,list) and n[0]=='no_connect' and
                tuple(round(float(v),6) for v in find(n,'at')[1:3])==nc)]
            for item in [r for r in pullups if r['array']==name]:
                x=round(ax-10.16+(item['pin']-2)*2.54,6);y=ay+1.27
                sym=copy.deepcopy(template);old_at=find(sym,'at');dx=x-float(old_at[1]);dy=y-float(old_at[2]);old_at[1:]=[x,y,0]
                find(sym,'uuid')[1]=uid()
                for p in find_all(sym,'property'):
                    at=find(p,'at');at[1]=float(at[1])+dx;at[2]=float(at[2])+dy
                field(sym,'Reference',item['ref']);field(sym,'Value','4.7K')
                field(sym,'MPN','0805W8F4701T5E');field(sym,'Manufacturer','UNI-ROYAL(Uniroyal Elec)')
                field(sym,'JLCPCB Part','C17673');field(sym,'JLCPCB Library','Basic')
                field(sym,'Link','https://jlcpcb.com/partdetail/UNIROYAL-UniroyalElec-0805W8F4701T5E/C17673')
                field(sym,'Description','4.7 kohm 1% 125 mW 0805 discrete CPU-interface pull-up')
                for p in find_all(sym,'pin'):find(p,'uuid')[1]=uid()
                def refs(n):
                    for c in n:
                        if isinstance(c,list):
                            if c[0]=='reference':c[1]=item['ref']
                            else:refs(c)
                refs(find(sym,'instances'))
                # Keep the dense pull-up block legible: value once in a note,
                # references vertical between adjacent 2.54 mm branches.
                for p in find_all(sym,'property'):
                    if p[1]=='Value':
                        effects=find(p,'effects');effects.append(S('hide',Sym('yes')))
                    if p[1]=='Reference':find(p,'at')[1:]=[x+.65,y,90]
                sch.append(sym);item['uuid']=find(sym,'uuid')[1]
                def wire(x1,y1,x2,y2):sch.append(S('wire',S('pts',S('xy',x1,y1),S('xy',x2,y2)),S('stroke',S('width',0),S('type',Sym('default'))),S('uuid',uid())))
                wire(x,y-3.81,x,ay-5.08)
                if item['pin']>2:
                    wire(x-2.54,ay-5.08,x,ay-5.08)
                    if item['pin']<9:sch.append(S('junction',S('at',x,ay-5.08),S('diameter',0),S('color',0,0,0,0),S('uuid',uid())))
            sch.append(S('text',f'{name} replaced by eight 4.7k / 1% Basic resistors; unused ninth element omitted',S('at',ax-10.16,ay-10.16,0),S('effects',S('font',S('size',.9,.9)),S('justify',Sym('left'))),S('uuid',uid())))
    path.write_text(dump(sch)+'\n')

for ref,r in selected.items():
    if ref in fps:
        for k,v in metadata(r).items():bfield(fps[ref],k,v)

def vec(x,y):return pcbnew.VECTOR2I(round(x*1e6),round(y*1e6))
def track(a,z,net,layer=pcbnew.F_Cu,w=.4):
    t=pcbnew.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetWidth(round(w*1e6));t.SetLayer(layer);t.SetNetCode(net);b.Add(t)
def via(x,y,net):
    v=pcbnew.PCB_VIA(b);v.SetPosition(vec(x,y));v.SetWidth(800000);v.SetDrill(400000);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNetCode(net);b.Add(v)
template_fp=fps['R3']
for name in ('SR1','SR2'):
    old=fps[name];common=next(p for p in old.Pads() if p.GetNumber()=='1');cx,cy=common.GetPosition().x/1e6,common.GetPosition().y/1e6;net=common.GetNetCode();via(cx,cy,net)
    busx=cx+3.4
    track((cx,cy),(busx,cy),net)
    items=[p for p in pullups if p['array']==name]
    track((busx,cy),(busx,min(p['y'] for p in items)),net)
    for item in items:
        fp=pcbnew.Cast_to_FOOTPRINT(template_fp.Duplicate(False));fp.SetParent(b);fp.SetReference(item['ref']);fp.SetValue('4.7K')
        path=pcbnew.KIID_PATH(old.GetPath());path.pop_back();path.push_back(pcbnew.KIID(item['uuid']));fp.SetPath(path)
        fp.SetOrientationDegrees(180);fp.SetPosition(vec(item['x']+2.2,item['y']))
        for p in fp.Pads():p.SetNetCode(net if p.GetNumber()=='1' else b.GetNetcodeFromNetname(item['net']))
        # At 180 degrees R0805 pad 1 is on the right, pad 2 on the left.
        r=dict(Selected_MPN='0805W8F4701T5E',Selected_manufacturer='UNI-ROYAL(Uniroyal Elec)',JLCPCB_part='C17673',Library='Basic',JLCPCB_URL='https://jlcpcb.com/partdetail/UNIROYAL-UniroyalElec-0805W8F4701T5E/C17673')
        for k,v in metadata(r).items():bfield(fp,k,v)
        fp.Reference().SetVisible(True);fp.Reference().SetTextSize(vec(.65,.65));fp.Reference().SetPosition(vec(item['x']+2.2,item['y']-1.0))
        b.Add(fp)
        for p in fp.Pads():
            x,y=p.GetPosition().x/1e6,p.GetPosition().y/1e6
            if p.GetNumber()=='1':track((x,y),(busx,y),net)
            else:
                pn=p.GetNetCode();via(item['x'],item['y'],pn);track((item['x'],item['y']),(x,y),pn)
    b.Remove(old)
pcbnew.SaveBoard(str(pcb),b)
(ROOT/'pullup-migration.json').write_text(json.dumps(pullups,indent=2)+'\n')
print('Updated component fields and replaced SR1/SR2 with 16 Basic pull-up resistors')
