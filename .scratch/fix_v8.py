import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); mm = lambda v: int(round(v * 1e6)); P = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y)); ni = b.GetNetInfo()
if '--remove' in sys.argv:
    def inside(Q, x0, y0, x1, y1): return x0 <= Q.x / 1e6 <= x1 and y0 <= Q.y / 1e6 <= y1
    v = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA' and t.GetNetname() == '+5V' and inside(t.GetStart(), 382.5, 148.9, 385.2, 153.2) and inside(t.GetEnd(), 382.5, 148.9, 385.2, 153.2)]
    for t in v: b.Remove(t)
    pcbnew.SaveBoard(sys.argv[1], b); print('removed', len(v), 'old B13 feed segments'); sys.exit()
L = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'I2': pcbnew.In2_Cu}
def seg(net, layer, x0, y0, x1, y1, w=0.4):
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(x0, y0)); t.SetEnd(P(x1, y1)); t.SetWidth(mm(w)); t.SetLayer(L[layer]); t.SetNet(ni.GetNetItem(net)); b.Add(t)
def via(net, x, y, d=0.8, drill=0.5):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(mm(d)); v.SetDrill(mm(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni.GetNetItem(net)); b.Add(v)
f = b.FindFootprintByReference('B13'); f.SetPosition(P(383.5, 146.0)); f.SetOrientationDegrees(270)
via('+5V', 383.5, 143.4, 1.2, 0.6); seg('+5V', 'B', 383.5, 143.4, 383.5, 144.8, 0.8); seg('+5V', 'F', 383.5, 143.4, 383.5, 145.05, 0.4)
b.FindFootprintByReference('C30').SetPosition(P(16.6, 57.0))
via('CLK_LAMP_ROW', 384.6, 148.2)
seg('+12VU', 'F', 38.4, 63.71, 40.41, 63.71)
pcbnew.SaveBoard(sys.argv[1], b); print('v8 fixes applied (B13 above the CLK via with a B.Cu +5V feed, C30 at 57.0, CLK via, R250 link)')
