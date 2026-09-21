# IPD: Verify the source-to-plan index, the single enumeration, and the backlog ledger after both children land

- Date: 2026-09-20
- Kind: child
- Concern: Orchestrator `y9s4vm` carries three E-items that NO CHILD COVERS, and the sharpest of them (E-03, the backlog `6h7y2y` ledger) is one the runner CANNOT discharge even in principle. `process_backlog_close` fires only when an AGENT-EXECUTED IPD finalizes, and an orchestrator is not agent-executed: `dispatch_orchestrator_item` and `ipd_lifecycle.retire_orchestrator` contain no backlog-close call at all (verified at HEAD: `'backlog' in source` is False for both). Worse, `evaluate_backlog_close` requires EVERY IPD carrier terminal and the parent ITSELF carries `- From-Backlog: 6h7y2y`, so the close is refused by construction while the parent sits unretired. Because `retire_orchestrator` also skips the pre-transition E/V checkpoint, a runner would mark the parent `executed` with all three items unperformed.
- Scope: Perform the whole-Set verification the parent cannot. IN: confirm both children reached `executed` in the required order, prove exactly ONE spec enumeration survives and that the review sweep and the plan action agree, verify the cross-Set single-traversal constraint against `setidhard`'s `bwgyum`, and verify backlog `6h7y2y` reached its correct CONDITIONAL terminal state with the actor named. OUT: performing either child's implementation, closing the backlog item on the parent's behalf without checking which branch applies, and inventing a `Blocks-Release` gate the item does not carry.
- Scope-Paths: .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md, .aw/records/backlog/done/
- Item-Dependencies: executed:jxxec8, executed:iuxtjy
- Status: to-review
- Set: graduate
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: yv4tb1
- From-Backlog: 6h7y2y

## Workflow history

- 2026-09-20 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored to own orchestrator `y9s4vm`'s E-01, E-02 and E-03, which the ORCHESTRATOR COVERAGE GATE refused a run over on 2026-09-21. AGENTS.md prescribes adding a child for uncovered parent work rather than deleting the item, so `y9s4vm`'s checklist is left EXACTLY as authored and this child is what makes those items performable under a pre-transition E/V checkpoint. THE PARENT ALREADY PROVED THE HARDEST PART OF THE CASE, and I re-verified it live rather than trusting the prose. `evaluate_backlog_close(repo, '6h7y2y', [])` returns `close=False` with `reason='IPD carrier(s) not executed: ...graduate-00-y9s4vm..., ...graduate-01-jxxec8..., ...graduate-02-iuxtjy...'`, naming the PARENT as a blocking carrier, exactly as the parent's E-03 documented. Also re-verified by introspection that neither `runner_shared.dispatch_orchestrator_item` nor `ipd_lifecycle.retire_orchestrator` mentions `backlog` at all, while `process_backlog_close` is called from the agent-executed finalize path in both hosts (`oc_runipd.py:2680`, `agy_runipd.py:1608`). So the close is a deliberate human-or-agent act after the Set, and this plan is the agent-executed member that can legitimately perform it. MEASURED AT HEAD `41f6a45b` AND THREE OF THE PARENT'S FIGURES MOVED, which is itself why a re-measuring child is needed rather than a parent asserting stale numbers. `6h7y2y` is `- Status: graduated` (in `.aw/records/backlog/graduated/`), so E-03's CONDITIONAL branch is the live one and an executor holding it to `done` unconditionally would be wrong. `runner_shared.discover_specs` still exists exactly ONCE (`grep -c "def discover_specs"` -> 1, at `runner_shared.py:5460`) and finds 17 specs of 36 on disk, not the 9 of 28 the parent recorded; the gap is documented in its own docstring and is not a defect, but the parent's figure must not be quoted. `ACTION_CHOICES` is still `("review", "plan", "execute")` with `ACTION_IMPLEMENTED` still `frozenset(("review",))` (`runner_shared.py:12707-12708`), so the fail-closed refusal is intact and must not be re-implemented. The `From-Spec: 25kzda` cluster is NINE plans, matching the parent's largest-legitimate-cluster figure, so CID-1 has a real subject. SIX plans carry BOTH a `From-Spec:` and a `From-Backlog:` bullet, not the five the parent's F-9 recorded, so a first-match-only index would now drop six edges. THE CROSS-SET CONSTRAINT IS STILL UNBUILT AND THEREFORE STILL LIVE: `Graduated-To` occurs ZERO times in `agent_workflows/` and `check.graduated-to-dangling` does not exist (`grep -c` -> 0), so `bwgyum` has not landed and CID-7 must be reported as half-satisfied rather than declared clean.
- 2026-09-20 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Discharge the `graduate` Set's whole-Set verification from an agent-executed plan, so the Set's completion criteria and its backlog ledger are checked by something a pre-transition E/V checkpoint gates, instead of being parked on a parent that a runner retires without reading and that cannot close its own backlog item by construction.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the children landed in the required order

- [ ] E-01 CONFIRM BOTH CHILDREN REACHED `executed` AND THAT ORDER 01 PRECEDED ORDER 02, reading the STATUS ON DISK and the FINALIZE COMMITS rather than trusting any table. The parent's E-01 is explicit that the order is the backlog item's own instruction, on the stated reason that the verb without the guard is "a machine for generating redundant plans faster than a human can".
  PROVE THE ORDER BY COMMIT, NOT BY ORDER DIGIT. Compare the two finalize commits' timestamps or ancestry. An Order digit is an intention; a commit is what happened. This is the same standard the sibling `specdirs` Set applies in its CID-1.
  - Depends on: none
  - Expected outcome: `jxxec8` and `iuxtjy` both read `- Status: executed` and sit in `.aw/records/plans/executed/`, with pasted evidence that Order 01's finalize commit precedes Order 02's.
  - Execution state: pending

### Task group 2: the two structural properties no child can assert alone

- [ ] E-02 PROVE EXACTLY ONE SPEC ENUMERATION SURVIVES, AND THAT THE REVIEW SWEEP AND THE PLAN ACTION RESOLVE THE SAME SPEC SET. This is the parent's named damage case: a parallel enumeration would make the two surfaces disagree about which specs exist.
  ASSERT BY IDENTITY, NOT BY GREP ALONE. The parent's CID-2 requires object identity plus a comparison of the two resolutions. Grep proves a name appears once; identity proves both callers reach the SAME function.
  MEASURED AT HEAD `41f6a45b` SO YOU CAN DETECT A REGRESSION: `grep -c "def discover_specs" agent_workflows/runner_shared.py` is 1, the definition is at `runner_shared.py:5460`, and `discover_specs(repo)` returns 17 records against 36 `*.spec.md` files on disk. DO NOT QUOTE THE PARENT'S "9 of 28": that figure is stale and the tree moves. The 17-of-36 gap is DOCUMENTED BEHAVIOR, not a bug: `discover_specs` deliberately skips a spec with no `- Id:` because such a spec "cannot be named by a selector, cannot carry a review record ... and cannot be attested". Re-measure and report your own numbers, and treat a DROP in the ratio as the signal, not the ratio itself.
  ALSO CONFIRM THE AST GUARD STILL HOLDS: the module is guarded by a test rejecting a new `"records/specs"` path literal in `runner_shared`. Confirm that test still passes, since it is what makes "no second enumeration" durable rather than momentary.
  - Depends on: E-01
  - Expected outcome: exactly one spec-discovery function in `runner_shared` proven by identity and not only by grep; the review sweep and the plan action shown to resolve the same spec set for the same repository; the AST path-literal guard test passing; re-measured counts reported rather than inherited.
  - Execution state: pending

- [ ] E-03 VERIFY THE CROSS-SET SINGLE-TRAVERSAL CONSTRAINT AGAINST `setidhard`'s `bwgyum`, which is the parent's coordination constraint and the one thing neither Set's children can see. Both Sets read ONE relationship from opposite ends: `bwgyum` adds the FORWARD `- Graduated-To: <setid>[, ...]` link on the source plus `check.graduated-to-dangling`, while this Set's child 01 builds the REVERSE index from source id6 to the plans citing it. Whichever landed SECOND must CONSUME what the first built rather than re-walking the tree.
  MEASURED AT HEAD `41f6a45b`: `bwgyum` HAS NOT LANDED. `Graduated-To` occurs ZERO times in `agent_workflows/` and `check.graduated-to-dangling` does not exist (`grep -c "graduated-to-dangling" agent_workflows/check_engine.py` -> 0). `bwgyum` is `approved` and still in `pending/`. So the EXPECTED outcome is that only ONE of the two Sets has landed.
  THE HONEST REPORT IS THEN "HALF-SATISFIED", NOT "CLEAN". The parent's CID-7 says so explicitly: "If only one of the two Sets has landed, state that plainly rather than declaring the CID satisfied." Do NOT declare the constraint met because no duplication exists yet; the duplication risk transfers to `bwgyum`, so the deliverable is a RECORDED note that `bwgyum` must consume child 01's index, placed where `bwgyum`'s executor will see it.
  - Depends on: E-01
  - Expected outcome: a statement of which of the two Sets has landed, measured rather than assumed; if only this one, an explicit half-satisfied verdict plus a recorded hand-off note that `bwgyum` must consume child 01's reverse index rather than re-walking the tree; if both, the single shared symbol named and the two directions shown to return consistent answers for the same source.
  - Execution state: pending

### Task group 3: the backlog ledger

- [ ] E-04 VERIFY BACKLOG `6h7y2y` REACHED ITS CORRECT TERMINAL STATE, PERFORM THE TRANSITION IF IT IS OWED, AND NAME THE ACTOR. This is the parent's E-03 and it is the item the runner cannot discharge: the close is refused while the parent is unretired because the parent is itself a carrier.
  THE TERMINAL STATE IS CONDITIONAL AND THE CONDITION DECIDES CORRECTNESS. `done` ONLY IF child 02 built the backlog half; `graduated` PLUS a filed follow-on if child 02's OQ-01 legitimately deferred it (there is no `discover_backlog` to consume, unlike `discover_specs`, which is why the deferral is permitted). Read child 02's shipped outcome to decide WHICH branch applies; do not assume `done`. An executor holding the item to `done` after a legitimate deferral would close an item whose half is unbuilt.
  MEASURED AT HEAD: the item is CURRENTLY `- Status: graduated` in `.aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md`. So if child 02 deferred, the state is ALREADY correct and this item is satisfied by verifying it and confirming a follow-on exists; if child 02 built the backlog half, a transition to `done` is owed.
  USE THE TOOLED SETTER WITH THE `--status` SPELLING, which runs the release-gate predicate: `aw backlog set done <item> --status done`. Do NOT hand-edit the status line (an opt-in pre-commit gate exists precisely to catch that, and the portable authority is the `aw check` rule). CONFIRM NO GATE IS INVENTED: the item carries NO `- Blocks-Release:`, and no plan in this Set may add one, so the close-legitimacy predicate has no gate to preserve. Verify that rather than assuming it.
  NAME WHO PERFORMED THE TRANSITION AND SAY IT WAS NOT AUTOMATION. The three precedent items closed this way (`kjzlgw`, `1ap48y`, `kxkc04`) each record the orchestrator caveat with a hand-written justification; the three the runner auto-closed (`q5pdiy`, `0zj66l`, `2k42zu`) have ZERO orchestrator carriers. Follow the first pattern.
  - Depends on: E-02, E-03
  - Expected outcome: `6h7y2y` reads `done` if child 02 built the backlog half, or `graduated` with a filed follow-on if it deferred; the branch chosen is justified by citing child 02's shipped outcome; the transition (if any) was performed through the tooled setter by a named actor rather than by runner automation; no plan in this Set carries `- Blocks-Release:`; `aw backlog check` clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR'S UNCOVERED ITEM GETS A CHILD, NOT A DELETION. AGENTS.md: "do NOT delete it: ADD A CHILD for it." `y9s4vm`'s checklist is untouched by this plan; its items are discharged by citing this child's evidence.
- A BACKLOG ITEM IS NOT CLOSED BY THE SET THAT DRAINS IT WHEN AN ORCHESTRATOR CARRIES THE LINK. `process_backlog_close` fires only at an agent-executed IPD's finalize (`oc_runipd.py:2680`, `agy_runipd.py:1608`); orchestrator retirement never calls it (verified by introspection: `'backlog' in inspect.getsource(...)` is False for both `dispatch_orchestrator_item` and `retire_orchestrator`), and `evaluate_backlog_close` refuses while ANY carrier including the orchestrator is unexecuted.
- `evaluate_backlog_close` NAMES THE PARENT AS A BLOCKER TODAY. Live call returns `close=False, reason='IPD carrier(s) not executed: ...y9s4vm..., ...jxxec8..., ...iuxtjy...'`. This plan being agent-executed is what gives the Set a legitimate place to perform the close.
- `discover_specs` EXISTS EXACTLY ONCE AND IS CAREFULLY BUILT. At `runner_shared.py:5460`, taking no injected parser because there is one spec record shape. It reads identity and status through shared authorities and adds NO path literal, guarded by an AST test. It finds 17 of 36 specs at HEAD and the gap is documented in its own docstring.
- `--action plan` ALREADY FAILS CLOSED. `ACTION_CHOICES = ("review", "plan", "execute")` and `ACTION_IMPLEMENTED = frozenset(("review",))` at `runner_shared.py:12707-12708`. Do not re-fix it.
- MULTIPLE PLANS PER SOURCE ARE LEGITIMATE. The `From-Spec: 25kzda` cluster is NINE plans at HEAD and is correct work. No child may implement a `count > 1` uniqueness rule.
- SIX PLANS CARRY BOTH A `From-Spec:` AND A `From-Backlog:` BULLET at HEAD (the parent's F-9 recorded five). A first-match-only index would drop one edge per such plan.
- THE FORWARD LINK IS UNBUILT. `Graduated-To` occurs zero times in `agent_workflows/` and `check.graduated-to-dangling` does not exist, so `bwgyum` has not landed.

## Findings

| Id | Severity | Location (measured at HEAD `41f6a45b`) | Finding | Evidence |
|---|---|---|---|---|
| F-01 | error | `y9s4vm` E-01..E-03 | All three parent items are covered by no child, and orchestrator retirement skips the E/V checkpoint, so a runner reports them complete unperformed. This plan closes that. | ORCHESTRATOR COVERAGE GATE refused `aw oc run` naming `y9s4vm` on 2026-09-21. |
| F-02 | error | `oc_runipd.evaluate_backlog_close` | The parent is itself a blocking carrier for its own backlog item, so the close is refused by construction while it is unretired. Confirmed live, not inferred. | `close=False, reason='IPD carrier(s) not executed: ...y9s4vm..., ...jxxec8..., ...iuxtjy...'`. |
| F-03 | info | `dispatch_orchestrator_item`, `retire_orchestrator` | Neither mentions `backlog` at all, so no runner path can close the item on an orchestrator's retirement. | `'backlog' in inspect.getsource(fn)` is False for both. |
| F-04 | warn | `y9s4vm` Step 0 ("finds 9 of 28 specs") | STALE. `discover_specs` finds 17 of 36 at HEAD. The ratio is documented behavior, not a defect, but the parent's figure must not be quoted as current. | `len(discover_specs(repo))` -> 17; `ls .aw/records/specs/*.spec.md | wc -l` -> 36. |
| F-05 | warn | `y9s4vm` F-9 ("five plans carry both") | STALE in the direction that matters: SIX plans carry both a `From-Spec:` and a `From-Backlog:` bullet, so a first-match index drops six edges, not five. | Counted over `.aw/records/plans/*/*.ipd.md`. |
| F-06 | info | `6h7y2y` | The item is `graduated`, so E-04's CONDITIONAL branch is live. An executor defaulting to `done` would be wrong. | `.aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-...backlog.md` reads `- Status: graduated`. |
| F-07 | info | `agent_workflows/` | `bwgyum` has not landed, so CID-7 is half-satisfiable at best and must be reported as such rather than declared clean. | `Graduated-To` zero occurrences; `check.graduated-to-dangling` zero occurrences. |

## Proposed changes (ordered, validatable)

1. Confirm both children `executed` with Order 01's finalize commit preceding Order 02's (E-01).
2. Prove one spec enumeration by identity, with the two surfaces agreeing and the AST guard passing (E-02).
3. Report the cross-Set traversal constraint honestly as half-satisfied, and record the hand-off note for `bwgyum` (E-03).
4. Verify (and if owed, perform through the tooled setter) `6h7y2y`'s conditional terminal transition, naming the actor (E-04).

This plan ships almost no code. Its deliverables are a verification record and, conditionally, one backlog status transition plus a hand-off note. That is the correct shape for the work the parent could not perform.

## Deferred / out of scope (with reason)

- IMPLEMENTING EITHER CHILD'S WORK. Child 01 owns the reverse index and child 02 owns the selector; this plan verifies, it does not build.
  - Carrier-Declined: A DIVISION OF LABOUR, not deferred work: both children are already authored and approved, and each owns its half. Nothing is left unowned for a carrier to hold.
- ADDING A `count > 1` UNIQUENESS RULE. Forbidden by the parent's hard constraints: 17 of 72 sources legitimately have more than one plan and the largest correct cluster is nine. A uniqueness rule would flag correct work and teach people to ignore the warning.
  - Carrier-Declined: A REJECTED DESIGN, recorded so it is not re-proposed. The parent's hard constraints forbid it on measured grounds (the largest legitimate cluster is nine plans), so there is no future state in which it should be built.
- RE-FIXING THE `--action plan` REFUSAL. It already fails closed (`ACTION_IMPLEMENTED = frozenset(("review",))`) and must keep doing so for anything child 02 did not implement.
  - Carrier-Declined: Correct as-is, not deferred. `ACTION_IMPLEMENTED = frozenset(("review",))` already fails closed, so there is no work to hand off.
- WEAKENING `check.from-backlog-dangling` OR `check.from-spec-dangling`. Both are `error` severity and validate the FORWARD direction. This Set adds a reverse VIEW and does not touch them.
  - Carrier-Declined: A PROHIBITION, not an obligation. Both rules are `error` severity and must stay untouched; a carrier would imply someone should later change them.
- ANSWERING THE "ALREADY IMPLEMENTED" CASE MECHANICALLY. There is no per-requirement tracking: a spec carries ONE whole-artifact status, and `implemented` requires only a resolvable citation rather than semantic verification. Backlog `f1sw71` tracks that gap and is `graduated` to decision plan `si24ia`.
  - Carrier-Declined: Already carried: backlog `f1sw71` owns this gap and is `graduated` to decision plan `si24ia`. A second carrier would duplicate a live record.
- BUILDING THE FORWARD `Graduated-To` LINK. That is `bwgyum`'s deliverable in the `setidhard` Set. This plan records the coordination note and stops.
  - Carrier-Declined: Already carried by plan `bwgyum` (Set `setidhard`), which is `approved` and owns the forward link plus its dangling check. E-03 records the coordination note rather than duplicating the work.
- ADDING A `Blocks-Release` GATE. The item carries none, and inventing one would fabricate a release gate.
  - Carrier-Declined: A PROHIBITION protecting an absent gate. The item carries none, so inventing one would fabricate a release blocker; there is nothing to carry.
- THE `Readiness:` FIELD. Deliberately ABSENT: it is `/plan-review`'s attested output, and hand-writing it would forge a review that never happened.
  - Carrier-Declined: The ABSENCE is the correct permanent state, not an omission to fix later. `/plan-review` writes that field; hand-writing one forges a review.

## Scope check

- Over-scope: none. This plan reads state, asserts properties, and performs at most one tooled backlog transition.
- Scope-Paths justification: the declared paths are the backlog item itself and the `done/` directory it may be relocated INTO, because E-04 may perform a `graduated` -> `done` transition and the tooled setter relocates the file with `git mv` (a single staged rename). Both endpoints must be declared or the finalize scope gate would refuse the rename. NO product-code path is declared, deliberately: this plan verifies code it does not change, and reading is not declaring. The hand-off note E-03 records goes in this plan's own file, which `_is_implicitly_allowed` already covers.
- Under-scope: this plan builds no index, adds no selector, adds no check, touches no dangling rule, and does not build the forward link. Each is a sibling's job or is excluded above.

## Required tests / validation

- `aw backlog check` clean after any transition.
- `aw check all` shows no new `check.from-backlog-dangling` or `check.from-backlog-gate-mismatch` finding attributable to this plan. NOTE the repo has PRE-EXISTING findings of other rules; judge on the DELTA for these two rule ids specifically, and name them rather than quoting a total.
- The AST path-literal guard test for `runner_shared` passes (E-02).
- Bare suite `python3 -m pytest`, judged on the failing NODE ID delta against a baseline measured in the executing worktree. AFTER minus BEFORE must be EMPTY. Do NOT copy this Set's cited baseline: the parent's own Step 0 records that its `1 failed, 5648 passed` figure and its named failure were BOTH stale, that `test_orchestrator_retirement.py` now passes, and that the one real failure it later measured was environmental (an untracked `opencode-recovery/` dump belonging to another party). Measure your own and name node ids, never totals.
- Do NOT delete another party's untracked files to make the suite green; this is a shared checkout.

## Spec / documentation sync

- NO SPEC AMENDMENT IS INTENDED and no `.spec.md` path is declared in `Scope-Paths`. Spec `25kzda`'s graduation text (a run "may produce more than one IPD") and spec `6m4kow`'s spec-review authority are both CONSUMED by this plan, not amended. If E-02 or E-03 finds that a shipped behavior contradicts either spec, STOP and record it: a spec edit is a contract change that must be declared in `Scope-Paths` before the run starts, so it needs its own plan.
- The hand-off note in E-03 is a PLAN-LEVEL record, not documentation: it belongs in this plan's evidence and, if the maintainer prefers, in a backlog item for `bwgyum`'s executor. It must not be written into `bwgyum` itself, which is another plan's file.

## Open questions

### OQ-01: If child 02 deferred the backlog half, who files the follow-on and is this plan allowed to file it?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: A CONTINGENT AUTHORITY QUESTION, not an outstanding obligation. It only arises if child 02 deferred the backlog half AND filed no follow-on, and in that case E-04's evidence RECORDS the missing follow-on as a finding, so nothing disappears unrecorded. The question is which of two legitimate routes an executor should take, which is a convention for the maintainer rather than work anyone owes.
- Resolution or deferral rationale: NON-BLOCKING because E-04's verification succeeds either way: the item is ALREADY `graduated`, so if child 02 deferred, the correct state is the current one and this plan's job is to CONFIRM a follow-on exists rather than to invent a status change. The open part is narrow: if child 02 deferred and NO follow-on was filed, the honest options are (a) this plan files one with `aw backlog new`, which is a small records-only act well within an agent's normal authority but slightly widens this plan's scope beyond verification, or (b) this plan reports the missing follow-on as a finding and leaves the filing to the maintainer, keeping the plan purely verificatory. RECOMMENDATION: (a), because a verification that discovers a missing record and declines to create it leaves the gap open with nobody owning it, and `aw backlog new` is exactly the tooled path for that. If the maintainer prefers (b), E-04's expected outcome should be narrowed to reporting only. Either way, this plan must NOT set the item `done` to make the branch tidy.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both children's `- Status:` lines and their file paths showing they sit in `.aw/records/plans/executed/`. Paste the ORDERING proof as commit evidence (timestamps or `git merge-base --is-ancestor`), not as a restatement of the Order digits. Also paste a summary of each child's `V-*` results showing they carry real observed evidence rather than assertions, since a child marked `executed` with empty evidence blocks would make this Set's completion claim hollow.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the identity proof that the review sweep and the plan action reach the SAME spec-discovery function (object identity, not grep), plus the two resolutions compared for the same repository showing an identical spec set. Paste `grep -c "def discover_specs" agent_workflows/runner_shared.py` and your OWN re-measured `len(discover_specs(repo))` against the on-disk `*.spec.md` count, and compare to the 1 and 17-of-36 recorded in this plan's Findings, explaining any change. Paste the AST path-literal guard test's summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the measurement of whether `bwgyum` has landed (`grep -c "graduated-to-dangling" agent_workflows/check_engine.py` and an occurrence count for `Graduated-To` in `agent_workflows/`), plus `bwgyum`'s current `- Status:` and directory. If only this Set has landed, paste the explicit HALF-SATISFIED verdict and the recorded hand-off note; a verdict of "satisfied, no duplication found" on a tree where the forward link does not exist yet does NOT satisfy this item, because the constraint is about what the SECOND Set must do. If both have landed, name the single shared symbol and paste the two directions returning consistent answers for one source.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `6h7y2y`'s final `- Status:` and file path, and paste the CITATION from child 02's shipped outcome that justifies which branch (`done` versus `graduated` plus follow-on) is correct. If a transition was performed, paste the tooled command used (the `--status` spelling) and its output; a hand-edited status line is not acceptable evidence. NAME THE ACTOR explicitly and state that the transition was not performed by runner automation, following the `kjzlgw`/`1ap48y`/`kxkc04` precedent. Paste a confirmation that no plan in this Set carries `- Blocks-Release:` and that `aw backlog check` is clean. Finally, paste the `aw check all` delta for `check.from-backlog-dangling` and `check.from-backlog-gate-mismatch` specifically, naming the rule ids rather than quoting a repo-wide total.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. No `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

THIS PLAN RUNS LAST IN ITS SET, BY CONSTRUCTION. It declares `Item-Dependencies: executed:jxxec8, executed:iuxtjy` because a whole-Set verification cannot precede the Set. Under a runner, `dependency_depth` sorts it last and both edges are re-checked AT DISPATCH, so if either child has not landed this item is marked `dependency-blocked` and the run continues rather than failing. That is correct behavior and not a defect to report.

WHY THIS CHILD IS THE RIGHT PLACE FOR THE BACKLOG CLOSE, stated because it is the subtle part. The close is refused while the parent is unretired, since `evaluate_backlog_close` requires every carrier terminal and the parent is itself a carrier. This plan carries `- From-Backlog: 6h7y2y` too, so it is a carrier as well and does NOT magically unblock the predicate on its own; what it provides is an AGENT-EXECUTED finalize, which is the only event that calls `process_backlog_close` at all. Expect the ordinary outcome to be that this plan VERIFIES the item's state and performs the transition deliberately through the tooled setter, exactly as the three `done/` precedents with orchestrator carriers were closed, rather than relying on automation firing. Do not read a refused automatic close as a defect.

WHAT THIS PLAN DOES TO ITS PARENT: NOTHING is deleted from `y9s4vm`. Its E-01, E-02 and E-03 stay exactly as authored, because that checklist is what makes `execute graduate` complete when a human drives the Set with no runner involved. This plan's row is ADDED to the parent's child table so the Set is covered, which lets the coverage gate pass and lets the runner retire the parent honestly. The parent's items are then discharged by CITING this child's pasted evidence.

Execution contract: commit ONLY files you changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A`, never `-a`, and never push. THIS IS A SHARED CHECKOUT with other agents and humans working concurrently: verify the staged set with `git diff --cached --name-only` before every commit and `git restore --staged <path>` anything that is not yours, and re-verify after ANY failed hook, because `pre-commit` restores unstaged changes on rejection and can leave paths you never staged in the index. Prefer the tooled path (`aw commit <plan> -- <paths>`), which snapshots the index before staging and commits only the intersection of your explicit paths with what it staged. Use the tooled `aw backlog set ... --status ...` spelling for any status change, never a hand edit. When every `E-*` is performed and every `V-*` carries pasted evidence, move this plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never by hand.
