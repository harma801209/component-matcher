# FOJAN resistor ordering-code evidence repair

2026-11-10 manufacturer verification: https://www.fosan.vip/ explicitly identifies
FOSAN (FOJAN) 富捷. The local FRC table also spells out the FOJAN company code
under a FOSAN header. Both labels select only these documented resistor
families; this does not authorize borrowing resistor codes for semiconductors.

The screenshot's FRC0402F1001TS previously showed TS as one unknown suffix.
This was an incomplete integration, not a lack of OEM documentation. The local
FRC specification (FJ-JS-3001-V2.0/2025.09.24, page 2) explicitly defines
T = 7 inch reel and S = Sn termination. They are now separate verified segments.

The local resistor folder contains 45 PDFs, including variants and a duplicate
FRL document. Public basenames, hashes, revision and ordering-page references
are stored in catalog_sources/fojan_naming_documents_20261105.json; no personal
folder paths, customer records or entire local files are uploaded.

The read-only guide now consults these documents by model family, not the
input row's possibly incorrect series/description or inventory parameters.
Packaging T/Q/R/B and termination S/C/A are decoded separately where the
specific series table defines them. FRT/FTH/FQT/FTR TCR codes, FRC-X/FRP-X,
FRC-P, FRL-L/FQL-L, alloy size/power/material and FQL's short size/power
layout use their own tables. Alloy M means Metal, not Sn; FCM 0M50 means
0.5 milliohm, not megaohms. Unknown remainders and missing required fields
stay visible and incomplete. Explaining codes does not prove purchasability,
qualification, production status or permitted electrical combinations.

Remaining genuine source limitations are explicit rather than hidden:

- FAR/FQA ordering examples end TS, while the electrode table defines T/A/F,
  not S. Do not borrow the single-chip Sn definition. Array size subsegments
  are not yet fully explained; the guide stays partial.
- FRB's document title and its FRJ product-code diagram disagree. Keep that
  series segment unverified instead of relabelling it silently.
- The FQL wide-electrode table names R as TRL but does not expand it. Preserve
  the unresolved special code. FRZ F appears in the example but is absent in
  the listed tolerance column; do not call its full code verified.
- Legacy families without a matching local source, malformed codes and unknown
  suffixes are not promoted to complete or hidden from the result options.

Because the existing TCR display helper consumes verified naming segments,
this is not treated as a CSS-only release: the public 28-category assets must
be rebuilt and the entire isolated-store release gate rerun after source freeze
2026-11-05T12:36:00+08:00. Keep the original library and runtime stores intact.
No account, authentication, security, session, private-configuration, game,
price or original Excel edits are in scope. Local verification, push and
formal UI acceptance must be reported separately.
