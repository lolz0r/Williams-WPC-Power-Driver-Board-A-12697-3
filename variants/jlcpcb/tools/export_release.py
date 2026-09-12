"""Portable, fail-fast KiCad manufacturing export with hashes and explicit readiness.
Usage: python3 tools/export_release.py [--output output/release-candidate]
Outputs remain a review candidate until every documented release gate is closed.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from kicad_env import cli, environment
from sourcing import SRC
from verify_artifacts import audit

ROOT=Path(__file__).resolve().parents[1]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'output/release-candidate');a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
 for d in ('reports','gerbers','drill','bom','assembly','schematic','3d'): (out/d).mkdir(exist_ok=True)
 pcb=ROOT/'wpc_power_driver_cost.kicad_pcb';sch=ROOT/'wpc_power_driver_cost.kicad_sch'
 commands=[]
 def run(args):
  command=[cli()]+[str(x) for x in args];commands.append(command)
  with (out/'reports/export.log').open('a') as log:
   r=subprocess.run(command,env=environment(),cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
  if r.returncode:raise RuntimeError(f'KiCad exited {r.returncode}: {command}; see export.log')
  print('Completed:', ' '.join(command[1:4]),flush=True)
 (out/'reports/export.log').write_text('')
 run(['sch','export','netlist','--format','kicadxml','-o',out/'reports/netlist.xml',sch])
 run(['sch','erc','--severity-all','--format','json','-o',out/'reports/erc.json',sch])
 run(['pcb','drc','--refill-zones','--save-board','--schematic-parity','--severity-all','--format','json','-o',out/'reports/drc.json',pcb])
 drc=json.loads((out/'reports/drc.json').read_text());erc=json.loads((out/'reports/erc.json').read_text())
 ev=[v for sheet in erc['sheets'] for v in sheet['violations']]
 assert not any(v['severity']=='error' for v in drc['violations']+ev), 'Electrical/PCB errors block export'
 assert not drc['unconnected_items'] and not drc['schematic_parity'], 'Connectivity/parity blocks export'
 parity=audit(pcb,out/'reports/netlist.xml');(out/'reports/artifact-parity.json').write_text(json.dumps(parity,indent=2)+'\n');assert parity['passed']
 run(['pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts','--subtract-soldermask','-o',str(out/'gerbers')+'/',pcb])
 run(['pcb','export','drill','--format','excellon','--excellon-separate-th','--excellon-units','mm','--drill-origin','absolute','--generate-map','--map-format','gerberx2','-o',str(out/'drill')+'/',pcb])
 run(['pcb','export','pos','--format','csv','--units','mm','--side','both','--exclude-dnp','-o',out/'assembly/positions.csv',pcb])
 run(['pcb','export','ipcd356','-o',out/'assembly/netlist.d356',pcb])
 run(['sch','export','pdf','-o',out/'schematic/schematic.pdf',sch])
 for name,layers in [('top','F.Cu,F.SilkS,Edge.Cuts'),('bottom','B.Cu,B.SilkS,Edge.Cuts'),('inner-ground','In1.Cu,Edge.Cuts'),('inner-signal','In2.Cu,Edge.Cuts'),('assembly','F.Fab,Edge.Cuts,Dwgs.User')]:
  run(['pcb','export','pdf','--layers',layers,'-o',out/'assembly'/f'{name}.pdf',pcb])
 # Build purchasable BOM directly from the fresh netlist, never .scratch/parts.json.
 rows=[];fuses=0
 for c in ET.parse(out/'reports/netlist.xml').findall('.//components/comp'):
  ref=c.attrib['ref'];fields={f.attrib['name']:f.text or '' for f in c.findall('fields/field')}
  if ref.startswith('H'):continue
  props={x.attrib.get('name'):x.attrib.get('value','') for x in c.findall('property')}
  dnp='dnp' in props
  fp=c.findtext('footprint') or ''
  clip_only='Fuseholder_Clip-5x20mm' in fp and fields.get('MPN')==SRC['FUSECLIP']['mpn']
  if 'Fuseholder_Clip-5x20mm' in fp and not clip_only:fuses+=1
  rows.append(dict(Refs=ref,Qty=2 if clip_only else 1,Value=c.findtext('value'),Footprint=fp,Manufacturer=fields.get('Manufacturer',''),MPN=fields.get('MPN',''),Description=fields.get('Description',c.findtext('description') or ''),Link=fields.get('Link',''),DNP='yes' if dnp else ''))
 for key,qty,refs in [('FUSECLIP',2*fuses,'F103-F116 clips'),('HS7020',5,'Heatsinks Q10 Q12 Q14 Q16 Q18'),('HS6224',1,'Heatsink BR3'),('HS5772',4,'Heatsinks D101 D102 D103 D104'),('M3X8',4,'BR1 hardware'),('M3NUT',4,'BR1 hardware'),('THERMALPASTE',1,'Assembly consumable; one syringe per build batch'),('M3X12',5,'Triac hardware'),('M3NUT',5,'Triac hardware'),('M4X16',1,'BR3/H9 hardware'),('M4NUT',1,'BR3 hardware')]:
  s=SRC[key];rows.append(dict(Refs=refs,Qty=qty,Value=key,Footprint='Mechanical',Manufacturer=s['mfr'],MPN=s['mpn'],Description=s['desc'],Link=s['link'],DNP=''))
 keys=list(rows[0])
 def write_csv(path,data):
  with path.open('w',newline='') as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(data)
 write_csv(out/'bom/all-components.csv',rows)
 groups={}
 for row in rows:
  if row['DNP'] or row['Refs'].startswith('TP'):continue
  k=(row['MPN'],row['Value'],row['Footprint']);g=groups.setdefault(k,dict(row,Qty=0,Refs=''));g['Qty']+=row['Qty'];g['Refs']=(g['Refs']+' '+row['Refs']).strip()
 write_csv(out/'bom/purchase-bom.csv',groups.values())
 assert all(r['MPN'] for r in rows if not r['DNP'] and not r['Refs'].startswith('TP')), 'Populated component lacks MPN'
 run(['pcb','export','step','--subst-models','--no-dnp','--force','-o',out/'3d/board.step',pcb])
 for side,rotation in [('top',None),('bottom',None),('perspective','-35,0,20')]:
  args=['pcb','render','--side','top' if rotation else side,'--quality','high','--width','2560','--height','1600','--background','opaque','-o',out/'3d'/f'{side}.png',pcb]
  if rotation:args[2:2]=['--perspective','--rotate',rotation,'--floor']
  run(args)
 (out/'FABRICATION.txt').write_text('ENGINEERING REVIEW CANDIDATE — consult READINESS.json before ordering.\n4 layers, Edge.Cuts nominal 449.152 x 272.910 mm, FR-4 Tg >=150 C, 1.6 mm nominal.\nF.Cu / B.Cu: 2 oz FINISHED (70 um). In1.Cu / In2.Cu: 1 oz (35 um).\nDielectric stack: 0.200 mm / 0.990 mm / 0.200 mm. Minimum finished PTH barrel copper 20 um.\nIn1 predominantly GND with an AC16_A route; In2 includes +5V plane and other routed signals.\nENIG; green LPI mask both sides; white silk; 100% bare-board electrical test against assembly/netlist.d356.\nAbsolute origin for Gerbers and Excellon. Separate plated and non-plated drill files.\nF.Paste/B.Paste are stencil data, not copper layers. See project docs for assembly and connector key pins.\n')
 readiness={'status':'REVIEW_CANDIDATE_NOT_RELEASED','fab_ready':False,'electrical_errors':0,'unconnected_items':0,'schematic_parity_issues':0,'drc_warnings':len(drc['violations']),'erc_warnings':len(ev),'remaining_gates':['Run tools/package_review.py to bind independent checks to this exact export','Regulator reverse-current / shutdown qualification','Simultaneous thermal, real loads, fuse/fault and cabinet/harness qualification','Fabricator DFM, procurement confirmation and first-article measurements'],'physical_qualification':'First-article cabinet fit, loaded supply/oscilloscope, fault/fuse and thermal measurements are not performed by software.'}
 (out/'READINESS.json').write_text(json.dumps(readiness,indent=2)+'\n')
 (out/'reports/commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 with zipfile.ZipFile(out/'gerbers-and-drills.zip','w',zipfile.ZIP_DEFLATED) as z:
  for directory in ('gerbers','drill'):
   for f in sorted((out/directory).iterdir()):z.write(f,f.relative_to(out))
  z.write(out/'FABRICATION.txt','FABRICATION.txt');z.write(out/'READINESS.json','READINESS.json')
 hashes={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file() and f.name!='SHA256.json'}
 (out/'SHA256.json').write_text(json.dumps(hashes,indent=2)+'\n');print(out)


if __name__=='__main__':main()
