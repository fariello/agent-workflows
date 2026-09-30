# IPD: Decide and build the spec requirement-ID convention that SPEC-PLAN-TRACE needs

- Date: 2026-09-30
- Kind: orchestrator
- Concern: Approved spec `25kzda` 4.8 declares `SPEC-PLAN-TRACE` with a fixed pass criterion, message template and `RETRY, then FAIL ITEM` Action. Its three siblings in that row shipped; TRACE alone has zero enforcement, because a spec requirement carries no machine-readable id by any agreed convention. Spec `z7nbn1` 4.4 deferred it to backlog `vy20et` and, until it exists, binds the repository to the negative claim that "a produced plan MUST NOT be described as trace-verified". The work splits cleanly at a decision the maintainer owns: the convention must be an approved spec BEFORE a parser reads it, because the convention IS the parser's input grammar, and in-tree research `vkub9o` recommended against a parser on grounds that must be reconciled rather than ignored.
- Scope: Coordinate two children: Order 01 authors the convention, retrofit policy and TRACE contract as a spec and hands it to human review; Order 02 builds the parser, the `spec_plan_trace` verifier, its production wiring and its tests, gated on that spec being approved. This orchestrator performs no product change of its own and writes no spec, no parser and no test.
- Scope-Paths: .aw/records/plans/pending/20260930-reqids-00-9wzlou-decide-and-build-the-spec-requirement-id-convention-that-spe.ipd.md
- Item-Dependencies: none
- Status: to-review
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: medium
- From-Backlog: vy20et
- Set: reqids
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9wzlou

## Workflow history
- 2026-09-30 same-status (aw set): status unchanged (to-review)

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored review-ready while graduating backlog `vy20et`. Carries orchestration only; every deliverable belongs to a child. The split is forced by a human approval gate between the two children, not chosen for convenience.

## Goal

Close backlog `vy20et` by shipping both halves it asks for, in the only order that works: the
requirement-ID convention as an APPROVED spec first, then the parser and the `SPEC-PLAN-TRACE` check
built against it. The Set's success condition is that TRACE enforces, that `z7nbn1` 4.4's deferral is
discharged, and that the check is described honestly as proving citation rather than implementation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: run the Set in order

- [ ] E-01 CONFIRM jjh4aj REACHED executed
  - Depends on: none
  - Expected outcome: `jjh4aj` (specify the requirement-ID convention, the retrofit/grandfathering policy and the TRACE contract) is in `.aw/records/plans/executed/` with status `executed`, every `V-*` carrying concrete evidence. Its deliverable is ONE new spec sitting at `- Status: to-review`, carrying no approval or readiness attestation.
  - Execution state: pending

- [ ] E-02 CONFIRM rtvdak REACHED executed
  - Depends on: E-01
  - Expected outcome: `rtvdak` (build the requirement-ID parser, `production_checks.spec_plan_trace`, its production wiring, the cutover registration and its tests) is in `.aw/records/plans/executed/` with status `executed`, every `V-*` carrying concrete evidence. It declares `- Item-Dependencies: executed:jjh4aj` and cannot legitimately start before E-01, because the five decisions that determine its code exist only in Order 01's spec.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | jjh4aj | `.aw/records/plans/pending/20260930-reqids-01-jjh4aj-specify-the-spec-requirement-id-addressing-convention-and-th.ipd.md` | Re-measures the spec corpus and the TRACE code path at execution HEAD, then creates ONE spec (via `aw specs new`) defining the requirement-ID namespace and the distinct acceptance namespace, the declaration-site rule, the retrofit/grandfathering policy on the existing stamped cutover mechanism, and the `SPEC-PLAN-TRACE` contract (scope, severity, grandfathered-spec pass, and the citation-not-implementation limit). Records its three design questions in the spec's own open-questions section for human ratification, then moves the spec to `to-review` with the setter. Writes NO code and edits no existing spec. | none |
| 02 | rtvdak | `.aw/records/plans/pending/20260930-reqids-02-rtvdak-build-the-requirement-id-parser-and-wire-spec-plan-trace-int.ipd.md` | Reads the five ratified decisions off the APPROVED spec, re-measures four landing sites, then implements the pure spec-side id parser, `production_checks.spec_plan_trace` as a fourth sibling verifier rendering `25kzda` 4.8's template, the cutover feature-key registration, one `findings.extend` call at the production site, and two test surfaces (pure parser units over five real corpus shapes; four end-to-end production tests plus the orchestrator case). Edits no `.spec.md`. | `executed:jjh4aj` |

## Completion criteria (the whole Set is done only when)

- Both children are in `.aw/records/plans/executed/` with `- Status: executed` and every `V-*` carrying concrete pasted evidence.
- ONE new spec exists defining the requirement-ID namespace, the distinct acceptance-criterion namespace, the declaration-site rule, the retrofit/grandfathering policy on the stamped cutover mechanism, and the `SPEC-PLAN-TRACE` contract; and it has reached `approved` by human attestation (`aw spec set approved <id6> --by-human`), which no agent may perform.
- `grep -rn 'SPEC-PLAN-TRACE' agent_workflows/` finds real enforcement, inverting the empty result executed plan `aeq7f8` recorded for the same command.
- `production_checks.spec_plan_trace` exists as a fourth sibling verifier, is called at the spec-production site beside the three shipped ones, and renders `25kzda` 4.8's message template.
- The cutover feature key is registered in `config.KNOWN_FEATURE_CUTOVERS` so grandfathering resolves to a stamped per-repository boundary rather than falling through to `None`.
- TRACE PASSES rather than fails for a grandfathered producing spec, a spec declaring no ids, and the acceptance half of a spec with no acceptance section; and a produced Set containing an Order-0 orchestrator does not fail merely because child-tracking rows cite no requirement.
- The bare suite (`python3 -m pytest`) shows an EMPTY after-minus-before failing node-ID set.
- The check is described in code as proving CITATION, not implementation, so `z7nbn1` 4.4's "MUST NOT be described as trace-verified" is replaced by an honest claim rather than an overclaim.

## Cross-IPD validation

The two children are validated independently, and the only cross-cutting properties are these. FIRST,
ORDER MATTERS AND IS ASYMMETRIC: Order 02's entire content is fixed by five decisions that exist only in
Order 01's APPROVED spec, so running them out of order does not merely reorder work, it would have Order
02 invent the convention in code. The runner sorts by dependency depth first and re-checks the edge at
dispatch, and Order 02's own first item refuses if the spec is not `approved`. SECOND, THE EDGE IS
NECESSARY BUT NOT SUFFICIENT: the dependency grammar offers `executed:`/`exists:`/`state:` edges over
plans, so `executed:jjh4aj` proves the spec was AUTHORED and handed to review and CANNOT express "and a
human approved it" (only `aw spec set approved <id6> --by-human` does that). The human act between the
children is therefore verified by Order 02's E-01 and by this plan's V-02, never by the runner. THIRD,
NEITHER CHILD MAY EDIT AN EXISTING `.spec.md`: Order 01 creates one and Order 02 declares none, so the
Set cannot silently amend `25kzda` while five other pending plans (`00pirb`, `cpi6p3`, `mt54wr`,
`6uhtko`, `4gx141`, measured at HEAD `764442f7`) queue edits to it. FOURTH, THE SURVEY RECONCILIATION
MUST SURVIVE BOTH CHILDREN: in-tree research `vkub9o` recommends "Do NOT build: a requirement parser",
and this Set builds one on the basis that the survey's decisive objection was a MISSING PLAN-TO-SPEC EDGE
which does not reach a check running inside the production dispatcher (which has already computed the
produced plan list), plus the maintainer's 2026-09-26 ruling that postdates the survey. Both children
re-measure that before writing anything, and if Order 01 concludes TRACE is still unbuildable, Order 02
must not proceed as though it had concluded otherwise.

## Deferred / out of scope (with reason)

- EVERY PRODUCT CHANGE. This orchestrator writes no spec, no parser, no check, no wiring and no test.
  - Carrier-Declined: STRUCTURALLY REQUIRED, not deferred work. Each deliverable is owned by a child named in the table above (Order 01 the spec, Order 02 the code), and the repository requires an orchestrator to carry orchestration only: the runner retires it once every child is `executed`, SKIPPING the pre-transition E/V checkpoint, so any work parked here would be marked complete having never been performed. The child table is the durable record.
- RETROFITTING EXISTING SPECS' REQUIREMENT IDS, A CORPUS-WIDE `aw check` RULE, A REQUIREMENTS-OUTSTANDING `aw attention` VIEW, A PARTIAL SPEC STATUS, AND `implemented` COMPUTED FROM COVERAGE.
  - Carrier-Declined: REJECTED OPTIONS (`vkub9o` Options B and C), costed in that survey and not disturbed by this Set; each child restates the specific exclusion it is nearest to, with its reason. A costed and rejected option is not an outstanding obligation, and `vkub9o` is the durable record if the maintainer revisits it.
- THE OTHER NINE UNBUILT `SPEC-*` CODES.
  - Carrier-Declined: OWNED BY AN APPROVED CONTRACT ELSEWHERE. `z7nbn1` 4.4 lists them as NOT IN SCOPE and leaves them with approved spec `25kzda` 4.8, which is revisited whenever that spec is. They were never in backlog `vy20et`'s scope.
- CLOSING BACKLOG `vy20et` AS `done`.
  - Carrier-Declined: A PROHIBITION, not an obligation. The runner sets the item `graduated` on verification; `done` would claim code Order 02 has not yet written. The item remains the durable record until then.

## Scope check

- Over-scope: none. `- Scope-Paths:` names only this plan file, which is the correct declaration for a plan whose whole function is coordination.
- Under-scope: this plan changes nothing by itself, and the Set cannot complete without a human act between its two children: Order 02's whole content is fixed by five decisions only an APPROVED spec settles, and an agent may not approve a spec. A reader asking "what can I run unattended?" should know that Order 01 is runnable once approved, while Order 02 additionally waits on the maintainer approving Order 01's spec, which no runner can perform or detect for them.

## Required tests / validation

THIS PLAN RUNS NO TESTS AND SHIPS NO CODE; its validation is that both children reached `executed` with
their own evidence, which is what the two `V-*` items below inspect. Each child owns the real test
surface: Order 01's validation is documentary and structural (`aw check` clean on the new spec, plus one
bare suite run as a records-only regression guard), and Order 02's is behavioral (pure parser units over
five real corpus shapes, four end-to-end production tests plus the orchestrator case, and an empty
after-minus-before failing node-ID set against the bare suite).

## Spec / documentation sync

NO SPEC OR DOCUMENT IS EDITED BY THIS PLAN. The Set's spec work is entirely Order 01's, which CREATES one
new spec and edits no existing one, and Order 02 declares no `.spec.md` at all. Two relationships are
therefore discharged by the children and recorded here only so the Set reads coherently: `z7nbn1` 4.4's
deferral of `SPEC-PLAN-TRACE` is ADDRESSED by Order 01's spec but not DISCHARGED until Order 02 executes,
and `25kzda` 4.8's TRACE row is ADOPTED verbatim by Order 02 unless Order 01's spec decided to amend it,
in which case that amendment belongs to the plan the spec names rather than to this Set.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: this orchestrator has no open design question of its own. The Set's three real questions (the mandatory-requirement marker, adopt-or-amend `25kzda` 4.8, and whether dotted section/paragraph ids count as a requirement namespace) all belong to Order 01, which records them with measured options and recommendations and places them in the spec's own open-questions section for human ratification at spec approval. Duplicating them here would create two places for one answer.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep jjh4aj` showing the plan in the terminal directory, plus its `- Status:` line reading `executed`. Paste the path and `- Status:` of the spec it created, showing `to-review`, and paste `grep -nE '^- (Approval|Readiness):' <spec>` returning NO match (proving no forged attestation). Confirm every `V-*` in `jjh4aj` carries non-empty `Observed evidence`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep rtvdak` and its `- Status:` line reading `executed`. Paste `grep -rn 'SPEC-PLAN-TRACE' agent_workflows/` showing the code now EXISTS (the inverse of `aeq7f8`'s recorded empty result), and paste `rtvdak`'s V-08 evidence block showing the four end-to-end outcomes and the empty after-minus-before failing node-ID set. Confirm the spec Order 01 produced reached `approved` before `rtvdak` executed, by pasting that spec's `## Workflow history` approval line with its `--by-human` attestation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A TWO-STEP SET WITH AN APPROVAL GATE IN THE MIDDLE, and approving this parent
does not approve the convention itself. Order 01 writes the requirement-ID convention and the TRACE
contract as a spec and stops at `to-review`. The maintainer then approves (or redirects) that spec, which
is where the design decisions are actually ratified. Only then does Order 02 build the parser and turn
`SPEC-PLAN-TRACE` into an enforcing check.

THE SET CANNOT RUN STRAIGHT THROUGH UNATTENDED, and that is by design rather than an oversight. Order 02
depends on a human approval that no dependency edge can express, so a run that queues both will
correctly execute Order 01 and then depend on the maintainer before Order 02 is legitimate. Order 02's
own first item refuses and reports if the spec is not `approved`.

THE REVIEWER'S SHARPEST QUESTION, NAMED HERE RATHER THAN BURIED IN A CHILD. In-tree research `vkub9o`
explicitly recommends "Do NOT build: a requirement parser", and this Set builds one. The reconciliation
is that the survey's decisive objection was a MISSING PLAN-TO-SPEC EDGE, and that objection does not reach
a check running inside the production dispatcher, which has already computed the produced plan list
itself; and that the maintainer's 2026-09-26 ruling postdates the survey and directs a convention AND a
parser as their own spec. Both children re-measure this before writing anything, and Order 01 may
legitimately conclude TRACE is still unbuildable. If a reviewer rejects the reconciliation, stop the Set
here rather than at Order 02.

EXECUTION CONTRACT FOR THIS PARENT. It performs no product change. Do not add a deliverable to it: if
the Set needs work no child covers, ADD A CHILD and add its row to the table above, because the runner
retires an orchestrator without an agent turn and without the pre-transition E/V checkpoint, so work
parked here would be marked complete having never been performed. Do not delete the child checklist
either; it is what makes the Set execute completely when a human runs it by hand. Never push.

POST-GATE LIFECYCLE MOVE. This plan is retired by the runner once BOTH children are `executed` on disk,
spending no agent turn. If the Set is executed by hand instead, tick each `E-*` only after confirming the
named child really reached `executed`, record the evidence in the matching `V-*`, then move this plan to
`.aw/records/plans/executed/` through the tooled transition, never by hand-editing the status.
