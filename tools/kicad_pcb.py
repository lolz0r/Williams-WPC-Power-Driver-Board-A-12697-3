"""KiCad 10 PCB writer: embeds library footprints, assigns nets, draws outline."""
import os, glob, copy, math, uuid
from sexp import parse, dump, find, find_all, S, Sym

FPDIR = glob.glob(os.path.expanduser(
    '~/.local/share/flatpak/runtime/org.kicad.KiCad.Library.Footprints/x86_64/stable/*/files/footprints'))[0]
_cache = {}

def uid():
    return str(uuid.uuid4())

LOCAL_FPDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'footprints'))   # project libraries (fp-lib-table)

def load_fp(lib_id):
    if lib_id not in _cache:
        lib, name = lib_id.split(':', 1)
        path = f'{LOCAL_FPDIR}/{lib}.pretty/{name}.kicad_mod'
        if not os.path.exists(path):
            path = f'{FPDIR}/{lib}.pretty/{name}.kicad_mod'
        _cache[lib_id] = parse(open(path).read())[0]
    return copy.deepcopy(_cache[lib_id])

def pad_centroid(fp):
    xs, ys = [], []
    for p in find_all(fp, 'pad'):
        if p[2] == 'np_thru_hole':
            continue
        at = find(p, 'at'); xs.append(float(at[1])); ys.append(float(at[2]))
    if not xs:
        return 0.0, 0.0
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

def rot_vec(x, y, deg):
    """KiCad board rotation (CCW positive on screen, y down): (x,y)->(x cos + y sin, -x sin + y cos)."""
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)

def r3(v):
    return round(v, 3)

LAYERS = [(0, 'F.Cu', 'signal'), (4, 'In1.Cu', 'power'), (6, 'In2.Cu', 'signal'), (2, 'B.Cu', 'signal'), (9, 'F.Adhes', 'user', 'F.Adhesive'), (11, 'B.Adhes', 'user', 'B.Adhesive'),
          (13, 'F.Paste', 'user'), (15, 'B.Paste', 'user'), (5, 'F.SilkS', 'user', 'F.Silkscreen'), (7, 'B.SilkS', 'user', 'B.Silkscreen'),
          (1, 'F.Mask', 'user'), (3, 'B.Mask', 'user'), (17, 'Dwgs.User', 'user', 'User.Drawings'), (19, 'Cmts.User', 'user', 'User.Comments'),
          (21, 'Eco1.User', 'user', 'User.Eco1'), (23, 'Eco2.User', 'user', 'User.Eco2'), (25, 'Edge.Cuts', 'user'), (27, 'Margin', 'user'),
          (31, 'F.CrtYd', 'user', 'F.Courtyard'), (29, 'B.CrtYd', 'user', 'B.Courtyard'), (35, 'F.Fab', 'user'), (33, 'B.Fab', 'user')]

class Board:
    def __init__(self, title):
        self.title = title
        self.footprints = []
        self.graphics = []
        self.nets = set()

    def footprint(self, ref, lib_id, cx, cy, rot, value, padnets, dnp=False, path='', sheetname='', sheetfile='',
                  center_on_pads=True, extra_fields=None, ref_size=1.0):
        fp = load_fp(lib_id)
        # origin so that pad centroid lands on (cx, cy)
        if center_on_pads:
            ox, oy = pad_centroid(fp)
            dx, dy = rot_vec(ox, oy, rot)
            x0, y0 = cx - dx, cy - dy
        else:
            x0, y0 = cx, cy
        node = [Sym('footprint'), lib_id, S('layer', 'F.Cu'), S('uuid', uid()), S('at', r3(x0), r3(y0), rot)]
        skip = {'property', 'pad', 'attr', 'layer', 'uuid', 'at', 'tstamp', 'path', 'sheetname', 'sheetfile', 'version', 'generator', 'generator_version', 'tedit'}
        desc = find(fp, 'descr'); tags = find(fp, 'tags')
        # properties
        def prop(k, v, layer, hide, at=(0, 0), size=1.0):
            eff = S('effects', S('font', S('size', size, size), S('thickness', 0.15)))
            n = S('property', k, v, S('at', r3(at[0]), r3(at[1]), rot), S('layer', layer))
            if hide: n.append(S('hide', Sym('yes')))
            n.append(S('uuid', uid())); n.append(eff)
            return n
        # keep library positions for Reference/Value text if available
        libprops = {p[1]: p for p in find_all(fp, 'property')}
        def lib_at(k, default):
            p = libprops.get(k)
            if p:
                at = find(p, 'at')
                return (float(at[1]), float(at[2]))
            return default
        node.append(prop('Reference', ref, 'F.SilkS', ref.startswith('H'), lib_at('Reference', (0, -3)), ref_size))
        node.append(prop('Value', value, 'F.Fab', False, lib_at('Value', (0, 3))))
        node.append(prop('Datasheet', '', 'F.Fab', True))
        node.append(prop('Description', desc[1] if desc else '', 'F.Fab', True))
        for k, v in (extra_fields or {}).items():
            node.append(prop(k, v, 'F.Fab', True))
        if path:
            node.append(S('path', path))
        if sheetname:
            node.append(S('sheetname', sheetname)); node.append(S('sheetfile', sheetfile))
        attr = [Sym('attr'), Sym('through_hole')]
        if ref.startswith('H'):
            attr += [Sym('exclude_from_pos_files'), Sym('exclude_from_bom')]
        if dnp:
            attr += [Sym('dnp')]
        node.append(attr)
        for x in fp[2:]:
            if not isinstance(x, list):
                continue
            key = x[0]
            if key in skip:
                continue
            y = copy.deepcopy(x)
            if key == 'fp_text':
                at = find(y, 'at')
                if at:
                    ang = float(at[3]) if len(at) > 3 else 0.0
                    while len(at) < 4: at.append(0)
                    at[3] = r3(ang + rot)
            if find(y, 'uuid') is None and key.startswith(('fp_', 'zone')):
                y.append(S('uuid', uid()))
            node.append(y)
        # 3D model stand-ins for footprints whose library model is missing (render/STEP only, no effect on fabrication)
        import re as _re
        m = _re.match(r'Connector_Molex:Molex_KK-396_A-41791-00(\d\d)_1x(\d\d)_P3\.96mm_Vertical', lib_id)
        if m:
            n = m.group(1)
            node = [x for x in node if not (isinstance(x, list) and x and x[0] == 'model')]
            node.append(S('model', f'${{KICAD10_3DMODEL_DIR}}/Connector_Molex.3dshapes/Molex_KK-254_AE-6410-{n}A_1x{n}_P2.54mm_Vertical.step',
                          S('offset', S('xyz', 0, 0, 0)), S('scale', S('xyz', 1.559, 1.45, 1.45)), S('rotate', S('xyz', 0, 0, 0))))
        # library footprints whose referenced STEP file is not shipped in this KiCad 3D package: closest available stand-ins (render only)
        STANDIN = {'Inductor_SMD:L_Bourns_SRP1245A': ('Inductor_SMD.3dshapes/L_Bourns_SRR1260.step', (1.04, 1.04, 1.08)),
                   'Package_SO:Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm': ('Package_SO.3dshapes/HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm.step', (1, 1, 1)),
                   'Relay_THT:Relay_DPDT_Omron_G2RL-2': ('Relay_THT.3dshapes/Relay_DPDT_Omron_G2RL.step', (1, 1, 1))}
        if lib_id in STANDIN:
            mdl, sc = STANDIN[lib_id]
            node = [x for x in node if not (isinstance(x, list) and x and x[0] == 'model')]
            node.append(S('model', '${KICAD10_3DMODEL_DIR}/' + mdl, S('offset', S('xyz', 0, 0, 0)), S('scale', S('xyz', *sc)), S('rotate', S('xyz', 0, 0, 0))))
        if lib_id.startswith('Fuse:Fuseholder_Clip-5x20mm_Keystone_3517_Inline'):
            # the library's 3517 model file is not shipped: stand in a 5x20 mm open fuse holder (with fuse) centred on the clip pair
            node = [x for x in node if not (isinstance(x, list) and x and x[0] == 'model')]
            node.append(S('model', '${KICAD10_3DMODEL_DIR}/Fuse.3dshapes/Fuseholder_Cylinder-5x20mm_Schurter_0031_8201_Horizontal_Open.step',
                          S('offset', S('xyz', 0.3, 0, 0)), S('scale', S('xyz', 1, 1, 1)), S('rotate', S('xyz', 0, 0, 0))))
        if lib_id.startswith('Fuse:Fuseholder_Clip-6.3x32mm_Littelfuse_102_Inline'):
            node = [x for x in node if not (isinstance(x, list) and x and x[0] == 'model')]
            node.append(S('model', '${KICAD10_3DMODEL_DIR}/Fuse.3dshapes/Fuseholder_Cylinder-6.3x32mm_Schurter_0031-8002_Horizontal_Open.step',
                          S('offset', S('xyz', -1.65, 0, 0)), S('scale', S('xyz', 0.912, 1, 1)), S('rotate', S('xyz', 0, 0, 0))))
        for p in find_all(fp, 'pad'):
            q = copy.deepcopy(p)
            at = find(q, 'at')
            ang = float(at[3]) if len(at) > 3 else 0.0
            while len(at) < 4: at.append(0)
            at[3] = r3((ang + rot) % 360)
            num = q[1]
            net = padnets.get(num)
            # strip old net/uuid
            q = [z for z in q if not (isinstance(z, list) and z and z[0] in ('net', 'uuid', 'tstamp'))]
            if net and q[2] != 'np_thru_hole':
                q.append(S('net', net)); self.nets.add(net)
            q.append(S('uuid', uid()))
            node.append(q)
        self.footprints.append(node)
        return node

    def line(self, a, b, layer='Edge.Cuts', width=0.1):
        self.graphics.append(S('gr_line', S('start', r3(a[0]), r3(a[1])), S('end', r3(b[0]), r3(b[1])),
                               S('stroke', S('width', width), S('type', Sym('solid'))), S('layer', layer), S('uuid', uid())))

    def arc(self, start, mid, end, layer='Edge.Cuts', width=0.1):
        self.graphics.append(S('gr_arc', S('start', r3(start[0]), r3(start[1])), S('mid', r3(mid[0]), r3(mid[1])), S('end', r3(end[0]), r3(end[1])),
                               S('stroke', S('width', width), S('type', Sym('solid'))), S('layer', layer), S('uuid', uid())))

    def rect(self, a, b, layer='Dwgs.User', width=0.15):
        self.graphics.append(S('gr_rect', S('start', r3(a[0]), r3(a[1])), S('end', r3(b[0]), r3(b[1])),
                               S('stroke', S('width', width), S('type', Sym('solid'))), S('fill', Sym('no')), S('layer', layer), S('uuid', uid())))

    def text(self, s, p, layer='F.SilkS', size=2.0, thick=0.3, rot=0, justify=None):
        eff = S('effects', S('font', S('size', size, size), S('thickness', thick)))
        if layer.startswith('B.'):
            justify = list(justify or []) + ['mirror']
        if justify: eff.append(S('justify', *[Sym(j) for j in justify]))
        self.graphics.append(S('gr_text', s, S('at', r3(p[0]), r3(p[1]), rot), S('layer', layer), S('uuid', uid()), eff))

    def zone(self, net, layer, pts, name, clearance=0.4, min_thick=0.3, thermal_gap=0.5, spoke=1.0):
        poly = S('pts', *[S('xy', r3(x), r3(y)) for x, y in pts])
        self.graphics.append(S('zone', S('net', net), S('layer', layer), S('uuid', uid()), S('name', name), S('hatch', Sym('edge'), 0.5),
                               S('connect_pads', S('clearance', clearance)), S('min_thickness', min_thick),
                               S('fill', Sym('yes'), S('thermal_gap', thermal_gap), S('thermal_bridge_width', spoke), S('island_removal_mode', 0)),
                               S('polygon', poly)))
        self.nets.add(net)

    def rounded_outline(self, w, h, r=3.0):
        # clockwise from top-left, KiCad y down
        self.line((r, 0), (w - r, 0)); self.arc((w - r, 0), (w - r * (1 - math.sqrt(0.5)), r * (1 - math.sqrt(0.5))), (w, r))
        self.line((w, r), (w, h - r)); self.arc((w, h - r), (w - r * (1 - math.sqrt(0.5)), h - r * (1 - math.sqrt(0.5))), (w - r, h))
        self.line((w - r, h), (r, h)); self.arc((r, h), (r * (1 - math.sqrt(0.5)), h - r * (1 - math.sqrt(0.5))), (0, h - r))
        self.line((0, h - r), (0, r)); self.arc((0, r), (r * (1 - math.sqrt(0.5)), r * (1 - math.sqrt(0.5))), (r, 0))

    def write(self, path):
        doc = [Sym('kicad_pcb'), S('version', 20260206), S('generator', 'pcbnew'), S('generator_version', '10.0'),
               S('general', S('thickness', 1.6), S('legacy_teardrops', Sym('no'))), S('paper', 'A2'),
               S('title_block', S('title', self.title), S('date', '2026-09-04'), S('rev', 'A'),
                 S('company', 'Reverse-engineered from Williams STTNG manual'))]
        lay = [Sym('layers')]
        for l in LAYERS:
            n = [l[0], l[1], Sym(l[2])]
            if len(l) > 3: n.append(l[3])
            lay.append(n)
        doc.append(lay)
        stack = S('stackup',
                  S('layer', 'F.SilkS', S('type', 'Top Silk Screen')), S('layer', 'F.Paste', S('type', 'Top Solder Paste')),
                  S('layer', 'F.Mask', S('type', 'Top Solder Mask'), S('thickness', 0.01)),
                  S('layer', 'F.Cu', S('type', 'copper'), S('thickness', 0.035)),
                  S('layer', 'dielectric 1', S('type', 'prepreg'), S('thickness', 0.2), S('material', 'FR4'), S('epsilon_r', 4.5), S('loss_tangent', 0.02)),
                  S('layer', 'In1.Cu', S('type', 'copper'), S('thickness', 0.035)),
                  S('layer', 'dielectric 2', S('type', 'core'), S('thickness', 1.05), S('material', 'FR4'), S('epsilon_r', 4.5), S('loss_tangent', 0.02)),
                  S('layer', 'In2.Cu', S('type', 'copper'), S('thickness', 0.035)),
                  S('layer', 'dielectric 3', S('type', 'prepreg'), S('thickness', 0.2), S('material', 'FR4'), S('epsilon_r', 4.5), S('loss_tangent', 0.02)),
                  S('layer', 'B.Cu', S('type', 'copper'), S('thickness', 0.035)),
                  S('layer', 'B.Mask', S('type', 'Bottom Solder Mask'), S('thickness', 0.01)),
                  S('layer', 'B.Paste', S('type', 'Bottom Solder Paste')), S('layer', 'B.SilkS', S('type', 'Bottom Silk Screen')),
                  S('copper_finish', 'None'), S('dielectric_constraints', Sym('no')))
        doc.append(S('setup', stack, S('pad_to_mask_clearance', 0), S('allow_soldermask_bridges_in_footprints', Sym('no')),
                     S('tenting', S('front', Sym('yes')), S('back', Sym('yes'))),
                     S('pcbplotparams', S('layerselection', Sym('0x00000000_00000000_55555555_5755f5ff')),
                       S('plot_on_all_layers_selection', Sym('0x00000000_00000000_00000000_00000000')),
                       S('disableapertmacros', Sym('no')), S('usegerberextensions', Sym('no')), S('usegerberattributes', Sym('yes')),
                       S('usegerberadvancedattributes', Sym('yes')), S('creategerberjobfile', Sym('yes')), S('svgprecision', 6),
                       S('plotframeref', Sym('no')), S('mode', 1), S('useauxorigin', Sym('no')), S('outputformat', 1), S('mirror', Sym('no')),
                       S('drillshape', 1), S('scaleselection', 1), S('outputdirectory', 'output/gerbers/'))))
        for g in self.graphics:
            doc.append(g)
        for f in self.footprints:
            doc.append(f)
        open(path, 'w').write(dump(doc) + '\n')
