"""Replace five reservoirs by ten individually annotated high-ripple capacitors."""
import copy,json,math,uuid
from pathlib import Path
import pcbnew as pcb
from sexp import parse,dump,find,find_all,S,Sym
ROOT=Path(__file__).resolve().parents[1]
b=pcb.LoadBoard(str(ROOT/'wpc_power_driver_cost.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
assert 'C59' not in fps,'One-shot migration already applied'
code='C443892';cat=json.loads((ROOT/'research/jlcpcb/catalog'/(code+'.json')).read_text());name='CP_Radial_D18.0mm_P7.50mm';fpname='Capacitor_THT:'+name
props={'Value':'4700uF 35V','MPN':cat['componentModelEn'],'Manufacturer':cat['componentBrandEn'],'JLCPCB Part':code,'JLCPCB Library':'Extended','Link':cat['url'],'Footprint':fpname,'Description':'GPD 4700uF 35V D18x30mm; 4.76A at120Hz/125C. Paired reservoir; each part separately annotated.','Price':'','Price100':''}
mapping=dict(zip(['C5','C6','C7','C11','C30'],['C59','C60','C61','C62','C63']));uuids={r:str(uuid.uuid4()) for r in mapping.values()};nets={r:{p.GetNumber():p.GetNetname() for p in fps[r].Pads()} for r in mapping}
def field(sym,k,v):
 q=next((p for p in find_all(sym,'property') if p[1]==k),None)
 if q is None:q=copy.deepcopy(next(p for p in find_all(sym,'property') if p[1]=='MPN'));q[1]=k;sym.append(q)
 q[2]=str(v)
schpath=ROOT/'power_supply.kicad_sch';sch=parse(schpath.read_text())[0]
for idx,(oldref,newref) in enumerate(mapping.items()):
 orig=next(s for s in find_all(sch,'symbol') if any(p[1:3]==['Reference',oldref] for p in find_all(s,'property')))
 for k,v in props.items():field(orig,k,v)
 sym=copy.deepcopy(orig);ax,ay=map(float,find(sym,'at')[1:3]);x,y=300.99+idx*27.94,375.92;find(sym,'at')[1:]=[x,y,0];find(sym,'uuid')[1]=uuids[newref]
 for p in find_all(sym,'property'):
  a=find(p,'at');a[1]=float(a[1])+x-ax;a[2]=float(a[2])+y-ay
 field(sym,'Reference',newref)
 for pin in find_all(sym,'pin'):find(pin,'uuid')[1]=str(uuid.uuid4())
 def reflabel(n):
  for q in n:
   if isinstance(q,list):
    if q[0]=='reference':q[1]=newref
    else:reflabel(q)
 reflabel(find(sym,'instances'));sch.append(sym)
 for pin,dy in [('1',-3.81),('2',3.81)]:
  net=nets[oldref][pin];local=net.startswith('/Power_Supply/');label=net.removeprefix('/Power_Supply/')
  node=S('label' if local else 'global_label',label,S('at',x,y+dy,0),S('effects',S('font',S('size',.8,.8)),S('justify',Sym('left'),Sym('bottom'))),S('uuid',str(uuid.uuid4())))
  if not local:node.insert(2,S('shape',Sym('input')))
  sch.append(node)
 sch.append(S('text',f'{newref} parallels {oldref}: total 9400uF',S('at',x,y+10.16,0),S('effects',S('font',S('size',.9,.9)),S('justify',Sym('left'))),S('uuid',str(uuid.uuid4()))))
schpath.write_text(dump(sch)+'\n')
def vec(x,y):return pcb.VECTOR2I(round(x*1e6),round(y*1e6))
def xy(p):return p.x/1e6,p.y/1e6
def tr(a,z,net):
 if math.dist(a,z)<.001:return
 t=pcb.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*z));t.SetWidth(2000000);t.SetLayer(pcb.F_Cu);t.SetNetCode(net);b.Add(t)
def via(p):
 v=pcb.PCB_VIA(b);v.SetPosition(p.GetPosition());v.SetWidth(4000000);v.SetDrill(2000000);v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNetCode(p.GetNetCode());b.Add(v)
plan=json.loads((ROOT/'research/selection.json').read_text());record=[]
for oldref,newref in mapping.items():
 old=fps[oldref];pads={p.GetNumber():p for p in old.Pads()};a=xy(pads['1'].GetPosition());z=xy(pads['2'].GetPosition());cx,cy=(a[0]+z[0])/2,(a[1]+z[1])/2
 horizontal=oldref=='C11';centers=[(cx-10,cy),(cx+10,cy)] if horizontal else [(cx,cy-10),(cx,cy+10)]
 for p in pads.values():via(p)
 newpads={'1':[],'2':[]}
 for ref,(x,y) in zip([oldref,newref],centers):
  f=pcb.FootprintLoad(str(ROOT/'footprints/Capacitor_THT.pretty'),name);f.SetFPIDAsString(fpname);f.SetReference(ref);f.SetValue(props['Value']);f.SetOrientationDegrees(-90 if horizontal else 0);f.SetPosition(vec(x,y-3.75) if horizontal else vec(x-3.75,y));path=pcb.KIID_PATH(old.GetPath())
  if ref==newref:path.pop_back();path.push_back(pcb.KIID(uuids[ref]))
  f.SetPath(path)
  for k,v in props.items():
   if k not in ['Footprint','Value']:f.SetField(k,v)
  for q in f.GetFields():
   if q.GetName() not in ['Reference','Value']:q.SetVisible(False)
  f.Reference().SetTextSize(vec(.8,.8));f.Reference().SetTextThickness(120000);f.Reference().SetPosition(vec(x,y-10.5))
  b.Add(f)
  for p in f.Pads():p.SetNetCode(pads[p.GetNumber()].GetNetCode());newpads[p.GetNumber()].append(xy(p.GetPosition()))
  plan[ref]=dict(code=code,value=props['Value'],footprint=fpname,reason=props['Description'])
 for pin,side in [('1',-1),('2',1)]:
  anchor=xy(pads[pin].GetPosition());nc=pads[pin].GetNetCode();points=newpads[pin]
  if horizontal:
   bus=cy+side*7;tr(anchor,(anchor[0],bus),nc);tr((cx-10,bus),(cx+10,bus),nc)
   for pt in points:tr((pt[0],bus),pt,nc)
  else:
   bus=cx+side*7;tr(anchor,(bus,anchor[1]),nc);tr((bus,cy-10),(bus,cy+10),nc)
   for pt in points:tr((bus,pt[1]),pt,nc)
 record.append(dict(original=oldref,added=newref,net=nets[oldref],centers=centers));b.Remove(old)
pcb.SaveBoard(str(ROOT/'wpc_power_driver_cost.kicad_pcb'),b)
(ROOT/'research/selection.json').write_text(json.dumps(plan,indent=2)+'\n');(ROOT/'research/capacitor-migration.json').write_text(json.dumps(record,indent=2)+'\n')
print('Installed 10 individually annotated 4700uF35V GPD capacitors')
