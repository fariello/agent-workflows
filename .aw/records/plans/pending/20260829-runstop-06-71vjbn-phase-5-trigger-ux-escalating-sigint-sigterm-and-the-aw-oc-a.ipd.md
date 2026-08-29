# IPD: Phase 5: trigger UX (escalating SIGINT, SIGTERM) and the aw oc/agy run stop command

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h R12-R17 define the only surfaces a human actually touches: first SIGINT (Ctrl-C) requests level 1 and repeated SIGINT escalates 1 -> 3 -> 4 with a printed hint, SIGTERM requests level 3, and `aw oc/agy run stop <run-id> --after-call|--after-set|--now|--now-force` requests any level out-of-band from a second terminal or a script. Until this child lands, all four levels exist but are UNREACHABLE by a user (Phases 2-4 are exercised by writing the Phase-1 record directly). The driver currently installs NO signal handler at all, so today a Ctrl-C is Python's default KeyboardInterrupt and a SIGTERM just kills it. This child also enforces the cross-level escalation on a wind-down budget breach (spec R11, A7) that Phase 3 only records.
- Scope: Add the signal handlers (SIGINT with escalation, SIGTERM) in BOTH drivers, the `stop` subcommand on both runners, the per-request progress reporting (spec R16), the unknown/finished-run error path (R17), and the budget-breach escalation enforcement (R11, A7). Also document the portable subset for platforms without POSIX signal semantics (R14/A10). Does NOT change any level's behavior (Phases 2-4 own that) and does NOT add `stop --all` (spec OQ-02, deferred).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_triggers.py
- Item-Dependencies: executed:m0z0ti
- Status: to-review
- Set: runstop
- Order: 6
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 71vjbn

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Make all four stop levels reachable by a human: escalating SIGINT, SIGTERM, and an out-of-band `aw oc/agy run stop <run-id> --<level>` command, with progress reporting, an honest error path for an unknown run, and enforcement of the wind-down budget escalation (spec R12-R17, R11, A5, A7, A10).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: signal triggers

- [ ] E-01 Register a SIGINT handler in BOTH drivers implementing spec R12's escalation: 1st SIGINT requests level 1, 2nd requests level 3, 3rd requests level 4, each via Phase 1's `request_stop(...)` so write-time monotonicity prevents a downgrade under rapid presses. The handler MUST do only the minimal record-and-return (no cleanup inside the handler); the existing poll acts on it (spec R7).
  - Depends on: none
  - Expected outcome: delivering SIGINT three times to a spawned driver yields recorded levels 1, then 3, then 4 with a 3-entry escalation history; the handler performs no teardown itself.
  - Execution state: pending
- [ ] E-02 Register a SIGTERM handler in BOTH drivers requesting level 3 (spec R13), replacing today's default-kill behavior in which the driver prints `Terminated` and exits while its child is orphaned.
  - Depends on: E-01
  - Expected outcome: SIGTERM to a spawned driver records level 3 (not an immediate exit), the turn stops at a safe checkpoint per Phase 3, and the Phase-0 invariants hold; the Phase-0 characterization test pinning the OLD orphan behavior is consciously updated with a note.
  - Execution state: pending

### Task group 2: the out-of-band command

- [ ] E-03 Add a `stop` subcommand to BOTH runners' own parsers (where `start` already lives, NOT `cli.py`'s `oc` group, since `aw oc run` forwards REMAINDER verbatim) accepting `<run-id>` and exactly one of `--after-call|--after-set|--now|--now-force`, mapping to levels 1-4 via `request_stop(...)`. Flag help MUST state that these control interruption FORCE only and that cleanup is unconditional (spec R15).
  - Depends on: E-01
  - Expected outcome: `aw oc run stop <run-id> --after-set` records level 2 for that run from a second process; `--help` shows all four flags and the cleanup-is-unconditional wording; the same works for `aw agy run stop`.
  - Execution state: pending
- [ ] E-04 Implement the honest error path (spec R17): `stop` on an unknown, already-finished, or already-stopping run reports that state and exits NONZERO for a nonexistent live run, mutating nothing. It must never appear to succeed.
  - Depends on: E-03
  - Expected outcome: `stop <bogus-run-id>` exits nonzero naming the unknown run and creates no file; `stop` on an already-stopping run reports the existing level and does not downgrade it.
  - Execution state: pending

### Task group 3: reporting and escalation enforcement

- [ ] E-05 Report progress on every accepted request (spec R16): print the level accepted, what the driver is waiting for, and how to escalate. Silence during wind-down is a defect.
  - Depends on: E-01, E-03
  - Expected outcome: each accepted request emits a line naming the level, the awaited boundary, and the escalation hint; captured output from a signalled run contains all three for each escalation step.
  - Execution state: pending
- [ ] E-06 Enforce the wind-down budget escalation Phase 3 only recorded (spec R11, A7): on a breach marker or an elapsed deadline read from Phase 1's record, escalate to the next level with the escalation RECORDED, so a hung turn can never make a stop hang forever.
  - Depends on: E-05
  - Expected outcome: a level-1 request against a fake child that will not finish escalates before the recorded deadline plus a bounded margin, records the escalation, and still satisfies all four Phase-0 invariants.
  - Execution state: pending
- [ ] E-07 Document and test the portable subset (spec A10): on a platform without POSIX signal semantics, level 1 and the out-of-band `stop` MUST still work and unsupported triggers MUST fail loudly rather than silently doing nothing. State the subset in the `stop` help and the module docstring.
  - Depends on: E-03
  - Expected outcome: with `sys.platform` monkeypatched to a non-POSIX value, registering an unsupported signal trigger raises or warns visibly (never silently no-ops), while `request_stop`/`stop` continue to function.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The driver installs NO signal handler today: the only `signal` references in `oc_runipd.py` are the constants at :1627-1628 and the escalation inside `terminate_process` (:1654-1666), which signals the CHILD, not a handler for the driver itself. So `signal.signal(...)` registration is genuinely new code, not a modification.
- Phase 1 (`gq6m2u`) provides `request_stop(run_dir, level, requester)` with WRITE-TIME monotonicity, which is exactly what makes escalating SIGINT safe: three rapid Ctrl-C presses cannot race into a downgrade.
- A signal handler must be async-signal-safe in practice: it should do the minimum (record the escalation via the Phase-1 atomic write) and let the polling loop act, matching spec R7's "driver POLLS a stop-request flag" rather than acting inside the handler.
- Phase 1 recorded the per-level budget and deadline; Phase 3 recorded a breach marker. This child is where the breach ESCALATES (spec A7), so the escalation logic reads one authoritative deadline rather than inventing a timeout.
- CLI convention: subcommands are declared on the runner's own parser; `aw oc run` currently forwards `argparse.REMAINDER` verbatim to `oc_runipd.main` (`cli.py`, the `oc`/`opencode` forwarding), so `stop` is added to the RUNNER's parser (where `start` already lives), not to `cli.py`'s `oc` group.
- `fcntl`-based `run_lock` (`oc_runipd.py:738-756`) is POSIX-only, and Windows lacks POSIX SIGTERM delivery: spec A10 requires the portable subset (level 1 + the out-of-band `stop`) to work and unsupported triggers to fail LOUDLY rather than silently no-op.

## Findings

The trigger matrix (spec R12-R14):

| Trigger | Level requested | Notes |
|---|---|---|
| 1st SIGINT (Ctrl-C) | 1 | prints what it is waiting for + how to escalate |
| 2nd SIGINT | 3 | "press again to stop harder" |
| 3rd SIGINT | 4 | terminal escalation |
| SIGTERM | 3 | scriptable single-shot |
| `stop --after-call` | 1 | out-of-band |
| `stop --after-set` | 2 | out-of-band; NOT reachable by signal (deliberate: no natural key for it) |
| `stop --now` | 3 | out-of-band |
| `stop --now-force` | 4 | out-of-band |

Note level 2 is reachable ONLY out-of-band. That is a deliberate consequence of the spec's escalation ladder (1 -> 3 -> 4) and is worth stating so a reviewer does not read it as an omission.

Two honesty requirements drive V-items: spec R15 forbids any flag name implying cleanup is optional (the names describe interruption force only), and spec R16 forbids silence during wind-down (the driver must say which level it accepted and what it is waiting for). Spec R17 requires `stop` on an unknown/finished run to exit nonzero rather than appear to succeed, which is the failure mode most likely to be implemented as a silent success.

## Proposed changes (ordered, validatable)

1. Signal handlers in both drivers: SIGINT with 1 -> 3 -> 4 escalation and a printed hint; SIGTERM -> level 3. Handler only records via the Phase-1 atomic write; the poll acts.
2. `stop` subcommand on both runners with the four level flags, writing the same record.
3. Progress reporting on each accepted request (spec R16) and the nonzero unknown-run path (R17).
4. Budget-breach escalation enforcement (spec R11, A7) reading Phase 1's deadline and Phase 3's breach marker.
5. New `tests/test_runner_stop_triggers.py` covering the matrix, escalation monotonicity under rapid signals, the error path, and the portable subset.

## Deferred / out of scope (with reason)

- Any level's BEHAVIOR: Phases 2-4 (`1qxuke`, `foi1b3`, `m0z0ti`). This child only requests levels.
- `stop --all` across concurrent runs: spec OQ-02, non-blocking, deliberately deferred (broad blast radius; ship per-run-id first).
- A unified top-level `aw run stop`: orchestrator OQ-01 defers it to the runner unification (backlog `dhuape`).
- Implementing a Windows lock primitive to replace `fcntl`: this child DOCUMENTS and tests the portable subset and fails loudly on unsupported triggers; replacing the lock is a separate concern.

## Scope check

- Over-scope: none. No level behavior is changed; only request surfaces and the escalation enforcement Phase 3 explicitly deferred here.
- Under-scope: none. Signals (R12-R13), the CLI verb (R14), flag-name honesty (R15), progress reporting (R16), the unknown-run path (R17), budget escalation (R11/A7), and the portable subset (A10) each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop_triggers.py -q` passes.
- Spec acceptance A5 (unknown run id exits nonzero, mutates nothing), A7 (budget breach escalates and still satisfies the invariants), and A10 (portable subset works; unsupported triggers fail loudly) are demonstrated.
- Rapid repeated SIGINT is tested for MONOTONIC escalation (never a downgrade), relying on Phase 1's write-time rule.
- Signal tests deliver real signals to a spawned driver process (not a mocked handler) so the handler registration itself is proven.
- `python -m pytest -q` remains green.

## Spec / documentation sync

- `aw oc run --help` and `aw agy run --help` gain the `stop` verb and its four flags; the help text MUST convey that the flags control interruption FORCE only and that cleanup is unconditional (spec R15).
- Document the portable subset (which triggers work without POSIX signals) in the `stop` help and the module docstring (spec A10).
- Spec `c4gd2h` becomes eligible for `implemented` only after the orchestrator's whole-Set verification (E-01 there), not here.

## Open questions

### OQ-01: Should level 2 (after-set) also be reachable by a signal?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: no. Spec R12's escalation ladder is explicitly 1 -> 3 -> 4, so there is no free key position for level 2, and overloading one would make the "press again to stop harder" model ambiguous. Level 2 stays out-of-band via `stop --after-set` (spec R14). Recorded here because a reviewer could otherwise read the gap as an omission rather than a decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output delivering three REAL SIGINTs to a spawned driver process (not a mocked handler) showing recorded levels 1 -> 3 -> 4 and a 3-entry escalation history, plus evidence the handler itself performed no teardown (cleanup observed only after the poll acted).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output delivering a real SIGTERM showing level 3 recorded and the turn stopping at a checkpoint, the four Phase-0 invariant observations, and the diff/note showing the Phase-0 characterization test pinning the old orphan behavior was consciously updated rather than silently deleted.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `aw oc run stop --help` AND `aw agy run stop --help` output showing all four flags and the cleanup-is-unconditional wording (spec R15), plus pasted pytest output showing a level recorded from a SEPARATE process for each of the four flags.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output for spec A5 showing `stop <bogus-run-id>` exiting nonzero with the run id named, plus a filesystem listing proving nothing was created; plus the already-stopping case showing the existing level reported and NOT downgraded.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted captured driver output from a signalled run containing, for EACH escalation step, the accepted level, the awaited boundary, and the escalation hint (spec R16). Missing any of the three fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted pytest output for spec A7 showing a level-1 request against a non-finishing fake child escalating before the recorded deadline plus a bounded margin, the escalation recorded in the run record, and all four Phase-0 invariants still satisfied.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted pytest output with `sys.platform` monkeypatched to a non-POSIX value showing an unsupported trigger raising or warning VISIBLY (asserted on the captured warning/exception, not on absence of a crash) while `request_stop`/`stop` still work; plus the pasted help text naming the portable subset.
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
