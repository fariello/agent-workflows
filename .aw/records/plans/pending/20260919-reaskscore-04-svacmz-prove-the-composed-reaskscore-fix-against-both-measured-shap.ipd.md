# IPD: Prove the composed reaskscore fix against both measured shapes and pin the five shared predicates unweakened

- Date: 2026-09-19
- Kind: child
- Concern: THE ORCHESTRATOR COVERAGE GATE REFUSED THIS SET ON 2026-09-19 (`aw oc run reaskscore`), reporting that `s0gnha` carries work no child covers, and the refusal is CORRECT rather than a false positive. Its E-02 (verify the five shared success and retirement constants are byte-identical on the MERGED result and the cross-host equality pins pass) and E-03 (reconstruct SHAPE A and SHAPE B end to end, and prove a turn that is BOTH host-truncated AND rescued by its re-ask is rescored WITHOUT also being retried) are both genuine verification work owned by nobody: measured 2026-09-19, no child mentions SHAPE A or SHAPE B at all, and no child anywhere mentions the collision case. Because the runner retires an orchestrator once its children are `executed` and deliberately SKIPS the pre-transition E/V checkpoint, those two items would be reported complete having never been performed or verified. E-03 is the worse loss: it is the only place the COMPOSED fix is demonstrated, and by construction no sibling can do it because each holds one third of the behavior.
- Scope: IN: own the verification the parent's E-02 and E-03 describe, as a child whose own V-items force pasted evidence. Reconstruct both measured failure shapes on the merged result; prove the truncated-and-rescued case is rescored and not retried, and that the predicate ORDERING guarantees it rather than leaving it to chance; assert the five named constants byte-identical and the cross-host equality pins and AST ordering pins pass unweakened. OUT: any product change whatsoever. This plan adds tests and evidence only, and MUST NOT modify runner behavior, because the three siblings own every behavioral change and a fourth hand in the same predicates is how a Set loses its safety property.
- Scope-Paths: tests/test_rununify_execute_item_gates.py, tests/test_rununify_run_queue.py, tests/test_reaskscore_composed.py
- Item-Dependencies: executed:skn8uk, executed:ty7w6o, executed:dy9ymn
- Status: to-review
- Set: reaskscore
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: svacmz
- From-Backlog: yxfw4k
- Blocks-Release: next
- Work-Kind: bug

## Workflow history

- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored in response to the orchestrator coverage gate refusing `aw oc run reaskscore`, which named `s0gnha` as carrying work no child covers. Owns the verification the parent's E-02 and E-03 describe so it is performed and verified by an agent turn rather than retired unperformed. The parent's checklist is deliberately LEFT INTACT, per the gate's own instruction and AGENTS.md. Inherits `Blocks-Release: next` and `Work-Kind: bug` from the Set.

## Goal

Make the Set's central claims checkable by an agent that must paste evidence: that the composed fix actually resolves both measured failure shapes, that the two fixes cannot collide destructively, and that no shared predicate was widened to get there.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The safety property (no predicate was widened)

- [ ] E-01 Assert on the MERGED result that the five shared constants are byte-identical to their pre-Set values: `EXECUTION_SUCCESS_STATES` (`agy_runipd.py:563`), `SUCCESS_STATES` (`agy_runipd.py:562`, an alias of `runner_shared.SUCCESS_STATES`), `EXECUTE_REPORTING_SUCCESS_STATES` (`runner_shared.py:10897`), `TERMINAL_STATES` (`agy_runipd.py:541`) and `SET_RETIREMENT_DONE_STATUS` (`runner_shared.py:6736`). Record each value, not merely that a test passed.
  - Depends on: none
  - Expected outcome: The five values are shown unchanged. Any widening is a FAILURE of this item, not a finding to note, because all four measured cascades were correct and a widened success bar trades a visible defect for an invisible one.
  - Execution state: pending

- [ ] E-02 Run the existing cross-host equality and ordering pins unweakened and show them passing: the `EQUAL_CONSTANTS` pin at `tests/test_rununify_run_queue.py:165` (which pins `EXECUTION_SUCCESS_STATES` and `TERMINAL_STATES` equal across hosts) and the AST ordering pins in `tests/test_rununify_execute_item_gates.py`. Confirm no sibling relaxed an assertion to make its own change pass.
  - Depends on: E-01
  - Expected outcome: Both pin families pass, and `git diff` against the pre-Set baseline shows no assertion in either file was loosened or deleted.
  - Execution state: pending

### Task group 2: The composed behavior (both measured shapes)

- [ ] E-03 Reconstruct SHAPE A end to end on the merged result: a first turn that writes no outcome, a defect re-ask that completes and commits the work, and a re-collection. Assert the item ends `substantially-complete` or better AND that its siblings are NOT `dependency-blocked`.
  - Depends on: E-02
  - Expected outcome: SHAPE A does not reproduce. The item's recorded disposition matches the work that exists on disk, and the cascade does not fire. Assert BOTH halves: a correct disposition with a still-cascading sibling set is a failure, since the cascade is what cost the four measured runs.
  - Execution state: pending

- [ ] E-04 Reconstruct SHAPE B end to end (a host-truncated turn that did nothing at all), asserting it is re-dispatched once within budget rather than blocking its Set. Then prove the COLLISION CASE is ordered rather than accidental: a turn that is BOTH truncated AND rescued by its re-ask must be rescored (the work exists) and MUST NOT be retried (retrying would re-dispatch completed, committed work). Assert the predicate ORDERING guarantees the exclusivity, not merely that one example came out right.
  - Depends on: E-03
  - Expected outcome: SHAPE B is retried once within budget. The truncated-and-rescued case is rescored and not retried, AND the test demonstrates why that holds in general: `dy9ymn`'s conjunction requires no outcome file, no commit, unchanged head and a clean tree, every one of which a rescued turn violates. A test that only samples one ordering FAILS this item.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Verified 2026-09-19: the coverage gate refused `aw oc run reaskscore` naming `s0gnha`, and its instruction is to ADD A CHILD and leave the parent's checklist in place. The verdict cache re-probes automatically because adding this child changes both inputs it keys on (the parent's E-item action text and its child table).
- Verified 2026-09-19: no sibling mentions SHAPE A or SHAPE B (`grep` returns 0 in all three), and no plan anywhere mentions the collision case, confirming both parent items are genuinely uncovered.
- Verified 2026-09-19: the five constants live at `agy_runipd.py:562,563,541` and `runner_shared.py:10897,6736`. The cross-host pin is `EQUAL_CONSTANTS` at `tests/test_rununify_run_queue.py:165`, covering `EXECUTION_SUCCESS_STATES` and `TERMINAL_STATES`.
- The parent's Cross-IPD validation section already states the exclusivity argument and explicitly says the Set "must DEMONSTRATE the exclusivity rather than assume it". This child is where that demonstration lives.
- The suite runs BARE as `python3 -m pytest` per AGENTS.md; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.
- `- Readiness:` is deliberately absent (it is `/plan-review`'s output; IPD-M107 refuses an unattested value).

## Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | Blocker | Two orchestrator items would be marked complete without being performed, and one of them is the Set's only end-to-end proof. This is the precise failure mode the coverage gate was built to stop, measured in production 2026-09-08 on a different rollup. | Gate output 2026-09-19 naming `s0gnha`; the parent's E-02 and E-03 text; runner retirement skips the pre-transition E/V checkpoint by design. |
| F-02 | High | The collision case (truncated AND rescued) is owned by NO plan in the Set, yet its failure mode is the most expensive one available: re-dispatching completed, committed work. | `grep -i "collide\|collision\|truncated and rescued"` across all three children returns nothing, 2026-09-19. |
| F-03 | Medium | The parent's E-02 asks for verification "against the merged result", which no child can perform in its own isolated worktree: each execute item gets its own lane, so only a plan that runs AFTER all three siblings can see the merged state. That makes this child's dependency edges load-bearing rather than decorative. | Runner isolates each execute item in its own worktree and returns changes through the merge-and-revalidate gate (AGENTS.md). |

## Proposed changes (ordered, validatable)

1. Assert the five shared constants byte-identical on the merged result (E-01).
2. Run the cross-host equality and AST ordering pins unweakened (E-02).
3. Reconstruct SHAPE A, asserting both the disposition and the absent cascade (E-03).
4. Reconstruct SHAPE B and prove the collision ordering holds in general (E-04).

## Deferred / out of scope (with reason)

- Any product or runner behavior change: the three siblings own every behavioral fix, and a fourth hand in the same predicates is how a Set loses the safety property its parent's E-02 exists to protect. This child adds tests and evidence only.
  - Carrier-Declined: A DELIBERATE SCOPE BOUNDARY, not deferred work. Every behavioral change this Set needs is already owned by `skn8uk`, `ty7w6o`, or `dy9ymn`, so there is no unowned work to carry. If this child's reconstruction reveals a NEW defect, the correct response is a new plan or backlog item filed at that point, not a silent widening of this one.
- The three candidate spec amendments the siblings each recorded as non-blocking open questions (`skn8uk` OQ-01 on `7ckptx` R2.1, `ty7w6o` OQ-02 on `7ckptx` R4, `dy9ymn` OQ-01 on `25kzda` 5.5).
  - Carrier-Declined: Each is ALREADY CARRIED by the sibling that raised it, as that plan's own recorded open question, so the obligation has a home and this child would be duplicating it. This child's E-02 independently confirms that no child edited a spec anyway, which is the check the parent's Cross-IPD section asks for.
- Closing the two source backlog items (`yxfw4k` may close; `x7wfyx` must be `graduated`, not `done`).
  - Carrier: yxfw4k
- Widening the coverage gate, the retirement predicate, or the E/V checkpoint so a parent like `s0gnha` could retire with uncovered items.
  - Carrier-Declined: THE OPPOSITE OF THIS SET'S PURPOSE, and explicitly forbidden by the parent's own Scope, which excludes loosening any dependency, success-bar, or orchestrator-retirement predicate "in every child without exception". The gate behaved correctly here; the defect was the missing child, which this plan supplies. Nothing is outstanding.

## Scope check

- Over-scope: none. Every E-item maps directly onto a clause of the parent's E-02 or E-03.
- Under-scope: none for the uncovered work. NOTE the parent's E-01 (sequence the children) is deliberately NOT claimed here: it is legitimate orchestration performed by executing the children, so it is exactly the kind of item that SHOULD remain on an orchestrator, and moving it would empty the checklist that makes `execute reaskscore` work when no runner is involved.

## Required tests / validation

Run the suite BARE: `python3 -m pytest`, and paste the actual summary line. This child's own deliverable IS test code, so the suite run is necessary but not sufficient: each V-item below additionally demands the specific reconstruction output, because a passing suite that never exercised SHAPE A would satisfy the letter of "tests pass" while proving nothing.

## Spec / documentation sync

No `.spec.md` edit, and none is declared in `- Scope-Paths:`. That is deliberate and is itself one of the parent's Cross-IPD checks ("NO CHILD EDITED A SPEC"), which E-02 confirms on the merged result. The three candidate amendments stay as their raising siblings' open questions.

## Open questions

### OQ-01: Should the composed reconstruction live in a new test module or extend an existing one?

- Blocking: no
- Status: open
- Owner: none
- Carrier-Declined: AN IMPLEMENTATION CHOICE RESOLVED INSIDE THIS PLAN'S OWN EXECUTION, with both routes conforming and no residual work either way. `- Scope-Paths:` names a new `tests/test_reaskscore_composed.py` alongside the two existing pin files, so the default is a new module for the reconstruction and in-place extension for the pins; the executing agent may instead extend an existing module if that fits the suite's conventions better, provided the scope reconciliation is honored. Recorded so the choice is made deliberately rather than discovered mid-execution.
- Resolution or deferral rationale: NOT BLOCKING because the reconstruction's VALUE is independent of its file location, and because V-03 and V-04 demand the reconstruction output itself rather than a file path. A new module is the stated default because SHAPE A and SHAPE B are end-to-end scenarios rather than unit assertions about one function, and burying them inside a gates-ordering module would make them hard to find when they next fail.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the ACTUAL VALUE of each of the five constants as read from the merged tree, beside its pre-Set value, with the file:line for each. A statement that "the constants are unchanged" without the values FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the passing output for the `EQUAL_CONSTANTS` pin (`tests/test_rununify_run_queue.py`) and the AST ordering pins (`tests/test_rununify_execute_item_gates.py`). Paste `git diff` for BOTH files against the pre-Set baseline, showing no assertion was loosened or removed. An empty diff is the expected and strongest result.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the SHAPE A reconstruction output showing the three stages (no-outcome first turn, completing defect re-ask, re-collection) and the final recorded disposition. Assert and paste BOTH halves: the item at `substantially-complete` or better, AND the sibling states showing none is `dependency-blocked`. Showing only the disposition FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the SHAPE B reconstruction showing exactly one re-dispatch within budget rather than a terminal block. Then paste the collision case: a turn both truncated and rescued, showing it rescored and NOT retried. Additionally paste the evidence that the ordering holds IN GENERAL, by showing `dy9ymn`'s conjunction evaluating False on each of its four conditions for a rescued turn (outcome file present, commit present, head moved, tree dirty). A single passing example without the general argument FAILS this item, because the cost of the ordering being accidental is re-dispatching committed work.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved svacmz --by-human`). Its `- Item-Dependencies: executed:skn8uk, executed:ty7w6o, executed:dy9ymn` edges are re-checked at dispatch and are load-bearing rather than decorative: the parent asks for verification against the MERGED result, and because each execute item runs in its own isolated worktree, only a plan dispatched after all three siblings have merged can observe that state. The runner sorts by dependency depth as its first key, so this child is queued last in the Set by construction.

WHY THIS PLAN EXISTS, recorded so a later reader does not mistake it for padding: the orchestrator coverage gate refused `aw oc run reaskscore` on 2026-09-19 because `s0gnha` carried E-02 and E-03 with no child covering them. The remedy the gate names is to add a child owning that work and leave the parent's checklist intact, which is exactly what this plan does. Do NOT respond to a future firing of that gate by deleting a parent's items.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
