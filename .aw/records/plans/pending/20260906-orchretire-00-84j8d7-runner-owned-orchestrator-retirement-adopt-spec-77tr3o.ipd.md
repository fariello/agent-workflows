# IPD: Runner-owned orchestrator retirement (adopt spec 77tr3o)

- Date: 2026-09-06
- Kind: orchestrator
- Concern: An Order-0 orchestrator is supposed to be retired to `executed` by the runner once its Set's last outstanding child completes, so it does not linger in `pending/` forever. That has never happened. Measured across all 102 durable run records at HEAD `844d195c`: `orchestrator-finalized` fired 0 times, `orchestrator-deferred` fired 28 times across 15 distinct orchestrators. `finalize_orchestrator` was written `801dd28a` (2026-08-27), three days AFTER the gated terminal transition landed `99760832` (2026-08-24), so it was born blocked and has never once succeeded. Four orchestrators sit in `pending/` today (`rh5tt6`, `h0zljh`, `5e4sb6`, `3m0urk`) and `AGENTS.md:42` tells every agent the mechanism works and not to raise it.
- Scope: ORCHESTRATOR - authors NO product code. Coordinates the three children that adopt spec `77tr3o`: the shared on-disk eligibility predicate (01), the runner-owned retirement transition resolving the E/V and receipt gates (02), and the both-host dispatch wiring plus the documentation correction (03). Owns the child sequence, the whole-Set completion criteria, and the cross-IPD validation. Its own execution work is E-01 only (whole-Set verification). Explicitly EXCLUDES the general `dependency-blocked`-is-terminal defect for ordinary items (`nueip1`), the `EXECUTION_SUCCESS_STATES` dependency-edge defect, the `aw set executed` worker-role bypass, and actually retiring the four currently-stuck orchestrators.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: orchretire
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 84j8d7
- Approval: 2026-09-06, recorded via aw ipd set: status set to approved
- From-Backlog: kxkc04
- From-Spec: 77tr3o

## Workflow history
- 2026-09-06 approved (aw set): status set to approved
- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: PR-001..PR-005 fixed, Readiness go-pending-approval

- 2026-09-06 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED, no deferrals, no open questions. Every load-bearing measurement re-verified independently at HEAD 46da9b40 (0 orchestrator-finalized vs 28 deferred across 103 run records and 15 distinct id6s; the 2026-08-24 gate predating the 2026-08-27 rollup; AGENTS.md:42 generated from engine.py:1207). PR-001 (HIGH) is the substantive one and was fixed in its OWNING plan pgq326 as new E-07/V-07: criterion 5 and child 03's E-04 specified only the SHARED ACTION DECIDER, but agy has no dispatch branch that reads `orchestrate` at all, so the Set could have shipped with V-04's object-identity assertion passing while `aw agy run` still spent an agent turn agent-executing an orchestrator, which is precisely the failure spec R-10 forbids. Also fixed: the recursive self-retirement note invited discharging this plan by the very rollup that SKIPS the E/V checkpoint, which would have marked the Set verified without performing E-01 (PR-002, HIGH); the gate carried no scope fence, honesty rule, or commit contract (PR-003, MEDIUM); "real run" overpromised what OQ-01 actually licenses (PR-004, MEDIUM); and the fourth refusal cause was not required evidence (PR-005, MEDIUM). Self-review disclosure carried in the review record: the reviewer authored these plans in the same session.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored complete from approved spec 77tr3o, which the maintainer approved by attestation after supplying the design contract himself. Graduated from backlog kxkc04, whose prescription this Set deliberately EXTENDS rather than follows: kxkc04 says "leave it queued", which is right for 27 of the 28 observed deferrals and would make the 28th (`rh5tt6`, `finalize-refused`) spin forever.
- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the runner actually retire a Set's orchestrator when the Set completes, on both hosts, with an
honest record of what was done and why, and without opening any route by which an ordinary plan reaches
`executed` without evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: whole-Set verification

- [ ] E-01 Verify the assembled Set end to end after all three children are `executed`: an orchestrator is retired by a scripted run when its last outstanding child completes, the retirement is refused for the three ineligible shapes (unfinished children, no children, unauthored child rows) AND for a refusing transition, both hosts reach the same DISPATCHED OUTCOME (no agent turn on either), and the corrected AGENTS.md claim matches demonstrated behavior. This is verification only and authors no product code.
  - Depends on: none
  - Expected outcome: a single pasted demonstration covering retire, each of the four refusals, host outcome symmetry, and the documentation claim, with the end-to-end coverage limit stated honestly.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Children are SEQUENTIAL, not parallel: 02 consumes 01's predicate, 03 wires both, and all three touch
`runner_shared.py`. Declaring them parallel would guarantee conflicts in the repo's most contended files.

| Order | Id | Child | Depends on |
|-------|----|-------|------------|
| 01 | `5942n7` | The shared on-disk Set-completeness decision predicate. Reads the PLANS TREE, not the run queue, so a run that completes only the Set's LAST outstanding child still sees a complete Set. Returns a typed reason per refusal. Refuses a Set whose child table declares unauthored rows (the `rununify` case). Implements R-1, R-2, R-3, R-9, R-10. | none |
| 02 | `ueg5cf` | The runner-owned retirement transition. Resolves the two structural gates EXPLICITLY: the `pre-transition` E/V requirement (R-5) and the `begin` receipt requirement (R-6), and writes the honest terminal history entry (R-4). R-5's shape is DECIDED by the maintainer, not the executor: a SEPARATE rollup transition, with `ipd_lint.py` out of bounds, plus a drift test pinning the shared gate set. Decides nothing; consumes 01. | 01 |
| 03 | `pgq326` | Both-host dispatch wiring. Replaces the single terminal-status write with retire/reconsider/terminate (R-7, R-8), makes the four refusal reasons distinguishable (R-9), gives the agy runner the `orchestrate` action it entirely lacks via SHARED code AND the dispatch branch that acts on it (R-10), and corrects the false AGENTS.md claim via its generator (R-11). | 01, 02 |

CHILD 03 CARRIES A GAP THIS ORCHESTRATOR IS RAISING RATHER THAN HIDING, because it is the one place
where a child's own validation could pass while the Set's completion criterion 5 remains false. Its
E-04 and V-04 specify only the shared ACTION DECIDER and prove it by object identity. That is the right
mechanism and it is HALF the job on agy: `agy_runipd.py:2973` computes `is_review = action == "review"`
and nothing else, and `:4138` calls `execute_item` for whatever the action is, so agy has NO branch
that reads `orchestrate` (verified: the token is absent from `agy_runipd.py` outside the unrelated
`orchestrate_isolation` import). Give agy the shared decider alone and it returns `orchestrate`, agy
ignores the value, and an agent turn is spent authoring against the orchestrator anyway. The Set is not
complete until agy's dispatch ACTS on the action, and this orchestrator's V-01 now requires the
dispatched OUTCOME on both hosts rather than the decision alone.

THE SET IS FULLY AUTHORED: every row above resolves to an existing plan file. This is stated explicitly
because child 01 E-03 implements a check for exactly this property, and `5e4sb6` is the counter-example
that motivated it (its child table declares a row `03+` that was never written).

## Completion criteria (the whole Set is done only when)

1. A runner dispatch retires an eligible orchestrator, and the retirement fires when that dispatch
   completed only the Set's LAST outstanding child, earlier children having executed in previous runs.
   The accepted evidence is a SCRIPTED run over a synthetic Set, not a genuine unattended multi-item
   run: OQ-01 resolves that, with the maintainer's confirmation, and the limit is stated at finalize.
   Read "real run" nowhere in this plan as promising an unattended proof.
2. `orchestrator-finalized` appears in an `events.jsonl` for the first time in this repository's
   history.
3. All FOUR refusal causes are distinguishable in the durable record, and no summary claims an unmet
   dependency it cannot name. The fourth cause, `transition refused`, is NOT optional to demonstrate:
   it is the `rh5tt6` case, the one whose misclassification as RECONSIDER produces an infinite retry.
4. An orchestrator whose children are merely unfinished is RECONSIDERED within the run; one whose child
   is permanently unfinishable TERMINATES without spinning.
5. `aw agy run` DISPATCHES an approved orchestrator as a retirement and spends NO agent turn on it.
   Sharing the action decider is necessary and NOT sufficient for this criterion: today
   `agy_runipd.py:2973` derives only `is_review = action == "review"` and `:4138` calls `execute_item`
   unconditionally, so an `orchestrate` action that agy has no branch for still takes the EXECUTE path.
   A decider that returns `orchestrate` into a host that ignores the value satisfies an object-identity
   assertion while still burning an agent turn on a plan the runner has superseded, which is the exact
   failure this criterion exists to prevent. Verify the DISPATCHED OUTCOME on agy, not only the decision.
6. No new route exists by which a CHILD plan reaches `executed` without evidence, demonstrated by a
   sabotage rather than asserted.
7. `AGENTS.md`'s managed block describes behavior the tests demonstrate, edited via `engine.py` and
   idempotent on re-render.
8. Bare `python3 -m pytest` green in the primary checkout, with failing node ids compared rather than
   totals.

## Cross-IPD validation

- The predicate (01) and the transition (02) must not drift: 02's tests include a case where the
  transition refuses because the predicate says ineligible.
- The dispatch (03) must consume 01 and 02 rather than reimplementing either; a second eligibility test
  or a second transition anywhere is a Set-level failure regardless of whether the suite passes.
- Host symmetry is verified at TWO levels, and object identity alone is insufficient. (i) The DECISION
  by object identity (`agy.<decider> is oc.<decider>`), not by comparing outputs, because equal outputs
  from two copies is precisely the re-fork this repo has already paid for. (ii) The DISPATCHED OUTCOME,
  because agy currently has no branch reading `orchestrate` at all, so identity of the decider is
  compatible with agy still agent-executing the plan. A Set that ships (i) without (ii) has moved the
  defect rather than fixed it, and its own tests would pass.
- The AGENTS.md correction (03 E-05) must be validated against the tests, not against intent: if a
  completion criterion above is not demonstrated, the sentence claiming it must not be written.

## Deferred / out of scope (with reason)

- `nueip1`: the general `dependency-blocked`-is-terminal defect for ORDINARY items and the
  all-or-nothing drain break. Same ~40-line region, different rule. Neither subsumes the other; fixing
  both here would make the Set unreviewable.
- `EXECUTION_SUCCESS_STATES` accepting `substantially-complete` for dependency EDGES
  (`oc_runipd.py:274`). This is why `xdr83v` was dispatched against a prerequisite whose work was
  stranded on a lane, and it deserves its own item.
- The `aw set executed` worker-role bypass (`status_set.py` checks `worker_role_active` zero times),
  which reopens `i452hf`.
- Retiring `rh5tt6`, `h0zljh`, `5e4sb6`, `3m0urk`. Under this Set's own rules only `rh5tt6` qualifies;
  `5e4sb6` fails the unauthored-rows check and the other two have unexecuted children. Doing it is a
  consequence of the fix, not part of the mechanism.

## Scope check

- Over-scope: none. This orchestrator writes no product code and its `Scope-Paths` is the plans
  directory only.
- Under-scope: the orchestrator cannot verify criterion 1 without a real run, which is expensive. The
  accepted evidence is a scripted run over a synthetic Set plus dispatch-level tests, and that limit
  must be stated at finalize rather than glossed as a full unattended proof.

## Required tests / validation

Bare `python3 -m pytest` in the primary checkout after all three children land, plus the end-to-end
demonstration E-01 requires. Baselines are measured per child at execution time in the executing
worktree; compare failing NODE IDS, never totals (a lane worktree legitimately reports
lane-environment failures, 35 measured on `xdr83v`'s lane).

## Open questions

### OQ-01: is a real unattended multi-item run required before this Set may be called done?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as no, and CONFIRMED BY THE MAINTAINER 2026-09-06 when
  asked directly, choosing the scripted rehearsal WITH the limit stated openly over either requiring a
  real run first or filing a follow-up item to confirm it later. A genuine unattended run over a real Set
  costs hours and hundreds of dollars (the observed run was 13h42m and $341.65), so requiring one as a
  completion gate would stall the fix indefinitely. A scripted run over a synthetic Set exercises the
  same dispatch path and is the evidence criterion 1 accepts. This mirrors the precedent recorded in
  `i452hf`, which closed noting that a real end-to-end unattended proof "needs an actual run" and was
  deliberately not held for one. The honest limit MUST be carried into the Set's finalize record rather
  than hidden, which is the condition attached to the answer. As this plan's own gate section notes, this
  orchestrator becomes the natural first real-world test once its children land.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste, in one place: (a) a scripted run retiring an orchestrator whose last outstanding child completed in that run, with the `orchestrator-finalized` event; (b) all FOUR refusal causes each naming its specific reason, the fourth being a REFUSING transition (the `rh5tt6` shape), shown to TERMINATE rather than retry; (c) host symmetry proven at BOTH levels: `agy.<decider> is oc.<decider>` returning True AND the agy DISPATCH outcome for an approved orchestrator, showing it was retired or refused with NO agent turn and NO `execute_item` call (an object-identity assertion alone does NOT satisfy this item, because agy today ignores the action value at `agy_runipd.py:2973`/`:4138`); (d) the AGENTS.md diff alongside the test that demonstrates each behavior it claims, plus an explicit statement of what the new sentence does NOT claim; (e) a sabotage showing a CHILD plan still cannot reach `executed` without evidence; and (f) the bare suite summary. State the end-to-end coverage limit explicitly: name it as a scripted synthetic-Set rehearsal and do NOT describe it as an unattended proof.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. All open questions are RESOLVED (OQ-01, non-blocking); no maintainer decision is
outstanding, so nothing here waits on a human beyond approval itself.

SCOPE FENCE: touch only `Scope-Paths` (`.aw/records/plans/pending`). This orchestrator authors NO
product code; if you find yourself editing a module under `agent_workflows/`, you are in the wrong plan.
Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and
JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize` refuses to complete without
a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path).

Verify the assembled Set only after all three children are `executed`. Do not claim a completion
criterion that the children's own evidence does not demonstrate, and specifically do not write an
AGENTS.md sentence asserting behavior no test exercises: the defect this Set fixes is a documented claim
that was never true, and repeating that pattern in the fix would be the worst possible outcome.

HONESTY RULE (hard MUST): when you report tests or validation passed, paste the ACTUAL runner output
into the `V-*` Observed evidence; never claim a success you did not run. State the end-to-end coverage
limit honestly, as a scripted synthetic-Set rehearsal rather than an unattended proof.

COMMITS: path-scoped only (`git commit -m msg -- <path>`); never `git add -A`/bare/`-a`; never push;
never create a tag or a release. Other agents may be working in this same checkout, so verify the staged
set (`git diff --cached --name-only`) before every commit and unstage anything that is not yours.

NOTE ON THIS PLAN'S OWN RETIREMENT, which is deliberately recursive AND carries a trap that must not be
walked into. Once this Set's children are all `executed`, this orchestrator becomes exactly the artifact
the Set teaches the runner to retire, so it is the natural first real-world subject of criterion 1.

BUT DO NOT RETIRE THIS PLAN BY THE ROLLUP INSTEAD OF PERFORMING E-01. The rollup exists precisely
BECAUSE it skips the `pre-transition` E/V checkpoint (spec R-5, shape (b)), so retiring this plan that
way would discharge it WITHOUT ever performing E-01/V-01, and E-01/V-01 is the whole-Set end-to-end
verification that is the ONLY evidence the Set actually works. Using the mechanism to skip the
verification that the mechanism functions would prove nothing while producing an `executed` plan
asserting it had been proven, which is precisely the never-true documented claim this Set exists to
correct.

THE CORRECT ORDER, therefore: perform E-01 and record V-01's evidence FIRST, and only then transition.
Whether the final transition is a `aw ipd finalize` or a demonstration of the new rollup is a free
choice ONCE the evidence exists; it is not a substitute for the evidence. If a runner retires this plan
automatically before E-01 was performed, that is a premature discharge to REPORT, not a proof to claim.

Two facts bound how easily that could happen, stated precisely because overstating the risk would be
its own false claim. `action_for` returns `orchestrate` for a `reviewed` orchestrator, not only an
approved one (verified directly), so the ACTION is decided before human approval. But the queue only
admits `to-review`/`draft`/`approved`/`auto-approved` as `queued` (`oc_runipd.py:2922-2924`), so a
merely `reviewed` plan is not dispatched, and the exposure begins at APPROVAL rather than at review.
That is narrow, and it is not zero: from the moment a human approves this plan it is rollup-eligible,
and its E-01 has by construction not yet run.

POST-GATE LIFECYCLE. Do not claim done or move this plan until every `V-*` is verified with concrete
pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed
by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
