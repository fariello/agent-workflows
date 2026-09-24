- Id: q6bbdb
- Status: open
- Blocks-Release: next
- Set: q6bbdb
- Priority: medium
- Work-Kind: bug
- Summary: 14 slow-marked test failures remain unrelated to the runner-stop path and need triage (installer cleanup, CLI conformance, role guard, release readiness, turn bounds)

## Workflow history
- 2026-09-23 created (aw backlog): 14 slow-marked test failures remain unrelated to the runner-stop path and need triage (installer cleanup, CLI conformance, role guard, release readiness, turn bounds)

## What

After plan `13xo5k` fixed the 19 runner-stop failures, `python3 -m pytest -m slow` still reports
14 failures at HEAD `67d1f8c0` + `13xo5k`. They are PRE-EXISTING (present in the measured baseline with
`13xo5k`'s changes stashed) and unrelated to the deliberate-stop path, so `13xo5k` deliberately did not
touch them. Filed so they are tracked rather than absorbed into a plan's report.

The failing node ids:

```
tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw
tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed
tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
tests/test_release_readiness.py::FullReportTests::test_build_report_go_on_clean_tree
tests/test_release_readiness.py::IpdLintGateTests::test_ipd_lint_all_phases_run_and_pass
tests/test_role_declaration_guard.py::ProtectedTestsDoNotDependOnTheAmbientRole::test_protected_files_pass_with_the_worker_marking_reasserted
tests/test_role_declaration_guard.py::ProtectedTestsDoNotDependOnTheAmbientRole::test_the_outcome_is_the_same_under_both_ambient_roles
tests/test_runner_stop_levels12.py::AgyDriverParityTests::test_agy_level_1_completes_only_the_in_flight_item
tests/test_runner_stop_levels12.py::AgyDriverParityTests::test_agy_level_2_finishes_the_current_set_only
tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_item_level_bookkeeping_path_is_still_wired
tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted
```

Also failing in the FAST (default) suite and equally pre-existing:

```
tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
```

## Note on two of them

`test_release_readiness.py::IpdLintGateTests::test_ipd_lint_all_phases_run_and_pass` and
`FullReportTests::test_build_report_go_on_clean_tree` are RELEASE GATES. If they are failing for a real
reason, that bears directly on release readiness and should be triaged first.

The two `runner_stop_triggers` and two `runner_stop_levels12` entries are stop-adjacent but were NOT
fixed by `13xo5k` and were failing before it; they are levels 1-2 and trigger wiring, not the
deliberate-stop handler bodies.

## Why this is filed separately

Per the repository rule that a live bug gates the next release, and to keep `13xo5k`'s scope honest:
that plan fixed what it measured and this item carries what it did not.
