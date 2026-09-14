"""Add a passive, environment-enabled bus observer to the local PinMAME checkout."""
from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parents[2]
checkout = root / '.scratch/pinmame'
path = checkout / 'src/wpc/wpc.c'
source = path.read_text()
marker = '  /* WPC_BOARD_VERIFY_OBSERVER: passive raw CPU writes. */'
addition = '''
  /* WPC_BOARD_VERIFY_OBSERVER: passive raw CPU writes. */
  {
    static FILE *trace = NULL;
    static int initialized = 0;
    const int address = offset + WPC_BASE;
    if (!initialized) {
      const char *name = getenv("PINMAME_WPC_TRACE");
      initialized = 1;
      if (name) {
        trace = fopen(name, "w");
        if (trace) fprintf(trace, "time,kind,address,data,mask\\n");
      }
    }
    if (trace && ((address >= 0x3fe0 && address <= 0x3fe6) || address == 0x3fff || address == 0x3fd4))
      fprintf(trace, "%.9f,W,%04x,%02x,ff\\n", timer_get_time(), address, data & 255);
  }
'''
if marker not in source:
    assert source.count('WRITE_HANDLER(wpc_w) {') == 1
    path.write_text(source.replace('WRITE_HANDLER(wpc_w) {', 'WRITE_HANDLER(wpc_w) {' + addition))
out = root / 'output/verification/pinmame'
out.mkdir(parents=True, exist_ok=True)
(out / 'provenance.json').write_text(json.dumps({
    'upstream': 'https://github.com/vpinball/pinmame',
    'commit': subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip(),
    'patched_wpc_c_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'observer': 'Passive fprintf at entry to wpc_w; no emulated register or timing changes.',
}, indent=2) + '\n')
(out / 'record_bus.patch').write_bytes(subprocess.check_output(['git', '-C', str(checkout), 'diff', '--', 'src/wpc/wpc.c']))
