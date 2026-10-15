- Id: 5slmvq
- Status: open
- Set: 5slmvq
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for _run_migrate_layout

## Workflow history
- 2026-10-15 created (aw backlog): Restore behavioral test coverage for _run_migrate_layout

Uncited trim-deleted test audit (findings doc hpjj44) identified unguarded property PROP-01 in agent_workflows/cli.py::_run_migrate_layout (277 exclusive lines).
Operator: return-none
Survivor verdict: survived (0 failing)
Control verdict: killed by 11 tests in tests.test_layout_migration.MigrateLayoutWizardTests
Deleted tests reaching:
- tests/test_awmigrename.py (79 exclusive lines, 9 removed funcs)
- tests/test_layout_migration.py (198 exclusive lines, 49 removed funcs)
Candidate tests: test_agents_readme_disposition_per_leftover_mode, test_apply_facet_transform, test_apply_moves_not_copies, test_cleanup_preserves_recreated_dir_content, test_cleanup_removes_manifest_only_file.
