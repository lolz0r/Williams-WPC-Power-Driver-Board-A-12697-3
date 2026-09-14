"""Closed-form RL conduction cross-check, independent of SPICE integration.
Switching/reverse-recovery losses are deliberately not included in this calculation.
"""
import argparse,bisect,hashlib,json,math
from pathlib import Path
from replay_rom import read_edges
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'output/verification/revision'
def segment(i0,t,resistance,inductance,on,mos=.015,vf=1.):
 r=resistance+mos if on else resistance
 tau=inductance/r;inf=86/r if on else -vf/r
 active=t if on else min(t,tau*math.log1p(i0*r/vf))
 delta=i0-inf;e=math.exp(-active/tau)
 area=inf*active+delta*tau*(-math.expm1(-active/tau))
 square=inf*inf*active+2*inf*delta*tau*(-math.expm1(-active/tau))+delta*delta*tau/2*(-math.expm1(-2*active/tau))
 end=max(0.,inf+delta*e) if active==t else 0.
 return end,max(0.,area),max(0.,square),max(i0,end)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--gameplay',action='store_true');args=parser.parse_args()
 directory=ROOT/'output/verification/prespin' if args.gameplay else REV
 sources=[('replay-gameplay',ROOT/'output/verification/pinmame/gameplay-prespin/bus.csv')] if args.gameplay else [('replay-diagnostics',ROOT/'output/verification/mame/diagnostics/bus.csv')]
 results=[]
 for folder,trace in sources:
  report=json.loads((directory/folder/'results.json').read_text());assert report['passed']
  assert report['trace_sha256']==hashlib.sha256(trace.read_bytes()).hexdigest()
  edges,last=read_edges(trace)
  for c in report['cases']:
   start,end=c['window_s'];history=max(0.,start-.2);seq=edges[c['channel']];times=[t for t,s in seq]
   splits=sorted({history,start,end,*[t for t,s in seq if history<t<end]});i=86/c['coil_ohm'] if history else 0.;energy=charge=0.;peak=0.
   for left,right in zip(splits,splits[1:]):
    state=seq[bisect.bisect_right(times,left)-1][1]
    i,area,square,pk=segment(i,right-left,c['coil_ohm'],c['coil_H'],state)
    if left>=start:
     peak=max(peak,pk)
     if state:energy+=square*.015
     else:charge+=area
   average=energy/(end-start);diode=charge/(end-start)
   checks={'conduction_only_temperature':50+average*62<=125,'forward_diode_average':diode<=3,'coil_current_bound':peak<=86/c['coil_ohm']*(1+1e-9)}
   results.append(dict(trace=folder,channel=c['channel'],window_s=[start,end],conduction_only_W=average,conduction_only_temperature_C=50+average*62,forward_diode_average_A=diode,coil_peak_A=peak,spice_total_temperature_C=c['checks']['tj_repeating']['value'],checks=checks,passed=all(checks.values())))
 report=dict(passed=all(c['passed'] for c in results),cases=results,assumptions={'rail_V':86,'hot_mos_R_ohm':.015,'flyback_Vf_V':1.,'ambient_C':50,'Rtheta_C_W':62},limitations=['Exact segment solution of fixed R/L and piecewise constant drive, using actual ROM edge times','Conduction-only check: omits switching, reverse recovery, mutual heating, wire inductance and real coil saturation','Low constant diode drop increases freewheel persistence; a sensitivity assumption, not a guaranteed diode bound','Independent conduction cross-check; transient sensitivity and physical SOA tests remain separate'])
 report['trace_sha256']=hashlib.sha256(trace.read_bytes()).hexdigest()
 (directory/'replay-rl-bound.json').write_text(json.dumps(report,indent=2)+'\n')
 print('RL conduction checks:',len(results),'passed:',report['passed']);print('Maximum conduction-only temperature',max(c['conduction_only_temperature_C'] for c in results))
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
