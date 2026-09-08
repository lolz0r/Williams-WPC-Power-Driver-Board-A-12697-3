"""Per-net copper audit (read-only): track length by layer, minimum width, via count for the power / HV / output nets."""
import pcbnew, re, collections, sys
b = pcbnew.LoadBoard(sys.argv[1])
pat = re.compile(r'^(\+5V|\+12V.*|\+18V|\+20V|\+50V.*|AC.*|GI._IN|GI._OUT|GI._RET|GI_RET|SOL\d\d(_TB)?|ROW\d|COL\d|/Power_Supply/.*|GND)$')
stat = collections.defaultdict(lambda: {'len': collections.Counter(), 'minw': {}, 'vias': 0, 'segs': 0})
for t in b.GetTracks():
    n = t.GetNetname()
    if not pat.match(n): continue
    s = stat[n]
    if t.GetClass() == 'PCB_VIA': s['vias'] += 1; continue
    ln = b.GetLayerName(t.GetLayer()); L = t.GetLength() / 1e6; w = t.GetWidth() / 1e6
    s['len'][ln] += L; s['segs'] += 1; s['minw'][ln] = min(s['minw'].get(ln, 99), w)
zones = collections.Counter(z.GetNetname() for z in b.Zones())
print('%-26s %7s %7s %7s %7s %5s  %s' % ('net', 'F.Cu', 'In2.Cu', 'B.Cu', 'vias', 'zones', 'min width per layer (mm)'))
for n in sorted(stat):
    s = stat[n]; L = s['len']
    print('%-26s %7.1f %7.1f %7.1f %7d %5d  %s' % (n, L['F.Cu'], L['In2.Cu'], L['B.Cu'], s['vias'], zones.get(n, 0), ' '.join('%s=%.2f' % (k, v) for k, v in sorted(s['minw'].items()))))
