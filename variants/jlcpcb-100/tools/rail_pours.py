"""Heat-spreading rail pours for the D2PAK Schottky bridge diodes (D101-D116) on F.Cu and B.Cu, 3x3 thermal via arrays in
their tabs, solid tab connection.  Geometry matches tools/placement_cost.py POS_MM (2026-09-07).  Zones are filled by the next
DRC refill (finish_board / finalize.sh).   Usage: flatpak run --command=python3 org.kicad.KiCad tools/rail_pours.py board.kicad_pcb"""
import pcbnew, sys
# (zone name, net, x0, y0, x1, y1)   [mm]
POURS = [('BR1_18V', '+18V', 339, 57, 379, 108), ('BR1_AC13A', '/Power_Supply/AC13_A_F', 340, 3, 356.7, 49), ('BR1_AC13B', 'AC13_B', 356.7, 3, 379, 49),
         ('BR2_5VRAW', '/Power_Supply/+5V_RAW', 293, 106, 308, 121), ('BR2_AC9A', 'AC9_AF', 277, 121, 288, 135), ('BR2_AC9B', 'AC9_B', 313, 121, 328, 135),
         ('BR4_20V', '+20V', 284, 4, 299, 20), ('BR4_AC16A', 'AC16_A_F', 271, 20, 281, 44), ('BR4_AC16B', 'AC16_B', 302, 20, 330, 44),
         ('BR5_AC98A', '/Power_Supply/AC98_A_F', 9, 3, 23.7, 15), ('BR5_AC98B', 'AC98_B', 23.7, 3, 38, 15), ('BR5_12VU', '+12VU', 9, 43, 38, 54)]
def main():
    pcb = sys.argv[1]; b = pcbnew.LoadBoard(pcb); mm = lambda v: int(round(v * 1e6)); ni = b.GetNetInfo()
    existing = {z.GetZoneName() for z in b.Zones()}; made = 0
    for name, net, x0, y0, x1, y1 in POURS:
        n = ni.GetNetItem(net)
        if n is None: print('  !! net not found', net); continue
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            zn = f'{name}_{b.GetLayerName(layer)}'
            if zn in existing: continue
            z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(n); z.SetZoneName(zn)
            ol = z.Outline(); ol.NewOutline()
            for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): ol.Append(mm(x), mm(y))
            z.SetLocalClearance(mm(0.4)); z.SetMinThickness(mm(0.5)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetAssignedPriority(2); z.SetIsFilled(False)
            b.Add(z); made += 1
    vias = 0; skipped = 0
    import math
    segs = [(t.GetNetCode(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth() / 2) for t in b.GetTracks() if t.GetClass() != 'PCB_VIA']
    vias_all = [(t.GetNetCode(), t.GetStart().x, t.GetStart().y, t.GetWidth(pcbnew.F_Cu) / 2) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
    pads_all = [(p.GetNetCode(), p) for f in b.GetFootprints() for p in f.Pads() if p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu)]   # paste-only sub-pads carry no copper
    def d_seg(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        if L2 == 0: return math.hypot(px - ax, py - ay)
        u = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2)); return math.hypot(px - ax - u * dx, py - ay - u * dy)
    def free(x, y, code, r=mm(0.4), clr=mm(0.45)):   # a through via touches every layer: keep 0.45 mm from any other net's copper
        for (c, ax, ay, bx, by, hw) in segs:
            if c != code and d_seg(x, y, ax, ay, bx, by) < r + hw + clr: return False
        for (c, vx, vy, vr) in vias_all:
            if c != code and math.hypot(x - vx, y - vy) < r + vr + clr: return False
        for (c, p) in pads_all:
            if c != code and p.HitTest(pcbnew.VECTOR2I(int(x), int(y)), r + clr): return False
        return True
    for f in b.GetFootprints():
        ref = f.GetReference()
        if not (ref.startswith('D1') and ref[1:].isdigit() and 101 <= int(ref[1:]) <= 116): continue
        tab = [p for p in f.Pads() if p.GetNumber() == '1'][0]; tab.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL); T = tab.GetPosition(); net = tab.GetNet()
        have = {(round(t.GetStart().x / 1e6, 2), round(t.GetStart().y / 1e6, 2)) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA'}
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                x, y = T.x + mm(1.6 * i), T.y + mm(1.6 * j)
                if (round(x / 1e6, 2), round(y / 1e6, 2)) in have: continue
                if not free(x, y, net.GetNetCode()): skipped += 1; continue
                v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(mm(0.8)); v.SetDrill(mm(0.5))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); b.Add(v); vias += 1
    pcbnew.SaveBoard(pcb, b); print(f'rail pours: {made} zones added, {vias} thermal vias ({skipped} positions skipped: other-net copper underneath)')
if __name__ == '__main__': main()
