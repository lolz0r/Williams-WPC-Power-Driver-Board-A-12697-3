"""One-shot native CAD migration from the saved JLC-3 source.
Run with KiCad Python. Every pad retains its logical native net.
"""
import copy,json,math,shutil,uuid
from pathlib import Path
import pcbnew as pcb
from sexp import parse,dump,find,find_all,S,Sym
ROOT=Path(__file__).resolve().parents[1]
plan=json.loads((ROOT/'research/selection.json').read_text())
def rect(x1,y1,x2,y2,layer):return f'(fp_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.12) (type default)) (fill none) (layer "{layer}"))'
def custom(name,pads,body,attr='through_hole',descr=''):
 x1,y1,x2,y2=body
 s=f'(footprint "{name}" (version 20241229) (generator pcbnew) (layer "F.Cu") (descr "{descr}") (attr {attr})'
 s+='(property "Reference" "REF**" (at 0 -6 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))'
 s+=f'(property "Value" "{name}" (at 0 6 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))'
 s+=rect(x1,y1,x2,y2,'F.Fab')+rect(x1-.5,y1-.5,x2+.5,y2+.5,'F.CrtYd')+''.join(pads)+')\n'
 (ROOT/'footprints/wpc_cost.pretty'/(name+'.kicad_mod')).write_text(s)
custom('HONGJU_FH1_200CK_G',[f'(pad "{n}" thru_hole {"rect" if n==1 else "circle"} (at {x} 0) (size 2.7 2.7) (drill 1.7) (layers "*.Cu" "*.Mask"))' for n,x in [(1,0),(2,22.6)]],(-1.1,-4.9,23.7,4.9),descr='HONGJU FH1-200CK-G complete 5x20 holder and cover, P22.6 D1.7, 10A250V')
# TLC TA series recommended land: 2x 2.5 mm width with 4.0 mm interior gap.
custom('TLC_TA_2410_Fuse',[f'(pad "{n}" smd rect (at {x} 0) (size 2.5 3.0) (layers "F.Cu" "F.Paste" "F.Mask"))' for n,x in [(1,-3.25),(2,3.25)]],(-3.1,-1.3,3.1,1.3),'smd','TLC TA time-lag 2410 ceramic fuse; soldered service replacement')
# Same 34 signal pads. XFCN drawing specifies D1.0 finished holes.
f=parse((ROOT/'footprints/wpc_cost.pretty/3M_N2534_6002_RB.kicad_mod').read_text())[0];f[1]='XFCN_EH254V_12_34P'
for pad in find_all(f,'pad'):find(pad,'drill')[1]=1.0
# Keep the conservative pre-existing latch courtyard; native positions are audited.
for q in find_all(f,'property'):
 if q[1] in ['Description','MPN','Manufacturer','Link','JLCPCB Part','JLCPCB Library']:q[2]=''
f[:]=[x for x in f if not(isinstance(x,list) and x[0]=='model')]
(ROOT/'footprints/wpc_cost.pretty/XFCN_EH254V_12_34P.kicad_mod').write_text(dump(f)+'\n')
def field(node,name,value):
 prop=next((x for x in find_all(node,'property') if x[1]==name),None)
 if prop is None:
  prop=copy.deepcopy(next(x for x in find_all(node,'property') if x[1]=='MPN'));prop[1]=name;node.append(prop)
 prop[2]=str(value)
def metadata(item):
 d=json.loads((ROOT/'research/jlcpcb/catalog'/(item['code']+'.json')).read_text())
 props={'MPN':d['componentModelEn'],'Manufacturer':d['componentBrandEn'],'JLCPCB Part':item['code'],'JLCPCB Library':{'base':'Basic','expand':'Extended'}[d['componentLibraryType']],'Link':d['url'],'Description':item['reason'],'Price':'','Price100':''}
 for src,dst in [('value','Value'),('footprint','Footprint')]:
  if src in item:props[dst]=item[src]
 if item.get('quantity',1)!=1:props['Purchased Quantity']=str(item['quantity'])
 if 'trim_to' in item:props['Assembly Modification']=f"Trim from pin-1 end to {item['trim_to']} positions; preserve key schedule."
 if item.get('footprint')=='wpc_cost:HONGJU_FH1_200CK_G' and item['code']!='C268204':props['Holder JLCPCB Part']='C268204'
 return props
for path in ROOT.glob('*.kicad_sch'):
 sch=parse(path.read_text())[0]
 for sym in find_all(sch,'symbol'):
  props={q[1]:q[2] for q in find_all(sym,'property')};ref=props.get('Reference')
  if ref in plan:
   for k,v in metadata(plan[ref]).items():field(sym,k,v)
 text=dump(sch).replace('JLC-3','JLC-100');path.write_text(text+'\n')
b=pcb.LoadBoard(str(ROOT/'wpc_power_driver_cost.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
def vec(x,y):return pcb.VECTOR2I(round(x*1e6),round(y*1e6))
def track(a,z,net,width=.5):
 if (a-z).EuclideanNorm()<1000:return
 t=pcb.PCB_TRACK(b);t.SetStart(a);t.SetEnd(z);t.SetWidth(round(width*1e6));t.SetLayer(pcb.F_Cu);t.SetNetCode(net);b.Add(t)
def via(v,net):
 p=pcb.PCB_VIA(b);p.SetPosition(v);p.SetWidth(1400000);p.SetDrill(700000);p.SetViaType(pcb.VIATYPE_THROUGH);p.SetLayerPair(pcb.F_Cu,pcb.B_Cu);p.SetNetCode(net);b.Add(p)
changes=[]
for ref,item in plan.items():
 old=fps[ref];props=metadata(item)
 if 'footprint' in item:
  fp=item['footprint'];lib,name=fp.split(':');new=pcb.FootprintLoad(str(ROOT/'footprints'/(lib+'.pretty')),name)
  new.SetFPIDAsString(fp);new.SetReference(ref);new.SetValue(old.GetValue());new.SetPath(old.GetPath());new.SetOrientation(old.GetOrientation());pos=old.GetPosition();angle=math.radians(old.GetOrientationDegrees())
  offset=.255 if ref.startswith('F') and ref!='F112' else 11.555 if ref=='F112' else .75 if ref in ['C2','C4','C9','C12'] else 0
  new.SetPosition(pos+vec(offset*math.cos(angle),-offset*math.sin(angle)))
  for f in old.GetFields():
   if f.GetName() not in ['Reference','Value']:new.SetField(f.GetName(),f.GetText())
  oldpads={}
  for p in old.Pads():
   if p.GetNumber():oldpads.setdefault(p.GetNumber(),[]).append(p)
  b.Add(new)
  for p in new.Pads():
   if not p.GetNumber():continue
   op=min(oldpads[p.GetNumber()],key=lambda q:(q.GetPosition()-p.GetPosition()).EuclideanNorm());p.SetNetCode(op.GetNetCode())
   if ref=='F112':via(op.GetPosition(),op.GetNetCode());track(op.GetPosition(),p.GetPosition(),op.GetNetCode(),1.5)
   else:track(op.GetPosition(),p.GetPosition(),op.GetNetCode(),.4 if ref.startswith('U') else 1.)
  new.Reference().SetVisible(old.Reference().IsVisible());new.Reference().SetPosition(old.Reference().GetPosition());new.Reference().SetTextSize(old.Reference().GetTextSize());new.Reference().SetTextThickness(old.Reference().GetTextThickness());new.Reference().SetTextAngle(old.Reference().GetTextAngle())
  b.Remove(old);fps[ref]=new
 fp=fps[ref]
 for k,v in props.items():
  if k=='Value':fp.SetValue(v)
  elif k!='Footprint':fp.SetField(k,v)
 for f in fp.GetFields():
  if f.GetName() not in ['Reference','Value']:f.SetVisible(False)
 # TE .045 square posts need recommended 1.78 mm holes; 1.8 allows tolerance.
 if ref.startswith('J') and item['code'] in ['C86500','C305801','C305802','C592598']:
  for p in fp.Pads():p.SetDrillSize(vec(1.8,1.8))
 changes.append({'reference':ref,**item})
for drawing in b.GetDrawings():
 if isinstance(drawing,pcb.PCB_TEXT):drawing.SetText(drawing.GetText().replace('JLC-3','JLC-100'))
pcb.SaveBoard(str(ROOT/'wpc_power_driver_cost.kicad_pcb'),b)
(ROOT/'research/applied-migration.json').write_text(json.dumps(changes,indent=2)+'\n')
print('Applied',len(changes),'native reference substitutions')
