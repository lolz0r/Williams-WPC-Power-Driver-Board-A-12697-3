import pcbnew, sys, math
b = pcbnew.LoadBoard(sys.argv[1]); cands = [tuple(map(float, a.split(','))) for a in sys.argv[2:]]
def d_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    if L2 == 0: return math.hypot(px - ax, py - ay)
    u = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2)); return math.hypot(px - ax - u * dx, py - ay - u * dy)
F = [(t.GetStart().x / 1e6, t.GetStart().y / 1e6, t.GetEnd().x / 1e6, t.GetEnd().y / 1e6, t.GetWidth() / 2e6) for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetLayer() == pcbnew.F_Cu]
V = [(t.GetStart().x / 1e6, t.GetStart().y / 1e6, t.GetWidth(pcbnew.F_Cu) / 2e6) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
pads = [p for f in b.GetFootprints() for p in f.Pads()]
for (x, y) in cands:
    d = min([d_seg(x, y, *s[:4]) - s[4] for s in F] + [math.hypot(x - v[0], y - v[1]) - v[2] for v in V] + [99])
    dp = min([math.hypot(x - p.GetPosition().x / 1e6, y - p.GetPosition().y / 1e6) - max(p.GetBoundingBox().GetWidth(), p.GetBoundingBox().GetHeight()) / 2e6 for p in pads])
    print('(%.0f, %.0f): nearest F.Cu copper %.1f mm, nearest pad %.1f mm' % (x, y, d, dp))
