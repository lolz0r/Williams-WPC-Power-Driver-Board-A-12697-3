import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1]); mm = lambda v: int(round(v * 1e6)); P = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y)); ni = b.GetNetInfo()
L = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'I2': pcbnew.In2_Cu}
def seg(net, layer, x0, y0, x1, y1, w=0.4):
    t = pcbnew.PCB_TRACK(b); t.SetStart(P(x0, y0)); t.SetEnd(P(x1, y1)); t.SetWidth(mm(w)); t.SetLayer(L[layer]); t.SetNet(ni.GetNetItem(net)); b.Add(t)
def via(net, x, y, d=0.8, drill=0.5):
    v = pcbnew.PCB_VIA(b); v.SetPosition(P(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetWidth(mm(d)); v.SetDrill(mm(drill)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(ni.GetNetItem(net)); b.Add(v)
# B13 (U13 bypass) out of the pin channel, to the left of the chip
f = b.FindFootprintByReference('B13'); f.SetPosition(P(383.5, 150.0)); f.SetOrientationDegrees(270)
# CLK_LAMP_ROW: via left of U13, into pin 3, and pin 3 -> pin 11 under the body
seg('CLK_LAMP_ROW', 'I2', 384.4, 148.2, 384.6, 148.2); via('CLK_LAMP_ROW', 384.6, 148.2)
seg('CLK_LAMP_ROW', 'F', 384.6, 148.2, 385.6, 148.36); seg('CLK_LAMP_ROW', 'F', 385.6, 148.36, 386.35, 148.36)
seg('CLK_LAMP_ROW', 'F', 386.35, 148.36, 387.6, 148.36); seg('CLK_LAMP_ROW', 'F', 387.6, 148.36, 390.0, 149.63); seg('CLK_LAMP_ROW', 'F', 390.0, 149.63, 391.3, 149.63)
# D0: pin 12 -> channel -> via -> In2 under D2's wall -> back up to the existing D0 via (397.4, 152.2)
seg('D0', 'F', 391.3, 148.36, 394.0, 148.36); seg('D0', 'F', 394.0, 148.36, 394.0, 150.4); via('D0', 394.0, 150.4)
seg('D0', 'I2', 394.0, 150.4, 394.0, 154.2); seg('D0', 'I2', 394.0, 154.2, 397.4, 154.2); seg('D0', 'I2', 397.4, 154.2, 397.4, 152.2)
# ROWCLR1: pin 13 -> right lane (x = 394.8) -> existing track at (394.4, 152.6)
seg('ROWCLR1', 'F', 391.3, 147.09, 392.6, 147.09); seg('ROWCLR1', 'F', 392.6, 147.09, 392.6, 147.4); seg('ROWCLR1', 'F', 392.6, 147.4, 394.8, 147.4)
seg('ROWCLR1', 'F', 394.8, 147.4, 394.8, 152.6); seg('ROWCLR1', 'F', 394.8, 152.6, 394.4, 152.6)
# +5V feed for the ROWCLR1 pull-up R149 (was through B13's pad)
seg('+5V', 'F', 394.0, 145.4, 394.0, 146.0, 0.8); seg('+5V', 'F', 394.0, 146.0, 397.6, 146.0, 0.8); seg('+5V', 'F', 397.6, 146.0, 397.6, 148.72, 0.8); seg('+5V', 'F', 397.6, 148.72, 399.46, 148.72, 0.8)
# D4: U11 pin-12 group -> via under the body edge -> In2 -> via -> existing east group
seg('D4', 'F', 354.4, 147.2, 354.4, 146.6); via('D4', 354.4, 146.6); seg('D4', 'I2', 354.4, 146.6, 365.8, 146.6); via('D4', 365.8, 146.6); seg('D4', 'F', 365.8, 146.6, 367.6, 144.4)
# SOL21_L: In2 corridor -> B.Cu -> R38
via('SOL21_L', 196.2, 117.5); seg('SOL21_L', 'B', 196.2, 117.5, 193.0, 117.5); seg('SOL21_L', 'B', 193.0, 117.5, 193.0, 135.0); via('SOL21_L', 193.0, 135.0, 1.2, 0.6); seg('SOL21_L', 'F', 193.0, 135.0, 196.2, 138.0)
# +12VU into R250.1 (the 3 mm bus only touches the pad)
seg('+12VU', 'F', 38.4, 63.71, 40.41, 63.71)
# GND stitch vias for J103 pins 1 and 4
for y in (28.0, 39.9): via('GND', 429.0, y, 1.2, 0.6); seg('GND', 'F', 432.0, y, 429.0, y, 0.8)
# H9 (BR3 bolt hole): drop its courtyard so the intended overlap with BR3 is not an error
h = b.FindFootprintByReference('H9')
for g in list(h.GraphicalItems()):
    if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd): h.Remove(g)
pcbnew.SaveBoard(sys.argv[1], b); print('hand routes + B13 move + H9 courtyard applied')
