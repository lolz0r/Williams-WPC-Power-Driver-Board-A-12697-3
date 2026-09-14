from pathlib import Path
import pcbnew as pcb
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'wpc_power_driver_cost.kicad_pcb';b=pcb.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
for ref,dx,dy in [('C11',3.5,0),('C62',3.5,0),('C30',8,5),('C63',8,5)]:fps[ref].Move(pcb.VECTOR2I(round(dx*1e6),round(dy*1e6)))
pcb.SaveBoard(str(path),b)
