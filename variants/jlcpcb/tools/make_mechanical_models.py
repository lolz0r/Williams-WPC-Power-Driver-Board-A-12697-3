"""Generate explicitly simplified CAD envelopes for assembly review (OpenCascade).
Nominal dimensions from Rubycon USC and Boyd board-level heatsink catalogue.
Fin details and lead bends are illustrative; envelope dimensions and mounting axes are controlled.
"""
from pathlib import Path
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox,BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.gp import gp_Pnt,gp_Dir,gp_Ax2
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Compound
from OCP.STEPControl import STEPControl_Writer,STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone

out=Path('models');out.mkdir(exist_ok=True)
def box(x,y,z,w,d,h):return BRepPrimAPI_MakeBox(gp_Pnt(x,y,z),w,d,h).Shape()
def cyl(x,y,z,r,h,axis=(0,0,1)):return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z),gp_Dir(*axis)),r,h).Shape()
def write(name,shapes):
 builder=BRep_Builder();compound=TopoDS_Compound();builder.MakeCompound(compound)
 for s in shapes:builder.Add(compound,s)
 w=STEPControl_Writer();w.Transfer(compound,STEPControl_AsIs);assert w.Write(str(out/(name+'.step')))==IFSelect_RetDone
# 25 mm diameter, 35 mm nominal body, 10 mm pin pitch, 4 mm snap-in lead length.
write('Rubycon_USC_25x35_envelope',[cyl(5,0,0,12.5,35),cyl(0,0,-4,.6,4),cyl(10,0,-4,.6,4)])
# TDK B41252A7109M000 nominal envelope. Worst-case body 26.4 diameter, 47 high.
write('TDK_B41252_25p4x45_envelope',[cyl(5,0,0,12.7,45),cyl(0,0,-6,.7,6),cyl(10,0,-6,.7,6)])
# Nichicon LLS2A222MELA: 25 mm diameter x 40 mm, 10 mm pitch.
write('Nichicon_LLS_25x40_envelope',[cyl(5,0,0,12.5,40),cyl(0,0,-6.3,.7,6.3),cyl(10,0,-6.3,.7,6.3)])
# TO-220 tab back y=3.16; standard model hole at x=2.54,z=16.005.
# Boyd 7019: width39.37, depth9.52, height25.40, hole3.81 at14.48 above lower edge.
x=2.54;y=3.17;z=16.005-14.48
spine=box(x-5.97,y,z,11.94,1.02,25.4)
spine=BRepAlgoAPI_Cut(spine,cyl(x,y-.1,16.005,1.905,1.3,(0,1,0))).Shape();shapes=[spine]
for level in range(5):
 zz=z+level*5.08
 for side in (-1,1):
  lo=x-19.685 if side<0 else x+5.97
  shapes.append(box(lo,y,zz,13.715,1.02,3.18))
  outer=x-19.685 if side<0 else x+18.665
  shapes.append(box(outer,y,zz,1.02,9.52,3.18))
  folded=x-19.685 if side<0 else x+11.0
  shapes.append(box(folded,y+8.5,zz,8.685,1.02,3.18))
write('Boyd_7019_simplified',shapes)
# Boyd 577102B00000G channel: 13.21 wide, 19.05 high, 9.52 deep.
# Mounting hole is 13.33 above the bottom; direct tab contact at y=3.17.
x,y,z=2.54,3.17,16.005-13.33
spine=box(x-6.605,y,z,13.21,1.27,19.05)
spine=BRepAlgoAPI_Cut(spine,cyl(x,y-.1,16.005,1.905,1.5,(0,1,0))).Shape()
shapes=[spine]
for side in (-1,1):
 xx=x-6.605 if side<0 else x+5.335
 # Envelope preserved; fin slots simplified from the manufacturer's drawing.
 for k in range(5):shapes.append(box(xx,y+1.27-9.52,z+k*3.81,1.27,9.52,2.5))
write('Boyd_5771_simplified',shapes)
shapes=[spine]
for side in (-1,1):
 xx=x-6.605 if side<0 else x+5.335
 for k in range(5):shapes.append(box(xx,y+1.27-12.70,z+k*3.81,1.27,12.70,2.5))
write('Boyd_5772_simplified',shapes)
# GBPC model centre: x9,y-2.6. Basket envelope26.92sq31.75 tall, bolt4.14.
x,y,z=9,-2.6,7.42;base=box(x-13.46,y-13.46,z,26.92,26.92,1.27)
base=BRepAlgoAPI_Cut(base,cyl(x,y,z-.1,2.07,1.7)).Shape();shapes=[base]
for axis in (0,1):
 for side in (-1,1):
  for k in range(6):
   s=-13.46+k*4.6
   shapes.append(box(x+s,y+side*12.46,z+1.27,3.4,1.,30.48) if axis==0 else box(x+side*12.46,y+s,z+1.27,1.,3.4,30.48))
write('Boyd_6223_simplified',shapes)
print(out)

# Molex SDA-41791 pages 1-2: nominal envelopes and 18.29 mm pins, 3.56 mm tails.
# 3.96 mm pitch. The friction-lock wall is simplified; dimensions replace scaled KK254 CAD.
for n in (3,4,5,6,7,9,11,12,13):
 length=3.96*(n-1)+3.81
 shapes=[box(-1.905,-2.41,0,length,7.52,3.30),box(-1.905,3.20,3.30,length,1.91,8.03)]
 for pin in range(n):
  shapes.extend([box(pin*3.96-.57,-.57,-3.56,1.14,1.14,3.56),box(pin*3.96-.57,-.57,3.30,1.14,1.14,11.43)])
 write(f'Molex_KK396_{n:02d}_envelope',shapes)
# Bourns SRP1265A lead-frame: 12.5 square body, 13.5 overall including terminals; 6.2 high.
write('Bourns_SRP1265A_envelope',[box(-6.25,-6.25,.15,12.5,12.5,6.05),box(-6.75,-2.35,0,2.75,4.7,2),box(4,-2.35,0,2.75,4.7,2)])

# Boyd 7020BG: 33.02 W x 11.94 D x 36.83 H, two holes 7.87 apart.
# Lower hole 14.48 mm above lower edge; direct mount to insulated BTA16 tab.
x,y,z=2.54,3.17,16.005-14.48
spine=box(x-8.89,y,z,17.78,1.27,36.83)
for dz in (0,7.87):spine=BRepAlgoAPI_Cut(spine,cyl(x,y-.1,16.005+dz,1.905,1.5,(0,1,0))).Shape()
shapes=[spine]
for level in range(6):
 zz=z+level*6.10
 for side in (-1,1):
  lo=x-16.51 if side<0 else x+8.89
  shapes.append(box(lo,y,zz,7.62,1.27,3.18))
  outer=x-16.51 if side<0 else x+15.24
  shapes.append(box(outer,y,zz,1.27,11.94,3.18))
  folded=x-16.51 if side<0 else x+9.525
  shapes.append(box(folded,y+10.67,zz,6.985,1.27,3.18))
write('Boyd_7020_simplified',shapes)

# Assembly fastener envelopes. M3 pan head (5.84 dia x 2.29 high), shaft,
# conservatively circumscribed M3 nut (real nut is hexagonal); threads omitted.
for length in (8,12):
 shaft=cyl(2.54,1.86,16.005,1.5,length,(0,1,0))
 head=cyl(2.54,-.43,16.005,2.92,2.29,(0,1,0))
 nut=cyl(2.54,4.45,16.005,3.175,2.4,(0,1,0))
 nut=BRepAlgoAPI_Cut(nut,cyl(2.54,4.44,16.005,1.51,2.42,(0,1,0))).Shape()
 write(f'M3x{length}_TO220_hardware_envelope',[shaft,head,nut])
# M4x16 screw through BR3, basket and H9; nut beneath PCB.
x,y,z=9,-2.6,7.42+1.27
shaft=cyl(x,y,z-16,2,16);head=cyl(x,y,z,3.8,3.0)
nut=cyl(x,y,-4.8,4.04,3.2);nut=BRepAlgoAPI_Cut(nut,cyl(x,y,-4.81,2.01,3.22)).Shape()
write('M4x16_BR3_hardware_envelope',[shaft,head,nut])

# 3M TS-0770 revision U (2026), straight N2534-6002-RB, 34 contacts.
# Nominal body 50.50 x 8.59 x 9.91 mm; include 0.3 mm solder standoff.
body=box(-3.025,-45.57,.3,8.59,50.5,9.91)
body=BRepAlgoAPI_Cut(body,box(-1.905,-44.55,3.78,6.35,48.46,7)).Shape()
body=BRepAlgoAPI_Cut(body,box(-3.1,-22.415,3.78,1.3,4.19,7)).Shape()
shapes=[body]
for row in range(17):
 for x in (0,2.54):shapes.append(box(x-.32,-row*2.54-.32,-2.84,.64,.64,12.79))
write('3M_N2534_6002_RB_envelope',shapes)
