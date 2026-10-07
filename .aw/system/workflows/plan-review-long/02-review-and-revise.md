# Step 2: Review and revise

## Purpose

Find every real plan defect, apply the Fix Bar, and improve the plan in place.

## Required context

Read `review-rubric.md` in full. Apply:

- the plan's goals and acceptance criteria;
- project instructions and guiding principles;
- domain invariants;
- all eight personas;
- the mandatory security lens;
- the rubric.

## 1. Record findings

Record each distinct actionable finding. Combine duplicate symptoms under one
root cause. Do not invent findings. A maintainer's sizing or splitting question is an
actionable FINDING to investigate by decomposition, never a signal to dismiss because the
size lint passed.

Each finding MUST contain:

- Severity: `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`.
- Scope: `IN-SCOPE`, `OVER-SCOPE`, or `UNDER-SCOPE`.
- Area: rubric and project-rule reference.
- Evidence: `path:line`, plus the symbol or a quoted string, for example the symbol `mod.func_name` beside its path and line.
- Finding and impact.
- Remediation Risk on complexity, usability, security, functionality, and
  overall.
- Decision: `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.
- Resolution or required next step.

Severity is for reporting only.

Write the findings to BOTH places:

1. The findings table in the final report.
2. A typed review record, `.aw/records/reviews/<...>.review.md`, using the same columns.

The record is what makes a severity readable by tooling. Before it, severity survived only as prose,
so a `HIGH` left unfixed gated nothing. This is a transcription of the classification you already
made, not a second classification.

Append a new `## Round <n>` for a re-review rather than editing an earlier round: the gate reads only
the CURRENT (last) round, so a finding you raised in round 1 and fixed in round 2 correctly stops
counting against the plan.

## 2. Apply the Fix Bar

Overall Remediation Risk is the highest applicable axis:

- **Low:** local, understood, easy to verify, unlikely to cause harm.
- **Medium:** bounded uncertainty with a clear verification path.
- **Medium-High:** material chance of significant complexity, usability harm,
  security weakness, or functional regression.
- **High:** likely major harm, foundational uncertainty, or no safe fix from
  available evidence.

Fix every Low or Medium risk finding.

A deferral MUST state:

- the Medium-High or High axis;
- why the fix is risky;
- needed decision or evidence;
- consequence of leaving it unresolved.

Effort, time, cost, and tokens are invalid reasons.

For over-scope, remove or explicitly exclude the unsupported work by default.

## 3. Revise in place

Make surgical, well-anchored edits:

- preserve valid content and required structure;
- replace ambiguity rather than appending duplicate prose;
- add missing guardrails, sequencing, acceptance criteria, tests, rollout,
  recovery, specification work, and validation;
- inject the gate execution contract if missing (resolved open questions, a scope
  fence, the hard-MUST honesty rule, path-scoped commit and never-push, lifecycle transition
  with conditional runner/executor ownership; flag both a hand-rolled `git mv` to `executed/`
  and an unconditional `aw ipd finalize` instruction);
- enforce per-E-item right-sizing (one concern / executable-in-one-focused-pass; split multi-deliverable items);
- remove unsupported or gold-plated scope;
- keep the plan concise and executable;
- do not weaken valid requirements.

### Orchestrator checklist row repair loop (`IPD-S407`)

For a plan whose own first `- Kind:` bullet reads `orchestrator` (read from the plan's own first
`- Kind:` bullet in front matter; never use a whole-file containment scan like
`grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as `m7gvuz`):

1. **Verify conformance (`IPD-S407`):** Every checklist item must be a typed child-tracking row
   matching `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`.
2. **Bounded repair loop:** If `IPD-S407` violations are reported, ask the agent to repair the
   checklist rows and re-run the check, up to an attempt budget of 2 (default 2 per
   `resolve_retry_budget(None) == 2`; the repository-policy tier of that precedence is unimplemented,
   backlog `dh3us4`).
3. **Verbatim refusal message:** The repair prompt MUST carry child 01's refusal message verbatim
   (which states the invariant, forbids satisfying it by deletion, and names both remedies: moving the
   step to a child with dependencies, or removing it if redundant).
4. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record
   (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording
   what the check reported, what changed, and the row count before and after (`rows: N -> M`) to
   distinguish relocation from deletion.

### Orchestrator review readiness (`IPD-S408`)

For a plan whose own first `- Kind:` bullet reads `orchestrator` (read from the plan's own first
`- Kind:` bullet in front matter; never use a whole-file containment scan like
`grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as `m7gvuz`):

1. **Verify review readiness (`IPD-S408`):** Run `aw ipd coverage <id6>` on the orchestrator under review.
2. **Bounded repair loop:** If coverage findings are reported, resolve each quoted finding by assigning it by id6 to a child in the `## Child IPDs` table or by adding a child plan and its row (never by deleting the checklist), up to an attempt budget of 2.
3. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording what `aw ipd coverage` reported and what changed.
4. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path; absence is the correct state, it is silent, and it makes downstream gates fail closed. State that `aw ipd set reviewed` refuses such an orchestrator after Order 05, so the reviewer resolves the findings before setting the status.

For cross-plan findings, fix the owning plan and cross-reference dependent
plans. Do not duplicate requirements.

When a revision corrects a mechanism, ordering, or classification, the
correction is not complete until every other item in the plan that quotes or
depends on the replaced wording has been swept and reconciled. This sweep
is not limited to `V-*` items: check every item, field, and prose block
(`E-*`, `V-*`, findings, proposed changes, gates, scope paths) against the plan
as it now reads, not merely your own diff. Grep for distinctive tokens of the
superseded wording (e.g. `PHASE_COMMITTED_INCOMPLETE` in `u23gbn`, where round 3
corrected E-06 and V-06 but left V-02 demanding an impossible state). If a stale
sibling belongs to an already executed plan and cannot be edited in place,
record the contradiction in a dated `## Workflow history` note where readers
will find it.

If the approach is not safely patchable, mark `REPLAN`, explain why, and state
the minimum shape of a sound replacement. Do not invent human product choices.

## Exit gate

Do not proceed until:

- [ ] Every rubric area is addressed or justified not applicable.
- [ ] Every real finding is recorded with evidence and all risk axes.
- [ ] Every Low or Medium risk finding is fixed.
- [ ] Every deferral meets the Fix Bar.
- [ ] Over-scope is removed or explicitly excluded.
- [ ] Revised plans remain concise, coherent, and executable.
- [ ] Replan findings identify the minimum required new direction.
- [ ] Orchestrator checklist rows conform to `IPD-S407` or are logged for honest exhaustion in Step 3.
- [ ] Orchestrator review readiness conforms to `IPD-S408` (via `aw ipd coverage <id6>`) or is logged for honest exhaustion in Step 3.
