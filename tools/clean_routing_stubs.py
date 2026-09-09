"""Remove native-DRC-reported dangling tracks/vias, preserving a rollback copy.
A fresh native DRC with zone refill must follow; do not release if new opens appear.
"""
import argparse
import json
from pathlib import Path
import shutil
from sexp import parse, dump, find

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('report',type=Path)
p.add_argument('--pcb',type=Path,default=Path('wpc_power_driver_cost.kicad_pcb'))
a=p.parse_args()
report=json.loads(a.report.read_text())
assert not report['unconnected_items'], 'Fix existing opens before removing stubs'
ids={i['uuid'] for v in report['violations'] if v['type'] in ('track_dangling','via_dangling') for i in v['items']}
root=parse(a.pcb.read_text())[0]
removed=[]
for item in list(root):
 if isinstance(item,list) and item[0] in ('segment','via'):
  uid=find(item,'uuid')
  if uid and uid[1] in ids:root.remove(item);removed.append(uid[1])
backup=Path('.scratch/release-baseline')/(a.report.stem+'-before-stub-cleanup.kicad_pcb')
backup.parent.mkdir(parents=True,exist_ok=True)
assert not backup.exists(), 'Use a distinct report filename for each cleanup pass'
shutil.copy2(a.pcb,backup)
a.pcb.write_text(dump(root)+'\n')
print('Removed',len(removed),'reported stubs; rollback:',backup)
