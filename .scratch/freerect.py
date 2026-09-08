"""Find free rectangles (no footprint bounding box + 1.5 mm margin, no NPTH) of a given size inside a window.  Args: board x0 y0 x1 y1 w h [w h ...]"""
import pcbnew, sys, numpy as np
b = pcbnew.LoadBoard(sys.argv[1]); x0, y0, x1, y1 = map(float, sys.argv[2:6]); sizes = [(float(sys.argv[i]), float(sys.argv[i + 1])) for i in range(6, len(sys.argv), 2)]
W, H = int(x1 - x0), int(y1 - y0); occ = np.zeros((H, W), dtype=bool); M = 1.5
for f in b.GetFootprints():
    bb = f.GetBoundingBox(False, False); ax, ay, bx, by = bb.GetLeft() / 1e6 - M, bb.GetTop() / 1e6 - M, bb.GetRight() / 1e6 + M, bb.GetBottom() / 1e6 + M
    ia, ja = max(0, int(ax - x0)), max(0, int(ay - y0)); ib, jb = min(W, int(bx - x0) + 1), min(H, int(by - y0) + 1)
    if ib > ia and jb > ja: occ[ja:jb, ia:ib] = True
bb = b.GetBoardEdgesBoundingBox(); occ[:, :max(0, int(bb.GetLeft() / 1e6 + 2 - x0))] = True; occ[:, max(0, int(bb.GetRight() / 1e6 - 2 - x0)):] = True; occ[:max(0, int(bb.GetTop() / 1e6 + 2 - y0)), :] = True; occ[max(0, int(bb.GetBottom() / 1e6 - 2 - y0)):, :] = True
S = np.zeros((H + 1, W + 1), dtype=np.int32); S[1:, 1:] = np.cumsum(np.cumsum(occ, 0), 1)
for w, h in sizes:
    w, h = int(w), int(h); found = []
    for j in range(0, H - h):
        for i in range(0, W - w):
            if S[j + h, i + w] - S[j, i + w] - S[j + h, i] + S[j, i] == 0: found.append((x0 + i, y0 + j))
    # report distinct spots (greedy, 8 mm apart)
    picked = []
    for p in found:
        if all(abs(p[0] - q[0]) > 8 or abs(p[1] - q[1]) > 8 for q in picked): picked.append(p)
    print(f'free {w}x{h} mm rectangles (top-left corners): {len(found)} cells, distinct spots: {picked[:14]}')
