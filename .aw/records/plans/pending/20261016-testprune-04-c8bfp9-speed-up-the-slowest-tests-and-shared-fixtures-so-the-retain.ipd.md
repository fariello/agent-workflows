# IPD: Speed up the slowest tests and shared fixtures so the retained full suite runs under 120 seconds

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `4ul37x` (Set `testprune`) SPEED UP section and its headline target: the FULL retained suite (`python3 -m pytest tests/ -m ''`) under 120s wall on 6 xdist workers. Baseline (research `7ry5kv` section "Slowest full-suite tests", main `eca2e2211`; the scratch log it came from is machine-local and not an artifact): 565.28s wall; the slowest 30 tests alone sum to 617.6s of worker time; the two slowest are `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[doctor]` at 118.10s and `tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_heavy_leaves[doctor]` at 64.25s, so the worst single test alone nearly equals the whole target and pins one worker's tail. Measured at authoring in this worktree: `aw partition -t plans -s approved --json` takes 28.1s to 30.7s when run with cwd at the repository (it walks this repository's full `.aw/records/` tree) but 0.40s in a minimal git repo with an empty `.aw/records/plans/`; `aw status` takes 9.8s at the repository; `aw doctor --agent` takes 0.62s in the minimal repo. So most of the heavy-leaf cost is the size of THIS repository's records corpus, which the exit-code, `--json`, `--fields`, `--agent` and NO_COLOR contracts do not depend on.
- Scope: After `83nnyn` has consolidated, (1) point conformance sweeps that do not assert on this repository's records at a seeded, session-built fixture project instead of `REPO_ROOT`; (2) replace subprocess `aw` invocations with in-process `agent_workflows.cli.main([...])` where the process boundary is not under test, keeping a small, named set of true subprocess smoke tests; (3) build installed-project and temp-repo templates once per session and copy per test; (4) replace real sleeps and wall-clock waits with injected clocks or shortened timeouts through existing parameters; (5) split remaining long tests so `--dist=worksteal` can balance; (6) record a justification for every test still over 2s. Never weakens an assertion; `livecorpus` tests stay and are sped up only by caching, never by narrowing their corpus.
- Scope-Paths: tests/, conftest.py, pyproject.toml, .gitignore, .aw/records/research/*testprune*
- Item-Dependencies: executed:83nnyn
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 4
- Highest E allocated: 11
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: c8bfp9
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): status set to reviewed
- 2026-10-16 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009, PR-010, PR-011, PR-012
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune) with baseline research offdhr/7ry5kv

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`python3 -m pytest tests/ -m ''` completes in under 120s wall (median of three warm runs, 6 workers, `--dist=worksteal`, `pytest-randomly` on) with no assertion weakened, and every test still over 2s carries a recorded justification.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Rule for every item: measure the targeted tests' `--durations` before and after and record both in the decision-table research; an item that does not reduce wall or tail time is reverted. Every converted test keeps the same assertions (exit code, record schema, field content, ANSI absence); if a conversion cannot preserve one, the test stays as it was.

### Task group 1: baseline

- [x] E-01 At this child's starting commit (after `83nnyn`), run the full suite three times warm (`python3 -m pytest tests/ -m '' --durations=0 --junitxml=<dir>/run<N>.xml`, uninstrumented, default `addopts` workers) and record: collected count, the three wall times and median, the top 50 call durations, the per-worker finish skew (from `--junitxml` per-test times grouped by the xdist worker reported in `-v` output; otherwise the longest single test as the tail floor), the slow-test census (count of tests over 2s, 5s and 10s), the sum of all call durations, and the full-suite union line and branch coverage with `python3 -m tests.tools.percov_run --out .aw/state/percov/c8bfp9-base` plus `percov_analyze` (the `qqrgv3` tooling; E-10 compares against it with `--compare`). Run with `AW_CONFIG_DIR` unset (see F-7).
  - Depends on: none
  - Expected outcome: baseline recorded in a `c8bfp9 baseline` section of the `qqrgv3` decision-table research; this child's target arithmetic stated (sum of call durations / 6 versus 120s, and the longest single test versus 120s).
  - Execution state: performed

### Task group 2: heavy conformance leaves off the live corpus

- [x] E-02 Add a seeded fixture project builder in `tests/conformance_matrix.py` (built once per session per worker: the existing `build_installed_project_template` (`git init`, local identity, `aw install . --yes`), plus a small committed records set: one pending plan, one backlog item, one spec, one research record, one review record, so every leaf has non-empty input; any id6 an `RUNNABLE_ARGV` entry names (today `f36de0` for `show`, `reviews decisions`, `record-history`; `25kzda` for `graduation`) must resolve in the seeded tree, and repo-relative path arguments (`workflow validate` / `workflow check-generated` `tests/fixtures/workflow-src/plan-review`) are rewritten to absolute paths under `REPO_ROOT` or copied into the project), and make `run_cli`/`run_cli_tty` callers in `tests/test_exit_contract_conformance.py` (`test_live_safe_leaves_exit_contract_membership_heavy`, `_cheap`), `tests/test_live_conformance_sweep.py` (`test_no_color_scenario_is_plain_heavy_leaves`, `_cheap_leaves`, help and usage sweeps), `tests/test_agent_surface_conformance.py::test_agent_surface_conformance` and `tests/test_shared_flag_honored.py` read tests use that project as `cwd` for every leaf, replacing the current `doctor`/`check`-only `scoped_repo_dir` special case. Before switching, record each switched leaf's `(exit code, outcome)` at `REPO_ROOT` and on the seeded project for both the human and `--agent` surfaces: a leaf whose outcome class changes (for example from `clean 0` to `cannot-run 2` because an argument no longer resolves) is a seeding defect to fix, not an accepted change, because the sweep would otherwise silently stop exercising that leaf's success path (review probe: `show f36de0`, `graduation 25kzda`, `reviews decisions f36de0`, `record-history f36de0` and `workflow validate tests/fixtures/...` all went from `clean 0` at the repository to `cannot-run 2` in an unseeded installed project). Tests that assert a property of THIS repository's records (the `livecorpus` marker, `TestLivePendingCorpus`) are untouched.
  - Depends on: E-01
  - Expected outcome: the `[doctor]` and `[partition]` node ids' durations drop (review probe, sandboxed `AW_HOME`, `AW_CONFIG_DIR` unset: `doctor` 61.5s at the repository versus 1.15s in an installed project; `partition -t plans -s approved --json` 3.4s versus 0.36s; `attention --check` 5.5s versus 1.7s); every leaf still asserts exit-code membership in `command_surface.get_declaration(leaf).exit_contract`, JSON parseability, schema-valid terminal records and ANSI absence; the per-leaf outcome-class table shows no class change.
  - Execution state: performed
- [x] E-03 Re-measure `LIVE_HEAVY_LEAVES` (`doctor`, `attention`, `status`) against the seeded project; if each is now under 2s, fold them into the cheap parametrization and drop the `slow` mark and `timeout(500)` from the heavy variants (the heavy split exists only because of the measured live-tree cost recorded in the `LIVE_HEAVY_LEAVES` comment); update that comment with the new measurement. Keep `tests/test_exit_contract_conformance.py`'s `LIVE_HEAVY_LEAVES <= LIVE_SAFE_LEAVES` subset test green (an empty set is a subset). `status` iterates every repository configured in the user config (`cli._repos_for_report`; review probe: 37 registered repos made `aw status` take 5.8s even in a fresh project until `AW_CONFIG_DIR` was unset, then 0.46s), so its seeded measurement must be taken with `AW_CONFIG_DIR` unset and `AW_HOME`/`XDG_CONFIG_HOME` sandboxed exactly as `conftest.py` does for tests. Moving a leaf out of `slow` adds it to `make test` only if its module is in the `core` selection; do not add a `core` mark here (hguae9 owns membership).
  - Depends on: E-02
  - Expected outcome: heavy and cheap parametrizations merged or the remaining heavy members justified with a measurement; `LIVE_HEAVY_LEAVES` comment shows the new numbers; the subset test passes.
  - Execution state: performed

### Task group 3: in-process instead of subprocess

- [ ] E-04 Introduce one in-process runner helper beside `run_cli` in `tests/conformance_matrix.py` (`run_cli_inproc(argv, *, cwd=None, env_overrides=None, no_color=False, ...)`, same keyword parameters and `RunResult` shape as `run_cli`): it saves and restores `os.getcwd()` with `os.chdir` in a `try/finally` (NOT `monkeypatch`, which is unavailable in the 430 `unittest.TestCase` modules and under `make test-serial`), applies the same environment `_pinned_env` builds via a save-and-restore of `os.environ` (so `NO_COLOR`, `COLUMNS`, `TERM`, `AW_ASCII_ONLY` behave as in the subprocess), redirects stdout/stderr to `io.StringIO`, calls `agent_workflows.cli.main(argv)`, maps `SystemExit` to a return code, and resets `sys.argv`. It follows the existing `_capture_cli` in `tests/test_usage_refusal_agent_record.py`. A captured `io.StringIO` is not a TTY, matching `run_cli`'s non-TTY pipes; if a converted test's output differs between `run_cli` and `run_cli_inproc` for the same argv (exit code or stdout bytes), the test stays subprocess and the difference is recorded. Add behavioral tests for the helper in `tests/test_conformance_inproc.py`: equal `(returncode, stdout)` against `run_cli` for a handful of cheap leaves (`--version`, `layout --agent`, a usage error), restored cwd and environment after a call that raises, and `NO_COLOR` honored.
  - Depends on: E-01
  - Expected outcome: `run_cli_inproc` exists beside `run_cli`; `tests/test_conformance_inproc.py` passes under pytest (`-n 6`, randomized) and under `python3 -m unittest tests.test_conformance_inproc`, showing equal `(returncode, stdout)` with `run_cli` for the chosen leaves, restored cwd and environment after a raising call, and `NO_COLOR` honored.
  - Execution state: pending
- [ ] E-11 Convert subprocess callers whose assertions are on exit code and stdout/stderr content only. Authoring census: 84 test modules launch `aw` via `run_cli` or `[sys.executable, "-m", ...]`, versus 107 that already call `cli.main(` in-process (review HEAD `8f1a94c58`: 85 and 117). Convert in module groups of at most about ten modules per commit, re-running each group under `-n 6` with randomization before the next. Keep subprocess where the boundary IS under test: TTY/pty behavior (`run_cli_tty`), signal and exit-130 handling (`test_universal_130_floor_and_signal_code_exclusion`), environment and PYTHONPATH isolation, re-exec (`AW_NO_REEXEC`), import-time side effects, the installed console script and wheel build (`tests/test_installed_version_reporting.py`), and the hguae9 core smoke set. Record that kept set (node ids plus reason) in the research.
  - Depends on: E-03, E-04
  - Expected outcome: converted modules pass under `-n 6` with randomization; process-global state that leaks between in-process calls (cwd, env, `sys.argv`, logging handlers, module caches) is reset by the helper and demonstrated by running converted modules in a shuffled order twice with distinct seeds; the kept-subprocess set is recorded with reasons; before and after module durations recorded; a conversion that does not reduce duration is reverted.
  - Execution state: pending
- [ ] E-05 Mock host-binary and network probes at the boundary in tests that are not about the host (for example `opencode`, `agy`, `git` version probes and any HTTP or PyPI lookup reached from `doctor`/`checkup`), using the existing probe seams in production code where present (or `unittest.mock.patch` of the probe function by symbol when no seam exists, since that adds no production code); tests that ARE about the probe keep the real call. Record each mocked seam by symbol. A mock replaces a probe only in a test whose assertions do not depend on the probe's real result; for `doctor` the review profile shows the cost on this repository is the records walk (`doctor.probe_artifacts` -> `check_engine.check_ipd_dependencies` -> `review_findings.subject_gating_blocks`, 50.7s of 99s profiled), not host probes, so E-02 is the main lever and E-05 is measured, not assumed.
  - Depends on: E-11
  - Expected outcome: the list of host-binary spawns outside the host-probe modules (found with a per-test `subprocess.Popen` argv probe plugin in scratch, or by reading) is recorded with a disposition each (mocked or kept with reason); `--durations` before and after for `checkup` and `doctor` tests recorded; a mock that does not reduce duration is reverted (rule for every item).
  - Execution state: pending

### Task group 4: fixtures, clocks, balancing

- [ ] E-06 Cache expensive per-test setup: reuse `build_installed_project_template` plus `clone_isolated_project` (session template, per-test copy) for every test that runs `aw install` into a fresh temp repo (authoring census: 24 modules reference install into a project, including `tests/test_installer.py`, 144 node ids, module `slow`), and the `83nnyn` E-09 bare-repo helper `tests/repo_template.py` `copy_template_repo` for git setup in modules `83nnyn` E-11 did not migrate. A template must be a plain function plus per-process cache (as `83nnyn` E-09 is), not only a pytest fixture, because `tests/test_installer.py` and most install-using modules are `unittest.TestCase` classes. Tests whose subject is the install itself (installer preservation and consent tables) keep installing, but share one template of the PRE-install state.
  - Depends on: E-11
  - Expected outcome: before and after durations recorded for `tests/test_installer.py` (authoring: `test_every_existing_file_state_is_handled_without_clobbering` 18.5s, `test_gitignored_opencode_does_not_abort` 17.7s, `test_the_users_gitignore_is_managed_without_being_clobbered` 13.8s, `test_every_consent_mode_disposes_of_a_drifted_file_correctly` 11.2s) and every other converted install-using module; each converted test that writes into its project is shown isolated (the template is unchanged after the module runs: a content digest of the template before and after).
  - Execution state: pending
- [ ] E-07 Remove real waits: replace `time.sleep` in test bodies (authoring census: 57 call sites in 42 files; review `rg -c 'time\.sleep\('` counted 57 occurrences in 24 files, re-derive at execution; including `time.sleep(60)` child processes in `tests/test_ipd_lifecycle_cli.py`, `tests/test_lane_owner_record_anchoring.py`, `tests/test_oc_runipd.py`, `time.sleep(10)` in `tests/test_stall_progress_agy.py` and `tests/test_capture_command_stream_bounds.py`, and `time.sleep(1.2)`/`time.sleep(1.5)` in `tests/test_hang_guard_budget.py`, which are inside generated child test files whose subject IS the hang guard's wall-versus-CPU distinction and are therefore kept) with injected clocks or the shortest timeout the code's existing parameters accept (for example `now=` parameters such as `suite_cache.prune_expired_records(now=...)`, `host_capability_registry` `is_expired(now=...)`, `run_viewer.parse_since_timestamp(now=...)`, `AW_TEST_WALL_TIMEOUT`). A sleeping child process used only as a long-lived pid to be killed is kept (it costs nothing once killed) and noted. A sleep whose duration IS the behavior under test (a stall threshold, a wall ceiling, a timeout firing) keeps a real wait but is shortened only through an existing parameter, never by loosening the threshold it checks. Where no seam exists, do not add a production seam in this child; record the test as justified.
  - Depends on: E-01
  - Expected outcome: per-site disposition recorded (converted, kept-as-kill-target, justified); converted tests' durations drop; no timing assertion loosened.
  - Execution state: pending
- [ ] E-08 Split or speed the remaining long single tests so worksteal can balance: for example `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta` (24.2s, `livecorpus`: parametrize over corpus shards so the full corpus is still covered), `tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun` (20.2s), `tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit` (20.0s, runs `mypy agent_workflows`; mypy is incremental by default and writes `.mypy_cache/` in the repository root, which does not exist in this checkout and is not in `.gitignore` (review check), so the run is always cold: either pass `--cache-dir` to a gitignored location such as `.aw/state/mypy-cache` (a persistent cache can mask nothing, because mypy invalidates per-module on content hash) or add `.mypy_cache/` to `.gitignore` and leave the default; record the warm and cold durations; a cold first run in CI is expected and justified in E-09), `tests/test_agy_runipd_cli.py::AgyFailClosedIntegrationGuardTests::test_the_MEASURED_INCIDENT_is_now_SURVIVED_defer_then_integrate` (17.8s), `tests/test_oc_runipd.py::EmptyReviewSweepExitsZeroTests::test_end_to_end_empty_sweep_cli` (16.8s), `tests/test_severity_truth_surfaces.py::test_attention_diagnostic_preserves_drift_severity_and_exit_code` (16.1s), `tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference` (15.2s), and the end-to-end runner tests at 10 to 15s (`test_runfresh_end_to_end`, `test_fix_it_global_caps`, `test_freeze_time_refusal`, `test_gradcover_end_to_end`, `test_agent_user_config_containment`). Corpus-wide shards must cover the same corpus as the original (shard union equals the full plan list, asserted at run time inside the test module: a collection-time hook or module-level helper computes the shards from the same `rglob` the test uses, and a separate test asserts the union of shards equals that list and the shards are disjoint; both must stay `livecorpus`, as the original is). A test split into several node ids keeps every assertion of the original across its parts. Tests that are already end-to-end runner reproductions of a measured incident (for example the `AgyFailClosedIntegrationGuardTests` incident test) keep their end-to-end shape and are sped up only by fixtures and clocks, or justified.
  - Depends on: E-06, E-07
  - Expected outcome: before and after durations for each named test (re-derived from the E-01 top 50, since the authoring list is context); the target is no single test over 15s and the longest test under one sixth of the achieved median wall time; any test above either bound after this item is listed with its justification in E-09 rather than weakened.
  - Execution state: pending

### Task group 5: justification and proof

- [ ] E-09 Record in the decision-table research a row for every test whose call duration is still over 2s in the E-10 runs: node id, duration, and the compelling reason (subprocess boundary under test, real pty, real signal, wheel build, corpus property, etc.). Add a non-failing report in `conftest.py` (`pytest_terminal_summary`, on the xdist controller only, i.e. `PYTEST_XDIST_WORKER` unset; call durations come from the `TestReport.duration` of `when == "call"` reports collected in `pytest_runtest_logreport`, which the controller receives from workers) that lists tests over 2s not present in a small allowlist file `tests/slow_allowlist.txt` (one `node id<TAB>reason` per line), so a new slow test is visible; it warns and never fails, because wall time varies by host. It must coexist with hguae9's core wall-time guard in the same `conftest.py` (that guard is `pytest_sessionfinish`; do not change its exit status). Add a behavioral test in `tests/test_slow_report.py` that runs pytest in a subprocess on a temp project carrying a copy of the hook and asserts: a 2.5s test absent from the allowlist is named in the warning and the run exits 0; the same test listed in the allowlist is not named (use `time.sleep` inside the generated child test only, with a threshold override env such as `AW_SLOW_REPORT_SECONDS=0.2` so the test itself stays fast).
  - Depends on: E-08
  - Expected outcome: every over-2s test in the E-10 runs is in the allowlist with a reason (the allowlist is re-derived from the E-10 runs, a live set); `tests/test_slow_report.py` passes; a full run shows the report's header with zero unlisted tests.
  - Execution state: pending
- [ ] E-10 Prove: three warm full runs `python3 -m pytest tests/ -m '' --durations=20` (median under 120s, `AW_CONFIG_DIR` unset), collected count equal to E-01's plus the tests this child added (`tests/test_conformance_inproc.py`, `tests/test_slow_report.py`, shard-union tests) and with every E-01 node id either present or split into named parts (this child deletes nothing; split ids reconciled by list), full union line and branch coverage from a fresh `percov_run` with `percov_analyze --compare .aw/state/percov/c8bfp9-base` listing zero lost lines or arcs, `python3 -m tests.tools.core_measure` showing no core module lower than before, bare `python3 -m pytest` passing including hguae9's core budget guard, and three randomized runs (`-p randomly`, distinct seeds) pass.
  - Depends on: E-09
  - Expected outcome: median under 120s or, per OQ-02, the achieved median with the remaining top durations and their justifications recorded and the miss reported to the maintainer; zero failures across the randomized runs; zero lost lines or arcs.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/conformance_matrix.py` owns the live CLI helpers (`run_cli`, `run_cli_tty`, `LIVE_SAFE_LEAVES`, `LIVE_HEAVY_LEAVES`, `live_cheap_leaves`, `RUNNABLE_ARGV`, `build_installed_project_template`, `clone_isolated_project`); `run_cli` runs `[sys.executable, "-m", "agent_workflows", *argv]` with cwd defaulting to `REPO_ROOT`, which is why heavy leaves walk this repository's records corpus.
- `LIVE_HEAVY_LEAVES` comment records per-invocation costs at high concurrency (doctor about 407s, attention about 48.5s, status about 37.7s); the heavy split is a cost workaround, not a contract.
- `tests/test_shared_flag_honored.py` and `tests/test_agent_surface_conformance.py` already define a session `scoped_repo_dir` for `doctor` and `check` only (F-2 below generalizes it).
- `conftest.py` owns the xdist worker cap (`pytest_xdist_auto_num_workers`, min(6, cpus/2)) and the hang guard (`AW_TEST_TIMEOUT`, `AW_TEST_WALL_TIMEOUT` default 240s); `pytest-randomly` stays on (pyproject comment). It also sandboxes `AW_HOME`/`XDG_CONFIG_HOME` per test and pops `AW_CONFIG_DIR` at import, so measurements taken outside pytest must do the same to be comparable (F-7).
- 430 of 557 test modules are `unittest.TestCase` classes and `make test-serial` runs `python3 -m unittest discover` without `conftest.py`, so shared helpers (`run_cli_inproc`, templates) are plain functions, never only pytest fixtures (`83nnyn` E-09 precedent).
- `qqrgv3` owns the coverage tooling (`tests/tools/percov_run.py`, `percov_analyze.py --compare`) and the decision-table research record; `hguae9` owns `tests/tools/core_measure.py` and the core budget guard; `83nnyn` owns `tests/repo_template.py`.
- hguae9 owns the `core` marker and a 30s core budget guard; this child must not move tests out of `core` or slow it.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | 565s wall; slowest 30 tests sum to 617.6s worker time; top test 118.1s | research `7ry5kv` "Slowest full-suite tests" |
| F-2 | Per-leaf cost is dominated by this repository's records corpus. Authoring: `partition` 28 to 31s at the repository vs 0.40s minimal; `status` 9.8s; `doctor --agent` 0.62s minimal. Review re-measure (HEAD `8f1a94c58`, sandboxed `AW_HOME`, `AW_CONFIG_DIR` unset): `doctor` 61.5s at the repository vs 1.15s in a freshly installed project; `partition` 3.4s vs 0.36s; `attention --check` 5.5s vs 1.7s; `status` 4.5s vs 0.46s | review timings in this worktree |
| F-3 | Heavy and partition conformance tests use cwd `REPO_ROOT` except `doctor`/`check` in two modules | `run_cli` default cwd; `cwd = scoped_repo_dir if leaf in ("doctor", "check")` in both modules |
| F-4 | 84 modules launch `aw` as a subprocess; 107 already use `cli.main(` in-process | `rg -l` counts at authoring |
| F-5 | 57 `time.sleep(` sites in 42 test files | `rg` count at authoring |
| F-6 | 24 modules install into temp projects; `test_installer.py` has 144 node ids and four tests over 11s | `rg -l`, collection, durations |
| F-7 | `aw status` reports every repository in the user config (`cli._repos_for_report`); inside an agent lane `AW_CONFIG_DIR` points at a populated config, so an unsandboxed measurement walked 37 repos (5.8s in an empty project) | review cProfile: `cli._collect_repo_status_details` called 37 times; 0.46s with `AW_CONFIG_DIR` unset; `conftest.py` "os.environ.pop(\"AW_CONFIG_DIR\", None)" |
| F-8 | Swapping `cwd` to an unseeded installed project silently changes some leaves from success to `cannot-run`, because their `RUNNABLE_ARGV` names a repo-local id6 or relative path | review probe: `show f36de0`, `graduation 25kzda`, `reviews decisions f36de0`, `record-history f36de0`, `workflow validate tests/fixtures/workflow-src/plan-review` each `clean 0` at the repository and `cannot-run 2` in the installed project |
| F-9 | On this repository `doctor`'s cost is the records walk, not host probes | review cProfile of `aw doctor --agent`: `doctor.probe_artifacts` 87.5s of 99.0s, of which `check_engine.check_ipd_dependencies` 50.7s via `review_findings.subject_gating_blocks` |
| F-10 | `mypy` always runs cold here: no `.mypy_cache/` exists and none is gitignored | review `ls -d .mypy_cache`, `.gitignore` |

## Proposed changes (ordered, validatable)

E-01 baseline -> E-02/E-03 heavy leaves off the live corpus (largest single win, about 180s of tail removed) -> E-04 in-process helper and its tests -> E-11 conversion in module groups -> E-05 probe mocking -> E-06 cached templates -> E-07 clocks (independent, after E-01) -> E-08 split long tests -> E-09 justification report -> E-10 proof. One `aw commit c8bfp9 -- <paths>` per item, or per module group for E-11.

## Deferred / out of scope (with reason)

- Adding new production clock or probe seams where none exists: production changes are outside this test-only Set; tests without a seam are justified in E-07/E-09 instead.
  - Carrier-Declined: the prompt `4ul37x` says "shortening timeouts through existing parameters"; a needed seam would be a separate backlog item filed by the executor if the justification list shows it pays off.
- Final whole-Set before/after report, mutation spot-check, flake check, CHANGELOG line.
  - Carrier: vgus66
- Speeding the core tier itself or changing its membership.
  - Carrier: hguae9
  - Carrier-Evidence: .aw/records/plans/executed/20261016-testtier-01-hguae9-split-the-suite-into-a-marker-selected-core-tier-under-30s-a.ipd.md
- Making `aw doctor`/`aw status` themselves faster on a large records corpus (F-9 shows `review_findings.subject_gating_blocks` dominates): a production performance change, outside this test-only Set; if the executor judges the measured cost user-perceptible, file it with `aw backlog new` citing F-2 and F-9.
  - Carrier-Declined: production code is out of scope for Set `testprune`; filing is the executor's call with the measurement attached.

## Scope check

- Over-scope: none.
- Under-scope: none. Running conformance sweeps on a seeded project changes WHICH tree a leaf reads, not what is asserted; the property "the leaf behaves on THIS repository's real records" is owned by `livecorpus` tests, which are untouched.

## Required tests / validation

Per item: the touched modules under `python3 -m pytest <modules> -o addopts="" -n 6 --durations=0` with randomization (seed pasted), `AW_CONFIG_DIR` unset. New helper tests: `python3 -m pytest tests/test_conformance_inproc.py tests/test_slow_report.py tests/test_uncollected_test_modules.py -o addopts=""` and `python3 -m unittest tests.test_conformance_inproc`. At the end: E-10's three full runs, `percov_run` plus `percov_analyze --compare`, `core_measure`, and bare `python3 -m pytest` (core), all pasted.

## Spec / documentation sync

N/A: no spec governs test runtime and no production code changes. `pyproject.toml` comments are updated only if a marker (`slow`) description changes in E-03; `.gitignore` gains `.mypy_cache/` only if E-08 chooses the default cache location. The `slow` allowlist `tests/slow_allowlist.txt` is test infrastructure, documented in its own header comment. The CHANGELOG line is owned by `vgus66`.

## Open questions

### OQ-01: Is it acceptable to run the heavy leaves on a seeded project instead of this repository?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from the tests' own assertions: `test_live_safe_leaves_exit_contract_membership_heavy` asserts only exit-code membership in the declared `exit_contract` on the human and `--agent` surfaces, and `test_no_color_scenario_is_plain_heavy_leaves` asserts only ANSI absence; neither reads this repository's records. The existing `scoped_repo_dir` comment ("verifies the emit contract without traversing this repository's full records tree") already made the same call for `doctor` and `check`. The seeded project is non-empty so leaves exercise their real render paths, and E-02's per-leaf outcome-class table (F-8) proves no leaf silently moves from a success path to a refusal.

### OQ-02: What if the target is missed after all items?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from the prompt (`4ul37x` "Never weaken an assertion to gain speed") and P16: the executor records the achieved median and the remaining top durations with justifications and stops rather than weakening assertions or deleting tests to hit the number; whether to accept the miss or open a follow-up is the maintainer's decision at review of this plan's evidence, so the executor reports the miss and does not decide it. (Owner corrected at review: no maintainer answer is recorded, so this is the author's resolution.)

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted three wall times and median, collected count, the top 50 call durations, the over-2s/5s/10s counts, sum of call durations, worker skew or tail floor, `percov_analyze` union line and arc totals with the baseline directory's `meta.json` HEAD, and the research section heading.
  - Observed evidence: Baseline recorded in `.aw/records/research/20261016-testprune-02-hwuvpx-test-prune-decision-table.assessment.md` section `## c8bfp9 baseline`. Uninstrumented wall times: Run 1 751.39s, Run 2 754.18s, Run 3 749.23s; Median: 751.39s. Collected count: 8610 tests. Sum of call durations: Run 1 4413.90s, Run 2 4397.76s, Run 3 4440.12s. Tail floor: 139.47s (`tests.test_exit_contract_conformance::test_live_safe_leaves_exit_contract_membership_heavy[doctor]`). Slow test census (Run 1): >2s: 637, >5s: 155, >10s: 41. Coverage: Statements covered 126,521/99,474 (82.81%), branches 165,372/40,572 (74.62%), git_head `88b0fda5825ba43662779d0585c0dcde0a70c7e5`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted before and after `--durations` lines for the `[doctor]` and `[partition]` node ids; the per-leaf `(exit, outcome)` table at `REPO_ROOT` versus the seeded project for both surfaces with zero class changes; the modules' summary lines; and a demonstration that an assertion still bites on the seeded project (temporarily remove the observed code from `doctor`'s declared `exit_contract` in `command_surface`, show `test_live_safe_leaves_exit_contract_membership_*[doctor]` fail, revert, empty `git diff -- agent_workflows/`).
  - Observed evidence: Before durations (Run 1 baseline): `139.47s call tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[doctor]`, `71.60s call tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_heavy_leaves[doctor]`, `1.24s call tests/test_agent_surface_conformance.py::test_agent_surface_conformance[partition]`. After durations (seeded project): `2.03s call tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[doctor]`, `1.07s call tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_heavy_leaves[doctor]`, `0.39s call tests/test_agent_surface_conformance.py::test_agent_surface_conformance[partition]`. Across all 63 switched leaves evaluated at REPO_ROOT versus seeded project on both human and agent surfaces, zero outcome class changes occurred (100% preservation). Conformance modules summary line: `465 passed in 55.31s`. Bite demonstration: temporarily modified `command_surface.py` to remove `1` from `doctor`'s `exit_contract=(0, 2)`; observed `FAILED tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[doctor]` with `AssertionError: leaf='doctor', surface='human', observed_rc=1, declared=(0, 2)`; reverted edit; confirmed empty `git diff -- agent_workflows/`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted re-measured per-leaf times for `doctor`, `attention`, `status` on the seeded project (with `AW_CONFIG_DIR` unset and sandboxed `AW_HOME`), the diff of the marks and the `LIVE_HEAVY_LEAVES` comment, and the subset test's pass line.
  - Observed evidence: Re-measured per-leaf timings on seeded project (`AW_CONFIG_DIR` unset, sandboxed environment): `doctor` human 0.986s, agent 0.942s; `attention` human 0.384s, agent 0.365s; `status` human 0.416s, agent 0.419s. All under 1.0s. Removed `@pytest.mark.slow` and `@pytest.mark.timeout(500)` from heavy tests in `tests/test_exit_contract_conformance.py` and `tests/test_live_conformance_sweep.py`. Updated `LIVE_HEAVY_LEAVES` comment in `tests/conformance_matrix.py`. Subset test: `tests/test_exit_contract_conformance.py::test_live_heavy_leaves_is_subset_of_safe_leaves PASSED`.
  - Result: pass
- [ ] V-04 validates E-04
  - Required evidence: pasted `tests/test_conformance_inproc.py` pass lines under pytest (seed) and under `python3 -m unittest tests.test_conformance_inproc`, and the test source showing the parity, restore-after-raise and `NO_COLOR` assertions.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: pasted list of converted modules per commit group, the kept-subprocess list with reasons, any `run_cli` versus `run_cli_inproc` difference found and its disposition, two shuffled runs of converted modules (seeds and summary lines), and before and after module durations.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted host-binary spawn list with dispositions, list of mocked seams by symbol, and before and after durations for affected `doctor`/`checkup` tests (reverted items shown reverted).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted before and after durations for the four `test_installer.py` tests named in E-06 and other converted modules, the template digest before and after a module run (equal), and the modules' summary lines under `-n 6` (seed) and, for `TestCase` modules, `python3 -m unittest`.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted per-site disposition table (one row per `time.sleep(` site re-derived by `rg -n` at execution, count stated) and before and after durations of converted tests, with the unchanged threshold values for any timing-behavior test.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted before and after durations for each item-listed test, the shard-union test's pass line and its source showing the union-equals-list and disjointness assertions, warm and cold `mypy` gate durations with the chosen cache location, and the list of tests still above 15s or above one sixth of the median, each with its E-09 justification.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted `tests/test_slow_report.py` pass line and source (unlisted slow test named and exit 0; listed one not named), the allowlist row count next to the over-2s count from the V-10 runs (equal), and the report section of one full run showing zero unlisted tests.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: pasted three full-run summary lines with wall times and the median (under 120s, or the OQ-02 miss report), `--durations=20`, the collected-count reconciliation against V-01 (added tests listed, split ids mapped, zero E-01 ids missing), `percov_analyze --compare` output with zero lost lines and arcs, the `core_measure` comparison, three randomized run summary lines with seeds, and the bare `python3 -m pytest` summary line with the core budget guard passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and explicit human approval (all open questions resolved), and only after `83nnyn` is executed (Item-Dependencies), in an isolated worktree (`aw work begin c8bfp9`, or the runner's lane). Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is allowed when needed and justified at finalize (`--scope-reason`), and a declared but unmodified path is acknowledged (`--scope-ack`; `.gitignore` and `pyproject.toml` are declared only for E-08's mypy cache and E-03's marker text). This plan changes no production code: every temporary mutation under `agent_workflows/` is reverted and shown reverted with an empty `git diff -- agent_workflows/`. Never weaken an assertion, raise a threshold, or delete a test to gain speed; a change that cannot keep every assertion is reverted. Respect `hguae9`'s `core` marker and budget guard: add or remove no `core` mark. Run every measurement with `AW_CONFIG_DIR` unset (F-7). Commit each item (or E-11 module group) via `aw commit c8bfp9 -- <paths>` (never `git add -A`); never push or tag. You MUST paste the ACTUAL runner output in each V-item; never claim a pass or a timing you did not run. Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the move to `executed/`; executed by hand, finish with `aw ipd lint --phase pre-transition` conforming and then `aw ipd finalize c8bfp9` (never a hand `git mv`), and publish with `aw integration-lock -- git merge --ff-only <branch>`.
