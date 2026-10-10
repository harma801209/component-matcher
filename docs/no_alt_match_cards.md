# Source-only search result grouping

When a part-number search finds source information but no alternative results,
`render_no_alt_match_card` places the model header, source table, empty-alternative
status and native report button inside one bordered Streamlit container. The status
and action share a lightly tinted footer. Successful alternative results and other
warning paths keep their existing rendering and matching semantics.

The header is native HTML, so it can wrap independently on narrow screens. The
table retains its column-resizing/copy-audit script and horizontal scrolling inside
an iframe, but no longer paints a separate closed card or blank rounded footer.
Source tables taller than the compact frame scroll internally. Scoped CSS cancels
Streamlit's markdown-container negative bottom margin for these HTML blocks;
otherwise the next table can overlap a header taller than one line.

Report submission remains the original native callback and server-side payload.
Card keys include the input-line instance, so repeated model inputs remain separate
and each action belongs to the corresponding source result. No report records or
runtime schemas are changed by this presentation update.

Validation: the isolated release gate includes a regression checking container
scope, callback identity, payload/model association, duplicate keys and audit-channel
propagation. `tools/preview_no_alt_match_cards.py` is a disposable local fixture with
temporary database paths and capture-only callbacks. `tools/check_no_alt_match_cards.py`
checks grouping, no header overlap/large table gap, source scrolling, callbacks and
1440/900/390px layouts. With `--public`, supply approved credentials through
`COMPONENT_QA_ACCOUNT` and `COMPONENT_QA_PASSWORD`; public checks do not click report
buttons or create test reports in production.
