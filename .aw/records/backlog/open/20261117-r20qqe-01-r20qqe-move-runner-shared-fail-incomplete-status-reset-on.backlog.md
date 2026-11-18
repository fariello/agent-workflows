- Id: r20qqe
- Status: open
- Set: r20qqe
- Work-Kind: bug
- Priority: high
- Summary: Move runner_shared._fail_incomplete status reset onto artifact_meta
- Short-Description: Move runner_shared._fail_incomplete status reset onto artifact_meta
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-18 created (aw backlog): Move runner_shared._fail_incomplete status reset onto artifact_meta

In agent_workflows/runner_shared.py inside run_review_sequence._fail_incomplete, an incomplete review sequence restores the plan status to to-review by calling re.sub(r"(?m)^- Status:.*$", "- Status: to-review", cur) and plan_file.write_text(...) directly, bypassing artifact_meta (xexn45 / 7yr827 missed this inner helper). Move this write onto artifact_meta (restore_legacy_snapshot or render_legacy_text / append) with a regression test before the metastore cutover (cxxmyv).
