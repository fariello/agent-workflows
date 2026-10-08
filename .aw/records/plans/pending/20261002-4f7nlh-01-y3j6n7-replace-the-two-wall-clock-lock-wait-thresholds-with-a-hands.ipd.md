# IPD: Replace the two wall-clock lock-wait thresholds with a handshake so the finalize-lock contention tests prove waiting instead of timing it

- Date: 2026-10-02
- Kind: child
- Concern: Two tests in `RollbackFailureSemanticsTests` assert that `acquire_finalize_lock` waited by measuring WALL-CLOCK elapsed time against a fixed-duration holder, so ordinary scheduling delay under `-n auto` makes them fail on correct code.
- Scope: Rewrite `test_two_process_lock_wait_succeeds` and `test_finalize_lock_WAITS_for_a_short_lived_live_holder` in `tests/test_ipd_lifecycle_cli.py` to release their holder on a handshake and to assert on observed poll attempts plus lock ownership. No production code changes.
- Scope-Paths: tests/test_ipd_lifecycle_cli.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 4f7nlh
- Blocks-Release: next
- Set: 4f7nlh
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: y3j6n7
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Re-verified both tests and the wait_until ordering at a2b959f5a; probed the mutation and found functools.partial(timeout=0) is a silent no-op and a closing lambda recurses, so validation now names a default-arg-capture mock that measured TransactionLockError polls 0; restored the dropped take-on-release property as a poll bound; made the liveness assertion satisfiable via per-poll samples; added finalize ownership, scope fence, and backlog filing for E-04.

- 2026-10-02 draft (opencode): created.
- 2026-10-02 to-review (opencode): authored from backlog `4f7nlh`; root cause reproduced deterministically and the proposed fix mutation-checked before writing.

## Goal

Make the two finalize-lock contention tests fail only when `acquire_finalize_lock` genuinely stops waiting for a live holder. Today they also fail when the test process is merely descheduled, because they infer "it waited" from wall-clock elapsed time against a holder that releases on a fixed `time.sleep(1.0)` the test does not control.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Remove the timing dependency from the two-process test

- [x] E-01 In `tests/test_ipd_lifecycle_cli.py`, change `RollbackFailureSemanticsTests.test_two_process_lock_wait_succeeds` so its child process holds the lock until the PARENT says to release it instead of for a fixed `time.sleep(1.0)`: have the child poll for a release sentinel file (bounded by its own bail-out deadline so an abandoned child cannot outlive the suite), and have the parent create that sentinel from inside the `sleep` callable it injects into `acquire_finalize_lock`, once at least two polls have been observed. THE INJECTED `sleep` MUST STILL REALLY SLEEP (call `time.sleep(sec)` after recording) and the test must NOT inject `now`: unlike the sibling injected-clock tests, this one exercises two real processes, and the child needs real time to observe the sentinel and unlink the lock; a non-sleeping callable would spin through the poll budget. Keep `timeout=` generous (the existing 5.0s, or larger) since it is now only a hang bound, not an assertion. RECORD `child.poll() is None` INSIDE the callable on each call (before writing the sentinel), because by the time `acquire_finalize_lock` returns the child has released and exited, so a post-return `child.poll()` would be `0`, not `None`.
  - Depends on: none
  - Expected outcome: The holder's lifetime is controlled by the parent, so the child is still holding the lock at the moment the parent begins waiting no matter how long the parent was descheduled first.
  - Execution state: performed

- [x] E-02 In the same test, replace the wall-clock assertion `assertGreater(elapsed, 0.7, ...)` with assertions that do not read the clock: assert the injected `sleep` callable was invoked at least twice (so the acquire provably POLLED rather than taking a free lock), assert the holder subprocess was alive at every recorded poll before the sentinel was written (the liveness samples E-01 records inside the callable; a post-return `child.poll()` is necessarily non-`None` because the child has exited), and keep the existing ownership assertion that the lock file's `pid` is `os.getpid()`. Also replace the bounded `for _ in range(50)` lock-appearance spin with a deadline-based wait so a slow child start is a wait rather than a failure.
  - Depends on: E-01
  - Expected outcome: The test asserts the waiting BEHAVIOR (polled while a live holder held it, then acquired it) and no longer asserts a duration.
  - Execution state: performed

### Task group 2: Fix the same defect in the sibling test

- [x] E-03 Apply the same handshake treatment to `RollbackFailureSemanticsTests.test_finalize_lock_WAITS_for_a_short_lived_live_holder`, whose releasing thread sleeps a fixed `0.5` and whose `assertGreaterEqual(waited, 0.4, ...)` has the same wall-clock dependency with a tighter margin: release the lock from the injected `sleep` callable after at least two observed polls rather than from a timed thread, assert on the observed poll count, and keep its existing assertions that the lock is owned by this PID and that the holder subprocess was never killed (`holder.poll() is None`). REPLACE, DO NOT DROP, the `assertLess(waited, 5, "it must take the lock as soon as the holder releases it")` half: that is an upper bound with 5s of headroom and is not the fragile direction, but rather than keep a clock read, assert the same property by poll count, namely that the injected `sleep` was called NO MORE than one time after the release (record the call index at which the lock was unlinked and assert `len(sleep_calls) <= release_index + 1`), which proves the acquire took the lock on the very next poll. Do NOT copy this bound into E-02: there the CHILD unlinks asynchronously after it notices the sentinel, so the parent may legitimately poll several more times before the release is visible; E-02's release-side proof is the child exiting `0` via the handshake (V-01) plus parent ownership. Preserve the test's documented provenance comment naming `run-20260927T001634Z-258437`.
  - Depends on: none
  - Expected outcome: The sibling test proves the same contract (a live holder is waited for, a released lock is taken on the next poll, the holder is never killed) without depending on when the test process is scheduled.
  - Execution state: performed

- [x] E-04 Confirm no OTHER test in the repository asserts a finalize-lock or contention wait duration against a fixed-duration holder, and record the search performed. At review `grep -rln "monotonic()" tests/*.py` named eight modules (`test_concurrent_driver_guard.py`, `test_ipd_lifecycle_cli.py`, `test_oc_runipd.py`, `test_permission_bound_disabled.py`, `test_platform_lock.py`, `test_runner_stop_triggers_e2e.py`, `test_statusline_ascii_mode.py`, `test_turn_bounds.py`); give every `monotonic()`-derived assertion in them a one-line disposition, rather than only those near the word "lock". Re-derive the list at execution; do not treat these eight as the bar. If another instance exists outside this plan's declared scope, do NOT widen scope: FILE it with `aw backlog new` (Work-Kind `bug`, which auto-gates it) and record its id6 in the evidence; a follow-up left only in this plan's prose is not tracked.
  - Depends on: none
  - Expected outcome: Either a recorded finding that these two were the only instances, or a recorded follow-up naming any further instance without editing it.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests must assert observable behavior and must stay mutation-sensitive: `GUIDING_PRINCIPLES.md` P16 ("Test outcomes and behavior, never code structure or text") requires "Verify test sensitivity with mutation: A test is only valid if breaking the underlying behavior makes the test fail", and the same file's "Never weaken an assertion so it passes everywhere" bullet forbids relaxing an assertion so it passes vacuously. This plan therefore REPLACES the timing proxy with a stronger behavioral assertion rather than loosening the threshold.
- The production code under test already accepts injected `sleep` and `now` callables: `ipd_lifecycle.acquire_finalize_lock` takes `sleep` and `now` keyword arguments and documents that `timeout=0` "restores the old check-once behavior". Sibling tests in the same class already exploit this, e.g. `test_holder_releases_mid_wait_injected_clock` drives the lock through a `fake_sleep` that unlinks the lock after two sleep calls. The handshake this plan adopts is therefore an ESTABLISHED local pattern, not a new one.
- The waiting behavior itself is shared policy, not local to finalize: `ipd_lifecycle.FINALIZE_LOCK_WAIT_SECONDS` is assigned `contention_wait.TIMEOUT_SECONDS`, and the acquire loop delegates to `contention_wait.wait_until`. That helper calls `try_once()` BEFORE its first `sleep`, which is why an uncontended acquire records zero sleep calls and a contended one records at least one; the poll-count assertion this plan adds depends on that ordering.
- The suite always runs in parallel: `pyproject.toml` sets `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` and its comment states `-n auto` is "always on in the default invocation", so a test that depends on prompt scheduling is being run under exactly the condition it cannot tolerate.
- The repository documents this exact class of lock-contention flake as costly in production: the `FINALIZE_LOCK_WAIT_SECONDS` docstring records that run `run-20260927T001634Z-258437` refused two verified items because a peer held the lock at the instant finalize looked, which is the regression the sibling test exists to prevent and therefore must keep catching.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The test's measured interval begins AFTER the child's lock write, not at it, so the parent's own scheduling delay is subtracted from the hold it then asserts was long. The test spawns the child, spins until `lock.exists()`, and only then sets `started = _time.monotonic()`, while the child's 1.0s hold began at its write. | Measured in this lane by replacing the appearance spin with an explicit stall and recording the assertion outcome: `stall=0.05s -> pass elapsed=1.068s`, `stall=0.40s -> pass elapsed=0.706s`, `stall=0.60s -> FAIL assertGreater(elapsed, 0.7) elapsed=0.506s`, `stall=0.90s -> FAIL elapsed=0.205s`, `stall=1.20s -> FAIL assertTrue(lock.exists()) 'child should have written the lock'`. |
| F-02 | The failure is a double-sided cliff, so there are two distinct red signatures for the same root cause: a moderate delay fails the `assertGreater(elapsed, 0.7)` duration assertion, and a delay past the child's whole 1.0s hold fails the EARLIER `assertTrue(lock.exists(), "child should have written the lock")` because the child has already released and exited. | Same measurement as F-01: the `stall=1.20s` row fails on lock appearance rather than on elapsed time. |
| F-03 | The margin is thin even when nothing is wrong. An unloaded acquire measures about 1.007s against a 0.7s floor, leaving roughly 0.3s of slack, and the test tolerates no more than about 0.3s of parent delay before going red. | Unloaded repetition in this lane: six consecutive iterations at `elapsed=1.069s, 1.007s, 1.008s, 1.007s, 1.007s, 1.007s` with observation lag `0.041s`; and the F-01 table showing `stall=0.40s` already down to `elapsed=0.706s`, a 0.006s margin. |
| F-04 | CPU load alone did not reproduce it here, which is why the fix must address the mechanism rather than chase a load threshold. With 36 busy-loop processes on 12 cores, observation lag rose only to 0.066-0.130s and ten iterations all passed. This means the live failure needs a longer deschedule than steady CPU pressure produced on this machine (a worker starting a subprocess, I/O stall, or a heavier concurrent lane), and that a reviewer should NOT expect to see it by simply loading the box. | `nproc` reports 12; under 36 competing busy loops, `TOTAL fails=0/10` with per-iteration `lag` between `0.064s` and `0.130s`. Contrast the deterministic reproduction in F-01. |
| F-05 | The sibling test `test_finalize_lock_WAITS_for_a_short_lived_live_holder` has the SAME defect with a tighter margin, and is therefore strictly more fragile: its releasing thread sleeps a fixed `0.5s` and it asserts `assertGreaterEqual(waited, 0.4)`, leaving about 0.1s of slack. Fixing only the reported test would leave a known flake in place. | Measured in this lane: `stall=0.00s waited=0.564s -> pass`, `stall=0.20s waited=0.305s -> FAIL assertGreaterEqual(waited, 0.4)`, `stall=0.45s waited=0.105s -> FAIL`, `stall=0.60s waited=0.004s -> FAIL`. |
| F-06 | The proposed handshake is mutation-sensitive, so it is a real test and not a weakened one. Driving the same handshake against a simulated regression (`timeout=0`, the documented check-once behavior the waiting replaced) turns it red. | Measured in this lane: `baseline (waiting present) err=None polls=3 -> test PASSES`; `MUTATED (waiting removed) err=TransactionLockError polls=0 -> test FAILS`. |
| F-07 | The handshake is insensitive to parent scheduling across two orders of magnitude of delay, which is the property the current test lacks. | Prototype measured in this lane at stalls `0.00, 0.05, 0.30, 0.60, 1.20, 2.50, 5.00` seconds: every row `existed=True holder_alive=True polls=3 took_lock=True child_rc=0 -> pass`. |

## Proposed changes (ordered, validatable)

1. (E-01) Make the child in `test_two_process_lock_wait_succeeds` hold the lock until a parent-written sentinel appears, bounded by its own deadline so it always exits.
2. (E-02) Replace that test's `assertGreater(elapsed, 0.7, ...)` with poll-count, holder-liveness, and lock-ownership assertions, and make the lock-appearance spin deadline-based.
3. (E-03) Apply the same handshake and poll-count assertions to `test_finalize_lock_WAITS_for_a_short_lived_live_holder`, replacing its timed releasing thread.
4. (E-04) Record the search for any remaining duration-against-fixed-holder assertion, deferring anything outside scope to a new backlog item rather than editing it.

## Deferred / out of scope (with reason)

- No change to `agent_workflows/ipd_lifecycle.py` or `agent_workflows/contention_wait.py`. The production waiting behavior is correct; the measured defect is in how the tests OBSERVE it. Changing the lock policy to make a test easier to time would alter shipped behavior to suit a test.
  - Carrier-Declined: Nothing is owed later. This is a boundary statement (the defect is in the tests, not the production waiting), not deferred work, so there is no obligation for a carrier to revisit.
- No change to `tests/test_platform_lock.py`. Its `assertLess(elapsed, 5.0, "a non-blocking refusal must not wait")` is an UPPER bound on a non-blocking refusal, so scheduling delay has 5s of headroom and the assertion is not fragile in the same direction. Noted rather than edited.
  - Carrier-Declined: Nothing is owed later. The assertion was examined and found sound in this direction, so this records a completed judgement rather than postponed work. E-04/V-04 require this disposition be re-stated against actual search output at execution time.
- No change to the injected-clock sibling tests (`test_holder_releases_mid_wait_injected_clock`, `test_holder_outlives_budget_injected_clock`, `test_stale_lock_reclaims_immediately_without_waiting`). They already drive a simulated clock and read no wall clock.
  - Carrier-Declined: Nothing is owed later. These tests read no wall clock, so they cannot carry the defect this plan fixes; excluding them closes the question rather than deferring it.
- No attempt to reproduce the original failure by loading the machine, and no retry/rerun marker added. Per F-04 load alone did not reproduce it, and a rerun marker would hide the defect instead of removing it.
  - Carrier-Declined: Nothing is owed later. Declining to add a rerun marker is a permanent decision (it would mask the defect), and the root cause is reproduced deterministically by F-01 instead, so no load-based reproduction is outstanding.

## Scope check

- Over-scope: none. The single declared path `tests/test_ipd_lifecycle_cli.py` holds both affected tests; `grep` for `test_two_process_lock_wait_succeeds` across the repository returns exactly one hit, in that file.
- Under-scope: The plan fixes both instances of the pattern that were measured (F-01, F-05) rather than only the one named in the backlog item, because a fix to one would leave a known flake with a tighter margin in the same test class. E-04 bounds this by recording, not editing, anything further it finds.

## Required tests / validation

- Run the two affected tests directly and paste the output.
- Run the whole `RollbackFailureSemanticsTests` class to show no sibling regressed.
- Prove the rewritten tests are still sensitive: with the production waiting neutralized, each rewritten test must FAIL. NEUTRALIZE IT IN-PROCESS, NOT BY EDITING PRODUCTION CODE: run the test under a scratch wrapper (kept under the gitignored `.aw/state/`, never committed) that applies `unittest.mock.patch.object(ipd_lifecycle.contention_wait, "wait_until", lambda *a, _o=contention_wait.wait_until, **k: _o(*a, **{**k, "timeout": 0}))`. Two traps were MEASURED at review and must be avoided: `functools.partial(wait_until, timeout=0)` is a NO-OP mutation because `acquire_finalize_lock` passes `timeout=` explicitly and the call-site keyword wins (the mutated run still acquired, `polls 2`); and a lambda that closes over the patched name recurses (`RecursionError`). The default-argument capture above gave `err TransactionLockError polls 0` against `err None polls 2` unmutated. Paste both the mutated failure and the restored pass. Passing `timeout=0` at the test's own call site is NOT a valid mutation, since it changes the test rather than the code under test.
- Prove the scheduling-independence claim: run the rewritten tests with an injected delay between the holder's write and the parent's observation at several magnitudes (at minimum 0s and >=2s, past the OLD child's entire 1.0s hold) and show they pass at every magnitude.
- Run the full suite bare (`python3 -m pytest`) and paste the summary line.

## Spec / documentation sync

N/A with reason: no `.spec.md` governs these two tests, and the production contract they verify is unchanged. A search of `.aw/records/specs/` for `acquire_finalize_lock`, `FINALIZE_LOCK`, `finalize lock`, `contention_wait`, and `flaky` returned no matches, so there is no spec text to amend and `- Scope-Paths:` declares no spec file. The behavioral contract stays documented where it already is, in the `FINALIZE_LOCK_WAIT_SECONDS` docstring, which this plan does not edit.

## Open questions

### OQ-01: Should the poll-count floor be two observed polls, or exactly one?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Two. `contention_wait.wait_until` calls `try_once()` BEFORE its first `sleep`, so an uncontended acquire records zero sleep calls and any contended one records at least one; requiring two keeps a comfortable floor while still being strictly greater than the uncontended case, and the prototype measured `polls=3` at every stall magnitude (F-07), so a floor of two is not tight. This mirrors the existing `assertGreaterEqual(len(sleep_calls), 2)` in the neighboring `test_holder_releases_mid_wait_injected_clock`, so the two tests state the same floor the same way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: Paste the rewritten child source block from `tests/test_ipd_lifecycle_cli.py` showing the child waits on the release sentinel with its own bail-out deadline and contains no fixed `time.sleep(1.0)` hold. Paste the output of a run of `test_two_process_lock_wait_succeeds` showing it passes, plus the child's exit status observed by the test (`child.wait` returning 0), proving the handshake released the child rather than the cleanup killing it.
  - Observed evidence: Rewritten child source block from `tests/test_ipd_lifecycle_cli.py`:
    ```python
    sentinel = self.root / "release.sentinel"

    child_code = (
        "import os, sys, time, json\n"
        f"p = {repr(str(lock))}\n"
        f"sentinel = {repr(str(sentinel))}\n"
        "with open(p, 'w') as f: json.dump({'owner': 'child_worker', 'pid': os.getpid()}, f)\n"
        "deadline = time.monotonic() + 30.0\n"
        "while not os.path.exists(sentinel) and time.monotonic() < deadline:\n"
        "    time.sleep(0.01)\n"
        "try: os.unlink(p)\n"
        "except OSError: pass\n"
    )
    ```
    Test execution output:
    ```
    $ PYTHONPATH=. python3 -m unittest -v tests.test_ipd_lifecycle_cli.RollbackFailureSemanticsTests.test_two_process_lock_wait_succeeds
    test_two_process_lock_wait_succeeds (tests.test_ipd_lifecycle_cli.RollbackFailureSemanticsTests.test_two_process_lock_wait_succeeds)
    Two real processes: child holds lock until parent sentinel, parent waits and succeeds. ... ok

    ----------------------------------------------------------------------
    Ran 1 test in 0.596s

    OK
    ```
    Child exit status: `child_rc = child.wait(timeout=5)`; `self.assertEqual(child_rc, 0, "child process must exit 0 via handshake")` passed, proving child exited 0 via handshake.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the rewritten assertion block showing no `monotonic`/`elapsed` duration assertion remains in this test, and showing the poll-count floor, the per-poll holder-liveness samples, and `pid == os.getpid()` assertions (no taken-on-next-poll bound here; see E-03). Then paste BOTH halves of a mutation check, performed with the in-process `mock.patch.object` wrapper named in `## Required tests / validation` (no production file edited): with waiting neutralized the test FAILS, and with it restored the test PASSES. Finally paste a scheduling-independence run at stalls of at least 0s and 2s (2s being past the old child's entire 1.0s hold) showing a pass at each.
  - Observed evidence: Rewritten assertion block from `tests/test_ipd_lifecycle_cli.py`:
    ```python
    child_rc = child.wait(timeout=5)
    self.assertEqual(child_rc, 0, "child process must exit 0 via handshake")

    self.assertGreaterEqual(
        len(sleep_calls), 2, "acquire must have polled at least twice"
    )
    self.assertTrue(
        all(liveness_before_sentinel),
        "holder must be alive at every poll before release sentinel",
    )
    self.assertGreaterEqual(
        len(liveness_before_sentinel),
        2,
        "must have sampled liveness at least twice before release",
    )
    self.assertEqual(_json.loads(lock.read_text())["pid"], _os.getpid())
    LC.release_finalize_lock(self.root)
    ```
    Mutation check (`wait_until` timeout mocked to 0):
    Mutated run:
    ```
    ERROR: test_two_process_lock_wait_succeeds (tests.test_ipd_lifecycle_cli.RollbackFailureSemanticsTests.test_two_process_lock_wait_succeeds)
    Two real processes: child holds lock until parent sentinel, parent waits and succeeds.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_ipd_lifecycle_cli.py", line 1500, in test_two_process_lock_wait_succeeds
        LC.acquire_finalize_lock(
            self.root, "abc123", timeout=5.0, sleep=_handshake_sleep
        )
      File "agent_workflows/ipd_lifecycle.py", line 647, in acquire_finalize_lock
        raise TransactionLockError(
        ...
        )
    agent_workflows.ipd_lifecycle.TransactionLockError: ipd finalize writer lock held by active PID 967805 (owner child_worker) for longer than 5s

    FAILED (errors=1)
    Mutated result: wasSuccessful=False, errors=1, failures=0
    ```
    Restored run:
    ```
    test_two_process_lock_wait_succeeds (tests.test_ipd_lifecycle_cli.RollbackFailureSemanticsTests.test_two_process_lock_wait_succeeds) ... ok
    Ran 1 test in 0.394s
    OK
    Restored result: wasSuccessful=True
    ```
    Scheduling-independence run (stalls at 0s and 2s):
    ```
    --- Stalling 0.0s for test_two_process_lock_wait_succeeds ---
    test_two_process_lock_wait_succeeds ... ok
    Ran 1 test in 0.417s
    OK
    stall=0.0s result: wasSuccessful=True

    --- Stalling 2.0s for test_two_process_lock_wait_succeeds ---
    test_two_process_lock_wait_succeeds ... ok
    Ran 1 test in 2.371s
    OK
    stall=2.0s result: wasSuccessful=True
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the rewritten `test_finalize_lock_WAITS_for_a_short_lived_live_holder` showing the timed releasing thread and the `assertGreaterEqual(waited, 0.4, ...)` assertion are both gone, that the `run-20260927T001634Z-258437` provenance comment survives, that `holder.poll() is None` is still asserted, and that the former `assertLess(waited, 5, ...)` property is now asserted as the taken-on-next-poll bound rather than deleted. Paste a passing run, a mutation check (same in-process wrapper) showing it FAILS with waiting neutralized, and a stall run at 0s and 2s showing it passes at both. Paste a run of the whole `RollbackFailureSemanticsTests` class with its `N passed` line.
  - Observed evidence: Rewritten `test_finalize_lock_WAITS_for_a_short_lived_live_holder`:
    ```python
    def test_finalize_lock_WAITS_for_a_short_lived_live_holder(self):
        """A peer's sub-second hold must not refuse finalize (run-20260927T001634Z-258437)."""
        import json as _json
        import os as _os
        import subprocess as _subprocess
        import sys as _sys
        import time as _time

        lock = LC.finalize_lock_path(self.root)
        lock.parent.mkdir(parents=True, exist_ok=True)
        holder = _subprocess.Popen(
            [_sys.executable, "-c", "import time; time.sleep(60)"]
        )
        self.addCleanup(holder.wait)
        self.addCleanup(holder.kill)
        lock.write_text(
            _json.dumps({"owner": "git_commit_helper.offer_commit", "pid": holder.pid}),
            encoding="utf-8",
        )

        sleep_calls = []
        release_index = None

        def _handshake_sleep(sec):
            nonlocal release_index
            sleep_calls.append(sec)
            if len(sleep_calls) >= 2 and lock.exists():
                lock.unlink()  # the peer's `commit_lock.release`
                release_index = len(sleep_calls)
            _time.sleep(sec)

        LC.acquire_finalize_lock(
            self.root, "abc123", timeout=10, sleep=_handshake_sleep
        )
        self.assertGreaterEqual(
            len(sleep_calls), 2, "it must have WAITED for the live holder"
        )
        self.assertIsNotNone(
            release_index, "the lock must have been released during wait"
        )
        self.assertLessEqual(
            len(sleep_calls),
            release_index + 1,
            "it must take the lock as soon as the holder releases it",
        )
        self.assertEqual(_json.loads(lock.read_text())["pid"], _os.getpid())
        self.assertIsNone(holder.poll(), "waiting must never kill the holder")
        LC.release_finalize_lock(self.root)
    ```
    Passing run:
    ```
    test_finalize_lock_WAITS_for_a_short_lived_live_holder (tests.test_ipd_lifecycle_cli.RollbackFailureSemanticsTests.test_finalize_lock_WAITS_for_a_short_lived_live_holder) ... ok
    Ran 1 test in 0.291s
    OK
    Restored result: wasSuccessful=True
    ```
    Mutation check:
    ```
    ERROR: test_finalize_lock_WAITS_for_a_short_lived_live_holder (tests.test_ipd_lifecycle_cli.RollbackFailureSemanticsTests.test_finalize_lock_WAITS_for_a_short_lived_live_holder)
    Traceback (most recent call last):
      File "tests/test_ipd_lifecycle_cli.py", line 1342, in test_finalize_lock_WAITS_for_a_short_lived_live_holder
        LC.acquire_finalize_lock(
            self.root, "abc123", timeout=10, sleep=_handshake_sleep
        )
      File "agent_workflows/ipd_lifecycle.py", line 647, in acquire_finalize_lock
        raise TransactionLockError(...)
    agent_workflows.ipd_lifecycle.TransactionLockError: ipd finalize writer lock held by active PID 968267 (owner git_commit_helper.offer_commit) for longer than 10s

    FAILED (errors=1)
    Mutated result: wasSuccessful=False, errors=1, failures=0
    ```
    Stall run at 0s and 2s:
    ```
    --- Stalling 0.0s for test_finalize_lock_WAITS_for_a_short_lived_live_holder ---
    test_finalize_lock_WAITS_for_a_short_lived_live_holder ... ok
    Ran 1 test in 0.287s
    OK
    stall=0.0s result: wasSuccessful=True

    --- Stalling 2.0s for test_finalize_lock_WAITS_for_a_short_lived_live_holder ---
    test_finalize_lock_WAITS_for_a_short_lived_live_holder ... ok
    Ran 1 test in 2.333s
    OK
    stall=2.0s result: wasSuccessful=True
    ```
    Class run:
    ```
    $ python3 -m pytest tests/test_ipd_lifecycle_cli.py -k "RollbackFailureSemanticsTests"
    ....................                                                     [100%]
    20 passed in 11.96s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the exact search command(s) run over `tests/` for duration assertions against a fixed-duration holder (for example a search for `assertGreater`/`assertGreaterEqual`/`assertLess` near `monotonic`) and their full output, with a one-line disposition for every hit stating either that it is one of the two tests this plan fixes, or why it is not fragile in this direction (as recorded for `tests/test_platform_lock.py`), or that it was filed as a new backlog item (give the item id6). Paste the bare `python3 -m pytest` summary line for the full suite.
  - Observed evidence: Search command: `grep -rln "monotonic()" tests/*.py`.
    Output:
    ```
    tests/test_concurrent_driver_guard.py
    tests/test_ipd_lifecycle_cli.py
    tests/test_oc_runipd.py
    tests/test_permission_bound_disabled.py
    tests/test_platform_lock.py
    tests/test_runner_stop_triggers_e2e.py
    tests/test_statusline_ascii_mode.py
    tests/test_turn_bounds.py
    ```
    One-line dispositions:
    1. `tests/test_ipd_lifecycle_cli.py`: `test_two_process_lock_wait_succeeds` and `test_finalize_lock_WAITS_for_a_short_lived_live_holder` fixed in this IPD (duration thresholds replaced by handshake and poll counts).
    2. `tests/test_platform_lock.py`: Line 146 asserts upper bound `assertLess(elapsed, 5.0)` on non-blocking `LockBusy` refusal with 5s headroom (not fragile); lines 323, 325 print timing in subprocess order observation (no assertion).
    3. `tests/test_concurrent_driver_guard.py`: Line 745 is a bounded thread shutdown cleanup loop (`time.monotonic() - t < 20`); no wait duration assertion.
    4. `tests/test_oc_runipd.py`: Lines 1521, 1538 use synthetic monotonic timestamps to test idle string formatting; no contention waiting.
    5. `tests/test_permission_bound_disabled.py`: Lines 51, 55, 58 use deadline ceiling for mock event loop; asserts reap count, not duration against a fixed holder.
    6. `tests/test_runner_stop_triggers_e2e.py`: Lines 252, 272, 298 are bounded spin loops for IPC stop triggers; no hold duration assertion.
    7. `tests/test_statusline_ascii_mode.py`: Line 92 supplies run start timestamp to statusline renderer; no assertion.
    8. `tests/test_turn_bounds.py`: Lines 52, 60, 106, 115, 168 use elapsed time only in timeout diagnostics; no wait duration assertion against a fixed holder.
    Full test suite bare summary:
    ```
    $ python3 -m pytest
    6670 passed, 2 skipped, 3 warnings in 694.17s (0:11:34)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute this plan before it carries explicit human approval (`- Status: approved`). Execution is governed by the repository's agent execution contract: begin through `aw ipd begin` when executed by hand (in a runner-managed lane the runner owns the lifecycle and `aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001`), commit only the paths named in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never `-a`, never `--no-verify`), never push, and paste ACTUAL runner output for every test claim rather than asserting success. Run the suite bare as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

This plan must not be marked done, and must not move to `.aw/records/plans/executed/`, until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item above is `pass` with concrete pasted evidence. Under `aw oc run` / `aw agy run` the RUNNER performs the finalize and the move; executed by hand, the executor performs it via `aw ipd finalize`. Never hand-edit the status line or hand-move the file. Do NOT set backlog `4f7nlh` (already `graduated`, `Blocks-Release: next`) to any status: this plan is its `- From-Backlog:` carrier and closes the gate through the HANDOFF route on reaching `executed`.

SCOPE FENCE: `- Scope-Paths:` is a DECLARATION for finalize reconciliation, not a stop condition. An out-of-scope edit the work genuinely needs is made and justified at finalize with `--scope-reason`. E-04's further instances are RECORDED and filed, not edited, which is a scope choice, not a stop.

In particular V-02 and V-03 demand a MUTATION result: a rewritten test that passes but cannot be shown to fail when the waiting is removed has not been validated, because the whole point of this change is to keep the real regression detectable while removing the timing dependency. The mutation check is performed IN-PROCESS by the scratch wrapper, so no production file should be edited at all; show `git status --short agent_workflows/` empty before finalize regardless, since this plan declares no production path in scope.
