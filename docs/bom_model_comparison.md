# Post-match BOM model-column comparison

The expanded comparison panel sits above the BOM result table. Select one
original column and one generated matching-model slot. Distinct Original/System
labels and positional keys prevent duplicate original headers or a source
column named 匹配型号 from being confused with the generated output.

Comparison is read-only and runs across the full active worksheet, independent
of main-table status/search filters and display pagination. It never rematches,
reprices, edits a source file, changes output slots or persists comparison
results in member/cost/BOM-job storage. UI selections are scoped to the uploaded
file signature and worksheet, and are excluded from matching-run signatures.
Multi-brand output slots can be selected individually.

Only case and whitespace are ignored. Hyphens, punctuation, ordering, suffixes
and ambiguous OCR characters remain significant; no fuzzy matching or code
repair is performed. Actual nulls and explicit missing-value placeholders
are reported as missing, never as consistent even when both sides are empty.
Different text is not proof of electrical incompatibility, and equal text is
not independent specification validation.

The page shows full-sheet consistent/different/missing counts, an automatic
warning for issues, and an issues-only grid by default. Its own 100-row paging
does not reduce summary coverage. Existing model parsers explain independently
known package, tolerance, resistance, capacitance, power, voltage and series
differences. Unknown codes and parser errors require human review, without
failing or altering the main BOM result. Parameter omissions do not become
invented differences; equal decoded basics never imply suffix interchangeability.

Pricing permissions and existing export contents are unchanged. New comparison
controls contain no costs or credentials. No matching/output version bump is
needed because the matching and export decisions themselves are unchanged.
