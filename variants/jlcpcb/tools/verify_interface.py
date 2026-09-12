"""Independent connector/pin and exhaustive byte-pattern checks of the exported netlist.
Reference: Williams STTNG operations manual printed quick-reference solenoid table (PDF p2),
WPC 16-9834.2 interface drawings, Nexperia HCT240/HCT574 pin/function tables.
Static logic only: SPICE separately checks analog timing, blanking and output stages.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET


def audit(path):
 root=ET.parse(path);pin={};nodes={};components={c.attrib['ref']:c for c in root.findall('.//components/comp')}
 for net in root.findall('.//nets/net'):
  name=net.attrib['name'];nodes[name]=[(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')]
  for ref,p in nodes[name]:pin[(ref,p)]=name
 failures=[];checks=0
 def check(condition,description):
  nonlocal checks
  checks+=1
  if not condition:failures.append(description)
 def net(ref,p):return pin.get((ref,str(p)))
 # Independent catalog ordering table, Molex SDA-41791/26-60-4xx0.
 kk_order={3:'0026604030',4:'0026604040',5:'0026604050',6:'0026604060',7:'0026604070',9:'0026604090',11:'0026604110',12:'0026604120',13:'0026604130'}
 for ref,c in components.items():
  match=re.search(r'Molex_KK-396_A-41791-00(\d\d)_',c.findtext('footprint') or '')
  if match:
   fields={f.attrib['name']:f.text for f in c.findall('fields/field')}
   check(str(fields.get('MPN','')).replace('-','').lstrip('0')==kk_order[int(match[1])].lstrip('0'),f'{ref} Molex KK396 catalog MPN')
 # Ribbon positions are external interface requirements, independent of board net names.
 for p in (4,6,14,16,18,20,22,24,26,28,30):check(net('J113',p)=='GND',f'J113-{p} ground')
 for bit in range(8):check(net('J113',29-2*bit)==f'D{bit}_N',f'Ribbon bit {bit}')
 check(net('J113',31)=='BLANKING','Ribbon blanking');check(net('J113',34)=='ZERO_CROSS','Ribbon zero cross')
 pairs=[(2,18),(4,16),(6,14),(8,12),(17,3),(15,5),(13,7),(11,9)]
 for a,y in pairs:check(net('U9',a) and net('U9',a)==net('U9',y)+'_N',f'U9 inversion pair {a}->{y}')
 for p in (1,19,10):check(net('U9',p)=='GND',f'U9 enable/ground {p}')
 check(net('U9',20)=='+5V','U9 power')
 groups=[('U5',10,1,8,'SOL'),('U4',11,9,8,'SOL'),('U3',9,17,8,'SOL'),('U2',12,25,4,'SOL'),('U18',8,1,8,'COL'),('U1',13,0,8,'GI')]
 for ref,clock,start,count,kind in groups:
  check(net(ref,11)==net('J113',clock),f'{ref} clock from J113-{clock}')
  check(net(ref,1)=='BLANKING',f'{ref} blanking');check(net(ref,20)=='+5V' and net(ref,10)=='GND',f'{ref} power')
  for bit in range(count):
   expected=f'SOL{start+bit:02}_L' if kind=='SOL' else f'COLDRV{start+bit}' if kind=='COL' else ('FLIP_RLY_L' if bit==7 else f'GI{bit+1}_L' if bit<5 else f'GI_BIT{bit}')
   check(net(ref,19-bit)==expected,f'{ref} Q{bit} expected {expected}, got {net(ref,19-bit)}')
  for word in range(256):
   ribbon={net('J113',29-2*bit):1-((word>>bit)&1) for bit in range(8)}
   buffered={net('U9',y):1-ribbon.get(net('U9',a),0) for a,y in pairs}
   actual=sum(buffered.get(net(ref,2+bit),-256)<<bit for bit in range(count))
   check(actual==(word&((1<<count)-1)),f'{ref} byte 0x{word:02x} maps incorrectly')
 # External output connector positions from the machine's quick reference.
 outputs={}
 for base,ref,pads in [(1,'J130',[1,2,4,5,6,7,8,9]),(9,'J127',[1,3,4,5,6,7,8,9]),(17,'J126',list(range(1,9))),(25,'J122',list(range(1,5)))]:
  for ch,p in enumerate(pads,base):outputs[ch]=(ref,p)
 for ch,(ref,p) in outputs.items():
  drain=f'SOL{ch:02}';check(net(ref,p)==drain,f'Output {ch} at {ref}-{p}')
  mos=[r for r,pinno in nodes.get(drain,[]) if pinno=='2' and r.startswith('Q')]
  check(len(mos)==1,f'Output {ch} has exactly one MOSFET drain')
  if len(mos)!=1:continue
  q=mos[0];check(net(q,3)=='GND',f'{q} source ground')
  gate=net(q,1);latch=f'SOL{ch:02}_L'
  resistors=[r for r in components if r.startswith('R') and {net(r,1),net(r,2)}=={gate,latch}]
  check(len(resistors)==1,f'{q} gate series resistor to correct latch')
  pulls=[r for r in components if r.startswith('R') and {net(r,1),net(r,2)}=={gate,'GND'}]
  check(len(pulls)==1,f'{q} gate pulldown for blanking')
 # OEM lamp connector maps and row latch pin functions, independently specified.
 for ref in ('J133','J134','J135'):
  for row,pad in enumerate((1,2,4,5,6,7,8,9),1):check(net(ref,pad)==f'ROW{row}',f'{ref}-{pad} row {row}')
 for ref in ('J137','J138'):
  for col,pad in enumerate((1,2,3,4,5,6,7,9),1):check(net(ref,pad)==f'COL{col}',f'{ref}-{pad} column {col}')
 row_latches=[('U13',2),('U13',1),('U12',2),('U12',1),('U11',2),('U11',1),('U10',2),('U10',1)]
 for row,(ref,unit) in enumerate(row_latches,1):
  clr,d,clk,pre,q=(1,2,3,4,5) if unit==1 else (13,12,11,10,9)
  check(net(ref,d)==f'D{row-1}',f'Row {row} data bit')
  check(net(ref,clk)==net('J113',7),f'Row {row} clock')
  check(net(ref,pre)=='+5V' and net(ref,clr)==f'ROWCLR{row}',f'Row {row} preset/overcurrent clear')
  mos=f'Q{91-row}';gate=net(mos,1)
  check(net(mos,2)==f'ROW{row}',f'Row {row} MOSFET drain')
  check(any({net(r,1),net(r,2)}=={gate,net(ref,q)} for r in components if r.startswith('R')),f'Row {row} gate from latch')
  check(any({net(r,1),net(r,2)}=={net(mos,3),'GND'} and components[r].findtext('value')=='0.22R' for r in components if r.startswith('R')),f'Row {row} current shunt')
 for word in range(256):
  data={f'D{i}':(word>>i)&1 for i in range(8)}
  actual=sum(data.get(net(ref,2 if unit==1 else 12),-256)<<bit for bit,(ref,unit) in enumerate(row_latches))
  check(actual==word,f'Row byte 0x{word:02x} maps incorrectly')
 for ref in ('J120','J121'):
  for gi,pad in enumerate((1,2,3,5,6),1):check(net(ref,pad)==f'GI{gi}_RET',f'{ref}-{pad} GI return')
  for gi,pad in enumerate(range(7,12),1):check(net(ref,pad)==f'GI{gi}_OUT',f'{ref}-{pad} GI fused hot')
 check(net('J119',1)=='GI5_OUT' and net('J119',3)=='GI5_RET','Coin door GI polarity')
 for channel,ref in [(20,'D1'),(21,'D9'),(22,'D10'),(23,'D12'),(24,'D11'),(25,'D8'),(26,'D7'),(27,'D6'),(28,'D5')]:
  check(net(ref,1)=='+20V' and net(ref,2)==f'SOL{channel}',f'JLC-2 STTNG flasher {channel} clamp returns to +20 V')
 for gi,triac in enumerate(('Q18','Q10','Q14','Q16','Q12'),1):
  check(net(triac,1)=='GI_RET' and net(triac,2)==f'GI{gi}_RET',f'GI {gi} triac terminal mapping')
  fuse=f'F{111-gi}'
  check({net(fuse,1),net(fuse,2)}=={f'GI{gi}_IN',f'GI{gi}_OUT'},f'GI {gi} hot-side fuse')
 return {'checks':checks,'failures':failures,'passed':not failures,'netlist_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'scope':'1792 exhaustive register byte patterns plus ribbon, output, lamp and GI pin topology. Analog thresholds, propagation and fault protection require separate SPICE/bench verification.'}


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('netlist',type=Path);a=p.parse_args();r=audit(a.netlist)
 out=Path('output/verification/revision/interface.json');out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
