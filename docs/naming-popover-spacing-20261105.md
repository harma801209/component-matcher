# Scoped naming-popover spacing edit — 2026-11-05

Request: remove the redundant explanatory line in the supplied screenshot and
move the naming-popover content upward. Keep interpretation, warnings, controls,
matching, price visibility and all other page/popover layouts unchanged.

## Exact changes

- Remove only the introductory sentence about result brands and clicking outside.
- Put the marker on the actual title, not an invisible inline span before it;
  this avoids an empty Markdown paragraph ahead of the heading.
- Scope12px top padding,18px sides,16px bottom and12px block gaps to the naming
  popover only. Title margin0 and slightly tighter code-chip margins.
- Keep incomplete/verified-segment counts, unknown-code labels, evidence and the
  final non-procurement disclaimer. Preserve fragment/widget keys and routing.
- Source marker2026-11-05T11:20:10+08:00; base307b8b4b7a17ed41349c445cf59c2c4f0d80e08b.

## Actual local-browser verification

Dedicated local fixture on127.0.0.1:8581 uses the real render helpers and production
theme, public resistor/capacitor examples only, with isolated runtime-store paths.
Same selected IAB browser2 via its documented tabs/Playwright API, not a native or
external browser workaround. The fresh local tab rendered successfully.

- FRC0402F1001TS intro absent; heading visible with measured top inset12.667px.
  Computed body padding12px18px16px; screenshot visually inspected.
- Partial4/5 status, TS pending verification, explanation table and evidence remain.
- Switching FOJAN/FRC to Walsin/WR updates the example toWR04X1001FTL and its code
  table; parent execution counter remains1, no parent matching re-execution.
- Capacitor/Murata GRM popover uses the same compact header and preserves pending
  thickness/tail definitions. No unrelated production tab was reloaded or edited.

This is an existing-component edit, not a screenshot-clone/prototype redesign.

## Public data-equivalence proof and mandatory gate

The conservative catalogue recipe includes root UI code. To preserve ready filters
without unnecessary data regeneration, a separate strict equivalence audit proves:
only STYLE and the one exact static heading HTML literal differ semantically in
model_naming_guide.py; every other AST node is identical to the accepted base.
All other root rule/evidence inputs match base, ignoring only release markers.
All28 public compressed assets match their base advertised hashes; catalogue
schema/counts/source fingerprints/asset entries are unchanged. No facts, identities,
pricing, qualifications or normalization rules are altered or inferred.

Audit: repair-shop-qa/naming-popover-ui-data-equivalence.py/.json.
Canonical data AST SHA92f33b95fb94dea00bcbfdf45825fe6275813f37a45905e26f967331055d90a7.
Readiness recipe updated only after that proof to
f1987e9a2e7de7f52c857d772bc28083ffca9774f78ec9432692217a5fbbdc9f;
the audit must also pass with--require-current. This is not a substitute for the
complete isolated-store safety gate, which is still required before commit/push.
No database, original Excel, account/security/session/private-config or game edit.

## Final local release verification

44 focused naming tests PASS/40.594s. Complete mandatory gate691 PASS in nine
serial groups93/50/50/50/50/17/180/153/48,1916.232s summed test time. The gate
explicitly confirms isolated stores and unchanged protected runtime-data
fingerprints. The equivalence/focused/full-gate chain exits0. No assertions or
required groups were skipped. Final source stayed frozen throughout.

Actual local browser verification above is separate from formal deployment.
Read-only formal baseline now works via the same IAB documented tabs API, but
the test browser is an independent guest session, not evidence the owner logged
out. No credentials, account creation or production login-state changes.
Post-publication checks are recorded outside the repository in
repair-shop-qa/naming-popover-spacing-publication-20261105.md.
