- Id: 5uqo2g
- Status: open
- Blocks-Release: next
- Set: 5uqo2g
- Priority: medium
- Work-Kind: bug
- Summary: Generic test git identity tokens like Test collide with artifact_meta._writer_ruleset when leak_sanitizer._GENERIC_DERIVED_TOKENS omits them

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-17 same-status (aw set): status -> open
- 2026-11-17 created (aw backlog): Generic test git identity tokens like Test collide with artifact_meta._writer_ruleset when leak_sanitizer._GENERIC_DERIVED_TOKENS omits them

tests/support.py::init_repo sets git config --local user.name Test. agent_workflows/leak_sanitizer.py::derive_warn_tokens derives derived:Test because _GENERIC_DERIVED_TOKENS omits test/tester/test user, causing artifact_meta.validate_new_events (via _writer_ruleset) to refuse titles/messages containing Test (observed in tests/test_generators_writing_standard_pointer.py::test_specs_new_writing_standard_pointer). IPD b3l7y6 filtered synthetic test git identities in artifact_meta._writer_ruleset to stay in scope; consider hoisting generic test tokens into leak_sanitizer._GENERIC_DERIVED_TOKENS or adjusting init_repo.
