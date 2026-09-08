import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); x0, y0, x1, y1 = map(float, sys.argv[2:6]); layers = sys.argv[6].split(',') if len(sys.argv) > 6 else None
def seg_hits(ax, ay, bx, by):
    # segment vs window (mm) via Liang-Barsky
    dx, dy = bx - ax, by - ay; t0, t1 = 0.0, 1.0
    for p, q in ((-dx, ax - x0), (dx, x1 - ax), (-dy, ay - y0), (dy, y1 - ay)):
        if p == 0:
            if q < 0: return False
        else:
            t = q / p
            if p < 0: t0 = max(t0, t)
            else: t1 = min(t1, t)
    return t0 <= t1
for f in b.GetFootprints():
    for p in f.Pads():
        P = p.GetPosition()
        if x0 <= P.x/1e6 <= x1 and y0 <= P.y/1e6 <= y1:
            try: sz = p.GetSize(pcbnew.F_Cu)
            except TypeError: sz = p.GetSize()
            print('PAD %s.%s %s @(%.2f,%.2f) %.2fx%.2f rot%.0f %s' % (f.GetReference(), p.GetNumber(), p.GetNetname(), P.x/1e6, P.y/1e6, sz.x/1e6, sz.y/1e6, p.GetOrientationDegrees(), 'TH' if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD else ''))
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        P = t.GetStart()
        if x0 <= P.x/1e6 <= x1 and y0 <= P.y/1e6 <= y1: print('VIA %s @(%.2f,%.2f) d%.1f' % (t.GetNetname(), P.x/1e6, P.y/1e6, t.GetWidth()/1e6))
    else:
        ln = b.GetLayerName(t.GetLayer())
        if layers and ln not in layers: continue
        S, E = t.GetStart(), t.GetEnd()
        if seg_hits(S.x/1e6, S.y/1e6, E.x/1e6, E.y/1e6): print('TRK %s %s (%.2f,%.2f)->(%.2f,%.2f) w%.1f' % (t.GetNetname(), ln, S.x/1e6, S.y/1e6, E.x/1e6, E.y/1e6, t.GetWidth()/1e6))
