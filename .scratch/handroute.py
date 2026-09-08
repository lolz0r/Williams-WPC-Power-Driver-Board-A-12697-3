"""usage: handroute.py board.kicad_pcb spec.json   spec: {"segs":[[net,layer,x0,y0,x1,y1,w],...],"vias":[[net,x,y,dia,drill],...]}"""
import pcbnew, sys, json
pcb, spec = sys.argv[1], json.load(open(sys.argv[2])); b = pcbnew.LoadBoard(pcb)
L = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'In1.Cu': pcbnew.In1_Cu, 'In2.Cu': pcbnew.In2_Cu}
mm = lambda v: int(round(v * 1e6))
for net, layer, x0, y0, x1, y1, w in spec.get('segs', []):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0))); t.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetWidth(mm(w)); t.SetLayer(L[layer]); t.SetNetCode(b.GetNetcodeFromNetname(net)); b.Add(t)
for net, x, y, dia, drill in spec.get('vias', []):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetWidth(mm(dia)); v.SetDrill(mm(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(b.GetNetcodeFromNetname(net)); b.Add(v)
pcbnew.SaveBoard(pcb, b); print('added', len(spec.get('segs', [])), 'segments,', len(spec.get('vias', [])), 'vias')
