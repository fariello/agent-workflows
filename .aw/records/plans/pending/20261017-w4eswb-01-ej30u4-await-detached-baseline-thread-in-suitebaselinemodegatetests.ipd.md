# IPD: await detached baseline thread in SuiteBaselineModeGateTests to eliminate xdist timeout

- Date: 2026-10-17
- Kind: child
- Concern: test suite baseline mode gate timeout under xdist CPU contention
- Scope: tests/test_suite_baseline_mode_gate.py
- Scope-Paths: tests/test_suite_baseline_mode_gate.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: w4eswb
- Set: w4eswb
- Order: 1
- Highest E allocated: 02
- Author: Gabriele Fariello <gabriele.fariello@gmail.com>
- Id: ej30u4

## Workflow history

- 2026-10-18 reviewed (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-17 draft (Gabriele Fariello <gabriele.fariello@gmail.com>): created via `aw ipd scaffold --from-backlog w4eswb`.
- 2026-10-17 to-review (Gabriele Fariello <gabriele.fariello@gmail.com>): authored review-ready plan to replace fixed sleep with active baseline drain join in SuiteBaselineModeGateTests and remove xfail quarantine.

## Goal

Eliminate test flakiness and timeouts in `SuiteBaselineModeGateTests.test_validation_off_starts_and_collects_suite_baseline` under pytest-xdist CPU contention by replacing the fragile fixed 50ms `time.sleep(0.05)` yield with a deterministic wait on the started `SuiteBaselineRun._drain` thread, and remove the `@pytest.mark.xfail` quarantine decorator.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Test harness synchronization and unquarantine

- [ ] E-01 In `tests/test_suite_baseline_mode_gate.py`:
  1. Update `SuiteBaselineModeGateTests._fake_oc_agent_commits_in_worktree` to accept an optional `active_baselines: list[runner_shared.SuiteBaselineRun] | None = None` parameter and remove `time.sleep(0.05)` (and its "Short yield" comment), instead iterating over `active_baselines or []` and joining each baseline's `_drain` thread with a bounded timeout (`b_run._drain.join(timeout=10.0)`). Callers that pass nothing (`test_validation_on_skips_suite_baseline`) then wait for nothing.
  2. In `SuiteBaselineModeGateTests.test_validation_off_starts_and_collects_suite_baseline`:
     - Remove the `@pytest.mark.xfail(strict=False, reason="flaky: w4eswb - timing out under xdist CPU contention")` quarantine decorator.
     - Capture `original_start = runner_shared.start_suite_baseline` BEFORE patching, define a wrapper `tracking_start(*args, **kwargs)` that calls `original_start(*args, **kwargs)`, appends the returned run to a local `active_baselines` list when it is not `None`, and returns the `(run, absent)` tuple unchanged; install it with `mock.patch.object(runner_shared, "start_suite_baseline", side_effect=tracking_start)` inside the existing `with (...)` block. Patching the `runner_shared` module global is what intercepts the call, because `execute_item_core` calls the bare name `start_suite_baseline` (`agent_workflows/runner_shared.py:41337`, `suite_baseline_run, suite_baseline = start_suite_baseline(`). Capturing the original first is required: calling `runner_shared.start_suite_baseline` from inside the wrapper while the patch is live would recurse into the mock.
     - Pass the tracked list to `_fake_oc_agent_commits_in_worktree(run_dir, active_baselines=active_baselines)` so the fake agent deterministically waits for the detached baseline process to drain before collection occurs.
  3. Remove the `import time` and `import pytest` lines, which become unused once the sleep and the only `pytest.` reference (the `xfail` decorator, line 187) are gone; leaving them makes the pre-commit `ruff --fix` hook (`.pre-commit-config.yaml`, `id: ruff`) rewrite the file and reject the first commit attempt (ruff `F401`, measured at review on a scratch copy).
  - Depends on: none
  - Expected outcome: `test_validation_off_starts_and_collects_suite_baseline` waits on the baseline's own drain thread instead of a fixed sleep, so its `state: "completed"` assertion no longer depends on the child process finishing within 50ms; the quarantine decorator and the now-unused imports are removed.
  - Execution state: pending
- [ ] E-02 Validate behavior and determinism:
  1. Run the edited file under xdist: `python3 -m pytest tests/test_suite_baseline_mode_gate.py -o addopts="" -n 6 -v` and confirm every test in the file reports `PASSED`, with no `XFAIL`, `XPASS`, or `FAILED` line (re-derive the test list from this run; do not compare against a count measured at authoring).
  2. Contrast probe proving the wait is what makes the test deterministic (scratch only, NEVER committed): copy the edited test file to a gitignored scratch path under `.aw/state/` (for example `.aw/state/ej30u4-probe/`), change only the baseline child argv in the copy from `"print('1 passed')"` to `"import time; time.sleep(1.5); print('1 passed')"` (a deliberately slow child far beyond the old 50ms yield), and run `PYTHONPATH=. python3 -m pytest -o addopts="" -p no:cacheprovider <copy> -k validation_off -v`. It must `PASS`. Then make a second scratch copy of the PRE-change file (from `git show <base>:tests/test_suite_baseline_mode_gate.py`, where `<base>` is the commit before E-01's change: `HEAD` if E-01 is not yet committed, otherwise `HEAD~1` of the E-01 commit) with the same argv change and the `xfail` decorator removed, run it the same way, and confirm it FAILS with `AssertionError: 'absent' != 'completed'`. Delete the scratch directory afterwards.
  3. Run the routine gate bare, `python3 -m pytest`, and confirm it reports no failures.
  - Depends on: E-01
  - Expected outcome: the edited file passes under xdist with no xfail/xpass; the slowed-child contrast shows the new wait passes where the old fixed sleep reports `absent`; the routine gate is green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/test_suite_baseline_mode_gate.py::SuiteBaselineModeGateTests::test_validation_off_starts_and_collects_suite_baseline` is listed in `tests/slow_allowlist.txt` (line 583) under `Integration boundary validation under multi-process environment`. That file only feeds the duration report (`conftest.py` `pytest_terminal_summary`, "0 unlisted slow tests"); it does NOT apply the `slow` marker. The test carries no `slow` marker, so the default `-m 'not slow and not livecorpus'` (`pyproject.toml` `addopts`) already collects all three tests in this file (verified at review with `--collect-only`); no `-m "slow or not slow"` override is needed.
- The repository runs pytest with `pytest-xdist` enabled (`-n auto --dist=worksteal`, `pyproject.toml` `addopts`), which introduces CPU contention and process scheduling delays during subprocess execution.
- In `agent_workflows/runner_shared.py`, `start_suite_baseline` (line 29609) creates a detached checkout and constructs a `SuiteBaselineRun`, whose `__init__` launches the child via `subprocess.Popen` and starts the daemon thread `self._drain = threading.Thread(target=self._pump, daemon=True)` (line 29439); `_pump` runs `self.process.communicate(timeout=self.timeout)`.
- At turn end, `runner_shared.execute_item_core` calls `suite_baseline_run.collect(wait_seconds=0.0)` (line 43260). `SuiteBaselineRun.collect` does `self._drain.join(timeout=0.0)`; if `self._drain.is_alive()` it kills the child and returns `suite_baseline_absent(...)`, i.e. `state: "absent"` (line 29510).
- Tests must test observable outcomes and side effects rather than pinning code structure (AGENTS.md rule "TEST OUTCOMES, NOT CODE STRUCTURE").

## Findings

| Finding | Severity | Description |
|---|---|---|
| F-01 | Medium | In `tests/test_suite_baseline_mode_gate.py`, `_fake_oc_agent_commits_in_worktree` relied on a fixed `time.sleep(0.05)` (50ms) to allow the detached baseline process (`sys.executable, "-c", "print('1 passed')"`) and its background `_drain` thread to complete. Under `pytest-xdist` CPU contention with multiple concurrent workers, Python interpreter startup and pipe communication frequently take longer than 50ms, causing `collect(wait_seconds=0.0)` to find `_drain.is_alive() == True`. This caused the runner to kill the baseline and record `state: "absent"`, leading to assertion failures on `self.assertEqual(collected.get("state"), "completed")`. |
| F-02 | Low | In commit `f762cafceda161e1364b6605fc0f7a166bf4b261`, `test_validation_off_starts_and_collects_suite_baseline` was quarantined with `@pytest.mark.xfail(strict=False, reason="flaky: w4eswb - timing out under xdist CPU contention")` to prevent intermittent failures from blocking test runs. |
| F-03 | Low | `test_validation_on_skips_suite_baseline` also called `_fake_oc_agent_commits_in_worktree(run_dir)`, unnecessarily incurring the 50ms sleep even though validation was ON and no baseline process was started. Removing the unconditional sleep speeds up `test_validation_on_skips_suite_baseline`. |
| F-04 | Low | Measured at review (HEAD `08fa69666`) on scratch copies with the baseline child slowed to `time.sleep(1.5)`: the current fixed-sleep shape fails with `AssertionError: 'absent' != 'completed'`, while the proposed drain-join shape passes. With the unslowed child both pass on an idle machine, which is why the defect only surfaces under contention. This confirms F-01's mechanism and that the fix removes it. |

## Proposed changes (ordered, validatable)

1. E-01: Remove `@pytest.mark.xfail` from `test_validation_off_starts_and_collects_suite_baseline`, track started `runner_shared.SuiteBaselineRun` instances via a wrapper around the captured original `runner_shared.start_suite_baseline` installed with `mock.patch.object(..., side_effect=...)`, have `_fake_oc_agent_commits_in_worktree` join `_drain` threads with a 10s bound instead of sleeping 50ms, and drop the now-unused `time` and `pytest` imports.
2. E-02: Run the file under xdist, run the slowed-child contrast probe on scratch copies, and run the routine gate.

## Deferred / out of scope (with reason)

- Changes to `agent_workflows/runner_shared.py` baseline collection timeout: The production collection timeout `wait_seconds=0.0` in `runner_shared.execute_item_core` is by-design so that real agent runs (which take many seconds or minutes) are never stalled at turn finish if a baseline is slow. The issue here is purely within the test harness where the fake agent finishes nearly instantly (unlike a real LLM agent).
  - Carrier-Declined: production behavior is intended; scope is confined to test harness synchronization
- Other tests in `tests/test_suite_baseline_mode_gate.py`: `test_attempt_validates_five_shapes` and `test_validation_on_skips_suite_baseline` do not start baselines and operate correctly.
  - Carrier-Declined: other tests in the file operate as expected; no defects present

## Scope check

- Over-scope: none. Changes are restricted solely to `tests/test_suite_baseline_mode_gate.py`.
- Under-scope: none. The change addresses the exact synchronization mechanism responsible for the timeout under xdist.

## Required tests / validation

- `python3 -m pytest tests/test_suite_baseline_mode_gate.py -o addopts="" -n 6 -v`: every test line `PASSED`, no `XFAIL`/`XPASS`/`FAILED`.
- Slowed-child contrast probe (E-02 step 2): edited copy `PASSED`, pre-change copy `FAILED` with `'absent' != 'completed'`.
- Routine gate `python3 -m pytest` reports no failures.

## Spec / documentation sync

N/A: test harness fix for existing integration test; no user-facing specifications or documentation modified.

## Open questions

### OQ-01: Should the test synchronize via thread join on `_drain` or increase `time.sleep(...)`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Synchronizing via `_drain.join(timeout=10.0)` is deterministic and non-racy. An arbitrary sleep increase (e.g. `time.sleep(1.0)`) would both slow down every test run unnecessarily and remain vulnerable to extreme CPU starvation under xdist on resource-constrained CI machines. Joining `_drain` returns as soon as the background process exits while allowing up to 10s if the CPU is heavily loaded. Demonstrated at review (F-04): with the child slowed to 1.5s, the drain-join shape passed and the fixed-sleep shape failed `'absent' != 'completed'`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff tests/test_suite_baseline_mode_gate.py` showing: removal of the `@pytest.mark.xfail` quarantine decorator; replacement of `time.sleep(0.05)` with the `active_baselines` `_drain.join(timeout=10.0)` loop; the `tracking_start` wrapper calling the `original_start` captured before patching and installed via `mock.patch.object(runner_shared, "start_suite_baseline", side_effect=tracking_start)`; and removal of the `import time` / `import pytest` lines. Also paste `ruff check tests/test_suite_baseline_mode_gate.py` output showing no `F401`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: (1) paste every per-test result line plus the summary line of `python3 -m pytest tests/test_suite_baseline_mode_gate.py -o addopts="" -n 6 -v`, showing each test `PASSED` and no `XFAIL`/`XPASS`/`FAILED`; (2) paste the `-k validation_off` result line and summary for BOTH slowed-child scratch copies from E-02 step 2: the edited copy `PASSED`, the pre-change copy `FAILED` with the `AssertionError: 'absent' != 'completed'` line, and `git status --short` afterwards showing no scratch file tracked; (3) paste the summary line of the bare routine gate `python3 -m pytest` showing no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit ej30u4 -- tests/test_suite_baseline_mode_gate.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
