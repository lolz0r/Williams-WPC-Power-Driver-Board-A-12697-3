from pathlib import Path
import json,time
from close_routes import Board
from sexp import parse,find_all,find,dump
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'wpc_power_driver_cost.kicad_pcb'
b=Board(path)
refs={f'R{i}' for i in range(310,326)}
b.original_ids={v['id'] for v in b.items if v.get('pin','').split('.')[0] not in refs}
items=json.loads((ROOT/'pullup-migration.json').read_text());results=[]
for pin in ['2','1']:
 for item in items:
  n=item['net'] if pin=='2' else '+5V';terminal=item['ref']+'.'+pin;t=time.monotonic()
  result=b.route(n,.1,source_pin=terminal);b.save();results.append(dict(pin=terminal,net=n,result=result))
  print(terminal,n,result,round(time.monotonic()-t,1),flush=True)
(ROOT/'output/verification/pullup-routing.json').write_text(json.dumps(results,indent=2)+'\n')
