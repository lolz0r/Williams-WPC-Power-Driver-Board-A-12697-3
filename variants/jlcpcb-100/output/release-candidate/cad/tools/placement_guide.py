"""Draw a native-pad assembly guide in board top-view coordinates."""
import csv
import json
import math
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/jlc-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from sexp import parse, find, find_all

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'output/release-candidate/jlcpcb-assembly'


def main():
    rows=list(csv.DictReader((OUT/'connector-orientation-check.csv').open()))
    board=parse((ROOT/'wpc_power_driver_cost.kicad_pcb').read_text())[0]
    fps={next(p[2] for p in find_all(f,'property') if p[1]=='Reference'):f for f in find_all(board,'footprint')}
    mapping={r['Upload_designator']:r for r in csv.DictReader((OUT/'placement-map.csv').open())}
    def points(ref):
        fp=fps[mapping[ref]['Native_reference']];at=list(map(float,find(fp,'at')[1:]));a=math.radians(at[2] if len(at)>2 else 0)
        pads=[]
        for p in find_all(fp,'pad'):
            if not p[1]:continue
            n=int(p[1]);x,y=map(float,find(p,'at')[1:3])
            if ref=='J115A' and n>6:continue
            if ref=='J115B':
                if n<7:continue
                n-=6
            pads.append((n,at[0]+x*math.cos(a)+y*math.sin(a),-at[1]+x*math.sin(a)-y*math.cos(a)))
        return pads
    vectors={'up':(0,1),'down':(0,-1),'left':(-1,0),'right':(1,0)}
    with PdfPages(OUT/'connector-orientation-guide.pdf') as pdf:
        fig,ax=plt.subplots(figsize=(16.5,11.7));fig.subplots_adjust(top=.88,bottom=.13,left=.05,right=.97)
        ax.set_aspect('equal');ax.set_xlim(-20,470);ax.set_ylim(-290,20)
        ax.plot([0,449.152,449.152,0,0],[0,0,-272.91,-272.91,0],color='#344754',lw=1)
        for r in rows:
            ps=points(r['Designator']);xs=[p[1] for p in ps];ys=[p[2] for p in ps]
            x=sum(xs)/len(xs);y=sum(ys)/len(ys);dx,dy=vectors[r['Tab_or_notch_top_view']]
            ax.scatter(xs,ys,s=4,color='#45616e');ax.scatter(float(r['Pin_1_X_mm']),float(r['Pin_1_Y_mm']),s=16,color='#c93425')
            ax.annotate('',xy=(x+9*dx,y+9*dy),xytext=(x,y),arrowprops={'arrowstyle':'->','color':'#167ca3','lw':1.2})
            ax.text(x+13*dx,y+13*dy,r['Designator'],fontsize=6.8,ha='center',va='center')
        for ref in ['U1','U2','U3']:
            ps=points(ref);xs=[p[1] for p in ps];ys=[p[2] for p in ps];ax.scatter(xs,ys,s=7,color='#5b537c')
            p=next(p for p in ps if p[0]==1);ax.scatter(p[1],p[2],s=22,color='#c93425')
            ax.text(sum(xs)/len(xs),min(ys)-4,ref+' CPL '+str(int(float(mapping[ref]['Rotation_deg'])))+'°',ha='center',va='top',fontsize=8)
        ax.set_xlabel('Gerber X (mm)');ax.set_ylabel('Gerber Y (mm), top view')
        fig.suptitle('JLC-100 assembly orientation guide — native holes and inward locking walls',fontsize=16,y=.97)
        fig.text(.5,.925,'Red = native pin 1    Blue arrow = friction-lock wall / J113 ribbon notch    Page corners follow board coordinates',ha='center',fontsize=11)
        fig.text(.06,.06,'CPL offsets already applied: U1 90°; U2/U3 270°; J110 180°; J113 90°.\nSupplier model/pad conflicts remain manual assembly gates. Use the detailed pages for every connector.\nDo not infer pin 1 from JLCPCB’s red/pink orientation dot. Verify physical pin functions and key posts.',fontsize=11)
        pdf.savefig(fig);fig.savefig(OUT/'connector-orientation-overview.png',dpi=140);plt.close(fig)
        for start in range(0,len(rows),12):
            fig,axes=plt.subplots(4,3,figsize=(16.5,11.7));fig.subplots_adjust(top=.86,bottom=.11,left=.045,right=.97,wspace=.21,hspace=.85)
            fig.suptitle('Connector details — board top view; red square = pin 1; orange × = remove only this post',fontsize=14,y=.97)
            fig.text(.5,.935,'Blue arrow points to friction wall (ribbon key notch for J113). All unmarked posts remain, including electrically unused posts.',ha='center',fontsize=10)
            for ax,r in zip(axes.flat,rows[start:start+12]):
                ref=r['Designator'];ps=points(ref);xs=[p[1] for p in ps];ys=[p[2] for p in ps]
                cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2
                key=int(r['Omit_post']) if r['Omit_post'] else None
                dx,dy=vectors[r['Tab_or_notch_top_view']]
                for n,x,y in ps:
                    ax.scatter(x-cx,y-cy,s=32 if n==1 else 19,marker='s' if n==1 else 'o',color='#c93425' if n==1 else '#344754',zorder=3)
                    if n==key:ax.scatter(x-cx,y-cy,s=90,marker='x',color='#e77e00',lw=2,zorder=4)
                    if ref!='J113' or n in [1,2,33,34]:
                        ax.text(x-cx-1.8*dx,y-cy-1.8*dy,str(n),fontsize=6.5,ha='center',va='center')
                ax.annotate('',xy=(8*dx,8*dy),xytext=(2*dx,2*dy),arrowprops={'arrowstyle':'->','color':'#167ca3','lw':2})
                ax.text(10*dx,10*dy,'notch' if ref=='J113' else 'tab',fontsize=8,ha='center',va='center',color='#167ca3')
                spanx=max(max(xs)-min(xs)+10,28);spany=max(max(ys)-min(ys)+10,28)
                ax.set_xlim(-spanx/2,spanx/2);ax.set_ylim(-spany/2,spany/2);ax.set_aspect('equal');ax.axis('off')
                ax.set_title(f"{ref}   {r['LCSC_part']}   CPL {float(r['CPL_rotation_deg']):g}°",fontsize=10,pad=12)
                status=r['Library_orientation_status'].replace('MANUAL: ','MANUAL: ')
                foot=f"Pin 1 ({float(r['Pin_1_X_mm']):.3f}, {float(r['Pin_1_Y_mm']):.3f}) mm | remove post {key if key else 'none'}\n{status}"
                ax.text(.5,-.18,foot,transform=ax.transAxes,ha='center',va='top',fontsize=7,color='#8d3a15' if status.startswith('MANUAL') else '#344754')
            for ax in list(axes.flat)[len(rows[start:start+12]):]:ax.axis('off')
            fig.text(.04,.015,'J115A uses native pins 1–6; J115B uses 7–12 (local key 3 = native 9). J120/J121 trim 13→11; J133/J134/J135 trim 10→9. See PCBA-remark.txt.',fontsize=9)
            pdf.savefig(fig);plt.close(fig)
    print('Wrote connector-orientation-guide.pdf and overview PNG')


if __name__=='__main__':main()
