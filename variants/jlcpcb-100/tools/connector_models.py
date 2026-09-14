"""Regenerate only selected TE/Molex connector envelopes, preserving native PCB.

OEM Williams assembly drawing page 61 controls the inward friction wall.
TE drawings 640445 AD7 and 640456 W3 control body and post dimensions.
Molex 41791 supplier solids and existing F.Fab control the lock-lip envelope.
These are simplified envelopes, not exact mold geometry or a fit certification.
"""
import hashlib
import json
from pathlib import Path
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Compound
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone
from OCP.gp import gp_Pnt
from sexp import parse, find, find_all
from connector_keys import KEYS

ROOT = Path(__file__).resolve().parents[1]


def box(x, y, z, w, d, h):
    return BRepPrimAPI_MakeBox(gp_Pnt(x, y, z), w, d, h).Shape()


def generate():
    board = parse((ROOT/'wpc_power_driver_cost.kicad_pcb').read_text())[0]
    rows, written = [], set()
    for fp in find_all(board, 'footprint'):
        props = {p[1]: p[2] for p in find_all(fp, 'property')}
        code, ref = props.get('JLCPCB Part'), props['Reference']
        te = code in {'C86500','C305801','C305802','C592598','C94118'}
        molex = code in {'C240823','C240824','C505166'}
        if not (te or molex):
            continue
        pads = [p for p in find_all(fp, 'pad') if p[1]]
        key = KEYS[int(ref[1:])]
        small = code == 'C94118'
        pitch, post = (2.54,.64) if small else (3.96,1.14)
        n = len(pads)
        shapes = []
        if te:
            # STEP Cartesian Y is opposite footprint local Y. Lock faces -Y.
            back, front, base, top, tail, tip = ((-3.175,2.54,2.54,7.747,3.556,10.033)
                if small else (-4.572,3.048,3.175,10.795,3.175,13.335))
            wall = .95  # simplified wall thickness; controlled outer envelope
            for first, count in ([(0,6),(6,6)] if ref == 'J115' else [(0,n)]):
                x = first*pitch-pitch/2
                shapes += [box(x,back,0,count*pitch,front-back,base),
                           box(x,back,base,count*pitch,wall,top-base)]
        else:
            back, front, base, top, tail, tip = -4.9,5.11,3.30,11.33,3.56,14.73
            length = (n-1)*pitch+3.81
            # Base body with lock lip toward -Y, matching the native fab outline.
            shapes += [box(-1.905,-2.41,0,length,7.52,base),
                       box(-1.905,back,0,length,2.49,top)]
        present = []
        for pad in pads:
            if str(pad[1]) == str(key):
                continue
            x, y = map(float, find(pad,'at')[1:3])
            shapes += [box(x-post/2,-y-post/2,-tail,post,post,tail),
                       box(x-post/2,-y-post/2,base,post,post,tip-base)]
            present.append(int(pad[1]))
        path = Path(find(fp,'model')[1].replace('${KIPRJMOD}',str(ROOT)))
        assert path.is_relative_to(ROOT/'models')
        if path not in written:
            builder = BRep_Builder(); compound = TopoDS_Compound(); builder.MakeCompound(compound)
            for s in shapes:
                builder.Add(compound,s)
            writer = STEPControl_Writer(); writer.Transfer(compound,STEPControl_AsIs)
            assert writer.Write(str(path)) == IFSelect_RetDone
            written.add(path)
        rows.append(dict(ref=ref,code=code,model=str(path.relative_to(ROOT)),
                         model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         omitted_key=key,present_posts=present,wall_local_cartesian_y='negative',
                         body_y_bounds=[back,front],plastic_height=top,post_tip_height=tip))
    report = dict(connectors=len(rows),unique_models=len(written),components=rows,
                  limitation='Simplified nominal envelopes; mold details, mating harness and manufacturing tolerances require physical review.')
    (ROOT/'output/verification/revision/connector-models.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Updated',len(written),'connector models for',len(rows),'native connectors')


if __name__ == '__main__':
    generate()
