# IPD: wire both host dispatch paths and correct the documented claim

- Date: 2026-09-06
- Kind: child
- Concern: Three defects on the dispatch side, all measured at HEAD `844d195c`. FIRST, the oc dispatch branch (`oc_runipd.py:6993-7031`) writes `runnable["status"] = "dependency-blocked"` on ANY failure; that value is in `TERMINAL_STATES` (`:254-272`) and the selection filter admits only `queued` (`:4071`, `:6919`), so the orchestrator is excluded FOREVER even when its children all finish later in the SAME run. The event is literally named `orchestrator-deferred`, and a deferral is by definition something you return to. SECOND, one `else` covers two unrelated failures, proven by the two recorded reasons on one run: `5e4sb6 | not-all-children-executed` and `rh5tt6 | finalize-refused`. So `kxkc04`'s prescription ("leave it queued") is correct for the first and would make the second SPIN FOREVER. THIRD, the agy runner has no orchestrate action at all: `action_for`, `finalize_orchestrator` and `_set_children_all_executed` are all absent from `agy_runipd` (verified by object identity, not grep), and `agy_runipd.py:1783` calls its own `determine_action` (`:1510-1514`), so `agy.determine_action('approved')` returns `'execute'` where `oc.action_for('orchestrator','approved')` returns `'orchestrate'`. `aw agy run` would AGENT-EXECUTE an orchestrator, spending a turn authoring against a plan whose purpose the runner has superseded.
- Scope: Wire child 01's predicate and child 02's transition into BOTH hosts' dispatch, replace the single terminal-status write with the reconsiderable-versus-dead distinction (spec `77tr3o` R-7, R-8), give the agy runner the `orchestrate` action it lacks via SHARED code rather than a copy (R-10), make the four refusal reasons distinguishable in the durable record (R-9), and correct the false `AGENTS.md` self-finalization claim (R-11). It does NOT change the eligibility predicate (child 01) or the transition (child 02), and it does NOT touch the general `dependency-blocked`-is-terminal defect for ORDINARY items, which is `nueip1`.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/engine.py, AGENTS.md, tests/test_orchestrator_retirement.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:5942n7, executed:ueg5cf
- Status: approved
- Readiness: go-pending-approval
- Set: orchretire
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: pgq326
- Approval: 2026-09-06, recorded via aw ipd set: status set to approved
- From-Backlog: kxkc04
- From-Spec: 77tr3o

## Workflow history
- 2026-09-06 executed-pending-transition (opencode its_direct/pt3-claude-opus-5-1m-us): All 7 E-items performed and all 7 V-items verified with pasted evidence; `aw ipd lint --phase pre-transition` reports CONFORMING. Implementation committed as abb3d648 (7 files, path-scoped). Suite 31 failed / 5458 passed against a measured baseline of 31 failed / 5431 passed in this same worktree, with an IDENTICAL failing node-id set (zero regressions); the 31 are lane-environmental (AW_EXECUTION_ROLE=worker begin/finalize refusals, and run_viewer's .aw/state resolution in a linked worktree). THE TERMINAL TRANSITION IS NOT PERFORMED HERE: `aw ipd finalize` refuses in the worker role (AW-LIFECYCLE-ROLE-001) and instructs the lane to report its result and let the driver transition the plan, so this plan is deliberately left in `pending/`. THREE FINDINGS the plan did not anticipate, each measured rather than reasoned: (1) the SELECTION GATE, not the dispatch branch, is what made the Set's primary case unreachable, so E-01 had to wire it too; (2) RECONSIDER is performed by that gate (skip, no status, no event), not by a deferred re-dispatch, so V-01's 're-dispatched twice' expectation was wrong; (3) the existing drain path does NOT terminate every dead Set, so OQ-01's answer is NO and a narrow actionability test was added (201 dispatches measured, reduced to 1), introducing a fifth typed refusal reason beyond the spec's four. Two out-of-scope test edits are justified in the outcome record.
- 2026-09-06 approved (aw set): status set to approved
- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: PR-301..PR-305 fixed, Readiness go-pending-approval

- 2026-09-06 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-305 all FIXED, no deferrals, no open questions. This plan's OWN review (the earlier entry below was a cross-plan edit made while reviewing 84j8d7, not a review of this plan), and the E-07 added then was re-reviewed here on the same footing as the rest. PR-301 (MED, and the one most likely to have wasted an executor's time): two line citations were inherited stale from kxkc04 and point ~1100 lines from the code they name. The skip-and-reconsider precedent is at `oc_runipd.py:6936-6940`, not `:5829-5833` (worktree-isolation prose), and the drain path is at `:6954`, not `:5847`; both corrected, and the gate now instructs the executor to re-locate a symbol by name rather than implement against whatever sits at a stale offset. PR-302 (MED): E-05 located the AGENTS.md text in `agents_managed_sections` "near engine.py:1146"; it is a string literal at `:1207` inside `agents_pointer_prose` (`:1058`), while `agents_managed_sections` (`:1502`) merely wraps that prose, so the executor would have edited the wrong function. PR-303 (MED): RECONSIDER was specified as "write no status", which is necessary and NOT sufficient, because selection still requires `dependency_status` satisfied and `cascade_dependency_blocked` (`:4039`) runs at the top of every iteration (`:6916`) and can relabel the item deliberately left `queued`; "not terminal" and "reachable again" are different properties and only the second fixes the bug. PR-304 (MED): the AGENTS.md correction had no requirement tying each new assertion to a test, and its neighbouring "Do NOT raise ... orchestrator finalization" instruction would have kept forbidding reports of the cases the mechanism deliberately refuses. PR-305 (LOW): the 95-vs-21 suite figure is stale (re-measured 155 vs 43), and two runner test modules an executor might reach for are outside Scope-Paths. Self-review disclosure in the review record.
- 2026-09-06 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): Cross-plan revision applied while reviewing orchestrator 84j8d7 (finding PR-001, HIGH, fixed in this owning plan per the reviewer's cross-plan rule). Added E-07/V-07: sharing the action decider (E-04) makes agy DECIDE `orchestrate` but agy has no branch that READS it (`orchestrate` absent from `agy_runipd.py`; `:2973` derives only `is_review`; `:4138` calls `execute_item` unconditionally), so E-04 alone would ship a decider whose value agy ignores while V-04's object-identity assertion still passed. Watermark advanced to 07. No other content altered; this plan's own review is separate and has not been performed.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored complete from approved spec 77tr3o. The agy asymmetry was verified by comparing module attributes and calling both action deciders, not by grep alone.
- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make orchestrator retirement actually happen at the end of a real run on both hosts, retry it when a
deferral clears within the run, terminate honestly when it never can, and stop the documentation
asserting a behavior that has never once occurred.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the oc dispatch branch

- [x] E-01 Replace the single `else` with the three-way outcome the two recorded reasons prove is needed: RETIRE (eligible per child 01, transition per child 02); RECONSIDER (children merely unfinished, so write NO status and let the next loop iteration re-test, exactly as an item skipped by the inner selection pass already does at `oc_runipd.py:6936-6940`, where the `for` loop simply `break`s on the first satisfied item and leaves every other item `queued`); TERMINATE (a child reached a non-success terminal state and can never become `executed`, or the child set is unauthored, or the transition itself refused). `finalize-refused` MUST be TERMINATE, not RECONSIDER: `rh5tt6` proves a refusal can be structural, and retrying it every iteration would spin.

  RECONSIDER IS NOT FREE: THE ORCHESTRATOR MUST BECOME SELECTABLE AGAIN, and writing no status is only half of that. The selection pass admits an item only when `dependency_status(item, state)` reports satisfied (`:6937`), and `dependency_depth` treats every non-orchestrator member of the Set as a prerequisite, so a reconsidered orchestrator is re-tested only when its own declared edges allow. Verify that a RECONSIDERED orchestrator is actually re-selected later in the same run rather than merely left unlabelled, because "not terminal" and "reachable again" are different properties and only the second one fixes the bug. Note also that `cascade_dependency_blocked` (`:4039`) propagates `dependency-blocked` over reverse edges to a fixed point and runs at the TOP of each iteration (`:6916`): confirm it does not re-label the orchestrator you deliberately left `queued`, which would silently undo RECONSIDER through a path E-01 never touches.
  - Depends on: none
  - Expected outcome: an orchestrator whose children finish mid-run is retired in that same run, demonstrably RE-SELECTED after being reconsidered rather than merely left unlabelled; one whose child failed terminally is marked terminal with the real reason; neither spins.
  - Execution state: performed

- [x] E-02 Make the four refusal reasons distinguishable in the durable record (spec R-9): "children exist and are unfinished: <ids with their statuses>", "no children of Set <setid> exist", "child table declares unauthored rows", "transition refused: <reason>". Today all four collapse into `dependency-blocked` plus an `unsatisfied_dependencies` list that was EMPTY for both observed cases, producing a run summary reading "dependency-blocked (unmet dependencies)" while naming no dependency. Keep the `orchestrator-deferred` event name for continuity but make its `reason` field carry the specific cause.
  - Depends on: E-01
  - Expected outcome: `events.jsonl` and the run report name the actual cause; no summary claims an unmet dependency it cannot name.
  - Execution state: performed

- [x] E-03 Verify, do not assume, that leaving an orchestrator RECONSIDERABLE cannot hang a run (spec R-8). The drain path (`oc_runipd.py:6954`, the `if runnable is None:` branch) already terminates a run whose remaining items are unsatisfiable: outside a wind-down it labels every remaining `queued` item `dependency-blocked` with per-edge reasons (`dependency_status_detailed`, `:6965-6970`) and then `break`s. Confirm an orchestrator left reconsiderable with permanently-unfinishable children reaches that path and is labelled there with a reason naming the dead children. If it does not, add the termination rather than reintroducing the premature terminal write.

  CHECK THE WIND-DOWN INTERACTION, which is the one shape that could still hang or lie: when a stop was requested, the same branch deliberately does NOT relabel the remainder (spec R22 forbids a fabricated disposition) and leaves items `queued`. Confirm that a reconsidered orchestrator under a wind-down exits cleanly as `queued` rather than spinning, and that the run does not then report it as blocked by a dependency it cannot name. Report which of the two branches your evidence exercised.
  - Depends on: E-01
  - Expected outcome: pasted evidence that a run with a dead child terminates rather than looping, with the reason naming the child, plus a statement of whether the existing drain path sufficed or a termination was added, and confirmation that the wind-down path neither spins nor fabricates a disposition.
  - Execution state: performed

### Task group 2: host symmetry and the documented claim

- [x] E-04 Give the agy runner the `orchestrate` action through SHARED code. Move the action decision (`oc_runipd.action_for`, `:2450-2463`) into `runner_shared.py` and have BOTH hosts import it, rather than adding a second copy to `agy_runipd.py`: the anti-re-fork discipline from `2r306y`/`818uru` is binding, and `agy_runipd.py:1313` already notes that agy losing `kind` breaks `action_for`. Ensure agy's queue entries carry `kind` so the shared decider can see it.
  - Depends on: none
  - Expected outcome: `agy` and `oc` return the SAME action for the same (kind, status) pair, verified by asserting the two call the same object rather than by comparing outputs alone.
  - Execution state: performed

- [x] E-07 Add the agy DISPATCH BRANCH that acts on the `orchestrate` action, which sharing the decider does NOT accomplish. E-04 makes agy DECIDE `orchestrate`; agy then IGNORES it. Verified at HEAD `844d195c`: the token `orchestrate` appears nowhere in `agy_runipd.py` outside the unrelated `orchestrate_isolation` import, `execute_item` derives only `is_review = action == "review"` (`:2973`), and the queue loop calls `execute_item` unconditionally (`:4138`). So without this item E-04 ships a decider returning a value into a host that spends an agent turn anyway, which is the very failure spec R-10 exists to prevent, and V-04's object-identity assertion would still PASS. Route agy's `orchestrate` items through the SAME shared retire/reconsider/terminate outcome E-01 and E-02 build for oc; do not fork a second copy of that logic into `agy_runipd.py`.
  - Depends on: E-01, E-02, E-04
  - Expected outcome: an approved orchestrator dispatched by `aw agy run` is retired, reconsidered, or terminated by the shared path with NO agent turn and no `execute_item` call, matching oc's outcome and not merely oc's decision.
  - Execution state: performed

- [x] E-05 Correct the false claim in the managed AGENTS.md block (spec R-11). `AGENTS.md:42` states an orchestrator "self-finalizes once every child of its Set reached `executed` ... so an Order-0 parent in the queue is correct and needs no human step" and instructs agents NOT to raise orchestrator finalization. That was never true: 0 successes in 103 run records. EDIT THE GENERATOR, not the rendered file: a hand-edit to `AGENTS.md` is overwritten on the next install. THE EXACT LOCATION, verified rather than approximated: the sentence is a string literal at `engine.py:1207`, inside `agents_pointer_prose` (defined at `:1058`), in the paragraph headed "The runners own ordering, isolation, and orchestrators (do NOT re-derive this)". `agents_managed_sections` (`:1502`) merely WRAPS that prose into the `aw:pointer` section (`:1519`), so editing it is not where the text lives. Regenerate via `merge_aw_block` (`:1587`).

  THE SURROUNDING PARAGRAPH MUST STAY COHERENT, which is more than swapping one clause. That paragraph exists to STOP agents from raising settled runner behavior, and its closing instruction (`engine.py:1218-1219`, rendered at `AGENTS.md:43`) explicitly lists "orchestrator finalization" among the things an agent must NOT raise because "those are solved". If the mechanism now genuinely works, that instruction can stay only for the cases the tests demonstrate; the refusal cases (unauthored child rows, a refusing transition) are things an agent legitimately MAY raise, so the sentence must not forbid reporting them. Say what the runner does, say what it deliberately does NOT do, and do not replace one overstatement with another.
  - Depends on: E-01, E-04
  - Expected outcome: the managed block describes behavior that the tests in E-06 actually demonstrate, the neighbouring "do NOT raise" instruction no longer forbids reporting a case the mechanism deliberately refuses, and a re-render is idempotent.
  - Execution state: performed

- [x] E-06 Extend the test modules with end-to-end dispatch coverage: an orchestrator retired mid-run once its last child completes; an orchestrator RECONSIDERED rather than terminally marked when a child is still running; a dead-child run that terminates with a naming reason; the agy host taking `orchestrate` rather than `execute` for an approved orchestrator; and the four distinct reasons appearing in `events.jsonl`. Cover BOTH hosts for the action decision, since a one-host fix passes every oc-only test (the failure mode `818uru` recorded).
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: tests that fail if either host regresses, and specifically if agy reverts to agent-executing an orchestrator.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Run the suite BARE (`python3 -m pytest`).
- `AGENTS.md`'s managed block is GENERATED from `engine.py`; edit the generator and re-render with `engine.merge_aw_block`, never the file directly. Verified this session: a hand-edit is replaced on re-render, and re-rendering after a generator edit is idempotent.
- The oc and agy runner suites are severely asymmetric, and the least-covered symbols are the most diverged. E-06's both-hosts requirement exists because of that measured gap. RE-MEASURED at review time, because the figure carried from `5e4sb6`'s E-01 (95 vs 21) is stale: `tests/test_oc_runipd.py` has 148 `def test_` and `tests/test_oc_runipd_cli.py` 7, versus `tests/test_agy_runipd_cli.py` 39 and `tests/test_agy_runipd_shim.py` 4. The ratio narrowed but the asymmetry stands (155 vs 43), and the conclusion is unchanged. Note `tests/test_oc_runipd_cli.py` and `tests/test_agy_runipd_shim.py` are NOT in this plan's `Scope-Paths`: if a dispatch case belongs in one of them, that is an out-of-scope edit to make and JUSTIFY at finalize, not a reason to force the test into the wrong module.
- An item merely SKIPPED by the inner selection pass writes no status and IS reconsidered; ordering is already correct right up until something is LABELLED. The bug is the labelling.

## Findings

| # | Sev | Where | Finding | Evidence |
|---|-----|-------|---------|----------|
| F-1 | HIGH | `oc_runipd.py:7015` | The deferral writes a TERMINAL status, so the orchestrator is never reconsidered even when its children finish in the same run. | `TERMINAL_STATES:254-272`; selection filter `:4071`, `:6919` |
| F-2 | HIGH | `oc_runipd.py:7014` | One `else` covers two unrelated failures, so `kxkc04`'s "leave it queued" fix would make the `finalize-refused` case spin forever. | recorded reasons `not-all-children-executed` and `finalize-refused` on one run |
| F-3 | HIGH | `agy_runipd.py:1783` | agy has NO orchestrate action; it would agent-execute an approved orchestrator. | `agy.determine_action('approved')`=`execute` vs `oc.action_for('orchestrator','approved')`=`orchestrate`; all three symbols absent from agy |
| F-4 | MED | `AGENTS.md:42` | Asserts self-finalization works and tells agents not to raise it; 0 successes in 102 runs. Text lives in `engine.py`, so a direct edit would be reverted. | `grep -rh orchestrator-finalized ... \| wc -l` = 0 |
| F-5 | LOW | `5e4sb6` event | The run summary reads "unmet dependencies" while naming none, because the no-children branch returns `(False, [])`. | `unfinished_children: []` in the event payload |
| F-6 | MED | `oc_runipd.py:4039`, `:6916` | RECONSIDER needs the orchestrator to be RE-SELECTABLE, which writing no status does not by itself guarantee. Selection requires `dependency_status` satisfied (`:6937`), and `cascade_dependency_blocked` runs at the TOP of every iteration and propagates `dependency-blocked` over reverse edges to a fixed point, so it could relabel the item E-01 deliberately left `queued` through a path E-01 never touches. "Not terminal" and "reachable again" are different properties; only the second fixes the bug. | source read at review time |
| F-7 | MED | citations | Two line references were inherited stale from `kxkc04` and point at unrelated code roughly 1100 lines away: the skip-and-reconsider precedent is at `:6936-6940`, not `:5829-5833` (which is worktree-isolation prose), and the drain path is at `:6954`, not `:5847`. An executor following them would read the wrong function while believing the plan had verified it. | `sed -n '5829,5833p'` vs `grep -n "for item in sorted(queued"` |
| F-8 | MED | `engine.py:1207` | E-05 located the false claim in `agents_managed_sections` "near `engine.py:1146`". The sentence is actually a string literal at `:1207` inside `agents_pointer_prose` (`:1058`); `:1146` is unrelated spec-status prose, and `agents_managed_sections` (`:1502`) only wraps the prose into a section. The paragraph's closing "Do NOT raise ... orchestrator finalization" instruction (`:1218-1219`) also needs revising, since the refusal cases are things an agent legitimately MAY report. | source read |
| F-9 | LOW | test suites | The cited 95-vs-21 suite asymmetry is stale. Re-measured: 148 + 7 oc tests versus 39 + 4 agy (155 vs 43). The asymmetry and the conclusion stand; the number does not. Also `tests/test_oc_runipd_cli.py` and `tests/test_agy_runipd_shim.py` are outside `Scope-Paths`. | `grep -c "def test_"` per module |

## Proposed changes (ordered, validatable)

1. E-01 three-way dispatch outcome replacing the single terminal write.
2. E-02 typed, distinguishable refusal reasons in the durable record.
3. E-03 verify the drain path terminates a dead Set.
4. E-04 shared action decider, giving agy `orchestrate`.
5. E-07 agy's dispatch branch that ACTS on that action (E-04 alone leaves it ignored).
6. E-05 correct the generator-owned AGENTS.md claim.
7. E-06 both-host end-to-end tests.

## Deferred / out of scope (with reason)

- The general `dependency-blocked`-is-terminal defect for ORDINARY items and the all-or-nothing drain break: `nueip1`. Same code region, different rule; fixing it here would widen this Set beyond its spec.
- `EXECUTION_SUCCESS_STATES` accepting `substantially-complete` for dependency EDGES: spec Section 4. It is why `xdr83v` was dispatched against an unlanded prerequisite, and it deserves its own item.
- Actually retiring `rh5tt6`, `h0zljh`, `5e4sb6`, `3m0urk`: only `rh5tt6` qualifies under these rules, and doing it is a consequence of the fix rather than part of it.

## Scope check

- Over-scope: `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` are in scope only for the dispatch and action-decision cases E-06 adds; do not refactor those modules.
- Under-scope: none. This child makes the Set's mechanism reachable from a real run, which is the point at which the whole Set becomes verifiable.

## Required tests / validation

`python3 -m pytest` bare, plus the end-to-end demonstration E-06 requires. Baseline measured in the executing worktree at execution time and pasted; compare failing NODE IDS, not totals. Note the honest limit: a fully unattended end-to-end proof needs a real multi-item run, which is expensive; E-06's dispatch-level tests plus a single scripted run over a synthetic Set are the accepted evidence, and that limit must be stated at finalize rather than glossed.

## Spec / documentation sync

Implements spec `77tr3o` R-7, R-8, R-9, R-10, R-11. E-05 corrects the managed AGENTS.md block via `engine.py`.

## Open questions

### OQ-01: does the drain path already terminate an orchestrator left reconsiderable with dead children?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: THE APPROACH IS RESOLVED by the maintainer 2026-09-06; the empirical answer is still E-03's to obtain. Asked whether to verify the existing drain path or add a dedicated reconsideration cap regardless, he chose VERIFY FIRST and add a termination ONLY IF the existing net does not cover this case, explicitly to avoid building a second mechanism that duplicates a job something else already does. So E-03 keeps its two-branch shape and must REPORT which branch it took. It is not blocking because either branch proceeds; it remains a question rather than an assumption because `kxkc04` warns against assuming it ("Verify that explicitly rather than assuming it") and because being wrong means a hung unattended run, which is worse than the lingering orchestrator this Set fixes.
- EMPIRICAL ANSWER (E-03, 2026-09-06): **NO for the general case, so a termination WAS added.** The
  branch taken is therefore "add the termination", and the maintainer's verify-first instruction was
  honored: the existing net was tested BEFORE anything was built.
  * WHERE THE DRAIN PATH DOES SUFFICE: when a child is in the queue in a non-success terminal state, the
    run terminates on its own (`rc=1`, 0 agent turns, reason naming the dead child). No new mechanism was
    added for that case.
  * WHERE IT CANNOT: when the unfinished child is unfinished ON DISK but ABSENT from this run's queue (or
    already terminal in it without reaching `executed` on disk), the orchestrator remains SELECTABLE, and
    the drain path is only reached when NOTHING is selectable. So the drain path is structurally
    incapable of catching it. MEASURED: 201 dispatches without termination before the fix, 1 after.
  * WHAT WAS ADDED, kept as narrow as the finding: an ACTIONABILITY test inside the existing decision
    (not a second mechanism, not a retry cap, no new loop state). A child counts as actionable only when
    this run will still act on it; otherwise the verdict is TERMINATE with the new typed reason
    `children-not-in-this-run`. That reason is a FIFTH beyond the spec's four, recorded here because the
    spec's four could not express a fact the measurement produced.
  * Full transcripts: `evidence/e03_drain_probe.py` (all three branches, including the wind-down) and
    `evidence/e03_spin_probe.py` (the 201-vs-1 measurement). Pinned by `ADeadSetTerminatesInsteadOfLooping`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a scripted run over a synthetic Set where the orchestrator is dispatched BEFORE its last child finishes, showing it is reconsidered and then RETIRED in the same run. Paste the queue/status transitions, not just the final state, so the reconsideration is visible rather than inferred, and specifically show the orchestrator being RE-SELECTED on a later iteration (an item left unlabelled but never re-dispatched has not been reconsidered, it has been forgotten). Also show `cascade_dependency_blocked` did not relabel it in the interim: paste its status at the top of the iteration after the reconsideration.
  - Observed evidence: A CORRECTION TO THE ITEM'S PREMISE, found by running it. The plan expected reconsideration to be
    performed by the DISPATCH branch (deferred, then re-dispatched). It is not. `run_queue` has TWO
    deferral points for an `orchestrate` item and the FIRST one fires: the SELECTION GATE
    (`dependency_status`) reports UNSATISFIED on a RECONSIDER verdict, so the inner selection pass
    SKIPS the item, leaving it `queued` with no status, no event, and no dispatch at all. So "RE-SELECTED
    on a later iteration" is the right property, but the first consideration never reaches the
    dispatcher, and a dispatch count of 2 would be wrong to demand. Evidence below is the per-iteration
    trace (`evidence/e01_reselection_probe.py`), which shows the skip, the child's turn, and the
    orchestrator's later consideration and retirement, plus the cascade's no-op at each iteration top:

        1. --- iteration 1 top: statuses={'orc100': 'queued', 'chi100': 'queued'} (cascade changed nothing)
        2. AGENT TURN(chi100)
        3. --- iteration 2 top: statuses={'orc100': 'queued', 'chi100': 'executed'} (cascade changed nothing)
        4. selection-gate(orc100): satisfied=True missing=[]
        5. DISPATCH(orc100): outcome=retire reason=''
        6. --- iteration 3 top: statuses={'orc100': 'executed', 'chi100': 'executed'} (cascade changed nothing)

        === run_queue rc=0
            orc100   status='executed'
            chi100   status='executed'

    Iteration 1 leaves `orc100` `queued` (not `dependency-blocked`), iteration 2 re-considers and
    retires it: RECONSIDERED then RETIRED IN THE SAME RUN, which the pre-change terminal write made
    impossible. F-6's cascade concern is answered directly: `cascade_dependency_blocked` "changed
    nothing" at every iteration top, including the one after the reconsideration, because it reads only
    DECLARED `dependencies` edges and an orchestrator's child-set relationship is not one.

    A SECOND FINDING, which changed the implementation. Wiring only the dispatch branch would have left
    the Set's PRIMARY use case unreachable. `initialize_run` derives an already-`executed` child's RUN
    status as `reviewed`, and the gate's old queue-scoped check counted that as unfinished, so for
    `aw oc run <setid>` on a Set complete on disk the gate BLOCKED and the dispatcher was never reached
    (`evidence/e01_setid_run_probe.py`, before the gate fix):

        === SELECTION GATE on orcaaa: satisfied=False missing=['executed:chiaaa']
        === ON-DISK VERDICT: eligible=True reason='eligible'
            => UNREACHABLE: the gate BLOCKS a Set that IS complete on disk

    After wiring the gate to the same shared decision, the same probe reports:

        === the REAL queue `initialize_run` built
            orcaaa  action='orchestrate'  run-status='queued'  initial='approved'  kind='orchestrator'
            chiaaa  action='execute'  run-status='reviewed'  initial='executed'  kind='child'
        === SELECTION GATE on orcaaa: satisfied=True missing=[]
        === ON-DISK VERDICT: eligible=True reason='eligible'
            => REACHABLE: the gate admits it and the dispatch branch retires it

    Pinned by `TheSelectionGateUsesTheSameDecision` (4 tests) and `AnOrchestratorIsRetiredMidRun` (3),
    and proven load-bearing by SABOTAGE 4 (revert the gate -> the cross-run test FAILS).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `events.jsonl` lines for all four refusal causes, each naming its specific reason, and show that the unfinished-children case names the ids AND their actual statuses. Also show no summary line claims an unmet dependency without naming one (the `5e4sb6` defect).
  - Observed evidence: FIVE causes, not four. E-03's measurement forced a fifth
    (`children-not-in-this-run`); see V-03. Real `events.jsonl` lines, one dispatch per cause:

        {"detail": "Set 'nokids' has no child plans on disk; retirement is gated on children being executed, and a Set with none has demonstrated nothing", "event": "orchestrator-deferred", "id6": "orcn01", "reason": "no-children", "setid": "nokids", "status": "dependency-blocked", "terminated": true, "unauthored_rows": [], "unfinished_children": []}
        {"detail": "Set 'unauth': the orchestrator's child table declares row(s) '03+' that resolve to no plan, so the child set is not fully authored", "event": "orchestrator-deferred", "id6": "orcu01", "reason": "unauthored-child-rows", "setid": "unauth", "status": "dependency-blocked", "terminated": true, "unauthored_rows": ["03+"], "unfinished_children": []}
        {"detail": "Set 'deadst' can never complete in this run: child(ren) chid01 (failed-safely) reached a non-success terminal state, so they cannot become executed", "event": "orchestrator-deferred", "id6": "orcd01", "reason": "children-terminally-failed", "setid": "deadst", "status": "dependency-blocked", "terminated": true, "unauthored_rows": [], "unfinished_children": [["chid01", "failed-safely"]]}
        {"detail": "Set 'strand' has 1 child(ren) not yet executed that this run will NOT act on: chis01 (approved). Nothing in this run can finish them, so waiting would repeat this decision unchanged; run them (or the whole Set) and the orchestrator is retired then", "event": "orchestrator-deferred", "id6": "orcs01", "reason": "children-not-in-this-run", "setid": "strand", "status": "dependency-blocked", "terminated": true, "unauthored_rows": [], "unfinished_children": [["chis01", "approved"]]}
        {"detail": "retirement transition refused: REFUSED: synthetic structural refusal", "event": "orchestrator-deferred", "id6": "orcf01", "reason": "finalize-refused", "setid": "refuse", "status": "dependency-blocked", "terminated": true, "unauthored_rows": [], "unfinished_children": []}

    Five DISTINCT `reason` values, and every `detail` substantiates its own reason: the unauthored case
    quotes the literal token `'03+'`, and both child-related cases carry `[id, ACTUAL STATUS]` pairs
    (`["chid01","failed-safely"]`, `["chis01","approved"]`) rather than bare ids.

    THE `5e4sb6` DEFECT, addressed on the exact axis it occurred. Its event carried
    `unfinished_children: []` while the summary read "dependency-blocked (unmet dependencies)", naming
    nothing. The per-item write is now:

        [nokids] item unsatisfied_dependencies=[] reason=no-children
        [unauth] item unsatisfied_dependencies=[] reason=unauthored-child-rows
        [deadst] item unsatisfied_dependencies=['executed:chid01'] reason=children-terminally-failed
        [strand] item unsatisfied_dependencies=['executed:chis01'] reason=children-not-in-this-run
        [refuse] item unsatisfied_dependencies=[] reason=finalize-refused

    Where a child is nameable the list NAMES it, so the summary can substantiate its claim. Where the
    list is legitimately empty (no children exist; the transition refused) there is no dependency to
    name, and the typed `orchestrator_refusal_reason` carries the real cause instead of an empty list
    being rendered as an unmet dependency. Pinned by
    `TheFourRefusalReasonsAreDistinguishable::test_a_terminated_item_never_claims_a_dependency_it_cannot_name`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a run where a child reaches a non-success terminal state, showing the run TERMINATES (not loops) and the orchestrator's recorded reason names the dead child. State plainly whether the existing drain path handled it or you added the termination.
  - Observed evidence: OQ-01 ANSWERED EMPIRICALLY, AND THE ANSWER IS "NO": the existing drain path did NOT suffice, so a
    termination WAS added. The maintainer's instruction was to verify the existing net first and add a
    termination only if it did not cover the case; it did not.

    WHICH BRANCH THE EVIDENCE EXERCISED, all three. `evidence/e03_drain_probe.py` drives the real
    `run_queue` with an iteration budget, so a spin fails loudly instead of hanging:

        === DEAD child (failed-safely): orchestrator must TERMINATE
            run_queue RETURNED rc=1  (it TERMINATED; it did not loop)
            orc001   action=orchestrate status='dependency-blocked'   reason=children-terminally-failed
            chi001   action=execute     status='failed-safely'
            agent turns spent (execute_item calls): 0

        === WIND-DOWN (level 2) with a LIVE child: must exit clean, NOT spin, NOT fabricate
            run_queue RETURNED rc=0  (it TERMINATED; it did not loop)
            orc001   action=orchestrate status='queued'
            chi001   action=execute     status='queued'
            agent turns spent (execute_item calls): 0

    The DEAD-child branch terminates with the reason naming the dead child, spending no agent turn. The
    WIND-DOWN branch exits rc=0 leaving both items `queued`: it neither spins nor fabricates a
    disposition (spec R22), and it does not report a dependency it cannot name.

    THE SPIN I MEASURED, which is why a termination was added rather than the drain path trusted. The
    naive rule (RECONSIDER whenever no child is terminally dead) hangs on a shape the drain path
    structurally cannot catch: the drain is reached only when NOTHING is selectable, and this
    orchestrator stays selectable forever. `evidence/e03_spin_probe.py` BEFORE the fix:

        verdict: SPUN: SPIN DETECTED: dispatched the orchestrator 201 times without the run terminating
        orchestrator dispatched 201 time(s)
        events written: 200

    AFTER adding the actionability gate (a child counts as actionable only when it is in THIS RUN'S queue
    in a non-terminal state), the same probe:

        verdict: TERMINATED
        run_queue rc=1
        orchestrator dispatched 1 time(s)
        orc001   status='dependency-blocked'   reason=children-not-in-this-run
        EVENT {"detail": "Set 'spinset' has 1 child(ren) not yet executed that this run will NOT act on: chib03 (approved). Nothing in this run can finish them, ...", "reason": "children-not-in-this-run", "terminated": true, ...}

    201 dispatches to 1. Waiting is bounded for a reason that follows from the scheduler rather than from
    hope: `queue_sort_key` ranks `dependency_depth` first and an orchestrator's depth counts every Set
    member as a prerequisite, so an ACTIONABLE child is always dispatched before the orchestrator is
    re-considered; each iteration therefore either advances that child or gives it a terminal status, and
    the latter flips the decision to TERMINATE. Pinned by
    `ADeadSetTerminatesInsteadOfLooping` (2 tests, both budget-guarded) and proven load-bearing by
    SABOTAGE 5 (revert the actionability gate -> the spin test FAILS).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a Python session asserting `agy.<action decider> is oc.<action decider>` (the same object, proving shared code rather than parity by coincidence) and showing both return `orchestrate` for an approved orchestrator. Paste an agy queue entry showing it carries `kind`. This item proves the DECISION only; the dispatched OUTCOME is V-07's, and this item must NOT be read as establishing host parity on its own.
  - Observed evidence: a real Python session against the shipped modules:

        >>> object identity (shared CODE, not parity by coincidence)
            agy.action_for is oc.action_for is rs.action_for            -> True
            agy.determine_action is oc.determine_action is rs.…         -> True
            agy.dispatch_orchestrator_item is oc.… is rs.…              -> True
            agy.action_for.__module__ = agent_workflows.runner_shared
        >>> both return `orchestrate` for an approved orchestrator
            agy.action_for('orchestrator','approved') -> orchestrate
            oc.action_for('orchestrator','approved')  -> orchestrate
        >>> and an agy queue entry carrying `kind`
            {"set": "kindset", "file": ".aw/records/plans/pending/20260906-kindset-00-orck01-o.ipd.md", "status": "approved", "order": 0, "dependencies": [], "kind": "orchestrator", "from_backlog": null}
            agy PlanRecord._fields (must NOT contain 'kind', per 818uru) -> ('id6', 'setid', 'status', 'order', 'path', 'rel_path', 'dependencies', 'dependency_error', 'from_backlog')

    Measured before this change for contrast: `agy.determine_action('approved')` returned `'execute'`
    while `oc.action_for('orchestrator','approved')` returned `'orchestrate'`, and `action_for` was
    absent from `agy_runipd` entirely.

    `kind` reaches agy WITHOUT touching its `PlanRecord`, whose distinctness `818uru` pinned with a test
    asserting it has no `kind` field; the field list above shows that invariant intact. It is carried
    through the MANIFEST instead, read via the one shared `_read_kind` (see decision 01-pgq326-D2).

    THIS ITEM PROVES THE DECISION ONLY, and the plan's warning was justified: SABOTAGE 3 shows this exact
    identity assertion still PASSING while agy ignores the value entirely. See V-07. Also note the
    decider's own immunity: reverting agy's QUEUE-BUILD line left all four tests in
    `TheActionDecisionIsSHAREDCode` passing until I added
    `test_the_QUEUE_BUILD_derives_orchestrate_on_both_hosts`, which observes the `action` actually frozen
    onto the queue entry (the value the dispatch loop reads). SABOTAGE 1 now fails against it.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the AGENTS.md diff, paste the `engine.py` generator change (showing it edits the string literal at `:1207` inside `agents_pointer_prose`, not a hand-edit of the rendered file), and paste a second `merge_aw_block` render showing it is IDEMPOTENT (no further change). Quote the new sentence and state what it does NOT claim, so the correction is not itself an overstatement. Then map EACH factual assertion in the new text to the specific E-06 test that demonstrates it; any assertion with no test behind it must be removed rather than shipped, because a documented claim no test exercises is the exact defect this Set exists to correct. Finally quote the neighbouring "Do NOT raise ... orchestrator finalization" instruction as it now reads and confirm it does not forbid reporting the cases the mechanism deliberately REFUSES.
  - Observed evidence: THE GENERATOR WAS EDITED, NOT THE RENDERED FILE. `git diff --numstat` shows
    `agent_workflows/engine.py` changed (the string literals inside `agents_pointer_prose`, whose
    location F-8 corrected to `:1207`) and `AGENTS.md` changed only as its RE-RENDER, produced by calling
    `engine.merge_aw_block`. The AGENTS.md diff is 3 insertions / 2 deletions confined to the
    "### The runners own ordering, isolation, and orchestrators" paragraph.

    IDEMPOTENT, checked by rendering twice:

        IDEMPOTENT: True     # merge_aw_block(current) == merge_aw_block(merge_aw_block(current))

    THE NEW SENTENCE, quoted:

        "an ORCHESTRATOR is not agent-executed, and once every child of its Set is `executed` ON DISK
         the runner retires it to `executed` in that same run, on BOTH hosts, spending no agent turn,
         so an Order-0 parent in the queue is correct and needs no human step"

    WHAT IT DOES NOT CLAIM, stated so the correction is not itself an overstatement: it does not claim
    retirement always succeeds, does not claim a refusal is a bug, does not claim anything about the
    AGENT-DRIVEN path (where an orchestrator's `E-*`/`V-*` items are still real work), and does not name
    `_set_children_all_executed`/`finalize_orchestrator` as the mechanism (the old text cited both as
    evidence for a rollup that had never once run). It says `executed` ON DISK deliberately, because
    that, not queue membership, is what the predicate reads.

    THE NEIGHBOURING INSTRUCTION AS IT NOW READS:

        "Do NOT raise file overlap, queue order, or an Order-0 parent's PLACEMENT in the queue: those
         are solved, and asserting otherwise is a claim about code you have not read."

    "orchestrator finalization" is GONE from that list, and the preceding paragraph now says the refusals
    "ARE worth reporting to a human, because each needs a human act". So the instruction no longer
    forbids reporting a case the mechanism deliberately refuses, which was the contradiction the gate
    flagged. Pinned by
    `TheDocumentedClaimMatchesTheCode::test_the_do_not_raise_instruction_no_longer_forbids_reporting_a_REFUSAL`.

    EACH ASSERTION MAPPED TO THE TEST THAT DEMONSTRATES IT, asserted mechanically by
    `test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module` (which fails if the claim is
    absent from the prose, so the prose and the tests cannot drift apart):

    | assertion in the new text | test that demonstrates it |
    |---|---|
    | "retires it" (retirement actually happens) | `AnOrchestratorIsRetiredMidRun` |
    | "same run" | `AnOrchestratorIsRetiredMidRun::test_reconsidered_then_retired_in_the_same_run_on_both_hosts` |
    | "ON DISK" (disk, not queue, decides completeness) | `TheSelectionGateUsesTheSameDecision` + `AnOrchestratorIsRetiredMidRun` |
    | "BOTH hosts" | `TheAgyHostActsOnTheDecision` |
    | "no agent turn" | `TheAgyHostActsOnTheDecision::test_agy_retires_an_approved_orchestrator_with_NO_agent_turn` |
    | "REFUSES" + "unauthored" (row) | `TheFourRefusalReasonsAreDistinguishable` |
    | "children this run cannot finish" | `ADeadSetTerminatesInsteadOfLooping` |

    No assertion in the new text lacks a test; the mapping test enumerates all seven.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the bare suite summary. Then paste a SABOTAGE per host: revert agy's action decision to `determine_action` and show the agy test FAILS; reinstate the terminal-status write and show the reconsideration test FAILS. Both are required because a one-host fix passes every oc-only test.
  - Observed evidence: THE BARE SUITE (`python3 -m pytest`, no added flags), final run:

        31 failed, 5458 passed, 3 skipped, 2 xfailed in 114.29s (0:01:54)

    BASELINE MEASURED IN THIS WORKTREE at the start, with my changes stashed:

        31 failed, 5431 passed, 3 skipped, 2 xfailed in 124.41s (0:02:04)

    COMPARED BY FAILING NODE ID, not by totals, as the plan requires:

        === node-id set vs baseline:
        IDENTICAL to baseline: ZERO regressions

    So all 31 failures pre-exist and NONE is mine; +27 net passing. The 31 are two environmental
    families, both properties of executing inside a managed lane rather than defects: (a) `begin`/
    `finalize` refusals, because this lane runs with `AW_EXECUTION_ROLE=worker` (verified:
    `worker_role_active(os.environ) is True`), which is the deliberate `wtiso-03` guard; and (b)
    `tests/test_run_viewer.py`, because a linked worktree resolves `.aw/state` relative to cwd (backlog
    `dh0uno`, the same measured effect `run_suite_check`'s docstring records).

    The new module alone: `python3 -m pytest tests/test_orchestrator_retirement.py` -> `112 passed`
    (was 105 before this child added the dispatch section).

    SABOTAGE, ONE PER HOST, full transcript in `evidence/sabotage_output.txt`. The harness reads pytest's
    OWN exit status (an earlier version piped into `tail` and read tail's status, which made every verdict
    read "PASSED" -- fixed, because a self-defeating harness is worse than none):

        SABOTAGE 1 (agy host): revert agy's queue-build to determine_action
        >>> SABOTAGE 1: test FAILED under sabotage (pytest rc=1)  <-- GOOD: property really pinned

        SABOTAGE 2 (oc host): force RECONSIDER back to a TERMINAL write
        >>> SABOTAGE 2 (RECONSIDER branch): test FAILED under sabotage (pytest rc=1)  <-- GOOD
        >>> SABOTAGE 2 (end-to-end, expected IMMUNE: child runs first by depth): test PASSED

        SABOTAGE 4 (oc selection gate): revert to the queue-scoped predicate
        >>> SABOTAGE 4: test FAILED under sabotage (pytest rc=1)  <-- GOOD

        SABOTAGE 5 (spin): revert the actionability gate
        >>> SABOTAGE 5: test FAILED under sabotage (pytest rc=1)  <-- GOOD

    Each file is restored from a pre-sabotage COPY and verified byte-identical with `cmp` (not
    `git diff --quiet`, which would false-alarm since these files legitimately differ from HEAD), and the
    final `grep -rn SABOTAGE agent_workflows/` prints "(none: clean)".

    TWO SABOTAGES DELIBERATELY DO NOT BITE, labelled as immune controls rather than hidden. The
    end-to-end mid-run test is immune to SABOTAGE 2 because `dependency_depth` dispatches the child FIRST
    (measured: child depth 0, orchestrator depth 1), so that run never reaches the RECONSIDER branch --
    which is exactly how the sabotage revealed that the branch needed its own direct test
    (`test_an_unfinished_child_yields_RECONSIDER_and_never_a_TERMINAL_disposition`, which does fail). Both
    are run above so the asymmetry is visible rather than asserted in prose.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste an `aw agy run` dispatch of an approved orchestrator over a synthetic Set showing the DISPATCHED OUTCOME (retired, reconsidered, or terminated) with NO agent turn: show that `execute_item` was not called and no session/prompt artifact was written for that item. Then paste a SABOTAGE proving this is not the decider test in disguise: leave the shared decider returning `orchestrate` but REMOVE agy's dispatch branch, and show V-04's identity assertion still PASSES while this item's test FAILS. That contrast is the whole point of separating the two.
  - Observed evidence: THE DISPATCHED OUTCOME on the agy host, through the real `agy_runipd.run_queue`:

        === `aw agy run` over a synthetic Set (orchestrator only in queue, child executed on disk)
            run_queue rc=0
            orc500  action=orchestrate  status='executed'
            execute_item CALLS (agent turns): []  <-- must be []
            sessions/ artifacts: (dir not created)
            prompts/ artifacts: (dir not created)
            events:
               {"detail": "Set 'agyset' is complete on disk: all 1 child(ren) are executed (chi500), and every row of the orchestrator's child table resolves to a plan", "event": "orchestrator-finalized", "id6": "orc500", "reason": "retire", "setid": "agyset"}

    RETIRED, with `execute_item` never called and NO session or prompt artifact written (both directories
    were never even created). Before this item, agy would have spent a full agent turn here.

    THE SABOTAGE THAT PROVES THIS IS NOT V-04 IN DISGUISE. The shared decider is left untouched (still
    returning `orchestrate`) and ONLY agy's dispatch branch is removed:

        SABOTAGE 3 (V-07, THE CONTRAST): leave the shared decider returning
        'orchestrate' but REMOVE agy's dispatch BRANCH.
        --- FIRST: does the DECIDER identity assertion (V-04) still pass?
        >>> SABOTAGE 3 / V-04 decider identity: test PASSED under sabotage
        --- SECOND: does the agy BRANCH test (V-07) fail?
        >>> SABOTAGE 3 / V-07 branch: test FAILED under sabotage (pytest rc=1)  <-- GOOD
        --- THIRD: and does agy actually spend an agent turn without the branch?
        >>> SABOTAGE 3 / V-07 no-agent-turn: test FAILED under sabotage (pytest rc=1)  <-- GOOD

    Exactly the contrast the plan demanded: V-04's identity assertion PASSES while both V-07 tests FAIL.
    That is the measured proof that E-04 alone would have shipped a decider whose value agy ignores, and
    it is why the two items are separate. V-04 must not be read as evidence of host parity.

    The outcome logic is NOT forked into `agy_runipd`: `test_neither_host_forks_the_outcome_logic` asserts
    by AST that neither host defines `dispatch_orchestrator_item` or `decide_orchestrator_dispatch`, and
    the branch test asserts agy's branch calls the shared performer and `continue`s (so control cannot
    fall through to `execute_item`).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. This child touches the most contended files in the repo, so stay strictly inside
`Scope-Paths` and do not refactor the runner suites beyond the cases E-06 adds. Do not expand scope
casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the
two-way scope reconciliation at finalize (`aw ipd finalize` refuses without a `--scope-reason` per
out-of-scope path and a `--scope-ack` per declared-but-unmodified path). `tests/test_oc_runipd_cli.py`
and `tests/test_agy_runipd_shim.py` are NOT in the fence: if a case belongs there, that is an
out-of-scope edit to justify, not a reason to force the test into the wrong module.

VERIFY EVERY LINE NUMBER BEFORE YOU RELY ON IT. Review found two citations inherited stale from
`kxkc04`, pointing ~1100 lines from the code they name (F-7), and one wrong generator location (F-8).
They are corrected in the text above, but the repo moves: if a cited line does not contain what the plan
says it contains, RE-LOCATE the symbol by name and note the correction in your evidence rather than
implementing against whatever happens to be at that offset. Do NOT fix `nueip1`'s
general `dependency-blocked` defect here, and do NOT change `EXECUTION_SUCCESS_STATES`; both are
deliberately deferred and widening this child would make the Set unreviewable. Edit the AGENTS.md
GENERATOR in `engine.py`, never the rendered file. `finalize-refused` is TERMINATE, not RECONSIDER;
getting that backwards produces an infinite retry loop, which is the one regression worse than the bug.
E-04 AND E-07 ARE BOTH REQUIRED and neither substitutes for the other: E-04 makes agy DECIDE
`orchestrate`, E-07 makes agy ACT on it. Shipping E-04 alone leaves agy agent-executing orchestrators
exactly as it does today while every parity test passes, so do not treat V-04 as evidence of host
symmetry. Route agy through the SHARED outcome path; do not fork a second copy into `agy_runipd.py`.
RECONSIDER MEANS RE-SELECTED, NOT MERELY UNLABELLED. Writing no status is necessary and not sufficient:
selection still requires `dependency_status` satisfied, and `cascade_dependency_blocked` runs at the top
of every iteration and can relabel the item you deliberately left `queued` (F-6). Prove re-selection
happened; an orchestrator left unlabelled and never re-dispatched has been forgotten, not reconsidered.

DO NOT REPLACE ONE OVERSTATEMENT WITH ANOTHER in AGENTS.md. Every factual assertion in the new text must
map to an E-06 test; an assertion with no test behind it must be deleted rather than shipped, because a
documented claim no test exercises is the precise defect this Set exists to correct. Keep the surrounding
paragraph coherent: its "Do NOT raise ... orchestrator finalization" instruction must not end up
forbidding an agent from reporting the cases the mechanism deliberately REFUSES.

PASTE ACTUAL OUTPUT for every `V-*`, including the sabotages. State the end-to-end coverage limit
honestly at finalize rather than implying a full unattended proof. Commit path-scoped only (`git commit
-m msg -- <path>`); never `git add -A`/bare/`-a`; never push; never tag or release; and because others
may be working in this checkout, verify `git diff --cached --name-only` before each commit and unstage
anything that is not yours. OQ-01 is yours to answer empirically via E-03.

POST-GATE LIFECYCLE. Do not claim done or move this plan until every `V-*` is verified with concrete
pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed
by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
