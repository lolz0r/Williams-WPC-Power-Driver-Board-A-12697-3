"""Production legend for the routed board (run on the final board, flatpak python):
 - fuse rating + purpose next to every fuse, connector function labels, board title / caution texts
 - three SMT fiducials (Fiducial_1mm_Mask2mm) in free corners
Usage: flatpak run --command=python3 org.kicad.KiCad tools/legend.py wpc_power_driver_cost.kicad_pcb"""
import pcbnew, sys, math, glob, os
FID_LIB = (glob.glob('/app/extensions/Library/footprints/Fiducial.pretty') + glob.glob(os.path.expanduser('~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/*/*/*/files/footprints/Fiducial.pretty')))[0]
FUSE_PURPOSE = {'F101': 'L FLIPPER (no fuse)', 'F102': 'R FLIPPER (no fuse)', 'F103': '+50V SOL', 'F104': '+50V SOL', 'F105': '+50V SOL', 'F106': 'G.I. #1', 'F107': 'G.I. #2', 'F108': 'G.I. #3',
                'F109': 'G.I. #4', 'F110': 'G.I. #5', 'F111': '+20V FLASH', 'F112': '+50V (51VAC)', 'F113': '+5V (9VAC)', 'F114': '+18V LAMPS', 'F115': '+12V SW.MATRIX', 'F116': '+12V POWER'}
CONN = {'J101': '9VAC / 13VAC IN', 'J102': '16VAC / 51VAC IN', 'J103': 'GND 8-DRV', 'J104': 'FUSED AC OUT', 'J105': 'FLIPPER AC', 'J106': '+20V BACKBOX', 'J107': '+50V/+20V PLAYFIELD',
        'J108': 'SPARE', 'J109': 'SPARE', 'J110': 'SPARE', 'J111': 'GPIO', 'J112': '9.8VAC IN', 'J113': 'CPU J211', 'J114': '+12V/+5V CPU', 'J115': 'G.I. IN', 'J116': '+12V/+5V COIN DOOR',
        'J117': '+12V/+5V DMD', 'J118': '+12V/+5V PLAYFIELD', 'J119': 'G.I. COIN DOOR', 'J120': 'G.I. OUT', 'J121': 'G.I. OUT', 'J122': 'SOL 25-28 PF', 'J123': 'SPARE', 'J124': 'SOL 25-28 BB',
        'J125': 'SOL 17-24 BB', 'J126': 'SOL 17-24 PF', 'J127': 'SOL 9-16', 'J130': 'SOL 1-8', 'J133': 'LAMP ROWS CAB', 'J134': 'LAMP ROWS SPARE', 'J135': 'LAMP ROWS PF', 'J136': 'LAMP COL 8', 'J137': 'LAMP COLS PF', 'J138': 'LAMP COLS BB'}
def main():
    pcb = sys.argv[1]; b = pcbnew.LoadBoard(pcb); mm = lambda v: int(round(v * 1e6))
    bb = b.GetBoardEdgesBoundingBox(); W, H = bb.GetWidth() / 1e6, bb.GetHeight() / 1e6; cx, cy = bb.GetCenter().x / 1e6, bb.GetCenter().y / 1e6
    def text(s, x, y, size=1.2, rot=0, layer=pcbnew.F_SilkS, thick=None):
        t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(thick or size * 0.16)); t.SetTextAngleDegrees(rot); b.Add(t)
    # idempotent: texts that already exist on the silkscreen are not added again (pcbnew's Remove() breaks the board object in this build)
    existing = {t.GetText() for t in b.Drawings() if t.GetClass() == 'PCB_TEXT'}
    _text = text
    def text(s, *a, **k):
        if s in existing: return
        _text(s, *a, **k)
    n = 0
    for f in b.GetFootprints():
        ref = f.GetReference(); P = f.GetPosition(); x, y = P.x / 1e6, P.y / 1e6; rot = f.GetOrientationDegrees() % 180
        if ref in FUSE_PURPOSE:
            val = f.GetValue().replace('no fuse (clips only)', '').strip(); label = f'{ref} {val} {FUSE_PURPOSE[ref]}'.replace('  ', ' ')
            # the 5x20 clip pair is ~26 mm long along its axis; put the label 5 mm off-axis
            if abs(rot - 90) < 1: text(label, x + 5.0, y, 1.2, 90)
            else: text(label, x, y - 5.0, 1.2, 0)
            n += 1
        elif ref in CONN:
            fb = f.GetBoundingBox(False, False); w, h = fb.GetWidth() / 1e6, fb.GetHeight() / 1e6
            horiz = w >= h; off = (h / 2 + 2.2) if horiz else (w / 2 + 2.2)
            if horiz: ty = y + off if cy > y else y - off; text(f'{ref} {CONN[ref]}', x, ty, 1.5, 0)
            else: tx = x + off if cx > x else x - off; text(f'{ref} {CONN[ref]}', tx, y, 1.5, 90)
            n += 1
    text('WPC POWER DRIVER REPLACEMENT (COST-OPTIMISED)  A-12697-3 FORM FACTOR', cx, cy - 4, 3.0, 0, pcbnew.F_SilkS, 0.45)
    text('CAUTION: "+50V" RAIL IS ~70 V DC - 51 VAC / 16 VAC / 13 VAC / 9 VAC AND 6.3 VAC G.I. ON THIS BOARD', cx, cy + 1, 1.8, 0, pcbnew.F_SilkS, 0.3)
    text('REV A  2026-09  4-LAYER 2oz/1oz  SEE docs/ASSEMBLY_NOTES.md FOR KEY PINS AND HEATSINKS', cx, cy + 5, 1.5, 0, pcbnew.F_SilkS, 0.25)
    # fiducials in three corners (positions are checked by DRC afterwards)
    have = {f.GetReference() for f in b.GetFootprints()}
    for ref, (fx, fy) in {'FID1': (5.0, 34.0), 'FID2': (443.0, 25.0), 'FID3': (5.0, 253.0)}.items():     # copper-free spots (checked 2026-09-07)
        if ref in have: continue
        fp = pcbnew.FootprintLoad(FID_LIB, 'Fiducial_1mm_Mask2mm'); fp.SetReference(ref); fp.SetValue('FIDUCIAL'); fp.SetPosition(pcbnew.VECTOR2I(mm(fx), mm(fy)))
        fp.Reference().SetVisible(False); b.Add(fp)
    pcbnew.SaveBoard(pcb, b); print(f'legend: {n} labels, 3 title/caution texts, fiducials FID1-3 at corners; board {W:.1f} x {H:.1f}')
if __name__ == '__main__': main()
