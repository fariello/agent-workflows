- Id: 1fmcdk
- Status: open
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: evaluate_ipd_dependencies bypasses meta state map when plans argument is given, silencing ipd lint dependency checks
- Short-Description: evaluate_ipd_dependencies bypasses meta state map when plans argument is given, silencing ipd lint dependency checks
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 created (aw backlog): evaluate_ipd_dependencies bypasses meta state map when plans argument is given, silencing ipd lint dependency checks

In the metadata-store cutover code patch (.aw/system/cutover/metastore-code.cutover.patch), agent_workflows/check_engine.py::_evaluate_ipd_dependencies_impl (around lines 8941-8955) branches on 'elif ps in overlay or plans is not None:' and calls artifact_meta.read_text(text, record_type='ipd') instead of consulting state_map or dep_value. Because ipd_lint.lint_file always passes plans=[(path, text)], every log-format plan's item_dependencies field (stored in meta/<id6>.jsonl, not in the two-field YAML mirror) reads as None, silently skipping check.ipd-dependency-dangling, check.ipd-dependency-ambiguous, check.ipd-dependency-cycle, and check.ipd-dependency-malformed during 'aw ipd lint'. Discovered during IPD psm9ac; blocks test_ipd_lint_resolves_companion_sibling_dependency in tests/test_companion_record_owner_root.py.
