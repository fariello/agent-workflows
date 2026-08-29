# IPD: Phase 1: durable monotonic stop-request flag and the cooperative checkpoint poll

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h R7-R9 and R11 require that a stop be REQUESTED durably and honored at cooperative checkpoints, not delivered as a raw kill. Today there is no request mechanism at all: the driver installs no signal handler, so a SIGINT/SIGTERM is handled by Python's default (KeyboardInterrupt/terminate) and the driver cannot distinguish 'wind down' from 'die'. A flag is also the only way the out-of-band `stop` command (Phase 5) can reach a driver in another process. Spec OQ-03 is RESOLVED: the flag is per-machine CONTROL state and lives inside the run dir that `wtiso` Phase 4 relocates out of the repo.
- Scope: Add the durable stop-request record (write/read/escalate) and the driver-side POLL that consults it at cooperative checkpoints, in BOTH drivers. Requests are durable, idempotent, and MONOTONIC (a request may only raise the level). Also add the per-level wind-down budget accounting (R11) that a later phase's escalation uses. Does NOT implement any level's behavior, any signal handler, or the CLI verb (Phases 2-5 own those): this child makes a request expressible and observable, nothing more.
- Scope-Paths: agent_workflows/runner_stop.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_stop.py
- Item-Dependencies: executed:2ouj70
- Status: to-review
- Set: runstop
- Order: 2
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: gq6m2u

## Workflow history
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
- [ ] E-02 Add `request_stop(run_dir, level, requester) -> StopRequest` writing the record ATOMICALLY (temp file + `os.replace`, following `ipd_authoring._atomic_write`, ipd_authoring.py:214-227) and enforcing MONOTONICITY at write time per spec R9: a request whose level is <= the stored level is a recorded no-op, never a downgrade; a higher level overwrites and appends to the escalation history.
  - Depends on: E-01
  - Expected outcome: writing 1 then 3 then 1 leaves level 3 with a two-entry history; writing 4 escalates to 4; no sequence can lower the level.
  - Execution state: pending
- [ ] E-03 Resolve the stop-request path from the SAME accessor the drivers use for `run_dir` (`oc_runipd.state_root`, :1162-1163; `agy_runipd.state_root`, :1232-1233) rather than constructing a root, so it inherits the `wtiso` Phase 4 out-of-repo relocation (spec OQ-03) and adds no second root.
  - Depends on: E-01
  - Expected outcome: the flag path is `<run_dir>/stop-request.json` for whatever `run_dir` the accessor returns; a test monkeypatching the accessor to a temp dir moves the flag with it, proving no hardcoded root; an AST/grep check scoped to `agent_workflows/` shows no new raw `.aw/state` construction.
  - Execution state: pending

### Task group 2: the driver-side poll

- [ ] E-04 Add `poll_stop(run_dir) -> int | None` and consult it in BOTH drivers at the two cooperative checkpoints: the per-line in-turn point (beside the existing `heartbeat.touch()`/`watchdog.touch()` calls, `oc_runipd.py:1774-1775`) and the between-item point where the next work item is dequeued. The poll is SIDE-EFFECT FREE and idempotent (spec R8): it reports the current level and never consumes the request.
  - Depends on: E-02, E-03
  - Expected outcome: both drivers observe a level written by another process mid-run; repeated polls return the same level without mutating the record; no level behavior is triggered yet (that is Phases 2-4).
  - Execution state: pending
- [ ] E-05 Record the per-level wind-down budget and its absolute deadline in the request record (spec R11) so Phases 2-4 read ONE authoritative value instead of each inventing a timeout. Do not enforce it here.
  - Depends on: E-02
  - Expected outcome: the record carries a budget and a computed deadline for the requested level; a test asserts the deadline is derived from `requested_at` plus the level's budget, and that reading it twice is stable.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec OQ-03 (RESOLVED) puts the flag at `platform_state.checkout_state_root(<checkout-id>)/runs/<run-id>/stop-request.json`. Until `wtiso` Phase 3+4 (`7p9n2v`, `58ha43`) land, `run_dir` is still `repo/.aw/records/runs/<run-id>` (`oc_runipd.state_root`, :1162-1163). Resolve the flag path from the SAME accessor the driver already uses for `run_dir` so this child inherits the relocation automatically and introduces no second root (the `wtiso` Phase 3 AST guard forbids raw `.aw/state` construction).
- `run_dir` already holds `driver.lock` (`oc_runipd.py:740`), so the run dir is the established home for per-run control files; the stop request belongs beside it, not in a new location.
- Atomic-write precedent to reuse: `ipd_authoring._atomic_write` (`ipd_authoring.py:214-227`, `tempfile.mkstemp` + `os.replace` with temp cleanup on failure). A torn stop-request file must never be readable as a valid lower level.
- The driver's existing per-line stream loop (`oc_runipd.py:1770-1786`) is the natural in-turn poll point, and its `heartbeat.touch()`/`watchdog.touch()` calls at :1774-1775 show the established shape for per-line side effects.
- Between-item checkpoints exist where the driver dequeues the next work item; the poll must be consulted there too (that is what Phase 2 levels 1-2 will act on).

## Findings

The request record must answer three questions unambiguously, because Phases 3-5 branch on them:

| Field | Why | Spec |
|---|---|---|
| level (1..4) | which level was requested | R7 |
| requested_at + requester | audit and the "deliberate vs crash" distinction | R21 |
| monotonic history | proves escalation only ever raised the level | R9 |

MONOTONICITY is the subtle requirement. Spec R9 says a request may only RAISE the level. That must be enforced at WRITE time (a level-1 write against an existing level-4 request is a no-op, not a downgrade), because two writers exist: the signal handler (Phase 5) and the out-of-band `stop` command (Phase 5) can race. Enforcing it at read time instead would make the stored record misleading.

IDEMPOTENCE (R8) means re-reading does not re-trigger. The poll therefore returns the CURRENT requested level rather than consuming an event, and the driver acts on a level transition, not on the presence of a file.

R11 (bounded wind-down budget) is accounted here but ENFORCED by the phase that owns each level: this child records the budget and the deadline in the request record so Phase 2/3/4 escalation logic reads one authoritative value instead of each inventing a timeout.

## Proposed changes (ordered, validatable)

1. New `agent_workflows/runner_stop.py`: the `StopRequest` record, atomic monotonic `request_stop(...)`, and `read_stop_request(...)`.
2. Driver-side `poll_stop(...)` consulted at the per-line in-turn point and at the between-item point, in both drivers, returning the current level without side effects.
3. New `tests/test_runner_stop.py` covering durability, idempotence, monotonicity, concurrency, and torn-write safety.

## Deferred / out of scope (with reason)

- Any level's BEHAVIOR (what actually completes before shutdown): Phases 2-4.
- Signal handlers and the `aw oc/agy run stop` verb: Phase 5 (`71vjbn`). This child provides the mechanism they call.
- Enforcing the wind-down budget: recorded here, enforced per-level by Phases 2-4.
- Relocating the run dir out of the repo: Set `wtiso` Phase 4. This child only resolves through the shared accessor so it inherits that move.

## Scope check

- Over-scope: none. No level behavior, no signal handling, no CLI.
- Under-scope: none. Durability (R7), idempotence (R8), monotonicity (R9), and budget accounting (R11) each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop.py -q` passes.
- Monotonicity is proven under CONCURRENCY (two writers racing), not just sequentially.
- Torn-write safety is proven by an injected mid-write failure leaving the previous valid record readable.
- No test uses a wall-clock sleep to define a checkpoint (spec R10 discipline applies to this Set's tests generally).
- `python -m pytest -q` remains green.

## Spec / documentation sync

- No user-facing doc change (no CLI surface in this child; Phase 5 documents the verb).
- Record in the module docstring that the flag location is spec c4gd2h OQ-03 and that it rides the `wtiso` Phase 4 relocation, so a future reader does not "fix" it back into the repo.

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
  - Required evidence: pasted pytest output for the monotonicity matrix (1->3->1 stays 3 with a 2-entry history; ->4 escalates; no downgrade possible) AND a CONCURRENCY test with two racing writers asserting the final stored level is the maximum requested and the file is never torn. Sequential-only evidence fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing the flag path follows a monkeypatched `state_root` into a temp dir (proving no hardcoded root), plus pasted output of the AST/grep check scoped to `agent_workflows/` showing no new raw `.aw/state` construction (orchestrator CID-2).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output showing a driver loop observing a level written by a SEPARATE process (not the same in-process object), and that N repeated polls return the same level with the record's mtime/content unchanged (proving side-effect freedom and idempotence, spec R8).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted pytest output asserting the recorded deadline equals `requested_at` + the level's budget for each of the four levels, and that re-reading yields a stable value.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking (spec OQ-01/OQ-03 are RESOLVED in c4gd2h).
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
