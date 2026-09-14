"""Create standalone plots from completed simulation data, not bench measurements."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/wpc-matplotlib')
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/verification/prespin/power-sequence'
groups={'normal-sequences':['5v_loss_restart_3A_250n','12v_loss_restart_0.75A_250n','12v_loss_restart_0.02A_250n'],'stress-and-precharge':['12v_loss_restart_2A_250n','5v_precharged_output_1A_250n','12v_precharged_output_0.75A_250n']}
for group,names in groups.items():
 fig,axes=plt.subplots(3,2,figsize=(11,8),layout='constrained')
 for row,name in enumerate(names):
  report=json.loads((OUT/(name+'.json')).read_text());data=np.loadtxt(OUT/(name+'.csv'),skiprows=1);time=data[:,0]*1000
  stop=1 if report['scenario']=='precharged_output' else 120;keep=time<=stop;vax,iax=axes[row]
  vax.plot(time[keep],data[keep,2],lw=.8,label='Raw input');vax.plot(time[keep],data[keep,1],lw=.9,label='Regulated output')
  iax.plot(time[keep],data[keep,4],lw=.45,color='#654194')
  for ax in [vax,iax]:
   ax.set_xlim(0,stop);ax.grid(alpha=.22);ax.set_xlabel('Time (ms)')
   if stop==120:ax.axvspan(25,85,color='gray',alpha=.12)
  vax.set_ylabel('Voltage (V)');iax.set_ylabel('Inductor current (A)');vax.legend(loc='upper right',fontsize=8)
  title=f"{report['rail']} / {report['output_load_A']:g} A / "+('precharged output' if stop==1 else 'AC loss and restart')
  vax.set_title(title,fontsize=10);m=report['measurements'];iax.set_title(f"Screen: {'PASS' if report['passed'] else 'FAIL'}; adaptive-step Imin {m['inductor_min']:.3f} A",fontsize=10)
 fig.suptitle('TI switching-model prediction — not a physical measurement\n'+('Gray interval: AC source interrupted; reservoirs discharge through the circuit' if group=='normal-sequences' else '2 A exceeds the +12 V fuse rating; precharged outputs are unqualified backfeed cases'),fontsize=11)
 fig.savefig(OUT/(group+'.png'),dpi=170);plt.close(fig)
print('Power-sequence plots written')
