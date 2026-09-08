"""Replace BR1/BR2/BR4/BR5 by 2x2 D2PAK Schottky quads (D101-D116) on the routed board.
DC pair (tab = rail) on the top row with the tabs facing each other, AC pair (tab = AC leg) on the bottom row with the tabs facing outward.
TO-263-2 footprint: tab (pad 2) toward +x at rot 0; courtyard 16.7 x 11.4 mm -> pitch 19 x 14 mm."""
import pcbnew, sys, glob, os
b = pcbnew.LoadBoard(sys.argv[1]); mm = lambda v: int(round(v * 1e6))
lib = (glob.glob('/app/extensions/Library/footprints/Package_TO_SOT_SMD.pretty') + glob.glob(os.path.expanduser('~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/*/*/*/files/footprints/Package_TO_SOT_SMD.pretty')))[0]
def quad(refs, x0, y0):     # refs: [dc_left, dc_right, ac_left, ac_right]
    return [(refs[0], x0, y0, 0), (refs[1], x0 + 19, y0, 180), (refs[2], x0, y0 + 14, 180), (refs[3], x0 + 19, y0 + 14, 0)]
PLAN = {'BR1': quad(['D101', 'D102', 'D103', 'D104'], 346, 64), 'BR2': quad(['D105', 'D106', 'D107', 'D108'], 346, 12),
        'BR4': quad(['D109', 'D110', 'D111', 'D112'], 281, 12), 'BR5': quad(['D113', 'D114', 'D115', 'D116'], 13, 18)}
have = {f.GetReference(): f for f in b.GetFootprints()}; n = 0
if '--remove-bridges' in sys.argv:
    for br in PLAN:
        if br in have: b.Remove(have[br]); print('  removed', br)
    pcbnew.SaveBoard(sys.argv[1], b); sys.exit()
hole = (glob.glob('/app/extensions/Library/footprints/MountingHole.pretty'))[0]
if 'H9' not in have:
    h = pcbnew.FootprintLoad(hole, 'MountingHole_5.5mm'); h.SetReference('H9'); h.SetValue('BR3 M4 bolt'); h.SetPosition(pcbnew.VECTOR2I(mm(251.99), mm(23.30))); h.SetParent(b); b.Add(h); print('  H9 5.5 mm NPTH under BR3')
for br, items in PLAN.items():
    for ref, x, y, rot in items:
        if ref in have: continue
        f = pcbnew.FootprintLoad(lib, 'TO-263-2'); f.SetReference(ref); f.SetValue('STPS20M100SG'); f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); f.SetOrientationDegrees(rot); f.SetParent(b); b.Add(f); n += 1
pcbnew.SaveBoard(sys.argv[1], b); print('added', n, 'D2PAK footprints')
