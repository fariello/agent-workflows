- Id: 5slmvq
- Status: done
- Graduated-To: 5slmvq
- Set: 5slmvq
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for _run_migrate_layout

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD 1ue3kr executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261016-5slmvq-01-1ue3kr-restore-behavioral-test-coverage-for-run-migrate-layout.ipd.md); evidence .aw/records/plans/executed/20261016-5slmvq-01-1ue3kr-restore-behavioral-test-coverage-for-run-migrate-layout.ipd.md
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T145446Z-2140972: 1ue3kr
- 2026-10-15 created (aw backlog): Restore behavioral test coverage for _run_migrate_layout

Uncited trim-deleted test audit (findings doc hpjj44) identified unguarded property PROP-01 in agent_workflows/cli.py::_run_migrate_layout (277 exclusive lines).
Operator: return-none
Survivor verdict: survived (0 failing)
Control verdict: killed by 11 tests in tests.test_layout_migration.MigrateLayoutWizardTests
Deleted tests reaching:
- tests/test_awmigrename.py (79 exclusive lines, 9 removed funcs)
- tests/test_layout_migration.py (198 exclusive lines, 49 removed funcs)
Candidate tests: test_agents_readme_disposition_per_leftover_mode, test_apply_facet_transform, test_apply_moves_not_copies, test_cleanup_preserves_recreated_dir_content, test_cleanup_removes_manifest_only_file.
