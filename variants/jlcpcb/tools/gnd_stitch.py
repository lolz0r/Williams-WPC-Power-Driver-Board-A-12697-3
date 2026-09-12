"""Add a stitching via next to every SMD pad of a plane net (default GND) that has no via/track of its own.
Freerouting 2.1 fails on connections whose target is the conduction area (NullPointerException), so SMD GND pads come back
unconnected from the SES import.  A via 1.2/0.6 mm is placed on the outward side of the pad (tries 8 directions, keeps the
first one that is clear of every other copper item) and joined to the pad with a short 0.4 mm track on F.Cu.
Usage: python3 tools/gnd_stitch.py board.kicad_pcb [--net GND] [--dry]"""
import sys, os, math, uuid, re
sys.path.insert(0, os.path.dirname(__file__))
from sexp import parse, dump, find, find_all, S, Sym

def rot(x, y, a):
    """KiCad board rotation (y down, CCW positive on screen) - same convention as kicad_pcb.rot_vec."""
    r = math.radians(a); return x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r)

def main(pcb, net='GND', dry=False):
    doc = parse(open(pcb).read())[0]
    pads = []      # (net, layer_set, cx, cy, hw, hh, angle, ref, padname, is_smd)
    for fp in find_all(doc, 'footprint'):
        at = find(fp, 'at'); fx, fy = float(at[1]), float(at[2]); fa = float(at[3]) if len(at) > 3 else 0.0
        ref = ''
        for pr in find_all(fp, 'property'):
            if pr[1] == 'Reference': ref = pr[2]
        for pad in find_all(fp, 'pad'):
            pn = find(pad, 'net'); pnet = str(pn[-1]) if pn else ''
            pat = find(pad, 'at'); px, py = float(pat[1]), float(pat[2]); pa = float(pat[3]) if len(pat) > 3 else fa
            sz = find(pad, 'size'); w, h = float(sz[1]), float(sz[2])
            dx, dy = rot(px, py, fa)
            layers = [str(l) for l in find(pad, 'layers')[1:]]
            smd = str(pad[2]) == 'smd'
            pads.append(dict(net=pnet, x=fx + dx, y=fy + dy, w=w, h=h, a=pa, ref=ref, name=str(pad[1]), smd=smd,
                             front=any(l in ('F.Cu', '*.Cu', 'F&B.Cu') for l in layers), layers=layers))
    segs = [dict(net=str(find(s, 'net')[-1]), x1=float(find(s, 'start')[1]), y1=float(find(s, 'start')[2]), x2=float(find(s, 'end')[1]), y2=float(find(s, 'end')[2]),
                 w=float(find(s, 'width')[1]), layer=str(find(s, 'layer')[1])) for s in find_all(doc, 'segment')]
    vias = [dict(net=str(find(v, 'net')[-1]), x=float(find(v, 'at')[1]), y=float(find(v, 'at')[2]), d=float(find(v, 'size')[1])) for v in find_all(doc, 'via')]
    # which SMD GND pads already touch a segment or via of the net?
    def pad_touch(p):
        r = max(p['w'], p['h']) / 2 + 0.05
        for v in vias:
            if v['net'] == net and math.hypot(v['x'] - p['x'], v['y'] - p['y']) < r + v['d'] / 2: return True
        for s in segs:
            if s['net'] != net or s['layer'] != 'F.Cu': continue
            if min(math.hypot(s['x1'] - p['x'], s['y1'] - p['y']), math.hypot(s['x2'] - p['x'], s['y2'] - p['y'])) < r + s['w'] / 2: return True
        return False
    todo = [p for p in pads if p['net'] == net and p['smd'] and p['front'] and not pad_touch(p)]
    print(f'{len(todo)} SMD {net} pads without a via/track')
    VIA_D, VIA_DRILL, CLR, TW = 1.2, 0.6, 0.25, 0.4
    def clear(x, y, rad, self_pad):
        """True if a disc (x,y,rad) is >= CLR from every copper item of another net (any layer for vias) and from own-net SMD pads too."""
        for p in pads:
            if p is self_pad: continue
            if p['net'] == net and p['smd']: pass  # own-net SMD pads: keep clearance too (do not short over the neighbour pad)
            elif p['net'] == net: continue
            # rotate point into pad frame
            lx, ly = rot(x - p['x'], y - p['y'], -p['a'])
            ddx = max(abs(lx) - p['w'] / 2, 0); ddy = max(abs(ly) - p['h'] / 2, 0)
            if math.hypot(ddx, ddy) < rad + CLR: return False
        for v in vias:
            if math.hypot(v['x'] - x, v['y'] - y) < rad + v['d'] / 2 + (0.1 if v['net'] == net else CLR): return False
        for s in segs:
            if s['net'] == net: continue
            # point-segment distance
            vx, vy = s['x2'] - s['x1'], s['y2'] - s['y1']; L2 = vx * vx + vy * vy
            t = 0 if L2 == 0 else max(0, min(1, ((x - s['x1']) * vx + (y - s['y1']) * vy) / L2))
            d = math.hypot(x - (s['x1'] + t * vx), y - (s['y1'] + t * vy))
            if d < rad + s['w'] / 2 + CLR: return False
        return True
    new = []; failed = []
    todo.sort(key=lambda p: -min(p['w'], p['h']))     # exposed pads first (their via-in-pad must not be taken by a neighbour)
    for p in todo:
        placed = False
        if min(p['w'], p['h']) >= 2.0:      # exposed thermal pad: via-in-pad at the centre
            vx, vy = round(p['x'], 3), round(p['y'], 3)
            new.append(S('via', S('at', vx, vy), S('size', VIA_D), S('drill', VIA_DRILL), S('layers', 'F.Cu', 'B.Cu'), S('net', net), S('uuid', str(uuid.uuid4()))))
            new.append(S('segment', S('start', vx, vy), S('end', round(vx + 0.01, 3), vy), S('width', TW), S('layer', 'F.Cu'), S('net', net), S('uuid', str(uuid.uuid4()))))
            vias.append(dict(net=net, x=vx, y=vy, d=VIA_D)); continue
        for dist in (1.3, 1.6, 2.0, 2.5):
            for ang in (0, 180, 90, 270, 45, 135, 225, 315):
                # step away along the pad's long axis first
                ox, oy = rot(dist, 0, ang)
                vx, vy = round(p['x'] + ox, 3), round(p['y'] + oy, 3)
                if not clear(vx, vy, VIA_D / 2, p): continue
                # the short track must also be clear along its way (check mid point)
                mx, my = (vx + p['x']) / 2, (vy + p['y']) / 2
                if not clear(mx, my, TW / 2, p): continue
                new.append(S('via', S('at', vx, vy), S('size', VIA_D), S('drill', VIA_DRILL), S('layers', 'F.Cu', 'B.Cu'), S('net', net), S('uuid', str(uuid.uuid4()))))
                new.append(S('segment', S('start', round(p['x'], 3), round(p['y'], 3)), S('end', vx, vy), S('width', TW), S('layer', 'F.Cu'), S('net', net), S('uuid', str(uuid.uuid4()))))
                vias.append(dict(net=net, x=vx, y=vy, d=VIA_D)); segs.append(dict(net=net, x1=p['x'], y1=p['y'], x2=vx, y2=vy, w=TW, layer='F.Cu'))
                placed = True; break
            if placed: break
        if not placed: failed.append(f"{p['ref']}-{p['name']}")
    print(f'placed {len(new) // 2} stitch vias; failed: {failed}')
    if dry: return
    txt = open(pcb).read().rstrip(); assert txt.endswith(')')
    open(pcb, 'w').write(txt[:-1] + '\n'.join('\t' + dump(it, 1) for it in new) + '\n)\n')

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    net = 'GND'
    if '--net' in sys.argv: net = sys.argv[sys.argv.index('--net') + 1]; a = [x for x in a if x != net]
    main(a[0], net, '--dry' in sys.argv)
