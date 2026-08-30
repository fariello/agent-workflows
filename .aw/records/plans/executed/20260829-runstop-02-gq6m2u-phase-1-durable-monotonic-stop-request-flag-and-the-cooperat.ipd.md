# IPD: Phase 1: durable monotonic stop-request flag and the cooperative checkpoint poll

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h R7-R9 and R11 require that a stop be REQUESTED durably and honored at cooperative checkpoints, not delivered as a raw kill. Today there is no request mechanism at all: the driver installs no signal handler, so a SIGINT/SIGTERM is handled by Python's default (KeyboardInterrupt/terminate) and the driver cannot distinguish 'wind down' from 'die'. A flag is also the only way the out-of-band `stop` command (Phase 5) can reach a driver in another process. Spec OQ-03 is RESOLVED: the flag is per-machine CONTROL state and lives inside the run dir that `wtiso` Phase 4 relocates out of the repo.
- Scope: Add the durable stop-request record (write/read/escalate) and the driver-side POLL that consults it at cooperative checkpoints, in BOTH drivers. Requests are durable, idempotent, and MONOTONIC (a request may only raise the level). Also add the per-level wind-down budget accounting (R11) that a later phase's escalation uses. Does NOT implement any level's behavior, any signal handler, or the CLI verb (Phases 2-5 own those): this child makes a request expressible and observable, nothing more.
- Scope-Paths: agent_workflows/runner_stop.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_stop.py
- Item-Dependencies: executed:2ouj70
- Status: executed
- Set: runstop
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: gq6m2u

## Workflow history
- 2026-08-30 executed (opencode its_direct/pt3-claude-opus-5-1m-us): Landed the durable monotonic stop-request record, the signal-handler-safe writer, and the cooperative poll at four checkpoints in both drivers; 54 new tests pass, full suite has zero net-new failures. [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: MODIFIED in commit 72fdf10 (in-turn + between-item poll wiring). Same re-frozen-base artifact.; in-scope-unmodified agent_workflows/oc_runipd.py: MODIFIED in commit 72fdf10 (in-turn + between-item poll wiring). Same re-frozen-base artifact.; in-scope-unmodified agent_workflows/runner_stop.py: MODIFIED, not unmodified: added in commit 72fdf10. Shows as unmodified only because begin was re-run after that commit (evidence edits staled the first receipt), re-freezing base_head to 72fdf10.; in-scope-unmodified tests/test_runner_stop.py: MODIFIED, not unmodified: added in commit 72fdf10 with 54 passing tests. Same re-frozen-base artifact.]
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-207. Two findings were established by MEASUREMENT, not reading. (1) BLOCKER: E-02 specified monotonicity via `tempfile.mkstemp` + `os.replace` alone, which makes each WRITE atomic but leaves the read-compare-write racy; a 200-trial two-writer harness (levels 4 vs 1) LOST the higher level in 100/200 trials (50%), so E-02 could not have passed its own V-02, and the failure mode is exactly the silent downgrade spec R9 exists to prevent. Serializing the read-modify-write under a short-lived SIDECAR lock measured 0/200 lost; E-02 now requires that, explicitly not a lock on the record file (which `os.replace` swaps). V-02 now demands >= 100 trials, since a single-trial test passes half the time by luck. (2) BLOCKER: that lock creates a signal-handler deadlock for Phase 5, which calls this writer from SIGINT/SIGTERM handlers - verified directly, the handler entered and hung until a 10s timeout killed it (exit 124), while a non-blocking-then-defer-to-poll path exits 0 with the request preserved. Added E-06/V-06 owning the handler-safe entry point, since the hazard is created here, not by the caller. Also corrected the per-line poll citation (:1774-1775 -> :1775-1776, plus the agy counterpart at :1844-1845), named the previously-vague between-item checkpoint concretely (`run_queue`'s dequeue loop, :2494-2500), recorded that `run_dir` is already in scope at both sites so no signature change is needed, fenced off reusing the run-long `run_lock` for this purpose, corrected the validation command (a bare `pytest -q` deselects the `slow` class these concurrency/signal tests belong to) to `make test-all`, measured the per-poll cost (~5 us absent, ~20 us present) to confirm the per-line placement needs no caching, and replaced the false "Under-scope: none" with the two real gaps.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Make a stop REQUEST a durable, idempotent, monotonically-escalating record that the driver polls at cooperative checkpoints (spec R7-R9, R11), so later phases can implement level behavior without inventing their own signalling and so an out-of-band `stop` command can reach a driver in another process.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the durable request record

- [x] E-01 Add `agent_workflows/runner_stop.py` with a `StopRequest` record (level 1-4, `requested_at`, `requester`, escalation history, wind-down budget/deadline) and `read_stop_request(run_dir) -> StopRequest | None` that returns None when absent and tolerates a malformed file by treating it as absent (fail safe, never crash the driver on a corrupt control file).
  - Depends on: none
  - Expected outcome: the record round-trips; a truncated/garbage file reads as None rather than raising; a valid file yields the exact level and metadata.
  - Execution state: performed
- [x] E-02 Add `request_stop(run_dir, level, requester) -> StopRequest` enforcing MONOTONICITY at write time per spec R9: a request whose level is <= the stored level is a recorded no-op, never a downgrade; a higher level overwrites and appends to the escalation history. CRITICAL (measured, see Findings): `tempfile.mkstemp` + `os.replace` alone is NOT sufficient. `os.replace` makes the WRITE atomic but leaves the READ-MODIFY-WRITE (read current level -> compare -> write) racy, and a measured 200-trial harness lost the higher level to a lower concurrent write in 100/200 trials (50%). The read-compare-write MUST therefore be serialized under an exclusive lock on a SEPARATE sidecar lock file (e.g. `stop-request.lock`, never the record itself, which is replaced by rename), which measured 0/200 lost updates. Keep `_atomic_write`'s temp+`os.replace` shape (`ipd_authoring.py:214-227`) for the write itself, INSIDE that lock. The lock acquisition MUST be non-blocking-with-fallback, never a blocking acquire (see E-06), because Phase 5's callers are signal handlers.
  - Depends on: E-01
  - Expected outcome: writing 1 then 3 then 1 leaves level 3 with a two-entry history; writing 4 escalates to 4; no sequence can lower the level; and a concurrency harness of two racing writers (4 and 1) yields the stored level 4 in 200/200 trials, not ~50%.
  - Execution state: performed
- [x] E-03 Resolve the stop-request path from the SAME accessor the drivers use for `run_dir` (`oc_runipd.state_root`, :1162-1163; `agy_runipd.state_root`, :1232-1233) rather than constructing a root, so it inherits the `wtiso` Phase 4 out-of-repo relocation (spec OQ-03) and adds no second root.
  - Depends on: E-01
  - Expected outcome: the flag path is `<run_dir>/stop-request.json` for whatever `run_dir` the accessor returns; a test monkeypatching the accessor to a temp dir moves the flag with it, proving no hardcoded root; an AST/grep check scoped to `agent_workflows/` shows no new raw `.aw/state` construction.
  - Execution state: performed

### Task group 2: the driver-side poll

- [x] E-04 Add `poll_stop(run_dir) -> int | None` and consult it in BOTH drivers at the two cooperative checkpoints: (a) the per-line in-turn point, beside the existing `heartbeat.touch()`/`watchdog.touch()` calls at `oc_runipd.py:1775-1776` and `agy_runipd.py:1844-1845` (corrected line numbers; `run_dir` IS in scope at both, being a parameter of `run_opencode` :1682 and `run_agy_turn` :1768, so no signature change is needed); and (b) the between-item point in `run_queue`'s dequeue loop (`oc_runipd.py:2495-2500`, where `queued`/`runnable` are selected), plus its `agy_runipd.py` counterpart. Also drain any signal-deferred request from E-06 here, since the poll is the documented durable-write point. The poll is otherwise SIDE-EFFECT FREE and idempotent (spec R8): it reports the current level and never consumes the request.
  - Depends on: E-02, E-03
  - Expected outcome: both drivers observe a level written by another process mid-run; repeated polls return the same level without mutating the record; a deferred signal request becomes durable at the next poll; no level behavior is triggered yet (that is Phases 2-4). Per-poll cost is negligible (measured ~5 us for the common absent-file case, ~20 us with a record present), so the per-line placement needs no caching.
  - Execution state: performed
- [x] E-05 Record the per-level wind-down budget and its absolute deadline in the request record (spec R11) so Phases 2-4 read ONE authoritative value instead of each inventing a timeout. Do not enforce it here.
  - Depends on: E-02
  - Expected outcome: the record carries a budget and a computed deadline for the requested level; a test asserts the deadline is derived from `requested_at` plus the level's budget, and that reading it twice is stable.
  - Execution state: performed

### Task group 3: signal-handler safety (the writer Phase 5 will call from a handler)

- [x] E-06 Make `request_stop` SIGNAL-HANDLER SAFE, because Phase 5 (`71vjbn` E-01/E-02) calls it from SIGINT/SIGTERM handlers and E-02 now takes a lock. A blocking lock acquire inside a handler DEADLOCKS the process when the signal lands while the main thread already holds that lock: measured directly (handler entered, then hung; the harness had to be killed at a 10s timeout, exit 124). Implement the handler-safe path: attempt `LOCK_EX | LOCK_NB`, and on `BlockingIOError` do NOT block - record the requested level in a process-local, async-signal-safe way (a module-level slot the handler only assigns) and let the already-required polling loop (spec R7) perform the durable write at its next checkpoint. Verified safe: the same harness with the non-blocking path exits 0 with the request deferred rather than deadlocking. Expose this as the documented entry point Phase 5 must use, so `71vjbn` cannot reintroduce a blocking write in a handler.
  - Depends on: E-02
  - Expected outcome: a test that raises a real signal while the lock is HELD shows the process survives and the level is durably recorded by the next poll (never lost, never deadlocked); and a test asserts the handler path performs no blocking acquire.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Spec OQ-03 (RESOLVED) puts the flag at `platform_state.checkout_state_root(<checkout-id>)/runs/<run-id>/stop-request.json`. Until `wtiso` Phase 3+4 (`7p9n2v`, `58ha43`) land, `run_dir` is still `repo/.aw/records/runs/<run-id>` (`oc_runipd.state_root`, :1162-1163). Resolve the flag path from the SAME accessor the driver already uses for `run_dir` so this child inherits the relocation automatically and introduces no second root (the `wtiso` Phase 3 AST guard forbids raw `.aw/state` construction).
- `run_dir` already holds `driver.lock` (`oc_runipd.py:740`), so the run dir is the established home for per-run control files; the stop request belongs beside it, not in a new location. Note the existing `run_lock` is a DIFFERENT lock with a different lifetime (held for the whole run, `main` :2926/:2958) and MUST NOT be reused to serialize stop-request writes: an out-of-band `stop` process could never take it while a run holds it. Use a dedicated short-lived sidecar lock.
- Atomic-write precedent to reuse: `ipd_authoring._atomic_write` (`ipd_authoring.py:214-227`, `tempfile.mkstemp` + `os.replace` with temp cleanup on failure). Reuse the WRITE shape, but note it provides no read-modify-write serialization; see the measured race in Findings. A torn stop-request file must never be readable as a valid lower level.
- The driver's existing per-line stream loop is the natural in-turn poll point: `oc_runipd.py:1770-1786` with `heartbeat.touch()`/`watchdog.touch()` at **:1775-1776** (the original draft cited :1774-1775, off by one), and the same shape in `agy_runipd.py:1841-1845`. `run_dir` is already a parameter at both sites (`run_opencode` :1682, `run_agy_turn` :1768).
- The between-item checkpoint is `run_queue`'s dequeue loop (`oc_runipd.py:2494-2500`: `while True` -> `load_state` -> select `queued` -> pick `runnable`), which is where Phase 2's levels 1-2 will branch.
- `fcntl` is POSIX-only and imported unconditionally by both drivers (`oc_runipd.py:17`, `agy_runipd.py:18`). A sidecar `flock` therefore adds no NEW portability constraint, but do not introduce a second lock abstraction: `platform_lock` is owned by `wtiso` Phase 5 (`2c122z`), and orchestrator OQ-02 governs the A10 story.
- Validation-command trap: default `addopts` (`pyproject.toml:122`) is `-m 'not slow'`, so a bare `python -m pytest -q` silently deselects `slow` subprocess/signal tests. This child's concurrency and signal tests belong in that class, so full-suite evidence must come from `make test-all`.

## Findings

The request record must answer three questions unambiguously, because Phases 3-5 branch on them:

| Field | Why | Spec |
|---|---|---|
| level (1..4) | which level was requested | R7 |
| requested_at + requester | audit and the "deliberate vs crash" distinction | R21 |
| monotonic history | proves escalation only ever raised the level | R9 |

MONOTONICITY is the subtle requirement. Spec R9 says a request may only RAISE the level. That must be enforced at WRITE time (a level-1 write against an existing level-4 request is a no-op, not a downgrade), because two writers exist: the signal handler (Phase 5) and the out-of-band `stop` command (Phase 5) can race. Enforcing it at read time instead would make the stored record misleading.

MEASURED: atomic write is NOT atomic read-modify-write (run 2026-08-29, before approving this plan). The original E-02 specified only `tempfile.mkstemp` + `os.replace`, then demanded a V-02 concurrency test asserting "the final stored level is the maximum requested". Those are inconsistent: `os.replace` makes each WRITE atomic but does nothing to serialize read -> compare -> write, so a lower-level writer that read before the higher-level writer replaced can still clobber it. A 200-trial two-writer harness (levels 4 and 1 racing):

- temp + `os.replace` only: **the higher level was LOST in 100/200 trials (50%)**
- read-compare-write serialized under an exclusive sidecar lock: **0/200 lost**

So E-02 as originally written could not have passed its own V-02, and the failure mode is exactly the operator-visible one spec R9 exists to prevent (pressing harder, then having the harder level silently downgraded). The lock MUST be a separate sidecar file, not the record itself, because the record is swapped by `os.replace` and a lock held on the replaced inode protects nothing.

MEASURED: a lock in a signal handler DEADLOCKS (same session). Since Phase 5 calls this writer from SIGINT/SIGTERM handlers, adding a lock creates a new hazard: a signal arriving while the main thread holds the sidecar lock re-enters on the SAME thread and a blocking acquire can never be satisfied. Observed directly - the handler printed "handler entered" and then hung until the 10s timeout killed it (exit 124). With the non-blocking + defer-to-poll pattern the same harness exits 0 and the request survives. This is why E-06 exists and why it must be the documented entry point Phase 5 uses.

EXECUTION-TIME RE-MEASUREMENT (2026-08-30, during execution). I did not take the two measured findings above on trust; I reproduced both against the shipped implementation. Both REPRODUCED, and I am recording the exact numbers rather than restating the plan's:

- Lost-update rate without the sidecar lock, 200 trials per mode, run twice: 87/200 (44%) and 106/200 (53%) lost; with the sidecar lock, 0/200 both times. The plan said 50%/0. Confirmed, and the spread across runs is itself the argument for a many-trial test.
- Blocking acquire in a signal handler: the handler entered and never returned, killed at the 10s timeout (exit 124), exactly as the plan recorded. The `request_stop_nowait` path exits 0 with `deferred=True` and the level durably present at the next poll.

ONE PLAN ESTIMATE CORRECTED. The plan states the per-poll cost as ~5 us absent / ~20 us present. Measured on this machine it is ~12 us absent / ~39 us present, i.e. about 2-3x the estimate. The plan's CONCLUSION still holds unchanged (a stream line costs far more than 39 us, so the per-line placement needs no caching), but the number in E-04 was optimistic and is corrected here rather than silently reused.

IDEMPOTENCE (R8) means re-reading does not re-trigger. The poll therefore returns the CURRENT requested level rather than consuming an event, and the driver acts on a level transition, not on the presence of a file.

R11 (bounded wind-down budget) is accounted here but ENFORCED by the phase that owns each level: this child records the budget and the deadline in the request record so Phase 2/3/4 escalation logic reads one authoritative value instead of each inventing a timeout.

## Proposed changes (ordered, validatable)

1. New `agent_workflows/runner_stop.py`: the `StopRequest` record, `read_stop_request(...)`, and a monotonic `request_stop(...)` whose read-compare-write is serialized under a short-lived SIDECAR lock (temp + `os.replace` for the write itself).
2. A signal-handler-safe request entry point: non-blocking lock attempt, deferring to the poll on contention, so Phase 5's handlers cannot deadlock the driver.
3. Driver-side `poll_stop(...)` consulted at the per-line in-turn point and the between-item dequeue point in both drivers (four sites), returning the current level without side effects and draining any deferred handler request.
4. New `tests/test_runner_stop.py` covering durability, idempotence, monotonicity under many-trial concurrency, torn-write safety, and signal-handler safety.

## Deferred / out of scope (with reason)

- Any level's BEHAVIOR (what actually completes before shutdown): Phases 2-4.
- Signal handlers and the `aw oc/agy run stop` verb: Phase 5 (`71vjbn`). This child provides the mechanism they call.
- Enforcing the wind-down budget: recorded here, enforced per-level by Phases 2-4 (and, for the cross-level escalation, Phase 5 per spec A7).
- REGISTERING signal handlers: Phase 5 (`71vjbn`). This child owns only the handler-SAFE writer that Phase 5 must call from its handler; the deadlock hazard is fixed here because it is created here.
- Relocating the run dir out of the repo: Set `wtiso` Phase 4. This child only resolves through the shared accessor so it inherits that move.

## Scope check

- Over-scope: none. No level behavior, no CLI, and no signal HANDLER (Phase 5 owns registration). E-06 is not over-scope: it hardens the writer this child owns against the deadlock its own new lock introduces, which cannot be deferred to the caller.
- Under-scope: as originally written, YES, in two ways now fixed. (1) Monotonicity was specified with a mechanism (atomic write) that measurably cannot deliver it under the concurrency V-02 demands (100/200 lost updates), so R9 was under-covered; E-02 now requires serialized read-modify-write. (2) The lock this introduces creates a signal-handler deadlock for Phase 5's callers, verified by measurement, with no E-item owning it; E-06/V-06 now do. Durability (R7), idempotence (R8), monotonicity (R9), budget accounting (R11), and handler safety each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop.py -q -m ''` passes (pass `-m ''` so `slow`-marked concurrency/signal tests in this file are not silently deselected).
- Monotonicity is proven under CONCURRENCY over MANY trials (>= 100 racing pairs, all yielding the maximum level), not sequentially and not in a single trial that a 50% race would pass by luck.
- Torn-write safety is proven by an injected mid-write failure leaving the previous valid record readable.
- Signal-handler safety is proven by delivering a REAL signal while the sidecar lock is held and showing no hang and no lost request; the test must time out rather than hang the suite.
- No test uses a wall-clock sleep to define a checkpoint (spec R10 discipline applies to this Set's tests generally). Note the concurrency test may use a tiny sleep to WIDEN a race window; that is a race-probe, not a checkpoint definition, and is permitted.
- `make test-all` (`python -m pytest tests/ -m ''`) remains green: the FULL suite, since a bare `python -m pytest -q` deselects `-m 'not slow'` per `pyproject.toml:122` and would skip exactly this child's new tests.

## Spec / documentation sync

- No user-facing doc change (no CLI surface in this child; Phase 5 documents the verb).
- Record in the module docstring that the flag location is spec c4gd2h OQ-03 and that it rides the `wtiso` Phase 4 relocation, so a future reader does not "fix" it back into the repo.
- Record in the module docstring WHY the sidecar lock exists (atomic write does not serialize read-modify-write; measured 50% lost-update rate without it) and WHY the handler path is non-blocking (a blocking acquire in a signal handler deadlocks), so a later reader does not "simplify" either away and silently reintroduce a downgrade or a hang.

## Open questions

### OQ-01: Enforce monotonicity at write time or at read time?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: at WRITE time. Two independent writers exist (the signal handler and the out-of-band `stop` command, both Phase 5) and they can race, so a read-time-only rule would leave a stored record that misrepresents what was requested. Write-time enforcement also makes the file itself the audit trail required by spec R9/R21. Resolved from the spec's own two-writer design, not deferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted pytest output covering round-trip, absent-file (None), truncated-file (None), and garbage-file (None) cases, showing the driver-safe failure mode rather than an exception.
  - Observed evidence: `python3 -m pytest tests/test_runner_stop.py::RecordRoundTripTests -m '' -n0 -p no:randomly` -> `7 passed in 0.14s`, covering every required case:
    ```
    tests/test_runner_stop.py::RecordRoundTripTests::test_round_trip_preserves_level_and_metadata PASSED
    tests/test_runner_stop.py::RecordRoundTripTests::test_absent_file_reads_as_none PASSED
    tests/test_runner_stop.py::RecordRoundTripTests::test_truncated_file_reads_as_none PASSED
    tests/test_runner_stop.py::RecordRoundTripTests::test_garbage_file_reads_as_none PASSED
    tests/test_runner_stop.py::RecordRoundTripTests::test_valid_json_with_unusable_level_reads_as_none PASSED
    tests/test_runner_stop.py::RecordRoundTripTests::test_directory_in_place_of_record_reads_as_none PASSED
    tests/test_runner_stop.py::RecordRoundTripTests::test_poll_on_malformed_file_returns_none_and_does_not_raise PASSED
    ```
    The DRIVER-SAFE failure mode is what these assert: each malformed case returns `None` (absent) rather than raising, so a corrupt control file cannot crash the driver. Two cases beyond the required set were added because they are reachable in practice: a structurally valid file whose `level` is out of range or the wrong type (`0/5/-1/'3'/None/True`) reads as None rather than being guessed at, and a DIRECTORY in the record's place also reads as None. Round-trip asserts level, level_name, requester, requested_at, first_requested_at, and a 1-entry history.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted pytest output for the monotonicity matrix (1->3->1 stays 3 with a 2-entry history; ->4 escalates; no downgrade possible) AND a CONCURRENCY test with two racing writers (4 vs 1) run over MANY trials asserting the stored level is 4 in EVERY trial. The trial count must be high enough to catch a 50%-per-trial race (>= 100 trials; a single-trial test passes half the time by luck and FAILS this item). Sequential-only evidence fails this item. Evidence must also show the serialization is a SIDECAR lock, not a lock on the replaced record file.
  - Observed evidence: TWO independent bodies of evidence, sequential and concurrent.
    (a) The monotonicity matrix: `python3 -m pytest tests/test_runner_stop.py::MonotonicityTests -m '' -n0 -p no:randomly` -> `8 passed in 0.30s`:
    ```
    tests/test_runner_stop.py::MonotonicityTests::test_one_then_three_then_one_stays_three_with_two_entry_history PASSED
    tests/test_runner_stop.py::MonotonicityTests::test_escalation_to_four PASSED
    tests/test_runner_stop.py::MonotonicityTests::test_no_sequence_can_lower_the_level PASSED
    tests/test_runner_stop.py::MonotonicityTests::test_equal_level_is_a_no_op_leaving_the_file_untouched PASSED
    tests/test_runner_stop.py::MonotonicityTests::test_first_requested_at_is_preserved_across_escalation PASSED
    tests/test_runner_stop.py::MonotonicityTests::test_invalid_level_is_rejected_loudly PASSED
    tests/test_runner_stop.py::MonotonicityTests::test_serialization_uses_a_sidecar_lock_not_the_record_file PASSED
    tests/test_runner_stop.py::MonotonicityTests::test_record_survives_os_replace_swapping_the_inode PASSED
    ```
    (b) The CONCURRENCY evidence, which is the half that matters: `python3 -m pytest tests/test_runner_stop.py::MonotonicityUnderConcurrencyTests -m '' -n0 -p no:randomly` -> `2 passed in 25.14s`. `test_racing_writers_never_lose_the_higher_level` runs **120 trials** (>= the 100 this item demands), each spawning two REAL competing processes (levels 4 and 1, high level launched first) released together on a file gate, and asserts the stored level is 4 in EVERY trial; it fails if even one trial loses the update. `test_many_concurrent_escalators_converge_on_the_maximum` races 8 writers `(1,2,3,4,3,2,1,2)` and asserts convergence on 4.
    I did not take the plan's measurement on trust; I RE-MEASURED it independently against this implementation with a two-writer harness at 200 trials per mode, comparing an atomic-write-only writer against the shipped sidecar-locked one, twice:
    ```
    unlocked : higher level (4) LOST in  87/200 trials     <- run 1
    locked   : higher level (4) LOST in   0/200 trials
    unlocked : higher level (4) LOST in 106/200 trials     <- run 2, final code
    locked   : higher level (4) LOST in   0/200 trials
    ```
    That reproduces the plan's finding (44% and 53% lost vs the plan's 50%) and confirms WHY a single-trial test would be worthless here: it would pass roughly half the time against the broken implementation.
    SIDECAR, not the record: `test_serialization_uses_a_sidecar_lock_not_the_record_file` asserts the lock path is a DISTINCT file named `stop-request.lock`, and `test_record_survives_os_replace_swapping_the_inode` asserts the record's inode CHANGES across an escalation, which is precisely why locking the record itself would protect nothing. `LockContentionTests::test_the_run_lock_is_not_reused_for_stop_requests` additionally asserts no `driver.lock` is created (the scope fence against reusing the run-long lock).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted pytest output showing the flag path follows a monkeypatched `state_root` into a temp dir (proving no hardcoded root), plus pasted output of the AST/grep check scoped to `agent_workflows/` showing no new raw `.aw/state` construction (orchestrator CID-2).
  - Observed evidence: (a) `python3 -m pytest tests/test_runner_stop.py::PathResolutionTests -m '' -n0 -p no:randomly` -> `4 passed in 0.12s`:
    ```
    tests/test_runner_stop.py::PathResolutionTests::test_resolution_follows_a_monkeypatched_state_root PASSED
    tests/test_runner_stop.py::PathResolutionTests::test_both_drivers_state_root_accessors_compose PASSED
    tests/test_runner_stop.py::PathResolutionTests::test_path_is_stop_request_json_inside_the_run_dir PASSED
    tests/test_runner_stop.py::PathResolutionTests::test_module_constructs_no_state_root_of_its_own PASSED
    ```
    `test_resolution_follows_a_monkeypatched_state_root` substitutes a `state_root` returning a temp dir and asserts the flag lands at `<temp>/elsewhere/runs/run-42/stop-request.json` AND that the result is NOT under the repo path, which is exactly the `wtiso` Phase 4 relocation behavior. `test_both_drivers_state_root_accessors_compose` feeds the REAL `oc_runipd.state_root` and `agy_runipd.state_root` through the same resolver.
    (b) The CID-2 check, scoped to `agent_workflows/`. A plain grep is misleading here, because the module's docstring deliberately MENTIONS `.aw/state` in a "do NOT move it back here" warning; the check must therefore distinguish prose from path construction. AST check excluding docstrings:
    ```
    runner_stop.py: non-docstring ".aw" literals -> NONE (constructs no state root)
    ```
    The same conclusion is enforced as a test (`test_module_constructs_no_state_root_of_its_own`, which strips comment lines and asserts no `.aw` literal appears in code), so a future edit that hardcodes a root fails the suite rather than silently passing. The two driver files' only `.aw` literals are their own pre-existing docstrings and receipt-path prose, untouched by this child.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted pytest output showing a driver loop observing a level written by a SEPARATE process (not the same in-process object), and that N repeated polls return the same level with the record's mtime/content unchanged (proving side-effect freedom and idempotence, spec R8). Plus evidence the poll is wired at BOTH checkpoints in BOTH drivers (per-line and between-item, four sites total), and that a signal-deferred request from E-06 is durably written at the next poll.
  - Observed evidence: (a) A SEPARATE PROCESS writing the level: `python3 -m pytest tests/test_runner_stop.py::CrossProcessPollTests -m '' -n0 -p no:randomly` -> `2 passed in 0.50s`:
    ```
    tests/test_runner_stop.py::CrossProcessPollTests::test_poll_observes_a_level_written_by_a_separate_process PASSED
    tests/test_runner_stop.py::CrossProcessPollTests::test_driver_loop_observes_a_mid_run_request PASSED
    ```
    Both spawn a real child interpreter to write the request (never the same in-process object), which is the out-of-band `stop` case. `test_driver_loop_observes_a_mid_run_request` models the driver's actual shape: a 50-iteration loop polling per line, with an out-of-band level-4 request injected at iteration 10, asserting `before: None after: 4`.
    (b) IDEMPOTENCE / side-effect freedom: `PollTests` -> `3 passed in 0.12s`. `test_repeated_polls_are_idempotent_and_leave_the_record_unchanged` performs 25 consecutive polls, asserting all 25 return 3 AND that the record's bytes and `st_mtime_ns` are unchanged, which is the spec R8 requirement that a poll reports rather than consumes.
    (c) WIRED AT FOUR SITES: `PollWiringTests` -> `5 passed in 0.08s`, asserting each driver contains exactly 2 `runner_stop.poll_stop(run_dir)` call sites, that the in-turn one follows `watchdog.touch()`, and that the between-item one is inside `run_queue`'s `while True` and BEFORE item selection. Confirmed directly:
    ```
    agent_workflows/oc_runipd.py:1953:                    runner_stop.poll_stop(run_dir)
    agent_workflows/oc_runipd.py:2707:        runner_stop.poll_stop(run_dir)
    agent_workflows/agy_runipd.py:1985:                    runner_stop.poll_stop(run_dir)
    agent_workflows/agy_runipd.py:2755:        runner_stop.poll_stop(run_dir)
    ```
    `run_dir` was already in scope at all four sites, so no signature changed. `test_this_child_wires_no_level_behavior` enforces the scope fence: neither driver branches on the poll's value and neither registers a signal handler (Phases 2-5 own those).
    (d) DEFERRED DRAIN: `DeferredRequestTests::test_nowait_defers_when_contended_and_the_poll_drains_it` asserts nothing is durable while the lock is held, then that the next poll writes level 4 durably and clears the slot (7 passed in 0.16s).
    (e) COST: measured per-poll overhead is ~12 us with no request present and ~39 us with one, on this machine. That is HIGHER than the plan's estimate of ~5/~20 us, which I am recording rather than restating the plan's number; the conclusion is unchanged (a stream line costs far more than 39 us, so the per-line placement still needs no caching).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted pytest output asserting the recorded deadline equals `requested_at` + the level's budget for each of the four levels, and that re-reading yields a stable value.
  - Observed evidence: `python3 -m pytest tests/test_runner_stop.py::BudgetTests -m '' -n0 -p no:randomly` -> `6 passed in 0.20s`:
    ```
    tests/test_runner_stop.py::BudgetTests::test_deadline_is_requested_at_plus_the_levels_budget PASSED
    tests/test_runner_stop.py::BudgetTests::test_every_level_has_a_budget PASSED
    tests/test_runner_stop.py::BudgetTests::test_level_four_has_a_zero_budget PASSED
    tests/test_runner_stop.py::BudgetTests::test_reading_the_deadline_twice_is_stable PASSED
    tests/test_runner_stop.py::BudgetTests::test_escalation_rebases_the_budget_on_the_new_level PASSED
    tests/test_runner_stop.py::BudgetTests::test_this_child_enforces_no_budget PASSED
    ```
    `test_deadline_is_requested_at_plus_the_levels_budget` loops over ALL FOUR levels and asserts `datetime.fromisoformat(deadline) == datetime.fromisoformat(requested_at) + timedelta(seconds=budget_for_level(level))` exactly, plus that the recorded `budget_seconds` matches the level's budget. `test_reading_the_deadline_twice_is_stable` asserts re-reading yields identical deadline and budget. The budgets (level 1: 7200s, level 2: 28800s, level 3: 600s deliberately equal to the drivers' `DEFAULT_STALL_TIMEOUT`, level 4: 0.0 by definition) are documented in the module with their derivation so a later phase argues with numbers rather than guessing. `test_this_child_enforces_no_budget` pins the scope boundary: a record whose deadline is a day past still polls normally here, because R11 is ACCOUNTED in this child and ENFORCED by Phases 2-4.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: pasted pytest output for a test that delivers a REAL signal while the sidecar lock is HELD, showing (a) the process does not hang (the test must fail on timeout rather than hang the suite) and (b) the requested level is durably recorded by the next poll with no lost update. Plus evidence that the handler path takes no blocking acquire (e.g. an assertion that the handler used `LOCK_NB` and fell back to the deferred slot). A test that only calls `request_stop` on the main thread FAILS this item, since it never exercises the deadlock the measurement found.
  - Observed evidence: `python3 -m pytest tests/test_runner_stop.py::SignalHandlerSafetyTests -m '' -n0 -p no:randomly` -> `4 passed in 8.22s`:
    ```
    tests/test_runner_stop.py::SignalHandlerSafetyTests::test_real_signal_while_lock_held_neither_hangs_nor_loses_the_request PASSED
    tests/test_runner_stop.py::SignalHandlerSafetyTests::test_the_blocking_variant_really_does_hang PASSED
    tests/test_runner_stop.py::SignalHandlerSafetyTests::test_handler_path_takes_no_blocking_acquire PASSED
    tests/test_runner_stop.py::SignalHandlerSafetyTests::test_request_stop_also_never_issues_a_blocking_acquire PASSED
    ```
    (a) NO HANG, NO LOST REQUEST: the first test spawns a child that HOLDS the sidecar lock on the main thread and then delivers a REAL `SIGINT` to itself (`os.kill(os.getpid(), SIGINT)`), so the handler re-enters on the same thread while the lock is held. This is not a main-thread `request_stop` call; it exercises the exact deadlock the plan measured. Child stdout, reproduced directly:
    ```
    main holds lock
    handler entered
    handler returned deferred=True
    handler exited
    main resumed
    poll -> 4
    exit=0
    ```
    The handler RETURNED (no hang), and the level was not lost: the next `poll_stop` wrote it durably and reported 4. The test is bounded by a 15s subprocess timeout and calls `self.fail(...)` on `TimeoutExpired`, so a reintroduced blocking acquire FAILS the suite instead of hanging it.
    (b) THE HAZARD IS REAL, not hypothetical: `test_the_blocking_variant_really_does_hang` runs the same probe with a deliberately BLOCKING `flock` and asserts it TIMES OUT. Measured independently:
    ```
    === BLOCKING (expect hang -> exit 124) ===
    main holds lock
    handler entered
    exit=124          <- killed at the 10s timeout; the handler never returned
    ```
    So the non-blocking design is load-bearing, and this characterization test will notice if the platform's lock semantics ever change.
    (c) NO BLOCKING ACQUIRE: `test_handler_path_takes_no_blocking_acquire` wraps `fcntl.flock`, records every operation flag, and asserts every exclusive acquire carries `LOCK_NB`; the contended path then falls back to the process-local deferred slot. `test_request_stop_also_never_issues_a_blocking_acquire` asserts the same for the ordinary writer, which retries `LOCK_NB` under a bounded deadline and raises `StopRequestError` instead of hanging (`LockContentionTests::test_request_stop_raises_when_the_lock_stays_contended` proves it fails fast).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking FOR THIS CHILD (spec OQ-01/OQ-03 are RESOLVED in c4gd2h). The orchestrator's OQ-02 (spec A10 / Windows) gates `71vjbn` only.
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan. Specifically: do NOT reuse or modify `run_lock` (a different lock with a run-long lifetime), do NOT introduce a `platform_lock`-style abstraction (owned by `wtiso` `2c122z`), and do NOT register any signal handler here (Phase 5 owns registration; this child only provides the handler-safe writer).
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
