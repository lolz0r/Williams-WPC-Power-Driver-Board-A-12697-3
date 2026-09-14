"""Fresh JLC-100 rectifier conduction corners, with conservative hot loss bounds."""
import hashlib,itertools,json,re
from pathlib import Path
from ngspice_lib import NgSpice
from corners import measurements
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'output/verification/inventory-bridge-final';OUT.mkdir(parents=True,exist_ok=True);ng=NgSpice();cases=[]
base=(HERE/'decks/bridge_loss.cir').read_text().split('.options')[0].replace('.include ../models.lib',f'.include {HERE/"models.lib"}').replace('DSCH20100','J100MBR').replace('min(12.0, max(0.97*v(dc18a) - 0.5, 0))','12.0')
base=re.sub(r'(?m)^(D\S*(?:5[ab]|20[ab]|12[ab])\s+\S+\s+\S+\s+)J100MBR$',r'\1J100ON20H',base)
base+='\n.model J100ON20H D(Is=2e-7 N=1.05 Rs=.0045 Cjo=1400p Bv=100 Ibv=1m)\n'
for hz,line,scale in itertools.product([50,60],[.9,1.,1.1],[.8,1.2]):
 src=re.sub(r'SIN\(0 ([\d.]+) 60\)',lambda m:f'SIN(0 {float(m[1])*line} {hz})',base)
 src=re.sub(r'(?m)^(C(?:18|20|5|12)\w*\s+\S+\s+\S+\s+)([\d.]+)u$',lambda m:m[1]+str(float(m[2])*.94*scale)+'u',src)
 commands=['let sim_end=time[length(time)-1]','print sim_end']
 for k in ['18a','5a','20a','12b']:
  commands += [f'let i_{k}=i(Vs{k})',f'let ia_{k}=abs(i_{k})',f'meas tran iavg_{k} AVG ia_{k} from=.8 to=1',f'meas tran irms_{k} RMS i_{k} from=.8 to=1',(f'let pd_{k}=.50*1.1*iavg_{k}/2+.005*(1.1*irms_{k})*(1.1*irms_{k})/2' if k=='18a' else f'let pd_{k}=.55*iavg_{k}/2+.0045*irms_{k}*irms_{k}/2'),f'print pd_{k}']
 src+='\n.options method=gear reltol=.001 minbreak=1p klu\n.tran 10u 1 0 10u uic\n.control\nrun\n'+'\n'.join(commands)+'\n.endc\n.end\n';p=OUT/f'bridge_{hz}_{line}_{scale}.cir';p.write_text(src);ng.cmd('destroy all');log=ng.run_deck(str(p));p.with_suffix('.log').write_text('\n'.join(log)+'\n');v=measurements(log);errors=[x for x in log if x.startswith('stderr') and 'Note:' not in x];passed=not errors and abs(v.get('sim_end',0)-1)<1e-8 and all('pd_'+k in v for k in ['18a','5a','20a','12b']);cases.append(dict(name=p.stem,passed=passed,measurements=v,errors=errors,deck_sha256=hashlib.sha256(src.encode()).hexdigest()));print(p.stem,passed,{k:v for k,v in v.items() if k.startswith('pd')},flush=True)
(OUT/'results.json').write_text(json.dumps(dict(passed=len(cases)==12 and all(c['passed'] for c in cases),cases=cases,loss_bound='MOT hot: .50*1.1*Iavg/2+.005*(1.1*Irms)^2/2, from100/150C typical curves with added voltage/current margin; two legs paralleled. onsemi MBRB20H100CTT4G: .55*Iavg/2+.0045*Irms^2/2, line through specified maximum125C VF .64V/10A and .73V/20A per leg; dual legs paralleled. Low-current interpolation is an engineering bound; compare maximum forward curve. Deck-local lower-drop J100ON20H extracts more conservative charging currents. MOT bound remains based on typical curves.',limitations=['Continuous all-lamp and flasher bounds, unmeasured winding resistance. No fuse/transformer qualification.','This report supplies dissipation to a separate copper/heatsink thermal model; simulation completion alone does not qualify temperatures.'],model_sha256=hashlib.sha256((HERE/'models.lib').read_bytes()).hexdigest()),indent=2)+'\n')
