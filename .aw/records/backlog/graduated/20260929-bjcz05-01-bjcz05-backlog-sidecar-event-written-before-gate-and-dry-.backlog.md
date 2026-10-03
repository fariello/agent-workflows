- Id: bjcz05
- Status: graduated
- Graduated-To: bjcz05
- Blocks-Release: next
- Set: bjcz05
- Priority: medium
- Work-Kind: bug
- Summary: backlog.run_set appends the history sidecar event BEFORE its close-legitimacy gate and BEFORE the dry-run decision, so a refused or previewed transition leaves a phantom event

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: ulepef
- 2026-09-29 created (aw backlog): backlog.run_set appends the history sidecar event BEFORE its close-legitimacy gate and BEFORE the dry-run decision, so a refused or previewed transition leaves a phantom event

Filed while authoring plan 47ttnv (backlog mawwlc), which deferred this row and needs a durable carrier for it.

Approved spec artifact-metadata-storage (2vev8j) Section 7 'Out of scope, and filed separately' already states this defect and says it is 'worth its own item', and no item existed. Quoting that spec: 'Specs append the event BEFORE validating and writing the Markdown, and backlog appends BEFORE its close-legitimacy gate and BEFORE the dry-run/apply decision, so a --dry-run PREVIEW or a REFUSED transition can leave a phantom event. This violates C5 today.'

So there are two halves: backlog.run_set calls record_history.append_advisory before its evaluate_blocking_close refusal and before the dry-run branch, and specs appends before validating/writing. Confirm both against the current tree before fixing; tests/test_backlog.py::test_backlog_set_status_done_dry_run_refuses_illegitimate_blocking_close_without_sidecar already asserts the sidecar does NOT exist after a refused dry-run close, so the exact reachable shape needs re-measuring rather than assuming.

NOTE the asymmetry this interacts with: status_set (the positional aw backlog set spelling) writes NO sidecar entry at all, so the two dispatch paths differ in history recording as well. Plan 47ttnv deliberately does not touch that.
