# Issue Ledger

## 2026-05-12 - Zero-ohm resistor shorthand skipped when full fallback is unavailable

- Bug: `0201 1/20W 0R` was parsed as an insufficient capacitor-style spec with only size `0201`, so public fast-index mode could not query the resistor library and displayed the full-library fallback warning.
- Cause: `0R` and `1/20W` were individually parseable, but `looks_like_resistor_context(...)` only promoted compact resistor tokens when the text also included `%`, `OHM`, `Ω`, or explicit resistor wording.
- Fix: Treat compact resistance plus power as resistor context, and treat zero-ohm plus a chip size as resistor context. This keeps the gate narrow enough to avoid promoting MLCC/order-code strings.
- Verification: `0201 1/20W 0R` now routes as `贴片电阻` and returns resistor search-index matches; guard checks for MLCC, varistor, and low-ohm resistor queries still route correctly.

## 2026-05-12 - Timing component specs routed through capacitor-style parsing

- Bug: Timing specs such as `晶振 16MHz 3225` were not parsed as crystal/oscillator specs; they could fall through to capacitor-style value parsing and return `规格不足` or zero matches.
- Bug: Exact timing part searches could return same-frequency alternatives all marked `完全匹配` without reliably promoting the queried model to the first row.
- Fix: Added a dedicated timing spec parser for crystal/oscillator frequency, package size, voltage, output type, and load capacitance. Timing matching now filters those fields directly and sorts exact model hits first.
- Fix: Regression value checks now use the generic component display value for non-capacitor devices, so MHz timing specs are tested correctly instead of relying on capacitor `容值_pf`.
- Verification: `晶振 16MHz 3225` now routes as `晶振` with 4 matches; `振荡器 25MHz 3.3V CMOS` routes as `振荡器` with 3 matches; timing regression cases `TIMING_CRYSTAL_ABRACON_ABM3B`, `TIMING_CRYSTAL_SPEC_16MHZ_3225`, `TIMING_OSC_SITIME_SIT1602`, and `TIMING_OSC_SPEC_25MHZ_3V3_CMOS` pass.

## 2026-05-12 - Film capacitor and varistor seed rows filtered out after lookup

- Bug: Source-backed film capacitor rows could be present in `components.db` and the search core table but still return zero matches because `容值_pf` existed as a blank DB column and `_pf` was not backfilled from `容值/容值单位` during prepared/search-sidecar generation.
- Bug: Varistor models such as `MOV-14D471K` could be parsed by the generic resistor model rule as a 471K resistor, which overwrote the original varistor tolerance and caused candidate filtering to miss valid 470V 14D rows.
- Fix: Backfill `_pf` and `容值_pf` from `容值/容值单位` when the DB column is blank, and block generic resistor model parsing when the current component type is a non-resistor such as a varistor.
- Fix: Try exact compact part lookup before other-passive spec parsing so source-backed official film models like `MKP1848C51060JK2` are not downgraded to `规格不足`.
- Verification: Targeted checks pass for `R82DC3100AA50J`, `MKP1848C51060JK2`, `薄膜电容 0.1uF 63V 5% PET`, and `MOV-14D471K`; new regression cases `FILM_KEMET_R82DC`, `FILM_VISHAY_MKP1848`, `FILM_SPEC_100NF_63V_PET`, and `VAR_MOV14D471K` pass.

## 2026-05-11 - ST power MOSFET model parsed as an incomplete capacitor spec

- Bug: `STP55NF06L` was present in the semiconductor seed/search index, but the query router treated the `55NF` substring as a capacitor value and returned `规格不足` instead of exact part results.
- Fix: Extended semiconductor compact-model blockers for common power-device prefixes including `STP`, `DMN`, `RQ`, `SSM`, `PMV`, `RB`, `CUS`, `DSA`, `SK`, `2SC`, `2STR`, `UMT`, `CDSOD`, and `ESDA` so these models route to semiconductor lookup before passive spec parsing.
- Verification: `STP55NF06L` now routes as `料号` with top result `STMicroelectronics STP55NF06L`; regression case `SEMI_MOS_STP55NF06L` passes.

## 2026-05-11 - MLCC spec routed as aluminum electrolytic on public page

- Bug: Public search for `1206 x7r 1uf k` was parsed as `铝电解电容`, with `1206*7mm` treated as an electrolytic body size, so no MLCC candidates were returned.
- Fix: Added a direct MLCC-first guard in `detect_query_mode_and_spec`: when `looks_like_mlcc_context(...)` is true, parse with `parse_spec_query(...)` before any other-passive/electrolytic parser can run.
- Verification: Public wrapper search now returns `陶瓷贴片电容（MLCC）规格条件` and MLCC results for `1206 x7r 1uf k`; local targeted check returns 201 MLCC matches.

## 2026-05-10 - Source-backed semiconductor seed library and prefix safety

- Bug: After semiconductor mis-match blocking was added, seeded official/source-backed semiconductor rows still needed a real matching path; otherwise the system could only say `暂不支持`.
- Bug: Package aliases such as `SMC` vs `DO-214AB/SMC` caused valid Schottky specs like `肖特基 40V 3A SMC` to miss the sourced `SS34` row.
- Bug: Prefix-like semiconductor inputs such as `SI2302` are common in BOMs, but treating them as exact matches would be unsafe because the full manufacturer suffix changes package/spec/orderability.
- Fix: Added semiconductor type matching for MOSFET/diode/BJT/TVS rows, including voltage/current/package/polarity and MOSFET `Rds(on)` checks. Added source-backed seed rows for 20 common semiconductor models.
- Fix: Normalized `DO-214AB/SMC`, `DO-214AA/SMB`, and `DO-214AC/SMA` package aliases and removed SQL package prefiltering for semiconductors so official package aliases are filtered safely in Python.
- Fix: Added semiconductor prefix lookup that can return sourced candidates for incomplete model prefixes while forcing procurement status `需确认`.
- Verification: Targeted checks passed for `SS34`, `SS34FA`, `BAT54`, `BAV99`, `1N5819`, `S8050`, `BC817`, `BC807`, `MMBT3906`, `SI2302CDS`, `SI2302`, `IRFZ44N`, `肖特基 40V 3A SMC`, and unsupported `SMAJ5.0CA`.

## 2026-05-10 - Unsupported semiconductor safety gate and passive false-safe fixes

- Bug: Unsupported semiconductor part numbers such as `2N7002` and `1N4148` could be misread as MLCC capacitance fragments; MOS specs containing `Rds(on)` / `50mΩ` could be routed into resistor matching.
- Bug: `0402 X5R 1uF 6.3V +/-10%` could be routed as an aluminum electrolytic spec because the electrolytic `uF + size` heuristic ran before the MLCC context check.
- Bug: Inductor specs with current/DCR/body-size and varistor specs with disc size could still show safe-looking recommendations even when candidate rows were missing or conflicting on those parameters.
- Bug: BOM candidate generation could concatenate a model-only column with a name-only column, producing polluted model strings for rows such as `NCU18WF104E60RB` + `NTC热敏电阻`.
- Fix: Added an explicit `暂不支持` gate for MOSFET, diode, TVS diode, and BJT patterns and wired it into search, BOM, and cache lookup paths so unsupported semiconductors cannot fall through to passive matching.
- Fix: Prioritized MLCC context before electrolytic context, added inductor current/DCR/body-size conflict checks, added varistor `14D471K` disc parsing, and stopped model+name concatenation when the BOM spec column is blank.
- Verification: Critical safety checks passed for `AO3400A`, `IRLZ44N`, `2N7002`, `1N4148`, `SS34`, `MMBT3904`, `S8050`, `SMBJ5.0CA`, MOS Rds(on) spec text, MLCC `0402 X5R 1uF 6.3V +/-10%`, inductor `4.7uH 3A 30mΩ 3x3mm`, varistor `14D471K 470V`, and the NTC BOM pollution case.

## 2026-05-10 - Procurement-safe resistor recommendation status

- Bug: Walsin resistor model `WR08W1002FTL` could be parsed by the generic resistor parser as `80mΩ` because the parser saw the `WR08W` series prefix before the real `1002` resistance code.
- Bug: BOM rows used `匹配成功` whenever candidates existed, so partial matches and parameter conflicts looked safe for采购/销售.
- Fix: Added a Walsin-specific chip resistor parser that reads the resistance code after the official series prefix, then derives size, tolerance, and power from the model.
- Fix: Added procurement-facing statuses: `可推荐`, `需确认`, `参数冲突`, `解析失败`, and a one-line recommendation summary above search results.
- Verification: `WR08W1002FTL` now parses as `0805 / 10KΩ / ±1% / 1/8W`; targeted regression `WALSIN_WR08W_10K` passes; classifier returns `参数冲突` for lower-power candidates and `可推荐` for exact resistor matches.

## 2026-04-29 - Kyocera AVX historical MLCC code and unsafe size fallback

- Bug: Kyocera AVX historical MLCC part numbers such as `06035C104K4T2A` were displayed with generic series `车规` instead of the actual automotive code inside the part number.
- Bug: MLCC rows with only a chip-size code could display a full length/width/height triplet from a nominal map and label it `尺寸码推断`, which made the thickness look more authoritative than the data allowed.
- Fix: Decode Kyocera AVX historical part numbers using the official Automotive MLCC ordering structure; display `4` when the failure-rate code after tolerance is `4`, and use Kyocera AVX official dimensions for the covered historical 0603 X7R 104 50V rows.
- Fix: Generic MLCC size-code fallback now fills only nominal length/width and labels the source as `封装码标称L/W`; stale `尺寸码推断` height values are cleared unless an official or model-rule source supplies height.
## 2026-05-10 - Verified MLCC thickness backfill for Walsin/PDC/HRE 0603 X7R 104 50V

- Bug: After removing unsafe generic MLCC height fallback, rows such as `0603B104K500CT` correctly kept nominal L/W from the package code but showed blank height even though the manufacturer/spec-sheet data includes the thickness.
- Fix: Added narrow verified dimension rules for Walsin, PDC/PSA, and HRE 0603 X7R 100nF 50V MLCC rows, including thickness and source labels from the relevant specification data instead of inferring height from `0603` alone.
- Fix: Added a targeted `--backfill-mlcc-dimensions --verified-only` path that updates both `components.db` and `cache/components_prepared_v5.parquet`, including refreshes where an existing verified source needs a more precise tolerance value.
- Verification: `component_matcher.py --backfill-mlcc-dimensions --verified-only` updated 12 database rows and 12 prepared-cache rows after the tolerance correction; direct DB/cache checks now show Walsin, PDC/PSA, and HRE rows with non-blank `高度（mm）` and verified `尺寸来源`.
