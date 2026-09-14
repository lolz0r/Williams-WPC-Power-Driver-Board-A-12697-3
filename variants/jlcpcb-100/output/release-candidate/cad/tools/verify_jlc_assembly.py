"""Independently check mixed-assembly upload files against purchase/CAD records."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from sexp import parse, find, find_all

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(out, root=ROOT):
    checks, failures = 0, []

    def check(ok, message):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(message)

    def read(name, fields=None):
        p = out/name
        with p.open(newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if fields:
                check(reader.fieldnames == fields, name + ' exact JLC header')
            rows = list(reader)
        check(bool(rows) and all(None not in r and all(v is not None for v in r.values()) for r in rows), name+' rectangular CSV')
        return rows

    bom = read('jlcpcb-assembly/BOM.csv', ['Comment','Designator','Footprint','LCSC Part #'])
    cpl = read('jlcpcb-assembly/CPL.csv', ['Designator','Mid X','Mid Y','Layer','Rotation'])
    mapping = read('jlcpcb-assembly/placement-map.csv')
    parts = read('bom/jlc-electronics-by-reference.csv')
    purchase = read('bom/jlc-electronics-purchase.csv')
    original_smt = read('assembly/jlc-smt-cpl.csv')
    source = {p['Designator']: p for p in parts}
    brefs, codes = [], {}
    for b in bom:
        check(bool(re.fullmatch(r'C\d+', b['LCSC Part #'])), 'Catalog code '+b['LCSC Part #'])
        for ref in b['Designator'].split(','):
            brefs.append(ref)
            codes[ref] = b['LCSC Part #']
    crefs = [r.get('Designator') for r in cpl]
    check(len(brefs) == len(set(brefs)), 'Unique BOM references')
    check(len(crefs) == len(set(crefs)), 'Unique CPL references')
    check(set(brefs) == set(crefs), 'Exact BOM/CPL reference correspondence')
    check(all(re.fullmatch(r'[A-Z]+\d+[A-Z]*', r or '') for r in brefs+crefs), 'Unambiguous uppercase alphanumeric upload references')
    total = sum(int(p['Quantity_per_board']) for p in parts)
    check(len(cpl) == len(brefs) == total == 440, 'Every purchased electronic unit appears once')
    expected = Counter({p['JLCPCB_part']: int(p['Quantity_per_board']) for p in purchase})
    check(Counter(codes.values()) == expected, 'Per-code quantities exactly match 100-board purchase BOM')
    byref = {r['Designator']: r for r in cpl}
    mapped = {r['Upload_designator']: r for r in mapping}
    check(set(mapped) == set(crefs), 'All placements have native reference mapping')
    native = {p['Parent'] for p in parts}
    check({m['Native_reference'] for m in mapping} == native and len(native) == 426, 'All 426 native electronic references covered')
    expanded = Counter(m['Source_BOM_designator'] for m in mapping)
    check(expanded == Counter({p['Designator']: int(p['Quantity_per_board']) for p in parts}), 'Composite assemblies expand to their actual purchased quantities')
    for ref, p in byref.items():
        check(p.get('Layer') in ['Top','Bottom'], ref+' layer')
        try:
            x,y,a = (float(p[k]) for k in ['Mid X','Mid Y','Rotation'])
            ok = all(math.isfinite(v) for v in [x,y,a]) and 0 <= a < 360 and 0 <= x <= 449.152 and -272.910 <= y <= 0
        except (KeyError,TypeError,ValueError):
            ok = False
        check(ok, ref+' finite millimetre coordinates and rotation inside board bounds')
        m = mapped[ref]
        check(codes[ref] == m['LCSC_part'] == source[m['Source_BOM_designator']]['JLCPCB_part'],ref+' exact purchased part code')
    for r in original_smt:
        check(byref.get(r['Designator']) == r, r['Designator']+' SMT-only and mixed upload placement agree')
    check(sum(m['Assembly']=='SMT' for m in mapping)==345, '345 SMT / 95 through-hole and inserted units')
    xml = ET.parse(out/'reports/netlist.xml')
    comps = {c.attrib['ref']: c for c in xml.findall('.//components/comp')}
    for ref in native:
        c = comps[ref]
        check(not any(p.attrib.get('name')=='dnp' for p in c.findall('property')), ref+' populated in native netlist')
    for n in list(range(103,112))+list(range(113,117)):
        fuse, holder = f'F{n}', f'FH{n}'
        f,h = mapped[fuse],mapped[holder]
        check(codes[holder]=='C268204', holder+' actual holder part')
        check(f['Assembly']=='Fuse cartridge insertion' and h['Assembly']=='THT holder',fuse+' assembly roles')
        check(abs(float(byref[fuse]['Mid X'])-float(byref[holder]['Mid X'])-.3)<1e-6 and byref[fuse]['Mid Y']==byref[holder]['Mid Y'],fuse+' documented >0.2mm selection offset')
        check(f['Actual_X_mm']==h['Actual_X_mm'] and f['Actual_Y_mm']==h['Actual_Y_mm'],fuse+' physical insertion is concentric')
    for ref in ['F101','F102']:
        check(codes[ref]=='C268204' and 'FH'+ref[1:] not in codes,ref+' exactly one empty spare holder')
    check(codes['F112']=='C3014110' and 'FH112' not in codes,'F112 single soldered fuse')
    check('J115' not in byref and codes['J115A']==codes['J115B']=='C86500','J115 exactly two six-pin headers')
    board = parse((root/'wpc_power_driver_cost.kicad_pcb').read_text())[0]
    fps = {next(p[2] for p in find_all(f,'property') if p[1]=='Reference'):f for f in find_all(board,'footprint')}
    from audit_placement_libraries import audit as audit_libraries
    libraries = audit_libraries(out, root, fps, mapped, byref, check)
    check(libraries['codes_audited']==69 and libraries['rows_audited']==440, 'All purchased codes and placements audited')
    check(libraries['connectors_with_library']==36 and libraries['connectors_without_library']==['J120','J121','J126'], 'All 39 purchased headers covered')
    # Independent OpenCascade bounds from the previously checked native models
    # catch origin/pin-centroid confusion without reusing export transforms.
    mech_path = root/'output/verification/revision/mechanical.json'
    mech = json.loads(mech_path.read_text())
    bodies = {c['ref']:c['bounds'] for c in mech['components'] if c['index']==0}
    for m in mapping:
        if m['Assembly']=='SMT' or m['Native_reference']=='J115':
            continue
        b = bodies[m['Native_reference']]
        delta = math.hypot(float(m['Actual_X_mm'])-(b[0]+b[3])/2,float(m['Actual_Y_mm'])-(b[1]+b[4])/2)
        check(delta < .08,m['Upload_designator']+' THT body center agrees with independent 3D envelope')
    a,b = byref['J115A'],byref['J115B']
    bounds = bodies['J115']
    check(abs((float(a['Mid X'])+float(b['Mid X']))/2-(bounds[0]+bounds[3])/2)<.08 and abs((float(a['Mid Y'])+float(b['Mid Y']))/2-(bounds[1]+bounds[4])/2)<.08,'J115 two housing centers agree with native composite envelope')
    check((out/'assembly/all-electronics-positions.csv').read_bytes()==(out/'jlcpcb-assembly/CPL.csv').read_bytes(),'Previously linked all-electronics filename is a valid combined CPL alias')
    remark = (out/'jlcpcb-assembly/PCBA-remark.txt').read_text()
    check(all(f'F{n} into FH{n}' in remark for n in list(range(103,112))+list(range(113,117))),'Order remark names every fuse/holder stack')
    check('J115B post 3' in remark and 'external-hardware.csv' in remark,'Order remark includes key and mechanical completion requirements')
    report = dict(passed=not failures,checks=checks,failures=failures,pcb_sha256=sha(root/'wpc_power_driver_cost.kicad_pcb'),
                  file_sha256={name:sha(out/name) for name in ['jlcpcb-assembly/BOM.csv','jlcpcb-assembly/CPL.csv','jlcpcb-assembly/placement-map.csv','jlcpcb-assembly/PCBA-remark.txt','jlcpcb-assembly/connector-orientation-check.csv','jlcpcb-assembly/component-orientation-check.csv','jlcpcb-assembly/connector-orientation-guide.pdf','jlcpcb-assembly/connector-orientation-overview.png','jlcpcb-assembly/orientation-change-log.csv','assembly/jlc-smt-cpl.csv']},
                  bom_groups=len(bom),cpl_entries=len(cpl),smt_entries=len(original_smt),tht_and_inserted_entries=len(cpl)-len(original_smt),
                  connector_library_entries_checked=libraries['connectors_with_library'],connector_entries_without_library=libraries['connectors_without_library'],
                  connector_library_source_sha256=libraries['source_sha256'],
                  placement_library_audit=libraries,
                  connector_library_scope=libraries['scope'],
                  independent_mechanical_report_sha256=sha(mech_path),live_jlcpcb_upload_tested=False)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'output/release-candidate')
    out=p.parse_args().output
    report=audit(out)
    (out/'reports/jlc-assembly-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print('JLC assembly check:',report['passed'],report['checks'],'checks;',report['failures'])
    raise SystemExit(0 if report['passed'] else 1)
