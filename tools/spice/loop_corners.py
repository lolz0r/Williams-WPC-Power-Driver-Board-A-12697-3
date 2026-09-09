"""TPS54360B datasheet small-signal loop sensitivity; not a measured Bode plot.
Equations 11-14 / 48-51: gmPS=12 A/V, gmEA=350 uA/V. Adds a half-cycle delay
and a pole at fsw/2 as conservative sensitivity terms, not a vendor AC model.
"""
import itertools
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path('output/verification/revision/loop');OUT.mkdir(parents=True,exist_ok=True)
f=np.logspace(0,6.2,4000);s=2j*np.pi*f;fsw=400e3;cases=[]
fig,axes=plt.subplots(2,1,sharex=True,figsize=(9,7))
for name,vo,rc,cc,cp,loads in [('U20',5.105,33.2e3,33e-9,470e-12,(.5,1.5,3.)),('U21',12.,42.2e3,100e-9,390e-12,(.5,1.,2.))]:
 minimum=(180,None)
 for load,cap,esr,rscale,cscale,pscale,gscale in itertools.product(loads,(.8,1.2),(.01,.0225,.0675),(.99,1.01),(.9,1.1),(.95,1.05),(.75,1.25)):
  co=660e-6*cap+5e-6 # derated ceramic, explicit assumption
  rl=vo/load
  zout=1/(1/rl+1/(esr+1/(s*co)))
  zcomp=1/(s*cp*pscale+1/(rc*rscale+1/(s*cc*cscale)))
  transfer=350e-6*zcomp*12*gscale*zout*(.8/vo)/(1+s/(2*np.pi*fsw/2))*np.exp(-s/(2*fsw))
  gain=20*np.log10(abs(transfer));phase=np.unwrap(np.angle(transfer))*180/np.pi
  crossings=np.flatnonzero((gain[:-1]>=0)&(gain[1:]<0));assert len(crossings)==1,'Unexpected loop crossings'
  i=crossings[0];frac=gain[i]/(gain[i]-gain[i+1]);fc=float(np.exp(np.log(f[i])*(1-frac)+np.log(f[i+1])*frac));pm=float(180+phase[i]*(1-frac)+phase[i+1]*frac)
  pi=np.flatnonzero((phase[:-1]>-180)&(phase[1:]<=-180))
  if len(pi):
   j=pi[0];frac=(-180-phase[j])/(phase[j+1]-phase[j]);gm=float(-(gain[j]*(1-frac)+gain[j+1]*frac))
  else:gm=None
  result=dict(rail=name,load_A=load,Cout_F=co,ESR_ohm=esr,Rc_scale=rscale,Cc_scale=cscale,Cp_scale=pscale,gmPS_scale=gscale,crossover_Hz=fc,phase_margin_deg=pm,gain_margin_dB=gm,passed=pm>=45 and gm is not None and gm>=10 and fc<fsw/10)
  cases.append(result)
  if pm<minimum[0]:minimum=(pm,(gain,phase,result))
 gain,phase,r=minimum[1]
 axes[0].semilogx(f,gain,label=f"{name}: worst PM {r['phase_margin_deg']:.1f}°, GM {r['gain_margin_dB']:.1f} dB")
 axes[1].semilogx(f,phase)
axes[0].axhline(0,color='gray',lw=.8);axes[1].axhline(-180,color='gray',lw=.8)
axes[0].set_ylim(-80,100);axes[1].set_ylim(-270,0);axes[1].set_xlim(10,400e3)
axes[0].set_ylabel('Loop gain (dB)');axes[1].set_ylabel('Loop phase (degrees)');axes[1].set_xlabel('Frequency (Hz)')
axes[0].legend();axes[0].set_title('Datasheet CCM model with delay/pole sensitivity — unmeasured')
for a in axes:a.grid(True,which='both',alpha=.25)
fig.tight_layout();fig.savefig(OUT/'bode.png',dpi=180)
report=dict(cases=cases,passed=all(c['passed'] for c in cases),source='https://www.ti.com/lit/ds/symlink/tps54360b.pdf',limitations=['Linearized CCM model; excludes Eco-mode/DCM, saturation and nonlinear startup/faults','gmPS +/-25%, capacitor ESR range and added delay/pole are engineering sensitivity assumptions','Reference and divider DC accuracy evaluated separately','Vendor-model and physical injection measurement still required'])
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print('Cases',len(cases),'pass',sum(c['passed'] for c in cases),'min PM',min(c['phase_margin_deg'] for c in cases),'min GM',min(c['gain_margin_dB'] for c in cases))
raise SystemExit(0 if report['passed'] else 1)
