"""Replay raw ROM writes through netlist-connected buffers/latches/output pins.
This is a settled-state digital integration check. It does not simulate the ASIC
watchdog, sub-cycle analog timing, lamps, triac commutation or load current.
"""
import argparse,csv,hashlib,json,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
# Independent WPC ASIC address / external connector assignment, from the manual.
CLOCK={0x3fe0:12,0x3fe1:10,0x3fe2:9,0x3fe3:11,0x3fe4:7,0x3fe5:8,0x3fe6:13}
BANKS={0x3fe0:(25,4),0x3fe1:(1,8),0x3fe2:(17,8),0x3fe3:(9,8)}
class Circuit:
 def __init__(self,path):
  doc=ET.parse(path);self.pin={};self.parts={c.attrib['ref']:c.findtext('value') for c in doc.findall('.//components/comp')}
  for x in doc.findall('.//nets/net'):
   for n in x.findall('node'):
    if n.attrib['pin'].isdigit():self.pin[n.attrib['ref'],int(n.attrib['pin'])]=x.attrib['name']
  self.ff=[]
  for ref,val in self.parts.items():
   if '574' in val:
    for i in range(8):self.ff.append((self.n(ref,2+i),self.n(ref,11),self.n(ref,19-i),self.n(ref,1),None))
   if '74HCT74' in val:
    for d,c,q,clr in [(2,3,5,1),(12,11,9,13)]:self.ff.append((self.n(ref,d),self.n(ref,c),self.n(ref,q),None,self.n(ref,clr)))
  assert len(self.ff)==56,len(self.ff)
  self.mem={q:0 for d,c,q,oe,clr in self.ff};self.blank=False;self.clear=set()
  self.sol=[];self.col=[];self.row=[];self.gi=[]
  for first,ref,pads in [(1,'J130',[1,2,4,5,6,7,8,9]),(9,'J127',[1,3,4,5,6,7,8,9]),(17,'J126',range(1,9)),(25,'J122',range(1,5))]:
   for pad in pads:
    drain=self.n(ref,pad);q=self.find('Q',2,drain);self.sol.append(self.resistor_other(self.n(q,1),set(self.mem)))
  for pad in [1,2,4,5,6,7,8,9]:
   q=self.find('Q',2,self.n('J133',pad));self.row.append(self.resistor_other(self.n(q,1),set(self.mem)))
  uln={self.n('U19',19-i):self.n('U19',i) for i in range(1,9)}
  for pad in [1,2,3,4,5,6,7,9]:
   q=self.find('Q',2,self.n('J137',pad));self.col.append(uln[self.resistor_other(self.n(q,1),set(uln))])
  for pad in [1,2,3,5,6]:
   q=self.find('Q',2,self.n('J120',pad));e=self.resistor_other(self.n(q,3),{self.n(r,2) for r,v in self.parts.items() if v=='MMBT4401'});bjt=self.find('Q',2,e)
   self.gi.append(self.resistor_other(self.n(bjt,1),set(self.mem)))
 def n(self,r,p):return self.pin[r,p]
 def find(self,prefix,p,n):
  found=[r for r in self.parts if r.startswith(prefix) and self.pin.get((r,p))==n];assert len(found)==1,(prefix,p,n,found);return found[0]
 def resistor_other(self,n,targets):
  found=[]
  for r in self.parts:
   if not r.startswith('R'):continue
   ends=[self.pin.get((r,i)) for i in [1,2]]
   if n in ends:
    other=ends[1-ends.index(n)]
    if other in targets:found.append(other)
  assert len(found)==1,(n,found);return found[0]
 def write(self,a,word,plug=True):
  if a not in CLOCK or not plug:return
  ribbon={self.n('J113',29-2*i):1-((word>>i)&1) for i in range(8)}
  data={self.n('U9',y):1-ribbon[self.n('U9',x)] for x,y in [(2,18),(4,16),(6,14),(8,12),(17,3),(15,5),(13,7),(11,9)]}
  clock=self.n('J113',CLOCK[a])
  for d,c,q,oe,clr in self.ff:
   if c==clock:self.mem[q]=0 if clr in self.clear else data[d]
 def outputs(self):
  driven={q:0 if (oe and self.blank) or clr in self.clear else self.mem[q] for d,c,q,oe,clr in self.ff}
  bits=lambda names:sum(driven[n]<<i for i,n in enumerate(names))
  return bits(self.sol),bits(self.row),bits(self.col),bits(self.gi)

def expected(reg):
 sol=sum((reg.get(a,0)&((1<<n)-1))<<(base-1) for a,(base,n) in BANKS.items())
 return sol,reg.get(0x3fe4,0),reg.get(0x3fe5,0),reg.get(0x3fe6,0)&31

def run(path,net):
 circuit=Circuit(net);regs={};last=-1.;checks=0;failures=[];counts={};active_sol=active_gi=active_row=active_col=0;matrix=0;multi=0;last_out=(0,0,0,0);unchanged=0
 for row in csv.DictReader(path.open()):
  t=float(row['time']);assert t>=last,('Nonmonotonic trace',last,t);last=t
  a=int(row['address'],16)
  if row['kind']!='W' or a not in CLOCK:continue
  word=int(row['data'],16);circuit.write(a,word);regs[a]=word;actual=circuit.outputs();want=expected(regs);checks+=1
  if actual!=want and len(failures)<20:failures.append(dict(time=t,address=hex(a),data=word,actual=actual,expected=want))
  counts[hex(a)]=counts.get(hex(a),0)+1
  so,ro,co,gi=actual;active_sol|=so;active_row|=ro;active_col|=co;active_gi|=gi
  for col in range(8):
   if co>>col&1:matrix|=ro<<(8*col)
  multi+=a==0x3fe5 and bool(co&(co-1));unchanged+=actual==last_out;last_out=actual
 return dict(trace=str(path.relative_to(ROOT)),trace_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),last_event_s=last,write_comparisons=checks,write_counts=counts,unchanged_output_writes=unchanged,active_solenoids=[i+1 for i in range(28) if active_sol>>i&1],active_rows=active_row.bit_count(),active_columns=active_col.bit_count(),active_gi_strings=active_gi.bit_count(),active_matrix_positions=matrix.bit_count(),multi_column_writes=multi,failures=failures,passed=checks>0 and not failures)

def faults(net):
 c=Circuit(net);checks=0;fail=[]
 def check(ok,label):
  nonlocal checks
  checks+=1
  if not ok:fail.append(label)
 for word in range(256):
  c.mem={k:(word>>i%8)&1 for i,k in enumerate(c.mem)};c.blank=True
  so,ro,co,gi=c.outputs();check((so,co,gi)==(0,0,0),f'unknown latched pattern {word} masked by BLANKING')
  reg={}
  for a in CLOCK:c.write(a,word);reg[a]=word
  so,ro,co,gi=c.outputs();check((so,co,gi)==(0,0,0),f'writes while blanked {word}')
  c.blank=False;check(c.outputs()==expected(reg),f'OE release retains words {word}')
  c.blank=True;before=dict(c.mem)
  for a in CLOCK:c.write(a,word^255,plug=False)
  check(c.mem==before,f'disconnected CPU cannot write {word}')
  so,ro,co,gi=c.outputs();check((so,co,gi)==(0,0,0),f'disconnect suppresses drivers {word}')
  c.blank=True
  for a in CLOCK:c.write(a,0)
  c.blank=False
  check(c.outputs()==(0,0,0,0),f'clear before release {word}')
 for row in range(8):
  c.write(0x3fe4,255);q=c.row[row];clr=next(clr for d,clk,out,oe,clr in c.ff if out==q);c.clear={clr};c.mem[q]=0
  check(c.outputs()[1]==255^(1<<row),f'row {row+1} asynchronous clear isolated')
  c.write(0x3fe4,255);check(c.outputs()[1]==255^(1<<row),f'row {row+1} held clear prevents relatch')
  c.clear=set();check(c.outputs()[1]==255^(1<<row),f'row {row+1} stays off until new clock');c.write(0x3fe4,255);check(c.outputs()[1]==255,f'row {row+1} rearmed')
 return dict(checks=checks,failures=fail,passed=not fail)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('traces',nargs='+',type=Path);a=p.parse_args();net=ROOT/'output/release-candidate/reports/netlist.xml'
 reports=[run(path.resolve(),net) for path in a.traces];fault=faults(net)
 result=dict(passed=all(r['passed'] for r in reports) and fault['passed'],netlist_sha256=hashlib.sha256(net.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),traces=reports,faults=fault,limitations=['Settled-state Boolean circuit; separate SPICE checks cover timing, OE turn-off and output currents','ASIC clocks assigned from WPC manual; CPU data represented active low on J113','Trace starts with assumed cleared latches; unknown initial contents separately tested under asserted BLANKING','PinMAME explicitly does not emulate the watchdog. BLANKING injection tests downstream response only, not watchdog generation or partial power','Releasing BLANKING can expose stale latched 1 bits: firmware must clear before enabling; no hardware automatic clear claimed','Lamp overcurrent clear is injected, comparator thresholds and delay covered separately','GI outputs are gate-enable commands; triacs can conduct until the next AC current zero'])
 out=ROOT/'output/verification/prespin/rom-logic.json';out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
