"""Add conservative through-via stitching in BR1's expanded thermal pour.
Checks all routed layers and pad extents before proposing vias; native DRC is mandatory afterwards.
Run using KiCad Python after a saved zone refill.
"""
import math
import pcbnew


def main():
    path='wpc_power_driver_cost.kicad_pcb'
    b=pcbnew.LoadBoard(path)
    net=b.FindNet('+18V');code=net.GetNetCode();mm=lambda x:round(x*1e6)
    tracks=list(b.GetTracks());pads=[p for f in b.GetFootprints() for p in f.Pads()]
    def distance(px,py,a,c):
        ax,ay=a.x/1e6,a.y/1e6;cx,cy=c.x/1e6,c.y/1e6
        dx,dy=cx-ax,cy-ay;l=dx*dx+dy*dy
        u=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/l)) if l else 0
        return math.hypot(px-ax-u*dx,py-ay-u*dy)
    def free(x,y):
        for t in tracks:
            if t.GetClass()=='PCB_VIA':
                if distance(x,y,t.GetStart(),t.GetEnd())<1.8:return False
            elif t.GetNetCode()!=code and distance(x,y,t.GetStart(),t.GetEnd())<t.GetWidth()/2e6+1.1:return False
        for p in pads:
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH or p.GetNetCode()!=code:
                if p.HitTest(pcbnew.VECTOR2I(mm(x),mm(y)),mm(1.1)):return False
        return True
    chosen=[]
    for x,y in [(x,y) for y in (70,75,80,85,90,95,100,105) for x in (345,350,355,360,365,370,375)]:
        if not free(x,y):continue
        if any(math.hypot(x-a,y-c)<9 for a,c in chosen):continue
        v=pcbnew.PCB_VIA(b);v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)));v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(mm(1.2));v.SetDrill(mm(.6));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetNet(net);b.Add(v);tracks.append(v);chosen.append((x,y))
    pcbnew.SaveBoard(path,b);print('Added bridge stitching:',chosen)


if __name__=='__main__':main()
