# IPD: Phase 3: event-derived lifecycle state and declared file scope

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 3 + section 7.3/7.5: a freely-editable `- Status:` field is trivially hand-editable, and file authorship in a shared dirty worktree cannot be reliably attributed. Lifecycle state should be DERIVED from validated events, and file scope should be DECLARED and compared to the actual index/diff, rather than inferred from timestamps or narrative.
- Scope: (1) Event-derived lifecycle state: represent transitions as validated events (e.g. IPD_CREATED -> WORK_STARTED -> TEST_EVIDENCE_RECORDED -> REVIEWED -> FINALIZED) with the visible status DERIVED from versioned events; the transition function rejects missing predecessors, stale tree ids, invalid actors, malformed evidence, and unauthorized terminal transitions. For ordinary repository assurance, versioned local events + CI validation suffice (authority countersigning is the deferred external-signing set). (2) Declared file scope: record an explicit task scope (the IPD `Scope-Paths` already exists) and COMPARE it to the git index + final diff; use isolated worktrees for concurrency; do NOT infer authorship from timestamps/narrative. This child integrates with the phase-1 engine (transition validity + scope drift are engine rules) and the phase-2 commands (which emit the events / enforce scope). Honest limit: local events are forgeable by a privileged local agent; authenticity depends on who can write/sign events (findings 5.4/7.3) - non-forgeable provenance is the deferred set.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/check_engine.py, agent_workflows/ipd_schema.py, agent_workflows/record_history.py, tests/
- Status: draft
- Set: agentadhere
- Order: 4
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: wqj1ne

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Derive lifecycle status from validated versioned events (rejecting invalid/out-of-order/unauthorized transitions) and enforce declared file scope by comparing the IPD's Scope-Paths to the actual git index/diff, so status and authorship are not freely editable or inferred.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: event-derived state

- [ ] E-01 Represent lifecycle transitions as validated versioned events with the visible status derived from them; the transition function rejects missing predecessors, stale tree ids, invalid actors, malformed evidence, and unauthorized terminal transitions. Integrate transition validity as phase-1 engine rules.
  - Depends on: none
  - Expected outcome: an invalid/out-of-order/unauthorized transition is rejected; a valid event sequence derives the expected status.
  - Execution state: pending

### Task group 2: declared scope enforcement

- [ ] E-02 Compare the IPD `Scope-Paths` to the git index + final diff and flag out-of-scope changes (engine rule); rely on isolated worktrees for concurrency; do not infer authorship from timestamps/narrative.
  - Depends on: E-01
  - Expected outcome: a change touching paths outside declared `Scope-Paths` is flagged; an in-scope change is clean.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `Scope-Paths` already exists in the IPD schema (ipd_schema.py `META_SCOPE_PATHS`, with a `grandfathered` sentinel) and is checked at the ready-to-execute gate - extend it to a diff comparison, do not invent a new field.
- `record_history.py` already appends versioned history to `.aw/records/history.jsonl`; event derivation should build on this sidecar, not a parallel log.
- `ipd_lifecycle.py` already computes changed paths since a frozen base (diff --name-only) for finalize - reuse for scope comparison.

## Findings

The building blocks (Scope-Paths, history sidecar, finalize diff) exist; Phase 3 makes status a DERIVED function of validated events and turns Scope-Paths into an enforced diff comparison. Authenticity remains local (forgeable); non-forgeable signing is deferred.

## Proposed changes (ordered, validatable)

1. Event model + derived-status function (built on `record_history`).
2. Transition-validity + scope-drift rules in the phase-1 engine.
3. `tests/`: invalid-transition rejection + scope-drift detection.

## Deferred / out of scope (with reason)

- External countersigning of protected events (authority assurance): deferred external-signing set.
- Migrating all existing status fields to pure derivation in one shot: may be phased; keep backward-compatible reads.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Invalid transitions (missing predecessor, stale tree id, invalid actor, malformed evidence, unauthorized terminal) are each rejected.
- A valid event sequence derives the correct visible status.
- A change outside declared `Scope-Paths` is flagged; in-scope is clean.

## Spec / documentation sync

- Document the event model + derived status and the scope-comparison rule (spec/docs); reconcile with the existing lifecycle docs.

## Open questions

### OQ-01: Migrate existing plans to event-derived status, or run derivation alongside the current field?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Run derivation alongside a backward-compatible read first (no big-bang migration); tighten to derived-only once stable. Decide at implementation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
