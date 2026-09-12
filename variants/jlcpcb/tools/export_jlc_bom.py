"""Build JLCPCB purchasing/SMT files from the fresh netlist and native placement.
Catalog archives are a dated public snapshot, not allocated stock or a quote.
"""
import csv, hashlib, json, math, re
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
from sexp import parse, find, find_all

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/release-candidate'
CAT = ROOT / 'research/jlcpcb/catalog'

def write(path, rows, keys=None):
    with path.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=keys or list(rows[0]));w.writeheader();w.writerows(rows)

def normalize(s): return re.sub('[^A-Z0-9]', '', s.upper()).lstrip('0')
def refkey(s): return (re.sub(r'\d', '', s), int(re.search(r'\d+', s)[0]))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';net=OUT/'reports/netlist.xml'
    board=parse(pcb.read_text())[0]
    fps={next(p[2] for p in find_all(f,'property') if p[1]=='Reference'):f for f in find_all(board,'footprint')}
    catalog={};parts=[];clips=[];native={};excluded=[]
    def selected(code):
        if code not in catalog: catalog[code]=json.loads((CAT/(code+'.json')).read_text())
        d=catalog[code];assert d['isBuyComponent']=='1', f'{code}: not purchasable through JLCPCB'
        return d
    for c in ET.parse(net).findall('.//components/comp'):
        ref=c.attrib['ref'];fields={f.attrib['name']:f.text or '' for f in c.findall('fields/field')}
        if ref.startswith(('H','TP')) or any(p.attrib.get('name')=='dnp' for p in c.findall('property')):
            excluded.append(ref);continue
        code=fields['JLCPCB Part'];d=selected(code);fp=fps[ref]
        library={'base':'Basic','expand':'Extended'}[d['componentLibraryType']]
        assert fields['JLCPCB Library']==library
        assert normalize(fields['MPN'])==normalize(d['componentModelEn']), (ref,fields['MPN'],d['componentModelEn'])
        for field in ['MPN','Manufacturer','JLCPCB Part','JLCPCB Library']:
            assert next(p[2] for p in find_all(fp,'property') if p[1]==field)==fields[field], (ref,field)
        method='SMT' if 'smd' in (find(fp,'attr') or []) else 'Through-hole/manual'
        qty=2 if ref in ['F101','F102'] else 1
        row=dict(Designator=ref,Quantity=qty,Value=c.findtext('value'),MPN=fields['MPN'],Manufacturer=fields['Manufacturer'],Footprint=c.findtext('footprint'),JLCPCB_part=code,Library=library,Assembly=method)
        parts.append(row);native[ref]=row
        if 'Fuseholder_Clip-5x20mm' in row['Footprint']:
            if ref not in ['F101','F102']:
                cd=selected('C3029536')
                parts.append(dict(row,Designator=ref+'A '+ref+'B',Quantity=2,Value='Fuse clips',MPN='3517',Manufacturer=cd['componentBrandEn'],JLCPCB_part='C3029536',Library='Extended',Assembly='Through-hole/manual'))
            at=list(map(float,find(fp,'at')[1:]));x,y=at[:2];a=math.radians(at[2] if len(at)>2 else 0)
            for pin,suffix in [('1','A'),('2','B')]:
                pads=[p for p in find_all(fp,'pad') if p[1]==pin]
                px=sum(float(find(p,'at')[1]) for p in pads)/len(pads);py=sum(float(find(p,'at')[2]) for p in pads)/len(pads)
                clips.append(dict(Designator=ref+suffix,Parent=ref,JLCPCB_part='C3029536',MPN='3517',X_mm=round(x+px*math.cos(a)+py*math.sin(a),6),Y_mm=round(-y+px*math.sin(a)-py*math.cos(a),6),Parent_rotation_deg=at[2] if len(at)>2 else 0,Note='Clip center between its two pins; orient retaining end away from fuse center'))
    assert len(clips)==32
    parts.sort(key=lambda r:refkey(r['Designator'].split()[0]))
    write(OUT/'bom/jlc-electronics-by-reference.csv',parts)
    groups={}
    for r in parts:
        code=r['JLCPCB_part'];g=groups.setdefault(code,dict(r,Designator=[],Quantity=0));g['Designator'].append(r['Designator']);g['Quantity']+=r['Quantity']
    purchase=[]
    for code,g in sorted(groups.items()):
        d=selected(code);g['Designator']=' '.join(g['Designator']);g['Stock_snapshot']=d['overseasStockCount'];g['Purchasing_status']='Stock covers one board' if d['overseasStockCount']>=g['Quantity'] else 'Preorder / replenish; confirm lead time and minimum order'
        g['Catalog_URL']=d['url'];g['Fetched_UTC']=d['fetched_utc'];purchase.append(g)
    write(OUT/'bom/jlc-electronics-purchase.csv',purchase)
    smt=[r for r in parts if r['Assembly']=='SMT'];sg={}
    for r in smt:
        k=(r['JLCPCB_part'],r['Footprint'],r['Value']);g=sg.setdefault(k,dict(Comment=r['Value'],Designator=[],Footprint=r['Footprint'],**{'LCSC Part #':r['JLCPCB_part']}));g['Designator'].append(r['Designator'])
    for r in sg.values():r['Designator']=','.join(sorted(r['Designator'],key=refkey))
    write(OUT/'bom/jlc-smt-bom.csv',list(sg.values()))
    positions={r['Ref']:r for r in csv.DictReader((OUT/'assembly/positions.csv').open())}
    cpl=[]
    for r in smt:
        ref=r['Designator'];p=positions[ref];at=list(map(float,find(fps[ref],'at')[1:]))
        assert abs(float(p['PosX'])-at[0])<1e-6 and abs(float(p['PosY'])+at[1])<1e-6
        assert p['Side']=='top'
        cpl.append({'Designator':ref,'Mid X':p['PosX'],'Mid Y':p['PosY'],'Layer':'Top','Rotation':f"{float(p['Rot'])%360:.6f}"})
    assert len(cpl)==len({p['Designator'] for p in cpl})==len(smt)
    write(OUT/'assembly/jlc-smt-cpl.csv',cpl)
    write(OUT/'assembly/fuse-clip-centers.csv',clips)
    write(OUT/'bom/jlc-through-hole-manual.csv',[r for r in parts if r['Assembly']!='SMT'])
    original=list(csv.DictReader((OUT/'bom/all-components.csv').open()))
    hardware=[r for r in original if r['Footprint']=='Mechanical' and r['MPN']!='3517']
    write(OUT/'bom/external-hardware.csv',hardware)
    report=dict(passed=True,pcb_sha256=sha(pcb),netlist_sha256=sha(net),native_populated_electronic_references=len(native),purchased_electronic_units=sum(r['Quantity'] for r in parts),smt_placements=len(smt),fuse_clips=len(clips),fuse_cartridges=14,distinct_catalog_codes=len(catalog),native_references_by_library=dict(Counter(r['Library'] for r in native.values())),purchased_units_by_library=dict(Counter({lib:sum(r['Quantity'] for r in parts if r['Library']==lib) for lib in ['Basic','Extended']})),distinct_codes_by_library=dict(Counter(r['Library'] for r in purchase)),excluded_native_refs=excluded,preorder_or_short_stock=[r for r in purchase if r['Stock_snapshot']<r['Quantity']],catalog_archives={code:dict(json_sha256=sha(CAT/(code+'.json')),html_sha256=sha(CAT/(code+'.html')),url=d['url'],fetched_utc=d['fetched_utc']) for code,d in catalog.items()},limitations=['Public catalog snapshot, no reserved stock or assembly quote; preorders can carry minimum quantities and uncertain lead times','JLCPCB assembly engineering must approve component orientation, polarity, exposed-pad paste and stencil process in its actual library','SMT upload pair intentionally excludes through-hole parts and external hardware; separate manual lists include all 32 fuse clips','All SMT origins are at nominal package body centers; signed absolute coordinates follow exported Gerbers; rotations follow native KiCad convention','No consumables or mechanical hardware are required to be sourced at JLCPCB per user clarification'])
    (OUT/'reports/jlc-sourcing.json').write_text(json.dumps(report,indent=2)+'\n')
    print({k:v for k,v in report.items() if k not in ['catalog_archives','excluded_native_refs','preorder_or_short_stock','limitations']})
    print('Preorder / stock shortage:',[(r['MPN'],r['Quantity'],r['Stock_snapshot']) for r in report['preorder_or_short_stock']])

if __name__=='__main__':main()
