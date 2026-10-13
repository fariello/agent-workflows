# IPD: Make the active-child stall watchdog test robust to interpreter startup under parallel load

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_does_not_trip_on_active_child` passes `--stall-timeout 0.5` to the driver. The watchdog clock (`runner_shared.StallWatchdog.__init__` sets `self._last_activity = time.monotonic()`) starts when the driver spawns the fake `active_opencode` child, so the 0.5s window must also cover the child's Python interpreter startup and its `import json, pathlib, re, sys, time` before it prints its first event. Under a full bare suite run (`-n auto`, many xdist workers) that startup can exceed 0.5s; `StallWatchdog._run` then sees `idle >= self.timeout`, reaps the child (traceback shows `KeyboardInterrupt` inside importlib), and the test fails with exit code 1 although the product behaved correctly. Backlog `ncpc8z`, `Work-Kind: bug`, `Blocks-Release: next`.
- Scope: Test-only change to the one flaky test: raise its stall timeout well above worst-case child startup and restructure the fake child so it stays ACTIVE (emitting events at gaps well under the timeout) for a total duration LONGER than the timeout, so the test still proves the property it exists for (activity resets the watchdog) instead of becoming vacuous. No production code change.
- Scope-Paths: tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: ncpc8z
- Blocks-Release: next
- Set: ncpc8z
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: masjx4
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog `ncpc8z`; review-ready.

## Goal

Eliminate the load-dependent false failure of `test_stall_watchdog_does_not_trip_on_active_child` while keeping it a real, falsifiable test that an active child is not killed by the stall watchdog.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Harden the active-child test

- [x] E-01 In `tests/test_oc_runipd.py` `StallWatchdogTests.test_stall_watchdog_does_not_trip_on_active_child`, change the driver argument `"--stall-timeout", "0.5"` to `"--stall-timeout", "3.0"` (a margin of roughly 6x over the 0.5s startup that was observed to be insufficient), and add a short comment stating why (the watchdog window includes child interpreter startup, which is slow under parallel suite load; backlog `ncpc8z`).
  - Depends on: none
  - Expected outcome: The test's driver invocation passes `--stall-timeout 3.0`; the comment names `ncpc8z`.
  - Execution state: performed

- [x] E-02 In the same test's fake `active_opencode` child source, replace the `for i in range(3): ... time.sleep(0.05)` loop with a loop that emits a `text` event every 0.5s for 8 iterations (about 4.0s of activity, which is LONGER than the 3.0s timeout while every gap stays at one sixth of it), keeping the existing `sessionID`, outcome-file write, and final `done` event unchanged. Add a comment stating that total activity exceeding the timeout is what makes the test fail if the watchdog ignored activity.
  - Depends on: E-01
  - Expected outcome: The child's active period (sum of sleeps) exceeds the stall timeout and each inter-event gap is well below it, so a watchdog that did not reset on stdout activity would trip and the test would fail.
  - Execution state: performed

- [x] E-03 Leave `test_stall_watchdog_terminates_silent_child_and_marks_interrupted` (0.3s timeout against a silent `time.sleep(60)` child) unchanged: a slow startup can only make that child MORE silent, so it cannot false-fail under load and it remains the negative control.
  - Depends on: none
  - Expected outcome: `git diff` shows no change to the silent-child test.
  - Execution state: performed

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
| F5 | Review rehearsal at HEAD `eecf0c8f1` (all edits reverted afterwards): with E-01 and E-02 applied, `StallWatchdogTests` gave `2 passed in 7.03s`; with `runner_shared.StallWatchdog.touch` made a no-op it gave `1 failed, 1 passed` (the active-child test failed), so the hardened test is falsifiable. The ORIGINAL test with `touch` made a no-op gave `1 passed`, confirming F2: today's test is vacuous. | Commands run in the review lane. |
| F6 | The CPU-burner load recipe does NOT reproduce the flake on a 12-core review host: 20 concurrent runs of the ORIGINAL test under 12 burners all exited 0 (the hardened test also gave 20 of 20). A deterministic reproduction does: injecting `time.sleep(1.0)` right after the child's imports (simulating slow startup) makes the original 0.5s configuration give `1 failed` and the hardened 3.0s configuration give `1 passed`. So V-02 now demands that deterministic contrast as the proof of the fix, and keeps the load run only as supporting evidence. | Commands run in the review lane. |

## Proposed changes (ordered, validatable)

1. E-01: raise the active-child test's `--stall-timeout` to 3.0.
2. E-02: make the child emit events every 0.5s for about 4.0s total so activity spans more than one timeout window.
3. E-03: leave the silent-child test untouched as the negative control.

## Deferred / out of scope (with reason)

- Changing `StallWatchdog` to start its clock at the first child output, or adding a startup grace period: that changes production behavior for real hung-at-startup agents (a child that never starts SHOULD be reaped after the configured timeout), and the backlog item identifies a test-timing defect, not a product defect.
  - Carrier-Declined: the current production behavior is correct (a child that never starts must be reaped); no defect to carry.
- Auditing other subprocess-timing tests for similar flakes: not identified by `ncpc8z`; file separately if observed.
  - Carrier-Declined: no other flake is measured or reported; an unmeasured audit is not an obligation.

## Scope check

- Over-scope: none.
- Under-scope: none; the only affected file is `tests/test_oc_runipd.py`, and falsifiability of the test is explicitly preserved by E-02 and proven by V-02.

## Required tests / validation

- The modified test passes in isolation (V-01).
- The modified test survives a deterministic simulated slow startup that fails the old configuration, passes repeatedly under concurrent CPU load, and FAILS when the watchdog is prevented from resetting on activity, proving it is not vacuous; every sabotage is temporary and reverted (V-02).
- The silent-child control is unchanged and passes, and the bare full suite shows an empty failure-set delta against the base commit (V-03).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes this test's timing.

## Open questions

### OQ-01: Is 3.0s the right timeout margin?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The backlog reports startup exceeding 0.5s under 37+ workers and the test taking about 7.5s in isolation; 3.0s gives roughly 6x margin over the failing bound while adding only about 4s of child activity. If V-02 shows any failure the executor raises the timeout (and the activity duration proportionally, keeping total activity greater than the timeout and gaps at most one sixth of it) and records the decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: `git diff tests/test_oc_runipd.py` excerpt showing `"--stall-timeout"` followed by `"3.0"` in `test_stall_watchdog_does_not_trip_on_active_child` with the `ncpc8z` comment, plus pasted output of `python3 -m pytest -o addopts="" tests/test_oc_runipd.py -k test_stall_watchdog_does_not_trip_on_active_child` showing `1 passed`.
  - Observed evidence:
    `git diff tests/test_oc_runipd.py` excerpt:
    ```diff
    @@ -1827,8 +1830,10 @@ class StallWatchdogTests(unittest.TestCase):
                         "--no-self-finalize",
                         "--repo",
                         os.fspath(repo),
    +                    # The watchdog window includes child interpreter startup, which is slow
    +                    # under parallel suite load (backlog ncpc8z); 3.0s provides roughly 6x margin.
                         "--stall-timeout",
    -                    "0.5",
    +                    "3.0",
                         "--opencode",
                         os.fspath(active_child),
                     ],
    ```
    Single test run:
    ```
    $ python3 -m pytest -o addopts="" tests/test_oc_runipd.py -k test_stall_watchdog_does_not_trip_on_active_child
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=326545321
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 182 items / 181 deselected / 1 selected

    tests/test_oc_runipd.py .                                                [100%]

    NOTE: 181 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ====================== 1 passed, 181 deselected in 6.76s =======================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: FOUR pasted observations. (a) The diff of the child loop (0.5s gaps, 8 iterations). (b) A load run: start one CPU-burning process per core (`for i in $(seq $(nproc)); do python3 -c 'while True: pass' & done`), run the test 20 times concurrently (20 backgrounded `python3 -m pytest -o addopts="" tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_does_not_trip_on_active_child` invocations whose exit codes are all printed), then kill the burners and paste `pgrep -fc 'while True: pass'` showing none remain; all 20 exit codes must be 0. This is SUPPORTING evidence only: it may not reproduce the flake on every host (F6). The observation is produced by the driver subprocess `agent_workflows.oc_runipd` spawning the E-02 child under `runner_shared.StallWatchdog`. (c) Falsifiability: temporarily make `runner_shared.StallWatchdog.touch` a no-op (working-tree edit only, never committed), rerun the single test and paste `1 failed`, then revert and paste empty `git diff --stat agent_workflows/runner_shared.py`. (d) Deterministic startup-delay contrast, which is the proof the fix addresses the defect: temporarily insert `time.sleep(1.0)` immediately after the child's `import` line (working-tree only, never committed) and paste the single-test result with the HARDENED values (`1 passed`) and then with `--stall-timeout` set back to `0.5` (`1 failed`); revert and paste `git diff tests/test_oc_runipd.py` showing only the E-01 and E-02 hunks remain.
  - Observed evidence:
    (a) Diff of the child loop:
    ```diff
    @@ -1809,9 +1809,12 @@ class StallWatchdogTests(unittest.TestCase):
                         executed.parent.mkdir(parents=True, exist_ok=True)
                         plan.rename(executed)

    -                    for i in range(3):
    +                    # Total activity (8 * 0.5s = 4.0s) exceeds the 3.0s stall timeout,
    +                    # proving the watchdog resets on stdout activity; if the watchdog
    +                    # ignored activity, the child would be terminated before finishing.
    +                    for i in range(8):
                             print(json.dumps({'type':'text','sessionID':'ses_activ1','part':{'text':f'step {i}'}}), flush=True)
    -                        time.sleep(0.05)
    +                        time.sleep(0.5)

                         outcome.write_text(json.dumps({'schema_version':1,'id6':'activ1','disposition':'executed','pushed':False}))
                         print(json.dumps({'type':'text','sessionID':'ses_activ1','part':{'text':'done'}}), flush=True)
    ```
    (b) Load run under 12 CPU burners with 20 concurrent test runs:
    ```
    Started 12 burners
    Run 1 exit code: 0
    Run 2 exit code: 0
    Run 3 exit code: 0
    Run 4 exit code: 0
    Run 5 exit code: 0
    Run 6 exit code: 0
    Run 7 exit code: 0
    Run 8 exit code: 0
    Run 9 exit code: 0
    Run 10 exit code: 0
    Run 11 exit code: 0
    Run 12 exit code: 0
    Run 13 exit code: 0
    Run 14 exit code: 0
    Run 15 exit code: 0
    Run 16 exit code: 0
    Run 17 exit code: 0
    Run 18 exit code: 0
    Run 19 exit code: 0
    Run 20 exit code: 0
    $ pgrep -fc '[w]hile True: pass' || echo 0
    0
    ```
    (c) Falsifiability test with sabotaged `touch`:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_does_not_trip_on_active_child
    ====================== 1 failed, 181 deselected in 8.27s =======================
    $ git diff --stat agent_workflows/runner_shared.py
    (empty)
    ```
    (d) Deterministic startup-delay contrast with `time.sleep(1.0)` injected:
    Hardened 3.0s timeout:
    ```
    $ python3 -m pytest -o addopts="" tests/test_oc_runipd.py -k test_stall_watchdog_does_not_trip_on_active_child
    ====================== 1 passed, 181 deselected in 11.97s ======================
    ```
    Old 0.5s timeout:
    ```
    $ python3 -m pytest -o addopts="" tests/test_oc_runipd.py -k test_stall_watchdog_does_not_trip_on_active_child
    FAILED tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_does_not_trip_on_active_child
    ====================== 1 failed, 181 deselected in 5.94s =======================
    ```
    Reverted and verified `git diff tests/test_oc_runipd.py` contains only E-01 and E-02 hunks.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `git diff tests/test_oc_runipd.py` shows no hunk inside `test_stall_watchdog_terminates_silent_child_and_marks_interrupted`; pasted output of `python3 -m pytest -o addopts="" tests/test_oc_runipd.py -k StallWatchdogTests` showing `2 passed`; and the pasted final summary lines of a bare full-suite run `python3 -m pytest` at the base commit (before E-01) and after E-02, with the failure-set delta stated as an explicit set of test ids. The bar is an EMPTY delta and no failure inside `StallWatchdogTests`; a pre-existing unrelated failure present at both points does not fail this item.
  - Observed evidence:
    `git diff tests/test_oc_runipd.py` shows changes only to `test_stall_watchdog_does_not_trip_on_active_child`; `test_stall_watchdog_terminates_silent_child_and_marks_interrupted` is completely unchanged.
    Output of `StallWatchdogTests`:
    ```
    $ python3 -m pytest -o addopts="" tests/test_oc_runipd.py -k StallWatchdogTests
    tests/test_oc_runipd.py ..                                               [100%]
    ====================== 2 passed, 180 deselected in 12.92s ======================
    ```
    Bare full suite before E-01 (at base commit 9906a0e3dd8bc26dd603fc2f541fda7ca834e203):
    ```
    8002 passed, 4 skipped, 18 xfailed, 3 warnings in 965.47s (0:16:05)
    ```
    Bare full suite after E-02:
    ```
    8002 passed, 4 skipped, 18 xfailed, 3 warnings in 968.29s (0:16:08)
    ```
    Failure-set delta: `set()` (empty delta, 0 failures at base commit and 0 failures after E-02; no failures in `StallWatchdogTests`).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Execute only after explicit human approval (`Status: approved`). OQ-01 is resolved. Commit only `tests/test_oc_runipd.py` (plus this plan, which the lifecycle writes) through `aw commit masjx4 -- tests/test_oc_runipd.py`; never `git add -A` or `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before committing. NEVER commit the V-02 sabotage edits (the no-op `touch` in `agent_workflows/runner_shared.py`, the injected `time.sleep(1.0)`, or the reverted `0.5`); revert each immediately after observing it. Paste the ACTUAL runner output for every test claim; never claim a pass you did not run. Kill every CPU burner V-02 starts.

SCOPE FENCE. The declared change is `tests/test_oc_runipd.py` only; no production code. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`, never silently.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` reads `pass` with pasted evidence, run `aw ipd lint --phase pre-transition` and require it conforming. In a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`; executing by hand, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit status or `git mv` the plan into `executed/`.
