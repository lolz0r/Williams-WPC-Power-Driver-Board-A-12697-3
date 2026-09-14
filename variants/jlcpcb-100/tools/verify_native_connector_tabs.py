"""Compare actual native STEP locking walls with the original Williams drawing.

The expected board directions are transcribed independently from the original
assembly drawing, not calculated from the current footprint rotation. Inspect
the centroid of a horizontal slice above each housing base to locate the wall.
J113 is separately excluded: the original was an unshrouded ribbon header and
the current simplified envelope does not model the replacement key notch.
"""
import hashlib
import json
import math
from pathlib import Path
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Pnt
from sexp import parse,find,find_all

ROOT=Path(__file__).resolve().parents[1]
# Native board top view: J101..103 at right, J104..112 at top,
# J114/J115 at left, J116..138 at bottom. Williams manual PDF page 61.
EXPECTED={**{n:'left' for n in range(101,104)},
          **{n:'down' for n in range(104,113)},
          114:'right',115:'right',
          **{n:'up' for n in range(116,139)}}


def main():
    pcb=ROOT/'wpc_power_driver_cost.kicad_pcb'
    board=parse(pcb.read_text())[0];rows=[]
    for fp in find_all(board,'footprint'):
        props={p[1]:p[2] for p in find_all(fp,'property')};ref=props['Reference']
        if not ref.startswith('J') or not ref[1:].isdigit() or int(ref[1:]) not in EXPECTED:continue
        model=find(fp,'model');path=Path(model[1].replace('${KIPRJMOD}',str(ROOT)))
        assert list(map(float,find(find(model,'offset'),'xyz')[1:]))==[0,0,0],ref+' review model offset'
        assert list(map(float,find(find(model,'rotate'),'xyz')[1:]))==[0,0,0],ref+' review model rotation'
        assert list(map(float,find(find(model,'scale'),'xyz')[1:]))==[1,1,1],ref+' review model scale'
        reader=STEPControl_Reader();assert reader.ReadFile(str(path))==IFSelect_RetDone;reader.TransferRoots();shape=reader.OneShape()
        bounds=Bnd_Box();BRepBndLib.AddOptimal_s(shape,bounds,False,False)
        clip=BRepPrimAPI_MakeBox(gp_Pnt(bounds.GetXMin()-1,bounds.GetYMin()-1,4),
                              bounds.GetXMax()-bounds.GetXMin()+2,bounds.GetYMax()-bounds.GetYMin()+2,1).Shape()
        op=BRepAlgoAPI_Common(shape,clip);op.Build();assert op.IsDone()
        mass=GProp_GProps();BRepGProp.VolumeProperties_s(op.Shape(),mass);assert mass.Mass()>1
        com=mass.CentreOfMass()
        pads=[list(map(float,find(p,'at')[1:3])) for p in find_all(fp,'pad') if p[1]]
        dx=com.X()-sum(p[0] for p in pads)/len(pads)
        dy=com.Y()+sum(p[1] for p in pads)/len(pads)
        at=list(map(float,find(fp,'at')[1:]));angle=at[2] if len(at)>2 else 0;a=math.radians(angle)
        wx,wy=dx*math.cos(a)-dy*math.sin(a),dx*math.sin(a)+dy*math.cos(a)
        direction=('right' if wx>0 else 'left') if abs(wx)>abs(wy) else ('up' if wy>0 else 'down')
        decisive=max(abs(wx),abs(wy))>.5 and max(abs(wx),abs(wy))>5*min(abs(wx),abs(wy))
        rows.append(dict(reference=ref,expected_original_wall=EXPECTED[int(ref[1:])],
                         measured_native_wall=direction,passed=decisive and direction==EXPECTED[int(ref[1:])],
                         wall_slice_offset_from_post_row_mm=[wx,wy],native_rotation_deg=angle,
                         model=str(path.relative_to(ROOT)),model_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    rows.sort(key=lambda r:int(r['reference'][1:]))
    report=dict(passed=len(rows)==37 and all(r['passed'] for r in rows),
                pcb_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),single_row_connectors_checked=len(rows),checks=rows,
                source='Williams STTNG Operations Manual PDF page 61 (printed 2-9), original A-12697-1 assembly drawing, visually rechecked 2026-09-14.',
                source_url='https://archive.org/download/arcademanual_Star_Trek_TNG_OPS/Star_Trek_TNG_OPS.pdf',
                source_sha256='5e89acb0e1fca7cb7e53e621869293e95bf97358e7b3b2d70f825c4204e2fb14',
                method='OpenCascade intersection of actual STEP solids with Z=4..5 mm slab above housing bases; transform centroid relative to native post row into board coordinates and compare independent original drawing direction.',
                exceptions={'J113':'Original unshrouded 2x17 header has no housing key notch. Replacement inward/right-facing notch is specified by assembly guide and pin-1 layout, not a copied original tab; simplified native STEP envelope omits notch detail. Physical ribbon socket key compatibility remains unverified.'},
                limitations=['Checks nominal native CAD, not the live JLCPCB assembly job or a physical board.',
                             'STEP models are simplified and this directional check does not establish mating geometry, mold tolerances or harness access.'])
    out=ROOT/'output/verification/revision/native-connector-tabs.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print('Native locking-wall audit:',report['passed'],len(rows),'single-row connectors;',[(r['reference'],r['measured_native_wall']) for r in rows if not r['passed']])
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
