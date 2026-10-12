# IPD: Make the active-child stall watchdog test robust to interpreter startup under parallel load

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_does_not_trip_on_active_child` passes `--stall-timeout 0.5` to the driver. The watchdog clock (`runner_shared.StallWatchdog.__init__` sets `self._last_activity = time.monotonic()`) starts when the driver spawns the fake `active_opencode` child, so the 0.5s window must also cover the child's Python interpreter startup and its `import json, pathlib, re, sys, time` before it prints its first event. Under a full bare suite run (`-n auto`, many xdist workers) that startup can exceed 0.5s; `StallWatchdog._run` then sees `idle >= self.timeout`, reaps the child (traceback shows `KeyboardInterrupt` inside importlib), and the test fails with exit code 1 although the product behaved correctly. Backlog `ncpc8z`, `Work-Kind: bug`, `Blocks-Release: next`.
- Scope: Test-only change to the one flaky test: raise its stall timeout well above worst-case child startup and restructure the fake child so it stays ACTIVE (emitting events at gaps well under the timeout) for a total duration LONGER than the timeout, so the test still proves the property it exists for (activity resets the watchdog) instead of becoming vacuous. No production code change.
- Scope-Paths: tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: ncpc8z
- Blocks-Release: next
- Set: ncpc8z
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: masjx4

## Workflow history

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog `ncpc8z`; review-ready.

## Goal

Eliminate the load-dependent false failure of `test_stall_watchdog_does_not_trip_on_active_child` while keeping it a real, falsifiable test that an active child is not killed by the stall watchdog.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Harden the active-child test

- [ ] E-01 In `tests/test_oc_runipd.py` `StallWatchdogTests.test_stall_watchdog_does_not_trip_on_active_child`, change the driver argument `"--stall-timeout", "0.5"` to `"--stall-timeout", "3.0"` (a margin of roughly 6x over the 0.5s startup that was observed to be insufficient), and add a short comment stating why (the watchdog window includes child interpreter startup, which is slow under parallel suite load; backlog `ncpc8z`).
  - Depends on: none
  - Expected outcome: The test's driver invocation passes `--stall-timeout 3.0`; the comment names `ncpc8z`.
  - Execution state: pending

- [ ] E-02 In the same test's fake `active_opencode` child source, replace the `for i in range(3): ... time.sleep(0.05)` loop with a loop that emits a `text` event every 0.5s for 8 iterations (about 4.0s of activity, which is LONGER than the 3.0s timeout while every gap stays at one sixth of it), keeping the existing `sessionID`, outcome-file write, and final `done` event unchanged. Add a comment stating that total activity exceeding the timeout is what makes the test fail if the watchdog ignored activity.
  - Depends on: E-01
  - Expected outcome: The child's active period (sum of sleeps) exceeds the stall timeout and each inter-event gap is well below it, so a watchdog that did not reset on stdout activity would trip and the test would fail.
  - Execution state: pending

- [ ] E-03 Leave `test_stall_watchdog_terminates_silent_child_and_marks_interrupted` (0.3s timeout against a silent `time.sleep(60)` child) unchanged: a slow startup can only make that child MORE silent, so it cannot false-fail under load and it remains the negative control.
  - Depends on: none
  - Expected outcome: `git diff` shows no change to the silent-child test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run the suite bare as `python3 -m pytest` (AGENTS.md repo-local development contract); `pyproject.toml` `addopts` already supply `-n auto --dist=worksteal`, which is exactly the parallel load that exposes this flake.
- Tests must assert observable behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); this test drives the real driver subprocess (`_DRIVER_CMD = [sys.executable, "-m", "agent_workflows.oc_runipd"]`) and asserts exit code and `state.json` item status, which this plan preserves.
- Watchdog semantics: `runner_shared.StallWatchdog._run` kills when `time.monotonic() - self._last_activity >= self.timeout`; `_last_activity` is set at construction (`oc_runipd` builds `StallWatchdog(process, timeout=stall_timeout)` right after spawning) and refreshed by `touch()` on each stdout line. `check_interval` is clamped to `timeout / 4.0`.
- Fake child executables are built with `support.make_fake_executable` (`tests/support.py`), which on POSIX writes a `#!<this interpreter>` script, so each child pays full interpreter startup.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | The 0.5s window covers child spawn + interpreter startup + imports before the first event. | `StallWatchdog.__init__` sets `_last_activity` at construction; the child's first `print` follows `import json, pathlib, re, sys, time`. |
| F2 | The current child's whole active period is about 0.15s (3 x 0.05s), shorter than the 0.5s timeout. | Child source loop `for i in range(3)` with `time.sleep(0.05)`. So even today the test would pass with a watchdog that never resets on activity, as long as startup is fast; it is weaker than its name claims. |
| F3 | Simply raising the timeout without lengthening activity would make the test vacuous. | With a 3.0s timeout and 0.15s of activity, a watchdog ignoring stdout would still pass. E-02 restores falsifiability. |
| F4 | The silent-child test cannot false-fail from slow startup. | Its child sleeps 60s and never prints; slowness only delays nothing it depends on. |

## Proposed changes (ordered, validatable)

1. E-01: raise the active-child test's `--stall-timeout` to 3.0.
2. E-02: make the child emit events every 0.5s for about 4.0s total so activity spans more than one timeout window.
3. E-03: leave the silent-child test untouched as the negative control.

## Deferred / out of scope (with reason)

- Changing `StallWatchdog` to start its clock at the first child output, or adding a startup grace period: that changes production behavior for real hung-at-startup agents (a child that never starts SHOULD be reaped after the configured timeout), and the backlog item identifies a test-timing defect, not a product defect.
- Auditing other subprocess-timing tests for similar flakes: not identified by `ncpc8z`; file separately if observed.

## Scope check

- Over-scope: none.
- Under-scope: none; the only affected file is `tests/test_oc_runipd.py`, and falsifiability of the test is explicitly preserved by E-02 and proven by V-02.

## Required tests / validation

- The modified test passes in isolation (V-01).
- The modified test passes repeatedly under heavy concurrent CPU load, and FAILS when the watchdog is prevented from resetting on activity, proving it is not vacuous; the sabotage is temporary and reverted (V-02).
- The silent-child control is unchanged and passes, and the full bare suite passes (V-03).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes this test's timing.

## Open questions

### OQ-01: Is 3.0s the right timeout margin?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The backlog reports startup exceeding 0.5s under 37+ workers and the test taking about 7.5s in isolation; 3.0s gives roughly 6x margin over the failing bound while adding only about 4s of child activity. If V-02 shows any failure the executor raises the timeout (and the activity duration proportionally, keeping total activity greater than the timeout and gaps at most one sixth of it) and records the decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff tests/test_oc_runipd.py` excerpt showing `"--stall-timeout"` followed by `"3.0"` in `test_stall_watchdog_does_not_trip_on_active_child` with the `ncpc8z` comment, plus pasted output of `python3 -m pytest -o addopts="" tests/test_oc_runipd.py -k test_stall_watchdog_does_not_trip_on_active_child` showing `1 passed`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: THREE pasted observations. (a) The diff of the child loop (0.5s gaps, 8 iterations). (b) A load run: start one CPU-burning process per core (`for i in $(seq $(nproc)); do python3 -c 'while True: pass' & done`), run the test 20 times concurrently (20 backgrounded `python3 -m pytest -o addopts="" tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_does_not_trip_on_active_child` invocations whose exit codes are all printed), then kill the burners; all 20 exit codes must be 0. The observation is produced by the driver subprocess `agent_workflows.oc_runipd` spawning the E-02 child under `runner_shared.StallWatchdog`. (c) Falsifiability: temporarily make `runner_shared.StallWatchdog.touch` a no-op (working-tree edit only, never committed), rerun the single test and paste `1 failed`, then revert and paste empty `git diff --stat agent_workflows/runner_shared.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff tests/test_oc_runipd.py` shows no hunk inside `test_stall_watchdog_terminates_silent_child_and_marks_interrupted`; pasted output of `python3 -m pytest -o addopts="" tests/test_oc_runipd.py -k StallWatchdogTests` showing `2 passed`; and the pasted final summary line of a bare full-suite run `python3 -m pytest` showing zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_oc_runipd.py` through `aw commit <this plan> -- tests/test_oc_runipd.py`; never commit the V-02 sabotage edit; never push. Move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
