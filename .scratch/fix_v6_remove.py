import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); victims = []
def inside(P, x0, y0, x1, y1): return x0 <= P.x / 1e6 <= x1 and y0 <= P.y / 1e6 <= y1
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA': continue
    n = t.GetNetname(); S, E = t.GetStart(), t.GetEnd()
    if n in ('CLK_LAMP_ROW', 'D0', 'ROWCLR1') and inside(S, 384.5, 146.0, 397.6, 156.0) and inside(E, 384.5, 146.0, 397.6, 156.0): victims.append(t)
    elif n == 'CLK_LAMP_ROW' and t.GetLayer() == pcbnew.In2_Cu and abs(S.y / 1e6 - 148.2) < 0.05 and abs(E.y / 1e6 - 148.2) < 0.05 and min(S.x, E.x) / 1e6 < 385 and max(S.x, E.x) / 1e6 > 392: victims.append(t)
    elif n == '+5V' and inside(S, 393.9, 145.2, 400.0, 149.0) and inside(E, 393.9, 145.2, 400.0, 149.0): victims.append(t)
    elif n == 'GND' and inside(S, 395.4, 150.4, 397.0, 150.8) and inside(E, 395.4, 150.4, 397.0, 150.8): victims.append(t)
for t in victims: b.Remove(t)
pcbnew.SaveBoard(sys.argv[1], b); print('removed', len(victims), 'segments around U13')
