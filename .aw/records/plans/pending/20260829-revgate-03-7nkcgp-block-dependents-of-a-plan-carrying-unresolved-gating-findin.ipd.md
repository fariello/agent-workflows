# IPD: Block dependents of a plan carrying unresolved gating findings

- Date: 2026-08-29
- Kind: child
- Concern: A dependency is satisfied purely by the target reaching `executed/`, so a plan with unresolved High/Blocker findings still releases everything that depends on it.
- Scope: Extend dependency satisfaction so a target carrying unresolved gating findings does NOT satisfy an `executed:` edge, in both host drivers and in the shared `Item-Dependencies` evaluator. Reuses the existing `dependency-blocked` state and cascade rather than adding a new outcome.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/check_engine.py, tests/test_review_findings_cascade.py
- Item-Dependencies: executed:plqjt7
- Status: to-review
- Set: revgate
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 7nkcgp
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored on the maintainer's requirement that if an item fails, everything depending on it is blocked until resolved.

## Goal

Stop a plan with unresolved serious findings from silently authorizing its dependents. The maintainer's
rule is that if an item fails, everything that depends on it waits; today satisfaction is decided by file
location alone, so a plan can be `executed/` with a Blocker still open and its dependents proceed as if
all were well.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: teach dependency satisfaction about findings

- [ ] E-01 In `oc_runipd.dependency_status` (`oc_runipd.py:1479-1505`), a dependency currently counts as
      satisfied for an execute action when its plan bucket is `executed` (`:1499-1501`) or, for an
      in-queue item, when its status is in `EXECUTION_SUCCESS_STATES` (`:1486`, `:1490`). Add a further
      condition: the target must ALSO carry no unresolved gating findings, evaluated through `15zvu6`'s
      parser plus the shared `is_gating` predicate. A target that fails this joins the existing
      `unsatisfied` list, so the caller's existing behavior (mark `dependency-blocked`, record
      `unsatisfied_dependencies`, emit the `dependency-blocked` event at `:2621-2632`) applies unchanged.
  - Depends on: none
  - Expected outcome: a dependent of a plan with an unresolved gating finding is marked
    `dependency-blocked` and starts no session.
  - Execution state: pending

- [ ] E-02 Apply the mirror-image change in `agy_runipd.dependency_status` (`agy_runipd.py:1613`), which
      has the same shape and the same `SUCCESS_STATES`/`EXECUTION_SUCCESS_STATES` constants
      (`agy_runipd.py:60-61`). Both drivers must agree, or the gate is host-dependent and an agent could
      evade it by switching host. Extract the shared predicate to ONE function consumed by both rather
      than duplicating the logic in each driver.
  - Depends on: E-01
  - Expected outcome: both hosts refuse identically; the predicate exists in exactly one place.
  - Execution state: pending

- [ ] E-03 Extend the shared `Item-Dependencies` evaluator in `check_engine.py` so an `executed:<id6>`
      edge pointing at a plan with unresolved gating findings is reported, consistent with how the
      spec's satisfaction rule already demands more than status text for that edge kind (terminal
      structure plus deterministic evidence, not merely a file whose status says `executed`). Reuse the
      existing dependency finding vocabulary rather than adding a new rule id if one fits; add a new id
      only if none does, and say which in the evidence.
  - Depends on: E-01
  - Expected outcome: `aw check` reports a dependency on a findings-blocked plan, so the condition is
    visible outside a run.
  - Execution state: pending

### Task group 2: make the block legible and recoverable

- [ ] E-04 Ensure the `dependency-blocked` event and the run report name the ROOT CAUSE, i.e. the
      specific finding id and severity on the target, not merely "dependency not satisfied". A blocked
      dependent whose message does not say WHY is the failure mode this Set exists to remove; an
      operator must be able to go straight to the finding. Include the target id6 and the finding id in
      the event payload.
  - Depends on: E-01, E-02
  - Expected outcome: the event and report identify the blocking finding precisely.
  - Execution state: pending

- [ ] E-05 Write `tests/test_review_findings_cascade.py` proving: a dependent of a plan with an
      unresolved `high`/`open` finding is `dependency-blocked` and starts NO session; once the finding is
      resolved, the same dependent becomes runnable on a subsequent pass (recovery works, because
      `dependency-blocked` is already re-queued on resume at `oc_runipd.py:2590-2604`); a `medium`
      finding does not block at threshold `high` but does at `medium`; threshold `off` disables blocking
      entirely; a TRANSITIVE dependent (A -> B -> C) is also blocked, per the maintainer's rule that
      everything depending on a failed item waits; and INDEPENDENT queue items still proceed, so the
      block is item-local and does not stall the whole run. Assert both drivers behave identically.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: blocking, cascade, recovery, threshold, and non-interference are all covered.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The runner ALREADY has the mechanism: `dependency_status` returns `(satisfied, unsatisfied)`
  (`oc_runipd.py:1479-1505`), and the caller marks blocked items and emits an event
  (`:2611-2632`). This plan adds a condition to an existing predicate; it does not add a new state,
  outcome, or code path.
- Recovery is ALREADY handled: `dependency-blocked` is in the set of statuses re-queued on resume
  (`oc_runipd.py:2590-2604`), so "blocked until resolved" needs no new resume logic. This is the main
  reason to extend the existing predicate rather than invent a parallel gate.
- Satisfaction today is location-based for out-of-queue targets (`bucket != "executed"`, `:1500`) and
  status-based for in-queue ones (`EXECUTION_SUCCESS_STATES`, `:1486`). Both need the additional
  condition, or the gate would be evadable depending on whether the target is in the same run.
- `agy_runipd` mirrors `oc_runipd` (`dependency_status` at `agy_runipd.py:1613`, same constants at
  `:60-61`), and the repo has a live backlog item about the two drivers needing a shared library, so new
  logic should be written ONCE and consumed twice rather than duplicated.
- Spec `25kzda` already states that `executed` status text alone must not satisfy an `executed:` edge
  (terminal structure and deterministic evidence are also required), so this plan's stricter rule is
  consistent with the intended design rather than novel.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Dependency satisfaction is decided by location/status only, with no notion of quality. | `oc_runipd.py:1499-1501` (`bucket != "executed"`) and `:1486`/`:1490` (`EXECUTION_SUCCESS_STATES`) |
| F-2 | The blocked state, its event, and its cascade already exist. | `oc_runipd.py:2611-2632` marks `dependency-blocked`, records `unsatisfied_dependencies`, and emits the event |
| F-3 | Recovery already exists, so "until resolved" is free. | `oc_runipd.py:2590-2604` re-queues `dependency-blocked` on resume |
| F-4 | The second driver has the same seam and must not diverge. | `agy_runipd.py:1613` `dependency_status`; `agy_runipd.py:60-61` the same two state sets |
| F-5 | The intended design already demands more than status text for an `executed:` edge. | Spec `25kzda` satisfaction rules for `executed:<id6>` |
| F-6 | The concrete motivating case is live in this repo. | In run `run-20260829T191652Z-4134000`, orchestrator `bl9q3d` sits `dependency-blocked` awaiting `executed:` children, demonstrating the cascade machinery working on real data |

## Proposed changes (ordered, validatable)

1. Add the findings condition to `oc_runipd.dependency_status` (E-01).
2. Mirror it in `agy_runipd` via ONE shared predicate (E-02).
3. Report the condition in the shared evaluator so it is visible outside a run (E-03).
4. Name the root-cause finding in the event and report (E-04).
5. Prove blocking, transitive cascade, recovery, thresholds, and non-interference (E-05).

## Deferred / out of scope (with reason)

- **Unifying the two drivers onto a shared runner library.** Out of scope: that is its own tracked
  concern. This plan extracts only the ONE new predicate to a shared location (E-02) and does not
  refactor the surrounding duplication.
- **Blocking on unresolved DECISIONS as well as findings.** Out of scope: `c621h9` keeps decisions
  report-only by design, and stacking a decision-based block here would contradict that.
- **Changing what satisfies `exists:` or `state:` edges.** Out of scope: only `executed:` asserts that
  work was completed and verified, so only it should require findings to be clean. Widening this to
  `exists:` would break the deliberate semantics that an `exists:` edge is a structural check.
- **Retroactively blocking already-executed dependents.** Out of scope: this gate applies at dispatch,
  and re-litigating completed work would be a migration, not a gate.

## Scope check

- Over-scope: none. One predicate, mirrored, plus reporting and tests.
- Under-scope: acknowledged. This blocks dependents of a plan whose findings were RECORDED. A target
  whose reviewer never recorded the finding is invisible here, exactly as in `plqjt7`; the honest claim
  is "recorded unresolved findings now block dependents", not "unsound work cannot release dependents".

## Required tests / validation

1. `python3 -m pytest tests/test_review_findings_cascade.py` green, run BARE (`addopts` already supplies
   `-q -n auto --dist=worksteal -m 'not slow'`; do not pass `-n0`, a second `-q`, or `-p no:randomly`).
2. Full default suite green with counts pasted, compared against the baseline at execution time.
3. A worked transitive case (A -> B -> C) demonstrated, showing C blocked by a finding on A.
4. Non-interference demonstrated: an independent queue item still executes while a blocked chain waits.

## Spec / documentation sync

- Spec `25kzda`'s dependency-satisfaction table gains a condition. That spec is `to-review` and MUST NOT
  be edited by this plan; note the required amendment in the execution evidence so it is reconciled when
  the spec is next reviewed.
- `.aw/records/reviews/README.md` (from `15zvu6`) should state that unresolved gating findings block
  dependents, since that is a consequence a reader of the reviews tree needs to know.

## Open questions

### OQ-01: Should a blocked dependent be `dependency-blocked` or a distinct new status?

- Blocking: no
- Status: resolved
- Owner: resolved from repository evidence during authoring
- Resolution or deferral rationale: RESOLVED - reuse `dependency-blocked`. It already carries the exact
  semantics (prerequisite not satisfied, no session started), it is already re-queued on resume
  (`oc_runipd.py:2590-2604`) so recovery is free, and it is already rendered in the runs viewer. A new
  status would need its own recovery path, its own viewer handling, and its own tests, for no semantic
  gain. E-04 supplies the missing specificity (which finding) inside the existing status rather than by
  adding one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a run (or a direct `dependency_status` call) on a fixture where the target
    plan is in `executed/` but carries a `high`/`open` finding, showing the dependent is NOT satisfied and
    is marked `dependency-blocked`, and paste proof NO session started for it. Then paste the same fixture
    with the finding resolved, showing satisfaction.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the identical fixture result for BOTH drivers, showing the same decision, and
    paste `grep -n` proving the predicate is defined once and imported by both rather than duplicated.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw check` reporting the `executed:` edge that points at a findings-blocked
    plan, and paste a clean run once resolved. State explicitly whether an existing rule id was reused or
    a new one added, and why.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `dependency-blocked` event payload showing the target id6, the finding
    id, and the severity, plus the run-report line an operator would read. A message that says only
    "dependency not satisfied" fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the test result with counts, and paste each case individually so none is
    vacuous: direct block; TRANSITIVE block (A -> B -> C with the finding on A); recovery after
    resolution on a resume pass; `medium` ignored at `high` and caught at `medium`; `off` disabling;
    and an INDEPENDENT item still executing during the block. Also paste an adversarial run proving the
    gate cannot be evaded by whether the target is in-queue versus out-of-queue (both code paths from
    E-01 exercised).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

CAUTION ON TIMING: this plan modifies `oc_runipd.py` and `agy_runipd.py`, which the wtiso Set is
concurrently rewriting across several phases. Do NOT execute it while a wtiso phase touching those files
is in flight; confirm the runner surface is quiet first, or expect an unmergeable conflict. This is a
sequencing constraint, not a dependency, so it is stated here rather than as an `Item-Dependencies` edge.

RESOLVE-BEFORE-REFUSING (maintainer instruction, 2026-08-29): if you hit an obstacle while executing
this plan, you MUST first do the work of finding a strong recommended path from repository evidence.
Reporting "cannot proceed" is a LAST resort, acceptable only when you can state (a) what you tried,
(b) the specific evidence that blocks each candidate approach, and (c) a concrete recommended option
with trade-offs for the maintainer to choose. Any question you resolve yourself while executing MUST be
recorded as a decision (see `c621h9`), so a wrong turn stays auditable.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE in
this checkout; verify the staged set before every commit with `git diff --cached --name-only` and never
stage, revert, or discard another party's work. Run the suite BARE. When every `V-*` item carries pasted
evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`.
