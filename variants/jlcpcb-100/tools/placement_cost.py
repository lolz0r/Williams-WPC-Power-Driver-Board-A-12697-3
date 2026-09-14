"""Placement for the cost-optimised board (copied from placement_modern.py).  Board outline, mounting holes, every connector, fuse,
bridge rectifier and big capacitor sit exactly where they are on the A-12697-3 assembly drawing (coordinates from the original
project's placement.py).  The generator places footprints by PAD CENTROID: the Keystone 3517 5x20 mm clip footprint (pads at 0 /
6.76 / 16.35 / 23.11 mm, centroid 11.555 mm) therefore lands with its fuse centre on the same board coordinate as the 3AG clip
footprint (centroid 17.105 mm) - no per-fuse adjustment needed.  DPAK MOSFETs keep the TO-220 spots and rotations; the GBJ bridges
(BR1/BR4) and the GBU8J (BR2) keep the GBPC block positions.  Coordinates are drawing-frame pixels (see placement.py)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'wpc_power_driver', 'tools'))
import placement as ORIG
PX_PER_IN, MM, BOARD_W, BOARD_H, EDGE_MARGIN = ORIG.PX_PER_IN, ORIG.MM, ORIG.BOARD_W, ORIG.BOARD_H, ORIG.EDGE_MARGIN
board_xy = ORIG.board_xy
GI_TRIAC = ORIG.GI_TRIAC

POS = {}
def P(ref, px, py, rot=0): POS[ref] = (px, py, rot)

# ---- everything that must not move: connectors, fuses, holes, bridges, big caps, ICs, test points, LEDs
KEEP = [r for r in ORIG.POS if r[0] in 'JFH'] + ['BR1', 'BR2', 'BR3', 'BR4', 'BR5', 'C5', 'C6', 'C7', 'C11', 'C30',
        'TP1', 'TP2', 'TP3', 'TP4', 'TP5', 'TP6', 'TP7', 'TP8', 'LED1', 'LED2', 'LED3', 'LED4', 'LED5', 'LED6', 'LED7',
        'R194', 'R196', 'R250', 'R251', 'R253', 'R192', 'R193', 'R260', 'SR1', 'U1', 'U2', 'U3', 'U4', 'U5', 'U6', 'U10', 'U11', 'U12', 'U13',
        'U15', 'U16', 'U18', 'U19', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B10', 'B11', 'B12', 'B13', 'B15', 'B16', 'B18', 'B19',
        'R197', 'R198', 'R254', 'R206', 'R255', 'R256', 'C21', 'R3', 'R4', 'R6', 'R162', 'C31', 'D33', 'D34',
        'R142', 'R143', 'R144', 'R145', 'R146', 'R147', 'R148', 'R149', 'C13', 'C14', 'C15', 'C16', 'C17', 'C18', 'C19', 'C20',
        'R150', 'R151', 'R152', 'R153', 'R172', 'R173', 'R174', 'R175', 'W2', 'RLY1', 'Q3', 'R202', 'R209', 'D35']
for r in KEEP:
    if r in ORIG.POS: POS[r] = ORIG.POS[r]      # the original project's placement may drop/rename parts
# U1 (triac/GI latch) rotated 180 deg on 2026-09-06: with GI_BIT5/GI_BIT6 -> J111 the original orientation is unroutable
# (pins 13/14 would have to cross GI5_L inside the U1 channel, which the In2 data-bus lines and B.Cu D7/BLANKING wall off).
x, y, r = POS['U1']; P('U1', x, y, (r + 180) % 360)
for r in ('J111', 'J133', 'J134', 'J135'):      # KK-254 footprints have their pin row along +X (pin headers: +Y)
    x, y, rot = POS[r]; POS[r] = (x, y, (rot + 270) % 360)
P('TP9', 600, 1650, 0)
# factory schematic (16-9834.2) / pinwiki: TP6 = +50V (near C8/R260), TP8 = +18V (near C6): swap the two designators of the assembly-drawing reading
POS['TP6'], POS['TP8'] = ORIG.POS['TP8'], ORIG.POS['TP6']
# interface fixes: U9 (74HCT240 data inverter) and its bypass at the original U9/B9 spot, SR2 next to SR1, R259 next to R260, W1 (G.I. return link) next to J115
POS['U9'] = ORIG.POS['U9']; POS['B9'] = ORIG.POS['B9']
P('SR2', 1090, 5145, 180); P('R259', 985, 1773, 90); P('W1', 2440, 5180, 0)
# ---- lamp columns (P-MOSFET at the TIP107 spot; gate-source R left, series R right)
for q in [91, 92, 93, 94, 95, 96, 97, 98]:
    x, y, _ = ORIG.POS[f'Q{q}']; P(f'Q{q}', x, y, 90)
colres = {95: ('R184', 'R185'), 96: ('R186', 'R187'), 97: ('R188', 'R189'), 98: ('R190', 'R191'), 91: ('R176', 'R177'), 92: ('R178', 'R179'), 93: ('R180', 'R181'), 94: ('R182', 'R183')}
for q, (rgs, rser) in colres.items():
    x, y, _ = POS[f'Q{q}']; P(rgs, x - 45, y + 45, 90); P(rser, x + 45, y + 45, 90)
# ---- lamp rows (N-MOSFET at the TIP102 spot; gate R left, 1k right, pull-down below)
rowres = {87: ('R164', 'R165', 'R304'), 88: ('R166', 'R167', 'R303'), 89: ('R168', 'R169', 'R302'), 90: ('R170', 'R171', 'R301'),
          83: ('R154', 'R155', 'R308'), 84: ('R156', 'R157', 'R307'), 85: ('R158', 'R159', 'R306'), 86: ('R160', 'R161', 'R305')}
for q, (r1k, rg, rpd) in rowres.items():
    x, y, _ = ORIG.POS[f'Q{q}']; P(f'Q{q}', x, y, 90)
    P(rg, x - 45, y + 45, 90); P(r1k, x + 45, y + 45, 90); P(rpd, x, y + 80, 0)
# ---- solenoid drivers
HP_X = [1730, 2020, 2320, 2625]
HP = {1: (3, 1643), 2: (2, 1643), 3: (1, 1643), 4: (0, 1643), 5: (0, 1936), 6: (1, 1936), 7: (2, 1936), 8: (3, 1936)}
HP_PARTS = {1: ('Q82', 'R141', 'R140', 'D32'), 2: ('Q80', 'R139', 'R138', 'D31'), 3: ('Q78', 'R137', 'R136', 'D30'), 4: ('Q76', 'R135', 'R134', 'D29'),
            5: ('Q64', 'R127', 'R126', 'D25'), 6: ('Q66', 'R129', 'R128', 'D26'), 7: ('Q68', 'R131', 'R130', 'D27'), 8: ('Q70', 'R133', 'R132', 'D28')}
for n, (col, y) in HP.items():
    q, rg, rpd, dio = HP_PARTS[n]; x = HP_X[col]
    P(rg, x + 45, y, 90); P(rpd, x, y, 90); P(q, x + 100, y, 90); P(dio, x + 165, y, 90)
LP_X = [1780, 2095, 2410, 2725]
LP_ROWS = {2186: [52, 54, 56, 58], 2446: [44, 46, 48, 50], 2729: [36, 38, 40, 42], 3009: [28, 30, 32, 34], 3409: [20, 22, 24, 26]}
DIO = {20: 5, 22: 6, 24: 7, 26: 8, 28: 9, 30: 10, 32: 11, 34: 12, 36: 1, 38: 2, 40: 3, 42: 38, 44: 17, 46: 18, 48: 19, 50: 20, 52: 21, 54: 22, 56: 23, 58: 24}
for y, qs in LP_ROWS.items():
    for col, qt in enumerate(qs):
        x = LP_X[col]; k = (qt - 20) // 2; r = 22 + 4 * k
        P(f'R{r}', x - 80, y, 90); P(f'R{r + 1}', x - 45, y, 90); P(f'Q{qt}', x, y, 90); P(f'D{DIO[qt]}', x + 45, y, 90)
# ---- GI triacs: NPN at the 2N5401 spot, base pull-down left, gate resistor right, base resistor row as before
for q, (x, y) in GI_TRIAC.items():
    P(q, x, y, 0)
GI_SMALL = {'Q17': (1880, 3682, 'R21', 'R19'), 'Q9': (2495, 3682, 'R9', 'R7'), 'Q13': (1580, 4192, 'R15', 'R13'), 'Q15': (2190, 4172, 'R18', 'R16'), 'Q11': (1900, 4640, 'R12', 'R10')}
for q, (x, y, rpd, rgate) in GI_SMALL.items():
    P(q, x, y, 0); P(rpd, x - 55, y, 90); P(rgate, x + 55, y, 90)
for i, r in enumerate(['R8', 'R11', 'R14', 'R17', 'R20']):
    P(r, 1385 + i * 40, 3922, 90)
# ---- power section
P('C8', 1115, 1493, 0); P('C32', 1115, 1760, 0)            # 2 x 2200uF/100V (old C8 spot + freed pre-driver area)
# +5V buck U20 cluster in the old LM323K heatsink area (520..1035 x 1816..2366)
P('U20', 778, 2091, 0); P('C33', 690, 2040, 90); P('C34', 690, 2110, 90); P('C35', 850, 2030, 0)
P('R261', 690, 2180, 90); P('R262', 690, 2240, 90); P('R263', 760, 2240, 90); P('R264', 880, 2080, 0); P('R265', 880, 2130, 0)
P('R266', 880, 2180, 0); P('C36', 880, 2230, 0); P('C37', 880, 2280, 0); P('D36', 780, 2170, 0); P('L1', 800, 2320, 0)
P('C4', 960, 2330, 0); P('C9', 960, 2470, 0); P('C38', 900, 2400, 0)
# +12V buck U21 cluster in the old LM7812 heatsink area (745..1045 x 3592..3752) and the freed C1/C3/W1 spots
P('U21', 895, 3660, 0); P('C39', 800, 3600, 90); P('C40', 800, 3670, 90); P('C41', 960, 3600, 0)
P('R267', 780, 3540, 90); P('R268', 830, 3540, 90); P('R269', 880, 3540, 90); P('R270', 1000, 3650, 0); P('R271', 1000, 3700, 0)
P('R272', 1000, 3750, 0); P('C42', 1000, 3800, 0); P('C43', 1000, 3850, 0); P('D37', 900, 3740, 0); P('L2', 895, 3830, 0)
P('C2', 820, 3760, 0); P('C12', 820, 3900, 0); P('C44', 900, 3920, 0)

# parts that have no counterpart on the A-12697-3 assembly drawing, placed in board millimetres (see gen_pcb.py)
POS_MM = {'C11': (325.951, 21.46, -90), # 1.2 mm right for the larger TDK capacitor courtyard
          'C21': (86.0, 73.6, 90),      # 10 nF zero-cross filter next to U6 pin 5 (added 2026-09-07; it had no position and was missing from the PCB)
          'J129': (275.5, 265.3, 180),  # 2.5 mm left of the drawing position: at 278.0 its housing sits inside mounting hole H6's courtyard
          'H9': (251.99, 23.30, 0),     # 5.5 mm NPTH for the M4 bolt of BR3 (GBPC3510W) - docs/THERMAL_AND_PROTECTION.md
          # discrete Schottky bridges (2026-09-07, docs/THERMAL_AND_PROTECTION.md section 8).  Project footprint D2PAK_Schottky_AKA:
          # pad 1 = tab = cathode.  Rotation 90 = tab up, 270 = tab down, 0 = tab right, 180 = tab left.  Pours: tools/rail_pours.py
          'D103': (350.0, 32.65, 0), 'D104': (363.4, 17.65, 0), 'D101': (350.0, 53.35, 180), 'D102': (376.0, 77.35, 180),   # BR1 +18V: AC pair (tabs up), DC pair (tabs down)
          'D105': (290.0, 114.0, 0), 'D106': (311.0, 114.0, 180), 'D107': (290.0, 128.0, 180), 'D108': (311.0, 128.0, 0),   # BR2 +5V raw: below C8 / left of U9; DC pair tabs facing, AC pair tabs outward
          'D109': (281.0, 12.0, 0), 'D110': (302.0, 12.0, 180), 'D111': (281.0, 26.0, 180), 'D112': (302.0, 26.0, 0),     # BR4 +20V: DC pair tabs facing, AC pair tabs outward
          'D115': (17.0, 19.0, 90), 'D116': (30.4, 19.0, 90), 'D113': (17.0, 40.0, 270), 'D114': (30.4, 40.0, 270)}       # BR5 +12V power: AC pair (tabs up), DC pair (tabs down)
          # BR5 +12V power
