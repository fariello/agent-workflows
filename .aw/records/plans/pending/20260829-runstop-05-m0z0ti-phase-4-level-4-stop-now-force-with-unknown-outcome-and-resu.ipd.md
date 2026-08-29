# IPD: Phase 4: level 4 stop-now-force with unknown_outcome and resume refusal

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h level 4 (STOP-NOW-FORCE) interrupts the current agent turn IMMEDIATELY rather than at a checkpoint, so the item's outcome may be INDETERMINATE and MUST be recorded `unknown_outcome` needing reconciliation before resume (spec R18-R19, R21-R22). This is the level that must never lie: because the driver does not know where the turn was cut, recording anything other than indeterminate would be a fabricated result. It is also the level a later run must REFUSE to blindly resume. Spec is explicit that the ONLY difference from level 3 is outcome CERTAINTY, not cleanliness: level 4 runs the identical Phase-0 cleanup.
- Scope: Implement level 4 in BOTH drivers: interrupt the turn immediately (reusing Phase 0's existing process-group escalation, never a bare kill), record the item `unknown_outcome` with the observed git state, end in the Phase-0 `clean_shutdown`, and make a subsequent run REFUSE to blindly resume such an item (reconcile or require explicit operator action) reusing the research ud28vy reconciliation model. Does NOT add signal handlers or the CLI verb (Phase 5), and does NOT redesign crash recovery (consumed, not re-specified).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_level4.py
- Item-Dependencies: executed:foi1b3
- Status: to-review
- Set: runstop
- Order: 5
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: m0z0ti

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Implement level 4 (STOP-NOW-FORCE): interrupt the turn immediately, record the interrupted item honestly as `unknown_outcome` with its observed git state, run the identical Phase-0 clean shutdown, and make a later run refuse to blindly resume it (spec R18-R19, R21-R22, A2, A6).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the immediate interrupt

- [ ] E-01 In BOTH drivers, on a level-4 request interrupt the current turn IMMEDIATELY (not at a checkpoint) by delegating to Phase 0's existing process-group escalation (`terminate_process`, oc_runipd.py:1632-1670), then route to `runner_shutdown.clean_shutdown(...)`. Do NOT issue a bare `kill` and do NOT add a second reaper (spec R5; spec level 4 is "interrupt + the reconciliation routine").
  - Depends on: none
  - Expected outcome: with a fake child mid-event and a level-4 request, the turn is cut without waiting for a checkpoint, the child and its group are reaped, and all four Phase-0 invariants hold identically to a level-3 stop.
  - Execution state: pending

### Task group 2: honest indeterminate recording

- [ ] E-02 Record the interrupted item as `unknown_outcome` using Phase 3's record shape with certainty=indeterminate (spec R18): the level that interrupted it, the OBSERVED git state captured at stop time, and the reconciliation a resume must perform first. Never record a last-completed-operation the driver did not observe.
  - Depends on: E-01
  - Expected outcome: the ledger shows the item `unknown_outcome` with captured git state and a stated reconciliation requirement; no fabricated last-operation field is present.
  - Execution state: pending
- [ ] E-03 Enforce spec R22 on this path: assert no item is recorded executed, complete, or successful after a level-4 stop, and record the stop as DELIBERATE (spec R21) so history shows operator intent rather than implying a crash.
  - Depends on: E-02
  - Expected outcome: after a level-4 stop the ledger contains a deliberate-stop record naming level 4, and zero items marked executed/complete/successful; a crash and a level-4 stop are distinguishable in the ledger.
  - Execution state: pending

### Task group 3: resume refusal

- [ ] E-04 In BOTH drivers, make a subsequent run REFUSE to blindly resume an `unknown_outcome` item (spec R19), reusing the research `ud28vy` reconciliation model rather than defining a new one. The refusal MUST name the item, its indeterminate state, and the reconciliation action required, so it is actionable rather than an opaque error.
  - Depends on: E-02
  - Expected outcome: starting a new run over a queue containing an `unknown_outcome` item exits nonzero without executing that item, printing the item id, its state, and the required reconciliation; no other queued item is silently skipped or executed out of order.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Phase 0 (`2ouj70`) owns the reaper: `terminate_process` already escalates SIGINT -> SIGTERM -> SIGKILL over the process GROUP (`oc_runipd.py:1632-1670`, `_SIGINT_GRACE_SECONDS=5.0`/`_SIGTERM_GRACE_SECONDS=2.0` at :1627-1628). Level 4 REUSES this; spec R5 forbids a second reaper and the spec explicitly says level 4 is "interrupt + the reconciliation routine. NOT a raw kill."
- Research `ud28vy` (`.aw/records/research/20260827-activework-00-ud28vy-active-work-lifecycle-and-toolset-redirect.findings.md`) owns the reconciliation model and the `unknown_outcome` concept; this child CONSUMES it (spec non-goal + GUIDING_PRINCIPLES P8 single source of truth) rather than defining a parallel mechanism.
- Phase 3 (`foi1b3`) already records an interrupted item with KNOWN certainty; level 4 must use the SAME record shape with certainty=indeterminate, not a second schema.
- Phase 3 also records a budget-breach/escalation-required marker when no checkpoint is reachable; level 4 is the escalation TARGET of that marker (the action itself is wired in Phase 5, spec A7).
- The driver prompt already mandates a per-item outcome JSON with an explicit `disposition` field including `failed-safely`, so an indeterminate disposition has an established home in an existing artifact rather than needing a new file.

## Findings

Why level 4 must record indeterminacy rather than a guess:

| What the driver knows after an immediate interrupt | Consequence |
|---|---|
| the turn was cut at an unobserved point | last completed operation is NOT knowable |
| the tree may hold a partial edit | git state must be captured, not assumed |
| the outcome artifact may be absent or half-written | its presence proves nothing |

Therefore spec R22 (never record executed/complete/successful) and R19 (refuse a blind resume) are the load-bearing requirements, and both are testable by OBSERVATION rather than by inspecting intent.

The resume-refusal has a subtle failure mode worth pinning: refusing must not be indistinguishable from a hard error. An operator needs to know WHY the resume was refused and what to do, so the refusal must name the item, its `unknown_outcome` state, and the reconciliation action. A V-item asserts the message content, not merely the nonzero exit.

Symmetry claim to verify (orchestrator CID-3): level 4 must exist in both drivers with identical semantics, since an operator switching hosts must not get a different guarantee.

## Proposed changes (ordered, validatable)

1. Immediate-interrupt path reusing Phase 0's process-group escalation, ending in `clean_shutdown`.
2. Record the interrupted item `unknown_outcome` with observed git state, using Phase 3's record shape with indeterminate certainty.
3. Resume refusal in both drivers: a later run detects an `unknown_outcome` item and refuses to blindly proceed, naming the reconciliation action.
4. New `tests/test_runner_stop_level4.py` proving indeterminacy is recorded, cleanliness still holds, and resume is refused.

## Deferred / out of scope (with reason)

- Signal handlers (repeated SIGINT escalating to level 4) and `aw oc/agy run stop --now-force`: Phase 5 (`71vjbn`); tests here request level 4 by writing the Phase-1 record directly.
- ENFORCING escalation from a Phase-3 budget breach into level 4: Phase 5 (spec A7). This child provides the level-4 behavior that escalation targets.
- Crash-recovery redesign and the reconciliation ALGORITHM: research `ud28vy` owns it; this child calls it.
- Automatic reconciliation without operator action: spec OQ-04 is non-blocking and leans operator-gated; this child implements the REFUSAL (R19) and leaves auto-reconcile out.

## Scope check

- Over-scope: none. No signals, no CLI, no reconciliation redesign.
- Under-scope: none. The immediate interrupt (spec level 4), the honest `unknown_outcome` record (R18, R22), the deliberate-vs-crash distinction (R21), and the resume refusal (R19) each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop_level4.py -q` passes.
- Spec acceptance A2 (repeated-interrupt path ends at level 4 with `unknown_outcome`) and A6 (a later run refuses to blindly resume) are demonstrated with a fake child.
- Every level-4 test also asserts the four Phase-0 invariants, proving cleanliness is IDENTICAL to level 3 (spec: the only difference is certainty).
- A test proves no item is ever recorded executed/complete/successful after a level-4 stop (spec R22).
- `python -m pytest -q` remains green.

## Spec / documentation sync

- Record in the driver comment that level 4's cleanliness is identical to level 3 and only certainty differs, citing spec c4gd2h, so a future reader does not "optimize" level 4 into a bare kill.
- Note in the code that the reconciliation routine is research `ud28vy`'s and must not be reimplemented here.
- No user-facing doc change yet; Phase 5 documents the trigger surface.

## Open questions

### OQ-01: Should a level-4 stop attempt reconciliation immediately, or only record `unknown_outcome` and defer?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: only RECORD and defer. Spec R19 requires refusing a blind resume, not auto-healing, and spec OQ-04 (non-blocking) leans operator-gated with automatic reconciliation allowed only when git state is provably clean. Attempting reconciliation inside the stop path would also run reconciliation while the tree is least trustworthy, and GUIDING_PRINCIPLES P10 (safety, reversibility) favors recording over acting. Resolved from the spec; auto-reconcile stays out of scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output showing the turn was cut mid-event (the event index proving no checkpoint was awaited), the process-table observation that no descendant survives, and the remaining three Phase-0 invariants (lock re-acquirable, ledger parses, `git status --porcelain` clean). Cleanliness must be shown EQUAL to the level-3 case.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted ledger contents after a level-4 stop showing `unknown_outcome`, the captured git state, and the stated reconciliation requirement; plus an assertion that no last-completed-operation value was invented. A prose claim of "recorded as unknown" fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output asserting zero executed/complete/successful markings after a level-4 stop (spec R22), plus pasted ledger records for a level-4 stop AND a simulated crash side by side showing they are distinguishable (spec R21).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output of a subsequent run over a queue containing an `unknown_outcome` item showing the nonzero exit, the item id and state in the message, and the named reconciliation action (spec A6); plus evidence the item was NOT executed and no other item ran out of order.
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
