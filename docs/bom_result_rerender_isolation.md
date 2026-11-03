# BOM result rerender and completed-task recovery

Start buttons queue a one-shot session-local intent, bound to the upload and
output mode. A leftover button return value is not a new start. Another explicit
click still queues a new intent; failed-row retry and interrupted-task resume
retain their existing paths.

Completed persisted jobs previously became resumable checkpoints too. This
reentered the workbook matching/progress pipeline, including model prefetch and
price lookups, even when every completed row was already stored. A complete job
is now restored directly from its existing rows, without a matcher or repricing.
Recovery requires the same authenticated owner, exact run signature (including
file, mapping, rules, customer/date/price-access scope), complete sheet set, all
row positions/source row numbers, and complete processed-row counts. Export is
rebuilt from those unchanged stored rows only. Invalid or scope-changed complete
jobs wait for an explicit start instead of automatically rematching.

The comparison component owns a nested result fragment. Its readiness and
comparison/filter/page events no longer rerun the parent's upload, start,
matching or export pipeline. Before emitting any captured rows on fragment
reruns, the server rechecks identity and current cost/customer/price scope. An
expired login or changed scope hides the captured result; there is no cached
authorization or client-side price permission.

Synthetic 138-row browser evidence distinguishes page-run and engine-run counts.
Original comparison advanced the parent page from2 to3 while engine count stayed1.
After isolation, scrolling and comparison/filter interactions leave the parent
at2 and engine at1. This alone does not establish that scrolling triggered an
actual match in the user's original workbook; the completed-job recovery bug is
independently reproduced with the actual persisted-upload restoration function.

No matching selection, quotes, member schema, runtime stores or original upload
is edited. The separately pending administrator-security changes are not part
of this release. Temporary test data does not authenticate a production account.
