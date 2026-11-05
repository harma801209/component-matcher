# BOM query/overlay reuse performance repair

Release stamp:2026-11-05 20:30 Asia/Shanghai. Base93048393.

## Confirmed regression

The previous start/progress repair acknowledged real starts and prevented a UI
rerun from draining queued rows, but did not eliminate per-row public-overlay
preparation or identical candidate fetches. User screenshots still showed0/138
after31 seconds and8/138 after90 seconds. The shared card subtitle includes
query work; these screenshots do not isolate Excel parsing time.

## Change boundary

- Cache successful public candidate-pair lists only within one source row,
  keyed by the complete specification including brand/special-purpose fields.
  Return independent lists; retry transient None/failure results normally.
- Keep public-index connections and TEMP manufacturer overlays within one
  worker lane in one BOM task, not one new connection scope per source row.
  Close on the owner worker thread after normal completion, error or interruption.
- Preserve bounded dispatch, actual-count heartbeats, checkpoint/source ordering,
  explicit start/resume, no scroll-triggered replay and row-local frame isolation.
  Partial lane/thread startup failures also enter cancellation/shutdown cleanup;
  their simulated low-resource regression must pass before publication.
- Default public execution to one CPU-bound lane. Same-host24-case control
  shows4 lanes use more CPU and take longer than1. Explicit worker settings and
  non-public behavior remain available. Do not bypass platform CPU throttling.
- For at least64 pending unique, explicitly identified MLCC requests, snapshot
  the exact final public capacitor SQL view into a TEMP indexed table once on
  its owner lane. Preserve every source row, column and duplicate. Defer this
  work until after a real first result; skip it for small/duplicate-only/resumed
  remainders and resistor jobs. No manufacturer overlay module changes.
- No shared member/customer/price/report/job connections, account/session
  changes, catalogue facts or matching-rule changes. SQL candidate/filter body
  moved intact to an uncached helper. Full model/spec qualification checks remain.

## Evidence and release requirements

24 different MLCC requests, four-worker93048393 baseline vs new public policy:
41.663s /119.922 CPU seconds to21.576s /20.484 CPU seconds. First completion
10.925s to5.312s. Overlay installs25 to1; actual candidate retrieval46 to24;
144 parse calls remain144. All output fields equal across24 rows. These are
local samples, not the currently active formal138-row upload or a speed promise.

The previously captured138-row workbook also reproduces the regression:
93048393 default8 workers315.034s /1559.281 CPU seconds,133 overlay installs,
360 candidate fetches. Query/lane reuse alone151.935s; the final deferred public
snapshot trial97.988s /96.609 CPU seconds,1 overlay install and132 candidate
fetches. All138 output rows/fields equal (including the existing six conflict
stops). The final frozen-source replay and complete gate are required again.
The20:15 frozen replay measured94.766s, first completion5.064s and93.219 CPU
seconds with the same exact output hash; a review-discovered thread-start cleanup
edge was then patched and the full chain restarted for the20:30 final candidate.
The20:30 frozen-source replay completed in84.033s (82.984 CPU seconds), first
completion5.007s; all138 output fields retain the same exact hash. This is one
same-host run, not a guarantee for the currently active formal upload.
An intermediate eager-snapshot trial worsened first-result latency; it was not
published. The first partial gate was stopped intentionally before this final
execution change and is not release approval.

Final validation:56 focused checks PASS80.770s; a new complete716-case safety
gate PASS in9 groups (117/50/50/50/50/17/181/153/48). All protected runtime
database/sidefile fingerprints across3 worktrees unchanged; all28 public payloads
unchanged. Receipt:bom-query-release-20261105.json. Publication and the user's
currently active formal upload acceptance are separate follow-up checks.

Execution-only equivalence proof traverses377 offline helpers, verifies the
unchanged candidate SQL/body and non-BOM delegation, unchanged public index/
parquet hashes and all28 binary-identical ready payloads. Recipe-only rebinding
is permitted by this proof; the mandatory full release gate is still required.

QA receipts are kept outside the repository under work/repair-shop-qa:
bom-query-output-equality-24-20261105.json, bom-query-equivalence-20261105.json,
and the forthcoming full gate/138-row comparison receipts. Do not describe a
gate or formal runtime check as passed until its actual receipt exists.

## Rollback and remaining operational limit

Revert only this execution repair to93048393 if verified output differs. Preserve
production runtime databases, user files and unrelated FOJAN work. A deployment
runtime restart may interrupt an active match and requires coordination. Cloud
CPU throttling was observed until2026-11-05 20:52:46; do not attempt to evade it.
