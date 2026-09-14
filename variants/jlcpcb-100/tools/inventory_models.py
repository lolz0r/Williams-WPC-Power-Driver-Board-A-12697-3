"""Generate dimensioned assembly envelopes for selected parts, including hardware.
Simplified envelopes are not supplier solid models; pin polarity is controlled by CAD pads.
"""
from pathlib import Path
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Pnt,gp_Dir,gp_Ax2,gp_Trsf,gp_Vec
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Compound
from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs,STEPControl_Reader
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'models/inventory';OUT.mkdir(parents=True,exist_ok=True)
class Shape:
 def __init__(self,s):self.s=s
 def cut(self,b):return Shape(BRepAlgoAPI_Cut(self.s,b.s).Shape())
 def translate(self,xyz):
  t=gp_Trsf();t.SetTranslation(gp_Vec(*xyz));return Shape(BRepBuilderAPI_Transform(self.s,t,True).Shape())
def box(x,y,z,w,d,h):return Shape(BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),w,d,h).Shape())
def cyl(x,y,z,r,h,axis=(0,0,1)):return Shape(BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*axis)),r,h).Shape())
def write(name,shapes):
 b=BRep_Builder();c=TopoDS_Compound();b.MakeCompound(c)
 for s in shapes:b.Add(c,s.s)
 w=STEPControl_Writer();w.Transfer(c,STEPControl_AsIs);w.Write(str(OUT/(name+'.step')))
def read(p):
 r=STEPControl_Reader();r.ReadFile(str(p));r.TransferRoots();return Shape(r.OneShape())
for name,d,h,p in [('GPD_4700u_35V',18,31.5,7.5),('NHA_1000u_100V',18.5,42,7.5),('Rubycon_ZLH_330u_25V',8,11.5,3.5),('KNSCHA_2200u_100V',25,40,10)]:write(name,[cyl(p/2,0,0,d/2,h),cyl(0,0,-4,.4,4),cyl(p,0,-4,.4,4)])
write('TLC_TA7',[box(-3.05,-1.25,0,6.1,2.5,2.5)])
# Holder origin: PCB lead 1 at 0; lead 2 at 22.6.
write('HONGJU_FH1_200CK_G',[box(-1.1,-4.9,0,24.8,9.8,12.15).cut(cyl(1.0,0,6,2.65,20.6,(1,0,0))),box(-.35,-.25,-4.45,.7,.5,4.45),box(22.25,-.25,-4.45,.7,.5,4.45)])
write('Fuse_5x20_cartridge',[cyl(1.3,0,6,2.5,20,(1,0,0))])
# Full J115 composite body and each trimmed/keyed header modeled separately below.
import sys
sys.path.insert(0,str(ROOT/'tools'))
from sexp import parse,find,find_all
b=parse((ROOT/'wpc_power_driver_cost.kicad_pcb').read_text())[0]
for f in find_all(b,'footprint'):
 props={p[1]:p[2] for p in find_all(f,'property')};ref=props['Reference'];code=props.get('JLCPCB Part')
 if code not in ['C86500','C305801','C305802','C592598','C94118']:continue
 pads=find_all(f,'pad');n=len(pads);small=code=='C94118';pitch=2.54 if small else 3.96;width=5.08 if small else 7.62;baseh=2.54 if small else 3.175;wallh=6.0 if small else 10.795;post=.64 if small else 1.14;tail=3.18;posth=8.13 if small else 10.16
 length=n*pitch;parts=[]
 runs=[(0,6),(6,6)] if ref=='J115' else [(0,n)]
 for first,count in runs:
  x=first*pitch-pitch/2;parts.extend([box(x,-2.54 if not small else -1.9,0,count*pitch,width,baseh),box(x,4.13 if not small else 2.18,baseh,count*pitch,.95,wallh)])
 for pad in pads:
  if str(pad[1]) == str(__import__('connector_keys').KEYS[int(ref[1:])]):continue # remove only explicit OEM key
  x=float(find(pad,'at')[1]);parts.extend([box(x-post/2,-post/2,-tail,post,post,tail),box(x-post/2,-post/2,baseh,post,post,posth)])
 write('TE_'+ref,parts)
# XFCN 34-pin long-ejector body, maximum closed latch envelope.
parts=[box(-2.88,-51.51,.3,8.3,62.38,16.6)]
for row in range(17):
 for x in [0,2.54]:parts.append(box(x-.32,-row*2.54-.32,-3,.64,.64,3))
write('XFCN_EH254V_12_34P_envelope',parts)
# GBPC-W formed to an 18x18 square. 0.12 standoff, max 11.23 body.
body=box(-5.5,-17.1,.12,29,29,11.23);body=body.cut(cyl(9,-2.6,0,2.795,12));parts=[body]
for x,y in [(0,6.4),(18,-11.6),(0,-11.6),(18,6.4)]:parts.append(cyl(x,y,-4,.535,4.12))
write('ONSEMI_GBPC2506W_formed',parts)
# Same Boyd basket, translated to the new bridge metal-base height (+3.81 mm).
old=read(ROOT/'models/Boyd_6223_simplified.step');write('Boyd_6223_on_GBPC2506W',[old.translate((0,0,3.93))])
# M4x20 (rather than old M4x16) accommodates the thicker rectifier case.
z=11.23+.12+1.27;shaft=cyl(9,-2.6,z-20,2,20);head=cyl(9,-2.6,z,3.375,2.6);nut=cyl(9,-2.6,-4.8,4.04,3.2).cut(cyl(9,-2.6,-4.81,2.01,3.22));write('M4x20_BR3_hardware',[shaft,head,nut])
print('Inventory envelopes generated')
# TI NS20: 5.3x12.6 mm body, 1.27 mm pitch, 2.0 mm maximum height.
parts=[box(-2.65,-6.3,.2,5.3,12.6,1.8)]
for side in [-1,1]:
 for pin in range(10):parts.append(box(-4.1 if side<0 else 2.65,-5.715+pin*1.27-.2,0,1.45,.4,.25))
write('TI_NS20',parts)

# Keep connector dimensions, friction walls and explicit key schedule authoritative.
from connector_models import generate
generate()
