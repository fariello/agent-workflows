- Id: mv18lz
- Status: open
- Set: mv18lz
- Priority: medium
- Work-Kind: chore
- Summary: Restore behavioral test coverage for manifest_entry_is_selectable preserving executed entries

## Workflow history
- 2026-10-01 created (aw backlog): Restore behavioral test coverage for manifest_entry_is_selectable preserving executed entries

Commit 19313eed deleted tests/test_runner_item_dependencies.py. Its InRunExecutedDependencyTests suite pinned that manifest_entry_is_selectable preserves executed plans as selectable queue entries. An in-memory mutation probe breaking this behavior left the test suite fully green, confirming this production property has zero surviving test coverage. Behavioral coverage should be restored driving the queue selection logic.
