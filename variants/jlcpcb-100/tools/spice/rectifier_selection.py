"""Compare a lower-loss 60 V rectifier with the existing 100 V design.
Manufacturer loss envelope is independent of the approximate 25 C electrical fit.
No vendor SPICE model is claimed: ST's downloadable archive was inaccessible.
"""
import json,re,itertools,hashlib
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[1]/'output/verification/revision/rectifier-selection';OUT.mkdir(parents=True,exist_ok=True)
base=(HERE/'decks/bridge_loss.cir').read_text().replace('.include ../models.lib','.include '+str(HERE/'models.lib'))
base=base.replace('DSCH20100','DSCH3060').replace('0.425*','0.395*').replace('0.0088*','0.0047*')
base=base.replace('.options','* 25 C approximate maximum-Vf fit: 0.515 V @15 A, 0.590 V @30 A.\n.model DSCH3060 D(Is=6e-7 n=1.05 Rs=.0038 Cjo=3n Tt=0 Bv=60 Ibv=1u Eg=.69 Xti=2)\n.options',1)
ng=NgSpice();results=[]
for frequency,scale in itertools.product((50,60),(.9,1,1.1)):
 s=re.sub(r'SIN\(0 ([\d.]+) 60\)',lambda m:f'SIN(0 {float(m[1])*scale} {frequency})',base)
 s=s.replace('from=233.33m','from=240m' if frequency==50 else 'from=250m');s=re.sub(r'^wrdata.*$','',s,flags=re.M)
 extra=[]
 for suffix in ('18a','20a','5a','12b'):
  extra.append(f'let reverse_{suffix}=v(dc{suffix})-v(ab{suffix})\nmeas tran vr_{suffix} MAX reverse_{suffix}')
 s=s.replace('.endc','\n'.join(extra)+'\n.endc');name=f'f{frequency}_line{scale}';p=OUT/(name+'.cir');p.write_text(s);ng.cmd('destroy all');log=ng.run_deck(str(p));(OUT/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
 losses={k:v.get('pd_'+k) for k in ('18a','20a','5a','12b')}
 reverse={k:v.get('vr_'+k) for k in losses};errors=[l for l in log if l.startswith('stderr') and 'Warning' not in l]
 result=dict(name=name,losses_W_per_package=losses,reverse_peaks_V=reverse,errors=errors,passed=not errors and all(x is not None and 0<x<4 for x in losses.values()) and all(x is not None and x<48 for x in reverse.values()))
 results.append(result);print(result,flush=True)
peak={k:max(r['losses_W_per_package'][k] for r in results) for k in results[0]['losses_W_per_package']}
# Upper leakage sensitivity deliberately uses the 100 mA maximum specified at
# full 60 V and 125 C, despite the much lower actual reverse voltage.
# Conservatively apply it for half a cycle at peak reverse voltage.
leakage={k:max(r['reverse_peaks_V'][k] for r in results)*.1*.5 for k in peak}
report=dict(cases=results,peak_conduction_W=peak,full_VRRM_leakage_bound_W=leakage,
 sources=['https://www.st.com/resource/en/datasheet/stps30m60s.pdf','https://estore.st.com/en/stps30m60st-cpn.html'],
 limitations='Loss equation at hot junction; approximate cold-Vf fit sets currents. Real transformer impedance and leakage at operating voltage need measurement. The 60 V selection requires controlled secondary transient peaks below 48 V; normal line peaks alone are insufficient surge qualification.',passed=all(r['passed'] for r in results))
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
