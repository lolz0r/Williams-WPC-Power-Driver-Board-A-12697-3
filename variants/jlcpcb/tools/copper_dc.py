"""Finite-volume DC resistance of actual filled +5V copper, including plated barrels.
Run with .venv Python. Four-neighbour square cells; two meshes expose discretisation error.
This is a numerical estimate, not a substitute for four-wire measurement of a PCB.
"""
import json
import hashlib
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.sparse.csgraph import connected_components
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

OUT=Path('output/verification/revision')
j=json.loads((OUT/'copper_geometry.json').read_text())
names=['F.Cu','In1.Cu','In2.Cu','B.Cu']
geoms={n:unary_union([Polygon(p['outer'],p['holes']) for p in j['copper']['+5V'][n]]) for n in names}


def solve(h):
 xs=np.arange(h/2,450,h);ys=np.arange(h/2,274,h);xx,yy=np.meshgrid(xs,ys);n=0;maps=[];ii=[];jj=[];gg=[]
 rho=1.724e-5 # ohm mm at 20 C
 def edge(a,b,g):ii.extend(a);jj.extend(b);gg.extend(np.broadcast_to(g,np.shape(a)))
 for name in names:
  mask=shapely.contains_xy(geoms[name],xx,yy);m=np.full(mask.shape,-1,dtype=np.int32);m[mask]=np.arange(n,n+mask.sum());n+=mask.sum();maps.append(m)
  g=j['copper_thickness_mm'][name]/rho
  for a,b in [(m[:,:-1],m[:,1:]),(m[:-1,:],m[1:,:])]:
   keep=(a>=0)&(b>=0);edge(a[keep],b[keep],g)
 def nearest(layer,x,y):
  m=maps[layer];ix=int(x/h);iy=int(y/h)
  candidates=[]
  for dy in range(-3,4):
   for dx in range(-3,4):
    a,b=iy+dy,ix+dx
    if 0<=a<m.shape[0] and 0<=b<m.shape[1] and m[a,b]>=0:candidates.append(((xs[b]-x)**2+(ys[a]-y)**2,int(m[a,b])))
  return min(candidates)[1] if candidates else None
 barrels={}
 for v in j['vias']:
  if v['net']=='+5V':barrels[(v['x'],v['y'])]=v['drill_mm']
 for v in j['terminals']:
  if v['net']=='+5V' and v['drill_mm']:barrels[(v['x'],v['y'])]=v['drill_mm']
 for (x,y),drill in barrels.items():
  nodes=[(i,nearest(i,x,y)) for i in range(4)];nodes=[(i,k) for i,k in nodes if k is not None]
  # Copper centres from the specified 1.6 mm stackup, 20 um minimum barrel wall.
  z=[.035,.2875,1.3125,1.565]
  for (a,ka),(b,kb) in zip(nodes,nodes[1:]):edge([ka],[kb],np.pi*drill*.020/(rho*(z[b]-z[a])))
 def terminal(ref,pad):
  t=next(t for t in j['terminals'] if t['ref']==ref and t['pad']==pad);return nearest(0,t['x'],t['y'])
 source=terminal('L1','2');sinks=[terminal('J114','3'),terminal('J114','4')]
 assert source is not None and all(s is not None for s in sinks)
 i=np.array(ii);k=np.array(jj);g=np.array(gg)
 matrix=coo_matrix((np.r_[g,g,-g,-g],(np.r_[i,k,i,k],np.r_[i,k,k,i])),shape=(n,n)).tocsr()
 _,labels=connected_components(matrix)
 assert all(labels[s]==labels[source] for s in sinks), f'Mesh {h} disconnected the required terminals'
 active=(labels==labels[source]);active[sinks]=False;indices=np.flatnonzero(active);rhs=np.zeros(len(indices));rhs[np.searchsorted(indices,source)]=1
 voltage=spsolve(matrix[indices][:,indices],rhs);r=float(voltage[np.searchsorted(indices,source)])
 return dict(mesh_mm=h,nodes=int(n),connected_nodes=len(indices)+len(sinks),resistance_20C_ohm=r,resistance_75C_ohm=r*(1+.00393*55),drop_at_3A_75C_V=3*r*(1+.00393*55))

results=[]
for h in (.5,.25):
 r=solve(h);results.append(r);print(r,flush=True)
report={'geometry_sha256':hashlib.sha256((OUT/'copper_geometry.json').read_bytes()).hexdigest(),'method':'Four-layer finite-volume sheet resistance; actual filled polygons, 2oz finished outer/1oz inner, 20um barrel plating, ideal source at L1-2, J114-3/4 tied at load. No connector/harness contact resistance.','cases':results,'relative_mesh_change':abs(results[-1]['resistance_20C_ohm']/results[0]['resistance_20C_ohm']-1),'measurement_required':True}
(OUT/'copper_dc.json').write_text(json.dumps(report,indent=2)+'\n')
