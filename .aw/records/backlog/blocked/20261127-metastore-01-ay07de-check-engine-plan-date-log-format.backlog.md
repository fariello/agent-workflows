- Id: ay07de
- Status: blocked
- Gate-Kind: artifact
- Gate-Ref: 639g02
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Plan date checks in check_engine._plan_date_compact and check_ipd_lint_reach read absent legacy date field on log-format plans
- Short-Description: Plan date checks in check_engine._plan_date_compact and check_ipd_lint_reach read absent legacy date field on log-format plans
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 blocked (aw set): Covered by Order 324 child plan 639g02 (single-valued From-Backlog carries 0wilvu).
- 2026-11-27 created (aw backlog): Plan date checks in check_engine._plan_date_compact and check_ipd_lint_reach read absent legacy date field on log-format plans

In the metadata-store cutover code patch (.aw/system/cutover/metastore-code.cutover.patch), two plan-date readers in agent_workflows/check_engine.py read fields.get('date') via artifact_meta.read_text or cached fields, which is always None on post-cutover log-format plans (log-format plans store filename_date/created_day in meta/<id6>.jsonl rather than a legacy '- Date:' bullet): (1) _plan_date_compact (around lines 11554-11595) returns None, causing carrier_severity_for_plan to downgrade every log-format plan's check.ipd-uncarried-obligation findings from error to info; (2) check_ipd_lint_reach (around lines 12638 and 12654-12658) gets raw_date=None and skips every terminal-directory plan, missing IPD-M105 and diverging from ipd_lint.lint_file. Discovered during IPD psm9ac; blocks CarrierDischargedRemedyTests, DynamicCutoverCheckEngineTests, and CheckIpdLintReachTerminalTreeTests in tests/test_check_engine.py.
