"""Datasheet-based averaged supply tests for the JLC-100 TPS552872-Q1 circuits.

This is an engineering average model, NOT TI's encrypted switching model.
It exercises the actual output filter, feedback/compensation, AC bridge and
reservoir, UVLO, startup ramp, current limits, and load/power sequences.
It cannot validate switching transitions, PFM bursts, EMI or silicon timing.
"""
import argparse
import cmath
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prototype_power_spec import ROOT, RAILS
from ngspice_lib import NgSpice
from corners import measurements


def phase_sweep(rail,rc):
    five=rail['ref']=='U20';vout=1.2*(1+rail['fb_ohm']/(2100 if five else 2000))
    current=3 if five else .75;load=vout/current;cases=[]
    for vin,cap_scale,esr,gm_scale,r_scale,cc_scale,cp_scale in itertools.product(
            [6.4,9,15] if five else [8.4,11,15,21], [.8,1.2], [.028,.056], [.8,1.2], [.99,1.01], [.75,1.25], [.95,1.05]):
        capacitance=660e-6*cap_scale+10e-6
        effective_esr=esr+rail['shunt_ohm'];d=max(0,1-vin/vout)
        frequencies=[10**(i/90) for i in range(541)];gain=[];phase=[]
        for f in frequencies:
            s=2j*math.pi*f
            z=1/(1/(rc*r_scale+1/(s*rail['cc_f']*cc_scale))+s*rail['cp_f']*cp_scale+1/1e9)
            error=.000190*gm_scale*z*1.2/vout
            if d:
                power=load*(1-d)/(2*.055)*(1+s*effective_esr*capacitance)*(1-s*10e-6/(load*(1-d)**2))/(1+s*load*capacitance/2)
            else:power=load/.055*(1+s*effective_esr*capacitance)/(1+s*load*capacitance)
            # Explicit sensitivity assumption for the unspecified inner-loop
            # bandwidth and sampling delay; not a guaranteed IC parameter.
            loop=error*power/(1+s/(2*math.pi*395000/10))*cmath.exp(-s/(2*395000))
            gain.append(20*math.log10(abs(loop)));p=math.degrees(cmath.phase(loop))
            if phase:
                while p-phase[-1]>180:p-=360
                while p-phase[-1]<-180:p+=360
            phase.append(p)
        cross=next((i for i in range(1,len(gain)) if gain[i-1]>=0>gain[i]),None)
        if cross:
            k=gain[cross-1]/(gain[cross-1]-gain[cross]);fc=frequencies[cross-1]*(frequencies[cross]/frequencies[cross-1])**k
            pm=180+phase[cross-1]+k*(phase[cross]-phase[cross-1])
        else:fc=pm=None
        pc=next((i for i in range(1,len(phase)) if phase[i-1]>=-180>phase[i]),None)
        gm=None if pc is None else -(gain[pc-1]+(-180-phase[pc-1])/(phase[pc]-phase[pc-1])*(gain[pc]-gain[pc-1]))
        cases.append(dict(vin_V=vin,capacitance_scale=cap_scale,bulk_pair_ESR_ohm=esr,gm_scale=gm_scale,
                          resistor_scale=r_scale,compensation_capacitance_scale=cc_scale,pole_capacitance_scale=cp_scale,crossover_Hz=fc,phase_margin_deg=pm,gain_margin_dB=gm,
                          passed=pm is not None and pm>=45 and (gm is None or gm>=10) and fc<39500))
    return dict(cases=cases,passed=all(c['passed'] for c in cases),
                interpretation='CCM averaged-loop screening. PFM/light-load operation and internal-loop assumptions require first-article measurement.')


def deck(rail,scenario,rc,step_us,frequency,line,cap_scale=.8,reference_scale=1,bulk_esr=.022,gm_scale=1):
    five=rail['ref']=='U20';vout=1.2*(1+rail['fb_ohm']/(2100 if five else 2000))
    full=3 if five else .75;bottom=2100 if five else 2000;cap=7520e-6 if five else 15040e-6
    en_top,en_bottom=(118e3,29.4e3) if five else (130e3,20e3)
    on=1.23*(1+en_top/en_bottom);hys=5e-6*en_top;ilim=.05/rail['shunt_ohm']
    env='1' if scenario in ['startup','load_step'] else '(time<25m || time>85m)' if scenario=='loss_restart' else '(time>25m)'
    loading=f'{full}' if scenario in ['startup','loss_restart'] else f'(.02+({full}-.02)*(time>25m && time<55m))' if scenario=='load_step' else '.02'
    pre=vout if scenario=='prebiased' else 0
    return f'''JLC-100 {rail['ref']} {scenario}; engineering averaged controller, not TI vendor model
.include {ROOT/'tools/spice/models.lib'}
Vsecondary sp sn SIN(0 {(12.7 if five else 18.8)*line} {frequency})
Bsource acdrive sn V=v(sp,sn)*{env}
Rwind1 acdrive ap .05
Rwind2 sn an .05
D1 ap vin J100MBR
D2 an vin J100MBR
D3 0 ap J100MBR
D4 0 an J100MBR
Rreservoir vin storage .05
Creservoir storage 0 {cap}
Rcin vin cin .005
Ccin cin 0 20u
{'Rlamp vin 0 2.5' if not five else 'Rrawbleed vin 0 5000'}
Venable esrc 0 1
Senable esrc enable vin 0 SUV
.model SUV SW(Ron=1 Roff=1e12 Vt={on-hys/2} Vh={hys/2})
Renable enable 0 1k
Cenable enable 0 1n
Css ss 0 1 IC=0
Bsoft 0 ss I=ternary_fcn(v(enable)>.5,ternary_fcn(v(ss)<{1.2*reference_scale},{1.2*reference_scale}/.0036,0),-v(ss)/10u)
Rfbtop out fb {rail['fb_ohm']}
Rfbbottom fb 0 {bottom}
Berror 0 comp I=ternary_fcn(v(enable)>.5,min(max({.000190*gm_scale}*(v(ss)-v(fb)),-20u),60u),0)
Bcompclamp comp 0 I=max(v(comp)-1.15,0)-max(.6-v(comp),0)+ternary_fcn(v(enable)<.5,(v(comp)-.6),0)
Rcomp comp cc {rc}
Ccomp cc 0 {rail['cc_f']} IC=.6
Cpole comp 0 {rail['cp_f']} IC=.6
Rgain comp 0 1e9
Bcommand command 0 V=min(max((v(comp)-.6)/.055,0),3.3)*v(enable)
Rinner command il 1
Cinner il 0 4u
Bstage 0 reg I=min(max(v(il),0)*min(1,max(v(vin),0)/max(v(reg),.8)),{ilim})*v(enable)
Binput vin 0 I=min(max(v(il),0)*min(1,max(v(vin),0)/max(v(reg),.8)),{ilim})*v(enable)*max(v(reg),0)/max(v(vin),3)/.9
Rlocal reg clocal .005
Clocal clocal 0 10u IC={pre}
Rsense reg out {rail['shunt_ohm']}
Rbulk out cbulk {bulk_esr}
Cbulk cbulk 0 {660e-6*cap_scale} IC={pre}
Bload out 0 I={loading}*tanh(v(out)/.1)
Routbleed out 0 100k
.ic v(comp)=.6 v(cc)=.6 v(reg)={pre} v(out)={pre}
.options method=gear reltol=.0001 abstol=1n vntol=1u klu itl4=200 minbreak=1p
.save v(vin) v(reg) v(out) v(il) v(comp) v(ss) v(enable) i(Bsource) @rsense[i]
.tran {step_us}u 120m 0 {step_us}u uic
.control
set numdgt=12
run
let sim_end=time[length(time)-1]
print sim_end
meas tran output_peak MAX v(out)
meas tran output_floor MIN v(out)
meas tran settled_min MIN v(out) from=105m to=120m
meas tran settled_max MAX v(out) from=105m to=120m
meas tran step_min MIN v(out) from=24m to=65m
meas tran step_max MAX v(out) from=24m to=65m
meas tran input_min MIN v(vin) from=105m to=120m
meas tran inductor_average_peak MAX v(il)
meas tran inductor_average_min MIN v(il)
meas tran shunt_current_peak MAX @rsense[i]
meas tran shunt_current_min MIN @rsense[i]
meas tran secondary_rms RMS i(Bsource) from=100m to=120m
.endc
.end
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--name',required=True)
    p.add_argument('--rc5',type=float,default=33000);p.add_argument('--rc12',type=float,default=42200)
    p.add_argument('--step-us',type=float,default=2);p.add_argument('--phase-only',action='store_true');p.add_argument('--fb5',type=float,default=6650);p.add_argument('--rails',default='U20,U21')
    p.add_argument('--cp12',type=float,default=1e-9);p.add_argument('--cp5',type=float,default=680e-12);p.add_argument('--cap-scale',type=float,default=.8);p.add_argument('--reference-scale',type=float,default=1);p.add_argument('--bulk-esr',type=float,default=.028);p.add_argument('--gm-scale',type=float,default=1)
    a=p.parse_args();RAILS[0]['fb_ohm']=a.fb5;RAILS[0]['cp_f']=a.cp5;RAILS[1]['cp_f']=a.cp12;rails=[r for r in RAILS if r['ref'] in a.rails.split(',')];out=ROOT/'output/verification/prototype-readiness'/a.name
    out.mkdir(parents=True,exist_ok=True);assert not (out/'results.json').exists(),'Preserve prior trials'
    loops={r['ref']:phase_sweep(r,a.rc5 if r['ref']=='U20' else a.rc12) for r in rails}
    cases=[]
    if not a.phase_only:
        ng=NgSpice()
        for rail,scenario,frequency,line in itertools.product(rails,['startup','load_step','loss_restart','prebiased'],[50,60],[.9,1.1]):
            name=f"{rail['ref']}_{scenario}_{frequency}Hz_{line}line";src=deck(rail,scenario,a.rc5 if rail['ref']=='U20' else a.rc12,a.step_us,frequency,line,a.cap_scale,a.reference_scale,a.bulk_esr,a.gm_scale)
            path=out/(name+'.cir');path.write_text(src);ng.cmd('destroy all');log=ng.run_deck(str(path));path.with_suffix('.log').write_text('\n'.join(log)+'\n')
            v=measurements(log);errors=[s for s in log if s.startswith('stderr') and not s.startswith('stderr Note:')]
            complete=not errors and abs(v.get('sim_end',0)-.12)<1e-8
            five=rail['ref']=='U20';lo,hi=(4.9,5.2) if five else (11.4,12.6)
            checks=dict(inductor_limit=complete and v['inductor_average_peak']<=3.301,completed=complete,settled=complete and v['settled_min']>=lo and v['settled_max']<=hi,
                        no_overvoltage=complete and v['output_peak']<=(5.25 if five else 12.6),
                        no_negative_output=complete and v['output_floor']>=-.05)
            if scenario=='load_step':checks['load_step']=complete and v['step_min']>=(4.75 if five else 11.4) and v['step_max']<=(5.25 if five else 12.6)
            cases.append(dict(name=name,measurements=v,checks=checks,passed=all(checks.values()),errors=errors,deck_sha256=hashlib.sha256(src.encode()).hexdigest()))
            print(name,checks,flush=True)
    result=dict(passed=all(v['passed'] for v in loops.values()) and all(c['passed'] for c in cases),loops=loops,cases=cases,
        parameters=vars(a),pcb_sha256=hashlib.sha256((ROOT/'wpc_power_driver_cost.kicad_pcb').read_bytes()).hexdigest(),
        model_kind='Engineering averaged model; not a manufacturer switching-model validation',
        limitations=['TI public PSpice transient model is encrypted and was not run in ngspice',
                     'PFM burst ripple, MOSFET/body-diode commutation, switching overshoot and EMI are outside this model',
                     'The slow output constant-current loop is approximated by a hard stage-current ceiling; overload recovery is not a silicon prediction',
                     'Inner current-loop time constant 4 us, sampling delay and +/-20% gm are engineering sensitivities',
                     'Forward-only average power flow reflects the selected topology/mode; it is not independent reverse-blocking silicon proof',
                     'Input winding resistance and lamp load are assumptions; constant full lamp load is a stress case, not measured gameplay',
                     'Capacitances use conservative effective values; controller loop and loaded rails require first-article oscilloscope checks'])
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS' if result['passed'] else 'FAIL',flush=True)


if __name__=='__main__':main()
