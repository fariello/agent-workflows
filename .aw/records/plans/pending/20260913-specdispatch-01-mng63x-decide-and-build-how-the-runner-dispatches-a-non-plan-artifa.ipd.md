# IPD: Decide and build how the runner dispatches a non-plan artifact

- Date: 2026-09-13
- Kind: child
- Concern: A RUNNER CAN SELECT A SPEC BUT CANNOT RUN ONE, and closing that is a DESIGN question the repository has not answered. Sibling plan `ui8b9b` makes `aw oc run reviews --type spec` SELECT the specs awaiting review; this plan is the other half, and it is much larger than a flag. MEASURED at HEAD `9697856e`: `build_dynamic_manifest` compiles ONLY discovered plans, a queue entry is plan-shaped (`oc_runipd.py:2959` writes `"configured_file": plan["file"]`) and its path is resolved through `resolve_plan_path` against the plans tree, and the dispatch table has no runnable shape for two spec statuses (`run_selection_policy._SPEC_ACTIONS` routes `approved` to `plan`, meaning "author IPDs from this spec", and OMITS `implementing` entirely because such a spec dispatches its `From-Spec` children rather than taking one action of its own). So a queued spec would reach code that assumes a plan at several points, and one of the actions it needs is not a turn at all but a fan-out.
  THE MAINTAINER'S INSTRUCTION, 2026-09-13, AND IT IS THE POINT OF THIS PLAN: **HOW execution is implemented needs DISCUSSION.** This plan is therefore filed DESIGN-FIRST and is deliberately NOT executable as authored. Its blocking OQ-01 is the design itself. Do NOT treat the checklist below as an approved approach; treat it as the shape of the decision that has to be made, with the measured constraints any answer must satisfy.
- Scope: How the runner admits, queues, dispatches and validates a NON-PLAN artifact, decided before it is built. IN: the design decision and its record; manifest admission for a non-plan artifact; a queue entry that is not plan-shaped; the per-status spec actions the dispatch table declares but nothing implements; the validation shape for a spec turn (which is `aw specs check`, never `aw ipd lint`). OUT: registering `--type` and the selection path, which is sibling `ui8b9b` and a dependency of this plan; backlog/prompt dispatch, which the same table declares and which this plan must not silently absorb; any change to the needs-review predicate.
- Scope-Paths: TBD AT DESIGN TIME. Deliberately unset: the paths depend on OQ-01's answer, and declaring a fence for an undecided design would either be wrong or would pre-commit the decision. This MUST be filled in before execution, and `aw ipd lint` will refuse the plan until it is.
- Item-Dependencies: executed:ui8b9b
- Status: to-review
- Set: specdispatch
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: mng63x
- Priority: medium
- Work-Kind: feature
- Blocks-Release: next
- From-Spec: 6m4kow

## Workflow history

- 2026-09-13 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Filed during `/spec-review` of spec `6m4kow`, at the maintainer's explicit direction: they chose "selection now, and file the execution half as its own release blocker too", and added that HOW execution is implemented needs DISCUSSION and that the fact must be captured loudly. This plan is that capture. IT IS DESIGN-FIRST BY INSTRUCTION, not by omission: the constraints below are measured, the approach is NOT chosen, and OQ-01 is blocking so no runner and no agent can execute it as though the design were settled. `- Scope-Paths:` is deliberately TBD for the same reason.
- 2026-09-13 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Decide, with the maintainer, HOW a runner should dispatch a non-plan artifact, and only then build it, so that a spec awaiting review can actually be reviewed by `aw oc run` rather than merely appearing in its selection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

READ THIS BEFORE THE CHECKLIST. The items below are DEPENDENT ON OQ-01 and are written as the decision's consequences, not as an approved approach. If OQ-01's answer changes the shape (for example, if the maintainer decides a spec turn should not run under the plan runner at all), this plan is SUPERSEDED and re-authored rather than edited item by item. Executing it in its current state would be building an unreviewed design.

### Task group 1: decide the design (must precede every other item)

- [ ] E-01 HOLD THE DESIGN DISCUSSION AND RECORD ITS OUTCOME, before any code. Put the measured constraints (Findings F-1 to F-5) in front of the maintainer, present the candidate shapes with their costs, and record the ruling with its rejected alternatives and its basis. The output is a DECISION RECORD this plan can be re-authored against, plus a filled-in `- Scope-Paths:`.
  THE THREE CANDIDATE SHAPES, stated so the discussion starts from something concrete rather than from a blank page. (a) GENERALIZE THE QUEUE ENTRY: make the manifest and the queue item artifact-neutral, the way the REVIEW RECORD was already made artifact-neutral by `eyh1fu` (a precedent that worked and is worth studying, since it faced the same "one type hardcoded everywhere" problem). Cost: it touches the runner's central data structure, which every host path reads. (b) A PARALLEL SPEC LANE: keep the plan queue as is and give a spec turn its own thin path. Cost: two dispatch mechanisms, which is the fork this repository has paid for before, and the exact shape `6ypimw` deleted when two runners each carried their own `_needs_review`. (c) DO NOT RUN SPEC REVIEW UNDER THE RUNNER AT ALL, and treat `--type spec` as a discovery aid feeding an attended `/spec-review`. Cost: the mandated action stays manual, but nothing in the runner grows a second shape. This third option is genuinely on the table and must not be dismissed: spec `25kzda` 3.3 mandates that spec review HAPPEN, not that a runner perform it.
  - Depends on: none
  - Expected outcome: a recorded decision naming the chosen shape, the rejected ones with reasons, and the paths it will touch.
  - Execution state: pending

### Task group 2: consequences of the decision (shape depends on E-01)

- [ ] E-02 ADMIT A NON-PLAN ARTIFACT INTO THE MANIFEST AND THE QUEUE, as the E-01 decision directs. The measured obstacles are named in F-2 and F-3 and both must be addressed, not worked around: the manifest is compiled from discovered PLANS, and a queue entry carries plan fields whose path is resolved as a plan. Whatever shape is chosen, a spec must not be represented as a degenerate plan, because that is how a plan-shaped assumption downstream becomes a silent wrong action on a real artifact.
  - Depends on: E-01
  - Expected outcome: a spec is queued as a spec, with no plan-shaped field carrying a fabricated value.
  - Execution state: pending

- [ ] E-03 IMPLEMENT THE PER-STATUS SPEC ACTIONS THE DISPATCH TABLE ALREADY DECLARES, and treat the two hard ones as first-class rather than as edge cases. `to-review` -> review is the straightforward one and is what closes the original gap. `approved` -> `plan` means AUTHOR CONFORMANT IPDS FROM THE SPEC, which is a generative action with no precedent in the runner and which produces artifacts a human must then review. `implementing` has NO ROW AT ALL because such a spec dispatches its `From-Spec` children as child queue items, which is a fan-out and not a turn. DECIDE EXPLICITLY which of these this plan delivers; delivering only `to-review` is a legitimate answer, and if so the others must be REFUSED with a message naming what is unimplemented rather than silently skipped.
  - Depends on: E-01, E-02
  - Expected outcome: each spec status either performs its declared action or refuses honestly by name; none is silently treated as a no-op.
  - Execution state: pending

- [ ] E-04 USE THE SPEC'S OWN VALIDATION GATE, NEVER THE PLAN'S, and pin that. A spec turn's structural gate is `aw specs check`; `aw ipd lint` is IPD-only, and the hazard is not that it errors but that it SKIPS: `spec-review`'s own prohibition (c) records that plan-review's preflight is GUARDED, so handed a spec it would pass by not running, and "a skipped gate that looks like a passed one is worse than an absent gate". A runner-driven spec turn must also satisfy the three checks spec `25kzda` 4.8 names (`SPEC-REVIEW-COMPLETE`, `SPEC-REVIEW-TRANSITION`, `SPEC-REVIEW-STRUCTURE`) and must produce the review record the `->reviewed` transition now requires as its attestation.
  - Depends on: E-03
  - Expected outcome: a runner-driven spec turn is gated by `aw specs check`, produces a conforming review record, and a test proves `aw ipd lint` is never invoked against a spec.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE ARTIFACT-NEUTRAL PRECEDENT EXISTS AND WORKED. Executed plan `eyh1fu` made the review record artifact-neutral (`- Subject-Id:` plus `- Subject-Type:` replacing a hardcoded `- Plan-Id:`), migrating every existing record in the same change and refusing a compatibility shim. Its review also found the load-bearing trap: a SECOND consumer keyed on the old field would have returned EMPTY and silently opened a gate. Any generalization here should expect the same class of hidden second consumer.
- A FORK IS THE COSTLIER MISTAKE IN THIS REPOSITORY, and it has been paid for. `6ypimw` deleted two verbatim `_needs_review` closures, one per runner, which had diverged from the dispatch table. `uyeko5` records `--full-auto` having defaulted opposite ways on the two hosts. A parallel spec lane must be judged against that history.
- THE DISPATCH TABLE IS THE AUTHORITY AND MUST NOT BE DUPLICATED. `run_selection_policy` owns per-type actions, and membership is derived from it BY CONSTRUCTION so the sweep and the table cannot disagree. New dispatch code consults it; it does not restate it.
- A SPEC'S STATUS AND HISTORY ARE TOOL-OWNED (`aw specs set` / `aw specs note`), a hook exists for that bypass, and `- Readiness:` is NEVER written onto a spec. A runner-driven spec turn is bound by all three, exactly as an agent-driven one is.
- `->reviewed` NOW REQUIRES A CONFORMING REVIEW RECORD as its attestation, enforced by one shared predicate consulted by both setter spellings and by `check.spec-review-unattested`. A runner-driven review that fails to file a parseable record cannot legally transition the spec, and a malformed record blocks the spec's later approval with a parse code.

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-1 | HIGH | maintainer instruction, 2026-09-13 | THE DESIGN IS UNDECIDED AND MUST BE DISCUSSED. This is not a gap in the plan; it is the plan's subject. Any agent that picks a shape and builds it is substituting its own judgement for a decision the maintainer reserved. |
| F-2 | HIGH | `build_dynamic_manifest` compiles only discovered plans; `discover_plans` walks the two plans trees | THE MANIFEST ADMITS ONLY PLANS, so selection and dispatch disagree about what can be in a queue. `ui8b9b` makes a spec selectable; nothing downstream can represent it. |
| F-3 | HIGH | `oc_runipd.py:2959` `"configured_file": plan["file"]`; `resolve_plan_path` resolves against the plans tree; `resolve_plan_path` is imported into the queue path at `oc_runipd.py:221` | THE QUEUE ENTRY IS PLAN-SHAPED AND ITS PATH RESOLUTION IS PLAN-SCOPED. A spec queued as a plan would resolve its path in the wrong tree, or resolve correctly by accident and then be handed to plan-shaped consumers. This is the concrete reason "just pass the type through" is insufficient. |
| F-4 | HIGH | `_SPEC_ACTIONS`: `approved` -> `ACTION_PLAN`; `implementing` absent with the comment that such a spec "dispatches its From-Spec children as child queue items rather than taking one action of its own" | TWO OF THE DECLARED SPEC ACTIONS ARE NOT REVIEW TURNS AT ALL. One is generative (author IPDs) and one is a fan-out. Neither has any precedent in the runner, and a plan that says "dispatch a spec" without naming them will meet them at execution time. |
| F-5 | MEDIUM | `spec-review` prohibition (c): plan-review's preflight is guarded, so handed a spec it SKIPS and "a skipped gate that looks like a passed one is worse than an absent gate" | THE WRONG VALIDATION GATE FAILS SILENTLY, so E-04 is a correctness item and not hygiene. A runner-driven spec turn that reuses the plan preflight would report a passed gate that never ran. |
| F-6 | MEDIUM | `ui8b9b` `- Status: to-review`, this plan's `- Item-Dependencies: executed:ui8b9b` | THIS PLAN CANNOT RUN FIRST. Selection must exist before dispatch has anything to dispatch, and the dependency is declared so the runner's dependency check enforces the order rather than relying on a reader noticing. |

## Proposed changes (ordered, validatable)

1. Hold the design discussion; record the ruling, the rejected shapes, and the paths it will touch (E-01).
2. Re-author or amend this plan against that ruling, filling in `- Scope-Paths:`.
3. Admit a non-plan artifact into the manifest and the queue in the chosen shape (E-02).
4. Implement or explicitly refuse each declared per-status spec action (E-03).
5. Gate a spec turn with the spec's own checker and require its review record (E-04).

## Deferred / out of scope (with reason)

- REGISTERING `--type` AND THE SELECTION PATH: sibling `ui8b9b`, and a declared dependency of this plan. Excluded so the two halves are separately reviewable and separately provable.
- BACKLOG AND PROMPT DISPATCH. The same dispatch table declares actions for them (`_BACKLOG_ACTIONS` routes `open` to `plan`; a prompt dispatches on its parsed run contract rather than a status). A generalization done here MIGHT make them reachable as a side effect, and that must be stated rather than absorbed silently: whatever E-01 decides, this plan delivers SPEC dispatch and must say explicitly what it leaves unreachable.
- ANY CHANGE TO `needs_review` OR THE DISPATCH TABLE'S CONTENT. Both are already correct; new code consults them.

## Scope check

- Over-scope: none. `- Scope-Paths:` is TBD rather than over-broad, which is the honest state for an undecided design; it must be filled before execution and the linter enforces that.
- Under-scope: THIS PLAN INTENTIONALLY DOES NOT CHOOSE THE DESIGN. That is under-scope by instruction, not by oversight, and OQ-01 is the mechanism that keeps it from being executed as though the choice had been made.

## Required tests / validation

Cannot be specified in full until E-01 fixes the shape; specifying them now would pre-commit the design. What is FIXED regardless of the answer, and must appear in any re-authored version:

- A spec turn is gated by `aw specs check` and NEVER by `aw ipd lint`, asserted statically as well as behaviorally, because the failure mode is a silent skip (F-5).
- A runner-driven spec review files a review record that PARSES, since the `->reviewed` transition requires it as attestation and an unparseable record blocks the spec's later approval.
- No spec's `- Status:` or `## Workflow history` is written by anything other than the setters, and no spec acquires `- Readiness:`.
- A declared-but-unimplemented spec action REFUSES by name rather than skipping silently (E-03).
- The suite run BARE with its actual summary line pasted, `aw check` no-worse-than-baseline with both counts, and `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `6m4kow` R-15 is the requirement this plan completes; sibling `ui8b9b` E-05 performs that spec's amendment and clears its `- Blocks-Release:`, and this plan must NOT duplicate that edit. What this plan owes the record is the DECISION from E-01, written where a future reader will find it (the decision belongs in a spec or an amendment to `25kzda`'s dispatch section, not only in this plan's prose, since it will govern backlog and prompt dispatch too). Which of those is correct depends on OQ-01's answer and is part of what E-01 must settle.

## Open questions

### OQ-01: HOW should the runner dispatch a non-plan artifact?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: THE MAINTAINER RESERVED THIS DECISION EXPLICITLY on 2026-09-13 ("HOW execution is implemented is something that needs discussion; capture that fact loudly"), so it is not resolvable from repository evidence and MUST NOT be resolved by an agent picking the most convenient shape. THE REPOSITORY SUPPLIES THE CONSTRAINTS, NOT THE ANSWER: the manifest admits only plans (F-2), the queue entry is plan-shaped with plan-scoped path resolution (F-3), two of the three declared spec actions are not review turns at all (F-4), and the wrong validation gate fails silently rather than loudly (F-5). Three candidate shapes with their costs are set out in E-01, including the option of NOT running spec review under the runner at all, which is genuinely open because spec `25kzda` 3.3 mandates that spec review HAPPEN and not that a runner perform it.
  WHY `- Blocking: no` DESPITE BEING UNDECIDED, since the opposite looks more cautious and is in fact wrong here. A `Blocking: yes` question asserts the PLAN cannot proceed. This plan's FIRST ITEM IS THE DISCUSSION: E-01 holds it and records the ruling, and E-02, E-03 and E-04 each declare `Depends on: E-01`, so the dependency graph already refuses to build anything before the design is settled. Marking it blocking as well would say the plan cannot START, which is false and would make its own first item unreachable. It was authored `yes` first and corrected on exactly that reasoning; the correction is recorded rather than quietly made, because "undecided" and "blocked" are different states and conflating them is what the distinction exists to prevent.
  WHAT WOULD CLOSE IT: a ruling naming the shape, the rejected alternatives, and what it leaves deliberately unreachable (backlog and prompt dispatch in particular). V-01 will not accept a ruling that lacks a human attestation, which is the real guard against an agent deciding this on its own authority.
  IF THE RULING CHANGES THIS PLAN'S SHAPE (for example, deciding a spec turn should not run under the plan runner at all), SUPERSEDE this plan rather than editing E-02 to E-04 item by item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the recorded decision, naming the chosen shape, the alternatives rejected WITH their reasons, the basis, and the filled-in `- Scope-Paths:`. Paste the maintainer's own words authorizing it, not a paraphrase, since this is a reserved decision and an unattributed ruling is indistinguishable from an agent's own choice. A decision recorded without a human attestation does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a queued spec's manifest and queue entries showing it represented AS A SPEC, with no plan-shaped field holding a fabricated value, and paste its path resolving through the specs tree rather than `resolve_plan_path`. Paste a grep proving no second discovery or dispatch mechanism was introduced if the chosen shape was generalization, or, if a parallel lane was chosen, paste the recorded justification against the fork history in the conventions section.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for EACH spec status the table declares, paste either the action performed or the refusal message naming what is unimplemented. A silent skip satisfies nothing. Explicitly paste the `approved` and `implementing` cases (F-4), because those are the two that have no runner precedent and are the ones most likely to be quietly no-ops.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw specs check` gating the turn; paste a static assertion that `aw ipd lint` is unreachable from the spec path (a behavioral test alone is insufficient, because the failure is a SKIP that looks like a pass); paste the three `25kzda` 4.8 checks exercised by name; paste the review record produced and its clean parse diagnostics; and paste a `git diff` proving the spec's `- Status:` and history were written only by the setters and that no `- Readiness:` appeared.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

ONLY E-01 IS EXECUTABLE AS AUTHORED, AND THAT IS DELIBERATE. E-01 is the DISCUSSION; E-02 to E-04 each declare `Depends on: E-01` and cannot legitimately start before the ruling exists, and `- Scope-Paths:` is TBD until it does. So the correct next action is the discussion, after which this plan is re-authored (or superseded, if the ruling changes its shape) with real paths and real validation items.

WHAT STOPS AN AGENT BUILDING FIRST, since the guard is not a blocking question (see OQ-01 for why it must not be): the E-item dependency graph, the unset `- Scope-Paths:` fence, and V-01's refusal to accept a design ruling that carries no human attestation. An agent that picks a shape and builds it will fail V-01 with nothing to paste.

Execution contract, for whenever that happens: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste ACTUAL runner output for every test claim; run the suite bare. Never hand-write another role's attestation: `- Readiness:` is `/plan-review`'s output and is deliberately absent here, `- Approval:` is the human's, and an amended spec's `- Status:` belongs to `aw specs set`.

RELEASE GATE: this plan carries `- Blocks-Release: next` by the maintainer's ruling, as the execution half of spec `6m4kow` R-15. Sibling `ui8b9b` carries the selection half. Clearing this gate requires the work, not the discussion.

Post-gate lifecycle: on completion, run `aw ipd lint --phase pre-transition`, verify every `V-*` with pasted evidence, then move this file to `.aw/records/plans/executed/` with a path-scoped lifecycle commit.
