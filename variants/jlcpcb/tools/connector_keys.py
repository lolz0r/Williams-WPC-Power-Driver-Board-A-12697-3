"""Explicit OEM key schedule and corresponding assembled-header CAD variants.
Run without options to audit. --models also updates the board's model references.
Manual PDF page 61 (printed 2-9); never infer a key from an arbitrary NC pin.
"""
import argparse,csv,json,re,hashlib
from pathlib import Path
from sexp import parse,dump,find,find_all
KEYS={101:3,102:7,103:None,104:3,105:3,106:4,107:4,108:None,109:6,110:5,111:4,112:4,113:None,114:6,115:9,116:1,117:1,118:1,119:2,120:4,121:4,122:7,123:2,124:4,125:4,126:9,127:2,128:4,129:3,130:3,131:2,132:4,133:3,134:3,135:3,136:1,137:8,138:8}
def main():
 p=argparse.ArgumentParser();p.add_argument('--models',action='store_true');a=p.parse_args()
 pcb=Path('wpc_power_driver_cost.kicad_pcb');b=parse(pcb.read_text())[0];rows=[];failures=[]
 for fp in find_all(b,'footprint'):
  props={p[1]:p[2] for p in find_all(fp,'property')};ref=props['Reference']
  if not re.fullmatch(r'J\d+',ref) or int(ref[1:]) not in KEYS:continue
  key=KEYS[int(ref[1:])];pads=find_all(fp,'pad')
  net='' if key is None else find(next(p for p in pads if str(p[1])==str(key)),'net')[-1]
  if key and not net.startswith('unconnected-'):failures.append(ref+' key is connected to '+net)
  rows.append(dict(Reference=ref,Positions=len(pads),Omit_pin='' if key is None else key,MPN=props.get('MPN'),Net_at_key=net))
  if a.models and key:
   from OCP.STEPControl import STEPControl_Reader,STEPControl_Writer,STEPControl_AsIs
   from OCP.IFSelect import IFSelect_RetDone
   from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
   from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
   from OCP.gp import gp_Pnt
   model=find(fp,'model');base=re.sub(r'_key\d+(?=\.step)','',model[1]);path=base.replace('${KIPRJMOD}',str(Path.cwd())).replace('${KICAD10_3DMODEL_DIR}','/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')
   target=Path('models')/(Path(path).stem+f'_key{key:02d}.step')
   if not Path(path).exists() and 'KK-254' in path:
    path='/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels/Connector_Molex.3dshapes/'+Path(path).name
   if not target.exists():
    reader=STEPControl_Reader();assert reader.ReadFile(path)==IFSelect_RetDone;reader.TransferRoots();shape=reader.OneShape()
    pitch=3.96 if 'KK396' in base else 2.54
    # Remove the selected pin column only; narrow bore through plastic depicts a pulled pin.
    half=.60 if pitch==3.96 else .40
    cut=BRepPrimAPI_MakeBox(gp_Pnt((key-1)*pitch-half,-half,-5),2*half,2*half,25).Shape()
    result=BRepAlgoAPI_Cut(shape,cut).Shape();writer=STEPControl_Writer();writer.Transfer(result,STEPControl_AsIs);assert writer.Write(str(target))==IFSelect_RetDone
   model[1]='${KIPRJMOD}/'+str(target)
 assert len(rows)==38
 if a.models:
  assert not failures;pcb.write_text(dump(b)+'\n')
 out=Path('output/verification/revision');rows.sort(key=lambda r:int(r['Reference'][1:]))
 with (out/'connector-keys.csv').open('w',newline='') as f:w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
 report=dict(passed=not failures,connectors=len(rows),keys=sum(r['Omit_pin']!='' for r in rows),failures=failures,pcb_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),source='Williams STTNG Operations Manual PDF page 61, printed 2-9; J121 key 4 visually rechecked 2026-09-08',limitation='Static schedule and NC check; physical harness orientation and mating fit require first article')
 (out/'connector-keys.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
