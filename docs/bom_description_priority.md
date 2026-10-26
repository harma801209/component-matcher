# BOM descriptions and separately translated FOJAN models

When a BOM specification/description contains independently parseable parameters
and its FOJAN manufacturer part number is in another mapped/auxiliary cell, the
description is the requirement. The separate MPN is a proposed translation for
validation, not a model-only authority.

- Parse and match the written description first. Keep the original cells.
- A separate MPN may be reused only after independent model/spec comparison and
  the ordinary specification matcher both accept it. Its model-only shortcut
  cannot bypass package, value, tolerance, power, voltage or special-use checks.
- Differences are retained in the final UI/export remarks and require human
  confirmation. Pricing is for the resulting description-based candidate, not
  silently for the conflicting translated MPN.
- A failed or unsupported description must not be replaced during export by an
  unpriced original-MPN slot or model-only price. No-match stays no-match.
- If a compatible MPN supplies context for an incomplete description, the model
  details are supplemental reference; written fields remain unchanged and the
  result requires confirmation.
- Direct part-number searches, model-only BOM rows without independent
  parameters, and an explicit model inside the specification retain the
  existing identity-based behavior and mismatch warnings. This release does
  not claim a universal all-brand MPN policy or infer who authored each cell.

BOM output version 6 invalidates old persisted job results. Query version 142
also separates old query caches. No account, price-list or catalogue data is
modified; validation uses isolated runtime stores.
