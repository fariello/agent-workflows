---
id: offdhr
created: 20261016
set: testprune
order: 01
topic: [testing]
model: 
kind: assessment
status: reference
outcome: informational
summary: Prune baseline: 8794 tests 565s; per-test coverage contexts for 3714 in-process tests, 1331 with zero unique lines, 70 modules where every test is redundant by line; 53 files with structure-pin candidates
consumed-by: []
---

# Test prune baseline (2026-10-16, main at 6ea45c974)

12-CPU host, 6 xdist workers, isolated worktree.

## Suite size and time
- Collected 8794 tests (`pytest tests/ -m '' --collect-only`); full run 8771 passed, 5 skipped, 18 xfailed in 565.28s wall (uninstrumented, see research `7ry5kv`).
- `--durations=30` is recorded in research `7ry5kv`; the two slowest are `doctor` live-leaf conformance tests at 118s and 64s.

## Per-test coverage contexts (coverage.py 7.15, `--cov-context=test`, lines only)
- Instrumented full run: 8776 passed in 735s.
- Distinct recorded test contexts: 3714. Parametrized cases collapse to one context per function, and tests that only spawn subprocesses record no in-process lines, so this number is less than 8794. Subprocess-only tests therefore need separate treatment: they are NOT redundant just because they show no lines here.
- Tests whose every covered line is also covered by some other test (0 unique lines): 1331 of 3714. This is a CANDIDATE set for consolidation, not a deletion list: equal lines can still be different assertions.
- Modules where EVERY recorded test has 0 unique lines: 70.

Top modules by recorded test functions (total, zero-unique):

| Module | Test functions | Zero-unique |
| --- | --- | --- |
| `tests/test_oc_runipd.py` | 105 | 60 |
| `tests/test_runner_shared.py` | 71 | 32 |
| `tests/test_installer.py` | 61 | 11 |
| `tests/test_cli.py` | 51 | 17 |
| `tests/test_ipd_lifecycle_cli.py` | 45 | 19 |
| `tests/test_status_set.py` | 44 | 22 |
| `tests/test_ipd_lint.py` | 39 | 13 |
| `tests/test_agy_runipd_cli.py` | 38 | 29 |
| `tests/test_attention.py` | 37 | 10 |
| `tests/test_aw_upgrade_test.py` | 34 | 0 |
| `tests/test_run_viewer.py` | 34 | 2 |
| `tests/test_backlog.py` | 33 | 17 |
| `tests/test_runner_profiles.py` | 32 | 8 |
| `tests/test_finalize_sendback.py` | 31 | 16 |
| `tests/test_verifier_corroboration.py` | 31 | 8 |
| `tests/test_orchestrator_retirement.py` | 30 | 15 |
| `tests/test_runner_backlog_close_behavior.py` | 30 | 12 |
| `tests/test_agy_run.py` | 29 | 0 |
| `tests/test_run_recovery_cli.py` | 29 | 0 |
| `tests/test_config.py` | 28 | 5 |
| `tests/test_group_verb_policy.py` | 28 | 17 |
| `tests/test_research_index.py` | 28 | 9 |
| `tests/test_run_analytics.py` | 27 | 1 |
| `tests/test_host_capability_registry.py` | 26 | 4 |
| `tests/test_workflow_schema_compiler.py` | 26 | 7 |

Modules where every recorded test has zero unique lines:

- `tests/test_agent_findings_severity.py`
- `tests/test_agent_surface_conformance.py`
- `tests/test_agents_block_target_neutral.py`
- `tests/test_agy_failed_state_parity.py`
- `tests/test_artifact_audit_index_cache.py`
- `tests/test_artifact_audit_verdicts.py`
- `tests/test_attention_blind_spot.py`
- `tests/test_attention_degraded_item.py`
- `tests/test_backlog_close_host_label.py`
- `tests/test_backlog_gate_follows_status.py`
- `tests/test_backlog_history_dedup_parity.py`
- `tests/test_backlog_transition_authority.py`
- `tests/test_bidi_control_rejection.py`
- `tests/test_capture_command_stream_bounds.py`
- `tests/test_check_engine_metadata_region.py`
- `tests/test_check_engine_status_meta.py`
- `tests/test_check_recovery_fidelity.py`
- `tests/test_clean_target_config_home.py`
- `tests/test_cli_parser_conflict_policy.py`
- `tests/test_command_surface_declarations.py`
- `tests/test_config_agent_surface.py`
- `tests/test_conformance_matrix_structure.py`
- `tests/test_coverage_record.py`
- `tests/test_descriptive_refusal_hoist.py`
- `tests/test_deselect_notice.py`
- `tests/test_drift_rule_registration.py`
- `tests/test_empty_result_convention_doc.py`
- `tests/test_exit_contract_conformance.py`
- `tests/test_exit_vocabulary_boundary.py`
- `tests/test_explicit_dir_non_project.py`
- `tests/test_family_root_agent_conformance.py`
- `tests/test_gate_pair_validation_parity.py`
- `tests/test_help_nontty_claim.py`
- `tests/test_history_date_clock_sidecar.py`
- `tests/test_history_label_parity.py`
- `tests/test_history_write_order.py`
- `tests/test_home_path_pattern_source.py`
- `tests/test_host_capability_wiring.py`
- `tests/test_hostcapgate_execute_requirement.py`
- `tests/test_human_renderer_agent_hint.py`
- `tests/test_index_check_agent_records.py`
- `tests/test_install_report_truth.py`
- `tests/test_install_source_option.py`
- `tests/test_installed_text_current.py`
- `tests/test_ipd_templates.py`
- `tests/test_lane_reaper_callshape.py`
- `tests/test_lifecycle_dirs.py`
- `tests/test_lifecycle_gate_coverage.py`
- `tests/test_lifecycle_legend_help_reach.py`
- `tests/test_loaded_code.py`
- `tests/test_no_project_exit_is_cannot_run.py`
- `tests/test_prior_attempt_projection.py`
- `tests/test_prompts_attention.py`
- `tests/test_releases_line_writers.py`
- `tests/test_retry_class_mapping.py`
- `tests/test_run_cli_human_redaction.py`
- `tests/test_run_dir_outcomes_parent_is_guaranteed.py`
- `tests/test_run_progress_count.py`
- `tests/test_run_summary_visible_width.py`
- `tests/test_runner_safety_probe_memo.py`
- `tests/test_runs_flag_position_parity.py`
- `tests/test_scaffold_history_clock.py`
- `tests/test_selector_type_containment.py`
- `tests/test_severity_tier_contract.py`
- `tests/test_specs_metadata_duplicate_bullet.py`
- `tests/test_subparser_descriptions.py`
- `tests/test_support_section.py`
- `tests/test_typecheck_gate.py`
- `tests/test_uncollected_test_modules.py`
- `tests/test_uninstall_layout_artifacts.py`

## Structure-pin candidates (static scan, heuristic)
53 files match at least one pattern (`inspect.getsource`, `ast.parse(`, reading `agent_workflows/*.py` text, `hasattr(<module>, "_...")`, census/line-count words). Highest: `tests/test_lost_guard_census.py` (19), `tests/test_runner_fork_scan_constants.py` (6), `tests/test_orchestrator_retirement.py`, `tests/test_runner_shared.py`, `tests/test_v_item_demonstration_reachability.py` (`inspect.getsource`). Each must be read; the word-based patterns over-match.

## Raw data
The coverage database (6.9 MB) and the derived per-test unique-line JSON are machine-local scratch and are regenerated by child `qqrgv3`'s tooling; they are not committed.

## CORRECTION (2026-10-16, found while authoring child `qqrgv3`)

The per-test context numbers above are a MEASUREMENT ARTIFACT, not facts about the suite. Under Python 3.14 the default coverage tracer recorded contexts for only 77 of 110 tests in `tests/test_status_set.py` (103 with the C tracer), and contexts were not propagated into subprocesses. "3714 contexts", "1331 zero-unique" and "70 all-redundant modules" therefore UNDERSTATE coverage and must not drive any deletion. A probe plugin that sets the context per test id, in-process and in spawned subprocesses, with branch coverage, recorded 110 of 110. Child `qqrgv3` builds that tooling and re-measures; its decision table supersedes these numbers.
