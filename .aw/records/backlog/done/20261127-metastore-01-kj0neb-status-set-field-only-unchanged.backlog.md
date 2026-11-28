- Id: kj0neb
- Status: done
- Close-Evidence: .aw/records/plans/executed/20261127-metastore-323-ztvubn-fix-post-cutover-status-set-selectors-and-runner-commit-log.ipd.md
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Same-status field-only updates report unchanged and skip event-log append in status_set._prepare_status_change
- Short-Description: Same-status field-only updates report unchanged and skip event-log append in status_set._prepare_status_change
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-28 done (aw set): Fixed and validated by executed Order 323 plan ztvubn.
- 2026-11-27 blocked (aw set): Covered by Order 323 child plan ztvubn (single-valued From-Backlog carries 2zknl8).
- 2026-11-27 created (aw backlog): Same-status field-only updates report unchanged and skip event-log append in status_set._prepare_status_change

In the metadata-store cutover code patch (.aw/system/cutover/metastore-code.cutover.patch), agent_workflows/status_set.py::_prepare_status_change (around lines 2154-2158) computes content_changed by comparing rendered Markdown text against the original Markdown file text. For post-cutover log-format records, same-status field-only updates such as 'aw ipd set to-review <id6> --from-spec <spec>' or '--from-spec -' modify only .aw/records/meta/<id6>.jsonl and leave the two-field YAML mirror unchanged. As a result, content_changed evaluates to False and the command exits 0 reporting 'unchanged' while silently dropping the event-log append. Discovered during IPD psm9ac; blocks 2 tests in tests/test_check_engine_from_spec_missing.py (test_cli_set_from_spec_writes_bullet, test_cli_clear_with_dash).
