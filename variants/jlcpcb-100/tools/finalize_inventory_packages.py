"""Correct datasheet land geometry and attach local inventory assembly envelopes."""
import copy,json,math
from pathlib import Path
import pcbnew as pcb
from sexp import parse,dump,find,find_all,S,Sym
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'wpc_power_driver_cost.kicad_pcb';b=pcb.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()};changed={};record=[]
# Do not regenerate automatically: this is a one-shot PCB geometry change.
assert fps['BR3'].GetFPID().GetLibNickname()=='Diode_THT','Already applied'
def vec(x,y):return pcb.VECTOR2I(round(x*1e6),round(y*1e6))
def absolute(f,x,y):
 a=math.radians(f.GetOrientationDegrees());p=f.GetPosition();return vec(p.x/1e6+x*math.cos(a)+y*math.sin(a),p.y/1e6-x*math.sin(a)+y*math.cos(a))
for f in fps.values():
 r=f.GetReference();code=f.GetFieldText('JLCPCB Part') if f.HasField('JLCPCB Part') else ''
 if code in ['C86500','C305801','C305802','C592598','C94118']:
  name='TE_'+r+'_Prepared';changed[r]='wpc_cost:'+name;f.SetFPIDAsString(changed[r])
 if r=='F112':
  for p in f.Pads():p.SetPosition(absolute(f,-2.75 if p.GetNumber()=='1' else 2.75,0))
 if r=='BR3':
  changed[r]='wpc_cost:ONSEMI_GBPC2506W_18mm_formed';f.SetFPIDAsString(changed[r])
  for p in f.Pads():
   xy={'1':(0,-6.4),'2':(18,11.6),'3':(0,11.6),'4':(18,-6.4)}[p.GetNumber()];record.append(dict(ref=r,pin=p.GetNumber(),from_xy=[p.GetPosition().x/1e6,p.GetPosition().y/1e6],to_local=xy));p.SetPosition(absolute(f,*xy))
  f.SetField('Assembly Modification','Form wire leads to 18 x 18 mm pattern; + to pad 1, - to pad 2, AC to 3/4; preserve 0.12 mm standoff. New body max 11.23 mm. M4x20 screw replaces M4x16.')
pcb.SaveBoard(str(path),b)
# Model paths and library copies via S-expression preserve all pad identities/nets.
bdoc=parse(path.read_text())[0]
for f in find_all(bdoc,'footprint'):
 pp={p[1]:p[2] for p in find_all(f,'property')};r=pp['Reference'];code=pp.get('JLCPCB Part');names=None
 if code=='C443892':names=['GPD_4700u_35V']
 elif code=='C109394':names=['Rubycon_ZLH_330u_25V']
 elif code=='C5456831':names=['KNSCHA_2200u_100V']
 elif r.startswith('J') and r in changed:names=['TE_'+r]
 elif r=='F112':names=['TLC_TA7']
 elif r=='J113':names=['XFCN_EH254V_12_34P_envelope']
 elif r.startswith('F'):names=['HONGJU_FH1_200CK_G']+(['Fuse_5x20_cartridge'] if r not in ['F101','F102'] else [])
 elif r=='BR3':names=['ONSEMI_GBPC2506W_formed','Boyd_6223_on_GBPC2506W','M4x20_BR3_hardware']
 if names:
  for m in find_all(f,'model'):f.remove(m)
  for name in names:
   assert (ROOT/'models/inventory'/(name+'.step')).exists(),name
   f.append(S('model','${KIPRJMOD}/models/inventory/'+name+'.step',S('offset',S('xyz',0,0,0)),S('scale',S('xyz',1,1,1)),S('rotate',S('xyz',0,0,0))))
path.write_text(dump(bdoc)+'\n')
# Library snapshots use relative pad coordinates and zero footprint rotation.
for f in find_all(bdoc,'footprint'):
 pp={p[1]:p[2] for p in find_all(f,'property')};r=pp['Reference']
 if r=='J113':
  for g in list(f):
   if isinstance(g,list) and g[0].startswith('fp_') and find(g,'layer')==['layer','F.CrtYd']:f.remove(g)
  pts=[(-3.38,-11.37),(5.92,-11.37),(5.92,52.01),(-3.38,52.01)]
  import uuid
  for aa,zz in zip(pts,pts[1:]+pts[:1]):f.append(S('fp_line',S('start',*aa),S('end',*zz),S('stroke',S('width',.05),S('type',Sym('default'))),S('layer','F.CrtYd'),S('uuid',str(uuid.uuid4()))))
 if r in changed or r in ['F112','J113']:
  lib=copy.deepcopy(f);lib[1]=str(f[1]).split(':')[-1];at=find(lib,'at');angle=float(at[3]) if len(at)>3 else 0;lib.remove(at)
  for item in list(lib):
   if isinstance(item,list) and item[0] in ['path','uuid','sheetname','sheetfile']:lib.remove(item)
  for p in find_all(lib,'pad'):
   at=find(p,'at')
   if len(at)>3:at[3]=float(at[3])-angle
   for item in list(p):
    if isinstance(item,list) and item[0] in ['net','uuid','pinfunction','pintype']:p.remove(item)
  for p in find_all(lib,'property'):
   if p[1]=='Reference':p[2]='REF**'
  (ROOT/'footprints/wpc_cost.pretty'/(lib[1]+'.kicad_mod')).write_text(dump(lib)+'\n')
path.write_text(dump(bdoc)+'\n')
for path in ROOT.glob('*.kicad_sch'):
 doc=parse(path.read_text())[0]
 for sym in find_all(doc,'symbol'):
  pp={p[1]:p for p in find_all(sym,'property')};r=pp.get('Reference',[None,None,None])[2]
  if r in changed:pp['Footprint'][2]=changed[r]
  if r=='BR3':
   q=pp.get('Assembly Modification')
   if q is None:q=copy.deepcopy(pp['MPN']);q[1]='Assembly Modification';sym.append(q)
   q[2]=fps['BR3'].GetFieldText('Assembly Modification')
 # Extend applicable symbol filters for explicit custom inventory packages.
 def visit(n):
  if not isinstance(n,list):return
  if n and n[0]=='property' and n[1]=='ki_fp_filters':
   if 'Molex' in n[2] and 'TE_*' not in n[2]:n[2]+=' TE_*'
   if 'Diode_Bridge' in n[2] and 'ONSEMI*' not in n[2]:n[2]+=' ONSEMI*'
  for q in n:visit(q)
 visit(doc);path.write_text(dump(doc)+'\n')
(ROOT/'research/package-finalization.json').write_text(json.dumps(dict(footprints=changed,pad_changes=record),indent=2)+'\n');print('Updated packages',len(changed))
