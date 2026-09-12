"""Reconcile routed PCB metadata with a fresh XML netlist and repair redundant vias.

Run with KiCad's Python. Does not regenerate placement or routing.
"""
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
import pcbnew


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pcb')
    p.add_argument('netlist')
    args = p.parse_args()
    board = pcbnew.LoadBoard(args.pcb)
    components = {c.attrib['ref']: c for c in ET.parse(args.netlist).findall('.//components/comp')}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in components:
            fp.SetExcludedFromBOM(True)
            fp.SetBoardOnly(True)
            continue
        c = components[ref]
        fp.SetValue(c.findtext('value') or '')
        fp.SetFPIDAsString(c.findtext('footprint') or '')
        for field in c.findall('fields/field'):
            fp.SetField(field.attrib['name'], field.text or '')
        if c.findtext('description'):
            fp.SetField('Description', c.findtext('description'))
        for field in fp.GetFields():
            if field.GetName() not in ('Reference', 'Value'):
                field.SetVisible(False)
        pads = [p for p in fp.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
        attr = fp.GetAttributes() & ~(pcbnew.FP_SMD | pcbnew.FP_THROUGH_HOLE)
        if pads and not ref.startswith('TP'):
            attr |= pcbnew.FP_SMD if all(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in pads) else pcbnew.FP_THROUGH_HOLE
        fp.SetAttributes(attr)
        # Schematic includes mounting-hole symbols; purchased BOM filters hardware separately.
        if ref in {'H' + str(n) for n in range(1, 9)}:
            fp.SetExcludedFromBOM(False)
    # Redundant same-net vias with overlapping drills. Their surviving same-net
    # annulus overlaps the removed position; subsequent DRC checks continuity.
    redundant = {'e42ef09a-6fa5-49a7-ba86-f82677b09af7', '50ff5ebe-8d59-422c-bc33-14a2cc1c51b1',
                 'bd4bb56b-2a74-47c2-893e-134761a36019'}
    removed = []
    for track in list(board.GetTracks()):
        if track.m_Uuid.AsString() in redundant:
            assert track.GetClass() == 'PCB_VIA'
            removed.append(track.m_Uuid.AsString())
            board.Remove(track)
    for zone in board.Zones():
        zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    pcbnew.SaveBoard(args.pcb, board)
    print('Reconciled', len(components), 'components; removed redundant vias:', removed)


if __name__ == '__main__':
    main()
