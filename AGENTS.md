# Repository Safety Rules

The member system and backend runtime records are production-critical.

## Mandatory safeguards

- Never delete, reset, replace, or seed over `member_auth.sqlite`, `cost_price_lists.sqlite`, or `no_match_reports.sqlite` during development, testing, migration, or deployment.
- All automated tests must use temporary database paths through `MEMBER_AUTH_DB_PATH`, `COST_PRICE_DB_PATH`, and `NO_MATCH_REPORT_DB_PATH`.
- Member, cost-list, and no-match schema changes must be additive and backward-compatible unless an explicit migration with verified backup and rollback is approved.
- Never publish an empty or stale local runtime database as the remote source of truth.
- Run `python tools/run_release_safety_gate.py` before every application or deployment change. A failed gate blocks commit and deployment.
- Verify member login, admin member listing, active cost-list history, and runtime snapshot restoration after changes that touch authentication, storage, backend, deployment, or startup behavior.
- Do not stage unrelated working-tree changes or local database files.

## Release condition

A functional fix is incomplete until the safety gate passes and protected runtime-data fingerprints remain unchanged.

## Default release behavior

- Unless the user explicitly requests a test version first, completed fixes must be published to the formal public page after verification.
- A local or test-page fix alone is not complete under the default workflow; run the safety gate, publish only the intended files, and verify the formal endpoint.
- Work explicitly requested as a test version must remain local until the user approves formal publication.
