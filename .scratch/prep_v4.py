import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); mm = lambda v: int(round(v * 1e6))
j = b.FindFootprintByReference('J129'); P = j.GetPosition(); j.SetPosition(pcbnew.VECTOR2I(mm(277.0), P.y)); print('J129 moved to x=277.0 (was %.2f) to clear mounting hole H6' % (P.x / 1e6))
# the two clip halves of the no-connect fuse pins F101-1 / F102-1 share a net: link them so DRC sees them connected
for ref in ('F101', 'F102'):
    f = b.FindFootprintByReference(ref); pads = [p for p in f.Pads() if p.GetNumber() == '1']
    a, c = pads[0].GetPosition(), pads[1].GetPosition(); t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(c); t.SetWidth(mm(1.0)); t.SetLayer(pcbnew.F_Cu); t.SetNet(pads[0].GetNet()); b.Add(t)
pcbnew.SaveBoard(sys.argv[1], b); print('clip links added')
