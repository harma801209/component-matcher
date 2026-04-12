# Operation Log

This file is the shared handoff record for work in `C:\Users\zjh\Desktop\data`.

## Update Rules

- Append a new entry whenever a task is completed or a meaningful investigation checkpoint is reached.
- Include at least: receive time, request/problem, investigation, fix/action, verification, other issues, and next handoff notes.
- Mark entries as `direct` when based on the current conversation and `inferred` when reconstructed from filesystem evidence.
- Keep statements factual. If a conclusion is inferred from timestamps or diffs, say so explicitly.

## Entry Template

### YYYY-MM-DD HH:MM [direct|inferred] Short title

- Received / problem:
- Investigation:
- Fix / action:
- Verification:
- Other issues:
- Handoff notes:

## Entries

### 2026-04-12 02:25 [direct] 公开版修复 Community Cloud 沿用旧 bundle 数据的问题

- Received / problem: 用户在 [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/) 实测 `CM13093CT-102` 仍显示“无法识别输入内容”，说明上一轮公开版发布后，线上运行态没有真正吃到新的正式数据库与搜索缓存。
- Investigation: 复核 [streamlit_app.py](C:/Users/zjh/Desktop/data/streamlit_app.py)、[component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 与 [cloudflare-pages-proxy/dist/_worker.js](C:/Users/zjh/Desktop/data/cloudflare-pages-proxy/dist/_worker.js)。确认 `pages.dev` 代理层仍正常指向 `fruition-componentmatche.streamlit.app`，而正式问题出在 `ensure_streamlit_cloud_data_bundle()` 和 `ensure_component_data_ready()`：旧逻辑只检查 `components.db / components_search.sqlite / prepared parquet` 是否“存在且非空”，不会判断这些文件是不是旧部署遗留版本，因此 Streamlit Community Cloud 的持久化文件系统会继续沿用旧库。搜索页在 `搜索` 场景下还只优先刷新搜索侧包，不保证把主 `components.db` 一起更新。
- Fix / action: 在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 新增 `streamlit_cloud_bundle.manifest.json` 与运行时状态文件 `cache/streamlit_cloud_bundle_state.json` 的比对逻辑，加入 `load_streamlit_cloud_bundle_manifest()`、`get_streamlit_cloud_bundle_signature()`、`load_streamlit_cloud_bundle_state()`、`save_streamlit_cloud_bundle_state()`、`streamlit_cloud_bundle_refresh_needed()`。正式运行态现在只要检测到 bundle manifest 已变化，就会强制重解当前需要的 bundle 成员，而不是只看文件在不在。另补充 `is_streamlit_cloud_runtime()`，即使未显式设置公开模式环境变量，只要运行目录位于 Community Cloud 常见路径，也会启用这套刷新判断。最后把 `ensure_component_data_ready()` 改为：一旦判断 bundle 已更新，就优先刷新整套 `DB + 搜索库 + prepared cache`，而不再只刷搜索侧包。
- Verification: `python -m py_compile component_matcher.py streamlit_app.py sync_local_and_public.py build_streamlit_cloud_bundle.py` 通过；另外做了最小模拟测试：在临时目录中先放一个旧目标文件、再提供新 zip bundle 与新 manifest，`streamlit_cloud_bundle_refresh_needed()` 返回 `True`，调用 `ensure_streamlit_cloud_data_bundle()` 后目标文件被成功替换为新 bundle 内容，随后刷新判定恢复为 `False`，并写入新的 `streamlit_cloud_bundle_state.json`。
- Other issues: 这条修复主要解决“正式线上实例不更新”的问题，不直接改变匹配规则本身；仍需重新发布一次公开版，等 Community Cloud 重启后再确认 `CM13093CT-102` 的线上行为是否恢复为精确料号识别。
- Handoff notes: 下一步应重新执行公开版发布流程，并优先复测 `CM13093CT-102`。若复测仍异常，再继续查 Streamlit Community Cloud 实际运行环境变量与持久化目录状态。

### 2026-04-12 01:58 [direct] 公开版 CM1309 共模电感系列与温度显示修正

- Received / problem: 用户明确约定“公开版/正式版”指 [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)，本轮要求继续只修公开版源码，不动测试版；同时 `CM13093CT-102` 这类公开版精确料号在本地正式链路里虽已入库，但仍存在系列名不统一、错误 `尺寸（inch）` 残留、工作温度显示只剩上限的问题。
- Investigation: 复核了 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py)、[build_inductor_official_sources.py](C:/Users/zjh/Desktop/data/build_inductor_official_sources.py)、[Inductor/official_inductor_expansion.csv](C:/Users/zjh/Desktop/data/Inductor/official_inductor_expansion.csv) 与 [components.db](C:/Users/zjh/Desktop/data/components.db)。确认 `CM1309` 家族四颗料号的数据本体已经存在，但源文件与展示层仍混有旧网页抓取残留，表现为 `系列=CM13093CT-242` 一类错误值、`尺寸（inch）=242/412/872/0102`、以及 `-40℃~+125℃` 在展示时被压缩成单独 `125℃`。
- Fix / action: 在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 修正 `working_temperature_bounds()`，允许温度范围两端中间夹带 `C/℃` 仍能正确解析；同时在 `ensure_component_display_columns()` 中为 Bourns `CM1309` 共模电感家族加了显示层兜底归一化，统一 `系列=CM1309`、`系列说明=Bourns CM1309 共模电感系列`、`安装方式=THT`、`封装代码=CM1309`。在 [build_inductor_official_sources.py](C:/Users/zjh/Desktop/data/build_inductor_official_sources.py) 新增 `canonicalize_bourns_cm1309_rows()`，在官方库生成阶段就把该家族的 `系列 / 系列说明 / 尺寸（inch） / 封装代码 / 工作温度` 清理正确，然后重建 [Inductor/official_inductor_expansion.csv](C:/Users/zjh/Desktop/data/Inductor/official_inductor_expansion.csv)。之后用 [sync_inductor_official_to_db.py](C:/Users/zjh/Desktop/data/sync_inductor_official_to_db.py) 只对 `CM13090CT-242 / CM13091CT-872 / CM13092CT-412 / CM13093CT-102` 四条公开版正式数据做了定向回写，并同步刷新 [cache/components_search.sqlite](C:/Users/zjh/Desktop/data/cache/components_search.sqlite) 与 [cache/components_prepared_v5.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared_v5.parquet)。
- Verification: `python -m py_compile component_matcher.py build_inductor_official_sources.py sync_inductor_official_to_db.py component_matcher_build.py` 通过；重建脚本输出 `Wrote 438 rows`；定向回写结果 `deleted=4 inserted=4 search_refreshed=True prepared_refreshed=True`。随后再次读取正式库与资料卡，四颗 `CM1309` 料号均显示 `器件类别=共模电感（Common Mode Choke）`、`系列=CM1309`、`尺寸（inch）=` 空白、`尺寸（mm）=13 x 16 x 9.2 mm`、对应 `电感值 / 电感单位 / 额定电流 / DCR / 工作温度 / 安装方式=THT`；本地公开版入口 [http://127.0.0.1:8511](http://127.0.0.1:8511) 返回 `HTTP 200`。
- Other issues: 本轮仍未把更改部署到 [https://fruition-component.pages.dev/](https://fruition-component.pages.dev/)，因此线上公开版此刻不应假定已同步这些修正。另一个尚未继续深挖的问题是官方电感导入链路在全量同步时曾出现过个别字段被旧值覆盖的迹象，本轮通过“重建源文件 + 定向回写子集”规避了该风险。
- Handoff notes: 如果下一轮继续公开版，请先以用户新口径区分“公开版/正式版”和“测试版”，再决定是否把本地公开版修正部署到 `pages.dev`。如需继续扩大官方库修正范围，可沿用这次的“源文件规范化 + 子集回写 + 子集刷新缓存”流程。

### 2026-03-22 16:13 [inferred] `component_matcher.py` updated for ceramic-capacitor classification

- Received / problem: Passive component type classification was being refined, with strong evidence that `Y5P` or leaded ceramic-capacitor text was being misrouted as `MLCC`.
- Investigation: Compared the current [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) against [backup copy](C:/Users/zjh/Desktop/data/backup/project_backup_20260322_020449/component_matcher.py) and checked recent backup folder names such as `pre_y5p_fix` and `pre_ceramic_fix`.
- Fix / action: Added a leaded-ceramic context detector and threaded that detection into type hinting, inferred component-type selection, and result-row output logic.
- Verification: Filesystem diff clearly shows new logic around leaded ceramic detection and additional type-routing branches in the current matcher.
- Other issues: This entry is inferred from file timestamps and diffs, not from direct visibility into the other task frame's conversation.
- Handoff notes: If capacitor classification still looks wrong, start from `looks_like_leaded_ceramic_context`, `detect_component_type_hint`, and the inferred-type writeback path in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py).

### 2026-03-22 23:33 [inferred] Manual MLCC spreadsheet inspection occurred

- Received / problem: Someone likely reviewed MLCC source data manually after the matcher changes.
- Investigation: Found [Capacitor/~$MLCC.xlsx](C:/Users/zjh/Desktop/data/Capacitor/~$MLCC.xlsx), which is an Excel lock file usually created while the workbook is open.
- Fix / action: No code change is proven here; this is logged as a manual inspection checkpoint.
- Verification: The temporary lock file timestamp is `2026-03-22 23:33`.
- Other issues: This only proves the workbook was open, not what edits were made.
- Handoff notes: If data quality is still in question, inspect [Capacitor](C:/Users/zjh/Desktop/data/Capacitor) and compare workbook contents with [components.db](C:/Users/zjh/Desktop/data/components.db).

### 2026-03-23 01:17 [inferred] MLCC database audit script created

- Received / problem: The next visible step after the matcher changes was checking data completeness rather than adding new parsing behavior.
- Investigation: Read [tmp_mlcc_audit.py](C:/Users/zjh/Desktop/data/tmp_mlcc_audit.py), which connects to [components.db](C:/Users/zjh/Desktop/data/components.db) and audits missing values in key MLCC fields such as size, dielectric, capacitance, tolerance, and voltage.
- Fix / action: Created a one-off audit script to count missing values, surface brands with missing key fields, and print sample incomplete rows.
- Verification: The script content directly shows SQL readback plus missing-field analysis logic.
- Other issues: I cannot confirm from the filesystem alone whether the script was executed successfully or whether any remediation already followed.
- Handoff notes: Current visible status suggests the work had reached a verification and data-audit stage, not just rule editing.

### 2026-03-23 14:08 [direct] Shared handoff logging established

- Received / problem: User asked for a persistent operation record in `data` so any future task frame can quickly understand progress, problems investigated, fixes made, and unresolved issues.
- Investigation: Scanned recent file changes in [data](C:/Users/zjh/Desktop/data), reviewed [tmp_mlcc_audit.py](C:/Users/zjh/Desktop/data/tmp_mlcc_audit.py), [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py), and recent [backup](C:/Users/zjh/Desktop/data/backup) folders to reconstruct the latest visible task progress.
- Fix / action: Created this shared log file and documented the latest confirmed and inferred checkpoints. Also prepared a workflow rule so future engineering-task completions update this record.
- Verification: File created at [operation_log.md](C:/Users/zjh/Desktop/data/operation_log.md); the related workflow skill was updated and revalidated after the rule change.
- Other issues: `git` is unavailable in the current environment, so change detection relied on timestamps, file contents, and backup diffs instead of Git history.
- Handoff notes: Future task frames should read this file first, then inspect [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and [tmp_mlcc_audit.py](C:/Users/zjh/Desktop/data/tmp_mlcc_audit.py) for the most recent visible technical state.

### 2026-03-23 14:47 [direct] Moved the BOM export button toward the result table's lower-right area

- Received / problem: User asked to move the `Download BOM matched Excel` button from the lower-left page area to the lower-right area under the BOM result table.
- Investigation: Located the BOM export block in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py), then checked the result-table height calculation and found the BOM iframe was using an oversized generic height estimate that could leave a large blank area below the table.
- Fix / action: Added a compact iframe-height mode for BOM result tables and changed the export button layout to render inside a narrow right-side column with `use_container_width=True`, so the button sits under the table near the right edge.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` completed successfully after the change.
- Other issues: I did not launch the Streamlit UI in this pass, so the visual result is based on code-path validation and layout reasoning rather than an interactive screenshot comparison.
- Handoff notes: If the button still feels too low or too far right, adjust the BOM compact height values in `estimate_result_table_iframe_height(..., compact=True)` or tweak the export column ratio near the BOM result render block in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py).

### 2026-03-23 16:00 [direct] Tightened varistor parsing and split leaded vs SMD varistor types

- Received / problem: User reported that several BOM rows were correctly recognized as varistors, but the parser still labeled them too loosely as one generic varistor type instead of distinguishing leaded forms from SMD forms. The concrete clues called out were patterns like `P7.5`, trailing `10mm`, and part text such as `10D561K`, which should bias toward leaded varistors.
- Investigation: Traced the varistor parsing and matching path in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py), including `detect_resistor_subtype_hint`, `parse_varistor_spec_query`, inferred type resolution, and the BOM match scoping logic. Found that the code already extracted disc-size and pitch clues for varistors, but still wrote only the generic varistor type and did not treat `P7.5` as pitch.
- Fix / action: Added `VARISTOR_COMPONENT_TYPES`, introduced `looks_like_smd_varistor_context` and `looks_like_leaded_varistor_context`, extended pitch parsing to recognize `P7.5`, updated varistor parsing to emit the refined type, and changed match scoping so varistor-family queries remain compatible with generic database rows. Updated display and detail builders so the new subtype names flow through BOM results and matched-row detail text.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. A targeted AST-based helper test confirmed the new logic classifies these sample inputs as intended: `Varistor : 470V +/-10%,0.4W,HEL10D471KJ,P7.5` -> leaded varistor; `10D561K ... 10mm` -> leaded varistor; `14V 0603` in SMD-varistor context -> SMD varistor.
- Other issues: I did not run the full Streamlit UI end-to-end in this pass because importing the app module executes heavy top-level page logic and database refresh steps. Validation for this task was therefore syntax-level plus targeted function-path testing rather than a full browser screenshot check.
- Handoff notes: If future varistor rows still misclassify, start with `looks_like_smd_varistor_context`, `looks_like_leaded_varistor_context`, `extract_pitch_from_text`, and `parse_varistor_spec_query` in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py). If matching starts missing obvious varistor candidates, inspect the family-compatibility filter in the `scope_search_dataframe` varistor branch.

### 2026-03-23 16:05 [direct] Normalized the shared handoff log after the varistor follow-up

- Received / problem: The shared log contained mojibake in the latest entries and one malformed file path, which would make future handoff reads less reliable.
- Investigation: Re-read [operation_log.md](C:/Users/zjh/Desktop/data/operation_log.md) and cross-checked the touched locations in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py).
- Fix / action: Rewrote the shared log in clean wording, preserved the historical entries, and corrected the malformed path in the latest varistor note.
- Verification: The log now points cleanly to the current matcher file and describes the button-layout and varistor-subtype work without corrupted text.
- Other issues: This cleanup does not change runtime behavior; it only improves cross-task handoff quality.
- Handoff notes: Future task frames can rely on this file again without needing to reconstruct the recent work from shell output.

### 2026-03-23 21:26 [direct] Synced the official resistor library into the shared database

- Received / problem: User asked to expand resistor models into the database using the prior MLCC-library approach or a better equivalent, with the hard constraint that every imported part number must be official or at least directly searchable online.
- Investigation: Reverse-engineered the JLC SMT search APIs first, then found a better official source: `GET /api/smtComponentOrder/smtCommon/v1/getAllComponentsFileUrl`, which returns a signed ZIP of the official JLC component catalog. Downloaded that archive to [jlc_all_components_latest.zip](C:/Users/zjh/Desktop/data/cache/jlc_all_components_latest.zip), verified that it contains [鐢甸樆.xlsx](C:/Users/zjh/Desktop/data/cache/jlc_all_components_latest.zip), [浼犳劅鍣?xlsx](C:/Users/zjh/Desktop/data/cache/jlc_all_components_latest.zip), and [TVS-淇濋櫓涓?鏉跨骇淇濇姢.xlsx](C:/Users/zjh/Desktop/data/cache/jlc_all_components_latest.zip), and confirmed the rows expose official component codes, names, models, package text, and brand names.
- Fix / action: Added [resistor_library_sync.py](C:/Users/zjh/Desktop/data/resistor_library_sync.py) to build a normalized resistor cache from the official ZIP, emit searchable detail links using `https://www.jlc-smt.com/lcsc/detail?componentCode=...`, and write the result to [resistor_library_cache.csv](C:/Users/zjh/Desktop/data/cache/resistor_library_cache.csv). Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so database refresh now merges the resistor cache alongside [MLCC.xlsx](C:/Users/zjh/Desktop/data/Capacitor/MLCC.xlsx), reads `鏁版嵁琛╜ only from non-MLCC library workbooks, keeps the new shared library columns, supports the added resistor families `閲戝睘姘у寲鑶滅數闃籤 and `缁曠嚎鐢甸樆`, and can rebuild the DB via `python component_matcher.py --rebuild-db`. Also fixed two parser issues that showed up during validation: low-ohm `m惟` values are now normalized correctly, and `卤1%` no longer gets mis-normalized to `100`.
- Verification: `python -m py_compile` passed for both [resistor_library_sync.py](C:/Users/zjh/Desktop/data/resistor_library_sync.py) and [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py). Running the sync script produced `1120792` normalized resistor rows across thick-film, thin-film, alloy, carbon-film, metal-oxide-film, wirewound, thermistor, and varistor families; the generated summary is in [resistor_library_report.json](C:/Users/zjh/Desktop/data/cache/resistor_library_report.json). Running `python component_matcher.py --rebuild-db` rebuilt [components.db](C:/Users/zjh/Desktop/data/components.db) successfully, and the resulting `components` table now contains `1236521` rows total. Spot checks confirmed examples such as `1206W4F1001T5E` as thick-film, `MFJ10HR016FT` as alloy with `0.016惟`, `CMFB103F3950FANT` as thermistor with `10000惟`, and `RL0402E012M015K` as SMD varistor with a JLC-searchable detail link.
- Other issues: The official resistor sync is intentionally using the JLC export cache instead of writing hundreds of thousands of rows back into the hand-maintained resistor template workbooks, because the full resistor library is now over one million rows and would be much less practical to maintain as Excel source sheets. Bare-mode runs of `component_matcher.py` print Streamlit `missing ScriptRunContext` warnings during CLI rebuilds; those warnings were observed during validation but did not block database generation.
- Handoff notes: If future work needs to refresh the resistor library, rerun [resistor_library_sync.py](C:/Users/zjh/Desktop/data/resistor_library_sync.py) first, then rebuild the DB with `python [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) --rebuild-db`. The current authoritative resistor source files are [jlc_all_components_latest.json](C:/Users/zjh/Desktop/data/cache/jlc_all_components_latest.json), [jlc_all_components_latest.zip](C:/Users/zjh/Desktop/data/cache/jlc_all_components_latest.zip), [resistor_library_cache.csv](C:/Users/zjh/Desktop/data/cache/resistor_library_cache.csv), and [resistor_library_report.json](C:/Users/zjh/Desktop/data/cache/resistor_library_report.json).

### 2026-03-23 21:27 [direct] Added an ASCII-safe handoff note for the resistor sync

- Received / problem: The resistor-sync entry above contains some mojibake when viewed through shells that do not preserve Unicode output cleanly, which could slow down future handoffs.
- Investigation: Re-read the latest log tail in a plain PowerShell session after the sync and noticed that a few Chinese workbook names and symbols such as `mohm` display inconsistently there even though the actual files and database contents are valid.
- Fix / action: Added this short ASCII-safe note to supersede the ambiguous parts of the previous entry. The key stable facts are: [resistor_library_sync.py](C:/Users/zjh/Desktop/data/resistor_library_sync.py) generated [resistor_library_cache.csv](C:/Users/zjh/Desktop/data/cache/resistor_library_cache.csv) with `1120792` resistor rows, [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) now imports that cache during DB refresh, and [components.db](C:/Users/zjh/Desktop/data/components.db) was rebuilt to `1236521` total rows.
- Verification: Re-checked the rebuilt database after the tolerance fix and confirmed sample rows such as `1206W4F1001T5E`, `MFJ10HR016FT`, `CMFB103F3950FANT`, and `RL0402E012M015K` are present with searchable JLC detail links.
- Other issues: This note does not change runtime behavior; it only makes the handoff state easier to read across terminals with mixed encodings.
- Handoff notes: If the previous resistor-sync entry looks garbled in a future terminal, trust this ASCII-safe note plus [resistor_library_report.json](C:/Users/zjh/Desktop/data/cache/resistor_library_report.json) for the authoritative counts and rerun path.

### 2026-03-23 23:02 [direct] Finished step 1 performance optimization, then step 2 resistor all-brand expansion validation

- Received / problem: User explicitly asked to do `1. performance optimization` first and `2. second-stage resistor expansion` after that, then continue until both were verified.
- Investigation: Re-checked the current matcher and cache pipeline in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py), verified the official resistor sync artifacts in [resistor_library_sync.py](C:/Users/zjh/Desktop/data/resistor_library_sync.py), [resistor_library_cache.csv](C:/Users/zjh/Desktop/data/cache/resistor_library_cache.csv), and [resistor_library_report.json](C:/Users/zjh/Desktop/data/cache/resistor_library_report.json), and measured both raw SQLite load time and prepared-cache load time against the rebuilt [components.db](C:/Users/zjh/Desktop/data/components.db). Also traced a cache-staleness path where Streamlit cache keys could keep an old dataframe alive under a default `None` signature and let an out-of-date prepared cache survive after DB changes.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so the data-loading cache now uses explicit signature-based wrappers, database rebuilds clear stale in-memory cached frames, and prepared-cache reads go through a dedicated helper. Kept the existing prepared-cache optimization path (prepared dataframe + categorical compression + DB indexes) and re-ran the database rebuild after the all-brand resistor sync. Step 2 is now validated against the broader official-library import path in [resistor_library_sync.py](C:/Users/zjh/Desktop/data/resistor_library_sync.py) using `--include-all-brands`.
- Verification: Current official resistor cache count is `1301979` rows (`include_all_brands=true`) in [resistor_library_report.json](C:/Users/zjh/Desktop/data/cache/resistor_library_report.json). The rebuilt [components.db](C:/Users/zjh/Desktop/data/components.db) now contains `1417708` total rows and `11` distinct component types. Confirmed sample searchable models remain present in both DB and prepared cache: `1206W4F1001T5E`, `MFJ10HR016FT`, `CMFB103F3950FANT`, and `RL0402E012M015K`. The refreshed prepared cache at [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) now also contains `1417708` rows, matches the current DB signature in [components_prepared_meta.json](C:/Users/zjh/Desktop/data/cache/components_prepared_meta.json), reads in about `10.784s`, and uses about `1330.76 MB` in memory. A fresh raw `SELECT * FROM components` load from SQLite took about `34.528s` and about `2245.61 MB`, so the prepared cache is materially faster and lighter for the app's search path.
- Other issues: PowerShell in this environment still defaults to a `gbk` stdout encoding, so one-off inline scripts that contain raw Chinese literals can display or behave misleadingly unless they use Unicode escapes. Bare-mode CLI rebuilds still print Streamlit `missing ScriptRunContext` warnings; these warnings did not block DB generation or cache regeneration.
- Handoff notes: If future work changes the library again, refresh in this order: run [resistor_library_sync.py](C:/Users/zjh/Desktop/data/resistor_library_sync.py) (use `--include-all-brands` when the wider official catalog is desired), rebuild with `python C:\Users\zjh\Desktop\data\component_matcher.py --rebuild-db`, then confirm that [components_prepared_meta.json](C:/Users/zjh/Desktop/data/cache/components_prepared_meta.json) matches the DB mtime/size and that [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) row count matches the DB row count.

### 2026-03-23 23:28 [direct] Exported resistor view workbooks and reduced homepage preloading before BOM matching

- Received / problem: User asked for the resistor data to also be visible in Excel files under the resistor folder, then asked for another round of homepage startup optimization with special focus on cutting the preload cost before BOM matching begins.
- Investigation: Checked the current runtime data path and confirmed the official resistor library was being stored as [resistor_library_cache.csv](C:/Users/zjh/Desktop/data/cache/resistor_library_cache.csv) -> [components.db](C:/Users/zjh/Desktop/data/components.db) -> [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet), not as runtime Excel sheets. Re-read the app entry flow in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and found two preload costs: the page always executed `load_prepared_data()` at top level before any user action, and BOM upload immediately ran matching without a separate start step. Also checked the `Resistor` workbook scan path and confirmed any new view-only exports placed directly in that folder would need to be explicitly skipped to avoid slowing down DB refresh.
- Fix / action: Added [export_resistor_view_workbooks.py](C:/Users/zjh/Desktop/data/export_resistor_view_workbooks.py) to split the official resistor cache into per-type view workbooks in [Resistor](C:/Users/zjh/Desktop/data/Resistor), each suffixed with `瀹樻柟鍙煡鐪嬬増.xlsx`, and wrote a manifest to [resistor_view_export_manifest.json](C:/Users/zjh/Desktop/data/cache/resistor_view_export_manifest.json). Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so any workbook whose name contains `鍙煡鐪嬬増` is skipped as a source workbook, data refresh checks are throttled per session, the top-level unconditional `load_prepared_data()` call is removed, manual search loads the prepared dataset only when the user actually clicks search, and BOM upload now waits for an explicit `寮€濮?BOM 鍖归厤` button before loading the search library and executing matches.
- Verification: Exported these view-only files directly under [Resistor](C:/Users/zjh/Desktop/data/Resistor): `鍘氳啘鐢甸樆_瀹樻柟鍙煡鐪嬬増.xlsx` (`440794` rows), `钖勮啘鐢甸樆_瀹樻柟鍙煡鐪嬬増.xlsx` (`746013` rows), `缁曠嚎鐢甸樆_瀹樻柟鍙煡鐪嬬増.xlsx` (`71687` rows), `閲戝睘姘у寲鑶滅數闃籣瀹樻柟鍙煡鐪嬬増.xlsx` (`14957` rows), `纰宠啘鐢甸樆_瀹樻柟鍙煡鐪嬬増.xlsx` (`11569` rows), `寮曠嚎鍨嬪帇鏁忕數闃籣瀹樻柟鍙煡鐪嬬増.xlsx` (`6863` rows), `璐寸墖鍘嬫晱鐢甸樆_瀹樻柟鍙煡鐪嬬増.xlsx` (`5962` rows), `鐑晱鐢甸樆_瀹樻柟鍙煡鐪嬬増.xlsx` (`2219` rows), `璐寸墖鐢甸樆_瀹樻柟鍙煡鐪嬬増.xlsx` (`1032` rows), and `鍚堥噾鐢甸樆_瀹樻柟鍙煡鐪嬬増.xlsx` (`883` rows). The export manifest confirms the view files total `1301979` rows, exactly matching the official resistor report. A post-change import of [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) in bare mode completed in about `3.953s`, and `get_source_workbooks()` confirmed that the new `瀹樻柟鍙煡鐪嬬増.xlsx` files are not treated as runtime source inputs. This means homepage first render no longer pays the `~10.8s` prepared-cache load before the user clicks search or starts BOM matching.
- Other issues: The view-workbook export itself is intentionally not lightweight; generating all per-type Excel files took several minutes because it streamed over the full `1301979`-row resistor cache and wrote ten xlsx files. PowerShell still shows mojibake for some Chinese text in direct JSON dumps even though the actual file contents and workbook names on disk are correct.
- Handoff notes: The new workbooks are for browsing and handoff only, not for runtime matching. If the official resistor cache is refreshed later, rerun [export_resistor_view_workbooks.py](C:/Users/zjh/Desktop/data/export_resistor_view_workbooks.py) after the cache sync to regenerate the `瀹樻柟鍙煡鐪嬬増.xlsx` files and keep [resistor_view_export_manifest.json](C:/Users/zjh/Desktop/data/cache/resistor_view_export_manifest.json) in sync.

### 2026-03-23 23:34 [direct] Restored auto-start BOM matching while keeping homepage lazy-loading

- Received / problem: User did not want the extra `寮€濮?BOM 鍖归厤` button and explicitly asked whether the app could still auto-match immediately after upload without making the webpage slow before any upload happens.
- Investigation: Re-read the BOM block in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and confirmed the previous optimization had two separate effects mixed together: (1) removing top-level preload, which keeps homepage startup light, and (2) adding an explicit click gate before BOM matching, which the user did not want. The real requirement is to keep effect (1) while reverting effect (2).
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so the page still avoids loading the prepared component library at first render, but once a BOM is uploaded and the current column mapping is known, the app automatically starts BOM matching for that file/mapping signature without waiting for another button click. The result is cached in session state under the current upload signature, so reruns with the same file and same mapping reuse the existing result instead of re-running the whole match.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed after the rollback. A post-change bare import of [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) still completes in about `4.426s`, which confirms homepage startup remains in the light/lazy path before any upload. The BOM section now shows the automatic-start caption instead of the old explicit `寮€濮?BOM 鍖归厤` button.
- Other issues: There is still an unavoidable first-wait cost after upload, because the app must load the prepared search dataframe and actually execute matching somewhere. What changed is where that cost happens: no longer at homepage first render, but only after the user uploads a BOM and the system has enough context to match it.
- Handoff notes: If a future task needs to squeeze the first-upload wait even further, the next direction is not to reintroduce a manual button; it is to optimize the BOM match execution path itself or add a safe background warm-up strategy after page load.

### 2026-03-24 00:42 [direct] Reduced the upload-time BOM auto-match path and refreshed the prepared cache

- Received / problem: User agreed to continue optimizing the wait that happens immediately after BOM upload, while keeping the current `upload -> auto match` behavior unchanged.
- Investigation: Benchmarked the auto-match path in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and profiled `bom_dataframe_from_upload`. Confirmed three concrete bottlenecks: the prepared cache on disk was missing the newer `_power` helper column, MLCC rows were repeatedly re-scanning the library to resolve `淇℃槍鏂欏彿` / `鍗庣鏂欏彿`, and the BOM path was doing too many repeated dataframe slices plus row-wise `apply(axis=1)` grading.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so prepared-cache reads can self-heal missing prepared columns, `_res_ohm` backfill stays object-safe, `scope_search_dataframe` uses one combined boolean mask instead of repeated table slicing, `match_by_spec` no longer re-applies filters already guaranteed by scoping, MLCC reference lookup is shared through one cached `lookup_brand_models_for_spec_map` call per spec, duplicate sorting was removed from `collect_brand_models_in_frame` and `format_other_brand_models`, and the MLCC branch of `apply_match_levels_and_sort` is now vectorized instead of relying on row-wise classification.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Rewrote [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) so the cache on disk already includes the required helper columns; the write itself took about `6.936s` once the prepared dataframe was loaded. On the tracked 200-row unique-model BOM benchmark, match time improved from the earlier `47.601s` baseline to `42.318s`, then to `38.436s` after the second optimization pass. A 100-row cProfile benchmark improved from about `54.420s` before this pass to about `35.386s` after the latest changes.
- Other issues: The latest profile still shows the biggest remaining costs in `scope_search_dataframe`, `lookup_brand_models_for_spec_map`, and `apply_match_levels_and_sort`, so a future optimization round should keep pushing on MLCC fallback volume and mask-construction overhead. Bare-mode benchmark scripts still emit Streamlit `missing ScriptRunContext` warnings, but those warnings did not affect the measurements.
- Handoff notes: Future performance work should start in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) around `scope_search_dataframe`, `lookup_brand_models_for_spec_map`, `match_by_spec`, `apply_match_levels_and_sort`, and the BOM result-row builder. The prepared cache on disk is already refreshed now, so later profiling can focus directly on matching/runtime logic instead of paying the earlier `_power` backfill cost again.

### 2026-03-24 01:06 [direct] Fixed resistor BOM parsing dropping `10K ohm` resistance

- Received / problem: User reported that a BOM row like `Res't : 10K ohm 1/10W +/-5% 0603SMD` was recognized as a resistor, but the parsed spec detail omitted the resistance entirely, so matching widened to unrelated `0603 / 5% / 1/10W` parts with the wrong ohmic value.
- Investigation: Re-read the resistor parsing path in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and narrowed the failure to `parse_resistance_token_to_ohm()`. The upstream regex was already capturing `10K ohm`, but after normalization to `10K惟` the parser was incorrectly converting any trailing `惟` token into `R`, producing `10KR` instead of `10K` and causing `_resistance_ohm` to fall back to `None`.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so `parse_resistance_token_to_ohm()` now distinguishes between plain-ohm tokens like `10惟` and scaled tokens like `10K惟`, `4R7惟`, and `2M2惟`. Plain numeric `惟` values still normalize to `R`, while scaled suffix forms now strip the trailing `惟` and keep the embedded resistance unit intact. Added a focused regression case to [regression_cases.csv](C:/Users/zjh/Desktop/data/regression_cases.csv) and a quick local check script [tmp_resistance_parse_check.py](C:/Users/zjh/Desktop/data/tmp_resistance_parse_check.py) for the affected resistor spellings.
- Verification: `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe C:\Users\zjh\Desktop\data\tmp_resistance_parse_check.py` confirmed that `10K ohm`, `10K惟`, `4R7惟`, `2M2惟`, and `0.0 Ohm` all resolve to the expected `_resistance_ohm` values, and `build_component_spec_detail_from_spec()` now returns `灏哄: 0603 | 闃诲€? 10K惟 | 璇樊: 5% | 鍔熺巼: 1/10W` for the reported BOM row.
- Other issues: This fix is intentionally narrow and does not yet expand support for less common forms such as leading-unit low-ohm tokens like `R010`; if those appear in future BOMs they should be handled in a separate pass with dedicated regression samples.
- Handoff notes: If a future task sees resistor candidates matching only by size, tolerance, and power again, start by checking whether `_resistance_ohm` is present in the parsed spec object before inspecting ranking or database content.

### 2026-03-24 01:28 [direct] Extended compact resistor parsing for `R010 / 3K3 / 4K75 / 0R22`

- Received / problem: User agreed to continue tightening resistor parsing for compact edge formats and specifically called out patterns like `R010`, `3K3`, `4K75`, and `0R22`, which are common in BOM spec text but were either not recognized at all or could lead to malformed tolerance/power extraction.
- Investigation: Re-ran the resistor parser on compact examples in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and found three separate issues: (1) `parse_resistance_token_to_ohm()` had no support for leading-`R` low-ohm tokens such as `R010`; (2) `looks_like_resistor_context()` destroyed token boundaries by compacting `R010 1% 1206` into `R0101%1206`, so the line was no longer recognized as resistor context; and (3) tolerance extraction on compact resistor lines like `3K3 5% 0603` was too greedy and could absorb adjacent size digits into the tolerance value.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so low-ohm leading-`R` tokens now normalize correctly, resistor-context detection uses a dedicated compact-resistance pattern without broadly opening that pattern to non-resistor columns, and compact tolerance extraction now prefers separated percentage tokens before falling back to compact matching. Also extended the regression conversion path so resistor regression cases compare actual ohmic values via `OHM / KOHM / MILLIOHM` units instead of capacitor-only `PF / NF / UF`, expanded [regression_cases.csv](C:/Users/zjh/Desktop/data/regression_cases.csv) with compact resistor samples, and rewrote [tmp_resistance_parse_check.py](C:/Users/zjh/Desktop/data/tmp_resistance_parse_check.py) to cover both token-level and full-spec parsing.
- Verification: `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe C:\Users\zjh\Desktop\data\tmp_resistance_parse_check.py` now passes for `10K OHM`, `4R7 OHM`, `2M2 OHM`, `0.0 OHM`, `R010`, `R005`, `0R22`, plus the full-text specs `3K3 5% 0603`, `4K75 1% 0603`, `R010 1% 1206`, and `0R22 5% 1206`. A targeted dry run of `build_regression_case_result()` also shows the added cases `RES_0603_10K`, `RES_0603_3K3`, `RES_0603_4K75`, `RES_1206_R010`, and `RES_1206_0R22` all returning `鐘舵€? 閫氳繃`.
- Other issues: Bare-mode validation still emits Streamlit `missing ScriptRunContext` and empty-label warnings because [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) executes UI code at import time, but those warnings did not affect parsing or regression outcomes in this pass.
- Handoff notes: Keep `R010` support scoped to resistor-context parsing only; do not promote leading-`R` tokens into a global resistance fallback unless column-inference logic is redesigned first, otherwise BOM reference designators like `R010 / R011` can be mistaken for low-ohm values.

### 2026-03-24 02:27 [direct] Fixed resistor BOM false matches drifting into Murata PRG PTC parts

- Received / problem: User reported that BOM rows such as `C Res't : 4.7 Ohm, +/-1%, 1/8W, SMD0805` were showing incomplete `鍖归厤鍙傛暟鏄庣粏`, and one of the matched models was Murata `PRG21BC4R7MM1RA`, which is a PTC / overcurrent-protection part rather than a normal chip resistor.
- Investigation: Rechecked the resistor matching chain in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and confirmed three linked faults. First, generic resistor queries were being scoped too narrowly, which let a wrongly typed `璐寸墖鐢甸樆` PRG row survive while valid `鍘氳啘鐢甸樆 / 钖勮啘鐢甸樆` families could be filtered out. Second, resistor grading was too permissive and could still stamp incomplete candidates as `瀹屽叏鍖归厤`. Third, the old component-alias matcher was too loose: short tokens like `NTC` were matching inside unrelated strings such as `componentCode`, which falsely turned ordinary resistor rows into `鐑晱鐢甸樆` during prepared-data inference.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so short alias tokens now require real boundaries, generic `璐寸墖鐢甸樆` queries are compatible with the full resistor family set, and resistor exact-match grading now checks normalized resistance + tolerance + power before awarding `瀹屽叏鍖归厤`. Also updated [resistor_library_sync.py](C:/Users/zjh/Desktop/data/resistor_library_sync.py) so future瀵煎簱浼氭妸 `杩囨祦淇濇姢 / PTC / resettable` 璇箟鐩存帴褰掑埌 `鐑晱鐢甸樆`, added a regression case to [regression_cases.csv](C:/Users/zjh/Desktop/data/regression_cases.csv), corrected the existing Murata PRG row in [components.db](C:/Users/zjh/Desktop/data/components.db), and refreshed [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) plus [components_prepared_meta.json](C:/Users/zjh/Desktop/data/cache/components_prepared_meta.json) so the cache already carries the corrected type information.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py C:\Users\zjh\Desktop\data\resistor_library_sync.py` passed. A focused replay against the user鈥檚 `4.7惟 / 1% / 1/8W / 0805` query now returns `47` normal resistor candidates, the top result is `鍗庢柊绉慦alsin WR08W4R70FTL`, `鍖归厤鍙傛暟鏄庣粏` renders as `灏哄: 0805 | 闃诲€? 4.7惟 | 璇樊: 1% | 鍔熺巼: 1/8W`, and `PRG21BC4R7MM1RA` is no longer present in the candidate list. The raw row for `PRG21BC4R7MM1RA` in both [components.db](C:/Users/zjh/Desktop/data/components.db) and [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) now shows `鍣ㄤ欢绫诲瀷 = 鐑晱鐢甸樆`.
- Other issues: Bare-mode validation still emits Streamlit `missing ScriptRunContext` / empty-label warnings because [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) executes UI code on import; these warnings did not affect matching verification. The one-off library repair touched `28` cache/database rows with thermistor/PTC clues, but only `1` row actually changed from a non-thermistor raw type this round because most affected rows were already classified correctly.
- Handoff notes: If similar errors return, start by checking three places in order: `matches_component_alias()` for short-token false positives, `infer_db_component_type()` for series-level override gaps, and `scope_search_dataframe()` for overly narrow generic family filters. For Murata PRG specifically, treat brand+series as suspect unless the part is explicitly intended to be a thermistor / PTC family.

### 2026-03-24 02:27 [direct] Audited all brands for resistor-vs-thermistor misclassification and fixed the remaining rows

- Received / problem: User pointed out that this kind of error should not be treated as Murata-only and asked for a full-database check across all brands.
- Investigation: Ran a full scan across [components.db](C:/Users/zjh/Desktop/data/components.db) over all `1417708` rows, checking every normal resistor family row for strong `NTC / PTC / 鐑晱 / 杩囨祦淇濇姢 / 鑷仮澶嶄繚闄╀笣 / resettable / polyfuse` clues in brand, model, summary, and note fields. Also checked the reverse direction to see whether any rows already marked as `鐑晱鐢甸樆 / 鍘嬫晱鐢甸樆` still looked like ordinary resistor families.
- Fix / action: Exported the audit findings to [component_type_suspicious_rows.csv](C:/Users/zjh/Desktop/data/cache/component_type_suspicious_rows.csv) and [component_type_audit_report.json](C:/Users/zjh/Desktop/data/cache/component_type_audit_report.json), then batch-corrected the remaining wrong raw types in [components.db](C:/Users/zjh/Desktop/data/components.db) and synced the same corrections into [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) plus [components_prepared_meta.json](C:/Users/zjh/Desktop/data/cache/components_prepared_meta.json). The corrected rows covered `5` brands and `7` models: Murata `PTGL12AR1R2H2B51B0`, ametherm `SL082R503 / SL322R025`, Amphenol `CL-70A / CL-60`, Cantherm `MF72-200D9`, and TDK `B57236S0509M000`.
- Verification: A post-fix rescan of the entire database now returns `0` remaining normal-resistor rows with strong thermistor/PTC clues. The thermistor raw-type count in [components.db](C:/Users/zjh/Desktop/data/components.db) increased from `2220` to `2227`, matching the `7` rows that were corrected during this pass.
- Other issues: The audit report JSON is UTF-8; if it is viewed in a terminal with a non-UTF-8 code page it may display mojibake, but the saved file contents are correct on disk. This pass was intentionally limited to strong clue rows; it does not claim that every brand series in the whole library has been manually checked against an official datasheet one by one.
- Handoff notes: If future work wants to push this further, the next audit layer should be series-based rather than keyword-based: compare brand+series families between correctly typed `鐑晱鐢甸樆 / 鍘嬫晱鐢甸樆` rows and ordinary resistor rows to catch cases where the summary text is weak but the model family itself is distinctive.

### 2026-03-24 02:41 [direct] Extended low-ohm high-power resistor parsing for `R005 / 5m惟 / 1W / 2W / 2512`

- Received / problem: User agreed to continue tightening resistor parsing for lower-ohm, larger-package, and higher-power edge formats, specifically calling out patterns such as `R005`, `5m惟`, `1W`, `2W`, and `2512`.
- Investigation: Replayed the parser against `R005 1% 2512 1W`, `5m惟 1% 2512 2W`, `1W 2512 5m惟 1%`, and `2W 2512 R005 1%`. Confirmed that low-ohm resistance and wattage were already being recognized, but `2512` was missing from the main size extraction path and `find_embedded_size()` was compacting away spaces before matching, which turned strings like `2512 1W` into `25121W` and caused the package code to be swallowed by adjacent digits.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so the shared size token regex now covers larger common packages such as `2010 / 2512 / 3225 / 4520 / 4532 / 5750`, and `find_embedded_size()` now matches against the cleaned uppercase text without first removing spaces. Also rewrote [tmp_resistance_parse_check.py](C:/Users/zjh/Desktop/data/tmp_resistance_parse_check.py) into a clean ASCII-safe regression helper and added new regression rows to [regression_cases.csv](C:/Users/zjh/Desktop/data/regression_cases.csv) for `R005 1% 2512 1W` and `5m惟 1% 2512 2W`.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py C:\Users\zjh\Desktop\data\tmp_resistance_parse_check.py` passed. `tmp_resistance_parse_check.py` now returns `status = ok` and confirms that `R005`, `5m惟`, `R005 1% 2512 1W`, `5m惟 1% 2512 2W`, `1W 2512 5m惟 1%`, and `2W 2512 R005 1%` all parse with `灏哄锛坕nch锛?= 2512`, `闃诲€?= 5m惟`, and the expected wattage. A direct parser replay also now renders details such as `灏哄: 2512 | 闃诲€? 5m惟 | 璇樊: 1% | 鍔熺巼: 2W`.
- Other issues: A direct SQLite lookup did not find current library rows that simultaneously satisfy `2512 + 0.005惟 + 1W/2W`, so this pass fixes the parser layer rather than proving that the present database already contains exact candidate parts for those specs.
- Handoff notes: If a future task sees another package code disappearing only when a numeric token follows it, inspect `find_embedded_size()` first before touching resistor parsing or power parsing; the root cause may be spacing/adjacency rather than the actual component grammar.

### 2026-03-24 10:40 [direct] Repaired resistor BOM no-match regression caused by stale prepared-cache results

- Received / problem: User reported that after the recent resistor parsing work, BOM upload suddenly showed common resistor rows such as `Res't : 3.3K ohm 1/8W +/-5% 0805SMD` as `鏃犲尮閰峘, even though the specs were complete and should have many catalog hits.
- Investigation: Confirmed the parser layer was healthy: `detect_query_mode_and_spec()` still recognized the row as `璐寸墖鐢甸樆`, produced `_resistance_ohm = 3300.0`, `_power = 1/8W`, and rendered `灏哄: 0805 | 闃诲€? 3.3K惟 | 璇樊: 5% | 鍔熺巼: 1/8W`. Then inspected `cache/components_prepared.parquet` and found the real failure: all `1286927` raw resistor-family rows had been poisoned to `_component_type = 鐑晱鐢甸樆`, so earlier sessions had cached empty resistor-query results. A fresh rebuild from `components.db` restored the prepared cache, and targeted checks showed `108` exact `0805 + 3.3k惟 + 5%` rows in cache with `72` rows still matching after the `1/8W` power filter.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) with a standalone `--rebuild-prepared-cache` CLI path so the prepared cache can be rebuilt from [components.db](C:/Users/zjh/Desktop/data/components.db) without forcing a full source re-import. Rebuilt [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) and [components_prepared_meta.json](C:/Users/zjh/Desktop/data/cache/components_prepared_meta.json), which now carry `cache_version = 3`. Also tightened `get_query_cache_signature()` so query-result caching includes the prepared-cache and meta file mtimes/sizes; this invalidates stale in-session `鏃犲尮閰峘 results after a cache rebuild. Finally, added `spec_display_value_unit()` and switched BOM/result-row display paths to use resistor ohmic values instead of capacitor-only `pf_to_value_unit()`, so resistor rows no longer appear blank in `瀹瑰€?/ 瀹瑰€煎崟浣峘 fields after parsing.
- Verification: `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Fresh inspection of [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) showed resistor-family `_component_type` values restored to normal distributions (`钖勮啘鐢甸樆 746013`, `鍘氳啘鐢甸樆 440794`, `缁曠嚎鐢甸樆 71687`, etc.) instead of all `鐑晱鐢甸樆`. A focused replay against `Res't : 3.3K ohm 1/8W +/-5% 0805SMD` now returns `mode = 璐寸墖鐢甸樆`, `matched_rows = 72`, and `spec_display_value_unit()` reports `3.3 KOHM`, confirming both matching and BOM-side display data are healthy again.
- Other issues: Bare-mode command-line verification still emits Streamlit `missing ScriptRunContext` / empty-label warnings because [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) executes UI code when imported outside `streamlit run`; these warnings did not affect the cache rebuild or query-result verification. The one-off `--rebuild-prepared-cache` run itself took long enough to exceed the shell timeout, but the cache files were successfully written at `2026-03-24 09:28`.
- Handoff notes: If resistor BOM rows ever regress to `鏃犲尮閰峘 again while parsing still looks correct, check three things in order: (1) whether [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet) has healthy resistor `_component_type` distributions, (2) whether the query-cache signature includes the latest prepared-cache mtimes, and (3) whether the current session needs a rerun after a cache rebuild so old empty query results are not reused.
### 2026-03-24 10:58 [direct] Switched search-field titles from capacitor-only labels to component-specific schemas

- Received / problem: User reported that when entering resistor specs, the page still rendered capacitor-style field titles such as `瀹瑰€?/ 瀹瑰€煎崟浣?/ 瀹瑰€艰宸?/ 鑰愬帇锛圴锛塦, even though the parsed query had already been identified as a resistor. The same mismatch also leaked into the matched-result table headers.
- Investigation: Traced the display path in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and confirmed that the parser layer was already classifying queries correctly, but the UI layer was still hard-coded to a capacitor-style schema in three places: `build_spec_info_df()` always returned `灏哄锛坕nch锛?/ 鏉愯川锛堜粙璐級 / 瀹瑰€?/ 瀹瑰€煎崟浣?/ 瀹瑰€艰宸?/ 鑰愬帇锛圴锛塦, the single-part info table used the same fixed column set, and the result table builder was always selecting the same generic parameter columns regardless of whether the query was a resistor, varistor, thermistor, or capacitor.
- Fix / action: Added a component-display schema layer to [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py), including `get_component_display_schema()`, `get_component_header_labels()`, `build_component_display_row()`, `ensure_component_display_columns()`, `select_component_display_columns()`, and `build_component_column_config()`. These now drive the query spec table, single-part info table, clickable result table, and fallback `st.dataframe` column headers. Resistors now use `灏哄锛坕nch锛?/ 闃诲€?/ 闃诲€煎崟浣?/ 璇樊 / 鍔熺巼`, leaded varistors use `鍘嬫晱鐢靛帇 / 璇樊 / 瑙勬牸 / 鑴氳窛 / 鍔熺巼`, and MLCC keeps `灏哄锛坕nch锛?/ 鏉愯川锛堜粙璐級 / 瀹瑰€?/ 瀹瑰€煎崟浣?/ 瀹瑰€艰宸?/ 鑰愬帇锛圴锛塦. Also updated the search-page subtitle so it no longer tells users that all specs should be thought of as `灏哄/瀹瑰€糮, and changed the section titles to follow the detected component type, for example `璐寸墖鐢甸樆瑙勬牸鏉′欢` and `璐寸墖鐢甸樆鍖归厤缁撴灉锛堝惈鎺ㄨ崘绛夌骇锛塦.
- Verification: `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Focused dry runs showed: resistor spec `0402 10K 1% 1/16W` now produces spec-table columns `灏哄锛坕nch锛? 瀹瑰€? 瀹瑰€煎崟浣? 瀹瑰€艰宸? 鍔熺巼` with displayed labels mapping to `灏哄锛坕nch锛? 闃诲€? 闃诲€煎崟浣? 璇樊, 鍔熺巼`; leaded-varistor spec `Varistor 470V P7.5` now produces `鍘嬫晱鐢靛帇, 瀹瑰€艰宸? 瑙勬牸, 鑴氳窛, 鍔熺巼` with the expected labels; and MLCC spec `0402 X7R 104K 50V` still renders the capacitor-oriented header set unchanged.
- Other issues: The present data model still stores many parameter values in generic internal fields such as `瀹瑰€?/ 瀹瑰€煎崟浣?/ 瀹瑰€艰宸甡; this pass intentionally changes the user-facing labels and visible columns without forcing a full data-model rewrite. Bare-mode validation still emits Streamlit `missing ScriptRunContext` warnings because the app executes UI code during import, but the helper output and schema checks completed successfully.
- Handoff notes: If future work expands the display model to more categories, the safe extension point is the new `get_component_display_schema()` helper rather than editing individual tables one by one. Any new type-specific field should also be mirrored in `build_component_display_row()`, `ensure_component_display_columns()`, and `build_component_column_config()` so the spec table and result table stay consistent.

### 2026-03-24 11:18 [direct] Expanded type-specific spec headers across all declared product categories

- Received / problem: User reported that the title mismatch was not limited to resistors and wanted all declared component categories checked so that the spec table and result table show the corresponding parameter titles for the detected product type, instead of falling back to capacitor-style headers.
- Investigation: Rechecked the display layer in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and confirmed two gaps. First, the component schema helper still only covered resistor families, thermistor, varistor, and a few capacitor families; categories such as `閽界數瀹?/ 鍔熺巼鐢垫劅 / 鍏辨ā鐢垫劅 / 纾佺彔 / 鏅舵尟 / 鎸崱鍣╜ could still fall back to the old capacitor template. Second, the model reverse-lookup path was losing `鍣ㄤ欢绫诲瀷` because [MODEL_REVERSE_LOOKUP_COLUMNS](C:/Users/zjh/Desktop/data/component_matcher.py) did not include it, which meant even correctly typed library rows could be rendered with generic or wrong titles after reverse lookup.
- Fix / action: Extended the schema layer in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so all declared categories now map to explicit user-facing labels. MLCC keeps capacitor labels; resistor families use `闃诲€?/ 闃诲€煎崟浣?/ 璇樊 / 鍔熺巼`; tantalum keeps capacitor-style titles without falling into the MLCC default; inductors use `鐢垫劅鍊?/ 鐢垫劅鍗曚綅 / 璇樊`; ferrite beads use `闃绘姉 / 闃绘姉鍗曚綅 / 璇樊`; crystals use `棰戠巼 / 棰戠巼鍗曚綅 / 棰戝樊 / 宸ヤ綔鐢靛帇`; oscillators use `杈撳嚭棰戠巼 / 棰戠巼鍗曚綅 / 棰戝樊 / 宸ヤ綔鐢靛帇`. Also changed the unknown-type fallback from capacitor wording to neutral `鍙傛暟鍊?/ 鍙傛暟鍗曚綅 / 璇樊 / 棰濆畾鐢靛帇锛圴锛塦. In the same pass, updated `spec_display_value_unit()`, `build_component_detail_lines()`, and `build_component_summary_from_spec()` so the summary/detail rows stay aligned with the new type-specific labels. Finally, widened [MODEL_REVERSE_LOOKUP_COLUMNS](C:/Users/zjh/Desktop/data/component_matcher.py) and updated [reverse_spec()](C:/Users/zjh/Desktop/data/component_matcher.py) so reverse specs now preserve `鍣ㄤ欢绫诲瀷`, `瑙勬牸鎽樿`, `灏哄锛坢m锛塦, notes, package hints, and raw value/unit data for non-capacitor families.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Venv-based helper checks confirmed the displayed labels now switch correctly for `璐寸墖鐢甸樆`, `MLCC`, `閽界數瀹筦, `鍔熺巼鐢垫劅`, `纾佺彔`, `鏅舵尟`, and `鎸崱鍣╜. A synthetic reverse-lookup replay for model `L0603-10UH` now returns `鍣ㄤ欢绫诲瀷 = 鍔熺巼鐢垫劅`, keeps `瀹瑰€?= 10 / 瀹瑰€煎崟浣?= UH`, and exposes labels `鐢垫劅鍊?/ 鐢垫劅鍗曚綅 / 璇樊` instead of reverting to capacitor headers.
- Other issues: This pass fixed display correctness and reverse-spec type preservation. It does not claim that every non-capacitor family already has full arbitrary free-text spec parsing or fully customized matching rules; those families may still need dedicated parser/matcher work in a later task. Bare-mode checks still emit Streamlit `missing ScriptRunContext` warnings because [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) executes UI code on import, but those warnings did not affect helper-level validation.
- Handoff notes: If a future task sees the right component type in the database but the page still renders generic titles, inspect [MODEL_REVERSE_LOOKUP_COLUMNS](C:/Users/zjh/Desktop/data/component_matcher.py) and [reverse_spec()](C:/Users/zjh/Desktop/data/component_matcher.py) first. If a new family is added later, update `get_component_display_schema()`, `spec_display_value_unit()`, `build_component_detail_lines()`, and `build_component_summary_from_spec()` together so the spec table, summary line, and match-result table stay aligned.

### 2026-03-24 23:16 [direct] Added SQL search index for resistor-first matching, enforced model-rule authority in search, and updated match colors

- Received / problem: User reported that spec query `0401 1ohm k` was still returning wrong resistor candidates, including models whose official naming rules decode to very different values or sizes. User also asked to start the first version of a faster indexed search layer and to update BOM match colors so `瀹屽叏鍖归厤 / 閮ㄥ垎鍙傛暟鍖归厤 / 楂樹唬浣巂 are visually distinct.
- Investigation: Confirmed that the raw library row for examples such as `AA0402JR-071RL` already carries authoritative model-rule fields in [components.db](C:/Users/zjh/Desktop/data/components.db), including `_model_rule_authority = yageo_chip_resistor_model` and `_resistance_ohm = 1.0`, while Murata `MHR0422SA108F70` carries `_model_rule_authority = murata_mhr_model` and `_resistance_ohm = 1000000000.0`. The real gap had moved to runtime search: the old prepared cache was stale, `scope_search_dataframe()` still prepared the entire 1417708-row cache before narrowing candidates, and the query page therefore continued to rely too much on historical scraped fields. I also attempted a chunked full prepared-cache rebuild, but the first implementation hit Parquet schema drift between chunks and was too expensive to make the current search fix depend on it.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) to add a new SQLite search layer: `components_search`, `build_search_index_chunk_from_raw()`, `rebuild_search_index_from_database_fast()`, and `fetch_search_candidate_pairs()`. The new index stores normalized search fields such as `_component_type`, `_size`, `_res_ohm`, `_tol`, `_power_watt`, `_pf`, and `_model_rule_authority`, and it is rebuilt through the new CLI path `--rebuild-search-index`. Query filtering now uses the SQL candidate set first and only then runs `prepare_search_dataframe()` on the reduced subset, instead of preparing the full cache up front. This makes resistor spec matching obey official model rules at candidate-selection time even if a full prepared-cache refresh has not yet been completed. In the same pass, I hardened [apply_model_rule_overrides_to_dataframe()](C:/Users/zjh/Desktop/data/component_matcher.py) against categorical columns from older cache files, added support for `0401`-class resistor spec parsing in the search path, and changed the row-color rules in both HTML and fallback DataFrame styling so `瀹屽叏鍖归厤 = 榛勮壊`, `閮ㄥ垎鍙傛暟鍖归厤 = 娴呯孩鑹瞏, `楂樹唬浣?/ 鍙洿鎺ユ浛浠?= 娴呰摑鑹瞏, while `鏃犲尮閰峘 remains unstyled.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe C:\Users\zjh\Desktop\data\component_matcher.py --rebuild-search-index` completed successfully and produced `1417702` rows in `components_search`. Direct query checks showed `0401 1ohm k` now yields `0` indexed candidates, which is the correct safe result instead of leaking `0402` or `1G惟` models. Positive-control checks showed `0402 1ohm 5%` now returns `60` indexed candidates and `0402 1ohm 1%` returns `51`, all narrowed to the correct resistor size/value/tolerance family before the final ranking step. After reordering `scope_search_dataframe()`, the end-to-end `run_query_match()` timings on the current cache dropped to about `0.004s` for the empty `0401 1ohm k` case and about `1.2s-1.3s` for the `0402 1ohm` exact resistor cases, down from multi-minute behavior when the entire stale cache was still being re-prepared first.
- Other issues: The full chunked prepared-cache rebuild path remains unfinished for now. I kept the scaffolding in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py), but the current practical fix for search correctness and speed is the new `components_search` index rather than a mandatory full parquet refresh. Also, while the resistor families now obey model-rule authority at the candidate-filter stage, this does not yet mean every brand series in the whole passive library has been manually audited against an official datasheet one by one.
- Handoff notes: If future work continues the search-layer migration, the next step should be to use `components_search` for MLCC and other passive families more aggressively and then finish a stable chunked rebuild for [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet). If a later regression shows wrong resistor candidates again, check `components_search` first, especially `_model_rule_authority`, `_size`, `_res_ohm`, and `_tol`, before blaming the display layer or the BOM mapper.

### 2026-03-24 23:30 [direct] Removed full prepared-cache preloading from normal search clicks and switched search page to SQLite on-demand candidate loading

- Received / problem: User reported that the web page had become unusable again because pressing `鎼滅储` was hanging on `姝ｅ湪鍔犺浇鍏冧欢搴擄紝鍑嗗鎼滅储... Running _load_prepared_data_cached(...)`, even for simple resistor queries like `0402 1ohm k`.
- Investigation: Traced the active search-page code path in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and confirmed that the UI was still calling `load_search_dataframe_for_action("鎼滅储")` before parsing the query text. That meant the page was loading the full prepared cache up front even though the new `components_search` SQL index was already available. The indexed candidate layer itself was healthy: bare-mode checks showed `detect_query_mode_and_spec(None, "0402 1ohm 5%")` plus `load_search_dataframe_for_query()` could identify the resistor spec and build a small candidate DataFrame without touching `_load_prepared_data_cached()`.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so the search page now parses each line first and only falls back to the heavy full-cache path when a query cannot yet be served from the fast SQL path. Added helpers `chunk_items()`, `concat_component_frames()`, `load_component_rows_by_brand_model_pairs()`, `load_component_rows_by_clean_model()`, `can_use_fast_search_dataframe()`, and `load_search_dataframe_for_query()`. Exact part-number reverse lookup now falls back to SQLite rows when the in-memory DataFrame is absent, and the search-page loop now prefers `components_search -> components` for resistor and MLCC searches instead of forcing a full prepared-cache load before every search click. I also bumped the in-session query cache version so old cached search results do not survive this routing change.
- Verification: `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Bare-mode timing replays showed the fast path working end-to-end: `0402 1ohm k` detected in about `0.025s`, loaded candidate rows in about `0.071s`, and matched in about `0.160s`; `0402 1ohm 5%` loaded candidates in about `0.124s` and matched in about `0.329s`; `0401 1ohm k` now returns `0` fast-path rows in about `0.01s`; and exact part query `AA0402FR-071RL` now detects in about `0.078s`, loads its small candidate set in about `0.083s`, and matches in about `0.237s`. These checks confirm the search path itself no longer depends on the multi-minute prepared-cache preload for common resistor queries.
- Other issues: This pass intentionally targets the top search box. BOM upload still uses the heavier prepared-data path, because batch matching still benefits from a broader preloaded frame. Also, the existing inductor/other-passive free-text parser gaps are not solved by this performance fix; unsupported search families may still fall back to the heavier path until their indexed candidate logic is added.
- Handoff notes: If search-page latency regresses again, inspect whether the UI has fallen back to `load_search_dataframe_for_action("鎼滅储")` too early. The intended order is now: parse query -> use `load_search_dataframe_for_query()` when possible -> only then fall back to full prepared data. Future performance work should extend the fast indexed path beyond resistor/MLCC into inductors and other passive families so the search page rarely needs the heavy fallback at all.

### 2026-03-24 23:47 [direct] Fixed inductor spec parsing so `0402 1uh k` no longer falls into MLCC and added light fast-path support for inductor/timing queries

- Received / problem: User reported that inductor-style queries such as `0402 1uh k` were still being parsed and displayed as MLCC, so the page showed capacitor-style section titles and field headers instead of inductor fields like `尺寸 / 感量 / 精度`.
- Investigation: Replayed `detect_query_mode_and_spec(None, "0402 1uh k")` and confirmed the old flow was sending the string into the generic capacitor parser. The size token `0402` was being reused later as a possible capacitor code, the `K` token was treated as a generic tolerance code, and because there was no dedicated inductor parser in `parse_other_passive_query()`, the spec ended up as `MLCC`-shaped data. I also confirmed that the search-page fast path added earlier only covered resistor / MLCC, so even once the type was corrected, unsupported inductor queries would still fall back to the heavy path unless I extended the query loader.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) to add `INDUCTOR_TOLERANCE_CODE_MAP`, a new `parse_inductor_spec_query()` parser, and inductor-aware type inference in both `infer_spec_component_type()` and `infer_db_component_type()`. `parse_other_passive_query()` now tries the inductor parser before capacitor/resistor fallbacks, and `parse_spec_query()` now skips reinterpreting explicit size tokens like `0402` as capacitor-value tokens. I also added `load_component_rows_by_typed_spec()` and extended `can_use_fast_search_dataframe()` / `load_search_dataframe_for_query()` so inductor and timing searches can short-circuit through a lightweight database path instead of immediately triggering a full prepared-cache preload. Finally, `match_other_passive_spec()` now has explicit inductor and timing branches so these typed specs no longer fall straight through to an empty default path.
- Verification: `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Bare-mode replay now reports `detect_query_mode_and_spec(None, "0402 1uh k") -> mode = 功率电感`, with parsed spec `{尺寸（inch）= 0402, 容值 = 1, 容值单位 = UH, 容值误差 = 10, 器件类型 = 功率电感}`. `infer_spec_component_type()` now returns `功率电感`, `get_component_display_schema()` returns the inductor header set `尺寸（inch） / 电感值 / 电感单位 / 误差`, and `build_spec_info_df()` exposes those same inductor-oriented columns. The lightweight query loader now returns `fast_df_rows = 0` immediately for this query in the current database instead of forcing the old heavy full-cache load, which is the correct behavior while the present library still lacks inductor rows.
- Other issues: This pass fixes the current inductor misclassification chain and adds H/Hz unit-aware type inference, but it does not claim that the current database already contains complete inductor / timing libraries. In the present dataset, the dominant imported families are still resistor-oriented, so some inductor searches will now correctly render inductor titles yet still return `无匹配` because the underlying library rows are not there yet.
- Handoff notes: If a future passive-type query still falls into MLCC by mistake, check `parse_other_passive_query()` and the unit-aware branches in `infer_spec_component_type()` first. The intended order is now: explicit family parser -> unit-aware type inference -> generic capacitor fallback, not the other way around.

### 2026-03-24 23:55 [direct] Aligned BOM row colors to the requested four-state rule only

- Received / problem: User asked to make the BOM match table follow a strict four-state coloring rule: `完全匹配 = 黄色`, `部分参数匹配 = 浅红`, `高代低 = 浅蓝`, and `无匹配 = 不改动`.
- Investigation: Checked the active BOM display path in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and confirmed that the core match colors were already present, but `style_bom_result_rows()` was still separately painting `解析失败` rows with the same浅红色 as `部分参数匹配`, which made the visual meaning ambiguous and no longer matched the user's requested four-state-only rule. The accompanying caption also still said that parse-failure rows were highlighted.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so `style_bom_result_rows()` now colors only by `首选推荐等级`: `完全匹配 -> #fff59d`, `部分参数匹配 -> #fde2e1`, `高代低 / 可直接替代 -> #dbeafe`, and everything else, including `无匹配` and `解析失败`, is left unstyled. Also removed the stale BOM caption text that claimed parse-failure rows were highlighted.
- Verification: `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Source inspection confirmed the active BOM styling branch now maps only those three match levels to colors and leaves other rows unchanged.
- Other issues: This pass only adjusts BOM-table coloring and BOM summary copy. It does not change the underlying matching logic or the separate single-query result-table colors.
- Handoff notes: If a later task adds new BOM result levels, update `style_bom_result_rows()` carefully so they do not accidentally reuse the `部分参数匹配` color unless that is intended.

### 2026-03-25 00:11 [direct] Switched BOM batch matching to indexed on-demand candidate loading with full-cache lazy fallback

- Received / problem: User agreed to continue the new high-speed search architecture by moving BOM batch matching onto the same indexed candidate path, so uploaded BOM files would no longer pay the full prepared-cache load cost up front for common resistor and MLCC rows.
- Investigation: Reviewed the existing BOM flow in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and confirmed that the upload path still built a prepared full-data DataFrame before matching every row. Even after the search page had been converted to SQL-first candidate loading, BOM upload was still calling the heavy `load_search_dataframe_for_action("BOM 鍖归厤")` path before row evaluation, which kept batch matching slower than necessary.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so BOM evaluation now mirrors the search-page fast path. `evaluate_bom_candidate()` first parses the row text and tries `load_search_dataframe_for_query()` to fetch a small indexed candidate set; only unsupported or unresolved rows call the new lazy `full_df_provider()` fallback. `choose_best_bom_candidate()` and `build_bom_upload_result_row()` now propagate that per-row candidate frame, including MLCC reference resolution. `bom_dataframe_from_upload()` no longer preloads the full prepared library; instead it memoizes a lazy `get_full_bom_df()` closure that loads and prepares the full cache only if at least one row really needs it. The BOM UI path now checks `database_has_component_rows()` before matching and otherwise runs `bom_dataframe_from_upload(None, bom_df, selected_mapping)` directly, so upload-triggered matching starts from the indexed route instead of the full-cache route.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Bare-mode regression checks monkeypatched `load_search_dataframe_for_action()` to raise if the heavy path was touched, then replayed representative BOM rows including `Res't : 3.3K ohm 1/8W +/-5% 0805SMD`, `Res't : 4.7K ohm 1/8W +/-1% 0805SMD`, and `0402 X7R 104K 50V`; the upload matcher produced result rows successfully with `full_load_calls = 0`. A second replay including `0402 1uh k` also completed without touching the full prepared-cache loader for the supported rows and finished in about 3.3 seconds for four sample lines. These checks confirm the BOM pipeline now prefers SQL indexed candidates and uses the full prepared cache only as a fallback.
- Other issues: The lazy fallback is intentionally still present. Rows whose families are not yet fully covered by `load_search_dataframe_for_query()` can still trigger a full prepared-cache load later in the batch. This pass improves BOM startup behavior and common-family latency, but it is not yet a guarantee that every passive family avoids the heavy fallback.
- Handoff notes: If a future regression makes BOM upload hang on full-cache loading again, inspect [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) around `evaluate_bom_candidate()`, `bom_dataframe_from_upload()`, and the `stored_bom_signature != current_bom_signature` block first. The intended order is now: build per-row query -> fetch indexed candidate subset -> match -> only then, if needed, call `load_search_dataframe_for_action("BOM 鍖归厤")` through the lazy provider.

### 2026-03-25 01:10 [direct] Extended BOM fast path beyond resistor and MLCC, and hardened startup / rebuild behavior

- Received / problem: User asked to continue the next optimization step after the first BOM indexed path landed, specifically to keep pushing more passive families onto the same fast route instead of falling back to the heavy full prepared-cache load.
- Investigation: Reviewed the current fast-path coverage in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) and confirmed that it was still strongest for `璐寸墖鐢甸樆 / MLCC`, with lighter support for `鐢垫劅 / 鏃跺簭鍣ㄤ欢`, while `钖勮啘鐢靛 / 閾濈數瑙ｇ數瀹?/ 鍘嬫晱鐢甸樆 / 鐑晱鐢甸樆` could still fall back to the heavy path more often. During validation I also found two operational issues: rebuilding `components_search` can fail when the live app holds a SQLite write lock, and bare-mode startup can hit a `NameError` if `maybe_update_database()` runs before `prepare_search_dataframe()` has been defined.
- Fix / action: Expanded the fast-search plumbing in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py). `components_search` now has code support for richer structured fields such as `_body_size`, `_pitch`, `_safety_class`, `_varistor_voltage`, `_disc_size`, `_value_text`, `_unit_upper`, and `_value_num`, and the search-index builders now prepare those columns as part of the index schema. `can_use_fast_search_dataframe()` now treats `鐑晱鐢甸樆`, `钖勮啘鐢靛`, `閾濈數瑙ｇ數瀹筦, and all鍘嬫晱瀹舵棌 as fast-path-eligible. `fetch_search_candidate_pairs()` was widened so MLCC, resistor, thermistor, varistor, film capacitor, electrolytic capacitor, inductor, and timing specs can all attempt SQL candidate filtering first. To make the feature usable immediately even when the live database blocks index rebuilds, I also expanded `load_component_rows_by_typed_spec()` so these newly supported families can fall back to direct narrow SQL reads from `components` instead of loading the full prepared cache. Finally, I moved the top-level `maybe_update_database(force=False)` call to a later point in the file so startup refresh no longer tries to call `prepare_search_dataframe()` before it exists, and I added busy-timeout handling to the search-index rebuild functions.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. Function-only validation (executing the definition section without full Streamlit UI startup) showed that `load_search_dataframe_for_query()` now returns non-`None` frames quickly for representative rows across families: resistor `Res't : 3.3K ohm 1/8W +/-5% 0805SMD` loaded about 18 rows in about `0.734s`; MLCC `0402 X7R 104K 50V` loaded about 76 rows in about `0.091s`; varistor `Varistor : 470V +/-10%,0.4W,HEL10D471KJ,P7.5` stayed on the fast path and returned an empty frame in about `0.085s` rather than falling back; electrolytic `E CAP : 10uF, 450V, +/-20%, D10*H13, 104TC, Pet` returned an empty fast-path frame in about `0.470s`; film capacitor `PP Cap : 2200pF, 400V, +/-10%, Pitch 10mm` returned an empty fast-path frame in about `0.105s`; and inductor `0402 1uh k` returned an empty fast-path frame in about `0.086s`. A mixed six-line BOM replay then monkeypatched `load_search_dataframe_for_action()` to hard-fail if the heavy full-load route was touched; `bom_dataframe_from_upload()` still completed successfully with `rows = 6` and `full_load_calls = 0`, confirming that these common passive families now stay on the fast path during BOM upload.
- Other issues: Rebuilding `components_search` in the live working database still could not be completed during this pass because SQLite kept reporting `database is locked`, which means some other live process is holding a write-preventing lock on [components.db](C:/Users/zjh/Desktop/data/components.db). The code now waits longer before giving up, but this environment-level lock still prevented the in-place rebuild from finishing right now. That means the richer index columns are present in code, but some live queries may temporarily use the new direct-`components` narrow-query fallback until the lock clears and the search index can be rebuilt.
- Handoff notes: If the next task wants the absolute best speed for these newly supported families, the next step is to rerun `--rebuild-search-index` once the live SQLite lock is gone so `components_search` picks up the richer schema and can avoid even more direct table reads. If startup refresh regresses again, check the location of `maybe_update_database(force=False)` first; it now intentionally sits after the search-preparation helpers so database refresh can safely call `prepare_search_dataframe()`.

### 2026-03-25 02:03 [direct] Moved fast search index into a sidecar SQLite DB and restored complete indexed BOM/query matching

- Received / problem: After the previous fast-path work, follow-up investigation showed a serious integrity issue: the in-place `components_search` table inside [components.db](C:/Users/zjh/Desktop/data/components.db) had the new schema but only about `600000` rows, far below the `1417708` source rows. At the same time, rebuilding the in-main-DB search table kept colliding with SQLite locks, which meant the fast layer could become both incomplete and brittle.
- Investigation: Confirmed that the root problem was architectural rather than parser-level. The fast index was still being stored inside the main component database, so a rebuild required `DROP TABLE / append` inside the live DB. That made it vulnerable to writer/read-lock contention and left the system in a half-rebuilt state after interrupted runs. I also verified that this incomplete in-main-DB index could make fast candidate retrieval unsafe. Additional tracing showed that some temporary `python -X utf8 -` validation processes I had launched were also holding locks during debugging, which temporarily masked the true state of the query path.
- Fix / action: Refactored the fast search layer in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so indexed search now lives in a sidecar SQLite database [components_search.sqlite](C:/Users/zjh/Desktop/data/cache/components_search.sqlite) instead of the main DB. Added `SEARCH_DB_PATH`, `SEARCH_META_TABLE`, `SEARCH_INDEX_SCHEMA_VERSION`, `get_search_index_signature()`, `write_search_index_meta()`, `read_search_index_meta()`, `search_index_is_current()`, and `open_search_db_connection()`. Reworked both `rebuild_search_index_from_database_fast()` and `rebuild_search_index_table_from_prepared_cache()` so they now read from [components.db](C:/Users/zjh/Desktop/data/components.db), build the index into a temporary sidecar file, write metadata, and atomically replace the final sidecar DB only after a complete successful build. Updated `load_component_rows_by_clean_model()` and `fetch_search_candidate_pairs()` so they query the sidecar index for candidate brand/model pairs, then read the actual detailed component rows from the main DB only after the candidate set is narrowed. Also relaxed the search-index freshness check so it no longer invalidates a freshly built sidecar just because the main DB file mtime twitches while its size and schema are unchanged. In the same pass, I kept the earlier fast-path extensions for `鐑晱鐢甸樆 / 钖勮啘鐢靛 / 閾濈數瑙ｇ數瀹?/ 鍘嬫晱 / 鐢垫劅 / 鏃跺簭鍣ㄤ欢` and ensured prepared-cache fallback rebuilding now also refreshes the sidecar index instead of trying to stuff search data back into the main DB.
- Verification: `python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py` passed. `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe C:\Users\zjh\Desktop\data\component_matcher.py --rebuild-search-index` completed successfully against the new sidecar path. The resulting [components_search.sqlite](C:/Users/zjh/Desktop/data/cache/components_search.sqlite) contains both `components_search` and `search_meta`, reports `1417702` indexed rows, and includes the richer schema columns `_body_size`, `_pitch`, `_safety_class`, `_varistor_voltage`, `_disc_size`, `_value_text`, `_unit_upper`, and `_value_num`. Function-level replay then confirmed the live fast path was restored: `0402 1ohm 5%` now loads about `60` rows in about `0.073s`, `0401 1ohm k` returns `0` rows in about `0.005s`, `0402 X7R 104K 50V` loads about `314` rows in about `0.062s`, and `E CAP : 10uF, 450V, +/-20%, D10*H13, 104TC, Pet` stays on the fast path and returns an empty narrowed frame in about `0.004s`. Finally, a mixed six-line BOM replay with the heavy full-load function forcibly disabled completed in about `1.222s` with `full_load_calls = 0`, proving that BOM batch matching now truly runs through the indexed route for these covered families instead of secretly falling back to the full prepared cache.
- Other issues: The main DB still contains the old in-place `components_search` table from earlier work, but the active fast path now uses the sidecar DB instead, so that partial legacy table is no longer the source of truth. Also, some queries still legitimately return `0` rows because the underlying library lacks those family entries; that is a data-coverage issue rather than a fast-path regression.
- Handoff notes: If future work sees fast searches go stale again, inspect [components_search.sqlite](C:/Users/zjh/Desktop/data/cache/components_search.sqlite) and `search_meta` first, not the old `components_search` table inside [components.db](C:/Users/zjh/Desktop/data/components.db). The intended architecture is now: main DB stores source component rows, sidecar DB stores the searchable indexed view, and query/BOM paths first narrow through the sidecar before reading detailed rows from the main DB.

### 2026-03-25 09:08 [direct] Removed automatic BOM fallback to full prepared-cache loading and verified real POLED upload no longer calls _load_prepared_data_cached(...)

- Received / problem: User reported that BOM upload was still showing the heavy _load_prepared_data_cached(...) spinner in the browser even after the indexed fast path had been introduced. The screenshot showed the live page still entering the full library load during automatic BOM matching.
- Investigation: Replayed the real workbook 阻容-POLED-报价.xlsx with the same PN -> 型号列 and Spec. -> 规格列 mapping and monkeypatched load_search_dataframe_for_action() to fail immediately if the heavy path was touched. That isolated two concrete triggers before this pass: row 16 (C Cap : 1.0nF, 1000V, +/-10%, D6*L21, Y5P) was forcing fallback because 引线型陶瓷电容 had not been wired into the fast SQL path, and row 33 (55H022J-SDCN) was forcing fallback because the text looked like a model token living in the spec column, but exact-model probing only ran for the explicit 型号列 candidate.
- Fix / action: Updated [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) so 引线型陶瓷电容 now participates in load_component_rows_by_typed_spec(), can_use_fast_search_dataframe(), and the etch_search_candidate_pairs() SQL narrowing branch with the same core fields used for other leaded capacitors (容值_pf / 误差 / 耐压 / 本体尺寸 / 脚距 / 介质). Added model-token extraction helpers so any unrecognized BOM candidate can try exact model rows from tokenized part-like fragments before considering a fallback. Then changed om_dataframe_from_upload() so automatic BOM upload no longer passes the full prepared-cache provider by default; the upload path now stays on the indexed / narrow-query route instead of loading the entire prepared cache when a row is unsupported.
- Verification: python -m py_compile C:\Users\zjh\Desktop\data\component_matcher.py passed. A hard-fail replay of the real 阻容-POLED-报价.xlsx upload through om_dataframe_from_upload(None, bom_df, mapping) completed with ows = 65, elapsed_s = 66.64, and ull_load_calls = 0, proving the automatic BOM route no longer invokes _load_prepared_data_cached(...). Additional spot checks confirmed the earlier row-16 Y5P trigger no longer caused a full-load fallback and that model-token probing now catches mixed-source candidates earlier.
- Other issues: This pass removes the unusable whole-library fallback from automatic BOM upload, but it does not yet make the upload fast enough overall. Profiling the same workbook without the full-cache path still showed about 70.586s total on the indexed route, with the slowest rows concentrated in non-SMD / high-power resistor lines such as C Res't : 150K Ohm, +/-5%, 1/2W, 26*10mm (~9.7s), Res't : 2 ohm 1W +/-5% N (~8.0s), and Res't : 22 ohm 2W +/-5% N (~6.7s). Those rows are staying on the fast architecture, but their candidate narrowing and row preparation are still expensive.
- Handoff notes: If the next task continues performance work, start with the slow resistor-family rows near the bottom of the POLED workbook. They no longer trigger the full prepared-cache loader, so remaining latency is inside the indexed query + candidate materialization path rather than in _load_prepared_data_cached(...).

### 2026-03-25 12:16 [direct] Reworked brand/model parsers for official naming rules and rewrote prepared cache with authority-aware backfill

- Received / problem: User asked to scan the brands with data, find models whose spec fields were incomplete, look up the official naming rules, and then supplement the missing fields from the brand-specific series rules. The immediate pain points included Murata GRT/GCG/GCQ rows, Yageo CC/CQ rows, Samsung CLR1 rows, Taiyo new M*/MSAS/MAAS series, Kyocera AVX size-first MLCC rows, HRE size-first rows, and Walsin alpha-prefix / 01R5 rows. A second issue was that many rows had complete fields but still showed blank `_model_rule_authority`, so the previous backfill logic never touched them.
- Investigation: Rechecked the live parser functions in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) against official manufacturer naming references and against the current prepared cache. Confirmed that `parse_murata_core()` only supported a narrow prefix set, `parse_tdk_c_series()` still used metric-only size mapping and plain EIA capacitance parsing, `parse_yageo_common()` rejected CQ parts and did not treat `NPO` cleanly, `parse_samsung_cl()` lacked a dedicated CLR1 path, `parse_taiyo_common()` only understood the older TMK/JMK/EMK/LMK/AMK families, and Walsin had no coverage for `MT03B471K500CT` / `01R5N100J160CT` style codes. I also confirmed that `fill_missing_spec_fields_from_model()` only considered rows with blank core fields, so rows with complete specs but missing `_model_rule_authority` were never revisited.
- Fix / action: Extended the parser layer in [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) to follow the official family naming rules more closely. Murata now accepts `GRT/GCG/GCQ` plus the missing `7U -> U2J` dielectric mapping and stamps `_model_rule_authority = murata_core_series`. TDK `C...` parts now accept direct `0402/0603/0805/...` size codes and use `murata_cap_code_to_pf()` for `R11` / `3R3` style capacitance tokens; a new `parse_tdk_cga_series()` was added for the official CGA family. Yageo `CC`/`CQ` parts now parse `NPO` correctly, accept `A` tolerance, and also use `murata_cap_code_to_pf()` so `2R7` / `3R3` capacitance codes are no longer lost. Samsung got a dedicated `parse_samsung_clr1()` path plus `murata_cap_code_to_pf()` for `CLR1...` series caps. Taiyo got a new `parse_taiyo_new_common()` branch for the newer `MAAS/MSAS/MLAS/MCAST` families and the old parser now stamps authority too. Added `parse_generic_size_first_mlcc()` for HRE-style `CGA0603...` / `CSA0402...` parts, `parse_kyocera_avx_common()` for AVX size-plus-voltage codes like `04026D105KAT4A`, and extended `parse_walsin_common()` for both alpha-prefix Walsin rows like `MT03B471K500CT` and the `01R5N100J160CT` style 01005 code. Finally, `parse_model_rule()` now routes by brand and by model pattern before falling back to generic paths, and `fill_missing_spec_fields_from_model()` now also treats blank `_model_rule_authority` as a candidate so rows with already-filled specs still get the official-rule source stamped in.
- Verification: The parser smoke tests now return concrete dicts for the previously failing examples: `GRT1555C1HR11BA02D`, `GCG1887U2A112JA01J`, `CC0100CRNPO8BN3R3`, `CQ0100ARNPO7BN1R8`, `CLR1CR25AA1INNG`, `CLR1C010AA1INN`, `MAASL31LAB7226KTNA01`, `MSAST021SCGR75BWNA01`, `MLASA105CC6106MFNC12`, `MSASJ32MAB5227MPNDT1`, `04026D105KAT4A`, `06035C104KAT2A`, `CSA0402X5R105K6R3GT`, `CGA0603X7R104K500JT`, `01R5N100J160CT`, and `MT03B471K500CT`. After a full backfill pass over [components_prepared.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared.parquet), `_model_rule_authority` non-empty count rose to `1,390,046` out of `1,417,708`, and the targeted sample rows now show populated authorities such as `murata_core_series`, `yageo_cc_cq`, `samsung_clr1`, `kyocera_avx_common`, `hre_generic_size_first`, `walsin_01005_series`, and `walsin_alpha_prefix`.
- Other issues: This pass does not magically make every brand/series perfect. Some families are still data-coverage limited, and there are still many non-capacitor or resistor families where some capacitor-oriented columns are naturally blank. The important change is that the main MLCC and MLCC-like passive families now backfill according to their official naming rules instead of depending on generic heuristics or leaving the source blank.
- Handoff notes: If the next task sees stale results in the UI, refresh the page so it picks up the rewritten prepared cache and search sidecar. If future audit work continues, the next safest targets are the remaining long-tail series and the resistor-heavy families that are outside the current MLCC parser scope.


### 2026-03-25 15:55 [direct] Backfilled 38 incomplete passive-capacitor models from official naming rules and synced hidden parquet/search fields

- Received / problem: User asked to inspect all brands with data, locate models whose spec fields were incomplete, search the official or officially searchable naming rules for those brand series, and then backfill the missing spec parameters from those naming rules so future searches and displays follow the official model syntax instead of generic web snippets.
- Verification: Re-ran the backfill script successfully and it reported updated 38 models. Re-checked all three storage layers: components.db now has 0 blank-type rows with a populated model, components_search.sqlite has 0 blank-type rows with a populated model and contains KCA55L7UMF102KL01L, and components_prepared.parquet also has 0 blank-type rows with a populated model. KCA55L7UMF102KL01L now shows ???? = MLCC and hidden _component_type = MLCC in the prepared cache, matching the search sidecar.
### 2026-03-25 20:35 [direct] Fixed PDC MT-series official decoding and rebuilt v5 prepared cache
- Problem: MT43X104K152EHE was still showing raw size code 43 in the UI.
- Fix: Rebuilt components_prepared_v5.parquet from the current parser, synced the legacy prepared cache path, and kept MT models routed through parse_pdc_mt_core() with 43->1812 and 152->1500V decoding.
- Verify: parse_model_rule('MT43X104K152EHE') now returns PDC / 1812 / X7R / 100nF / 1500V / pdc_mt_series.
- Note: If the browser still shows 43, refresh or restart the running Streamlit session so it picks up the new cache.

### 2026-03-26 02:07 [direct] Added a BOM upload progress card with stage updates
- Problem: Large BOM uploads made the page look frozen without any visible feedback.
- Fix: Added a custom progress card UI for BOM uploads, with stages for file reading, matching, export generation, a live progress bar, elapsed time, and row/status counters.
- Verify: component_matcher.py now renders progress updates during BOM processing and compiles successfully.

### 2026-03-26 02:07 [direct] BOM manual mapping UI changed to a toggle button
- Problem: The BOM column-mapping area was always expanded and took too much space.
- Fix: Replaced the always-visible manual mapping block with a toggle button labeled "鎵句笉鍒拌鏍兼墜鍔ㄥ畾浣嶅尮閰嶄綅缃?. Clicking it expands/collapses the original column selector block, and the last chosen mapping is preserved in session state.
- Verify: component_matcher.py compiles successfully after the toggle-state refactor.

### 2026-03-26 02:07 [direct] BOM manual mapping toggle version preserved
- Problem: The BOM column-mapping area was always expanded and took too much space.
- Fix: Added a toggle button to expand/collapse the original manual mapping block while preserving the last selected mapping in session state.
- Verify: component_matcher.py compiles successfully after the refactor.

### 2026-03-26 02:19 [direct] Tightened BOM result table spacing so the download button sits closer to the table
- Problem: The BOM download button was visually separated from the result table by too much blank space.
- Fix: Added a BOM-specific iframe height estimator and a BOM-specific table wrapper class with reduced bottom margin, then switched the BOM result render to use that tighter layout.
- Verify: component_matcher.py compiles successfully after the layout adjustment.

### 2026-03-26 02:23 [direct] Tightened BOM result iframe height again so the download button sits directly under the table
- Problem: Even after the earlier spacing reduction, there was still too much blank space between the BOM table and the download button.
- Fix: Reduced the BOM-specific iframe height estimator further so the table area stays tight and the download button appears immediately below the table.
- Verify: component_matcher.py compiles successfully after the height change.

### 2026-03-26 02:32 [direct] Moved BOM download button into the result table footer and restored table height
- Problem: The BOM result table looked too short, and the download button still felt detached from the table.
- Fix: Restored the BOM iframe height to the previous fuller size and rendered the download button as an inline footer inside the same result-table iframe so it sits directly under the table content.
- Verify: component_matcher.py compiles successfully after the footer/button layout change.

### 2026-03-26 03:41 [direct] Added manual correction rules table and model naming interpreter
- Problem: The system needed a way to manually override wrong factory rules and to explain how a model is parsed from the official naming convention.
- Fix: Added an editable manual correction rules table with save/apply/reset actions, plus a model naming interpreter that breaks down series rules and shows a manual-rule note when a row is matched; also removed the expensive whole-cache manual override pass from prepared-cache loading so the new tools stay usable.
- Verify: component_matcher.py now compiles successfully, and the manual rule and interpreter sections are visible in the new Advanced Tools area.

### 2026-03-26 03:41 [direct] Removed the manual correction rules table and naming interpreter from the live app
- Problem: The manual rule table and naming-rule interpreter were no longer needed in the live UI, but the code needed to be preserved for future restoration.
- Fix: Removed the Advanced Tools section from the main app, disabled manual-rule influence on cache signatures and model parsing, and saved a full backup copy of the current component_matcher.py in backup/component_matcher_20260326_manual_tools_backup.py.
- Verify: component_matcher.py compiles successfully after the removal.

### 2026-03-26 05:14 [direct] Backfilled missing passive-component series names from official naming rules
- Problem: Many passive-component rows still had missing or placeholder series values such as blank, "??", or generic labels, which made models like TDK C5750X5R2E105K230KA and Panasonic ERJ-U06F1001V show incomplete metadata.
- Fix: Added a series backfill layer based on official naming patterns for major passive families (TDK, Murata, Samsung, Yageo, Panasonic, KOA, Vishay, Stackpole, ROHM, Bourns, Walsin, PDC, Taiyo Yuden, plus common electrolytic / film / thermistor / varistor prefixes), wired it into import/prepared-cache paths, and ran a full database backfill on components.db.
- Verify: Full DB scan now shows 1,417,708 rows with placeholder series reduced to blank=687,133, "??"=14,844, and sample models now resolve as TDK C5750X5R2E105K230KA -> series C5750 and Panasonic ERJ-U06F1001V -> series ERJ-U06F. The prepared cache was rebuilt from the updated DB as well.
- 2026-03-26 23:50 Murata series normalization: backfilled official Murata series prefixes into components.db / components_prepared_v5.parquet / components_search.sqlite. GRM/GCM/GRT and other Murata passive families now resolve to official series codes; Murata rows with missing/placeholder series are down to 0.

### 2026-03-27 03:31 [direct] Imported official aluminum electrolytic capacitor libraries and cleaned Nichicon noise rows
- Problem: Aluminum electrolytic capacitor coverage was still incomplete and many rows lacked a trustworthy series value, while Nichicon's official PDF also contributed a few non-product noise rows that were polluting the database.
- Fix: Built an official-source importer for Nichicon, Chemi-Con, and Panasonic aluminum electrolytic capacitor catalogs / naming references, generated `Capacitor/aluminum_electrolytic_library.csv`, rebuilt `components.db`, rebuilt `components_prepared_v5.parquet`, and rebuilt `cache/components_search.sqlite`. Then added a Nichicon series-prefix backfill rule and removed 3 non-product Nichicon noise rows (`16`, `31.5`, `20`) from the CSV, DB, prepared cache, and search sidecar.
- Verify: Aluminum electrolytic rows now total 9,686 with series blank count at 0; Nichicon series blanks are 0; the prepared cache and search sidecar were regenerated, and the new official-source report confirms the imported catalog coverage.

### 2026-03-27 21:54 [direct] Added Jianghai official naming rules and expanded the aluminum electrolytic library
- Problem: Jianghai aluminum electrolytic parts still had incomplete series values in the database, and the importer did not yet include Jianghai official naming-rule sources.
- Fix: Downloaded and parsed Jianghai official catalogs (`CD137U`, `CD263`, `PHLB`, `HPA`), added Jianghai series-prefix extraction rules (`UP`, `BK`, `ELB`, `VLB`, `HLB`, `JLB`, `KLB`, `DPA`, `EPA`, `GPA`, `JPA`, `KPA`, `APA`, `CPA`), wired the Jianghai importer into `aluminum_electrolytic_library_sync.py`, and rebuilt `Capacitor/aluminum_electrolytic_library.csv`, `components.db`, `components_prepared_v5.parquet`, and `cache/components_search.sqlite`.
- Verify: The refreshed report now contains 9,801 aluminum electrolytic rows in total, with 106 Jianghai rows and Jianghai series coverage recorded in the report; sample Jianghai rows now resolve as `ECG2GUP222MC080 -> UP` and `PHR1ELB221MBAB35W -> ELB`, and both the main database and search sidecar include 106 Jianghai records.

### 2026-03-27 22:45 [direct] Tightened Jianghai aluminum electrolytic naming rules from additional series catalogs
- Problem: The Jianghai aluminum electrolytic naming rules were still missing several series-prefix families, so some model strings could not be backfilled to a precise series.
- Fix: Reviewed the extra official Jianghai series catalogs in the provided ZIPs and added additional series-prefix mappings to the Jianghai rule set, including `ABZ`, `DQH/WQH/EQH/GQH`, `VNF/GNF/WNF`, `VPR/GPR`, `EVA/GVA/JVA`, `EVZ/GVZ/JVZ`, and `ELA/VLA/HLA/JLA/KLA/VVA/HVA/KVA`.
- Verify: `component_matcher.py` and `aluminum_electrolytic_library_sync.py` compile successfully, and the latest rebuild completed successfully so the updated naming rules are available in the database and search sidecar.

### 2026-03-28 07:34 [direct] Expanded Jianghai aluminum electrolytic row-level import from additional official series catalogs
- Problem: The Jianghai importer only covered the earlier core series catalogs, so several official series PDFs in the local Jianghai archive were not yet contributing row-level records or series names to the database.
- Fix: Added row-level import support for the extra official Jianghai series catalogs (`CD293`, `CD29H`, `CD29NF`, `CD137S`, `CDA220`, `CDC220`, `PHLA`, `PHVA`) and extended the Jianghai naming-rule mapping to cover the newly observed series families (`CBZ`, `KBZ`, `VBZ`, `WBZ`, `XBZ`) on top of the earlier rule set.
- Verify: Rebuilt `Capacitor/aluminum_electrolytic_library.csv`, `components.db`, `components_prepared_v5.parquet`, and refreshed `cache/components_search.sqlite` by copying the newly populated `components_search` table from the rebuilt main DB. Current Jianghai coverage is 448 rows with series blank count at 0; the main DB search table has 1,427,769 rows and the search sidecar is synchronized to the same row count.

### 2026-03-28 08:49 [direct] Fixed electrolytic capacitor tolerance parsing for compact spec strings
- Problem: Compact electrolytic spec strings such as `470.0uF_±20%16V_插件,D6.3xL12mm/脚距2.5mm` were letting the tolerance parser swallow the adjacent voltage/suffix text, which caused the rendered `容值误差` field to show a corrupted value like `+/-2016V_插件`.
- Fix: Tightened `parse_tolerance_token()` so it only accepts a leading tolerance prefix, and added spec-string preprocessing to split underscore-separated fragments and tolerance/voltage boundaries before token parsing.
- Verify: Re-running the sample now yields a clean electrolytic spec summary with `容值误差=20%`, `耐压（V）=16V`, `尺寸(mm)=6.3*12mm`, and the rendered spec table shows the correct column values instead of the corrupted tolerance text.

### 2026-03-28 09:30 [direct] Added a standalone build runner to separate database rebuilds from the Streamlit UI
- Problem: `component_matcher.py` still mixed the Streamlit UI path and the maintenance/rebuild path in one module, which made rebuild actions harder to isolate from the runtime page and kept the app entrypoint overloaded.
- Fix: Added `component_matcher_build.py` as a standalone build runner that boots `component_matcher.py` in a headless dummy-Streamlit context and exposes explicit `--db`, `--search-index`, `--prepared-cache`, `--backfill-series`, and `--all` actions; also added a build-mode environment guard in `component_matcher.py` so the automatic database refresh is skipped during build imports.
- Verify: `component_matcher.py` and `component_matcher_build.py` both compile successfully. The new build runner successfully imports the module and starts a search-index rebuild job without launching the interactive UI, confirming the maintenance path is now separable from the page runtime.

### 2026-03-28 10:48 [direct] Shrunk the search sidecar and switched search-index rebuilds to the prepared cache fast path
- Problem: `components_search.sqlite` was still carrying several maintenance-only columns and rebuilding the sidecar from the raw database was too slow for comfortable iteration.
- Fix: Removed redundant search-sidecar columns such as `_value_text`, `_power`, `_volt`, `_tol_kind`, `_tol_num`, and `_model_rule_authority`, preserved sparse values as `NULL` to reduce SQLite storage overhead, and changed the search-index rebuild path to prefer `components_prepared_v5.parquet` before falling back to the raw database. Also added bulk-load pragmas and safe multi-row insert chunk sizing so the search rebuild no longer hits SQLite variable-count limits.
- Verify: Rebuilt `cache/components_search.sqlite` successfully. The sidecar row count remains `1,427,769`, the schema version is now `3`, and the file size dropped from `545,431,552` bytes to `508,895,232` bytes while staying synchronized with `components.db` and the current prepared cache.

### 2026-03-28 12:16 [direct] Split the search sidecar into family tables and added per-source normalized caches for incremental updates
- Problem: The search sidecar was still a single wide table, which kept query indexes broader than necessary, and `update_database()` still re-parsed every official source file on each refresh even when only a few sources changed.
- Fix: Split the sidecar into family tables (`components_search_core`, `components_search_resistor`, `components_search_capacitor`, `components_search_value`, `components_search_varistor`) with family-specific column sets and indexes; updated the search lookup path to query the matching family table for exact-model and typed-spec candidates; and added per-source normalized caches under `cache/source_normalized/` so `update_database()` now reuses cached normalized source frames unless the source file signature changes.
- Verify: `component_matcher.py` and `component_matcher_build.py` compile successfully. The rebuilt sidecar now contains 5 family tables plus `search_meta`, with counts `core=1,427,772`, `resistor=1,289,147`, `capacitor=125,764`, `value=0`, and `varistor=12,826`; the final `components_search.sqlite` size is `418,566,144` bytes. A real resistor query (`0402 1ohm 5%`) now resolves to 60 candidate pairs through the resistor family table, and exact model lookup for `C5750X5R2E105K230KA` still resolves through the core table.

### 2026-03-28 13:28 [direct] Upgraded BOM upload to support workbook-level multi-sheet matching and original-workbook export
- Problem: BOM uploads were still treated as a single DataFrame, so multi-sheet workbooks only matched one sheet and the downloaded file flattened the result into a new single-sheet workbook instead of preserving the original pages and format.
- Fix: Added workbook-aware BOM loading that reads all sheets/pages from uploaded Excel files, introduced per-sheet mapping state and sheet selector UI so different pages can be browsed independently, processed every sheet in the workbook during matching, and changed BOM export to write match columns back into the original workbook structure instead of regenerating a flat result sheet.
- Verify: `component_matcher.py` and `component_matcher_build.py` compile successfully after the workbook-level BOM changes. The code path now preserves sheet-level results in session state and uses the original workbook bytes when generating the download payload.

### 2026-03-28 14:02 [direct] Removed pandas categorical deprecation spam and filtered empty frames before concat
- Problem: The app console was repeatedly printing `DeprecationWarning` for `pd.api.types.is_categorical_dtype(...)` and a `FutureWarning` from `pd.concat(...)` when some intermediate frames were empty or all-NA, which made the Streamlit terminal noisy during normal page operation.
- Fix: Replaced all remaining `is_categorical_dtype` checks with `isinstance(series.dtype, pd.CategoricalDtype)` and tightened the concat helper to ignore empty/all-NA DataFrames before concatenation so pandas no longer emits the deprecation and future warnings.
- Verify: `component_matcher.py` and `component_matcher_build.py` both pass `py_compile` after the warning cleanup.

### 2026-03-28 13:50 [direct] Replaced the empty Streamlit search label to stop accessibility warnings
- Problem: The search box used `st.text_area("")`, which causes Streamlit to emit a label accessibility warning and print a traceback-like warning block in the cmd window during normal app startup.
- Fix: Changed the search input to `st.text_area("查询输入", ..., label_visibility="collapsed")` so the widget keeps the same appearance while satisfying Streamlit's label requirement and silencing the warning.
- Verify: `component_matcher.py` and `component_matcher_build.py` both pass `py_compile` after the label fix.

### 2026-03-28 14:03 [direct] Added a lightweight console-noise filter for nonessential pandas and Streamlit warnings
- Problem: Even after fixing the empty-label widget, the runtime could still surface benign warning noise from pandas deprecations or Streamlit's own nonfatal logger output, which distracts from real errors.
- Fix: Added a small startup filter that ignores pandas `DeprecationWarning` / `FutureWarning` and raises Streamlit logger thresholds to `ERROR`, while keeping actual exceptions and tracebacks visible.
- Verify: `component_matcher.py` and `component_matcher_build.py` both pass `py_compile` after the console-noise filter was added.

### 2026-03-28 14:14 [direct] Swept backup component matcher scripts for the same warning noise
- Problem: Several historical `component_matcher.py` backups still used the old empty search label and older pandas categorical checks, so launching an older snapshot could still emit the same nonessential warning noise.
- Fix: Batch-updated the backup scripts under `backup/` to use the hidden search label variant and the newer categorical handling pattern so they no longer trigger the same Streamlit accessibility warning or pandas deprecation spam.
- Verify: A full scan of the backup `component_matcher.py` snapshots no longer finds the empty search label or `is_categorical_dtype(...)` usage patterns that previously caused the warning output.

### 2026-03-28 14:19 [direct] Wrapped all hot-path DataFrame concatenations with a warning-suppressing helper
- Problem: The runtime was still surfacing a repeated pandas `FutureWarning` at the component-merge concat site, making the cmd window noisy even though the behavior was nonfatal.
- Fix: Added a small `safe_concat_dataframes()` helper that wraps `pd.concat(...)` in a targeted `warnings.catch_warnings()` block for the known empty/all-NA future warning, and switched the hot-path concat call sites to use it.
- Verify: `component_matcher.py` and `component_matcher_build.py` both pass `py_compile` after the concat helper change, and the file no longer has direct `pd.concat(...)` calls outside the helper itself.

### 2026-03-28 14:31 [direct] Extended the warning cleanup into the MLCC import helper
- Problem: The MLCC import helper also used raw `pd.concat(...)` in several merge paths, which could surface the same pandas empty/all-NA `FutureWarning` during import or rebuild tasks.
- Fix: Added the same `safe_concat_dataframes()` wrapper and a top-level filter to `mlcc_excel_importer.py`, then switched the master-sheet merge, the full master refresh, and grouped merge paths to the safe concat helper.
- Verify: `component_matcher.py`, `component_matcher_build.py`, and `mlcc_excel_importer.py` all pass `py_compile` after the import-helper cleanup.

### 2026-03-28 14:51 [direct] Removed the BOM auto-start explanation text from the manual-mapping area
- Problem: The BOM manual-mapping section displayed an extra explanatory caption saying the current upload and sheet mapping would auto-start BOM matching, which the user wanted hidden from the page.
- Fix: Removed that caption line from the BOM matching flow so only the progress card and actual results remain visible.
- Verify: `component_matcher.py` and `component_matcher_build.py` both pass `py_compile` after the caption removal.

### 2026-03-28 15:03 [direct] Kept the BOM completion card stable when expanding the manual-mapping panel
- Problem: Clicking the manual-mapping toggle could visually reset the top BOM status card back to a read-phase appearance even when the uploaded file and mapping had not changed, which made the page jump from the completed state to a less useful intermediate state.
- Fix: Added a cached-result check so the BOM status card stays in the completed/downloadable state when the same workbook is already matched, and only falls back to the read-phase card when no cached result exists for the current upload.
- Verify: `component_matcher.py` and `component_matcher_build.py` both pass `py_compile` after the status-card stabilization change.

### 2026-03-28 15:17 [direct] Moved the BOM result summary text into the completion card
- Problem: The "解析完成" and "器件类型分布" lines were rendered as separate captions outside the BOM completion card, so the completion summary felt detached from the finished state the user wanted.
- Fix: Added a completion-only summary block inside the BOM progress card HTML and moved the summary lines into the finished-state payload so those texts now appear inside the completed card rather than below it.
- Verify: `component_matcher.py` passes `py_compile` after the completion-card summary merge.

### 2026-03-28 15:20 [direct] Moved the BOM parse explanation column behind the status column
- Problem: The BOM result table showed the "解析说明" column in the middle of the table, while the user wanted that explanation to appear after the status column on the right side.
- Fix: Reordered the BOM display column list so "解析说明" is rendered after "状态" in the matching results table.
- Verify: `component_matcher.py` passes `py_compile` after the BOM column-order update.

### 2026-03-28 15:23 [direct] Removed the manual-mapping section title text
- Problem: The left-side title "BOM列识别与手动指定" was still visible above the manual mapping controls, but the user wanted only the button and controls without that title text.
- Fix: Removed the title markdown from the manual-mapping header row so the section now shows only the button and the actual mapping controls.
- Verify: `component_matcher.py` passes `py_compile` after the title-text removal.

### 2026-03-28 15:27 [direct] Fixed the BOM completion-card summary variable order
- Problem: After moving the BOM parse explanation into the completion card, the completion-state summary referenced `success_count` before those counts were computed, causing the BOM upload flow to fail with a NameError.
- Fix: Computed the current sheet result DataFrame and success/fail/no-match counters before building the completion card payload, then passed those values into the summary block.
- Verify: `component_matcher.py` passes `py_compile` after the summary-variable ordering fix.

### 2026-03-28 15:35 [direct] Reduced empty vertical space in search result tables
- Problem: The query result sections were using oversized iframe heights for small result sets, leaving large blank areas under the result table and between result blocks.
- Fix: Tightened the iframe height estimate for search result tables, using a compact path for small row counts so the table blocks shrink closer to their actual content height.
- Verify: `component_matcher.py` passes `py_compile` after the result-height adjustment.

### 2026-03-28 15:40 [direct] Compressed the small-result iframe height further
- Problem: The first height reduction still left too much blank space below short search result tables.
- Fix: Lowered the compact iframe height baseline and per-row estimate again, and widened the compact path to cover small result sets more aggressively.
- Verify: `component_matcher.py` passes `py_compile` after the second result-height compression.

### 2026-03-28 15:45 [direct] Tightened the search result table spacing again
- Problem: The compact search result blocks were still leaving too much blank space before the next section.
- Fix: Reduced the search result wrapper bottom margin to zero and lowered the compact iframe height baseline/per-row estimate further so short result tables sit closer to the following content.
- Verify: `component_matcher.py` passes `py_compile` after the third spacing reduction.

### 2026-03-28 15:50 [direct] Compressed the search result iframe one more time
- Problem: The search result iframe was still noticeably taller than the actual table content, leaving the query title too far below the table.
- Fix: Lowered the compact search-result height estimate again and widened the compact path so short result tables can sit directly above the query title with less empty gap.
- Verify: `component_matcher.py` passes `py_compile` after the fourth search-result spacing reduction.

### 2026-03-28 15:55 [direct] Reduced query title and section title spacing
- Problem: Even after compressing the result iframe, the text blocks below the table still carried extra top/bottom spacing that kept the next query section too far away.
- Fix: Reduced the margins on the query title, section titles, and result titles so the search output stacks more tightly with less visual whitespace.
- Verify: `component_matcher.py` passes `py_compile` after the title-spacing reduction.

### 2026-03-28 16:00 [direct] Moved the query content label into the result block
- Problem: The `查询内容：...` line was still rendered outside the result iframe, so it appeared below the empty gap instead of inside the red-box area.
- Fix: Rendered the query content label as an inline footer inside the result HTML block, so it now appears inside the result section instead of below it.
- Verify: `component_matcher.py` passes `py_compile` after moving the query label into the result block.

### 2026-03-28 19:41 [direct] Turned the query content line into a bordered subsection
- Problem: The query content line was close to the table, but it still looked like a plain line instead of a clearly separated lower subsection.
- Fix: Replaced the plain query line with a bordered inline block that uses a left accent bar, a section label (`└ 查询内容`), and a value line underneath so it reads like the next block below the table.
- Verify: `component_matcher.py` passes `py_compile` after the query-subsection styling update.

### 2026-03-28 21:04 [direct] Wrapped each result into a single card block
- Problem: The query content subsection was still visually separate from the table, so each model result did not read like one complete block.
- Fix: Wrapped the whole result table plus query footer inside a shared bordered card container, so one model now appears as one self-contained section.
- Verify: `component_matcher.py` passes `py_compile` after the card-wrapper update.

### 2026-03-28 21:09 [direct] Renamed the part-info section header
- Problem: The section header above the matched part info still read `料号资料`, which was too generic for the new query-result card layout.
- Fix: Renamed the header to `匹配料号资料` so the matched item card is clearer and consistent with the rest of the result section.
- Verify: `component_matcher.py` passes `py_compile` after the header rename.

### 2026-03-28 21:11 [direct] Simplified the query footer and renamed the match section
- Problem: The lower blue box still showed the `查询内容` label even though the user only wanted the query value, and the second section title was still too long.
- Fix: Removed the `查询内容` label from the blue footer block so only the query value remains inside the bordered box, and renamed `其他品牌资料（含推荐等级）` to `匹配结果`.
- Verify: `component_matcher.py` passes `py_compile` after the footer and section-title update.

### 2026-03-28 21:36 [direct] Merged the part-info area into the match card for the `料号` flow
- Problem: In the `料号` search flow, the matched part info still rendered as a separate block, and the query value sat below the card instead of being part of the same visual section.
- Fix: Rendered `匹配料号资料` and `匹配结果` together inside one bordered card for the `料号` branch, with the query value moved into a pill beside the section title; the standalone lower query box is no longer used for this flow.
- Verify: `component_matcher.py` passes `py_compile` after the combined-card update.

### 2026-03-28 21:44 [direct] Added extra spacing after the `料号` match card
- Problem: The combined `料号` card was still visually too close to the next model section, making the block feel abruptly cut off.
- Fix: Added a small spacer after each `料号` match card so the next model block starts with clearer separation.
- Verify: `component_matcher.py` passes `py_compile` after the spacing tweak.

### 2026-03-28 21:57 [direct] Added a bottom footer band to the `料号` match card
- Problem: The `料号` block still looked visually cut on the bottom edge, and the transition to the next model card felt too abrupt.
- Fix: Added a subtle bottom footer band inside the combined `料号` card, normalized the card padding to feel more symmetrical, and kept a slightly larger spacer after the card so the next model block sits farther away.
- Verify: `component_matcher.py` passes `py_compile` after the footer-band update.

### 2026-03-28 22:10 [direct] Increased the `料号` card iframe height so the bubble frame is not clipped
- Problem: The combined `料号` card still got clipped at the bottom in the iframe, so the bubble frame did not look complete.
- Fix: Increased the iframe height estimate for the `料号` branch and added a small extra height buffer so the card border and footer band can render fully.
- Verify: `component_matcher.py` passes `py_compile` after the height adjustment.

### 2026-03-28 22:17 [direct] Tightened the `料号` card height and spacing
- Problem: The combined `料号` bubble still left too much blank space before the next model block, so the frame did not look complete.
- Fix: Reduced the iframe height estimate, lowered the post-card spacer, and kept the internal footer band so the card still closes visually without feeling cut off.
- Verify: `component_matcher.py` passes `py_compile` after the height/spacing adjustment.

### 2026-03-28 23:47 [direct] Raised the `料号` iframe minimum height to prevent bubble clipping
- Problem: The combined `料号` card still rendered with a clipped bottom edge in the actual browser, so the bubble looked cut off even though the content was logically complete.
- Fix: Increased the minimum iframe height for the `料号` branch to leave enough room for the outer border and footer band to render fully.
- Verify: Browser check showed the iframe height increased to 888px while the card body rendered to 902px, which fully enclosed the block without clipping.

- 2026-03-29 10:46 ?????????????????? spacer????????/???????????

### 2026-03-29 11:02 [direct] Capped result tables to about 10 visible rows
- Problem: The single-model result card still felt too tall because the internal result table could expand well beyond the desired visible height, leaving the bubble frame feeling oversized.
- Fix: Reduced the table wrapper max-height to `min(460px, 44vh)` for both normal and BOM result tables so only about ten rows remain visible before the table scrolls internally.
- Verify: `component_matcher.py` passes `py_compile` after the height cap adjustment.

### 2026-03-29 11:18 [direct] Moved the model pill next to the `匹配料号资料` title
- Problem: The query/model pill was stuck on the far right of the header row instead of sitting in the blank space immediately after `匹配料号资料`.
- Fix: Switched the header row to left-aligned flex layout and moved the pill inline after the title so it lands in the red-box area the user marked.
- Verify: `component_matcher.py` passes `py_compile` after the header layout change.

### 2026-03-29 11:27 [direct] Tightened the single-model bubble spacing again
- Problem: The single-model bubble still left too much vertical whitespace between the result table card and the next block.
- Fix: Reduced the combined card iframe floor to `560px` and tightened the card gap/padding so the model block sits closer to the next section.
- Verify: `component_matcher.py` passes `py_compile` after the spacing adjustment.
- 2026-03-29: 进一步收紧匹配结果卡片布局，将结果表内部最大高度从 460px 降到 420px，并把单型号卡 iframe 估高下调到更贴近实际内容，目标是缩短结果卡与下一型号卡之间的空白距离。

### 2026-03-29 11:39 [direct] Switched result cards to auto-fit iframe height
- Problem: The blank area between the result bubble and the next bubble was still being stretched by fixed iframe height estimates, even though the inner tables themselves were already capped to about ten visible rows.
- Fix: Added `Streamlit.setFrameHeight(...)` reporting inside the iframe HTML, tightened the card padding/gaps, and shortened the divider/title spacing between the `匹配料号资料` and `匹配结果` sections so the bubble can shrink to its actual content height instead of leaving dead space.
- Verify: `component_matcher.py` passes `py_compile` after the auto-height and spacing cleanup.
### 2026-03-29 11:58 [direct] Standardized visible rows to about ten per table
- Problem: Result tables still showed too few visible rows because the iframe and wrapper heights were being capped too aggressively.
- Fix: Raised the result-table and BOM-table wrapper max-heights to `min(560px, 52vh)`, adjusted the iframe estimates to cap around ten visible rows, and widened the single-model card estimate so the table can scroll internally after roughly ten rows.
- Verify: `component_matcher.py` and `component_matcher_build.py` pass `py_compile` after the height update.
### 2026-03-29 12:04 [direct] Corrected the lingering 420px table cap
- Problem: One older CSS block still capped `.result-table-wrap` and `.bom-result-table-wrap` at `min(420px, 40vh)`, which kept the visible rows below the requested ten-row target.
- Fix: Updated the remaining CSS caps to `min(560px, 52vh)` so the result tables can expose about ten rows and scroll internally instead of compressing the viewport.
- Verify: `component_matcher.py` and `component_matcher_build.py` pass `py_compile` after the final table-height correction.
### 2026-03-29 12:18 [direct] Reduced the gap between single-model bubble cards
- Problem: The large blank area between one model's `匹配结果` table and the next model's `匹配料号资料` card was still being caused by the outer single-model iframe using an overly tall minimum height.
- Fix: Reworked `estimate_match_card_iframe_height()` to size the combined card around roughly 10 visible result rows and removed the old `-36` offset at the `components.html(...)` call site, so the next bubble can sit much closer to the previous one.
- Verify: `component_matcher.py` passes `py_compile` after the single-model iframe height adjustment.
### 2026-03-29 12:46 [direct] Restored a real bottom closure band for single-model bubbles
- Problem: The single-model combined result card still looked cut off because the iframe-local `.match-card-footer` was zeroed out and the card HTML never appended a footer element, so the bottom edge could never visually close.
- Fix: Gave the iframe-local `.match-card-footer` a visible rounded closure band, appended `<div class="match-card-footer"></div>` to the single-model `match_card_html`, and raised `estimate_match_card_iframe_height()` to reserve footer space while still targeting roughly 10 visible result rows.
- Verify: `component_matcher.py` passes `py_compile` after the single-model footer restoration.
### 2026-03-29 12:53 [direct] Shortened the single-model bubble bottom band
- Problem: After restoring the bottom closure band, the bubble footer became much taller than the user wanted even though the visible row count was now correct.
- Fix: Reduced the footer reservation from `112px` to `28px`, tightened its top margin, and lowered the single-model iframe height estimate range so the bubble bottom ends much closer to the horizontal scrollbar while keeping about 10 visible rows.
- Verify: `component_matcher.py` passes `py_compile` after the footer-height reduction.
### 2026-03-30 06:06 [direct] Completed Jianghai aluminum parsing, reverse-spec rules, and stock-site expansion
- Problem: Jianghai aluminum capacitors were still missing a usable closed loop: the electrolytic spec parser did not reliably capture `工作温度` / `寿命（h）` / `安装方式` / `特殊用途`, the Jianghai model-rule reverse parser only covered part of the naming scheme, and the Jianghai library had not been expanded with stock-site models, which also left `WBZ` / `GBZ` style high-voltage parts incorrectly decoded on rated voltage.
- Fix: Extended `component_matcher.py` so aluminum-electrolytic text queries can parse and filter `容值`、`误差`、`耐压`、`工作温度`、`寿命`、`尺寸`、`安装方式` and `特殊用途`, added Jianghai family-specific reverse rules for polymer / hybrid / radial / snap-in series, and stopped Jianghai source rows from being overwritten by conflicting model-rule guesses when exact source data already exists. Extended `aluminum_electrolytic_library_sync.py` to ingest Jianghai models from the local JLC stock archive, crawl representative JLC detail pages for series-level `工作温度` / `寿命（h）` / `脚距（mm）`, merge those values back into official Jianghai rows, and refresh the aluminum-electrolytic library, database, prepared cache, and search index.
- Verify: `parse_electrolytic_spec_query("铝电容_270uF_±20%_16V_-25-105℃_5000h_6.6×7.2mm_贴片_消费")` now returns the expected structured fields; Jianghai aluminum rows increased from `638` to `866`; exact rows such as `ECS2WBZ471MLA350040V` and `ECS2GBZ391MLB300035V` now resolve to `450V/-25~85℃/3000h` and `400V/-40~85℃/3000h`; `python aluminum_electrolytic_library_sync.py`, `python -m py_compile component_matcher.py aluminum_electrolytic_library_sync.py`, database spot checks, reverse-spec spot checks, and a local Streamlit smoke test all passed.

### 2026-03-30 13:16 [direct] Expanded Jianghai aluminum library to 1318 rows and corrected screw-terminal voltage decoding
- Problem: The second Jianghai expansion pass uncovered two quality issues: several official PDF table rows packed multiple Jianghai models into one cell and were being imported as concatenated fake models, and `CD137U/CD137S` screw-terminal rows could decode to impossible voltages like `22000V` because the builder was picking up the page capacitance range instead of the actual series voltage tier.
- Fix: Reworked `aluminum_electrolytic_library_sync.py` so Jianghai PDF row parsing can split one table cell into multiple models for `CD137U` / `CD137S` / `CD293` / `CD29H` / `CD29NF` and the `CDA` / `CDC` axial families, added exact screw-series voltage maps for `GUP/WUP/VPR/GPR/WPR/HPR`, and switched the screw-terminal builders to use those series rules instead of the broken page-level voltage capture. Regenerated the aluminum-electrolytic CSV/report, refreshed the Jianghai slice in `components.db`, then incrementally rewrote the prepared cache and rebuilt the search sidecar database so the new Jianghai data was available to the live search path without another full DB rebuild.
- Verify: Jianghai aluminum rows increased from `1234` to `1318`, the total aluminum CSV now contains `11013` rows, and representative models now resolve correctly in both the database and model-rule reverse path: `ECG2GUP222MC080 -> 400V`, `ECG2WUP182MC080 -> 450V`, `ECG2VPR222MC080 -> 350V`, `ECG2GPR182MC080 -> 400V`, `ECG2WPR152MC080 -> 450V`, `ECG2HPR102MC080 -> 500V`; `python -m py_compile aluminum_electrolytic_library_sync.py`, `python aluminum_electrolytic_library_sync.py`, DB spot checks, prepared-cache spot checks, and search-sidecar rebuild all passed.

### 2026-03-30 16:02 [direct] Split MLCC inch size from vendor-specific length/width/thickness
- Problem: The MLCC result tables only showed `尺寸（inch）` and treated package code as the only size signal, which hid the fact that different vendors can have different real `长/宽/厚` for the same inch code. The PDC `MT` parser also stopped at size/material/value/tolerance/voltage and did not decode the official thickness code into real dimensions.
- Fix: Updated `component_matcher.py` so MLCC display schemas now keep `尺寸（inch）` as a standalone package-code column and add separate `长度(mm)` / `宽度(mm)` / `厚度(mm)` columns. Added `长度（mm）` / `宽度（mm）` / `高度（mm）` as preserved library fields, threaded them through model-rule merge/backfill and display formatting, and extended the PDC `MT` rule decoder to parse thickness code `G` and emit official dimensions for `MT32X103K202EGZ` (`3.30±0.40 / 2.50±0.30 / 2.50±0.30`) instead of mixing them into `尺寸（inch）`.
- Verify: `python -m py_compile component_matcher.py` passed; `parse_pdc_mt_core("MT32X103K202EGZ")` now returns separate `长度（mm）` / `宽度（mm）` / `高度（mm）`; `select_component_display_columns(..., "MLCC")` now exposes separate MLCC dimension columns; `FS15B105K6R3PKG` still shows `尺寸（inch）=0402` with the new dimension columns blank rather than incorrectly deriving fake vendor dimensions. A full `component_matcher_build.py --db --prepared-cache --search-index` refresh was attempted but did not complete in a reasonable time, so the code path was validated directly through module-level checks instead of a full rebuild.

### 2026-03-30 16:24 [direct] Enabled Samsung MLCC vendor-size backfill during display rendering
- Problem: Even after splitting `尺寸（inch）` from `长/宽/厚`, the live MLCC result tables still showed blank physical dimensions for most Samsung rows because the database only stored the package code and the Samsung dimension cache had never been connected to the display path.
- Fix: Added a Samsung MLCC dimension backfill layer to `component_matcher.py` that reads `cache/samsung_all_statuses_base.json` plus `cache/samsung_package_cache.json`, maps packaged part numbers like `CL05A105KQ5NNNC` back to Samsung's base part records, and fills `长度（mm）` / `宽度（mm）` / `高度（mm）` during MLCC parsing and result-table rendering without changing the meaning of `尺寸（inch）`. Also added a small parser for explicit dimension text in freeform notes so rows that already carry plain-text mm dimensions can reuse the same display columns.
- Verify: `python -m py_compile component_matcher.py` passed; `parse_samsung_cl("CL05A105KQ5NNNC")` now returns `1.00±0.05 / 0.50±0.05 / 0.50±0.05`; `build_component_display_row()` preserves those values under independent MLCC `长度/宽度/厚度` columns; `select_component_display_columns()` on an existing Samsung workbook row now outputs `尺寸（inch）=0402` plus the three Samsung physical-dimension columns without requiring a full database rebuild.

### 2026-03-30 17:23 [direct] Added generic MLCC datasheet-based length/width/thickness backfill for non-Samsung brands
- Problem: After Samsung support landed, most other MLCC brands still only showed `尺寸（inch）` because the database usually stored an LCSC detail link rather than direct official dimensions, and the live display path had no generic way to turn those datasheets into `长/宽/厚`.
- Fix: Extended `component_matcher.py` with a cached MLCC LCSC datasheet backfill layer. The new path extracts the real PDF URL from `https://www.lcsc.com/datasheet/Cxxxxxxx.pdf`, parses the first pages with `pypdf`, finds size-table rows to recover `长度（mm）/宽度（mm）/高度（mm）`, and stores the result in `cache/mlcc_lcsc_dimension_cache.json` for reuse. Also added brand-aware nominal model decoding for Murata and TDK so `尺寸（inch）` remains separate while Murata/TDK rows can still backfill physical dimensions even when the PDF only exposes part-number dimension codes. The merge logic now prefers richer `±` dimension strings over bare nominal numbers, so datasheet-derived tolerances can override earlier coarse values.
- Verify: `python -m py_compile component_matcher.py` passed; direct lookups now resolve `CC0100KRX7R6BB391 -> 0.4±0.02 / 0.2±0.02 / 0.2±0.02`, `01R5N100J160CT -> 0.40±0.02 / 0.20±0.02 / 0.20±0.02`, `C0402X7R1A102K020BC -> 0.40±0.02 / 0.20±0.02 / 0.20±0.02`, and `GRM43R5C2A103JD01L -> 4.50 / 3.20 / 1.80`; row-level `infer_mlcc_dimension_fields_from_record()` checks on database rows also confirmed Samsung, TDK, Yageo, Walsin, and Murata results now return independent physical-dimension fields without changing the meaning of `尺寸（inch）`.

### 2026-03-30 18:27 [direct] Attempted real-page MLCC spot checks and confirmed the browser automation gap
- Problem: A real browser-level verification was needed after the MLCC dimension backfill landed, but the long-running local Streamlit session on port `8501` did not respond to automated `搜索` clicks, which made it unsafe to claim an end-to-end page check had passed.
- Fix: Installed `playwright`, downloaded a fresh Chromium runtime, and started a clean Streamlit session on port `8502` to retry the page test in a new browser context. Browser automation could fill the search box and locate the visible `搜索` button, but even after waiting over four minutes the page still did not render the result section under automation. To avoid a false pass, I fell back to verifying the exact same display-side enrichment path on real database rows with `infer_mlcc_dimension_fields_from_record()` rather than pretending the browser run succeeded.
- Verify: `http://127.0.0.1:8501` and `http://127.0.0.1:8502` both returned `200`; the browser automation consistently found the search textarea plus the visible `搜索` button on `8502`; however no result section appeared under automated clicks. Display-path verification on live rows still confirmed `CL05A105KQ5NNNC -> 1.00±0.05 / 0.50±0.05 / 0.50±0.05`, `C0402X7R1A102K020BC -> 0.40±0.02 / 0.20±0.02 / 0.20±0.02`, `CC0100KRX7R6BB391 -> 0.4±0.02 / 0.2±0.02 / 0.2±0.02`, `01R5N100J160CT -> 0.40±0.02 / 0.20±0.02 / 0.20±0.02`, and `GRM43R5C2A103JD01L -> 4.50 / 3.20 / 1.80`.

### 2026-03-30 20:43 [direct] Added visible progress feedback and exact-model DB fallback for normal search
- Problem: The normal search path could feel frozen because it had no progress card like the BOM flow, and when an exact part number was not fully covered by naming rules the code could fall back to loading the full prepared library before re-detecting specs, causing long first-hit waits with no clear “matching in progress” feedback.
- Fix: Updated `component_matcher.py` to wrap manual search input in a Streamlit form, added a reusable search-progress state builder on top of the existing BOM progress card UI, and threaded stage updates through the normal search flow so the page now shows `准备开始 / 解析输入 / 载入候选库 / 执行匹配 / 整理结果 / 搜索已完成` with current input, path, candidate count, and elapsed time. Also added `resolve_search_query_dataframe_and_spec()` so exact-looking part numbers first try a direct DB lookup via `load_component_rows_by_clean_model()` before falling back to a full-library load.
- Verify: `python -m py_compile component_matcher.py` passed. Module-level checks confirmed `resolve_search_query_dataframe_and_spec("FS31X105K101EPG") -> fast_query, 318 rows` and `resolve_search_query_dataframe_and_spec("FM21X102K101PXG") -> fast_query, 285 rows` without forcing a full prepared-data load. A fresh local Streamlit session on `http://127.0.0.1:8504` returned `200`; browser automation still did not provide a trustworthy end-to-end submit signal in headless mode, so the verification for this pass remains code-path and local-server based rather than a false browser-pass claim.

### 2026-03-30 21:27 [direct] Reduced multi-line search latency with batched exact-row prefetch and candidate-frame caches
- Problem: After adding visible progress, multi-line manual searches still felt slower than before because the normal search loop handled each line serially. Even when every input already matched a fast exact-part path, the code still reloaded exact model rows and rebuilt candidate frames line by line, so four to eight exact part numbers could accumulate several seconds of avoidable repeated DB work.
- Fix: Extended `component_matcher.py` with `load_component_rows_by_clean_models_map()` so exact-looking part numbers can batch-prefetch their source rows in one search-index pass, then updated `load_search_dataframe_for_query()` and `resolve_search_query_dataframe_and_spec()` to reuse those prefetched rows instead of calling `load_component_rows_by_clean_model()` for every line. Also added a per-request `query_frame_cache` plus a bounded session-level `_query_dataframe_cache` so repeated same-input / same-spec lookups can reuse candidate frames across the current run and later searches in the same browser session.
- Verify: `python -m py_compile component_matcher.py` passed. Same-process timing comparison on representative multi-line exact-part batches showed a reduction from `3.834s -> 2.750s` for a 4-line batch (`0402B333K250CT / 0805X225K500CT / 0402B333K250CT / WR12W1R00FTL`) and `5.051s -> 4.613s` for an 8-line mixed exact-part batch; exact-row prefetch alone added only about `0.396s` while removing repeated per-line exact-row DB fetches. The search flow now also reports when a line is using `本轮缓存` or `会话缓存`, so repeated searches are both faster and easier to explain.

### 2026-03-30 21:45 [direct] Removed live LCSC datasheet fetching from manual-search result rendering
- Problem: Manual search still felt extremely slow even after query-side optimizations because the UI was spending most of its time in the `正在生成展示内容` stage, not in matching. Profiling on `0402B333K250CT` showed the heavy cost came from MLCC display enrichment calling `lookup_mlcc_lcsc_dimension_fields()` row by row during result-table rendering, which could trigger live LCSC datasheet/PDF fetches just to backfill `长度（mm）/宽度（mm）/高度（mm）`.
- Fix: Added an `allow_online_lookup` gate to the MLCC dimension enrichment chain in `component_matcher.py` (`lookup_mlcc_lcsc_dimension_fields -> infer_mlcc_dimension_fields_from_record -> enrich_mlcc_dimension_fields_in_record/dataframe -> build_component_display_row/select_component_display_columns`) and defaulted the live search display path to cache-only behavior. Search results now still use model rules, brand-specific decoders, local notes, and any previously cached LCSC dimensions, but they no longer block the UI by fetching remote datasheets while rendering the table.
- Verify: `python -m py_compile component_matcher.py` passed. Same-process timings dropped to `0402B333K250CT: total 0.43s (resolve 0.216s / match 0.015s / prepare_show 0.199s)`, `0402 33nF 25V X7R 10%: total 0.267s`, and the representative 4-line batch (`0402B333K250CT / 0805X225K500CT / 0402B333K250CT / WR12W1R00FTL`) completed in `1.114s`, confirming the former multi-second render stall was removed from the manual-search path.

### 2026-03-30 22:22 [direct] Fixed Walsin `0402X105K250CT` MLCC dimensions and hardened ambiguous `0402/1005` cache parsing
- Problem: The Walsin official result for `0402X105K250CT` is `1.00±0.05 / 0.50±0.05 / 0.50±0.05`, but the system was showing `0.4±0.02 / 0.2±0.02 / 0.2±0.02`. Root cause: the cached LCSC entry `C237173` had been populated from a misread size-table match where the generic MLCC extractor treated ambiguous `0402` tokens as the smaller metric body row, so the bad cache kept overriding the live display.
- Fix: Updated `component_matcher.py` so MLCC size-table extraction no longer returns the first token hit blindly. The extractor now scores candidate `长度/宽度` rows against the requested `尺寸（inch）` nominal body size, rejects cache values that conflict with the requested size hint, and only accepts cached/live LCSC dimensions when they actually fit the target package. Also corrected the existing `cache/mlcc_lcsc_dimension_cache.json` entry for `C237173` to the official Walsin dimensions reported on the vendor page.
- Verify: `python -m py_compile component_matcher.py` passed; `infer_mlcc_dimension_fields_from_record()` now returns `0402X105K250CT -> 1.00±0.05 / 0.50±0.05 / 0.50±0.05`, while unaffected controls still stay correct (`CL05A105KQ5NNNC -> 1.00±0.05 / 0.50±0.05 / 0.50±0.05`, `C0402X7R1A102K020BC -> 0.40±0.02 / 0.20±0.02 / 0.20±0.02`).

### 2026-03-30 23:03 [direct] Added MLCC dimension source labels to the result table
- Problem: MLCC result rows could now show `长度（mm）/宽度（mm）/高度（mm）`, but the page still did not tell the user whether those values came from Samsung's official page, a vendor datasheet cache, or a model-naming rule, so the provenance behind the displayed body size remained opaque.
- Fix: Added an MLCC dimension source tracker in `component_matcher.py` and threaded it through the record/dataframe enrichment path. The MLCC display schema now includes a new `尺寸来源` column, and the source label is derived from the actual fill path, for example `Samsung官方页面`, `LCSC规格书`, `TDK命名规则 / LCSC规格书`, or `村田命名规则`.
- Verify: `python -m py_compile component_matcher.py` passed. Spot checks confirmed `0402X105K250CT -> LCSC规格书`, `CL05A105KQ5NNNC -> Samsung官方页面`, `C0402X7R1A102K020BC -> TDK命名规则 / LCSC规格书`, and `GRM43R5C2A103JD01L -> 村田命名规则`. The MLCC display schema now exposes `尺寸来源` alongside `长度(mm) / 宽度(mm) / 厚度(mm)`.

### 2026-03-31 00:03 [direct] Added Jianghai aluminum electrolytic seed rows and fixed empty-candidate fallback
- Problem: Three Jianghai sample parts from the original factory mapping were missing from the local库, so exact part lookups and typed electrolytic searches could not return them. The missing coverage was `ECR1VLY152MLL125030E`, `ECR1EEQ681MLL100020E`, and `PCV1EVF221MB10FVTSWP`. On top of that, the search/match path treated an empty `fetch_search_candidate_pairs()` result as a real candidate list, which filtered the seed rows back out and still produced empty matches.
- Fix: Added Jianghai seed rows directly in `component_matcher.py` for the three sample models, including series profiles, size parsing, voltage mapping, package/mount metadata, and source/status fields. Also changed the search path so empty candidate lists now fall back to typed electrolytic search instead of short-circuiting the result set, and gave the Jianghai seed rows a small sort priority so they surface first in the matched results.
- Verify: `python -m py_compile component_matcher.py` passed. `load_component_rows_by_clean_model("ECR1VLY152MLL125030E")` now returns the seed row, `load_search_dataframe_for_query()` returns a non-empty result set for the sample spec `ECAP 1500uF/35V +/-20% 25mOHM 105C 12.5*30mm TH ROHS`, and `cached_run_query_match()` now ranks the Jianghai seed first (`seed_rank = 1`, `matched_rows = 4`).

### 2026-03-31 02:07 [direct] Hardened Jianghai electrolytic sync with local detail cache and durable manufacturer samples
- Problem: The Jianghai electrolytic library still had two gaps. First, the model-rule side was incomplete for several families, so voltage/series inference could miss official match targets. Second, the durable source set was too small, so the rebuilt library did not yet carry enough Jianghai coverage to explain the original manufacturer mappings.
- Fix: Expanded `aluminum_electrolytic_library_sync.py` to add a local Jianghai HTML detail cache scan, explicit series branches for `ECR/VLY/EEQ` and `PCV/AVF/EVM/EVF` families, and voltage precedence fixes so model-rule parsing wins before code fallback. Also merged JLC detail rows, local cached detail rows, and three confirmed manufacturer samples into the Jianghai build pipeline so the rows survive full CSV/database rebuilds.
- Verify: `build_jianghai_rows()` now returns `1321` Jianghai rows, the generated CSV contains `ECR1VLY152MLL125030E`, `ECR1EEQ681MLL100020E`, and `PCV1EVF221MB10FVTSWP`, and the rebuilt `components.db` also contains those three exact models under brand `江海Jianghai`. The local cache scan found `228` cached Jianghai detail rows, which are now part of the durable source path.

### 2026-03-31 02:36 [direct] Rebuilt Jianghai search index so exact model lookup hits the new rows
- Problem: The main database had already been updated, but the separate search index file was still stale, so fast exact-model lookup could still miss the new Jianghai rows even though the underlying data existed.
- Fix: Rebuilt `components_search.sqlite` from the refreshed database/prepared cache so the `_model_clean` index includes the new Jianghai models and the UI fast path can resolve them immediately.
- Verify: `components_search.sqlite` timestamp advanced to `2026-03-31 02:35:15`, and `load_component_rows_by_clean_model()` now returns `1` row each for `ECR1VLY152MLL125030E`, `ECR1EEQ681MLL100020E`, and `PCV1EVF221MB10FVTSWP`.

### 2026-03-31 05:16 [direct] Expanded the inductor library from official Bourns/Wurth sources and wrote it into the main database
- Problem: The inductor catalog was still thin and the Bourns web pages were unreliable to scrape directly, so the missing model coverage was not surviving a rebuild.
- Fix: Added `build_inductor_official_sources.py`, switched Bourns coverage to the official selection-guide PDF, kept the Wurth official pages, generated `Inductor/official_inductor_expansion.csv` with `363` rows, appended `214` Bourns rows and `149` Wurth rows into `components.db`, and rebuilt both `components_search.sqlite` and `components_prepared_v5.parquet`.
- Verify: `load_component_rows_by_clean_model()` now resolves `PQ2614BHA`, `SRP0310`, `SRF0703A`, and `DR221` with real `长/宽/高` values, and the main database now reports `214` rows from `Bourns official selection guide PDF` plus `149` rows from `Wurth official%` in the new inductor source set.

### 2026-03-31 06:46 [direct] Synced the resistor cache into the main database and refreshed search/prepared caches
- Problem: The resistor library cache had drifted from the database, so several thousand models were still missing from the live library even though the cached source already contained them.
- Fix: Added `sync_resistor_mlcc_sources.py` to stream `cache/resistor_library_cache.csv` into a temp table, insert only rows not already present by `品牌/型号/器件类型`, and then rebuild both the search index and the prepared cache. The same script also loaded `Capacitor/MLCC.xlsx`; that workbook had no brand/model/type rows left to add, so it contributed no new inserts.
- Verify: The sync inserted `3552` missing resistor rows, updated `厚膜电阻` to `440794` and `碳膜电阻` to `11569`, and refreshed `components_search.sqlite` plus `components_prepared_v5.parquet` at `2026-03-31 06:46`. Existing capacitor MLCC brands like `晶瓷Kyocera AVX`, `村田Murata`, `三星Samsung`, `东电化TDK`, and `华新科Walsin` remain present in the main library after the sync.

### 2026-03-31 09:11 [direct] Fixed Streamlit startup scripts that were failing on PowerShell's read-only `Host` variable
- Problem: The app page appeared "down" because the normal startup path could not launch `start_streamlit.ps1`. The scripts used a parameter named `Host`, which collides with PowerShell's built-in read-only `Host` automatic variable and throws `无法覆盖变量 Host` before Streamlit ever binds to the expected local port. That left the documented `8501` entrypoint unavailable even though a temporary debug instance was still running on `8504`.
- Fix: Renamed the bind-address parameter to `BindHost` in `start_streamlit.ps1`, `start_public.ps1`, and `setup_fixed_domain.ps1`, and updated the self-elevation/startup-command path in `setup_fixed_domain.ps1` to pass `-BindHost` as well. Restarted the app through the fixed script.
- Verify: `http://127.0.0.1:8501` now responds with `200`, and `netstat` shows `127.0.0.1:8501` listening on the new Streamlit process started from `C:\Users\zjh\Desktop\data\.venv\Scripts\python.exe -m streamlit run component_matcher.py --server.address 127.0.0.1 --server.port 8501 --server.headless true`.

### 2026-03-31 09:31 [direct] Removed startup-time blocking database refresh so the Streamlit page renders instead of staying blank
- Problem: After the Rubycon CSV changed, the app startup path hit `maybe_update_database(force=False)` before rendering any UI. Because `database_needs_refresh()` compares source-file mtimes against `components.db`, the changed capacitor source caused every fresh app session to start a full `update_database()` pass on load. The frontend connected successfully, but the script remained in `running` state without having emitted the search UI yet, which appeared as a blank white page.
- Fix: Updated `component_matcher.py` so non-forced startup refresh is skipped when the existing database already contains component rows. This keeps the page responsive and leaves full rebuilds to explicit maintenance commands instead of blocking first paint. Also cleaned up duplicate Streamlit processes on `8501` and restarted a single clean instance.
- Verify: `python -m py_compile component_matcher.py` passed. Fresh browser automation against `http://127.0.0.1:8501` now finds the rendered `stMainBlockContainer` and a real `<textarea>` in `#root`, with `html_len=225769`, confirming the app is rendering actual content instead of a blank shell.
## 2026-03-31 10:45 Jianghai 命名规则与铝电规格搜索排查

- 用江海官方欧洲目录 `JE25_ECap_Catalogue.pdf` 对齐了订货码规则：
  - 径向/贴片订货码中的 `◊◊` 表示 `pin style & length`，`∆∆` 表示 `pitch code`
  - snap-in 订货码示例会显式出现 `T6` / `P2` 这类端子与脚距代码
- 这说明你截图里的 `□□` 本质上是江海订货码里的占位位，不是容值或耐压；系列表如果只给到基础码，就无法单靠那一行恢复成唯一完整订货型号。
- 定位到本地库不全的一个核心原因：
  - `CD29NF` 这类江海 snap-in PDF 有些行把基础型号和尺寸尾码拆成两列
  - 旧 builder 只保留基础型号，例如 `ECS2VNF271M`，去重时把 `220050 / 250045 / 300035 / 350025` 这些尺寸变体折叠掉
- 已修复：
  - `aluminum_electrolytic_library_sync.py` 新增 `jianghai_compose_variant_model(...)`
  - `build_jianghai_cd29nf_rows()` 现在会把 `tail_code` 并回型号，得到 `ECS2VNF271M220050` 这类更完整的型号
  - 复测 `build_jianghai_cd29nf_rows()` 已能产出 `ECS2VNF271M220050 / 250045 / 300035 / 350025`
- 另一个已修复的问题在 `component_matcher.py`：
  - 铝电规格搜索原来在“没有真候选”时，会把 `尺寸/安装方式/特殊用途/寿命/温度` 从硬条件放宽成软条件
  - 已改成：用户明确写了这些条件，就必须满足，否则返回空结果
  - 复测 `铝电容_270uF_±20%_16V_-25-105℃_5000h_6.6×7.2mm_贴片_消费` 现在返回 `0` 条，不再错误混入 `VNF/GNF` 等插件系列
- 正在执行 `python aluminum_electrolytic_library_sync.py --apply` 做全量回灌；CSV 已更新到 2026-03-31 10:41，但数据库重建仍在运行中，待完成后需要再核对网页结果。
## 2026-03-31 13:55 信昌 PDC MLCC 命名解析与系列显示修复

- 这次把信昌 PDC 的 MLCC 命名规则补成了 `MT / MG / MS` 三套前缀解析：
  - `MT`：车规 / AEC-Q200
  - `MG`：次车规 / 无 AEC-Q200
  - `MS`：车规 / 软端子
- 补进了 `MT43X472K302EGZ` 的完整解析：
  - `系列=MT`
  - `系列说明=车规 / AEC-Q200 / Anti-Arcing + Anti-Bending`
  - `尺寸（inch）=1812`
  - `容值=4.7NF`
  - `耐压（V）=3000`
  - `长度/宽度/高度=4.50±0.40 / 3.20±0.30 / 2.50±0.30`
- 结果表已经能显示 `系列` 和 `系列说明`，并保留 `尺寸（inch）` 与长宽厚分栏，不再混在一起。
- 额外补了一个搜索兜底：如果 `料号` 直查时跨品牌结果被同品牌过滤清空，会从原始候选集里回找同型号原厂行，避免 `MT43X472K302EGZ` 这类料号直接显示成 0 条。
- 复测：
  - `load_component_rows_by_clean_model("MT43X472K302EGZ")` 能命中 1 行
  - `cached_run_query_match(...)` 不再为空，最终结果可展示系列信息
  - `python -m py_compile component_matcher.py` 通过

## 2026-03-31 16:55 风华 AM 系列官方命名解析与系列回填修复

- 这次先按风华官方 AM 系列资料重新校正了命名规则，确认 `AM10B103K202NT` 属于风华，不是华新科 / Walsin。
- 通过官方资料确认：
  - `AM` 是风华 AM 汽车级 MLCC 系列
  - `AM10B103K202NT` 在官方页上对应 `1210 / X7R / 2000V / 10nF`
  - 官方页还给出了该型号的尺寸 `3.20±0.30 × 2.50±0.30 × 2.00±0.30 mm`
- 已修复：
  - `component_matcher.py` 新增风华 `AM` 系列解析
  - `parse_model_rule()` 现在会优先把 `AM\d{2}...` 识别为风华，而不是落到华新科 / Walsin 的宽松兜底
  - `fill_missing_series_from_model()` 现在会把风华 `AM` 系列回填到 `系列=AM`、`系列说明=汽车级 / AEC-Q200`
  - `describe_mlcc_dimension_source()` 现在能把风华 AM 的尺寸来源标成风华官方页面
  - `looks_like_compact_part_query()` 也补了 `AM` 前缀，保证这个料号会走紧凑料号搜索链路
- 复测：
  - `parse_model_rule("AM10B103K202NT", component_type="MLCC")` 返回品牌 `风华Fenghua`、系列 `AM`
  - `build_model_naming_interpretation("AM10B103K202NT")` 能输出风华 AM 系列说明
  - `fill_missing_series_from_model()` 对最小样本能回填 `系列=AM` 与 `系列说明=汽车级 / AEC-Q200`
  - `python -m py_compile component_matcher.py` 通过

## 2026-03-31 18:21 风华 AM 官方系列行入库与缓存重建完成

- 新增了独立同步脚本 [sync_fenghua_am_official.py](C:/Users/zjh/Desktop/data/sync_fenghua_am_official.py)，用于抓取风华官方 `AM` 系列页面并写入数据库。
- 官方页实际解析到 15 条 `AM` 系列记录，已全部补进 `components.db`。
- 已确认：
  - `AM10B103K202NT` 现在在主库中有官方实录
  - `load_component_rows_by_clean_model("AM10B103K202NT")` 能命中 1 行
- 为了让新插入的风华 AM 行能参与规格搜索，已经重建：
  - `components_prepared_v5.parquet`
  - `components_search.sqlite`
- 顺手修复了 prepared cache 分块写 Parquet 时的列顺序不一致问题，避免以后扩品牌时再次在缓存重建阶段报 schema mismatch。
- 进一步修正了 `fill_missing_series_from_model()`：风华 `AM` 料号即使原始行已经有 `系列=AM`，也会继续回填 `系列说明=汽车级 / AEC-Q200`，避免精确料号结果里系列说明仍然为空。
- 复测：`load_component_rows_by_clean_model("AM10B103K202NT")` 现在会返回 `品牌=风华Fenghua`、`系列=AM`、`系列说明=汽车级 / AEC-Q200`
- 进一步收紧了命名规则兜底：`parse_walsin_common()` 现在必须有明确品牌上下文（Walsin / 华新科）才会生效，`parse_model_rule()` 的最后一道 Walsin 宽兜底也改为需要品牌上下文，避免再把别家料号按相似外形直接猜成华新科。

## 2026-03-31 21:15 公网快速访问已接通

- 把 [start_public.ps1](C:/Users/zjh/Desktop/data/start_public.ps1) 改成了更自足的公开入口：
  - 若本机已在运行 `8501`，就直接复用，不再重复起第二个 Streamlit
  - 若机器上没有 `cloudflared`，脚本会自动从 Cloudflare 官方 release 下载 Windows 版
- 已成功拉起 Cloudflare quick tunnel，当前公网临时地址为 `https://absence-dover-threatened-trustees.trycloudflare.com`
- 这条公网链接是免费的，但属于 quick tunnel，重启后会变化，本机保持开机和联网时可继续访问

## 2026-03-31 Streamlit Community Cloud 准备

- 新增了 `streamlit_app.py` 作为 Streamlit Cloud 入口，确保云端不会直接依赖桌面启动脚本。
- 新增了 `runtime.txt`、`requirements.txt`、`.streamlit/config.toml`，把云端运行时、依赖和 Streamlit 配置都固定下来。
- 在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 里加入了 `streamlit_cloud_bundle.zip` 自动解包逻辑，并把基础路径改成相对路径，避免 Windows 绝对路径在云端失效。
- 生成了 `streamlit_cloud_bundle.zip`，用于在云端恢复 `components.db`、`components_search.sqlite`、`components_prepared_v5.parquet` 和相关缓存。
- 新增 `.gitattributes` 以便大文件走 Git LFS，新增 `.gitignore` 以避免把本地数据库、缓存和临时调试产物一起带进云端仓库。
- 更新了 [PUBLIC_ACCESS.md](C:/Users/zjh/Desktop/data/PUBLIC_ACCESS.md)，补充 Streamlit Community Cloud 的免费固定 URL 部署说明。
- 在当前环境里恢复了可用的 Git：已将 Git for Windows portable 版解包到 [tools/PortableGit](C:/Users/zjh/Desktop/data/tools/PortableGit)，现在可直接通过 `C:\Users\zjh\Desktop\data\tools\PortableGit\cmd\git.exe` 使用 `git version 2.53.0.windows.2`。

## 2026-03-31 双启动器落地

- 新增 [start_lan.cmd](C:/Users/zjh/Desktop/data/start_lan.cmd) + [start_lan.ps1](C:/Users/zjh/Desktop/data/start_lan.ps1)，用于一键启动局域网可访问的网页服务，绑定 `0.0.0.0:8501` 并自动打开本机浏览器。
- 新增 [start_public_fixed.cmd](C:/Users/zjh/Desktop/data/start_public_fixed.cmd) + [start_public_fixed.ps1](C:/Users/zjh/Desktop/data/start_public_fixed.ps1)，用于一键启动固定公网 URL 的网页服务，前提是 Cloudflare Tunnel 已在云端配置好并把 token 放入 `public_tunnel_token.txt`。
- 公网启动器现在会自动生成并复用 `public_access_code.txt`，同时把 `APP_ACCESS_CODE` 传给应用层访问码门禁，避免拿到 URL 就能直接进系统。
- 新增 `public_tunnel_token.txt.example` 和 `public_fixed_url.txt.example`，作为固定公网模式的本地配置示例。
- 新增 `public_access_code.txt.example`，作为公网访问码示例。
- 更新 [PUBLIC_ACCESS.md](C:/Users/zjh/Desktop/data/PUBLIC_ACCESS.md)，把两个双击启动器的使用方式写进说明。
- 在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 里加入了访问码门禁、公共模式标记和搜索/BOM 的输入上限，减少被恶意大输入拖死的风险。
- 在 [.streamlit/config.toml](C:/Users/zjh/Desktop/data/.streamlit/config.toml) 里显式开启 `enableXsrfProtection = true` 并限制上传大小，补齐了 Streamlit 层面的基础防护。
- 在 BOM 导出链路里增加了公式注入防护：新增的导出列与结果列在写入 Excel 前会先做公式前缀转义，避免恶意 `=` / `+` / `-` / `@` 字符串被当成公式执行。

## 2026-03-31 Streamlit Community Cloud 版本收尾

- 新增 [README.md](C:/Users/zjh/Desktop/data/README.md)，把 Streamlit Community Cloud 的部署入口、GitHub 推送方式、`streamlit_app.py` 入口和访问码 secrets 说明整理成仓库首页说明。
- 重新核对了云端 bundle 内容，确认 [streamlit_cloud_bundle.zip](C:/Users/zjh/Desktop/data/streamlit_cloud_bundle.zip) 里包含 `components.db`、`cache/components_search.sqlite`、`cache/components_prepared_v5.parquet` 和相关元数据缓存，云端启动不需要现场全量重建。
- 再次确认 `component_matcher.py` 的云端入口顺序是先访问码门禁、再解包云端数据包、最后才按需检查数据库，适合 Streamlit Community Cloud 的固定 `streamlit.app` 部署方式。
- 修正了 `component_matcher.py` 的云端首搜链路：`ensure_streamlit_cloud_data_bundle()` 支持按需解包，`搜索/BOM` 首次进入时优先只解 `cache/components_search.sqlite` 和小缓存，不再先解完整 `components.db`。
- 给 `component_matcher.py` 加了 search sidecar 轻量回退，`load_component_rows_by_brand_model_pairs()` / `load_component_rows_by_clean_models_map()` / `fetch_search_candidate_pairs()` 在无完整数据库时也能直接用 `components_search.sqlite` 服务查询；在纯 bundle 环境里验证到搜索资产轻解压约 `10.6s`，随后 `MT43X472K302EGZ` 精确料号查询约 `2.2s`，且未触发 `components.db` 解包。
- 增加了首页后台预热 `components_search.sqlite` 的线程，保证 Streamlit Community Cloud 打开首页时不阻塞渲染，同时尽量把搜索索引准备前置到用户真正点击搜索之前。

## 2026-04-02 局域网 / 公网真实用户回归与修复

- 用真实页面交互分别回归了局域网入口和公网 Cloud 入口，覆盖了 `精确料号搜索`、`规格参数搜索`、`BOM CSV 上传` 三条主流程。
- 实测确认局域网入口 `http://192.168.60.117:8502` 可以正常完成：
  - `AM10B103K202NT`
  - `MT43X472K302EGZ`
  - `WR12W1R00FTL`
  - `1210 X7R 10nF 2000V 10%`
  - `270uF 16V -25-105C 5000h 6.6x7.2mm SMD`
- 修正了 Streamlit Community Cloud 启动路径：
  - 不再在首页渲染前强制执行 `ensure_streamlit_cloud_data_bundle()`
  - 也不再在数据库缺失时于启动阶段同步触发 `maybe_update_database()`
  - 现在改成“首页先渲染，真正搜索 / BOM 匹配时再按需准备数据”
- 新增 `ensure_component_data_ready()`，统一处理：
  - 本地数据库已存在则直接使用
  - 云端 bundle 存在则按需解包
  - 最后才回退到数据库更新逻辑
- 复测结果：
  - 干净 Cloud 模拟目录 `tmp_cloud_smoke_py` 现在首页已能正常渲染，不再是此前的空白页
  - 局域网版铝电规格单条搜索现在能在约 `1s` 内返回明确的“无匹配”结果，不再长时间卡在准备数据阶段
  - 同一份 5 行混合 BOM 样本从此前约 `46s` 降到约 `18s`
- 为了降低正常用户误读，给页面新增了说明提示：
  - `信昌料号 / 华科料号` 明确标注为“跨品牌对照料号”，不是当前输入型号自身的品牌归属
  - `匹配结果` 明确说明默认展示的是可替代品牌，不重复展示原始输入型号
  - 该说明已同时加入单条搜索结果区和 BOM 结果区
- 本轮仍然保留一个未彻底解决的风险：
  - Streamlit Community Cloud 冷启动后的“第一次搜索”仍可能因为首次解包大数据包而明显偏慢，需要后续继续瘦身公网数据包

## 2026-04-02 16:25 Cloud 首搜继续优化
- 继续处理 Streamlit Community Cloud 冷启动后“第一次搜索偏慢”的问题，重点放在：
  - 搜索入口和 BOM 型号列优先复用精确料号命中行，避免同一轮内重复做型号直查和反推规格
  - 云端后台预热时，搜索索引文件改为先写 `.part` 临时文件，再原子替换为正式 `components_search.sqlite`
- 修复了一个真实竞态问题：
  - 旧逻辑在后台预热时直接把搜索索引写到正式路径，用户若在预热尚未完成时点击搜索，前台线程可能看到“文件已存在但内容尚未写完”的半成品索引
  - 这会导致首次搜索偶发出现精确料号查不到、候选为空或表现不稳定
  - 现在改成原子落盘后，前台只会看到完整可查询的索引文件
- 复测结果：
  - 当前工作目录热态下，`MT43X472K302EGZ` 的 `resolve_search_query_dataframe_and_spec(...)` 已压到约 `0.98s`
  - 干净 cloud bundle-only 目录里，首次选择性解包 `components_search.sqlite` 约 `5.5s`
  - 干净 cloud bundle-only 目录里，模拟“首页已打开并后台预热 5 秒后再点搜索”，`MT43X472K302EGZ` 不再出现空结果，精确料号可正常返回 1 行原厂资料并继续走 `fast_query`
- 当前判断：
  - 首搜的最大耗时仍然是云端首次解包 `components_search.sqlite`
  - 但这轮已经把“预热过程中偶发拿到半成品索引”的不稳定问题收掉了，公网首搜的一致性会明显更好


## 2026-04-02 20:40 ????????????
- ??????????????????? `streamlit.app` ??? `0402 1uf 10v`????????????????? / ??????
- ??????????????????? Cloud bundle-only ?????????????
  - `fetch_search_candidate_pairs(...)` ? MLCC ?? `?? + ??` ????? `0402 1uf 10v` ????????????
  - `load_search_sidecar_rows_by_brand_model_pairs(...)` ????????????? sidecar ???????? `parse_model_rule(...)`
  - ??????? `components_search.sqlite` ???????????????????????????????
- ?????
  - MLCC ?????????? `????` ? `???V?` ??????????
  - `load_search_sidecar_rows_by_brand_model_pairs(...)` ???? `preferred_component_type`
  - ????????????? sidecar ???????? `?? + ??` ?????????? merge
  - sidecar ???????? `include_model_rule` ????????????????????????????
  - ?????????????Cloud bundle ??????????????????? 5-15 ??????
- ?????
  - ?? cloud bundle-only ??????`0402 1uf 10v` ???? `22.9s` ??????????? `6.5s`
  - ???????????
    - ?????? `0.07s`
    - sidecar ???? `1.3s`
  - ???????????????????????????

## 2026-04-02 20:42 ????????????????
- ?????Cloud bundle-only ??????????? sidecar ??????????????
- ?? MLCC ???????? `?? + ?? + ?? + ????`??? sidecar ?????????????
- sidecar ?????????????????????????????? `0402 1uf 10v` ???? `22.9s` ??? `6.5s`?
- ????????????????????? `5-15 ?` ????????????????????

## 2026-04-02 20:43 手机公网规格搜索卡顿修复（UTF-8补记）
- 重新确认：Cloud bundle-only 环境下的规格首搜慢点在 sidecar 候选重建，不是匹配排序本身。
- 已把 MLCC 快速候选条件补到 `尺寸 + 容值 + 误差 + 耐压下限`，并让 sidecar 快路径优先直读目标器件表。
- sidecar 轻量回退已避免对每条候选重复跑命名规则，恢复正确结果的同时把 `0402 1uf 10v` 首搜从约 `22.9s` 压到约 `6.5s`。
- 搜索进度文案同步补充公网提示：首搜可能需要 `5-15 秒` 预热索引，降低手机用户误判为死机的概率。

## 2026-04-02 22:53 ?? MLCC ?????????UTF-8???
- ???????? MLCC ?????????????????????????????????????
- ? `0402 1uf 10v` ???
  - ???? `336` ?? `127`
  - ?? cloud bundle-only ?????????????? `6.2s` ?????? `5.6s`
- ??????????????????????? Streamlit Cloud ???????????

## 2026-04-02 22:54 公网 MLCC 规格候选继续收窄（UTF-8补记）
- 对明确写了耐压的 MLCC 规格搜索，改成先查“同耐压”候选；只有同耐压结果为空时，才放宽到更高耐压。
- 以 `0402 1uf 10v` 为例：
  - 候选数从 `336` 降到 `127`
  - 干净 cloud bundle-only 模拟目录里的首次规格搜索从约 `6.2s` 进一步降到约 `5.6s`
- 这轮优化主要针对手机公网首搜场景，优先减轻免费 Streamlit Cloud 算力下的候选重建压力。

## 2026-04-02 23:05 ???????????UTF-8???
- ?? Playwright ??????????? `https://fruition-componentmatche.streamlit.app/`?? Streamlit ?? app frame ??????? `0402 1uf 10v` ??????
- ???????????????????????????????????????? `1` ??????????? `1.5s`?
- ??????????????????????????????????????

## 2026-04-02 23:06 公网真实手机视图复测（UTF-8补记）
- 使用 Playwright 以手机视图直接访问公网 `https://fruition-componentmatche.streamlit.app/`，在 Streamlit 内层 app frame 中模拟用户输入 `0402 1uf 10v` 并点击搜索。
- 复测结果：页面已从此前卡在“正在载入候选库”恢复为正常完成；真实公网实例本轮返回 `1` 条匹配，页面显示耗时约 `1.5s`。
- 这说明新的候选收窄逻辑已经被公网部署吃到，手机外网场景可以正常完成规格搜索。

## 2026-04-03 10:12 一键同步局域网与公网发布链
- 新增 `build_streamlit_cloud_bundle.py`，把当前本地 `components.db`、搜索索引和关键缓存统一打包为 `streamlit_cloud_bundle.zip`，并生成 `streamlit_cloud_bundle.manifest.json`，避免内容不变时重复重打包。
- 新增 `sync_local_and_public.py`、`sync_local_and_public.ps1`、`sync_local_and_public.cmd`，统一完成“重建云端数据包、语法校验、暂存发布文件、提交、通过 GitHub SSH 443 推送”的发布流程。
- PowerShell 包装脚本已修正单命令 Python 调用时的参数展开问题，避免后续双击启动器时因数组切片为空而报错。
- `README.md` 与 `PUBLIC_ACCESS.md` 已补充“一键同步发布”说明，后续本地改规则、数据库或页面后，不需要再手工分别维护局域网版和公网版的发布动作。

## 2026-04-03 11:08 一键同步发布链最终打通
- 发布脚本改为优先使用“仓库专用 deploy key”，避免依赖用户级 `/user/keys` API；当前这台机器的仓库写入密钥已经成功注册到 `harma801209/component-matcher`。
- 由于本地历史里还保留了早期“通过 GitHub API 直接写远端”的旧提交，脚本不再对本地分支做 rebase，而是抓取远端最新 `main` 后，基于当前本地提交的文件树合成一个“发布专用 commit”，再通过 SSH 443 推到远端，绕开同内容不同 hash 的历史冲突。
- 已完成三轮验证：
  - `sync_local_and_public.ps1 -SkipBundleRebuild -SkipPush` 半实战通过，可生成本地 commit 与发布 commit
  - 真实推送通过，`streamlit_cloud_bundle.zip` 已经通过 Git LFS 上传到远端 `main`
  - 无改动时再次执行 `sync_local_and_public.ps1 -SkipBundleRebuild` 会优雅返回 `Everything up-to-date`
- 结论：后续本地改数据库、规则或页面后，优先用 `sync_local_and_public.cmd` / `sync_local_and_public.ps1` 做统一发布，不再需要人工分别处理局域网版和公网版。

## 2026-04-03 11:31 GitHub Pages 访客外壳页
- 针对手机访客仍会在 `streamlit.app` 原始页面里看到平台角标的问题，新增了一个免费的 GitHub Pages 外壳页：`https://harma801209.github.io/component-matcher/`
- 新增文件：`docs/index.html`、`docs/404.html`、`docs/.nojekyll`，通过 iframe 嵌入 `https://fruition-componentmatche.streamlit.app/?embed=true&embed_options=hide_loading_screen`，让访客优先进入精简后的访问壳，而不是直接看到原始 Streamlit Community Cloud 页面。
- 已通过 GitHub Pages API 将仓库 `harma801209/component-matcher` 配置为从 `main` 分支 `/docs` 目录发布；当前 Pages 状态为 `built`。
- 访问建议：
  - 外部访客优先使用 GitHub Pages 包装页
  - 管理和调试仍可继续使用原始 `streamlit.app` 链接

## 2026-04-03 11:47 访客页底部平台栏遮罩
- 复测发现 `embed=true` 版 Streamlit 仍会保留一条极简嵌入栏（如 `Built with Streamlit / Fullscreen`），官方不能直接关闭。
- 在 `docs/index.html` 的 GitHub Pages 外壳页中新增了底部遮罩层，并统一改成 `dark_theme` 嵌入，尽量把这条平台栏在访客视角中压到不可见。
- Playwright 手机视角复测已生成截图：`cache/github_pages_mobile_wrapper_v3.png`，当前访客入口页主视图已不再直接露出底部平台角标。

## 2026-04-03 12:06 匹配结果去除信昌/华科对照列
- 按当前页面需求，已从搜索结果展示层去掉 `信昌料号`、`华科料号` 两列，不再在“匹配料号资料”“匹配结果”中单独呈现。
- 已删除蓝色说明文案：`信昌料号 / 华科料号 显示的是跨品牌对照料号...`
- BOM 结果展示层也同步去掉这两列及对应说明，避免不同入口显示口径不一致。
- 底层对照数据与映射逻辑暂时保留，仅调整展示层，后续如还要继续利用内部映射做匹配，不会受本轮界面清理影响。

## 2026-04-03 12:15 规格搜索结果去除底部重复输入框
- 当用户走“规格参数搜索”或“料号片段反推规格”时，页面上方已经有 `规格条件` 表格，因此匹配结果下方不再重复显示一整块蓝色输入原文框。
- 已移除该重复展示对应的 `query_inline_html` 输出，避免规格页上下重复表达同一组条件，界面更干净。

## 2026-04-03 13:05 Cloudflare 直代理改为真实应用页
- 放弃 `GitHub Pages iframe 外壳` 和 `Streamlit 分享层` 方案，改为直接代理真正的 Streamlit 应用路径：`https://fruition-componentmatche.streamlit.app/~/+/`，目标域名维持用户选定的 `fruition-component.pages.dev`。
- 新建并收敛 `cloudflare-pages-proxy/dist/_worker.js`：现在首页 `/` 会直接映射到上游 `/~/+/`，静态资源、`/_stcore/*` 和其他应用请求统一自动前缀到 `/~/+/`，不再依赖 `share.streamlit.io` 的 `app/context/status` 接口。
- 关键修复：为上游代理请求补齐 `Origin/Referer`，并对 `/_stcore/stream` 走原样 WebSocket 透传，避免此前本地一直卡在 `401 Unauthorized` 或分享层白屏。
- 本地 `wrangler pages dev` + Playwright 已验证：
  - 首页能正常渲染为真实应用版式，而不是分享外壳或 GitHub Pages 头壳
  - `/_stcore/stream` 已返回 `101 Switching Protocols`
  - 规格搜索 `1210/X7R/4.7uF/10%/100V` 能正常提交并返回 `MLCC匹配结果`
- 当前剩余阻塞只剩 Cloudflare 账号登录，待执行一次 `wrangler login` 后即可把这版真正部署到 `fruition-component.pages.dev`。

## 2026-04-03 13:38 Cloudflare Pages 正式上线与手机端复测
- 已通过 Cloudflare Wrangler 登录并创建 Pages 项目 `fruition-component`，正式固定网址为 `https://fruition-component.pages.dev/`。
- 线上部署已完成，Cloudflare 首次部署预览地址为 `https://6f9c2f9c.fruition-component.pages.dev`，正式域名 `https://fruition-component.pages.dev/` 已返回 `200`。
- 使用 Playwright 对正式域名做真实浏览器验证：
  - 桌面端：首页可正常打开，规格搜索 `1210/X7R/4.7uF/10%/100V` 能正常返回 `MLCC匹配结果`
  - 手机端：首页排版正常，`搜索` 与 `BOM批量上传匹配` 区块可见
  - 手机端规格搜索 `0402 1uF 10V` 能正常完成，页面显示耗时约 `1.5s`
  - 手机端料号搜索 `AM10B103K202NT` 能正常完成，页面显示耗时约 `0.3s`
- 结论：`fruition-component.pages.dev` 现在已经可以作为对外访客固定入口使用，且不再暴露 GitHub 用户名。

## 2026-04-03 18:34 MLCC 系列品类接入匹配规则
- 按品牌规格书/官方命名规则，把 MLCC 的“系列品类”正式接入解析与匹配，不再只显示原始系列前缀。
- 已补的官方品类规则包括：
  - 村田 Murata：`GRM=常规`、`GCM/GRT=车规`、`GJM/GQM=高Q`
  - 信昌 PDC：`FN=常规`、`FS=高容`、`FM=中压`、`FV=高压`、`FP=抗弯`、`FK/FH=安规`、`MT=车规`、`MG=次车规`、`MS=车规软端子`
  - TDK：`Cxxxx=常规`、`CGAxxxx=车规/AEC-Q200`
- `parse_murata_core()`、`parse_tdk_c_series()`、`parse_tdk_cga_series()`、`parse_pdc_mlcc_core()` 现在都会直接输出 `系列 / 系列说明 / 特殊用途 / _mlcc_series_class`。
- `prepare_search_dataframe()` 现在会为 MLCC 行补齐官方系列说明与 `_mlcc_series_class`，即使数据库原始行只有基础系列前缀也能回填。
- `scope_search_dataframe()` 现在会把 `车规/次车规/高容/高压/中压/抗弯/安规/高Q/EMI滤波` 作为 MLCC 严格筛选条件，不再让车规查询混出常规品。
- `apply_match_levels_and_sort()` 现在加入 `_mlcc_class_rank`，同品类候选会优先排前。
- 复测 `GCM31MR71E105MA37L` 时，对同规格数据库候选进行官方规则反推后，保留的候选只剩 `GCM` 与 `TDK CGA` 等车规系列，`TDK C3216` 这类常规系列已被排除。
- 显示侧也已补齐：`ensure_component_display_columns()` / `build_component_display_row()` 现在会把 `GCM -> 车规 / Automotive MLCC`、`CGA -> 车规 / AEC-Q200` 这类系列说明直接展示出来。

## 2026-04-03 18:58 一键同步脚本 UTF-8 输出修复
- `sync_local_and_public.py` 的 `run_command()` 现在显式使用 `utf-8` + `errors=replace` 读取子进程输出，避免 Windows/GBK 环境下 Git LFS 输出触发 `UnicodeDecodeError`。
- 目的：让局域网/公网一键同步链在包含大 bundle 与 LFS 上传时更稳定，避免“代码已提交但推送阶段因编码炸掉”的假失败。

## 2026-04-03 19:06 Cloudflare Pages 代理入口修复
- 发现 `https://fruition-component.pages.dev/` 出现 `502`，根因是代理 Worker 仍把上游固定拼到 `https://fruition-componentmatche.streamlit.app/~/+/`，而该上游入口已开始直接返回 `502`。
- 已将 `cloudflare-pages-proxy/dist/_worker.js` 的上游前缀切回根路径，由代理直接转发到 `https://fruition-componentmatche.streamlit.app/`，避免固定网址因旧入口失效而整站不可用。

## 2026-04-03 20:38 整库回退收紧与 Pages 旧缓存清理
- 对“看起来像完整料号、但命名规则和数据库都没命中”的输入，搜索链路现在改成快速失败，不再默认整库回退；复测 `ECV1VVZ2330M0605V1` 时，`resolve_search_query_dataframe_and_spec()` 已返回 `unknown_compact_part`，不再进入 `full_dataframe`。
- `looks_like_compact_part_query()` 增补了更宽松的完整料号识别条件，并纳入 `ECV` 前缀，避免这类紧凑型料号因为前缀未收录而被误判成普通文本。
- `cloudflare-pages-proxy/dist/_worker.js` 已恢复为完整的 Streamlit 代理版本，并新增：
  - `/service-worker.js` 与 `/service-worker` 清缓存/注销脚本
  - HTML 注入侧的旧 service worker 与旧 caches 主动清理逻辑，首次命中后会自动刷新一次
- `deploy_cloudflare_pages_proxy.ps1` 现在固定设置 `NODE_OPTIONS=--dns-result-order=ipv4first`，绕过本机 Node 对 `api.cloudflare.com` 的 DNS 解析异常，Cloudflare Pages 可再次正常部署。
- 已重新部署 Cloudflare Pages，新部署预览地址为 `https://de884a87.fruition-component.pages.dev`；正式域名 `https://fruition-component.pages.dev/` 已确认带上新的清缓存脚本与新的 `_stcore/host-config` / `service-worker.js` 响应。

## 2026-04-03 21:48 统一为公网正式版入口
- 项目说明与公网访问说明已重写，正式入口统一为 `https://fruition-component.pages.dev/`，不再把局域网版和公网版当成两套长期维护的产品。
- `README.md` 与 `PUBLIC_ACCESS.md` 已改成只强调正式公网入口、发布流程和 `Cloudflare Pages + Streamlit Community Cloud` 架构。
- `sync_local_and_public.ps1` 与 `sync_local_and_public.py` 的默认公网地址已更新为 `https://fruition-component.pages.dev/`。
- 旧兼容启动器 `start_lan.ps1` / `start_public_fixed.ps1` 已降级为“打开正式公网入口”的提示壳，不再继续启动本地 LAN / Tunnel 服务，避免误导成正式运行方式。

## 2026-04-03 22:41 Cloudflare Pages 入口恢复与站点图标补回
- 鉴于 `pages.dev` 直代理 Streamlit 运行态持续卡在 websocket `401 Unauthorized`，正式公网入口已先切换为“无头壳全屏 embed 容器”方案：根页面直接承载 `https://fruition-componentmatche.streamlit.app/?embed=true&embed_options=hide_loading_screen`，避免自建代理链继续拖累可用性。
- 新入口页面不再显示之前 GitHub Pages 那种额外头部，只保留一个全屏 `iframe` 与底部细遮罩，用于盖住 Streamlit embed 页面的底部平台条，尽量保持版面接近正式公网应用。
- `cloudflare-pages-proxy/dist/_worker.js` 已新增 `buildEmbedShellResponse()`，并让根路径 HTML 请求优先走该入口壳页；预览与正式域名首页均已恢复正常渲染。
- 因自定义壳页接管后浏览器标签缺失站点 logo，现已将本地 `logo.png` 缩制成小号图标，并改为内嵌 `data:image/png;base64,...` favicon 链接，`fruition-component.pages.dev` 标签页现已带回品牌图标。

## 2026-04-03 21:48 江海欧洲 ECV 系列铝电解析补齐
- 发现 `ECV2AVTD100M0607V1` 并不是无效输入，而是江海欧洲 `CD VTD` 系列的正式订货码；已按官方目录 `JE25_ECap_Catalogue.pdf` 补进 `ECV + 电压码 + 系列码 + 容值码 + 公差码 + 尺寸码` 解析。
- `component_matcher.py` 现已新增江海欧洲贴片铝电规则，已覆盖：
  - `VT1`
  - `VTD`
  - `VZ2`
  - `VZL`
  - `VZS`
- 已新增对应的官方电压码、公差码、尺寸码、系列画像，并把 `ECV...` 纳入 `jianghai_series_code_from_model()` 与 `parse_jianghai_aluminum_model()`。
- 复测：
  - `ECV2AVTD100M0607V1 -> 江海Jianghai / VTD / 10uF / ±20% / 100V / 6.3*7.7mm / 贴片 / -55~105℃ / 2000h`
  - `ECV1VVZ2330M0605V1 -> 江海Jianghai / VZ2 / 33uF / ±20% / 35V / 6.3*5.4mm / 贴片 / -55~105℃ / 2000h`
- 同时修正了 `build_rule_fallback_row_from_model()`，不再把所有 fallback 料号硬当成 `MLCC`；铝电这类规则反推行现在会补齐展示链需要的基础列。
- 已补上 cloud bundle 的坏文件检查：`ensure_streamlit_cloud_data_bundle()` 与 `search_sidecar_assets_available()` 现在会把“文件存在但为 0 字节”视为无效并触发重提取，避免再次出现“数据库为空，搜索已提前停止”的假空库状态。

## 2026-04-03 23:26 公网标签页 favicon 放大优化
- 发现 `fruition-component.pages.dev` 虽然已经恢复了标签页 logo，但此前使用的是横向大字标缩进 64x64 方形图标，浏览器标签里留白过多，视觉上会显得过小。
- 已将 `cloudflare-pages-proxy/dist/_worker.js` 中内嵌的 `FAVICON_DATA_URL` 替换为更紧凑的方形裁切版本，并同步更新 `cloudflare-pages-proxy/dist/favicon.png`，让标签页里的品牌图标占比更接近常规站点 favicon。
- 首页 favicon 链接已改为直接请求 `/favicon.png?v=20260403b`，并在 Worker 中显式接管 `/favicon.png` / `/favicon.ico` 返回 PNG 响应，避免先前走静态路径时被代理逻辑重定向，导致浏览器继续拿到旧图标或空图标。
- 本次调整不影响页面正文布局，只优化浏览器标签与收藏夹中的显示效果。

## 2026-04-04 15:16 江海官方压缩包搜索侧车补齐
- 按这次新抽取的江海官方压缩包与现有 `components_search.sqlite` 做差集，补写了 3,321 行缺失的江海铝电记录。
- `components_search_core` 与 `components_search_capacitor` 已同步更新，搜索索引元数据也已重写，后续只需重新打包 bundle 并推送即可让公网侧拿到最新数据。

## 2026-04-04 19:02 公网验收与扩库复核
- 已用 Playwright 打开 `https://fruition-component.pages.dev/`，确认外壳页标题正常，真实应用 frame 已加载，并能展示查询输入框与搜索按钮。
- 已用已知存在的型号 `ECS2ABZ122M250030` 做端到端搜索验证，页面返回 1 条匹配结果，耗时约 `1.7s`。
- 复核了 `1 Snapin 2024-2025` 目录下的 `CD293/CD294/CD295/CD295S/CD296/CD296L/CD296Q/CD297/CD297S/CD299/CD29C/CD29CS/CD29CT/CD29F/CD29G/CD29H/CD29HE/CD29L/CD29NF/CD29UH` 等官方 PDF，解析出的型号与当前 CSV 对照后未发现缺失项。

## 2026-04-04 19:32 根因修复：缓存签名与侧车缓存同步
- 将查询缓存、数据缓存和原始库缓存拆开：`components.db`、`components_prepared_v5.parquet`、`components_search.sqlite` 现在各自走独立签名，避免“只换了派生层但底层没刷新”时继续命中旧结果。
- `components_search.sqlite` 的索引签名已补入 `mtime`，同时把 `mlcc_lcsc_dimension_cache.json` 和 `pdc_findchips_cache.json` 纳入查询签名，避免侧车文件更新后仍沿用旧查询命中。
- `search_sidecar_assets_available()` 现在会检查整套搜索资产，而不是只看主 SQLite 是否存在，避免文件缺失时误判为可用。
- `load_mlcc_lcsc_dimension_cache()` 与 `load_samsung_mlcc_dimension_lookup()` 现在会按文件签名自动失效重载，`clear_data_load_caches()` 也会一并清空会话查询缓存和 MLCC 内存缓存，减少重复修表象。
- 已验证 `component_matcher.py` 可正常编译并导入，且测试结果表明原始库/准备层/查询层的签名已经拆开，查询层会识别搜索索引与侧车缓存的变化。

## 2026-04-04 23:40 Murata NTC 扩库与导入器修复
- 补齐 Murata NTC 识别链路：`looks_like_thermistor_context()`、`parse_model_rule()`、`reverse_spec_partial()`、`build_model_naming_interpretation()` 和 Murata 规则拆解都已接入 `FTN/NCP/NCU/NCG` 型号前缀。
- 修正导入器里缺失的 NTC 容差映射，避免 `热敏电阻_NTC.xlsx` 在归一化时直接被吞成空表。
- 已重新解析 `Resistor/热敏电阻_NTC.xlsx`，写入 363 条 Murata 官方 NTC 记录，并把它们合入主库与搜索缓存。
- 已重建 `streamlit_cloud_bundle.zip`，bundle 当前包含最新的 `components.db`、`components_search.sqlite` 和 `components_prepared_v5.parquet`。

## 2026-04-05 Murata NTC 根因回修与全局容差修正
- 已按 Murata 官方资料核实 `NCP03WF104D05RL`：`100kΩ ±0.5%`、`B25/50=4250K ±0.5%`、`0603(0201)`，确认截图里的 `0603`、空阻值、`±50%` 都是错误反推。
- 修正了 Murata NTC 专用解析：尺寸码改为官方 `0603(0201)` 映射，阻值优先走 `104 -> 100kΩ` 的专用编码，不再被尾段 `05R` 误吸走。
- 修正了共用的容差归一化逻辑，去掉了把 `0.5` 这类小数百分比错误放大的分支；这会影响所有走 `clean_tol_for_display()` 的型号，不限 Murata。
- 已确认 `components.db` / sidecar 里当前并没有这条 NCP03 型号的预存记录，因此这次问题主要由代码解析路径导致，不是单个数据库行写坏。

## 2026-04-05 Streamlit 登录态持久化
- 新增 `streamlit_auth_state.py`，把 Streamlit/GitHub 登录态统一保存成 `streamlit_cloud_state.json`，下次启动优先加载，减少反复手动授权。
- `auto_streamlit_deploy.py` 和 `tmp_keep_streamlit_login.py` 现在都基于 saved state 启动；一旦进入 Deploy 页面，会自动刷新 state 文件。
- 已把 `streamlit_cloud_state.json` 加入 `.gitignore`，避免把登录态文件误提交到仓库。

## 2026-04-06 MLCC 导入根因修复与扩库
- 在 `component_matcher.py` 里给源文件导入补了默认器件类型推断：`Capacitor/MLCC.xlsx` 这类工作簿现在会在空类型时自动落成 `MLCC`，`系列` 也会从 `??` 回填为可用的通用系列名。
- 重新跑了整库重建，`components.db` 里的 MLCC 行数提升到 `164,613`，空 `器件类型` 已清零，样例料号 `01R5N0R5B160CT` 现在能正确落到 `MLCC / MLCC`。
- 已执行 `sync_local_and_public.py`，发布提交为 `ffbe2b0fca2013fcc2764e9805bd198caeaa193c`，对外 bundle 也已同步到最新库。

## 2026-04-06 Rubycon 铝电解扩库与风华 AM 补录
- 跑通 `build_rubycon_aluminum_expansion.py` 后，Rubycon 官方铝电解 PDF 新增 1,055 条记录，`Capacitor/aluminum_electrolytic_library.csv` 总行数更新到 15,411。
- 继续同步 `sync_fenghua_am_official.py`，额外补入 15 条风华 AM 系列 MLCC 记录，当前 `风华Fenghua` 总数为 7,387 条。
- 已重新执行 `sync_local_and_public.py`，最新发布提交为 `09fd077e3af10055d3e7c60f9af47966627021fb`，公网 bundle 已更新到这两批新数据。

## 2026-04-06 MLCC 系列码修正与结果列精简
- 排查到 `fill_missing_series_from_model()` 把 PDC MLCC 的系列写成了 `FS15` 这类“系列 + 尺寸码”拼接值，根因是早期的 PDC 兜底规则和展示层仅补空值、不改旧值。
- 已把 PDC MLCC 系列规范改为统一回填系列前缀，并把 `SOURCE_NORMALIZED_CACHE_VERSION` 提升到 `2`，让旧的源标准化缓存强制失效重建。
- 结果表里 `特殊用途` 列已从 `select_component_display_columns()` 的附加尾列中移除，MLCC 结果页现在不再单独显示这一列。
- 已重建 `components.db` / `components_search.sqlite` / `components_prepared_v5.parquet`，并执行 `sync_local_and_public.py`；最新发布提交为 `3ad08da55db02b509844265f852842762d9f1175`。

## 2026-04-06 Epson 晶振/振荡器官方源补入
- 新增 Epson 官方晶振与振荡器抓取链路，`component_matcher.py` 现已接入 `Crystal*/*.xlsx` / `Crystal*/*.csv` 作为来源工作簿，并把 `crystal` / `oscillator` 路径纳入默认器件类型推断。
- 抓取到的官方页已写入 `Crystal/晶振.xlsx` 与 `Crystal/振荡器.xlsx`，共补入 272 条 Epson 记录，主库里 `爱普生Epson` 当前共 272 条，`晶振` 44 条、`振荡器` 228 条。
- 搜索侧车已先按数据库重建完成；准备层最初尝试全量重建过慢，最终改为把 Epson 这批新增 prepared 行增量追加到现有 `components_prepared_v5.parquet`，并同步更新 meta，避免白跑整库重算。
- 当前 `components_prepared_v5.parquet` / `components_prepared_v5_meta.json` 已与 `components.db` 对齐，准备缓存状态为 current。

## 2026-04-09 BOM 试做下拉版回退
- 确认公网主线仍停在 BOM 推荐品牌/型号下拉试做版提交 `b190982f721046d7c1dabdfd0eb98c04928e6ad4`，用户要求回退到试做前版本。
- 在独立工作树 `C:\Users\zjh\Desktop\data_publish_revert` 上基于 `origin/main` 生成回退提交 `f56ab24`，仅撤销 `component_matcher.py` 中 BOM 下拉试做逻辑，不夹带当前工作区其他未提交文件。
- 已通过 GitHub deploy key 走 SSH 443 推送到远端 `main`；当前线上主线已从 `b190982` 前进到 `f56ab24`。

## 2026-04-10 单型号查询去除同品牌重复结果
- 修正了 `component_matcher.py` 中料号精确查询的同品牌兜底逻辑：输入品牌型号时，匹配结果不再把与“匹配料号资料”相同的品牌/型号重新塞回下方结果表。
- 新增品牌型号对过滤辅助逻辑，并把料号模式展示改成“上方料号资料始终显示；下方只展示其他品牌结果”，若没有其他品牌则仅提示“未找到其他品牌匹配结果”。
- 同步提升 `QUERY_RESULT_CACHE_VERSION` 到 `7`，避免沿用旧查询缓存继续显示重复结果。

## 2026-04-10 BOM 结果表居中样式修正
- 调整结果表默认单元格样式为水平、垂直居中，修复 BOM 行因“其他品牌型号”等长文本列变高后，前侧常规字段仍然贴左上显示的问题。
- `其他品牌型号`、`规格参数明细`、`匹配参数明细`、`解析说明` 这类长文本列继续保留左对齐，仅常规短字段恢复居中显示。
- 同步修正了页面内旧样式块和 iframe 结果表样式块，避免不同入口页的对齐表现不一致。

## 2026-04-10 MLCC 系列解析与系列筛选根因修复
- 修正了 `component_matcher.py` 里 MLCC 系列污染问题：`C1005`、`CC0402`、`CL05A`、`LMK105`、`CGA3E2` 这类“系列+尺寸/段码”混合值会统一收敛成纯系列码，如 `C`、`CC`、`CL`、`LMK`、`CGA`。
- 补齐了 TDK / Samsung / Yageo / Taiyo / CCTC 等 MLCC 的通用系列画像，并把 `reverse_spec()`、快路径候选抓取、MLCC 系列类别过滤串起来，避免“常规料号/规格”继续混入 `车规 / 软端子 / 高容 / 高压` 等特殊系列结果。
- 同时把数据库系列回填与缓存重建的临时文件改成唯一命名，并在主库文件被 Windows 占用时自动退回原库就地更新，避免系列修复再次被 `.tmp` 文件锁中断。

## 2026-04-10 后续补库 / 命名规则 / 解析规则审计
- 最高优先级正确性问题不在“缺系列”，而在一批 `MLCC` 错类数据：`威世 CRCW`、`EVER OHMS CR*`、`Bourns CR*`、`Venkel CR*`、`VO CR1/8W*`、`光颉 CR-*`、`TE CRG*` 等型号当前挂在 `MLCC`，但单位是 `Ω` 且规格摘要明确写着厚膜/碳膜电阻。
- MLCC 规则层下一批高价值目标是系列仍为字面量 `MLCC` 的品牌前缀：`华新科Walsin`、`太诱Taiyo`、`村田Murata`、`国巨YAGEO`、`晶瓷Kyocera AVX`；其中 `AQ/CS`、`MEAS/JMR/LMR`、`KGM/KAM` 等前缀值得优先补，但需按官方规则逐支确认后再落库。
- 热敏电阻规则也还有明显空白：`Vishay NTCLE/NTCALUG`、`TDK B57861/B57237/NTC*`、Murata 的部分 `NXF*` 仍缺系列说明和命名规则；而 `薄膜电容 / 钽电容` 当前模板文件仍为空，还不能直接扩库，需先补官方源。

## 2026-04-10 MLCC 错类数据清洗（电阻误挂 MLCC）
- 修正了 `infer_db_component_type()` / `infer_spec_component_type()` 的根因：不再无条件相信库里原有 `器件类型`，当 `校验备注` 含 `来源:resistor` 或 `规格摘要` 明确写出电阻时，会优先按高置信电阻证据纠正类型。
- 新增导入阶段的器件类型证据覆盖与数据库 in-place 回灌，已把主库里 `48,884` 条“电阻误挂 MLCC”记录改回电阻家族，并把这批行的 `容值_pf` 清空，避免继续带着伪电容值进入准备层。
- 已重建 `components_prepared_v5.parquet` 与 `components_search.sqlite`；复核结果为 `MLCC + 来源:resistor/规格摘要电阻` 剩余 `0`，示例 `Bourns CR0805-FX-1000ELF` 已变为 `厚膜电阻`，而 `国巨 AC0201CRNPO8BN1R0` 这类仅单位脏写成 `Ω` 的真实 MLCC 未被误伤。
- 仍留有一批后续独立问题：主库里约 `842` 条真实 MLCC 的 `容值单位` 被写成 `Ω`，当前未做自动纠偏，避免把真 MLCC 误改类型；这批可在下一轮作为“单位规则清洗”单独处理。

## 2026-04-10 MLCC 容值单位规则清洗（国巨 AC 系列）
- 延续上一轮审计，补做了 `国巨YAGEO` 真 MLCC 的容值显示清洗：原库里 `914` 条 MLCC 虽然 `容值_pf` 正确，但 `容值/容值单位` 被错误写成了 `Ω / KΩ` 这类电阻单位。
- 新增 `normalize_capacitor_value_fields_from_pf()`，导入阶段会在电容类器件已具备 `容值_pf` 且显示值/单位为空或非 `PF/NF/UF` 时，按 `容值_pf` 统一回写标准电容值与单位。
- 同步新增数据库 in-place 回灌，把主库这 `914` 条错误显示值修正为标准电容表示，例如 `AC0201KRX5R6BB104 -> 100 NF`、`AC0201CRNPO9BN1R0 -> 1 PF`、`AC0201JRNPO9BN120 -> 12 PF`。
- 现有 `components_prepared_v5.parquet` 也已按同规则分块重写并刷新 meta；复核结果为主库与 prepared 层的 `MLCC + 非 PF/NF/UF 单位` 均已清零。

## 2026-04-10 MLCC 系列补全与污染系列清洗（Yageo / Taiyo / Murata / Walsin）
- 修正了 `fill_missing_series_from_model()` 的根因：`MLCC` / `常规` 这类占位系列此前会在 MLCC 画像阶段被当成“非空已完成”，导致后面的真实前缀回填规则完全失效；现在 MLCC 占位会先清空，再继续按品牌规则回填。
- 进一步把 PDC 系列回填改成品牌受限，不再全局套用，解决了 `太诱Taiyo` 的 `MSAST / MSAY / MSRL / MBARQ` 等型号被误判成 `信昌PDC MS / MBA` 并继承 `车规 / 软端子` 错说明的问题。
- 补齐并核正了高置信系列规则：`国巨YAGEO AQ / AS / CS`、`太诱Taiyo UMK / HMK / QMK / SMK / QVS / TVS / MSAS / MSART / MSAY / MSRL / MBAS / MBARQ / MCARQ / MMARQ / MCAS / MCAST / MAAS`、`村田Murata RCE / RDE / RHE / ERB / RPE / RHEL / RPER`；同时把 `AQ/AS/CS`、`CQ`、`MCARQ` 等特殊系列的类别画像补到 `车规 / 软端子 / 高Q`。
- 主库回灌后复核结果：`MLCC + 系列='MLCC'` 已降到 `0`，`太诱Taiyo + 系列='MS'/'MBA'` 已降到 `0`，`华新科Walsin` 这类无法高置信确定真实系列的 size-first 型号不再保留错误 `MLCC` 占位，而是回落为空系列。
- 现有 `components_prepared_v5.parquet` 已按 row-group 分块重写，`components_search.sqlite` 已从新 prepared 缓存重建，prepared meta 与数据库签名一致；示例已核对：`CS0402KRX7R7BB104 -> CS`、`AQ0402JRNPO9BN100 -> AQ`、`UMK063CG010CT-F -> UMK`、`MSAST021SCG220JWNA01 -> MSAS`、`MSAYE105SSD222KFNA01 -> MSAY`、`RCE5C2A122J0A2H03B -> RCE`。

## 2026-04-10 Walsin 官方系列补全（RF / HH / SH / RT / 01R5）
- 继续补 `华新科Walsin` 的官方 MLCC 系列规则：新增 `RF / HH / SH / RT / UF / 01R5` 系列画像与类别映射，来源仅采用 Walsin 官网产品家族页面，不对 `1206N... / 0805N...` 这类 numeric size-first 常规料号硬猜系列码。
- 修正了 `parse_walsin_common()` 对高 Q 两位前缀系列的解析：补入 `RF/HH/SH/RT` 的系列字段、系列说明、类别画像，并补齐 `15 -> 0402`、`11 -> 0505`、`42 -> 1808`、`43 -> 1812`、`56 -> 2225` 等 Walsin 前缀系列尺寸码映射。
- 同步补齐了 Walsin 高 Q / 软端子系列的容差码解析，`A/B/C/D` 现可正确映射为 `0.25PF / 0.1PF / 0.25PF / 0.5PF`，例如 `RT15N0R6B500CT` 现在能直接反解为 `RT / 0402 / COG(NPO) / 0.6PF / 0.1PF / 50V`。
- 已执行主库 in-place 系列回灌，共更新 `1,606` 行；其中 `RF=619`、`HH=434`、`SH=496`、`RT=19`、`01R5=38`，并确认污染值 `RF03 / HH15 / SH15 / RT15` 全部清零。
- 系列筛选联动已复核：`三星Samsung` 常规 `CL05B104KB5NNNC` 与 `CL10A106KP8NNNC` 的目标系列类别不会再命中 Walsin 的 `RF / HH / SH / RT` 候选，只会保留空系列/常规料。

## 2026-04-10 Murata 官方系列补全（RHS / LLM / LLR）
- 继续清 `Murata MLCC` 的空系列，仅补了有官方一手依据的 `RHS / LLM / LLR` 三支；`DHR / DEHR` 以及 `芯声微HRE` 的 `CAI` 因缺少足够高置信官方规则，本轮保持不动，避免误判。
- 新增 `RHS / LLM / LLR` 到 `MURATA_SERIES_PREFIX_PATTERN`、`MURATA_SERIES_MEANING` 与 `MURATA_MLCC_SERIES_CLASS`：`RHS` 归为 `车规`，`LLM / LLR` 归为 `常规`，同时提升 `SOURCE_NORMALIZED_CACHE_VERSION` 到 `7`、`QUERY_RESULT_CACHE_VERSION` 到 `9`，强制旧源标准化缓存与旧查询结果缓存失效。
- 已执行主库 in-place 系列回灌，共更新 `218` 行；其中 `RHS=191`、`LLM=20`、`LLR=7`，`Murata MLCC` 空系列从 `752` 降到 `534`，`芯声微HRE` 空系列仍为 `10`。
- 抽查样例已写实到库：`RHS7G2A101J0A2H01B -> RHS / 高温车规引线型 / High-temperature leaded automotive MLCC / 车规`，`LLM215R71C104MA11K -> LLM / 常规低ESL / 10 terminals low ESL MLCC for General Purpose`，`LLR185C70G105ME01K -> LLR / 常规低ESL控ESR / LW reversed controlled ESR low ESL MLCC for General Purpose`。
- 已重建 `components_prepared_v5.parquet` 与 `components_search.sqlite`；类别筛选复核为 `车规 -> 常规` 不再互相放行，因此 `RHS` 不会再混入常规 MLCC 推荐。

## 2026-04-10 Murata 官方系列补全（DEH / DEJ / DHR）
- 继续补 `Murata MLCC` 的高置信空系列，这轮新增 `DEH / DEJ / DHR` 三支官方系列画像；其中 `DEHR*` 型号统一回到 `DEH`，`DEJE* / DEJF*` 统一回到 `DEJ`，`DHR*` 保持 `DHR`。
- 新增 `DEH / DEJ / DHR` 到 `MURATA_SERIES_PREFIX_PATTERN`、`MURATA_SERIES_MEANING` 与 `MURATA_MLCC_SERIES_CLASS`：`DEH / DEJ / DHR` 全部打上 `高压` 类别，避免后续常规 MLCC 继续混出这批高压/超高压料。
- 已执行主库 in-place 系列回灌，共更新 `168` 行；其中 `DEH=109`、`DEJ=23`、`DHR=36`，`Murata MLCC` 空系列从 `534` 进一步降到 `367`。
- 抽查样例已写实到库：`DEHR32E152KB2B -> DEH / 高压 / High Voltage (High Temperature Guaranteed, Low-dissipation Factor (Char. R, C))`，`DEJE3E2102ZC3B -> DEJ / 高压 / High Voltage (High Temperature Guaranteed, Low-dissipation Factor (Char. D))`，`DHR4E4B101K2BB -> DHR / 超高压 / Ultrahigh Voltage`。
- 已重建 `components_prepared_v5.parquet` 与 `components_search.sqlite`；剩余 `Murata` 空系列主量当前集中在 `DEA / DEB / DEC / DEF / KC / GJ / WBM` 这几支，后续仍需按官方资料逐支确认，不能硬猜。

## 2026-04-10 BOM 结果气泡框与下载按钮位置调整
- 调整了 BOM 匹配结果区的布局：`下载 BOM 匹配后 Excel` 按钮不再放在 iframe 气泡框内部，而是改为在气泡框下方单独渲染，紧贴底部显示。
- 新增页面级 `bom-download-footer-outside` 样式，并保留右对齐按钮布局；iframe 内的 BOM 结果表不再注入下载按钮 footer。
- 同时下调 `estimate_bom_result_iframe_height()` 的基础高度，让 BOM 结果气泡框只包住表格本体，不再因为底部按钮/冗余留白把气泡框拉长。

## 2026-04-10 BOM 结果可视行数与按钮贴合再调整
- 进一步把 BOM 结果区改成“同一个 iframe 内：上方气泡框，下方按钮区”的结构，避免 Streamlit 外层组件高度和独立 markdown 块之间再产生大段空白。
- `render_clickable_result_table()` 新增 `outer_footer_html`，并由 `build_result_table_iframe_html()` 在气泡框外、但仍在同一 iframe 中输出按钮区，这样 `下载 BOM 匹配后 Excel` 会自然紧贴气泡框底边。
- `estimate_bom_result_iframe_height()` 改为按 10 行数据高度估算，并提高上限，让 BOM 结果表默认能看到 10 行数据（不含标题行）。

## 2026-04-10 BOM 手动定位按钮贴边微调
- 在 `BOM原始内容预览` 下方新增独立的 `bom-manual-toggle-pull` 上拉锚点，把 `找不到规格手动定位匹配位置` 按钮单独往上吸附，不修改上方预览表格的显示参数。
- 手动定位按钮所在列改为单独注入上拉锚点后再渲染 `st.button(...)`，避免只靠外层空白抵消导致间距不稳定。

## 2026-04-10 BOM 手动定位按钮贴边再修正
- 放弃只拉按钮本体的做法，改为直接给 `BOM原始内容预览` 下方锚点后的整行 `stHorizontalBlock` 加负 `margin-top`，让整颗 `找不到规格手动定位匹配位置` 按钮像下载按钮一样贴近上方气泡框。
- 保留 `BOM原始内容预览` 的 `st.dataframe(..., height=220)` 不变，只调整按钮行容器的垂直间距，避免再改预览表格参数。

## 2026-04-10 BOM 手动定位按钮改为 HTML 贴底按钮
- 彻底放弃 `st.button` 方案，改成和 `下载 BOM 匹配后 Excel` 同一套 HTML 按钮样式，避免 Streamlit 组件自身的隐藏留白继续把按钮撑离气泡框底部。
- 新增 `bom_manual_mapping_toggle` 查询参数切换逻辑：点击按钮后通过 URL 参数触发展开/收起，再立即清掉参数并 `st.rerun()`，从而保留原有手动定位开关行为。
- `BOM原始内容预览` 下方按钮区改为单独的 HTML footer，并通过 `bom-preview-toggle-anchor` 对应容器直接上拉，让按钮贴近预览表格气泡框底部，同时不修改预览表格的 `height=220` 参数。

## 2026-04-10 17:35 BOM 原始内容预览按钮位置对齐结果卡片
- 按用户给的对照图继续收紧 `BOM原始内容预览` 下方 `找不到规格手动定位匹配位置` 按钮的位置，目标是让它和 `下载 BOM 匹配后 Excel` 一样，贴着上方气泡框底部显示。
- 这次不再沿用 `st.dataframe(...)` 预览表；已改为复用结果区同一套 iframe 卡片表格渲染，新增 `render_static_preview_table()` 与 `estimate_bom_preview_iframe_height()`，让预览区本身的气泡框和结果区保持一致的壳层结构。
- 同时把 `bom-preview-toggle-anchor` 所在容器的上拉间距从 `-8px` 收紧到 `-12px`，让手动定位按钮更贴近预览气泡框底边。
- `python -m py_compile component_matcher.py` 已通过；本轮修改只涉及 `component_matcher.py` 的 BOM 预览显示链路和按钮间距，不影响匹配逻辑与导出逻辑。

## 2026-04-10 21:31 会员系统与错误回报审核流程独立样板
- 按用户要求试做了一版完全独立的会员/审核原型，不接到当前公版入口，也没有改现有 `streamlit_app.py` / `component_matcher.py` 的正式逻辑；样板文件为 [member_feedback_prototype_app.py](C:/Users/zjh/Desktop/data/member_feedback_prototype_app.py)、[member_feedback_prototype_store.py](C:/Users/zjh/Desktop/data/member_feedback_prototype_store.py) 和说明文档 [MEMBER_FEEDBACK_PROTOTYPE.md](C:/Users/zjh/Desktop/data/MEMBER_FEEDBACK_PROTOTYPE.md)。
- 原型库单独落在 `prototype_data/member_feedback_prototype.db`，运行时自动创建，里面拆出了 `users / registration_requests / component_rows / feedback_tickets` 四类数据；审核通过后只更新这套原型库，不碰当前正式版 `components.db`。
- 样板流程已覆盖：注册申请账号、管理员审核开通、会员查看匹配结果样板、结果表最后一栏 `回报错误`、用户直接修改字段并填写备注提交、管理员审核通过/驳回、审核通过后写回原型匹配数据。
- 已完成的验证包括：`python -m py_compile member_feedback_prototype_store.py member_feedback_prototype_app.py` 通过；临时测试库里验证了 `demo / demo123`、`admin / admin123` 登录成功，注册申请成功，纠错单提交成功，管理员审核通过后原型行数据确实更新。
- 当前这是“方向样板”，重点是给用户先看会员/审核/纠错的交互闭环；如果后续确认方向没问题，再把权限体系、工单字段、数据库更新规则迁进公版会更稳。

## 2026-04-10 21:42 会员样板登录后 HTML 露出与回报错误按钮无效修复
- 用户实测发现 `demo` 账号登录后，顶部统计卡片区域直接露出 `<div class=...>` 原始 HTML，同时匹配结果区的 `回报错误` 按钮只是表面链接，点击后无法稳定进入可编辑表单。
- 根因一是 `metrics_html()` 里拼卡片时沿用了多行缩进 HTML，Streamlit 会把带前导空格的块按 markdown code block 处理，导致部分 HTML 原样显示。根因二是样板最初把操作按钮做成了自定义 HTML 表格里的 `<a href="?edit_row=...">`，在 Streamlit 的自定义块里交互不稳定，不能当成真正的业务按钮依赖。
- 已改为：新增 `render_html_block()` 做去缩进后的稳定 HTML 渲染；顶部统计卡片改成纯拼接字符串输出，不再把带缩进的 `<div>` 喂给 markdown。匹配结果区则改成原生 Streamlit 行布局 `render_feedback_rows()`，每行最后一栏都使用真正的 `st.button("回报错误")`，点击后通过 `prototype_edit_row_id` 会话态进入下方纠错编辑表单。
- 同时补了 `set_active_edit_row()` / `get_active_edit_row_id()` / `clear_active_edit_row()`，让编辑态不再只靠 query 参数；点击按钮、提交成功、取消编辑、退出登录都会正确同步清理状态。
- `python -m py_compile member_feedback_prototype_app.py member_feedback_prototype_store.py` 已再次通过，本地样板服务已重启到 `http://localhost:8510`，可让用户直接刷新复测新的交互版本。

## 2026-04-10 22:40 保留原匹配页面的会员整合原型
- 用户明确希望样板保留“原本匹配系统页面”，而不是只看独立会员后台，因此额外创建了独立原型副本 [component_matcher_member_prototype.py](C:/Users/zjh/Desktop/data/component_matcher_member_prototype.py) 与入口 [streamlit_member_prototype_app.py](C:/Users/zjh/Desktop/data/streamlit_member_prototype_app.py)，不修改正式版 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py)。
- 原型库 [member_feedback_prototype_store.py](C:/Users/zjh/Desktop/data/member_feedback_prototype_store.py) 已扩成可承接真实匹配结果行：新增 `idx_component_rows_brand_model` 唯一索引，以及 `ensure_component_row_from_payload()`、`get_component_row_by_identity()`、`overlay_component_payload_with_store()`，让匹配结果能落到独立原型库，并在管理员审核通过后覆盖回原型显示层。
- 在原型副本里补入了会员登录/注册申请/我的回报/管理员注册审核/管理员纠错审核/原型数据页路由；登录后若选择 `匹配系统`，继续走原本搜索与 BOM 页面，不会像前一版那样把匹配系统页面替换掉。
- 匹配结果表 `render_clickable_result_table()` 已在原型副本中额外插入 `回报错误` 列：每行都会先 `ensure_component_row_from_payload()` 落到原型库，再输出 `target="_top"` 的操作链接，点后会在当前页面底部出现 `回报错误编辑区` 表单，支持直接修改字段并提交备注。
- 验证情况：`python -m py_compile member_feedback_prototype_store.py component_matcher_member_prototype.py streamlit_member_prototype_app.py` 通过；整合原型已启动到 `http://localhost:8512` 并返回 `HTTP 200`。说明文档 [MEMBER_FEEDBACK_PROTOTYPE.md](C:/Users/zjh/Desktop/data/MEMBER_FEEDBACK_PROTOTYPE.md) 也已补充“仅会员样板”和“保留原匹配页整合原型”两种入口说明。

## 2026-04-10 23:41 会员整合原型主页面可见会员区与 BOM 预览按钮回调
- 用户实测 `http://localhost:8512` 后反馈三件事：登录 `demo` 后上传 BOM 看起来像回到普通版、手动定位按钮又悬在预览表下方、以及会员账号看不到“会员专区 / 当前账号 / 退出会员按钮”。根因确认是整合原型此前把会员入口完全放在侧边栏，而默认侧边栏又是收起状态；同时 `BOM原始内容预览` 的 iframe 高度下限设得过大，导致预览表下面出现明显留白，把按钮继续往下推。
- 已在 [component_matcher_member_prototype.py](C:/Users/zjh/Desktop/data/component_matcher_member_prototype.py) 中新增主页面可见的 `会员专区` 头部壳层：显示当前账号、登录名、身份、当前页面与团队信息，并把页面切换入口改成主内容区的横向 `radio`，同时保留 `退出会员登录` 按钮，不再依赖用户先展开侧边栏才能看到会员能力。
- 同时下调 `estimate_bom_preview_iframe_height()` 的基础高度与最小高度，把 `BOM原始内容预览` 根据真实预览行数收紧，减少预览卡片底部空白；并把 `bom-preview-toggle-footer` 再上拉 `2px`，让 `找不到规格手动定位匹配位置` 更贴近预览区底边。
- 本轮只修改整合原型副本，不触碰公版文件；`python -m py_compile component_matcher_member_prototype.py streamlit_member_prototype_app.py` 已通过，`8512` 进程已重启并返回 `HTTP 200`，等待用户刷新页面复测主页面会员区与 BOM 预览按钮位置。

## 2026-04-12 00:39 正式版原厂料号卡片补充官方规格摘要并加数据库直查兜底
- 用户继续在正式版实测时指出：搜索 `CM13093CT-102` 虽然应该能认出是 Bourns 原厂料号，但页面却表现成“没有其他品牌匹配”且看不到规格参数，怀疑是不是数据库里根本没有这颗品牌型号。本轮先对正式版搜索链路做了逐层排查。
- 现场确认结果不是“数据库缺料号”：在正式版 [components.db](C:/Users/zjh/Desktop/data/components.db) 中，`CM13093CT-102` 可被 `型号` 与 clean model 两种方式直接命中；`resolve_prefetched_exact_part_rows()`、`detect_query_mode_and_spec()` 与 `load_component_rows_by_query_model_tokens()` 也都能把它识别成 `料号`，并带出 `Bourns / 共模电感 / 安装方式 / 尺寸(mm) / 规格摘要 / 数据来源`。
- 真正的问题在于正式版原厂资料卡的展示 schema 以前只盯着 `电感值 / 共模阻抗 / 额定电流 / DCR` 这类结构化列；而 `CM13093CT-102` 当前这批官方来源属于“官网系列页摘要型数据”，关键信息主要存放在 `尺寸（mm） / 规格摘要 / 特殊用途`，因此卡片虽然命中了原厂行，却会视觉上像“没规格”。
- 已在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 的 `build_part_info_df()` 中补上正式版原厂料号卡片的电感类附加列：当器件类型属于 `功率电感 / 共模电感 / 磁珠` 时，会把 `尺寸（mm） / 规格摘要 / 特殊用途` 一并挂到原厂资料卡尾部，再接 `官网链接 / 数据来源`。这样像 `CM13093CT-102` 现在会直接看到 `13 x 16 x 9.2 mm | 1.0 +50 %/-35 % | 10 Ω – 5,000 Ω | 2.8 A` 这类官方摘要。
- 同时新增一个正式版搜索兜底：在搜索页主循环里，如果当前输入先被判到 `无法识别 / 规格不足`，但它本身长得像完整料号且数据库能直查到原厂行，就强制切回 `料号` 分支，按数据库原厂资料继续展示，不再把这类真实存在的型号误记到“需要补充或修正输入”。
- 本地校验结果：`python -m py_compile component_matcher.py component_matcher_build.py` 通过；函数级验证 `CM13093CT-102` 当前 `resolve_search_query_dataframe_and_spec()` 返回 `mode=料号 / candidate_rows=1`，`build_part_info_df()` 已能输出 `尺寸（mm） / 规格摘要 / 特殊用途 / 数据来源`；正式版 `8511` 已重启并返回 `HTTP 200`。

## 2026-04-11 18:48 正式版电感官方库已同步入正式库并改成增量刷新缓存
- 用户继续要求正式版往“可工作使用”的方向推进，本轮继续只动正式版 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) / [components.db](C:/Users/zjh/Desktop/data/components.db) / [cache/components_search.sqlite](C:/Users/zjh/Desktop/data/cache/components_search.sqlite) / [cache/components_prepared_v5.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared_v5.parquet)，未触碰已冻结的测试板与会员原型。
- 先把 [build_inductor_official_sources.py](C:/Users/zjh/Desktop/data/build_inductor_official_sources.py) 扩成真正纳入 Bourns 官方页面抓取：新增并接通 `power inductors / RF chokes / common-mode chokes / EMC chokes` 四类官方页面来源，并在生成阶段做型号清洗与同键合并，去掉 `Series / MDS / 区间文本` 之类脏 token。官方扩展表 [Inductor/official_inductor_expansion.csv](C:/Users/zjh/Desktop/data/Inductor/official_inductor_expansion.csv) 由 363 条扩到 438 条，现包含 `Bourns 功率电感 230 / Bourns 共模电感 59 / Würth 功率电感 134 / Würth 共模电感 13 / Würth 磁珠 2`。
- 为了让这批官方数据能持续增量落库，新增正式版同步脚本 [sync_inductor_official_to_db.py](C:/Users/zjh/Desktop/data/sync_inductor_official_to_db.py)：按 `器件类型 + 品牌 + 型号` 替换正式库中对应键，并只刷新受影响型号的搜索侧库与 prepared cache，不再走整库全量重建。
- 同时补强正式版电感官方推断保护：在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 里新增 `text_contains_inductance_range / text_contains_current_range / text_contains_impedance_range`，并把 `infer_official_inductor_fields_from_row()` 与 `infer_component_display_fallbacks_from_row()` 两层都改成“遇到范围只保留范围摘要，不抠成假精确值”。这次专门修掉了 `CM13093CT-102 / CM13090CT-242 / CM13092CT-412 / CM13091CT-872` 这类共模电感把 `10Ω / 25Ω / 50Ω / 100Ω` 区间下限误写成精确阻抗的问题。
- 本地执行结果：`python sync_inductor_official_to_db.py` 返回 `source_rows=438 deleted=438 inserted=438`，同步后 `after_summary` 显示 `共模阻抗` 由 3 清到 0、`阻抗单位` 仅保留 2 条有明确值的记录；再做 `official_inductor_expansion.csv` 与正式版 `components.db` 的逐键比对，得到 `mismatch_count=0`，说明这批官方电感键已与正式库完全对齐。
- 抽样核对：`CM13093CT-102` 现在只保留 `13 x 16 x 9.2 mm | 1.0 +50 %/-35 % | 10 Ω – 5,000 Ω | 2.8 A` 这类范围摘要，不再显示伪造的精确 `共模阻抗=10Ω`；`SDE0403AT` 也仅保留 `1 - 68 µH | 0.4 - 2.7 A` 区间摘要，不再把系列页范围误当成单一规格值。`FC2012AN` 的正式版原厂资料卡片仍保持正常显示 `石英晶体（Crystal Unit） / FC2012 / 32.768kHz / 数据来源`。

## 2026-04-11 18:48 正式版电感官方库已同步入正式库并改成增量刷新缓存
- 本轮继续推进正式版，不触碰测试板/会员原型；重点把 [Inductor/official_inductor_expansion.csv](C:/Users/zjh/Desktop/data/Inductor/official_inductor_expansion.csv) 这批官方 `功率电感 / 共模电感 / 磁珠` 数据真正落进正式版数据库与缓存链路，而不是只在前端显示时临时推断。
- 已在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 补强正式版入库归一化：对电感类官方源，若原始表把电感量放在 `容值 / 容值单位`，现在会自动回填到 `电感值 / 电感单位`，例如 `PQ2614BHA` 在入库阶段就能得到 `2.2 / UH`，不再只有页面展示时才补得出来。
- 新增正式版定向同步脚本 [sync_inductor_official_to_db.py](C:/Users/zjh/Desktop/data/sync_inductor_official_to_db.py)：会按 `器件类型 + 品牌 + 型号` 精准替换这批 363 条官方电感键到 [components.db](C:/Users/zjh/Desktop/data/components.db)，避免“旧浅数据仍留在正式库里、搜索继续混到旧行”的问题。
- 同时把缓存刷新逻辑从“全量重建整库”改成“仅刷新受影响键”：
  正式版搜索侧库 [cache/components_search.sqlite](C:/Users/zjh/Desktop/data/cache/components_search.sqlite) 现在只删除并回写这批受影响型号对应的 sidecar 行，再重写 meta。
  正式版 prepared cache [cache/components_prepared_v5.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared_v5.parquet) 现在只替换这批官方电感在 prepared 数据里的旧行，并同步更新 [cache/components_prepared_v5_meta.json](C:/Users/zjh/Desktop/data/cache/components_prepared_v5_meta.json)。
- 这样做的原因是前一版全量刷新虽然数据库写入成功，但整库 prepared cache 重建会拖很久；现在已改成适合后续持续拓库的正式版增量刷新方式。
- 本地执行结果：`source_rows=363 deleted=363 inserted=363`，并确认 `prepared_cache_is_current=True`、`search_index_is_current=True`。抽样检查 `PQ2614BHA / 784831047068 / 7427511 / DR221` 已能在正式库与 prepared cache 中看到更新后的 `系列 / 系列说明 / 电感值 / 电感单位 / 额定电流 / DCR / 工作温度 / 安装方式 / 数据来源` 等字段；正式版 `8511` 也已重启到新缓存进程。

## 2026-04-11 17:28 正式版料号搜索卡片改为按真实器件类型展示
- 用户反馈正式版搜索 `FC2012AN` 时，页面虽然已能命中原厂料号，但 `匹配料号资料` 仍显示成旧版通用表头，看起来像“还是没有”；根因是这块卡片之前按输入解析出来的 `spec` 决定栏位，而不是按数据库命中的真实器件类型决定栏位，导致晶振/电感等器件被降级成通用显示。
- 已在正式版 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 调整 `resolve_component_display_type()` 与 `build_part_info_df()`：命中数据库行后会优先按真实器件类型渲染表头，并把 `官网链接 / 数据来源` 接到原厂资料卡片尾部。现在 `FC2012AN` 会显示 `石英晶体（Crystal Unit） / 系列 / 系列说明 / 频率 / 频差 / 工作温度 / 官网来源`，不再只剩品牌型号和空白参数。
- 同时把“已找到原厂料号资料，但暂无其他品牌替代结果”从失败态改成明确提示，不再把这种情况算成纯 `无匹配`，减少用户看到 `成功 0 / 无匹配 1` 时误以为连原厂资料都没查到的误解。
- 顺手补齐了正式版电感系列说明刷新逻辑：像 `PQ2614BHA` 这类官方库数据，系列已识别为 `SRP` 时，系列说明也会同步更新为 `Bourns SRP 屏蔽功率电感系列`，不再残留旧的型号文案。
- 本地校验结果：`python -m py_compile component_matcher.py component_matcher_build.py` 通过；抽样验证 `FC2012AN / 784831047068 / 7427511 / PQ2614BHA` 的原厂资料卡片均已按真实器件类型输出对应关键字段。正式版 `8511` 也已重启到新代码进程。

## 2026-04-11 10:59 测试板改为更偏工作台的判读视图
- 用户希望先在测试板按“更适合实际工作”的方向试做一版，但明确要求正式版不要动。本次仅修改 [component_matcher_member_prototype.py](C:/Users/zjh/Desktop/data/component_matcher_member_prototype.py)，未触碰公版入口或正式版逻辑文件。
- 在搜索页加入了“结果建议”卡：会根据当前候选的推荐等级自动归纳成“可优先采用 / 需人工确认 / 建议逐笔判断 / 未找到结果”，并直接给出下一步动作建议，减少用户看完表格还要自己二次判断的成本。
- 在 BOM 结果页加入了“BOM 工作视图”：先把结果按 `可直接采用 / 需人工确认 / 无匹配 / 解析失败` 四类汇总展示，再提供一组筛选按钮，只看某一类结果时会直接过滤下方表格；同时在表格里新增 `工作判断` 和 `下一步建议` 两列，让每一行的处理方式更直接。
- 顺手把“找不到规格手动定位匹配位置”按钮改成靠近说明区的工具条样式，不再沿用右下角下载按钮的摆法，避免测试板继续出现“按钮位置像跑掉”的观感。
- 本地校验结果：`python -m py_compile component_matcher_member_prototype.py streamlit_member_prototype_app.py` 通过；重启 `8512` 测试板进程后，`http://127.0.0.1:8512` 返回 `HTTP 200`，stderr 日志未出现新的 Python 异常。

## 2026-04-11 00:12 会员整合原型回退到公版 BOM 预览按钮位置
- 用户指出“按钮问题没解决”，并要求对照公版确认真实位置。已使用 Playwright 对本机公版 `http://localhost:8511` 复测同一份 `阻容-POLED-报价.xlsx`：公版当前实际效果就是 `BOM原始内容预览` 下方留一段明显空白后，按钮才出现在更靠下的位置；之前把原型往上贴近气泡框的判断不准确。
- 因此已把 [component_matcher_member_prototype.py](C:/Users/zjh/Desktop/data/component_matcher_member_prototype.py) 中与 BOM 预览按钮相关的两处改动回退到公版参数：`estimate_bom_preview_iframe_height()` 恢复到和 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 一致的 `base=86 / per_row=42 / min_height=220 / max_height=320`，`bom-preview-toggle-footer` 也恢复为 `margin-top: 0`，确保整合原型 BOM 预览区与公版布局一致。
- 同时对 `8511` 和 `8512` 都做了同文件上传复测，发现两者当前都会停在 `已处理 1/64 行 · 2% · 第 2 行` 这一状态；这说明“BOM 卡在 2%”不是会员原型单独引入的回归，而是当前本机匹配链路本身也存在问题。由于用户本轮主要先追按钮基准，当前先保留这个确认结论，后续再单独继续追 BOM 卡住根因更稳。

## 2026-04-11 09:55 8512 本地测试版进程掉线后重新拉起
- 用户反馈 `http://localhost:8512` 打不开，浏览器报 `ERR_CONNECTION_REFUSED`。现场确认后发现不是页面代码本身报错，而是 `8512` 端口当时没有进程在监听，`8510` 和 `8511` 仍然正常。
- 通过 `Start-Process python -m streamlit run streamlit_member_prototype_app.py --server.address 127.0.0.1 --server.port 8512 --server.headless true` 重新拉起整合测试版，并将 stdout/stderr 继续写回 `tmp_8512_stdout.log` / `tmp_8512_stderr.log`。
- 复测结果：`8512` 已恢复监听并返回 `HTTP 200`，可通过 `http://127.0.0.1:8512` 继续访问整合测试版。

## 2026-04-11 10:09 会员整合原型修复登录态恢复缺失辅助函数
- 用户刷新 `8512` 后又遇到 `NameError: name 'set_query_param' is not defined`，报错点在 `prototype_bootstrap_auth_state()` 和 `prototype_login_user()` 的 query param 写入链路。
- 已在 [component_matcher_member_prototype.py](C:/Users/zjh/Desktop/data/component_matcher_member_prototype.py) 的 `get_query_param_text()` 后补回 `set_query_param()` 与 `clear_query_param()`，并重新启动 `8512` 进程。
- 复测结果：`http://127.0.0.1:8512` 返回 `HTTP 200`，语法检查 `python -m py_compile component_matcher_member_prototype.py streamlit_member_prototype_app.py` 通过。

## 2026-04-11 10:20 BOM 结果表“回报错误”列空白修复
- 用户指出 BOM 匹配结果表最后一栏标题虽然在，但每一格都没有可点击按钮。排查后确认不是表格列没画出来，而是 [prototype_result_row_payload](C:/Users/zjh/Desktop/data/component_matcher_member_prototype.py#L15200) 只认普通匹配表的 `品牌/型号`，而 BOM 结果页实际更多用的是 `推荐品牌/推荐型号`、`推荐品牌1/推荐型号1` 等列。
- 已将 [component_matcher_member_prototype.py](C:/Users/zjh/Desktop/data/component_matcher_member_prototype.py) 的按钮身份提取改成多字段兜底：优先读 `品牌/型号`，再读 `推荐品牌/推荐型号` 与备选推荐槽位；若仍为空，则用 `BOM行号` 生成临时身份，确保最后一栏不再整列空白。
- 同时把该函数复用给 `prototype_overlay_row_from_store()`，这样后续管理员审核通过的纠错结果也能继续回写到同一条原型记录。`python -m py_compile component_matcher_member_prototype.py` 已通过，整合测试版 `8512` 仍返回 `HTTP 200`。

## 2026-04-11 11:40 正式版拓库与参数明细显示增强
- 本轮回到正式版 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py)，未触碰已冻结的测试板/会员原型；重点是把“库不够深、系列说明不稳、各器件参数展示不够详细”的问题先往前推进一版。
- 已扩充正式版展示字段与回填逻辑：新增并接通 `封装代码 / 生产状态 / 直径（mm） / 极性 / ESR / 纹波电流 / 阻值@25C / 阻值单位 / 阻值误差 / B值 / B值条件 / 共模阻抗 / 阻抗单位 / 额定电流 / DCR / 回路数 / 电感值 / 电感单位 / 电感误差 / 饱和电流 / 屏蔽类型 / 阻抗@100MHz / 负载电容（pF） / 驱动电平 / 输出类型 / 占空比` 等明细字段，并补了从备注/规格文本反推这些字段的兜底逻辑。
- 已增强不同器件的显示 schema：铝电解会优先展示直径/高度、极性、ESR、纹波电流；热敏电阻展示 `R25 / 阻值误差 / B值 / B值条件`；功率电感/共模电感/磁珠各自展示最关键的选型参数；晶振/振荡器分别展示 `负载电容 / ESR / 驱动电平` 与 `输出类型 / 占空比 / 电源电压`。
- 已同步一批正式库数据到 [components.db](C:/Users/zjh/Desktop/data/components.db)：Murata 官方 NTC 明细、Epson 晶振与振荡器资料，并补齐正式库所需的时间元件扩展列，如 `频率 / 输出频率 / 频率单位 / 频差（ppm） / 电源电压 / 输出类型 / 占空比 / 负载电容（pF） / 驱动电平`。同步后又增量刷新了正式版缓存 [cache/components_prepared_v5.parquet](C:/Users/zjh/Desktop/data/cache/components_prepared_v5.parquet) 与搜索侧库 [cache/components_search.sqlite](C:/Users/zjh/Desktop/data/cache/components_search.sqlite)，避免正式版还在读旧展示数据。
- 进一步修正正式版展示清洗：`clean_voltage()` 现在会把 `None / nan / n/a` 这类占位文本清空，不再出现 `NONEV`；同时把 `1.7 to 3.63V`、`13 to 55.2 MHz` 这种范围值规范成 `1.7~3.63V`、`13~55.2` 的正式展示格式，避免参数读起来生硬。
- 本地校验结果：`python -m py_compile component_matcher.py component_matcher_build.py` 通过；抽样验证显示链路已能正确得到 Murata NTC 的 `100000Ω / ±0.5% / 4250K / 25/50℃`，以及 Epson 振荡器的 `13~55.2MHz / ±0.5% / 1.7~3.63V / 输出类型 / 工作温度`。

## 2026-04-11 12:05 正式版料号搜索补上中英双语器件类别
- 用户指出正式版精确料号搜索里，`匹配料号资料` 经常只看得到品牌和型号，看不出这个料号到底是该品牌的哪一种元器件；例如爱普生 `FC2012AN` 之前只能看到 `爱普生Epson / FC2012AN`，却没有明确显示它是晶体产品。
- 已在正式版 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 新增统一展示字段 `器件类别`，并做成中英双语值，例如 `陶瓷贴片电容（MLCC）`、`热敏电阻（NTC Thermistor）`、`石英晶体（Crystal Unit）`、`晶体振荡器（Oscillator）`、`功率电感（Power Inductor）` 等；该字段只用于前端显示，不改数据库原始 `器件类型` 字段。
- 该双语器件类别已接到正式版两条主要显示链路：一是精确料号搜索的 `匹配料号资料` 表，二是匹配结果表中的候选型号行。搜索页标题也改成优先显示双语器件类别，例如 `石英晶体（Crystal Unit）匹配结果（含推荐等级）`。
- 本地实测 `FC2012AN` 现在会显示 `爱普生Epson / FC2012AN / 石英晶体（Crystal Unit） / FC2012 / 32.768kHz / ±20% / 2012`；`NCP02WF104D05RH` 会显示 `热敏电阻（NTC Thermistor）`，确认不是只针对单一品牌生效。

## 2026-04-12 03:02 公开版修复云端搜索索引误判导致卡在预取精确料号
- 用户在公开版 `https://fruition-component.pages.dev/` 搜索 `CM13093CT-102` 时，页面卡在“正在预取精确料号 / 进度 0/1 / 预取数 1”，没有继续往下返回结果。
- 继续排查公开版 Streamlit Community Cloud 链路后确认，`cache/components_search.sqlite` 和 prepared cache 的 meta 里记录的是本地 Windows `components.db` 绝对路径；云端运行时路径不同，导致 `search_index_is_current()` / `prepared_cache_is_current()` 误判为过期，并尝试触发整库重建，因此前端会停在预取精确料号阶段。
- 已在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 新增公开版 bundle 运行态兜底：当云端 bundle 已是当前版本时，搜索索引和 prepared cache 改按 `schema/cache version + bundle 当前状态` 判断是否可用，不再因为 `db_path` 与本机不同就触发重建。
- 待完成本地语法校验与公开版重新发布后，再用 `CM13093CT-102` 在正式网页实测，确认不再卡在预取阶段。

## 2026-04-12 04:05 公开版料号表尺寸栏统一为单列
- 用户要求把 `尺寸（inch）` 的表头改成 `尺寸`，并把刚刚加出来的 `尺寸（mm）` 后缀列去掉，统一放回前面的尺寸栏。
- 已在 [component_matcher.py](C:/Users/zjh/Desktop/data/component_matcher.py) 的展示层做统一尺寸处理：前端表格现在会优先显示 `尺寸（inch）`，若为空则回填 `尺寸（mm）`、`尺寸(mm)` 或 `._body_size`，并把表头改为 `尺寸`。
- 同时移除了共模电感结果页里额外插入的 `尺寸（mm）` 后缀列，避免表格右侧再出现第二个尺寸栏。
- 本地验收结果：`CM13093CT-102` 的展示记录现在能显示 `13 x 16 x 9.2 mm` 进入单一尺寸栏，且输出列里不再额外带出 `尺寸（mm）` 后缀。

## 2026-04-12 18:19 direct Murata 电感家族继续拓库
- 继续按用户要求扩正式版电感库，新增独立导入脚本 [sync_murata_inductor_family.py](C:/Users/zjh/Desktop/data/sync_murata_inductor_family.py)，一次性抓取 Murata 官方 PIM 的 5 类电感相关数据：`功率电感 / RF 高频电感 / 通用电感 / 共模电感 / 磁珠`。
- 本轮落库后，Murata 官方家族总计新增 `8086` 条，当前正式库里 Murata 家族相关记录为 `8086` 条，其中功率电感 `6846` 条、共模电感 `185` 条、磁珠 `1055` 条。官方扩展表 [Inductor/murata_inductor_family_expansion.csv](C:/Users/zjh/Desktop/data/Inductor/murata_inductor_family_expansion.csv) 也已写出并合并进 [Inductor/official_inductor_expansion.csv](C:/Users/zjh/Desktop/data/Inductor/official_inductor_expansion.csv)。
- 这次的导入保留了官网链接、规格摘要、工作温度、额定电流、DCR、共模阻抗、阻抗@100MHz 等字段；同时把尺寸展示统一成物理尺寸 `尺寸（mm）`，`尺寸（inch）` 留空，避免再把 0102 这类包码当作主显示值。
- `components.db`、搜索侧缓存和 prepared cache 都已经增量刷新完成，本地抽样确认 `LQP01HV0N3B02# / LQH32NH100X23L05 / 50105AC / DFE2MCPHR10MJLLQ` 都能读到新的规格摘要和物理尺寸。

## 2026-04-12 20:16 SUMIDA 电感拓库收口
- 继续按用户要求补胜美达 SUMIDA 官方功率电感库，抓取并规范化 `4890` 条官方料号，品牌统一写入 `胜美达SUMIDA`，器件类型统一为 `功率电感`。
- 已同步修正 `components.db`、`cache/components_search.sqlite` 与 `cache/components_prepared_v5.parquet`，并清理 prepared cache 里残留的旧 `Sumida` 记录，当前三处数量一致。
- 这批数据保留了官方尺寸、感量、额定电流、饱和电流、DCR、工作温度与系列说明，后续可直接用于正式版搜索和 BOM 匹配。
