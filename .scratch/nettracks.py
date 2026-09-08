import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
for name in sys.argv[2:]:
    print('==', name)
    segs = []
    for t in b.GetTracks():
        if t.GetNetname() != name: continue
        if t.GetClass() == 'PCB_VIA': segs.append(('VIA', '', t.GetStart().x/1e6, t.GetStart().y/1e6, 0, 0))
        else: segs.append(('TRK', b.GetLayerName(t.GetLayer()), t.GetStart().x/1e6, t.GetStart().y/1e6, t.GetEnd().x/1e6, t.GetEnd().y/1e6))
    seen = set()
    for s in sorted(segs, key=lambda s: (s[1], s[2], s[3])):
        if s in seen: continue
        seen.add(s)
        if s[0] == 'VIA': print('  VIA (%.2f,%.2f)' % (s[2], s[3]))
        elif abs(s[2]-s[4]) + abs(s[3]-s[5]) >= 1.0: print('  %s %s (%.2f,%.2f)->(%.2f,%.2f)' % (s[0], s[1], s[2], s[3], s[4], s[5]))
    print('  (%d items, %d unique, short segments < 1 mm omitted)' % (len(segs), len(seen)))
