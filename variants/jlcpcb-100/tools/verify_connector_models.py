"""Read actual STEP solids and independently check every retained connector tail."""
import hashlib
import json
from pathlib import Path
from OCP.STEPControl import STEPControl_Reader
from OCP.IFSelect import IFSelect_RetDone
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Pnt
from sexp import parse,find,find_all
from connector_keys import KEYS

ROOT=Path(__file__).resolve().parents[1]


def main():
    board=parse((ROOT/'wpc_power_driver_cost.kicad_pcb').read_text())[0]
    checks=[];hashes={}
    for fp in find_all(board,'footprint'):
        props={p[1]:p[2] for p in find_all(fp,'property')};ref=props['Reference']
        if not ref.startswith('J') or not ref[1:].isdigit():continue
        model=find(fp,'model');path=Path(model[1].replace('${KIPRJMOD}',str(ROOT)))
        reader=STEPControl_Reader();assert reader.ReadFile(str(path))==IFSelect_RetDone;reader.TransferRoots()
        hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
        explorer=TopExp_Explorer(reader.OneShape(),TopAbs_SOLID);tails=[]
        while explorer.More():
            bounds=Bnd_Box();BRepBndLib.AddOptimal_s(explorer.Current(),bounds,False,False)
            a=(bounds.GetXMin(),bounds.GetYMin(),bounds.GetZMin(),bounds.GetXMax(),bounds.GetYMax(),bounds.GetZMax())
            if a[2]<-.5 and a[3]-a[0]<2 and a[4]-a[1]<2:
                tails.append(((a[0]+a[3])/2,(a[1]+a[4])/2))
            explorer.Next()
        expected=[];key=KEYS[int(ref[1:])]
        for pad in find_all(fp,'pad'):
            if not pad[1] or str(pad[1])==str(key):continue
            x,y=map(float,find(pad,'at')[1:3]);expected.append((x,-y))
        ok=len(tails)==len(expected) and all(any(abs(x-xx)<.02 and abs(y-yy)<.02 for xx,yy in tails) for x,y in expected)
        basis='Separate tail solids'
        if ref=='J111':
            # This library fuses plastic and metal into one solid. Probe the
            # actual solder-tail volume at every hole, including the absent key.
            ok=True;present=0;basis='Boolean probes of solder tails in fused STEP solid'
            for pad in find_all(fp,'pad'):
                if not pad[1]:continue
                x,y=map(float,find(pad,'at')[1:3])
                cube=BRepPrimAPI_MakeBox(gp_Pnt(x-.1,-y-.1,-2),.2,.2,.4).Shape()
                op=BRepAlgoAPI_Common(reader.OneShape(),cube);op.Build();assert op.IsDone()
                mass=GProp_GProps();BRepGProp.VolumeProperties_s(op.Shape(),mass)
                exists=abs(mass.Mass())>.01;present+=int(exists)
                ok=ok and exists == (str(pad[1])!=str(key))
            tails=[None]*present
        checks.append(dict(reference=ref,passed=ok,expected_posts=len(expected),step_posts_found=len(tails),omit_key=key,basis=basis))
    report=dict(passed=all(c['passed'] for c in checks),checks=checks,model_sha256=hashes,
                scope='Actual STEP tail-solid counts and native XY positions; only explicit OEM key removed. Unconnected non-key posts retained.')
    path=ROOT/'output/release-candidate/reports/connector-model-check.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print('STEP connector post check:',report['passed'],len(checks),'connectors',[c for c in checks if not c['passed']])
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
