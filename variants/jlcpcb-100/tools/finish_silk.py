from pathlib import Path
import pcbnew as K
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'wpc_power_driver_cost.kicad_pcb';b=K.LoadBoard(str(p));fps={f.GetReference():f for f in b.GetFootprints()}
def pt(x,y):return K.VECTOR2I(K.FromMM(x),K.FromMM(y))
for r,x,y in [('R310',23,110),('R311',23,107),('R321',17.2,118),('R319',23,86)]:
 t=fps[r].Reference();t.SetPosition(pt(x,y));t.SetTextAngle(K.EDA_ANGLE(0,K.DEGREES_T));t.SetTextSize(pt(.8,.8));t.SetTextThickness(K.FromMM(.12))
for t in b.GetDrawings():
 if isinstance(t,K.PCB_TEXT) and t.GetText()=='F115 3/4A S.B. +12V SW.MATRIX':t.SetPosition(pt(77.5,84))
K.SaveBoard(str(p),b)
