# Issue Ledger

## 2026-07-14 - Resistor matches did not prioritize FOJAN

- Bug: Resistor results ranked PDC, Walsin, and UNI-ROYAL ahead of FOJAN. An exact FOJAN query such as `FRC0603F1402TS` also removed the source FOJAN row from the lower match table, so changing brand rank alone would not fix the reported screen.
- Root cause: The resistor brand order assigned FOJAN rank 4, and the shared same-brand exclusion removed every source-brand row before result sorting.
- Fix: Make FOJAN the unique first resistor brand, followed by PDC, Walsin, and UNI-ROYAL. Preserve the exact FOJAN source row for FOJAN resistor queries, while other source brands remain excluded and explicit brand filters remain strict.
- Verification: Both `FRC0603F1402TS` and `0603 14K 1% 1/10W` now return `FOJAN(富捷) / FRC0603F1402TS / 完全匹配` as the first result. Focused regressions cover brand ranks, FOJAN exact-model retention, non-FOJAN source exclusion, and explicit brand filtering.

## 2026-07-09 - FOJAN alloy resistor specs lacked FRM/FPM source-backed candidates

- Bug: Alloy resistor specs such as `合金电阻 电阻10毫欧 ±1% 1206` and `贴片合金电阻 0.06R 2512 3W ±1%` did not return FOJAN alloy models. Some alloy specs could also be polluted by the older FOJAN FRL low-ohm thick-film fallback.
- Root cause: The FOJAN rule fallback only generated FRC/FRL price-series resistor models. FRM/FPM alloy ordering rules were not parsed or generated, and the FRC/FRL fallback was not gated away from explicit `合金电阻` specs.
- Fix: Added FRM/FPM alloy model parsing and source-scoped spec fallback; limited FRC/FRL fallback to non-alloy resistor specs; added FOJAN FRM/FPM manufacturer packaging MOQ rules.
- Verification: `python -m unittest tests.test_system_regression.SystemRegressionTests.test_13_manufacturer_packaging_moq_is_source_backed tests.test_system_regression.SystemRegressionTests.test_14_fojan_alloy_resistor_rules_are_source_scoped` and `python -m unittest tests.test_system_regression` passed.
- Remaining scope: FOJAN alloy generation is intentionally limited to source-backed ranges now available in code. Wider FRM/FPM coverage needs a complete official ordering table before adding more generated values.

## 2026-06-23 - Invalid resistor package code still returned partial matches

- Bug: A resistor spec with a mistyped package such as `0420 10K 1%` could still show partial-match resistor results from other package sizes.
- Root cause: `0420` was not a recognized size token, so the parser treated the query as if no size was provided and matched only on resistance/tolerance.
- Fix: Detect standalone leading-zero numeric tokens that look like mistyped passive package codes but are not supported size tokens, mark the spec as blocked, and route it through the existing safety warning path instead of matching.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed. `贴片电阻 0420 10K 1%` and `SMD;RES;10K;±1%;0420` now resolve to `mode=暂不支持` with zero candidates and a `尺寸输入错误` reason, while valid `0402` and `0603` resistor specs still parse normally.

## 2026-06-22 - FOJAN series correction missed final HTML rendering

- Bug: After the first FOJAN series display fix, the page could still show `FRC0402J` for `FRC0402J223 TS` in the rendered match table.
- Root cause: The library row and display dataframe were normalized, but the final clickable HTML table path could still receive stale/generated series text from an already-built result dataframe.
- Fix: Applied the FOJAN official-series normalizer again inside `render_clickable_result_table()` after official-status handling and immediately before visible columns are rendered.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed. A synthetic final-table row with `系列=FRC0402J` renders as `FRC / 普通厚膜贴片电阻`, and rendered HTML for actual `FRC0402J223 TS` contains `FRC` without an `FRC0402J` series cell.

## 2026-06-22 - FOJAN resistor display included size/tolerance in series

- Bug: FOJAN resistor results could display series values such as `FRC0201P`, where `0201` is the size and `P` is the tolerance code; the visible series should be only `FRC`.
- Root cause: Some display/result-table paths could preserve stale or generated FOJAN series text instead of forcing the official series profile derived from the model.
- Fix: Added a display-time FOJAN resistor series normalizer that rewrites FOJAN resistor rows from the official model profile before pricing/display column selection and again before final display formatting.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed. A synthetic row with `系列=FRC0201P` and model `FRC0201P000TS` is normalized to `FRC / 普通厚膜贴片电阻`; the real `FRC0201P000TS` library row and selected display columns also show `FRC`.

## 2026-06-22 - No-match admin resolution did not feed future searches

- Bug: The no-match report admin page only stored a note and closed the report. There was no place to enter the corrected brand/model, so the same reported input could still fail on the next search.
- Root cause: `no_match_reports` stored only report metadata and `resolved_note`; `resolve_search_query_dataframe_and_spec()` never checked resolved reports before normal parsing/search.
- Fix: Added schema migration fields for `resolved_brand`, `resolved_model`, `resolved_component_type`, and `library_status`; changed the admin form to require a corrected model before closing; and added a search-first resolver that maps the original reported query or the entered model back to the stored resolution. If the entered model is already in the library it uses that row; otherwise it creates a synthetic backend-supplied row from the captured spec.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed. A temp SQLite flow submitted `SMD;RES;10K;±1%;0201;1;16W`, resolved it to `富捷 / FRC0603J103 TS`, and subsequent searches for both the original input and `FRC0603J103TS` returned through `no_match_admin_resolution:library_model`. The synthetic fallback builds a searchable row for an unknown test model.

## 2026-06-22 - FRC 1% zero-ohm rows missed the shared 5% price

- Bug: FOJAN FRC 1% zero-ohm resistor rows showed blank cost because the pricing table has no 1% price in the 0R rows.
- Root cause: `lookup_resistor_series_pricing()` selected only the tolerance-specific price column. For FRC, zero-ohm 1% pricing is a business exception: it should use the same price as the 5% zero-ohm row for the same size and power.
- Fix: Added a narrow fallback for `FRC + 1% + 0Ω` to read the matching rule's `Price5Percent` when `Price1Percent` is blank.
- Verification: Direct checks return `FRC0201/0402/0603/1206 0Ω ±1%` prices from the 5% 0R rows; `FRC0603 10Ω ±1%` still uses the 1% column; FRL pricing is unchanged. Display checks for `0603 0R 1%`, `0402 0R 1%`, and `1206 0R 1%` show FRC cost/MOQ populated.

## 2026-05-29 - Slash-separated MLCC spec treated capacitance as tolerance

- Bug: Query `0603/NPO/12pF/5%/100V` showed `容值误差=12pF` and returned zero matches even though the database contains matching 0603 COG/NPO 12pF 5% 100V MLCC rows.
- Root cause: In `parse_spec_query()`, tolerance parsing ran before capacitance parsing. Because bare `12PF` can be a valid pF tolerance token in other contexts, the parser consumed the capacitance token as tolerance before it had a chance to set `容值_pf`.
- Fix: Parse explicit capacitance tokens before tolerance tokens inside the spec-token loop, while still allowing bare pF tolerance tokens after capacitance is already known.
- Verification: Direct search now parses `0603/NPO/12pF/5%/100V` as `0603 / COG(NPO) / 12pF / +/-5% / 100V` and returns fully matched Murata 0603 COG/NPO 12pF 5% 100V candidates.

## 2026-05-28 - Prefix-C EIA-size MLCC was misparsed as TDK C series

- Bug: Query `C1812X473K102TFF` was displayed as `TDK / C / 1812 / 1nF`, and replacement candidates were 1nF rows.
- Root cause: `parse_tdk_c_series()` accepted any `C*` string of sufficient length and returned a partial parse even when the material, voltage, and tolerance slices were invalid. For this EIA-size-first MLCC pattern, `473` is the capacitance code and `102` is the voltage code, but the loose TDK parser treated `102` as capacitance.
- Fix: Added a dedicated prefix-C EIA-size-first MLCC parser for `C + 1812 + X + 473 + K + 102...`, and made the TDK C-series parser return `None` unless its size/capacitance/tolerance/voltage slices validate. The TDK parser still supports two-letter legacy temperature codes such as `CH/JB`.
- Verification: Direct search now parses `C1812X473K102TFF` as `1812 / X7R / 47nF / +/-10% / 1000V` and returns fully matched `PDC FP43X473K102...` / `PDC FV43X473K102...` candidates instead of 1nF rows.

## 2026-05-19 - Chinese ceramic-resistor wording routed to MLCC

- Bug: Inputs such as `陶瓷电阻 ±1% SMD 0603 4.7KΩ` were routed as MLCC because the broad MLCC alias token `陶瓷` matched before resistor parsing. The parser only kept `0603 + ±1%`, missed the `4.7KΩ` resistance, and returned no resistor candidates.
- Fix: Added a low-level MLCC blocker for explicit resistor wording / ohm units so `陶瓷电阻` and similar Chinese BOM text cannot be stolen by the MLCC route.
- Verification: `陶瓷电阻 ±1% SMD 0603 4.7KΩ` now routes as `贴片电阻`, parses `0603 / 4.7KΩ / ±1%`, and returns 114 fast-index matches. Regression case `RES_CN_CERAMIC_RES_0603_4K7` passes.

## 2026-05-13 - Series table rebuild leaked transient helper columns into SQLite

- Bug: `python component_matcher.py --backfill-series` failed with `sqlite3.OperationalError: table components has no column named _mlcc_series_class`.
- Cause: The rebuild path streamed chunks through `fill_missing_series_from_model(...)`; later chunks could carry transient helper columns that are not part of the persisted `components` schema, so `to_sql(..., append)` eventually tried to write a column the destination table never had.
- Fix: Capture the persisted `components` column order from `PRAGMA table_info("components")` before rebuilding and reindex every filled chunk back to that schema before writing.
- Verification: The rebuilt code compiles, and subsequent in-place series backfill runs completed successfully without reproducing the schema-drift failure.

## 2026-05-13 - Valid resistor series codes ending in `T` were normalized incorrectly

- Bug: Official resistor series such as Vishay `MCT` could not recover their official description even when the series profile already existed; they fell back to placeholder text like `威世Vishay 0603 薄膜电阻系列`.
- Cause: `normalize_series_code(...)` stripped a trailing `T` when the shortened code was *not* known, which turned valid codes such as `MCT` into invalid `MC`.
- Fix: Only strip a trailing `T` when the shortened code *is* a registered official series code.
- Verification: `MCT06030C1000FP500` now resolves to `MCT / 精密薄膜电阻器`, `TNPW080510K0BEEA` still resolves correctly, and the passive-series unresolved count dropped after backfill.

## 2026-05-12 - Exact passive part rows downgraded or overwritten during fallback parsing

- Bug: Exact passive models that already existed in the DB could be downgraded to `spec insufficient` / `unrecognized`, or could return the wrong family/value after generic model parsing. Observed examples included `PMR18EZPFU10L0`, `RTT021002FTH`, `CSS2H-2512R-L500F`, `CM0805D900R-10`, `0805USB-901MLC`, and `0402CS-2N2XJLU`.
- Cause: The router required capacitor-oriented core-param counts before accepting some exact part hits; incompatible parsed-model families could overwrite a stored DB family; parsed resistor model values could replace a better summary-derived resistance; and the reverse lookup subset omitted inductor/common-mode detail fields needed for exact-part specs.
- Fix: Preserve exact DB hits as `料号`, gate parsed-rule merging by component-family compatibility, avoid overwriting an existing resistance unless conflicts are intentionally allowed, prioritize summary/explicit resistance extraction before model-text heuristics, and include reverse-lookup fields for resistor/inductor detail values.
- Fix: The search-sidecar lightweight fallback now reconstructs `共模阻抗`, `电感值`, and `阻抗@100MHz` from sidecar value tables in no-DB public mode.
- Verification: All `25` newly added exact passive seed models route as `料号`; targeted checks return corrected values for `PMR18EZPFU10L0=10mΩ`, `RTT021002FTH=10kΩ`, `CM0805D900R-10=90Ω common-mode`, `0805USB-901MLC=290Ω`, `0402CS-2N2XJLU=2.2nH`, and `HI0805R800R-10=80Ω@100MHz`. Simulated no-DB public mode returns the same family-specific core values for representative samples.

## 2026-05-12 - Semiconductor display reused generic capacitor-style detail fields

- Bug: Semiconductor rows such as `SS34`, `AO3400A`, and `MMBT3904` stored their key values in compatibility fields like `耐压（V）` and `DCR`, but the visible detail text collapsed to generic output such as `耐压: 40V`.
- Cause: The component-specific display schema handled some table headers, but `build_component_detail_lines(...)` had no semiconductor branch, so MOSFET/diode/BJT/TVS detail strings fell through to the generic passive fallback.
- Fix: Split semiconductor display schemas by device type (`MOSFET`, `二极管`, `TVS二极管`, `三极管`) and added semiconductor-specific detail labels such as `Vds`, `Id`, `Rds(on)`, `VRRM`, `IF(AV)`, `VRWM`, `Vceo`, and `Ic`.
- Verification: Targeted checks now show semiconductor spec/detail output with device-specific labels instead of capacitor-style generic labels.

## 2026-05-12 - KNSCHA DHF aluminum electrolytic exact model was unrecognized

- Bug: `DHF025M687G160S1AA` is an aluminum electrolytic capacitor, but the search router returned `无法识别` because the exact model was absent from the source-backed seed/search index and no KNSCHA DHF fallback model rule existed.
- Cause: Existing aluminum electrolytic model rules covered Jianghai and a few seeded brands; `DHF...` was neither in `components.db` nor in the public search sidecar.
- Fix: Added a source-backed KNSCHA/科尼盛 DHF seed row for `680uF / ±20% / 25V / DIP / D8xL16mm / P=3.5mm / 105℃ / 5000h`, added a narrow exact fallback parser, and refreshed the public search sidecar/bundle parts.
- Verification: Local DB and no-DB public-mode simulations both route `DHF025M687G160S1AA` as `料号 / 铝电解电容` with `680UF`, `25V`, `8*16mm`, and `P=3.5`; regression case `ALU_KNSCHA_DHF025M687` passes.

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

## 2026-05-26 - Numeric size-first MLCC part skipped public fast search

- Bug: Brandless compact MLCC numbers such as `1812B103K102LT` were treated as MLCC context, but `parse_spec_query()` extracted only size `1812` and returned `规格不足`. In public/cloud mode this then fell through to the unavailable full-dataframe fallback and displayed `当前环境未加载整库回退数据`.
- Fix: Added a numeric size-first MLCC parser and wired it into `parse_model_rule()` / `reverse_spec_partial()`. The parser decodes size, dielectric, capacitance, tolerance, and numeric voltage codes, including Walsin-style `102 -> 1000V`.
- Verification: `1812B103K102LT` now parses as `MLCC / 1812 / X7R / 10NF / ±10% / 1000V`, uses the fast query path, and returns PDC `FV43X103K102...` matches instead of requiring full-dataframe fallback.
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

## 2026-05-13 - Resistor result rows must show real manufacturer series

- Bug: FOJAN resistor rows such as `FRC0402F10R0TS` were displayed with size-fragment pseudo-series like `FRC0402F` instead of the manufacturer family `FRC`; the same regression class still affected Walsin `SR04X...` rows, which surfaced as `SR04X` rather than `SR`.
- Fix: Added FOJAN official resistor family mappings for `FRC/FRP/FRL/FRS/FRH/FRV/FRQ/FRR/FRG/FRD/FRM/FPM/FPL/FPS/FQP`, then added a Walsin `SR` official series profile and canonical resolver path.
- Fix: Reused filtered cache synchronization instead of another full global cache rebuild: `5,490` FOJAN prepared rows and `72` Walsin `SR` prepared rows were refreshed from the updated database.
- Verification: `0402 10R 1%` now returns `FOJAN(富捷) FRC0402F10R0TS -> FRC / 普通厚膜贴片电阻`; `FRQ0402F1000TS` now returns `华新科Walsin SR04X1000FTL -> SR` with the anti-sulfuration automotive series description. The passive-series unresolved total fell from `223,059` to `217,497`.

## 2026-05-13 - Expansion audit must measure series semantics, not only brand presence

- Bug: The expansion audit could report `gaps=0` once a brand/type pair existed in the database, even if that brand still lacked usable manufacturer-series semantics for most rows. That let “brand is present” look like “the library is actually ready.”
- Fix: Upgraded `audit_library_expansion.py` to track `semantic_ready_rows`, `semantic_gap_rows`, and `semantic_status` (`ready / partial_series / series_gap / brand_gap`) for every target pair.
- Fix: Added seed-ingest admission checks so `sync_passive_gap_seed.py` refuses rows missing `品牌 / 型号 / 系列 / 系列说明 / 官网链接 / 数据来源`.
- Verification: The audit now reports `173` brand-covered target pairs but still exposes `66` target pairs with incomplete series semantics, which matches the actual remaining rule debt instead of hiding it behind a zero-gap brand count.

## 2026-05-13 - Series semantics standard applies to the whole component library

- Bug: The working process still referenced passive-specific gap reporting, which understated the user's actual requirement: all component classes, including inductors, timing parts, MOSFETs, diodes, BJTs, and TVS devices, must be modeled by real manufacturer-series rules.
- Fix: Added `tools/build_series_semantics_gap_report.py` to scan the entire database, not only passive parts, and report semantic-ready vs semantic-gap rows by component type and brand/type pair.
- Fix: Updated the publish/expansion runbook to explicitly apply the series-rule admission standard to `电容 / 电阻 / 电感 / 磁珠 / 共模 / 压敏 / 热敏 / 晶振 / 振荡器 / MOSFET / 二极管 / 三极管 / TVS`.
- Verification: The new whole-library report covers `1,458,793` component rows, finds `220,119` series-semantics gap rows, and writes both markdown and JSON artifacts for follow-on cleanup prioritization.

## 2026-05-27 - Samsung CL MLCC dielectric code mapping

- Bug: Brandless Samsung MLCC query `CL10Y225KO96PJC` was generated from the parser instead of a DB row, and the parser decoded Samsung `CL..Y...` as `X7T`. Samsung official product page for `CL10Y225KO96PJ#` lists the part as `X7S`, 2.2uF, +/-10%, 16V, 0603.
- Root cause: `parse_samsung_cl()` and `parse_samsung_cl_partial()` used an incorrect Samsung CL temperature-characteristic map: `Y -> X7T` and `Z -> X7R`. Official Samsung samples confirm `X -> X6S`, `Y -> X7S`, and `Z -> X7T`.
- Fix: Corrected both Samsung CL parser maps in `component_matcher.py`, bumped query cache/public code stamps, and added regression case `MLCC_SAMSUNG_CL10Y225KO96PJC`.
- Verification: Direct parser checks now return `CL10Y225KO96PJC -> X7S / 2.2uF / +/-10% / 16V`, `CL10Z106MP96PNC -> X7T`, `CL10X225KL8NRW -> X6S`, and `CL10B104KB8NNNC -> X7R`.

## 2026-05-27 - PDC FMF current-sense resistor misclassified as MLCC

- Bug: Query `FMF25FPJR001XBHM` displayed as `信昌PDC / 陶瓷贴片电容（MLCC） / FM / 中压`, with blank size/value fields and no useful replacement table.
- Root cause: The generic PDC MLCC parsers accepted any `FM*`, `FP*`, `FV*`, etc. prefix and returned immediately even when the following characters did not match the capacitor size-code structure. `FMF...` is actually PDC's `FMF` metal-strip current-sense resistor family, so it was intercepted before resistor parsing.
- Fix: Added a PDC `FMF` metal-strip current-sense resistor parser and made PDC MLCC `FN/FS/FM/FP/FV/FK/FH` parsers require a real two-digit MLCC size code after the series prefix. Updated full and partial parse paths so a failed PDC MLCC attempt falls through to resistor parsing instead of returning `None` early.
- Verification: Direct search now parses `FMF25FPJR001XBHM` as `合金电阻 / FMF / 2512 / 1mΩ / ±1% / 2W` and returns 5 fully matched current-sense resistor candidates.

## 2026-05-28 - Resistor display schema moved series description too far right

- Bug: The FMF display fix made resistor tables inconsistent with MLCC and other component tables by moving `系列说明` after size/value/tolerance/power. Alloy-resistor rows also exposed verbose generated descriptions that repeated brand and pseudo-series.
- Root cause: The resistor display schema was changed globally to prioritize electrical fields, while display-time series cleanup only filled blank descriptions and did not rewrite stale generated resistor descriptions.
- Fix: Restored resistor schema order to `系列 -> 系列说明 -> 参数`, added a compact alloy-resistor schema, refreshed resistor series profiles during display cleanup, and shortened resistor fallback descriptions to avoid repeating brand/model fragments.
- Verification: Direct display checks show `FMF25FPJR001XBHM` as `FMF / 金属条电流检测电阻（AEC-Q200） / 2512 / 1mΩ / ±1% / 2W`; `FRM252WFR001TML` is normalized to `FRM / 高功率合金采样电阻`; generic alloy fallbacks display `合金电阻系列`.

## 2026-05-27 - RALEC LR current-sense resistor skipped public fast search

- Bug: Query `LR2512-22R001F4` returned `有结果 0` and the public fallback warning even though it is a valid RALEC current-sense resistor.
- Root cause: The exact model was absent from `components.db`, and the resistor parser did not understand RALEC `LR/LRE` metal-alloy low-resistance naming. The generic resistor extraction also risked interpreting `22R001` as `22.001Ω` instead of using the RALEC segment structure where `22` is terminal/power and `R001` is resistance.
- Fix: Added a RALEC `LR/LRE` parser that decodes size, terminal/power code, low-ohm value, tolerance, and packaging; added official series profiles; inserted `LR2512-22R001F4`; normalized existing RALEC `LR/LRE` rows; fixed `mΩ` normalization so it is not converted to `MΩ`; bumped cache/public stamps; refreshed selected prepared-cache and search-sidecar rows; rebuilt the public bundle parts.
- Verification: Direct search now parses `LR2512-22R001F4` as `合金电阻 / LR / 2512 / 1mΩ / +/-1% / 2W` and returns 5 fully matched candidates including `旺诠RALEC LR2512-22R001F4`.

## 2026-05-28 - HRE CGA size-first MLCC routed as insufficient spec

- Bug: Query `CGA0805X7R225K500MT` returned zero results and the warning `请最少输入三个规格参数`.
- Root cause: The query looked like MLCC context, so the spec parser ran first and extracted only `0805` plus `X7R`. The full model parser was not reached, even though the model contains package, dielectric, capacitance, tolerance, and voltage codes.
- Fix: Try compact part-number parsing before returning MLCC `规格不足`; classify brandless HRE-style `CGA/CAA/CAI/CIA/CSA/CSS/CSO` size-first MLCC models as `芯声微HRE`; allow failed TDK `C*` partial parsing to fall through to generic model parsing.
- Verification: Direct search now parses `CGA0805X7R225K500MT` as `芯声微HRE / CGA / 0805 / X7R / 2.2uF / +/-10% / 50V`, routes as `料号`, and returns same-spec MLCC candidates.

## 2026-05-28 - Capacitor height hidden because official body-size text was not split

- Bug: Many non-MLCC capacitor rows looked like they had no height/thickness even when official catalog-derived body size text existed, for example Rubycon `5X11` aluminum electrolytic rows.
- Root cause: The database/cache stored body-size strings in `尺寸（mm）` or `_body_size`, but normalization did not split them into `直径（mm）/长度（mm）/宽度（mm）/高度（mm）`. The fast search sidecar capacitor table also did not carry these display fields, so even corrected rows could lose height in search results.
- Fix: Added non-MLCC capacitor dimension splitting, cleaned polluted scalar dimension fields, refreshed capacitor rows in the prepared cache, and extended the capacitor sidecar schema to include explicit dimension and source columns.
- Verification: Direct search for `6.3ZLJ220M5X11` now displays `直径 5` and `高度 11`; direct search for `PCP1CPA330M15V` displays `长度 7.3 / 宽度 4.3 / 高度 1.9`; the capacitor sidecar schema now includes `高度（mm）`.

## 2026-06-03 - Hyphenated HoLRS milliohm resistor query skipped public search

- Bug: Query `HoLRS6568-5W-0.1mR-1%` returned zero results plus the public fallback warning `当前环境未加载整库回退数据；本条输入已跳过`.
- Root cause: The exact HoLRS6568 row is not currently in the database, and the generic resistor context regex did not allow `-` after an `mR` milliohm token, so `0.1mR-1%` was not treated as a usable resistor value before the public app tried the unavailable full-dataframe fallback.
- Fix: Added `-` to resistor token boundaries and classified explicit `HOLRS/LRS` or true milliohm low-ohm notation as `合金电阻` during spec parsing.
- Verification: Direct parsing maps `HoLRS6568-5W-0.1mR-1%` to `合金电阻 / 0.1mΩ / ±1% / 5W`; the fast search path returns 2 same-resistance candidates instead of triggering full-dataframe fallback; regression case `RES_SPEC_HOLRS_HYPHEN_MR_POWER` passes.

## 2026-06-05 - HoLRS6568 exact row must route as part, not only resistor spec

- Bug: After the parser fix, `HoLRS6568-5W-0.1mR-1%` could be parsed as a resistor spec, but it still did not show as a formal original part because the exact row was absent and `%` caused the compact-part detector to skip exact lookup.
- Root cause: Some official resistor model numbers encode tolerance as a literal percentage suffix. Treating `%` as a universal spec separator blocked exact lookup for official models such as `...-1%`.
- Fix: Added a source-backed Milliohm HoLRS6568 sync script, inserted 15 HoLRS6568 family rows, refreshed prepared/search caches, and allowed `%` in no-space compact part queries while still blocking slash/space specification inputs.
- Verification: Direct query now routes as `料号`, returns `Milliohm(毫欧) HoLRS6568-5W-0.1mR-1%` as `完全匹配`, and regression case `RES_SPEC_HOLRS_HYPHEN_MR_POWER` passes with size `6568`, value `0.1mΩ`, tolerance `±1%`.
## 2026-06-13 - Resistor `mR` and `MR` unit case collision

- Bug: `0402 1mΩ` / `1mR` searches could surface `105`-coded 1MΩ chip resistors such as `0402WGJ0105TCE`, `CQ02WGJ0105TCE`, and `FRC0402J105TS`.
- Root cause: Explicit resistance parsing used case-insensitive `mR`, so `MR`/`Mr` was treated as milliohm. The prepared parquet and SQLite sidecar had already cached many `MΩ` text rows as sub-ohm values.
- Fix: Made `mR/mr` milliohm and `MR/Mr` megaohm in the parser, made the low-ohm branch use a case-sensitive milliohm pattern, bumped the query cache version/stamp, corrected 46,272 cached `MΩ` resistor rows in prepared parquet and search sidecar, and rebuilt the Streamlit cloud bundle parts.
- Verification: `0402 1mΩ 5% 1/16W` and `0402 1mR 5% 1/16W` return no `105` models; `0402 1MR 5% 1/16W` and `0402 1MΩ 5% 1/16W` return 1MΩ candidates; `1206 0.01R 5% 1/4W` still returns only 10mΩ rows.

## 2026-06-15 - Resistor DB value fields still held stale sub-ohm values

- Bug: Exact part `FRC0402J106TS` displayed `10mΩ` even though its summary and resistor code indicate `10MΩ`; semicolon spec `1M;5%;0402;0402WGJ0105TCE;厚声` could miss the known `105`-coded 1MΩ row because `components.db` still stored `0.001Ω` / `0.01Ω` in structured value fields.
- Root cause: The earlier `mR`/`MR` repair corrected prepared/search caches but not the underlying DB rows. Exact-part display and later cache refreshes can rehydrate from `components.db`, so stale sub-ohm source fields came back.
- Fix: Added `sync_resistor_values_from_summary.py` to compare resistor `规格摘要` explicit resistance against structured fields, update only true numeric mismatches in `components.db`, and incrementally refresh affected prepared/search rows. Applied it to `141,336` resistor rows.
- Verification: DB, prepared parquet, and search sidecar now show `0402WGJ0105TCE` and `FRC0402J105TS` as `1MΩ / 1,000,000Ω`, while `0402WGJ0106TCE` and `FRC0402J106TS` are `10MΩ / 10,000,000Ω`. Direct search for `1M;5%;0402;0402WGJ0105TCE;厚声` returns `0402WGJ0105TCE`; `FRC0402J106TS` no longer appears as milliohm.

## 2026-06-15 - Compound resistor input glued exact model to spec suffix

- Bug: Query `FRC0402J105TS1M;5%;0402;0402WGJ0105TCE;厚声` did not surface FOJAN `FRC0402J105TS`, even though the source row is a valid `1MΩ ±5% 0402` thick-film resistor.
- Root cause: The query contains a valid model prefix `FRC0402J105TS` immediately followed by the spec token `1M` with no separator. The token extractor treated `FRC0402J105TS1M` as one unknown model-like token, then the MLCC/spec parser classified the whole input as insufficient spec before exact-model lookup could recover.
- Fix: Added known-model-prefix recovery for model-like query tokens whose suffix looks like a resistor/spec token, and applied that fallback for `无法识别 / 规格不足 / 解析失败` paths before full-dataframe fallback. Regression now exercises this through the same resolver used by the app.
- Verification: The query now resolves through `model_token_prefix_lookup` as `料号`, reverse-specs `FRC0402J105TS` to `1MΩ / ±5% / 0402`, returns 30 candidates, and places `FOJAN(富捷) FRC0402J105TS` first. Targeted resistor regression cases for `1MR`, lowercase `1mR`, UNI-ROYAL `105`, FOJAN `106`, and the compound FOJAN query all pass.

## 2026-06-18 - FOJAN 5% J-code TS resistor models lost the manufacturer space

- Bug: FOJAN 5% thick-film resistor rows displayed models such as `FRC0603J103TS` / `FRQ0603J103TS`, but LCSC/JLCPCB list these MPNs with a space before the packaging suffix, e.g. `FRC0603J103 TS`.
- Root cause: Earlier FOJAN resistor seed rows normalized the complete manufacturer part number with `clean_model`, which is appropriate for lookup keys but not for the display MPN. That collapsed the official `J... TS` spacing for 5% J-code rows.
- Fix: Added `sync_fojan_jcode_ts_spacing.py` and applied it only to `FOJAN/富捷 + 电阻 + FR?xxxxJ...TS` rows. The script updated `components.db`, prepared parquet, and search sidecar display models to `...J... TS` while keeping `_model_clean` without spaces so both spaced and unspaced user inputs still resolve.
- Verification: `10K 5% 1/10W 0603`, `FRC0603J103TS`, and `FRC0603J103 TS` all return `FOJAN(富捷) FRC0603J103 TS` and `FRQ0603J103 TS`. DB/prepared/sidecar spot checks confirm `FRC0402J105 TS`, `FRC0603J103 TS`, and `FRQ0603J103 TS` exist, while their old no-space display rows no longer remain.

## 2026-06-18 - Low-ohm resistor gaps and Milliohm/RALEC/Bourns parsing

- Bug: Some low-ohm resistor parts existed but could not be found by specification search, and some exact models were parsed by generic resistor logic. Examples: `HoLLR2010-1.5W-2mR-1%` was read from the `2010` package fragment instead of `2mΩ`; `CRF0805-JZ-R001ELF` parsed as generic thick-film instead of Bourns metal-foil current-sense; 2010/1210/0805 milliohm specs had 0 candidates in the fast resistor index.
- Root cause: `Decimal` was missing in `component_matcher.py`, so Milliohm's dedicated parser silently returned `None`; `HoLR/HoLLR/HoLRS` were not included in the model-rule candidate prefix list; Bourns CRF0805 had no dedicated parser; and the library lacked official-source rows for several 0805/1210/2010 milliohm ranges.
- Fix: Imported `Decimal`, added `HoLLR2010` support to the Milliohm parser, added `HoLR/HoLLR/HoLRS` model-rule prefixes, added a Bourns CRF0805 parser, and filled RALEC LR1210 display fields. Added `sync_milliohm_hollr2010.py`, `sync_ralec_lr1210_resistors.py`, and `sync_bourns_crf0805_resistors.py`; synced 80 Milliohm HoLLR2010 rows, 32 RALEC LR1210 rows, and 28 Bourns CRF0805 rows, with prepared/search caches refreshed by clean model key.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py audit_resistor_spec_coverage.py sync_milliohm_hollr2010.py sync_ralec_lr1210_resistors.py sync_bourns_crf0805_resistors.py` passed. Fast index now returns `HoLLR2010-1.5W-1mR-1%`, `HoLLR2010-1.5W-2mR-5%`, `LR1210-2AR002J4`, `LR1210-2AR005J4`, `CRF0805-FZ-R001ELF`, and `CRF0805-JZ-R002ELF` for the corresponding milliohm specs. `audit_resistor_spec_coverage.py` now reports 0 actionable normal-chip gaps and only 2 actionable low-ohm gaps, both `1210 1mΩ ±1/±5%`, which were not filled because the checked official RALEC LR1210 range starts at 2mΩ.
## 2026-06-22 - Halogen-free text blocked resistor spec parsing

- Bug: Query `0603 10R +/-5% RoHS reach Halogen-free` could fall away from resistor parsing and surface MLCC/capacitor-style results in the search UI.
- Root cause: `looks_like_resistor_context()` blocked resistor parsing whenever the compact text contained `UF`, `NF`, or `PF`. The environmental phrase `Halogen-free` becomes `HALOGENFREE`, which contains the substring `NF`, even though it is not a capacitance value.
- Fix: Replaced the broad substring blocker with `has_explicit_capacitance_value_token()`, which only treats real capacitance tokens such as `10nF`, `0.1uF`, `33pF`, `4n7`, and `1u0` as capacitor evidence.
- Verification: Direct parser checks now route `0603 10R +/-5% RoHS reach Halogen-free` as `贴片电阻 / 0603 / 10Ω / +/-5%`; the full search resolver uses `fast_query` and returns 99 resistor matches with no MLCC rows in final matches. Guard query `0603 10nF +/-5% Halogen-free` still routes as MLCC.

## 2026-06-23 - FOJAN exact-part info table kept stale pseudo-series

- Bug: The formal site still showed `FOJAN(富捷) FRC0402J223 TS` in the exact-part `匹配料号资料` table with `系列=FRC0402J` and generated text `FOJAN(富捷) FRC0402J 厚膜电阻系列`, even though the local DB/cache row and final result-table normalizer had already been corrected to `FRC`.
- Root cause: The exact-part info card can be built from public sidecar/spec-derived rows before final display column selection, so stale/generated FOJAN pseudo-series needed to be corrected earlier in `build_part_info_df()`. The live Streamlit instance also continued serving an older checkout/cache after the previous publish nudge.
- Fix: Added a FOJAN series normalization pass directly inside `build_part_info_df()` for both exact-hit and synthetic fallback rows, bumped `QUERY_RESULT_CACHE_VERSION`, `PUBLIC_CODE_STAMP`, `PUBLIC_RELEASE_STAMP`, and the Cloudflare iframe cache buster.
- Verification: Synthetic exact-part rows with `系列=FRC0402J` now render as `FRC / 普通厚膜贴片电阻`; local Streamlit search for `FRC0402J223TS` shows the `匹配料号资料` row as `FRC` with no `FRC0402J` series cell.

## 2026-06-23 - FOJAN FRC0201 resistor specs missed valid range rows

- Bug: Several 0201 resistor spec inputs, such as `10R;1%;0201;0201WMF100JTCE;...`, `12K;5%;0201`, `221K;1%;0201`, and `9.09K;1%;0201`, did not return FOJAN FRC rows even though the FOJAN price range table covers those 0201 values.
- Root cause: This was mixed. Inputs like `1;16W` were parsed as literal `16W`, which over-filtered candidates. Separately, the library had only a sparse set of FOJAN FRC0201 rows, so many valid values inside the official range were absent from both `components.db` and the fast search sidecar.
- Fix: Taught `find_power_in_text()` to interpret split fractional power tokens such as `1;16W` and `1;20W` as `1/16W` and `1/20W`, added `1/20W`/`1/32W` canonical display labels, and inserted nine missing FOJAN FRC0201 rows into the DB/search sidecar: `FRC0201F10R0 TS`, `FRC0201J123 TS`, `FRC0201J303 TS`, `FRC0201F47R0 TS`, `FRC0201F1003 TS`, `FRC0201J224 TS`, `FRC0201F2213 TS`, `FRC0201F5100 TS`, and `FRC0201F9091 TS`.
- Verification: Direct parser tests map `1;16W` to `1/16W` and `1;20W` to `1/20W`. Full query checks for the no-power 0201 specs above now return FOJAN FRC rows. `0201 1/16W` still correctly excludes FOJAN FRC0201 because FOJAN's provided table rates FRC0201 as `1/20W`, lower than a real `1/16W` requirement.

## 2026-06-23 - Resistor power was treated as high-replaces-low

- Bug: Resistor spec searches could recommend higher-power parts as `高代低`, for example allowing 1/8W or 1/4W candidates into a 1/10W requirement.
- Root cause: The fast resistor sidecar query used `_power_watt >= target`, and the ranking logic treated a higher wattage as a strictly better resistor parameter. A later in-memory filter also only narrowed to same-power rows when such rows were found, otherwise it left all candidates in place.
- Fix: Changed resistor power to an exact-match requirement in the fast sidecar query and in-memory filtering, removed higher-wattage as a `高代低` trigger, and changed recommendation conflicts to report any power mismatch rather than only lower power.
- Verification: `0603 10R +/-5% 1/10W`, `0603 10R 5% 1/8W`, and `0603 10R 5% 1/4W` each return candidates with only the requested inferred power.

## 2026-06-24 - Member login state was lost after returning to search

- Bug: Logging in from the fixed top-right member entry showed the member center as logged in, but clicking `返回搜索` returned to the search page with the top-right button back at `会员登录`.
- Root cause: The member token was stored only in Streamlit `session_state`. The fixed navigation links change query params and can reload the Streamlit app/session, so the server-side session token was not available after returning to search.
- Fix: Added a `member_token` query param restore path, made `current_member()` recover active members from that token, wrote the token to the URL on login/register, preserved it in fixed member/admin navigation links, and cleared it on logout.
- Verification: Function-level regression simulates login, empty-session reload with URL token, member restoration, token-preserving return-search href, and logout token cleanup.

## 2026-06-24 - Configured backend admin could not log in as member

- Bug: The member login page rejected `amdin/123456`, even though that account was the configured backend administrator account.
- Root cause: The backend admin credential check and the member system were separate. Member authentication only read rows from `cache/member_auth.sqlite` and never seeded the configured backend admin into the `members` table.
- Fix: Added configured-admin member synchronization before member authentication and member admin listing. The configured admin is created or repaired as an active `admin` member, with the password stored as the existing PBKDF2 salted hash rather than plaintext.
- Verification: Temp DB regression confirmed `amdin/123456` logs in as an active admin member, wrong password fails, the stored hash is not plaintext, and the account appears in the member-management list; `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-24 - Member admin timestamps were shown in UTC

- Bug: Member admin columns such as `注册时间`, `最后登录`, and `更新时间` showed times around `01:xx` when the user expected current China-time values.
- Root cause: `current_timestamp_text()` used `time.strftime()` with the server's local timezone. Streamlit Cloud's host timezone is UTC, so timestamps were written and displayed 8 hours behind Beijing time.
- Fix: Made timestamp generation explicitly use `Asia/Shanghai`, added `member_auth_meta` with a one-time migration key, and when running on a UTC-hosted environment shifted existing member/session timestamp strings by +8 hours exactly once.
- Verification: Temp DB regression confirmed legacy UTC member timestamps migrate to Beijing time, migration does not repeat, and new timestamps match `Asia/Shanghai`; `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-24 - BOM `.xls` uploads could be misreported as empty

- Bug: Uploading a data-bearing `.xls` BOM could show `上传文件内容为空，未能生成可匹配数据`.
- Root cause: The deployed requirements did not include `xlrd`, so true legacy BIFF `.xls` files could fail to parse. Additionally, ERP exports commonly save HTML tables with an `.xls` suffix; the reader only tried Excel engines and collapsed parse failures into an empty workbook.
- Fix: Added `xlrd` to requirements and added an HTML table fallback for Excel uploads, with explicit `utf-8-sig`, `gb18030`, `big5`, and `latin1` decode attempts before parsing so Chinese headers survive.
- Verification: Function-level regression confirmed a GB18030 HTML table named `.xls` loads as a non-empty workbook with Chinese columns and rows, while CSV upload still works; `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-24 - Joyin JSN NTC equivalents were absent from the local library

- Bug: Searching a Murata NTC such as `NCP15XH103F03RC` could not return 信昌/久尹 equivalents because `components.db` had zero `JOYIN(久尹)` thermal resistor rows; only Joyin varistor rows existed.
- Fix: Added `sync_joyin_ntc_thermistors.py` to parse the local JSN-A/C/G/H official PDFs, expand the `X` / `Y` tolerance placeholders into real part numbers, import generated Joyin NTC rows, and refresh prepared/search sidecar caches. Added Joyin JSN series recognition and made NTC matching/sorting consider B value and B condition.
- Verification: Imported 6,780 Joyin JSN NTC rows. `NCP15XH103F03RC` now resolves through `fast_query` with 61 matched rows, including 56 `JOYIN(久尹)` rows; B=3380K / 25/50℃ Joyin rows are marked `完全匹配` and sorted before nearby non-B-exact variants.

## 2026-06-24 - FOJAN FRC0201 5% 33R was absent from searchable range rows

- Bug: Query `0201 5% 33R` returned other resistor brands but no `FOJAN(富捷)` result, even though the FOJAN price range table covers `FRC 0201 1/20W` 5% values from `10R-10M`.
- Root cause: The previous FRC0201 fix only inserted several user-reported gap values, leaving the wider official range sparse. Generated resistor rows also stored the tolerance in `阻值误差`, while the fast search sidecar's `_tol` field was derived only from `容值误差`, so newly generated resistor rows could still be filtered out by tolerance.
- Fix: Added `sync_fojan_frc0201_range_rows.py` to rebuild FOJAN FRC0201 range-generated rows from the pricing/range table, set both resistor and generic tolerance fields, and refresh prepared/search sidecar caches. Updated `prepare_search_dataframe()` to fall back from `容值误差` to `阻值误差` when populating `_tol`.
- Verification: Rebuilt 909 generated FOJAN FRC0201 rows. The resistor sidecar row for `FRC0201J330 TS` now has `_size=0201`, `_tol=5`, `_res_ohm=33.0`, `_power_watt=0.05`. Full query checks return `FOJAN(富捷) FRC0201J330 TS` for `0201 5% 33R`, `FRC0201F33R0TS` for `0201 1% 33R`, and `FRC0201J683 TS` for `0201 5% 68K`, with FOJAN cost/MOQ populated.

## 2026-06-24 - Joyin JSN NTC series semantics were unclear and over-ranked

- Bug: For Murata regular NTC `NCP15XH103F03RC`, the Joyin results could show pseudo-series such as `JSNA103F`, English generic series descriptions, and multiple Joyin JSN-A/C/G/H rows all marked as `完全匹配`.
- Root cause: Some runtime/display paths could reuse stale series text derived from the part-number prefix instead of the final Joyin suffix. The ranking logic compared electrical parameters and B value but did not distinguish Joyin regular JSN-G/H from automotive JSN-A/C when the source Murata series is regular NCP.
- Fix: Added Joyin JSN suffix semantics (`A=车规高温`, `C=车规`, `G=常规`, `H=常规高温`), Chinese series descriptions from the Joyin PDFs, display-time normalization for stale Joyin rows, and NCP-to-JSN-G series-class ranking/level rules.
- Verification: Reimported 6,780 Joyin NTC rows. `NCP15XH103F03RC` now returns `JSN-G` rows first with Chinese `常规贴片 NTC` series descriptions; JSN-H/JSN-C/JSN-A remain visible but are downgraded to `需确认替代`.

## 2026-06-24 - Member login entry was visible inside backend admin

- Bug: The fixed top-right `会员登录` button was still visible while the user was already on the authenticated backend admin page.
- Root cause: The backend entry button and member entry button were rendered independently. `render_member_entry_button()` did not check whether `admin=1` backend mode was active.
- Fix: Made `render_member_entry_button()` return without rendering whenever the backend admin page is requested.
- Verification: Function-level regression confirmed that in admin mode the member entry renderer does not call `current_member()` and does not emit `st.markdown()`.

## 2026-06-24 - Compound model/spec queries could be very slow

- Bug: Mixed input such as `FRC0402J105TS1M;5%;0402;0402WGJ0105TCE;厚声` could take about 60-75 seconds before returning results.
- Root cause: The model-token extractor treated the entire semicolon-delimited string as a possible part number before trying the real embedded model token. That caused an expensive normalized full-library lookup on an impossible model string.
- Fix: The extractor now avoids adding whole raw strings that contain separators, and the resolver performs an early model-token/prefix lookup before the heavier spec-search path. Model and prefix lookups now try the fast search sidecar before falling back to the slower database scan.
- Verification: The same compound query now resolves through `model_token_prefix_lookup` in about 1.6 seconds; direct token lookup for `FRC0402J105TS1M;5%;0402;0402WGJ0105TCE;厚声` finds `FRC0402J105TS` in under one second. `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-24 - BOM reader errors could still look like empty uploads

- Bug: A real `.xls` BOM could still be reported as an empty upload when the runtime lacked the required legacy Excel reader or when every parser failed.
- Root cause: Some read failures were collapsed into empty workbook data, so the front end could only show a generic empty-file message instead of the actual parser/dependency failure.
- Fix: `read_uploaded_bom_workbook()` now carries a `read_error`/`read_warning` field through the result and the UI displays the actionable failure reason. Empty byte uploads are separated from parser failures.
- Verification: The local real BOM `C:\Users\zjh\Desktop\待完成\阻容待下6-22.xls` reads 199 rows after installing the declared `xlrd` dependency; missing `xlrd` now produces a clear install/convert-to-xlsx message rather than a misleading empty-file status.

## 2026-06-24 - Streamlit entrypoint had corrupted startup text

- Bug: `streamlit_app.py` contained mojibake in startup error strings and could produce confusing startup diagnostics.
- Fix: Rewrote the entrypoint wrapper with valid UTF-8 Chinese startup messages while keeping the same `component_matcher.main()` launch behavior.
- Verification: Local Streamlit smoke test on port 8511 returned HTTP 200, and `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-25 - Backend admin login did not carry member state back to search

- Bug: Logging in through the backend admin entry as `amdin`, then clicking `返回搜索`, returned to the search page with `会员登录` shown again.
- Root cause: Backend authentication only set `_no_match_admin_authenticated`. It did not create a member session token, and the backend return-search link did not intentionally carry a member token.
- Fix: After successful backend admin credential validation, the app now synchronizes the configured admin member account, creates a normal member session, writes `member_token` into query params, and preserves that token on the backend `返回搜索` link.
- Verification: Function-level temp DB test confirmed backend admin login creates a valid admin member session and renders a return-search URL with `member_token`. Local Streamlit browser flow confirmed `admin=1` login returns to search with `会员中心` visible and `会员登录` hidden.

## 2026-06-25 - Member login was lost after closing and reopening the page

- Bug: A user could log in successfully, close the page, reopen the app within the desired active window, and still see the logged-out state.
- Root cause: Member sessions were only carried by Streamlit session state or the `member_token` query parameter. Closing the page removed Streamlit session state, and reopening the base URL did not include the query token, even though the server-side session row still existed.
- Fix: Added a browser persistence bridge that stores the member token in same-site cookie/localStorage for one hour, restores it into the URL query parameter when the app is reopened, clears it on logout or invalid token, and changed server session expiry to a sliding one-hour timeout extended on every valid token use.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-25 - BOM upload did not continue after required member login

- Bug: If a visitor uploaded a BOM/image before logging in, the app showed the member login panel. After successful login, the uploaded file still appeared in the uploader UI but matching did not automatically continue, forcing a second upload.
- Root cause: The BOM flow stopped immediately on the login requirement before caching the uploaded file bytes. A login rerun/query update could leave the frontend uploader display intact while the Python-side `UploadedFile` object was no longer available for processing.
- Fix: Cache the uploaded BOM file bytes/name/type/size in Streamlit session before enforcing member login, wrap that cache with an UploadedFile-compatible object, and reuse it after login when the original Python upload object is gone.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-26 - Image BOM OCR accepted garbled text as matchable rows

- Bug: Uploading a small Chinese quote-sheet screenshot could produce OCR preview and match rows full of fragments such as `ee a ee`, `masons`, and `or ||`.
- Root cause: The image OCR flow treated any non-empty Tesseract result as usable. A failed Chinese-table OCR pass could therefore flow into BOM parsing/matching as if it were real content.
- Fix: Increase small-image OCR scaling, try sharpened/thresholded variants and multiple page segmentation modes, score OCR output for recognizable BOM headers, models, specs, prices, Chinese characters, and digits, and reject low-quality OCR output with an explicit message before matching. If Chinese OCR packages are not detected, the error now says so.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed. Simulated OCR quality tests reject the garbled sample and accept both a quote-table dataframe and a compact valid resistor spec line.

## 2026-06-26 - Image BOM upload stayed at the reading progress card

- Bug: Uploading a dense quote-sheet PNG could leave the public page at `BOM 文件读取中` / 3% for too long.
- Root cause: OCR processing tried too many large enhanced variants and page segmentation modes without a bounded per-call timeout. On Streamlit Cloud, Tesseract can spend a long time on small dense table screenshots.
- Fix: Limit OCR to two bounded image variants and two page segmentation modes, reduce small-image scale target, add per-pass Tesseract timeouts, and add a total OCR budget that returns a clear timeout message if the image cannot be read quickly enough.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed. The user's PNG preprocessing now produces a `2000x716` image with two variants. Local real OCR remains unavailable because no Tesseract executable is installed on this Windows machine.

## 2026-06-26 - Image BOM OCR lost row/column structure for quote screenshots

- Bug: The public page could finish OCR on the user's FOJAN quote-sheet PNG but output 9 failed rows, garbled OCR preview text, and an incorrect MLCC distribution instead of the visible 12-row resistor quote table.
- Root cause: The image OCR pipeline only used free-text OCR grouping. For small dense grid screenshots, Tesseract's word order and line grouping can be wrong even though the visual table grid is clear.
- Fix: Add a grid-table OCR path before the free-text fallback. It detects horizontal/vertical grid lines, reconstructs header/data row intervals, enlarges each row, masks grid strokes, OCRs the row image, and assigns OCR words back to detected columns. A second cell-by-cell fallback now crops and OCRs each detected cell when row-level OCR is still not meaningful.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed. Local image analysis on the reported PNG detects 11 table columns and 12 data rows after the header. Cloud OCR verification is required after deployment because local Tesseract is unavailable.

## 2026-06-24 - Backend resolved no-match reports did not become searchable library rows

- Bug: After resolving a no-match report in the backend with a correct brand/model, searching the same or equivalent specification could still return no match.
- Root cause: Backend resolution only updated `cache/no_match_reports.sqlite` as a mapping. It did not write a component row into `components.db` or the fast search sidecar. For direct backend-resolution hits, the candidate row could also be filtered out by the normal second-stage matching/exclusion path.
- Fix: Backend resolution now builds a supplemental component row, upserts it into `components.db`, appends it to the appropriate fast search sidecar table, refreshes sidecar metadata, clears query/data caches, and marks direct resolution specs so `run_query_match()` preserves the backend candidate.
- Verification: Isolated temp-DB flow submitted a no-match report, resolved it as `FOJAN(富捷) / FRC0603J103 TS`, confirmed the row was inserted into `components.db`, confirmed the resistor sidecar row contained `0603 / 10000Ω / 5% / 0.1W`, confirmed direct report lookup returned one `后台补料` row, and confirmed equivalent spec search `0603 10K ±5% 1/10W` returned one `完全匹配` row.

## 2026-06-26 - Backend daily search trend chart rendered raw HTML

- Bug: The backend search-record module displayed raw `<div class="search-trend-row">...` markup under "每日十大规格趋势" instead of the intended bar chart.
- Root cause: The HTML string was indented inside a triple-quoted Python string. Streamlit Markdown interpreted that indentation as a code block, so the tags were escaped and shown as text.
- Fix: Dedent/strip the trend chart wrapper and each generated row before sending the final markup to `st.markdown(..., unsafe_allow_html=True)`.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-26 - No-match report button cleared the current search results

- Bug: Clicking "回报物料无匹配型号" submitted the report but left the page with only the success notice and the search input, so users had to search again to see the prior result.
- Root cause: `st.button(..., on_click=...)` triggers a full Streamlit rerun. The callback persisted the report notification but did not preserve or replay the search request, and the result UI was only rendered in the one-run `search_clicked` branch.
- Fix: Give the search input a stable session key, save the last search text, set a restore flag in the report callback, and treat that restore flag as a one-shot search request on the rerun. Restored renders skip duplicate member search-log insertion.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed.

## 2026-06-26 - Yageo MLCC 630V part displayed blank voltage

- Bug: Searching `0.01uF;630V;±10%;0805;X7R;YAGEO;CC0805KKX7RZBB103;无卤` showed the Yageo original-material row with an empty `额定电压（V）` field even though the query text includes `630V`.
- Root cause: The Yageo CC-series voltage-code map was stale and omitted `Z = 630V`; exact/mixed model searches also trusted blank library voltage fields instead of filling them from explicit voltage text in the query.
- Fix: Centralized the Yageo voltage-code map and updated parsing so `Z -> 630`, `B -> 500`, `C -> 1000`, and `D -> 2000`; added an explicit-query voltage fallback before search cache keys, BOM matching, regression checks, and front-end search rendering.
- Verification: `python -m py_compile component_matcher.py streamlit_app.py` passed. Static validation confirmed `CC0805KKX7RZBB103` voltage code `Z -> 630` and `parse_voltage_from_text()` extracts `630` from the reported query.
## 2026-06-29 - Formal shell did not retain member login safely

- Bug: A member could log in on the formal Cloudflare page, close it, and reopen it within one hour but still appear logged out. The first `postMessage` bridge draft also used a wildcard target origin, which could expose the opaque session token if the direct Streamlit page were embedded by another site.
- Root cause: Streamlit renders the persistence script inside a sandboxed nested component iframe, so it cannot directly write the Cloudflare shell's cookie or localStorage. The first bridge also rendered before `current_member()` validated the query token, so an invalid token was saved and the deferred clear flag was never reliably rendered on a second run.
- Fix: The Streamlit component validates the member session before deciding whether to save or clear it and posts only to `https://fruition-component.pages.dev`. The Cloudflare shell creates a cryptographically random per-load channel, passes it into the Streamlit iframe, accepts only messages with that channel, stores the token for one hour, injects it on reopen, and removes one-time `member_token` values from the visible shell URL.
- Verification: Three bridge source regressions, all seven system regressions, Python compilation, Worker syntax validation, and `git diff --check` passed. Formal deployment and browser verification are recorded separately in `operation_log.md`.

## 2026-06-29 - Cloudflare deployment failures returned a success exit code

- Bug: `deploy_cloudflare_pages_proxy.ps1` could print Wrangler `fetch failed` while the PowerShell process still exited successfully, allowing automation to report a deployment that did not happen.
- Root cause: The script invoked `wrangler.cmd` but did not inspect `$LASTEXITCODE`; the surrounding `finally` only restored the working directory.
- Fix: Check `$LASTEXITCODE` immediately after Wrangler returns and throw on any nonzero value.
- Verification: PowerShell AST parsing passed, and a real transient Wrangler failure was distinguished from the later successful deployment whose formal HTML exposed the new cache buster.

## 2026-06-30 - Member login panel failed after the Streamlit 1.58 reboot

- Bug: Searching on the formal site while logged out displayed Streamlit's red `Missing Submit Button` error instead of a usable member login panel.
- Root cause: The login and registration controls were nested in `st.form` blocks that rendered incorrectly on the formal Streamlit 1.58 runtime after the application reboot.
- Fix: Replaced the two member forms with ordinary keyed inputs and keyed buttons while retaining the existing authentication, registration, validation, and rerun behavior.
- Verification: Python compilation, Worker syntax validation, diff checks, and all 14 member/system regressions passed. Clean local and formal-site browser flows searched `FRC0603J100 TS`, displayed the member login button, and contained no `Missing Submit Button` error.

## 2026-06-30 - Real FOJAN cost workbook imported zero rows

- Bug: Uploading `富捷电阻报价单-富临通701-客户.xlsx` displayed the warning that no importable cost data was found, although the visible sheet contained the expected FOJAN quote matrix.
- Root cause: The `5%` and `1%` header cells were stored by Excel as numeric values `0.05` and `0.01` with percentage number formatting. The parser only recognized literal text headers such as `5%` and `1%`.
- Fix: Normalize tolerance headers from literal percent text, full-width percent text, and Excel's numeric percentage values before locating the two price columns. The regression fixture now uses numeric percentage cells with `0%` formatting, matching the recurring customer template.
- Verification: The unmodified 11.4 KB source workbook parsed, imported, activated, and persisted 40 rows. Browser upload showed current rows `40` and one active history item with no relevant console errors. Representative costs resolved as `FRC0603J100=2.8`, `FRC0603J103=3.38`, `FRC0603F1002=3.84`, and `FRC0603F8R20=5.33`; all 14 regressions passed.

## 2026-06-30 - PDC series descriptions repeated the visible series code

- Bug: Search results displayed values such as `系列=FCF` next to `系列说明=PDC FCF ...`, redundantly repeating the vendor and series code.
- Root cause: PDC official resistor profiles embedded `PDC + series code` in the description, and older cached rows also contained variants such as `PDC FCF-E`.
- Fix: PDC official descriptions now contain only the product-purpose description. The display formatter also removes legacy `PDC {series}` and `PDC {series}-{variant}` prefixes so existing cached rows are corrected immediately.
- Verification: Dedicated tests covered `FCF`, `FCF-E`, and `FWF` while preserving a non-PDC description; all 15 member/system regressions passed.

## 2026-06-30 - Member login paused on repeated remote snapshot reads

- Bug: A normal formal-site member login took about 10.6 seconds from clicking `登录` until the authenticated page appeared.
- Root cause: One login synchronously pulled the complete remote member snapshot in `authenticate_member()`, `get_member_by_username()`, and `get_member_by_id()`, then uploaded the session snapshot. Normal session validation also pulled the remote snapshot on every Streamlit rerun.
- Fix: Coalesce member snapshot reads for 15 seconds per local replica. Login still forces one fresh pull, account/profile/password/admin mutations still force fresh pulls, and the new session still uploads to remote storage.
- Verification: The remote-snapshot regression asserts one GET and one PUT per login and zero additional remote requests across three immediate session validations. All 15 member/system regressions passed.

## 2026-06-30 - Other-passive searches could fall back to mismatched models

- Bug: Film-capacitor, varistor, inductor, crystal, and oscillator searches could retain unrelated candidates when no row matched an explicitly requested material, tolerance, body, pitch, voltage, value, frequency, output type, or load capacitance, then label those candidates as complete matches.
- Root cause: `match_other_passive_spec()` applied several explicit filters only when `same_value.any()` was true. A zero-match condition therefore skipped the filter instead of returning no result.
- Fix: Explicit other-passive specifications are now hard constraints. Tighter tolerances remain eligible where the component class permits high-to-low substitution, but absent or conflicting critical values no longer fall through to another brand/model.
- Verification: A dedicated regression covers negative and positive inductor, leaded-varistor, and crystal cases. Mismatches return no model while exact specifications still return the expected model.

## 2026-07-01 - Generic passive fields hid missing parameters and caused wrong common-mode matches

- Bug: Some varistor rows stored clamping voltage in the generic voltage field, while common-mode choke rows could store inductance in the generic value field even when the user searched by impedance. This could produce semantically wrong brand/model candidates.
- Root cause: The runtime cache allowed one generic value/unit pair to stand in for component-specific fields, and the library had no separate nominal-varistor-voltage column. Missing-field coverage therefore looked better than the data actually supported.
- Fix: Added separate nominal/clamping-voltage semantics, safe MOV model decoding, official Panasonic common-mode and Vishay NTCS backfills, exact common-mode impedance/inductance matching, blank-model rejection, and a repeatable critical-parameter coverage report.
- Follow-up fix: The real text parser originally recognized only `nH/uH/mH` values. It now recognizes common-mode and ferrite-bead `Ω/KΩ/OHM/KOHM` tokens and the `0302/0504/0804` magnetic-component packages, so user text reaches the strict impedance matcher.
- Verification: `EXC14CE121U` is indexed as `120 Ω`; nominal `MOV-14D471K=470 V` matches while its `775 V` clamp value does not. Main/search SQLite integrity checks pass and all 16 member/system regressions pass.
- Remaining data work: Official sources are still required for aluminum-electrolytic ESR/ripple/life gaps, undecodable varistor nominal voltages, incomplete common-mode families, and crystal family rows without one exact load capacitance. These rows remain blank or range-based by design and are not silently guessed.

## 2026-07-02 - MLCC searches ignored trailing application requirements

- Bug: `47nF 1210 630V 谐振电容` returned ordinary X7R models because only the numeric/package fields reached MLCC matching.
- Root cause: The MLCC parser did not populate `特殊用途`, and resonant-capacitor semantics were not part of the strict series-class vocabulary.
- Fix: Parse application classes from the full query, add `谐振/Resonant` as a strict MLCC class, filter candidates by that class, and show the recognized application in the specification table.
- Verification: The reported query returns no ordinary X7R fallback; a same-spec explicit resonant candidate is accepted and a general-purpose X7R candidate is rejected. The full 17-test member/system suite passes.

## 2026-07-02 - MLCC application aliases could bypass strict matching

- Bug: The strict application filter recognized `软端子` but not common equivalent notes such as `软端`, `柔性端子`, `软终端`, or `FLEXITERM`.
- Root cause: Application matching used a canonical class correctly, but the alias vocabulary was narrower than the terms users place in specification remarks.
- Fix: Expanded automotive, soft-termination, high-Q/low-loss, and EMI-filter aliases. Multiple notes remain cumulative hard constraints, so `车规软端` requires a candidate classified as both automotive and soft termination.
- Verification: Regression coverage now includes all strict MLCC application classes and aliases; ordinary candidates and candidates satisfying only one part of a combined requirement are rejected. All 17 member/system tests pass.

## 2026-07-02 - Missing FOJAN range model lost brand and cost

- Bug: Exact search `FRC0402F5233TS` decoded as `0402 / 523KΩ / 1% / 1/16W`, but the part-information row had blank cost and the result did not visibly identify the input model as FOJAN.
- Root cause: The exact model was absent from the component library. The naming-rule fallback parsed its electrical parameters but left the brand blank and produced pseudo-series `FRC0402F`, so neither the active FOJAN range rule nor the official `FRC` profile could match.
- Fix: Infer `FOJAN(富捷)` for valid missing-library `FRC/FRL` resistor part numbers before applying model rules. The fallback now resolves the official `FRC` series and is priced by the current active range list without requiring one database row per resistance value.
- Verification: The original workbook maps this model to `FRC / 0402 1/16W / 10R-1M / 1%`, cost `1.7`, MOQ `10000PCS`. The full 17-test member/system suite passes.

## 2026-07-03 - FOJAN rule fallback accepted invalid models and mispriced 1% zero-ohm parts

- Bug: Missing-library strings such as `FRC0402F5243TS`, `FRC0402F9993TS`, and `FRC0402F0003TS` were accepted as FOJAN models. Separately, 1% zero-ohm FRC rows used the 5% zero-ohm price, so 0805 displayed `4.4` instead of `5.2`.
- Root cause: The fallback regex accepted any digits/R value code and the generic resistor parser could bypass failed FOJAN brand inference. The zero-ohm pricing branch explicitly fell back from `price_1` to `price_5`.
- Fix: Validate FRC/FRL structure, value-code shape, series range, and E24/E96 resistance values before creating a rule row. Require an applicable active price rule. Generate the same validated FOJAN row for complete specification searches. Price every 1% zero-ohm FRC row from that size's 1% `10R-1M` segment.
- Verification: Invalid model negatives return no fallback; `0402 523KΩ 1% 1/16W` includes `FRC0402F5233TS`. Zero-ohm checks cover every priced size from 0201 through 2512. All 19 member/system tests pass.

## 2026-07-03 - Cost lists and no-match reports were not durable across instances

- Bug: Member accounts survived Streamlit instance replacement through D1, but uploaded cost lists and no-match reports remained local SQLite files and could disappear with an instance reset.
- Root cause: Only `member_auth.sqlite` used the authenticated snapshot API. The two other runtime databases had no remote snapshot, history, checksum, or restore path.
- Fix: Add an authenticated `/api/runtime-store/snapshot` endpoint with separate `cost-price` and `no-match` keys, optimistic versions, SHA-256 validation, bounded payloads, and per-store history. Runtime reads use a 60-second refresh window; mutations force a pull before writing and flush afterward. An existing valid local SQLite database automatically seeds an empty remote store on its first read.
- Verification: A regression uploads each database, switches to a fresh local path, and restores the records from its remote snapshot. Worker source/security tests, Python/JavaScript compilation, unauthenticated endpoint `401`, and all 19 member/system tests pass.

## 2026-07-03 - Unique-model backfill proposed invalid varistor inch packages

- Bug: The key-parameter dry-run proposed 99 new `尺寸（inch）` fills, including radial 5mm `MVR05D/xxKD05` varistors copied as `2020` packages.
- Root cause: The unique-model copier treated any single populated duplicate value as authoritative, even for varistor inch dimensions where historical component-type and package mappings are unreliable.
- Fix: Exclude varistor `尺寸（inch）` from duplicate-row propagation. Varistor body/disc dimensions continue to use explicit model decoding and source-backed fields.
- Verification: The follow-up dry-run reports `unique_model_values=0`; no unsafe parameter rows were written.

## 2026-07-03 - Newly activated FOJAN cost lists did not inherit the 1% zero-ohm rule

- Bug: Static FOJAN series pricing mapped 1% 0R to the same-size 1% `10R-1M` price, but the separate active cost-list lookup still tried to match literal 0R and could return no price after a new workbook was uploaded and activated.
- Root cause: The earlier correction covered `lookup_resistor_series_pricing()` only; `lookup_active_cost_price_for_row()` retained the generic resistance-range lookup.
- Fix: For FRC 1% zero-ohm rows, active-list lookup now selects the current workbook's same-size 1% rule using the `10R` boundary. The value is dynamic and follows each newly activated workbook rather than a hard-coded cost.
- Verification: An uploaded workbook containing 5% 0R=`2.60` and 1% `10R-1M`=`3.10` prices `FRC0603F0000TS` at `3.10`. The full 12-test system regression suite passes.

## 2026-07-03 - Release workflow did not enforce runtime-data isolation

- Risk: The normal publish workflow validated Python syntax but did not run the member/backend regression suite or prove that local runtime databases remained unchanged. The no-match database path also lacked the environment override already used by member and cost databases.
- Fix: Added a mandatory release safety gate that runs syntax checks and the complete system suite with all three runtime databases redirected to a temporary directory. It fingerprints the member, cost-list, and no-match SQLite files plus WAL/SHM/journal files before and after validation and blocks release on any change.
- Prevention: Added repository-level safety rules requiring additive migrations, protected runtime records, isolated tests, and post-change verification. The one-click publish path now invokes the gate before bundle building, committing, or pushing.
- Verification: The gate passes 13 system tests, including an explicit assertion that all runtime database paths are inside the temporary test directory. Protected database fingerprints are unchanged and all three local SQLite integrity checks return `ok`.

## 2026-07-03 - Search results lacked source-backed manufacturer packaging quantities

- Gap: The result `MOQ` field only came from an active cost workbook or FOJAN price table. Other brands had no fallback even when the manufacturer explicitly published standard reel quantities.
- Risk: Treating package size as a universal MOQ would be inaccurate because reel quantity can depend on series, case, thickness, carrier material, reel diameter, and ordering-code suffix.
- Fix: Added a strict manufacturer-packaging rule layer. Cost-list MOQ remains authoritative; only a blank MOQ falls back to an explicitly labeled manufacturer standard package quantity with an official source.
- First coverage: 81,796 rows across Panasonic ERJ/ERA, YAGEO RC, TDK C1608/080/A MLCC, and Vishay NTCS0402E/0603E/0805E.
- Verification: Datasheet/model-page samples confirm electrical parameters and package quantities. The full 14-test safety gate passes and protected member/backend runtime databases remain unchanged.

## 2026-07-04 - Manufacturer package quantity coverage was limited to the first brand batch

- Gap: Murata, Samsung, additional YAGEO/TDK capacitor sizes, and TDK NTC thermistors still had blank fallback MOQ values even where ordering-code packaging and official package quantities were available.
- Fix: Added source-backed rules for Murata GRM/GCM/GCJ, YAGEO CC 0201/0402/0603, TDK C0603/C1005/C2012 and NTCG06/10/16, and Samsung CL models with explicit 7-inch packaging code `C` plus a supported thickness class.
- Accuracy boundary: YAGEO CC 0805 can have different quantities under the same apparent packaging letter, Samsung non-`C` suffixes have reel/quantity options, and Murata inductor `#` suffixes do not identify one package. Those cases remain blank instead of receiving a guessed MOQ.
- Coverage: Source-backed manufacturer fallback now covers 105,824 library rows, an increase of 24,028 over the first batch. Active cost-list MOQ remains authoritative and is never overwritten.
- Verification: The full 14-test release safety gate passes; protected member, cost-list, and no-match runtime databases are unchanged.

## 2026-07-09 - Backslash-separated chip-resistor specs were parsed as capacitors or incomplete specs

- Bug: Inputs like `贴片\499R\±1%\1/16W\0402 ROHS`, `贴片\499K\±1%\1/16W\0402 ROHS`, and `贴片\51R\±5%\1/16W\0402 ROHS` did not search as chip-resistor specifications. `499K` could be misread by the generic capacitor parser, while `499R` and `51R` were reported as incomplete specs.
- Root cause: The resistor value token boundary accepted `/` but not backslash `\`, and query-mode detection reached MLCC/generic spec parsing before trying a complete resistor spec parse.
- Fix: Treat backslash as a resistor value delimiter and run the explicit resistor-spec parser before MLCC/generic spec parsing. The three reported inputs now resolve as `贴片电阻 / 0402 / 1/16W` with `499Ω`, `499KΩ`, and `51Ω`.
- Verification: Added regression coverage for all three original strings. The focused resistor test passes, and the release safety gate passes all 14 system tests with member, cost-list, and no-match databases isolated and protected runtime fingerprints unchanged.

## 2026-07-05 - Complete source-decodable manufacturer package quantity audit

- Gap: The prior four passes covered only 130,455 of 1,676,716 library rows and left several high-volume surface-mount families with blank manufacturer fallback quantities.
- Fix: Added strict ordering-code decoders for KOA current chip families with `TP/TD/TE`, YAGEO RT/AC/AA/AT/RE/PT/AR/RL/RP, Vishay CRCW 0201 plus lead-free/lead-bearing package codes, and Vishay TNPW package codes. Active cost-list MOQ remains authoritative.
- Coverage: A fresh full-library execution covers 452,883 rows, a net increase of 322,428. The scan executes the production lookup function against every library row rather than estimating by series counts.
- Accuracy boundary: Legacy KOA RN73, axial/military resistors, ambiguous YAGEO AF reels, undefined CRCW/TNPW legacy suffixes, and components missing thickness or package suffix remain blank. These are final source-data exceptions, not candidates for size-only defaults.
- Data safety: No component, member, cost-list, or no-match SQLite database is modified by these lookup rules or the read-only audit.
- Verification: The release safety gate passes all 14 system regressions with isolated temporary databases; every protected runtime database fingerprint is unchanged.

## 2026-07-04 - High-volume Samsung and Walsin families still lacked manufacturer package quantities

- Gap: Samsung RC/RCS resistors and Walsin WR resistors/general-purpose MLCCs had blank fallback MOQ values despite carrying explicit manufacturer packaging codes.
- Fix: Decode Samsung `CS`, Walsin WR size/package/termination combinations, and Walsin MLCC `T` packaging together with exact case thickness. The rules link to current manufacturer catalogs and do not trust inconsistent display-size fields when the ordering code is authoritative.
- Accuracy boundary: Walsin 1812 rows at 3.20mm, bulk/nonstandard WR suffixes, and unsupported reel options remain blank. Active cost-list MOQ continues to override every manufacturer fallback.
- Coverage: Added 22,616 rows, increasing total source-backed manufacturer package coverage to 128,440 library rows.
- Verification: The full 14-test release safety gate passes and protected member, cost-list, and no-match runtime databases are unchanged.

## 2026-07-04 - Specialized Walsin MLCC and Samsung current-sense families lacked package quantities

- Gap: Walsin SH/RF/HH/MT capacitors and Samsung RU/RUK/RUT/RJ resistors still had blank manufacturer fallback MOQ values.
- Fix: Added per-series Walsin size-code, case-size, thickness, and `CT` validation from four current manufacturer specifications. Expanded Samsung `CS` decoding to documented current-sense and wide-terminal families, including the RJ1220 2mΩ embossed-tape exception.
- Accuracy boundary: RUW and Walsin rows whose thickness is absent from the corresponding series table remain blank; values are not copied from a different Walsin MLCC family.
- Coverage: Added 2,015 rows and increased total source-backed manufacturer package coverage to 130,455 rows.
- Verification: The full 14-test release safety gate passes; protected member, cost-list, and no-match runtime databases are unchanged.

## 2026-07-09 - Brand-qualified specification searches still returned other brands

- Bug: A query such as `富捷 0402 1% 10K` or `0402 1% 10K 富捷` parsed the electrical specification, but the brand text was not treated as a strict result constraint.
- Root cause: Brand inference was only used for exact/model-derived rows and for same-brand exclusion. Free-text specification parsing did not preserve a requested-brand flag, so later matching still considered all brands.
- Fix: Detect supported brand aliases in the full query text, persist a requested-brand flag on the parsed spec, and apply that filter before candidate-row matching, database candidate selection, and final same-brand exclusion.
- Verification: Added regression coverage proving plain `0402 1% 10K` returns multiple brands while `富捷 0402 1% 10K`, `0402 1% 10K 富捷`, and `FOJAN 0402 1% 10K` return only FOJAN rows. The focused resistor test and release safety gate pass with protected runtime database fingerprints unchanged.

## 2026-07-09 - Decimal-K backslash resistor spec was not covered by regression

- Bug: The reported input `贴片\1.24K\±1%\1/16W\0402 ROHS` was still observed as no-result in the running system even though the current local parser resolves it to a complete chip-resistor spec.
- Root cause: The prior backslash-separated resistor regression covered integer `R/K` values but did not lock decimal KΩ notation such as `1.24K`.
- Fix: Add `贴片\1.24K\±1%\1/16W\0402 ROHS` to the same regression path, proving it parses to `1240Ω`, `0402`, `±1%`, and `1/16W` and stays in resistor mode rather than generic capacitor/no-match handling.
- Verification: The focused resistor regression and release safety gate pass with protected runtime database fingerprints unchanged.

## 2026-07-09 - Exact FOJAN search displayed both spaced and compact model variants

- Bug: Searching `FRC0603J102 TS` showed both the real database row `FRC0603J102 TS` and a generated fallback row `FRC0603J102TS` in the matched part-data panel.
- Root cause: Frame merging deduplicated by raw `品牌 + 型号`. The exact-row loader and FOJAN rule fallback share the same `clean_model`, but their raw model strings differ only by spacing.
- Fix: Merge component frames by `品牌 + clean_model + 器件类型`, and rank `型号编码解析` fallback rows below real database rows so the stored original model text wins.
- Verification: The reported query now returns one FOJAN exact-normalized row, `FRC0603J102 TS`; focused regression and release safety gate pass with protected runtime database fingerprints unchanged.

## 2026-07-09 - ROHM brand hint and FOJAN default-power fallback gaps

- Bug: `ROHM` in a free-text resistor spec was not treated as a brand hint, so `贴片电阻 10K 0603 ±1% 0.25W ESR系列 ROHM` returned other brands instead of the matching ROHM ESR row.
- Root cause: The brand alias table covered several passive vendors but omitted `ROHM/罗姆/羅姆`. Separately, FOJAN FRC/FRL fallback generation required the user to explicitly enter the default power even when size, tolerance, and resistance were otherwise complete.
- Fix: Add ROHM aliases to requested-brand filtering. Let FOJAN FRC/FRL fallback use the standard power for the size when no power is specified, while still rejecting explicit mismatched power.
- Boundary: FOJAN FRM/FPM alloy series are present only as imported rows today. Full official-series generation must be implemented from source-backed datasheet naming rules, not by treating FRL as alloy or guessing model codes.
- Verification: `ROHM` ESR query now returns `ROHM / ESR03EZPF1002`; no-power FOJAN examples generate `FRC0805F9100TS` and `FRL1206FR010TS`; focused regression and release safety gate pass with protected runtime database fingerprints unchanged.

## 2026-07-12 - Local test page was offline after the workstation reboot

- Incident: `http://127.0.0.1:8520/` stopped responding because the reboot terminated the local Streamlit process; no process was listening on port 8520 afterward.
- Safety finding: The previous local Python process had reached 7.18 GB of virtual memory on a machine with 7.67 GB of physical RAM, so restarting it without a guard could repeat the resource-exhaustion incident.
- Mitigation: Restarted only the local `streamlit_app.py` entrypoint with database auto-update disabled and attached the Python process to a Windows Job Object with a 1 GB process-memory limit. No database rebuild, automated test, or application-data write was run.
- Verification: Port 8520 is listening on `127.0.0.1`, `/?bom=1` returns HTTP 200, and the restarted Python process initially uses about 62 MB of working memory.
- Follow-up: The first post-reboot login created a valid active-member token but left one Python thread in a full-CPU rerun loop. The member database remained readable, passed `PRAGMA quick_check`, and the token had a valid expiry. Restarting only the capped local Streamlit process preserved the session token and cleared the loop; the replacement process added only 0.02 CPU seconds over a three-second sample and used about 144 MB.
- BOM follow-up: A subsequent BOM run consumed one CPU core continuously for several minutes while memory stayed near 184-197 MB and the browser connection remained established. This confirms a CPU-bound single-row matching path rather than a memory-limit or database failure. The stuck run was stopped, and the capped test server was restarted with `BOM_MATCH_DEBUG=1` and isolated stdout/stderr logs so the next identical upload can identify the exact row and query path.
- Performance fix: BOM matching now bulk-prefetches exact model rows once per sheet, shares a bounded 256-entry normalized query cache across workbook sheets, tries the richest combined specifications before weak single-column fallbacks, reuses the recommendation already calculated during candidate evaluation, and avoids generating the own-brand export candidate frame twice per row. Debug mode records row start and completion timing, so a future single-row stall identifies the unresolved input immediately.
- Verification: Candidate-order/cache regressions and existing BOM export/cost regressions pass. The complete 20-test release safety gate passes under a 1 GB process-memory guard, with protected member, cost-list, and no-match fingerprints unchanged.
- Real BOM evidence: The repeated header row `MPN3 / Description / 项目` was incorrectly processed as a component and consumed 65.991 seconds. Subsequent resistor rows completed in 1.276-2.288 seconds each, proving the page was progressing but still too slow for large files.
- Follow-up fix: Detect and preserve repeated header/description rows as `已跳过` without querying the library. Before calculating cost/MOQ, restrict the candidate frame to the selected or configured business-brand groups; unrelated matched brands no longer run pricing and manufacturer-packaging enrichment.
- Follow-up verification: Header-skip and brand-prefilter regressions pass, the selected-brand cost regression remains correct, and the complete 20-test release safety gate passes with protected runtime fingerprints unchanged.
- UX finding: In the logged-out BOM flow, the member token can be created successfully and the resumed BOM match can run while the submitted login dialog remains visually busy. The prior diagnostic run confirmed row processing behind that dialog. After a local service restart, the token remains valid but the in-memory upload is gone, so an idle server plus a stale dialog does not mean matching is still running. The flow should be split into an explicit post-login restore/progress state instead of coupling login submission to synchronous BOM execution.
- UX fix: Successful login from a waiting BOM upload now records a dedicated post-login stage. The next run only displays `会员登录成功 / BOM恢复中` and performs one lightweight rerun so the login dialog closes; the following run clears the stage, confirms the cached upload was restored, and starts workbook parsing. If the cached bytes are unavailable, the page reports that login succeeded and asks for the file to be selected again instead of appearing stuck.
- Verification: Login-route and BOM resume-state regressions pass. The complete 20-test release safety gate passes under the 1 GB guard, and protected member, cost-list, and no-match fingerprints remain unchanged.

## 2026-07-14 - Yageo resistor query omitted the valid FOJAN alternative

- Bug: `100Ω;50V;±1%;1/16W;0402;RC0402FR-07100RL;无卤` showed the Yageo source row but reported that no other-brand alternative was available, even though `FOJAN(富捷) / FRC0402F1000TS` was already generated as a candidate.
- Root cause: FOJAN FRC rows had blank maximum-working-voltage and halogen-free fields. The explicit `50V` constraint therefore rejected the FOJAN candidate before result display; resistor note text such as `无卤` was also not merged into the parsed specification.
- Fix: Backfill query-time FRC maximum working voltage by official package table, mark FRC candidates as halogen-free, extract `无卤/無鹵/HALOGEN-FREE`, and apply explicit resistor special-use requirements as strict filters.
- Verification: The original full query now returns exactly one alternative match, `FOJAN(富捷) / FRC0402F1000TS / 0402 / 100Ω / ±1% / 50V / 无卤`. The focused regression passes, and the complete 20-test release safety gate passes under a 1 GB job-memory limit with protected runtime fingerprints unchanged.

## 2026-07-14 - Direct resistor specification reused an obsolete empty page result

- Bug: Searching `100Ω;50V;±1%;1/16W;0402;` directly showed zero matches even though the current resolver produced `FOJAN(富捷) / FRC0402F1000TS`. The specification table also displayed `100;50V;` as a false series name.
- Root cause: Existing Streamlit sessions could retain the pre-fix empty DataFrame because the query-result cache version had not changed. Separately, the resistor parser keeps the original specification text in the temporary `型号` field, and the display profile treated that non-model text as a model when inferring a series.
- Fix: Bump the query-result cache version so old empty frames cannot be reused. Only use `型号` for display-series inference when it passes the compact-part-number check.
- Verification: Regression coverage now requires the direct specification to parse as `0402 / 100Ω / ±1% / 1/16W / 50V`, generate `FRC0402F1000TS`, return that model, and leave the specification-table series blank. Focused regression and the complete 20-test release safety gate pass; protected runtime fingerprints remain unchanged.

## 2026-07-14 - Chinese `士/土` tolerance typo blocked resistor specification matching

- Bug: `2010 100K士1%` was reported as having only two parameters even though it represents package `2010`, resistance `100KΩ`, and tolerance `±1%`.
- Root cause: The resistor-context gate, resistance parser, and tolerance parser recognized `±1%` but did not normalize the common Chinese input/OCR variants `士1%` and `土1%`.
- Fix: Normalize `士/土` to `±` only when it directly introduces a numeric percentage and is not part of a preceding Chinese word. Apply the normalized text consistently to resistor detection, resistance extraction, and tolerance extraction; invalidate stale query-result caches.
- Verification: The original input parses as three parameters and resolves through the fast index to 66 candidates, with `FOJAN(富捷) / FRC2010F1003TS` first. Regression also covers `土1%`, full-width `士1％`, standard `±1%`, and a Chinese-word false-positive guard.

## 2026-07-14 - FOJAN FRC `RS` suffix sorted before standard `TS`

- Bug: The matched results for the reported `0402 / 1KΩ / ±1% / 1/16W / 50V` query showed `FRC0402F1001RS` before the standard `FRC0402F1001TS` because both rows were completely matched and the final tie-breaker used alphabetical model order.
- Fix: Add a FOJAN FRC model-family sort key and rank the `TS` suffix before other FRC suffixes within the same model family. Match level, component constraints, brand priority, and database rows remain unchanged.
- Verification: The real query now returns `FRC0402F1001TS` followed by `FRC0402F1001RS`; an isolated sorting regression keeps both rows and enforces that order.

## 2026-07-14 - Selecting custom BOM brands immediately started a blocking rerun

- Bug: Switching the BOM output mode to `指定品牌` immediately changed the run signature and synchronously restarted the entire workbook match. While that work or a concurrent deployment restart was in progress, the page appeared frozen at the upload area.
- Fix: Separate custom-brand configuration from execution. Switching mode or changing selected brands now only updates settings; `开始指定品牌匹配` explicitly starts the run. Automatic-brand mode keeps its existing automatic behavior, and clicking the custom start button again intentionally reruns a completed configuration.
- Verification: Regression coverage requires custom mode to stay idle until explicitly started, while automatic mode still starts on a changed signature. The selected-brand cost/export regression continues to pass.

## 2026-07-14 - BOM matching started before the successful-login dialog closed

- Bug: Uploading a BOM while logged out, then logging in, showed the successful restore message behind a disabled login dialog while synchronous BOM parsing started. The account was already authenticated, but the stale dialog made the page look stuck on login.
- Root cause: The post-login transition used consecutive server-side `st.rerun()` calls. The success run never completed normally, so Streamlit had no completed page cycle in which to remove the previous dialog before the next blocking match began.
- Fix: Finish the successful-login page with `st.stop()`, schedule a one-second Streamlit fragment refresh, and only start the full BOM run after that completed browser paint. Keep an `立即开始 BOM 匹配` button as a fallback while preserving the cached upload.
- Verification: Focused regressions require the success transition to render, schedule auto-resume, and stop without a consecutive rerun; timer and manual-start readiness are both covered.

## 2026-07-15 - Unlabeled numeric resistor values fell through the public fast index

- Bug: BOM-style text such as `0,50mW Resistor R_0201 1%` and `150,50mW Resistor R_0201 1%` identified package, power, and tolerance but missed the resistance value, then fell through to the full-dataframe path that is intentionally unavailable on the public low-memory runtime.
- Root cause: Resistance parsing required `R/K/M/Ω` notation. It did not support a plain numeric first field even when the row explicitly said `Resistor` and the next delimited field was a power value.
- Fix: Parse a non-negative leading numeric value as ohms only under the narrow structure `number + field delimiter + power`, with an explicit resistor label. Invalidate stale empty query caches. Capacitor rows, unlabeled package-only resistor rows, and unrelated numeric text remain excluded.
- Verification: The two reported forms now use the fast index and return `FRC0201F0000TS` and `FRC0201F1500TS`. Regression coverage also checks every resistor/capacitor row visible in the supplied list and the exact `NCP03WF104F05RL` thermistor token path.

## 2026-07-15 - Joyin NTC B-value tolerance was ignored during matching

- Bug: `NCP03WF104F05RL` incorrectly marked `JSNZ104F425GABXG`, `JSNZ104F425HABXG`, and `JSNZ104F425JABXG` as complete matches alongside `JSNZ104F425FABXG`.
- Root cause: The model parser decoded the first tolerance code as R25 tolerance but discarded the second tolerance code for the B value. The result table also had no separate B-value-tolerance column, so all four rows appeared to have the same `±1%` requirement.
- Fix: Decode and display `B值误差`, infer the official Murata NCP03WF B25/50 tolerance, and include B-value tolerance in thermistor match grading and sorting.
- Verification: Real-database replay keeps `JSNZ104F425FABXG` as `完全匹配`; the G/H/J B-tolerance variants are now `需确认替代` and display `±2% / ±3% / ±5%` respectively.

## 2026-07-16 - Source-brand token blocked valid cross-brand resistor alternatives

- Bug: `10KΩ;75V;±1%;1/10W;0603;FENGHUA;RS-03K1002FT;无卤` found the Fenghua source row but reported no other-brand alternative, even though `FOJAN(富捷) / FRC0603F1002TS` satisfied every requested parameter.
- Root cause: The brand token beside an exact source part number was reused as an explicit output-brand filter. The candidate scope was reduced to Fenghua before cross-brand matching, so the valid FOJAN row never reached grading.
- Fix: Exact-part and embedded-model-token lookups now retain the detected brand as the source brand but clear the requested-brand output filter. Direct specification searches such as `富捷 0603 10K 1%` remain restricted to the requested brand.
- Verification: Exact real-data replay returns `FOJAN(富捷) / FRC0603F1002TS / 完全匹配`; focused regression also confirms that explicit specification brand filters remain active.

## 2026-07-16 - BOM output exposed nonstandard FOJAN FRC suffix formatting

- Bug: BOM matching displayed and exported F-tolerance models such as `FRC0201F1003 TS` with a space before `TS`; one library row also produced `FRC0402F1001RS` instead of the standard `FRC0402F1001TS`.
- Root cause: Matching compared compact model keys but preserved the original library display string in recommendation and BOM export fields. Six F-tolerance source rows contained a space, and one F plus one J row used the obsolete `RS` suffix.
- Fix: Canonicalize FOJAN FRC output by tolerance family without altering the source BOM or runtime database: F uses a four-character value code immediately followed by `TS`, J uses a three-character value code followed by ` TS`, and P remains compact. Obsolete FRC `RS` display suffixes are emitted as `TS`; model validation now enforces the correct code length.
- Verification: Full replay of all 37 rows in `星际需求0715.xlsx` with the selected FOJAN brand returns a nonblank FOJAN model for every row and zero format anomalies. The two reported cases now output `FRC0402F1001TS` and `FRC0201F1003TS`.

## 2026-07-16 - Structured source descriptions lost explicit resistor parameters

- Bug: Several semicolon-delimited source descriptions, including Fenghua `0402 / 1KΩ / ±1%`, `0402 / 10KΩ / ±5%`, and `0402 / 510Ω / ±5%`, failed to return valid FOJAN alternatives. `1206 / 0.05Ω / ±1% / 1/4W / 无卤` also excluded the existing `FRL1206FR050TS` row.
- Root cause: Embedded source-model decoding replaced the explicitly entered tolerance with an incorrect model-derived value. FRL rows retained `低阻值` as their only special-use token, so the strict `无卤` requirement rejected them even though the FOJAN FRL specification is halogen-free. Equivalent FOJAN rows from multiple component-type sources could also survive as duplicate display results.
- Fix: Preserve explicit query size, value, tolerance, power, voltage, and special-use fields when an embedded source model is resolved; treat strong embedded part tokens as source metadata rather than brand filters; merge `无卤` into FOJAN FRC/FRL query candidates; and deduplicate results by canonical brand/model. Cybermax `CMBH` and `CMLH` prefixes now route to ferrite-bead and power-inductor parsing instead of resistor parsing.
- Verification: Batch replay returns a FOJAN model for all 22 resistor descriptions in the supplied image, including `FRL1206FR050TS`; direct brand-only searches remain restricted. Focused regressions cover explicit-parameter precedence, FRL halogen-free matching, canonical deduplication, and Cybermax family classification.

## 2026-07-16 - Legacy FOJAN suffix rows duplicated after display normalization

- Bug: Searching `0402 / 1/16W / 1KΩ / ±1%` could display `FRC0402F1001TS` twice.
- Root cause: The library contains both legacy `FRC0402F1001RS` and standard `FRC0402F1001TS` rows. An older formal runtime normalized both labels to the standard `TS` form after result matching, making two distinct source rows look identical.
- Fix: Keep canonical FOJAN deduplication in the matching layer and repeat the same canonical brand/model deduplication immediately before both search-result tables are rendered. Raise the query cache version so existing sessions cannot reuse stale duplicate results.
- Verification: A full FRC library audit found only two canonical legacy pairs (`FRC0402F1001` and `FRC0402J563`); both now render once. Additional `0603 / 10KΩ / ±1%` and `0805 / 330Ω / ±5%` checks report zero duplicate display keys.

## 2026-07-16 - Search-result iframe left a large blank area above the footer

- Bug: After the last visible search-result row, the page could retain several hundred pixels of empty space before the footer even though the table already used its own internal scrollbar.
- Root cause: The table height cap used `52vh` inside a Streamlit iframe, where viewport units refer to the iframe itself. The iframe then reported `documentElement.scrollHeight`, which is never smaller than its current viewport, so an oversized initial iframe could not shrink to the actual result-card height.
- Fix: Use fixed content caps for normal and BOM result tables, show about eight normal result rows before internal scrolling, and report the bottom edge of actual body content to Streamlit instead of the iframe viewport height. Exact-part match cards use the same bounded-height behavior.
- Verification: The focused regression confirms no `52vh` or viewport `scrollHeight` sizing remains. A headless browser check with 20 rows measured a 440px scrollable table and a 460px result card inside a 900px viewport, allowing the host iframe to collapse to the real content boundary.

## 2026-07-16 - Cost maintenance supported only whole-list replacement

- Gap: A manufacturer could quote one model separately, but the backend accepted only complete Excel/CSV cost lists. Adding one quote required rebuilding and re-uploading the whole list, and switching lists could discard an ad hoc change.
- Design: Add an independent exact-model cost layer keyed by canonical brand and model. Active single-item records take priority over the current whole list, remain available when the whole list changes, and fall back to the current list when disabled.
- Fix: Added additive `cost_price_manual_items` storage with create/update/disable history, operator and quote notes; added a `单笔成本` admin tab; included single-item records in remote cost snapshots, search enrichment, BOM matching, and Excel export. Records are disabled rather than physically deleted.
- Verification: Isolated database tests cover use without a whole list, override priority, list replacement, disable fallback, re-enable, BOM export, and remote snapshot restoration. A browser workflow confirmed create, edit preload, disable control, and the unchanged whole-list upload tab.

## 2026-07-16 - Incomplete NTC specifications were labeled as complete matches

- Bug: `Thermistor NTC 10K OHM 240mW 1% 0402 SMD` marked many Joyin models as `完全匹配` even though the query omitted B value, B condition, and B tolerance. Candidate power was also misread from the `1.7mW/℃` dissipation constant instead of the official `Max Power=170mW`.
- Root cause: Thermistor completeness required only size, R25, and R25 tolerance; blank B fields passed matching checks. Generic power extraction accepted the first mW token in the source notes.
- Fix: Require size, R25, R25 tolerance, B value, B condition, and B tolerance before an NTC candidate can be `完全匹配`. Parse only labeled thermistor maximum power, use the official Joyin size rule as a low-memory public fallback, and treat a lower maximum power as a conflict.
- Verification: The reported query keeps the candidates visible but marks all Joyin 0402 rows `需确认替代` and reports `240mW` required versus `170mW` available. A complete `B25/50=3370K ±1%` query marks only the F-code Joyin model complete; G/H/J remain confirmation-required. The 23-test release safety gate passed with protected runtime-data fingerprints unchanged.

## 2026-07-16 - Old database hits hid new timing product-number rows

- Bug: Epson official crystal and oscillator products existed in the prepared/search caches, but a specification such as `32.768kHz / 3215 / 7pF / ±20ppm` returned only old series-level rows or no usable product number.
- Root cause: Candidate loading used `components.db` first and queried the search sidecar only when the entire database result was empty. A partial old database hit therefore suppressed all missing product-number candidates from the sidecar. Legacy timing tolerances stored as `20PPM` also failed comparison after query normalization produced `20`.
- Fix: Always merge database and sidecar candidate rows before exact brand/model filtering and canonical deduplication. Timing tolerance comparison now normalizes both candidate and query values by removing the `ppm` suffix.
- Verification: The crystal specification now returns `Q13FC13500002`, `X1A0001410001`, and `X1A0001610003` as complete Epson matches. A 25MHz oscillator specification returns five complete Epson matches, and an Abracon exact-model query returns Epson alternatives. A regression test covers partial database plus sidecar merging; the full 23-test safety gate passes with protected databases unchanged.

## 2026-07-17 - Timing library covered Epson but not the other official brands

- Gap: Crystal and oscillator specification matching had detailed Epson product numbers, while most other manufacturers were represented by only a few legacy seed rows or broad series names.
- Data integration: Added 29,075 official timing rows from Abracon, Kyocera, NDK, KDS, TXC, Murata, and SiTime sources. The official feeds also include acquired or catalog brands such as Fox, Ecliptek, NEL, ILSI, MMD, and AEL. The resulting library contains 23,726 exact product numbers, 4,011 NDK model/frequency/specification combinations, 968 official product-number templates, 266 official series ranges, and 104 configurable SiTime series.
- Matching fix: Exact frequency rows, frequency ranges, discrete frequency options, tolerance options, voltage options, and load-capacitance options can now enter the fast timing search. Series, templates, and configurable products are labeled `需确认配置` instead of `完全匹配`.
- Detail fix: Crystal and oscillator result tables now expose data granularity, frequency ranges/options, tolerance options, voltage/load options, storage temperature, temperature characteristic, overtone, AEC grade, official specification number, package quantity, long-term stability, and phase-noise fields when available.
- Legacy cleanup: Canonicalize Epson, Kyocera, KDS, Murata, NDK, TXC, Abracon, and SiTime aliases for search and deduplication. When an old seed row and a richer official row share the same product number, the official row wins.
- Verification: The generated source has 29,075 rows, 13 normalized brand labels, zero blank models, and zero duplicate brand/model pairs. Real-cache searches return 53 candidates for `16MHz / 3225 / ±20ppm`, five exact part-level matches for `40MHz / 2016 / 8pF / ±20ppm`, and 19 exact oscillator matches for `25MHz / 3225 / 3.3V / CMOS / ±25ppm`.

## 2026-07-17 - Epson timing details were stored but not enforced

- Bug: Epson's official product feed exposed temperature-range tolerance, 25C aging, turnover temperature, parabolic coefficient, and overtone order, but those fields were not fully imported or compared. Sparse crystal and oscillator searches could therefore be labeled complete even when important timing parameters were absent or conflicting.
- Root cause: The Epson synchronizer imported only the common frequency, package, nominal tolerance, voltage, and load fields. Timing matching treated those common fields as sufficient for a complete result and did not distinguish the primary frequency tolerance from labeled temperature-characteristic and aging ppm values.
- Fix: Import and display `frequencyTolTempRange`, `frequencyAging`/`25CAging`, `turnoverTemp`, `parabolicCoef`, and `overtoneOrder`. Parse the same requirements from user input, reject known detailed conflicts, and reserve `完全匹配` for queries and candidates that contain the required operating-temperature, aging, and crystal-family detail fields. Exact product-number searches remain exact.
- Cache safety: Epson refresh now combines the 29,075-row multi-brand official timing source before rebuilding the prepared cache and search sidecar, so refreshing Epson can no longer hide Abracon, Kyocera, NDK, KDS, TXC, Murata, SiTime, or acquired-brand rows.
- Verification: The Epson source contains 6,060 unique product numbers with aging populated on all rows; all 1,411 MHz crystal rows have temperature characteristic and overtone, and all 75 kHz crystal rows have turnover and parabolic data. Real-cache replays return exact Epson matches for full MHz-crystal, 32.768kHz-crystal, and oscillator specifications, while the corresponding sparse query is correctly labeled `部分参数匹配`.

## 2026-07-17 - Epson RTC model RX8025T-UC was not recognized

- Bug: Entering the exact Epson model `RX8025T-UC` returned `无法识别输入内容`, even though the part is an RTC module with a built-in 32.768kHz compensated crystal.
- Root cause: The Epson synchronizer covered crystal units and oscillators but not Epson's RTC feed. Exact-model lookup also scanned the 1.5GB component database before consulting the fast search sidecar, and the reverse-lookup field list omitted RTC-specific details.
- Fix: Import Epson's official `rtc.json` feed, retain official product-number rows plus confirmation-required series aliases, and add channel-confirmed China-market `RX8025T-UB/UC` rows with explicit source status. Add `实时时钟模块` as a distinct component type, expose RTC fields, query the fast index before the large database, and preserve RTC/crystal detail fields during exact-model reverse lookup.
- Verification: The generated Epson source contains 6,158 rows including 66 official RTC product numbers and the two RX8025T variants. Both prepared and SQLite search caches contain `RX8025T-UC`. The real exact lookup returns one Epson RTC row, resolves as `料号` in 0.032 seconds after candidate loading, and exposes I²C, 1.8~5.5V timekeeping voltage, and 0.8µA typical backup current. All 16 Epson timing integration tests pass.

## 2026-07-18 - Epson aliases and partial timing matches lacked actionable confirmation details

- Bug: `FC2012AN`, historic Epson TSX-3225 number `X1E000021013900`, and compound input `SG2520HGN_X1G0058910005` were not consistently resolved as exact source parts. Partial crystal/oscillator/RTC alternatives also did not explain which missing or conflicting parameters required customer confirmation, and the BOM download omitted that explanation.
- Root cause: Compound model tokens were not split and ranked toward the official product number; two channel-confirmed TSX-3225 aliases and the FC2012AN series alias were absent; generic model parsing could run before the richer exact database row; and result grading had no reusable confirmation-detail field.
- Fix: Resolve compound Epson inputs by exact product number, add the TSX-3225 historic/base aliases and the FC2012AN official series alias, prefer exact database timing rows, preserve ESR/aging/overtone/stability/noise fields, and add `待确认参数` to search results, BOM previews, and downloaded Excel. Partial timing rows now list source gaps, candidate gaps, known differences, and concrete customer/engineering checks.
- Verification: RX8025T-UC/UB correctly report no cross-brand RTC replacement; FC2012AN returns seven NDK/TXC partial candidates with CL/ESR/drive/aging/turnover checks; X1E000021013900 resolves to TSX-3225 but rejects known Abracon/Kyocera conflicts; and SG2520HGN_X1G0058910005 resolves to the exact 100MHz HCSL Epson PN and returns Abracon partial candidates with output, pin, timing-edge, and jitter/noise checks. Focused timing and BOM-export regressions pass.

## 2026-07-18 - Confirmation details duplicated the purpose of remark one

- Bug: Search results and BOM outputs added a wide standalone `待确认参数` column while the existing `备注1` field remained empty, increasing horizontal scrolling and splitting related notes across two columns.
- Root cause: The timing confirmation generator wrote to a new result-only field instead of the established component remark field. BOM export appended that field without checking whether the uploaded workbook already contained `备注1`.
- Fix: Merge generated confirmation details into `备注1`, preserve and append to existing candidate or customer remarks, suppress duplicate text on repeated rendering, and remove the standalone field from search, BOM preview, and Excel export. Existing workbook `备注1` cells are updated in place rather than duplicated.
- Verification: 28 focused timing/BOM tests pass, including existing-note preservation, idempotent search rendering, DataFrame export, and styled workbook export with a single `备注1` column.

## 2026-07-18 - BOM preview height reduction clipped the table bottom

- Bug: After reducing result-page blank space, the BOM original-content preview could be cut off at its lower iframe boundary, hiding the final visible row and the bottom scrolling area.
- Root cause: The preview reused the BOM result wrapper's 560px internal cap, while its host iframe estimator allowed at most 320px. When browser-side height reporting did not expand the iframe in time, the larger inner wrapper was clipped.
- Fix: Give BOM previews a dedicated 440px scroll wrapper and a 260px compact OCR wrapper. Raise the initial iframe estimate to include the header, visible rows, card border, and scrollbar while retaining actual-content shrink reporting for short tables.
- Verification: The focused iframe regression passes. A 1540px-wide browser render with 20 rows measured the preview wrapper at 440px, its card bottom at 450px, and the host estimate at 460px, leaving the complete lower boundary visible without restoring a large blank section.

## 2026-07-18 - BOM candidate explanations were detached from their matched brands

- Bug: A BOM row could export multiple matched brands and models, but `匹配说明` and `备注1` were stored once at row level. The second and later candidates therefore had no identifiable explanation or remark, and the shared text could describe only the primary recommendation.
- Root cause: Candidate export slots contained brand, model, cost, update time, MOQ, and lead time only. Recommendation text and confirmation details were appended before all candidate slots from the row-level recommendation.
- Fix: Generate explanation and confirmation remark from each selected candidate row, store them in that candidate's export slot, and output each complete group in this order: brand, model, cost, update time, MOQ, lead time, explanation, remark. Customer-provided source `备注1` remains unchanged; candidate notes use `匹配备注`, `匹配备注2`, and later numbered columns.
- Verification: Focused DataFrame and styled-workbook tests cover two brands with different explanations and remarks, group adjacency, source-note preservation, and the downloaded Excel column order.

## 2026-07-18 - Special resistor requirements returned ordinary or partially qualified series

- Bug: Searches for automotive, anti-sulfur, high-voltage, high-power, surge, and combined special resistor requirements either mixed in ordinary thick-film models or appeared to have very little series coverage.
- Root cause: The library already held hundreds of thousands of special resistor rows, but the shared special-use parser recognized only a narrow subset. Exact resistor matching filtered size/value/tolerance/power without enforcing special use, and combined requirements used any-token intersection instead of requiring all requested tags.
- Fix: Normalize the full resistor requirement vocabulary, apply special use as a hard constraint in scoped, exact, and partial matching, and require the requested tag set to be a subset of each candidate's tags. Add 48 officially identified FOJAN series profiles without synthesizing unverified part-number ranges.
- Verification: A focused regression covers parsing, combined-tag semantics, ordinary-row rejection, and representative FOJAN profiles. Real-library replays found valid automotive, anti-sulfur, high-voltage, high-power, surge, and automotive-plus-anti-sulfur alternatives with no tag violations. No runtime database or cache file was changed.

## 2026-07-22 - BOM upload started the default match before output-brand confirmation

- Bug: Uploading a BOM immediately started `主营品牌自动匹配`. Choosing `指定品牌` afterward required a second full workbook run; restoring an upload after member login triggered the same premature automatic run.
- Root cause: `should_start_bom_matching` treated every new workbook/settings signature as an automatic-mode start signal. Only the custom-brand branch required a button click, and its multiselect also preselected a brand.
- Fix: Treat a button click as the only valid match-start signal for both modes. Leave the mode unselected for a new workbook, require at least one custom brand, preserve existing results while settings are only being edited, and clear/replace them only after an explicit new start.
- Verification: Unit coverage confirms automatic and custom modes stay idle without a click and can rerun only after a click. An isolated Playwright upload confirms the page remains at `BOM 文件读取完成` / 0%, automatic mode exposes a start button without running, and custom mode has no default brand and keeps its start button disabled until selection.

## 2026-07-22 - Explicit multi-brand common-part searches lost valid alternatives

- Bug: Common resistor and MLCC inputs ending in lists such as `品牌:厚声/翔胜/华科/国巨` resolved the embedded source model but reported no other-brand alternatives, even though electrically compatible rows existed in the library.
- Root cause: The brand parser collapsed a slash-separated list to one inferred brand, and the matching pipeline treated `无卤`/`无铅` as hard special-use constraints. Most candidate rows have complete electrical parameters but no explicit compliance metadata, so they were discarded before recommendation grading.
- Fix: Preserve slash-separated brand text as source metadata in automatic mode, map `翔胜` to the existing `VO(翔胜)` brand, and apply a union whitelist only through the explicit target-brand mode or a `指定品牌:` directive. Treat missing `无卤`/`无铅` metadata as a confirmation requirement instead of proof of incompatibility. Functional requirements such as automotive, anti-sulfur, high-voltage, high-power, industrial, soft-termination, and resonant remain hard constraints.
- Verification: The 12 reported inputs were replayed against the real candidate library and now retain cross-brand electrical alternatives. Representative resistor rows include Walsin, Yageo, and VO; the 0603 X7R 220pF input includes Yageo and CCTC alternatives. Rows without explicit halogen-free evidence are labeled `需确认替代` with an original-datasheet warning. Focused resistor, MLCC, and special-use regressions pass.

## 2026-07-22 - Brand text could not distinguish source metadata from target filtering

- Bug: A pasted customer BOM line and a manually entered target-brand request could both look like `规格 + 品牌`. Inferring intent from the brand word alone could either hide valid cross-brand alternatives or ignore a requested brand restriction.
- Root cause: Search parsing used every recognized brand token as a hard candidate filter. There was no independent search-scope control, so source metadata and output intent shared one field.
- Fix: Add an explicit `自动匹配其他品牌 / 指定品牌` search control. Automatic mode treats brands in pasted text as source metadata and does not narrow the candidate pool. Custom mode requires selection of 1-5 target brands and applies a union whitelist. A per-line `指定品牌:` / `目标品牌:` / `输出品牌:` directive remains available for explicit text-driven filtering, and pending login searches retain their selected scope.
- Verification: Regression coverage uses identical `富捷 0402 1% 10K` input in both modes: automatic mode retains cross-brand candidates, while custom mode returns only FOJAN. Multi-brand custom and line-directive filters pass. An isolated Streamlit browser run confirms the default mode, custom selector rendering, and selection requirement without using production databases.

## 2026-07-22 - Specified-brand BOM rows reported recommendations without output models

- Bug: In specified-brand BOM matching, rows could display `可推荐` or `需确认` even when every selected-brand model slot was blank. A workbook containing both `国巨型号` and a partially populated `PDC料号` column also auto-selected the PDC result column as the source model, producing a false diode classification and one parse failure.
- Root cause: Recommendation status was calculated from the all-brand candidate frame before selected-brand export filtering, and it was never reconciled after the selected-brand slots were built. Model-column scoring compared only nonblank samples, so a sparse `料号` result column narrowly outranked a complete `型号` source column.
- Fix: Reconcile status after export-slot generation and require at least one nonblank selected-brand model before retaining `可推荐`, `需确认`, or conflict output. Blank selected-brand results now become `无匹配`, clear generic recommendation data, and explain that the manufacturer may have no equivalent or the database may lack it. Model-column scoring now includes whole-column completeness.
- Verification: The reported 250-row workbook now maps `国巨型号` as the source model and all 250 rows parse as MLCC rather than 249 MLCC plus one false diode. A 13-row real-file sample covering populated/blank PDC models and high-voltage/automotive rows returns nine recommendations and four no-matches with zero blank-model recommendations and zero parse failures. Focused regression coverage passes.
## 2026-07-22 - Search result tables clipped the last visible row

- Symptom: multi-line searches showed a partial final result row above the horizontal scrollbar, and the next result card started too close to the unfinished frame.
- Root cause: the result wrapper used a fixed `max-height` unrelated to rendered row heights, while iframe auto-sizing reserved only two pixels below the card.
- Fix: align each scroll viewport to the measured header plus complete visible rows and scrollbar height, clip content to the rounded card, and reserve 16 pixels below each iframe.
- Regression: `test_02e_result_iframe_shrinks_to_actual_content` now checks the row-alignment and bottom-reserve script contract.
