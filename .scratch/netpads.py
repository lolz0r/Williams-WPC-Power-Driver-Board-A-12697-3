import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
for name in sys.argv[2:]:
    print('==', name)
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == name:
                try: sz = p.GetSize(pcbnew.F_Cu)
                except TypeError: sz = p.GetSize()
                print('  PAD', f.GetReference(), p.GetNumber(), '@(%.2f,%.2f)' % (p.GetPosition().x/1e6, p.GetPosition().y/1e6), 'size %.2fx%.2f' % (sz.x/1e6, sz.y/1e6), 'SMD' if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD else 'TH', 'rot', f.GetOrientationDegrees(), 'layers', [b.GetLayerName(l) for l in p.GetLayerSet().Seq()][:2])
    n = sum(1 for t in b.GetTracks() if t.GetNetname() == name); print('  tracks/vias:', n)
