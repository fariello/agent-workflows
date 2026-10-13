# IPD: Serialize full suites machine-wide with a lock whose wait the stall watchdog sees

- Date: 2026-10-12
- Kind: child
- Concern: Nothing bounds how many full suites run at once on one machine. On 2026-10-12, seven concurrent drivers (four review sweeps, three execute runs) on a 12-core host ran load average 75-88; each execute turn's full suite (`python3 -m pytest` at `-n auto`) then outran the 900s stall watchdog, and runs `run-20261012T170951Z-1138207`, `run-20261012T170958Z-1138454` and `run-20261012T171028Z-1138872` lost 9 of 11 turns to `ipd-stalled` (each killed at exactly `stall_timeout: 900.0`). A lock alone would make this WORSE: an agent's `aw suite` blocked on a lock prints nothing the driver can see, because opencode reports a shell tool only when it completes, and `runner_shared.StallWatchdog._run` reaps on idle unless `progress_checker` reports progress.
- Scope: IN: a machine-wide slot lock taken inside `suite_cache.run_full_suite` (Order 02) around every cache-MISS run, default `max(1, os.cpu_count() // 6)` slots, configurable by `AW_SUITE_SLOTS`; a bounded, loud wait (a progress line at least every 60s, matching `INTEGRATION_LOCK_PROGRESS_SECONDS`); a heartbeat file the waiter touches, keyed by the agent turn's run and item ids, which both hosts' stall watchdogs read as progress; an env marker so a pytest launched by a test does not re-enter the lock; tests; docs. OUT: cache hits (they take no slot); narrowed runs (never pass through `aw suite`); bounding DRIVER concurrency or warning on host load (separate defect, deferred); changing the stall timeout default.
- Scope-Paths: agent_workflows/suite_cache.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/stall_progress.py, tests/test_suite_slot_lock.py, docs/cli-human-guide.md, CHANGELOG.md
- Item-Dependencies: executed:0o0wt2
- Status: reviewed
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

## Workflow history

- 2026-10-13 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-010 (record `.aw/records/reviews/20261012-suiteeff-03-xvm6no-serialize-full-suites-machine-wide-with-a-lock-whose-wait-th.review.md`)
- 2026-10-13 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 03 of Set `suiteeff` from backlog `58x9mw`.

## Goal

At most N full suites run on a machine at once, a suite waiting for a slot says so every minute, and that waiting never gets an agent turn killed as stalled.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the slot lock

- [ ] E-01 CAPTURE THE BASELINE: run the bare suite `aw suite --no-cache` (Order 02's command) before the first edit; record its summary line and failing node ids.
  - Depends on: none
  - Expected outcome: a recorded summary line and failing-node-id list.
  - Execution state: pending

- [ ] E-02 In `suite_cache.py`, add `suite_slot(*, progress, heartbeat) -> ContextManager[SlotOutcome]`: N lock files `suite-slot-<k>.lock` (k in `0..N-1`, N the resolved slot count from Order 02's `AW_SUITE_SLOTS` resolution, reused and not re-implemented) under a MACHINE-wide, PER-USER directory resolved in this order: `AW_SUITE_LOCK_DIR` when set (tests and operators), else `$XDG_RUNTIME_DIR/agent-workflows/` when set, else `<tempfile.gettempdir()>/agent-workflows-<user>/` where `<user>` is `os.getuid()` on POSIX and `getpass.getuser()` where `getuid` does not exist (Windows is a supported platform, `platform_lock`); created with mode 0o700, and REFUSED (fail open: run without a slot, one stderr warning) when it already exists owned by another uid or writable by group/other, so another local user cannot pre-create it to block or spoof slots; each taken with `platform_lock.acquire(..., blocking=False)` in a poll loop (the integration lock's pattern: `platform_lock` reserves `blocking=True` to one caller). A sidecar holder file per slot (`suite-slot-<k>.holder.json`, written atomically AFTER the lock is held and removed on release) records pid, host, repo path, run id, item id6 and start time for diagnostics; it is advisory only and is NEVER used to decide whether a slot is free (the OS lock decides, so a holder file left by a crashed process cannot wedge a slot), and an unreadable or stale holder file renders as `unknown holder`. Poll every 1s (injectable `sleep`/`now`, as `runner_shared.integration_lock` does, so tests need not wait in real time). The wait is BOUNDED by `AW_SUITE_SLOT_TIMEOUT` (default 3600s; a non-positive or malformed value falls back to the default with one warning); on expiry it RUNS ANYWAY with a loud warning and `SlotOutcome.acquired=False`, rather than failing the suite, because a refused suite would fail an item over contention, which is worse than oversubscribing once. It prints `progress("aw suite: waiting for a test-suite slot (N of N held: <holder summaries>); waited <s>s")` IMMEDIATELY on the first busy poll and then every `INTEGRATION_LOCK_PROGRESS_SECONDS` (60s, reused, not a new constant), to stderr by default, and calls `heartbeat()` on every poll. Wrap the cache-MISS branch of `run_full_suite` in it, so EVERY caller of `run_full_suite` (the `aw suite` CLI and all three runner seams Order 02 routed through it) takes a slot; a cache hit takes no slot. Record `slot: {acquired, waited_seconds, slot_index}` on the `SuiteRunResult` (and so on the seams' records) so a reader can see contention. Machine-wide, not repo-wide, because the contended resource is the CPU. An unsupported lock primitive (`platform_lock` raising anything other than `LockBusy`) fails OPEN: run without a slot, one warning.
  - Depends on: E-01
  - Expected outcome: with `AW_SUITE_SLOTS=1`, a second concurrent `aw suite --no-cache` prints the waiting line on its first busy poll naming the first holder, and starts after the first finishes; a slot held by a killed process is free again immediately (the OS released the lock) even though its holder file remains.
  - Execution state: pending

- [ ] E-03 Nested-run guard: `run_full_suite` sets `AW_SUITE_SLOT_HELD=1` in the suite's environment, and `suite_slot` is a no-op when that variable is already set, so a test that itself spawns `aw suite` or the runner's baseline inside a held slot cannot deadlock waiting on its parent. The marker is set ONLY in the suite child's environment and never in the parent process, so it cannot leak into the caller. Do NOT scrub it in `conftest.py`: tests run INSIDE a held slot, and a test that spawns `aw suite` relying on the inherited marker is exactly the nested case the guard exists for; a test that needs slot behavior sets `AW_SUITE_LOCK_DIR` and unsets the marker explicitly on the env it passes (E-06). HONEST LIMIT, stated because it is real: a test session already holding a slot runs any nested `aw suite` UNBOUNDED by the slot count, which is the intended trade (a deadlock is worse than one nested oversubscription).
  - Depends on: E-02
  - Expected outcome: with `AW_SUITE_SLOTS=1` and the single slot held, a nested `aw suite` launched with `AW_SUITE_SLOT_HELD=1` completes without waiting and prints no waiting line; the same launch without the marker waits.
  - Execution state: pending

### Task group 2: make the wait visible to the stall watchdog

- [ ] E-04 Heartbeat channel. Define in `suite_cache.py` `heartbeat_path(run_id, item_id6) -> Path` under the same machine-wide directory (`heartbeat-<run_id>-<id6>`, both components validated against `[A-Za-z0-9._-]+` and anything else yields no path, so an environment value cannot steer the write outside the directory), and make `suite_slot`'s default `heartbeat` touch it (mtime update, creating it if absent) on every poll, using `AW_RUN_ID` / `AW_ITEM_ID6` (already exported to every agent turn by both launchers, `git_commit_helper.RUN_ID_ENV` / `ITEM_ID6_ENV`); with either unset it touches nothing. Also touch it WHILE the suite itself runs (a daemon thread inside `run_full_suite`, stopped and joined when the suite exits), at an interval of `min(60, AW_SUITE_HEARTBEAT_SECONDS)` where the env override exists only so tests need not wait 60s; so a long but healthy suite inside an agent turn is likewise visible, which removes the second half of the 2026-10-12 stall. The touching interval MUST be shorter than any stall timeout it is meant to defeat; 60s against the 900s default is a 15x margin, and the docs (E-06) say a `--stall-timeout` below 60s is not protected. Remove the heartbeat file when the driver's turn ends (E-05), so files do not accumulate. Add `stall_progress.SuiteHeartbeatObserver(run_id, id6)` whose `poll()` returns True when the heartbeat file's mtime advanced since the last poll (the first poll records the starting mtime, or absence, and returns False, so a file left by an earlier attempt is not mistaken for progress), fail-safe like `SubagentProgressObserver` (never raises, returns False on any error). It does NOT import `suite_cache` at module top level if that would create a cycle; it may recompute the path through a shared helper.
  - Depends on: E-02
  - Expected outcome: while a slot wait or a suite is in progress for a turn's run/item, the observer's `poll()` returns True at least once per minute; with no activity it returns False.
  - Execution state: pending

- [ ] E-05 Wire the observer into both hosts' stall watchdogs. `StallWatchdog` takes one `progress_checker`; add a small combinator in `runner_shared` (`any_progress(*checkers)`, calling every checker each time so none is starved, swallowing exceptions per checker, returning True if any returned True) and pass `any_progress(<existing observer>.poll, SuiteHeartbeatObserver(run_id, id6).poll)` at the oc site (`oc_runipd.run_opencode`, where `watchdog.progress_checker = observer.poll`) and the agy site (`agy_runipd.run_agy_turn`, `StallWatchdog(process, timeout=stall_timeout, progress_checker=observer.poll)`), with `run_id`/`id6` taken from the SAME `state["run_id"]` / `item["id6"]` values those launchers export as `AW_RUN_ID`/`AW_ITEM_ID6`, so the watcher and the agent's `aw suite` agree on the path. Leave each host's `ProgressPoller` (which also drives the statusline) on its existing observer only: the heartbeat is consulted at the watchdog's pre-reap check, which is the decision that matters. Existing observers keep working unchanged. Remove the heartbeat file in each launcher's turn teardown (fail-safe).
  - Depends on: E-04
  - Expected outcome: a fake-host turn whose child is silent on stdout but touches the heartbeat path for its exported `AW_RUN_ID`/`AW_ITEM_ID6` more often than a short stall timeout is NOT reaped, while a fake child that is silent and touches nothing for the same period still is (measured at review: with today's code a silent fake opencode child under `stall_timeout: 1.0` raised `StallTimeout` after 1.78s).
  - Execution state: pending

### Task group 3: tests and docs

- [ ] E-06 Add `tests/test_suite_slot_lock.py` (behavioral, P16; every cell sets `AW_SUITE_LOCK_DIR` to a per-test temp dir and pops `AW_SUITE_SLOT_HELD` from the env it passes, so the cells neither touch the real machine-wide directory nor inherit the outer suite's slot marker): (a) two subprocesses calling `suite_slot` with `AW_SUITE_SLOTS=1` serialize (recorded enter/exit timestamps prove non-overlap) and the waiter prints the waiting line naming the holder's pid; (b) with 2 slots, two hold concurrently and a third waits; (c) `AW_SUITE_SLOT_TIMEOUT=2` runs anyway, prints the warning and reports `acquired=False`; (d) the nested guard (E-03), both with and without the marker; (e) the heartbeat observer returns False on first poll, True after a touch, False again with no further touch, and never raises on a missing directory; (f) a holder killed with SIGKILL frees its slot for the next waiter despite its leftover holder file (POSIX only, skipped elsewhere); (g) END TO END on each host, using the harness shape of `tests/test_commit_run_trailers_env.py` (patch `observe_opencode_policy` and `lane_containment.record_host_posture`) but with a REAL child built by `support.make_fake_executable` rather than a mocked `Popen`: drive `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` with `options.stall_timeout` 1.0 and a child that stays silent on stdout for 4s while touching `suite_cache.heartbeat_path(os.environ["AW_RUN_ID"], os.environ["AW_ITEM_ID6"])` every 0.3s, and assert no `StallTimeout`; and a control child that sleeps silently for 4s DOES raise `StallTimeout`. The heartbeat cell uses the env-exported ids, which is the coupling under test.
  - Depends on: E-03, E-05
  - Expected outcome: the file passes; cell (g) fails on both hosts with E-05's wiring reverted.
  - Execution state: pending

- [ ] E-07 Docs and CHANGELOG: a paragraph in `docs/cli-human-guide.md` beside Order 02's `aw suite` paragraph (slots and their default, `AW_SUITE_SLOTS`, `AW_SUITE_SLOT_TIMEOUT`, `AW_SUITE_LOCK_DIR`, what the waiting line means, that waiting never fails a suite, that a `--stall-timeout` below 60s is not protected by the heartbeat) and a `- Fixed:` bullet in `CHANGELOG.md`'s `## 2.0.0 (pending)` list; no em or en dashes.
  - Depends on: E-06
  - Expected outcome: both edits exist and contain no em or en dash.
  - Execution state: pending

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
- Heartbeats for long shell commands other than `aw suite`: needs a general mechanism (opencode does not stream tool output); separate defect.

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

- [ ] V-01 validates E-01
  - Required evidence: the pasted pre-change summary line and failing node ids.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted terminal output of two concurrent `AW_SUITE_SLOTS=1 aw suite --no-cache` runs in this checkout, the second showing at least one waiting line naming the first's pid and repo, with start/end timestamps showing no overlap, and the second's `--agent` record showing `slot.waited_seconds > 0` (code path: `run_full_suite` -> `suite_slot`); plus E-06 cells (a), (b), (c) and (f) passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted E-06 cell (d) passing in both directions, and `git diff --stat conftest.py` showing it unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted E-06 cell (e) passing plus a `stat -c %Y` sequence of a heartbeat file taken 60s apart during a real `aw suite` run with `AW_RUN_ID`/`AW_ITEM_ID6` set, showing the mtime advancing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted E-06 cell (g) passing on both hosts, and failing on both with the E-05 wiring reverted (then restored); pasted passing `tests/test_oc_runipd.py::StallWatchdogTests`, `tests/test_stall_progress_agy.py`, `tests/test_commit_run_trailers_env.py` and `tests/test_interrupt_attempt_metadata.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted passing `python3 -m pytest tests/test_suite_slot_lock.py` with the per-cell result lines (`-rA`); pasted post-change `aw suite --no-cache` summary with no new failing node id versus V-01.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: `git diff docs/cli-human-guide.md CHANGELOG.md` pasted, and `git diff -U0 docs/cli-human-guide.md CHANGELOG.md | grep -nP '^\+.*[\x{2013}\x{2014}]'` pasted returning nothing.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its open question (OQ-01) is resolved. Depends on `0o0wt2` executed: if `agent_workflows/suite_cache.py` or `run_full_suite` is absent when you begin, STOP and report (a prerequisite whose symbols are absent), because every item builds inside it. Run `aw ipd begin xvm6no` before the first edit. Scope fence: `- Scope-Paths:` declares every path this plan expects to change; an out-of-scope edit is made and then JUSTIFIED at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every `V-*` MUST carry the ACTUAL pasted runner output; never claim a pass that was not run. Commit only Scope-Paths via `aw commit xvm6no -- <paths>`; never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns the terminal transition and the executor does NOT run `aw ipd finalize`; run by hand, finish with `aw ipd finalize xvm6no` once `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status: executed` and never `git mv` the file.
