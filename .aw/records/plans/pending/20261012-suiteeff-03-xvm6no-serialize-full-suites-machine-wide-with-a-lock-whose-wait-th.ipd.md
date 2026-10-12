# IPD: Serialize full suites machine-wide with a lock whose wait the stall watchdog sees

- Date: 2026-10-12
- Kind: child
- Concern: Nothing bounds how many full suites run at once on one machine. On 2026-10-12, seven concurrent drivers (four review sweeps, three execute runs) on a 12-core host ran load average 75-88; each execute turn's full suite (`python3 -m pytest` at `-n auto`) then outran the 900s stall watchdog, and runs `run-20261012T170951Z-1138207`, `run-20261012T170958Z-1138454` and `run-20261012T171028Z-1138872` lost 9 of 11 turns to `ipd-stalled` (each killed at exactly `stall_timeout: 900.0`). A lock alone would make this WORSE: an agent's `aw suite` blocked on a lock prints nothing the driver can see, because opencode reports a shell tool only when it completes, and `runner_shared.StallWatchdog._run` reaps on idle unless `progress_checker` reports progress.
- Scope: IN: a machine-wide slot lock taken inside `suite_cache.run_full_suite` (Order 02) around every cache-MISS run, default `max(1, os.cpu_count() // 6)` slots, configurable by `AW_SUITE_SLOTS`; a bounded, loud wait (a progress line at least every 60s, matching `INTEGRATION_LOCK_PROGRESS_SECONDS`); a heartbeat file the waiter touches, keyed by the agent turn's run and item ids, which both hosts' stall watchdogs read as progress; an env marker so a pytest launched by a test does not re-enter the lock; tests; docs. OUT: cache hits (they take no slot); narrowed runs (never pass through `aw suite`); bounding DRIVER concurrency or warning on host load (separate defect, deferred); changing the stall timeout default.
- Scope-Paths: agent_workflows/suite_cache.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/stall_progress.py, tests/test_suite_slot_lock.py, docs/cli-human-guide.md, CHANGELOG.md
- Item-Dependencies: executed:0o0wt2
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 58x9mw
- Blocks-Release: next
- Set: suiteeff
- Order: 3
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xvm6no

## Workflow history

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

- [ ] E-02 In `suite_cache.py`, add `suite_slot(*, progress, heartbeat) -> ContextManager[SlotOutcome]`: N lock files `suite-slot-<k>.lock` under a MACHINE-wide directory (`$XDG_RUNTIME_DIR/agent-workflows/` when set, else `<tempfile.gettempdir()>/agent-workflows-<uid>/`, mode 0o700), each taken with `platform_lock.acquire(..., blocking=False)` in a poll loop (the integration lock's pattern: `platform_lock` reserves `blocking=True` to one caller). A sidecar holder file per slot records pid, host, repo, run id, item id6 and start time for diagnostics. The wait is BOUNDED by `AW_SUITE_SLOT_TIMEOUT` (default 3600s); on expiry it RUNS ANYWAY with a loud warning rather than failing the suite, because a refused suite would fail an item over contention, which is worse than oversubscribing once. Every 60s of waiting it calls `progress("waiting for a test-suite slot (N of N held: <holder summaries>); waited <s>s")` and on every poll it calls `heartbeat()`. Wrap the cache-MISS branch of `run_full_suite` in it; a cache hit takes no slot. Machine-wide, not repo-wide, because the contended resource is the CPU.
  - Depends on: E-01
  - Expected outcome: with `AW_SUITE_SLOTS=1`, a second concurrent `aw suite --no-cache` prints the waiting line within 60s naming the first holder, and starts after the first finishes.
  - Execution state: pending

- [ ] E-03 Nested-run guard: `run_full_suite` sets `AW_SUITE_SLOT_HELD=1` in the suite's environment, and `suite_slot` is a no-op when that variable is already set, so a test that itself spawns `aw suite` or the runner's baseline inside a held slot cannot deadlock waiting on its parent. Add `AW_SUITE_SLOT_HELD` to the import-time scrub in `conftest.py` ONLY IF the test for E-05 shows an outer held marker otherwise leaks into unrelated tests; if added, extend Scope-Paths in the same commit and say so in V-03.
  - Depends on: E-02
  - Expected outcome: a suite run inside a held slot that launches a nested `aw suite` completes without waiting.
  - Execution state: pending

### Task group 2: make the wait visible to the stall watchdog

- [ ] E-04 Heartbeat channel. Define in `suite_cache.py` `heartbeat_path(run_id, item_id6) -> Path` under the same machine-wide directory (`heartbeat-<run_id>-<id6>`), and make `suite_slot`'s default `heartbeat` touch it (mtime update) on every poll, using `AW_RUN_ID` / `AW_ITEM_ID6` (already exported to every agent turn by both launchers, `git_commit_helper.RUN_ID_ENV` / `ITEM_ID6_ENV`); with either unset it touches nothing. Also touch it once per minute WHILE the suite itself runs (a daemon thread inside `run_full_suite`), so a long but healthy suite inside an agent turn is likewise visible, which removes the second half of the 2026-10-12 stall. Add `stall_progress.SuiteHeartbeatObserver(run_id, id6)` whose `poll()` returns True when the heartbeat file's mtime advanced since the last poll, fail-safe like `SubagentProgressObserver`.
  - Depends on: E-02
  - Expected outcome: while a slot wait or a suite is in progress for a turn's run/item, the observer's `poll()` returns True at least once per minute; with no activity it returns False.
  - Execution state: pending

- [ ] E-05 Wire the observer into both hosts' stall watchdogs. `StallWatchdog` takes one `progress_checker`; add a small combinator in `runner_shared` (`any_progress(*checkers)`, calling every checker each time so none is starved, swallowing exceptions per checker) and pass `any_progress(<existing observer>.poll, SuiteHeartbeatObserver(run_id, id6).poll)` at the oc site (`oc_runipd.run_opencode`, where `watchdog.progress_checker = observer.poll`) and the agy site (`agy_runipd.run_agy_turn`, `StallWatchdog(process, timeout=stall_timeout, progress_checker=observer.poll)`). Existing observers keep working unchanged.
  - Depends on: E-04
  - Expected outcome: a fake-host turn whose child runs an `aw suite` that waits longer than a short `--stall-timeout` is NOT reaped, while a fake child that does nothing for the same period still is.
  - Execution state: pending

### Task group 3: tests and docs

- [ ] E-06 Add `tests/test_suite_slot_lock.py` (behavioral, P16; a temp machine-wide dir via an env override `AW_SUITE_LOCK_DIR` honored by E-02 for tests): (a) two processes with `AW_SUITE_SLOTS=1` serialize (timestamps prove non-overlap) and the waiter prints the waiting line naming the holder; (b) with 2 slots, two run concurrently and a third waits; (c) a timeout of 2s runs anyway and prints the warning; (d) the nested guard (E-03); (e) the heartbeat observer flips on touch and stays False without; (f) END TO END on each host: drive `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` with a scripted host whose child holds a long suite-slot wait while emitting nothing on stdout, with `--stall-timeout 3`, and assert the turn is not reported stalled, and a control child that sleeps silently IS. Add a paragraph to `docs/cli-human-guide.md` (slots, `AW_SUITE_SLOTS`, what the waiting line means) and a `- Fixed:` bullet to `CHANGELOG.md`; no em or en dashes.
  - Depends on: E-03, E-05
  - Expected outcome: the file passes; cell (f) fails with E-05's wiring reverted.
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
3. Tests and docs (E-06).

## Deferred / out of scope (with reason)

- Bounding driver concurrency or refusing to start on a loaded host: a separate defect; this plan bounds the expensive part (suites).
- Heartbeats for long shell commands other than `aw suite`: needs a general mechanism (opencode does not stream tool output); separate defect.

## Scope check

- Over-scope: none.
- Under-scope: `conftest.py` may be needed by E-03; the item says how to add it if so.

## Required tests / validation

New `tests/test_suite_slot_lock.py`; existing stall-watchdog tests (`tests/test_oc_runipd.py` `StallWatchdogTests`, `tests/test_stall_progress.py`) must still pass; post-change `aw suite --no-cache` against E-01.

## Spec / documentation sync

`docs/cli-human-guide.md`, `CHANGELOG.md`. No spec amendment: spec `25kzda`'s stall contract ("no observed PROGRESS") is unchanged; this adds a progress source.

## Open questions

### OQ-01: Slot count default?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to `max(1, cpu_count // 6)` (2 on 12 cores), paired with Order 02's `-n = cpu_count // slots` (6 workers each), so two suites together use the cores once. One slot would queue seven drivers behind a 216s-median, 622s-p90 suite; see orchestrator `z3cqvz` OQ-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted pre-change summary line and failing node ids.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted terminal output of two concurrent `AW_SUITE_SLOTS=1 aw suite --no-cache` runs in this checkout, the second showing at least one waiting line naming the first's pid and repo, with start/end timestamps showing no overlap (code path: `run_full_suite` -> `suite_slot`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted E-06 cell (d) passing, and either "conftest unchanged" with the cell evidence that no marker leaked, or the conftest diff plus the Scope-Paths edit.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted E-06 cell (e) passing plus a `stat -c %Y` sequence of a heartbeat file taken 60s apart during a real `aw suite` run with `AW_RUN_ID`/`AW_ITEM_ID6` set, showing the mtime advancing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted E-06 cell (f) passing on both hosts, and failing with the E-05 wiring reverted (then restored); pasted passing `StallWatchdogTests` and `tests/test_stall_progress.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted passing `python3 -m pytest tests/test_suite_slot_lock.py`; pasted post-change `aw suite --no-cache` summary with no new failing node id versus V-01; docs and CHANGELOG diff with no em/en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Ready for `/plan-review` then human approval. Depends on `0o0wt2` executed. Commit only Scope-Paths via `aw commit xvm6no -- <paths>`; never push; paste real output into each `V-*`.
