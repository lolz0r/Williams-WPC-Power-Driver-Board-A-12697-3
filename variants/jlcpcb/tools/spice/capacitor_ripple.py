"""Reservoir-capacitor RMS ripple and ESR sensitivity, with explicit assumptions.
The two BR1 capacitors have independent +/-20% capacitance and 2:1 ESR corners.
Ratings are compared without unsubstantiated ambient-temperature uprating.
"""
import itertools
import json
import re
import argparse,hashlib
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'output/verification/revision/capacitor-ripple'
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=OUT);ap.add_argument('--method',choices=['trap','gear'],default='gear');ap.add_argument('--maxstep',default='10u');ap.add_argument('--case');ap.add_argument('--klu',action='store_true');args=ap.parse_args();OUT=args.output
OUT.mkdir(parents=True,exist_ok=True)
base=(HERE/'decks/bridge_loss.cir').read_text().split('.options')[0]
base=base.replace('.include ../models.lib','.include '+str(HERE/'models.lib'))
# Capacitor identification and catalogue rated ripple at 120 Hz.
spec={'18a':(['C6','C7'],10000,7.89),'18b':(['C6','C7'],10000,7.89),
      '20a':(['C11'],10000,7.89),'20b':(['C11'],10000,7.89),
      '5a':(['C5'],10000,7.89),'12a':(['C30'],10000,7.89)}
ng=NgSpice();results=[]
for frequency,line,esr,imbalance in itertools.product((50,60),(1.,1.1),(.02,.05,.1),(False,True)):
 name=f'f{frequency}_line{line}_esr{esr}_imbalance{imbalance}'
 if args.case and name!=args.case:continue
 source=re.sub(r'SIN\(0 ([\d.]+) 60\)',lambda m:f'SIN(0 {float(m[1])*line} {frequency})',base)
 commands=[];limits={}
 for suffix,(refs,cap,rating) in spec.items():
  replacements=[]
  for index,ref in enumerate(refs):
   tag=suffix+'_'+ref.lower()
   capacitance=cap*((.8 if index==0 else 1.2) if imbalance else 1.)
   resistance=esr*((2 if index==0 else 1) if imbalance else 1.)
   replacements.extend([f'Resr{tag} dc{suffix} r{tag} {resistance}',f'Vc{tag} r{tag} c{tag} 0',f'C{tag} c{tag} 0 {capacitance}u'])
   commands.append(f'meas tran rms_{tag} RMS i(Vc{tag}) from=800m to=1')
   commands.append(f'meas tran dc_{tag} AVG i(Vc{tag}) from=800m to=1')
   # 100 Hz factor 0.9 conservatively bounds the manufacturer 2016 page 16 curve.
   limits['rms_'+tag]=dict(ref=ref,rating_A=rating*(.9 if frequency==50 else 1),ESR_ohm=resistance,capacitance_uF=capacitance,
                           load='fuse-limit informational' if suffix=='20b' else 'design load')
  source=re.sub(r'^C'+suffix+r' .*$', '\n'.join(replacements),source,flags=re.M)
 source+=f'\n.options reltol=0.002 method={args.method}'+(' klu itl4=100' if args.klu else '')+f'\n.tran {args.maxstep} 1 0 {args.maxstep} uic\n.control\nrun\n'+'\n'.join(commands)+'\n.endc\n.end\n'
 name=f'f{frequency}_line{line}_esr{esr}_imbalance{imbalance}'
 deck=OUT/(name+'.cir');deck.write_text(source)
 ng.cmd('destroy all');log=ng.run_deck(str(deck));values=measurements(log)
 (OUT/(name+'.log')).write_text('\n'.join(log)+'\n')
 errors=[s for s in log if s.startswith('stderr') and 'Warning' not in s]
 checks={k:dict(s,measured_A=values.get(k),passed=k in values and 0<=values[k]<=s['rating_A']) for k,s in limits.items()}
 results.append(dict(name=name,frequency_Hz=frequency,line_scale=line,checks=checks,errors=errors,deck_sha256=hashlib.sha256(deck.read_bytes()).hexdigest(),
                     passed=not errors and all(c['passed'] for c in checks.values() if c['load']=='design load')))
 print(name, 'PASS' if results[-1]['passed'] else 'FAIL',flush=True)
report=dict(cases=results,passed=bool(results) and all(r['passed'] for r in results),method=args.method,maxstep=args.maxstep,klu=args.klu,
 limitations='Approximate rectifiers, assumed transformer resistance from bridge_loss.cir, ESR sweep is sensitivity rather than vendor tolerance. 1 s settling and integer mains periods. TDK parts require measured LOCAL ambient <=60 C for 7.89 A limit for all five 10,000 uF reservoirs. 100 Hz factor 0.9 conservatively bounds the TDK B41252 2016 page 16 curve (100 Hz normalized to 1, 120 Hz approximately 1.01). Fuse-limit load is informational, not a sustained-load qualification.',
 sources=['https://product.tdk.com/en/search/capacitor/aluminum-electrolytic/snap_multi_large/info?part_no=B41252A7109M000'])
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)
