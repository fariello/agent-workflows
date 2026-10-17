# IPD: await detached baseline thread in SuiteBaselineModeGateTests to eliminate xdist timeout

- Date: 2026-10-17
- Kind: child
- Concern: test suite baseline mode gate timeout under xdist CPU contention
- Scope: tests/test_suite_baseline_mode_gate.py
- Scope-Paths: tests/test_suite_baseline_mode_gate.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: w4eswb
- Set: w4eswb
- Order: 1
- Highest E allocated: 02
- Author: Gabriele Fariello <gabriele.fariello@gmail.com>
- Id: ej30u4

## Workflow history

- 2026-10-17 draft (Gabriele Fariello <gabriele.fariello@gmail.com>): created via `aw ipd scaffold --from-backlog w4eswb`.
- 2026-10-17 to-review (Gabriele Fariello <gabriele.fariello@gmail.com>): authored review-ready plan to replace fixed sleep with active baseline drain join in SuiteBaselineModeGateTests and remove xfail quarantine.

## Goal

Eliminate test flakiness and timeouts in `SuiteBaselineModeGateTests.test_validation_off_starts_and_collects_suite_baseline` under pytest-xdist CPU contention by replacing the fragile fixed 50ms `time.sleep(0.05)` yield with a deterministic wait on the started `SuiteBaselineRun._drain` thread, and remove the `@pytest.mark.xfail` quarantine decorator.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Test harness synchronization and unquarantine

- [ ] E-01 In `tests/test_suite_baseline_mode_gate.py`:
  1. Update `SuiteBaselineModeGateTests._fake_oc_agent_commits_in_worktree` to accept an optional `active_baselines: list[runner_shared.SuiteBaselineRun] | None = None` parameter and remove `time.sleep(0.05)`, instead iterating over `active_baselines` and joining each baseline's `_drain` thread with a bounded timeout (`b_run._drain.join(timeout=10.0)`).
  2. In `SuiteBaselineModeGateTests.test_validation_off_starts_and_collects_suite_baseline`:
     - Remove the `@pytest.mark.xfail(strict=False, reason="flaky: w4eswb - timing out under xdist CPU contention")` quarantine decorator.
     - Wrap `runner_shared.start_suite_baseline` using `mock.patch.object` with a tracking side effect that captures created `runner_shared.SuiteBaselineRun` instances into a local list.
     - Pass the tracked list to `_fake_oc_agent_commits_in_worktree(run_dir, active_baselines=active_baselines)` so the fake agent deterministically waits for the detached baseline process to drain before collection occurs.
  - Depends on: none
  - Expected outcome: `test_validation_off_starts_and_collects_suite_baseline` runs deterministically without arbitrary sleeps or race conditions under xdist, and the quarantine decorator is removed.
  - Execution state: pending
- [ ] E-02 Run pytest targeting `tests/test_suite_baseline_mode_gate.py` both in isolation and under the full test suite with xdist enabled and `-m "slow or not slow"`, verifying that `test_validation_off_starts_and_collects_suite_baseline` passes cleanly with `PASSED` status (no `XFAIL` or `XPASS`) and zero regressions.
  - Depends on: E-01
  - Expected outcome: `tests/test_suite_baseline_mode_gate.py` passes all 3 tests with 3 passed under pytest-xdist.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/test_suite_baseline_mode_gate.py::SuiteBaselineModeGateTests::test_validation_off_starts_and_collects_suite_baseline` is registered in `tests/slow_allowlist.txt` under `Integration boundary validation under multi-process environment`.
- When running pytest targeting this test, pytest requires `-m "slow or not slow"` to include tests allowlisted as slow.
- The repository runner runs pytest with `pytest-xdist` enabled across multiple parallel workers by default, which introduces significant CPU contention and process scheduling delays during subprocess execution.
- In `agent_workflows/runner_shared.py`, `start_suite_baseline` launches a detached baseline process via `subprocess.Popen` in a separate worktree and starts a background thread `_drain` running `self.process.communicate(timeout=...)`.
- At item completion, `runner_shared.execute_item_core` invokes `suite_baseline_run.collect(wait_seconds=0.0)`. A zero-timeout `join(0.0)` is performed on `_drain`; if `_drain.is_alive()` is true, the baseline process is killed and recorded as `state: "absent"`.
- Tests must test observable outcomes and side effects rather than pinning code structure (AGENTS.md rule "TEST OUTCOMES, NOT CODE STRUCTURE").

## Findings

| Finding | Severity | Description |
|---|---|---|
| F-01 | Medium | In `tests/test_suite_baseline_mode_gate.py`, `_fake_oc_agent_commits_in_worktree` relied on a fixed `time.sleep(0.05)` (50ms) to allow the detached baseline process (`sys.executable, "-c", "print('1 passed')"`) and its background `_drain` thread to complete. Under `pytest-xdist` CPU contention with multiple concurrent workers, Python interpreter startup and pipe communication frequently take longer than 50ms, causing `collect(wait_seconds=0.0)` to find `_drain.is_alive() == True`. This caused the runner to kill the baseline and record `state: "absent"`, leading to assertion failures on `self.assertEqual(collected.get("state"), "completed")`. |
| F-02 | Low | In commit `f762cafceda161e1364b6605fc0f7a166bf4b261`, `test_validation_off_starts_and_collects_suite_baseline` was quarantined with `@pytest.mark.xfail(strict=False, reason="flaky: w4eswb - timing out under xdist CPU contention")` to prevent intermittent failures from blocking test runs. |
| F-03 | Low | `test_validation_on_skips_suite_baseline` also called `_fake_oc_agent_commits_in_worktree(run_dir)`, unnecessarily incurring the 50ms sleep even though validation was ON and no baseline process was started. Removing the unconditional sleep speeds up `test_validation_on_skips_suite_baseline`. |

## Proposed changes (ordered, validatable)

1. E-01: Remove `@pytest.mark.xfail` from `test_validation_off_starts_and_collects_suite_baseline`, track started `runner_shared.SuiteBaselineRun` instances via `mock.patch.object(runner_shared, "start_suite_baseline")`, and have `_fake_oc_agent_commits_in_worktree` join `_drain` threads with a 10s bound instead of sleeping 50ms.
2. E-02: Run pytest across `tests/test_suite_baseline_mode_gate.py` with xdist and `-m "slow or not slow"` to verify clean pass without xpass/xfail.

## Deferred / out of scope (with reason)

- Changes to `agent_workflows/runner_shared.py` baseline collection timeout: The production collection timeout `wait_seconds=0.0` in `runner_shared.execute_item_core` is by-design so that real agent runs (which take many seconds or minutes) are never stalled at turn finish if a baseline is slow. The issue here is purely within the test harness where the fake agent finishes nearly instantly (unlike a real LLM agent).
  - Carrier-Declined: production behavior is intended; scope is confined to test harness synchronization
- Other tests in `tests/test_suite_baseline_mode_gate.py`: `test_attempt_validates_five_shapes` and `test_validation_on_skips_suite_baseline` do not start baselines and operate correctly.
  - Carrier-Declined: other tests in the file operate as expected; no defects present

## Scope check

- Over-scope: none. Changes are restricted solely to `tests/test_suite_baseline_mode_gate.py`.
- Under-scope: none. The change addresses the exact synchronization mechanism responsible for the timeout under xdist.

## Required tests / validation

- `python3 -m pytest tests/test_suite_baseline_mode_gate.py -k "test_validation_off_starts_and_collects_suite_baseline" -m "slow or not slow" -v` reports `1 passed` (not xpass).
- `python3 -m pytest tests/test_suite_baseline_mode_gate.py -m "slow or not slow" -v` reports all 3 tests passed (`3 passed`).
- Full test suite via `python3 -m pytest` passes with no regressions.

## Spec / documentation sync

N/A: test harness fix for existing integration test; no user-facing specifications or documentation modified.

## Open questions

### OQ-01: Should the test synchronize via thread join on `_drain` or increase `time.sleep(...)`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Synchronizing via `_drain.join(timeout=10.0)` is deterministic and non-racy. An arbitrary sleep increase (e.g. `time.sleep(1.0)`) would both slow down every test run unnecessarily and remain vulnerable to extreme CPU starvation under xdist on resource-constrained CI machines. Joining `_drain` returns as soon as the background process exits (typically in 15-30ms) while allowing up to 10s if the CPU is heavily loaded.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff tests/test_suite_baseline_mode_gate.py` showing removal of the `@pytest.mark.xfail` quarantine decorator, replacement of `time.sleep(0.05)` with `active_baselines` synchronization, and addition of the tracking patch on `runner_shared.start_suite_baseline`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the summary line of `python3 -m pytest tests/test_suite_baseline_mode_gate.py -k "test_validation_off_starts_and_collects_suite_baseline" -m "slow or not slow" -v` showing `1 passed` (no xpass), and paste the summary line of `python3 -m pytest tests/test_suite_baseline_mode_gate.py -m "slow or not slow" -v` showing `3 passed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit ej30u4 -- tests/test_suite_baseline_mode_gate.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
