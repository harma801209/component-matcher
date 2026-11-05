# BOM start/progress interruption repair — 2026-11-05

## Evidence and scope

The user confirmed pressing Start for the 138-row upload while the page still
showed file-read/0%/waiting-for-click. A live cloud warning independently reported
CPU throttling until 2026-11-05 14:33:03 Asia/Shanghai. Runtime logs showed long
periods of `bom-match` workers; these logs do not identify the user's exact job.

Synthetic execution of the actual row coordinator reproduced three defects:

1. Exact-model and authorized-cost preparation preceded any progress callback.
2. A blocked row produced no progress callbacks until completion.
3. A UI-style BaseException after the first result still executed all 20 queued
   unique rows because executor context shutdown waited for the entire queue.

This establishes reproducible defects, not proof that every live wait shares
one cause. Cloud resource limits remain a separate operational constraint.

## Repair

- Acknowledge Start before preview/task persistence/index preparation.
- Emit explicit preparation stages before exact lookup and authorized pricing.
- Keep at most the worker limit in flight. Refill only after main-thread result,
  checkpoint and progress handling succeeds; never submit the full workbook.
- Emit one-second heartbeats while waiting for slow rows; count only completed
  rows, with actual elapsed time, never invent a completion percentage.
- On interruption cancel pending work without waiting for the workbook to drain.
  Already running Python calls cannot be forcibly killed; at most the active
  worker count may finish. No worker owns UI updates or checkpoints.
- A same-scope interrupted attempt is shown as interrupted rather than falsely
  asking for the first click. It does not create an automatic start intent.
- Preserve explicit start nonces, strict completed-result recovery, authorization,
  cost snapshots, source order, dedupe, checkpoints and export behavior.
- Refresh only the stateless BOM coordinator on a runtime-cache miss, and include
  its file identity in that cache key. A hot worker may have imported the previous
  module before deployment; without this its new bounded helper is unavailable.
  Authentication and session modules are not reloaded or changed.

No authentication/session/security policy, game, raw workbook, protected runtime
store, bundle, proxy, requirements or runtime configuration changes.

## Actual row performance follow-up

User reported the live task progressing slowly from2 to21/138. Actual public MLCC
row profiling found5 index-opening calls preparing the same overlays repeatedly.
The330nF case took10.706s, with8.537s in opening/preparation. A3-case baseline
using published e072 code took21.746s; optimized12.541s. Every result field in
all3 rows was equal, including statuses, chosen models and warning explanations.
These are local evidence-backed microbenchmarks, not live138-row timings.

Public-index connections now have one worker-local, row-local lifetime. Nested
read helpers may call close, but the row owner releases the real handle in its
finally block. Main index access is enforced read-only; member/cost/report/job
connections never use this pool. Different rows/threads do not share a handle.
Cold public catalogue preparation is serialized once before parallel dispatch,
avoiding simultaneous lru_cache misses. Ordinary non-BOM close behavior remains
unchanged. Progress labels distinguish last-completed rows from pending work.

The first full gate was intentionally stopped after148 passing tests to diagnose
this real latency. It is not a full release pass. Final full validation must run
from the beginning after this change.

The28 ready categories were already fully rebuilt during this repair, with all
compressed payloads identical to published e072. After the row-only optimization,
a fail-closed AST/dependency certificate independently checked377 offline-build
functions: neither BOM execution nor its connection scope is reachable from the
unchanged offline builder. All data/rule functions and ordinary connection SQL
setup are unchanged; only3 application functions changed. The public-index and
detail inputs retain their reviewed SHA256 values, and all28 compressed payloads
were rehashed against published e072. Only the conservative recipe binding was
updated after this certificate passed. This avoids rebuilding identical data a
second time; it does not replace or reduce the mandatory full safety gate.

## Verification / release

The three new behavior regressions failed before the patch. All 17 run-control
tests passed afterwards, including preserved source order/deduplication/resume.
Full-gate, data-equivalence and live acceptance results are recorded separately;
local tests must not be called live 138-row acceptance.

Final source15:12 completed27 focused checks and the entire702-test mandatory
gate. Groups104/50/50/50/50/17/180/153/48 all passed. Protected fingerprints for
all3 worktrees and reviewed public inputs remained unchanged. All28 ready
payloads retained their published hashes. Publication and authenticated formal
138-row acceptance are separate stages, not implied by these local results.
