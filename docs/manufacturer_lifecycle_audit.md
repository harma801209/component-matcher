# Official lifecycle audit — coverage and rules

This is **not a completed all-brand audit**. The read-only inventory on
2026-10-20 contains 1,748,627 distinct brand/model pairs and 346 raw brand labels
(aliases are not yet all consolidated). No unknown model is inferred to be in
production from datasheet availability, search presence, product family, or a
default `Active`/`量产` value in the old library.

## Completed first adapter

Samsung MLCC: the official product page's **生产状况** table row is paired with
the exact product heading and explicitly listed packaging codes. Packaging
suffixes are never generated. The resulting evidence is intersected with actual
library identities. Each result records the official URL, raw/normalized status,
UTC retrieval time, source HTML SHA-256 and parser revision.

The first 30 successfully parsed pages verified **51 existing library models**:
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
