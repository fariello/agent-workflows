- Id: eqjdre
- Status: open
- Set: eqjdre
- Work-Kind: bug
- Priority: high
- Summary: After the metastore cutover, aw research mv and set-assign move a log-format research record with git mv but append no rename event, so the replayed path goes stale and no path history survives (AC-34)
- Short-Description: After the metastore cutover, aw research mv and set-assign move a log-format research record with git mv but append no rename event, so the replayed path goes stale and no path history survives (AC-34)
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-25 created (aw backlog): After the metastore cutover, aw research mv and set-assign move a log-format research record with git mv but append no rename event, so the replayed path goes stale and no path history survives (AC-34)

Found while executing plan g45vyv (cutover code patch, rename-ledger retirement).

What happens: `research_refs._apply_renames` (used by `aw research set-assign` and `aw research mv`) moves the file with `_git_mv` and then appends only a `set` event for changed set/order/model/kind fields. It never appends an `{op: rename, verb, path}` event, unlike `artifact_rename._apply_log_rename` (`aw rename`, `aw group`) and `plans_refs` (`aw archive plans`).

Why it matters after the cutover: before g45vyv the rename ledger (`record_history.record_rename`, `.aw/records/history.jsonl`) at least recorded the move. g45vyv retires the ledger (spec 4sd62s 5.2 step 2, AC-31), so on the switched tree the move leaves no path-history record, and the log's replayed path still names the old file.

Measured on a scratch worktree holding HEAD 4fe284f8d plus both cutover patches (after g45vyv): a log-format research record `rs34ef` created at `research/20261109-demo-01-rs34ef-sample.findings.md`, then `aw research mv rs34ef --slug moved --apply`: exit 0, events appended: none, file on disk `research/20261109-demo-01-rs34ef-moved.findings.md`, `artifact_meta.read("rs34ef").path` still `research/20261109-demo-01-rs34ef-sample.findings.md`.

Fix direction: give `research_refs._apply_renames` the same path-bearing `rename` event the other rename verbs write (append the event and let `artifact_meta` move the file, as `_apply_log_rename` does), inside `metastore-code.cutover.patch`, with a behavioral test for `mv` and `set-assign`.
