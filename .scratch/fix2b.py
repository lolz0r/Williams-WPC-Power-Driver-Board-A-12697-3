import pcbnew, sys, json
pcb = sys.argv[1]; uuids = set(json.load(open(pcb + '.kill.json'))); b = pcbnew.LoadBoard(pcb); n = 0
for t in list(b.GetTracks()):
    if t.m_Uuid.AsString() in uuids: b.Remove(t); n += 1
pcbnew.SaveBoard(pcb, b); print('pass B removed', n)
