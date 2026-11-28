- Id: 197ak8
- Status: done
- Close-Evidence: .aw/records/plans/executed/20261127-metastore-324-639g02-fix-post-cutover-check-engine-log-readers-and-dependency-hoo.ipd.md
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Dependency pre-commit hook fails open when staged meta log fails replay with corrupt item_dependencies
- Short-Description: Dependency pre-commit hook fails open when staged meta log fails replay with corrupt item_dependencies
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-28 done (aw set): Fixed and validated by executed Order 324 plan 639g02.
- 2026-11-27 blocked (aw set): Covered by Order 324 child plan 639g02 (single-valued From-Backlog carries 0wilvu).
- 2026-11-27 created (aw backlog): Dependency pre-commit hook fails open when staged meta log fails replay with corrupt item_dependencies

In the metadata-store cutover code patch (.aw/system/cutover/metastore-code.cutover.patch), agent_workflows/hooks/ipd_dependency_statement_gate.py::_staged_ipd_overlay (around lines 121-162) executes 'if res.kind != "ok" or res.state is None: continue' when artifact_meta.read_at returns ReadAtResult(kind='corrupt') on a staged meta/<id6>.jsonl whose item_dependencies value is malformed (for example, duplicate edges). Dropping the corrupt entry leaves overlay_states empty, so the pre-commit gate returns exit code 0 instead of refusing with check.ipd-dependency-malformed. Discovered during IPD psm9ac; blocks HookRefusalTests.test_refuses_staged_malformed in tests/test_ipd_dependency_statement_gate.py.
