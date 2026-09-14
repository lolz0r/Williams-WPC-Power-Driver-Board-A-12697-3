"""Remove erroneous feature models and clip only DRC-reported silk strokes.
References and fab-layer polarity/outline drawings are preserved.
"""
from pathlib import Path
import json,sys,re
from sexp import parse,dump,find,find_all,S
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'wpc_power_driver_cost.kicad_pcb';b=parse(p.read_text())[0];d=json.loads((ROOT/'output/verification/native-final1/drc.json').read_text());ids={i['uuid'] for v in d['violations'] if v['type'] in ['silk_overlap','silk_over_copper'] for i in v['items']};removed=[]
for f in find_all(b,'footprint'):
 pp={q[1]:q[2] for q in find_all(f,'property')};r=pp['Reference']
 if r.startswith('FID'):
  for m in find_all(f,'model'):f.remove(m)
 if r in ['U1','U2','U3','U4','U5','U9','U18']:
  for m in find_all(f,'model'):m[1]='${KIPRJMOD}/models/inventory/TI_NS20.step'
 for q in list(f):
  if isinstance(q,list) and q[0] in ['fp_line','fp_circle','fp_arc','fp_poly','fp_rect'] and find(q,'uuid') and str(find(q,'uuid')[1]) in ids and find(q,'layer')==['layer','F.SilkS']:
   removed.append(dict(ref=r,uuid=str(find(q,'uuid')[1])));f.remove(q)
p.write_text(dump(b)+'\n');(ROOT/'research/silkscreen-clipped-strokes.json').write_text(json.dumps(removed,indent=2)+'\n');print('Clipped',len(removed),'reported strokes; references retained')
