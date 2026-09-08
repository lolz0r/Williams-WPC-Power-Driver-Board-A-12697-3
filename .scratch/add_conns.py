import pcbnew, sys
dst = pcbnew.LoadBoard(sys.argv[1]); src = pcbnew.LoadBoard(sys.argv[2]); have = {f.GetReference() for f in dst.GetFootprints()}; n = 0
for ref in sys.argv[3:]:
    if ref in have: print('  already present', ref); continue
    f = src.FindFootprintByReference(ref); g = pcbnew.FOOTPRINT(f); g.SetParent(dst); dst.Add(g); n += 1
    print('  added', ref, '(%.2f, %.2f) rot %.0f' % (g.GetPosition().x / 1e6, g.GetPosition().y / 1e6, g.GetOrientationDegrees()))
pcbnew.SaveBoard(sys.argv[1], dst); print('added', n, 'footprints')
