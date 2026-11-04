# Six open items — acceptance ledger

User requested completion of all six items, not just a reminder or local patch.
Administrator/security/password/session policy and game redemption remain excluded.
Starting main revision: `b9790f73378ea52cc60884f02ebc144e6f5beab4`.
Working branch: `codex/six-open-items-20261104` in `search-overlay-perf-release`.
The separate dirty `bom-spec-policy-20261103` worktree and its unrelated bundle
must remain intact. Never merge the security branch wholesale.

| Item | Required acceptance | Current status |
| --- | --- | --- |
| Formal fixes | Live source/result TCR columns;130K no false conflict; direct MLCC naming; search timing | Final02:28 code passes local actual-path replay: both tables have TCR, source50ppm,27 alternatives (16 verified/11 unknown), no130K false conflict. Last owner-confirmed formal version was16:25 on Nov4; IAB read still times out, so current live worker/authenticated acceptance is not established. |
| BOM policy | Merge literals/independent columns, conflicts visible, brand isolation, qualification hard limits, checked manual/MT preference, upgrade separation; original Excel untouched | Integrated and complete683-case release gate passed. All138 source rows enter merged parsing,16 examples replayed through actual matching and six real conflicts stop. Non-MLCC families remain on their own paths. Unverified manual tails are not force-adopted. |
| Statistics/classification | Consistent day/week/month/all chart/detail/frequency scope and distinct members; generic chip does not imply thick film | Non-security functions integrated; seven scope/process regressions and the full gate pass. Actual cross-day SQL counts distinct members rather than summing daily counts. Process-only metal film does not imply SMT. |
| Naming coverage | Every returned brand/series/code accurately explained from original evidence | Reviewed Walsin MT, YAGEO CC X7R and MFR additions integrated; original Taiyo/general-Walsin handlers retained. Global coverage remains incomplete:517158 complete/54213 partial/1139098 unexplained in the supplied snapshot, not a census of all live output. |
| Exact-model lifecycle | Current exact product status, canonical source, retrieval date and verifiable receipt; unknown stays unknown | Existing9501 reviewed identities retained; final renderer requires exact identity/source/date and prevents duplicate-index evidence crossover. No new lifecycle data imported. Fresh Taiyo exact receipt saved separately for validated follow-up, not applied to base or other suffix identities. |
| Parameter/model gaps | Applicable electrical fields and explicitly listed identities from original data; no Cartesian generation or invented tails | Blank-only temperature limits added for2190 already-listed Walsin MT identities;127683 MLCC identities unchanged. Walsin/AMOTECH and other-family applicable-field/source/identity gaps remain open; no invented ordering codes. |

Any final statement must distinguish local checks, main push, public entry health
and authenticated live acceptance. Neither HTTP200 nor a Git push proves the
live worker runs the new revision. A passing release gate is mandatory; a focused
test or a stale manifest is not sufficient. All automated runs use isolated
member/cost/report/BOM paths and preserve protected runtime fingerprints.

## Integration procedure

`work/repair-shop-qa/prepare-six-item-integration.py` is read-only: it compares
common-base AST functions with reviewed pending and latest-main functions,
emitting apply_patch plans only. Concurrent modifications are reported instead
of overwritten. In particular preserve the published indexed Walsin branch and
RT/TCR/naming fixes. Remaining conflicts require individual review.

No temporary production administrator was created. No deployment/auth secrets
were read or edited. No original workbook or runtime database is a release input.

## Bounded audit results (not an all-six completion claim)

- Naming audit streamed every row of the supplied 1,710,469-record public
  Parquet snapshot after MFR follow-up: 517,158 complete, 54,213 partial and
  1,139,098 unexplained.
  This is not a census of every live overlay identity. Raw labels are not true
  manufacturer/series counts. Unknown brands remain visible.
- Lifecycle audit of the existing search-index identity set: 1,748,627 raw
  brand/model identities, 9,501 exact identities with reviewed evidence,
  1,739,126 still pending. No new lifecycle evidence was imported. The ordinary
  upper/lower result renderer now uses only exact source/date evidence and
  labels legacy Active or sales notes without such evidence as unverified.
- Ready MLCC asset has 127,683 unchanged identities. Against published b979,
  only _temp_low and _temp_high changed, for exactly 2,190 already-listed Walsin
  MT identities. Other values and model identities are unchanged.
- Current ready snapshots contain 25,923 Walsin MLCC identities, including
  2,201 MT-prefixed identities, of which 2,190 have these verified temperature
  limits. 15,373 Walsin MLCC rows still lack temperature limits; unknown or
  unlisted identities do not inherit MT's table.
- AMOTECH's 424 MLCC/broadband/high-Q identities have populated size, material,
  capacitance, tolerance and voltage filter fields. Three old broadband exact
  identities lack rated operating-temperature limits. Their source specifies
  a TCC test interval, which is not silently promoted to an operating rating.
  Non-MLCC AMOTECH families were not falsely audited against pF/MLCC fields.
  Field presence alone does not establish provenance or complete correctness.
- The original 138-row workbook was read only; SHA256 remains
  81918b5a59e9ed66c765b58b8baae7ba1fa0ad3c1e8d4d9a0e516a6c4300c585.

Audit JSON and diagnostic source scripts reside in the separate repair-shop-qa
directory, not in production runtime stores. The ready build completed all 28
categories serially without memory exhaustion. Rebuild and full gate after the
missing-import correction remain mandatory before any commit or publication.

## Follow-up after owner reply

Owner has no internal OEM manuals and authorized continued public-primary-source
research, not guessed definitions or a lowered full-coverage standard. Added
YAGEO MFR V4 original page2 seven-segment guide, with power/type restrictions,
explicit E/F TCR only, and historical F-form phase-out notice kept separate from
exact-model lifecycle. Original PDF SHA256:
b460acdb476469774e0785a8ef85aec79e2d95fe41beaa79c5a414e4e95e3fe0.
Source: https://yageogroup.com/content/datasheet/asset/file/YAGEO-MFR_DATASHEET
Pages2 and16 were rendered and visually checked. All42 naming tests passed.

The second complete gate passed its first193 cases, then exposed a standalone
raw-MLCC fixture without a derived capacitance cache column. Preparation now
initializes that cache as missing and derives pF solely from the supplied literal
value and unit. The hard-qualification regression explicitly removes cached
columns and checks47000pF; it and two BOM-policy regressions pass. No omitted
electrical value is guessed. Third resource run was superseded before completion,
not accepted as a pass. Review also found that a process-only metal-film label
(such as axial MFR) must not automatically acquire a chip-mounting assertion in
trend summaries. Mixed process aggregation uses the resistor parent and preserves
explicitly generic chip/unknown-process labels. Seven statistics regressions pass,
including this mounting boundary. Only verified own builder28688 and its current
child were stopped; no user applications were closed. Final code freeze22:54;
fourth full resource/gate run is mandatory and pending.

## Once-only 02:00 continuation — 2026-11-05

Resumed after the authorized time, preserving both dirty worktrees. The old
once-only automation was deleted after accepting this run; no repeat was added.
The first resumed complete gate passed all683 cases in nine serial groups,
with isolated stores and unchanged protected fingerprints. The actual helper
diagnostic then passed:138 rows enter merged parsing; six conflicts remain
blocked; original Excel hash unchanged; both final RT tables contain TCR,
original50ppm and27 alternatives (16 verified,11 unknown);130K produces no false
warning, while220K still conflicts. Local FN18 resolve+match took9.633s then
2.095s; these are local helper measurements, not live-browser latency.

Final review added a duplicate-source-index lifecycle regression. It reproduced
a real evidence crossover: label-based assignment could give an unverified
identity the next row's reviewed status. Corrected only this presentation helper
to assign by row position, preserving both indexes and the input frame. The
regression checks both row orders, exact status/source isolation and immutability.
Code freeze is now2026-11-05T02:28:00+08:00. Therefore the previous683-case pass
and previous ready recipe are superseded for release: rebuild all28 serially,
rerun the complete gate and actual-path diagnostic before committing/pushing.

Public-source research continued while the serial build ran. A fresh original
Taiyo MEASJ063BB5225MF1A01 HTML receipt (2026-11-05T02:31:32+08:00) explicitly
lists status "Mass Production (Previous Category)" for that complete identity;
SHA2564ebdbf6a36ef52d82dad77109e9776fda339407574df1557cfe186ca4ffb598f.
[Exact original](https://ds.yuden.co.jp/TYCOMPAS/ut/detail?pn=MEASJ063BB5225MF1A01&u=M).
Saved in repair-shop-qa/taiyo-primary-followup-20261105.json with receipt details,
not imported into this frozen release or applied to the basic MEAS identity.
Its per-model Part Number document endpoint returned404. The current
[general-purpose guide](https://www.yuden.co.jp/en/product/support/pdf_spice_spara/upload/c_mlcc_S_e.pdf)
(c_mlcc_S_e-E14R01, SHA2567c61d70f59ff3013c0097690a70631b4498f3eb3119054a8bfd470cf0c3d7d0d)
was downloaded and pages1/3 visually checked. It applies to MSAS/MSAR/MSAY/MSRL,
not MEAS. Section10 labels an internal code without per-character definitions;
neither this nor stock data resolves the missing MEAS internal suffix meanings.

Rechecked the original AMOTECH ABCUB10201X104KNDG Rev02 PDF directly, not a
distributor's inferred fields; SHA256371ced97249b0c9b9456c615be1b3168bc04f7aca3ba656338d215677c5a2a25.
[Original](https://www.amotech.co.kr/pdf/bro/ABCUB10201X104KNDG_Datasheet.pdf).
Pages2/3 were rendered and visually checked. Material code2 is explicitly an
internal code; its dielectric identity is not published there. The−55..125°C
interval labels the capacitance-TCC test, not an operating-temperature rating.
This recheck therefore does not justify filling either missing field or claiming
current exact-model production status from a2020 datasheet.

The allowed IAB formal-page binding still timed out after45seconds during this
continuation. No alternate native stack, authentication injection or temporary
administrator was used. Authenticated formal acceptance remains blocked.

The post-review rebuild completed all28 categories serially without exhausting
memory. Final recipe is
bc681edc7e9cd93c5c5eb43da84e4b1ceee1135087519d4c32b93a0c21e2a543.
All28 assets pass current manifest/input verification. MLCC gzip remains
48009c712561635e3ca2673f93e6eeb8ace1ee3049e7c7fc2eac9aa2fbbde0a1,
identical to the previously reviewed2190-field-only completion. The new complete
gate and final helper replay run sequentially after that build; no parallel
large-memory tests or skipped mandatory modules.

## Final local release gate — 2026-11-05

The post-review complete gate passed683 tests in nine mandatory serial groups
(93/50/50/50/50/17/172/153/48),1272.176s summed unittest time. It explicitly
confirmed isolated member/cost/report/BOM stores and unchanged protected runtime
fingerprints. The complete build/gate/replay command exited0. Evidence is in
repair-shop-qa/six-ready-build-resume-v2.log and six-safety-gate-resume-v2.log.

Final actual-path replay uses code stamp2026-11-05T02:28:00+08:00 and passes:
all138 inputs use merged parsing;16 real row examples were evaluated; six real
conflict rows72/109/114/123/131/132 stop without selecting a model. Original Excel
SHA remains81918b5a59e9ed66c765b58b8baae7ba1fa0ad3c1e8d4d9a0e516a6c4300c585.
Both final RT HTML tables have the explicit TCR header immediately after power,
source50ppm and27 alternatives (16 independently verified,11 pending). Same130K
has no warning; a genuine220K description still warns against model130K.
FN18 local resolve+match measurements are9.375s then2.144s,95 matches each.
These do not establish live-browser latency or prove an instant cold search.

This makes the bounded batch eligible for scoped publication; the actual main
push and anonymous endpoint check are recorded in the separate publication
receipt. It does not close authenticated formal acceptance or global naming,
lifecycle and parameter coverage. Remaining unexplained records include both
not-yet-implemented published rules and genuinely unpublished/internal codes;
it would be incorrect to blame every remaining gap on unavailable OEM manuals.
Security/admin/password/session and game features are unchanged.
