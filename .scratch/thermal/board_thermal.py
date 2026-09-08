"""Read-only thermal geometry audit of the routed cost board (pcbnew, KiCad 10 flatpak).
1. bridges BR1-BR5 and triacs Q10/Q12/Q14/Q16/Q18: position, rotation, body/courtyard bbox, neighbours within a window (courtyard bboxes)
2. DPAK MOSFETs: drain-tab pad net, copper area of that net on the tab layer inside 25.4 mm and 12.7 mm windows (pads + tracks + zone fills), vias, other-layer copper
"""
import pcbnew, sys, json, math, collections
b = pcbnew.LoadBoard(sys.argv[1])
MM = 1e6
def mm(v): return v / MM
fps = {f.GetReference(): f for f in b.GetFootprints()}
def crtyd_bbox(f):
    # F.CrtYd bounding box in mm (x0,y0,x1,y1); falls back to the footprint bbox
    try:
        bb = f.GetLayerBoundingBox(pcbnew.LSET.FromHex('0') if False else pcbnew.LSET(pcbnew.F_CrtYd))
    except Exception:
        bb = None
    if bb is None or bb.GetWidth() == 0:
        bb = f.GetBoundingBox(False, False)
    return (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetX() + bb.GetWidth()), mm(bb.GetY() + bb.GetHeight()))
def body_bbox(f):
    try:
        bb = f.GetLayerBoundingBox(pcbnew.LSET(pcbnew.F_Fab))
        if bb.GetWidth() > 0: return (mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetX() + bb.GetWidth()), mm(bb.GetY() + bb.GetHeight()))
    except Exception: pass
    return None
out = {}
# ---------------- 1. placement of the heatsinked parts and their neighbours
targets = ['BR1', 'BR2', 'BR3', 'BR4', 'BR5', 'Q10', 'Q12', 'Q14', 'Q16', 'Q18']
crt = {r: crtyd_bbox(f) for r, f in fps.items()}
def overlap_dist(a, bb):
    dx = max(bb[0] - a[2], a[0] - bb[2], 0); dy = max(bb[1] - a[3], a[1] - bb[3], 0)
    return math.hypot(dx, dy), dx, dy
place = {}
for r in targets:
    f = fps[r]; p = f.GetPosition(); c = crt[r]
    nb = []
    for r2, c2 in crt.items():
        if r2 == r: continue
        d, dx, dy = overlap_dist(c, c2)
        if d <= 30:
            nb.append(dict(ref=r2, fp=fps[r2].GetFPIDAsString().split(':')[-1], gap=round(d, 2), crtyd=[round(v, 2) for v in c2],
                           value=fps[r2].GetValue(), side='B' if fps[r2].IsFlipped() else 'F'))
    nb.sort(key=lambda n: n['gap'])
    pads = [dict(num=pd.GetNumber(), net=pd.GetNetname(), x=round(mm(pd.GetPosition().x), 2), y=round(mm(pd.GetPosition().y), 2)) for pd in f.Pads()]
    place[r] = dict(fp=f.GetFPIDAsString(), x=round(mm(p.x), 3), y=round(mm(p.y), 3), rot=f.GetOrientationDegrees(), side='B' if f.IsFlipped() else 'F',
                    crtyd=[round(v, 2) for v in c], body=body_bbox(f) and [round(v, 2) for v in body_bbox(f)], pads=pads, neighbours=nb)
out['placement'] = place
# board outline
bb = b.GetBoardEdgesBoundingBox()
out['board'] = [mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetX() + bb.GetWidth()), mm(bb.GetY() + bb.GetHeight())]
# ---------------- 2. DPAK drain copper
def rect_poly(x0, y0, x1, y1):
    ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)): ps.Append(int(x * MM), int(y * MM))
    return ps
MAXERR = int(0.005 * MM)
def item_poly(item, layer):
    ps = pcbnew.SHAPE_POLY_SET()
    try: item.TransformShapeToPolygon(ps, layer, 0, MAXERR, pcbnew.ERROR_INSIDE)
    except TypeError:
        try: item.TransformShapeToPolygon(ps, layer, 0, MAXERR, pcbnew.ERROR_INSIDE, False)
        except Exception as e: print('poly err', type(item), e, file=sys.stderr)
    return ps
zones = list(b.Zones())
tracks = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA']
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
allpads = [(f.GetReference(), pd) for f in b.GetFootprints() for pd in f.Pads()]
by_net_tracks = collections.defaultdict(list)
for t in tracks: by_net_tracks[t.GetNetname()].append(t)
by_net_pads = collections.defaultdict(list)
for r, pd in allpads: by_net_pads[pd.GetNetname()].append((r, pd))
by_net_vias = collections.defaultdict(list)
for v in vias: by_net_vias[v.GetNetname()].append(v)
by_net_zones = collections.defaultdict(list)
for z in zones: by_net_zones[z.GetNetname()].append(z)
layers = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'In1.Cu': pcbnew.In1_Cu, 'In2.Cu': pcbnew.In2_Cu}
def net_area(net, layer_id, win):
    """area (mm2) of copper of `net` on `layer_id` inside the window polygon: union of pads, tracks, zone fills"""
    acc = pcbnew.SHAPE_POLY_SET()
    for r, pd in by_net_pads[net]:
        if not pd.IsOnLayer(layer_id): continue
        acc.Append(item_poly(pd, layer_id))
    for t in by_net_tracks[net]:
        if t.GetLayer() != layer_id: continue
        acc.Append(item_poly(t, layer_id))
    for z in by_net_zones[net]:
        if not z.IsOnLayer(layer_id): continue
        try: fill = z.GetFilledPolysList(layer_id)
        except Exception: continue
        acc.Append(fill)
    acc.Simplify()
    acc.BooleanIntersection(win)
    try: return mm(mm(acc.Area()))
    except Exception: return None
dpak = {}
for r, f in sorted(fps.items()):
    if 'TO-252' not in f.GetFPIDAsString(): continue
    pads = list(f.Pads())
    tab = max(pads, key=lambda pd: pd.GetSize().x * pd.GetSize().y if hasattr(pd.GetSize(), 'x') else 0)
    net = tab.GetNetname(); tl = pcbnew.B_Cu if f.IsFlipped() else pcbnew.F_Cu
    tp = tab.GetPosition(); tx, ty = mm(tp.x), mm(tp.y)
    res = dict(value=f.GetValue(), net=net, x=round(mm(f.GetPosition().x), 2), y=round(mm(f.GetPosition().y), 2), rot=f.GetOrientationDegrees(), side='B' if f.IsFlipped() else 'F',
               tab_pad=round(mm(mm(item_poly(tab, tl).Area())), 2))
    for name, half in (('w25', 12.7), ('w13', 6.35), ('w50', 25.4)):
        win = rect_poly(tx - half, ty - half, tx + half, ty + half)
        res[name + '_tab_layer'] = round(net_area(net, tl, win) or 0, 1)
        other = 0
        for ln, lid in layers.items():
            if lid == tl: continue
            other += net_area(net, lid, win) or 0
        res[name + '_other_layers'] = round(other, 1)
        res[name + '_vias'] = sum(1 for v in by_net_vias[net] if abs(mm(v.GetStart().x) - tx) <= half and abs(mm(v.GetStart().y) - ty) <= half)
    # track widths leaving the tab
    ws = sorted({round(mm(t.GetWidth()), 2) for t in by_net_tracks[net] if t.GetLayer() == tl})
    res['track_widths_tab_layer'] = ws
    res['zones_on_net'] = len(by_net_zones[net])
    dpak[r] = res
out['dpak'] = dpak
# TO-220 triac tab (pad 2 = A2/MT2? check nets) copper too
tri = {}
for r in ['Q10', 'Q12', 'Q14', 'Q16', 'Q18']:
    f = fps[r]
    for pd in f.Pads():
        tri.setdefault(r, {})[pd.GetNumber()] = pd.GetNetname()
out['triac_pads'] = tri
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print('written', sys.argv[2])
