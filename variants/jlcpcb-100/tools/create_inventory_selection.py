"""Explicit substitution plan; applied only to the isolated inventory variant."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
original=ET.parse(ROOT.parent/'jlcpcb/output/release-candidate/reports/netlist.xml')
bycode={};native={}
for c in original.findall('.//components/comp'):
 fields={f.attrib['name']:f.text or '' for f in c.findall('fields/field')};r=c.attrib['ref'];native[r]=fields
 bycode.setdefault(fields.get('JLCPCB Part'),[]).append(r)
selection={}
def choose(refs,code,why,**kw):
 for r in refs.split() if isinstance(refs,str) else refs:
  selection[r]=dict(code=code,reason=why,**kw)
def replace(old,code,why,**kw):choose(bycode[old],code,why,**kw)
replace('C19272254','C22397842','Same RYQ pinout, 4 A average-current limit; tested at guaranteed 3.3 A minimum.',value='TPS552872QWRYQRQ1')
replace('C3844168','C138687','Same 10 uF 50 V X7R 1210 electrical class and land pattern.')
replace('C77020','C307331','Basic 100 nF 50 V X7R 0402, same land pattern.')
replace('C274001','C17427','Same 118 kohm 1% 0805 UVLO resistor.')
choose('R266','C17633','Basic 33 kohm replaces 33.2 kohm; compensation verified by supply sweeps.',value='33K')
replace('C705613','C875839','Same 0.22 ohm 1% 1 W 2512 current sensing resistor.')
replace('C6788','C2878759','Same TI HCT574 logic and pin order; narrower 5.3 mm NS package.',footprint='Package_SO:SO-20_5.3x12.6mm_P1.27mm')
replace('C132264','C6772','Same TI HCT240 logic and pin order; narrower 5.3 mm NS package.',footprint='Package_SO:SO-20_5.3x12.6mm_P1.27mm')
replace('C1579638','C109394','Same 330 uF 25 V; 3.5 mm lead spacing and 0.056 ohm per capacitor max impedance.',footprint='Capacitor_THT:CP_Radial_D8.0mm_P3.50mm')
replace('C1582025','C5456831','Same 2200 uF 100 V D25 x 40 mm snap-in; 2.29 A rated ripple.')
replace('C6130373','C250866','10000 uF 35 V D25 x 45 mm snap-in; ripple validation required.')
replace('C222114','C5143116','100 V dual 20 A Schottky; physical A-K-A leads already paralleled on native board.',value='MBR40100A')
replace('C969989','C3874015','100 V dual 15 A Schottky; physical A-K-A leads already paralleled on native board.',value='MBRB30100CT')
replace('C435891','C906984','600 V 25 A GBPC-W bridge, 300 A surge; verify thermal bounds.',value='GBPC2506W')
replace('C151826','C8512','Basic NPN emitter follower; same SOT-23 B-E-C pins; beta=100 conservative model.',value='MMBT2222A')
replace('C39797','C9102','8 A 600 V insulated triac, same 50 mA quadrant-IV limit; 80 A surge and 32 A2s checked.',value='BTA08-600CRG')
replace('C151086','C5381754','Same 5 A time-lag 250 V 5x20 ceramic fuse.',value='5A T')
replace('C3157012','C5381743','Same 0.75 A time-lag 250 V 5x20 ceramic fuse.',value='0.75A T')
choose('F112','C3014110','7 A time-lag 125 VAC, 200 A breaking capacity, 139.419 A2s; soldered 2410 replaces scarce cartridge.',value='7A T 125VAC',footprint='wpc_cost:TLC_TA_2410_Fuse')
replace('C3029536','C268204','Empty holders at F101/F102; no fuse cartridge installed.',value='Empty fuse holder')
for r in native:
 if r.startswith('F') and r!='F112':
  selection.setdefault(r,dict(code=native[r]['JLCPCB Part'],reason='Retain fuse rating.'))['footprint']='wpc_cost:HONGJU_FH1_200CK_G'
replace('C17656945','C86500','TE MTA156 friction lock, 1.14 mm square pins; same 3.96 mm grid.')
replace('C587091','C305801','TE MTA156 friction lock, 1.14 mm square pins; same 3.96 mm grid.')
replace('C17420444','C305802','TE MTA156 friction lock, 1.14 mm square pins; same 3.96 mm grid.')
replace('C17226055','C592598','TE MTA156 13 positions, same mating geometry.')
replace('C17541501','C592598','Trim last two positions from 13-position TE header; preserve pin 1 and key position.',trim_to=11)
replace('C7426778','C86500','Two 6-position TE headers at 12-position grid; dress mating seam to fit common harness.',quantity=2)
replace('C587032','C94118','Trim last position from TE MTA100 10-position header to nine; same 0.64 mm square pins and 2.54 mm grid.',trim_to=9)
replace('C17502444','C5200275','34-pin 2.54 mm ejector header, same signal order; 1.0 mm holes and checked shroud orientation.',footprint='wpc_cost:XFCN_EH254V_12_34P')
# MOSFET assignment is finalized after hot-loss trials, before application.
(ROOT/'research/selection.json').write_text(json.dumps(selection,indent=2)+'\n')
print(len(selection),'explicit reference changes')
