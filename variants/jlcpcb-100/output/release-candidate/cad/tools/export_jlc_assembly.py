"""Export a matching JLCPCB BOM/CPL for every purchased electronic unit.

Native electrical references can describe composite assemblies (fuse + holder,
or two headers). Upload references identify the individual purchased parts.
The mapping and PCBA remark explicitly preserve that relationship.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil

from sexp import parse, find, find_all
from placement_rules import ROTATIONS, MANUAL, correction

ROOT = Path(__file__).resolve().parents[1]
BOM_FIELDS = ['Comment', 'Designator', 'Footprint', 'LCSC Part #']
CPL_FIELDS = ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation']
STACK_OFFSET_MM = 0.3
TE_CODES = {'C86500', 'C305801', 'C305802', 'C592598', 'C94118'}
# Offsets are specific to the purchased part AND the native footprint.
# Checked against numbered LCSC/EasyEDA library pads, not just body outlines.
# Evidence and independent pin correspondence: verify_jlc_assembly.py.


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(rows)


def refkey(ref):
    return (re.sub(r'\d.*', '', ref), int(re.search(r'\d+', ref)[0]), ref)


def tht_center(fp, code, pins=None):
    """Physical body center in local KiCad coordinates, including body offsets."""
    pads = [p for p in find_all(fp, 'pad') if p[1] and (pins is None or p[1] in pins)]
    if code in {'C240823', 'C240824', 'C505166'}:
        # Including inward friction-lock lip: Cartesian Y -4.90..5.11.
        x = sum(float(find(p, 'at')[1]) for p in pads) / len(pads)
        return x, -0.105, 'Molex housing including friction-lock lip; supplier model and native F.Fab agree'
    if code in TE_CODES:
        # Dimensioned native inventory models, not the inherited Molex F.Fab.
        # STEP has Cartesian Y up; footprint local Y points down.
        x = sum(float(find(p, 'at')[1]) for p in pads) / len(pads)
        return x, (0.3175 if code == 'C94118' else 0.762), 'TE drawing 640456 / 640445 housing center; friction wall inward'
    circles = [g for g in find_all(fp, 'fp_circle') if find(g, 'layer') == ['layer', 'F.Fab']]
    if circles:
        assert len(circles) == 1, fp[1]
        x, y = map(float, find(circles[0], 'center')[1:])
        return x, y, 'Radial capacitor F.Fab body-circle center'
    points = []
    for g in fp:
        if not isinstance(g, list) or find(g, 'layer') != ['layer', 'F.Fab']:
            continue
        if g[0] in ['fp_rect', 'fp_line']:
            points.extend(tuple(map(float, find(g, k)[1:])) for k in ['start', 'end'])
    assert points, 'No reviewed THT body outline: ' + fp[1]
    return ((min(p[0] for p in points) + max(p[0] for p in points)) / 2,
            (min(p[1] for p in points) + max(p[1] for p in points)) / 2,
            'Native F.Fab body-outline bounding-box center')


def transform(fp, x, y):
    at = list(map(float, find(fp, 'at')[1:]))
    angle = at[2] if len(at) > 2 else 0
    a = math.radians(angle)
    return at[0] + x * math.cos(a) + y * math.sin(a), -at[1] + x * math.sin(a) - y * math.cos(a), angle % 360


def export(out, root=ROOT):
    pcb = root / 'wpc_power_driver_cost.kicad_pcb'
    board = parse(pcb.read_text())[0]
    fps = {next(p[2] for p in find_all(f, 'property') if p[1] == 'Reference'): f for f in find_all(board, 'footprint')}
    parts = read_csv(out / 'bom/jlc-electronics-by-reference.csv')
    smt = {r['Designator']: r for r in read_csv(out / 'assembly/native-smt-positions.csv')}
    keys = {f'J{k}': v for k, v in __import__('connector_keys').KEYS.items()}
    cpl, mapping, groups, expanded = [], [], {}, Counter()
    folder = out / 'jlcpcb-assembly'
    for part in parts:
        source, parent, code = part['Designator'], part['Parent'], part['JLCPCB_part']
        fp = fps[parent]
        assert find(fp, 'layer')[1] == 'F.Cu', 'Bottom placement needs a reviewed transform'
        qty = int(part['Quantity_per_board'])
        holder = source.endswith('_HOLDER')
        refs = ['J115A', 'J115B'] if parent == source == 'J115' else [('FH' + parent[1:]) if holder else source]
        assert qty == len(refs), (source, qty, refs)
        catalog = json.loads((root / 'research/jlcpcb/catalog' / (code + '.json')).read_text())
        # The upload package describes the actual purchased unit, not the whole
        # composite PCB footprint (notably each six-pin J115 header and fuse).
        package = catalog['componentSpecificationEn'].replace('插件', 'Through-hole')
        group = groups.setdefault(code, {'Comment': part['MPN'], 'Designator': [], 'Footprint': package, 'LCSC Part #': code})
        for ref in refs:
            pins = {str(i) for i in (range(1, 7) if ref == 'J115A' else range(7, 13))} if parent == 'J115' else None
            note = part['Assembly_note']
            if source in smt:
                row = dict(smt[source])
                x, y = float(row['Mid X']), float(row['Mid Y'])
                angle = float(row['Rotation'])
                kind, basis = 'SMT', 'Native KiCad body origin; angle corrected separately against exact purchased library'
            else:
                px, py, basis = tht_center(fp, code, pins)
                x, y, angle = transform(fp, px, py)
                kind = 'THT'
                if holder:
                    kind = 'THT holder'
                elif parent.startswith('F') and parent not in ['F101', 'F102', 'F112']:
                    kind = 'Fuse cartridge insertion'
                row = {'Designator': ref, 'Mid X': f'{x:.6f}', 'Mid Y': f'{y:.6f}', 'Layer': 'Top', 'Rotation': f'{angle:.6f}'}
            native_angle = angle
            offset = correction(code, fp[1])
            if offset:
                angle = (native_angle + offset) % 360
                row['Rotation'] = f'{angle:.6f}'
                note += f' CPL rotation includes {offset:+d} deg LCSC library correction; native PCB rotation is {native_angle:g} deg.'
            if code in MANUAL:
                note += ' ' + MANUAL[code]
            if ref in ['J120', 'J121', 'J126']:
                note += ' C592598 must be checked/selected on the JLCPCB Select Parts page; a matched but unchecked row is excluded from assembly. No public LCSC footprint was returned for this code; use native pin-1/key drawing for manual placement.'
            actual_x, actual_y = x, y
            if kind == 'Fuse cartridge insertion':
                # JLCPCB's stacked-assembly instructions require >0.2 mm
                # separation in the upload to allow both parts to be selected.
                # Actual placement is concentric with the holder, not offset.
                row['Mid X'] = f'{x + STACK_OFFSET_MM:.6f}'
                note = f'Insert {parent} into FH{parent[1:]}. CPL X +0.3 mm is a stacked-part selection offset only; actual position is holder center.'
            if parent in keys and keys[parent] is not None:
                key = keys[parent]
                if ref == 'J115A':
                    note += ' No key post removed in J115A.'
                elif ref == 'J115B':
                    note += ' Remove local post 3 (native J115 pin 9).'
                else:
                    note += f' Remove key post {key}; retain its PCB hole.'
            group['Designator'].append(ref)
            expanded[code] += 1
            cpl.append(row)
            mapping.append(dict(Upload_designator=ref,Native_reference=parent,Source_BOM_designator=source,
                                LCSC_part=code,Assembly=kind,Native_footprint=fp[1],
                                Actual_X_mm=f'{actual_x:.6f}',Actual_Y_mm=f'{actual_y:.6f}',
                                CPL_X_mm=row['Mid X'],CPL_Y_mm=row['Mid Y'],
                                Rotation_deg=row['Rotation'],Native_rotation_deg=f'{native_angle:.6f}',
                                Library_rotation_offset_deg=offset,Center_basis=basis,Assembly_note=note))
    cpl.sort(key=lambda r: refkey(r['Designator']))
    mapping.sort(key=lambda r: refkey(r['Upload_designator']))
    bom = []
    for code, g in sorted(groups.items()):
        g['Designator'] = ','.join(sorted(g['Designator'], key=refkey))
        bom.append(g)
    assert len(cpl) == len({r['Designator'] for r in cpl}) == sum(int(p['Quantity_per_board']) for p in parts)
    assert {r['Upload_designator'] for r in mapping} == {r['Designator'] for r in cpl}
    write_csv(folder / 'BOM.csv', bom, BOM_FIELDS)
    write_csv(folder / 'CPL.csv', cpl, CPL_FIELDS)
    write_csv(out / 'assembly/jlc-smt-cpl.csv', [r for r in cpl if r['Designator'] in smt], CPL_FIELDS)
    write_csv(folder / 'placement-map.csv', mapping, list(mapping[0]))
    # Repair the previously linked filename too. Its matching BOM is BOM.csv.
    shutil.copy2(folder / 'CPL.csv', out / 'assembly/all-electronics-positions.csv')
    shutil.copy2(root / 'docs/JLCPCB_UPLOAD.md', folder / 'README.md')
    shutil.copy2(root / 'docs/CONNECTOR_PREVIEW_REVIEW.md', folder / 'CONNECTOR_PREVIEW_REVIEW.md')
    shutil.copy2(out / 'bom/external-hardware.csv', folder / 'external-hardware.csv')
    cartridges = [r for r in mapping if r['Assembly'] == 'Fuse cartridge insertion']
    remark = 'JLC-100 complete electronics assembly: fit all SMT and through-hole parts in BOM.csv/CPL.csv.\n'
    remark += 'J113 C5200275: corrected CPL rotation 90 deg (native PCB 180 deg). Long axis parallel to left board edge; pin 1 at absolute Gerber X=8.220 mm, Y=-128.459 mm, bottom/right of the 34-pin array when viewed from the top. Preserve ribbon key orientation.\n'
    remark += 'U1=90 deg, U2/U3=270 deg; all SMT offsets are already applied. J110=180 deg; friction-lock wall toward board interior. Follow component-orientation-check.csv and connector-orientation-guide.pdf. Do not add corrections a second time.\n'
    remark += 'TE C86500/C305801/C305802 and Molex C588986 have conflicting public 3D housing and numbered-pad orientations. CPL follows the inward friction wall; manually resolve library placement against native pin/key guide before assembly. C505166 has no public 3D housing: verify its inward friction wall manually. D101-D104 C5143116 have a misframed supplier model: retain native tab against heatsink, manually verify.\n'
    remark += 'J120/J121/J126: select and fit C592598 (TE 1-640445-3), three purchased headers per board. This matched row was unchecked in the reported preview. Quote manual placement/preparation; do not omit these connectors because a library preview is unavailable.\n'
    remark += 'Fuse cartridges are stacked parts: insert ' + '; '.join(f"{r['Upload_designator']} into FH{r['Native_reference'][1:]}" for r in cartridges) + '.\n'
    remark += 'The 13 cartridge coordinates have an intentional +0.3 mm X offset for part selection only. Insert each cartridge concentrically into its holder and fit the included cover. F101/F102 are empty spare holders. F112 is a soldered TA7 fuse.\n'
    remark += 'J115A covers native J115 pins 1-6; J115B covers 7-12. Remove J115B post 3 (native pin 9). Follow placement-map.csv and connector-keys.csv for all other key posts. Trim J120/J121 from 13 to 11 positions and J133/J134/J135 from 10 to 9; dress the J115 seam.\n'
    remark += 'For every prepared header, count physical posts from the native pin-1 end in connector-orientation-guide.pdf, not from conflicting public-library labels. J115B post 3 is the third post counted from the native J115 pin-7 end. Retain all unused posts except the explicit key.\n'
    remark += 'BR3: form leads to its documented 18 mm square, preserve +/minus/AC pin mapping, and use M4x20 hardware.\n'
    remark += 'Please include and quote the manual operations above and the external heatsinks/fasteners/paste in external-hardware.csv; confirm consignment/sourcing and fitting before production. Full build details: INVENTORY_AND_ASSEMBLY.md.\n'
    (folder / 'PCBA-remark.txt').write_text(remark)
    report = dict(passed=True,pcb_sha256=sha(pcb),bom_sha256=sha(folder/'BOM.csv'),cpl_sha256=sha(folder/'CPL.csv'),
                  map_sha256=sha(folder/'placement-map.csv'),bom_groups=len(bom),cpl_rows=len(cpl),
                  native_references=len({r['Native_reference'] for r in mapping}),
                  assembly_counts=dict(Counter(r['Assembly'] for r in mapping)),per_board_by_code=dict(expanded),
                  coordinate_convention='mm; KiCad absolute Gerber origin, Cartesian Y up, positive CCW degrees',
                  part_rotation_offsets_deg=ROTATIONS,
                  corrected_entries=sum(bool(r['Library_rotation_offset_deg']) for r in mapping),
                  stacked_upload_offset_mm=STACK_OFFSET_MM,live_jlcpcb_upload_tested=False,
                  sources=['https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly',
                           'https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly',
                           'https://jlcpcb.com/capabilities/pcb-assembly-capabilities'],
                  limitations=['Format and coverage validated locally; JLCPCB import/part matching/assembly acceptance not exercised.',
                               'All purchased codes audited. Supplier model/pad conflicts and missing libraries are explicit manual assembly gates; corrected live preview remains untested.',
                               'CPL cartridge offset is for selection only. Submit PCBA-remark.txt and placement-map.csv for manual assembly.',
                               'External mechanical hardware is listed for quotation/consignment; no JLC inventory codes have been invented.'])
    (out/'reports/jlc-assembly-export.json').write_text(json.dumps(report,indent=2)+'\n')
    print('JLC mixed assembly:',len(bom),'BOM groups;',len(cpl),'CPL entries;',report['assembly_counts'])
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'output/release-candidate')
    export(p.parse_args().output)
