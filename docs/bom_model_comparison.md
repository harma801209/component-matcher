# Post-match BOM model-column comparison

Every displayed BOM result header has a real checkbox before its title. Check
two columns (normally original MPN and generated 匹配型号), then click 型号比对
in the compact toolbar directly above the table. Selecting alone does not run
comparison. There is no separate selector/dropdown panel. Selected-column chips
remain visible while horizontally scrolling and allow either choice to be
removed. Distinct Original/System labels and positional IDs disambiguate
duplicate headers. Any two displayed columns can be checked; only displayed,
already-authorized columns are accepted by the server.

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

After clicking, the page shows full-sheet consistent/different/missing counts,
a warning for issues, and an issues-only grid by default. Its own 100-row paging
does not reduce summary coverage. Existing model parsers explain independently
known package, tolerance, resistance, capacitance, power, voltage and series
differences. Unknown codes and parser errors require human review, without
failing or altering the main BOM result. Parameter omissions do not become
invented differences; equal decoded basics never imply suffix interchangeability.

The component receives only the existing escaped, permission-filtered page
table and positional header choices, never raw hidden data or credentials.
The comparison frame uses the same cost-permission gate and preserves raw
original cells even if their headers overlap display-normalizer field names.
A content revision rejects stale button events after data changes. Draft
checkbox changes remain browser-local; only clicking the button sends the
selected positions. A previous report labels the compared pair explicitly.
Pricing permissions and existing export contents are unchanged; no matching
or output-version bump is needed. The component has no external dependencies,
network calls, persistent browser storage or application-data writes.
