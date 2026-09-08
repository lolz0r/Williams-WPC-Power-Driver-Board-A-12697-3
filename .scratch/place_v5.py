import pcbnew, sys
sys.path.insert(0, '/home/lolz0r/tng/wpc_power_driver_cost/tools'); sys.path.insert(0, '/home/lolz0r/tng/wpc_power_driver/tools'); import placement_cost as PC
pcb = sys.argv[1]; b = pcbnew.LoadBoard(pcb); mm = lambda v: int(round(v * 1e6)); have = {f.GetReference(): f for f in b.GetFootprints()}
if '--remove' in sys.argv:
    n = 0
    for r in list(have):
        if r.startswith('D1') and r[1:].isdigit() and 101 <= int(r[1:]) <= 116: b.Remove(have[r]); n += 1
    pcbnew.SaveBoard(pcb, b); print('removed', n, 'old diode footprints'); sys.exit()
lib = '/home/lolz0r/tng/wpc_power_driver_cost/footprints/wpc_cost.pretty'; n = 0
for ref, (x, y, rot) in PC.POS_MM.items():
    if ref in ('C21', 'H9'): continue
    if ref in have:
        f = have[ref]; f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); f.SetOrientationDegrees(rot); print('  moved', ref, (x, y, rot)); continue
    f = pcbnew.FootprintLoad(lib, 'D2PAK_Schottky_AKA'); f.SetReference(ref); f.SetValue('STPS20M100SG'); f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); f.SetOrientationDegrees(rot); f.SetParent(b); b.Add(f); n += 1
    tab = [p for p in f.Pads() if p.GetNumber() == '1'][0]; T = tab.GetPosition(); print('  %s at (%.1f, %.1f) rot %d: tab offset (%+.1f, %+.1f)' % (ref, x, y, rot, T.x / 1e6 - x, T.y / 1e6 - y))
pcbnew.SaveBoard(pcb, b); print('placed', n, 'diodes')
