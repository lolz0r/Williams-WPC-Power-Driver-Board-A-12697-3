"""Compare a KiCad XML netlist with PCB pad assignments and component fields.

This checks artifact consistency, not routed continuity or electrical correctness.
Prefer --netlist pointing to a fresh kicad-cli export over the saved default.
Exit 1 means mismatches require review; extra mechanical PCB items are informational.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from sexp import parse, find, find_all

ROOT = Path(__file__).resolve().parents[1]


def audit(pcb, netlist):
    board = parse(pcb.read_text())[0]
    xml = ET.parse(netlist)
    parts, pins, conflicts = {}, {}, []
    for fp in find_all(board, 'footprint'):
        fields = {p[1]: p[2] for p in find_all(fp, 'property')}
        ref = fields.get('Reference')
        parts[ref] = {'value': fields.get('Value'), 'footprint': str(fp[1]),
                      **{k: fields.get(k, '') for k in ('MPN', 'Manufacturer')}}
        for pad in find_all(fp, 'pad'):
            net = find(pad, 'net')
            if net:
                key, name = (ref, str(pad[1])), str(net[-1])
                if key in pins and pins[key] != name:
                    conflicts.append({'pin': key, 'nets': [pins[key], name]})
                pins[key] = name
    expected = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name']
                for net in xml.findall('.//nets/net') for n in net.findall('node')}
    mismatches = [{'pin': key, 'netlist': expected.get(key), 'pcb': pins.get(key)}
                  for key in sorted(set(expected) | set(pins)) if expected.get(key) != pins.get(key)]
    components = {}
    for c in xml.findall('.//components/comp'):
        custom = {f.attrib['name']: f.text or '' for f in c.findall('fields/field')}
        components[c.attrib['ref']] = {**{k: c.findtext(k) for k in ('value', 'footprint')},
                                     **{k: custom.get(k, '') for k in ('MPN', 'Manufacturer')}}
    fields = [{'ref': ref, 'field': field, 'netlist': value, 'pcb': parts.get(ref, {}).get(field)}
              for ref, values in components.items() for field, value in values.items()
              if value != parts.get(ref, {}).get(field)]
    return {'inputs': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (pcb, netlist)},
            'netlisted_pins': len(expected), 'pcb_net_assigned_pins': len(pins),
            'net_mismatches': mismatches, 'duplicate_pad_net_conflicts': conflicts,
            'component_field_mismatches': fields,
            'extra_pcb_references': sorted(set(parts) - set(components)),
            'passed': not (mismatches or conflicts or fields)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcb', type=Path, default=ROOT / 'wpc_power_driver_cost.kicad_pcb')
    parser.add_argument('--netlist', type=Path, default=ROOT / 'output/reports/wpc_power_driver_cost-netlist.xml')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/verification/artifacts.json')
    args = parser.parse_args()
    report = audit(args.pcb, args.netlist)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f"{report['netlisted_pins']} netlisted pins; {len(report['net_mismatches'])} net mismatches; "
          f"{len(report['component_field_mismatches'])} component field mismatches")
    print(f"{'PASS' if report['passed'] else 'FAIL (review required)'}: {args.output}")
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
