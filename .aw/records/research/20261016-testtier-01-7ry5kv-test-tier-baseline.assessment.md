---
id: 7ry5kv
created: 20261016
set: testtier
order: 01
topic: [testing]
model: 
kind: assessment
status: reference
outcome: informational
summary: Baseline for test tiers: default 695 tests ~19s but 28% line coverage (93/196 modules at zero) vs full 8794 tests ~565s at 75%
consumed-by: []
---

# Test tier baseline (2026-10-16, main at eca2e2211)

Host: 12 CPUs; xdist auto resolves to 6 workers (`conftest.pytest_xdist_auto_num_workers`). Measured in an isolated worktree.

## Counts and wall times

| Tier (today) | Selection | Tests | Wall (warm) |
| --- | --- | --- | --- |
| default `python3 -m pytest` | 19 `testpaths` modules, `-m 'not slow and not livecorpus'` | 695 | 25.09s, 18.31s, 20.90s (median 20.90s) |
| full `pytest tests/ -m ''` | everything | 8794 collected; 8771 passed, 5 skipped, 18 xfailed | 565.28s |
| `tests/` with default markers | `-m 'not slow and not livecorpus'` | 8502 | not timed |
| `slow` / `livecorpus` | markers | 280 / 12 | not timed separately |

## Coverage of `agent_workflows/` (coverage.py 7.15, branch, xdist workers combined)

| Run | Line coverage | Lines | Branches |
| --- | --- | --- | --- |
| default (695 tests) | 28% | 29309 / 93730 | 7973 / 37902 |
| full (8794 tests) | 75% | 72507 / 93730 | 26266 / 37902 |

The default reaches ZERO lines in 93 of 196 modules (74 of which the full suite does cover). So the routine gate, which is also the runner merge gate (`suite_cache.SUITE_CHECK_ARGV` = bare `python3 -m pytest`), cannot see regressions in roughly half the codebase.

Largest gaps (full minus default, percent covered):

| Module | Default % | Full % | Statements |
| --- | --- | --- | --- |
| `docs_render.py` | 0.0 | 100.0 | 51 |
| `command_surface.py` | 0.0 | 98.9 | 72 |
| `run_analytics_schema.py` | 0.0 | 96.7 | 322 |
| `host_cmd.py` | 0.0 | 96.4 | 64 |
| `run_analytics_statistics.py` | 0.0 | 95.8 | 313 |
| `workflow_compiler.py` | 0.0 | 95.7 | 81 |
| `pypi_links.py` | 0.0 | 94.9 | 56 |
| `run_analytics.py` | 0.0 | 93.8 | 342 |
| `run_analytics_pricing.py` | 0.0 | 92.6 | 186 |
| `security_hardening.py` | 0.0 | 89.8 | 174 |
| `install_history.py` | 0.0 | 89.0 | 63 |
| `workflow_profile.py` | 0.0 | 88.5 | 63 |
| `run_dashboard.py` | 0.0 | 88.1 | 435 |
| `workflow_source.py` | 0.0 | 87.5 | 84 |
| `release_readiness.py` | 0.0 | 87.1 | 257 |
| `production_checks.py` | 0.0 | 86.7 | 685 |
| `host_runner.py` | 0.0 | 86.4 | 120 |
| `host_adapters.py` | 0.0 | 86.2 | 256 |
| `partition.py` | 0.0 | 86.2 | 615 |
| `workflow_artifacts_prune.py` | 0.0 | 84.4 | 226 |
| `leak_sanitizer_config.py` | 0.0 | 83.8 | 110 |
| `source_offsets.py` | 0.0 | 83.6 | 135 |
| `precommit_scope_gate.py` | 0.0 | 82.8 | 59 |
| `run_analytics_spa.py` | 0.0 | 82.3 | 590 |
| `workflow_loader.py` | 0.0 | 82.2 | 59 |
| `comms_broker.py` | 0.0 | 82.0 | 391 |
| `lanes_cli.py` | 0.0 | 81.8 | 369 |
| `run_analytics_cache.py` | 0.0 | 81.6 | 258 |
| `project_registry.py` | 0.0 | 81.2 | 196 |
| `readiness_recheck.py` | 0.0 | 81.1 | 187 |
| `reviews.py` | 0.0 | 80.0 | 142 |
| `agy_run.py` | 0.0 | 79.9 | 399 |
| `host_capability_registry.py` | 0.0 | 79.6 | 613 |
| `comms.py` | 0.0 | 78.8 | 90 |
| `workflow_schema.py` | 0.0 | 78.7 | 228 |
| `plans_archive.py` | 0.0 | 78.6 | 241 |
| `coverage_record.py` | 15.8 | 93.8 | 169 |
| `executed_transition_gate.py` | 0.0 | 76.2 | 192 |
| `duration.py` | 0.0 | 75.0 | 22 |
| `subtest_rows.py` | 0.0 | 74.8 | 97 |

Full table: regenerate with the method below.

## Slowest full-suite tests (`--durations=30`, first 15)

```
118.10s call     tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[doctor]
64.25s call     tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_heavy_leaves[doctor]
27.24s call     tests/test_agent_surface_conformance.py::test_agent_surface_conformance[partition]
24.21s call     tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
23.69s call     tests/test_shared_flag_honored.py::test_fields_flag_honored_read[partition]
23.40s call     tests/test_shared_flag_honored.py::test_json_flag_honored_read[partition]
20.52s call     tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_exhaustive_sweep
20.22s call     tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun
20.04s call     tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit
18.52s call     tests/test_installer.py::InstallPreservationTests::test_every_existing_file_state_is_handled_without_clobbering
17.80s call     tests/test_agy_runipd_cli.py::AgyFailClosedIntegrationGuardTests::test_the_MEASURED_INCIDENT_is_now_SURVIVED_defer_then_integrate
17.71s call     tests/test_installer.py::InstallerEndToEndTests::test_gitignored_opencode_does_not_abort
16.99s call     tests/test_shared_flag_honored.py::test_fields_flag_honored_read[checkup]
16.75s call     tests/test_oc_runipd.py::EmptyReviewSweepExitsZeroTests::test_end_to_end_empty_sweep_cli
16.09s call     tests/test_severity_truth_surfaces.py::test_attention_diagnostic_preserves_drift_severity_and_exit_code
```

Two `doctor` live-leaf conformance tests alone take 118s and 64s, longer than the whole target for the thorough tier's slowest worker; they dominate xdist tail latency.

## Method

`python3 -m pytest --cov=agent_workflows --cov-branch --cov-report=` (default) and `python3 -m pytest tests/ -m '' -n auto --dist=worksteal -o addopts="" -p no:randomly --cov=agent_workflows --cov-branch` (full), `coverage json`, compared per file. Coverage-instrumented wall times (70.7s default, 719s full) are not the baseline wall times.
