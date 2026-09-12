"""Historical one-shot BR1 routing migration; use only a pre-upgrade checkout.
Normal verification/export never invokes this script. Output is .scratch/rectifier-trial.
"""
import sys,copy,math,shutil,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pcbnew
from sexp import parse,dump,find,find_all,S
root=Path.cwd();native=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Package_TO_SOT_THT.pretty/TO-220-3_Vertical.kicad_mod')
f=parse(native.read_text())[0];f[1]='TO220_Schottky_AKA_5772'
for p in find_all(f,'pad'):p[1]='1' if p[1]=='2' else '2'
# Assembly courtyard includes the channel heatsink; its model is added after fit check.
for rect in find_all(f,'fp_rect'):
 if find(rect,'layer')[1]=='F.CrtYd':
  find(rect,'start')[1:]=[-4.565,-4.95];find(rect,'end')[1:]=[9.645,8.76]
fpfile=root/'footprints/wpc_cost.pretty/TO220_Schottky_AKA_5772.kicad_mod';fpfile.write_text(dump(f)+'\n')
b=pcbnew.LoadBoard('wpc_power_driver_cost.kicad_pcb');data=[]
for old in b.GetFootprints():
 ref=old.GetReference()
 if ref not in ['D101','D102','D103','D104']:continue
 assert 'D2PAK' in old.GetFPIDAsString(), 'Already upgraded; use a pre-upgrade source board'
 anodes=[p for p in old.Pads() if p.GetNumber()=='2'];k=next(p for p in old.Pads() if p.GetNumber()=='1')
 a=old.GetOrientationDegrees();x,y=old.GetPosition().x/1e6,old.GetPosition().y/1e6
 if ref=='D102':x+=12.6
 shift={'D101':0,'D102':24,'D103':-15,'D104':-30}[ref]
 # Original local (-7.65,-2.54) is physical lead 1.
 r=math.radians(a);ox=x-7.65*math.cos(r)-2.54*math.sin(r);oy=y+7.65*math.sin(r)-2.54*math.cos(r)+shift
 data.append(dict(ref=ref,old=old,fields={ff.GetName():ff.GetText() for ff in old.GetFields()},path=old.GetPath(),x=ox,y=oy,a=a-90,k=k.GetNetname(),anode=anodes[0].GetNetname(),oldk=(k.GetPosition().x/1e6,k.GetPosition().y/1e6),olda=[(p.GetPosition().x/1e6,p.GetPosition().y/1e6) for p in anodes],shift=shift))
for d in data:
 new=pcbnew.FootprintLoad(str(fpfile.parent),fpfile.stem)
 new.SetFPIDAsString('wpc_cost:'+fpfile.stem);new.SetReference(d['ref']);new.SetValue('STPS20M100ST');new.SetPath(d['path'])
 for name,value in d['fields'].items():
  if name not in ('Reference','Value'):new.SetField(name,value)
 new.SetField('MPN','STPS20M100ST');new.SetField('Manufacturer','STMicroelectronics')
 for field in new.GetFields():
  if field.GetName() not in ('Reference','Value'):field.SetVisible(False)
 model=pcbnew.FP_3DMODEL();model.m_Filename=str(root/'models/Boyd_5772_simplified.step');new.Models().push_back(model)
 new.SetOrientationDegrees(d['a']);new.SetPosition(pcbnew.VECTOR2I(round(d['x']*1e6),round(d['y']*1e6)))
 b.Add(new)
 for p in new.Pads():p.SetNet(b.GetNetInfo().GetNetItem(d['k'] if p.GetNumber()=='1' else d['anode']))
 # Cathode pin to previous tab/pour; original thermal stitches remain.
 k=next(p for p in new.Pads() if p.GetNumber()=='1')
 def track(start,end,net,layer,width=1.0):
  t=pcbnew.PCB_TRACK(b);t.SetStart(pcbnew.VECTOR2I(round(start[0]*1e6),round(start[1]*1e6)));t.SetEnd(pcbnew.VECTOR2I(round(end[0]*1e6),round(end[1]*1e6)));t.SetWidth(round(width*1e6));t.SetLayer(layer);t.SetNet(b.GetNetInfo().GetNetItem(net));b.Add(t)
 if d['ref']=='D101':track((k.GetPosition().x/1e6,k.GetPosition().y/1e6),d['oldk'],d['k'],pcbnew.F_Cu)
 if d['ref']=='D102':
  for p in new.Pads():
   if p.GetNumber()=='2':
    dst=(p.GetPosition().x/1e6,p.GetPosition().y/1e6);outer=367 if dst[0]<376 else 380.8
    elbow=(outer,74.89);top=(outer,45)
    track(dst,elbow,d['anode'],pcbnew.F_Cu,1.5);track(elbow,top,d['anode'],pcbnew.F_Cu,1.5)
    if outer==380.8:track(top,(375,45),d['anode'],pcbnew.F_Cu,1.5)
 if d['ref']=='D101':
  track((347.46,53.35),(347.46,50.5),d['anode'],pcbnew.F_Cu)
  track((347.46,50.5),(352.54,50.5),d['anode'],pcbnew.F_Cu)
  track((352.54,50.5),(352.54,53.35),d['anode'],pcbnew.F_Cu)
  track((352.54,53.35),(354,54.2),d['anode'],pcbnew.F_Cu)
# Move one obstructing AC16_A trunk to a 3 mm inner route with native through vias.
track((371,61.4),(383,61.4),'AC16_A',pcbnew.In1_Cu,3)
track((383,61.4),(381.5,62.9),'AC16_A',pcbnew.In1_Cu,3)
track((381.5,62.9),(381.5,97.6),'AC16_A',pcbnew.In1_Cu,3)
track((381.5,97.6),(374.6,97.6),'AC16_A',pcbnew.In1_Cu,3)
track((374.6,97.6),(374.6,99.6),'AC16_A',pcbnew.F_Cu,3)
v=pcbnew.PCB_VIA(b);v.SetPosition(pcbnew.VECTOR2I(374600000,97600000));v.SetWidth(1800000);v.SetDrill(1000000);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(b.GetNetInfo().GetNetItem('AC16_A'));b.Add(v)
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in {'953bf823-3f92-4631-951e-c270cc884de0','1d065ab3-98a8-4db2-bbc8-78c62a916fea'}:b.Remove(t);continue
 if t.m_Uuid.AsString()=='51a65e06-b9e4-4662-b656-4d12cf506e14':b.Remove(t);continue
 if t.GetClass()!='PCB_TRACK' or t.GetNetname()!='/Power_Supply/AC13_A_F':continue
 # Remove old fanout joining the two anodes across the new cathode pin.
 if t.m_Uuid.AsString() in {'cfb068df-1d6f-43bc-8874-74255d60def4','9209522f-ae66-4512-8fb9-39d0642ae3f3','2caa36d9-c281-408d-bbb7-f514c0be3f5b','1dfedd29-6827-4453-8640-0de2f8943da1','107b9ebc-093e-4bcd-865d-ddc238f843b0'}:b.Remove(t)
for d in data:b.Remove(d['old'])
out=root/'.scratch/rectifier-trial';out.mkdir(exist_ok=True)
pcbnew.SaveBoard(str(out/'board.kicad_pcb'),b);shutil.copy2('wpc_power_driver_cost.kicad_pro',out/'board.kicad_pro')
(out/'fp-lib-table').write_text((root/'fp-lib-table').read_text().replace('${KIPRJMOD}',str(root)))
print(out)
