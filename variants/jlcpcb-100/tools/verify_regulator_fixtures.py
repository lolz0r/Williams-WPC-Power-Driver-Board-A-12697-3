"""Bind JLC-3 averaged supply evidence to the final native netlist.

Checks selected parts, controller pin topology and modeled passive values.
The encrypted TI switching model was not run. Old TPS54360 results remain
historical; see verify_legacy_regulator_fixtures.py for their original audit.
"""
import hashlib,json,math,re
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/prototype-readiness'
net=ROOT/'output/release-candidate/reports/netlist.xml';tree=ET.parse(net)
values={c.attrib['ref']:c.findtext('value') for c in tree.findall('.//components/comp')};pins={}
for n in tree.findall('.//nets/net'):
 for p in n.findall('node'):pins[p.attrib['ref'],p.attrib['pin']]=n.attrib['name']
def number(s):
 m=re.match(r'([0-9.]+(?:[eE][+-]?[0-9]+)?)([kKmMuUnNpP]?)',str(s));assert m,s
 return float(m[1])*{'':1,'k':1e3,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12}[m[2].lower()]
checks=[]
def check(ok,label):checks.append(dict(passed=bool(ok),description=label))
def pin(ref,num):return pins.get((ref,str(num)))
def two(ref,a,b):check((pin(ref,1),pin(ref,2))==(a,b),ref+' two-terminal topology')
evidence=[]
selected={name:['U20','U21'] for name in ['buckboost-qualified-nominal','buckboost-qualified-high','buckboost-qualified-low']}
for folder,refs in selected.items():
 p=OUT/folder/'results.json';report=json.loads(p.read_text())
 for u in refs:
  check(report['loops'][u]['passed'],folder+' '+u+' averaged CCM loop sensitivity')
  cs=[c for c in report['cases'] if c['name'].startswith(u+'_')]
  check(len(cs)==16,folder+' '+u+' four sequences at 50/60 Hz and low/high line')
  check(all(c['passed'] for c in cs),folder+' '+u+' transient screens')
  for c in cs:
   path=p.parent/(c['name']+'.cir');src=path.read_text()
   check(hashlib.sha256(src.encode()).hexdigest()==c['deck_sha256'],path.name+' retained deck hash')
   records={a[0]:a for line in src.split('.control')[0].splitlines() if len(a:=line.split())>=4}
   five=u=='U20';rr=261 if five else 267;cc=33 if five else 39
   for name,ref in [('Rfbtop',f'R{rr+3}'),('Rfbbottom',f'R{rr+4}'),('Rcomp',f'R{rr+5}'),('Ccomp',f'C{cc+3}'),('Cpole',f'C{cc+4}'),('Rsense','R326' if five else 'R327')]:
    check(math.isclose(number(records[name][3]),number(values[ref]),rel_tol=1e-8),path.name+' '+ref+' native value')
   check('RMS i(Bsource)' in src,path.name+' RMS measures the actual driven AC source')
   check(math.isclose(number(records['Cbulk'][3]),660e-6*report['parameters']['cap_scale'],rel_tol=1e-8),path.name+' explicit bulk capacitance tolerance')
  evidence.append(dict(report=str(p.relative_to(ROOT)),rail=u,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),cases=len(cs)))
for five in [True,False]:
 u='U20' if five else 'U21';rr=261 if five else 267;cc=33 if five else 39
 raw='/Power_Supply/+5V_RAW' if five else '+18V';out='+5V' if five else '+12V';n=lambda suffix:'/Power_Supply/'+u+'_'+suffix
 check(values[u]=='TPS552892RYQR',u+' controller identity')
 for num,netname in {1:n('EN'),2:'GND',5:'GND',6:n('RT'),7:raw,8:n('SW1'),9:'GND',10:n('SW2'),11:n('REG'),12:n('REG'),13:out,14:n('FB'),15:n('COMP'),17:'GND',18:n('VCC'),19:n('BOOT2'),20:n('BOOT1')}.items():
  check(pin(u,num)==netname,u+' TI pin '+str(num))
 for num in [3,4,16,21]:check((pin(u,num) or '').startswith('unconnected-'),u+' intentional open pin '+str(num))
 cb2,cv,hi,ho,ci3,ci4,co2=[f'C{i}' for i in range(45 if five else 52,52 if five else 59)]
 for ref in [f'C{cc}',f'C{cc+1}',ci3,ci4]:two(ref,raw,'GND');check(math.isclose(number(values[ref]),10e-6,rel_tol=1e-10),ref+' 10 uF input bypass')
 for ref in [f'C{cc+5}',co2]:two(ref,n('REG'),'GND');check(math.isclose(number(values[ref]),10e-6,rel_tol=1e-10),ref+' 10 uF local output bypass')
 for ref in (['C4','C9'] if five else ['C2','C12']):two(ref,out,'GND');check(math.isclose(number(values[ref]),330e-6,rel_tol=1e-10),ref+' output bulk capacitance')
 two(f'C{cc+2}',n('BOOT1'),n('SW1'));two(cb2,n('BOOT2'),n('SW2'));two(cv,n('VCC'),'GND');two(hi,raw,'GND');two(ho,n('REG'),'GND')
 two('L1' if five else 'L2',n('SW1'),n('SW2'));two('R326' if five else 'R327',n('REG'),out)
 two(f'R{rr}',raw,n('EN'));two(f'R{rr+1}',n('EN'),'GND');two(f'R{rr+2}',n('RT'),'GND')
 two(f'R{rr+3}',out,n('FB'));two(f'R{rr+4}',n('FB'),'GND');two(f'R{rr+5}',n('COMP'),n('CC'))
 two(f'C{cc+3}',n('CC'),'GND');two(f'C{cc+4}',n('COMP'),'GND')
 for ref in (['C5'] if five else ['C6','C7']):two(ref,raw,'GND');check(math.isclose(number(values[ref]),.01,rel_tol=1e-10),ref+' retained reservoir')
 bridge=105 if five else 101;ac=[pin(f'D{bridge+i}',2) for i in [0,1]]
 for i in range(4):
  ref=f'D{bridge+i}';check(values[ref] in ['STPS20M100S','STPS20M100ST'],ref+' bridge identity');two(ref,*((raw,ac[i]) if i<2 else (ac[i-2],'GND')))
 check(('D36' if five else 'D37') not in values,u+' obsolete catch diode removed')
report=dict(passed=all(c['passed'] for c in checks),checks=len(checks),failures=[c for c in checks if not c['passed']],netlist_sha256=hashlib.sha256(net.read_bytes()).hexdigest(),evidence=evidence,
 scope='TI controller pin configuration and native passive topology; selected averaged decks and their explicit tolerance values; complete transient runs and CCM phase/gain margin screens.',
 limitations=['Engineering average model, not TI silicon switching-model validation','PFM, commutation/backfeed currents, EMI and short-circuit recovery need first-article measurement','Constant 2.5-ohm lamp load and winding resistance are stress assumptions; transformer/fuse qualification needs actual load data'])
(OUT/'regulator-fixture-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Regulator fixture audit:',report['checks'],'checks; PASS',report['passed'],report['failures']);raise SystemExit(0 if report['passed'] else 1)
