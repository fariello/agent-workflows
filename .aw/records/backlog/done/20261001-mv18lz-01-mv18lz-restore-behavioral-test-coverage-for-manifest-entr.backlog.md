- Id: mv18lz
- Status: done
- Graduated-To: mv18lz
- Set: mv18lz
- Priority: medium
- Work-Kind: chore
- Summary: Restore behavioral test coverage for manifest_entry_is_selectable preserving executed entries

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD df486j executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-mv18lz-01-df486j-restore-behavioral-test-coverage-for-manifest-entry-is-selec.ipd.md); evidence .aw/records/plans/executed/20261012-mv18lz-01-df486j-restore-behavioral-test-coverage-for-manifest-entry-is-selec.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005650Z-2322198: df486j
- 2026-10-01 created (aw backlog): Restore behavioral test coverage for manifest_entry_is_selectable preserving executed entries

Commit 19313eed deleted tests/test_runner_item_dependencies.py. Its InRunExecutedDependencyTests suite pinned that manifest_entry_is_selectable preserves executed plans as selectable queue entries. An in-memory mutation probe breaking this behavior left the test suite fully green, confirming this production property has zero surviving test coverage. Behavioral coverage should be restored driving the queue selection logic.
