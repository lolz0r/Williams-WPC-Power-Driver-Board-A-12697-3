import sys
"""Write the KiCad project: schematic sheets + project file; extract netlist json."""
import os, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from sexp import dump, S, Sym
import kicad_sch as K
import design_cost as D

PROJECT = 'wpc_power_driver_cost'
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def write_schematics():
    root, sheets = D.build_all()
    doc = root.write(os.path.join(OUT, root.filename), PROJECT, root.uuid, 1)
    # hierarchical sheet symbols on the root
    for i, sh in enumerate(sheets):
        col, row = i % 3, i // 3
        x, y = 30 + col * 110, 60 + row * 60
        w, h = 90, 40
        node = [Sym('sheet'), S('at', x, y), S('size', w, h), S('exclude_from_sim', Sym('no')), S('in_bom', Sym('yes')),
                S('on_board', Sym('yes')), S('dnp', Sym('no')), S('fields_autoplaced', Sym('yes')),
                S('stroke', S('width', 0.1524), S('type', Sym('solid'))), S('fill', S('color', 0, 0, 0, 0.0)),
                S('uuid', sh.uuid),
                S('property', 'Sheetname', sh.name, S('at', x, y - 0.7, 0), S('effects', S('font', S('size', 1.5, 1.5)), S('justify', Sym('left'), Sym('bottom')))),
                S('property', 'Sheetfile', sh.filename, S('at', x, y + h + 0.6, 0), S('effects', S('font', S('size', 1.27, 1.27)), S('justify', Sym('left'), Sym('top')))),
                S('instances', S('project', PROJECT, S('path', f'/{root.uuid}', S('page', str(i + 2)))))]
        doc.append(node)
    doc.append(S('sheet_instances', S('path', '/', S('page', '1'))))
    open(os.path.join(OUT, root.filename), 'w').write(dump(doc) + '\n')
    for i, sh in enumerate(sheets):
        d = sh.write(os.path.join(OUT, sh.filename), PROJECT, root.uuid, i + 2)
        open(os.path.join(OUT, sh.filename), 'w').write(dump(d) + '\n')
    return root, sheets

def netlist(sheets):
    """Merge per-sheet connectivity into global nets via global labels / power nets."""
    parent = {}
    def f(a):
        while parent.get(a, a) != a:
            parent[a] = parent.get(parent[a], parent[a]); a = parent[a]
        return a
    def u(a, b):
        ra, rb = f(a), f(b)
        if ra != rb: parent[ra] = rb
    groups = []
    for sh in sheets:
        for n in sh.connectivity():
            key = ('n', sh.name, len(groups)); groups.append((key, sh, n))
            for g in n['glabels']:
                u(key, ('g', g))
    nets = {}
    for key, sh, n in groups:
        root = f(key)
        e = nets.setdefault(root, {'pins': set(), 'glabels': set(), 'labels': set(), 'sheets': set()})
        e['pins'] |= set(n['pins']); e['glabels'] |= set(n['glabels']); e['labels'] |= set((sh.name, l) for l in n['labels']); e['sheets'].add(sh.name)
    out = {}
    for e in nets.values():
        if not e['pins']:
            continue
        if e['glabels']:
            name = sorted(e['glabels'])[0]
        elif e['labels']:
            shn, l = sorted(e['labels'])[0]; name = f'/{shn}/{l}'
        else:
            ref, pin = sorted(e['pins'])[0]; name = f'Net-({ref}-Pad{pin})'
        if len(e['pins']) == 1 and not e['glabels'] and not e['labels']:
            ref, pin = list(e['pins'])[0]
            name = f'unconnected-({ref}-Pad{pin})'
        out[name] = sorted(e['pins'])
    return out

def write_project(sheets):
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5, "copper_text_size_v": 1.5,
                          "copper_text_thickness": 0.3, "silk_line_width": 0.15, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
            "rules": {"min_clearance": 0.2, "min_copper_edge_clearance": 0.5, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.5,
                      "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1, "min_resolved_spokes": 0, "min_silk_clearance": 0.0,
                      "min_text_height": 0.8, "min_text_thickness": 0.08, "min_through_hole_diameter": 0.5, "min_track_width": 0.25,
                      "min_via_annular_width": 0.15, "min_via_diameter": 0.6, "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True},
            "copper_layer_count": 4, "track_widths": [0.0, 0.3, 0.5, 1.0, 2.0, 3.0], "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 1.2, "drill": 0.6}, {"diameter": 1.8, "drill": 1.0}],
            "drc_exclusions": [], "diff_pair_dimensions": [], "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore", "silk_overlap": "ignore", "silk_over_copper": "ignore", "silk_edge_clearance": "ignore", "footprint_type_mismatch": "ignore", "solder_mask_bridge": "ignore", "hole_to_hole": "warning", "npth_inside_courtyard": "warning"}}},
        "boards": [], "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 3},
        "net_settings": {
            "classes": [
                {"name": "Default", "clearance": 0.2, "track_width": 0.4, "via_diameter": 1.2, "via_drill": 0.6, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "bus_width": 12, "wire_width": 6, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647},
                {"name": "Power", "clearance": 0.2, "track_width": 1.0, "via_diameter": 1.8, "via_drill": 1.0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "bus_width": 12, "wire_width": 6, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 0},
                {"name": "HV", "clearance": 0.4, "track_width": 1.6, "via_diameter": 1.8, "via_drill": 1.0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "bus_width": 12, "wire_width": 6, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 0},
                {"name": "Heavy", "clearance": 0.4, "track_width": 5.0, "via_diameter": 1.8, "via_drill": 1.0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "bus_width": 12, "wire_width": 6, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 0},
                {"name": "Bus", "clearance": 0.4, "track_width": 3.0, "via_diameter": 1.8, "via_drill": 1.0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "bus_width": 12, "wire_width": 6, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 0},
                {"name": "Coil", "clearance": 0.3, "track_width": 1.6, "via_diameter": 1.8, "via_drill": 1.0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "bus_width": 12, "wire_width": 6, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 0},
                {"name": "Drive", "clearance": 0.3, "track_width": 1.0, "via_diameter": 1.8, "via_drill": 1.0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                 "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "bus_width": 12, "wire_width": 6, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 1},
            ],
            "meta": {"version": 4},
            "net_colors": None, "netclass_assignments": None,
            "netclass_patterns": [
                {"netclass": "Heavy", "pattern": "GI_RET*"}, {"netclass": "Bus", "pattern": "+18V"}, {"netclass": "Bus", "pattern": "+50V*"}, {"netclass": "Bus", "pattern": "+20V"},
                {"netclass": "Bus", "pattern": "+5V"}, {"netclass": "Bus", "pattern": "/Power_Supply/+5V_RAW"}, {"netclass": "Bus", "pattern": "+12VU"}, {"netclass": "Bus", "pattern": "AC*"},
                {"netclass": "Bus", "pattern": "GI?_IN"}, {"netclass": "Bus", "pattern": "GI?_OUT"}, {"netclass": "Bus", "pattern": "FLIP_?_AC"}, {"netclass": "Bus", "pattern": "/Power_Supply/AC*"},
                {"netclass": "Power", "pattern": "GND"}, {"netclass": "Power", "pattern": "+12V"}, {"netclass": "Power", "pattern": "+12V_F"},
                {"netclass": "HV", "pattern": "+18V"}, {"netclass": "HV", "pattern": "+20V"}, {"netclass": "HV", "pattern": "+50V*"},
                {"netclass": "HV", "pattern": "AC*"}, {"netclass": "HV", "pattern": "GI*_IN"}, {"netclass": "HV", "pattern": "GI*_OUT"},
                {"netclass": "HV", "pattern": "GI*_RET*"}, {"netclass": "HV", "pattern": "FLIP_?_AC"}, {"netclass": "HV", "pattern": "/Power_Supply/AC*"}, {"netclass": "Power", "pattern": "/Power_Supply/+5V_RAW"}, {"netclass": "Power", "pattern": "/Power_Supply/U2?_SW"},
                {"netclass": "Drive", "pattern": "/GI_Triacs/*"},
                {"netclass": "Coil", "pattern": "SOL[0-9][0-9]"}, {"netclass": "Coil", "pattern": "SOL[0-9][0-9]_TB"}, {"netclass": "Drive", "pattern": "COL[0-9]"}, {"netclass": "Drive", "pattern": "ROW[0-9]"},
                {"netclass": "Drive", "pattern": "ROW[0-9]_E"}, {"netclass": "Drive", "pattern": "/Sol_*/S*_D"},
            ]},
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "", "pos_files": "", "specctra_dsn": "", "step": "", "svg": "", "vrml": ""}, "page_layout_descr_file": ""},
        "erc": {"rule_severities": {"lib_symbol_issues": "ignore", "footprint_link_issues": "ignore", "endpoint_off_grid": "warning"}},
        "schematic": {"drawing": {"default_line_thickness": 6.0, "default_text_size": 50.0, "label_size_ratio": 0.375, "pin_symbol_size": 25.0, "text_offset_ratio": 0.15},
                      "legacy_lib_dir": "", "legacy_lib_list": [], "meta": {"version": 1}},
        "sheets": [], "text_variables": {}
    }
    json.dump(pro, open(os.path.join(OUT, f'{PROJECT}.kicad_pro'), 'w'), indent=2)

if __name__ == '__main__':
    if '--overwrite-derived-schematic' not in sys.argv:
        raise SystemExit('Historical generator replaces schematic UUIDs and project rules. Use tools/export_release.py for the routed revision; explicit --overwrite-derived-schematic is required to regenerate.')
    root, sheets = write_schematics()
    nets = netlist(sheets)
    json.dump(nets, open(os.path.join(OUT, '.scratch', 'nets.json'), 'w'), indent=1)
    parts = {r: {k: v for k, v in p.items()} for r, p in D.PARTS.items()}
    json.dump(parts, open(os.path.join(OUT, '.scratch', 'parts.json'), 'w'), indent=1)
    write_project(sheets)
    npins = sum(len(v) for v in nets.values())
    print('sheets written; nets', len(nets), 'pins', npins, 'parts', len(parts))
    # sanity: list nets with single pin (unconnected)
    singles = [n for n, p in nets.items() if len(p) == 1 and not n.startswith('unconnected')]
    print('single-pin named nets:', singles[:40])
