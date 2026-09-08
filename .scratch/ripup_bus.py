import pcbnew, sys, fnmatch
sys.path.insert(0, '/home/lolz0r/tng/wpc_power_driver_modern/tools'); import satroute as SR
pcb = sys.argv[1]; b = pcbnew.LoadBoard(pcb); victims = []; nets = set()
for t in list(b.GetTracks()):
    n = t.GetNetname()
    if SR.netclass(n) in ('Heavy', 'Bus'): victims.append(t); nets.add(n)
for t in victims: b.Remove(t)
pcbnew.SaveBoard(pcb, b); print('ripped', len(victims), 'items of', len(nets), 'heavy/bus nets:', ' '.join(sorted(nets)))
