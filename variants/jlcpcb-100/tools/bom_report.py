"""Markdown BOM with one distributor link per line item + qty-1 and qty-100 cost roll-ups (from .scratch/parts.json written by
gen_project.py).  Also writes output/bom/cost_summary.json (per cost group) for the README.
Qty-1 prices: DigiKey/Mouser single-unit prices captured during sourcing; where none was visible an estimate (marked ~) is used so
that the roll-up is complete.  Qty-100 prices: estimated unit price when buying for 100 boards (see tools/sourcing.py)."""
import os, json, collections, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
parts = json.load(open(os.path.join(ROOT, '.scratch', 'parts.json')))
import sys; sys.path.insert(0, os.path.dirname(__file__))
from sourcing import SRC

FP_FUSE_TAG = 'Fuseholder_Clip-5x20mm'
groups = collections.OrderedDict()
n_fuse_positions = 0
for ref, p in sorted(parts.items(), key=lambda kv: (kv[1].get('pn', ''), kv[0])):
    if ref.startswith('H'): continue
    if FP_FUSE_TAG in p['fp']:
        n_fuse_positions += 1
        if p.get('pn') == SRC['FUSECLIP']['mpn']:   # F101/F102: clips only - counted in the synthetic clip line below
            continue
    key = (p.get('pn', ''), p['value'] if not p.get('pn') else '', p['fp'], bool(p.get('dnp')))
    g = groups.setdefault(key, dict(refs=[], p=p))
    g['refs'].append(ref)

def natural(r):
    m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2))) if m else (r, 0)

def unit1(p):
    """(price, estimated?) for the qty-1 roll-up."""
    if p.get('price') is not None: return p['price'], False
    if p.get('price_est') is not None: return p['price_est'], True
    return None, False

def group_of(p):
    d = (p.get('desc') or '') + ' ' + (p.get('pn') or '') + ' ' + (p.get('value') or '')
    pn = p.get('pn') or ''
    if 'MOSFET' in d: return 'MOSFETs'
    if 'Bridge rectifier' in d or pn.startswith('STPS20M100'): return 'Bridge rectifiers'
    if pn.startswith(('TPS54360', 'SRP1265', 'B560C')): return 'Buck converters (IC, inductor, diode)'
    if 'snap-in' in d or 'radial' in d: return 'Electrolytic capacitors'
    if 'Fuse' in d: return 'Fuses + clips'
    if 'header' in d.lower() or pn.startswith(('0026604', '0022232', '30334')): return 'Connectors'
    if pn.startswith(('74HCT', 'SN74', 'LM339', 'TBD62083')): return 'Logic / comparators / driver'
    if pn.startswith(('BTA16', 'MMBT4401', '577002', '7019BG', '7020BG', '6224BG', 'MPMS', 'MHNZ')): return 'Triacs + gate transistors + heatsinks'
    if pn.startswith(('S1M', 'S3M', '1N4148', 'LTST')): return 'Diodes + LEDs'
    if pn.startswith(('RC0805', 'RC2512', 'RL2512', 'CL21', 'CL32', '4610X')): return 'SMD passives'
    if 'Relay' in d: return 'Relay option (DNP)'
    return 'Misc / test points'

lines = ['# Bill of materials - WPC Power Driver Board (cost-optimised modern version)', '',
         'One line per orderable part.  Links are DigiKey product pages (product IDs seen in Sep 2026 searches) or DigiKey exact part-number searches for passives / connector variants.',
         'Unit $ (1) = DigiKey (Mouser for the IRLR024N / IRFR5305 DPAK parts) single-unit price where it was visible during sourcing; `~` marks an estimate used so that the roll-up is complete.',
         'Unit $ (100) = estimated unit price when buying for 100 boards (100 x the per-board quantity, i.e. reel / 1000-piece breaks for the parts used 8-32 times per board).', '',
         '| Qty | Refs | Value | Manufacturer | MPN | Description | Footprint | Unit $ (1) | Ext $ (1) | Unit $ (100) | Ext $ (100) | DNP |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
tot1 = tot100 = 0.0; n_items = 0; n_est = 0; n_unpriced = 0
by_group = collections.defaultdict(lambda: [0.0, 0.0, 0])
rows = []
for (pn, val, fp, dnp), g in groups.items():
    p = g['p']; refs = sorted(g['refs'], key=natural); q = len(refs)
    rows.append((q, refs, p, fp, dnp))
# synthetic mechanical lines: fuse clips (2 per fused / clip-only position), the heatsinks and their hardware (docs/THERMAL_AND_PROTECTION.md)
clip = dict(SRC['FUSECLIP']); clip['value'] = 'clip'; clip['desc'] = clip['desc'] + f' - {n_fuse_positions} positions incl. F101/F102 (clips only)'
clip.update(pn=clip['mpn'], dnp=False)
rows.append((2 * n_fuse_positions, ['F101-F116 (2 per position)'], clip, 'Fuse:' + FP_FUSE_TAG + '_Keystone_3517', False))
n_hs = 0
for key, qty, refs, note in [('HS7019', 5, 'Q10, Q12, Q14, Q16, Q18 (mechanical)', 'G.I. triacs, bolted to the insulated TO-220 tab'),
                             ('HS6224', 1, 'BR3 (mechanical)', 'GBPC3510W, on the upward-facing metal base, M4 through the centre hole'),
                             ('M3X12', 5, 'Q10-Q18 hardware', 'with M3 nut; thread-lock'), ('M3NUT', 5, 'Q10-Q18 hardware', ''),
                             ('M4X16', 1, 'BR3 hardware', 'captive under the block (no PCB hole in this revision)'), ('M4NUT', 1, 'BR3 hardware', '')]:
    hs = dict(SRC[key]); hs['value'] = 'heatsink' if key.startswith('HS') else 'hardware'; hs.update(pn=hs['mpn'], dnp=False, desc=hs['desc'] + (f' - {note}' if note else ''))
    rows.append((qty, [refs], hs, '-', False)); n_hs += qty if key.startswith('HS') else 0

def fmt(v, est=False): return '' if v is None else (('~' if est else '') + f'{v:.2f}')
for q, refs, p, fp, dnp in rows:
    u1, est = unit1(p); u100 = p.get('price100')
    e1 = None if (u1 is None or dnp) else u1 * q; e100 = None if (u100 is None or dnp) else u100 * q
    if not dnp:
        n_items += q
        if e1 is not None: tot1 += e1
        if est: n_est += q
        if u1 is None and u100 is None and p.get('pn'): n_unpriced += q
        if e100 is not None: tot100 += e100
        grp = by_group[group_of(p)]; grp[0] += e1 or 0; grp[1] += e100 or 0; grp[2] += q
    link = p.get('link', ''); pn = p.get('pn', ''); mpn = f'[{pn}]({link})' if link else pn
    refs_s = ', '.join(refs) if len(refs) <= 12 else ', '.join(refs[:10]) + f', ... ({q} total)'
    lines.append(f"| {q} | {refs_s} | {p['value']} | {p.get('mfr', '')} | {mpn} | {p.get('desc', '')} | {fp.split(':')[-1]} | {fmt(u1, est)} | {fmt(e1, est)} | {fmt(u100)} | {fmt(e100)} | {'DNP' if dnp else ''} |")
lines += ['', f'**{n_items} placed parts (incl. {2 * n_fuse_positions} fuse clips, {n_hs} heatsinks and 12 screws / nuts) in {len(rows)} line items.  Parts cost per board: {tot1:.2f} USD at qty 1 ({n_est} parts priced by estimate), '
          f'{tot100:.2f} USD at qty 100; {n_unpriced} parts without any price.**', '', '## Cost by group', '',
          '| group | parts | per board, qty 1 (USD) | per board, qty 100 (USD) |', '|---|---|---|---|']
order = ['MOSFETs', 'Electrolytic capacitors', 'Connectors', 'Bridge rectifiers', 'Fuses + clips', 'Buck converters (IC, inductor, diode)', 'Logic / comparators / driver',
         'SMD passives', 'Diodes + LEDs', 'Triacs + gate transistors + heatsinks', 'Misc / test points', 'Relay option (DNP)']
summary = {}
for gname in order + [g for g in by_group if g not in order]:
    if gname not in by_group: continue
    e1, e100, n = by_group[gname]
    lines.append(f'| {gname} | {n} | {e1:.2f} | {e100:.2f} |'); summary[gname] = dict(qty=n, cost1=round(e1, 2), cost100=round(e100, 2))
lines.append(f'| **total components per board** | {n_items} | **{tot1:.2f}** | **{tot100:.2f}** |')
lines += ['', 'Not included: the bare 4-layer 449 x 273 mm PCB, assembly, thermal compound for the six bolted heatsinks, M4 hardware for the 8 mounting holes, shipping / tax / attrition.  Heatsinks: docs/THERMAL_AND_PROTECTION.md (the OEM chassis bracket is replaced by device-mounted Boyd heatsinks on the triacs and BR3; the +18V / +20V / +5V raw / +12V power bridges are discrete D2PAK Schottky diodes cooled by board copper).']
os.makedirs(os.path.join(ROOT, 'output', 'bom'), exist_ok=True)
open(os.path.join(ROOT, 'output', 'bom', 'BOM-cost.md'), 'w').write('\n'.join(lines) + '\n')
summary['_total'] = dict(qty=n_items, cost1=round(tot1, 2), cost100=round(tot100, 2), line_items=len(rows), estimated_qty1=n_est)
json.dump(summary, open(os.path.join(ROOT, 'output', 'bom', 'cost_summary.json'), 'w'), indent=1)
print(f'BOM: {len(rows)} line items, {n_items} parts, qty-1 {tot1:.2f} USD ({n_est} estimated), qty-100 {tot100:.2f} USD, {n_unpriced} unpriced')
for g in summary:
    if g != '_total': print(f'  {g:42s} {summary[g]["qty"]:4d}  {summary[g]["cost1"]:7.2f}  {summary[g]["cost100"]:7.2f}')
