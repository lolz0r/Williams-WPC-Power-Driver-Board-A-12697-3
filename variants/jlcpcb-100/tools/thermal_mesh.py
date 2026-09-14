"""Four-layer finite-volume thermal sensitivity model from filled copper geometry.
Approximate natural-convection/radiation boundary; temperatures require bench correlation.
Includes dielectric coupling, plated barrels and simultaneous bridge dissipation.
"""
import json
import argparse
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gap-aware',action='store_true');p.add_argument('--pitch',type=float,default=2.);p.add_argument('--bridge-dir',type=Path,default=Path('output/verification/inventory-bridge-final'));args=p.parse_args()
OUT=Path('output/verification/revision');j=json.loads((OUT/'copper_geometry.json').read_text())
h=args.pitch;xs=np.arange(h/2,449.2,h);ys=np.arange(h/2,272.9,h);xx,yy=np.meshgrid(xs,ys);ny,nx=xx.shape;size=nx*ny;board_size=4*size;total=board_size+4
names=['F.Cu','In1.Cu','In2.Cu','B.Cu'];depth=[.035,.2875,1.3125,1.565];ii=[];jj=[];gg=[]
def edges(a,b,g):ii.extend(np.ravel(a));jj.extend(np.ravel(b));gg.extend(np.ravel(np.broadcast_to(g,np.shape(a))))
for layer,name in enumerate(names):
 geom=unary_union([Polygon(p['outer'],p['holes']) for net in j['copper'].values() for p in net[name]])
 # Four sub-cell samples reduce single-pixel sensitivity of small pads/traces.
 fill=sum(shapely.contains_xy(geom,xx+dx,yy+dy).astype(float) for dx,dy in [(-.5,-.5),(-.5,.5),(.5,-.5),(.5,.5)])/4
 sheet=.4*j['copper_thickness_mm'][name]*fill+.0003*.4 # W/K per square, copper 400 and FR4 0.3 W/mK
 ids=np.arange(layer*size,(layer+1)*size).reshape(ny,nx)
 for axis,(a,b,ka,kb) in enumerate([(ids[:,:-1],ids[:,1:],sheet[:,:-1],sheet[:,1:]),(ids[:-1,:],ids[1:,:],sheet[:-1,:],sheet[1:,:])]):
  conductance=2*ka*kb/(ka+kb)
  if args.gap_aware:
   # Parallel strips across the shared cell width, series material samples along
   # the centre-to-centre path. Resolves narrow thermal breaks missed by area averaging.
   x=xx[:,:-1] if axis==0 else xx[:-1,:];y=yy[:,:-1] if axis==0 else yy[:-1,:]
   conductance=np.zeros_like(x);n=max(10,int(h/.1))
   for transverse in np.linspace(-.4*h,.4*h,5):
    resistance=np.zeros_like(x)
    for longitudinal in (np.arange(n)+.5)*h/n:
     copper=shapely.contains_xy(geom,x+(longitudinal if axis==0 else transverse),y+(transverse if axis==0 else longitudinal))
     k=.4*j['copper_thickness_mm'][name]*copper+.0003*.4
     resistance+=1/k/n
    conductance+=1/resistance/5
  edges(a,b,conductance)
 if layer:edges(ids-size,ids,.0003*h*h/(depth[layer]-depth[layer-1]))
barrels={(v['x'],v['y']):v['drill_mm'] for v in j['vias']}
barrels.update({(t['x'],t['y']):t['drill_mm'] for t in j['terminals'] if t['drill_mm']})
for (x,y),drill in barrels.items():
 k=min(ny-1,max(0,int(y/h)))*nx+min(nx-1,max(0,int(x/h)))
 for layer in range(3):edges([k+layer*size],[k+(layer+1)*size],.4*np.pi*drill*.020/(depth[layer+1]-depth[layer]))
# Conduction maxima across the twelve line/frequency/capacitance corners. Include
# MOT: two6mA legs at100V/125C. Onsemi: two3mA legs, bounding the manufacturer MAXIMUM reverse-current curve (<2mA through30V at125C); actual rails peak below27V.
# All four bridges and an additional 8 W board background operate simultaneously.
import re, hashlib
losses={}
for key in ('18a','5a','20a','12b'):
 values=[]
 for path in sorted(args.bridge_dir.glob('bridge_*.log')):
  match=re.search(r'stdout pd_'+key+r'\s*=\s*([-+\d.eE]+)',path.read_text())
  if match:values.append(float(match[1]))
 assert len(values)==12,(key,len(values))
 losses[key]=max(values)
source=np.zeros(total);source[:board_size]=8./board_size
sources={};lead_edges=[]
for number in range(101,117):
 ref=f'D{number}';group='18a' if number<=104 else '5a' if number<=108 else '20a' if number<=112 else '12b'
 rms={'18a':13.3,'5a':9.86,'20a':17.07,'12b':12.47}[group]
 peak=rms*1.1*np.sqrt(2)
 if number>104:assert peak<30,'onsemi3mA per-leg leakage curve bound requires VR<30V'
 power=losses[group]+(.012 if number<=104 else .006)*peak
 t=next(t for t in j['terminals'] if t['ref']==ref and t['pad']=='1')
 if number<=104:
  # Dedicated junction node: direct heatsink cooling plus separately swept lead
  # coupling. No copper-area Rtheta assigned to these through-hole devices.
  ids=np.array([board_size+number-101]);source[ids]+=power
  pad=min(ny-1,max(0,int(t['y']/h)))*nx+min(nx-1,max(0,int(t['x']/h)))
  lead_edges.append((int(ids[0]),pad))
 else:
  mask=(abs(xx-t['x'])<=4)&(abs(yy-t['y'])<=4)
  ids=np.flatnonzero(mask);source[ids]+=power/len(ids)
 sources[ref]=(ids,power)
i=np.array(ii);k=np.array(jj);g=np.array(gg);base=coo_matrix((np.r_[g,g,-g,-g],(np.r_[i,k,i,k],np.r_[i,k,k,i])),shape=(total,total)).tocsr()
results=[]
heatsink_rth=4.0+.5+24.4*1.25 # JC max, interface allowance, 25% sink derating
for lead_rth in (30.,1000.):
 for ambient_exchange in (3.,5.,8.,12.):
  diagonal=np.zeros(total);diagonal[:size]=ambient_exchange*1e-6*h*h;diagonal[3*size:board_size]=ambient_exchange*1e-6*h*h
  diagonal[board_size:]=1/heatsink_rth
  matrix=base+coo_matrix((diagonal,(np.arange(total),np.arange(total))),shape=(total,total)).tocsr()
  ai=np.array([a for a,b in lead_edges]);bi=np.array([b for a,b in lead_edges]);g=np.full(4,1/lead_rth)
  matrix+=coo_matrix((np.r_[g,g,-g,-g],(np.r_[ai,bi,ai,bi],np.r_[ai,bi,bi,ai])),shape=(total,total)).tocsr()
  rise=spsolve(matrix,source)
  temperatures={ref:float(50+max(rise[ids])+(power*2.0 if int(ref[1:])>104 else 0)) for ref,(ids,power) in sources.items()}
  result={'combined_convection_radiation_W_m2K':ambient_exchange,'BR1_junction_to_pad_sensitivity_C_W':lead_rth,'ambient_C':50,'diode_junction_estimates_C':temperatures,'BR1_peak_C':max(temperatures[f'D{i}'] for i in range(101,105)),'within_device_derated_targets':all(t<=(150 if int(ref[1:])<=104 else 125) for ref,t in temperatures.items())}
  results.append(result);print(result,flush=True)
report={'method':f'{h} mm finite-volume, gap-aware={args.gap_aware}, 4 copper sheets, FR4 dielectric coupling and 20 um plated through barrels. onsemi MBRB20H100CTT4G D2PAK 2.0 C/W junction-to-pad. MOT TO220 4 C/W engineering upper assumption (datasheet does not specify RthJC); 175 C-rated device screened to150 C, onsemi175 C devices screened to125 C to remain within specified leakage test temperature. TO220 dedicated junction/sink nodes; 8 W distributed background plus simultaneous simulated corner bridge losses and max leakage.',
 'geometry_sha256':hashlib.sha256((OUT/'copper_geometry.json').read_bytes()).hexdigest(),
 'bridge_results_sha256':hashlib.sha256((args.bridge_dir/'results.json').read_bytes()).hexdigest(),
 'leakage_bound':'MOT12mA/package at100V/125C table. Onsemi6mA/package is2x3mA per-leg bound from MAXIMUM125C reverse curve through30V (curve below2mA); actual peak26.6V or less. Full-cycle peak-voltage heat is conservative. Not based on typical leakage.',
 'conduction_maxima_W':losses,'diode_total_power_W':{r:p for r,(ids,p) in sources.items()},
 'BR1_heatsink_junction_to_ambient_C_W':heatsink_rth,
 'BR1_isolated_no_board_cooling_C':50+sources['D101'][1]*heatsink_rth,
 'total_applied_heat_W':float(source.sum()),
 'limitations':['No enclosure airflow or measured boundary coefficient; catalog heatsink orientation must be preserved','Lead thermal resistance 30/1000 C/W is engineering sensitivity, not a manufacturer parameter','Coarse pad/via discretisation; no model calibration','Uniform background does not represent local regulator/driver hotspots','Manufacturer 125 C loss equation; temperature-dependent electrothermal iteration not performed','MOT hot forward bound uses typical100/150C curves with added margin, not guaranteed maximum. Higher specified175C junction permits150C screening target; original125C common target no longer applies to these four devices. Confirm RthJC and steady case temperatures physically.','Not a physical thermal qualification'],
 'sources':['research/datasheets/C5143116.pdf','research/datasheets/C235758.pdf','https://info.boydcorp.com/hubfs/Thermal/Air-Cooling/Boyd-Board-Level-Cooling-Channel-5770.pdf'], 'cases':results}
(OUT/('thermal_mesh_gap.json' if args.gap_aware else 'thermal_mesh.json')).write_text(json.dumps(report,indent=2)+'\n')
