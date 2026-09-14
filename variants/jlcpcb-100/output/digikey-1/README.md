# DigiKey sourcing estimate — one board

> **WARNING: These are unverified, experimental boards. Use at your own risk.**
> This sourcing proposal does not qualify the board or its substitute components.
> Independent engineering review and physical first-article testing are required.

Prepared 2026-09-14 in USD for **one populated board, without production spares**,
using the current `variants/jlcpcb-100` design as the source. The original variant
name does not change this quote's board quantity.

- [DigiKey-BOM.csv](DigiKey-BOM.csv): quantities, original and selected parts,
  DigiKey order numbers, all electronic references, hardware, and review notes.
- [DigiKey-pricing.csv](DigiKey-pricing.csv): itemized prices and purchase costs,
  followed by a priced subtotal and the unresolved complete-total row.
- [DigiKey-totals.csv](DigiKey-totals.csv): category subtotals, minimum-purchase
  overhead, exclusions, and completeness status.
- [source-reference-coverage.csv](source-reference-coverage.csv): maps every row
  in the source BOM to this sourcing BOM.
- [validation.json](validation.json): quantity, price and coverage checks, with
  hashes of the unchanged PCB and release inputs.

## Cost and completeness

| Amount | USD |
| --- | ---: |
| Priced electronics, including candidates | 300.65 |
| Hardware purchase quantities | 78.24 |
| One 3mL thermal-paste syringe | 14.33 |
| Added fuse-holder covers | 12.38 |
| **Priced purchase subtotal** | **405.60** |
| Parts allocated to one board, including the full paste syringe | 363.30 |
| Minimum-purchase excess included in the purchase subtotal | 42.30 |
| **Complete BOM total** | **Unresolved** |

**78 of 79 required procurement lines are priced. F115 is still required and
unpriced.** The specified Reomax 5.250.0750A is a 0.75A ceramic time-delay 5x20mm
fuse. No DigiKey replacement matching that requirement was verified. The
Littelfuse 0239.750TXP has a glass body and only 35A breaking capacity, so it was
excluded. Its price is not silently used to fill the gap. Compare the
[original Reomax specification](https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2303300930_Reomax-BTC0750_C5381743.pdf)
with the [DigiKey listing for the rejected fuse](https://www.digikey.com/en/products/detail/littelfuse-inc/0239-750TXP/3424896).

Prices are estimates from public DigiKey US product pages retrieved on
2026-09-14. The pages are cached, and their crawl ages are recorded per line.
They are not a live checkout quote or reserved inventory. All 78 priced lines
show sufficient stock for their purchase quantities in the recorded snapshots.
Every item includes its supporting product URL. Tax, tariffs, freight, fees,
PCB fabrication, assembly labor, tooling, and other process consumables are
excluded.

The five screw/nut lines have lowest published price tiers of 100 pieces. Their
purchase quantities are 100 each, even though the board uses only 1–9 of each.
The excess is reusable hardware stock. Other lines use the exact required
quantity, without rounding up to obtain price breaks. Cut tape is selected for
SMT parts; no Digi-Reel fee is included. Line amounts are rounded to cents using
decimal arithmetic before totals are summed.

## Design coverage and substitution limits

The source design has 440 purchased electronic units: **345 SMT, 82 soldered
through-hole units, and 13 fuse cartridges**. The BOM also includes 30 original
hardware pieces and one thermal-paste syringe provision. J115 buys two headers,
represented as J115A and J115B. There are 23 DNP or fabricated board features
shown with zero purchase quantity; those are excluded from pricing.

The proposed SCHURTER 0031.8201 holders need **15 separate 0853.0551 covers**,
including covers for the two empty holders. Their pairing is documented in the
[SCHURTER OGN drawing](https://media.digikey.com/pdf/Data%20Sheets/Schurter%20PDFs/DS_486_Fuseholders.pdf).
Fit to the existing Hongju footprint and surrounding parts still needs review.

There are 28 priced candidate/accessory lines and one unresolved requirement.
Candidates include replacement resistors, capacitors, diodes, LEDs, a transistor,
triacs, fuses, fuse holders, the J113 header, and the M4 screw. Their original
parts remain visible alongside the proposed DigiKey parts. The detailed review
requirements are in the BOM's Notes column.

Specific sourcing decisions:

- The original 10uF Samsung capacitor has zero stock in the retrieved product
  snapshot; a Taiyo Yuden 10uF/50V/X7R/1210 candidate is priced.
- The original BTA08-600CRG product page showed two units, despite a conflicting
  search snapshot showing 2002. The quote instead prices five BTA08-800CRG
  candidates. Review all trigger quadrants, pin/tab drawing and thermal ratings.
- F112 uses the proposed Bel Fuse 0680H7000-05, rated 7A and 125VAC/125VDC, with a
  slow-blow response. Time-current and protection coordination remain unverified.
  The initially considered Littelfuse 0454007.MR was rejected because its AC
  rating is 72V.
- D101–D104 use a proposed STPS40150CT 150V Schottky pair. Forward-loss and thermal
  performance must be checked against the original 100V part and its heatsink.
- Existing connector trimming/key-pin preparation and BR3 lead forming remain
  necessary where the original selected part is retained. The different J113
  housing needs its own fit and cable check.

This is a **sourcing proposal**, not a new released PCB variant. The existing
SPICE results qualify the existing modeled design and do not establish that
these proposed substitutions are equivalent. No PCB, Gerber, JLC BOM, or CPL was
changed, and no new DigiKey-specific CPL is implied. Engineering review and any
necessary design changes precede using these candidates for assembly.

Regenerate from the saved sourcing facts with:

```sh
python variants/jlcpcb-100/tools/build_digikey_one_board.py
```

Research inputs are in `variants/jlcpcb-100/research/digikey-1/`.
