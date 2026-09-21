# IPD: Prove the composed reaskscore fix against both measured shapes and pin the five shared predicates unweakened

- Date: 2026-09-19
- Kind: child
- Concern: THE ORCHESTRATOR COVERAGE GATE REFUSED THIS SET ON 2026-09-19 (`aw oc run reaskscore`), reporting that `s0gnha` carries work no child covers, and the refusal is CORRECT rather than a false positive. Its E-02 (verify the five shared success and retirement constants are byte-identical on the MERGED result and the cross-host equality pins pass) and E-03 (reconstruct SHAPE A and SHAPE B end to end, and prove a turn that is BOTH host-truncated AND rescued by its re-ask is rescored WITHOUT also being retried) are both genuine verification work owned by nobody: measured 2026-09-19, no child mentions SHAPE A or SHAPE B at all, and no child anywhere mentions the collision case. Because the runner retires an orchestrator once its children are `executed` and deliberately SKIPS the pre-transition E/V checkpoint, those two items would be reported complete having never been performed or verified. E-03 is the worse loss: it is the only place the COMPOSED fix is demonstrated, and by construction no sibling can do it because each holds one third of the behavior.
- Scope: IN: own the verification the parent's E-02 and E-03 describe, as a child whose own V-items force pasted evidence. Reconstruct both measured failure shapes on the merged result; prove the truncated-and-rescued case is rescored and not retried, and that the predicate ORDERING guarantees it rather than leaving it to chance; assert the five named constants byte-identical and the cross-host equality pins and AST ordering pins pass unweakened. OUT: any product change whatsoever. This plan adds tests and evidence only, and MUST NOT modify runner behavior, because the three siblings own every behavioral change and a fourth hand in the same predicates is how a Set loses its safety property.
- Scope-Paths: tests/test_rununify_execute_item_gates.py, tests/test_rununify_run_queue.py, tests/test_reaskscore_composed.py
- Item-Dependencies: executed:skn8uk, executed:ty7w6o, executed:dy9ymn
- Status: approved
- Readiness: go-pending-approval
- Set: reaskscore
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: svacmz
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Backlog: yxfw4k
- Blocks-Release: next
- Work-Kind: bug

## Workflow history
- 2026-09-19 approved (aw set): status set to approved

- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /askme: OQ-02 RESOLVED VIA THE RECOMMENDED SHAPE (a), clearing this plan's only blocking question and with it its `no-go`. `ty7w6o` PR-001 was resolved on its OWN plan (its blocking route question settled by the maintainer, who chose the body-prose edit), and this plan's refused dependency edge cleared as the side effect the question predicted. RE-MEASURED WITH THE SAME PREDICATES THE QUESTION CITED: `review_findings.subject_gating_blocks(repo,'ty7w6o')` now returns `()` where it returned one HIGH/open block for PR-001, and `check_engine.evaluate_ipd_dependencies(repo)` returns NO `check.ipd-dependency-findings-blocked` drift for this file where it previously returned one reading "dependency `executed:ty7w6o` resolves but does not satisfy the edge"; the parent's twin block cleared too (`s0gnha` PR-005 resolved from the repository, now `()`). Because the refusal runs through the SHARED predicate (`runner_shared._findings_block_reason` -> `subject_gating_blocks`), one resolution clears it on both hosts and in `aw check` alike. NEITHER NOT-RECOMMENDED SHAPE WAS TAKEN: the repository gate threshold is untouched and still the `high` default, and the `executed:ty7w6o` edge is untouched, so the merged-result property the edge exists for survives intact. The consequence the question warned of is averted: the Set's only end-to-end proof of the composed fix will now dispatch instead of being marked `dependency-blocked` and silently skipped. PR-001 recorded FIXED; `aw ipd lint --phase review-finalize` now `conforming`. Readiness `no-go` -> `go-pending-approval`; HUMAN APPROVAL IS STILL REQUIRED and no agent may write it.
- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-006, five FIXED, PR-001 left OPEN and escalated as blocking OQ-02; Readiness `no-go` pending that answer. Reviewed at HEAD `27d399ed`; the plan was byte-identical to the sealed lane input and the tree was clean, so no pre-review snapshot. `aw ipd lint --phase author` reported `clean` before the revisions; `--phase review-finalize` reports only the expected `IPD-Q501` (OQ-02 blocking and open) after them. Watermark unchanged at 04: every finding was fixed by strengthening an existing item, none by adding one. THE PLAN SHOULD EXIST AND ITS PREMISE CHECKS OUT: no sibling mentions SHAPE A or SHAPE B (0 `grep` hits in all three) and none mentions the collision case, so the parent's two items really were uncovered, and its tests-and-evidence-only fence is the right shape. THE BLOCKER IS NOT FIXABLE FROM INSIDE THIS FILE: measured by running `check_engine.evaluate_ipd_dependencies` on it, the `executed:ty7w6o` edge is REFUSED (`check.ipd-dependency-findings-blocked`, "ty7w6o: review finding PR-001 is high/open and unresolved"), enforced through the shared `review_findings.subject_gating_blocks` both runners consume, so a run would mark this item `dependency-blocked` and the Set's only end-to-end proof would never execute. FOUR SUBSTANTIVE CORRECTIONS, each measured. (1) E-01 named ONE site per constant, but the five names have EIGHT definition sites, and the omitted third `TERMINAL_STATES` copy (`runner_shared.py:12262`) is the one `reconcile_disposition` reads at `:12624` - the exact function `skn8uk` calls a second time - so a one-sided widening there would have passed. (2) E-02 credited `EQUAL_CONSTANTS` with pinning the constants; it compares oc against agy ONLY, so an identical widening of both hosts passes and the shared copy is out of reach. (3) V-02 demanded an empty `git diff`, already false by 3 insertions/2 deletions from unrelated main commit `eee6f427` (0 assert lines) and about to be more so because `skn8uk` declares the other pin file; re-expressed as an assertion-level bar. (4) E-04's general exclusivity argument rested on all four of `dy9ymn`'s conditions, two of which that plan's own review measured VACUOUS on an isolated turn, so the argument was unsound though its conclusion is right; re-based onto the two load-bearing conditions. Unlike all three siblings, every citation in this plan resolves accurately. Full record: `.aw/records/reviews/20260919-reaskscore-04-svacmz-prove-the-composed-reaskscore-fix-against-both-measured-shap.review.md`.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored in response to the orchestrator coverage gate refusing `aw oc run reaskscore`, which named `s0gnha` as carrying work no child covers. Owns the verification the parent's E-02 and E-03 describe so it is performed and verified by an agent turn rather than retired unperformed. The parent's checklist is deliberately LEFT INTACT, per the gate's own instruction and AGENTS.md. Inherits `Blocks-Release: next` and `Work-Kind: bug` from the Set.

## Goal

Make the Set's central claims checkable by an agent that must paste evidence: that the composed fix actually resolves both measured failure shapes, that the two fixes cannot collide destructively, and that no shared predicate was widened to get there.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The safety property (no predicate was widened)

- [ ] E-01 Assert on the MERGED result that the five shared CONSTANTS are byte-identical to their pre-Set values, ENUMERATING EVERY DEFINITION SITE OF EACH rather than one site per name. Record each value, not merely that a test passed.
  FIVE NAMES, EIGHT DEFINITION SITES, ACROSS THREE FILES. Measured at review, because the plan as authored named one site per constant and so had a real hole: (1) `EXECUTION_SUCCESS_STATES` is defined TWICE, as a separate set literal per host (`oc_runipd.py:492` AND `agy_runipd.py:563`), and `tests/test_runner_shared.py::test_EXECUTION_SUCCESS_STATES_is_EQUAL_on_both_hosts_even_though_duplicated` records in terms that the two are "EQUAL BUT NOT IDENTICAL", so asserting one proves nothing about the other; (2) `SUCCESS_STATES` is defined ONCE (`runner_shared.py:10843`) and re-exported by both hosts (`oc_runipd.py:491`, `agy_runipd.py:562`), which the same file pins with `assertIs`, so here one assertion genuinely covers all three names; (3) `TERMINAL_STATES` is defined THREE TIMES (`oc_runipd.py:470`, `agy_runipd.py:541`, and `runner_shared.py:12262` as a `frozenset`); (4) `EXECUTE_REPORTING_SUCCESS_STATES` once (`runner_shared.py:10897`), DERIVED BY SUBTRACTION from `SUCCESS_STATES` rather than written as a literal, so assert the derivation still holds and not merely the value; (5) `SET_RETIREMENT_DONE_STATUS` once (`runner_shared.py:6736`).
  THE SHARED `TERMINAL_STATES` COPY IS THE ONE THIS SET CANNOT AFFORD TO SKIP, and it is the site the plan originally omitted. `runner_shared.reconcile_disposition` (`runner_shared.py:12575-12628`) reads the SHARED copy at `:12624` (`if disposition in TERMINAL_STATES - {"dependency-blocked", "not-attempted"}`), and `reconcile_disposition` is the EXACT function `skn8uk` calls a SECOND time for its rescore. So a widening of the shared copy would change the rescore's own verdict, and an assertion covering only the two host copies would not see it. Note also that E-02's `EQUAL_CONSTANTS` pin compares oc against agy ONLY (`tests/test_rununify_run_queue.py:391`), so it does not close this gap either: the shared third copy must be asserted HERE. Measured at review, all three are equal today (each `{approved, blocked, dependency-blocked, executed, failed-safely, integration-blocked, merge-conflict, not-attempted, partial, reviewed, substantially-complete}`). UPDATED 2026-09-21 (`l2mzxn`): the integration vocabulary was renamed, so each copy now ALSO contains the canonical `merge-needs-human` and `merge-refused` beside the pre-rename `integration-blocked`/`merge-conflict`, which are retained so a durable run directory still classifies. The deferrable pair (`merge-retry`, `merge-unchecked`) is DELIBERATELY ABSENT from `TERMINAL_STATES`. Compare the three copies programmatically rather than against this hand-written set.
  - Depends on: none
  - Expected outcome: All EIGHT definition sites are read and their values recorded, with the three `TERMINAL_STATES` copies shown mutually equal and `EXECUTE_REPORTING_SUCCESS_STATES` shown still derived from `SUCCESS_STATES` by subtraction. Any widening is a FAILURE of this item, not a finding to note, because all four measured cascades were correct and a widened success bar trades a visible defect for an invisible one.
  - Execution state: pending

- [ ] E-02 Run the existing cross-host equality and ordering pins unweakened and show them passing: the `EQUAL_CONSTANTS` pin (`tests/test_rununify_run_queue.py:165`, asserted by `test_the_equal_constants_are_still_equal_across_hosts` at `:390`) and the AST ordering pins in `tests/test_rununify_execute_item_gates.py`. Confirm no sibling relaxed an assertion to make its own change pass.
  KNOW WHAT THIS PIN DOES AND DOES NOT COVER, so E-01 is not wrongly believed redundant. `EQUAL_CONSTANTS` is `("EXECUTION_SUCCESS_STATES", "TERMINAL_STATES")` and its loop compares `getattr(oc_runipd, name)` against `getattr(agy_runipd, name)` ONLY. So it proves the two HOST copies agree; it says NOTHING about their VALUE (both hosts could be widened identically and it would still pass) and NOTHING about `runner_shared.TERMINAL_STATES`, the third copy `reconcile_disposition` actually reads. E-01 is what pins the values and the shared copy; this item pins cross-host agreement. Neither subsumes the other, and a report that runs only this pin has not performed E-01.
  THE TWO ORDERING PINS THIS SET PERTURBS ARE NAMED, because `skn8uk` E-06 edits this very file and a sibling editing the file that holds the safety pin is the case worth watching: `test_submissions_are_collected_before_the_disposition_is_reconciled` (`:207`) and `test_the_disposition_is_reconciled_before_integration` (`:261`). Both resolve their target through `_execute_item_ast`, which follows each host's delegation into `runner_shared.execute_item_core`, so both read the shared body `skn8uk` edits. Confirm each still passes AND that its assertions are unchanged, not merely that the file's suite is green: a sibling that loosened one of these two and added a new passing test would leave the file green while removing the guard.
  - Depends on: E-01
  - Expected outcome: Both pin families pass, and `git diff` against the pre-Set baseline shows no assertion in either file was loosened or deleted. The two named ordering pins are quoted and shown unchanged.
  - Execution state: pending

### Task group 2: The composed behavior (both measured shapes)

- [ ] E-03 Reconstruct SHAPE A end to end on the merged result: a first turn that writes no outcome, a defect re-ask that completes and commits the work, and a re-collection. Assert the item ends `substantially-complete` or better AND that its siblings are NOT `dependency-blocked`.
  - Depends on: E-02
  - Expected outcome: SHAPE A does not reproduce. The item's recorded disposition matches the work that exists on disk, and the cascade does not fire. Assert BOTH halves: a correct disposition with a still-cascading sibling set is a failure, since the cascade is what cost the four measured runs.
  - Execution state: pending

- [ ] E-04 Reconstruct SHAPE B end to end (a host-truncated turn that did nothing at all), asserting it is re-dispatched once within budget rather than blocking its Set. Then prove the COLLISION CASE is ordered rather than accidental: a turn that is BOTH truncated AND rescued by its re-ask must be rescored (the work exists) and MUST NOT be retried (retrying would re-dispatch completed, committed work). Assert the predicate ORDERING guarantees the exclusivity, not merely that one example came out right.
  ARGUE THE EXCLUSIVITY FROM THE TWO CONDITIONS THAT ACTUALLY BITE, NOT FROM ALL FOUR. `dy9ymn`'s review (2026-09-19, its E-01) established by measurement that two of its four conditions are VACUOUS on an isolated turn: `attempt["ending_head"]` and `attempt["ending_status"]` are read as `git_head(repo)`/`git_status(repo)` on the MAIN CHECKOUT while a lane works in `work_dir`, so `starting_head == ending_head` and an empty `ending_status` hold BY CONSTRUCTION for an isolated lane even when it committed substantial real work. The measured failure shape is an isolated lane turn. So an exclusivity argument resting on "unchanged head and a clean tree" would be resting on two conditions that are TRUE for the rescued case too, and would prove nothing.
  THE LOAD-BEARING CONDITIONS ARE (a) NO OUTCOME FILE and (b) NO LANE COMMIT (read from `describe_lane`/`inspect_lane`'s `commits_ahead`/`dirty`, per `dy9ymn` E-01 as revised). A rescued turn violates BOTH: `skn8uk`'s rescore fires only when `"outcome" in receipt["collected"]` (its E-02, as revised at review, because a gate on `receipt["status"]` passes on a lane that submitted nothing), so a rescued turn has an outcome file by definition; and SHAPE A's rescued turn committed its work, so `commits_ahead > 0`. Build the general argument on those two, and state explicitly that the head and tree conditions are NOT part of it on an isolated turn, with the mode named for any control that uses them.
  - Depends on: E-03
  - Expected outcome: SHAPE B is retried once within budget. The truncated-and-rescued case is rescored and not retried, AND the test demonstrates why that holds in general from the two load-bearing conditions, naming the mode in which each is meaningful. A test that only samples one ordering FAILS this item, and so does a general argument resting on the two vacuous conditions.
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
| F-04 | Blocker | THIS PLAN CANNOT DISPATCH TODAY: its `executed:ty7w6o` edge is refused because `ty7w6o` carries an unresolved HIGH review finding, so a run marks this item `dependency-blocked` and the Set's only end-to-end proof never executes. Added at review; the remedy is work on `ty7w6o`, not an edit here. Escalated as blocking OQ-02. | `check_engine.evaluate_ipd_dependencies` on this file returns `check.ipd-dependency-findings-blocked`: "dependency `executed:ty7w6o` resolves but does not satisfy the edge: ty7w6o: review finding PR-001 is high/open and unresolved". Refusal path: `runner_shared.py:10240` -> `review_findings.subject_gating_blocks`, consumed at `oc_runipd.py:3761-3765`. |
| F-05 | High | E-01 named ONE definition site per constant, but two of the five names are defined more than once (`EXECUTION_SUCCESS_STATES` twice, `TERMINAL_STATES` three times), and the site it omitted is the one `skn8uk`'s rescore actually reads. A one-sided widening of `runner_shared.TERMINAL_STATES` would have passed the item as authored. FIXED: E-01 and V-01 now enumerate all eight sites. | `oc_runipd.py:470,492`; `agy_runipd.py:541,563`; `runner_shared.py:10843,10897,12262,6736`. `reconcile_disposition` (`runner_shared.py:12575`) reads the shared copy at `:12624`. `tests/test_runner_shared.py:1407` records the two host copies as "EQUAL BUT NOT IDENTICAL". |
| F-06 | Medium | V-02 demanded a `git diff` with "an empty diff the expected and strongest result", which is unsatisfiable: the pin file already differs from the authoring-era baseline by unrelated main commits, and `skn8uk` legitimately edits the other pin file. As authored the item forces either a false failure or a papered-over one. FIXED: the bar is now assertion-level with sibling attribution. | `git diff --stat 4f4aaa27..HEAD -- tests/test_rununify_run_queue.py` = 3 insertions, 2 deletions, from `eee6f427` "docs: repoint 9 citations"; 0 changed lines match `assert`. |
| F-07 | Medium | E-04's general exclusivity argument rested on all four of `dy9ymn`'s conditions, two of which that plan's own review measured as VACUOUS on an isolated turn (the measured shape). The argument would have been unsound even though its conclusion is right. FIXED: E-04/V-04 now argue from the two load-bearing conditions and require the mode to be named. | `dy9ymn` E-01 as revised: `ending_head`/`ending_status` read the MAIN checkout while the lane is `work_dir`, so both hold by construction for an isolated lane that committed real work. |

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

### OQ-02: `ty7w6o`'s unresolved HIGH finding blocks this plan's dependency edge; how should the Set proceed?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001, F-04
- Resolution or deferral rationale: RESOLVED 2026-09-19 VIA SHAPE (a), THE RECOMMENDED ONE: `ty7w6o` PR-001 was resolved on its own plan, and this edge cleared as the side effect this question predicted it would. The blocking finding there was a real defect (its E-05 route printed `unchanged` and wrote nothing), the maintainer settled its route by `/askme` the same day, choosing the body-prose edit, and `ty7w6o` is now `Readiness: go-pending-approval`. NEITHER NOT-RECOMMENDED SHAPE WAS TAKEN: the repository gate threshold is untouched and still the `high` default (`config.findings_gate_threshold` returns `high`), and this plan's `- Item-Dependencies: executed:ty7w6o` edge is untouched, so the merged-result property the edge exists for is intact.
  RE-MEASURED AFTER THE RESOLUTION, with the same predicates this question cited, so the clearing is demonstrated rather than assumed. `review_findings.subject_gating_blocks(repo, 'ty7w6o')` now returns `()` where it returned one HIGH/open block for PR-001; `check_engine.evaluate_ipd_dependencies(repo)` returns NO `check.ipd-dependency-findings-blocked` drift for this file, where it previously returned one with detail "dependency `executed:ty7w6o` resolves but does not satisfy the edge"; and the parent's twin block cleared too, `subject_gating_blocks(repo, 's0gnha')` returning `()` after its own PR-005 was resolved from the repository. Because the refusal runs through the SHARED predicate this question names (`runner_shared._findings_block_reason` -> `review_findings.subject_gating_blocks`, consumed for execute-action edges in both drivers), one resolution clears it on both hosts and in `aw check` alike; nothing host-specific was needed.
  WHAT REMAINS IS THIS PLAN'S OWN PR-001, NOT THE EDGE, and the distinction matters because they were one question: `subject_gating_blocks(repo, 'svacmz')` still reports this plan's own BLOCKER row until it is recorded resolved, which is a statement about this review record and no longer about a sibling. THE ORIGINAL CONSEQUENCE THIS QUESTION WARNED OF IS AVERTED: the Set's only end-to-end proof of the composed fix will now dispatch rather than being marked `dependency-blocked` and silently skipped.
  ORIGINAL FINDING, PRESERVED BECAUSE IT WAS ACCURATE AND ITS RECOMMENDATION WAS FOLLOWED: BLOCKING, because it decides whether this plan can run at all and the repository cannot answer it: the fix requires either work on a sibling or a maintainer's judgement about the Set's shape. MEASURED AT REVIEW, not remembered: `check_engine.evaluate_ipd_dependencies` on this file returns `check.ipd-dependency-findings-blocked` with detail "dependency `executed:ty7w6o` resolves but does not satisfy the edge: ty7w6o: review finding PR-001 is high/open and unresolved", `aw check` reports the same rule at `error` severity, and the refusal is enforced through the SHARED predicate (`runner_shared._findings_block_reason` at `runner_shared.py:10240` -> `review_findings.subject_gating_blocks`, consumed for execute-action edges at `oc_runipd.py:3761-3765`), so it holds on both hosts and in `aw check` alike. CONSEQUENCE IF UNANSWERED: `aw oc run reaskscore` marks THIS item `dependency-blocked` and continues, so the Set's ONLY end-to-end proof of the composed fix silently never runs, which is the same class of loss (a verification reported as handled but never performed) that caused this plan to be authored. The same rule blocks the PARENT via `s0gnha` PR-005, also HIGH and open. THE THREE SHAPES: (a) RESOLVE `ty7w6o` PR-001 on its own plan (it is a real defect: its E-05 route printed `unchanged` and wrote no history), which clears this edge as a side effect and is the honest ordering, since `ty7w6o` is also `Readiness: no-go` and is not runnable today either; (b) LOWER the repository gate threshold (`review_findings_gate.block_at`, currently the `high` default) so a HIGH no longer blocks, which is a repository-wide policy change made to unblock one Set and would weaken every other dependency edge, so it is NOT recommended; (c) DROP this plan's `executed:ty7w6o` edge, which silences the gate while destroying the property the edge exists for (observing the MERGED result that only a post-merge dispatch can see) and is therefore the wrong fix. THE RECOMMENDATION IS (a), and it needs no change to this plan. Recorded rather than chosen because it is a sequencing and priority judgement about a sibling, which is the maintainer's call.
- Carrier: ty7w6o

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the ACTUAL VALUE at each of the EIGHT definition sites (not five), beside its pre-Set value, with `file:line` for each: `EXECUTION_SUCCESS_STATES` at `oc_runipd.py:492` and `agy_runipd.py:563`; `SUCCESS_STATES` at `runner_shared.py:10843` plus the `assertIs` re-export proof for both hosts; `TERMINAL_STATES` at `oc_runipd.py:470`, `agy_runipd.py:541` and `runner_shared.py:12262`; `EXECUTE_REPORTING_SUCCESS_STATES` at `runner_shared.py:10897`; `SET_RETIREMENT_DONE_STATUS` at `runner_shared.py:6736`. A statement that "the constants are unchanged" without the values FAILS this item, and so does a paste covering only five sites, because the duplicated names are the ones a one-sided edit hides in.
    ALSO REQUIRED: the three `TERMINAL_STATES` copies shown MUTUALLY EQUAL, and `EXECUTE_REPORTING_SUCCESS_STATES` shown still equal to `SUCCESS_STATES - {"reviewed"}` (its derivation, not a literal), so a change to `SUCCESS_STATES` that silently propagated is visible as such.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the passing output for the `EQUAL_CONSTANTS` pin (`tests/test_rununify_run_queue.py::test_the_equal_constants_are_still_equal_across_hosts`) and the AST ordering pins (`tests/test_rununify_execute_item_gates.py`), INCLUDING the two named pins `test_submissions_are_collected_before_the_disposition_is_reconciled` and `test_the_disposition_is_reconciled_before_integration` quoted and shown unchanged.
    DIFF AGAINST THE SET'S OWN MERGE-BASE, AND DO NOT EXPECT AN EMPTY DIFF. Establish the baseline as the merge-base of this lane and the commit that introduced the Set's parent (`git merge-base HEAD <parent-add-commit>`), NOT as a remembered hash. Measured at review, `tests/test_rununify_run_queue.py` ALREADY differs from the authoring-era baseline `4f4aaa27` by 3 insertions and 2 deletions, landed by unrelated main commits (`eee6f427` "docs: repoint 9 citations", after `d4dd6b88`), and that diff touches ZERO assertion lines (measured: 0 changed lines matching `assert`). So the original instruction to expect an empty diff was UNSATISFIABLE and an executor following it literally would either report a false failure or paper over it.
    THE ACTUAL BAR IS ASSERTION-LEVEL, NOT FILE-LEVEL: for each changed line in either pin file, show it is a comment, docstring, or citation rather than an assertion, or else name the sibling that changed it and why. Explicitly state the sibling attribution for `tests/test_rununify_execute_item_gates.py`, which `skn8uk` declares in its own `- Scope-Paths:` and will legitimately have edited (its E-06 adds a pin and corrects a docstring); a changed assertion there is expected and must be shown to be an ADDITION or a correction, never a relaxation of either named pin.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the SHAPE A reconstruction output showing the three stages (no-outcome first turn, completing defect re-ask, re-collection) and the final recorded disposition. Assert and paste BOTH halves: the item at `substantially-complete` or better, AND the sibling states showing none is `dependency-blocked`. Showing only the disposition FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the SHAPE B reconstruction showing exactly one re-dispatch within budget rather than a terminal block, WITH the per-item counter's value beside each outcome (`dy9ymn` E-04 keeps it on the item mirroring `integration_attempts`); a status alone cannot distinguish a retry that fired once because the budget allowed one from a retry that fired once because the code hardcoded one.
    Then paste the collision case: a turn both truncated and rescued, showing it rescored and NOT retried. Additionally paste the evidence that the ordering holds IN GENERAL by showing `dy9ymn`'s conjunction refused for a rescued turn on the TWO LOAD-BEARING conditions (outcome file present; lane `commits_ahead > 0`), and state explicitly that the head-unchanged and clean-tree conditions are VACUOUS on an isolated turn and therefore form no part of the argument. An argument resting on those two, or a claim that all four conditions are violated on an isolated lane, FAILS this item as unsound even if its conclusion is right.
    A single passing example without the general argument also FAILS this item, because the cost of the ordering being accidental is re-dispatching committed work.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST NOT execute until a human approves it (`aw set approved svacmz --by-human`). Its `- Item-Dependencies: executed:skn8uk, executed:ty7w6o, executed:dy9ymn` edges are re-checked at dispatch and are load-bearing rather than decorative: the parent asks for verification against the MERGED result, and because each execute item runs in its own isolated worktree, only a plan dispatched after all three siblings have merged can observe that state. The runner sorts by dependency depth as its first key, so this child is queued last in the Set by construction.

THIS PLAN IS CURRENTLY DEPENDENCY-BLOCKED BY A SIBLING'S UNRESOLVED REVIEW FINDING, and that is a live
gate rather than a theoretical one, so do not read the approval sentence above as the only thing standing
between this plan and a run. MEASURED AT REVIEW by invoking the evaluator directly
(`check_engine.evaluate_ipd_dependencies` on this file): `check.ipd-dependency-findings-blocked`, detail
"dependency `executed:ty7w6o` resolves but does not satisfy the edge: ty7w6o: review finding PR-001 is
high/open and unresolved". `aw check` reports the same rule against this file at `error` severity. The
mechanism is shared and therefore not bypassable per surface: `_findings_block_reason`
(`runner_shared.py:10240`) delegates to `review_findings.subject_gating_blocks`, the same predicate
`aw check`, `ipd_set_plan` and both host runners consume, and each host refuses an execute-action
dependency on it (`oc_runipd.py:3761-3765`). So `aw oc run reaskscore` will mark THIS item
`dependency-blocked` and continue, exactly as it would for an unmet `executed:` edge.
WHAT CLEARS IT IS WORK ON `ty7w6o`, NOT AN EDIT HERE. `ty7w6o` PR-001 is HIGH and `open` (its `aw backlog
set` route printed `unchanged` and wrote no history), and its own `- Readiness:` is `no-go`. Removing this
plan's `executed:ty7w6o` edge would silence the gate while destroying the property the edge exists for
(observing the MERGED result), so it is the wrong fix and is explicitly not authorized here. `s0gnha`
PR-005 is likewise HIGH and `open`, which blocks the parent on the same rule. Recorded as OQ-02.

WHY THIS PLAN EXISTS, recorded so a later reader does not mistake it for padding: the orchestrator coverage gate refused `aw oc run reaskscore` on 2026-09-19 because `s0gnha` carried E-02 and E-03 with no child covering them. The remedy the gate names is to add a child owning that work and leave the parent's checklist intact, which is exactly what this plan does. Do NOT respond to a future firing of that gate by deleting a parent's items.

On completion: append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` as a post-gate lifecycle step via `aw ipd finalize`, never as a checklist item. Commit path-scoped; never push.
