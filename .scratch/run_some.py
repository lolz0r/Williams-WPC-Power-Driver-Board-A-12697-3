import os, sys, time
sys.path.insert(0, 'tools/spice')
from ngspice_lib import NgSpice
ng = NgSpice()
for name in sys.argv[1:]:
    deck = os.path.abspath(f'tools/spice/decks/{name}.cir')
    os.chdir(os.path.dirname(deck)); ng.cmd('destroy all'); t0 = time.time(); log = ng.run_deck(deck)
    os.chdir('/home/lolz0r/tng/wpc_power_driver_cost')
    errs = [l for l in log if 'stderr' in l and 'Warning' not in l]
    meas = [l.replace('stdout', '').strip() for l in log if 'stdout' in l and '=' in l and ' at' not in l.split('=')[0] and 'Data Rows' not in l]
    print(f'== {name} ({time.time()-t0:.0f} s)'); print('   ' + ' | '.join(m.split('=')[0].strip() + '=' + m.split('=')[1].split()[0] for m in meas if m.split('=')[1].strip()))
    for e in errs[:6]: print('   ERR', e[:200])
