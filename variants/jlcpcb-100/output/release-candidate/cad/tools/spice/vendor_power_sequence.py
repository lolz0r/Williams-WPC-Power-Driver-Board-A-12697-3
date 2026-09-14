"""TI switching model with actual rectifier/reservoir topology during loss/restart.
The mains source may stop, but cannot clamp the DC reservoir to an imposed voltage.
No model parameters or board protection circuits are changed by this experiment.
"""
import argparse,hashlib,json,math,re,time
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements

ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--rail',choices=['5v','12v'],required=True);ap.add_argument('--load',type=float);ap.add_argument('--scenario',choices=['loss_restart','precharged_output'],default='loss_restart');ap.add_argument('--maxstep',default='250n');ap.add_argument('--stop-ms',type=float,default=120);args=ap.parse_args()
out=ROOT/'output/verification/prespin/power-sequence';out.mkdir(parents=True,exist_ok=True)
is5=args.rail=='5v';vout=5.105 if is5 else 12.;load=args.load if args.load is not None else (3. if is5 else 2.)
name=f'{args.rail}_{args.scenario}_{load:g}A_{args.maxstep}';target=out/(name+'.cir')
original=ROOT/'output/verification/revision/vendor-buck'/('5v_vin15.34.cir' if is5 else '12v_vin20.69.cir')
source=original.read_text();source=source[:source.index('.save')]
source=re.sub(r'^Vin vin 0 .*\nRin vin vinf .02', '', source, flags=re.M)
source=re.sub(r'^Istep.*$', '', source, flags=re.M)
source=re.sub(r'^Rload vout 0 .*$',f'Rload vout 0 {vout/load:.12g}',source,flags=re.M)
# Lowest capacitance and low line; retained secondary/wiring resistance assumption.
cap=8000 if is5 else 16000;vpk=(12.7 if is5 else 18.8)*.9
if args.scenario=='loss_restart':
    waveform=f'{vpk}*sin(2*3.141592653589793*60*time)*((time<25m)?1:((time<85m)?0:min((time-85m)/100u,1)))'
else:
    waveform=f'{vpk}*sin(2*3.141592653589793*60*time)*min(time/100u,1)'
    source=source.replace('Cout1 vout c1 330u',f'Cout1 vout c1 330u IC={vout}').replace('Cout2 vout c2 330u',f'Cout2 vout c2 330u IC={vout}')
    source=source.replace('Cc3 vout 0 10u',f'Cc3 vout 0 10u IC={vout}')
source+=f'''
* AC secondary, winding resistance, four Schottky diodes and reservoir.
Bsecondary secp secn V={waveform}
Rsec1 secp acp .05
Rsec2 secn acn .05
Dbridge1 acp vinf DSCH20100
Dbridge2 acn vinf DSCH20100
Dbridge3 0 acp DSCH20100
Dbridge4 0 acn DSCH20100
Creservoir stored 0 {cap}u
Rreservoir stored vinf .05
Rrawbleed vinf 0 5000
'''
if not is5:source+='Rlamps vinf 0 2.5\n'
end=args.stop_ms/1000;uic=' uic' if args.scenario=='precharged_output' else ''
source+=f'''
.save v(vout) v(vinf) v(en) v(sw) i(L1) @d.xu.d_u8_d13[id]
.options reltol=.005 abstol=1u vntol=1m method=gear klu itl4=100
.tran 1u {end:g} 0 {args.maxstep}{uic}
.control
run
let sim_end=time[length(time)-1]
print sim_end
meas tran output_peak MAX v(vout)
meas tran output_min MIN v(vout)
meas tran inductor_peak MAX i(L1)
meas tran inductor_min MIN i(L1)
meas tran body_reverse_peak MAX @d.xu.d_u8_d13[id]
meas tran input_min MIN v(vinf)
meas tran before_loss AVG v(vout) from=20m to=24m
meas tran recovery AVG v(vout) from={end-.005:g} to={end:g}
set wr_singlescale
set wr_vecnames
linearize v(vout) v(vinf) v(en) i(L1)
wrdata {out/(name+'.csv')} v(vout) v(vinf) v(en) i(L1)
.endc
.end
'''
class ProgressSpice(NgSpice):
    def _send_char(self,s,i,u):
        result=super()._send_char(s,i,u)
        if b'Reference value' in s:
            (out/(name+'.progress')).write_text(s.decode(errors='replace')+'\n')
        return result
target.write_text(source);ng=ProgressSpice();ng.cmd('set ngbehavior=ps');start=time.monotonic();log=ng.run_deck(str(target));elapsed=time.monotonic()-start
(out/(name+'.log')).write_text('\n'.join(log)+'\n');v=measurements(log)
limits={'output_peak':(0,5.25 if is5 else 12.6),'output_min':(-.3,13),'inductor_peak':(0,10),'inductor_min':(-1,10),'recovery':(4.95,5.2) if is5 else (11.4,12.6),'sim_end':(end-1e-8,end+1e-8)}
if args.scenario=='loss_restart':limits['before_loss']=(4.95,5.2) if is5 else (11.4,12.6)
checks={k:dict(value=v.get(k),min=lo,max=hi,passed=k in v and lo<=v[k]<=hi) for k,(lo,hi) in limits.items()}
errors=[l for l in log if l.startswith('stderr') and 'Warning' not in l and not l.startswith('stderr Note:')]
report=dict(name=name,rail=args.rail,scenario=args.scenario,output_load_A=load,elapsed_s=elapsed,measurements=v,checks=checks,errors=errors,passed=not errors and all(c['passed'] for c in checks.values()),deck_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),base_deck_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),reservoir_uF=cap,secondary_peak_V=vpk,raw_lamp_load_ohms=None if is5 else 2.5,limitations=['Typical TI switching model with approximate rectifiers, no board parasitics or thermal feedback','Low line / minus 20 percent reservoir; actual transformer impedance remains to be measured','Reverse-current bound of 1 A is an engineering screening threshold, not a manufacturer guarantee of internal body-diode SOA','Short-circuit survival and arbitrary external backfeed are not qualified by a passing loss/restart case'])
(out/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
