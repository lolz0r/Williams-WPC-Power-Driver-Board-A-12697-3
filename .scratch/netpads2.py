import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
for net in sys.argv[2:]:
    pads = sorted(f'{f.GetReference()}.{p.GetNumber()}' for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net)
    print(net, ':', ' '.join(pads))
