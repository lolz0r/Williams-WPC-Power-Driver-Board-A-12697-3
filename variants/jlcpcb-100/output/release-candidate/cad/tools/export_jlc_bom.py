"""Export a complete, source-derived 100-board BOM and matching SMT and complete-electronics CPLs.
Includes native THT parts, supplementary holders, multi-piece headers and hardware.
"""
import argparse,csv,hashlib,json,math,re
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
from sexp import parse,find,find_all
from sourcing import SRC
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub('[^A-Z0-9]','',s.upper()).lstrip('0')
def refkey(s):return (re.sub(r'\d.*','',s),int(re.search(r'\d+',s)[0]) if re.search(r'\d+',s) else 0,s)
def write(p,rows,keys=None):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys or list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'output/release-candidate');a=p.parse_args();out=a.output
 pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';net=out/'reports/netlist.xml';board=parse(pcb.read_text())[0];fps={next(p[2] for p in find_all(f,'property') if p[1]=='Reference'):f for f in find_all(board,'footprint')};cats={};parts=[];native={};excluded=[];features=[];assembly=[]
 def cat(code):
  if code not in cats:cats[code]=json.loads((ROOT/'research/jlcpcb/catalog'/(code+'.json')).read_text())
  d=cats[code];assert d['isBuyComponent']=='1',code;return d
 def row(ref,parent,qty,value,code,fp,method,note=''):
  d=cat(code);return dict(Designator=ref,Parent=parent,Quantity_per_board=qty,Value=value,MPN=d['componentModelEn'],Manufacturer=d['componentBrandEn'],Footprint=fp,JLCPCB_part=code,Library={'base':'Basic','expand':'Extended'}[d['componentLibraryType']],Assembly=method,Assembly_note=note)
 def center(ref,padnums=None):
  fp=fps[ref];at=list(map(float,find(fp,'at')[1:]));x,y=at[:2];ang=at[2] if len(at)>2 else 0;rad=math.radians(ang)
  pads=[p for p in find_all(fp,'pad') if p[1] and (padnums is None or p[1] in padnums)]
  if pads:
   px=sum(float(find(p,'at')[1]) for p in pads)/len(pads);py=sum(float(find(p,'at')[2]) for p in pads)/len(pads)
  else:px=py=0
  return dict(X_mm=round(x+px*math.cos(rad)+py*math.sin(rad),6),Y_mm=round(-y+px*math.sin(rad)-py*math.cos(rad),6),Rotation_deg=ang%360,Side='Top')
 for c in ET.parse(net).findall('.//components/comp'):
  ref=c.attrib['ref'];fields={f.attrib['name']:f.text or '' for f in c.findall('fields/field')}
  if ref.startswith(('H','TP')) or any(q.attrib.get('name')=='dnp' for q in c.findall('property')):
   excluded.append(ref);features.append(dict(Designator=ref,Parent=ref,Quantity_per_board=0,Value=c.findtext('value'),MPN=fields.get('MPN',''),Manufacturer=fields.get('Manufacturer',''),Footprint=c.findtext('footprint'),JLCPCB_part=fields.get('JLCPCB Part',''),Library='Not purchased',Assembly='DNP or fabricated board feature',Assembly_note='Native design feature; no purchased placement in this variant.',DNP='yes'));continue
  fp=fps[ref];pp={x[1]:x[2] for x in find_all(fp,'property')};code=fields['JLCPCB Part'];d=cat(code);lib={'base':'Basic','expand':'Extended'}[d['componentLibraryType']]
  assert fields['JLCPCB Library']==lib and norm(fields['MPN'])==norm(d['componentModelEn']),(ref,fields,d)
  for k in ['MPN','Manufacturer','JLCPCB Part','JLCPCB Library','Purchased Quantity','Holder JLCPCB Part']:assert fields.get(k,'')==pp.get(k,''),(ref,k)
  qty=int(fields.get('Purchased Quantity','1'));method='SMT' if 'smd' in (find(fp,'attr') or []) else 'Through-hole/manual'
  note=fields.get('Assembly Modification',fields.get('Assembly Note',''))
  if ref=='J115':note='Two 640445-6 headers: J115A pins 1-6; J115B pins 7-12. Align friction walls; dress seam if necessary. Preserve pin-1/key mapping.'
  if ref in ['J120','J121']:note='Trim 13-position 1-640445-3 to 11: remove pins/body 12-13 at far end. Preserve pin 1 and friction wall; deburr.'
  if ref in ['J133','J134','J135']:note='Trim 10-position 1-640456-0 to 9: remove final position 10. Preserve pin 1, key and friction wall; deburr.'
  if ref=='F112':note='TLC TA7 soldered 2410 time-lag 7 A fuse; replacement requires desoldering. No holder. Do not up-rate.'
  r=row(ref,ref,qty,c.findtext('value'),code,c.findtext('footprint'),method,note);parts.append(r);native[ref]=r
  if ref=='J115':
   for suffix,pins in [('A',range(1,7)),('B',range(7,13))]:assembly.append(dict(Designator=ref+suffix,Parent=ref,JLCPCB_part=code,**center(ref,{str(i) for i in pins}),Center_definition='Average contact position of this six-position subassembly',Assembly_note=note))
  else:assembly.append(dict(Designator=ref,Parent=ref,JLCPCB_part=code,**center(ref),Center_definition='Mean native terminal position; use assembly drawing for body offset/polarity',Assembly_note=note))
  if fields.get('Holder JLCPCB Part'):
   h=fields['Holder JLCPCB Part'];parts.append(row(ref+'_HOLDER',ref,1,'5x20 holder with cover',h,c.findtext('footprint'),'Through-hole/manual','Fit holder before inserting the separately listed cartridge.'))
   assembly.append(dict(Designator=ref+'_HOLDER',Parent=ref,JLCPCB_part=h,**center(ref),Center_definition='Holder center between its two PCB leads',Assembly_note='FH1-200CK-G includes insulating cover; cartridge listed separately.'))
 parts.sort(key=lambda r:refkey(r['Designator']));groups={}
 for r in parts:
  k=r['JLCPCB_part'];g=groups.setdefault(k,dict(JLCPCB_part=k,MPN=r['MPN'],Manufacturer=r['Manufacturer'],Library=r['Library'],Designators=[],Quantity_per_board=0));g['Designators'].append(r['Designator']);g['Quantity_per_board']+=r['Quantity_per_board']
 purchase=[]
 for code,g in sorted(groups.items()):
  d=cat(code);g['Designators']=' '.join(g['Designators']);need=100*g['Quantity_per_board'];extra=max(10,math.ceil(.05*need));required=need+extra;stock=int(d['overseasStockCount']);available=int(d['canPresaleNumber']);usable=min(stock,available)
  tiers=[t for t in d['prices'] if int(t['startNumber'])<=required];price=float(max(tiers,key=lambda t:int(t['startNumber']))['productPrice']) if tiers else None
  g.update(Boards=100,Build_quantity=need,Spare_quantity=required-need,Required_quantity=required,Preorder_MOQ_informational=d.get('preMinPurchaseNum'),Physical_stock=stock,Orderable_stock=available,Conservative_available=usable,Inventory_surplus=usable-required,Inventory_pass=usable>=required,Unit_price_USD=price,Run_cost_USD=round(required*price,4) if price is not None else '',Catalog_URL=d['url'],Fetched_UTC=d['fetched_utc']);purchase.append(g)
 hardware=[]
 for key,qty,parent in [('HS7020',5,'Q10 Q12 Q14 Q16 Q18'),('HS6224',1,'BR3'),('HS5772',4,'D101 D102 D103 D104'),('M3X8',4,'D101 D102 D103 D104'),('M3X12',5,'Q10 Q12 Q14 Q16 Q18'),('M3NUT',9,'D101 D102 D103 D104 Q10 Q12 Q14 Q16 Q18'),('M4X16',1,'BR3 H9'),('M4NUT',1,'BR3 H9'),('THERMALPASTE',1,'All ten heatsink interfaces')]:
  d=SRC[key].copy()
  if key=='M4X16':d.update(mpn='MJ420MPP',desc='M4 x 20 mm JIS-B1111 Phillips pan screw, zinc steel; thicker GBPC2506W / 6223BG mounting');key='M4X20'
  hardware.append(dict(Designator=key,Parent=parent,Quantity_per_board=qty if key!='THERMALPASTE' else 'as needed',Value=d['desc'],MPN=d['mpn'],Manufacturer=d['mfr'],Footprint='Mechanical model attached to parent footprint',JLCPCB_part='',Library='External hardware',Assembly='Mechanical/manual',Assembly_note='Externally procured; inventory not covered by JLCPCB audit. '+('One 3 mL syringe initial batch provision; replenish according to measured application consumption.' if key=='THERMALPASTE' else f'100-board build requires {qty*100} plus 5% spares.')))
 write(out/'bom/jlc-electronics-by-reference.csv',parts);write(out/'bom/jlc-electronics-purchase.csv',purchase);write(out/'bom/jlc-through-hole-manual.csv',[r for r in parts if r['Assembly']!='SMT']);write(out/'bom/external-hardware.csv',hardware);write(out/'bom/all-components.csv',[dict(r,DNP='') for r in parts+hardware]+features);write(out/'bom/unpopulated-and-board-features.csv',features);write(out/'assembly/electronics-placement-details.csv',assembly)
 smt=[r for r in parts if r['Assembly']=='SMT'];sg={};cpl=[]
 positions={r['Ref']:r for r in csv.DictReader((out/'assembly/positions.csv').open())}
 for r in smt:
  ref=r['Designator'];p=positions[ref];at=list(map(float,find(fps[ref],'at')[1:]));assert abs(float(p['PosX'])-at[0])<1e-6 and abs(float(p['PosY'])+at[1])<1e-6;assert p['Side']=='top' and r['Quantity_per_board']==1
  k=(r['JLCPCB_part'],r['Footprint'],r['Value']);g=sg.setdefault(k,dict(Comment=r['Value'],Designator=[],Footprint=r['Footprint'],**{'LCSC Part #':r['JLCPCB_part']}));g['Designator'].append(ref)
  cpl.append({'Designator':ref,'Mid X':p['PosX'],'Mid Y':p['PosY'],'Layer':'Top','Rotation':f"{float(p['Rot'])%360:.6f}"})
 for r in sg.values():r['Designator']=','.join(sorted(r['Designator'],key=refkey))
 write(out/'bom/jlc-smt-bom.csv',list(sg.values()));write(out/'assembly/native-smt-positions.csv',cpl)
 from export_jlc_assembly import export as export_assembly
 export_assembly(out)
 assert len(cpl)==len(set(r['Designator'] for r in cpl))==len(smt)
 assert set(native)=={r['Parent'] for r in assembly}
 counts=Counter(r['Library'] for r in native.values());shorts=[r for r in purchase if not r['Inventory_pass']]
 report=dict(passed=not shorts,boards=100,reserve_policy='100 x per-board quantity + max(10,ceil(5% build quantity)); public in-stock assembly quantities, pre-order MOQ is informational',pcb_sha256=sha(pcb),netlist_sha256=sha(net),native_populated_electronic_references=len(native),purchased_electronic_units=sum(r['Quantity_per_board'] for r in parts),smt_placements=len(smt),through_hole_native_references=sum(r['Assembly']!='SMT' for r in native.values()),native_references_by_library=dict(counts),basic_smt_placements=sum(r['Library']=='Basic' for r in smt),distinct_catalog_codes=len(cats),fuse_holders=sum(r['Quantity_per_board'] for r in parts if r['JLCPCB_part']=='C268204'),fuse_cartridges=sum(r['Designator'].startswith('F') and r['Designator'] not in ['F101','F102','F112'] and not r['Designator'].endswith('_HOLDER') for r in parts),electronic_run_with_spares_USD=round(sum(r['Run_cost_USD'] for r in purchase),2),stock_reserved=False,shortfalls=shorts,excluded_native_refs=excluded,external_hardware=hardware,catalog_archives={c:dict(json_sha256=sha(ROOT/'research/jlcpcb/catalog'/(c+'.json')),url=d['url'],fetched_utc=d['fetched_utc']) for c,d in cats.items()},limitations=['Public stock/orderable snapshot; no purchase, reservation or assembly quotation. Recheck before order.','100-board inventory covers electronics, including all through-hole components and purchased subassemblies. External heatsinks/fasteners/thermal paste appear in complete BOM and parent CAD models but are not JLC stock-qualified.','JLC assemblyComponentFlag and manufacturing acceptance differ from catalog purchasability; THT and connector modification require agreed manual/consignment assembly.','SMT CPL uses native KiCad body origins and reviewed exact-part rotation offsets, absolute Gerber origin; unresolved library conflicts require manual assembly review.'])
 (out/'reports/jlc-sourcing.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['catalog_archives','external_hardware','excluded_native_refs','limitations']});assert report['passed'],'Inventory shortfalls'
if __name__=='__main__':main()
