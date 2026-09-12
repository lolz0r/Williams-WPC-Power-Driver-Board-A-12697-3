# Mechanical models

`tools/make_mechanical_models.py` generates project STEP envelopes using OpenCascade.
They are dimensional review aids, not manufacturer production CAD. Fin slots, lead
bends, fastener threads and nut profiles are simplified. Native KiCad component
models are resolved from the installed KiCad library; those models retain their
upstream licenses. No manufacturer CAD or vendor SPICE redistribution is implied.

Controlled dimensions come from TDK B41252, Nichicon LLS, Bourns SRP1265A, Molex
SDA-41791 and Boyd board-level cooling drawings. Current selected heatsinks are
577202B00000G, 7020BG and 6223BG. Older 7019/6224/5771 envelopes are historical
experiments and are not selected by the current board. Hardware envelopes include
M3×8, M3×12 and M4×16 screws/nuts. The native TO-220 leads are untrimmed.

The 3.96 mm headers now use dimensioned KK396 envelopes instead of scaled KK254
models. Stock full-pin headers still need OEM key-pin preparation. Models describe
nominal geometry; component tolerance, cabinet fit, solder and mating-harness access
are separate checks. See `docs/ASSEMBLY_AND_FIRST_ARTICLE.md`.

J113 uses the project N2534-6002-RB nominal envelope, including solder standoff.
`tools/connector_keys.py --models` makes keyed header variants by removing the
specified pin column. KK254 variants derive from the installed KiCad Connector_Molex
models; KK396 variants derive from the project dimensioned envelopes.
The original full-pin models remain available as manufacturing stock-part references.

The M4 hardware head envelope (7.6 mm diameter × 3.0 mm) conservatively bounds the selected Kanebridge MJ416MPP head (6.75 × 2.60 mm); shaft remains M4 × 16 mm.
