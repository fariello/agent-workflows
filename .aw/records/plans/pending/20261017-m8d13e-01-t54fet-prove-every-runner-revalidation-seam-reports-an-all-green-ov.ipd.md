# IPD: Prove every runner revalidation seam reports an all-green over-budget tree as green

- Date: 2026-10-17
- Kind: child
- Concern: Backlog `m8d13e` reports that the core-tier wall-time budget in the root `conftest.py` turned all-green suites into exit 1 under host load, so the runner's post-merge revalidation reported RED with no failing test ids and refused integration of correct lanes. The runner-side demotion shipped in commit `8b798b0b8` (backlog `ytz6z4`) and is regression-tested only on `suite_cache.run_full_suite` called directly; the three runner seams that actually produce the refusal (`runner_shared.run_suite_check`, the concurrent baseline `runner_shared.start_suite_baseline` which shells out to `aw suite`, and the post-merge `runner_shared.make_integration_validation_runner`) have no test proving an all-green over-budget tree stays green through them, so a later refactor of any one seam can silently reintroduce the exact `m8d13e` symptom.
- Scope: Add one new behavioral test module that drives each of the three runner seams against a throwaway git fixture repository whose only test passes but always overruns a deliberately tiny core-tier budget, asserting the seam reports green with the budget at its default (unset) enforcement, plus a positive control per seam proving the fixture really trips the budget when enforcement is explicitly requested (so the green results are not vacuous). It does NOT change production code, the 30s budget value, core-marker membership, the bare-`pytest` enforcement rule (carried by plan `44nfmd`), or the send-back wording (also `44nfmd`).
- Scope-Paths: tests/test_runner_seams_core_budget.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: m8d13e
- Blocks-Release: next
- Set: m8d13e
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: t54fet
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-17 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog m8d13e with Step 0 evidence; review-ready.

## Goal

Make the `m8d13e` fix provable at the layer where the defect was observed: every runner seam that decides whether a merged or baseline tree is green must report an all-green tree as green even when the core-tier wall-time budget is overrun, and a regression in any seam must fail a named test rather than reappear as an unexplained "no test ids recorded" refusal during an unattended run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: fixture

- [x] E-01 Create `tests/test_runner_seams_core_budget.py` (NOT `core`-marked: it launches several pytest subprocesses and belongs in the explicit-path and thorough tiers, not the 30s core tier). Add a fixture helper `_over_budget_repo(path)` that `git init`s a repository (configure `user.name`/`user.email` locally, as `tests/test_suite_cache.py::_init_fixture_repo` does), writes a `pytest.ini` (`[pytest]`, `addopts = -q`, `testpaths = tests`), a `.gitignore` (`.pytest_cache/`, `__pycache__/`), one passing test `tests/test_ok.py` that sleeps 0.05s, and a fixture-local `conftest.py` (its own `pytest_sessionstart` records `time.perf_counter()`) whose controller-only `pytest_sessionfinish(trylast=True)` reproduces the root `conftest.pytest_sessionfinish` ENFORCEMENT RULE verbatim in effect: skip when `PYTEST_XDIST_WORKER` is set; budget from `AW_CORE_BUDGET_SECONDS` (default 30.0); on overrun write a banner containing `CORE TIER BUDGET EXCEEDED` to stderr and set `session.exitstatus = 1` only when `int(AW_TEST_CPU_COUNT or os.cpu_count())>=12` and `AW_CORE_BUDGET_ENFORCE != "0"`, else write the `WARNING:` banner. The fixture conftest deliberately has NO core-filter gate, because the seams append `-n <workers>` through `suite_cache.build_suite_child_env` and the toy project has no xdist relay of `_core_filter_applied` (the reason the existing `ytz6z4` test needed `-n 0`, see its docstring). `git add -A` and commit every fixture file inside the fixture repo (this is the throwaway repo's own commit; nothing is committed to this checkout here). Add an env helper mirroring `tests/test_suite_cache.py::_fixture_env` (`AW_NO_REEXEC=1`, `PYTHONPATH` = this checkout, pop `PYTEST_ADDOPTS`, `PYTEST_CURRENT_TEST`, `PYTEST_XDIST_WORKER`, `AW_TEST_TIER`) that additionally sets `AW_CORE_BUDGET_SECONDS=0.01` and `AW_TEST_CPU_COUNT=12` and removes `AW_CORE_BUDGET_ENFORCE` unless a test passes it explicitly. APPLY IT SO THE POPPED KEYS ARE REALLY ABSENT: use `mock.patch.dict(os.environ, <helper result>, clear=True)` (or `monkeypatch.setenv` plus `monkeypatch.delenv(..., raising=False)` for each removed key). `patch.dict(..., clear=False)` only adds and overwrites keys and never removes one, so under xdist (the thorough tier's `-n auto`) the test process's own `PYTEST_XDIST_WORKER` would leak into every child, the fixture hook would return early, every green test would pass vacuously and every control would fail. Measured at review with a prototype of this fixture: with `clear=False` and `PYTEST_XDIST_WORKER=gw0` in the parent, the seam-1 control returned `passing True exit 0`; with `clear=True` it returned `passing False exit 1 failures ()`. Each test builds its OWN fixture repo under `tmp_path`, because the suite cache key (`suite_cache.SUITE_KEY_ENV_VARS`) does not include `AW_CORE_BUDGET_ENFORCE`, so a PASS cached by one test would otherwise be served to the next and make its assertion vacuous.
  - Depends on: none
  - Expected outcome: a reusable over-budget fixture whose bare run with `AW_CORE_BUDGET_ENFORCE=1` exits 1 with zero failing tests, and with the variable unset under a seam exits 0.
  - Execution state: performed

### Task group 2: one test pair per seam

- [x] E-02 Seam 1, the integration gate check. Add `test_run_suite_check_green_on_all_green_over_budget_tree`: with the fixture env applied as E-01 requires (popped keys really absent) and `AW_CORE_BUDGET_ENFORCE` absent, call `runner_shared.run_suite_check(repo, "run-m8d13e01")` and assert `passing is True`, `exit_code == 0`, `cached is False` (proves an observed run, not a served cache record), and that `os.environ` has no `AW_CORE_BUDGET_ENFORCE` afterwards (the run-evidence path restores it). Add the positive control `test_run_suite_check_red_when_enforce_requested` on a fresh repo with `AW_CORE_BUDGET_ENFORCE=1` in the environment: assert `passing is False`, `exit_code == 1` and `failures == ()`, which is exactly the zero-ids RED shape `m8d13e` reported.
  - Depends on: E-01
  - Expected outcome: both tests pass; the control proves the fixture trips the budget, so the green assertion is meaningful.
  - Execution state: performed

- [x] E-03 Seam 2, the concurrent pre-work baseline (the seam behind the `m8d13e` "base commit 130s" measurement). Add `test_suite_baseline_green_on_all_green_over_budget_tree`: under the same environment, read the fixture HEAD with `git rev-parse HEAD`, call `runner_shared.start_suite_baseline(repo, id6="m8d13e", attempt=1, base_commit=<head>, argv=list(runner_shared.SUITE_CHECK_ARGV), extract_failures=runner_shared.extract_suite_failures, parse_summary=runner_shared.parse_suite_summary)` (the same call `tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun` makes, which rewrites the argv to `python -m agent_workflows suite --agent --no-serve-failures`), collect with `wait_seconds=120.0` inside `try`/`finally` that calls `runner_shared.remove_suite_baseline_checkout`, and assert `state == runner_shared.SUITE_BASELINE_COMPLETED`, `exit_code == 0` and `failures == ()`. Add the positive control on a fresh repo with `AW_CORE_BUDGET_ENFORCE=1`: assert `exit_code != 0` and `failures == ()`.
  - Depends on: E-01
  - Expected outcome: both tests pass; the baseline seam reports a green base commit as green under an overrun.
  - Execution state: performed

- [x] E-04 Seam 3, post-merge revalidation, the seam whose RED became the "combined-red, no test ids recorded" refusal. Add `test_post_merge_revalidation_green_on_all_green_over_budget_tree`: build `state = {"repo": str(repo), "run_id": "run-m8d13e03", "options": {"validate": False}}` and `item = {"id6": "m8d13e", "base_commit": <head>, "lane_head": <head>, "attempts": []}` and a `run_dir` under `tmp_path`, exactly as the existing seam test does; call `runner_shared.make_integration_validation_runner(state, run_dir, item, suite_check=runner_shared.run_suite_check)("", ["tests/test_ok.py"])` and assert it returns `True` and that `item["post_merge_revalidation"]["passed"] is True`. Add the positive control on a fresh repo with `AW_CORE_BUDGET_ENFORCE=1`: assert the runner returns `False`, the recorded `passed` is `False`, and the recorded `failures` is empty, reproducing the `m8d13e` record shape.
  - Depends on: E-01
  - Expected outcome: both tests pass; the post-merge revalidation record of an all-green over-budget merged tree says passed.
  - Execution state: performed

### Task group 3: run and record

- [x] E-05 Run the new module explicitly, serially (`python3 -m pytest -o addopts="" -v tests/test_runner_seams_core_budget.py`) AND under workers (`python3 -m pytest -o addopts="" -n 2 -v tests/test_runner_seams_core_budget.py`, which proves the env helper really strips `PYTEST_XDIST_WORKER`), the neighbouring contracts unchanged (`python3 -m pytest tests/test_core_tier_selection.py tests/test_suite_cache.py`), the bare core tier `python3 -m pytest`, and `aw sanitize --agent`. If any GREEN-case test fails because a seam really does report RED, do NOT weaken the test and do NOT edit production code under this plan (it is outside `- Scope-Paths:`): set this item and the failing seam's E-item to `blocked`, record the failing seam and its output, and report it as a live regression of `ytz6z4` needing a corrective plan.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: six new tests pass; existing files pass unchanged; core tier green; sanitizer pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The enforcement rule lives in `conftest.pytest_sessionfinish` (docstring "Enforce the wall-time budget on the core tier (IPD hguae9 E-05)"): it reads `AW_CORE_BUDGET_SECONDS` (default 30.0), `AW_TEST_CPU_COUNT`, and fails only when `cpu_count >= 12 and AW_CORE_BUDGET_ENFORCE != "0"`; it returns early on xdist workers and when `_core_filter_applied` is not set.
- `suite_cache.build_suite_child_env` carries the `ytz6z4` demotion: `base.setdefault(AW_CORE_BUDGET_ENFORCE_ENV, "0")`, and `run_full_suite`'s run-evidence branch mirrors it into `os.environ` and restores it in a `finally`. It also appends `-n <workers>` to `PYTEST_ADDOPTS`, which is why the fixture conftest must not depend on a core-filter flag relayed from workers.
- `runner_shared.run_suite_check` calls `suite_cache.run_full_suite(repo_dir, argv=list(SUITE_CHECK_ARGV), use_cache=True, serve_failures=False, ..., run_id=run_id)`, i.e. the run-evidence branch.
- `runner_shared.start_suite_baseline` rewrites a bare `python -m pytest` argv to `python -m agent_workflows suite --agent --no-serve-failures` and launches it via `SuiteBaselineRun` with a copy of `os.environ`, so the baseline reaches `run_full_suite` through the `aw suite` CLI (`cli.py`, the `_sc.run_full_suite(` call), and therefore through `build_suite_child_env` as well.
- `runner_shared.make_integration_validation_runner(state, run_dir, item, suite_check=...)` records `item["post_merge_revalidation"]` with `passed`, `failures`, `cached`, `digest`; the existing seam test `tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun` drives all three seams on a fixture repo and is the shape to copy.
- `suite_cache.SUITE_KEY_ENV_VARS` lists `AW_EXECUTION_ROLE`, `AW_NO_REEXEC`, `FORCE_COLOR`, `NO_COLOR`, `PYTEST_ADDOPTS`, `PYTHONPATH`, `TERM`; `AW_CORE_BUDGET_ENFORCE` is not part of the cache key, hence one fixture repo per test.
- A budget-only RED is never cached: `run_full_suite` stores a failure only after `_confirm_failing_node_ids` re-runs extracted node ids, and a budget-only red has none.
- Review prototype (scratch under gitignored `.aw/state/review-t54fet/`, HEAD `4e7e2aea5`) of exactly this fixture and these calls, env applied with `clear=True`: unset enforcement -> seam 1 `passing True exit 0 cached False`, `AW_CORE_BUDGET_ENFORCE` absent afterwards; seam 2 `completed exit 0 failures ()`; seam 3 `True`, `passed True`. With `AW_CORE_BUDGET_ENFORCE=1` -> seam 1 `passing False exit 1 failures ()`; seam 2 `completed exit 1 failures ()`; seam 3 `False`, `passed False`, `failures []` (its reason also names a `not-started` baseline, which does not change the asserted shape). Each call took about 2 to 4s; the outer checkout's `git status` was unchanged.
- Tests must assert observable behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); this module calls the seams and asserts on their returned results and recorded state, never on source text.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The `m8d13e` symptom (RED, no ids, refused green lane) is produced by the runner seams, not by bare pytest | backlog `m8d13e` summary; send-back text "no test ids recorded" built in `runner_shared` beside the `combined-red-sent-back` event |
| F-2 | The runner-side fix already shipped, three minutes after `m8d13e` was filed | `git log`: `0c29be0b8` (file `m8d13e`) 2026-10-16 21:17, `8b798b0b8` (ytz6z4 fix) 21:20; `8b798b0b8` is an ancestor of this lane's HEAD |
| F-3 | That fix's regression tests exercise `run_full_suite` directly only | `tests/test_core_tier_selection.py::test_gate_suite_passes_an_all_green_over_budget_tree` (subprocess and run-evidence ids) and `::test_gate_suite_honors_explicit_enforce`; no test drives `run_suite_check`, `start_suite_baseline` or `make_integration_validation_runner` over an over-budget tree |
| F-4 | The baseline seam reaches the demotion by a different route (the `aw suite` CLI subprocess) than the gate seams (in-process run-evidence), so one test on `run_full_suite` does not cover it | `runner_shared.start_suite_baseline` argv rewrite; `SuiteBaselineRun.__init__` `child_env = dict(os.environ)` |
| F-5 | The bare-pytest half and the explanation half of this defect are already planned | pending plan `44nfmd` (Set `48hjbx`) lists `m8d13e` among the duplicates it carries |

## Proposed changes (ordered, validatable)

1. E-01: over-budget fixture repo and env helper.
2. E-02 to E-04: a green test and a positive control for each runner seam.
3. E-05: run and record.

## Deferred / out of scope (with reason)

- Load-aware enforcement for bare `python3 -m pytest`, a budget-only reason in `suite_cache`, and replacing the "no test ids recorded" send-back text: already designed in pending plan `44nfmd`; duplicating it here would put two plans on the same lines of `conftest.py`, `suite_cache.py` and `runner_shared.py`.
  - Carrier: 44nfmd
  - Carrier-Evidence: .aw/records/plans/executed/20261017-48hjbx-01-44nfmd-make-the-core-tier-wall-time-budget-load-aware-and-name-a-bu.ipd.md
- Adding `AW_CORE_BUDGET_ENFORCE` to `suite_cache.SUITE_KEY_ENV_VARS` so an explicit-enforce caller is never served a PASS cached under the default demotion: the budget is a load-dependent property and not a property of the tree, which is the ruling `ytz6z4` shipped, so serving that PASS is consistent with the gate's question; the only explicit-enforce test (`test_gate_suite_honors_explicit_enforce`) uses `use_cache=False`.
  - Carrier-Declined: not a defect under the `ytz6z4` ruling; nothing is left unfixed for `m8d13e`.
- Changing the 30s budget value or core membership: deliberate design of executed plan `hguae9`; this bug is about load, not the budget value.
  - Carrier-Declined: deliberate design, not a defect.

## Scope check

- Over-scope: none; one new test file.
- Under-scope: none; every runner seam that decides green-or-red for integration (gate check, baseline, post-merge revalidation) gets a green test and a positive control, and the remaining surfaces of the defect are carried by `44nfmd`.

## Required tests / validation

- New `tests/test_runner_seams_core_budget.py` (six tests), unchanged `tests/test_core_tier_selection.py` and `tests/test_suite_cache.py`, the bare core tier, and `aw sanitize --agent`. Actual runner output must be pasted in each `V-*`.

## Spec / documentation sync

- N/A: no `.spec.md` governs the core-tier budget (the rule lives in plan `hguae9`, `pyproject.toml` and `CONTRIBUTING.md`), and this plan adds tests only, with no user-visible behavior change, so no doc or CHANGELOG line is warranted.

## Open questions

### OQ-01: Is a tests-only plan the right graduation of a bug whose fix already shipped?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, resolved from repository evidence. The production fix for the runner path is `8b798b0b8` (F-2) and the remaining production changes are carried by `44nfmd` (F-5), so the uncovered part of `m8d13e` is proof at the seams where the symptom appeared (F-3, F-4). A second production change here would duplicate `44nfmd` on the same lines.

### OQ-02: Should the new module be in the core tier?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. It launches six pytest suites (one through the `aw suite` CLI and a detached worktree), and the core tier has a 30s budget (`conftest.pytest_sessionfinish`) that this very defect shows is tight under load. Explicit-path runs, `make test-all` and CI's thorough tier cover it, matching the AGENTS.md repo-local "HOW TO RUN THE SUITE" tiering.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git diff --stat` showing only `tests/test_runner_seams_core_budget.py` added, and pasted output of a manual bare run of the fixture produced by `_over_budget_repo` (from a short `python3 -c` driver that builds it under a `tempfile.mkdtemp()` directory, run with a clean env that has no `PYTEST_XDIST_WORKER`) with `AW_CORE_BUDGET_SECONDS=0.01 AW_TEST_CPU_COUNT=12 AW_CORE_BUDGET_ENFORCE=1 python3 -m pytest -p no:cacheprovider` showing `1 passed`, the `CORE TIER BUDGET EXCEEDED` banner and exit status 1 (code path: the fixture conftest's `pytest_sessionfinish`, created by E-01).
  - Observed evidence:
```
 tests/test_runner_seams_core_budget.py | 215 +++++++++++++++++++++++++++++++++
 1 file changed, 215 insertions(+)
```
Manual bare fixture run:
```
EXIT STATUS: 1
STDOUT:
.                                                                        [100%]
1 passed in 0.07s

STDERR:

================================ CORE TIER BUDGET EXCEEDED ================================
Core tier wall time: 0.08s exceeded budget of 0.01s.
===========================================================================================
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted `-v` lines for `test_run_suite_check_green_on_all_green_over_budget_tree` and `test_run_suite_check_red_when_enforce_requested` both PASSED (code path: `runner_shared.run_suite_check` -> `suite_cache.run_full_suite` run-evidence branch).
  - Observed evidence:
```
tests/test_runner_seams_core_budget.py::test_run_suite_check_green_on_all_green_over_budget_tree PASSED [ 83%]
tests/test_runner_seams_core_budget.py::test_run_suite_check_red_when_enforce_requested PASSED [ 66%]
```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `-v` lines for the baseline green test and its positive control both PASSED (code path: `runner_shared.start_suite_baseline` -> `SuiteBaselineRun` -> `aw suite` -> `suite_cache.run_full_suite`).
  - Observed evidence:
```
tests/test_runner_seams_core_budget.py::test_suite_baseline_green_on_all_green_over_budget_tree PASSED [100%]
tests/test_runner_seams_core_budget.py::test_suite_baseline_red_when_enforce_requested PASSED [ 50%]
```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted `-v` lines for the post-merge revalidation green test and its positive control both PASSED (code path: `runner_shared.make_integration_validation_runner` -> `runner_shared.run_suite_check`).
  - Observed evidence:
```
tests/test_runner_seams_core_budget.py::test_post_merge_revalidation_green_on_all_green_over_budget_tree PASSED [ 16%]
tests/test_runner_seams_core_budget.py::test_post_merge_revalidation_red_when_enforce_requested PASSED [ 33%]
```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted final summary lines of BOTH explicit new-module runs (serial and `-n 2`), each with the six tests passed and 0 failed, the summary line of the `tests/test_core_tier_selection.py tests/test_suite_cache.py` run with zero failed, the `N passed` summary line of the bare `python3 -m pytest` run with zero failed, and the `aw sanitize --agent` result record with status pass.
  - Observed evidence:
```
Serial new-module run:
============================== 6 passed in 14.60s ==============================

Parallel (-n 2) new-module run:
============================== 6 passed in 16.14s ==============================

Neighbouring contracts (tests/test_core_tier_selection.py tests/test_suite_cache.py):
28 passed in 37.75s

Bare core tier / full suite summary:
993 passed in 75.23s (0:01:15)
(and aw suite: 993 passed in 34.63s; AW_CORE_BUDGET_ENFORCE=0 python3 -m pytest: 993 passed in 40.75s)

Sanitizer (aw sanitize --agent):
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5882,"findings":0,"evidence":["leak-scan"],"next":null}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Follow the execution contract in AGENTS.md: commit only `tests/test_runner_seams_core_budget.py` through `aw commit t54fet -- tests/test_runner_seams_core_budget.py`, never push, and paste actual test output into each `V-*`. A green-case failure is a live regression to report (E-05), never a reason to weaken a test. Move the plan to `.aw/records/plans/executed/` only through `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms.
