"""Generate the PCB from parts.json / nets.json / placement."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import kicad_pcb as P
import placement_cost as PL

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def main():
    parts = json.load(open(os.path.join(OUT, '.scratch', 'parts.json')))
    nets = json.load(open(os.path.join(OUT, '.scratch', 'nets.json')))
    padnet = {}
    for net, pins in nets.items():
        for ref, pin in pins:
            padnet[(ref, pin)] = net
    b = P.Board('WPC Power Driver Board - cost-optimised modern re-implementation (A-12697-3 form factor)')
    W, H = PL.BOARD_W, PL.BOARD_H
    b.rounded_outline(W, H, 4.0)
    missing = []
    items = {}
    for ref, p in sorted(parts.items()):
        if ref in getattr(PL, 'POS_MM', {}):                 # parts placed directly in board millimetres (added after the assembly-drawing placement)
            x, y, r = PL.POS_MM[ref]
        elif ref not in PL.POS:
            missing.append(ref); continue
        else:
            px, py, rot = PL.POS[ref]
            x, y, r = PL.board_xy(px, py, rot)
        items[ref] = dict(lib=p['fp'], x=x, y=y, rot=r)
    if missing:
        print('NO PLACEMENT for', missing)
    import deoverlap
    # connectors, holes, fuses, bridges and the big capacitors keep their original A-12697-3 positions exactly
    fixed = [r for r in items if r.startswith(('J', 'H', 'F', 'BR')) or r in ('C5', 'C6', 'C7', 'C11', 'C30')]   # C8/C32 (+50V) were re-arranged on the modern board and may relax
    # connectors: clamp so that their courtyard is >= 2 mm inside the board edge
    for r in fixed:
        it = items[r]
        bb = deoverlap.placed_bbox(it['lib'], 0, 0, it['rot'])
        fp = P.load_fp(it['lib']); cx, cy = P.pad_centroid(fp); dx, dy = P.rot_vec(cx, cy, it['rot'])
        x0, y0 = it['x'] - dx, it['y'] - dy
        bx0, by0, bx1, by1 = bb[0] + x0, bb[1] + y0, bb[2] + x0, bb[3] + y0
        if bx0 < 2.0: it['x'] += 2.0 - bx0
        if bx1 > W - 2.0: it['x'] -= bx1 - (W - 2.0)
        if by0 < 2.0: it['y'] += 2.0 - by0
        if by1 > H - 2.0: it['y'] -= by1 - (H - 2.0)
    items, niter, disp = deoverlap.relax(items, W, H, margin=float(os.environ.get('DEOVERLAP_MARGIN', '0.9')), edge=2.0, fixed=fixed, iters=3000)
    print('deoverlap iterations', niter, 'largest moves', [(round(d, 1), r) for d, r in disp[:6]])
    # report residual overlaps
    boxes = {}
    for r, it in items.items():
        fp = P.load_fp(it['lib']); cx, cy = P.pad_centroid(fp); dx, dy = P.rot_vec(cx, cy, it['rot'])
        bb = deoverlap.placed_bbox(it['lib'], it['x'] - dx, it['y'] - dy, it['rot']); boxes[r] = bb
    rs = list(boxes); res = []
    for i in range(len(rs)):
        for j in range(i + 1, len(rs)):
            A, Bb = boxes[rs[i]], boxes[rs[j]]
            if min(A[2], Bb[2]) - max(A[0], Bb[0]) > 0.05 and min(A[3], Bb[3]) - max(A[1], Bb[1]) > 0.05:
                res.append((rs[i], rs[j]))
    print('residual courtyard overlaps:', len(res), res[:20])
    for ref, it in items.items():
        p = parts[ref]
        pn = {pin: net for (rf, pin), net in padnet.items() if rf == ref}
        b.footprint(ref, p['fp'], it['x'], it['y'], it['rot'], p['value'], pn, dnp=p.get('dnp', False),
                    extra_fields={'MPN': p.get('pn', ''), 'Sheet': p.get('sheet', '')})
    json.dump(items, open(os.path.join(OUT, '.scratch', 'placed.json'), 'w'), indent=1)
    # heatsink keep-out drawings (Dwgs.User) for triac heatsinks, Q1 heatsink, BR1/BR2 heatsink assembly
    def rect_draw(px0, py0, px1, py1, label):
        x0, y0, _ = PL.board_xy(px0, py0, 0); x1, y1, _ = PL.board_xy(px1, py1, 0)
        b.rect((min(x0, x1), min(y0, y1)), (max(x0, x1), max(y0, y1)), 'Dwgs.User')
        b.text(label, ((x0 + x1) / 2, (y0 + y1) / 2), 'Dwgs.User', 1.5, 0.2)
    rect_draw(130, 860, 1140, 1240, 'HEAT SINK ASSY (BR1 GBJ1510 / BR2 GBU8J)')
    for q, (x, y) in PL.GI_TRIAC.items():
        rect_draw(x - 120, y - 120, x + 120, y + 120, f'{q} CLIP HEATSINK 577002B00000G')
    # silkscreen texts
    b.text('WPC POWER DRIVER - MODERN (COST)  rev A', (W / 2, H / 2 - 6), 'B.SilkS', 4.0, 0.5)
    b.text('Functional replacement for Williams A-12697-3 (DPAK MOSFET drivers, buck regulators) - not a Williams product', (W / 2, H / 2), 'B.SilkS', 2.0, 0.25)
    b.text('CAUTION: the "+50V" rail is ~70 V DC; 51/16/13/9 VAC and 6.3 VAC G.I. present on this board', (W / 2, H / 2 + 6), 'B.SilkS', 2.5, 0.3)
    # GND pours on both layers (skipped with NO_ZONES=1 for autorouting; added back afterwards by tools/add_zones.py)
    # 4-layer stack: In1.Cu is a solid GND plane; outer-layer GND pours optional (PLANE_ONLY=1 keeps only the plane)
    if not os.environ.get('NO_ZONES'):
        b.zone('GND', 'In1.Cu', [(1, 1), (W - 1, 1), (W - 1, H - 1), (1, H - 1)], 'GND_PLANE', clearance=0.4, min_thick=0.4, thermal_gap=0.5, spoke=1.2)
        if not os.environ.get('PLANE_ONLY'):
            for layer, nm in (('F.Cu', 'GND_F'), ('B.Cu', 'GND_B')):
                b.zone('GND', layer, [(1, 1), (W - 1, 1), (W - 1, H - 1), (1, H - 1)], nm)
    out = os.path.join(OUT, 'wpc_power_driver_cost.kicad_pcb')
    b.write(out)
    print('wrote', out, 'footprints', len(b.footprints), 'nets', len(b.nets))

if __name__ == '__main__':
    main()
