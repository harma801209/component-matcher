# Scheduled non-security work — 2026-11-04

Historical first-run notes: started at the authorized Beijing 03:30 trigger,
base `634630dc`, then working branch `codex/bom-spec-policy-20261103`.
The current integration/02:00 continuation is based on `b9790f73`, on
`codex/six-open-items-20261104` in `search-overlay-perf-release`.
See [the current acceptance ledger](six-open-items-progress-20261104.md) for
post-review resource, complete-gate, publication and live-acceptance results.
This is a bounded reviewed batch, **not completion of all-brand coverage**.

## Explicitly excluded

No authentication, password, administrator, role or session policy changes.
No temporary administrator creation, secret configuration, game changes or
real-goods redemption work. The security branch was not merged. The initial AST
extraction covered only BOM policy and nine read-only search-statistics functions;
the current integration additionally contains the reviewed TCR, naming and exact
lifecycle-display changes recorded in the acceptance ledger. Runtime databases and the user's workbook are not
release inputs.

## BOM policy

Merge MLCC literal descriptions and independent capacity, tolerance, voltage,
dielectric and size columns. Stop on conflicts with both values visible;
never silently choose a translated MPN over customer requirements. Brand-scoped
parsing remains separate. Automotive, soft termination and safety classes are
hard requirements. Fully checked exact manual alternatives rank first, then
Walsin MT. Higher-voltage/tighter-tolerance candidates need confirmation.
Unverified basic ordering identities are not completed by invented suffixes.
BOM result version is 7. Legacy FOJAN/resistor behavior is covered separately.

The previous read-only 138-row workbook reproduction found six real input
conflicts (Excel rows 72,109,114,123,131,132). It did not force those rows to
agree with manual alternatives. Original workbook SHA256:
`81918b5a59e9ed66c765b58b8baae7ba1fa0ad3c1e8d4d9a0e516a6c4300c585`.

## Statistics and process classification

Only the non-security statistics/classification functions were extracted from
`dd9403d6`. Day/week/month/all controls now define the same scope for the chart,
detail and frequency table. Cross-day distinct members are counted in SQL, not
summed daily. Generic chip resistor is not evidence of thick-film process.
Mixed process trends retain the specific processes and explicitly unknown
process rather than taking whichever label happened to arrive first.
Six isolated synthetic-event regressions pass.

## New manufacturer evidence

- Walsin MT: original September-2026 PDF, pages 2–3, downloaded and visually
  reviewed. SHA256 `3b770f76f2410b51c239c3f173ac42b21ab4750f8a663daed736b2c5a4de1fb3`.
  [Original](https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_Automotive_MT.pdf).
  MT03/15/18/21/31/32, dielectric, capacity, tolerance, voltage, C electrode and
  T/G reel codes are explained. Base or unknown suffixes remain incomplete.
  Rules are Walsin-only; overlapping PDC MT does not inherit them.
  For the 2,190 already-listed MT base identities, the exact-series dielectric
  rating table supports X8G −55..150°C, C0G/X7R −55..125°C, X6S −55..105°C.
  Search/detail completion is blank-only; contradictory supplied material or
  temperature fields are retained, not silently overwritten. Price and
  lifecycle are not inferred from this family datasheet.
- YAGEO CC X7R: original March-6-2026 V27 PDF page 2, downloaded and visually
  reviewed. SHA256 `3aa10c5d01fbea28f638f1e4bca56a14b9b3342f593d68641830b1cbdb3720e6`.
  [Original](https://yageogroup.com/content/datasheet/asset/file/UPY-GPHC_X7R_6_3V-TO-250V).
  Explain only the published size, tolerance, packing, X7R, 6.3–250V and
  capacitance fields. The table prints BB but does not define each B; BB remains
  visibly unverified. Other CC dielectrics do not inherit this table.

## Lifecycle attempt and remaining evidence gaps

The bounded Panasonic ERJ12NF exact-page batch could not fetch valid receipts:
repeated TLS-verified HTTP reads timed out. A separate ordinary HTTPS retry
also timed out. TDK exact-product pages were discoverable, but subsequent
retrievals could not produce stable reviewable model/status receipts. No
status was imported from snippets, historical catalogues, stock, series or
absence. Existing 9,501 lifecycle evidence identities are unchanged; this run
does not claim new lifecycle coverage.

All-brand/all-series naming, exact-model current lifecycle coverage, and the
remaining Walsin/AMOTECH parameter and ordering-identity gaps remain open.
Unpublished or inaccessible definitions need the actual original code table
or exact-model manufacturer confirmation, not a guessed meaning. Nothing is
hidden from matching output to make coverage look complete.

## Release validation

Before the current batch: 17 focused BOM/FOJAN/safety regressions passed.
This run's source/statistics/naming tests: 52 passed before the final narrow
MT index-temperature assertion was added. The mandatory full gate must pass
after resource generation; focused tests are not a substitute.

Previous monolithic builds exhausted Windows commit. The build now runs one
category per fresh subprocess, never concurrent workers. The same mandatory
test inventory runs in bounded serial subprocesses, including all system
regressions and all existing account/game regression tests without modifying
those product features. Failed validation still blocks commit/publication.
Final build, full-gate and formal acceptance results are recorded separately.
