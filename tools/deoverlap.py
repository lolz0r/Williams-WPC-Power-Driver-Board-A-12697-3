"""Push-apart placement relaxation using footprint courtyard bounding boxes."""
import math
from sexp import find, find_all
import kicad_pcb as P

def fp_bbox(lib_id):
    """Courtyard bbox (x0,y0,x1,y1) of library footprint (unrotated), falls back to pads+1mm."""
    fp = P.load_fp(lib_id)
    xs, ys = [], []
    for g in find_all(fp, 'fp_line') + find_all(fp, 'fp_rect') + find_all(fp, 'fp_circle') + find_all(fp, 'fp_poly'):
        lay = find(g, 'layer')
        if not lay or lay[1] != 'F.CrtYd':
            continue
        if g[0] == 'fp_circle':
            c = find(g, 'center'); e = find(g, 'end'); r = math.hypot(float(e[1]) - float(c[1]), float(e[2]) - float(c[2]))
            xs += [float(c[1]) - r, float(c[1]) + r]; ys += [float(c[2]) - r, float(c[2]) + r]
        elif g[0] == 'fp_poly':
            for pt in find_all(find(g, 'pts'), 'xy'):
                xs.append(float(pt[1])); ys.append(float(pt[2]))
        else:
            for k in ('start', 'end'):
                p = find(g, k); xs.append(float(p[1])); ys.append(float(p[2]))
    if not xs:
        for p in find_all(fp, 'pad'):
            at = find(p, 'at'); sz = find(p, 'size')
            xs += [float(at[1]) - float(sz[1]) / 2 - 1, float(at[1]) + float(sz[1]) / 2 + 1]
            ys += [float(at[2]) - float(sz[2]) / 2 - 1, float(at[2]) + float(sz[2]) / 2 + 1]
    return min(xs), min(ys), max(xs), max(ys)

def placed_bbox(lib_id, x0, y0, rot):
    """Axis-aligned bbox of the courtyard for footprint origin (x0,y0) rotated rot."""
    bx0, by0, bx1, by1 = fp_bbox(lib_id)
    pts = [P.rot_vec(x, y, rot) for x, y in ((bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1))]
    xs = [x0 + p[0] for p in pts]; ys = [y0 + p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

def relax(items, board_w, board_h, margin=0.6, edge=1.5, fixed=(), iters=400):
    """items: dict ref -> dict(lib, x, y, rot) where x,y is the pad-centroid position.
    Moves non-fixed items to remove courtyard overlaps.  Returns updated dict."""
    import kicad_pcb as P2
    info = {}
    for ref, it in items.items():
        fp = P2.load_fp(it['lib'])
        cx, cy = P2.pad_centroid(fp)
        dx, dy = P2.rot_vec(cx, cy, it['rot'])
        bb = fp_bbox(it['lib'])
        # bbox relative to pad centroid, rotated
        pts = [P2.rot_vec(x - cx, y - cy, it['rot']) for x, y in ((bb[0], bb[1]), (bb[2], bb[1]), (bb[0], bb[3]), (bb[2], bb[3]))]
        hx = max(abs(p[0]) for p in pts); hy = max(abs(p[1]) for p in pts)
        # asymmetric bbox
        ox0 = min(p[0] for p in pts); ox1 = max(p[0] for p in pts); oy0 = min(p[1] for p in pts); oy1 = max(p[1] for p in pts)
        info[ref] = dict(x=it['x'], y=it['y'], ox0=ox0, ox1=ox1, oy0=oy0, oy1=oy1, area=(ox1 - ox0) * (oy1 - oy0), fixed=ref in fixed,
                         x0=it['x'], y0=it['y'])
    refs = list(info)
    def box(r):
        i = info[r]; return (i['x'] + i['ox0'] - margin / 2, i['y'] + i['oy0'] - margin / 2, i['x'] + i['ox1'] + margin / 2, i['y'] + i['oy1'] + margin / 2)
    moved_total = 0
    for it in range(iters):
        moved = 0
        # spatial hash
        cell = 20.0
        grid = {}
        for r in refs:
            b = box(r)
            for gx in range(int(b[0] // cell), int(b[2] // cell) + 1):
                for gy in range(int(b[1] // cell), int(b[3] // cell) + 1):
                    grid.setdefault((gx, gy), []).append(r)
        seen = set()
        for lst in grid.values():
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    a, b_ = lst[i], lst[j]
                    if (a, b_) in seen: continue
                    seen.add((a, b_))
                    A, Bb = box(a), box(b_)
                    ox = min(A[2], Bb[2]) - max(A[0], Bb[0]); oy = min(A[3], Bb[3]) - max(A[1], Bb[1])
                    if ox <= 0 or oy <= 0: continue
                    ia, ib = info[a], info[b_]
                    if ia['fixed'] and ib['fixed']: continue
                    # move along the axis of least overlap
                    if ox < oy:
                        d = ox + 0.05; sign = 1 if (ia['x'] + (ia['ox0'] + ia['ox1']) / 2) < (ib['x'] + (ib['ox0'] + ib['ox1']) / 2) else -1
                        if ia['fixed']: ib['x'] += sign * d
                        elif ib['fixed']: ia['x'] -= sign * d
                        else:
                            wa = ib['area'] / (ia['area'] + ib['area']); ia['x'] -= sign * d * wa; ib['x'] += sign * d * (1 - wa)
                    else:
                        d = oy + 0.05; sign = 1 if (ia['y'] + (ia['oy0'] + ia['oy1']) / 2) < (ib['y'] + (ib['oy0'] + ib['oy1']) / 2) else -1
                        if ia['fixed']: ib['y'] += sign * d
                        elif ib['fixed']: ia['y'] -= sign * d
                        else:
                            wa = ib['area'] / (ia['area'] + ib['area']); ia['y'] -= sign * d * wa; ib['y'] += sign * d * (1 - wa)
                    moved += 1
        # keep inside board
        for r in refs:
            i = info[r]
            if i['fixed']: continue
            b = box(r)
            if b[0] < edge: i['x'] += edge - b[0]; moved += 1
            if b[2] > board_w - edge: i['x'] -= b[2] - (board_w - edge); moved += 1
            if b[1] < edge: i['y'] += edge - b[1]; moved += 1
            if b[3] > board_h - edge: i['y'] -= b[3] - (board_h - edge); moved += 1
        moved_total += moved
        if moved == 0:
            break
    out = {}
    for r in refs:
        i = info[r]
        out[r] = dict(items[r]); out[r]['x'] = round(i['x'], 3); out[r]['y'] = round(i['y'], 3)
    disp = sorted(((math.hypot(info[r]['x'] - info[r]['x0'], info[r]['y'] - info[r]['y0']), r) for r in refs), reverse=True)
    return out, it + 1, disp[:10]
