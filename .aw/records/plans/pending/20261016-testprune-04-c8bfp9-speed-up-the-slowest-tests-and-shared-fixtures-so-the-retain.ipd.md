# IPD: Speed up the slowest tests and shared fixtures so the retained full suite runs under 120 seconds

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `4ul37x` (Set `testprune`) SPEED UP section and its headline target: the FULL retained suite (`python3 -m pytest tests/ -m ''`) under 120s wall on 6 xdist workers. Baseline (research `7ry5kv`, `/tmp/opencode/testtier-full.log` `--durations=30`, main `eca2e2211`): 565.28s wall; the slowest 30 tests alone sum to 617.6s of worker time; the two slowest are `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership_heavy[doctor]` at 118.10s and `tests/test_live_conformance_sweep.py::test_no_color_scenario_is_plain_heavy_leaves[doctor]` at 64.25s, so the worst single test alone nearly equals the whole target and pins one worker's tail. Measured at authoring in this worktree: `aw partition -t plans -s approved --json` takes 28.1s to 30.7s when run with cwd at the repository (it walks this repository's full `.aw/records/` tree) but 0.40s in a minimal git repo with an empty `.aw/records/plans/`; `aw status` takes 9.8s at the repository; `aw doctor --agent` takes 0.62s in the minimal repo. So most of the heavy-leaf cost is the size of THIS repository's records corpus, which the exit-code, `--json`, `--fields`, `--agent` and NO_COLOR contracts do not depend on.
- Scope: After `83nnyn` has consolidated, (1) point conformance sweeps that do not assert on this repository's records at a seeded, session-built fixture project instead of `REPO_ROOT`; (2) replace subprocess `aw` invocations with in-process `agent_workflows.cli.main([...])` where the process boundary is not under test, keeping a small, named set of true subprocess smoke tests; (3) build installed-project and temp-repo templates once per session and copy per test; (4) replace real sleeps and wall-clock waits with injected clocks or shortened timeouts through existing parameters; (5) split remaining long tests so `--dist=worksteal` can balance; (6) record a justification for every test still over 2s. Never weakens an assertion; `livecorpus` tests stay and are sped up only by caching, never by narrowing their corpus.
- Scope-Paths: tests/, conftest.py, pyproject.toml, .aw/records/research/*testprune*
- Item-Dependencies: executed:83nnyn
- Status: to-review
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 4
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: c8bfp9

## Workflow history
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune) with baseline research offdhr/7ry5kv

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`python3 -m pytest tests/ -m ''` completes in under 120s wall (median of three warm runs, 6 workers, `--dist=worksteal`, `pytest-randomly` on) with no assertion weakened, and every test still over 2s carries a recorded justification.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Rule for every item: measure the targeted tests' `--durations` before and after and record both in the decision-table research; an item that does not reduce wall or tail time is reverted. Every converted test keeps the same assertions (exit code, record schema, field content, ANSI absence); if a conversion cannot preserve one, the test stays as it was.

### Task group 1: baseline

- [ ] E-01 At this child's starting commit (after `83nnyn`), run the full suite three times warm (`python3 -m pytest tests/ -m '' --durations=50`, uninstrumented) and record: collected count, the three wall times and median, `--durations=50`, and the per-worker finish skew (from `-v` worker ids or `--durations` grouped by worker if `pytest-xdist` reports it; otherwise the longest single test as the tail floor). Also record the slow-test census: count of tests over 2s, 5s and 10s.
  - Depends on: none
  - Expected outcome: baseline recorded in the decision-table research; this child's target arithmetic stated (sum of durations / 6 versus 120s).
  - Execution state: pending

### Task group 2: heavy conformance leaves off the live corpus

- [ ] E-02 Add a session-scoped seeded fixture project in `tests/conformance_matrix.py` (built once: `git init`, local identity, `aw install . --yes` via the existing `build_installed_project_template`, plus a small committed records set: one pending plan, one backlog item, one spec, one research record, so every leaf has non-empty input), and make `run_cli`/`run_cli_tty` callers in `tests/test_exit_contract_conformance.py` (`test_live_safe_leaves_exit_contract_membership_heavy`, `_cheap`), `tests/test_live_conformance_sweep.py` (`test_no_color_scenario_is_plain_heavy_leaves`, `_cheap_leaves`, help and usage sweeps), `tests/test_agent_surface_conformance.py::test_agent_surface_conformance` and `tests/test_shared_flag_honored.py` read tests use that project as `cwd` for every leaf, replacing the current `doctor`/`check`-only `scoped_repo_dir` special case. Tests that assert a property of THIS repository's records (the `livecorpus` marker, `TestLivePendingCorpus`) are untouched.
  - Depends on: E-01
  - Expected outcome: the `[doctor]` heavy tests drop from 118s and 64s to a few seconds; `[partition]` sweeps from about 23 to 27s to under 2s each; every leaf still asserts exit-code membership in `command_surface.get_declaration(leaf).exit_contract`, JSON parseability, schema-valid terminal records and ANSI absence.
  - Execution state: pending
- [ ] E-03 Re-measure `LIVE_HEAVY_LEAVES` (`doctor`, `attention`, `status`) against the seeded project; if each is now under 2s, fold them into the cheap parametrization and drop the `slow` mark and `timeout(500)` from the heavy variants (the heavy split exists only because of the measured live-tree cost recorded in the `LIVE_HEAVY_LEAVES` comment); update that comment with the new measurement.
  - Depends on: E-02
  - Expected outcome: heavy and cheap parametrizations merged or the remaining heavy members justified with a measurement; `LIVE_HEAVY_LEAVES` comment shows the new numbers.
  - Execution state: pending

### Task group 3: in-process instead of subprocess

- [ ] E-04 Introduce one in-process runner helper beside `run_cli` (`run_cli_inproc(argv, cwd=...)`: `monkeypatch.chdir`, `contextlib.redirect_stdout`/`redirect_stderr`, calls `agent_workflows.cli.main(argv)`, maps `SystemExit` to a return code, returns the same result shape as `run_cli`) following the existing `_capture_cli` in `tests/test_usage_refusal_agent_record.py`. Convert subprocess callers whose assertions are on exit code and stdout/stderr content only. Authoring census: 84 test modules launch `aw` via `run_cli` or `[sys.executable, "-m", ...]`, versus 107 that already call `cli.main(` in-process. Keep subprocess where the boundary IS under test: TTY/pty behavior (`run_cli_tty`), signal and exit-130 handling (`test_universal_130_floor_and_signal_code_exclusion`), environment and PYTHONPATH isolation, re-exec (`AW_NO_REEXEC`), import-time side effects, the installed console script and wheel build (`tests/test_installed_version_reporting.py`), and the hguae9 core smoke set. Record that kept set (node ids plus reason) in the research.
  - Depends on: E-03
  - Expected outcome: converted modules pass under `-n 6` with randomization; process-global state that leaks between in-process calls (cwd, env, `sys.argv`, logging handlers, module caches) is reset by the helper and demonstrated by running converted tests in a shuffled order twice.
  - Execution state: pending
- [ ] E-05 Mock host-binary and network probes at the boundary in tests that are not about the host (for example `opencode`, `agy`, `git` version probes and any HTTP or PyPI lookup reached from `doctor`/`checkup`), using the existing probe seams in production code where present; tests that ARE about the probe keep the real call. Record each mocked seam by symbol.
  - Depends on: E-04
  - Expected outcome: no test outside the host-probe modules spawns a host binary other than `git` and `python`; `--durations` for `checkup` and `doctor` tests drops.
  - Execution state: pending

### Task group 4: fixtures, clocks, balancing

- [ ] E-06 Cache expensive per-test setup: reuse `build_installed_project_template` plus `clone_isolated_project` (session template, per-test copy) for every test that runs `aw install` into a fresh temp repo (authoring census: 24 modules reference install into a project, including `tests/test_installer.py`, 144 node ids, module `slow`), and the `83nnyn` E-09 bare-repo template for git setup. Tests whose subject is the install itself (installer preservation and consent tables) keep installing, but share one template of the PRE-install state.
  - Depends on: E-04
  - Expected outcome: `tests/test_installer.py` (`test_every_existing_file_state_is_handled_without_clobbering` 18.5s, `test_gitignored_opencode_does_not_abort` 17.7s, `test_the_users_gitignore_is_managed_without_being_clobbered` 13.8s, `test_every_consent_mode_disposes_of_a_drifted_file_correctly` 11.2s) and other install-using modules show reduced durations.
  - Execution state: pending
- [ ] E-07 Remove real waits: replace `time.sleep` in test bodies (authoring census: 57 call sites in 42 files, including `time.sleep(60)` child processes in `tests/test_ipd_lifecycle_cli.py`, `tests/test_lane_owner_record_anchoring.py`, `tests/test_oc_runipd.py`, `time.sleep(10)` in `tests/test_stall_progress_agy.py` and `tests/test_capture_command_stream_bounds.py`, and `time.sleep(1.5)` in `tests/test_hang_guard_budget.py`) with injected clocks or the shortest timeout the code's existing parameters accept (for example `now=` parameters such as `suite_cache.prune_expired_records(now=...)`, `host_capability_registry` `is_expired(now=...)`, `run_viewer.parse_since_timestamp(now=...)`, `AW_TEST_WALL_TIMEOUT`). A sleeping child process used only as a long-lived pid to be killed is kept (it costs nothing once killed) and noted. Where no seam exists, do not add a production seam in this child; record the test as justified.
  - Depends on: E-01
  - Expected outcome: per-site disposition recorded (converted, kept-as-kill-target, justified); converted tests' durations drop; no timing assertion loosened.
  - Execution state: pending
- [ ] E-08 Split or speed the remaining long single tests so worksteal can balance: for example `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta` (24.2s, `livecorpus`: parametrize over corpus shards so the full corpus is still covered), `tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun` (20.2s), `tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit` (20.0s, runs `mypy agent_workflows`: enable mypy's incremental cache in a session-scoped cache dir, or justify), `tests/test_agy_runipd_cli.py::AgyFailClosedIntegrationGuardTests::test_the_MEASURED_INCIDENT_is_now_SURVIVED_defer_then_integrate` (17.8s), `tests/test_oc_runipd.py::EmptyReviewSweepExitsZeroTests::test_end_to_end_empty_sweep_cli` (16.8s), `tests/test_severity_truth_surfaces.py::test_attention_diagnostic_preserves_drift_severity_and_exit_code` (16.1s), `tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference` (15.2s), and the end-to-end runner tests at 10 to 15s (`test_runfresh_end_to_end`, `test_fix_it_global_caps`, `test_freeze_time_refusal`, `test_gradcover_end_to_end`, `test_agent_user_config_containment`). Corpus-wide shards must cover the same corpus as the original (shard union equals the full plan list, asserted).
  - Depends on: E-06, E-07
  - Expected outcome: no single test over 15s; the longest test is under one sixth of the achieved median wall time.
  - Execution state: pending

### Task group 5: justification and proof

- [ ] E-09 Record in the decision-table research a row for every test whose call duration is still over 2s in the E-10 runs: node id, duration, and the compelling reason (subprocess boundary under test, real pty, real signal, wheel build, corpus property, etc.). Add a non-failing report in `conftest.py` (`pytest_terminal_summary`, controller only) that lists tests over 2s not present in a small allowlist file under `tests/`, so a new slow test is visible; it warns and never fails, because wall time varies by host.
  - Depends on: E-08
  - Expected outcome: every over-2s test is in the allowlist with a reason; a run with a temporary `time.sleep(3)` test shows the warning naming it; revert leaves an empty diff.
  - Execution state: pending
- [ ] E-10 Prove: three warm full runs `python3 -m pytest tests/ -m '' --durations=20` (median under 120s), collected count equal to E-01's (this child deletes nothing), full union line and branch coverage equal to or above the E-01 measurement (in-process conversion should raise recorded coverage), hguae9 core tier still passes its budget guard, and three randomized runs (`-p randomly`, distinct seeds) pass.
  - Depends on: E-09
  - Expected outcome: median under 120s; zero failures across the randomized runs; coverage not lower.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/conformance_matrix.py` owns the live CLI helpers (`run_cli`, `run_cli_tty`, `LIVE_SAFE_LEAVES`, `LIVE_HEAVY_LEAVES`, `live_cheap_leaves`, `RUNNABLE_ARGV`, `build_installed_project_template`, `clone_isolated_project`); `run_cli` runs `[sys.executable, "-m", "agent_workflows", *argv]` with cwd defaulting to `REPO_ROOT`, which is why heavy leaves walk this repository's records corpus.
- `LIVE_HEAVY_LEAVES` comment records per-invocation costs at high concurrency (doctor about 407s, attention about 48.5s, status about 37.7s); the heavy split is a cost workaround, not a contract.
- `tests/test_shared_flag_honored.py` and `tests/test_agent_surface_conformance.py` already define a session `scoped_repo_dir` for `doctor` and `check` only (F-2 below generalizes it).
- `conftest.py` owns the xdist worker cap (`pytest_xdist_auto_num_workers`, min(6, cpus/2)) and the hang guard (`AW_TEST_TIMEOUT`, `AW_TEST_WALL_TIMEOUT` default 240s); `pytest-randomly` stays on (pyproject comment).
- hguae9 owns the `core` marker and a 30s core budget guard; this child must not move tests out of `core` or slow it.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | 565s wall; slowest 30 tests sum to 617.6s worker time; top test 118.1s | `/tmp/opencode/testtier-full.log` `--durations=30`; research `7ry5kv` |
| F-2 | `partition` costs 28 to 31s at the repository and 0.40s in a minimal repo; `status` 9.8s at the repository; `doctor --agent` 0.62s in a minimal repo | authoring timings in this worktree |
| F-3 | Heavy and partition conformance tests use cwd `REPO_ROOT` except `doctor`/`check` in two modules | `run_cli` default cwd; `cwd = scoped_repo_dir if leaf in ("doctor", "check")` in both modules |
| F-4 | 84 modules launch `aw` as a subprocess; 107 already use `cli.main(` in-process | `rg -l` counts at authoring |
| F-5 | 57 `time.sleep(` sites in 42 test files | `rg` count at authoring |
| F-6 | 24 modules install into temp projects; `test_installer.py` has 144 node ids and four tests over 11s | `rg -l`, collection, durations |

## Proposed changes (ordered, validatable)

E-01 baseline -> E-02/E-03 heavy leaves off the live corpus (largest single win, about 180s of tail removed) -> E-04/E-05 in-process conversion and probe mocking -> E-06 cached templates -> E-07 clocks -> E-08 split long tests -> E-09 justification report -> E-10 proof. One `aw commit c8bfp9 -- <paths>` per item.

## Deferred / out of scope (with reason)

- Adding new production clock or probe seams where none exists: production changes are outside this test-only Set; tests without a seam are justified in E-07/E-09 instead.
  - Carrier-Declined: the prompt `4ul37x` says "shortening timeouts through existing parameters"; a needed seam would be a separate backlog item filed by the executor if the justification list shows it pays off.
- Final whole-Set before/after report, mutation spot-check, flake check, CHANGELOG line.
  - Carrier: vgus66
- Speeding the core tier itself or changing its membership.
  - Carrier: hguae9

## Scope check

- Over-scope: none.
- Under-scope: none. Running conformance sweeps on a seeded project changes WHICH tree a leaf reads, not what is asserted; the property "the leaf behaves on THIS repository's real records" is owned by `livecorpus` tests, which are untouched.

## Required tests / validation

Per item: the touched modules under `-n 6` with randomization and `--durations`. At the end: E-10's three full runs, coverage, and bare `python3 -m pytest` (core), all pasted.

## Spec / documentation sync

N/A: no spec governs test runtime. `pyproject.toml` comments are updated only if a marker (`slow`) description changes in E-03. The CHANGELOG line is owned by `vgus66`.

## Open questions

### OQ-01: Is it acceptable to run the heavy leaves on a seeded project instead of this repository?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from the tests' own assertions: `test_live_safe_leaves_exit_contract_membership_heavy` asserts only exit-code membership in the declared `exit_contract` on the human and `--agent` surfaces, and `test_no_color_scenario_is_plain_heavy_leaves` asserts only ANSI absence; neither reads this repository's records. The existing `scoped_repo_dir` comment ("verifies the emit contract without traversing this repository's full records tree") already made the same call for `doctor` and `check`. The seeded project is non-empty so leaves exercise their real render paths.

### OQ-02: What if the target is missed after all items?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: The executor records the achieved median and the remaining top durations with justifications and stops rather than weakening assertions or deleting tests to hit the number; whether to accept the miss or open a follow-up is the maintainer's decision at review of this plan's evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted three wall times and median, collected count, `--durations=50` head, and the over-2s/5s/10s counts.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted before and after `--durations` lines for the `[doctor]` and `[partition]` node ids, the modules' summary lines, and a demonstration that an assertion still bites (temporarily add an undeclared exit code path or remove a code from one leaf's declared `exit_contract`, show the failure, revert with empty diff).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted re-measured per-leaf times for `doctor`, `attention`, `status` on the seeded project, and the diff of the marks and the `LIVE_HEAVY_LEAVES` comment.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted list of converted modules, the kept-subprocess list with reasons, two shuffled runs of converted modules (seeds and summary lines), and before and after module durations.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted list of mocked seams by symbol and before and after durations for affected `doctor`/`checkup` tests.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted before and after durations for the four `test_installer.py` tests named in E-06 and the module summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted per-site disposition table (57 rows or the measured count) and before and after durations of converted tests.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted before and after durations for each named test, and for corpus shards the assertion output showing shard union equals the full plan list.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted allowlist row count equal to the over-2s count from V-10, and the warning output naming a temporary 3s test, followed by the revert's empty `git diff`.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: pasted three full-run summary lines with wall times (median under 120s), `--durations=20`, collected count equal to V-01, union line and branch coverage before and after, three randomized run summary lines with seeds, and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and explicit human approval, and only after `83nnyn` is executed. Work in an isolated worktree via `aw work begin c8bfp9`; commit each item with `aw commit c8bfp9 -- <paths>`; never push or tag; publish via `aw integration-lock -- git merge --ff-only <branch>`. Paste ACTUAL runner output in every V-item. On completion run `aw ipd lint --phase pre-transition` and move the plan to `executed/` through the lifecycle tooling.
