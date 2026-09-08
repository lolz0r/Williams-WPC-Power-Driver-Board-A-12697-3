import pcbnew, sys, math
pcb = sys.argv[1]; b = pcbnew.LoadBoard(pcb)
mm = lambda v: int(round(v * 1e6)); P = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
L = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'In2.Cu': pcbnew.In2_Cu}
def near(a, x, y, tol=0.03): return math.hypot(a.x/1e6 - x, a.y/1e6 - y) <= tol
KILL = []   # (kind, net, x0, y0, x1, y1)
def rm_seg(net, x0, y0, x1, y1): KILL.append(('seg', net, x0, y0, x1, y1))
def rm_via(net, x, y): KILL.append(('via', net, x, y, 0, 0))
def apply_kills():
    found = [False] * len(KILL); victims = []
    for t in list(b.GetTracks()):
        for i, (kind, net, x0, y0, x1, y1) in enumerate(KILL):
            if t.GetNetname() != net: continue
            if kind == 'via' and t.GetClass() == 'PCB_VIA' and near(t.GetStart(), x0, y0): victims.append(t); found[i] = True
            elif kind == 'seg' and t.GetClass() == 'PCB_TRACK' and ((near(t.GetStart(), x0, y0) and near(t.GetEnd(), x1, y1)) or (near(t.GetStart(), x1, y1) and near(t.GetEnd(), x0, y0))): victims.append(t); found[i] = True
    for t in victims: b.Remove(t)
    for i, f in enumerate(found):
        if not f: print('  !! not found', KILL[i])
    print('  removed', len(victims), 'items'); KILL.clear()
def seg(net, layer, x0, y0, x1, y1, w=0.4):
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(x0, y0)); t.SetEnd(P(x1, y1)); t.SetWidth(mm(w)); t.SetLayer(L[layer]); t.SetNetCode(CODES[net]); b.Add(t)
def via(net, x, y, dia=0.8, drill=0.5):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(mm(dia)); v.SetDrill(mm(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(CODES[net]); b.Add(v)
EN, BOOT = '/Power_Supply/U21_EN', '/Power_Supply/U21_BOOT'
CODES = {n: b.GetNetcodeFromNetname(n) for n in (EN, BOOT)}   # net lookup breaks after Remove() in this swig build
for f in b.GetFootprints():
    if f.GetReference() in ('R268', 'R267'):
        for p in f.Pads(): print('  pad', f.GetReference(), p.GetNumber(), p.GetNetname(), '(%.2f,%.2f)' % (p.GetPosition().x/1e6, p.GetPosition().y/1e6))
# 1. undo the first EN attempt
rm_seg(EN, 150.91, 72.04, 150.91, 70.75); rm_seg(EN, 150.91, 70.75, 154.6, 70.75); rm_seg(EN, 154.6, 70.75, 154.6, 69.2); rm_seg(EN, 154.6, 69.2, 156.8, 69.2)
rm_via(EN, 150.91, 70.75); rm_via(EN, 156.8, 69.2)
# 2. move the BOOT via down to free the B.Cu corridor
rm_via(BOOT, 155.6, 70.6); rm_seg(BOOT, 156.2, 70.6, 155.6, 70.6); apply_kills()
via(BOOT, 155.6, 71.2); seg(BOOT, 'F.Cu', 155.6, 70.6, 155.6, 71.2); seg(BOOT, 'In2.Cu', 155.6, 71.2, 156.2, 71.2)
# 3. EN: pad 3 -> via A -> B.Cu at y=70.0 -> via B -> R268.1
via(EN, 150.85, 70.75); seg(EN, 'F.Cu', 150.91, 72.04, 150.85, 70.75)
seg(EN, 'B.Cu', 150.85, 70.75, 151.6, 70.0); seg(EN, 'B.Cu', 151.6, 70.0, 157.0, 70.0); seg(EN, 'B.Cu', 157.0, 70.0, 157.6, 70.9)
via(EN, 157.6, 70.9); seg(EN, 'F.Cu', 157.6, 70.9, 157.11, 69.58)
# 4. rotate U1 by 180 deg and rip up its nets inside the window
u1 = b.FindFootprintByReference('U1'); print('  U1 at (%.2f,%.2f) rot %.0f' % (u1.GetPosition().x/1e6, u1.GetPosition().y/1e6, u1.GetOrientationDegrees()))
u1.SetOrientationDegrees(u1.GetOrientationDegrees() + 180)
nets = {p.GetNetname() for p in u1.Pads()} - {'GND', '+5V'}
x0, y0, x1, y1 = 138, 95, 165, 120
def inside(p): return x0 <= p.x/1e6 <= x1 and y0 <= p.y/1e6 <= y1
n = 0
for t in list(b.GetTracks()):
    if t.GetNetname() not in nets: continue
    if t.GetClass() == 'PCB_VIA':
        if inside(t.GetStart()): b.Remove(t); n += 1
    elif inside(t.GetStart()) and inside(t.GetEnd()): b.Remove(t); n += 1
print('  U1 rotated; removed', n, 'track items of', len(nets), 'U1 nets inside the window')
pcbnew.SaveBoard(pcb, b); print('saved')
