"""Cost-optimised board sourcing table (extends the modern board's table).  Every entry was checked on DigiKey / Mouser
(Sep 2026, WebSearch snippets - see README "Sourcing notes"); `link` is the DigiKey product page (where a product ID was
verified) or a DigiKey exact-keyword result page.  `price` = DigiKey (or Mouser where noted) qty-1 USD where it was visible,
else None; `price100` = estimated unit price when buying for 100 boards (i.e. 100 x the per-board quantity: reel / 1000-piece
breaks for the parts used 8-32 times per board, 100-piece breaks for the others).  Where no break was visible the rules
0.55-0.7x (semiconductors), 0.3x (passives), 0.6x (connectors / electromechanical) of the qty-1 price were applied."""
DK = 'https://www.digikey.com/en/products/detail/'
KW = 'https://www.digikey.com/en/products/result?keywords='

def kw(mpn): return KW + mpn.replace('#', '%23').replace(',', '%2C').replace('/', '%2F')

SRC = {
    # ---- power semiconductors (new DPAK parts)
    'IRLR3110Z': dict(mfr='Infineon', mpn='IRLR3110ZTRPBF', desc='N-MOSFET 100 V 63 A 14 mOhm @10 V / 16 mOhm @4.5 V logic-level, DPAK (TO-252)',
                      link=DK + 'infineon-technologies/IRLR3110ZTRPBF/1928415', price=1.90, price100=0.78),   # 2800 pcs = full reels
    'IRLR024N':  dict(mfr='Infineon', mpn='IRLR024NTRPBF', desc='N-MOSFET 55 V 17 A 65 mOhm @10 V / 40 mOhm @4.5 V logic-level, DPAK (TO-252)',
                      link=DK + 'infineon-technologies/IRLR024NTRPBF/812549', price=1.02, price100=0.45),   # 800 pcs; TME shows 0.27 @1000
    'IRFR5305':  dict(mfr='Infineon', mpn='IRFR5305TRPBF', desc='P-MOSFET -55 V -31 A 65 mOhm @-10 V, DPAK (TO-252)',
                      link=DK + 'infineon-technologies/IRFR5305TRPBF/811407', price=1.98, price100=0.88),   # 800 pcs
    # ---- interface fixes after the WPC schematic (16-9834.2) review: inverting data buffer, pull-up networks, bleeder
    'HCT240':   dict(mfr='Nexperia', mpn='74HCT240D,653', desc='Octal inverting buffer / line driver, 3-state, SO-20 (7.5 mm) - J113 data bus inverter (the CPU drives the ribbon through a 74LS240)', link=kw('74HCT240D,653'), price=None, price_est=0.75, price100=0.42),
    'RNET47K':  dict(mfr='Bourns', mpn='4610X-101-472LF', desc='Resistor network 9x4.7 k bussed, SIP-10 (ribbon pull-ups)', link=kw('4610X-101-472LF'), price=None, price_est=0.55, price100=0.35),
    # ---- kept from the modern board
    'IRLB4030': dict(mfr='Infineon', mpn='IRLB4030PBF', desc='N-MOSFET 100 V 180 A 4.3 mOhm logic-level, TO-220AB', link=DK + 'infineon-technologies/IRLB4030PBF/2096639', price=None, price100=1.20),
    'TRIAC':    dict(mfr='STMicroelectronics', mpn='BTA16-600CRG', desc='Triac 16 A 600 V, 4-quadrant (Igt 25/50 mA), insulated TO-220AB', link=DK + 'stmicroelectronics/BTA16-600CRG/669145', price=None, price_est=1.45, price100=0.95),
    'NPN':      dict(mfr='Diodes Inc', mpn='MMBT4401-7-F', desc='NPN 40 V 600 mA, SOT-23', link=DK + 'diodes-incorporated/MMBT4401-7-F/775841', price=None, price_est=0.12, price100=0.05),
    # ---- bridge rectifiers (2026-09-07: the low-voltage bridges are four discrete D2PAK Schottky diodes each, the GBJ / GBU entries stay for reference)
    'SCH20100': dict(mfr='STMicroelectronics', mpn='STPS20M100SG-TR', desc='Schottky rectifier 100 V 20 A, D2PAK (TO-263-2, tab = cathode) - discrete bridge element for +18V / +5V raw / +20V / +12V power', link=DK + 'stmicroelectronics/STPS20M100SG-TR/2122461', price=1.58, price100=0.52),   # DigiKey: 1.58 @1, 0.782 @100, 0.519 @1000 reel (16 per board)
    # BR3 must be the WIRE-LEAD version: the footprint (Diode_Bridge_28.6x28.6x7.3mm_P18.0mm_P11.6mm, 1.4 mm drills) takes the GBPC-W leads; the -E4/51 without W has 0.25 in faston lugs (thermal review 2026-09-07)
    'BR35':     dict(mfr='Vishay', mpn='GBPC3510W-E4/51', desc='Bridge rectifier 35 A 1000 V, GBPC-W (28.6 mm square block, wire leads, #10 centre hole, metal base up when PCB-mounted)', link=DK + 'vishay-semiconductor-diodes-division/GBPC3510W-E4-51/605926', price=None, price_est=7.00, price100=4.70),   # lug version was 6.36 / 4.26
    'BR15GBJ':  dict(mfr='Diodes Inc', mpn='GBJ1510-F', desc='Bridge rectifier 15 A 1000 V, GBJ (30 x 20 x 4 mm, leads + ~ ~ - at 10/7.5/7.5 mm)', link=DK + 'diodes-incorporated/GBJ1510-F/768786', price=2.76, price100=1.22),
    'BR8GBU':   dict(mfr='Vishay', mpn='GBU8J-E3/51', desc='Bridge rectifier 8 A 600 V, GBU', link=DK + 'vishay-general-semiconductor-diodes-division/GBU8J-E3-51/2139855', price=None, price_est=1.70, price100=1.00),
    'BR4V':     dict(mfr='Vishay', mpn='GBU4J-E3/51', desc='Bridge rectifier 4 A 600 V, GBU', link=DK + 'vishay-semiconductor-diodes-division/GBU4J-E3-51/2139840', price=2.67, price100=1.20),
    # ---- small diodes
    'S1M':      dict(mfr='Diodes Inc', mpn='S1M-13-F', desc='Rectifier 1 A 1000 V, SMA', link=DK + 'diodes-incorporated/S1M-13-F/804909', price=0.19, price100=0.07),
    'S3M':      dict(mfr='Diodes Inc', mpn='S3M-13-F', desc='Rectifier 3 A 1000 V, SMC', link=DK + 'diodes-incorporated/S3M-13-F/725029', price=0.54, price100=0.20),
    '1N4148W':  dict(mfr='Diodes Inc', mpn='1N4148W-7-F', desc='Small-signal diode 75 V 150 mA, SOD-123', link=kw('1N4148W-7-F'), price=None, price_est=0.12, price100=0.03),
    'B560C':    dict(mfr='Diodes Inc', mpn='B560C-13-F', desc='Schottky 5 A 60 V, SMC', link=DK + 'diodes-incorporated/B560C-13-F/768773', price=None, price_est=0.62, price100=0.30),
    # ---- ICs
    'TPS54360': dict(mfr='Texas Instruments', mpn='TPS54360BDDAR', desc='60 V 3.5 A step-down converter, HSOP-8 PowerPAD (TPS54560B pin-compatible)', link=DK + 'texas-instruments/TPS54360BDDAR/10434703', price=4.52, price100=3.05),
    'HCT574':   dict(mfr='Nexperia', mpn='74HCT574D,653', desc='Octal D-type flip-flop, 3-state, SO-20 (7.5 mm)', link=DK + 'nexperia-usa-inc/74HCT574D-653/763412', price=None, price_est=0.75, price100=0.42),
    'HCT74':    dict(mfr='Texas Instruments', mpn='SN74HCT74DR', desc='Dual D flip-flop with preset/clear, SOIC-14', link=DK + 'texas-instruments/SN74HCT74DR/276479', price=None, price_est=0.55, price100=0.30),
    'LM339':    dict(mfr='Texas Instruments', mpn='LM339DR', desc='Quad comparator, SOIC-14', link=DK + 'texas-instruments/LM339DR/276657', price=0.29, price100=0.12),
    'DRV8':     dict(mfr='Toshiba', mpn='TBD62083AFWG,EL', desc='8-ch DMOS sink driver (ULN2803 pin-compatible), SOIC-18W', link=DK + 'toshiba-semiconductor-and-storage/TBD62083AFWG-EL/5514124', price=None, price_est=1.10, price100=0.75),
    'LED':      dict(mfr='Lite-On', mpn='LTST-C170KRKT', desc='LED red 631 nm, 0805', link=DK + 'liteon/LTST-C170KRKT/386779', price=0.18, price100=0.07),
    # ---- passives
    'L10U':     dict(mfr='Bourns', mpn='SRP1265A-100M', desc='Inductor 10 uH 10 A shielded, 12.5x12.5 mm', link=DK + 'bourns-inc/SRP1265A-100M/4876620', price=None, price_est=2.10, price100=1.30),
    'RNET':     dict(mfr='Bourns', mpn='4610X-101-471LF', desc='Resistor network 9x470 R bussed, SIP-10', link=DK + 'bourns-inc/4610X-101-471LF/1089204', price=None, price_est=0.55, price100=0.35),
    'RS022':    dict(mfr='Yageo', mpn='RL2512FK-070R22L', desc='Resistor 0.22 R 1% 1 W current sense, 2512', link=DK + 'yageo/RL2512FK-070R22L/2827691', price=None, price_est=0.35, price100=0.12),
    'C100N':    dict(mfr='Samsung', mpn='CL21B104KBCNNNC', desc='Capacitor 100 nF 50 V X7R, 0805', link=DK + 'samsung-electro-mechanics/CL21B104KBCNNNC/3886661', price=None, price_est=0.10, price100=0.01),
    'C10U':     dict(mfr='Samsung', mpn='CL32B106KBJNNWE', desc='Capacitor 10 uF 50 V X7R, 1210', link=DK + 'samsung-electro-mechanics/CL32B106KBJNNWE/3889046', price=None, price_est=0.45, price100=0.12),
    'C10N':     dict(mfr='Samsung', mpn='CL21B103KBANNNC', desc='Capacitor 10 nF 50 V X7R, 0805', link=kw('CL21B103KBANNNC'), price=None, price_est=0.10, price100=0.01),
    'C1N5':     dict(mfr='Samsung', mpn='CL21B152KBANNNC', desc='Capacitor 1.5 nF 50 V X7R, 0805', link=kw('CL21B152KBANNNC'), price=None, price_est=0.10, price100=0.01),
    'C2N2':     dict(mfr='Samsung', mpn='CL21B222KBANNNC', desc='Capacitor 2.2 nF 50 V X7R, 0805', link=kw('CL21B222KBANNNC'), price=None, price_est=0.10, price100=0.01),
    'C33N':     dict(mfr='Samsung', mpn='CL21B333KBANNNC', desc='Capacitor 33 nF 50 V X7R, 0805', link=kw('CL21B333KBANNNC'), price=None, price_est=0.10, price100=0.01),
    'C390P':    dict(mfr='Samsung', mpn='CL21C391JBANNNC', desc='Capacitor 390 pF 50 V C0G, 0805', link=kw('CL21C391JBANNNC'), price=None, price_est=0.10, price100=0.01),
    'C470P':    dict(mfr='Samsung', mpn='CL21C471JBANNNC', desc='Capacitor 470 pF 50 V C0G, 0805', link=kw('CL21C471JBANNNC'), price=None, price_est=0.10, price100=0.01),
    'C150N':    dict(mfr='Samsung', mpn='CL21B154KBCNNNC', desc='Capacitor 150 nF 50 V X7R, 0805', link=kw('CL21B154KBCNNNC'), price=None, price_est=0.12, price100=0.02),
    'C470N':    dict(mfr='Samsung', mpn='CL21B474KBFNNNE', desc='Capacitor 470 nF 50 V X7R, 0805', link=kw('CL21B474KBFNNNE'), price=None, price_est=0.15, price100=0.03),
    'C330U':    dict(mfr='Panasonic', mpn='EEU-FR1E331', desc='Capacitor 330 uF 25 V low-ESR 105C, radial 10x12.5 mm', link=DK + 'panasonic-electronic-components/EEU-FR1E331/2433549', price=None, price_est=0.62, price100=0.30),
    'C2200U25': dict(mfr='Panasonic', mpn='EEU-FR1E222', desc='Capacitor 2200 uF 25 V low-ESR 105C, radial 12.5x25 mm', link=kw('EEU-FR1E222'), price=None, price_est=1.40, price100=0.65),
    'C10000U25': dict(mfr='Rubycon', mpn='25USC10000MEFCSN25X25', desc='Capacitor 10000 uF 25 V snap-in 25x25 mm, 85C 3000 h (USC)', link=DK + 'rubycon/25USC10000MEFCSN25X25/3565219', price=None, price_est=2.90, price100=1.85),   # 400 pcs
    'C2200U100': dict(mfr='Nichicon', mpn='LLS2A222MELA', desc='Capacitor 2200 uF 100 V snap-in 25x40 mm', link=DK + 'nichicon/LLS2A222MELA/2548962', price=None, price_est=3.60, price100=2.20),   # 200 pcs
    # ---- connectors / mechanical
    'IDC34':    dict(mfr='3M', mpn='30334-5002HB', desc='Box header 2x17 2.54 mm shrouded, vertical', link=DK + '3m/30334-5002HB/1237402', price=None, price_est=1.10, price100=0.65),
    'KK254_5':  dict(mfr='Molex', mpn='0022232051', desc='KK 254 header 1x5 2.54 mm friction lock', link=kw('0022232051'), price=None, price_est=0.45, price100=0.28),
    'KK254_9':  dict(mfr='Molex', mpn='0022232091', desc='KK 254 header 1x9 2.54 mm friction lock', link=kw('0022232091'), price=None, price_est=0.75, price100=0.45),
    'FUSECLIP': dict(mfr='Keystone', mpn='3517', desc='Fuse clip 5 x 20 mm PCB mount, 15 A, tin (2 per fuse)', link=DK + 'keystone-electronics/3517/316010', price=0.32, price100=0.135),  # 3200 pcs: 0.13 @5000 seen
    'F8A':      dict(mfr='Littelfuse', mpn='0217008.MXP', desc='Fuse 8 A 250 V fast-acting 5x20 mm glass (217 series)', link=DK + 'littelfuse-inc/0217008-MXP/777551', price=0.57, price100=0.32),
    'F7A':      dict(mfr='Littelfuse', mpn='0239007.MXP', desc='Fuse 7 A 125 V Slo-Blo 5x20 mm glass (239 series)', link=DK + 'littelfuse-inc/0239007.MXP/778234', price=None, price_est=0.90, price100=0.50),
    'F5A':      dict(mfr='Littelfuse', mpn='0239005.MXP', desc='Fuse 5 A 125 V Slo-Blo 5x20 mm glass (239 series)', link=DK + 'littelfuse-inc/0239005-MXP/778232', price=1.48, price100=0.38),   # 700 pcs
    'F3A':      dict(mfr='Littelfuse', mpn='0239003.MXP', desc='Fuse 3 A 250 V Slo-Blo 5x20 mm glass (239 series)', link=DK + 'littelfuse-inc/0239003-MXP/778224', price=1.15, price100=0.40),   # 400 pcs
    'F3/4A':    dict(mfr='Littelfuse', mpn='0239.750MXP', desc='Fuse 3/4 A 250 V Slo-Blo 5x20 mm glass (239 series)', link=kw('0239.750MXP'), price=1.00, price100=0.60),   # Newark 0.667 @100
    # ---- heatsinks + hardware (thermal review 2026-09-07, docs/THERMAL_AND_PROTECTION.md).  Boyd board-level catalogue values = natural convection at a 75 C rise.
    # The earlier 577002B00000G clip (listed here as 25 C/W) is a 32 C/W part per the catalogue and gave Tj ~165 C on an incandescent G.I. string - replaced.
    'HS7019':   dict(mfr='Boyd (Aavid)', mpn='7019BG', desc='Heatsink TO-220 bolt-on narrow channel with folded-back fins, 11.0 C/W, 39.4 x 9.5 x 25.4 mm, no PCB tabs (device screw only)', link=kw('7019BG'), price=None, price_est=1.75, price100=1.15),
    'HS7020':   dict(mfr='Boyd (Aavid)', mpn='7020BG', desc='Heatsink TO-220 bolt-on narrow channel with folded-back fins, 8.7 C/W, 33.0 x 11.9 x 36.8 mm, no PCB tabs (device screw only; #6 / M3 hole of the GBJ / GBU bridges)', link=DK + 'aavid-thermal-division-of-boyd-corporation/7020BG/1625705', price=None, price_est=2.40, price100=1.55),
    'HS6224':   dict(mfr='Boyd (Aavid)', mpn='6224BG', desc='Heatsink square basket for bridge rectifiers, 9.4 C/W, 26.92 mm sq x 31.75 mm, 4.77 mm hole (M4), sits on the metal base of the GBPC block', link=kw('6224BG'), price=None, price_est=8.50, price100=6.20),   # 6223BG: DigiKey 8.87 @1, 6.14 @1000; 6224BG Future 6.42
    'M3X12':    dict(mfr='B&F Fastener Supply', mpn='MPMS 003 0012 PH', desc='Screw M3 x 12 mm pan head Phillips, zinc (heatsink to TO-220 / GBJ / GBU)', link=kw('MPMS 003 0012 PH'), price=None, price_est=0.10, price100=0.04),
    'M3NUT':    dict(mfr='B&F Fastener Supply', mpn='MHNZ 003', desc='Hex nut M3, zinc', link=kw('MHNZ 003'), price=None, price_est=0.06, price100=0.02),
    'M4X16':    dict(mfr='B&F Fastener Supply', mpn='MPMS 004 0016 PH', desc='Screw M4 x 16 mm pan head Phillips, zinc (6224BG basket through the GBPC3510W centre hole)', link=kw('MPMS 004 0016 PH'), price=None, price_est=0.12, price100=0.05),
    'M4NUT':    dict(mfr='B&F Fastener Supply', mpn='MHNZ 004', desc='Hex nut M4, zinc', link=kw('MHNZ 004'), price=None, price_est=0.08, price100=0.03),
    'HS220':    dict(mfr='Aavid (Boyd)', mpn='577002B00000G', desc='Clip-on heatsink TO-220, 32 C/W (catalogue) - NO LONGER USED, kept for reference', link=kw('577002B00000G'), price=None, price_est=0.55, price100=0.35),
    'RLY':      dict(mfr='Omron', mpn='G2RL-2 DC12', desc='Relay DPDT 12 V coil (DNP - Fliptronic games)', link=kw('G2RL-2 DC12'), price=None, price_est=3.20, price100=2.20),
}
# KK 396 vertical friction-lock headers, tin: 26-60-4xxx (9-circuit page verified; others by exact keyword)
_KK100 = {3: 0.35, 4: 0.40, 5: 0.45, 6: 0.50, 7: 0.55, 9: 0.65, 11: 0.78, 12: 0.82, 13: 0.88}
_KK1 = {3: 0.55, 4: 0.62, 5: 0.70, 6: 0.78, 7: 0.85, 9: 0.95, 11: 1.20, 12: 1.30, 13: 1.40}
for n in [3, 4, 5, 6, 7, 9, 11, 12, 13]:
    mpn = f'00266040{n:02d}'
    SRC[f'KK{n}'] = dict(mfr='Molex', mpn=mpn, desc=f'KK 396 header 1x{n} 3.96 mm vertical friction lock, tin',
                         link=(DK + 'molex/0026604090/79784') if n == 9 else kw(mpn), price=0.95 if n == 9 else None, price_est=_KK1[n], price100=_KK100[n])

def r0805(val):
    """Yageo RC0805FR-07<val>L 1% 0805 (exact-keyword DigiKey link)."""
    code = val.replace('.', 'R') if 'R' not in val else val
    mpn = f'RC0805FR-07{code}L'
    return dict(mfr='Yageo', mpn=mpn, desc=f'Resistor {val} 1% 0.125 W, 0805', link=kw(mpn), price=None, price_est=0.10, price100=0.01)

def r0805b(val):
    """Yageo RT0805BRD07<val>L 0.1 % 25 ppm thin-film 0805 (feedback dividers)."""
    code = val.replace('.', 'R') if 'R' not in val else val
    mpn = f'RT0805BRD07{code}L'
    return dict(mfr='Yageo', mpn=mpn, desc=f'Resistor {val} 0.1% 25 ppm thin film 0.125 W, 0805', link=kw(mpn), price=None, price_est=0.25, price100=0.06)

def r2512(val, tol='J'):
    mpn = f'RC2512{tol}K-07{val}L'
    return dict(mfr='Yageo', mpn=mpn, desc=f'Resistor {val} 5% 1 W, 2512', link=kw(mpn), price=None, price_est=0.30, price100=0.08)
