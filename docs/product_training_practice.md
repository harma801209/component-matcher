# Product training practice tools

The formal `?training=1` lesson contains three independent tools below its existing
3D workspace: model-code explanation, scenario exercises, and a wrong-answer notebook.
These do not invoke search, price lookups, or business-database writes.

## Decoder scope and evidence

- FOJAN FRC / FRL / FRM / FCM: format-level explanations, using the existing
  `component_matcher.py` naming patterns and previously checked series evidence.
  The training tool deliberately does not establish standard-value membership,
  resistance ranges, terminal availability, power combinations, or catalog existence.
  It does not generate replacement order numbers. Missing FCM precision is identified
  as an unknown precision code, not automatically supplied as F.
- YAGEO: the exact `RC0603FR-0710KL` example and documented compact alias only.
  Source: https://www.yageogroup.com/component-documentation/download/specsheet/RC0603FR-0710KL
  Verified on 2026-10-10. Its 0.1 W rating has a 70°C condition; 75 V is not a
  guarantee of acceptable dissipation at all resistance/temperature conditions.
- Murata: `GRM188R71H104KA93` electrical base and its `D` packaging example.
  Source: https://www.murata.com/en-us/products/productdetail?partno=GRM188R71H104KA93%23
  Base identifiers are not categorically called invalid when the packaging code
  is absent. Nominal capacitance is not a working-bias guarantee.
- `1N4148`: a generic designation does not identify its manufacturer. Nexperia's
  datasheet is an explicitly named reading example, not a brand inference.
  Source: https://assets.nexperia.com/documents/data-sheet/1N4148_1N4448.pdf

Uncovered brands/families return "not covered", not a claim that the input is wrong.
One-character differences from curated examples are suggestions to verify, never
automatic substitutions. Only whitespace/case normalization is allowed. Rendering
uses text nodes for inputs, and all source links are static trusted URLs.

## Exercises and state

Eight scenarios (two per component family) plus the original four classroom quizzes
share one notebook. Each question explains its conditions and distinguishes a
classroom initial screen from a real production substitution decision. The original
quiz wording and answers are supplied by `TrainingLesson.quizzes()` rather than
duplicated in the notebook.

Versioned `localStorage` key: `fruition_training_practice_v1`. Only known question IDs,
answer indexes, last-answer correctness and bounded attempt counts are stored. No
member identity, session token, raw model input or business data is stored.
Stored shapes are validated and correctness is recalculated from current questions.
Changing browser accounts does not isolate this anonymous record; the UI explicitly
states that limitation. Clearing requires confirmation. Cross-tab storage changes
are handled. Denied/corrupt storage falls back to memory with a visible warning.

Wrong answers enter the notebook; answering correctly on retry removes them.
The original four course completion indicators reflect the same last-answer state.
Knowledge tabs and practical-tool tabs are scoped independently.

## Verification

`tests/test_product_training.py` covers script syntax, units, missing/invalid input,
unsupported models, question grading, untrusted stored records, and page isolation.
Run `tools/check_training_practice.py` for isolated browser interaction, persistence,
storage-failure, injection and responsive checks; `--public` checks the formal page.
The complete release gate must pass before publication. Existing presentation,
login, backend runtime data, search and BOM checks remain required.
