# IPD: Deferred Questions Autonomous Decisions and Skip Records

- Date: 2026-08-23
- Kind: child
- Concern: Prevent needless interruption without hiding decisions or skipped work.
- Scope: Versioned run events, exact stop/defer classifier, generated projections, durable summaries, and answer/resume linkage.
- Status: to-review
- Set: execset
- Order: 2
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 3m4e54

## Workflow history
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created from stop-policy and record-taxonomy audit.

## Goal

Make autonomous decisions and deferrals explicit, durable, reviewable, and resumable while stopping the Set only when the user’s two conditions are both true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Versioned events

- [ ] E-01 Extend the closed ledger compatibly with `question_raised`, `question_disposition`, `human_answer`, `autonomous_decision`, `scope_deferred`, `work_claim`, `lane_outcome`, `integration_result`, and `set_checkpoint`; reconcile the missing `investigator` role; define closed Set states `planned|running|waiting_input|partial|complete|failed|cancelled`, legal transitions, resume semantics, coordinator-only authority, and completion refusal.
  - Depends on: none
  - Expected outcome: every decision, skip, lane, and checkpoint is attributable and hash-chained.
  - Execution state: pending

### Material change 2: Exact no-stop classifier

- [ ] E-02 Implement a pure classifier: decide robustly and record, else defer subgraph, else defer IPD, else drain independent frontier and only then emit `hard_stop_needs_input`; route unresolved `unknown_outcome` through deterministic reconciliation and that same predicate; lexically contain legacy child `STOP` instructions.
  - Depends on: E-01
  - Expected outcome: no question terminates the Set unless input is materially required and neither subgraph nor IPD can be safely skipped.
  - Execution state: pending

### Material change 3: Inspectable and durable records

- [ ] E-03 Generate local `decisions.md`, `open-questions.md`, and `deferred-work.md`; write/update a tracked walkthrough at partial/terminal checkpoints and every integrated decision-bearing commit; promote unresolved questions to blocked backlog records with `Gate-Kind: decision`, resume command, and close-on-answer behavior; on recovery promote any local untracked decision/question checkpoint before new work.
  - Depends on: E-02
  - Expected outcome: the user can inspect every consultation-preferred decision and every unanswered question through normal AW records/attention.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Runtime questions must not be appended to approved IPDs' authoring-time Open Questions.
- `.aw/workflow-artifacts/<workflow>/<run-id>/` is the local authoritative run convention and is intentionally untracked.
- Blocked backlog items already support `Gate-Kind: decision` and surface in `aw attention`; walkthroughs are the durable narrative record.
- `run_gates.py` currently stops every headless human gate and therefore needs set-level containment/refinement, not removal of consent gates.

## Findings

The current ledger is closed and cannot truthfully store decisions/questions. Existing `STOP and report` text is child-scoped in practice but not stated. A run with deferred work needs a first-class `partial` result and must leave affected IPDs pending.

## Proposed changes (ordered, validatable)

```text
hard_stop = needs_human
            AND no_robust_decision
            AND cannot_defer_subgraph
            AND cannot_defer_ipd
```

Autonomous decision fields include scope, selected option, alternatives, basis/evidence, why no prompt, `consultation_preferred`, confidence, reversibility, blast radius, affected files, and validation. Question fields include context, why input is required, affected nodes/descendants, disposition, options, recommendation, backlog ref, and resume trigger. Record decisions before mutation; reversals append `supersedes` events.

## Deferred / out of scope (with reason)

- Product-level ADR content is updated only when within approved scope; otherwise create backlog follow-up.
- Comms and record-history sidecars are not decision stores.

## Scope check

- Over-scope: none.
- Under-scope: unknown-outcome side effects must keep the existing explicit reconciliation requirement.

## Required tests / validation

Truth-table every classifier and Set-state transition; adversarially test trivial questions, missing tone, release approval, ambiguous target repo, all-children-deferred, unknown-outcome reconcile/defer, illegal actor/transition, completion refusal, ledger compatibility, decision checkpoint crash recovery, backlog promotion, answer/resume, and no false completion.

## Spec / documentation sync

Update lifecycle wording so `STOP THIS IPD` returns control to the Set coordinator; define local versus durable records and partial status.

## Open questions

### OQ-01: Should every tactical choice reach DECISIONS.md?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. Keep tactical/reversible choices in the run decision projection and durable walkthrough; promote only material product decisions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: old and new ledgers validate under explicit version rules; each new kind/role has positive and negative schema tests; transition-table tests reject illegal actors, illegal edges, and completion with any unresolved required node.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: exhaustive truth-table and adversarial fixtures show robust choices are recorded, deferrable subgraphs/IPDs never stop the Set, independent work drains first, and only the exact four-clause predicate yields `hard_stop_needs_input`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a partial fixture generates consistent local projections, tracked walkthrough, attention-visible blocked backlog item, answer linkage, and successful resume while deferred E-items remain pending; crash recovery promotes a decision checkpoint before releasing another lane.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes cover authoritative facts, stop semantics, and human inspection.

Requires explicit approval. Never synthesize consent, approval, release authority, credentials, or irreversible choices.
