"""Correct KK396 order-code digits in schematic and routed PCB metadata only."""
from pathlib import Path
import re
for p in list(Path('.').glob('*.kicad_sch'))+[Path('wpc_power_driver_cost.kicad_pcb')]:
 s=p.read_text()
 for n in (3,4,5,6,7,9,11,12,13):s=s.replace(f'00266040{n:02d}',f'0026604{n:02d}0')
 p.write_text(s)
