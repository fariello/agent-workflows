# IPD: wire both host dispatch paths and correct the documented claim

- Date: 2026-09-06
- Kind: child
- Concern: Three defects on the dispatch side, all measured at HEAD `844d195c`. FIRST, the oc dispatch branch (`oc_runipd.py:6993-7031`) writes `runnable["status"] = "dependency-blocked"` on ANY failure; that value is in `TERMINAL_STATES` (`:254-272`) and the selection filter admits only `queued` (`:4071`, `:6919`), so the orchestrator is excluded FOREVER even when its children all finish later in the SAME run. The event is literally named `orchestrator-deferred`, and a deferral is by definition something you return to. SECOND, one `else` covers two unrelated failures, proven by the two recorded reasons on one run: `5e4sb6 | not-all-children-executed` and `rh5tt6 | finalize-refused`. So `kxkc04`'s prescription ("leave it queued") is correct for the first and would make the second SPIN FOREVER. THIRD, the agy runner has no orchestrate action at all: `action_for`, `finalize_orchestrator` and `_set_children_all_executed` are all absent from `agy_runipd` (verified by object identity, not grep), and `agy_runipd.py:1783` calls its own `determine_action` (`:1510-1514`), so `agy.determine_action('approved')` returns `'execute'` where `oc.action_for('orchestrator','approved')` returns `'orchestrate'`. `aw agy run` would AGENT-EXECUTE an orchestrator, spending a turn authoring against a plan whose purpose the runner has superseded.
- Scope: Wire child 01's predicate and child 02's transition into BOTH hosts' dispatch, replace the single terminal-status write with the reconsiderable-versus-dead distinction (spec `77tr3o` R-7, R-8), give the agy runner the `orchestrate` action it lacks via SHARED code rather than a copy (R-10), make the four refusal reasons distinguishable in the durable record (R-9), and correct the false `AGENTS.md` self-finalization claim (R-11). It does NOT change the eligibility predicate (child 01) or the transition (child 02), and it does NOT touch the general `dependency-blocked`-is-terminal defect for ORDINARY items, which is `nueip1`.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/engine.py, AGENTS.md, tests/test_orchestrator_retirement.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:5942n7, executed:ueg5cf
- Status: to-review
- Set: orchretire
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: pgq326
- From-Backlog: kxkc04
- From-Spec: 77tr3o

## Workflow history

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

- [ ] E-01 Replace the single `else` with the three-way outcome the two recorded reasons prove is needed: RETIRE (eligible per child 01, transition per child 02); RECONSIDER (children merely unfinished, so write NO status and let the next loop iteration re-test, exactly as an item skipped by the inner selection pass already does at `oc_runipd.py:5829-5833`); TERMINATE (a child reached a non-success terminal state and can never become `executed`, or the child set is unauthored, or the transition itself refused). `finalize-refused` MUST be TERMINATE, not RECONSIDER: `rh5tt6` proves a refusal can be structural, and retrying it every iteration would spin.
  - Depends on: none
  - Expected outcome: an orchestrator whose children finish mid-run is retired in that same run; one whose child failed terminally is marked terminal with the real reason; neither spins.
  - Execution state: pending

- [ ] E-02 Make the four refusal reasons distinguishable in the durable record (spec R-9): "children exist and are unfinished: <ids with their statuses>", "no children of Set <setid> exist", "child table declares unauthored rows", "transition refused: <reason>". Today all four collapse into `dependency-blocked` plus an `unsatisfied_dependencies` list that was EMPTY for both observed cases, producing a run summary reading "dependency-blocked (unmet dependencies)" while naming no dependency. Keep the `orchestrator-deferred` event name for continuity but make its `reason` field carry the specific cause.
  - Depends on: E-01
  - Expected outcome: `events.jsonl` and the run report name the actual cause; no summary claims an unmet dependency it cannot name.
  - Execution state: pending

- [ ] E-03 Verify, do not assume, that leaving an orchestrator RECONSIDERABLE cannot hang a run (spec R-8). The drain path (`oc_runipd.py:5847`, when `runnable is None`) already terminates a run whose remaining items are unsatisfiable; confirm an orchestrator left reconsiderable with permanently-unfinishable children reaches that path and is labelled there with a reason naming the dead children. If it does not, add the termination rather than reintroducing the premature terminal write.
  - Depends on: E-01
  - Expected outcome: pasted evidence that a run with a dead child terminates rather than looping, with the reason naming the child.
  - Execution state: pending

### Task group 2: host symmetry and the documented claim

- [ ] E-04 Give the agy runner the `orchestrate` action through SHARED code. Move the action decision (`oc_runipd.action_for`, `:2450-2463`) into `runner_shared.py` and have BOTH hosts import it, rather than adding a second copy to `agy_runipd.py`: the anti-re-fork discipline from `2r306y`/`818uru` is binding, and `agy_runipd.py:1313` already notes that agy losing `kind` breaks `action_for`. Ensure agy's queue entries carry `kind` so the shared decider can see it.
  - Depends on: none
  - Expected outcome: `agy` and `oc` return the SAME action for the same (kind, status) pair, verified by asserting the two call the same object rather than by comparing outputs alone.
  - Execution state: pending

- [ ] E-07 Add the agy DISPATCH BRANCH that acts on the `orchestrate` action, which sharing the decider does NOT accomplish. E-04 makes agy DECIDE `orchestrate`; agy then IGNORES it. Verified at HEAD `844d195c`: the token `orchestrate` appears nowhere in `agy_runipd.py` outside the unrelated `orchestrate_isolation` import, `execute_item` derives only `is_review = action == "review"` (`:2973`), and the queue loop calls `execute_item` unconditionally (`:4138`). So without this item E-04 ships a decider returning a value into a host that spends an agent turn anyway, which is the very failure spec R-10 exists to prevent, and V-04's object-identity assertion would still PASS. Route agy's `orchestrate` items through the SAME shared retire/reconsider/terminate outcome E-01 and E-02 build for oc; do not fork a second copy of that logic into `agy_runipd.py`.
  - Depends on: E-01, E-02, E-04
  - Expected outcome: an approved orchestrator dispatched by `aw agy run` is retired, reconsidered, or terminated by the shared path with NO agent turn and no `execute_item` call, matching oc's outcome and not merely oc's decision.
  - Execution state: pending

- [ ] E-05 Correct the false claim in the managed AGENTS.md block (spec R-11). `AGENTS.md:42` states an orchestrator "self-finalizes once every child of its Set reached `executed` ... so an Order-0 parent in the queue is correct and needs no human step" and instructs agents NOT to raise orchestrator finalization. That was never true: 0 successes in 102 runs. EDIT THE GENERATOR, not the rendered file: the text lives in `engine.py`'s `agents_managed_sections` (the paragraph near `engine.py:1146`), and a hand-edit to `AGENTS.md` is overwritten on the next install. Regenerate via the merge helper, and state the NEW behavior without a new overstatement (say what the runner does, and that a Set with unauthored children is deliberately not retired).
  - Depends on: E-01, E-04
  - Expected outcome: the managed block describes behavior that the tests in E-06 actually demonstrate, and a re-render is idempotent.
  - Execution state: pending

- [ ] E-06 Extend the test modules with end-to-end dispatch coverage: an orchestrator retired mid-run once its last child completes; an orchestrator RECONSIDERED rather than terminally marked when a child is still running; a dead-child run that terminates with a naming reason; the agy host taking `orchestrate` rather than `execute` for an approved orchestrator; and the four distinct reasons appearing in `events.jsonl`. Cover BOTH hosts for the action decision, since a one-host fix passes every oc-only test (the failure mode `818uru` recorded).
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: tests that fail if either host regresses, and specifically if agy reverts to agent-executing an orchestrator.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Run the suite BARE (`python3 -m pytest`).
- `AGENTS.md`'s managed block is GENERATED from `engine.py`; edit the generator and re-render with `engine.merge_aw_block`, never the file directly. Verified this session: a hand-edit is replaced on re-render, and re-rendering after a generator edit is idempotent.
- The oc and agy runner suites are severely asymmetric (95 vs 21 tests, measured in `5e4sb6`'s E-01), and the least-covered symbols are the most diverged. E-06's both-hosts requirement exists because of that measured gap.
- An item merely SKIPPED by the inner selection pass writes no status and IS reconsidered; ordering is already correct right up until something is LABELLED. The bug is the labelling.

## Findings

| # | Sev | Where | Finding | Evidence |
|---|-----|-------|---------|----------|
| F-1 | HIGH | `oc_runipd.py:7015` | The deferral writes a TERMINAL status, so the orchestrator is never reconsidered even when its children finish in the same run. | `TERMINAL_STATES:254-272`; selection filter `:4071`, `:6919` |
| F-2 | HIGH | `oc_runipd.py:7014` | One `else` covers two unrelated failures, so `kxkc04`'s "leave it queued" fix would make the `finalize-refused` case spin forever. | recorded reasons `not-all-children-executed` and `finalize-refused` on one run |
| F-3 | HIGH | `agy_runipd.py:1783` | agy has NO orchestrate action; it would agent-execute an approved orchestrator. | `agy.determine_action('approved')`=`execute` vs `oc.action_for('orchestrator','approved')`=`orchestrate`; all three symbols absent from agy |
| F-4 | MED | `AGENTS.md:42` | Asserts self-finalization works and tells agents not to raise it; 0 successes in 102 runs. Text lives in `engine.py`, so a direct edit would be reverted. | `grep -rh orchestrator-finalized ... \| wc -l` = 0 |
| F-5 | LOW | `5e4sb6` event | The run summary reads "unmet dependencies" while naming none, because the no-children branch returns `(False, [])`. | `unfinished_children: []` in the event payload |

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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a scripted run over a synthetic Set where the orchestrator is dispatched BEFORE its last child finishes, showing it is reconsidered and then RETIRED in the same run. Paste the queue/status transitions, not just the final state, so the reconsideration is visible rather than inferred.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `events.jsonl` lines for all four refusal causes, each naming its specific reason, and show that the unfinished-children case names the ids AND their actual statuses. Also show no summary line claims an unmet dependency without naming one (the `5e4sb6` defect).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a run where a child reaches a non-success terminal state, showing the run TERMINATES (not loops) and the orchestrator's recorded reason names the dead child. State plainly whether the existing drain path handled it or you added the termination.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a Python session asserting `agy.<action decider> is oc.<action decider>` (the same object, proving shared code rather than parity by coincidence) and showing both return `orchestrate` for an approved orchestrator. Paste an agy queue entry showing it carries `kind`. This item proves the DECISION only; the dispatched OUTCOME is V-07's, and this item must NOT be read as establishing host parity on its own.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the AGENTS.md diff, paste the `engine.py` generator change, and paste a second `merge_aw_block` render showing it is IDEMPOTENT (no further change). Quote the new sentence and state what it does NOT claim, so the correction is not itself an overstatement.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare suite summary. Then paste a SABOTAGE per host: revert agy's action decision to `determine_action` and show the agy test FAILS; reinstate the terminal-status write and show the reconsideration test FAILS. Both are required because a one-host fix passes every oc-only test.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste an `aw agy run` dispatch of an approved orchestrator over a synthetic Set showing the DISPATCHED OUTCOME (retired, reconsidered, or terminated) with NO agent turn: show that `execute_item` was not called and no session/prompt artifact was written for that item. Then paste a SABOTAGE proving this is not the decider test in disguise: leave the shared decider returning `orchestrate` but REMOVE agy's dispatch branch, and show V-04's identity assertion still PASSES while this item's test FAILS. That contrast is the whole point of separating the two.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. This child touches the most contended files in the repo, so stay strictly inside
`Scope-Paths` and do not refactor the runner suites beyond the cases E-06 adds. Do NOT fix `nueip1`'s
general `dependency-blocked` defect here, and do NOT change `EXECUTION_SUCCESS_STATES`; both are
deliberately deferred and widening this child would make the Set unreviewable. Edit the AGENTS.md
GENERATOR in `engine.py`, never the rendered file. `finalize-refused` is TERMINATE, not RECONSIDER;
getting that backwards produces an infinite retry loop, which is the one regression worse than the bug.
E-04 AND E-07 ARE BOTH REQUIRED and neither substitutes for the other: E-04 makes agy DECIDE
`orchestrate`, E-07 makes agy ACT on it. Shipping E-04 alone leaves agy agent-executing orchestrators
exactly as it does today while every parity test passes, so do not treat V-04 as evidence of host
symmetry. Route agy through the SHARED outcome path; do not fork a second copy into `agy_runipd.py`.
PASTE ACTUAL OUTPUT for every `V-*`, including the sabotages. State the end-to-end coverage limit
honestly at finalize rather than implying a full unattended proof. OQ-01 is yours to answer empirically
via E-03.

POST-GATE LIFECYCLE. Do not claim done or move this plan until every `V-*` is verified with concrete
pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed
by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
