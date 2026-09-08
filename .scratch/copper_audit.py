"""Per-net copper audit of the routed board: track length by layer, minimum width, via count, for the power/HV nets."""
import pcbnew, re, collections, sys
b = pcbnew.LoadBoard(sys.argv[1])
pat = re.compile(r'^(\+5V|\+5V_RAW|\+12V.*|\+18V.*|\+20V.*|\+50V.*|AC.*|GI._IN|GI._OUT|GI_RET.*|FLIP_._AC|/Power_Supply/.*SW|/Power_Supply/\+5V_RAW)$')
stat = collections.defaultdict(lambda: {'len': collections.Counter(), 'minw': {}, 'vias': 0, 'segs': 0})
for t in b.GetTracks():
    n = t.GetNetname()
    if not pat.match(n): continue
    s = stat[n]
    if t.GetClass() == 'PCB_VIA': s['vias'] += 1; continue
    ln = b.GetLayerName(t.GetLayer()); L = t.GetLength() / 1e6; w = t.GetWidth() / 1e6
    s['len'][ln] += L; s['segs'] += 1; s['minw'][ln] = min(s['minw'].get(ln, 99), w)
print('%-28s %7s %7s %7s %7s  %s' % ('net', 'F.Cu', 'In2.Cu', 'B.Cu', 'vias', 'min width per layer'))
for n in sorted(stat):
    s = stat[n]; L = s['len']
    print('%-28s %7.1f %7.1f %7.1f %7d  %s' % (n, L['F.Cu'], L['In2.Cu'], L['B.Cu'], s['vias'], ' '.join('%s=%.1f' % (k, v) for k, v in sorted(s['minw'].items()))))
