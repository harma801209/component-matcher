# FOJAN high-power specification matching

## Confirmed failure

`1.2Ω ±1% 500mW,1206` parsed correctly: 1.2 ohms, 1%, 0.5 W,
1206. However, the catalogue candidate builder returned no special-series rows.
Adding `高功率` to the identical requirements returned `FRP1206F1R20TS`.
The bug was a keyword-only activation gate, not a milli/watt conversion error
or evidence that FOJAN cannot manufacture this specification.

## Manufacturer evidence

[FOJAN FRP manufacturer specification, FJ-JS-3001-V1.0 / 2025.01.01,
hosted by LCSC](https://atta.szlcsc.com/upload/public/pdf/source/20251201/9FAB26F784B289B46BE5060BCFE21636.pdf):

- Page 2: FRP ordering fields, `F` = ±1%, four-character resistance code,
  `T` reel and `S` termination.
- Page 4: 1206 is 1/2 W at 70°C; 1% resistance range is 1Ω–10MΩ.
- Page 5: derating above 70°C; the nominal rating is not an unconditional
  operating guarantee at every ambient temperature.

`FRP1206F1R20TS` is the order-code candidate derived from these manufacturer
rules. This is not a claim of physical stock, a confirmed quotation or a
manufacturer-confirmed lifecycle status for this exact part number.

## Fix and boundaries

With no explicit specialty requested, an explicit power above ordinary FRC's
rating activates the existing general FRP/FCP profiles. Each candidate must still
pass the existing exact power, package, resistance range, tolerance, brand and
subtype checks. Do not silently add automotive/anti-surge/low-TCR variants,
lower the requested wattage, mutate the query or mark an FRC quarter-watt part
as a half-watt complete match. Explicit special-use filtering is unchanged.

Both text search and BOM matching use the same candidate builder. Release stamps
invalidate old query caches. No library rebuild, pricing rule change, protected
runtime database migration or game changes are needed for this fix.

## Regression coverage

Tests cover the original query, underscore/decimal-watt notation, FRP0805 and
FCP1206 ratings, exact-match fields, brand/subtype and special-use constraints,
unsupported power/tolerance/range, ordinary or absent power, and BOM output.
