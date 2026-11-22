- Id: nlnvrn
- Status: open
- Set: nlnvrn
- Work-Kind: bug
- Priority: medium
- Summary: check_engine._identity_declared_values omits record_type when calling artifact_meta.read_text, so check_name_identity misses Id and Set on aw-prompt comment headers
- Short-Description: check_engine._identity_declared_values omits record_type when calling artifact_meta.read_text, so check_name_identity misses Id and Set on aw-prompt comment headers
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): check_engine._identity_declared_values omits record_type when calling artifact_meta.read_text, so check_name_identity misses Id and Set on aw-prompt comment headers

While converting `tests/test_identity_rename_hint.py` (plan `1upea0` E-03) onto `tests/record_builder.py`, `RecordBuilder().prompt(id6='pr0001', ...)` produced a valid HTML-comment prompt header (`<!-- aw-prompt: ... | Id: pr0001 | ... -->`), but `agent_workflows/check_engine.py::_identity_declared_values` calls `artifact_meta.read_text(region)` without passing `record_type`. With the default `record_type='ipd'`, `artifact_meta.read_text` does not parse `<!-- aw-prompt: ... -->` comments and returns `fields={}` (whereas `artifact_meta.read_text(region, record_type='prompt')` returns `id6='pr0001'` and `set_id='pr0001'`). Consequently `check_engine.check_name_identity` emits zero findings for prompt records in canonical `aw-prompt` format, forcing `TestIdentityRenameHint.test_all_other_mapped_types_hints_resolve` to keep a legacy bullet literal (`"- Id: pr0001\n- Status: draft\n"`) until `_identity_declared_values` accepts and forwards `record_type`.
