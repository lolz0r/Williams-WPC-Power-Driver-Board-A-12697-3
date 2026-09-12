#!/usr/bin/env python3
"""Conservative incremental copper routing on an isolated board (Shapely/Numba).

Uses physical pads/tracks, actual project net classes, through-hole spacing,
three signal layers, and exact polygon validation after grid search. Does not
remove existing copper, alter rules, or install the candidate. KiCad DRC remains
mandatory. Filled zones are left to KiCad; ground stitching is a separate step.
"""
import argparse, fnmatch, heapq, json, math, time, uuid
from pathlib import Path
import numpy as np
from numba import njit
import shapely
from shapely.geometry import Point, LineString, box
from shapely.affinity import rotate, translate
from shapely.ops import unary_union, nearest_points
from sexp import parse, dump, find, find_all, S
LAYERS = ['F.Cu', 'In2.Cu', 'B.Cu']

@njit(cache=True)
def search(block, vias, source, target, bounds):
    L,H,W=block.shape; N=L*H*W
    dist=np.full(N,2147483647,np.int32); prev=np.full(N,-1,np.int32)
    heap=[(0,0,0)];heap.pop()
    x0,y0,x1,y1=bounds
    for l,y,x in zip(*np.where(source)):
        i=(l*H+y)*W+x;dist[i]=0
        h=10*(max(x0-x,0,x-x1)+max(y0-y,0,y-y1))
        heapq.heappush(heap,(h,0,i))
    while heap:
        _,d,i=heapq.heappop(heap)
        if dist[i]!=d:continue
        x=i%W;y=(i//W)%H;l=i//(W*H)
        if target[l,y,x]:return prev,i
        for k in range(6):
            xx=x;yy=y;ll=l;cost=10
            if k==0:xx+=1
            elif k==1:xx-=1
            elif k==2:yy+=1
            elif k==3:yy-=1
            else:
                if vias[y,x]:continue
                ll=(l+(1 if k==4 else 2))%3;cost=250
            if xx<0 or yy<0 or xx>=W or yy>=H or block[ll,yy,xx]:continue
            j=(ll*H+yy)*W+xx;nd=d+cost
            if nd<dist[j]:
                dist[j]=nd;prev[j]=i
                h=10*(max(x0-xx,0,xx-x1)+max(y0-yy,0,yy-y1))
                heapq.heappush(heap,(nd+h,nd,j))
    return prev,-1

def xy(o,k):return tuple(map(float,find(o,k)[1:3]))
def net(o):
    n=find(o,'net');return str(n[-1]) if n else ''
def uid(o):return str(find(o,'uuid')[1])
def circle(x,y,r):return Point(x,y).buffer(r,quad_segs=16)

class Board:
    def __init__(self,path):
        self.path=path;self.doc=parse(path.read_text())[0];self.items=[];self.holes=[];self.smd=[];self.new=[];self.plane_tracks=[]
        pro=json.loads(path.with_suffix('.kicad_pro').read_text())['net_settings']
        self.classes={c['name']:c for c in pro['classes']};self.patterns=pro['netclass_patterns']
        for f in find_all(self.doc,'footprint'):
            ref=next(v[2] for v in find_all(f,'property') if v[1]=='Reference')
            fa=find(f,'at');fx,fy=map(float,fa[1:3]);ang=float(fa[3]) if len(fa)>3 else 0
            for p in find_all(f,'pad'):
                a=find(p,'at');rx,ry=map(float,a[1:3]);rad=math.radians(ang)
                x=fx+rx*math.cos(rad)+ry*math.sin(rad);y=fy-rx*math.sin(rad)+ry*math.cos(rad)
                pa=float(a[3]) if len(a)>3 else ang;w,h=xy(p,'size');shape=str(p[3])
                if shape=='circle':poly=circle(0,0,w/2)
                elif shape=='oval':
                    poly=LineString([(-(w-h)/2,0),((w-h)/2,0)]).buffer(h/2) if w>=h else LineString([(0,-(h-w)/2),(0,(h-w)/2)]).buffer(w/2)
                elif shape=='roundrect':
                    r=min(w,h)*float(find(p,'roundrect_rratio')[1])
                    poly=box(-w/2+r,-h/2+r,w/2-r,h/2-r).buffer(r,quad_segs=16)
                elif shape=='rect':poly=box(-w/2,-h/2,w/2,h/2)
                else:raise ValueError(f'Unsupported pad geometry {shape}')
                poly=translate(rotate(poly,-pa,origin=(0,0)),x,y)
                ls=[str(z) for z in find(p,'layers')[1:]];layers=list(range(3)) if '*.Cu' in ls or 'F&B.Cu' in ls else [i for i,l in enumerate(LAYERS) if l in ls]
                self.items.append(dict(id=uid(p),net=net(p),poly=poly,layers=layers,pin=f'{ref}.{p[1]}',hole_clearance=.25 if p[2]=='np_thru_hole' else 0))
                dr=find(p,'drill')
                if dr:
                    nums=[float(v) for v in dr[1:] if not isinstance(v,list) and v!='oval']
                    self.holes.append(circle(x,y,max(nums)/2))
                if p[2]=='smd':self.smd.append(poly)
        for t in find_all(self.doc,'segment'):
            layer=str(find(t,'layer')[1])
            if layer not in LAYERS:
                self.plane_tracks.append(LineString([xy(t,'start'),xy(t,'end')]).buffer(float(find(t,'width')[1])/2+.4));continue
            self.items.append(dict(id=uid(t),net=net(t),poly=LineString([xy(t,'start'),xy(t,'end')]).buffer(float(find(t,'width')[1])/2),layers=[LAYERS.index(layer)]))
        if find_all(self.doc,'arc'):raise ValueError('Track arcs unsupported')
        for v in find_all(self.doc,'via'):
            x,y=xy(v,'at');self.holes.append(circle(x,y,float(find(v,'drill')[1])/2))
            self.items.append(dict(id=uid(v),net=net(v),poly=circle(x,y,float(find(v,'size')[1])/2),layers=list(range(3)),via=(x,y)))
        self.contacts=[];self.contact_windows=box(0,0,0,0)
    def params(self,n):
        names=[p['netclass'] for p in self.patterns if fnmatch.fnmatchcase(n,p['pattern'])]
        return self.classes[names[0] if names else 'Default']
    def groups(self,n):
        items=[v for v in self.items if v['net']==n];parent=list(range(len(items)))
        def root(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        geoms=[v['poly'] for v in items]
        if geoms:
            pairs=shapely.STRtree(geoms).query(geoms,predicate='dwithin',distance=.00002)
            for i,j in zip(*pairs):
                if i>j and set(items[i]['layers'])&set(items[j]['layers']):parent[root(i)]=root(j)
        groups={}
        for i,v in enumerate(items):groups.setdefault(root(i),[]).append(v)
        # Small branches first, targeting all already routed copper of this net.
        return sorted(groups.values(),key=lambda g:sum(v['poly'].area for v in g))
    def route(self,n,pitch,grid_margin=None,ground_pin=None,local=True,source_pin=None):
        groups=self.groups(n)
        if len(groups)<2:return 'connected'
        source=groups[0];target=[v for g in groups[1:] for v in g]
        if source_pin:
            source=next(g for g in groups if any(v.get('pin')==source_pin for v in g))
            def original(v):return v['id'] in self.original_ids
            if any(original(v) for v in source):return 'connected to existing copper'
            target=[v for g in groups if g is not source for v in g if original(v)]
            origin=unary_union([v['poly'] for v in source]);target=sorted(target,key=lambda v:origin.distance(v['poly']))[:100]
        c=self.params(n);width=.4;dia=1.;drill=.5;clear=c['clearance']
        if ground_pin:
            from shapely.geometry import Polygon
            plane=[]
            for z in find_all(self.doc,'zone'):
                if net(z)=='GND' and find(z,'layer')[1]=='In1.Cu':
                    plane += [Polygon([tuple(map(float,q[1:3])) for q in find(f,'pts')[1:]]).buffer(0) for f in find_all(z,'filled_polygon')]
            plane=max(plane,key=lambda p:p.area)
            source=next(g for g in groups if any(v.get('pin')==ground_pin for v in g))
            def plane_via(v):return v.get('via') and plane.contains(Point(*v['via']))
            if any(plane_via(v) for v in source):return 'connected to ground plane'
            target=[v for g in groups if g is not source for v in g if plane_via(v)]
            origin=next(v['poly'] for v in source if v.get('pin')==ground_pin)
            target=sorted(target,key=lambda v:origin.distance(v['poly']))[:20]
            width,clear,dia,drill=.2,.16,.52,.25
        # Signal vias can use any permitted project geometry, including the small
        # MCU fanout size, while preserving the specified track width/clearance.
        if width<=.3:dia,drill=.52,.25
        if local:
            aa,zz=nearest_points(unary_union([v['poly'] for v in source]),unary_union([v['poly'] for v in target]))
            bx0,by0,bx1,by1=min(aa.x,zz.x),min(aa.y,zz.y),max(aa.x,zz.x),max(aa.y,zz.y)
            margin=6.
        else:
            bx0,by0,bx1,by1=unary_union([v['poly'] for v in source+target]).bounds
            margin=12.
        x0=max(1.,math.floor((bx0-margin)/pitch)*pitch);y0=max(1.,math.floor((by0-margin)/pitch)*pitch)
        x1=min(447.,bx1+margin);y1=min(270.,by1+margin)
        window=box(x0-3,y0-3,x1+3,y1+3)
        foreign=[v for v in self.items if v['net']!=n]
        candidates=shapely.STRtree([v['poly'] for v in foreign]).query(window,predicate='intersects')
        foreign=[foreign[int(i)] for i in candidates]
        obs=[unary_union([v['poly'].buffer(max(clear,self.params(v['net'])['clearance'],v.get('hole_clearance',0))+.008) for v in foreign if l in v['layers']]) for l in range(3)]
        for l in (0,2):
            lands=unary_union([p['poly'] for p in self.contacts if p['net']==n and l in p['layers']])
            obs[l]=unary_union([obs[l],self.contact_windows.difference(lands).intersection(window)])
        # Include holes and solder-mask openings even when copper shares the net.
        # obs already includes a copper safety margin. Do not double it at
        # vias: the resulting artificial blockage can close valid fanout gaps.
        # Tented drill edges retain 0.16 mm from SMT mask openings.
        vb=unary_union([o.buffer(dia/2+.001) for o in obs]+[o.buffer(dia/2+.001) for o in self.plane_tracks if o.intersects(window)]+[h.buffer(drill/2+.51) for h in self.holes if h.intersects(window)]+[p.buffer(drill/2+.16) for p in self.smd if p.intersects(window)])
        xs=np.arange(x0,x1+pitch/2,pitch);ys=np.arange(y0,y1+pitch/2,pitch)
        X,Y=np.meshgrid(xs,ys);H,W=X.shape
        if H*W>8500000:return 'window too large'
        block=np.zeros((3,H,W),dtype=np.bool_);src=block.copy();dst=block.copy()
        for l in range(3):
            block[l]=shapely.intersects_xy(obs[l].buffer(width/2+(pitch*.51 if grid_margin is None else grid_margin)),X,Y)
            src[l]=shapely.intersects_xy(unary_union([v['poly'] for v in source if l in v['layers']]),X,Y)&~block[l]
            dst[l]=shapely.intersects_xy(unary_union([v['poly'] for v in target if l in v['layers']]),X,Y)&~block[l]
        via=shapely.intersects_xy(vb,X,Y)|(Y>270)|(X<2)|(X>447)|(Y<2)
        if not src.any() or not dst.any():
            if local:return self.route(n,pitch,grid_margin,ground_pin,False,source_pin)
            return f'no terminals ({src.sum()}/{dst.sum()})'
        _,ty,tx=np.where(dst);bounds=(int(tx.min()),int(ty.min()),int(tx.max()),int(ty.max()))
        prev,end=search(block,via,src,dst,bounds)
        if end<0:
            if local:return self.route(n,pitch,grid_margin,ground_pin,False,source_pin)
            visited=(prev.reshape((3,H,W))>=0)|src
            pockets=[]
            for l in range(3):
                yy,xx=np.where(visited[l])
                if len(xx):pockets.append((LAYERS[l],len(xx),tuple(round(v,3) for v in (xs[xx.min()],ys[yy.min()],xs[xx.max()],ys[yy.max()]))))
            print('Search reach:',n,pockets,flush=True)
            return 'no path'
        points=[];i=end
        while i>=0:
            points.append((int(i//(H*W)),round(float(xs[i%W]),5),round(float(ys[(i//W)%H]),5)))
            i=int(prev[i])
        points.reverse();compressed=[]
        for pt in points:
            if len(compressed)>1:
                a,b=compressed[-2:]
                if a[0]==b[0]==pt[0] and ((a[1]==b[1]==pt[1]) or (a[2]==b[2]==pt[2])):compressed[-1]=pt;continue
            compressed.append(pt)
        # Remove grid staircases using exact line-of-sight checks. Vias delimit
        # each layer run; every shortened segment must retain copper clearance.
        smooth=[];i=0
        expanded=[o.buffer(width/2+.006) for o in obs]
        while i<len(compressed):
            smooth.append(compressed[i])
            if i==len(compressed)-1:break
            j=i+1
            if compressed[j][0]==compressed[i][0]:
                for k in range(i+2,len(compressed)):
                    if compressed[k][0]!=compressed[i][0]:break
                    if LineString([compressed[i][1:],compressed[k][1:]]).intersects(expanded[compressed[i][0]]):break
                    j=k
            i=j
        compressed=smooth
        changes=[];geometries=[];newholes=[]
        for a,b in zip(compressed,compressed[1:]):
            ident=str(uuid.uuid4())
            if a[0]!=b[0]:
                poly=circle(a[1],a[2],dia/2)
                if any(poly.intersects(o) for o in obs):return 'via validation failed'
                hole=circle(a[1],a[2],drill/2)
                if any(hole.distance(h)<.5 for h in newholes):return 'new drill spacing validation failed'
                changes.append(S('via',S('at',a[1],a[2]),S('size',dia),S('drill',drill),S('layers','F.Cu','B.Cu'),S('net',n),S('uuid',ident)))
                geometries.append(dict(id=ident,net=n,poly=poly,layers=list(range(3))))
                newholes.append(hole)
            else:
                poly=LineString([a[1:],b[1:]]).buffer(width/2)
                if poly.intersects(obs[a[0]]):return 'track validation failed'
                changes.append(S('segment',S('start',*a[1:]),S('end',*b[1:]),S('width',width),S('layer',LAYERS[a[0]]),S('net',n),S('uuid',ident)))
                geometries.append(dict(id=ident,net=n,poly=poly,layers=[a[0]]))
        self.new+=changes;self.items+=geometries;self.holes+=newholes
        return f'added {len(changes)} copper items; {len(self.groups(n))} groups remain'
    def save(self):
        if self.new:
            s=self.path.read_text().rstrip();tmp=self.path.with_suffix('.route-tmp');tmp.write_text(s[:-1]+'\n'+'\n'.join(dump(v) for v in self.new)+'\n)\n');tmp.replace(self.path);self.new=[]

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('pcb',type=Path);ap.add_argument('drc',type=Path);ap.add_argument('--pitch',type=float,default=.1);ap.add_argument('--nets');ap.add_argument('--grid-margin',type=float);ap.add_argument('--ground-pads');ap.add_argument('--priority-drc',type=Path);a=ap.parse_args()
    b=Board(a.pcb);report=json.loads(a.drc.read_text());ids={v['id']:v for v in b.items}
    nets=[]
    entries=(json.loads(a.priority_drc.read_text())['unconnected_items'] if a.priority_drc else [])+report['unconnected_items']
    for u in entries:
        names=[ids[i['uuid']]['net'] for i in u['items'] if i['uuid'] in ids]
        if names and names[0]!='GND' and names[0] not in nets:nets.append(names[0])
    if a.nets:nets=a.nets.split(',')
    if a.ground_pads:nets=a.ground_pads.split(',')
    for n in nets:
        start=time.monotonic()
        for _ in range(10):
            result=b.route('GND' if a.ground_pads else n,a.pitch,a.grid_margin,n if a.ground_pads else None)
            print(n,result,f'{time.monotonic()-start:.1f}s',flush=True)
            b.save()
            if not result.startswith('added'):break
