"""Ensure the independent library audit rejects the user's previous CPL angles."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
from sexp import parse,find,find_all
from audit_placement_libraries import audit

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/release-candidate'


def main():
    baseline=ROOT/'research/orientation-baseline-CPL.csv'
    old={r['Designator']:r for r in csv.DictReader(baseline.open())}
    mapped={r['Upload_designator']:r for r in csv.DictReader((OUT/'jlcpcb-assembly/placement-map.csv').open())}
    for ref,m in mapped.items():
        m['Rotation_deg']=old[ref]['Rotation']
        m['Library_rotation_offset_deg']=str((float(old[ref]['Rotation'])-float(m['Native_rotation_deg']))%360)
    b=parse((ROOT/'wpc_power_driver_cost.kicad_pcb').read_text())[0]
    fps={next(p[2] for p in find_all(f,'property') if p[1]=='Reference'):f for f in find_all(b,'footprint')}
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='jlc-placement-regression-') as tmp:
        out=Path(tmp);(out/'jlcpcb-assembly').mkdir()
        audit(out,ROOT,fps,mapped,old,lambda ok,msg:None if ok else rejected.append(msg))
    required=['U1','U2','U3','U9','U19','Q20','Q83','Q91','Q9','D105','J110','J111']
    passed=all(any(msg.startswith(ref+' ') for msg in rejected) for ref in required)
    report=dict(passed=passed,baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
                tested_references=required,rejected_checks=len(rejected),rejections=rejected,
                scope='Actual archived previous CPL angles rejected by functional pad and friction-wall geometry audit; generated CSVs isolated in a temporary directory.')
    (OUT/'reports/placement-regression-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Prior-CPL regression:',passed,len(rejected),'checks reject previous incorrect orientations')
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
