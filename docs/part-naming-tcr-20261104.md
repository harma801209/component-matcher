# Complete-part naming entry and YAGEO RT TCR — 2026-11-04

## Scope

- Add the same inline naming popover to complete-part lookup as specification and fragment searches. Both a visible source part with alternatives and source-only results have an entry. The popup consumes only publicly displayable fields from the source and final displayed alternatives; it never reads cost or account fields.
- Keep the title and button content-width, without a fixed spacer. Multiple inputs have independent widgets. Popup selections use the existing fragment mechanism rather than rerunning matching.
- Add original-source Taiyo MEAS and Walsin general-purpose MLCC numbering explanations. Missing packaging/internal codes remain explicitly incomplete; unknown brands remain selectable and visibly unverified. This is not completion of all-brand naming coverage.
- Show resistor TCR in source and result schemas. Preserve retained values; fill missing YAGEO RT TCR only from a complete, brand-scoped ordering code. Never copy a source model's TCR to alternatives or add a TCR matching constraint implicitly.
- Correct the RT value offset: RT0603BRE07130KL contains packing R, TCR E, reel 07 and resistance 130K. The generic RC offset previously consumed 07 as ohms and could return 7.13 Mohm; the RT-specific ordering layout returns 130 kohm.
- No authentication, administrator, session, price, game, original Excel or runtime database changes.

## Manufacturer evidence

- YAGEO RT, 2026-02-12 V17, page 2: A/B/C/D/E = 5/10/15/25/50 ppm/°C. `RT0603BRE07130KL` therefore has ±50 ppm/°C, not 25. [Original PDF](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RT_1-TO-0-01_ROHS_L). Numbering page visually checked; PDF SHA256 `00a9148c2958122200e8a93292e389392a795adcfe40562d6ca4f690d1e5d7d1`. This interprets an ordering code; it does not establish current production or orderability.
- Taiyo `c_mlcc_E_e-E12R01`, pages 1–2: [MEAS original numbering](https://www.yuden.co.jp/en/product/support/pdf_spice_spara/upload/c_mlcc_E_e.pdf). Original PDF SHA256 `67717acd89eaee1eaa9f796ff4a79a5843d644383579a35d708d901c8e171c9b`; both pages visually checked. Historical E category is not silently rewritten after the [2026 category consolidation](https://www.yuden.co.jp/en/news/category/change_to_part_numbers.html).
- Walsin General-purpose MLCC, Oct. 2026, page 2: [Original numbering](https://www.passivecomponent.com/wp-content/uploads/datasheet/WTC_MLCC_General_Purpose.pdf). Original PDF SHA256 `7e544e6bbdb438554f3c5051d4a4d933599095880aa603f1342e0fba6ec7cf59`; numbering page visually checked. This table is not applied to PDC or Walsin MT.

## Verification (before publication)

- Red reproduction: absent TCR raised KeyError; after adding TCR, the same regression exposed the 7.13 Mohm RT offset defect. The test was retained and parser corrected, not its expected value weakened.
- 39 focused naming/TCR tests passed (32.678 s). After adding the full mixed user input, its source lookup/display regression passed (24.921 s).
- Actual local browser: source MEAS popup and matched Walsin complete-code table visible; source-only entry also works; parent-run counter stayed 1 after selecting a different brand. Screenshots in `work/repair-shop-qa/cap-naming-*.jpg`. AppTest's explicit `.run()` performs a full script execution, so the no-parent-rerun claim comes from actual browser verification, not that test harness.
- All 28 ready-resource categories rebuilt successfully; every compressed payload is byte-identical to the published baseline. Only manifest recipe changed to `cdfe76683d9fc0619587a3ded7af9ccce485a4e413fdf3b7d26a07da8d47b168`. Source fingerprints and model counts are unchanged.
- Mandatory full safety gate: **664 tests passed in 1626.374 seconds**, isolated databases and unchanged protected runtime fingerprints. Log: `work/repair-shop-qa/naming-tcr-safety-gate-final.log`. Source remained frozen through ready build and gate.
- Publication uses only the seven intended files, a fast-forward push from baseline `8552ebad`; the unrelated untracked bundle, separate BOM WIP, security and game branches are not included. Publication SHA/endpoint outcome are recorded separately in `work/repair-shop-qa/part-naming-tcr-publication.md`.
- Formal authenticated acceptance is not implied by local checks. Pre-publication formal browser reading timed out twice; no authenticated content acceptance is claimed yet.
