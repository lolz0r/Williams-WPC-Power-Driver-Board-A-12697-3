import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); mm = lambda v: int(round(v * 1e6)); P = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y)); ni = b.GetNetInfo()
L = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'I2': pcbnew.In2_Cu}
def seg(net, layer, x0, y0, x1, y1, w=0.4):
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(x0, y0)); t.SetEnd(P(x1, y1)); t.SetWidth(mm(w)); t.SetLayer(L[layer]); t.SetNet(ni.GetNetItem(net)); b.Add(t)
def via(net, x, y, d=0.8, drill=0.5):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(mm(d)); v.SetDrill(mm(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni.GetNetItem(net)); b.Add(v)
f = b.FindFootprintByReference('B13'); f.SetPosition(P(383.5, 153.6)); f.SetOrientationDegrees(270)
for p in f.Pads(): print('  B13 pad', p.GetNumber(), p.GetNetname(), '(%.2f, %.2f)' % (p.GetPosition().x / 1e6, p.GetPosition().y / 1e6))
via('CLK_LAMP_ROW', 384.6, 148.2)
seg('+12VU', 'F', 38.4, 63.71, 40.41, 63.71)
seg('+5V', 'F', 386.35, 149.63, 384.6, 149.63); seg('+5V', 'F', 384.6, 149.63, 384.6, 152.65); seg('+5V', 'F', 384.6, 152.65, 383.5, 152.65)
for ref in ('C30', 'SR2', 'B12', 'B13'):
    g = b.FindFootprintByReference(ref); cy = g.GetCourtyard(pcbnew.F_CrtYd).BBox(); print('  %s courtyard (%.1f,%.1f)-(%.1f,%.1f)' % (ref, cy.GetLeft() / 1e6, cy.GetTop() / 1e6, cy.GetRight() / 1e6, cy.GetBottom() / 1e6))
pcbnew.SaveBoard(sys.argv[1], b); print('v7 fixes applied')
