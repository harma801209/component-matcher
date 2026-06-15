# Issue Ledger

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
