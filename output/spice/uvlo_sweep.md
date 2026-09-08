# +5V raw rail vs mains and load (averaged TPS54360B model, C5 = 10000 uF, GBU8J)

| mains | 9 VAC peak (V) | +5V load (A) | raw minimum (V) | raw average (V) | raw ripple p-p (V) | +5V minimum (V) |
|---|---|---|---|---|---|---|
| 100% | 12.70 | 2 | 9.10 | 9.45 | 0.69 | 5.000 |
| 100% | 12.70 | 3 | 8.34 | 8.86 | 1.03 | 5.000 |
| 90% | 11.43 | 2 | 7.67 | 8.06 | 0.77 | 5.000 |
| 90% | 11.43 | 3 | 6.80 | 7.40 | 1.17 | 5.000 |
| 88% | 11.18 | 2 | 7.38 | 7.78 | 0.79 | 5.000 |
| 88% | 11.18 | 3 | 6.48 | 7.10 | 1.20 | 5.000 |
| 85% | 10.79 | 2 | 6.93 | 7.36 | 0.83 | 5.000 |
| 85% | 10.79 | 3 | 5.98 | 6.64 | 1.26 | 5.000 |

The buck regulates 5.0 V down to Vin = 5.6 V (0.97 Vin - 0.5 = 5.0); the UVLO stop level must sit below the raw-rail minimum of the
worst case that the board has to survive (88 % mains, 3 A) with margin for the EN threshold spread (1.1-1.3 V, i.e. +/- 8 % on the stop level).
