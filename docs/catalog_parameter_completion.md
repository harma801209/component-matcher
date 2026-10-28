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
