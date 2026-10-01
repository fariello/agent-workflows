# IPD: State the deferral passthrough's real reachability and stop the rescore docstring citing a comment that no longer exists

- Date: 2026-09-29
- Kind: child
- Concern: `runner_shared.reconcile_disposition`'s deferral passthrough (`if item.get("status") == INTEGRATION_DEFERRED_STATUS`) is DEAD on `execute_item_core`'s first score, because `execute_item_core` writes `item["status"] = "running"` at dispatch, and it is ALSO dead on the post-re-ask rescore, because `record_integration_refusal` (the only writer of `merge-retry`) runs LATER in the same body than the rescore does. `rescore_is_an_improvement`'s docstring nonetheless directs a reader to "the comment above `reconcile_disposition`'s deferral passthrough, `oc_runipd.py:6120-6132`", and that comment NO LONGER EXISTS: commit `6b94a4d9` deleted the host copy when it collapsed the function into `runner_shared`, and `oc_runipd.py` is now 5296 lines, so the cited range is past end of file. So the one reachable caller is documented by a dangling pointer, and two live comments overstate what the branch does.
- Scope: Correct the two comments that misdescribe the deferral passthrough (the dangling `oc_runipd.py:6120-6132` citation in `rescore_is_an_improvement`, and `reconcile_disposition`'s docstring rung list plus the `runrecon-02` comment that calls the branch a fall-through the exit-code fallback shares), state the passthrough's REAL reachable caller by symbol, and add a behavioral test pinning both the branch's surviving contract and its unreachability from `execute_item_core`'s two scoring points. KEEPS THE BRANCH: it is live via `reattempt_deferred_integrations` -> `resume --retry-incomplete`, so deleting it would be a behavior change, and this plan proves that rather than assuming it. EXCLUDES deleting or reordering any branch of `reconcile_disposition`, EXCLUDES touching `rescore_is_an_improvement`'s refusal list or `RESCORE_DISPOSITION_RANK`, and EXCLUDES the three other stale `oc_runipd.py:<line>` citations the same file carries (a separate class, filed not fixed).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_deferral_passthrough_reachability.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: ddzc4h
- Set: defpass
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: gyam7x

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: gyam7x verified (set defpass, attempt 1).
- 2026-09-30 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 through PR-007, all FIXED in place. Reviewed at HEAD `f2326296` in an isolated lane; typed record at `.aw/records/reviews/20260929-defpass-01-gyam7x-state-the-deferral-passthrough-s-real-reachability-and-stop.review.md`. `aw ipd lint --phase author` reported clean with one `IPD-Z602` advisory BEFORE semantic review; `--phase review-finalize` conforms with no advisory after revision.
  ALL EIGHT FINDINGS RE-DERIVED BY RUNNING CODE AND ALL EIGHT HOLD. `oc_runipd.py` is 5278 lines against a cited range ending at 6132, so F-05's citation is past EOF. The ordering: `execute_item_core` spans 30498 to 34542, the `"running"` write at 30905, first score 31694, rescore 32214, in-body refusals 32818/34075/34087, all after it. `item["status"] = decision.status` at 10213 is the sole writer anywhere in `agent_workflows/` and sits inside `record_integration_refusal`. `merge-retry` is absent from all three `TERMINAL_STATES` and `outcome_precedence_disposition` returns `None` for it. AND EVERY ASSERTION THE PLAN ONLY SPECIFIES WAS DEMONSTRATED: all three E-05 assertions run as written, the recorder driven through the harness's own `reconcile=` seam captures `['running', 'fail-verify']`, and E-06's falsification was performed in place (assertion (1) returns `fail-verify` at exit 0 and `fail-gate` at nonzero with the branch deleted; (2) and (3) unchanged), then reverted with `agent_workflows/` clean.
  THREE HIGH FINDINGS. PR-001 and PR-002: FIVE deferred rows named no durable carrier, so `check.ipd-uncarried-obligation` reported this plan at `error` and it could not have reached `approved`; four are genuine non-tasks and now carry `Carrier-Declined`, while OQ-01 deferred real work to an item that DID NOT EXIST, so the reviewer filed `ma8aig` carrying the four-citation sweep plus OQ-01's design question with all seven offsets re-resolved. PR-003: E-06 told the executor to copy the tree OUTSIDE the worktree, which violates the lane contract and defeats the driver's integration, for a two-line mutation revertible by one path-scoped command; E-06 now mutates in place with the restore proof required.
  FOUR FURTHER FINDINGS. PR-004: E-05's assertion (3) could have been satisfied by a scripted recorder, which is exactly the weakness the plan's own F-07 identifies in the existing coverage, so it now must DELEGATE to the real function and name the outcome pairing that actually reaches the rescore. PR-005: the rescore does NOT see `running`, it sees the first score's own result (`item["status"] = disposition` at 32051 runs between them), which makes the unreachability structural rather than an ordering accident; recorded as F-10 and pinned by a count assertion. PR-006: F-02's list of intervening status assignments omitted `fail-gate`. PR-007: the gate lacked the conditional runner-versus-executor finalize ownership.
  `IPD-Z602` ON E-01 WAS INVESTIGATED BY DECOMPOSITION, not waved through: sub-facts (a) and (b) are the same comparison stated twice and (a) through (c) are answered by one sorted position list, so the correct split is two items and not four. The citation check became E-07 because it reads a different file and has its own failure mode (past EOF versus resolves-to-wrong-code); the ordering fact was restructured as ONE proof and the advisory cleared.

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `ddzc4h`. GATE NOTE: the item carries NO `- Blocks-Release:`, so this plan inherits none; `- Work-Kind: chore` and `- Priority: low` are INHERITED from the item and are correct, because no user-perceptible behavior changes (the code edits are comments; the only new executable code is a test). THE ITEM'S CENTRAL CLAIM VERIFIES, AND ITS SCOPE WAS TOO NARROW IN ONE DIRECTION AND TOO BROAD IN ANOTHER. VERIFIED: `execute_item_core` writes `item["status"] = "running"` before dispatch (`runner_shared.py:30868`), and the first score at `runner_shared.py:31657` therefore cannot see `merge-retry`, so the passthrough is dead on the first score exactly as the item says. TOO NARROW: the item asks only whether the passthrough has "ANY reachable caller in `execute_item_core`", and the answer is that it has a reachable caller OUTSIDE it - `reattempt_deferred_integrations` sets `merge-retry` through `record_integration_refusal` (`runner_shared.py:10173`), the run ends, and `resume --retry-incomplete` requeues a `merge-retry` item (`oc_runipd.run_queue`'s status set names both `integration-deferred` and `merge-retry`), after which a LATER turn's `reconcile_disposition` can legitimately see a deferral the item still carries. So the branch is NOT dead code and MUST NOT be deleted; the defect is purely descriptive. TOO BROAD, CORRECTED HERE: the item's hypothesis that "the deferral is only ever set downstream by `record_integration_refusal`" is CONFIRMED (that is the sole `item["status"] = decision.status` write of `merge-retry`, and `deferred_integration_items` selects on it), which is what makes the item's suspicion about the comment correct. A THIRD DEFECT NOT IN THE ITEM was found by following the citation and is in scope because it is the same sentence: the cited comment was DELETED by `6b94a4d9` and the line range is past EOF, so the docstring points a reader at nothing. NOTHING HERE IS OBSOLETE: grepping the 137 pending plans for `reconcile_disposition` / `rescore_is_an_improvement` returns four files and none touches these comments (`vbhat9` deliberately excludes `runner_shared.py`, `entv1d` cites the function in a finding only, `oi0sv9` cites the `StopAtCheckpoint` call site, `wqk5s2`/`oi0sv9` neither reads nor writes the passthrough).

## Goal

Make the deferral passthrough's documentation say what is true: name its one REACHABLE route (a deferral that outlives its run and is requeued by `resume --retry-incomplete`), drop the claim that it is reachable as a first-score fall-through, and replace the dangling `oc_runipd.py:6120-6132` pointer with a live symbol citation. Lock the result with a behavioral test that both exercises the branch through its real route and proves it cannot fire at either of `execute_item_core`'s two scoring points. No runtime behavior changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Re-measure the three claims at execution HEAD

- [x] E-01 RE-MEASURE THE ONE ORDERING FACT BOTH COMMENT FIXES ASSERT, at execution HEAD rather than trusting this plan's authoring numbers, because `runner_shared.py` is the repository's highest-churn file and every offset below will have moved. THIS IS A SINGLE PROOF, not a list of checks: compute `execute_item_core`'s line span, then locate four constructs inside it by content string (`item["status"] = "running"`, `disposition, outcome = reconcile_disposition(`, `rescored, rescored_outcome = reconcile_disposition(`, and every `record_integration_refusal(`), and read the answer off ONE sorted position list. The claim it must support is that the `"running"` write precedes the first score and the rescore precedes every in-body refusal, which together mean neither scoring point can observe `merge-retry`. NOTE THE BODY-BOUNDS SUBTLETY review hit and authoring did not state: `record_integration_refusal` has call sites OUTSIDE `execute_item_core`, so filter to the calls inside the computed span or the ordering will appear false for an irrelevant reason. Record the measured positions for evidence; write NONE of them into a comment as a bare offset. IF THE ORDERING HAS CHANGED, STOP AND REPORT before E-03, because it is the single fact both rewrites assert and documenting an unproven route would reproduce the exact defect this plan exists to correct. Review measured at HEAD `f2326296`: span 30498 to 34542, write 30905, first score 31694, rescore 32214, in-body refusals 32818/34075/34087, all after it.
  - Depends on: none
  - Expected outcome: one sorted position list pasted, the in-body filtering stated explicitly, and the ordering conclusion drawn from it, or a STOP report that the ordering drifted.
  - Execution state: performed

- [x] E-07 RE-MEASURE THE DANGLING CITATION ITSELF, which is a separate fact from the ordering one and is what E-03 actually repairs. Confirm that `oc_runipd.py` still has FEWER lines than the largest offset the cited range names, so the range the docstring names (the one quoted in `rescore_is_an_improvement`, locatable by the content string `for why). By`) is genuinely past end of file rather than merely moved. Review measured `oc_runipd.py` at 5278 lines, so both endpoints are past EOF by a wide margin. IF the file has grown past 6132, do NOT proceed to E-03 on the assumption the citation is dangling: re-resolve what now sits at those lines and report, because a citation that resolves to the WRONG code needs different wording from one that resolves to nothing, and F-08 records three citations in this very file that fail the second way rather than the first.
  - Depends on: none
  - Expected outcome: the host file's line count pasted beside the cited range, with an explicit statement of which failure mode applies (past EOF, or resolves-to-wrong-code).
  - Execution state: performed

- [x] E-02 PROVE the passthrough's REACHABLE route exists before documenting it, so E-03 states a measured fact and not a plausible story. Establish by reading code that all three links hold: (i) `record_integration_refusal` is the ONLY writer of `INTEGRATION_DEFERRED_STATUS` onto `item["status"]` (locate by `item["status"] = decision.status`; confirm no other assignment of that constant to an item status exists in `agent_workflows/`); (ii) `reattempt_deferred_integrations` calls it for an item whose lane refused integration; and (iii) each host's `run_queue` `--retry-incomplete` status set contains BOTH `"merge-retry"` and the pre-rename `"integration-deferred"`, so a deferral that outlived its run is requeued rather than stranded. Also record the one fact that makes the branch matter: `merge-retry` is NOT in `TERMINAL_STATES` on either host, so without the explicit branch the exit-code fallback would relabel it to a TERMINAL status and destroy the deferral.
  - Depends on: E-01
  - Expected outcome: the writer-to-requeue chain confirmed link by link with each link cited by symbol, plus a recorded check that `merge-retry` is absent from both hosts' `TERMINAL_STATES`.
  - Execution state: performed

### Task group 2: Correct the three misleading comments

- [x] E-03 REPLACE the dangling citation in `runner_shared.rescore_is_an_improvement`'s docstring. Locate the sentence by its content string `for why). By` (in the paragraph beginning `THREE STATUSES ARE NEVER REPLACEABLE IN EITHER DIRECTION`), which currently directs the reader to `the comment above :func:`reconcile_disposition`'s deferral passthrough, `oc_runipd.py:6120-6132``. Cite the LIVE location by symbol instead (the passthrough inside `runner_shared.reconcile_disposition`), with NO bare line offset. ALSO CORRECT THE CLAIM THAT SENTENCE MAKES, which E-01(c) measures: the docstring asserts `merge-retry` "is NOT in `DEFECT_REASK_SKIPPED_STATUSES`, so a re-ask can fire on a deferred item and reach the rescore", and while the membership half is TRUE the conclusion is NOT, because the only writer of that status runs later in `execute_item_core` than the rescore does. Restate it as what it is: defence in depth, for the same reason the paragraph's next two sentences already give for `interrupted` and `unknown_outcome`. DO NOT change the `never_replaceable` tuple, the rank table, or any behavior; this is docstring text only, and the entry stays.
  - Depends on: E-02
  - Expected outcome: `rescore_is_an_improvement`'s docstring cites a location that exists, no longer claims the deferral is a live pre-rescore value, and keeps `merge-retry` in the refusal tuple with its retention justified as defence in depth; no executable line of the function changes.
  - Execution state: performed

- [x] E-04 CORRECT the two comments in `reconcile_disposition` itself that describe the passthrough as a fall-through of the ordinary scoring path. First, the `runrecon-02` comment above the outcome read (locate by the content string `declines to answer still falls through to the deferral passthrough and the exit-code fallback`): it lumps the passthrough together with the exit-code fallback as things reached when the precedence helper declines, which is true only in the LATER-TURN case and misleads a reader into thinking a first score can land there. Second, the function's own docstring rung list (locate by the content string `4. Integration deferred status fallback.`): the word `fallback` is what makes rung 4 read like a sibling of rung 5. In BOTH, name the ONE route E-02 established (a prior turn's deferral, re-scored on a later turn after `--retry-incomplete` requeued the item) and say plainly that `execute_item_core`'s own two scoring points cannot reach it. Keep both edits to comment and docstring text; change no branch, no ordering, and no return value.
  - Depends on: E-02
  - Expected outcome: both comments describe the passthrough by its real route and explicitly exclude the two `execute_item_core` scoring points, with the branch, its position after the outcome block, and its return value untouched.
  - Execution state: performed

### Task group 3: Lock it behaviorally

- [x] E-05 ADD `tests/test_deferral_passthrough_reachability.py` pinning the passthrough's surviving CONTRACT and its unreachability as OUTCOMES, never as code structure. Three behavioral assertions, each driving real code and asserting on real returns: (1) THE CONTRACT: call `reconcile_disposition` on an item whose `status` is `INTEGRATION_DEFERRED_STATUS` with exit code 0 AND with a nonzero exit code, and assert it returns `merge-retry` BOTH times, which is what keeps a later turn from destroying a deferral the exit-code fallback would otherwise relabel; assert the returned status is absent from `TERMINAL_STATES` in the same test, so the test states WHY it matters. (2) THE NEGATIVE CONTROL that proves assertion (1) is not vacuous: the same call on an item whose `status` is `"running"` (the value `execute_item_core` actually holds at its first score) must NOT return `merge-retry`, and must return the exit-code fallback instead. (3) THE UNREACHABILITY, measured by OBSERVATION rather than by reading source: drive `execute_item_core` through the established harness in `tests/test_defect_report.py::RescoreAfterAReaskTests` and pass the recorder through that harness's OWN `reconcile=` parameter, which review verified exists on its `_drive` helper and installs the callable with `mock.patch.object(oc_runipd, "reconcile_disposition", reconcile)`; the recorder must DELEGATE to the real `reconcile_disposition` after capturing, so the turn proceeds normally and the assertion is about production behavior rather than about a stub (this is precisely where F-07's existing test is weak). Capture `item["status"]` AS PASSED at every call and assert that NO captured value is `merge-retry` across both scoring points. REVIEW RAN THIS EXACT PROBE in this lane and measured `['running', 'fail-verify']` from two calls, so assert the COUNT is two as well: the two captured values are the first score seeing `running` and the rescore seeing the FIRST SCORE'S OWN RESULT, which is a sharper statement than F-02 makes and is what makes the rescore's blindness structural rather than incidental. Drive it with `first_outcome=NO_REPORT_PARTIAL` and `reask_outcome=REASK_STILL_PARTIAL`, which is the pairing that actually triggers a re-ask and therefore reaches the rescore; a pairing that completes on the first outcome yields ONE call and would make the assertion vacuous. The test MUST NOT use `inspect`, `ast`, regex over source, or any substring search of production code, MUST NOT count call sites, and MUST NOT assert any comment text survives. Name in its module docstring that assertion (3) is the one that would go red if a future change made the status reachable there, which is a legitimate signal to re-read E-03/E-04's wording rather than to loosen the test.
  - Depends on: E-01
  - Expected outcome: a new test file whose three assertions pass, whose negative control fails if the passthrough is deleted, and which reads no production source text.
  - Execution state: performed

- [x] E-06 PROVE the new test can FAIL, because a reachability test that passes trivially is worse than none. MUTATE IN PLACE AND REVERT BY PATH NAME; do NOT copy the tree outside the worktree. Delete the two-line passthrough from `reconcile_disposition` in `agent_workflows/runner_shared.py`, run the new test file, record that E-05's assertion (1) goes RED, then restore with `git checkout -- agent_workflows/runner_shared.py` and prove `git status --short` shows the file unmodified. THE OUTSIDE-THE-WORKTREE INSTRUCTION THIS REPLACES WAS WRONG ON TWO COUNTS, recorded so it is not reinstated: an executing agent's authorized workspace IS the lane and writing a tree copy outside it defeats the driver's integration, and the copy is unnecessary because the mutation is two lines reverted by one path-scoped command. Never revert with `git stash`, a bare `git reset`, or `git checkout .`, since this checkout is shared. ALSO record that assertions (2) and (3) still PASS with the branch deleted, which is the honest statement of what each assertion covers: only (1) guards the branch's existence, while (2) and (3) describe the surrounding reachability. Review performed this exact mutation in this lane and measured assertion (1) returning `('fail-verify', None)` at exit 0 and `('fail-gate', None)` at nonzero (both RED against an expected `merge-retry`), assertion (2) unchanged, and assertion (3)'s captured list still `['running', 'fail-verify']`. Then run the full suite BARE on the restored tree and paste the summary line.
  - Depends on: E-05
  - Expected outcome: pasted red output for assertion (1) naming the observed wrong statuses, a recorded note that (2) and (3) are insensitive to that deletion, `git status --short` proving `agent_workflows/runner_shared.py` restored, and a pasted bare full-suite summary.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan's subject matter IS an expired offset, so every citation it writes obeys the rule it is enforcing.
- TESTS ASSERT OUTCOMES, NOT CODE STRUCTURE (`GUIDING_PRINCIPLES` P16, restated in `AGENTS.md`): no `inspect`, no `ast`, no regex over production source, no caller-count or symbol-census assertions, and no assertion that a comment or docstring string survives. This constrains E-05 sharply, since the natural way to test "this branch is unreachable" is to read the source, and that is exactly what is forbidden; E-05 therefore observes real calls instead.
- `reconcile_disposition` is a SINGLE SHARED DEFINITION, and both hosts expose the same object: `tests/test_recovone_single_definition.py::TestSingleDefinitionIdentity::test_identity_pins` asserts `assertIs` between each host attribute and `runner_shared`'s. So one edit in `runner_shared.py` reaches both hosts and neither host file needs to appear in `Scope-Paths`.
- The status vocabulary is DUAL: `l2mzxn` renamed `integration-deferred` to `merge-retry`, and both spellings remain readable because the requeue set is matched against statuses read from DURABLE run directories written before the rename. Any prose this plan writes must use the constant (`INTEGRATION_DEFERRED_STATUS`) or both spellings, never the legacy one alone.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S CORE CLAIM IS TRUE. `execute_item_core` sets `item["status"] = "running"` before dispatch and saves state; its first `reconcile_disposition` call comes several hundred lines later in the same body. So at the first score `item["status"]` is `"running"`, never `merge-retry`, and the passthrough cannot fire. | `runner_shared.py:30868` (`item["status"] = "running"`, immediately followed by `save_state`); first score at `runner_shared.py:31657`. |
| F-02 | THE RESCORE CANNOT SEE A DEFERRAL EITHER, AND FOR A STRONGER REASON THAN THE ITEM GIVES. The item notes `merge-retry` is not in `DEFECT_REASK_SKIPPED_STATUSES` (confirmed: the frozenset holds 12 statuses and `merge-retry` is not among them), and infers a re-ask could therefore reach the rescore carrying one. But ORDER forbids it: the rescore (locate by `rescored, rescored_outcome = reconcile_disposition(`) precedes every `record_integration_refusal(` call in this body, the nearest being the review arm's (locate by `review_decision = record_integration_refusal(`) and the execute arm's later still. Between the `"running"` write and the rescore, the only assignments to `item["status"]` are `fail-gate`, `fail-lane` (three times), `fail-begin`, `interrupted`, and the scored `disposition` itself. CORRECTED AT REVIEW: authoring's list omitted `fail-gate`, which does not weaken the conclusion (no intervening assignment writes the deferred status, which is the only thing that matters) but the enumeration is now complete as measured. | `runner_shared.DEFECT_REASK_SKIPPED_STATUSES`; the `rescored, rescored_outcome = reconcile_disposition(` call versus the three `record_integration_refusal(` call sites in `runner_shared.execute_item_core` and `runner_shared.reattempt_deferred_integrations`. Probed: `INTEGRATION_DEFERRED_STATUS in DEFECT_REASK_SKIPPED_STATUSES` -> `False`. |
| F-03 | THE BRANCH IS NEVERTHELESS LIVE, so it must NOT be deleted, and this is the correction to the item's framing. `record_integration_refusal` writes `item["status"] = decision.status` (which is `merge-retry` when the ladder defers), the run can END with the item still deferred, and each host's `--retry-incomplete` requeue set explicitly names both `"integration-deferred"` and `"merge-retry"` with an in-tree comment saying a deferral "can outlive its run". A later turn's `reconcile_disposition` can then legitimately observe the status. | `runner_shared.py:10173`; `oc_runipd.run_queue`'s requeue status set (comment `integpath-03 (`51vw4y`): a DEFERRED integration can outlive its run`); twin in `agy_runipd`. |
| F-04 | WITHOUT THE BRANCH THE DEFERRAL WOULD BE DESTROYED, which is why F-03 matters rather than being a curiosity. `merge-retry` is deliberately absent from `TERMINAL_STATES` on both hosts, so `outcome_precedence_disposition` returns None for it and control would reach the exit-code fallback, relabelling it `fail-verify` (exit 0) or `fail-gate` (nonzero) - both TERMINAL, so the item would never be re-attempted. | Probed: `merge-retry` in shared / oc / agy `TERMINAL_STATES` -> `False, False, False`; `outcome_precedence_disposition(None, {"disposition": "merge-retry"})` -> `None`; `fail-verify` and `fail-gate` both in `TERMINAL_STATES` -> `True`. |
| F-05 | THE CITED COMMENT NO LONGER EXISTS, which the item does not mention and which is the most concrete defect here. `rescore_is_an_improvement`'s docstring cites `oc_runipd.py:6120-6132`; `oc_runipd.py` is 5296 lines. The comment was real when cited: it was added by `11013cb1` as `integpath-03 (`51vw4y`) E-01: PASS THE NON-TERMINAL DEFERRAL THROUGH, EXPLICITLY` / `THIS IS THE SILENT-DOWNGRADE TRAP`, and `6b94a4d9` deleted the host copy when it replaced the body with `reconcile_disposition = runner_shared.reconcile_disposition`. The prose it pointed at did NOT survive the move: `grep -n 'SILENT-DOWNGRADE' agent_workflows/*.py` matches nothing on this tree. | `wc -l agent_workflows/oc_runipd.py` -> `5296`; `git log -S 'SILENT-DOWNGRADE TRAP'` -> `6b94a4d9`, `11013cb1`; `git show 6b94a4d9 -- agent_workflows/oc_runipd.py` shows the block deleted and replaced by the one-line rebind. |
| F-06 | THE SURVIVING COMMENTS UNDERSTATE AND OVERSTATE IN DIFFERENT PLACES, so both need the same correction. `reconcile_disposition`'s docstring calls rung 4 `Integration deferred status fallback.`, and the `runrecon-02` comment says whatever the precedence helper "declines to answer still falls through to the deferral passthrough and the exit-code fallback below". Both frame the passthrough as a sibling of the exit-code fallback on the ordinary path, which F-01/F-02 refute for every `execute_item_core` score. | `runner_shared.py:29573` (docstring rung 4); `:29688` (the `falls through to the deferral passthrough` comment). |
| F-07 | EXISTING COVERAGE PINS THE CONTRACT BUT NOT THE REACHABILITY, which is the gap E-05 fills. `tests/test_runner_shared.py` drives `reconcile_disposition` on a `merge-retry` item for both hosts and asserts the passthrough returns it (exit code 0 only, no nonzero case, no negative control), and `tests/test_defect_report.py::RescoreAfterAReaskTests::test_deferral_behavior` pins the rescore's refusal using a SCRIPTED `reconcile_disposition` that RETURNS `merge-retry` - a stub, so it proves nothing about whether production can produce that value there. Nothing asserts the status is unreachable at either scoring point. | `tests/test_runner_shared.py::test_deferred_item_dependency_cascade_and_reconcile` (comment `Reconcile disposition passes deferral through`); `tests/test_defect_report.py::test_deferral_behavior`'s `def scripted(...)` returning `R.INTEGRATION_DEFERRED_STATUS`. |
| F-08 | THREE MORE STALE `oc_runipd.py:<line>` CITATIONS SURVIVE IN THE SAME FILE, found by scanning rather than assumed. `runner_shared.py` carries five such citations; besides F-05's, the two in the comments beginning `The pre-``pgq326`` dispatch branch` and `THE THREE FACTS, measured at execution inside` name host line ranges past EOF, and the ones in `SET_RETIREMENT_DONE_STATUS`'s comment and in `queue_artifact_path`'s docstring name host offsets that land on unrelated lines. They are the same defect class but a different sentence each, with no shared fix, so they are FILED and not swept here. | `grep -n 'oc_runipd\.py:[0-9]' agent_workflows/runner_shared.py` -> 5 matches; the four non-F-05 matches checked individually against `wc -l agent_workflows/oc_runipd.py` and against the content actually at each cited offset. |
| F-09 | ADDED AT REVIEW. THE PASSTHROUGH'S FULL CONTRACT AND ITS NEGATIVE CONTROL ARE BOTH DIRECTLY DEMONSTRABLE, so E-05's three assertions are known implementable rather than merely specified. Driving the real function on a temporary root: a `merge-retry` item returns `('merge-retry', None)` at BOTH exit codes, and a `running` item returns `('fail-verify', None)` at exit 0 and `('fail-gate', None)` at nonzero. And the E-05 assertion (3) recorder was RUN through the named harness's own `reconcile=` seam, capturing exactly `['running', 'fail-verify']` from two calls with no `merge-retry`. | four direct `reconcile_disposition` calls on a temp root; the recorder probe driving `RescoreAfterAReaskTests._drive(first_outcome=NO_REPORT_PARTIAL, reask_outcome=REASK_STILL_PARTIAL, reconcile=recorder)` |
| F-10 | ADDED AT REVIEW. THE RESCORE SEES THE FIRST SCORE'S OWN RESULT, NOT `running`, which is a sharper unreachability argument than F-02 makes. The captured pair is `['running', 'fail-verify']`: `item["status"] = disposition` runs between the two scoring points, so by the rescore the status is whatever the first score decided. Since every value the first score can return is either terminal or `merge-retry`-only-if-already-`merge-retry`, the rescore's blindness is structural rather than a happy ordering accident. E-05 now asserts the captured COUNT too, so a pairing that completes on the first outcome (one call, vacuous assertion) cannot satisfy it. | the recorder probe's captured list; the `item["status"] = disposition` assignment measured between the `"running"` write and the rescore |
| F-11 | ADDED AT REVIEW. FIVE OF THIS PLAN'S DEFERRED ROWS NAMED NO DURABLE CARRIER, so `check.ipd-uncarried-obligation` reported the plan at severity `error` and it could not have reached `approved`. Four are genuine non-tasks (a refused deletion, two explicit no-change decisions) and now carry `Carrier-Declined`; the fifth, OQ-01, deferred a real design question to a follow-up item that DID NOT EXIST, which is the shape the rule is built to catch. | `ce.check_durable_carrier(root)` before: `error`, "5 obligation(s) name no durable carrier"; after filing `ma8aig` and adding the declines: clean |
| F-12 | ADDED AT REVIEW. E-06's ORIGINAL INSTRUCTION TO COPY THE TREE OUTSIDE THE WORKTREE CONTRADICTS THE EXECUTION CONTRACT, and is also unnecessary. An executing agent's authorized workspace is the lane, and writing outside it defeats the driver's integration. The mutation is two lines: review deleted the passthrough in place, measured assertion (1) going RED as `('fail-verify', None)` and `('fail-gate', None)`, and reverted with one path-scoped `git checkout --`. | the in-place mutation run and its revert, with `git status --short` clean for `agent_workflows/` |

## Proposed changes (ordered, validatable)

1. Re-measure the ONE ordering fact both comment fixes assert, from a single sorted position list (E-01).
1b. Re-measure the dangling citation itself and state which failure mode applies, past EOF or resolves-to-wrong-code (E-07).
2. Confirm the writer-to-requeue chain that makes the branch live, and the `TERMINAL_STATES` absence that makes it necessary (E-02).
3. Repoint `rescore_is_an_improvement`'s dangling citation at a live symbol and downgrade its reachability claim to defence in depth (E-03).
4. Correct `reconcile_disposition`'s own docstring rung and the `runrecon-02` fall-through comment to name the real route (E-04).
5. Add the behavioral test: contract on both exit codes, negative control on `running`, and observed unreachability across both scoring points (E-05).
6. Prove assertion (1) can fail against a branch-deleted scratch copy, record what (2) and (3) do and do not cover, and run the bare suite (E-06).

## Deferred / out of scope (with reason)

- DELETING THE PASSTHROUGH IS REFUSED, not deferred. F-03 and F-04 together show the branch is reachable through `resume --retry-incomplete` and that its absence would convert a non-terminal deferral into a terminal status, destroying the lane's re-attempt. The item's phrasing ("whether the passthrough has ANY reachable caller") invites deletion; the measured answer is no.
  - Carrier-Declined: nothing is owed, because this row records a REFUSAL rather than postponed work. F-03 and F-04 measure the branch as live and its removal as destructive (re-verified at review: `merge-retry` is absent from all three `TERMINAL_STATES` and `outcome_precedence_disposition(None, {"disposition": "merge-retry"})` returns `None`, so control would reach the exit-code fallback and relabel a non-terminal deferral `fail-verify` or `fail-gate`, both terminal). Naming a carrier would schedule a deletion this plan argues against.
- THE OTHER FOUR STALE `oc_runipd.py:<line>` CITATIONS (F-08) are left alone. Each needs its own re-measurement of what the cited code now says and where it moved, and bundling them here would put four unrelated prose edits behind one review. Recommend a single follow-up backlog item covering all four, plus the question of whether a mechanical check should refuse a `<file>:<line>` citation past EOF in tracked source (which would also catch the `agy_runipd.py` offsets in the same `THE THREE FACTS, measured at execution inside` comment). THE ITEM NOW EXISTS: filed at review as `ma8aig`, carrying every offset re-resolved against both host files plus OQ-01's design question, so the sweep starts from measurement rather than from a rediscovery.
  - Carrier: ma8aig
- NO CHANGE TO `DEFECT_REASK_SKIPPED_STATUSES`. Adding `merge-retry` to it would make the docstring's claim true by construction and would also be a real behavior change (it would suppress a defect re-ask for a deferred item), which is out of this plan's descriptive fence and would need its own justification.
  - Carrier-Declined: deliberately nobody's task. This row records a change the plan argues AGAINST making, not one it postpones: the membership half of the docstring's claim is already true (measured at review: `INTEGRATION_DEFERRED_STATUS in DEFECT_REASK_SKIPPED_STATUSES` is `False` over a 12-status frozenset), and the fix for the false CONCLUSION is E-03's rewording, which is in scope. A carrier here would schedule a behavior change nobody wants.
- NO CHANGE TO `rescore_is_an_improvement`'s refusal tuple or rank table. The entry stays for the same defence-in-depth reason the paragraph already gives for its two neighbours.
  - Carrier-Declined: no outstanding work. The tuple and the rank table are CORRECT as they stand and this plan changes neither; the defect is the docstring sentence explaining the entry, which E-03 fixes in scope. Naming a carrier would assert someone still owes an edit to code that measures right.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` receives comment and docstring edits only; the sole new executable code is a test file. The three other stale citations in the same file are deliberately untouched (F-08), carried by `ma8aig`. Note the backlog item filed at review is NOT in `- Scope-Paths:` because it was committed WITH the review rather than by the executor; the executor must not re-file it.
- Under-scope: the four remaining stale citations (F-08) and any mechanical guard against a past-EOF citation are not fixed here; both are carried by backlog `ma8aig`, FILED AT REVIEW (the plan as authored named no item, which `check.ipd-uncarried-obligation` reports at severity `error`; see F-11). Neither host driver file is edited, which is correct rather than a gap: the function is a single shared definition and both hosts rebind the same object (Step 0).

## Required tests / validation

- `python3 -m pytest tests/test_deferral_passthrough_reachability.py` for the new file, plus a run with `-o addopts=""` when per-test counts are needed.
- `python3 -m pytest tests/test_runner_shared.py tests/test_defect_report.py tests/test_recovone_single_definition.py` for the three files whose existing assertions touch `reconcile_disposition`, the rescore, and the single-definition identity.
- `python3 -m pytest` BARE for the full suite (the configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do not add flags).
- The falsification run in E-06, performed by deleting the passthrough IN PLACE inside this lane and reverting with `git checkout -- agent_workflows/runner_shared.py`. Not a tree copy outside the worktree: the lane IS the authorized workspace, and a two-line mutation reverted by one path-scoped command needs no copy.

## Spec / documentation sync

N/A with reason. No `.spec.md` governs `reconcile_disposition`'s comment text, and no `- Scope-Paths:` entry is a spec file, so neither runner will announce a declared spec edit for this plan. The two specs that do govern nearby behavior are unchanged BY DESIGN and were checked rather than assumed: `c4gd2h` R22 (never record a disposition the runner did not observe) is untouched because no branch, ordering, or return value changes, and `25kzda` says nothing about the deferral passthrough's documentation. The documentation being corrected lives INSIDE the changed file, which is where this repository keeps it.

## Open questions

### OQ-01: Should a mechanical check refuse a `<file>:<line>` citation that points past end of file in tracked source?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: RESOLVED AS "DEFER THE DECISION, BUT NOT THE OBLIGATION", and the distinction is what changed at review. The authoring answer was substantively right and structurally incomplete: it deferred the question to a follow-up item that DID NOT EXIST, so `check.ipd-uncarried-obligation` reported this question at severity `error` (an obligation that "vanishes with no record" once the plan reaches `executed`). The reviewer filed `ma8aig` during review, carrying both the four-citation sweep and this design question, so the question now has a durable home and the row carries `- Carrier: ma8aig`. THE SUBSTANCE IS UNCHANGED AND WAS RE-MEASURED: the repository forbids a bare offset for IPD prose only (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`) and nothing checks offsets inside Python comments. Review resolved all seven host-line citations in `runner_shared.py` against both host files and the split is sharper than authoring stated: FOUR are past EOF (`oc_runipd.py` is 5278 lines, `agy_runipd.py` is 4162) and so are mechanically decidable, while THREE resolve to real lines that are wrong anyway, landing on `)`, on a bare `#`, and on an unrelated comment about closures. That is the measured case both for the cheap check and against relying on it, and it is now recorded where the decision will be taken.
- Carrier: ma8aig

### OQ-02: Is `--retry-incomplete` the ONLY route by which a `merge-retry` item reaches `reconcile_disposition` again?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as "it is the only route that reaches a NEW TURN's score, and one other route reaches the status without a score". The requeue set in each host's `run_queue` is what converts a surviving deferral back to `queued` for a fresh turn. The in-run ladder (`reattempt_deferred_integrations`) re-attempts the INTEGRATION with no agent turn and therefore never calls `reconcile_disposition` at all, and `resolve_exhausted_deferrals` rewrites the status to `fail-merge` directly. This distinction is exactly what E-04 must state, which is why it is answered in the plan rather than left for the executor: the branch's route is "a later turn after a requeue", not "the ladder".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the sorted position list E-01 computes: `execute_item_core`'s line span, the `item["status"] = "running"` write, the first-score and rescore `reconcile_disposition` calls, and every `record_integration_refusal(` call, with the out-of-body call sites shown as EXCLUDED and the filtering stated (review measured three in-body and two outside). Then state, on one line each, that the write precedes the first score and that the rescore precedes every in-body refusal, which is the conjunction both comment rewrites assert. If any position drifted from this plan's numbers the pasted output must show the NEW value and the report must say so explicitly rather than silently adopting it. The host-file line count belongs to V-07, not here.
  - Observed evidence: PASS. Measured at execution HEAD: write (31639) precedes first score (32428) and rescore (32958) precedes all in-body refusals (33570, 34832, 34844).
    `execute_item_core` line span: 31221 to 35298 (drifted from review span 30498 to 34542 due to intervening commits in `runner_shared.py`).

    All occurrences of constructs in `runner_shared.py`:
    Line 10278: `def record_integration_refusal(` [outside `execute_item_core`: EXCLUDED]
    Line 10668: `decision = record_integration_refusal(` in `reattempt_deferred_integrations` [outside `execute_item_core`: EXCLUDED]
    Line 31103: `record_integration_refusal(` in `run_review_lane_in_worktree` [outside `execute_item_core`: EXCLUDED]
    Line 31639: `item["status"] = "running"` [inside `execute_item_core`: INCLUDED]
    Line 32428: `disposition, outcome = reconcile_disposition(` [inside `execute_item_core`: INCLUDED]
    Line 32958: `rescored, rescored_outcome = reconcile_disposition(` [inside `execute_item_core`: INCLUDED]
    Line 33570: `review_decision = record_integration_refusal(` [inside `execute_item_core`: INCLUDED]
    Line 34832: `decision = record_integration_refusal(` [inside `execute_item_core`: INCLUDED]
    Line 34844: `decision = record_integration_refusal(` [inside `execute_item_core`: INCLUDED]

    Sorted position list inside `execute_item_core` (out-of-body call sites filtered out):
    Line 31639: `item["status"] = "running"`
    Line 32428: first score: `disposition, outcome = reconcile_disposition(...)`
    Line 32958: rescore: `rescored, rescored_outcome = reconcile_disposition(...)`
    Line 33570: in-body refusal 1: `record_integration_refusal(...)`
    Line 34832: in-body refusal 2: `record_integration_refusal(...)`
    Line 34844: in-body refusal 3: `record_integration_refusal(...)`

    The write `item["status"] = "running"` (line 31639) precedes the first score (line 32428).
    The rescore (line 32958) precedes every in-body refusal (lines 33570, 34832, 34844).
    Neither scoring point can observe `merge-retry`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `grep -n` output showing every assignment of `INTEGRATION_DEFERRED_STATUS` (or `decision.status`) to an item status across `agent_workflows/`, demonstrating `record_integration_refusal` is the sole writer; paste the `--retry-incomplete` status set from ONE host showing both `"integration-deferred"` and `"merge-retry"` present; and paste the executed probe `python3 -c` output for `merge-retry` membership in `runner_shared`, `oc_runipd`, and `agy_runipd` `TERMINAL_STATES` (all three must print False) plus `outcome_precedence_disposition(None, {"disposition": "merge-retry"})` printing `None`. A missing link means E-03/E-04's wording is unsupported: stop and report rather than documenting an unproven route.
  - Observed evidence: PASS. Confirmed record_integration_refusal is sole writer to item status, oc requeue set contains both spellings, and merge-retry is absent from all TERMINAL_STATES.
    Grep for assignment of `INTEGRATION_DEFERRED_STATUS` or `decision.status` to item status across `agent_workflows/`:
    `agent_workflows/runner_shared.py:10354:    item["status"] = decision.status`
    (No other assignment of `INTEGRATION_DEFERRED_STATUS` or `decision.status` to an item status exists across `agent_workflows/`).

    `--retry-incomplete` status set from `agent_workflows/oc_runipd.py:3476-3490`:
    ```python
    3476:                 "integration-blocked",
    3477:                 "merge-conflict",
    3478:                 # integpath-03 (`51vw4y`): a DEFERRED integration can outlive its run (an interrupt or
    3479:                 # a crash between the deferral and the next loop iteration), and it is by definition
    3480:                 # non-terminal, so a resume must be able to pick it up. Listed here rather than left to
    3481:                 # the ladder alone because the ladder only runs inside a live dispatch loop.
    3482:                 "integration-deferred",
    3483:                 # `l2mzxn` renamed all four. BOTH vocabularies are listed because this set is matched
    3484:                 # against a status read from a DURABLE run directory: the pre-rename spellings keep an
    3485:                 # already-stranded item recoverable, and the canonical ones cover every new run.
    3486:                 "merge-needs-human",
    3487:                 "merge-refused",
    3488:                 "merge-retry",
    3489:                 "merge-unchecked",
    3490:             }:
    ```

    Executed probe output for `merge-retry` membership and `outcome_precedence_disposition`:
    ```
    runner_shared.TERMINAL_STATES contains merge-retry: False
    oc_runipd.TERMINAL_STATES contains merge-retry: False
    agy_runipd.TERMINAL_STATES contains merge-retry: False
    outcome_precedence_disposition(None, {"disposition": "merge-retry"}): None
    fail-verify in TERMINAL_STATES: True
    fail-gate in TERMINAL_STATES: True
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the FULL edited paragraph of `rescore_is_an_improvement`'s docstring. Confirm by inspection, stating each as a separate line: (a) it contains no `oc_runipd.py:` substring and no bare line offset; (b) it cites the passthrough by symbol; (c) it no longer asserts a re-ask can reach the rescore carrying a deferral, and instead labels the entry defence in depth; and (d) `merge-retry` is STILL in the `never_replaceable` tuple. Paste `git diff --stat` for the file proving only comment/docstring lines changed in this item, and paste `python3 -m pytest tests/test_defect_report.py` output showing the rescore tests still pass, since they assert the behavior this docstring describes.
  - Observed evidence: PASS. rescore_is_an_improvement docstring cites live symbol without offsets, states defence in depth, keeps refusal tuple, and tests pass.
    Full edited paragraph of `rescore_is_an_improvement`'s docstring:
    ```python
    THREE STATUSES ARE NEVER REPLACEABLE IN EITHER DIRECTION, all as DEFENCE IN DEPTH against future
    rescore reachability rather than live pre-rescore states today. While
    :data:`INTEGRATION_DEFERRED_STATUS` (`merge-retry`) is NOT in
    :data:`DEFECT_REASK_SKIPPED_STATUSES`, it cannot be the `before` value at the rescore point
    either: `execute_item_core`'s only writer of that status runs later than the rescore, and
    relabelling a deferral would destroy it (see the deferral passthrough inside
    :func:`runner_shared.reconcile_disposition` for why). Similarly, `runner_stop.STOPPED_DISPOSITION`
    (`interrupted`) and `runner_stop.FORCED_DISPOSITION` (`unknown_outcome`) ARE both already in that
    skip set, so neither can be the `before` value at the rescore point today; their entries here are
    defence in depth against a future widening of the skip set.
    ```

    Confirmation by inspection:
    (a) The paragraph contains no "oc_runipd.py:" substring and no bare line offset.
    (b) It cites the passthrough by symbol (:func:`runner_shared.reconcile_disposition`).
    (c) It no longer asserts a re-ask can reach the rescore carrying a deferral, and instead labels the entry defence in depth.
    (d) `INTEGRATION_DEFERRED_STATUS` is STILL in the `never_replaceable` tuple:
    ```python
        never_replaceable = (
            INTEGRATION_DEFERRED_STATUS,
            runner_stop.STOPPED_DISPOSITION,
            runner_stop.FORCED_DISPOSITION,
        )
    ```

    `git diff --stat` for `agent_workflows/runner_shared.py`:
    `agent_workflows/runner_shared.py | 31 ++++++++++++++++++-------------`
    `1 file changed, 18 insertions(+), 13 deletions(-)`

    `python3 -m pytest tests/test_defect_report.py`:
    `23 passed in 4.39s`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste both edited comment blocks in full (the `reconcile_disposition` docstring rung list and the `runrecon-02` fall-through comment). Confirm on separate lines that each names the later-turn-after-requeue route, that each explicitly says `execute_item_core`'s own scoring points cannot reach the branch, and that neither describes rung 4 as a `fallback` sibling of rung 5. Paste `git diff` for `reconcile_disposition`'s body showing the executable lines are IDENTICAL (the `if item.get("status") == INTEGRATION_DEFERRED_STATUS:` branch, its position after the `outcome_precedence_disposition` block, and the return tuple all unchanged).
  - Observed evidence: PASS. Both reconcile_disposition comments updated to name later-turn requeue route and exclude execute_item_core scoring points; executable lines identical.
    Both edited comment blocks in full:

    1. `reconcile_disposition` docstring rung list:
    ```python
    Reconciles an item's terminal status from five rungs in strict precedence:
      1. Deliberate operator stops (`runstop foi1b3`): if stopped deliberately, returns STOPPED_DISPOSITION.
      2. Plan review actions: reviewed/approved if exit 0 and status permits, fail-gate otherwise.
      3. Executed plans: outcome_precedence_disposition against disk bucket and outcome file.
      4. Prior-turn deferral passthrough: preserves a prior turn's deferral re-scored on a later turn
         after `--retry-incomplete` requeued the item; `execute_item_core`'s own two scoring points
         cannot reach it.
      5. Exit code fallback: fail-verify if exit 0, fail-gate otherwise.
    ```

    2. `runrecon-02` fall-through comment:
    ```python
    # runrecon-02 (`fduoj4`) E-02: the outcome read and the bucket/outcome precedence are now the two
    # SHARED helpers above, so the CRASH path (`reconcile_interrupted`) honors the same rules from the
    # same code rather than from a second copy. The behavior here is unchanged: the rungs the helper
    # applies are the three this function applied inline, in the same order. If the helper declines to
    # answer, the deferral passthrough preserves a prior turn's deferral re-scored on a later turn after
    # `--retry-incomplete` requeued the item (a branch `execute_item_core`'s own two scoring points cannot
    # reach), before falling through to the exit-code fallback below. Both stay HERE because they are this
    # caller's and not the precedence's.
    ```

    Confirmation:
    Each block names the later-turn-after-requeue route via `--retry-incomplete`.
    Each explicitly states that `execute_item_core`'s own two scoring points cannot reach the branch.
    Neither describes rung 4 as a fallback sibling of rung 5.
    `git diff` shows `reconcile_disposition`'s executable lines are IDENTICAL:
    ```python
        established = outcome_precedence_disposition(bucket, outcome)
        if established is not None:
            return established, outcome
        if item.get("status") == INTEGRATION_DEFERRED_STATUS:
            return INTEGRATION_DEFERRED_STATUS, outcome
        return ("fail-verify" if exit_code == 0 else "fail-gate"), outcome
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_deferral_passthrough_reachability.py -o addopts=""` output showing every test passing with its node ids visible. Paste the new file's assertion for the observed-status recorder, showing it asserts on values CAPTURED FROM REAL CALLS and not on source text, and showing the recorder DELEGATES to the real `reconcile_disposition` rather than returning a scripted value: a recorder that scripts its return reproduces F-07's weakness and fails this item. Paste the captured list and the captured COUNT (review measured `['running', 'fail-verify']`, two calls), and state which `first_outcome`/`reask_outcome` pairing was used, since a pairing that completes on the first outcome yields one call and makes the assertion vacuous. Confirm on one line each that the file imports none of `inspect`/`ast`, performs no regex or substring search over any `agent_workflows/*.py` content, asserts no call counts as a correctness proxy, and asserts no comment text survives. Also confirm the nonzero-exit case and the `running` negative control are both present, since assertion (1) alone would pass against a broken implementation that returned `merge-retry` unconditionally.
  - Observed evidence: PASS. tests/test_deferral_passthrough_reachability.py added with 3 passing assertions observing real calls without source inspection.
    `python3 -m pytest tests/test_deferral_passthrough_reachability.py -o addopts="" -v`:
    ```
    tests/test_deferral_passthrough_reachability.py::DeferralPassthroughReachabilityTests::test_unreachability_observed_across_scoring_points PASSED [ 33%]
    tests/test_deferral_passthrough_reachability.py::DeferralPassthroughReachabilityTests::test_negative_control_running PASSED [ 66%]
    tests/test_deferral_passthrough_reachability.py::DeferralPassthroughReachabilityTests::test_passthrough_contract PASSED [100%]
    3 passed in 0.55s
    ```

    Observed-status recorder in `tests/test_deferral_passthrough_reachability.py`:
    ```python
        harness = test_defect_report.RescoreAfterAReaskTests()
        captured_statuses: list[Any] = []
        real_reconcile = runner_shared.reconcile_disposition

        def recorder(
            repo: Path,
            item: dict[str, Any],
            run_dir: Path,
            exit_code: int,
            plan_repo: Path | None = None,
        ) -> tuple[str, dict[str, Any] | None]:
            captured_statuses.append(item.get("status"))
            return real_reconcile(
                repo, item, run_dir, exit_code, plan_repo=plan_repo
            )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _run_dir, _state, _item, _events, _gate, launches = harness._drive(
                root,
                first_outcome=harness.NO_REPORT_PARTIAL,
                reask_outcome=harness.REASK_STILL_PARTIAL,
                reconcile=recorder,
            )
            self.assertEqual(2, len(launches))
            self.assertEqual(2, len(captured_statuses))
            self.assertEqual(["running", "fail-verify"], captured_statuses)
            self.assertNotIn(
                runner_shared.INTEGRATION_DEFERRED_STATUS, captured_statuses
            )
    ```

    Observed values:
    Captured list: `['running', 'fail-verify']`
    Captured count: 2
    Pairing used: `first_outcome=harness.NO_REPORT_PARTIAL`, `reask_outcome=harness.REASK_STILL_PARTIAL`

    Confirmation:
    The test file imports none of `inspect` or `ast`.
    It performs no regex or substring search over any `agent_workflows/*.py` content.
    It asserts no call counts as a correctness proxy.
    It asserts no comment text survives.
    Both the nonzero-exit case and the "running" negative control are present and exercised.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the RED output from running the new test file with the passthrough deleted IN PLACE, showing assertion (1) failing and naming BOTH observed wrong statuses (`fail-verify` at exit 0 and `fail-gate` at nonzero, in place of `merge-retry`). Paste the same run's result for assertions (2) and (3), which must PASS, and state in one line that this is the honest scope of each assertion rather than a defect in the test. Paste `git status --short` showing `agent_workflows/runner_shared.py` restored and unmodified, and state that the revert was by path name and NOT by `git stash`, a bare `git reset`, or `git checkout .`. Then paste the BARE `python3 -m pytest` summary line from the restored tree (the `N passed` line; do not add `-q`, which would suppress it). Do NOT report a scratch copy outside the worktree; if one was used, that is a contract violation to report rather than evidence to paste.
  - Observed evidence: PASS. In-place falsification confirmed assertion (1) fails naming fail-verify and fail-gate while (2) and (3) pass; restored cleanly; full suite passed.
    Red output from running `tests/test_deferral_passthrough_reachability.py` with passthrough deleted in place:
    ```
    =================================== FAILURES ===================================
    ________ DeferralPassthroughReachabilityTests.test_passthrough_contract ________

        def test_passthrough_contract(self) -> None:
    ...
    >           self.assertEqual(
                    {0: (expected, None), 1: (expected, None)},
                    results,
                    f"expected {expected} on both exit codes, got {results}",
                )
    E           AssertionError: {0: ('merge-retry', None), 1: ('merge-retry', None)} != {0: ('fail-verify', None), 1: ('fail-gate', None)}
    E           - {0: ('merge-retry', None), 1: ('merge-retry', None)}
    E           + {0: ('fail-verify', None), 1: ('fail-gate', None)} : expected merge-retry on both exit codes, got {0: ('fail-verify', None), 1: ('fail-gate', None)}

    tests/test_deferral_passthrough_reachability.py:49: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_deferral_passthrough_reachability.py::DeferralPassthroughReachabilityTests::test_passthrough_contract
    ========================= 1 failed, 2 passed in 1.11s ==========================
    ```

    Assertions (2) and (3) passed during that same run:
    ```
    tests/test_deferral_passthrough_reachability.py::DeferralPassthroughReachabilityTests::test_unreachability_observed_across_scoring_points PASSED [ 33%]
    tests/test_deferral_passthrough_reachability.py::DeferralPassthroughReachabilityTests::test_negative_control_running PASSED [100%]
    ```
    Only assertion (1) guards the branch's existence, while assertions (2) and (3) describe surrounding reachability.

    Restoration by path name:
    ```
    $ git checkout -- agent_workflows/runner_shared.py
    $ git status --short
    ?? tests/test_deferral_passthrough_reachability.py
    ```
    (Revert performed by path name, not `git stash`, bare `git reset`, or `git checkout .`).

    Bare full-suite summary from restored tree (`python3 -m pytest`):
    `3821 passed, 2 skipped, 3 warnings in 79.53s (0:01:19)`
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `wc -l agent_workflows/oc_runipd.py` beside the line range the `rescore_is_an_improvement` docstring cites (quote the citation as it stands pre-edit), and state on one line which failure mode applies: PAST EOF, or resolves-to-wrong-code. Review measured 5278 lines against a cited range ending at 6132, so past EOF. If the file has grown past the cited range, this item is satisfied ONLY by also pasting what now sits at those lines, because that case needs different wording from E-03 and is the shape F-08 records for three other citations in the same file.
  - Observed evidence: PASS. oc_runipd.py is 5223 lines against cited range 6120-6132; failure mode is PAST EOF.
    Line count of `agent_workflows/oc_runipd.py`:
    `5223 agent_workflows/oc_runipd.py`

    Pre-edit cited range in `rescore_is_an_improvement` docstring:
    `the comment above :func:`reconcile_disposition`'s deferral passthrough, `oc_runipd.py:6120-6132`, for why`

    Failure mode:
    PAST EOF (5223 < 6120 < 6132).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXECUTION CONTRACT. Commit only the two paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Run the suite BARE as `python3 -m pytest` and paste ACTUAL output for every test claim; do not claim a pass that was not run. Other agents and humans may be working concurrently in this checkout, so verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`; `runner_shared.py` is a high-traffic file and a co-worker's edit to it must not enter this commit.

WHAT AN EXECUTOR MUST NOT DO. Do not delete or reorder any branch of `reconcile_disposition`: F-03 and F-04 establish the passthrough is live through `resume --retry-incomplete` and that its removal would convert a non-terminal deferral into a terminal status. Do not add `merge-retry` to `DEFECT_REASK_SKIPPED_STATUSES` to make the old docstring claim true; that is a behavior change outside this fence. Do not touch the other four stale host-line citations (F-08); they are carried by backlog `ma8aig`, which was FILED AT REVIEW, so do not re-file it either. Do not copy the tree outside this lane for E-06's falsification: mutate in place and revert by path name (F-12). Do not satisfy E-05 with a source-reading test: the reachability assertion must observe real calls, per `GUIDING_PRINCIPLES` P16. Do not change backlog `ddzc4h`'s `- Status:` by hand; the runner sets `graduated` on verification.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` carries pasted, non-empty observed evidence, run `aw ipd lint --phase pre-transition` and finalize through the tooled path so the plan moves to `.aw/records/plans/executed/` with a scope-reconciled, path-scoped commit. TRANSITION OWNERSHIP IS CONDITIONAL: under a runner (`aw oc run` / `aw agy run`) the DRIVER owns the terminal transition and finalize, so an executing agent must NOT run `aw ipd finalize` itself; on a hand-run execution the executor finalizes through the sanctioned verb (`aw ipd finalize`, or `aw ipd set executed <plan>`). Either way NEVER hand-edit `- Status:` and NEVER `git mv` this file into `executed/`: a hand-rolled move skips the pre-transition checkpoint that is the only thing standing between an unvalidated plan and a terminal record. If the finalize scope gate refuses on a declared-but-unmodified path, acknowledge it with `--scope-ack` rather than making a cosmetic edit to satisfy it. If E-01 reports drift that invalidates F-02's ordering claim, STOP before E-03: the wording of both comment fixes depends on it, and documenting an unproven route would reproduce the exact defect this plan exists to correct.
