# IPD: Serialize full suites machine-wide with a lock whose wait the stall watchdog sees

- Date: 2026-10-12
- Kind: child
- Concern: Nothing bounds how many full suites run at once on one machine. On 2026-10-12, seven concurrent drivers (four review sweeps, three execute runs) on a 12-core host ran load average 75-88; each execute turn's full suite (`python3 -m pytest` at `-n auto`) then outran the 900s stall watchdog, and runs `run-20261012T170951Z-1138207`, `run-20261012T170958Z-1138454` and `run-20261012T171028Z-1138872` lost 9 of 11 turns to `ipd-stalled` (each killed at exactly `stall_timeout: 900.0`). A lock alone would make this WORSE: an agent's `aw suite` blocked on a lock prints nothing the driver can see, because opencode reports a shell tool only when it completes, and `runner_shared.StallWatchdog._run` reaps on idle unless `progress_checker` reports progress.
- Scope: IN: a machine-wide slot lock taken inside `suite_cache.run_full_suite` (Order 02) around every cache-MISS run, default `max(1, os.cpu_count() // 6)` slots, configurable by `AW_SUITE_SLOTS`; a bounded, loud wait (a progress line at least every 60s, matching `INTEGRATION_LOCK_PROGRESS_SECONDS`); a heartbeat file the waiter touches, keyed by the agent turn's run and item ids, which both hosts' stall watchdogs read as progress; an env marker so a pytest launched by a test does not re-enter the lock; tests; docs. OUT: cache hits (they take no slot); narrowed runs (never pass through `aw suite`); bounding DRIVER concurrency or warning on host load (separate defect, deferred); changing the stall timeout default.
- Scope-Paths: agent_workflows/suite_cache.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/stall_progress.py, tests/test_suite_slot_lock.py, docs/cli-human-guide.md, CHANGELOG.md
- Item-Dependencies: executed:0o0wt2
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 58x9mw
- Blocks-Release: next
- Set: suiteeff
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xvm6no
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved

- 2026-10-13 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-010 (record `.aw/records/reviews/20261012-suiteeff-03-xvm6no-serialize-full-suites-machine-wide-with-a-lock-whose-wait-th.review.md`)
- 2026-10-13 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 03 of Set `suiteeff` from backlog `58x9mw`.

## Goal

At most N full suites run on a machine at once, a suite waiting for a slot says so every minute, and that waiting never gets an agent turn killed as stalled.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the slot lock

- [x] E-01 CAPTURE THE BASELINE: run the bare suite `aw suite --no-cache` (Order 02's command) before the first edit; record its summary line and failing node ids.
  - Depends on: none
  - Expected outcome: a recorded summary line and failing-node-id list.
  - Execution state: performed

- [x] E-02 In `suite_cache.py`, add `suite_slot(*, progress, heartbeat) -> ContextManager[SlotOutcome]`: N lock files `suite-slot-<k>.lock` (k in `0..N-1`, N the resolved slot count from Order 02's `AW_SUITE_SLOTS` resolution, reused and not re-implemented) under a MACHINE-wide, PER-USER directory resolved in this order: `AW_SUITE_LOCK_DIR` when set (tests and operators), else `$XDG_RUNTIME_DIR/agent-workflows/` when set, else `<tempfile.gettempdir()>/agent-workflows-<user>/` where `<user>` is `os.getuid()` on POSIX and `getpass.getuser()` where `getuid` does not exist (Windows is a supported platform, `platform_lock`); created with mode 0o700, and REFUSED (fail open: run without a slot, one stderr warning) when it already exists owned by another uid or writable by group/other, so another local user cannot pre-create it to block or spoof slots; each taken with `platform_lock.acquire(..., blocking=False)` in a poll loop (the integration lock's pattern: `platform_lock` reserves `blocking=True` to one caller). A sidecar holder file per slot (`suite-slot-<k>.holder.json`, written atomically AFTER the lock is held and removed on release) records pid, host, repo path, run id, item id6 and start time for diagnostics; it is advisory only and is NEVER used to decide whether a slot is free (the OS lock decides, so a holder file left by a crashed process cannot wedge a slot), and an unreadable or stale holder file renders as `unknown holder`. Poll every 1s (injectable `sleep`/`now`, as `runner_shared.integration_lock` does, so tests need not wait in real time). The wait is BOUNDED by `AW_SUITE_SLOT_TIMEOUT` (default 3600s; a non-positive or malformed value falls back to the default with one warning); on expiry it RUNS ANYWAY with a loud warning and `SlotOutcome.acquired=False`, rather than failing the suite, because a refused suite would fail an item over contention, which is worse than oversubscribing once. It prints `progress("aw suite: waiting for a test-suite slot (N of N held: <holder summaries>); waited <s>s")` IMMEDIATELY on the first busy poll and then every `INTEGRATION_LOCK_PROGRESS_SECONDS` (60s, reused, not a new constant), to stderr by default, and calls `heartbeat()` on every poll. Wrap the cache-MISS branch of `run_full_suite` in it, so EVERY caller of `run_full_suite` (the `aw suite` CLI and all three runner seams Order 02 routed through it) takes a slot; a cache hit takes no slot. Record `slot: {acquired, waited_seconds, slot_index}` on the `SuiteRunResult` (and so on the seams' records) so a reader can see contention. Machine-wide, not repo-wide, because the contended resource is the CPU. An unsupported lock primitive (`platform_lock` raising anything other than `LockBusy`) fails OPEN: run without a slot, one warning.
  - Depends on: E-01
  - Expected outcome: with `AW_SUITE_SLOTS=1`, a second concurrent `aw suite --no-cache` prints the waiting line on its first busy poll naming the first holder, and starts after the first finishes; a slot held by a killed process is free again immediately (the OS released the lock) even though its holder file remains.
  - Execution state: performed

- [x] E-03 Nested-run guard: `run_full_suite` sets `AW_SUITE_SLOT_HELD=1` in the suite's environment, and `suite_slot` is a no-op when that variable is already set, so a test that itself spawns `aw suite` or the runner's baseline inside a held slot cannot deadlock waiting on its parent. The marker is set ONLY in the suite child's environment and never in the parent process, so it cannot leak into the caller. Do NOT scrub it in `conftest.py`: tests run INSIDE a held slot, and a test that spawns `aw suite` relying on the inherited marker is exactly the nested case the guard exists for; a test that needs slot behavior sets `AW_SUITE_LOCK_DIR` and unsets the marker explicitly on the env it passes (E-06). HONEST LIMIT, stated because it is real: a test session already holding a slot runs any nested `aw suite` UNBOUNDED by the slot count, which is the intended trade (a deadlock is worse than one nested oversubscription).
  - Depends on: E-02
  - Expected outcome: with `AW_SUITE_SLOTS=1` and the single slot held, a nested `aw suite` launched with `AW_SUITE_SLOT_HELD=1` completes without waiting and prints no waiting line; the same launch without the marker waits.
  - Execution state: performed

### Task group 2: make the wait visible to the stall watchdog

- [x] E-04 Heartbeat channel. Define in `suite_cache.py` `heartbeat_path(run_id, item_id6) -> Path` under the same machine-wide directory (`heartbeat-<run_id>-<id6>`, both components validated against `[A-Za-z0-9._-]+` and anything else yields no path, so an environment value cannot steer the write outside the directory), and make `suite_slot`'s default `heartbeat` touch it (mtime update, creating it if absent) on every poll, using `AW_RUN_ID` / `AW_ITEM_ID6` (already exported to every agent turn by both launchers, `git_commit_helper.RUN_ID_ENV` / `ITEM_ID6_ENV`); with either unset it touches nothing. Also touch it WHILE the suite itself runs (a daemon thread inside `run_full_suite`, stopped and joined when the suite exits), at an interval of `min(60, AW_SUITE_HEARTBEAT_SECONDS)` where the env override exists only so tests need not wait 60s; so a long but healthy suite inside an agent turn is likewise visible, which removes the second half of the 2026-10-12 stall. The touching interval MUST be shorter than any stall timeout it is meant to defeat; 60s against the 900s default is a 15x margin, and the docs (E-06) say a `--stall-timeout` below 60s is not protected. Remove the heartbeat file when the driver's turn ends (E-05), so files do not accumulate. Add `stall_progress.SuiteHeartbeatObserver(run_id, id6)` whose `poll()` returns True when the heartbeat file's mtime advanced since the last poll (the first poll records the starting mtime, or absence, and returns False, so a file left by an earlier attempt is not mistaken for progress), fail-safe like `SubagentProgressObserver` (never raises, returns False on any error). It does NOT import `suite_cache` at module top level if that would create a cycle; it may recompute the path through a shared helper.
  - Depends on: E-02
  - Expected outcome: while a slot wait or a suite is in progress for a turn's run/item, the observer's `poll()` returns True at least once per minute; with no activity it returns False.
  - Execution state: performed

- [x] E-05 Wire the observer into both hosts' stall watchdogs. `StallWatchdog` takes one `progress_checker`; add a small combinator in `runner_shared` (`any_progress(*checkers)`, calling every checker each time so none is starved, swallowing exceptions per checker, returning True if any returned True) and pass `any_progress(<existing observer>.poll, SuiteHeartbeatObserver(run_id, id6).poll)` at the oc site (`oc_runipd.run_opencode`, where `watchdog.progress_checker = observer.poll`) and the agy site (`agy_runipd.run_agy_turn`, `StallWatchdog(process, timeout=stall_timeout, progress_checker=observer.poll)`), with `run_id`/`id6` taken from the SAME `state["run_id"]` / `item["id6"]` values those launchers export as `AW_RUN_ID`/`AW_ITEM_ID6`, so the watcher and the agent's `aw suite` agree on the path. Leave each host's `ProgressPoller` (which also drives the statusline) on its existing observer only: the heartbeat is consulted at the watchdog's pre-reap check, which is the decision that matters. Existing observers keep working unchanged. Remove the heartbeat file in each launcher's turn teardown (fail-safe).
  - Depends on: E-04
  - Expected outcome: a fake-host turn whose child is silent on stdout but touches the heartbeat path for its exported `AW_RUN_ID`/`AW_ITEM_ID6` more often than a short stall timeout is NOT reaped, while a fake child that is silent and touches nothing for the same period still is (measured at review: with today's code a silent fake opencode child under `stall_timeout: 1.0` raised `StallTimeout` after 1.78s).
  - Execution state: performed

### Task group 3: tests and docs

- [x] E-06 Add `tests/test_suite_slot_lock.py` (behavioral, P16; every cell sets `AW_SUITE_LOCK_DIR` to a per-test temp dir and pops `AW_SUITE_SLOT_HELD` from the env it passes, so the cells neither touch the real machine-wide directory nor inherit the outer suite's slot marker): (a) two subprocesses calling `suite_slot` with `AW_SUITE_SLOTS=1` serialize (recorded enter/exit timestamps prove non-overlap) and the waiter prints the waiting line naming the holder's pid; (b) with 2 slots, two hold concurrently and a third waits; (c) `AW_SUITE_SLOT_TIMEOUT=2` runs anyway, prints the warning and reports `acquired=False`; (d) the nested guard (E-03), both with and without the marker; (e) the heartbeat observer returns False on first poll, True after a touch, False again with no further touch, and never raises on a missing directory; (f) a holder killed with SIGKILL frees its slot for the next waiter despite its leftover holder file (POSIX only, skipped elsewhere); (g) END TO END on each host, using the harness shape of `tests/test_commit_run_trailers_env.py` (patch `observe_opencode_policy` and `lane_containment.record_host_posture`) but with a REAL child built by `support.make_fake_executable` rather than a mocked `Popen`: drive `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` with `options.stall_timeout` 1.0 and a child that stays silent on stdout for 4s while touching `suite_cache.heartbeat_path(os.environ["AW_RUN_ID"], os.environ["AW_ITEM_ID6"])` every 0.3s, and assert no `StallTimeout`; and a control child that sleeps silently for 4s DOES raise `StallTimeout`. The heartbeat cell uses the env-exported ids, which is the coupling under test.
  - Depends on: E-03, E-05
  - Expected outcome: the file passes; cell (g) fails on both hosts with E-05's wiring reverted.
  - Execution state: performed

- [x] E-07 Docs and CHANGELOG: a paragraph in `docs/cli-human-guide.md` beside Order 02's `aw suite` paragraph (slots and their default, `AW_SUITE_SLOTS`, `AW_SUITE_SLOT_TIMEOUT`, `AW_SUITE_LOCK_DIR`, what the waiting line means, that waiting never fails a suite, that a `--stall-timeout` below 60s is not protected by the heartbeat) and a `- Fixed:` bullet in `CHANGELOG.md`'s `## 2.0.0 (pending)` list; no em or en dashes.
  - Depends on: E-06
  - Expected outcome: both edits exist and contain no em or en dash.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Bounded, loud waits: `runner_shared.integration_lock` polls a non-blocking acquire and prints progress every `INTEGRATION_LOCK_PROGRESS_SECONDS` (60s) because "a silent block is operationally identical to a hang"; `platform_lock.acquire` reserves `blocking=True` to one caller.
- The stall watchdog's only extension seam is `progress_checker` (`StallWatchdog.__init__`); both hosts already pass an observer (`SubagentProgressObserver`, `AgyTranscriptProgressObserver`).
- Agent turns carry `AW_RUN_ID` and `AW_ITEM_ID6` (both launchers, "Always overwrite or pop, never inherit").
- Behavioral tests only (P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | Oversubscription caused the stalls. | 2026-10-12 load 75-88 on 12 cores; 9 of 11 execute turns across three runs `ipd-stalled` at 900s; review sweeps (no suite) 0 stalls. |
| F-02 | A long shell command is invisible to the driver. | Session `01-5s31xp-attempt-1.jsonl` ends with the agent's text "Baseline run first."; opencode log shows `python3 -m pytest -rf 2>&1 \| tail -15` evaluated at 17:12:25Z, turn reaped at 17:27:26Z with no further stdout event. |
| F-03 | The watchdog has a progress seam. | `StallWatchdog._run`: on idle >= timeout it calls `self._progress_checker()` and continues on True. |

## Proposed changes (ordered, validatable)

1. Slot lock with a bounded loud wait (E-02) and nested guard (E-03).
2. Heartbeat file and observer (E-04), wired on both hosts (E-05).
3. Tests (E-06) and docs (E-07).

## Deferred / out of scope (with reason)

- Bounding driver concurrency or refusing to start on a loaded host: a separate defect; this plan bounds the expensive part (suites).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Heartbeats for long shell commands other than `aw suite`: needs a general mechanism (opencode does not stream tool output); separate defect.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none; E-03 now decides `conftest.py` is NOT changed and says why.

## Required tests / validation

New `tests/test_suite_slot_lock.py`; existing stall-watchdog and launcher tests must still pass: `tests/test_oc_runipd.py::StallWatchdogTests`, `tests/test_stall_progress_agy.py` (the file named `tests/test_stall_progress.py` before review does not exist), `tests/test_commit_run_trailers_env.py`, `tests/test_interrupt_attempt_metadata.py`, and Order 02's `tests/test_suite_cache.py`; post-change `aw suite --no-cache` against E-01. Invariants: (I1) at most N concurrent cache-miss suites per user per machine; (I2) a wait never fails a suite and is never silent past its first busy poll; (I3) a stale holder file never blocks a slot; (I4) the stall watchdog treats an advancing heartbeat for the turn's own run/item as progress and nothing else changes for a turn that never touches it.

## Spec / documentation sync

`docs/cli-human-guide.md`, `CHANGELOG.md` (the docs E-item). No spec amendment: spec `25kzda` classifies "stall or turn-limit expiry" as `failed-safely`/`timeout` with evidence "turn timer or runner watchdog" (its failure-class table) and does not enumerate the watchdog's progress sources, so adding one changes no spec text.

## Open questions

### OQ-01: Slot count default?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED to `max(1, cpu_count // 6)` (2 on 12 cores), paired with Order 02's `-n = max(2, cpu_count // slots)` (6 workers each), so two suites together use the cores once. One slot would queue seven drivers behind a 216s-median, 622s-p90 suite; see orchestrator `z3cqvz` OQ-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted pre-change summary line and failing node ids.
  - Observed evidence:
```
Pre-change baseline run:
$ python3 -m agent_workflows suite --no-cache
=============================== warnings summary ===============================
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_KILLED_holder_does_not_strand_the_lock
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_second_holder_is_genuinely_EXCLUDED_and_the_holder_is_NAMED
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_the_lock_is_reacquirable_after_the_holder_exits
  <python-lib>/multiprocessing/popen_fork.py:76: DeprecationWarning: This process (pid=3456886) is multi-threaded, use of fork() may lead to deadlocks in the child.
    self.pid = os.fork()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
NOTE: 292 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
8364 passed, 4 skipped, 18 xfailed, 3 warnings in 778.27s (0:12:58)

Failing node ids: none (0 failures).
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted terminal output of two concurrent `AW_SUITE_SLOTS=1 aw suite --no-cache` runs in this checkout, the second showing at least one waiting line naming the first's pid and repo, with start/end timestamps showing no overlap, and the second's `--agent` record showing `slot.waited_seconds > 0` (code path: `run_full_suite` -> `suite_slot`); plus E-06 cells (a), (b), (c) and (f) passing.
  - Observed evidence:
```
Two concurrent runs in this checkout with AW_SUITE_SLOTS=1:
Run 1 started at 2026-10-14T07:02:41.923420+00:00 (PID 3526900), ended at 2026-10-14T07:08:16.431758+00:00, rc 0.
Run 2 started at 2026-10-14T07:02:51.926874+00:00 (PID 3527236), ended at 2026-10-14T07:18:01.272978+00:00.

Run 2 stderr showing periodic waiting lines naming first holder pid and repo:
aw suite: waiting for a test-suite slot (1 of 1 held: pid 3526900 (/mnt/md1/VC/agent-workflows/.aw/worktrees/xvm6no)); waited 0s
aw suite: waiting for a test-suite slot (1 of 1 held: pid 3526900 (/mnt/md1/VC/agent-workflows/.aw/worktrees/xvm6no)); waited 60s
aw suite: waiting for a test-suite slot (1 of 1 held: pid 3526900 (/mnt/md1/VC/agent-workflows/.aw/worktrees/xvm6no)); waited 120s
aw suite: waiting for a test-suite slot (1 of 1 held: pid 3526900 (/mnt/md1/VC/agent-workflows/.aw/worktrees/xvm6no)); waited 180s
aw suite: waiting for a test-suite slot (1 of 1 held: pid 3526900 (/mnt/md1/VC/agent-workflows/.aw/worktrees/xvm6no)); waited 240s
aw suite: waiting for a test-suite slot (1 of 1 held: pid 3526900 (/mnt/md1/VC/agent-workflows/.aw/worktrees/xvm6no)); waited 301s

Run 2 machine --agent record slot object:
"slot":{"slot_acquired":true,"acquired":true,"waited_seconds":323.579,"slot_index":0,"timeout_seconds":0.0}

Timestamps prove non-overlap: Run 1 released slot at 07:08:16; Run 2 acquired slot at 07:08:16 after waiting 323.579s.

E-06 cells (a), (b), (c), (f) passing:
$ python3 -m pytest tests/test_suite_slot_lock.py -k "test_two_subprocesses or test_two_slots or test_slot_timeout or test_dead_holder" -v
tests/test_suite_slot_lock.py::test_two_subprocesses_serialize_and_print_waiting_line PASSED
tests/test_suite_slot_lock.py::test_two_slots_concurrent_and_third_waits PASSED
tests/test_suite_slot_lock.py::test_slot_timeout_runs_anyway_with_warning PASSED
tests/test_suite_slot_lock.py::test_dead_holder_frees_slot_despite_leftover_file PASSED
4 passed in 7.02s
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted E-06 cell (d) passing in both directions, and `git diff --stat conftest.py` showing it unchanged.
  - Observed evidence:
```
$ python3 -m pytest tests/test_suite_slot_lock.py::test_nested_guard_with_and_without_marker -v
tests/test_suite_slot_lock.py::test_nested_guard_with_and_without_marker PASSED [100%]
1 passed in 0.46s

$ git diff --stat conftest.py
(empty output, conftest.py unmodified)
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted E-06 cell (e) passing plus a `stat -c %Y` sequence of a heartbeat file taken 60s apart during a real `aw suite` run with `AW_RUN_ID`/`AW_ITEM_ID6` set, showing the mtime advancing.
  - Observed evidence:
```
$ python3 -m pytest tests/test_suite_slot_lock.py::test_heartbeat_observer_lifecycle_and_nonexistent_dir -v
tests/test_suite_slot_lock.py::test_heartbeat_observer_lifecycle_and_nonexistent_dir PASSED [100%]
1 passed in 0.12s

Heartbeat file stat -c %Y sequence sampled at 60s intervals during real aw suite run:
2026-10-14T07:03:51.929027+00:00: 1791961431
2026-10-14T07:04:51.933536+00:00: 1791961491
2026-10-14T07:05:51.933691+00:00: 1791961551
(mtime advanced by +60 seconds at each 60s sample)
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted E-06 cell (g) passing on both hosts, and failing on both with the E-05 wiring reverted (then restored); pasted passing `tests/test_oc_runipd.py::StallWatchdogTests`, `tests/test_stall_progress_agy.py`, `tests/test_commit_run_trailers_env.py` and `tests/test_interrupt_attempt_metadata.py`.
  - Observed evidence:
```
Cell (g) passing on both hosts (with E-05 wiring):
$ python3 -m pytest tests/test_suite_slot_lock.py -k "test_stall_watchdog_heartbeat_e2e" -v
tests/test_suite_slot_lock.py::test_stall_watchdog_heartbeat_e2e_oc PASSED [ 50%]
tests/test_suite_slot_lock.py::test_stall_watchdog_heartbeat_e2e_agy PASSED [100%]
2 passed in 12.01s

Cell (g) failing on both hosts when E-05 wiring is reverted (hb_child reaped as stalled):
$ python3 -m pytest tests/test_suite_slot_lock.py -k "test_stall_watchdog_heartbeat_e2e" -v
FAILED tests/test_suite_slot_lock.py::test_stall_watchdog_heartbeat_e2e_oc - agent_workflows.runner_shared.StallTimeout: OpenCode child turn stalled: no output for 2s
FAILED tests/test_suite_slot_lock.py::test_stall_watchdog_heartbeat_e2e_agy - agent_workflows.runner_shared.StallTimeout: Antigravity child turn stalled: no output for 2s
2 failed in 5.34s

Cell (g) restored and passing on both hosts:
2 passed in 12.01s

Existing watchdog and runner test suites passing:
$ python3 -m pytest tests/test_oc_runipd.py::StallWatchdogTests tests/test_stall_progress_agy.py tests/test_commit_run_trailers_env.py tests/test_interrupt_attempt_metadata.py -v
============================== 32 passed in 9.41s ==============================
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted passing `python3 -m pytest tests/test_suite_slot_lock.py` with the per-cell result lines (`-rA`); pasted post-change `aw suite --no-cache` summary with no new failing node id versus V-01.
  - Observed evidence:
```
$ python3 -m pytest tests/test_suite_slot_lock.py -rA
=========================== short test summary info ============================
PASSED tests/test_suite_slot_lock.py::test_heartbeat_observer_lifecycle_and_nonexistent_dir
PASSED tests/test_suite_slot_lock.py::test_nested_guard_with_and_without_marker
PASSED tests/test_suite_slot_lock.py::test_dead_holder_frees_slot_despite_leftover_file
PASSED tests/test_suite_slot_lock.py::test_two_slots_concurrent_and_third_waits
PASSED tests/test_suite_slot_lock.py::test_slot_timeout_runs_anyway_with_warning
PASSED tests/test_suite_slot_lock.py::test_two_subprocesses_serialize_and_print_waiting_line
PASSED tests/test_suite_slot_lock.py::test_stall_watchdog_heartbeat_e2e_oc
PASSED tests/test_suite_slot_lock.py::test_stall_watchdog_heartbeat_e2e_agy
8 passed in 8.20s

Post-change full suite run:
$ python3 -m agent_workflows suite --no-cache
=============================== warnings summary ===============================
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_KILLED_holder_does_not_strand_the_lock
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_second_holder_is_genuinely_EXCLUDED_and_the_holder_is_NAMED
tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_the_lock_is_reacquirable_after_the_holder_exits
  <python-lib>/multiprocessing/popen_fork.py:76: DeprecationWarning: This process (pid=4028573) is multi-threaded, use of fork() may lead to deadlocks in the child.
    self.pid = os.fork()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
NOTE: 292 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
8372 passed, 4 skipped, 18 xfailed, 3 warnings in 506.43s (0:08:26)

Failing node ids: none (0 failures, 8372 passed vs pre-change 8364 passed + 8 new tests).
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: `git diff docs/cli-human-guide.md CHANGELOG.md` pasted, and `git diff -U0 docs/cli-human-guide.md CHANGELOG.md | grep -nP '^\+.*[\x{2013}\x{2014}]'` pasted returning nothing.
  - Observed evidence:
```
$ git diff docs/cli-human-guide.md CHANGELOG.md
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 2c4c20d47..1ec891512 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -25,6 +25,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th
 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

 - Changed: added `aw suite` (`agent_workflows/suite_cache.py`) as the single full-suite entry point with a tree-keyed result cache in `<git-common-dir>/aw-suite-cache` (14-day expiry, `--no-cache` bypass, `--explain` key breakdown) and a bounded xdist worker count (`max(2, cpus // slots)` from `AW_SUITE_SLOTS`, default `max(1, cpus // 6)`), and routed the runner's `run_suite_check`, `start_suite_baseline`, and `make_integration_validation_runner` seams through `run_full_suite` so an exact-key cached pass is reused across lanes and checkouts while a cached failure is never served to a gate.
+- Fixed: concurrent test suite oversubscription across driver runs is now prevented machine-wide by a slot lock (`AW_SUITE_SLOTS`, default `max(1, cpus // 6)`) with bounded loud waiting, nested-run protection (`AW_SUITE_SLOT_HELD`), and a periodic stall watchdog heartbeat channel wired into both OpenCode and Antigravity drivers.
 - Added: red-CI run-start gate on `aw oc run` and `aw agy run` refuses to start new run work (including under `--prepare-only`) when the saved checkup record reports CI's last pass is more than `ci_checkup_interval_commits` first-parent commits behind `ci_checkup_branch`, unless every selected plan belongs to a Set in `ci_red_exempt_sets` (default `[]`, configured to `["cihealth"]` in this repository) or `--allow-red-ci "<why>"` is provided with a recorded justification; unknown CI state warns without blocking, and durable `red-ci` refusals are shown by `aw runs`.
 - Added: read-only `aw releases readiness` command (and `aw release readiness` alias) to evaluate and render the GO / NO-GO release-readiness report in human, `--json`, and `--agent` modes, exiting 0 on GO, 1 on NO-GO, and 2 on cannot-run. Explicit `--suite-passed` / `--suite-failed` and `--residual-risk-signer` flags supply human attestations without guessing defaults, and `release_readiness.gate_full_suite(None)` reports `full suite result not supplied` instead of `full suite RED`.
 - Fixed: the run dashboard and verifier corroboration now count an Antigravity tool call that ended in the FAILED state, matching what the live stream shows.
diff --git a/docs/cli-human-guide.md b/docs/cli-human-guide.md
index 46c605f62..bae4f9eb4 100644
--- a/docs/cli-human-guide.md
+++ b/docs/cli-human-guide.md
@@ -131,3 +131,5 @@ profile.
 ## Running the full test suite (`aw suite`)

 `aw suite` runs or serves the repository's bare full `pytest` suite with a bounded xdist worker count (`max(2, cpus // slots)` where `slots` comes from `AW_SUITE_SLOTS`, default `max(1, cpus // 6)`) and caches passing verdicts and confirmed reproducible failures in `<git-common-dir>/aw-suite-cache/<digest>.json` with a 14-day expiry. The cache key (`digest`) is a SHA-256 over the working-tree git tree (including tracked edits and untracked non-ignored files), the normalized argv after the interpreter (excluding `-n`), `sys.version` and `sys.executable`, the sorted `name==version` installed distributions, and behavior-changing environment variables (`PYTEST_ADDOPTS`, `PYTHONPATH`, `AW_NO_REEXEC`, `NO_COLOR`, `FORCE_COLOR`, `TERM`, and `AW_EXECUTION_ROLE`; inspect with `aw suite --explain`). State outside the key (wall clock, network, or `.aw/state`) is bounded by default marker deselection (`slow` and `livecorpus`), per-test `AW_HOME`/`XDG_CONFIG_HOME` sandboxing, and the 14-day record expiry; pass `--no-cache` to force a fresh run and update the stored entry. A cached failure is advisory for `aw suite` only and never reaches a runner gate (every gate failure and gate re-check is always an observed live run).
+
+Cache misses serialize across all runs on the machine using a slot lock under `AW_SUITE_LOCK_DIR` (defaults to `$XDG_RUNTIME_DIR/agent-workflows` or `/tmp/agent-workflows-<uid>`). The number of slots defaults to `max(1, cpus // 6)` and can be configured with `AW_SUITE_SLOTS`. When all slots are busy, `aw suite` prints periodic waiting lines showing holder pids and elapsed wait time. Waiting never fails a suite: if the wait exceeds `AW_SUITE_SLOT_TIMEOUT` (default 3600s), `aw suite` prints a warning and runs anyway without a slot. While waiting or running a suite inside a driver turn, `aw suite` touches a machine-wide heartbeat file every 60 seconds to signal ongoing progress to the runner stall watchdog; turns configured with a `--stall-timeout` below 60s are not protected by this heartbeat.

$ git diff -U0 docs/cli-human-guide.md CHANGELOG.md | grep -nP '^\+.*[\x{2013}\x{2014}]'
(empty output, returncode 1)
```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its open question (OQ-01) is resolved. Depends on `0o0wt2` executed: if `agent_workflows/suite_cache.py` or `run_full_suite` is absent when you begin, STOP and report (a prerequisite whose symbols are absent), because every item builds inside it. Run `aw ipd begin xvm6no` before the first edit. Scope fence: `- Scope-Paths:` declares every path this plan expects to change; an out-of-scope edit is made and then JUSTIFIED at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every `V-*` MUST carry the ACTUAL pasted runner output; never claim a pass that was not run. Commit only Scope-Paths via `aw commit xvm6no -- <paths>`; never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns the terminal transition and the executor does NOT run `aw ipd finalize`; run by hand, finish with `aw ipd finalize xvm6no` once `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status: executed` and never `git mv` the file.
