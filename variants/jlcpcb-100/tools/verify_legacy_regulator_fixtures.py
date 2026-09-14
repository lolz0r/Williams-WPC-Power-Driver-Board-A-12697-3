"""Compare saved regulator SPICE fixtures with the final KiCad netlist.
Collapse only explicitly modeled ESR/DCR nodes for connectivity comparisons.
Source/load/temperature/parasitic assumptions remain separate from native values.
"""
import hashlib,json,math,re
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/prespin'
net=ROOT/'output/release-candidate/reports/netlist.xml';tree=ET.parse(net)
values={c.attrib['ref']:c.findtext('value') for c in tree.findall('.//components/comp')};pins={}
for n in tree.findall('.//nets/net'):
 for p in n.findall('node'):pins[p.attrib['ref'],p.attrib['pin']]=n.attrib['name']
def number(s):
 m=re.match(r'([0-9.]+)([kKmMuUnNpP]?)',s);assert m,s
 return float(m[1])*{'':1,'k':1e3,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12}[m[2].lower()]
checks=[]
def check(ok,label):checks.append(dict(passed=bool(ok),description=label))
for rail,u in [('5v','U20'),('12v','U21')]:
 is5=rail=='5v';rr=261 if is5 else 267;cc=33 if is5 else 39
 check(values[u]=='TPS54360BDDAR',u+' selected regulator identity')
 mapping={name:[str(rr+i)] for i,name in enumerate(['Ren1','Ren2','Rrt','Rfb1','Rfb2','Rc'])}
 mapping={name:['R'+x for x in refs] for name,refs in mapping.items()}
 mapping.update(Cin=[f'C{cc}',f'C{cc+1}'],Cboot=[f'C{cc+2}'],Cc=[f'C{cc+3}'],Cp=[f'C{cc+4}'],Cc3=[f'C{cc+5}'],Cout1=['C4' if is5 else 'C2'],Cout2=['C9' if is5 else 'C12'],L1=['L1' if is5 else 'L2'])
 aliases={'0':'GND','vout':'+5V' if is5 else '+12V'}
 aliases.update({s:pins[u,str(pin)] for s,pin in [('boot',1),('vinf',2),('en',3),('rt',4),('fb',5),('comp',6),('sw',8)]})
 aliases.update(cc=pins[f'R{rr+5}','2'],c1='GND',c2='GND',linductor=aliases['vout'])
 check(pins[u,'7']==pins[u,'9']=='GND',u+' ground and exposed pad')
 for path in sorted((OUT/'power-sequence').glob(rail+'_*.cir')):
  records={a[0]:a for line in path.read_text().split('.control')[0].splitlines() if len(a:=line.split())>=4}
  check(records['XU'][1:]==['boot','comp','en','0','sw','rt','vinf','fb','0','TPS54360_TRANS'],path.name+' vendor port order')
  for name,refs in mapping.items():
   row=records[name];actual=sum(number(values[ref]) for ref in refs)
   check(math.isclose(number(row[3]),actual,rel_tol=1e-10),path.name+' '+name+' value '+','.join(refs))
   wanted=sorted(aliases[n] for n in row[1:3])
   for ref in refs:check(sorted(pins[ref,str(i)] for i in [1,2])==wanted,path.name+' '+name+' topology '+ref)
  diode='D36' if is5 else 'D37';d=records['Dcatch']
  check(values[diode]=='B560C' and d[3]=='DB560C' and [aliases[n] for n in d[1:3]]==[pins[diode,'2'],pins[diode,'1']],path.name+' catch diode identity and polarity')
  raw=aliases['vinf'];caps=['C5'] if is5 else ['C6','C7']
  check(math.isclose(number(records['Creservoir'][3]),.8*sum(number(values[c]) for c in caps),rel_tol=1e-10),path.name+' reservoir at minus 20 percent')
  for c in caps:check(pins[c,'1']==raw and pins[c,'2']=='GND',path.name+' '+c+' reservoir topology')
  bridge=105 if is5 else 101
  ac=[pins[f'D{bridge+i}','2'] for i in [0,1]]
  for i in range(4):
   ref=f'D{bridge+i}';check(values[ref] in ['STPS20M100S','STPS20M100ST'],path.name+' '+ref+' bridge identity')
   wanted=(raw,ac[i]) if i<2 else (ac[i-2],'GND')
   check((pins[ref,'1'],pins[ref,'2'])==wanted,path.name+' '+ref+' bridge polarity')
report=dict(passed=all(c['passed'] for c in checks),checks=len(checks),failures=[c for c in checks if not c['passed']],netlist_sha256=hashlib.sha256(net.read_bytes()).hexdigest(),decks={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'power-sequence').glob('*.cir'))},scope='Regulator port mapping, actual R/C/L values and topology, catch diode, raw-rail bridge and reservoir assignment. Explicit lumped ESR/DCR nodes are collapsed only for native connectivity matching.',limitations=['Winding resistance, rectifier fit, input phase, ESR/DCR, lamp load, reverse-current and voltage screens are engineering assumptions, not independently extracted measurements','TPS54360 model is the documented typical vendor model used for the B part; no complete process-corner model','Other load capacitance, wiring and board parasitics remain outside this fixture'])
(OUT/'regulator-fixture-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('Regulator fixture audit:',report['checks'],'checks; PASS',report['passed'],report['failures'])
raise SystemExit(0 if report['passed'] else 1)
