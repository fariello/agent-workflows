# IPD: Decide and build the spec requirement-ID convention that SPEC-PLAN-TRACE needs

- Date: 2026-09-30
- Kind: orchestrator
- Concern: Approved spec `25kzda` 4.8 declares `SPEC-PLAN-TRACE` with a fixed pass criterion, message template and `RETRY, then FAIL ITEM` Action. Its three siblings in that row shipped; TRACE alone has zero enforcement, because a spec requirement carries no machine-readable id by any agreed convention. Spec `z7nbn1` 4.4 deferred it to backlog `vy20et` and, until it exists, binds the repository to the negative claim that "a produced plan MUST NOT be described as trace-verified". The work splits cleanly at a decision the maintainer owns: the convention must be an approved spec BEFORE a parser reads it, because the convention IS the parser's input grammar, and in-tree research `vkub9o` recommended against a parser on grounds that must be reconciled rather than ignored.
- Scope: Coordinate two children: Order 01 authors the convention, retrofit policy and TRACE contract as a spec and hands it to human review; Order 02 builds the parser, the `spec_plan_trace` verifier, its production wiring and its tests, gated on that spec being approved. This orchestrator performs no product change of its own and writes no spec, no parser and no test.
- Scope-Paths: .aw/records/plans/pending/20260930-reqids-00-9wzlou-decide-and-build-the-spec-requirement-id-convention-that-spe.ipd.md
- Item-Dependencies: none
- Status: draft
- Coverage: fail
- Coverage-Fingerprint: 174d25c7615db68a1d03528b95fb77f9305a2782df8b9d4e2031d9a4b6061979
- Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
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
- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): each completion criterion and cross-cutting property now names its owner; the backlog close is the runner's.
- 2026-10-06 draft (aw set): demoted approved -> draft: APPROVAL WITHDRAWN: returned to authoring by gradcover 52opph: uncovered obligation: Close backlog `vy20et` by shipping both halves it asks for
- 2026-10-06 coverage fail (aw oc run): fingerprint 174d25c7615d, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review complete; 5 findings all fixed; the human approval gate is now runner-enforced via a state:spec:approved edge written by Order 01 E-09

- 2026-10-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101 (HIGH, fixed), PR-102 (MEDIUM, fixed), PR-103 (MEDIUM, fixed), PR-104 (LOW, fixed), PR-105 (LOW, fixed). Reviewed at HEAD `b66eb5f9`; plan byte-identical to the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` reported `clean`, and because this plan's own first `- Kind:` bullet reads `orchestrator` the `IPD-S407` child-row check applied and reported NO violation, so no repair loop ran. THE ORCHESTRATOR COVERAGE QUESTION, which is the one that matters most for a parent, PASSES: every one of the eight completion criteria maps to a named child item (the spec to `jjh4aj` E-03..E-09, the parser/verifier/wiring/cutover/tests to `rtvdak` E-03..E-08), so the parent carries orchestration only and the runner may legitimately retire it without an agent turn. THE DOMINANT FINDING IS THAT THE PLAN ARGUED AWAY A GUARD THE REPOSITORY ALREADY SHIPS: it claimed the dependency grammar offers edges only "over plans" so no edge "CANNOT express 'and a human approved it'", and concluded the human gate is undetectable by any runner. Measured, `25kzda` 2.7's grammar admits `state:spec:approved:<id6>`, `parse_dependency_token` returns a valid `state`/`spec`/`approved` edge, `edge_satisfied` refuses the dependent with "needs exactly 'approved'", and `aw ipd dependencies set rtvdak executed:jjh4aj state:spec:approved:<id6> --dry-run` validates. So the Set's one human gate was being left to an agent's self-discipline when the runner could hold it; Order 01 E-09 now writes that edge and the parent's V-02 verifies it. Three further corrections: the five-plan `25kzda` co-editor list was partly false and stale (`00pirb` has executed; `mt54wr` and `6uhtko` never declared that path, including at the cited HEAD; 13 pending plans declare it now), replaced by a re-derivation rule; the gate lacked the paste-actual-output honesty rule, a path-scoped commit instruction and conditional finalize ownership, all added; and the survey reconciliation is now recorded as STRONGER than authored, because `vkub9o`'s decisive objection was filed as backlog `1zknu7`, is `done`, and its recommendation #2 shipped as `check.plan-spec-link-missing` firing on 34 plans. Full findings and decisions: `.aw/records/reviews/20260930-reqids-00-9wzlou-decide-and-build-the-spec-requirement-id-convention-that-spe.review.md`.
- 2026-09-30 same-status (aw set): status unchanged (to-review)

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored review-ready while graduating backlog `vy20et`. Carries orchestration only; every deliverable belongs to a child. The split is forced by a human approval gate between the two children, not chosen for convenience.

## Goal

Ship both halves backlog `vy20et` asks for (the item closes through the runner's normal backlog close when the last carrier executes, never by hand from this plan), in the only order that works: the
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

- [Owner: jjh4aj and rtvdak] Both children are in `.aw/records/plans/executed/` with `- Status: executed` and every `V-*` carrying concrete pasted evidence.
- [Owner: jjh4aj (its E-09 writes the edge)] Order 02's `- Item-Dependencies:` carried `state:spec:approved:<spec-id6>` beside `executed:jjh4aj` before it executed, written by `aw ipd dependencies set` during Order 01's E-09, so the Set's human approval gate was enforced by the runner rather than only by Order 02's own first item (added at review 2026-10-01).
- [Owner: jjh4aj (creates the spec); the human approval is the maintainer's, enforced by the edge] ONE new spec exists defining the requirement-ID namespace, the distinct acceptance-criterion namespace, the declaration-site rule, the retrofit/grandfathering policy on the stamped cutover mechanism, and the `SPEC-PLAN-TRACE` contract; and it has reached `approved` by human attestation (`aw spec set approved <id6> --by-human`), which no agent may perform.
- [Owner: rtvdak] `grep -rn 'SPEC-PLAN-TRACE' agent_workflows/` finds real enforcement, inverting the empty result executed plan `aeq7f8` recorded for the same command.
- [Owner: rtvdak] `production_checks.spec_plan_trace` exists as a fourth sibling verifier, is called at the spec-production site beside the three shipped ones, and renders `25kzda` 4.8's message template.
- [Owner: rtvdak (E-06)] The cutover feature key is registered in `config.KNOWN_FEATURE_CUTOVERS` so grandfathering resolves to a stamped per-repository boundary rather than falling through to `None`.
- [Owner: rtvdak (E-08)] TRACE PASSES rather than fails for a grandfathered producing spec, a spec declaring no ids, and the acceptance half of a spec with no acceptance section; and a produced Set containing an Order-0 orchestrator does not fail merely because child-tracking rows cite no requirement.
- [Owner: jjh4aj and rtvdak, each at its own boundary; rtvdak V-08 is the last] The bare suite (`python3 -m pytest`) shows an EMPTY after-minus-before failing node-ID set.
- [Owner: rtvdak (E-05)] The check is described in code as proving CITATION, not implementation, so `z7nbn1` 4.4's "MUST NOT be described as trace-verified" is replaced by an honest claim rather than an overclaim.

## Cross-IPD validation

[Owners: the FIRST and SECOND properties are enforced by the runner through `rtvdak`'s `state:spec:approved:89xjll` edge and checked by `rtvdak` V-01; the THIRD by each child's `- Scope-Paths:` and the finalize scope gate, with the co-editor re-derivation done by `rtvdak` at execution; the FOURTH by `rtvdak`, which builds the parser and must record the survey reconciliation in its own evidence. This plan performs none of them.] The two children are validated independently, and the only cross-cutting properties are these. FIRST,
ORDER MATTERS AND IS ASYMMETRIC: Order 02's entire content is fixed by five decisions that exist only in
Order 01's APPROVED spec, so running them out of order does not merely reorder work, it would have Order
02 invent the convention in code. The runner sorts by dependency depth first and re-checks the edge at
dispatch, and Order 02's own first item refuses if the spec is not `approved`. SECOND, THE APPROVAL GATE
IS MACHINE-EXPRESSIBLE AND MUST BE EXPRESSED, which CORRECTS this plan's own earlier claim that it is
not. The authored text said the grammar offers edges "over plans" so `executed:jjh4aj` "CANNOT express
'and a human approved it'". That is FALSE, measured: spec `25kzda` Section 2.7's grammar admits
`state-edge = "state:" target-type ":" status ":" id6` with `target-type = "ipd" | "spec" | "backlog"`,
`runner_shared.parse_dependency_token("state:spec:approved:<id6>")` parses to
`ItemDependency(kind='state', target_type='spec', status='approved', ...)`, and
`runner_shared.edge_satisfied`'s `state:` branch refuses with
"spec <id6> is <actual>, needs exactly 'approved'" until the spec really carries that status. So the
runner CAN hold Order 02 until a human approves the spec, and it should: a gate the machine can check
must not be left to an executing agent's self-discipline. Order 02 must therefore ADD
`state:spec:approved:<spec-id6>` to its `- Item-Dependencies:` once the id6 exists, which is why Order
01's E-09 now owns writing it through the setter (the id6 is minted at Order 01 execution time, so it
cannot be authored in advance). Order 02's E-01 refusal and this plan's V-02 REMAIN as the second layer,
because the edge proves the status field says `approved` while only the spec's own history proves a human
attested it with `--by-human`. THIRD,
NEITHER CHILD MAY EDIT AN EXISTING `.spec.md`: Order 01 creates one and Order 02 declares none, so the
Set cannot silently amend `25kzda` while other pending plans queue edits to it. THE PROPERTY IS THE BAR,
NOT THE COUNT: re-derive the co-editor population at execution with
`rg -l '^- Scope-Paths:.*25kzda' .aw/records/plans/pending/` rather than trusting a number, because this
is a LIVE artifact population that drifts daily. The authored list of five (`00pirb`, `cpi6p3`, `mt54wr`,
`6uhtko`, `4gx141`, "measured at HEAD `764442f7`") was partly wrong and is now stale, which is itself the
reason for the re-derivation rule: re-measured at review HEAD `b66eb5f9`, `00pirb` has since EXECUTED (it
is `b7tlsh`/`00pirb` in `executed/`), while `mt54wr` and `6uhtko` declare no `25kzda` path at all and
never did, including at the cited HEAD; 13 pending plans now declare one. The claim that matters is
unchanged and is what an executor must hold: THIS Set declares no `.spec.md` edit at all, so it cannot
collide with any of them whatever their number. FOURTH, THE SURVEY RECONCILIATION
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
- Under-scope: this plan changes nothing by itself, and the Set cannot complete without a human act between its two children: Order 02's whole content is fixed by five decisions only an APPROVED spec settles, and an agent may not approve a spec. A reader asking "what can I run unattended?" should know that Order 01 is runnable once approved, while Order 02 additionally waits on the maintainer approving Order 01's spec.
  CORRECTED 2026-10-01 AT REVIEW: the authored clause "which no runner can perform or detect for them" is wrong in its second half and the error mattered, because it argued away a guard the repository already ships. A runner cannot PERFORM the approval, which is right and is the whole point of `--by-human`. It CAN DETECT it: `state:spec:approved:<id6>` is a legal edge and `runner_shared.edge_satisfied` refuses the dependent until the spec holds exactly that status. Order 01's E-09 now writes that edge onto Order 02, so Order 02 is held by the RUNNER and not merely by its own first item's self-discipline. See "Cross-IPD validation" SECOND for the measurement.

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

## Coverage findings

- "Close backlog `vy20et` by shipping both halves it asks for"
- "NOT THE COUNT: re-derive the co-editor population at execution with"
- "Order 02's E-01 refusal and this plan's V-02 REMAIN as the second layer, because the edge proves the status field says `approved` while only the spec's own history proves a human"
- "and it has reached `approved` by human attestation (`aw spec set approved <id6> --by-human`), which no agent may perform."

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep jjh4aj` showing the plan in the terminal directory, plus its `- Status:` line reading `executed`. Paste the path and `- Status:` of the spec it created, showing `to-review`, and paste `grep -nE '^- (Approval|Readiness):' <spec>` returning NO match (proving no forged attestation; confirmed at review that this command exits 1 with no output on a real `to-review` spec, so an empty result is the pass and not a broken command). Confirm every `V-*` in `jjh4aj` carries non-empty `Observed evidence`. ALSO paste Order 02's `- Item-Dependencies:` line, which E-09 must have extended to `executed:jjh4aj, state:spec:approved:<spec-id6>` naming the id6 of the spec just created, and paste `aw check --agent` (or `aw check plans`) showing no dangling-dependency finding against `rtvdak`. If that edge is absent, Order 01 did not finish its last item: say so rather than proceeding, because the Set's human gate is then unenforced by the runner.
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

AND THE RECONCILIATION IS NOW STRONGER THAN THE AUTHORED TEXT CLAIMS, measured at this Set's 2026-10-01
plan review. The survey's decisive objection was not merely out of reach of the dispatcher: it has since
been FIXED. The survey filed its "single most important structural finding" as backlog `1zknu7`, which is
now `done`, discharged by executed plan `0ykozn`, and the survey's own recommendation #2 ("add ONE
`aw check` rule on the JOIN EDGE, not on requirement ids") SHIPPED as
`check.plan-spec-link-missing`, which fires on 34 plans in the live tree right now. The survey's
worked example moved with it: `c4gd2h` had 0 plans carrying `- From-Spec:` against 37 mentioning it when
the survey measured, and at review 1 of 71 carries the edge with a live checker nagging the rest. So the
survey's #3 ("do NOT build a requirement parser") rested on a blocker that its own #2 was written to
remove, and #2 is done. That does NOT make the survey wrong, and no child may cite this as licence to
skip its own re-measurement: the survey's cost arguments against a corpus-wide retrofit are untouched and
are exactly what this Set still defers. It removes the ONE objection that would have made TRACE
pointless. Re-derive both numbers at execution rather than quoting these.

EXECUTION CONTRACT FOR THIS PARENT. It performs no product change. Do not add a deliverable to it: if
the Set needs work no child covers, ADD A CHILD and add its row to the table above, because the runner
retires an orchestrator without an agent turn and without the pre-transition E/V checkpoint, so work
parked here would be marked complete having never been performed. Do not delete the child checklist
either; it is what makes the Set execute completely when a human runs it by hand.

PASTE ACTUAL OUTPUT; NEVER CLAIM A RESULT YOU DID NOT OBSERVE. Every `V-*` command below must be RUN and
its real output pasted into `Observed evidence`. A claimed pass with no pasted output does not satisfy
this plan, and for a parent whose only job is to verify its children that rule IS the plan's whole value:
an orchestrator that asserts "both children executed" without pasting the directory listing and the
status lines has verified nothing.

COMMIT PATH AND SCOPE. Commit only `- Scope-Paths:` (this plan file alone) through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, and never push. Verify the staged set with
`git diff --cached --name-only` before committing and unstage anything you did not modify with
`git restore --staged <path>`. THE SCOPE LINE IS A DECLARATION, NOT A STOP CONDITION: if an out-of-scope
edit genuinely turns out to be necessary, make it and JUSTIFY it to `aw ipd finalize` with a
`--scope-reason` per path rather than halting, which is what that gate already enforces.

POST-GATE LIFECYCLE MOVE. Reaching `.aw/records/plans/executed/` is UNCONDITIONALLY OWED, but its OWNER
is CONDITIONAL. Under `aw oc run` / `aw agy run` the RUNNER retires this plan once BOTH children are
`executed` on disk, spending no agent turn, so an executing agent must NOT invoke `aw ipd finalize` on it
in a runner-driven execution. If the Set is executed BY HAND instead, tick each `E-*` only after
confirming the named child really reached `executed`, record the pasted evidence in the matching `V-*`,
and then finalize through the sanctioned verb (`aw ipd finalize`, or `aw ipd set executed <plan>`). Either
way NEVER hand-edit `- Status:` and NEVER `git mv` this file into `executed/` yourself.

A RETIREMENT REFUSAL IS NOT A FAILURE AND MUST BE REPORTED RATHER THAN WORKED AROUND. The runner refuses
to retire this plan if any child row names an unauthored plan, if a child cannot finish in this run, or if
its own transition refuses, and it names which. The remedy is to run the remaining child or resolve what
it named; it is never to delete a checklist row or a child row to make the refusal go away, which would
destroy the orchestration record this plan exists to carry.
