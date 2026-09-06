# IPD: the runner-owned orchestrator retirement transition

- Date: 2026-09-06
- Kind: child
- Concern: `finalize_orchestrator` (`oc_runipd.py:773-796`) has NEVER once succeeded. Measured across all 102 durable run records: `orchestrator-finalized` fired 0 times, `orchestrator-deferred` fired 28 times across 15 distinct orchestrators. It was born broken: the gated terminal transition landed `99760832` (2026-08-24) and `finalize_orchestrator` was written `801dd28a` (2026-08-27), three days later, against a gate that already refused it. Two gates block it and both are structural, not incidental. FIRST, it shells to `aw ipd set executed`, which requires a `begin` receipt; an orchestrator is never agent-executed so nothing ever calls `aw ipd begin` for it and no receipt can exist. SECOND, with a receipt present (verified by writing one, then deleting it) the `pre-transition` checkpoint refuses on six `IPD-S404` findings because `check_checkpoint` (`ipd_lint.py:694-725`) requires every `E-*` performed and every `V-*` evidenced UNCONDITIONALLY, and `grep -c orchestrator agent_workflows/ipd_lint.py` is 0 so the linter has no orchestrator concept at all. That is the contradiction: the honesty gate demands evidence for items that, under `aw run`, are by design performed by nobody.
- Scope: Make a runner-owned retirement transition that actually works, resolving spec `77tr3o` R-5 (the E/V pre-transition requirement) and R-6 (the receipt requirement) EXPLICITLY rather than by bypass, and writing an honest terminal history entry per R-4. Consumes child 01's predicate; it performs the transition and does NOT decide eligibility itself. It does NOT touch either runner's dispatch branch (child 03), does NOT relax any gate for CHILD plans, and adds NO path by which an ordinary plan can reach `executed` without evidence.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_lint.py, agent_workflows/runner_shared.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: executed:5942n7
- Status: to-review
- Readiness: go-pending-approval
- Set: orchretire
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ueg5cf
- From-Backlog: kxkc04
- From-Spec: 77tr3o

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored complete from approved spec 77tr3o. Both blocking gates reproduced verbatim at HEAD 844d195c before authoring; the probe receipt written to expose the second gate was deleted.
- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give the runner a terminal transition it can actually perform on an Order-0 orchestrator whose Set is
complete, which states truthfully that the plan was RETIRED as a rollup step rather than executed, and
which cannot be reused to sneak an ordinary plan past its evidence gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: resolve the two gates

- [ ] E-01 DECIDE and record which of spec R-5's two permitted shapes this Set implements, then state the reason in this plan's Workflow history before writing code. The two are: (a) teach `check_checkpoint` a `Kind: orchestrator` + runner-rollup exemption scoped to THIS transition; or (b) add a distinct runner-owned rollup transition that does not route through the E/V checkpoint while keeping every other gate. Weigh them on the criterion the spec sets: no new route by which a CHILD plan reaches `executed` without evidence. Record the rejected option and why.
  - Depends on: none
  - Expected outcome: a written decision in this plan naming the chosen shape and the reason, so a reviewer can judge the choice rather than infer it from the diff.
  - Execution state: pending

- [ ] E-02 Implement the chosen E/V resolution. If (a), the exemption MUST test `Kind: orchestrator` AND a runner-rollup caller signal, so a human running `aw ipd finalize` by hand on an orchestrator still faces the normal E/V requirement (the agent-driven path is unchanged, per spec Scope). If (b), the new transition MUST still perform: status legality, the plan move, the plans-index refresh, the path-scoped lifecycle commit, and post-transition lint. Whichever is chosen, add a comment at the site naming spec `77tr3o` R-5 and stating the honesty rule, because a future reader must not over-generalize the exemption.
  - Depends on: E-01
  - Expected outcome: retiring `rh5tt6` no longer produces the six `IPD-S404` findings, while a CHILD plan with unperformed E-items is still refused identically to today.
  - Execution state: pending

- [ ] E-03 Resolve the receipt requirement (spec R-6) explicitly: either the rollup transition does not require a `begin` receipt, or the runner mints one as part of the rollup. Do NOT silently reuse the child-plan receipt path, which is what fails today. If a receipt is minted, it must be recognizable as a rollup receipt rather than an execution receipt, so it cannot be mistaken for evidence that an agent executed the orchestrator.
  - Depends on: E-01
  - Expected outcome: the "no begin receipt for <id6>" refusal no longer blocks a legitimate rollup, and no receipt is left behind claiming an execution that did not happen.
  - Execution state: pending

### Task group 2: the honest record

- [ ] E-04 Write the terminal history entry per spec R-4: it MUST record that the orchestrator was RETIRED as a rollup step of a runner Set completion, name the run id, and name the children whose execution justified it. It MUST NOT claim the orchestrator's own `E-*`/`V-*` items were performed. Note the existing message string (`"Orchestrator rollup: all children of set X executed (aw oc run, no agent turn)"`) has never actually been written to a plan, so there is no precedent to preserve and the wording is free; it must satisfy the attribution lint, which means keeping the actor string parenthesis-free (`driver_actor`'s documented constraint at `oc_runipd.py:799-810`; today's `--actor "aw oc run (orchestrator rollup)"` contains parentheses and would misparse).
  - Depends on: E-02, E-03
  - Expected outcome: a retired orchestrator's history line names the rollup, the run, and the children, and passes the attribution lint.
  - Execution state: pending

- [ ] E-05 Extend `tests/test_orchestrator_retirement.py` (created by child 01) with transition-level tests: a complete Set retires and lands in `executed/` with the honest history line; a CHILD plan with unperformed E-items is still refused; a human `aw ipd finalize` on an orchestrator outside the rollup path still faces the E/V requirement; and the terminal entry passes the attribution lint. Include a test that the retirement refuses when child 01's predicate says ineligible, so the two halves cannot drift apart.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: tests that fail if the exemption widens to ordinary plans, which is the regression that matters most.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Run the suite BARE (`python3 -m pytest`); configured `addopts` already parallelize and quieten it.
- `finalize` CONSUMES the receipt on success (`ipd_lifecycle.py:2114`), which is why `nna8yz` has no receipt today: its agent finalized in-lane and consumed it. Any minted rollup receipt must not resurrect that confusion.
- The attribution lint parses `- <date> <status> (<actor>): <msg>` and misparses a parenthesized actor; `driver_actor` renders the model as `model=<model>` for exactly this reason.
- `aw set executed` delegates to the gated finalize but checks `worker_role_active` ZERO times (`status_set.py`), unlike `aw ipd finalize`. That is a separate defect (spec Section 4) and must not be "fixed" incidentally here, but do not build the rollup on top of it either.

## Findings

| # | Sev | Where | Finding | Evidence |
|---|-----|-------|---------|----------|
| F-1 | BLOCKER | all runs | The rollup has never worked. 0 `orchestrator-finalized` vs 28 `orchestrator-deferred` across 102 runs. | `grep -rh ... .aw/records/runs/*/events.jsonl \| wc -l` |
| F-2 | BLOCKER | `ipd_lint.py:694-725` | `pre-transition` requires every E performed and V evidenced unconditionally; the linter has no orchestrator concept (`grep -c orchestrator` = 0). | reproduced: six `IPD-S404` findings on `rh5tt6` with a receipt present |
| F-3 | BLOCKER | `oc_runipd.py:773-796` | The rollup requires a `begin` receipt that cannot exist for a plan that is never agent-executed. | reproduced: "no begin receipt for rh5tt6" |
| F-4 | MED | `oc_runipd.py:785` | The rollup actor string `"aw oc run (orchestrator rollup)"` contains parentheses, which the attribution lint's actor capture misparses. | `driver_actor` docstring at `:799-810` documents the constraint |
| F-5 | LOW | timeline | The gate (`99760832`, 2026-08-24) predates the rollup (`801dd28a`, 2026-08-27), so this was never a regression; it never worked. | `git merge-base --is-ancestor 801dd28a 99760832` false |

## Proposed changes (ordered, validatable)

1. E-01 record the R-5 shape decision with its reason.
2. E-02 implement the E/V resolution, scoped so the agent-driven path is unchanged.
3. E-03 implement the receipt resolution without reusing the child path.
4. E-04 write the honest, lint-passing terminal entry.
5. E-05 tests, including the exemption-must-not-widen case.

## Deferred / out of scope (with reason)

- Deciding eligibility: child 01 owns the predicate; this plan consumes it.
- Wiring dispatch and removing the terminal-status write: child 03.
- The `aw set executed` worker-role bypass reopening `i452hf`: spec Section 4, separately filed.
- Retiring the four stuck orchestrators: a consequence, not the mechanism.

## Scope check

- Over-scope: `ipd_lint.py` is in `Scope-Paths` but is touched ONLY if E-01 chooses shape (a). If (b) is chosen it must be left unmodified, and the finalize record must say so rather than leaving an unexplained in-scope-unmodified path.
- Under-scope: nothing here is reachable from a real run until child 03 wires the dispatch sites.

## Required tests / validation

`python3 -m pytest` bare. Baseline measured in the executing worktree at execution time and pasted; compare failing NODE IDS, not totals (a lane worktree legitimately reports lane-environment failures: 35 measured on `xdr83v`'s lane).

## Spec / documentation sync

Implements spec `77tr3o` R-4, R-5, R-6. If E-01 chooses shape (a), the `ipd-spec` documentation of the `pre-transition` checkpoint must record the orchestrator exemption, because a checkpoint that silently exempts a Kind is exactly the kind of undocumented special case this repo's own linter discipline exists to prevent.

## Open questions

### OQ-01: linter exemption (a) or a separate rollup transition (b)?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: DELIBERATELY LEFT to execution, per spec `77tr3o` OQ-1, which states both are defensible and the choice needs the code in front of the decider. It is NOT blocking because the spec supplies the binding constraint that makes either answer safe: no new route by which a child plan reaches `executed` without evidence. E-01 requires the decision and its reason to be RECORDED, so the reviewer judges a stated choice rather than reverse-engineering it. Escalate to the maintainer only if both shapes turn out to violate the constraint, which would mean the requirement itself needs revisiting.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: quote the decision paragraph added to this plan's Workflow history, naming the chosen shape, the rejected one, and the reason, and state explicitly how the choice satisfies "no new route by which a child plan reaches executed without evidence".
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a successful retirement of a synthetic complete Set showing NO `IPD-S404` findings, AND paste a CHILD plan with unperformed E-items still being refused with the same findings it produces today. Both are required: the first shows the gate opened where intended, the second shows it did not open anywhere else.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a retirement succeeding with no pre-existing `begin` receipt. If a rollup receipt is minted, paste it and show it is distinguishable from an execution receipt; if none is minted, show `.aw/state/ipd-lifecycle/` contains no new file for the retired id6.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the retired orchestrator's terminal history line, showing it names the rollup, the run id, and the justifying children, and does NOT claim its own E/V items were performed. Paste `aw ipd lint` output for the retired plan showing the attribution lint passes (this is where a parenthesized actor would fail).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the bare suite summary with the new tests passing. Then paste a SABOTAGE showing the exemption cannot widen: modify the exemption predicate to also accept `Kind: child` and show the "child still refused" test FAILS. A test that only passes proves nothing about the boundary it is supposed to defend.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Stay inside `Scope-Paths`; both runners' dispatch branches are OUT of bounds (child
03 owns them). You MUST NOT add any path by which an ordinary plan reaches `executed` without evidence,
and V-02/V-05 exist to prove you did not. Do not weaken the CHILD-plan gates, do not touch
`EXECUTION_SUCCESS_STATES` or `TERMINAL_STATES`, and do not incidentally "fix" the `aw set executed`
worker-role bypass. Record the E-01 decision BEFORE writing the code it governs. PASTE ACTUAL OUTPUT for
every `V-*`. If `ipd_lint.py` ends up unmodified because you chose shape (b), say so explicitly at
finalize with a `--scope-reason` rather than leaving an unexplained in-scope-unmodified path. OQ-01 is
deliberately open and is yours to decide and record; escalate only if both shapes violate the
no-new-route constraint.

POST-GATE LIFECYCLE. Do not claim done or move this plan until every `V-*` is verified with concrete
pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed
by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
