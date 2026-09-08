"""KiCad schematic writer with symbol-library embedding and connectivity tracking."""
import os, glob, math, uuid, copy
from sexp import parse, dump, find, find_all, S, Sym

SYMDIR = glob.glob(os.path.expanduser(
    '~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Symbols/x86_64/stable/*/files/symbols'))[0]

_libcache = {}

def load_lib(libname):
    if libname not in _libcache:
        _libcache[libname] = parse(open(f'{SYMDIR}/{libname}.kicad_sym').read())[0]
    return _libcache[libname]

def lib_symbol_raw(libname, name):
    lib = load_lib(libname)
    for s in find_all(lib, 'symbol'):
        if s[1] == name:
            return s
    raise KeyError(f'{libname}:{name}')

def uid():
    return str(uuid.uuid4())

class SymDef:
    """Resolved symbol definition (extends flattened) with pin geometry."""
    def __init__(self, libname, name, override=None):
        self.libname, self.name = libname, name
        raw = copy.deepcopy(lib_symbol_raw(libname, name))
        ext = find(raw, 'extends')
        if ext:
            base = copy.deepcopy(lib_symbol_raw(libname, ext[1]))
            # take base's sub-symbols and graphics, keep derived properties
            raw = [x for x in raw if not (isinstance(x, list) and x and x[0] == 'extends')]
            props = {p[1]: p for p in find_all(raw, 'property')}
            merged = [Sym('symbol'), name]
            for x in base[2:]:
                if isinstance(x, list) and x and x[0] == 'property':
                    if x[1] in props:
                        merged.append(props[x[1]])
                    else:
                        merged.append(x)
                elif isinstance(x, list) and x and x[0] == 'symbol':
                    y = copy.deepcopy(x)
                    y[1] = name + x[1][len(ext[1]):]
                    merged.append(y)
                else:
                    merged.append(x)
            # add derived-only properties
            for k, p in props.items():
                if not any(isinstance(x, list) and x and x[0] == 'property' and x[1] == k for x in merged):
                    merged.append(p)
            raw = merged
        self.raw = raw
        if override:
            override(self.raw)
        self.pins = {}   # (unit, number) -> (x, y, angle, name, etype)
        self.units = set()
        for sub in find_all(self.raw, 'symbol'):
            unit = int(sub[1].rsplit('_', 2)[1])
            for p in find_all(sub, 'pin'):
                at = find(p, 'at'); nm = find(p, 'name')[1]; num = find(p, 'number')[1]
                self.pins[(unit, num)] = (float(at[1]), float(at[2]), float(at[3]), nm, p[1])
                if unit:
                    self.units.add(unit)
        if not self.units:
            self.units = {1}
        self.power = find(self.raw, 'power') is not None

    @property
    def lib_id(self):
        return f'{self.libname}:{self.name}'

    def embedded(self):
        """lib_symbols entry with name 'lib:name'."""
        r = copy.deepcopy(self.raw)
        r[1] = self.lib_id
        return r

    def unit_pins(self, unit):
        return {num: v for (u, num), v in self.pins.items() if u == unit or u == 0}


def rot_pt(px, py, rot, mirror):
    """Library (y-up) point -> schematic offset (y-down) after mirror then rotation."""
    if mirror == 'x':
        py = -py
    elif mirror == 'y':
        px = -px
    a = math.radians(rot)
    rx = px * math.cos(a) - py * math.sin(a)
    ry = px * math.sin(a) + py * math.cos(a)
    return rx, -ry


def r2(v):
    """Snap to the 1.27 mm (50 mil) schematic grid."""
    return round(round(v / 1.27) * 1.27 + 0.0, 4)


class Sheet:
    def __init__(self, name, filename, paper='A3', title=''):
        self.name, self.filename, self.paper, self.title = name, filename, paper, title
        Sheet.counter = getattr(Sheet, 'counter', 0) + 1
        self.index = Sheet.counter
        self.uuid = uid()
        self.items = []          # raw s-expr items
        self.libsyms = {}        # lib_id -> SymDef
        self.symbols = []        # (ref, unit, SymDef, x, y, rot, mirror, props, uuid, dnp)
        self.pinpts = []         # (ref, pin, x, y)
        self.wires = []          # ((x1,y1),(x2,y2))
        self.labels = []         # (name, x, y)
        self.nc = []             # (x,y)
        self.junctions = set()
        self.texts = []

    # --- drawing primitives -------------------------------------------------
    def symbol(self, ref, sdef, x, y, rot=0, mirror=None, unit=1, value='', footprint='',
               dnp=False, fields=None, ref_off=None, val_off=None, hide_value=False, hide_ref=False):
        self.libsyms[sdef.lib_id] = sdef
        x = round(round(x / 1.27) * 1.27, 4); y = round(round(y / 1.27) * 1.27, 4)
        u = uid()
        props = {'Reference': ref, 'Value': value, 'Footprint': footprint, 'Datasheet': '', 'Description': ''}
        if fields:
            props.update(fields)
        self.symbols.append(dict(ref=ref, unit=unit, sdef=sdef, x=x, y=y, rot=rot, mirror=mirror,
                                 props=props, uuid=u, dnp=dnp, ref_off=ref_off, val_off=val_off,
                                 hide_value=hide_value, hide_ref=hide_ref))
        for num, (px, py, pa, nm, et) in sdef.unit_pins(unit).items():
            dx, dy = rot_pt(px, py, rot, mirror)
            self.pinpts.append((ref, num, r2(x + dx), r2(y + dy), unit, et))
        return u

    def pin(self, ref, num, unit=None):
        for r, n, x, y, u, et in self.pinpts:
            if r == ref and n == str(num) and (unit is None or u == unit):
                return (x, y)
        raise KeyError(f'pin {ref}.{num} u{unit}')

    def wire(self, a, b):
        a = (r2(a[0]), r2(a[1])); b = (r2(b[0]), r2(b[1]))
        if a != b:
            self.wires.append((a, b))

    def path(self, *pts):
        for a, b in zip(pts, pts[1:]):
            self.wire(a, b)

    def junction(self, p):
        self.junctions.add((r2(p[0]), r2(p[1])))

    def label(self, name, p, rot=0, glob=False, shape='passive', size=1.27):
        self.labels.append((name, r2(p[0]), r2(p[1]), rot, glob, shape, size))

    def glabel(self, name, p, rot=0, shape='passive'):
        self.label(name, p, rot, True, shape)

    def power(self, net, p, rot=0, sdef=None):
        """Power symbol; net name = symbol name."""
        sdef = sdef or POWER[net]
        ref = f'#PWR{self.index:02d}{len([s for s in self.symbols if s["ref"].startswith("#PWR")]) + 1:03d}'
        self.symbol(ref, sdef, p[0], p[1], rot, value=net, hide_ref=True)
        return ref

    def pwr_flag(self, p, rot=0):
        ref = f'#FLG{self.index:02d}{len([s for s in self.symbols if s["ref"].startswith("#FLG")]) + 1:03d}'
        self.symbol(ref, POWER['PWR_FLAG'], p[0], p[1], rot, value='PWR_FLAG', hide_ref=True)

    def noconnect(self, p):
        self.nc.append((r2(p[0]), r2(p[1])))

    def text(self, s, p, size=1.5, bold=False, rot=0):
        self.texts.append((s, r2(p[0]), r2(p[1]), size, bold, rot))

    # --- connectivity --------------------------------------------------------
    def connectivity(self):
        """Return list of nets: each {'name': str|None, 'pins': [(ref,pin)], 'labels': [...]}"""
        parent = {}
        allkeys = set()
        def find_(a):
            while parent.get(a, a) != a:
                parent[a] = parent.get(parent[a], parent[a]); a = parent[a]
            return a
        def union(a, b):
            allkeys.add(a); allkeys.add(b)
            ra, rb = find_(a), find_(b)
            if ra != rb: parent[ra] = rb
        for a, b in self.wires:
            union(('p', a), ('p', b))
        # points that lie in the middle of a wire segment connect to it (KiCad semantics)
        pts = set()
        for a, b in self.wires: pts.add(a); pts.add(b)
        for name, x, y, *_ in self.labels: pts.add((x, y))
        def on_seg(p, a, b):
            if p == a or p == b: return False
            if abs((b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0])) > 1e-3: return False
            return min(a[0],b[0])-1e-6 <= p[0] <= max(a[0],b[0])+1e-6 and min(a[1],b[1])-1e-6 <= p[1] <= max(a[1],b[1])+1e-6
        for p in pts:
            if p not in self.junctions:
                continue
            for a, b in self.wires:
                if on_seg(p, a, b):
                    union(('p', p), ('p', a))
        groups = {}
        pins_at = {}
        for ref, num, x, y, u, et in self.pinpts:
            pins_at.setdefault((x, y), []).append((ref, num, et))
        # pins connect to wire endpoints at same point
        for pt, lst in pins_at.items():
            for ref, num, et in lst:
                union(('pin', ref, num), ('p', pt))
        for name, x, y, rot, glob, shape, size in self.labels:
            union(('lbl', name, glob), ('p', (x, y)))
        # power symbols -> net by value
        for s in self.symbols:
            if s['sdef'].power and s['props']['Value'] != 'PWR_FLAG':
                for num, (px, py, pa, nm, et) in s['sdef'].unit_pins(s['unit']).items():
                    union(('pin', s['ref'], num), ('lbl', s['props']['Value'], True))
        nets = {}
        for key in list(allkeys) + [('pin', r, n) for r, n, *_ in self.pinpts]:
            root = find_(key)
            nets.setdefault(root, {'pins': [], 'labels': [], 'glabels': [], 'pts': []})
            if key[0] == 'pin':
                if not key[1].startswith('#'):
                    nets[root]['pins'].append((key[1], key[2]))
            elif key[0] == 'lbl':
                (nets[root]['glabels'] if key[2] else nets[root]['labels']).append(key[1])
            elif key[0] == 'p':
                nets[root]['pts'].append(key[1])
        out = []
        for root, n in nets.items():
            n['pins'] = sorted(set(n['pins']))
            n['glabels'] = sorted(set(n['glabels'])); n['labels'] = sorted(set(n['labels']))
            if not n['pins'] and not n['glabels'] and not n['labels']:
                continue
            out.append(n)
        return out

    # --- output --------------------------------------------------------------
    def auto_paper(self):
        xs, ys = [], []
        for s in self.symbols:
            xs += [s['x'] - 20, s['x'] + 25]; ys += [s['y'] - 25, s['y'] + 25]
        for a, b in self.wires:
            xs += [a[0], b[0]]; ys += [a[1], b[1]]
        for name, x, y, *_ in self.labels:
            xs += [x - 15, x + 15]; ys += [y]
        for s, x, y, *_ in self.texts:
            xs += [x, x + 6 * max(len(l) for l in s.split('\n')) * 0.6]; ys += [y, y + 3 * (s.count('\n') + 1)]
        if not xs:
            return self.paper
        w, h = max(xs), max(ys)
        for name, pw, ph in (('A4', 297, 210), ('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594)):
            if w <= pw - 10 and h <= ph - 12:
                return name
        return 'A0'

    def write(self, path, project, root_uuid, page):
        if not getattr(self, 'is_root', False):
            self.paper = self.auto_paper()
        doc = [Sym('kicad_sch'), S('version', 20260306), S('generator', 'eeschema'), S('generator_version', '10.0'),
               S('uuid', self.uuid), S('paper', self.paper),
               S('title_block', S('title', self.title), S('date', '2026-09-04'), S('rev', 'A'),
                 S('company', 'Modern re-implementation of the Williams A-12697-3 (same form factor)'))]
        libs = [Sym('lib_symbols')]
        for lid in sorted(self.libsyms):
            libs.append(self.libsyms[lid].embedded())
        doc.append(libs)
        for (x, y) in sorted(self.junctions):
            doc.append(S('junction', S('at', x, y), S('diameter', 0), S('color', 0, 0, 0, 0), S('uuid', uid())))
        for (x, y) in self.nc:
            doc.append(S('no_connect', S('at', x, y), S('uuid', uid())))
        for a, b in self.wires:
            doc.append(S('wire', S('pts', S('xy', a[0], a[1]), S('xy', b[0], b[1])),
                         S('stroke', S('width', 0), S('type', Sym('default'))), S('uuid', uid())))
        for s, x, y, size, bold, rot in self.texts:
            fx = S('font', S('size', size, size))
            if bold: fx.append(S('bold', Sym('yes')))
            doc.append(S('text', s, S('exclude_from_sim', Sym('no')), S('at', x, y, rot),
                         S('effects', fx, S('justify', Sym('left'), Sym('top'))), S('uuid', uid())))
        for name, x, y, rot, glob, shape, size in self.labels:
            just = {0: ['left', 'bottom'], 180: ['right', 'bottom'], 90: ['left', 'bottom'], 270: ['right', 'bottom']}[rot % 360]
            eff = S('effects', S('font', S('size', size, size)), S('justify', Sym(just[0]), Sym(just[1])))
            if glob:
                doc.append(S('global_label', name, S('shape', Sym(shape)), S('at', x, y, rot),
                             S('fields_autoplaced', Sym('yes')), eff, S('uuid', uid()),
                             S('property', 'Intersheetrefs', '${INTERSHEET_REFS}', S('at', x, y, 0),
                               S('effects', S('font', S('size', 1.27, 1.27)), S('hide', Sym('yes'))))))
            else:
                doc.append(S('label', name, S('at', x, y, rot), eff, S('uuid', uid())))
        for s in self.symbols:
            sd = s['sdef']
            node = [Sym('symbol'), S('lib_id', sd.lib_id), S('at', s['x'], s['y'], s['rot'])]
            if s['mirror']:
                node.append(S('mirror', Sym(s['mirror'])))
            node += [S('unit', s['unit']), S('exclude_from_sim', Sym('no')), S('in_bom', Sym('no' if s['ref'].startswith('#') else 'yes')),
                     S('on_board', Sym('no' if s['ref'].startswith('#') else 'yes')), S('dnp', Sym('yes' if s['dnp'] else 'no')),
                     S('uuid', s['uuid'])]
            i = 0
            for k, v in s['props'].items():
                if k == 'Reference':
                    off = s['ref_off'] or (2.54, -2.54)
                elif k == 'Value':
                    off = s['val_off'] or (2.54, 0)
                else:
                    off = (0, 0)
                hide = (k not in ('Reference', 'Value')) or (k == 'Value' and s['hide_value']) or (k == 'Reference' and s['hide_ref'])
                eff = S('effects', S('font', S('size', 1.27, 1.27)), S('justify', Sym('left')))
                if hide:
                    eff.append(S('hide', Sym('yes')))
                node.append(S('property', k, v, S('at', r2(s['x'] + off[0]), r2(s['y'] + off[1]), 0), eff))
                i += 1
            for num in sd.unit_pins(s['unit']):
                node.append(S('pin', num, S('uuid', uid())))
            node.append(S('instances', S('project', project, S('path', f'/{root_uuid}/{self.uuid}' if page != 1 else f'/{root_uuid}',
                                                              S('reference', s['ref']), S('unit', s['unit'])))))
            doc.append(node)
        return doc


def make_power_symbol(name, base='+5V', libname='power'):
    """Clone a power symbol from the library under a new name (net name = name)."""
    sd = SymDef(libname, base)
    raw = copy.deepcopy(sd.raw)
    raw[1] = name
    for p in find_all(raw, 'property'):
        if p[1] == 'Value':
            p[2] = name
    for sub in find_all(raw, 'symbol'):
        sub[1] = name + sub[1][len(base):]
        for pin in find_all(sub, 'pin'):
            find(pin, 'name')[1] = name
    obj = SymDef.__new__(SymDef)
    obj.libname, obj.name, obj.raw = libname, name, raw
    obj.pins = {}; obj.units = set()
    for sub in find_all(raw, 'symbol'):
        unit = int(sub[1].rsplit('_', 2)[1])
        for p in find_all(sub, 'pin'):
            at = find(p, 'at'); nm = find(p, 'name')[1]; num = find(p, 'number')[1]
            obj.pins[(unit, num)] = (float(at[1]), float(at[2]), float(at[3]), nm, p[1])
            if unit: obj.units.add(unit)
    if not obj.units: obj.units = {1}
    obj.power = True
    return obj

POWER = {
    '+5V': SymDef('power', '+5V'),
    '+12V': SymDef('power', '+12V'),
    'GND': SymDef('power', 'GND'),
    'PWR_FLAG': SymDef('power', 'PWR_FLAG'),
}
for _n in ['+50V', '+20V', '+18V', '+12VU', '+5V_IN']:
    POWER[_n] = make_power_symbol(_n)
