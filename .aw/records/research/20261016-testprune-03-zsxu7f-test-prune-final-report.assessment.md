---
id: zsxu7f
created: 20261017
set: testprune
order: 03
topic: [testing]
model: 
kind: assessment
status: active
outcome: informational
summary: Test prune final report: 8622 tests in 681s median wall time with coverage parity and zero surviving mutations
consumed-by: []
---

# Test Prune Final Report (Set testprune)

## Suite Metrics (Before and After)

Comprehensive measurement comparison between baseline at Set start and the final retained test suite:

| Metric | Before (Set Start) | After (Retained Suite) | Delta | Notes |
|---|---|---|---|---|
| **Collected Tests** | 9,801 (qqrgv3) / 9,101 (Set-start on current code) | 8,622 | -1,179 (-12.0%) / -479 (-5.3%) | Historical baseline at 6ea45c974: 8,794 |
| **Test Modules** | 576 (qqrgv3 baseline) | 589 | +13 modules (+2.3%) | Added tools, templates, matrix tests |
| **Full Suite Wall Time (3 warm runs)** | 565.28s historical / 1,936s per-test cov | 699.87s, 663.17s, 681.42s (Median: 681.42s) | Median: 681.42s | Achieved median reported per OQ-02 and c8bfp9 |
| **Bare `pytest` (Core Suite)** | 28.5s baseline | 753 passed in 25.57s | Under 30s budget | Core budget guard passing |
| **Leaf Command Coverage** | 170 leaves | 170/170 leaves driven (100.0%) | 0 regressions | 753 passed in 25.94s under leaf probe |
| **Core Module Coverage Regressions** | 0 | 0 of 197 modules regressed | 0 regressions | Verified by `core_measure` tool |
| **Covered Statements** | 125,344 (82.06%) | 126,503 (82.81%) | +1,159 (+0.75%) | Exact comparison on current code |
| **Covered Branches** | 163,618 (73.65%) | 165,325 (74.58%) | +1,707 (+0.93%) | Higher union coverage retained |

### Top 20 Slowest Test Durations (`--durations=20`)
Captured from warm full suite execution on 6 xdist workers (`--dist=worksteal`):

| Duration | Stage | Node ID |
|---|---|---|
| 32.63s | call | `tests/test_placement_switch_companion_execute.py::TestPlacementSwitchCompanionExecute::test_case_2_resume_all_fault_points_pair_c` |
| 32.22s | call | `tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference` |
| 30.23s | call | `tests/test_placement_switch_execute.py::TestPlacementSwitchExecute::test_03_fault_points_resume_to_same_end_state` |
| 24.65s | call | `tests/test_records_root_switch_execute.py::TestRecordsRootSwitchExecute::test_04_fault_points_resume_to_completed_state` |
| 23.31s | call | `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_exhaustive_sweep` |
| 23.25s | call | `tests/test_placement_switch_companion_execute.py::TestPlacementSwitchCompanionExecute::test_case_2_resume_all_fault_points_pair_a` |
| 19.75s | call | `tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun` |
| 17.42s | call | `tests/test_placement_switch_companion_execute.py::TestPlacementSwitchCompanionExecute::test_case_3_rollback_pre_sources_removed_pair_a` |
| 16.98s | call | `tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_e05_spec_5_5_checker_rejects_stale_owner` |
| 15.89s | call | `tests/test_fields_flag_reach.py::FieldsFlagReachTests::test_fields_flag_end_to_end_projection` |
| 14.72s | call | `tests/test_placement_switch_execute.py::TestPlacementSwitchExecute::test_04_pre_sources_removed_fault_points_rollback_byte_identical` |
| 14.13s | call | `tests/test_gradcover_end_to_end.py::TestGradcoverEndToEnd::test_e01_e06_e07_success_path_graduate_review_orchestrate` |
| 14.01s | call | `tests/test_fix_it_global_caps.py::TestEndToEndGlobalCaps::test_case_b_per_set_cap_stops_second_item` |
| 13.32s | call | `tests/test_shared_flag_honored.py::test_partition_fields_branch_behavior` |
| 12.92s | call | `tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_6_recovery_resume_and_rollback` |
| 12.75s | call | `tests/test_freeze_time_refusal.py::TestPreservedBehaviorCases::test_5_3a_in_run_failure_cascades_fail_depend_and_independent_item_completes` |
| 12.67s | call | `tests/test_installer.py::UntrackedGitignoreInstallTests::test_the_users_gitignore_is_managed_without_being_clobbered` |
| 12.22s | call | `tests/test_fix_it_global_caps.py::TestEndToEndGlobalCaps::test_case_c_per_run_cap_stops_second_item` |
| 12.01s | call | `tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e02_agy_restart_enabled` |
| 11.97s | call | `tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e02_oc_restart_enabled` |

### Target Wall Time Outcome and Analysis
Per IPD `c8bfp9` OQ-02 and `vgus66` E-08, the headline target of < 120s wall clock on 6 workers was measured and evaluated. The achieved median full-suite wall time across 3 warm runs is 681.42s (Run 1: 699.87s, Run 2: 663.17s, Run 3: 681.42s). The raw sum of call durations across the 8,622 tests is ~4,000s, establishing a theoretical lower bound of ~666s on 6 workers even under zero setup overhead and ideal balance. Because the project policy strictly forbids deleting behavioral tests or weakening assertions to gain speed ("Never delete a test to make a measurement pass"), the retained test corpus cannot reach 120s without test deletion. Every test exceeding 2.0s duration has been censused, justified with compelling operational reasons, and allowlisted in `tests/slow_allowlist.txt`.

## Per-Category Classification Counts

The 5 children of Set `testprune` executed distinct responsibilities across the suite:

1. **`qqrgv3` (Tooling and Baseline)**:
   - Authored per-test coverage tooling (`covctx_plugin.py`, `percov_run.py`, `percov_analyze.py`, `classify.py`).
   - Ran initial full baseline (9,801 collected tests across 576 modules).
   - Scaffolding of the central decision table in research record `hwuvpx`.
2. **`tv72xy` (Structure Pin Deletions)**:
   - Deleted 85 tests across 26 modules that pinned internal code structure rather than observable outcomes.
   - Breakdown: 48 architecture-freeze pins, 19 name-shape/ast inspection tests, 18 internal helper existence/constant length checks.
3. **`83nnyn` (Consolidation into Table-Driven Tests)**:
   - Consolidated 20 test files, collapsing 966 repetitive tests into compact, parameterized accumulate tables.
   - Achieved 100% statement and branch coverage preservation across all consolidated files.
4. **`c8bfp9` (Performance Optimization and Slow-Test Census)**:
   - Converted 109 test files to in-process execution (`run_cli_inproc`) and cached filesystem fixtures.
   - Zero deletions.
   - Identified, censused, and justified 610 slow tests (>2.0s) in research `hwuvpx`.
5. **`vgus66` (Verification and Parity Proof)**:
   - Derived union coverage parity: Retained suite has +1,159 statements and +1,707 branches covered compared to Set-start tests on identical code.
   - Core regression verification: Leaf probe confirmed 170/170 leaves driven (100.0%) in 25.94s, bare pytest passes in 25.57s (<30s budget), and 0 core modules regressed.
   - Mutation spot-check: 20 sampled mutations across `83nnyn` and `c8bfp9` tested; all 20 failed the original test, were caught by the retained suite, and reverted cleanly (0 surviving mutations).
   - Randomized flake check: 3 full runs with distinct seeds passed with 0 failures and 0 flakes.

## Deleted Tests and Rationale

A total of 85 tests were deleted by child plan `tv72xy`. Every deleted node id, source file, deletion category, and specific rationale is recorded in full detail in the "Recorded deletions" section of research record `hwuvpx` (`.aw/records/research/20261016-testprune-02-hwuvpx-test-prune-decision-table.assessment.md`).

Summary of deletion rationales:
- **Architecture Freeze Pins**: Tests asserting that specific module boundaries, internal wrapper functions, or non-public APIs remained unchanged.
- **AST / Source Code Inspection**: Tests using `ast` or `inspect` to check function docstrings, comment banners, or symbol census rather than executing behavior.
- **Internal Constant Length Checks**: Tests asserting the length of internal tuples or lists (e.g. `len(VERIFY_ABSENCE_CODES) == 4`) rather than testing the code paths that handle those codes.
- **Private Name / Host Identity Pins**: Tests asserting that internal functions were imported or re-exported under specific private names, superseded by end-to-end behavioral CLI tests.

## Mutation Spot-Check Results

Per IPD `vgus66` E-04 and E-05, a stratified random sample of 20 applicable tests (8 from `83nnyn`, 12 from `c8bfp9`) plus 2 defect-citing structure-pin tests was drawn and evaluated with single-line mutations that reintroduce the targeted bug.

### 20 Sampled Applicable Mutations

| ID | Child | Node ID | Targeted Production Symbol | Mutation Description | Original Test Fails | Retained Test Catches | Revert Verified |
|---|---|---|---|---|---|---|---|
| mut-01 | 83nnyn | `tests/test_descriptive_refusal_hoist.py::test_all_five_routes_match_frozen_table_for_nonempty_verbs` | `attention_contract.refuse_unsafe_descriptive` | Invert newline check in descriptive refusal | Yes (FAILED) | Yes (`test_refuse_unsafe_descriptive_accumulate_table`) | Yes (clean) |
| mut-02 | 83nnyn | `tests/test_group_verb_policy.py::test_group_setid_refusal` | `config.check_setid_length_policy` | Bypass max_length check on setid | Yes (FAILED) | Yes (`test_group_setid_refusal`) | Yes (clean) |
| mut-03 | 83nnyn | `tests/test_oc_runipd.py::HeartbeatFormattingTests::test_heartbeat_idle_formatting_over_60s` | `render_stream.format_compact_duration` | Mutate minute format string `m` -> `min` | Yes (FAILED) | Yes (`HeartbeatFormattingTests::test_heartbeat_idle_formatting`) | Yes (clean) |
| mut-04 | 83nnyn | `tests/test_runs_repo_alias.py::test_dir_control_parses_to_dir_attr` | `cli._build_parser.runs_sub` | Alter destination argument from `dir` to `dir_other` | Yes (FAILED) | Yes (`test_dir_control_parses_to_dir_attr`) | Yes (clean) |
| mut-05 | 83nnyn | `tests/test_statusline_ascii_mode.py::TestStatuslineAsciiModePurity::test_format_statusline_lines_ascii_purity_swept_states` | `render_stream.format_statusline_lines` | Emit Unicode corner in ASCII mode border | Yes (FAILED) | Yes (`test_format_statusline_lines_ascii_purity_swept_states`) | Yes (clean) |
| mut-06 | 83nnyn | `tests/test_statusline_stop_tally.py::TestStatuslineStopTallyRendering::test_statusline_rectangular_with_badges` | `render_stream.format_statusline_lines` | Off-by-one in bottom border padding | Yes (FAILED) | Yes (`test_statusline_rectangular_with_badges`) | Yes (clean) |
| mut-07 | 83nnyn | `tests/test_usage_refusal_agent_record.py::test_required_arg_leaf_agent_mode` | `renderers.emit_usage_refusal` | Mutate status from `cannot-run` to `failed` | Yes (FAILED) | Yes (`test_required_arg_leaf_modes`) | Yes (clean) |
| mut-08 | 83nnyn | `tests/test_usage_refusal_agent_record.py::test_required_arg_leaf_json_mode` | `renderers.emit_usage_refusal` | Mutate exit_code from 2 to 3 | Yes (FAILED) | Yes (`test_required_arg_leaf_modes`) | Yes (clean) |
| mut-09 | c8bfp9 | `tests/test_agent_checked_count.py::HumanCheckedCountTests::test_research_check_refs_reports_files_on_dangling_tree` | `research_refs.run_check_refs` | Mutate message prefix from `across` to `in` | Yes (FAILED) | Yes (`test_research_check_refs_reports_files_on_dangling_tree`) | Yes (clean) |
| mut-10 | c8bfp9 | `tests/test_attention_degraded_item.py::AttentionDegradedItemTests::test_board_renders_degraded_item_under_blocked` | `attention.render_board` | Mutate markdown header marker `#` vs `##` | Yes (FAILED) | Yes (`test_board_renders_degraded_item_under_blocked`) | Yes (clean) |
| mut-11 | c8bfp9 | `tests/test_attention_degraded_item.py::AttentionDegradedItemTests::test_paths_flag_prints_degraded_path` | `attention.run_attention_command` | Omit writing path on `--paths` flag | Yes (FAILED) | Yes (`test_paths_flag_prints_degraded_path`) | Yes (clean) |
| mut-12 | c8bfp9 | `tests/test_attention_degraded_item.py::AttentionDegradedItemTests::test_safety_property_no_false_release_blocker` | `attention.scan` | Assign false `blocks_release` on degraded item | Yes (FAILED) | Yes (`test_safety_property_no_false_release_blocker`) | Yes (clean) |
| mut-13 | c8bfp9 | `tests/test_check_severity_tally.py::CheckSeverityTallyTests::test_exit_code_independence` | `artifact_core.drift_exit_code` | Force exit 0 when error drift is present | Yes (FAILED) | Yes (`test_exit_code_independence`) | Yes (clean) |
| mut-14 | c8bfp9 | `tests/test_explicit_dir_non_project.py::ExplicitDirNonProjectMatrixTests::test_attention_explicit_dir_nonexistent_and_file_and_state_only` | `project_context.diagnose_project_search_failure` | Alter error string for missing project | Yes (FAILED) | Yes (`test_attention_explicit_dir_nonexistent_and_file_and_state_only`) | Yes (clean) |
| mut-15 | c8bfp9 | `tests/test_handoff_ready_gate.py::TestBacklogSetterSubprocess::test_both_spellings_refuse_identically_on_not_ready_and_write_nothing` | `check_engine.evaluate_handoff_ready` | Mutate finding code `no-handoff` to `missing-handoff` | Yes (FAILED) | Yes (`test_both_spellings_refuse_identically_on_not_ready_and_write_nothing`) | Yes (clean) |
| mut-16 | c8bfp9 | `tests/test_handoff_ready_gate.py::TestPredicateUnit::test_ready_case_1_ready_set_with_passing_orchestrator` | `check_engine.evaluate_handoff_ready` | Force `ready=False` for conforming orchestrator | Yes (FAILED) | Yes (`test_ready_case_1_ready_set_with_passing_orchestrator`) | Yes (clean) |
| mut-17 | c8bfp9 | `tests/test_handoff_ready_gate.py::TestProductionAndIsolation::test_isolated_lane_graduates_against_lane_plans_with_separate_gate_dir` | `status_set.run_set_command` | Pass `gate_root` instead of `repo_root` | Yes (FAILED) | Yes (`test_isolated_lane_graduates_against_lane_plans_with_separate_gate_dir`) | Yes (clean) |
| mut-18 | c8bfp9 | `tests/test_spec_setter_refuses_when_handoff_is_not_ready` | `status_set.run_set_command` | Bypass `not handoff_res.ready` check | Yes (FAILED) | Yes (`test_spec_setter_refuses_when_handoff_is_not_ready`) | Yes (clean) |
| mut-19 | c8bfp9 | `tests/test_spec_setter_succeeds_when_handoff_is_ready` | `status_set.run_set_command` | Force refusal even when handoff is ready | Yes (FAILED) | Yes (`test_spec_setter_succeeds_when_handoff_is_ready`) | Yes (clean) |
| mut-20 | c8bfp9 | `tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_unsupported_type_specs` | `cli._run_noun_verb` | Change status `cannot-run` to `failed` | Yes (FAILED) | Yes (`test_unsupported_type_specs`) | Yes (clean) |

### Defect-Citing Structure Pins (tv72xy, Excluded as Not-Applicable)
- `tests/test_orchestrator_retirement.py::OrchestratorRetirementRowAuditAndHonestRecord::` (citing `kjqqzf`): Structure-pin deletion asserting internal table structure of retirement audit. Excluded as not-applicable per E-04/E-05 (refactor/structure pin, no production behavioral change).
- `tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::` (citing `1fzist`): Structure-pin deletion asserting constant length `len(VERIFY_ABSENCE_CODES) == 4`. Excluded as not-applicable per E-04/E-05 (internal constant census).

**Summary**: 20/20 applicable mutations made the original test fail, were caught by the retained suite, and were reverted cleanly. Zero mutations survived (E-06 required 0 restorations).

## Tests Kept Despite Matching Delete Criterion

Tests with zero unique statements and zero unique branches in the per-test coverage matrix that were retained with compelling operational reasons:
1. **Behavioral Contract Guards**: Tests asserting specific CLI error messages, exit codes, or user-facing diagnostics (e.g. `tests/test_usage_refusal_agent_record.py` leaf-command refusal checks). While the underlying CLI dispatch lines are exercised by other integration tests, these tests guard user contract stability.
2. **Subprocess and Conformance Matrix Tests**: Conformance tests in `tests/test_live_conformance_sweep.py` and `tests/conformance_matrix.py` asserting format compliance across machine output modes (`--json`, `--agent`, `--fields`).
3. **Cross-Process & Concurrency Contention**: Tests in `tests/test_suite_slot_lock.py` and `tests/test_concurrent_driver_guard.py` verifying multi-process coordination, watchdog timeouts, and file locks where code paths overlap but timing behaviors are distinct.
4. **Parameter Boundary Invariants**: Tests in `tests/test_statusline_stop_tally.py` and `tests/test_statusline_ascii_mode.py` sweeping all badge combinations to verify box-drawing rectangularity and pure ASCII encoding across all states.

## Flakes and Dispositions

Three full test runs of all 8,622 tests with `pytest-randomly` enabled using distinct seeds:
- **Run 1** (`--randomly-seed=101161`): 8,611 passed, 5 skipped, 2 xfailed, 4 xpassed in 699.87s
- **Run 2** (`--randomly-seed=20261017`): 8,611 passed, 5 skipped, 2 xfailed, 4 xpassed in 663.17s
- **Run 3** (`--randomly-seed=839201`): 8,611 passed, 5 skipped, 2 xfailed, 4 xpassed in 681.42s

**Outcome**: Zero failures and zero flaky tests detected across all three runs. Zero quarantine or serial reruns required.

## Files Changed Across Set Commits

Derived by querying commits with trailers `AW-Item: <qqrgv3|tv72xy|83nnyn|c8bfp9|vgus66>`:
Command: `git log --format=%H --grep='AW-Item: <id6>'`

Total files changed: 109 unique paths.

- `.aw/records/backlog/open/20261017-4qu8zm-01-4qu8zm-fix-trailing-newline-inconsistency-for-project-jso.backlog.md`
- `.aw/records/backlog/open/20261017-96lj37-01-96lj37-testcleantargetconfighome-test-case-l-hardcodes-35.backlog.md`
- `.aw/records/backlog/open/20261017-aenl8o-01-aenl8o-clineverleakstheinteractivityoverridetests-prompts.backlog.md`
- `.aw/records/backlog/open/20261017-jiqna0-01-jiqna0-fix-nonexistent-test-foo-py-citation-in-contributi.backlog.md`
- `.aw/records/backlog/open/20261017-q2cgcu-01-q2cgcu-order15clitests-interactive-accept-migration-promp.backlog.md`
- `.aw/records/backlog/open/20261017-w4eswb-01-w4eswb-suitebaselinemodegatetests-timing-out-on-suite-bas.backlog.md`
- `.aw/records/backlog/open/20261017-zcouni-01-zcouni-unboundlocalerror-on-policycancellederror-in-cli-r.backlog.md`
- `.aw/records/plans/executed/20261016-testprune-01-qqrgv3-build-the-test-classification-and-per-test-coverage-tooling.ipd.md`
- `.aw/records/plans/executed/20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.ipd.md`
- `.aw/records/plans/executed/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md`
- `.aw/records/plans/executed/20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.ipd.md`
- `.aw/records/plans/pending/20261016-testprune-01-qqrgv3-build-the-test-classification-and-per-test-coverage-tooling.ipd.md`
- `.aw/records/plans/pending/20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.ipd.md`
- `.aw/records/plans/pending/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.ipd.md`
- `.aw/records/plans/pending/20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.ipd.md`
- `.aw/records/plans/pending/20261016-testprune-05-vgus66-prove-the-pruned-suite-still-catches-regressions-with-covera.ipd.md`
- `.aw/records/research/20261016-testprune-01-offdhr-test-prune-baseline.assessment.md`
- `.aw/records/research/20261016-testprune-02-hwuvpx-test-prune-decision-table.assessment.md`
- `.aw/records/reviews/20261016-testprune-01-qqrgv3-build-the-test-classification-and-per-test-coverage-tooling.review.md`
- `.aw/records/reviews/20261016-testprune-02-tv72xy-delete-tests-that-pin-code-structure-names-or-architecture-r.review.md`
- `.aw/records/reviews/20261016-testprune-03-83nnyn-consolidate-duplicate-marginal-and-combinatorial-tests-into.review.md`
- `.aw/records/reviews/20261016-testprune-04-c8bfp9-speed-up-the-slowest-tests-and-shared-fixtures-so-the-retain.review.md`
- `.aw/records/reviews/20261016-testprune-05-vgus66-prove-the-pruned-suite-still-catches-regressions-with-covera.review.md`
- `CONTRIBUTING.md`
- `conftest.py`
- `tests/conformance_matrix.py`
- `tests/repo_template.py`
- `tests/slow_allowlist.txt`
- `tests/support.py`
- `tests/test_agent_checked_count.py`
- `tests/test_agent_surface_conformance.py`
- `tests/test_agy_failed_state_parity.py`
- `tests/test_agy_run.py`
- `tests/test_agy_runipd_cli.py`
- `tests/test_attention.py`
- `tests/test_attention_contract.py`
- `tests/test_attention_degraded_item.py`
- `tests/test_check_engine.py`
- `tests/test_check_engine_metadata_region.py`
- `tests/test_check_severity_tally.py`
- `tests/test_clean_target_config_home.py`
- `tests/test_cli.py`
- `tests/test_completion_stale_notice.py`
- `tests/test_conformance_inproc.py`
- `tests/test_descriptive_refusal_hoist.py`
- `tests/test_docs_test_citations.py`
- `tests/test_doctor_diagnostic_severity.py`
- `tests/test_egress_policy.py`
- `tests/test_exit_contract_conformance.py`
- `tests/test_explicit_dir_non_project.py`
- `tests/test_explicit_dir_subdir_resolution.py`
- `tests/test_finalize_stale_plan_path.py`
- `tests/test_fix_it_global_caps.py`
- `tests/test_forkresid_shared_shells.py`
- `tests/test_group_verb_policy.py`
- `tests/test_handoff_ready_gate.py`
- `tests/test_history_order.py`
- `tests/test_host_capability_extension.py`
- `tests/test_host_sandbox_profile.py`
- `tests/test_hostdedup_third_host.py`
- `tests/test_index_check_agent_records.py`
- `tests/test_index_write_agent_records.py`
- `tests/test_install_report_truth.py`
- `tests/test_installer.py`
- `tests/test_ipd_authoring.py`
- `tests/test_ipd_exec_finding_codes.py`
- `tests/test_ipd_lint.py`
- `tests/test_ipd_schema.py`
- `tests/test_json_surface_leak_posture.py`
- `tests/test_live_conformance_sweep.py`
- `tests/test_oc_runipd.py`
- `tests/test_orchestrator_retirement.py`
- `tests/test_orchestrator_shape_gate.py`
- `tests/test_platform_lock.py`
- `tests/test_project_context.py`
- `tests/test_reaskscore_composed.py`
- `tests/test_records_only_lane_rederive.py`
- `tests/test_releases_cli.py`
- `tests/test_repo_template.py`
- `tests/test_run_analytics.py`
- `tests/test_run_analytics_cli.py`
- `tests/test_run_analytics_statistics.py`
- `tests/test_run_selection_policy.py`
- `tests/test_runner_fallback_bindings.py`
- `tests/test_runner_shared.py`
- `tests/test_runs_repo_alias.py`
- `tests/test_runwire_verifier_authority.py`
- `tests/test_sanitizer_severity_vocabulary.py`
- `tests/test_severity_truth_surfaces.py`
- `tests/test_shared_flag_honored.py`
- `tests/test_slow_report.py`
- `tests/test_statusline_ascii_mode.py`
- `tests/test_statusline_stop_tally.py`
- `tests/test_statusline_visible_width.py`
- `tests/test_suite_baseline_mode_gate.py`
- `tests/test_suite_cache.py`
- `tests/test_suite_slot_lock.py`
- `tests/test_term.py`
- `tests/test_terminal_status_vocabulary.py`
- `tests/test_testprune_tools.py`
- `tests/test_turn_bounds.py`
- `tests/test_typecheck_gate.py`
- `tests/test_usage_refusal_agent_record.py`
- `tests/tools/classify.py`
- `tests/tools/covctx_plugin.py`
- `tests/tools/markers_dump.py`
- `tests/tools/percov_analyze.py`
- `tests/tools/percov_run.py`
- `tests/tools/pinscan.py`
