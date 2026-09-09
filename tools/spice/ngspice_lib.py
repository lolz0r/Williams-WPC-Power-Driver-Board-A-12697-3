"""Minimal ctypes driver for libngspice (shared library shipped inside the KiCad flatpak).
Run with:  flatpak run --command=python3 org.kicad.KiCad tools/spice/ngspice_lib.py deck.cir
"""
import ctypes, ctypes.util, os, sys, json, glob

class VecInfo(ctypes.Structure):
    _fields_ = [('v_name', ctypes.c_char_p), ('v_type', ctypes.c_int), ('v_flags', ctypes.c_short),
                ('v_realdata', ctypes.POINTER(ctypes.c_double)), ('v_compdata', ctypes.c_void_p), ('v_length', ctypes.c_int)]

SendChar = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
SendStat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
ControllerExit = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
SendData = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p)
SendInitData = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)
BGThreadRunning = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)

class NgSpice:
    def __init__(self, path=None):
        path = path or os.environ.get('NGSPICE_LIBRARY') or ctypes.util.find_library('ngspice')
        if not path:
            path = next((p for p in (
                '/opt/homebrew/opt/libngspice/lib/libngspice.dylib',
                '/usr/local/opt/libngspice/lib/libngspice.dylib',
                '/app/lib/libngspice.so.0') if os.path.exists(p)), None)
        if not path:
            raise RuntimeError('Install libngspice or set NGSPICE_LIBRARY to its shared library path')
        self.lib = ctypes.CDLL(path)
        self.log = []
        self._cb = [SendChar(self._send_char), SendStat(self._send_stat), ControllerExit(self._exit),
                    SendData(self._send_data), SendInitData(self._send_init), BGThreadRunning(self._bg)]
        self.lib.ngSpice_Init(*self._cb, None)
        self.lib.ngSpice_Command.argtypes = [ctypes.c_char_p]
        self.lib.ngGet_Vec_Info.restype = ctypes.POINTER(VecInfo)
        self.lib.ngGet_Vec_Info.argtypes = [ctypes.c_char_p]
        self.lib.ngSpice_AllVecs.restype = ctypes.POINTER(ctypes.c_char_p)
        self.lib.ngSpice_AllVecs.argtypes = [ctypes.c_char_p]
        self.lib.ngSpice_CurPlot.restype = ctypes.c_char_p
        # The shared-library API does not read the executable's spinit file.
        # Homebrew ships XSPICE code models beside libngspice.
        model_dir = os.environ.get('NGSPICE_CODEMODELS')
        if not model_dir and sys.platform == 'darwin':
            model_dir = os.path.join(os.path.dirname(os.path.realpath(path)), 'ngspice')
        if model_dir:
            for model in sorted(glob.glob(os.path.join(model_dir, '*.cm'))):
                self.cmd(f'codemodel {model}')
    def _send_char(self, s, i, u):
        self.log.append(s.decode(errors='replace')); return 0
    def _send_stat(self, s, i, u): return 0
    def _exit(self, status, immediate, quit_, i, u): return 0
    def _send_data(self, a, n, i, u): return 0
    def _send_init(self, a, i, u): return 0
    def _bg(self, running, i, u): return 0
    def cmd(self, s):
        return self.lib.ngSpice_Command(s.encode())
    def run_deck(self, path):
        self.log.clear()
        self.cmd(f'source {path}')
        return self.log
    def vectors(self):
        plot = self.lib.ngSpice_CurPlot()
        names = []
        arr = self.lib.ngSpice_AllVecs(plot)
        i = 0
        while arr[i]:
            names.append(arr[i].decode()); i += 1
        out = {}
        for n in names:
            vi = self.lib.ngGet_Vec_Info(f'{plot.decode()}.{n}'.encode())
            if not vi: continue
            v = vi.contents
            if v.v_realdata:
                out[n] = [v.v_realdata[k] for k in range(v.v_length)]
        return out

if __name__ == '__main__':
    ng = NgSpice()
    log = ng.run_deck(sys.argv[1])
    print('\n'.join(l for l in log if 'stdout' in l or 'stderr' in l)[-3000:])
    vec = ng.vectors()
    print('vectors:', {k: len(v) for k, v in vec.items()})
