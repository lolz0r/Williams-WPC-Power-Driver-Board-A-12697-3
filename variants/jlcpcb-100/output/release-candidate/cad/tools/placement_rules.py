"""Part-specific CPL rotations relative to this project's native footprints.

Angles are CCW. Public LCSC package data is archived in research/jlc-placement-libraries.
Connector model/pad conflicts are manual assembly instructions, not library validation.
"""
ROTATIONS = {
    'C2878759': -90, 'C6772': -90, 'C352961': -90, 'C7948': -90,
    'C165895': -90, 'C485687': 180, 'C2624': 180, 'C3007': 90,
    'C8512': 180, 'C235758': -90,
    'C5200275': -90, 'C505166': 180, 'C94118': 180,
    'C86500': 180, 'C305801': 180, 'C305802': 180,
    'C592598': 180, 'C588986': 180,
}
# These packages have a supplier model facing opposite the numbered pad pattern.
# Fit the friction wall to the OEM inward-facing side. Assembly must resolve the
# library conflict; this must never be reported as numbered-pad verification.
MODEL_PAD_CONFLICTS = {'C86500', 'C305801', 'C305802', 'C588986'}
MANUAL = {
    **{c: 'Supplier housing and numbered pads disagree by 180 deg; CPL follows inward friction wall. Assembler must resolve model/pad conflict against native pin/key guide.' for c in MODEL_PAD_CONFLICTS},
    'C592598': 'No public library; TE family wall orientation inferred, manual placement required. Select matched C592598 row; trim J120/J121 and remove only specified key posts.',
    'C505166': 'Numbered pads verified; supplier library has no 3D housing. Confirm inward friction wall manually.',
    'C5143116': 'Anodes are symmetric; public TO-220 3D model is below PCB / wrongly framed. Retain native tab direction and require manual tab-to-heatsink review.',
    'C906984': 'No public library; manually preserve native +, minus, AC and formed-lead mapping.',
}


def correction(code, footprint):
    angle = ROTATIONS.get(code, 0)
    if not angle:
        return 0
    guards = {
        'C2878759': 'SO-20', 'C6772': 'SO-20', 'C352961': 'SOIC-14',
        'C7948': 'SOIC-14', 'C165895': 'SOIC-18',
        'C485687': 'TO-252', 'C2624': 'TO-252', 'C3007': 'TO-252',
        'C8512': 'SOT-23', 'C235758': 'D2PAK_Schottky_AKA',
        'C5200275': 'XFCN_EH254V_12_34P', 'C505166': '41791-0005',
        'C94118': 'TE_J', 'C86500': 'TE_J', 'C305801': 'TE_J',
        'C305802': 'TE_J', 'C592598': 'TE_J', 'C588986': 'KK-254',
    }
    assert guards[code] in footprint, f'Review rotation for changed footprint: {code} {footprint}'
    return angle
