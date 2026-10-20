# Passive catalogue specifications: missing-field repair

The specification browser now applies blank-only completion to all indexed
passive categories, not just MLCC. It does **not** claim that every historical
library row has been fully verified against a current manufacturer datasheet.
Some imported entries are series envelopes or have legacy classification errors.
Those must not be given invented scalar ratings to make a blank disappear.

## Sources and precedence

An existing nonempty indexed value (including zero) wins. Otherwise use one
actual prepared record's normalized or explicit specification fields. Keep the
first whole source record for duplicate identities; do not blend specifications
from several records. MLCC's established brand/type/authority-guarded decoder
can additionally restore missing capacitance/voltage. Existing MLCC-specific
size/material/tolerance corrections remain in effect.

| Catalogue parameter | Accepted source |
| --- | --- |
| Package / size code | Explicit inch/package code; for leaded parts, retain their actual axial/radial/package designation rather than requiring an SMD code |
| Body dimensions | Explicit physical dimensions, including tolerances and units; never a guessed size from power or a vague SMD label |
| Lead pitch | Explicit `脚距（mm）`, preserving mm |
| Capacitance / voltage | Explicit values and recognized units, or the existing verified MLCC brand decoder |
| Temperature bounds | A complete explicit working-temperature range; never a number found inside a model, storage/reflow temperature, or a dielectric class extrapolation |
| Inductance | Explicit inductance and unit; never interpret an impedance as an inductance |
| Impedance | Preserve the original range and test conditions; expose a scalar only for an unambiguous scalar label, retaining its companion condition text |
| Frequency | Explicit output/crystal frequency with unit |
| Resistance / power / tolerance | Already normalized specification fields where the indexed field is blank; power must also pass the existing `TRUSTED_RESISTOR_POWER_SOURCES` allowlist. `size` and other untrusted inferred powers remain unknown, not copied back over the index's deliberate omission |

The projected source whitelist excludes costs, customers, authentication data
and free-form private annotations. Certification, lifecycle, stock and test
conditions are not fabricated.

Manufacturer references confirming why these distinctions matter:

- [Yageo MFR manufacturer datasheet](https://yageogroup.com/content/Resource%20Library/Datasheet/YAGEO-MFR_DATASHEET.pdf): leaded resistors have axial forms and physical dimensions, not mandatory SMD footprints.
- [Abracon ACML-0201 manufacturer specification](https://abracon.com/Magnetics/new/ACML-0201.pdf): impedance is specified with frequency/measurement conditions. A series range is not a single orderable part's rating.
- [Murata temperature-characteristic measurement reference](https://ds.murata.com/simsurfing_data/pdf/en-us/mlcc/sim_mlcc_measuringcond_e.pdf): temperature-characteristic codes and measurement conditions must not be silently substituted for missing model-specific specifications.
- [Analog Devices MAX6615](https://www.analog.com/en/products/max6615.html): some legacy thermistor-category imports are actually controllers with thermistor inputs; a fabricated resistance/B value would be incorrect. Classification cleanup is separate from this blank-only projection.

## Applicable controls

Profiles no longer demand MLCC lead pitch/electrolytic lifetime, inductor
saturation current for ferrite beads, oscillator supply/enable data for a passive
crystal, or crystal load capacitance for an oscillator/RTC module. Meaningful
unknown parameters remain visible as unknown; these changes do not hide them
by deleting parts or pretending that unverified certification means certified.

## Runtime and safety

Read source columns in bounded Arrow batches; cache immutable compressed
specification records rather than millions of Python dictionaries. Read the
current index's actual gaps so already populated fields need not be recopied.
Bulk-install into connection-local TEMP tables. No prepared-library, shipped
search-index or member/cost/report database is rewritten.

One read-only completed source per public data revision/category is shared under
a lock. Its cache key contains no account context; the cache has bounded entries
and expires. Repeated filter/sort/page requests reuse that source, not rebuild
hundreds of thousands of rows. Every count, facet, numeric range and result cell
queries the same completed source. Original indexed identities/counts, original
model-search handoff and authorization remain unchanged.
