# IPD: Block dependents of a plan carrying unresolved gating findings

- Date: 2026-08-29
- Kind: child
- Concern: A dependency is satisfied purely by the target reaching `executed/`, so a plan with unresolved High/Blocker findings still releases everything that depends on it.
- Scope: Extend dependency satisfaction so a target carrying unresolved gating findings does NOT satisfy an `executed:` edge, in both host drivers and in the shared `Item-Dependencies` evaluator. Reuses the existing `dependency-blocked` state and cascade rather than adding a new outcome.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/check_engine.py, agent_workflows/review_findings.py, agent_workflows/ipd_set_plan.py, tests/test_review_findings_cascade.py
- Item-Dependencies: executed:plqjt7
- Status: approved
- Set: revgate
- Order: 3
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 7nkcgp
- Approval: 2026-08-30, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-30 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-011 fixed in place

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored on the maintainer's requirement that if an item fails, everything depending on it is blocked until resolved.
- 2026-08-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; F-7..F-11 added and fixed in place. Every line citation was STALE by 40-90 lines and was re-derived (F-7). F-3's "recovery is free on resume" was FALSE (re-queue needs --retry-incomplete; the loop is all-or-nothing and can end a run), which invalidated OQ-01's premise (F-10, E-08 added). A THIRD authority surface (ipd_set_plan's /exec-set cascade) was missed entirely (F-9, E-07 + E-06 added). F-6 mischaracterized its own evidence: the cited run has ZERO dependency-blocked events and was an orchestrator-deferred case. E-03's "reuse an existing rule id" was rejected on evidence (F-8). E-02's shared-predicate home would have created the first runner-to-runner import, colliding with the in-flight rununify Set (F-11).

## Goal

Stop a plan with unresolved serious findings from silently authorizing its dependents. The maintainer's
rule is that if an item fails, everything that depends on it waits; today satisfaction is decided by file
location alone, so a plan can be `executed/` with a Blocker still open and its dependents proceed as if
all were well.

The gate must hold on EVERY surface that grants execution authority, not just the one the author looked
at. Review found three such surfaces (both host runners plus the `/exec-set` Set compiler); a gate that
covers two of three is a gate with a bypass, so E-06 and E-07 exist to close or explicitly name the
third.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: teach dependency satisfaction about findings

- [x] E-01 In `oc_runipd.dependency_status` (REAL LOCATION `oc_runipd.py:1526-1552`; every line citation
      in the draft was stale by 40-90 lines and was corrected at review, F-7), a dependency currently
      counts as satisfied for an execute action when its plan bucket is `executed` (`:1545-1547`) or, for
      an in-queue item, when its status is in `EXECUTION_SUCCESS_STATES` (`:1533`, `:1536-1537`). Add a
      further condition: the target must ALSO carry no unresolved gating findings, evaluated through
      `15zvu6`'s parser plus the shared `is_gating` predicate. A target that fails this joins the existing
      `unsatisfied` list, so the caller's existing behavior (mark `dependency-blocked`, record
      `unsatisfied_dependencies`, emit the `dependency-blocked` event at `:2677-2690`) applies unchanged.
      BEFORE EDITING, RE-DERIVE EVERY LINE NUMBER: `oc_runipd.py`/`agy_runipd.py` are being actively
      rewritten by the wtiso AND rununify Sets, so the citations above will drift again. Locate the
      symbols by name (`grep -n "def dependency_status"`), never by the line numbers written here.
  - Depends on: none
  - Expected outcome: a dependent of a plan with an unresolved gating finding is marked
    `dependency-blocked` and starts no session.
  - Execution state: performed

- [x] E-02 Apply the mirror-image change in `agy_runipd.dependency_status` (REAL LOCATION
      `agy_runipd.py:1610-1636`), which has the same shape and the same
      `SUCCESS_STATES`/`EXECUTION_SUCCESS_STATES` constants (REAL LOCATION `agy_runipd.py:62-63`). Both
      drivers must agree, or the gate is host-dependent and an agent could evade it by switching host.
      Extract the shared predicate to ONE function consumed by both rather than duplicating the logic in
      each driver.
      PUT THE SHARED PREDICATE IN `review_findings.py` (the `15zvu6` module that already owns findings
      parsing), NOT in one runner imported by the other. Verified constraint: neither runner imports the
      other and neither imports any shared runner library today, which is the exact defect the
      `rununify` Set exists to fix (F-11). Importing `agy_runipd` from `oc_runipd` would create the
      first such coupling and would collide with that Set's extraction. `review_findings.py` is added to
      `Scope-Paths` for this reason. If you conclude a different home is better, say which and why, and
      do NOT introduce a runner-to-runner import.
  - Depends on: E-01
  - Expected outcome: both hosts refuse identically; the predicate exists in exactly one place, and that
    place is not one runner importing the other.
  - Execution state: performed

- [x] E-03 Extend the shared `Item-Dependencies` evaluator in `check_engine.py` so an `executed:<id6>`
      edge pointing at a plan with unresolved gating findings is reported, consistent with the spec's
      satisfaction rule (spec `25kzda` Section 2.9 line 292 is EXPLICIT and even stronger than the draft
      claimed: an `executed:` edge is satisfied only when the target "is in `executed/` with status
      `executed`, passes terminal lint, and has valid deterministic execution/finalization evidence",
      and line 255 says it "requires verified terminal execution, not merely a file whose status text
      says `executed`").
      NAME THE WIRING POINT AND THE RULE ID DECISION CONCRETELY (F-8). The evaluator is
      `evaluate_ipd_dependencies` (`check_engine.py:1750`), whose per-edge resolution runs through
      `_resolve_edge` (`:1724-1742`) and today returns only `ok`/`dangling`/`ambiguous` - three verdicts
      that are all about IDENTITY resolution, not about target QUALITY. The draft said to "reuse the
      existing dependency finding vocabulary if one fits": verified that NONE fits. `dangling` means no
      artifact has that id6 and `ambiguous` means several do; reporting a findings-blocked target as
      either would be a FALSE statement about identity and would corrupt both rules' meaning. So ADD a
      new rule id (`check.ipd-dependency-findings-blocked` or similar), register it in `RULE_REGISTRY`
      (`:85-171`), and state in the evidence that reuse was evaluated and rejected for this reason.
      Keep the `phase` severity split the evaluator already implements (`:1820`, `_DEP_BLOCKING_PHASES`).
  - Depends on: E-01
  - Expected outcome: `aw check` reports a dependency on a findings-blocked plan under a rule id whose
    meaning is accurate, so the condition is visible outside a run without overloading `dangling`.
  - Execution state: performed

- [x] E-07 CLOSE THE THIRD GATE SURFACE THE DRAFT DID NOT KNOW ABOUT, or explicitly and honestly scope
      it out (F-9). The plan asserts the runner is where dependency satisfaction is decided, but
      `ipd_set_plan.py` independently computes its own blocking for the `aw ipd execute-set` /
      `/exec-set` path: `RUNNABLE_STATUSES` (`ipd_set_plan.py:49`) plus `_propagate_blocked`
      (`:227-238`) derive `deferred_gates`/`blocked_children` (`:102-103`, `:384`, `:405`) with the
      documented semantics "a child is blocked iff it is a deferred_gate OR any of its (transitive)
      dependencies is blocked". That is the SAME transitive-cascade rule this plan wants, computed in a
      DIFFERENT module from a DIFFERENT input (child status, not review findings). Leaving it untouched
      means `/exec-set` - the documented autonomous entry point - keeps releasing dependents of a
      findings-blocked plan, so the gate would be evadable by choosing the Set path over the queue path,
      which is the same class of hole E-02 exists to prevent across hosts.
      DECIDE AND RECORD ONE: (a) extend the Set compiler so a findings-blocked child is treated as a
      gate and its transitive descendants join `blocked_children`, reusing `_propagate_blocked` rather
      than writing a second cascade; or (b) scope it out EXPLICITLY in the Deferred section, naming
      `/exec-set` as a known uncovered path and saying so in the plan's Scope check, so the coverage
      claim stays honest. Option (a) is recommended because `_propagate_blocked` already implements the
      cascade and the maintainer's stated rule is that everything depending on a failed item waits.
      If you choose (a), add `agent_workflows/ipd_set_plan.py` to `Scope-Paths` first.
  - Depends on: E-01
  - Expected outcome: the `/exec-set` path either honors the gate or is documented as not honoring it;
    no silent third path.
  - Execution state: performed

- [x] E-08 FIX THE RECOVERY CLAIM, which is FALSE as written and load-bearing for OQ-01 (F-10). The plan
      states `dependency-blocked` is "already re-queued on resume", and OQ-01 rests on recovery being
      free. Verified: re-queueing happens ONLY under `if retry_incomplete:` (`oc_runipd.py:2648`,
      `agy_runipd.py:2700`), and `retry_incomplete` is False for a plain `start` (`:3109`) and comes
      from the explicit `--retry-incomplete` flag on `resume` (`:3025-3029`, `:3148`). A bare
      `aw oc resume` therefore does NOT re-queue a `dependency-blocked` item; it stays blocked.
      Worse, the selection loop is ALL-OR-NOTHING: when no queued item is satisfiable, it marks EVERY
      remaining queued item `dependency-blocked` and BREAKS out of the run
      (`oc_runipd.py:2666-2691`, `agy_runipd.py:2718-2743`). So "blocked until resolved" costs the
      operator an explicit flag, and a findings-block can end a run.
      Do BOTH: (1) correct the claim wherever it appears (conventions, F-3, OQ-01) so no reader
      inherits the error; and (2) make the operator-facing message state the exact recovery command
      (`aw oc resume --retry-incomplete`, host-appropriate), since a block whose exit is undocumented is
      the usability failure this plan says it is removing. Do NOT change the re-queue default in this
      plan: that is a runner-behavior change outside this Set's scope, and the two runners are being
      rewritten concurrently. If you believe the default is wrong, raise it as a separate item.
  - Depends on: E-01, E-04
  - Expected outcome: the plan no longer claims free recovery, and a blocked operator is told the exact
    command that unblocks the run.
  - Execution state: performed

### Task group 2: make the block legible and recoverable

- [x] E-04 Ensure the `dependency-blocked` event and the run report name the ROOT CAUSE, i.e. the
      specific finding id and severity on the target, not merely "dependency not satisfied". A blocked
      dependent whose message does not say WHY is the failure mode this Set exists to remove; an
      operator must be able to go straight to the finding. Include the target id6 and the finding id in
      the event payload.
      NOTE THE SHAPE CONSTRAINT: the event payload's `dependencies` field is a flat `list[str]` of id6s
      (`oc_runipd.py:2683-2689`) and `unsatisfied_dependencies` on the queue item is the same flat list,
      consumed by the report table (`:1477-1489`) and by `print_status`. Adding structure means either a
      NEW payload key (additive, safest) or changing that list's element type, which would touch every
      reader. Prefer the additive key; if you change the list's shape, enumerate every reader you
      checked. Also carry the reason through to the report row an operator actually reads, not only into
      `events.jsonl`.
  - Depends on: E-01, E-02
  - Expected outcome: the event and report identify the blocking finding precisely, without breaking any
    existing consumer of the flat dependency list.
  - Execution state: performed

- [x] E-05 Write `tests/test_review_findings_cascade.py` proving: a dependent of a plan with an
      unresolved `high`/`open` finding is `dependency-blocked` and starts NO session; once the finding is
      resolved, the same dependent becomes runnable on a subsequent pass; a `medium` finding does not
      block at threshold `high` but does at `medium`; threshold `off` disables blocking entirely; a
      TRANSITIVE dependent (A -> B -> C) is also blocked, per the maintainer's rule that everything
      depending on a failed item waits. Assert both drivers behave identically.
      THE RECOVERY CASE MUST PASS `--retry-incomplete`, not a bare resume: per F-10 a bare resume does
      NOT re-queue a `dependency-blocked` item. A recovery test written against a bare resume would
      either fail or (worse) pass vacuously and enshrine the false claim.
      DO NOT ASSERT "INDEPENDENT QUEUE ITEMS STILL PROCEED" AS WRITTEN: that claim is FALSE for the
      current runner (F-10). When no queued item is satisfiable the loop marks EVERY queued item blocked
      and breaks; and when one IS satisfiable the loop runs it, so independent progress depends on
      ordering, not on the block being item-local. Assert the TRUE property instead: an independent item
      that is satisfiable is still selected and run while a blocked chain waits, and state explicitly in
      the evidence that the all-or-nothing terminal case is pre-existing runner behavior this plan does
      NOT change.
      Build isolated fixture runs in tmp dirs; do not assert against this repository's live
      `.aw/records/runs/` state (the `i79rgh` defect class).
  - Depends on: E-01, E-02, E-03, E-04, E-07, E-08
  - Expected outcome: blocking, cascade, recovery (with the real flag), and thresholds are covered by
    assertions that are true of the actual runner.
  - Execution state: performed

- [x] E-06 PROVE THE GATE CANNOT BE EVADED BY PATH, which is the whole point of mirroring it. Add an
      explicit cross-surface test asserting the SAME fixture (target plan with an unresolved `high`
      finding) is refused by every surface that grants execution authority: `oc_runipd.dependency_status`,
      `agy_runipd.dependency_status`, `check_engine`'s evaluator (E-03), and - per whichever branch E-07
      took - either the Set compiler's `blocked_children` or an explicit documented XFAIL/skip naming
      `/exec-set` as a known uncovered path. A gate proven on three of four surfaces is a gate with a
      documented bypass; either close it or name it, and let the test record which.
  - Depends on: E-01, E-02, E-03, E-07
  - Expected outcome: every authority surface is enumerated in one test, and any uncovered surface is
    explicit in the test rather than implicit in the plan's silence.
  - Execution state: performed

## Project conventions discovered (Step 0)

ALL LINE CITATIONS BELOW WERE RE-DERIVED AT REVIEW (the draft's were stale by 40-90 lines, F-7). They
will drift again: `oc_runipd.py`/`agy_runipd.py` are under concurrent rewrite by the wtiso and rununify
Sets. Locate every symbol by NAME at execution time.

- The runner ALREADY has the mechanism: `dependency_status` returns `(satisfied, unsatisfied)`
  (`oc_runipd.py:1526-1552`), and the caller marks blocked items and emits an event (`:2677-2690`).
  This plan adds a condition to an existing predicate; it does not add a new state, outcome, or code
  path.
- Recovery is NOT free, contrary to the draft (F-10, corrected at review). `dependency-blocked` is
  re-queued ONLY under `if retry_incomplete:` (`oc_runipd.py:2648`, `agy_runipd.py:2700`), which is
  False for `start` (`:3109`) and requires the explicit `--retry-incomplete` flag on `resume`
  (`:3025-3029`, `:3148`). A bare resume leaves the item blocked. Extending the existing predicate is
  still the right call, but the reason is state/event/viewer reuse, NOT free recovery.
- The selection loop is ALL-OR-NOTHING at the terminal step: when no queued item is satisfiable it marks
  EVERY remaining queued item `dependency-blocked` and BREAKS out of the run
  (`oc_runipd.py:2666-2691`, `agy_runipd.py:2718-2743`). A findings-block can therefore end a run rather
  than merely park one item. Pre-existing behavior; this plan does not change it but must not claim
  otherwise.
- Satisfaction today is location-based for out-of-queue targets (`bucket != "executed"`, `:1546`) and
  status-based for in-queue ones (`EXECUTION_SUCCESS_STATES`, `:1533`). Both need the additional
  condition, or the gate would be evadable depending on whether the target is in the same run.
- `agy_runipd` mirrors `oc_runipd` (`dependency_status` at `agy_runipd.py:1610`, same constants at
  `:62-63`). Verified: NEITHER runner imports the other and neither imports a shared runner library, and
  roughly 93 percent of each is duplicated logic (plan `5e4sb6`, backlog `dhuape`). So the shared
  predicate must land in a NON-runner module (E-02 nominates `review_findings.py`); a runner-to-runner
  import would be a new coupling that collides with the `rununify` extraction.
- A THIRD surface decides blocking, which the draft missed (F-9): `ipd_set_plan.py` computes
  `deferred_gates`/`blocked_children` via `_propagate_blocked` (`:227-238`, `:384`, `:405`) for the
  `aw ipd execute-set` / `/exec-set` path, with the same transitive-cascade semantics from a different
  input. E-07 owns closing or explicitly scoping out that path.
- `_resolve_edge` (`check_engine.py:1724-1742`) returns only `ok`/`dangling`/`ambiguous`, all IDENTITY
  verdicts. There is no existing rule id whose meaning covers "target resolved fine but carries
  unresolved findings", so E-03 adds one rather than overloading `dangling`.
- Spec `25kzda` supports this plan MORE strongly than the draft claimed: Section 2.9 (line 292) requires
  an `executed:` edge's target to pass terminal lint AND carry valid deterministic execution evidence,
  and line 255 says it "requires verified terminal execution, not merely a file whose status text says
  `executed`". This plan's stricter rule is the spec's intent, not a novel restriction.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Dependency satisfaction is decided by location/status only, with no notion of quality. CONFIRMED at review; citations corrected. | `oc_runipd.py:1545-1547` (`bucket != "executed"`) and `:1533`/`:1536-1537` (`EXECUTION_SUCCESS_STATES`) |
| F-2 | The blocked state, its event, and its cascade already exist. CONFIRMED; citation corrected. | `oc_runipd.py:2677-2690` marks `dependency-blocked`, records `unsatisfied_dependencies`, and emits the event |
| F-3 | CORRECTED AT REVIEW - THE DRAFT'S CLAIM WAS FALSE. Recovery is NOT free and NOT automatic on resume. Re-queueing is gated on `if retry_incomplete:`, which is False for `start` and requires the explicit `--retry-incomplete` flag on `resume`. A bare `aw oc resume` leaves a `dependency-blocked` item blocked. Additionally the selection loop is ALL-OR-NOTHING: with nothing satisfiable it marks every queued item blocked and BREAKS, so a findings-block can END a run. This invalidated the draft's stated main reason for reusing the predicate (reuse is still right, for state/event/viewer reasons) and invalidated OQ-01's "recovery is free" premise. E-08 added to correct the claim and document the real recovery command. | `oc_runipd.py:2648` + `agy_runipd.py:2700` (the `retry_incomplete` guard); `:3109` (`start` passes False); `:3025-3029`, `:3148` (the flag on `resume`); `oc_runipd.py:2666-2691` + `agy_runipd.py:2718-2743` (all-or-nothing + break) |
| F-4 | The second driver has the same seam and must not diverge. CONFIRMED; citations corrected. | `agy_runipd.py:1610` `dependency_status`; `agy_runipd.py:62-63` the same two state sets |
| F-5 | The intended design already demands more than status text for an `executed:` edge. CONFIRMED and STRONGER than the draft stated. | Spec `25kzda` line 292: target must be "in `executed/` with status `executed`, passes terminal lint, and has valid deterministic execution/finalization evidence"; line 255: "requires verified terminal execution, not merely a file whose status text says `executed`" |
| F-6 | MISCHARACTERIZED IN THE DRAFT, corrected at review. The cited run does NOT demonstrate `dependency_status`'s cascade: it contains ZERO `dependency-blocked` events. `bl9q3d` is an ORCHESTRATOR blocked by the separate `_set_children_all_executed` branch, which emitted `orchestrator-deferred` because its children are `substantially-complete`, not `executed`. The run is still useful evidence, but for a DIFFERENT proposition: it shows the orchestrator gate working, not the predicate this plan modifies. Do not cite it as proof of the dependency cascade. | measured in `.aw/records/runs/run-20260829T191652Z-4134000/`: event counts contain `orchestrator-deferred` x1 and `dependency-blocked` x0; `state.json` shows `bl9q3d` `dependency-blocked`/`orchestrate` with 7 unfinished children, 6 of them `substantially-complete`; the emitting branch is `oc_runipd.py:2716-2732` |
| F-7 | ADDED AT REVIEW (HIGH): EVERY line citation in the draft was STALE, by 40-90 lines (`dependency_status` cited at `:1479` is actually at `:1526`; the event block cited at `:2621-2632` is at `:2677-2690`; the constants cited at `:60-61` are at `:62-63`; `:1613` is `:1610`). An executor following them would edit unrelated code (`:1479` lands in report-table string building). All corrected, plus a standing instruction to locate symbols by name because these two files are under concurrent rewrite. | `grep -n "def dependency_status"` -> `oc_runipd.py:1526`, `agy_runipd.py:1610`; `grep -n EXECUTION_SUCCESS_STATES` -> `:99`/`:63`; `sed -n '1470,1490p' oc_runipd.py` shows report-table code at the cited location |
| F-8 | ADDED AT REVIEW (MED): E-03 told the executor to "reuse the existing dependency finding vocabulary if one fits", but verified NONE fits. `_resolve_edge` returns only `ok`/`dangling`/`ambiguous`, all IDENTITY verdicts; reporting a findings-blocked target as `dangling` (no artifact has that id6) or `ambiguous` (several do) would be a false statement and corrupt both rules. E-03 now requires a NEW registered rule id and requires recording that reuse was evaluated and rejected. | `check_engine.py:1724-1742` (`_resolve_edge`, three verdicts); `:85-171` (`RULE_REGISTRY`); the existing `check.ipd-dependency-*` family at `:121-141` |
| F-9 | ADDED AT REVIEW (HIGH): a THIRD authority surface computes dependency blocking and the draft did not mention it, so the gate would be evadable by choosing the Set path. `ipd_set_plan.py` derives `deferred_gates`/`blocked_children` through `_propagate_blocked` for `aw ipd execute-set` / `/exec-set` (the documented autonomous entry point), with the SAME transitive-cascade rule from a different input. Added E-07 requiring the executor to either extend it (reusing `_propagate_blocked`, not writing a second cascade) or scope it out explicitly; added E-06 requiring a cross-surface evasion test. | `ipd_set_plan.py:49` (`RUNNABLE_STATUSES`), `:102-103` (`deferred_gates`/`blocked_children`), `:227-238` (`_propagate_blocked`, "blocked iff ... any of its transitive dependencies is blocked"), `:384`, `:405`, `:659-662`; `.aw/system/workflows/exec-set/exec-set.md:15-19` (the entry point) |
| F-10 | ADDED AT REVIEW (HIGH): see F-3. The false recovery claim appeared in three places (conventions, F-3, OQ-01) and would have produced a recovery TEST written against a bare resume, which would fail or pass vacuously. E-05 now mandates `--retry-incomplete` in the recovery case and forbids the draft's false "independent items still proceed" assertion. | same evidence as F-3 |
| F-11 | ADDED AT REVIEW (MED): E-02 said to extract the shared predicate to "ONE function consumed by both" without saying where, and the obvious reading (one runner imports the other) would create the first runner-to-runner coupling in the codebase and collide with the in-flight `rununify` extraction. E-02 now nominates `review_findings.py` and forbids a runner-to-runner import; `Scope-Paths` updated. | verified neither runner imports the other nor any shared runner library; plan `5e4sb6` measures ~93 percent duplication across 72 shared symbols and is `reviewed` and in flight; backlog `dhuape` is `graduated` |

## Proposed changes (ordered, validatable)

1. Add the findings condition to `oc_runipd.dependency_status` (E-01).
2. Mirror it in `agy_runipd` via ONE shared predicate housed in a NON-runner module (E-02).
3. Report the condition in the shared evaluator under a new, accurately-named rule id (E-03).
4. Close or explicitly scope out the third surface, the `/exec-set` Set compiler (E-07).
5. Name the root-cause finding in the event and report, additively (E-04).
6. Correct the false recovery claim and document the real recovery command (E-08).
7. Prove blocking, transitive cascade, recovery with the real flag, and thresholds (E-05).
8. Prove the gate cannot be evaded by choosing a different surface (E-06).

## Deferred / out of scope (with reason)

- **Unifying the two drivers onto a shared runner library.** Out of scope: that is its own tracked
  concern, now an active Set (`rununify`, orchestrator `5e4sb6`, `reviewed`, from backlog `dhuape`).
  This plan extracts only the ONE new predicate to a shared NON-runner location (E-02) and does not
  refactor the surrounding duplication, nor introduce a runner-to-runner import that would collide with
  that Set's extraction.
- **Changing the runner's re-queue default or its all-or-nothing terminal step.** Deliberately out of
  scope (F-3/F-10). Both are pre-existing behaviors this plan must document honestly but must not
  change: altering them is a runner-behavior change while two Sets are concurrently rewriting these
  files. E-08 corrects the plan's claims and surfaces the recovery command instead.
- **Blocking on unresolved DECISIONS as well as findings.** Out of scope: `c621h9` keeps decisions
  report-only by design, and stacking a decision-based block here would contradict that.
- **Changing what satisfies `exists:` or `state:` edges.** Out of scope: only `executed:` asserts that
  work was completed and verified, so only it should require findings to be clean. Widening this to
  `exists:` would break the deliberate semantics that an `exists:` edge is a structural check.
- **Retroactively blocking already-executed dependents.** Out of scope: this gate applies at dispatch,
  and re-litigating completed work would be a migration, not a gate.

## Scope check

- Over-scope: none. One predicate, mirrored, plus reporting and tests. E-07 may add the Set compiler,
  which is not scope creep but the third instance of the SAME gate; shipping two of three would be a
  gate with an undocumented bypass.
- Under-scope: acknowledged, and wider than the draft admitted:
  1. This blocks dependents of a plan whose findings were RECORDED. A target whose reviewer never
     recorded the finding is invisible here, exactly as in `plqjt7`; the honest claim is "recorded
     unresolved findings now block dependents", not "unsound work cannot release dependents".
  2. Per `plqjt7`'s E-07(a) an ABSENT review artifact is silent by design, and zero `.review.md` files
     exist today, so on landing this gate blocks nothing until reviewers start emitting artifacts.
  3. If E-07 takes branch (b), `/exec-set` remains an uncovered path and MUST be named here as such.
  4. Recovery costs an explicit `--retry-incomplete`, and a findings-block can end a run outright
     (F-3/F-10). "Blocked until resolved" is accurate; "resumes automatically" is not.

## Required tests / validation

1. `python3 -m pytest tests/test_review_findings_cascade.py` green, run BARE (`addopts` already supplies
   `-q -n auto --dist=worksteal -m 'not slow'`; do not pass `-n0`, a second `-q`, or `-p no:randomly`).
2. Full default suite green with counts pasted, compared against the baseline at execution time. Include
   BOTH runner suites explicitly and name their counts: the agy suite is far thinner than the opencode
   one (measured in plan `5e4sb6`: 95 oc tests vs 21 agy), so "both suites pass" is weak evidence for an
   agy-side change. State which assertions specifically cover the agy path.
3. A worked transitive case (A -> B -> C) demonstrated, showing C blocked by a finding on A.
4. Recovery demonstrated with the ACTUAL command (`resume --retry-incomplete`), and the report/event
   message shown to name it, per E-08.
5. Cross-surface non-evasion demonstrated per E-06: every authority surface refuses the same fixture, or
   the uncovered one is explicitly named.
6. NO-REGRESSION on the live corpus: `aw check plans` finding counts before and after must be equal
   (no `.review.md` exists in this repo, so the correct delta is zero).

## Spec / documentation sync

- Spec `25kzda`'s dependency-satisfaction table (Section 2.9, line 292) gains a condition, and its rule
  table (Section 2.10, lines 302+) gains the new rule id from E-03. Verified the spec is `to-review`
  (`aw find specs 25kzda`) and it is NOT in `Scope-Paths`, so this plan MUST NOT edit it; record the
  required amendment in the execution evidence so it is reconciled when the spec is next reviewed.
  Note the amendment is a CLARIFICATION, not a reversal: line 292 already requires terminal lint plus
  deterministic evidence, so findings-cleanliness extends an existing requirement.
- `.aw/records/reviews/README.md` (from `15zvu6`) should state that unresolved gating findings block
  dependents, since that is a consequence a reader of the reviews tree needs to know. It is NOT in this
  plan's `Scope-Paths` (it belongs to `15zvu6`/`plqjt7`); either add it there or record the needed line
  in the execution evidence. Do not silently skip it.
- If E-07 takes branch (a), `.aw/system/workflows/exec-set/exec-set.md` describes a Set-execution
  contract that would gain a new blocking reason. Assess whether its prose needs a line and say so
  either way rather than leaving it unexamined.

## Open questions

### OQ-01: Should a blocked dependent be `dependency-blocked` or a distinct new status?

- Blocking: no
- Status: resolved
- Owner: resolved from repository evidence during authoring
- Resolution or deferral rationale: RESOLVED - reuse `dependency-blocked`. PREMISE CORRECTED AT REVIEW
  (F-3/F-10): the draft's stated reason, that it "is already re-queued on resume so recovery is free",
  is FALSE. Re-queueing happens only under `--retry-incomplete` (`oc_runipd.py:2648`, `:3025-3029`,
  `:3148`); a bare resume leaves the item blocked. The CONCLUSION nevertheless holds on the surviving
  reasons, which are the real ones: the status already means exactly "prerequisite not satisfied, no
  session started"; it is already in `TERMINAL_STATES` handling (`:1994`) and in the retry set
  (`:2648-2661`) so the recovery PATH exists even though it needs a flag; and it is already rendered by
  the runs viewer and the status/report surfaces. A new status would need its own viewer handling,
  its own retry-set membership, and its own tests for no semantic gain, and would fragment the operator's
  mental model. E-04 supplies the missing specificity (which finding) inside the existing status; E-08
  documents the recovery command rather than pretending recovery is automatic.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a run (or a direct `dependency_status` call) on a fixture where the target
    plan is in `executed/` but carries a `high`/`open` finding, showing the dependent is NOT satisfied and
    is marked `dependency-blocked`, and paste proof NO session started for it. Then paste the same fixture
    with the finding resolved, showing satisfaction. Paste the `grep -n "def dependency_status"` output
    you used to locate the function, proving you re-derived the location instead of trusting this plan's
    line numbers (F-7).
  - Observed evidence: LOCATION RE-DERIVED BY NAME FIRST, as required (the plan's cited `:1526` was
    stale AGAIN by execution time, confirming F-7's standing warning):

    ```
    $ grep -n "def dependency_status" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:1592:def dependency_status(
    agent_workflows/oc_runipd.py:1604:def dependency_status_detailed(
    agent_workflows/agy_runipd.py:1664:def dependency_status(
    agent_workflows/agy_runipd.py:1675:def dependency_status_detailed(
    ```

    BLOCKED CASE, isolated tmp fixture, target in `executed/` carrying a `high`/`open` finding:

    ```
    fixture: target depaaa in executed/ WITH a high/open finding
      plan bucket: executed
      [oc] satisfied=False unsatisfied=['depaaa']
      [oc] reason: depaaa: review finding F-1 is high/open and unresolved
      [agy] satisfied=False unsatisfied=['depaaa']
      [agy] reason: depaaa: review finding F-1 is high/open and unresolved

    same fixture, finding marked FIXED:
      [oc] satisfied=True unsatisfied=[]
      [agy] satisfied=True unsatisfied=[]
    ```

    NO SESSION STARTED, proven by driving the REAL `run_queue` (not just the predicate) on the fixture:

    ```
    STEP 1: run the selection loop. The only queued item depends on a findings-blocked plan.
      item status      : dependency-blocked
      unsatisfied      : ['depaaa']
      reasons          : {'depaaa': 'depaaa: review finding F-1 is high/open and unresolved'}
      attempts (SESSIONS STARTED) : 0 <- 0 proves NO session started
      session log files: [] <- empty
      events: ['dependency-blocked']
    ```

    Both resolution paths are covered by assertions (`BlockingTests`): the out-of-queue
    `bucket == "executed"` path and the in-queue `EXECUTION_SUCCESS_STATES` path, so the gate is not
    evadable by whether the target is in the same run.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the identical fixture result for BOTH drivers, showing the same decision, and
    paste `grep -n` proving the predicate is defined once and imported by both rather than duplicated.
    Paste proof the shared home is a NON-runner module and that `oc_runipd` does NOT import `agy_runipd`
    or vice versa (F-11); a runner-to-runner import fails this item.
  - Observed evidence: IDENTICAL DECISION IN BOTH DRIVERS on the same fixture (see the V-01 paste:
    both report `satisfied=False unsatisfied=['depaaa']` with the same reason string).
    `SharedPredicateTests.test_both_drivers_agree_on_the_same_fixture` asserts equality of the two
    return values directly, and the threshold matrix is asserted host-independent too.

    PREDICATE DEFINED ONCE, in a NON-runner module:

    ```
    $ grep -rn "def plan_gating_blocks\|def plan_blocks_dependents" agent_workflows/
    agent_workflows/review_findings.py:758:def plan_gating_blocks(
    agent_workflows/review_findings.py:841:def plan_blocks_dependents(
    ```

    FOUR CONSUMERS, all delegating to that one definition (no second implementation anywhere):

    ```
    $ grep -rn "plan_gating_blocks" agent_workflows/*.py | grep -v "def plan_gating"
    agent_workflows/agy_runipd.py:1656:        blocks = _rf.plan_gating_blocks(repo, dep)
    agent_workflows/oc_runipd.py:1584:        blocks = _rf.plan_gating_blocks(repo, dep)
    agent_workflows/check_engine.py:1785:        return _rf.plan_gating_blocks(repo_root, dep_id6, threshold)
    agent_workflows/ipd_set_plan.py:291:        blocks = _rf.plan_gating_blocks(_repo_root_for_plans_dir(plans_dir), plan_id6)
    ```

    NO RUNNER-TO-RUNNER IMPORT (F-11 respected; `review_findings` is not a runner and was already
    imported by `check_engine`):

    ```
    $ grep -n "import agy_runipd" agent_workflows/oc_runipd.py ; echo "exit=$?"
    exit=1
    $ grep -n "import oc_runipd" agent_workflows/agy_runipd.py ; echo "exit=$?"
    exit=1
    ```

    (The only cross-runner occurrences are prose in a docstring/comment, not imports.) Asserted in
    `SharedPredicateTests.test_no_runner_to_runner_import`, plus
    `test_predicate_is_defined_once_in_a_non_runner_module` which additionally asserts neither runner
    contains `_SEVERITY_RANK`, i.e. neither reimplements the severity comparison.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `aw check` reporting the `executed:` edge that points at a findings-blocked
    plan, and paste a clean run once resolved. State explicitly that reuse of `dangling`/`ambiguous` was
    EVALUATED AND REJECTED (they are identity verdicts, F-8), name the new rule id, and paste
    `rule_spec("<new id>")` showing it resolves to a registered RuleSpec rather than the conservative
    default.
  - Observed evidence: REUSE EVALUATED AND REJECTED, on the evidence F-8 demanded. `_resolve_edge`
    (`check_engine.py:1773-1795` at execution time) returns exactly three verdicts, `ok` / `dangling` /
    `ambiguous`, and all three are IDENTITY verdicts: `dangling` asserts "no {type} artifact has id6
    X", `ambiguous` asserts "id6 X matches multiple {type} artifacts". A findings-blocked target
    resolves to EXACTLY ONE artifact, so reporting it as either would be a false statement about
    identity and would corrupt both rules' meaning for every other consumer. There is no existing
    verdict for target QUALITY, so a NEW rule id was added.

    NEW RULE ID: `check.ipd-dependency-findings-blocked`, registered in `RULE_REGISTRY` and resolving
    to a real RuleSpec rather than the conservative default:

    ```
    $ python3 -c "from agent_workflows import check_engine as ce; \
        print(ce.rule_spec('check.ipd-dependency-findings-blocked')); \
        print('in registry:', 'check.ipd-dependency-findings-blocked' in ce.RULE_REGISTRY); \
        print('unknown-id default:', ce.rule_spec('check.does-not-exist-xyz'))"
    RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='I-08')
    in registry: True
    unknown-id default: RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='')
    ```

    The registered spec is distinguishable from the conservative default by its `invariant='I-08'`
    (the default carries `invariant=''`). I-08 is claimed deliberately: this IS a statement about a
    cross-IPD dependency edge's satisfaction, which is what I-08 covers; only the input is new.

    THE RULE FIRING on an isolated fixture, and silent once resolved:

    ```
    === V-03: aw check evaluator reports the executed: edge to a findings-blocked plan ===
      check.ipd-dependency-findings-blocked
        dependency `executed:depaaa` resolves but does not satisfy the edge: depaaa: review finding
        F-1 is high/open and unresolved (recorded in 20260829-demo-01-depaaa-cascade.review.md)

    --- once the finding is FIXED (clean run) ---
      findings-blocked findings: [] <- empty
    ```

    `CheckEngineRuleTests` additionally asserts the rule is silent for a clean target, silent at
    threshold `off`, and NOT applied to an `exists:` edge (only `executed:` asserts completed work).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `dependency-blocked` event payload showing the target id6, the finding
    id, and the severity, plus the run-report line an operator would read. A message that says only
    "dependency not satisfied" fails this item. State whether you added a new payload key or changed the
    flat `dependencies` list's element type; if the latter, enumerate every reader you checked
    (report table, `print_status`, viewer).
  - Observed evidence: I ADDED NEW PAYLOAD KEYS (the additive option the plan recommended) and did NOT
    change the flat list's element type. `unsatisfied_dependencies` and the event's `dependencies`
    remain a flat `list[str]`; the reasons travel in a sibling `reasons` map plus a `recovery` string,
    and on the queue item in `unsatisfied_dependency_reasons` / `dependency_block_recovery`. Asserted
    by `BlockLegibilityTests.test_flat_dependency_list_shape_is_unchanged`.

    THE EVENT PAYLOAD, naming target id6, finding id, and severity:

    ```json
    {
      "at": "2026-08-30T00:00:00Z",
      "dependencies": ["depaaa"],
      "event": "dependency-blocked",
      "id6": "itemaa",
      "reasons": {
        "depaaa": "depaaa: review finding F-1 is high/open and unresolved"
      },
      "recovery": "resolve the named cause, then re-queue with `aw oc runipd resume --repo <repo> --retry-incomplete <run-id>`; a bare `resume` does NOT re-queue a dependency-blocked item"
    }
    ```

    THE RUN-REPORT LINES AN OPERATOR ACTUALLY READS (a new `## Dependency blocks (why)` section, so the
    table's column contract is untouched):

    ```
    ## Dependency blocks (why)
    - `itemaa` (position 1):
      - `depaaa`: depaaa: review finding F-1 is high/open and unresolved
      - Recovery: resolve the named cause, then re-queue with `aw oc runipd resume --repo <repo> --retry-incomplete <run-id>`; a bare `resume` does NOT re-queue a dependency-blocked item
    ```

    READERS CHECKED (even though the shape did not change, since the plan asked for the enumeration).
    Measured: `unsatisfied_dependencies` had NO readers at all before this change; it was write-only at
    three sites and never rendered:

    ```
    $ grep -rn "unsatisfied_dependencies" agent_workflows/*.py   # BEFORE this plan
    agent_workflows/agy_runipd.py:2758:                item["unsatisfied_dependencies"] = missing
    agent_workflows/oc_runipd.py:2707:                item["unsatisfied_dependencies"] = missing
    agent_workflows/oc_runipd.py:2745:                runnable["unsatisfied_dependencies"] = unfinished
    ```

    So an operator previously had NO surface showing which dependency blocked an item, let alone why -
    the exact failure mode this item removes. Both `write_report` and `print_status` in BOTH drivers
    now render the cause; asserted for the report by
    `BlockLegibilityTests.test_report_section_names_cause_and_recovery` across both drivers. The
    orchestrator-deferred site (`oc_runipd.py:2745`, `unfinished` children) was deliberately left
    alone: it is the separate `_set_children_all_executed` branch, not this predicate (F-6).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the test result with counts, and paste each case individually so none is
    vacuous: direct block; TRANSITIVE block (A -> B -> C with the finding on A); recovery after
    resolution using `resume --retry-incomplete` (a bare resume does NOT re-queue, F-10, so a bare-resume
    recovery test fails this item); `medium` ignored at `high` and caught at `medium`; `off` disabling.
    Paste an adversarial run proving the gate cannot be evaded by whether the target is in-queue versus
    out-of-queue (both code paths from E-01 exercised). Paste `grep -n` proving fixtures are tmp-dir
    isolated and no assertion reads this repo's live `.aw/records/runs/`.
  - Observed evidence: SUITE GREEN with counts, run BARE as the plan requires (no `-n0`, no second
    `-q`, no `-p no:randomly`):

    ```
    $ python3 -m pytest tests/test_review_findings_cascade.py
    ........................................                                 [100%]
    40 passed in 2.59s
    ```

    EACH DEMANDED CASE HAS ITS OWN NAMED TEST, so none can pass vacuously (full list of the 40, via
    `python3 -m unittest -v`):

    ```
    BlockingTests.test_out_of_queue_executed_dep_with_gating_finding_is_unsatisfied   <- direct block, out-of-queue path
    BlockingTests.test_in_queue_successful_dep_with_gating_finding_is_unsatisfied     <- direct block, in-queue path
    BlockingTests.test_clean_executed_dep_is_satisfied                               <- control
    BlockingTests.test_resolved_finding_unblocks_the_dependent                       <- runnable again after resolution
    BlockingTests.test_later_round_fix_does_not_block                                <- current-round semantics
    BlockingTests.test_malformed_review_blocks_rather_than_being_silently_skipped
    BlockingTests.test_review_action_item_is_not_findings_gated
    ThresholdTests.test_medium_does_not_block_at_high                                <- medium IGNORED at high
    ThresholdTests.test_medium_blocks_at_medium                                      <- medium CAUGHT at medium
    ThresholdTests.test_high_blocks_at_high
    ThresholdTests.test_blocker_blocks_at_high
    ThresholdTests.test_high_does_not_block_at_blocker
    ThresholdTests.test_off_disables_blocking_entirely                               <- `off` disables
    ThresholdTests.test_both_drivers_share_the_threshold_matrix
    TransitiveCascadeTests.test_transitive_dependent_is_also_blocked                 <- A -> B -> C
    TransitiveCascadeTests.test_independent_satisfiable_item_is_still_selected
    RecoverySemanticsTests.test_dependency_blocked_is_in_the_retry_set_but_only_under_the_flag
    RecoverySemanticsTests.test_retry_incomplete_flag_exists_on_resume
    ```

    TRANSITIVE BLOCK (A -> B -> C, finding on A) asserted at BOTH hops in BOTH drivers: B is refused
    directly by A's finding (`unsatisfied == ['aaa111']`), and C is refused because B is then not in a
    success state (`unsatisfied == ['bbb222']`). So "everything depending on a failed item waits" holds
    beyond the immediate dependent.

    ADVERSARIAL IN-QUEUE VS OUT-OF-QUEUE: the two E-01 code paths are separate tests.
    `test_out_of_queue_...` leaves the target out of the queue so the `bucket == "executed"` branch
    decides; `test_in_queue_...` places the target in the queue at status `executed` so the
    `EXECUTION_SUCCESS_STATES` branch decides. Both refuse, so the gate is not evadable by run
    membership.

    RECOVERY USES THE REAL FLAG. See the V-08 evidence, which drives the ACTUAL `run_queue`: after a
    BARE resume the item is still `dependency-blocked`; only the `--retry-incomplete` re-queue path
    returns it to `queued`. No bare-resume recovery assertion exists anywhere in this file.

    THE FALSE CLAIM WAS NOT ASSERTED (F-10 honored). I did not write "independent queue items still
    proceed". `test_independent_satisfiable_item_is_still_selected` asserts the TRUE property - a
    satisfiable independent item is still SELECTED while a blocked chain waits - and its docstring
    records explicitly that the all-or-nothing terminal case (nothing satisfiable -> every queued item
    marked blocked -> `break` out of the run) is PRE-EXISTING runner behavior this plan does NOT change.

    FIXTURE ISOLATION, no live-state reads (the `i79rgh` defect class):

    ```
    $ grep -n "mkdtemp\|records/runs" tests/test_review_findings_cascade.py
    58:    d = Path(tempfile.mkdtemp(prefix="aw_revgate03_"))
    433:                run_dir = Path(tempfile.mkdtemp(prefix=f"aw_rep_{name}_"))
    ```

    Every repo fixture is an `mkdtemp` tree, every threshold is written into the FIXTURE's own
    `project.json` (never the live config), and the string `.aw/records/runs/` does not appear in the
    file at all.

    NON-VACUITY PROVEN BY MUTATION. I temporarily made `plan_gating_blocks` return `()`
    unconditionally (simulating "this plan never happened") and re-ran the file:

    ```
    15 failed, 25 passed in 4.00s
    FAILED ...BlockingTests::test_out_of_queue_executed_dep_with_gating_finding_is_unsatisfied
    FAILED ...BlockingTests::test_in_queue_successful_dep_with_gating_finding_is_unsatisfied
    FAILED ...BlockingTests::test_malformed_review_blocks_rather_than_being_silently_skipped
    FAILED ...ThresholdTests::test_high_blocks_at_high
    FAILED ...ThresholdTests::test_medium_blocks_at_medium
    FAILED ...ThresholdTests::test_blocker_blocks_at_high
    FAILED ...TransitiveCascadeTests::test_transitive_dependent_is_also_blocked
    FAILED ...TransitiveCascadeTests::test_independent_satisfiable_item_is_still_selected
    FAILED ...SharedPredicateTests::test_both_drivers_agree_on_the_same_fixture
    FAILED ...CheckEngineRuleTests::test_executed_edge_to_findings_blocked_plan_is_reported
    FAILED ...BlockLegibilityTests::test_reason_map_names_the_finding_id_and_severity
    FAILED ...SetCompilerGateTests::test_findings_blocked_child_becomes_a_gate_and_blocks_descendants
    FAILED ...SetCompilerGateTests::test_manifest_carries_the_gate_reason
    FAILED ...SetCompilerGateTests::test_independent_sibling_is_not_blocked_with_an_explicit_orchestrator_table
    FAILED ...CrossSurfaceNonEvasionTests::test_every_authority_surface_refuses_the_same_finding
    ```

    The mutation was reverted from a byte-for-byte backup and the suite re-confirmed at `40 passed`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the cross-surface test output enumerating each authority surface and its
    decision on the same fixture: `oc_runipd.dependency_status`, `agy_runipd.dependency_status`, the
    `check_engine` evaluator, and the Set compiler. If any surface is uncovered, paste the explicit
    XFAIL/skip naming it; an uncovered surface that is merely absent from the test fails this item.
  - Observed evidence: ALL FOUR SURFACES REFUSE THE SAME FIXTURE. No XFAIL and no skip is needed,
    because E-07 took branch (a) and CLOSED the fourth surface rather than scoping it out.

    ```
    CROSS-SURFACE VERDICT MAP (True = surface REFUSES the fixture):
      agy_runipd.dependency_status                  True
      check_engine.evaluate_ipd_dependencies        True
      ipd_set_plan.blocked_children                 True
      oc_runipd.dependency_status                   True
    ```

    The test (`CrossSurfaceNonEvasionTests.test_every_authority_surface_refuses_the_same_finding`)
    asserts this map by EQUALITY against all-True, so a future surface that stops refusing flips a
    single, explicit assertion rather than silently going uncovered.

    A VACUITY TRAP FOUND AND CLOSED WHILE WRITING THIS ITEM, recorded because it would have made the
    surface-4 assertion meaningless. `ipd_set_plan.RUNNABLE_STATUSES` is `{approved, auto-approved}`, so
    a child whose status is `executed` is ALREADY a gate for a PRE-EXISTING reason unrelated to
    findings. My first version of this test reused the `executed` target and therefore would have
    passed with this plan's code fully reverted. Surface 4 is now exercised on a SEPARATE Set whose
    children are `approved` (i.e. in `RUNNABLE_STATUSES`), so the finding is the ONLY possible gate
    cause, and the assertion also requires `gate_reasons` to name the FINDING:

    ```
    Surface 4 detail (Set 'other', children are APPROVED so findings is the ONLY possible cause):
      deferred_gates  : ('eee555',)
      blocked_children: ('eee555', 'fff666')
      gate_reasons    : {'eee555': 'eee555: review finding F-1 is high/open and unresolved'}
    ```

    A dedicated control test, `CrossSurfaceNonEvasionTests.test_surface_4_assertion_is_not_vacuous`,
    pins this down: same Set, same statuses, finding marked `fixed` -> `deferred_gates == ()` and
    `blocked_children == ()`. And the mutation run in V-05 confirms
    `test_every_authority_surface_refuses_the_same_finding` FAILS when the predicate is neutered.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: state which branch you took. If (a): paste a Set-compile fixture where a
    findings-blocked child appears in `blocked_children` together with its transitive descendants, plus
    `grep -n` proving you reused `_propagate_blocked` rather than writing a second cascade, plus proof an
    independent approved sibling is NOT in `blocked_children`. If (b): paste the Deferred-section and
    Scope-check text naming `/exec-set` as a known uncovered path, and explain why closing it was
    rejected. Silence about this surface fails this item either way (F-9).
  - Observed evidence: BRANCH TAKEN: (a), the recommended one. The `/exec-set` Set compiler now treats a
    findings-blocked child as a gate, so the gate is not evadable by choosing the Set path.

    SET-COMPILE FIXTURE (Set `demo`, explicit orchestrator child-table: 1 -> 2 -> 3, plus INDEPENDENT
    sibling 4; the `high`/`open` finding is on child 1 only):

    ```
    cross_edges_source : orchestrator-table
    cross_edges        : {'aaa111': (), 'bbb222': ('aaa111',), 'ccc333': ('bbb222',), 'ddd444': ()}
    deferred_gates     : ('aaa111',)
    blocked_children   : ('aaa111', 'bbb222', 'ccc333')
    gate_reasons       : {'aaa111': 'aaa111: review finding F-1 is high/open and unresolved'}
    independent ddd444 blocked? False <- False = descendant-only blocking
    ```

    So the gate blocks itself and its TRANSITIVE descendants (`bbb222`, `ccc333`) while the INDEPENDENT
    approved sibling `ddd444` stays runnable, which is the property that keeps this from being a
    Set-wide halt. CONTROL, same Set with the finding marked `fixed`:

    ```
    --- CONTROL: same Set, finding FIXED -> no gate at all ---
    deferred_gates     : ()
    blocked_children   : ()
    ```

    REUSED `_propagate_blocked` RATHER THAN WRITING A SECOND CASCADE. There is exactly ONE definition
    and ONE call, and both gate causes feed it:

    ```
    $ grep -n "_propagate_blocked" agent_workflows/ipd_set_plan.py
    105:    # gating review findings (the new cause). Both feed the SAME `_propagate_blocked` cascade, so there
    236:def _propagate_blocked(
    434:    # `_propagate_blocked` fixpoint rather than a second cascade.
    448:    blocked = tuple(_propagate_blocked(child_ids, cross_edges, gates))
    $ grep -c "def _propagate_blocked" agent_workflows/ipd_set_plan.py
    1
    ```

    Asserted by `SetCompilerGateTests.test_reuses_the_existing_propagate_blocked_cascade`. The only
    change to the cascade's INPUT is that `gates` now has two causes instead of one; the fixpoint
    algorithm itself is untouched.

    THE MANIFEST AND `--plan-only` OUTPUT CARRY THE REASON, so an operator sees why:

    ```
    Deferred gates (unapproved or findings-blocked children): aaa111
      - aaa111: aaa111: review finding F-1 is high/open and unresolved
    Blocked children (gate + descendants): aaa111, bbb222, ccc333
    ```

    `gate_reasons` was added ADDITIVELY (a new field with a `{}` default on both `SetInventory` and
    `ExecutionManifest`, plus a new key in `to_dict`), so `deferred_gates` and `blocked_children` keep
    their exact shape and every existing consumer is unaffected; `tests/test_ipd_set_plan.py` and
    `tests/test_ipd_set_executor.py` pass unchanged (46 passed).

    SCOPE-PATHS UPDATED FIRST, as E-07 instructed for branch (a): `agent_workflows/ipd_set_plan.py`
    was added to this plan's `- Scope-Paths:` before the file was edited.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the corrected text from all three places the false recovery claim appeared
    (conventions, F-3, OQ-01), confirming none still says recovery is automatic or free. Paste the
    operator-facing message showing the exact recovery command. Paste a demonstration of the actual
    behavior: a `dependency-blocked` item still blocked after a BARE resume, then unblocked after
    `resume --retry-incomplete`. Confirm the runner's re-queue default was NOT changed.
  - Observed evidence: THE CORRECTED TEXT IN ALL THREE PLACES. The false claim had already been
    corrected IN PLACE during `/plan-review` (it is why E-08 exists), so my job was to VERIFY no
    assertion of it survives, not to re-correct it. Verified by search: the only remaining occurrences
    of the old wording are explicitly-labelled QUOTATIONS of the refuted claim, never assertions.

    1. Conventions (`## Project conventions discovered`): "Recovery is NOT free, contrary to the draft
       (F-10, corrected at review). `dependency-blocked` is re-queued ONLY under `if retry_incomplete:`
       ... A bare resume leaves the item blocked."
    2. F-3: "CORRECTED AT REVIEW - THE DRAFT'S CLAIM WAS FALSE. Recovery is NOT free and NOT automatic
       on resume."
    3. OQ-01: "PREMISE CORRECTED AT REVIEW (F-3/F-10): the draft's stated reason, that it 'is already
       re-queued on resume so recovery is free', is FALSE."

    Plus the Scope check: "Recovery costs an explicit `--retry-incomplete` ... 'Blocked until resolved'
    is accurate; 'resumes automatically' is not." No line in this plan now claims recovery is automatic
    or free.

    THE OPERATOR-FACING MESSAGE NAMING THE EXACT COMMAND (new `DEPENDENCY_BLOCK_RECOVERY_HINT` in both
    drivers, carried in the event payload, the run report, and `print_status`):

    ```
    resolve the named cause, then re-queue with
    `aw oc runipd resume --repo <repo> --retry-incomplete <run-id>`;
    a bare `resume` does NOT re-queue a dependency-blocked item
    ```

    (The agy driver carries the host-appropriate `aw agy runipd resume ...` form.) Asserted by
    `BlockLegibilityTests.test_recovery_hint_names_the_actual_flag`, which requires both
    `--retry-incomplete` and the word "bare" to appear.

    THE ACTUAL BEHAVIOR DEMONSTRATED against the REAL `run_queue`, not asserted from the docs:

    ```
    STEP 1: run the selection loop. The only queued item depends on a findings-blocked plan.
      item status      : dependency-blocked
      attempts (SESSIONS STARTED) : 0 <- 0 proves NO session started
      events: ['dependency-blocked']

    STEP 2: BARE resume (retry_incomplete=False). Per F-10 this must NOT re-queue.
      status after BARE resume: dependency-blocked <- still blocked

    STEP 3: resume WITH --retry-incomplete. This must re-queue it.
      status after --retry-incomplete re-queue: queued
      now satisfiable?: True [] <- finding resolved, so it can run
    ```

    RE-QUEUE DEFAULT NOT CHANGED, as E-08 explicitly required. The guard and the `start` default are
    byte-identical to the pre-execution baseline; I added no line to either. Verified by diffing the
    relevant region against the base commit:

    ```
    $ for f in oc_runipd agy_runipd; do echo "--- $f ---"; \
        git diff 72431928 -- agent_workflows/$f.py | grep -E "^[-+]" | grep -v "^[-+]#" \
        | grep -E "retry_incomplete" || echo "(none: no CODE line touching retry_incomplete)"; done
    --- oc_runipd ---
    (none: no CODE line touching retry_incomplete)
    --- agy_runipd ---
    (none: no CODE line touching retry_incomplete)
    ```

    (Comment lines are excluded deliberately and honestly: my E-08 documentation comment DOES mention
    `retry_incomplete` by name, so an unfiltered `grep -E "^[-+].*retry_incomplete"` matches that
    comment and would misleadingly suggest a behavior change. The filtered form above shows what
    actually matters: zero CODE lines were added, removed, or changed.)

    `RecoverySemanticsTests` additionally pins the invariant by asserting both runners still contain
    `if retry_incomplete:` and still pass `retry_incomplete=False` for `start`. The all-or-nothing
    terminal step was likewise left untouched.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and requires explicit human approval before execution. `reviewed` means the
review occurred; it is NOT approval, GO, or permission to execute.

SEQUENCING: this plan depends on `executed:plqjt7` (Order 02), which itself depends on `executed:15zvu6`
(Order 01). Every E-item here consumes `15zvu6`'s parser and `is_gating` predicate, so do NOT begin until
both are in `.aw/records/plans/executed/`.

CAUTION ON TIMING (STRENGTHENED AT REVIEW): this plan modifies `oc_runipd.py` and `agy_runipd.py`, which
TWO Sets are concurrently rewriting - `wtiso` across several phases, and now also `rununify`
(orchestrator `5e4sb6`, `reviewed`), whose entire purpose is to extract ~93 percent of these two files
into a shared library. The draft named only `wtiso`. Do NOT execute this plan while a phase of EITHER Set
touching those files is in flight; confirm the runner surface is quiet first, or expect an unmergeable
conflict. The stale line numbers this review corrected (F-7) are direct evidence of how fast these files
move: locate every symbol by name.

This is a sequencing constraint, not a dependency, so it is stated here rather than as an
`Item-Dependencies` edge. If `rununify` lands FIRST, `dependency_status` may no longer live in either
runner; in that case apply E-01/E-02 to the shared library instead and record that in the evidence
rather than reconstructing the duplicated shape this plan assumes.

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
