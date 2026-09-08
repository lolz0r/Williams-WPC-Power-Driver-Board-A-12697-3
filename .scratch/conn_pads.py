import pcbnew, sys
b = pcbnew.LoadBoard('/home/lolz0r/tng/wpc_power_driver_cost/wpc_power_driver_cost.kicad_pcb')
rows = []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if not ref.startswith('J'): continue
    pads = {p.GetNumber(): p for p in fp.Pads()}
    nums = sorted(int(k) for k in pads)
    first, last = pads[str(nums[0])], pads[str(nums[-1])]
    def xy(p):
        c = p.GetPosition(); return (round(pcbnew.ToMM(c.x), 2), round(pcbnew.ToMM(c.y), 2))
    extra = ''
    if ref == 'J113':
        extra = ' pin2 %s pin33 %s' % (xy(pads['2']), xy(pads['33']))
    rows.append((ref, len(nums), xy(first), xy(last), fp.GetOrientationDegrees(), extra))
for r in sorted(rows, key=lambda r: int(r[0][1:])):
    print('%-5s n=%2d pin1=%s pinN=%s rot=%s%s' % r)
