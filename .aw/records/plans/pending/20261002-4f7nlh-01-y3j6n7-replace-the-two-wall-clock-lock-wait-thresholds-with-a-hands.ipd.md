# IPD: Replace the two wall-clock lock-wait thresholds with a handshake so the finalize-lock contention tests prove waiting instead of timing it

- Date: 2026-10-02
- Kind: child
- Concern: Two tests in `RollbackFailureSemanticsTests` assert that `acquire_finalize_lock` waited by measuring WALL-CLOCK elapsed time against a fixed-duration holder, so ordinary scheduling delay under `-n auto` makes them fail on correct code.
- Scope: Rewrite `test_two_process_lock_wait_succeeds` and `test_finalize_lock_WAITS_for_a_short_lived_live_holder` in `tests/test_ipd_lifecycle_cli.py` to release their holder on a handshake and to assert on observed poll attempts plus lock ownership. No production code changes.
- Scope-Paths: tests/test_ipd_lifecycle_cli.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: 4f7nlh
- Blocks-Release: next
- Set: 4f7nlh
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: y3j6n7

## Workflow history

- 2026-10-02 draft (opencode): created.
- 2026-10-02 to-review (opencode): authored from backlog `4f7nlh`; root cause reproduced deterministically and the proposed fix mutation-checked before writing.

## Goal

Make the two finalize-lock contention tests fail only when `acquire_finalize_lock` genuinely stops waiting for a live holder. Today they also fail when the test process is merely descheduled, because they infer "it waited" from wall-clock elapsed time against a holder that releases on a fixed `time.sleep(1.0)` the test does not control.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Remove the timing dependency from the two-process test

- [ ] E-01 In `tests/test_ipd_lifecycle_cli.py`, change `RollbackFailureSemanticsTests.test_two_process_lock_wait_succeeds` so its child process holds the lock until the PARENT says to release it instead of for a fixed `time.sleep(1.0)`: have the child poll for a release sentinel file (bounded by its own bail-out deadline so an abandoned child cannot outlive the suite), and have the parent create that sentinel from inside the `sleep` callable it injects into `acquire_finalize_lock`, once at least two polls have been observed.
  - Depends on: none
  - Expected outcome: The holder's lifetime is controlled by the parent, so the child is still holding the lock at the moment the parent begins waiting no matter how long the parent was descheduled first.
  - Execution state: pending

- [ ] E-02 In the same test, replace the wall-clock assertion `assertGreater(elapsed, 0.7, ...)` with assertions that do not read the clock: assert the injected `sleep` callable was invoked at least twice (so the acquire provably POLLED rather than taking a free lock), assert the holder subprocess was still alive when the parent observed the lock (`child.poll() is None`), and keep the existing ownership assertion that the lock file's `pid` is `os.getpid()`. Also replace the bounded `for _ in range(50)` lock-appearance spin with a deadline-based wait so a slow child start is a wait rather than a failure.
  - Depends on: E-01
  - Expected outcome: The test asserts the waiting BEHAVIOR (polled while a live holder held it, then acquired it) and no longer asserts a duration.
  - Execution state: pending

### Task group 2: Fix the same defect in the sibling test

- [ ] E-03 Apply the same handshake treatment to `RollbackFailureSemanticsTests.test_finalize_lock_WAITS_for_a_short_lived_live_holder`, whose releasing thread sleeps a fixed `0.5` and whose `assertGreaterEqual(waited, 0.4, ...)` has the same wall-clock dependency with a tighter margin: release the lock from the injected `sleep` callable after at least two observed polls rather than from a timed thread, assert on the observed poll count, and keep its existing assertions that the lock is owned by this PID and that the holder subprocess was never killed (`holder.poll() is None`). Preserve the test's documented provenance comment naming `run-20260927T001634Z-258437`.
  - Depends on: none
  - Expected outcome: The sibling test proves the same contract (a live holder is waited for, a released lock is taken, the holder is never killed) without depending on when the test process is scheduled.
  - Execution state: pending

- [ ] E-04 Confirm no OTHER test in the repository asserts a finalize-lock or contention wait duration against a fixed-duration holder, and record the search performed. If another instance exists outside this plan's declared scope, do NOT widen scope: record it in the Findings section as a follow-up for a separate backlog item.
  - Depends on: none
  - Expected outcome: Either a recorded finding that these two were the only instances, or a recorded follow-up naming any further instance without editing it.
  - Execution state: pending

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
- Prove the rewritten tests are still sensitive: with the production waiting neutralized (the documented `timeout=0` check-once behavior, applied to a throwaway copy or via a temporary local edit that is reverted), each rewritten test must FAIL. Paste both the mutated failure and the restored pass.
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

- [ ] V-01 validates E-01
  - Required evidence: Paste the rewritten child source block from `tests/test_ipd_lifecycle_cli.py` showing the child waits on the release sentinel with its own bail-out deadline and contains no fixed `time.sleep(1.0)` hold. Paste the output of a run of `test_two_process_lock_wait_succeeds` showing it passes, plus the child's exit status observed by the test (`child.wait` returning 0), proving the handshake released the child rather than the cleanup killing it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the rewritten assertion block showing no `monotonic`/`elapsed` duration assertion remains in this test, and showing the poll-count, `child.poll() is None`, and `pid == os.getpid()` assertions. Then paste BOTH halves of a mutation check: with waiting neutralized (check-once `timeout=0`) the test FAILS, and with it restored the test PASSES. Finally paste a scheduling-independence run at stalls of at least 0s and 2s (2s being past the old child's entire 1.0s hold) showing a pass at each.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the rewritten `test_finalize_lock_WAITS_for_a_short_lived_live_holder` showing the timed releasing thread and the `assertGreaterEqual(waited, 0.4, ...)` assertion are both gone, that the `run-20260927T001634Z-258437` provenance comment survives, and that `holder.poll() is None` is still asserted. Paste a passing run, a mutation check showing it FAILS with waiting neutralized, and a stall run at 0s and 2s showing it passes at both. Paste a run of the whole `RollbackFailureSemanticsTests` class with its `N passed` line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the exact search command(s) run over `tests/` for duration assertions against a fixed-duration holder (for example a search for `assertGreater`/`assertGreaterEqual`/`assertLess` near `monotonic`) and their full output, with a one-line disposition for every hit stating either that it is one of the two tests this plan fixes, or why it is not fragile in this direction (as recorded for `tests/test_platform_lock.py`), or that it was filed as a new backlog item (give the item id6). Paste the bare `python3 -m pytest` summary line for the full suite.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Do not execute this plan before it carries explicit human approval (`- Status: approved`). Execution is governed by the repository's agent execution contract: begin through `aw ipd begin`, commit only the paths named in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never `-a`, never `--no-verify`), never push, and paste ACTUAL runner output for every test claim rather than asserting success. Run the suite bare as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

This plan must not be marked done, and must not move to `.aw/records/plans/executed/`, until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item above is `pass` with concrete pasted evidence. In particular V-02 and V-03 demand a MUTATION result: a rewritten test that passes but cannot be shown to fail when the waiting is removed has not been validated, because the whole point of this change is to keep the real regression detectable while removing the timing dependency. Any temporary edit made to production code to perform that mutation check must be reverted before finalize, and the clean `git status` for `agent_workflows/` shown, since this plan declares no production path in scope.
