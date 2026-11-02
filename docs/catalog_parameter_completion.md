# MLCC catalogue parameter completion

The catalogue completes **existing indexed identities only**, in connection-local
temporary tables. It does not rewrite the prepared library, search store, runtime
databases or model-generation rules. Counts, filtering, sorting and displayed
values all query the same completed table. Missing data is never zero.

Priority: nonempty indexed value → one actual prepared record's explicit field →
established brand-specific model decoder. Conflicting known values are preserved;
duplicate records are not merged into a fabricated combined specification.

Additional narrowly scoped corrections:

* Sunway MC/MA/MH `0100`: manufacturer body 0.40×0.20mm, normalize the vendor code
  to standard 01005 inch. No unscoped `0100` replacement for other brands.
  Manufacturer-authored source: [Sunway MLCC specification, construction/dimensions](https://atta.szlcsc.com/upload/public/pdf/source/20260421/0F84881359996816E3F1000B3F12305B.pdf).
* CCTC TCC0603/0805/1206 M3L: retain **M3L**, never relabel it X7R or C0G.
  Manufacturer-authored source: [CCTC DRAAW108H/0-2020, numbering section](https://www.compel.ru/wordpress/wp-content/uploads/2022/10/cctc_m3l-series.pdf).
* Mounting: an explicit prepared mounting value wins. Only recognized chip
  families with an already validated standard SMD footprint receive `贴片`.
  A generic MLCC classification alone is insufficient: for example legacy
  Murata DE* leaded parts and unknown families remain unclassified.
* Absolute pF tolerances stay absolute and display with their unit. They must not
  turn into percent values. [Yageo manufacturer numbering table, page24](https://www.mouser.com/pdfDocs/yageo-mlcc_2018_0720.pdf)
  and [Samsung manufacturer numbering reference](https://product.samsungsem.com/mlcc/basic-search.do)
  explain the distinction.

The existing brand decoder is accepted only when its authority marker and brand
agree with the record and it does not identify a different device type. This is
blank completion, **not proof a generated ordering combination is sold**.

Do not infer safety certification, production status, actual availability, body
thickness or test-condition-dependent electrical limits from these rules.
Unverified/unsupported codes remain missing until primary-source confirmation.
Prepared MLCC reads are projected to identity and these four parameter families;
prices, customer data and authentication columns are never loaded. Retrieval is
lazy when the specification catalogue is used, not ordinary-search startup.

## Browse-query performance — 2026-10-28

After all existing parameter and lifecycle overlays, each shared passive-kind
resource freezes **only the public filter fields**, exact identities and lifecycle
citations into a narrow connection-local `catalog_browse_source`. Unit expressions
are evaluated once; known zero, missing values, duplicates and original source
conflicts keep the same semantics. No new model or electrical value is inferred.
The original published index, prepared asset and protected runtime stores are not
modified. The temporary projection is discarded with its read-only connection.

Two TEMP indexes support existing brand/model ordering and the exact existing
deduplication identity. The uniqueness audit runs on this completed projection,
not a second random-read scan of the whole raw sidecar.

Within the existing per-source lock, an aggregate-only LRU cache reuses the total,
facet counts and numeric bounds by SQL and bound values. Page, page size, sort and
membership changes cannot force identical aggregates to run again. A facet still
excludes its own selection, so its unchanged counts can also be reused. Fresh
conditions produce fresh counts; no approximation, sampling or stale-while-loading
results are introduced. Model page rows are fetched separately and the original
member gate, matching handoff, display, comparison and CSV actions are unchanged.

The cache belongs to one frozen connection/revision/kind, never a member or cost
scope; it rejects cross-connection reuse. It holds at most 128 aggregate entries
and 50,000 scalar cells, with immutable stored rows and copied response lists.
Existing revision keys (code, query index/WAL and prepared asset signatures),
resource expiry and cold-restore canonicalization remain in force. No extra
source download, full-library rebuild or ordinary-search startup work is added.

Regression coverage includes pre/post filter/page/sort equivalence, converted
units, NULL/blank brands, duplicate and empty models, lifecycle source citations,
cache eviction, cross-connection rejection, anonymous row suppression, and
read-only source fingerprints. Timings are diagnostic, not test assertions: they
depend on hardware and exclude network/startup/first parameter-asset restoration.

### First category selection follow-up

The query cache above does not eliminate cold specification preparation. The
follow-up avoids decoding unrelated Parquet row groups, then conservatively
prunes resistor rows only when all indexed package/electrical fields are present
and body size is the sole additional field. Every indexed gap is retained, as
are explicit prepared bodies, physical dimensions (including Unicode text), and
existing FOJAN series-rule candidates. Rows without package/rule-resistance gaps
run only the unchanged body-size branch; explicit power/tolerance transfers
remain unchanged. Dense missing-identity sets bypass Arrow membership pruning,
avoiding a large hash rebuild for every batch. All other schemas/types retain
the general decoder.
This does not discard missing-data rows or hide missing options from the index.

MLCC's first source pass skips unchanged records only **after** first-whole-record
deduplication. Applicable SMD-family regexes are cached per public brand, without
changing their patterns, matching scope or excluding valid families. The later
indexed completion still applies all original mounting rules. On cold asset
restoration, only the published detail asset is restored before canonicalizing
the revision; details are no longer decoded twice under missing/restored keys.

The original validated temporary-table installation and final projection remain
unchanged. Data patches, lifecycle citations, duplicates, known zeros and exact
facet counts retain the same semantics.

Selecting a category immediately shows an accessible loading message. Replayed
old component arguments cannot dismiss it; a new view/acknowledgement does.
This is feedback for actual work, not an animation or stale count pretending the
category has loaded. No extra input, matching or account actions are introduced.

## FOJAN verified follow-up — 2026-10-20

FRC/FPS/FPL dimensions are taken from the **L × W × H** table on page 3,
including each axis tolerance, scoped to the exact series and size. Resistance
is decoded only where the page 2 order-code table is unambiguous. Existing
nonempty data/zero values are retained. No lifecycle state or power is inferred.

- FRC, FJ-JS-3001-V2.0/2025.09.24: [official PDF](http://www.fojan.cn/Private/Files/20260117/6390425653118283306794915.pdf)
- FPS, FJ-JS-3001-V2.0/2025.01.01: [official PDF](http://www.fojan.cn/Private/Files/20260104/6390313964867467102454149.pdf)
- FPL, FJ-JS-3001-V1.0/2025.01.01: [official PDF](http://www.fojan.cn/Private/Files/20260326/6391013095361233781944979.pdf)

The official server's HTTPS certificate failed hostname validation during this
audit; documents were retrieved through the public HTTP product-page links.
Do not disable certificate verification or send any credentials to this host.
`FPQ1206F6800TS` remains unverified: the similarly named **FQP** series is not
evidence for **FPQ**. Its size-derived power must not be promoted to rated power.
# 发布前生成的筛选数据（2026-11-02）

用户首次选择品类不应承担规格补全、TEMP 表构建和全品类初始统计。
`tools/build_catalog_ready.py --details <已核验的公开 prepared.parquet>`
现在离线执行原有完整补全及原厂生产状态流程，导出 `catalog_ready/` 中
28 个独立压缩 SQLite 文件和版本清单。每个文件只含原有筛选投影：
品牌、型号、参数、原厂状态及其公开证据，不含成本、客户、会员或登录信息。
只使用 manifest SHA256 对得上的既有公开查询索引和明细文件，不重建基础库。

运行时先校验公开源版本及规则／证据指纹，按所选品类解压并以只读方式打开；
初始总数、各参数精确数量与范围已经预计算，首次展示不再扫描全品类。
后续联动仍用相同 SQL 和精确计数，会员结果权限、排序、分页和型号交接不变。
不通过缩减物料、近似数量或先显示未补全资料来换速度。

指纹涵盖根目录规则代码、公开 catalog_sources/data JSON 与原厂状态证据；
Windows/Linux 换行差异和发布 stamp 不算规则变化。索引存在时校验真实内容，
非空 WAL、规则变化、明细变化、压缩包损坏或品类不一致均不使用该旧资产，
而回退到原有正确但较慢的路径。数据文件缺失时只读发布清单即可确认版本，
不用为了展示参数先恢复 113MB 明细。所有缓存仅存公开目录数据。

发布门禁包含 `tests.test_catalog_prebuilt`：必须覆盖全部品类、总数一致、
压缩资产校验通过、代码与证据版本一致。改动规则／证据后须重新构建。
不宣称零网络延迟；冷进程仍有应用启动和一次按品类解压，但不再逐条补规格。
