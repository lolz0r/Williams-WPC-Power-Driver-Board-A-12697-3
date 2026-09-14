"""Audit the actual JLC-3 native source against the preserved parent board."""
from pathlib import Path
import hashlib,json
from sexp import parse,find,find_all

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def footprints(p):
    b=parse(p.read_text())[0]
    return {next(t[2] for t in find_all(f,'property') if t[1]=='Reference'):f for f in find_all(b,'footprint')}
def props(f):return {t[1]:t[2] for t in find_all(f,'property')}
def padnet(f,pin):return next(find(p,'net')[-1] for p in find_all(f,'pad') if p[1]==str(pin))

expected=json.loads((ROOT/'baseline-sha256.json').read_text())
migration=json.loads((ROOT/'research/prototype-power-migration.json').read_text());power_parts=migration['parts'];removed_power=set(migration['removed_refs'])
checks=[]
def check(ok,description):checks.append(dict(passed=bool(ok),description=description))
for name,h in expected.items():check(sha(BASE/name)==h,'Preserved original '+name)
old=footprints(BASE/'wpc_power_driver_cost.kicad_pcb');new=footprints(ROOT/'wpc_power_driver_cost.kicad_pcb')
check(set(old)-set(new)=={'SR1','SR2'}|removed_power,'Only SIP arrays and obsolete asynchronous catch diodes removed')
check(set(new)-set(old)=={f'R{i}' for i in range(310,326)}|(set(power_parts)-set(old)), 'Exactly the pull-ups and documented JLC-3 supply parts added')
for ref in old.keys()&new.keys():
    if ref in power_parts:continue
    for tag in ['at','layer']:check(find(old[ref],tag)==find(new[ref],tag),ref+' retained '+tag)
    a=find_all(old[ref],'pad');b=find_all(new[ref],'pad');check(len(a)==len(b),ref+' retained pad count')
    for p,q in zip(a,b):
        check(p[1:4]==q[1:4],ref+' pad identity/type '+str(p[1]))
        for tag in ['at','size','drill','layers']:check(find(p,tag)==find(q,tag),ref+' pad '+str(p[1])+' '+tag)
        oldnet=(find(p,'net') or ['',''])[-1]
        expectednet='+20V' if oldnet in {f'SOL{i}_TB' for i in range(21,29)} else oldnet
        check(expectednet==(find(q,'net') or ['',''])[-1],ref+' pad '+str(p[1])+' net (including documented JLC-2 clamp return)')
for ref,spec in power_parts.items():
    f=new[ref];p=props(f)
    for field in ['Value','Footprint','MPN','Manufacturer','JLCPCB Part']:
        actual=str(f[1]) if field=='Footprint' else p.get(field,'')
        check(actual==spec['properties'].get(field,''),ref+' JLC-3 '+field)
    wanted=set(spec['nets'])
    check({str(v[1]) for v in find_all(f,'pad') if v[1]}==wanted,ref+' documented pin inventory')
    for pin,net in spec['nets'].items():
        actual=padnet(f,pin)
        check(actual==net if net else actual.startswith('unconnected-'),ref+' JLC-3 pin '+pin+' net')
for item in json.loads((ROOT/'pullup-migration.json').read_text()):
    f=new[item['ref']];p=props(f)
    check(padnet(old[item['array']],1)=='+5V' and padnet(old[item['array']],item['pin'])==item['net'],item['ref']+' original array mapping')
    check(padnet(f,1)=='+5V' and padnet(f,2)==item['net'],item['ref']+' new pull-up topology')
    check(p['MPN']=='0805W8F4701T5E' and p['JLCPCB Part']=='C17673',item['ref']+' selected 4.7k Basic part')
for ref in ['C2','C4','C9','C12']:check(props(new[ref])['MPN']=='EEU-FR1E331B',ref+' factory-formed 5 mm lead pitch')
for ref in ['D1','D2','D3','D9','D10','D11','D12','D38']:check(props(new[ref])['MPN']=='M7',ref+' M7 replacement')
check(props(new['R192'])['Value']=='470','LED4 current-limiting resistor is 470 ohms')
for ref,f in new.items():
    p=props(f)
    if ref.startswith('U') and ('574' in p.get('MPN','') or '240' in p.get('MPN','')):check('HCT' in p['MPN'],ref+' TTL-compatible HCT retained')
for name,h in json.loads((ROOT/'output/verification/spice/inputs.json').read_text()).items():
    check(sha(ROOT/'tools/spice'/name)==h,'Base SPICE input hash '+name)
for ref in ['D5','D6','D7','D8','D9','D10','D11','D12']:
    check(padnet(new[ref],1)=='+20V',ref+' STTNG flasher cathode has a board-side +20 V return')
report=dict(passed=all(c['passed'] for c in checks),checks=len(checks),failures=[c for c in checks if not c['passed']],pcb_sha256=sha(ROOT/'wpc_power_driver_cost.kicad_pcb'),original_board_sha256=sha(BASE/'wpc_power_driver_cost.kicad_pcb'),preserved_baseline_files=expected,scope='All components outside the explicitly enumerated JLC-3 supply migration retain original positions and pad geometry. New supply values and each pin net match the migration specification. SIP arrays replaced by sixteen correctly connected resistors. JLC-2 explicitly merges SOL21..28_TB into +20V for STTNG flashers; other pad nets retained. Source consistency and model-input hashes; not a complete transistor-level extraction of this PCB.')
(ROOT/'output/verification/revision/source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Source audit:',report['checks'],'checks, passed',report['passed'],report['failures']);raise SystemExit(0 if report['passed'] else 1)
