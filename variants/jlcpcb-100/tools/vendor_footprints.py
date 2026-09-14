"""Make library access portable using snapshots of embedded project footprints.
This preserves the board's existing custom pad geometry; it is not an independent
land-pattern validation. Manufacturer dimensions are audited separately.
"""
from pathlib import Path
import copy,hashlib,json
from sexp import parse,dump,find,find_all,S,Sym
ROOT=Path(__file__).resolve().parents[1];b=parse((ROOT/'wpc_power_driver_cost.kicad_pcb').read_text())[0];seen={};libs=set()
for f in find_all(b,'footprint'):
 name=str(f[1])
 if ':' not in name:continue
 lib,part=name.split(':',1)
 if name in seen:continue
 libs.add(lib);p=ROOT/'footprints'/(lib+'.pretty')/(part+'.kicad_mod');p.parent.mkdir(exist_ok=True)
 d=copy.deepcopy(f);d[1]=part
 placement=find(d,'at');angle=float(placement[3]) if placement and len(placement)>3 else 0
 # Native pad/text angles include the parent rotation; a library has no placement.
 for n in find_all(d,'pad')+find_all(d,'property')+find_all(d,'fp_text'):
  at=find(n,'at')
  if at and len(at)>3:at[3]=(float(at[3])-angle)%360
 d[:]=[n for n in d if not(isinstance(n,list) and n[0] in ['at','path','sheetname','sheetfile','uuid'])]
 d[2:2]=[S('version',20241229),S('generator',Sym('pcbnew'))]
 for prop in find_all(d,'property'):
  if prop[1]=='Reference':prop[2]='REF**'
  elif prop[1]=='Value':prop[2]=part
 for pad in find_all(d,'pad'):pad[:]=[n for n in pad if not(isinstance(n,list) and n[0] in ['net','pinfunction','pintype'])]
 p.write_text(dump(d)+'\n');seen[name]=dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
table=S('fp_lib_table',S('version',7),*[S('lib',S('name',lib),S('type','KiCad'),S('uri','${KIPRJMOD}/footprints/'+lib+'.pretty'),S('options',''),S('descr','Embedded project footprint snapshot; see research/footprint-sources.json')) for lib in sorted(libs)])
(ROOT/'fp-lib-table').write_text(dump(table)+'\n');(ROOT/'research/footprint-sources.json').write_text(json.dumps(dict(source='Native board embedded footprints, preserving existing custom modifications',footprints=seen),indent=2)+'\n');print(len(seen),'footprints in',len(libs),'local libraries')
