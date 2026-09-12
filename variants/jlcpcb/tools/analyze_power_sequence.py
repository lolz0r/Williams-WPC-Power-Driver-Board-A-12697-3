"""Expose full-cycle recovery ripple, separately from the original SPICE screens."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/prespin/power-sequence'
cases=[]
for path in sorted(OUT.glob('*_loss_restart_*.csv')):
 d=np.loadtxt(path,skiprows=1);report=json.loads(path.with_suffix('.json').read_text())
 assert report['checks']['sim_end']['passed']
 sample=d[d[:,0]>=.095];t=sample[:,0];v=sample[:,1];lo,hi=(4.95,5.25) if report['rail']=='5v' else (11.4,12.6)
 cases.append(dict(name=path.stem,csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),window_s=[float(t[0]),float(t[-1])],output_min_V=float(v.min()),output_max_V=float(v.max()),output_average_V=float(np.trapezoid(v,t)/(t[-1]-t[0])),raw_min_V=float(sample[:,2].min()),time_above_upper_screen_s=float(np.trapezoid((v>hi).astype(float),t)),time_below_lower_screen_s=float(np.trapezoid((v<lo).astype(float),t)),screen_band_V=[lo,hi]))
assert len(cases)==4,'Wait for all four AC-interruption runs to finish'
result=dict(cases=cases,scope='Last 25 ms after restart: three complete 120 Hz rectified cycles at 60 Hz mains, from saved 1 us interpolated samples. Supplementary observations, not a replacement or relaxation of the original adaptive-step checks.',limitations=['Typical model and assumed transformer/load; not measured voltage limits','1 us interpolation may omit very short extrema; primary reports preserve adaptive-step extrema','Original final-five-millisecond averages are retained; this adds a complete-cycle view'])
(OUT/'recovery-ripple.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
