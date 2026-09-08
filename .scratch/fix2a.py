import pcbnew, sys, math, json
pcb = sys.argv[1]; b = pcbnew.LoadBoard(pcb)
mm = lambda v: int(round(v * 1e6)); P = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
L = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'In2.Cu': pcbnew.In2_Cu}
EN, BOOT = '/Power_Supply/U21_EN', '/Power_Supply/U21_BOOT'; CODES = {n: b.GetNetcodeFromNetname(n) for n in (EN, BOOT)}
def near(a, x, y, tol=0.03): return math.hypot(a.x/1e6 - x, a.y/1e6 - y) <= tol
KILL = [('seg', EN, 150.91, 72.04, 150.91, 70.75), ('seg', EN, 150.91, 70.75, 154.6, 70.75), ('seg', EN, 154.6, 70.75, 154.6, 69.2), ('seg', EN, 154.6, 69.2, 156.8, 69.2),
        ('via', EN, 150.91, 70.75, 0, 0), ('via', EN, 156.8, 69.2, 0, 0), ('via', BOOT, 155.6, 70.6, 0, 0), ('seg', BOOT, 156.2, 70.6, 155.6, 70.6)]
u1 = b.FindFootprintByReference('U1'); nets = {p.GetNetname() for p in u1.Pads()} - {'GND', '+5V'}
x0, y0, x1, y1 = 138, 95, 165, 120
def inside(p): return x0 <= p.x/1e6 <= x1 and y0 <= p.y/1e6 <= y1
uuids = []; found = [False] * len(KILL)
for t in b.GetTracks():
    for i, (kind, net, ax, ay, bx, by) in enumerate(KILL):
        if t.GetNetname() != net: continue
        if kind == 'via' and t.GetClass() == 'PCB_VIA' and near(t.GetStart(), ax, ay): uuids.append(t.m_Uuid.AsString()); found[i] = True
        elif kind == 'seg' and t.GetClass() == 'PCB_TRACK' and ((near(t.GetStart(), ax, ay) and near(t.GetEnd(), bx, by)) or (near(t.GetStart(), bx, by) and near(t.GetEnd(), ax, ay))): uuids.append(t.m_Uuid.AsString()); found[i] = True
    if t.GetNetname() in nets:
        if t.GetClass() == 'PCB_VIA' and inside(t.GetStart()): uuids.append(t.m_Uuid.AsString())
        elif t.GetClass() != 'PCB_VIA' and inside(t.GetStart()) and inside(t.GetEnd()): uuids.append(t.m_Uuid.AsString())
for i, f in enumerate(found):
    if not f: print('  !! not found', KILL[i])
json.dump(sorted(set(uuids)), open(pcb + '.kill.json', 'w')); print('  to remove:', len(set(uuids)), 'items;', len(nets), 'U1 nets')
def seg(net, layer, ax, ay, bx, by, w=0.4):
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(ax, ay)); t.SetEnd(P(bx, by)); t.SetWidth(mm(w)); t.SetLayer(L[layer]); t.SetNetCode(CODES[net]); b.Add(t)
def via(net, x, y, dia=0.8, drill=0.5):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(mm(dia)); v.SetDrill(mm(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(CODES[net]); b.Add(v)
via(BOOT, 155.6, 71.2); seg(BOOT, 'F.Cu', 155.6, 70.6, 155.6, 71.2); seg(BOOT, 'In2.Cu', 155.6, 71.2, 156.2, 71.2)
via(EN, 150.85, 70.75); seg(EN, 'F.Cu', 150.91, 72.04, 150.85, 70.75)
seg(EN, 'B.Cu', 150.85, 70.75, 151.6, 70.0); seg(EN, 'B.Cu', 151.6, 70.0, 157.0, 70.0); seg(EN, 'B.Cu', 157.0, 70.0, 157.6, 70.9)
via(EN, 157.6, 70.9); seg(EN, 'F.Cu', 157.6, 70.9, 157.11, 69.58)
print('  U1 rot before', u1.GetOrientationDegrees()); u1.SetOrientationDegrees(u1.GetOrientationDegrees() + 180); print('  U1 rot after', u1.GetOrientationDegrees())
pcbnew.SaveBoard(pcb, b); print('pass A saved')
