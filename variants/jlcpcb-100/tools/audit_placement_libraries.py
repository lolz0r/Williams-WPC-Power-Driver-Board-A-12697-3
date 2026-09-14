"""Audit every purchased part against archived, exact-code public LCSC geometry.

Centered pad patterns check orientation; unlike a package-angle lookup this also
checks pin functions for the project's common-cathode rectifiers and DPAK FETs.
Reports distinguish validated geometry, symmetry and unresolved supplier data.
"""
from collections import defaultdict, Counter
import csv
import hashlib
import itertools
import json
import math
from functools import lru_cache
from pathlib import Path
from sexp import find, find_all
from connector_keys import KEYS


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rotate(p, angle):
    a = math.radians(angle); x,y = p
    return x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a)


def centered(groups):
    allp = [p for ps in groups.values() for p in ps]
    mean = [sum(p[k] for p in allp)/len(allp) for k in (0,1)]
    return {n: [(p[0]-mean[0],p[1]-mean[1]) for p in ps] for n,ps in groups.items()}


def error(native, library, angle):
    # Duplicate anodes are interchangeable; cathode/tab is not.
    errors = []
    for pin, pts in native.items():
        choices = [rotate(p,angle) for p in library[pin]]
        errors += min(([math.dist(p,q) for p,q in zip(pts,perm)]
                       for perm in itertools.permutations(choices)),key=lambda e:sum(v*v for v in e))
    return math.sqrt(sum(e*e for e in errors)/len(errors)), max(errors)


@lru_cache(maxsize=None)
def supplier_wall(path, plastic_material):
    """Measure which side contains the tall plastic, relative to contact row."""
    vertices=[];groups=defaultdict(set);material=None
    for line in path.read_text().splitlines():
        if line.startswith('v '):vertices.append(tuple(map(float,line.split()[1:4])))
        elif line.startswith('usemtl '):material=line.split()[1]
        elif line.startswith('f '):
            groups[material].update(int(v.split('/')[0])-1 for v in line.split()[1:])
    plastic=[vertices[i] for i in groups[plastic_material]]
    metal=[vertices[i] for key,indices in groups.items() if key!=plastic_material and key in ['1','2'] for i in indices]
    low=min(p[2] for p in plastic);high=max(p[2] for p in plastic)
    upper=[p for p in plastic if p[2]>low+.65*(high-low)]
    row=(min(p[1] for p in metal)+max(p[1] for p in metal))/2
    wall=sum(p[1] for p in upper)/len(upper)-row
    assert abs(wall)>1, 'Ambiguous friction wall in '+str(path)
    return 1 if wall>0 else -1


def audit(out, root, fps, mapped, byref, check):
    evidence, rows, connectors = {}, [], []
    manifest=root/'research/jlc-placement-libraries/mechanical-sources.json'
    evidence[str(manifest.relative_to(root))]=sha(manifest)
    for source in json.loads(manifest.read_text())['sources']:
        if source['file']:
            path=root/source['file'];evidence[source['file']]=sha(path)
            check(evidence[source['file']]==source['sha256'],'Unchanged mechanical source '+source['file'])
    for ref,m in mapped.items():
        code = m['LCSC_part']; fp = fps[m['Native_reference']]
        path = root/'research/jlc-placement-libraries'/f'{code}.json'
        evidence[str(path.relative_to(root))] = sha(path)
        data = json.loads(path.read_text())
        metadata=path.with_name(code+'-source.json')
        evidence[str(metadata.relative_to(root))]=sha(metadata)
        check(json.loads(metadata.read_text())['sha256']==sha(path),ref+' archived library matches retrieval hash')
        at = list(map(float,find(fp,'at')[1:])); native_angle = (at[2] if len(at)>2 else 0)%360
        angle = float(byref[ref]['Rotation']); offset = (angle-native_angle)%360
        native = defaultdict(list)
        for p in find_all(fp,'pad'):
            if p[1]:
                x,y = map(float,find(p,'at')[1:3]); native[str(p[1])].append((x,-y))
        # RYQ pin 9 has overlapping thermal/copper pad objects at the same point.
        # They are one electrical land, not two separately placed leads.
        native = {n:list(dict.fromkeys(points)) for n,points in native.items()}
        if ref in ['J115A','J115B']:
            start = 6 if ref == 'J115B' else 0
            native = {str(int(n)-start):pts for n,pts in native.items() if start<int(n)<=start+6}
        check(abs(float(m['Native_rotation_deg'])-native_angle)<1e-6,ref+' records native angle')
        check(abs((native_angle+float(m['Library_rotation_offset_deg']))%360-angle)<1e-6,ref+' records applied offset')
        row = dict(Designator=ref,LCSC_part=code,Native_rotation_deg=native_angle,
                   CPL_rotation_deg=angle,Checked_pads=0,Centered_RMS_error_mm='',
                   Best_numbered_pad_offsets_deg='',Status='',Detail='')
        p1=rotate(native['1'][0],native_angle)
        row.update(Native_pad_1_X_mm=f'{at[0]+p1[0]:.6f}',Native_pad_1_Y_mm=f'{-at[1]+p1[1]:.6f}')
        if m['Assembly']=='Fuse cartridge insertion':
            row.update(Status='Manual insertion',Detail='Cartridge inserted concentrically in separate holder; CPL selection offset is not physical placement.')
        elif not data.get('success'):
            nonpolar = ref.startswith('R')
            row.update(Status='No library; nonpolarized' if nonpolar else 'MANUAL: no library',
                       Detail='Retain native axis; 180 deg electrically equivalent.' if nonpolar else 'Native assembly drawing and polarity/key control placement; no library claim.')
        else:
            d = data['result']
            check(d['lcsc']['number']==code and d['owner']['uuid']=='0819f05c4eef4c71ace90d822a990e87'
                  and d['packageDetail']['owner']['uuid']==d['owner']['uuid'],ref+' exact-code LCSC-owned library')
            library = defaultdict(list)
            for s in d['packageDetail']['dataStr']['shape']:
                if s.startswith('PAD~'):
                    p = s.split('~'); n = p[8]
                    if code == 'C3007': n = {'4':'2'}.get(n,n) # D: LCSC4, native2
                    if code == 'C235758': n = {'1':'2','3':'2','4':'1'}[n] # A,A,K
                    if code == 'C5143116': n = {'1':'2','3':'2','2':'1'}[n] # A,A,K
                    library[n].append((float(p[2])*.254,-float(p[3])*.254))
            if ref.startswith('J'):
                library = {n:library[n] for n in native if n in library}
            same = set(library)==set(native) and all(len(library[n])==len(native[n]) for n in native)
            check(same,ref+' complete pad/function correspondence')
            if same:
                n,l = centered(native),centered(library)
                scores = {a:error(n,l,a) for a in [0,90,180,270]}
                best = min(v[0] for v in scores.values())
                fits = [a for a,v in scores.items() if v[0] <= best+0.001]
                rms,mx = error(n,l,offset)
                row.update(Checked_pads=sum(map(len,n.values())),Centered_RMS_error_mm=f'{rms:.6f}',
                           Best_numbered_pad_offsets_deg='/'.join(map(str,fits)))
                conflict = code in {'C86500','C305801','C305802','C588986'}
                nonpolar = ref.startswith(('R','L')) or (ref.startswith('C') and m['Assembly']=='SMT') or code in ['C268204','C3014110']
                if conflict:
                    check((offset+180)%360 in fits,ref+' explicitly detected 180 degree model/pad conflict')
                    row.update(Status='MANUAL: housing/pad conflict',Detail='CPL follows inward friction wall; numbered public pads face opposite. Resolve library model at assembly review; native pin/key guide is authoritative.')
                elif nonpolar and (offset+180)%360 in fits:
                    row.update(Status='Nonpolarized; axis checked',Detail='180 degree reversal has identical electrical function.')
                    check(best<.5,ref+' nonpolarized pitch/axis fits')
                else:
                    check(offset in fits,ref+' CPL uses best functional pad orientation')
                    # SMT land sizes vary; centered lead spacing is more useful
                    # than a zero-error demand on different recommended lands.
                    check(rms < (.01 if ref.startswith('J') else .6),ref+' centered package pitch/geometry fits')
                    row.update(Status='Functional pad orientation checked',Detail='Centered land pattern; SMT pad lengths may differ. Does not certify live JLC 3D model or absolute placement.')
                if code == 'C505166':
                    row.update(Status='MANUAL: housing unavailable',Detail='Numbered pads checked; no public 3D housing. Require inward friction wall.')
                if code == 'C5143116':
                    row.update(Status='MANUAL: invalid 3D frame',Detail='Common cathode and two interchangeable anodes checked; supplier solid lies below PCB. Retain native tab-to-heatsink orientation.')
                if ref == 'J113':
                    world = {pin:[(at[0]+rotate(p,native_angle)[0],-at[1]+rotate(p,native_angle)[1]) for p in pts] for pin,pts in native.items()}
                    for pin,pts in l.items():
                        x,y = rotate(pts[0],angle)
                        check(math.dist((float(byref[ref]['Mid X'])+x,float(byref[ref]['Mid Y'])+y),world[pin][0])<1e-6,'J113 absolute library pin '+pin+' at native hole')
        rows.append(row)
        if ref.startswith('J'):
            p = rotate(native['1'][0],native_angle)
            tab = rotate((0,-1),native_angle) if ref!='J113' else rotate((-1,0),native_angle)
            # Model wall directions measured from upper plastic vertices.
            # TE/Molex public models use zero c_rotation for these codes.
            plastic_material = {'C86500':'2','C305801':'2','C305802':'2','C94118':'1','C588986':'1','C240823':'1','C240824':'1'}
            if code in plastic_material:
                raw = root/'research/jlc-preview'/f'{code}-supplier.obj'
                evidence[str(raw.relative_to(root))] = sha(raw)
                node=json.loads(next(s[8:] for s in data['result']['packageDetail']['dataStr']['shape'] if s.startswith('SVGNODE~')))
                check(all(float(v)==0 for v in node['attrs']['c_rotation'].split(',')),ref+' supplier wall frame has no additional model rotation')
                wall = rotate((0,supplier_wall(raw,plastic_material[code])),angle)
                check(math.dist(tab,wall)<1e-6,ref+' supplier friction wall faces OEM inward side')
            key = KEYS[int(m['Native_reference'][1:])]
            if ref=='J115A': key=None
            if ref=='J115B': key=3
            k = None if key is None else rotate(native[str(key)][0],native_angle)
            direction = ('right' if tab[0]>.5 else 'left' if tab[0]<-.5 else 'up' if tab[1]>.5 else 'down')
            connectors.append(dict(Designator=ref,LCSC_part=code,Native_rotation_deg=native_angle,CPL_rotation_deg=angle,
                                   Pin_1_X_mm=f'{at[0]+p[0]:.6f}',Pin_1_Y_mm=f'{-at[1]+p[1]:.6f}',
                                   Omit_post=key or '',Key_X_mm='' if k is None else f'{at[0]+k[0]:.6f}',
                                   Key_Y_mm='' if k is None else f'{-at[1]+k[1]:.6f}',
                                   Tab_or_notch_top_view=direction,Checked_pins=row['Checked_pads'],
                                   Library_orientation_status=row['Status'],Detail=row['Detail']))
    for name,content in [('component-orientation-check.csv',rows),('connector-orientation-check.csv',connectors)]:
        with (out/'jlcpcb-assembly'/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(content[0]));w.writeheader();w.writerows(content)
    return dict(source_sha256=evidence,status_counts=dict(Counter(r['Status'] for r in rows)),
                manual_references=[r['Designator'] for r in rows if r['Status'].startswith('MANUAL')],
                codes_audited=len({r['LCSC_part'] for r in rows}),rows_audited=len(rows),
                connectors_with_library=sum(r['Checked_pins']>0 for r in connectors),
                connectors_without_library=[r['Designator'] for r in connectors if not r['Checked_pins']],
                scope='Centered functional pad rotations, connector wall direction, J113 absolute holes. Explicit manual gates for inconsistent or unavailable library geometry; live assembly acceptance untested.')
