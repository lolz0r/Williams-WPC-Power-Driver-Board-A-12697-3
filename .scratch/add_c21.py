import pcbnew, sys, glob, os
b = pcbnew.LoadBoard(sys.argv[1]); mm = lambda v: int(round(v * 1e6))
if b.FindFootprintByReference('C21'): print('C21 already on board'); sys.exit()
lib = (glob.glob('/app/extensions/Library/footprints/Capacitor_SMD.pretty') + glob.glob(os.path.expanduser('~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/*/*/*/files/footprints/Capacitor_SMD.pretty')))[0]
f = pcbnew.FootprintLoad(lib, 'C_0805_2012Metric'); f.SetReference('C21'); f.SetValue('10nF'); f.SetPosition(pcbnew.VECTOR2I(mm(86.0), mm(73.6))); f.SetOrientationDegrees(90)
f.SetParent(b); b.Add(f); pcbnew.SaveBoard(sys.argv[1], b); print('C21 added at (86.0, 73.6) rot 90')
