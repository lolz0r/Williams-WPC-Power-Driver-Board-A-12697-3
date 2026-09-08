import pcbnew, sys
sys.path.insert(0, '/home/lolz0r/tng/wpc_power_driver_modern/tools'); import satroute as SR
pcb = sys.argv[1]; classes = set(sys.argv[2].split(',')); nets = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else set()
b = pcbnew.LoadBoard(pcb); victims = [t for t in b.GetTracks() if SR.netclass(t.GetNetname()) in classes or t.GetNetname() in nets]
hit = {t.GetNetname() for t in victims}
for t in victims: b.Remove(t)
pcbnew.SaveBoard(pcb, b); print('ripped', len(victims), 'items of', len(hit), 'nets')
