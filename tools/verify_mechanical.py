"""Independent OpenCascade STEP model bounds and solid-intersection review.
Nominal CAD only: does not certify harness access, tolerances or cabinet fit.
"""
import json
import hashlib
import math
import argparse
from pathlib import Path
from OCP.BRep import BRep_Builder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform,BRepBuilderAPI_GTransform
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Trsf,gp_Ax1,gp_Pnt,gp_Dir,gp_Vec,gp_GTrsf,gp_Mat,gp_XYZ
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/revision'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path,default=OUT);args=parser.parse_args();OUT=args.directory
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')
parts=json.loads((OUT/'mechanical-inputs.json').read_text());cache={};items=[];missing=[]
def bounds(shape):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(shape,b,False,False);return b.Get()
def transform(shape,tr):return BRepBuilderAPI_Transform(shape,tr,True).Shape()
def rotate(shape,axis,angle):
 if not angle:return shape
 t=gp_Trsf();t.SetRotation(gp_Ax1(gp_Pnt(0,0,0),gp_Dir(*axis)),math.radians(angle));return transform(shape,t)
for part in parts:
 if part['dnp']:continue
 assert not part['bottom'],'Bottom component transform requires separate validation'
 for index,model in enumerate(part['models']):
  raw=model['path'].replace('${KIPRJMOD}',str(ROOT))
  for v in ('KICAD9_3DMODEL_DIR','KICAD10_3DMODEL_DIR','KICAD8_3DMODEL_DIR'):raw=raw.replace('${'+v+'}',str(LIB))
  p=Path(raw)
  if p.suffix.lower()=='.wrl':p=p.with_suffix('.step')
  if not p.exists():missing.append({'ref':part['ref'],'path':raw});continue
  if str(p) not in cache:
   reader=STEPControl_Reader();assert reader.ReadFile(str(p))==IFSelect_RetDone;reader.TransferRoots();cache[str(p)]=reader.OneShape()
  shape=cache[str(p)]
  if model['scale']!=[1.,1.,1.]:
   sx,sy,sz=model['scale'];g=gp_GTrsf(gp_Mat(sx,0,0,0,sy,0,0,0,sz),gp_XYZ(0,0,0));shape=BRepBuilderAPI_GTransform(shape,g,True).Shape()
  for axis,angle in zip(((1,0,0),(0,1,0),(0,0,1)),model['rotation']):shape=rotate(shape,axis,-angle)
  t=gp_Trsf();t.SetTranslation(gp_Vec(*model['offset']));shape=transform(shape,t)
  shape=rotate(shape,(0,0,1),part['angle'])
  t=gp_Trsf();t.SetTranslation(gp_Vec(part['x'],-part['y'],1.6));shape=transform(shape,t)
  items.append({'ref':part['ref'],'index':index,'path':str(p),'bounds':bounds(shape),'shape':shape})
 print(part['ref'],flush=True)
collisions=[];candidates=0
for i,a in enumerate(items):
 for b in items[i+1:]:
  aa=a['bounds'];bb=b['bounds']
  if not all(min(aa[k+3],bb[k+3])-max(aa[k],bb[k])>.02 for k in range(3)):continue
  candidates+=1
  op=BRepAlgoAPI_Common(a['shape'],b['shape']);op.Build()
  if not op.IsDone():collisions.append(dict(a=a['ref'],b=b['ref'],error='intersection failed'));continue
  props=GProp_GProps();BRepGProp.VolumeProperties_s(op.Shape(),props);volume=abs(props.Mass())
  if volume>.01:collisions.append(dict(a=a['ref'],a_model=a['index'],b=b['ref'],b_model=b['index'],intersection_mm3=volume))
report=dict(mechanical_inputs_sha256=hashlib.sha256((OUT/"mechanical-inputs.json").read_bytes()).hexdigest(),model_file_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in cache},models=len(items),unique_model_files=len(cache),bounding_box_candidates=candidates,missing_models=missing,
             model_less_refs=[p['ref'] for p in parts if not p['models'] and not p['dnp']],collisions=collisions,
             components=[{k:v for k,v in item.items() if k!='shape'} for item in items],
             scaled_models=[{'ref':p['ref'],'models':p['models']} for p in parts if any(m['scale']!=[1.,1.,1.] for m in p['models'])],
             limitations=['Nominal library CAD and simplified heatsink envelopes; fin details illustrative','Project KK396, inductor and large-capacitor models use nominal manufacturer dimensions; remaining library models require tolerance review','No cabinet or mating harness CAD supplied','Ten simplified screw/nut sets included; threads, solder fillets, manufacturing tolerances and tool access require separate assessment','Bounds use board top Z=1.6 mm; CAD transform convention must be compared with native KiCad render'])
(OUT/'mechanical.json').write_text(json.dumps(report,indent=2)+'\n');print('COLLISIONS',collisions);print('MISSING',missing)
