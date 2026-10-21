# Official lifecycle audit — coverage and rules

This is **not a completed all-brand audit**. The read-only inventory on
2026-10-20 contains 1,748,627 distinct nonempty brand/model pairs and 345 raw brand
labels with models (346 including the empty-model-only label; aliases are not
yet all consolidated). No unknown model is inferred to be in
production from datasheet availability, search presence, product family, or a
default `Active`/`量产` value in the old library.

## Exact-product page adapter

Samsung MLCC: the official product page's **生产状况** table row is paired with
the exact product heading and explicitly listed packaging codes. Packaging
suffixes are never generated. The resulting evidence is intersected with actual
library identities. Each result records the official URL, raw/normalized status,
UTC retrieval time, source HTML SHA-256 and parser revision.

The original 30 successfully parsed pages verified **51 existing library models**:
42 Mass Production and 9 Pre Mass Production, out of 7,048 Samsung MLCC models.
These are distinct states; pre-mass-production is not mass production. The rest
are pending, not silently assigned a lifecycle state. Other manufacturer
adapters, and the all-brand audit, remain unfinished.

The catalogue shows `原厂生产状态` where this official overlay is installed.
Verified status links open the official source; the tooltip records the check
time. Models with no exact-model evidence read `未核实`. Overlays are TEMP-only,
identity-preserving LEFT JOINs: public index, member and price stores are not
rewritten. The audit does not change the price/replacement matching rules.

## Resume

Run `tools/collect_manufacturer_lifecycle.py --limit 30 --output
manufacturer_lifecycle_evidence.json` from the repository root. The collector
respects official robots policy, verifies TLS, fetches one page at a time, waits
at least one second, bounds document size and records attempted pages in
`manufacturer_lifecycle_evidence.audit.json`. Use `--retry` only for deliberate
rechecks. A blocked/failed/unrecognized page stays unconfirmed, never “stopped”
or “active.” Review counts and statuses, update the release stamp, pass the
safety gate and publish reviewed evidence; live end-user searches never crawl.

Next adapters must follow each official site's rules, associate a status with an
exact ordering code (not a legend or broad family), preserve planned EOL/last-buy
dates separately, and prove status mapping with tests before backfill. CAPTCHA,
authentication and manufacturer confirmation requirements are not bypassed.

Primary example: [Samsung CL10B104KB8NNN#](https://product.samsungsem.com/cn/mlcc/CL10B104KB8NNN.do).

## Reviewed expansion — 2026-10-20

**9,473 existing identities** are now verified: 8,064 chip resistors, 92 power
inductors and 1,317 MLCCs, all Samsung. MLCC states are 1,182 Mass Production
and 135 Pre Mass Production. All matched resistor/inductor states are Mass
Production. The remaining **1,739,154 identities are pending**, not automatically
in production or discontinued. `manufacturer_lifecycle_coverage.json` lists
every raw brand label, including zero-coverage brands.

The chip-resistor search returns exact ordering codes; import intersects these
with existing library identities. A similar prefix is not proof. The official
power-inductor grid explicitly appends `#` to its product group: only that
existing `#` identity is accepted, not generated packaging variants. Endpoints
and payloads were observed in the official basic-search pages, not guessed.
Receipts retain requests, response hashes and retrieval-completion timestamps;
imports reject changed responses/mismatched receipts. Status links open the
official search page because the evidence endpoint is POST, not a clickable GET.

Initial export receipts use preserved responses' original completion mtimes,
explicitly marked in each receipt. Future collector runs record direct times.

In the actual completed catalogue chain, Samsung thick-film resistors have
8,066 identities: 8,064 verified and 2 unconfirmed. Four remaining power gaps
were filled from explicit OEM values: RC1005J000CS/RCS1005J000CS = 1/16 W;
RC0603J000CS/RCS0603J000CS = 1/20 W. Resistance, rated power, package and tolerance
are now nonempty for this brand/category. Known values and zero resistance win.
No 0 V defaults, size-derived power or condition-free current limits are imported.
Power-inductor body dimensions retain the explicit maximum-thickness qualifier.

All specification-browsing kinds now mask unverified legacy `Active` defaults
as `未核实`, including categories with no matching evidence. This TEMP display
projection does not change matching inputs, stored records, prices, training,
or the separate ordinary-search legacy displays.

Other brands remain unfinished. TDK's official PDF and Murata's public simulator
returned access-denied responses in this retrieval environment; no challenge,
login, robots restriction or certificate check was bypassed and neither was
backfilled. Reading a status legend or finding a datasheet is not model evidence.

For public exports, run `tools/collect_samsung_catalogue.py --category cr
--output-dir <private-folder>` (also `--category pi`), then
`tools/import_samsung_catalogue_evidence.py --folder <private-folder> --output
manufacturer_lifecycle_evidence.json`. Run one collector per host. Robots rates,
TLS verification and bounded responses remain enforced; 401/403/429 stops a run.
MLCC collection reuses a normal HTTPS session without raising its request rate.
Cancelled batches resume from their recorded checkpoints.

After import run `tools/audit_manufacturer_coverage.py --output
docs/manufacturer_lifecycle_coverage.json`, update both release stamps, pass the
safety gate and verify the formal page. Exact public sources:
[chip resistors](https://product.samsungsem.com/cn/cr/basic-search.do),
[power inductors](https://product.samsungsem.com/cn/pi/basic-search.do).

## Cold filter entry repair — 2026-10-21

Formal verification exposed a pre-existing cold-entry gap: category browsing
opened the search index without first preparing it. On a fresh public worker,
ordinary text search prepared the published query asset, but opening filters
first showed the generic unavailable warning. Running an ordinary search then
opening filters reproduced the distinction without any runtime-store changes.

The categories loader now prepares only `SEARCH_DB_PATH` when missing, through
the existing scoped public-bundle restoration routine, before opening it. It
does not rebuild the component library, fetch the full prepared asset, restore
member/cost stores, or need a preceding user search. Isolated cold/warm/failed-
restoration tests verify call order, path scope, connection closing and failure
without creating an empty SQLite file. The source index itself remains unchanged.

The exact-source release gate passes 370 tests (499.729 seconds), using isolated
test stores with unchanged protected-runtime fingerprints. Formal browser
acceptance follows publication; that gate alone is not a claim of UI acceptance.
