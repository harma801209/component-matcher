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
