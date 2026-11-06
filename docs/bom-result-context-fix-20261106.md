# BOM result-table context unpack repair — 2026-11-06

## Confirmed root cause

The cost-bearing result table calls `bom_result_view_authorization_scope(True)`.
`selected_sales_cost_customer_context()` returns three fields (type, name,
normalized key), but that caller unpacked only two. The regression reproduces
`ValueError: too many values to unpack (expected 2, got 3)` for both general
and named-customer contexts. This is a result-rendering failure, not a failed
manufacturer/specification match.

## Scope

Consume the third field with an ignored variable, exactly like other existing
callers. Preserve the existing customer authorization, identity/price scope,
cutoff and callback checks. No account/role/session policy, matching/quoting
rules, worker concurrency, source workbook or runtime data change.

Tests cover the actual three-field selector, cost-bearing comparison-panel
rendering, scope revalidation after member identity changes, preservation of
source/result frames, and logged-out/unpriced/no-cost views.

All other matcher AST nodes (except the display release stamp) are unchanged
from 60927029. All 28 catalogue assets and reviewed source files must remain
binary-identical; the manifest recipe is refreshed for this UI-only source fix.

33 focused checks passed after the original two customer cases reproduced the
failure before the fix. The old scope-only test fixture also incorrectly returned
two values; it now follows the real three-value contract. A fresh complete 718-test
release gate passed (117/50/50/50/50/19/181/153/48). Protected runtime-data
fingerprints across three worktrees are unchanged; all 28 catalogue payloads
remain binary-identical. Formal acceptance is recorded separately; local checks
alone are not deployment acceptance.
