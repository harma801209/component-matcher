# Ordinary search latency repair — 2026-11-04

Base 634630dc, isolated branch `codex/search-overlay-perf-20261104`.
The separate BOM/statistics/naming WIP is preserved, not included in this
performance release. No auth, role, session, administrator, game, price or
runtime-store changes.

## Reproduction and repair

FN18X104K500PBG parses promptly as PDC FN /0603/X7R/100nF/10%/50V.
The added Walsin overlay wrapped every manufacturer's specification columns
behind CASE/COALESCE and LEFT JOINs, preventing the original compound
specification index from serving the caller's predicates. Its identity-only
core view also unnecessarily joined completion tables. Several connections
per query repeated the setup.

The repaired view partitions the unchanged non-Walsin rows from the Walsin
completion branch. NULL brands/types remain on the unchanged branch. Existing
upstream overlays and all actual manufacturer additions remain. Core retains
its original rows without completion joins. Walsin blank completion, exact
old-value corrections, alias/base deduplication and read-only evidence are
unchanged. No brand is hidden and no matching requirement is relaxed.

The new regression failed before the fix: EXPLAIN QUERY PLAN scanned the base
capacitor table. After repair it uses the fixture's compound specification
index, and exact core-model lookup uses its model index without completion
LEFT JOINs. The test also covers NULL records, prior overlay rows and X7S
completion. Existing Walsin tests pass.

## Timing and identity acceptance

QA scripts and full brand/model sets are outside the release tree in
`work/repair-shop-qa/search-perf-ab.py`, `search-perf-ab.json`, and logs.
They import reviewed public search/detail inputs, use temporary member, cost,
report and BOM stores, disable maintenance/remote sync, and never edit the
user's workbook or production database. Diagnostic numeric-library thread
limits affect only those subprocesses, not application or OS settings.

First repair comparison (before the final redundant core-join removal):

| Query | Released seconds | Repaired seconds | Unique brand/model pairs |
|---|---:|---:|---:|
| FN18X104K500PBG first | 24.429 | 9.918 | 98 |
| FN18X104K500PBG warm | 18.477 | 6.422 | 98 |
| 0805 X7S 10uF 25V 10% | 16.044 | 1.719 | 21 |
| 0603 X7R 100nF 50V 10% | 20.452 | 2.081 | 98 |
| 0402 C0G 22pF 50V 5% | 21.065 | 1.765 | 54 |

Every complete brand/model set matched the released result, not just its count.
These are local comparative measurements, not the public browser's elapsed
time. Final timing, asset build, safety gate, publication and formal acceptance
are recorded below only after their respective checks complete.

## Final checks and release

Final repair (including identity-only core simplification): FN first 6.301s,
warm 3.962s; X7S 1.938s, X7R 3.340s, C0G 2.897s. All five exact brand/model
sets equal the released baseline. JSON reload initially compared lists to
tuples in the QA harness; normalizing those containers fixed that test-only
comparison. No application result was changed to pass it.

All 28 ready categories rebuilt successfully. The two published source
fingerprints are unchanged; only the MLCC gzip payload and manifest recipe
changed (127,683 MLCC identities retained). Recipe:
`0bf36d40bc84fdf9d3f9ebcaac82559630b5a51f52ad624db392b5e2a71f70e7`.

Mandatory full safety gate: **659 tests passed in 1204.455s**, isolated stores,
protected production-data fingerprints unchanged. Log:
`work/repair-shop-qa/perf-safety-gate.log`.

Publication uses a whitelisted Git commit/fast-forward push, not the broad sync
script (which would unnecessarily rebuild bundle/runtime inputs). No proxy,
deployment configuration or public bundle source changes. The unrelated
untracked `streamlit_cloud_bundle.zip` is deliberately not staged. Stamps
trigger the normal Streamlit checkout update. Public endpoint checks and
authenticated browser acceptance are tracked separately; local timing is not
proof of the formal worker's response time.
