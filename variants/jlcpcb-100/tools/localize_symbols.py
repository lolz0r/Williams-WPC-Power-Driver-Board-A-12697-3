"""Freeze embedded schematic symbols in a project library for reproducible ERC.

Run after schematic generation. Keeps pins, unit geometry and instance UUIDs;
unions actual footprint filters for shared symbols across the hierarchy.
"""
from pathlib import Path
import copy
from sexp import parse, dump, find, find_all, S


def main():
    files = list(Path('.').glob('*.kicad_sch'))
    roots = {p: parse(p.read_text())[0] for p in files}
    filters, definitions = {}, {}
    for root in roots.values():
        for sym in find_all(root, 'symbol'):
            lib = find(sym, 'lib_id')
            if not lib:
                continue
            props = {x[1]: x[2] for x in find_all(sym, 'property')}
            if props.get('Footprint'):
                filters.setdefault(lib[1], set()).add(props['Footprint'].split(':')[-1])
    for root in roots.values():
        for sym in find_all(find(root, 'lib_symbols'), 'symbol'):
            old_id = sym[1]
            old_name = old_id.split(':')[-1]
            name = old_name if old_id.startswith('wpc_symbols:') else old_id.replace(':', '_')
            new = copy.deepcopy(sym)
            new[1] = name
            for sub in find_all(new, 'symbol'):
                assert sub[1].startswith(old_name + '_'), (old_id, sub[1])
                sub[1] = name + sub[1][len(old_name):]
            for prop in find_all(new, 'property'):
                if prop[1] == 'ki_fp_filters':
                    prop[2] = ' '.join(sorted(set(prop[2].split()) | filters.get(old_id, set())))
            if name in definitions:
                assert dump(definitions[name]) == dump(new), 'Conflicting embedded definitions: ' + name
            definitions[name] = new
            sym[:] = copy.deepcopy(new)
            sym[1] = 'wpc_symbols:' + name
        for sym in find_all(root, 'symbol'):
            lib = find(sym, 'lib_id')
            if lib and not lib[1].startswith('wpc_symbols:'):
                lib[1] = 'wpc_symbols:' + lib[1].replace(':', '_')
    for p, root in roots.items():
        p.write_text(dump(root) + '\n')
    Path('wpc_symbols.kicad_sym').write_text(dump(S('kicad_symbol_lib', S('version', 20211014),
        S('generator', 'kicad_symbol_editor'), *[definitions[n] for n in sorted(definitions)])) + '\n')
    Path('sym-lib-table').write_text('(sym_lib_table\n (version 7)\n (lib (name "wpc_symbols")(type "KiCad")(uri "${KIPRJMOD}/wpc_symbols.kicad_sym")(options "")(descr "Project symbol snapshots with verified footprint filters"))\n)\n')
    print('Frozen', len(definitions), 'symbol definitions')


if __name__ == '__main__':
    main()
