# IPD: Phase 1: durable monotonic stop-request flag and the cooperative checkpoint poll

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h R7-R9 and R11 require that a stop be REQUESTED durably and honored at cooperative checkpoints, not delivered as a raw kill. Today there is no request mechanism at all: the driver installs no signal handler, so a SIGINT/SIGTERM is handled by Python's default (KeyboardInterrupt/terminate) and the driver cannot distinguish 'wind down' from 'die'. A flag is also the only way the out-of-band `stop` command (Phase 5) can reach a driver in another process. Spec OQ-03 is RESOLVED: the flag is per-machine CONTROL state and lives inside the run dir that `wtiso` Phase 4 relocates out of the repo.
- Scope: Add the durable stop-request record (write/read/escalate) and the driver-side POLL that consults it at cooperative checkpoints, in BOTH drivers. Requests are durable, idempotent, and MONOTONIC (a request may only raise the level). Also add the per-level wind-down budget accounting (R11) that a later phase's escalation uses. Does NOT implement any level's behavior, any signal handler, or the CLI verb (Phases 2-5 own those): this child makes a request expressible and observable, nothing more.
- Scope-Paths: agent_workflows/runner_stop.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_stop.py
- Item-Dependencies: executed:2ouj70
- Status: approved
- Set: runstop
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: gq6m2u
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
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

- [ ] E-01 Add `agent_workflows/runner_stop.py` with a `StopRequest` record (level 1-4, `requested_at`, `requester`, escalation history, wind-down budget/deadline) and `read_stop_request(run_dir) -> StopRequest | None` that returns None when absent and tolerates a malformed file by treating it as absent (fail safe, never crash the driver on a corrupt control file).
  - Depends on: none
  - Expected outcome: the record round-trips; a truncated/garbage file reads as None rather than raising; a valid file yields the exact level and metadata.
  - Execution state: pending
- [ ] E-02 Add `request_stop(run_dir, level, requester) -> StopRequest` enforcing MONOTONICITY at write time per spec R9: a request whose level is <= the stored level is a recorded no-op, never a downgrade; a higher level overwrites and appends to the escalation history. CRITICAL (measured, see Findings): `tempfile.mkstemp` + `os.replace` alone is NOT sufficient. `os.replace` makes the WRITE atomic but leaves the READ-MODIFY-WRITE (read current level -> compare -> write) racy, and a measured 200-trial harness lost the higher level to a lower concurrent write in 100/200 trials (50%). The read-compare-write MUST therefore be serialized under an exclusive lock on a SEPARATE sidecar lock file (e.g. `stop-request.lock`, never the record itself, which is replaced by rename), which measured 0/200 lost updates. Keep `_atomic_write`'s temp+`os.replace` shape (`ipd_authoring.py:214-227`) for the write itself, INSIDE that lock. The lock acquisition MUST be non-blocking-with-fallback, never a blocking acquire (see E-06), because Phase 5's callers are signal handlers.
  - Depends on: E-01
  - Expected outcome: writing 1 then 3 then 1 leaves level 3 with a two-entry history; writing 4 escalates to 4; no sequence can lower the level; and a concurrency harness of two racing writers (4 and 1) yields the stored level 4 in 200/200 trials, not ~50%.
  - Execution state: pending
- [ ] E-03 Resolve the stop-request path from the SAME accessor the drivers use for `run_dir` (`oc_runipd.state_root`, :1162-1163; `agy_runipd.state_root`, :1232-1233) rather than constructing a root, so it inherits the `wtiso` Phase 4 out-of-repo relocation (spec OQ-03) and adds no second root.
  - Depends on: E-01
  - Expected outcome: the flag path is `<run_dir>/stop-request.json` for whatever `run_dir` the accessor returns; a test monkeypatching the accessor to a temp dir moves the flag with it, proving no hardcoded root; an AST/grep check scoped to `agent_workflows/` shows no new raw `.aw/state` construction.
  - Execution state: pending

### Task group 2: the driver-side poll

- [ ] E-04 Add `poll_stop(run_dir) -> int | None` and consult it in BOTH drivers at the two cooperative checkpoints: (a) the per-line in-turn point, beside the existing `heartbeat.touch()`/`watchdog.touch()` calls at `oc_runipd.py:1775-1776` and `agy_runipd.py:1844-1845` (corrected line numbers; `run_dir` IS in scope at both, being a parameter of `run_opencode` :1682 and `run_agy_turn` :1768, so no signature change is needed); and (b) the between-item point in `run_queue`'s dequeue loop (`oc_runipd.py:2495-2500`, where `queued`/`runnable` are selected), plus its `agy_runipd.py` counterpart. Also drain any signal-deferred request from E-06 here, since the poll is the documented durable-write point. The poll is otherwise SIDE-EFFECT FREE and idempotent (spec R8): it reports the current level and never consumes the request.
  - Depends on: E-02, E-03
  - Expected outcome: both drivers observe a level written by another process mid-run; repeated polls return the same level without mutating the record; a deferred signal request becomes durable at the next poll; no level behavior is triggered yet (that is Phases 2-4). Per-poll cost is negligible (measured ~5 us for the common absent-file case, ~20 us with a record present), so the per-line placement needs no caching.
  - Execution state: pending
- [ ] E-05 Record the per-level wind-down budget and its absolute deadline in the request record (spec R11) so Phases 2-4 read ONE authoritative value instead of each inventing a timeout. Do not enforce it here.
  - Depends on: E-02
  - Expected outcome: the record carries a budget and a computed deadline for the requested level; a test asserts the deadline is derived from `requested_at` plus the level's budget, and that reading it twice is stable.
  - Execution state: pending

### Task group 3: signal-handler safety (the writer Phase 5 will call from a handler)

- [ ] E-06 Make `request_stop` SIGNAL-HANDLER SAFE, because Phase 5 (`71vjbn` E-01/E-02) calls it from SIGINT/SIGTERM handlers and E-02 now takes a lock. A blocking lock acquire inside a handler DEADLOCKS the process when the signal lands while the main thread already holds that lock: measured directly (handler entered, then hung; the harness had to be killed at a 10s timeout, exit 124). Implement the handler-safe path: attempt `LOCK_EX | LOCK_NB`, and on `BlockingIOError` do NOT block - record the requested level in a process-local, async-signal-safe way (a module-level slot the handler only assigns) and let the already-required polling loop (spec R7) perform the durable write at its next checkpoint. Verified safe: the same harness with the non-blocking path exits 0 with the request deferred rather than deadlocking. Expose this as the documented entry point Phase 5 must use, so `71vjbn` cannot reintroduce a blocking write in a handler.
  - Depends on: E-02
  - Expected outcome: a test that raises a real signal while the lock is HELD shows the process survives and the level is durably recorded by the next poll (never lost, never deadlocked); and a test asserts the handler path performs no blocking acquire.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output covering round-trip, absent-file (None), truncated-file (None), and garbage-file (None) cases, showing the driver-safe failure mode rather than an exception.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output for the monotonicity matrix (1->3->1 stays 3 with a 2-entry history; ->4 escalates; no downgrade possible) AND a CONCURRENCY test with two racing writers (4 vs 1) run over MANY trials asserting the stored level is 4 in EVERY trial. The trial count must be high enough to catch a 50%-per-trial race (>= 100 trials; a single-trial test passes half the time by luck and FAILS this item). Sequential-only evidence fails this item. Evidence must also show the serialization is a SIDECAR lock, not a lock on the replaced record file.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the flag path follows a monkeypatched `state_root` into a temp dir (proving no hardcoded root), plus pasted output of the AST/grep check scoped to `agent_workflows/` showing no new raw `.aw/state` construction (orchestrator CID-2).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output showing a driver loop observing a level written by a SEPARATE process (not the same in-process object), and that N repeated polls return the same level with the record's mtime/content unchanged (proving side-effect freedom and idempotence, spec R8). Plus evidence the poll is wired at BOTH checkpoints in BOTH drivers (per-line and between-item, four sites total), and that a signal-deferred request from E-06 is durably written at the next poll.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted pytest output asserting the recorded deadline equals `requested_at` + the level's budget for each of the four levels, and that re-reading yields a stable value.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted pytest output for a test that delivers a REAL signal while the sidecar lock is HELD, showing (a) the process does not hang (the test must fail on timeout rather than hang the suite) and (b) the requested level is durably recorded by the next poll with no lost update. Plus evidence that the handler path takes no blocking acquire (e.g. an assertion that the handler used `LOCK_NB` and fell back to the deferred slot). A test that only calls `request_stop` on the main thread FAILS this item, since it never exercises the deadlock the measurement found.
  - Observed evidence:
  - Result: pending

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
