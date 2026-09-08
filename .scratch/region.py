import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); x0, y0, x1, y1 = map(float, sys.argv[2:6])
def inside(p): return x0 <= p.x/1e6 <= x1 and y0 <= p.y/1e6 <= y1
for f in b.GetFootprints():
    for p in f.Pads():
        if inside(p.GetPosition()):
            sz = p.GetSize(pcbnew.F_Cu) if hasattr(p, 'GetSize') else None
            try: sz = p.GetSize(pcbnew.F_Cu)
            except TypeError: sz = p.GetSize()
            print('PAD', f.GetReference(), p.GetNumber(), p.GetNetname(), '@(%.2f,%.2f)' % (p.GetPosition().x/1e6, p.GetPosition().y/1e6), 'size %.2fx%.2f' % (sz.x/1e6, sz.y/1e6), 'SMD' if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD else 'TH', p.GetLayerSet().Seq()[0] if p.GetLayerSet().Seq() else '')
for t in b.GetTracks():
    if inside(t.GetStart()) or inside(t.GetEnd()):
        if t.GetClass() == 'PCB_VIA': print('VIA', t.GetNetname(), '@(%.2f,%.2f)' % (t.GetStart().x/1e6, t.GetStart().y/1e6))
        else: print('TRK', t.GetNetname(), b.GetLayerName(t.GetLayer()), '(%.2f,%.2f)->(%.2f,%.2f)' % (t.GetStart().x/1e6, t.GetStart().y/1e6, t.GetEnd().x/1e6, t.GetEnd().y/1e6), 'w%.1f' % (t.GetWidth()/1e6))
