# IPD: Rescore the disposition after a defect re-ask whose recollection changed the outcome

- Date: 2026-09-19
- Kind: child
- Concern: A DEFECT RE-ASK THAT COMPLETES THE WORK IS NEVER RESCORED, SO A FULLY SUCCESSFUL TURN IS RECORDED `partial` AND CASCADES `dependency-blocked` ACROSS ITS WHOLE SET. `execute_item_core` scores the turn ONCE (`runner_shared.py:13107`), before the defect re-ask block (`:13220`). When the first turn wrote no outcome file, that score is correctly the empty-outcome fallback `partial` (`oc_runipd.py:6135`, twin `agy_runipd.py:2988`). The re-ask then resumes the SAME session, the resumed turn does the entire job, and the injected `recollect` (`runner_shared.py:8943-8947`) re-collects the lane submissions, writing the agent's now-complete outcome to `<run_dir>/outcomes/<NN>-<id6>.json` - the EXACT path the scorer reads, as `lane_containment.py:607` states in as many words. NOTHING RESCORES IT. The block re-reads that file for the defect report ALONE (`:8949`) and mutates only the five `defect_*` keys, so the local `disposition`, `attempt["disposition"]`, `item["status"]` and `item["last_outcome"]` all keep their pre-re-ask values. `integration_gate_relevant` (`:13337`) then reads the stale local, so no verifier runs, no suite check runs, the lane is never integrated, `driver_finalize` is never called, and the item lands `partial`. Had it been rescored it would have returned `substantially-complete` (the deliberate downgrade of a self-claimed `executed`, `oc_runipd.py:6114-6117`), which IS inside that gate and inside `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:492`), and no sibling would have blocked.
- Scope: Rescore the disposition from the RE-COLLECTED outcome after a defect re-ask, in `runner_shared.execute_item_core` only, positioned after the defect record is persisted and before `integration_gate_relevant` is computed. Make the rescore MONOTONIC (it may only improve a disposition, never downgrade one), gate it on the recollection having actually reported success, and carry the improvement onto all four stale carriers plus a durable event. EXCLUDES changing `reconcile_disposition` itself on any host (it is already correct and pure). EXCLUDES the agy host-truncation trigger (`ty7w6o` owns it) and the zero-work retry (`dy9ymn` owns it). EXCLUDES loosening any dependency, orchestrator-retirement, or success-bar predicate: the cascade is correct and only its TRIGGER is wrong.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_defect_report.py, tests/test_rununify_execute_item_gates.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: reaskscore
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: yxfw4k
- Blocks-Release: next
- Work-Kind: bug
- Id: skn8uk
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved

- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED, none deferred, none open; Readiness `go-pending-approval`. Reviewed at HEAD `249e6a8d`; the plan was byte-identical to the sealed lane input and the tree was clean, so no pre-review snapshot. `aw ipd lint --phase author` reported `clean` before the revisions and `--phase review-finalize` reports `clean` after them. THE DIAGNOSIS IS CORRECT AND THE FIX IS THE RIGHT ONE, and I re-verified the whole mechanism by AST rather than by reading its prose: the three carriers, the scoring call, the defect block, the `recollect` binding and `integration_gate_relevant` all sit where and as described, and the insertion window is a real 2-line gap at function top level. THE HEADLINE FINDING IS A GATE THAT WOULD HAVE BEEN DECORATIVE. E-02 said to gate the rescore on the recollection "having reported success" and V-02 named `status: complete`; measured by RUNNING `collect_lane_submissions` against an empty lane, that receipt comes back `status: "complete"`, `collected: []`, `failed: []` with the outcome recorded `absent`, because `status` is set unconditionally and an absent submission joins NEITHER list. So a gate on `status`, or on `failed` being empty, passes on a lane that submitted nothing; the only sound condition is `"outcome" in receipt["collected"]`, which E-02 now requires and V-02 now pins with the absent-outcome case as a mandatory third negative control. FOUR MORE CORRECTIONS, each measured. (1) E-05 and E-04 claimed `aw runs` would surface the new event: `run_viewer.py` mentions `events.jsonl` once, in a filename tuple, and parses no line of it; no driver event is rendered there at all, so the claim is dropped, the honest durability claim kept, and the pre-existing gap recorded as non-blocking OQ-03 with `run_viewer.py` explicitly fenced out. (2) E-06 described the AST pins wrongly three ways: there is exactly ONE tuple-to-`disposition` assignment today, not three (the two stop handlers assign `item["status"], _`, a Subscript the pins cannot see), and pin 2 anchors on `integrate_lane_branch`, not `integration_is_earned`; its CONCLUSION that both pins survive is correct and was re-derived arithmetically. (3) E-01's refusal of the stopped and forced dispositions is defence-in-depth, not a live path, since both values are already in `DEFECT_REASK_SKIPPED_STATUSES`; `integration-deferred` is NOT, which confirms E-03 is load-bearing. (4) All 12 `runner_shared.py` line citations have drifted (the file grew 13844 -> 14082 after authoring) while every other file's citations still resolve; the load-bearing ones are re-anchored by symbol and the drift is stated as a standing warning. Also confirmed the cited run directories are gitignored and absent, so F-1/F-2/F-5 cannot be re-verified from the tree, while both cited lane commits DO exist with matching subjects. Full record: `.aw/records/reviews/20260919-reaskscore-01-skn8uk-rescore-the-disposition-after-a-defect-re-ask-whose-recollec.review.md`.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `yxfw4k` after measuring the defect twice in consecutive runs on 2026-09-18 (`zqs0px` in `run-20260918T193638Z-2963696`, `zz5yxq` in `run-20260918T190723Z-2697256`). Both items' work was completed and committed on their lanes, both outcome files say `executed`, both were recorded `partial`, and each cascaded three siblings into `dependency-blocked` for a `BLOCKED` run with 0 of 4 executed. Inherits the item's `Blocks-Release: next`.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the driver score a turn on the BEST EVIDENCE IT HOLDS rather than on the evidence it held at an
earlier instant. Concretely: when a defect re-ask re-collects an outcome that reports more completion
than the pre-re-ask score, adopt the better score before any gate reads it, so a turn whose work is
finished and committed is not recorded `partial` and does not block its Set.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the monotonic rescore rule, host-neutral and pure

- [ ] E-01 ADD A PURE, HOST-NEUTRAL PREDICATE `rescore_is_an_improvement(before, after)` TO `runner_shared.py`, ANSWERING ONE QUESTION: may this rescored disposition replace the one already computed? It MUST be a pure function of two status strings, defined by an explicit RANK over dispositions rather than by a membership test, because the question is comparative ("is `after` better than `before`") and a set test cannot answer it. Required behavior, each of which is a case `V-01` pins: an improvement is permitted (`partial` -> `substantially-complete`, `partial` -> `executed`, `failed-safely` -> `substantially-complete`); an equal score is NOT an improvement (so nothing is rewritten and no event is emitted when the re-ask changed nothing); a DOWNGRADE is REFUSED (`substantially-complete` -> `partial`, `executed` -> anything lower), which is the safety property that makes this change unable to harm a turn that already succeeded; and `integration-deferred`, `runner_stop.STOPPED_DISPOSITION` and `runner_stop.FORCED_DISPOSITION` are NEVER replaceable in either direction, because each is a deliberate driver or operator decision that an agent's outcome file has no standing to overrule. An unknown status on either side MUST refuse (fail closed), so a future disposition added elsewhere cannot silently acquire replace-ability here.
  WHAT THE REFUSAL LIST BUYS, STATED HONESTLY AFTER MEASUREMENT, so nobody mistakes belt for braces. `runner_stop.STOPPED_DISPOSITION` is `"interrupted"` and `runner_stop.FORCED_DISPOSITION` is `"unknown_outcome"`, and BOTH are already members of `runner_shared.DEFECT_REASK_SKIPPED_STATUSES`, so `defect_reask_is_warranted` refuses a re-ask on either and neither can ever be the `before` value at the rescore point. Their entries here are therefore DEFENCE IN DEPTH against a future widening of that skip set, not a live path - keep them, and do not describe them as the safety property that matters. `"integration-deferred"` is the opposite case and is the one that genuinely matters: it is NOT in the skip set, so a re-ask CAN fire on a deferred item and reach the rescore, which is exactly why E-03 exists and why it is load-bearing rather than theoretical.
  - Depends on: none
  - Expected outcome: `runner_shared.rescore_is_an_improvement` exists, is importable, has no I/O and no argument it can mutate, and returns True for exactly the improving pairs enumerated above.
  - Execution state: pending

- [ ] E-02 ADD THE RESCORE CALL TO `execute_item_core`, AT THE ONE POSITION WHERE IT HAS EFFECT AND CANNOT RACE A GATE: after the defect record is persisted onto `attempt`/`item` and its `defect-report-recorded` event is appended, and BEFORE `integration_gate_relevant` is computed. ANCHOR BY SYMBOL, NOT BY LINE: the insertion point is the blank line between the `append_jsonl(... "event": "defect-report-recorded" ...)` call that closes the `if not is_review:` block and the `suite_result: Any = None` / `integration_gate_relevant = (` pair that follows it. Verified at review: that window is 2 lines wide, the rescore sits at function top level (4-space indent, NOT inside `if not is_review:`), and the existing top-level `save_state(run_dir, state)` after the `integration_gate_relevant` block already covers it, which is what lets E-04 add no new call site.
  It MUST be gated on all three of: a re-ask actually having been performed this attempt; the recollection having actually collected THE OUTCOME; and `rescore_is_an_improvement` returning True.
  READ THE RECEIPT'S `collected` LIST, NOT ITS `status`, AND THIS IS THE ONE DETAIL THAT DECIDES WHETHER THE GATE WORKS AT ALL. Read the receipt with `lane_containment.read_collection_receipt` (never infer from a file existing, which spec `7ckptx` R2.5 forbids in terms), then require `"outcome" in receipt["collected"]`. DO NOT gate on `receipt["status"] == "complete"` and DO NOT gate on `receipt["failed"]` being empty. MEASURED AT REVIEW by running `collect_lane_submissions` against an EMPTY lane: the receipt came back `status: "complete"`, `collected: []`, `failed: []`, with the outcome submission recorded `result: "absent"`. `collect_lane_submissions` sets `status = RECEIPT_COMPLETE` UNCONDITIONALLY once its three collects return, and `_collect_one` classifies a missing source `absent`, which appears in NEITHER `collected` NOR `failed`. So both of the tempting gates PASS on a lane that submitted nothing, and a rescore behind either would call `reconcile_disposition` a second time with no new evidence and re-derive the same `partial` - a decorative gate that looks like a safeguard. Only `"outcome" in receipt["collected"]` distinguishes collected from absent.
  The second call MUST pass the ORIGINAL executor `exit_code`, never the re-ask's `reask_rc`, because the fallback branch keys on it and the re-ask's exit code is a different fact already recorded separately as `attempt["defect_reask_exit_code"]`. Pass `plan_repo` exactly as the first call does (`Path(work_dir) if work_dir else None`).
  - Depends on: E-01
  - Expected outcome: a second `disposition, outcome = reconcile_disposition(...)` tuple assignment exists in `execute_item_core`, positioned between the defect event append and `integration_gate_relevant`, reached only under those three conditions, with the recollection condition reading `"outcome" in receipt["collected"]`.
  - Execution state: pending

- [ ] E-03 PRESERVE THE `integration-deferred` PASSTHROUGH ACROSS THE SECOND CALL, WHICH IS THE ONE WAY THIS CHANGE COULD DESTROY DATA RATHER THAN MERELY MIS-SCORE. `reconcile_disposition` READS `item["status"]` for its deferral passthrough (`oc_runipd.py:6133`, twin `agy_runipd.py:2986`), and `execute_item_core` has ALREADY overwritten `item["status"]` with the first disposition by this point (currently `:13193`). So the second call runs with an input the first call did not have. E-01's refusal list already prevents replacing a deferral, and this item makes the property explicit and tested rather than emergent: assert that an item whose status is `integration-deferred` at the rescore point retains it, and that the rescore neither rewrites it nor emits an event. The comment at `oc_runipd.py:6120-6132` explains why relabelling a deferral `partial` destroys it; do not re-derive that reasoning, cite it.
  - Depends on: E-02
  - Expected outcome: a deferred item passes through the rescore unchanged, pinned by a test that fails if the refusal is removed.
  - Execution state: pending

- [ ] E-04 CARRY THE IMPROVED SCORE ONTO ALL FOUR STALE CARRIERS, not only the local. The measured defect leaves `item["last_outcome"] = null` beside a fully collected outcome file, which is the defect in one line and is itself a reporting bug: `run_viewer.py` reads `item.get("last_outcome")` for the disposition and summary it displays (verified at review; unlike the `events.jsonl` claim in E-05, THIS reader is real), so a stale `None` there means the run report cannot describe a turn that succeeded. On an accepted rescore, update the local `disposition`, `attempt["disposition"]`, `item["status"]`, `item["last_outcome"]` (to the re-collected outcome dict) and `item["verification_status"]` handling, then persist.
  THE FIVE CARRIERS ARE SET TOGETHER IN ONE CONTIGUOUS BLOCK immediately before the `if not is_review:` defect block (`attempt["disposition"]`, `attempt["verification"]`, `attempt["verification_status"]`, `item["status"]`, `item["last_outcome"]`, `item["verification_status"]`); re-read that block when writing the rescore so no carrier is missed. Note the plan's own prose says FOUR while the block sets six fields across two objects; the four that decide the item's FATE are the local `disposition`, `attempt["disposition"]`, `item["status"]` and `item["last_outcome"]`, and `verification_status` is deliberately left alone per OQ-02.
  DO NOT ADD A NEW `save_state` CALL SITE: `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` counts call sites per runner (it pins `save_state: 22` as relocated into `execute_item_core`). Verified at review that no new site is needed: an existing top-level `save_state(run_dir, state)` sits just after the `integration_gate_relevant` block, downstream of the rescore's insertion point and at the same indent level, so the rescore's mutations are persisted by it. Confirm that pin passes unweakened and record what it required.
  - Depends on: E-02
  - Expected outcome: after an accepted rescore, all four fate-deciding carriers agree with each other and with the re-collected outcome file; `item["last_outcome"]` is non-`None`; and `test_no_call_site_was_rewritten` passes with no new `save_state` site added.
  - Execution state: pending

- [ ] E-05 EMIT A DURABLE `ipd-rescored` EVENT ON EVERY ACCEPTED RESCORE, naming `id6`, `attempt`, `before`, `after`, and the reason the rescore was permitted. A silent status rewrite is exactly the class of change a human must be able to audit afterwards, and scrollback is not a record. Use the same `append_jsonl(run_dir / "events.jsonl", {...})` shape the adjacent `defect-report-recorded` event uses, so the new record is not a novel channel. Emit NOTHING when the rescore is refused or is not an improvement, so the event's presence means "a re-ask changed this item's fate" and never "the code ran".
  DO NOT CLAIM `aw runs` WILL DISPLAY IT, which the plan asserted before review and which is FALSE. Measured: `run_viewer.py` mentions `events.jsonl` exactly once, in a filename tuple used to decide which files a run directory contains, and it NEVER parses a line of it; no existing driver event is rendered there either (`defect-report-recorded`, `dependency-blocked`, `ipd-stalled`, `turn-bound-expired` all appear zero times in `run_viewer.py`). The honest claim is that the event is DURABLE and GREPPABLE in the run directory, which is what makes the rewrite auditable after the fact, and that is sufficient for this plan. The item's value does NOT depend on a viewer change and this plan must NOT grow one: `run_viewer.py` is deliberately absent from `- Scope-Paths:`, and surfacing driver events in the run report is a separate reporting concern with its own review surface (see OQ-03).
  - Depends on: E-02
  - Expected outcome: `events.jsonl` carries one `ipd-rescored` record per accepted rescore and none otherwise, verified by reading the file; no claim is made or relied upon about `aw runs` rendering it, and `run_viewer.py` is not edited.
  - Execution state: pending

### Task group 2: regression surface

- [ ] E-06 PIN THE ORDERING ON THE CALL GRAPH IN `tests/test_rununify_execute_item_gates.py` AND RE-BASE THE ONE DOCSTRING THIS CHANGE FALSIFIES. Two existing AST pins are involved: `test_submissions_are_collected_before_the_disposition_is_reconciled` and `test_the_disposition_is_reconciled_before_integration`. Both resolve their target through `_execute_item_ast`, which FOLLOWS each host's `execute_item` delegation into `runner_shared.execute_item_core`, so they read the shared body this plan edits.
  WHAT THEY ACTUALLY ASSERT, MEASURED AT REVIEW, because the plan as authored described this wrongly in three ways and an implementer trusting the description would predict the wrong outcome. They collect the lines of every `ast.Assign` whose target is a TUPLE containing a `Name` called `disposition`. TODAY THERE IS EXACTLY ONE such assignment in `execute_item_core` (the scoring call), NOT three: the two stop-handler calls assign to `item["status"], _`, whose first element is a `Subscript` and not a `Name`, so the AST pins never see them. Pin 1 asserts `min(collect_lane_submissions) < max(disposition_assign)`; pin 2 asserts `max(disposition_assign) < first(integrate_lane_branch)` - note the anchor is `integrate_lane_branch`, NOT `integration_is_earned`, which sits earlier. Adding the rescore makes `max(disposition_assign)` the RESCORE line, and both inequalities still hold because the rescore sits after the collect and well before the merge; confirmed arithmetically at review against the current line numbers. So neither pin needs weakening - VERIFY that rather than assuming it, and if either fails, report it as a finding rather than relaxing the assertion.
  THE DOCSTRING COUNT IS CURRENTLY CORRECT AND THIS CHANGE FALSIFIES IT. The docstring in `test_submissions_are_collected_before_the_disposition_is_reconciled` states `execute_item` "calls `reconcile_disposition` THREE times on each host"; measured at review, `execute_item_core` does call it exactly three times, so the count is true today and becomes FOUR. Correct it, because a stale count in a characterization test is how the next reader is misled. Note the same docstring's parenthetical cites `oc_runipd.py:7344` and `:7372` for the two early-recovery calls; those offsets have drifted and now land on unrelated lines, so re-anchor them by symbol (the two `except` handlers inside `execute_item_core`) rather than copying the stale numbers forward.
  ADD ONE NEW PIN: the rescore call is positioned AFTER the `defect-report-recorded` event append and BEFORE `integration_is_earned`, asserted on the call graph rather than on byte offsets, matching this file's stated convention in its module docstring. Pin it against `integration_is_earned` specifically, since that is the gate the stale score actually misleads and it is EARLIER than the `integrate_lane_branch` anchor pin 2 uses, so this new pin is strictly stronger than pin 2 on the property this plan cares about.
  - Depends on: E-02
  - Expected outcome: the two existing pins pass unweakened, the docstring's count is corrected from three to four and its two drifted offsets re-anchored by symbol, and one new ordering pin exists that fails if the rescore is moved after `integration_is_earned`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- EVERY `runner_shared.py` LINE NUMBER IN THIS PLAN HAS DRIFTED AND MUST NOT BE TRUSTED. Measured at review: all 12 distinct `runner_shared.py:<line>` citations in this file now point at unrelated lines (the file grew from 13844 to 14082 lines after authoring), while every `oc_runipd.py`, `agy_runipd.py`, `lane_containment.py`, `run_viewer.py` and `tests/` citation still resolves correctly. None is out of range, so none announces itself; each one silently lands on plausible-looking other code. RE-DERIVE EACH ANCHOR BY SYMBOL before acting on it. The substance of every claim was re-verified at review and holds; only the offsets are wrong.
- THE LIVE `reconcile_disposition` IS THE PER-HOST COPY, NOT THE SHARED ONE. `execute_item_core` binds it with `getattr(driver_module, "reconcile_disposition", globals().get("reconcile_disposition"))`, and both drivers define their own (`oc_runipd.py:6027`, `agy_runipd.py:2903`, both still accurate), so the shared `runner_shared.reconcile_disposition` body is not what runs in production. This plan does NOT edit any of the three, which is what keeps it a one-file product change; an implementer who decides to edit them must expect the cross-host equality pins (`tests/test_rununify_run_queue.py:165`, accurate) to bite.
- CALLING `reconcile_disposition` MORE THAN ONCE IN ONE BODY IS AN ESTABLISHED SHAPE, not a novelty this plan introduces: measured at review, `execute_item_core` calls it THREE times today. TWO OF THE THREE ARE NOT TUPLE ASSIGNMENTS, and the difference is what E-06 turns on: the two stop handlers assign `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` with a hardcoded `exit_code=1`, whose first target element is a `Subscript`, so the AST ordering pins (which look for a TUPLE target containing a `Name` called `disposition`) see only ONE assignment today. The rescore adds the second one they can see.
- IT IS A PURE FUNCTION. None of the three copies writes state: no `save_state`, no `append_jsonl`, no item mutation. Failures are swallowed (`except DriverError: outcome = None`). That is what makes a second call safe.
- `recollect` IS ALREADY BOUND CORRECTLY AND WRITES TO THE PATH THE SCORER READS. `functools.partial(..., attempt=attempt_no)` at `runner_shared.py:13275` keeps the receipt in the same attempt slot (incrementing `collection_runs`), and the destination is `run_dir / "outcomes" / f"{item_slug(item)}.json"` (`lane_containment.py:607-615`). So the input this plan rescores from is already on disk when `perform_defect_reask` returns; nothing new needs collecting.
- COLLECTION MUST BE READ FROM ITS RECORD, NOT INFERRED. Spec `7ckptx` R2.5 requires an attempt-keyed collection record and states that "Absence of a record means NOT collected and MUST NOT be inferred from a file existing somewhere." `lane_containment.read_collection_receipt` is that reader.
- THE RE-ASK IS BOUNDED AT EXACTLY ONE BY CONTRACT, structurally rather than by a counter (`perform_defect_reask` docstring, `runner_shared.py:8911`; `already_reasked` gate at `:8833`). This plan adds no loop and must not appear to: the rescore happens at most once because the re-ask does.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | The re-collected outcome says `executed` while the item says `partial`, in the same run directory. | `run-20260918T193638Z-2963696/outcomes/02-zqs0px.json` -> `"disposition": "executed"`, 4 files changed, commit `08416ebd`; same run's `state.json` queue entry -> `"status": "partial"`, `"last_outcome": null`. |
| F-2 | The recollection SUCCEEDED, so the re-ask path worked exactly as designed and only the scoring is wrong. | `collections/02-zqs0px-attempt-1.json` -> `"collection_runs": 2`, `"status": "complete"`, `"collected": ["outcome","report","decisions"]`, `"failed": []`. |
| F-3 | The work exists and is not lost, so this is a scoring defect rather than a data-loss defect. | `git log d445e6e6..aw/lane/zqs0px_attempt3` -> `08416ebd docs(nobugship-01): record no-known-bugs rule...`; lane preserved with reason "the item finished 'partial' rather than executed". |
| F-4 | The cascade that followed is CORRECT and must not be loosened; only its trigger is wrong. | `events.jsonl` -> `dependency-blocked` for `di08i9` ("prerequisite reached a non-success terminal state"), then `rgaasb`, then `orchestrator-deferred` for `qmgn12`. `EXECUTION_SUCCESS_STATES = {"executed","substantially-complete"}` (`oc_runipd.py:492`) correctly excludes `partial`. |
| F-5 | Reproduced independently in a second run on a different Set, so it is systematic and not a one-off. | `run-20260918T190723Z-2697256`: `zz5yxq` recorded `partial`, outcome file `"disposition": "executed"`, lane commit `8247a13c`, siblings `7ewc74`/`m85gxh`/`bsc457` all `dependency-blocked`. |
| F-6 | `substantially-complete` is the disposition a correct rescore produces, and it is sufficient to unblock the siblings. | `reconcile_disposition` downgrades a self-claimed `executed` to `substantially-complete` (`oc_runipd.py:6114-6117`), which is in `EXECUTION_SUCCESS_STATES` (`:492`) and in the `("executed","substantially-complete")` gate literal (`runner_shared.py:13337`). |
| F-7 | `substantially-complete` will NOT retire the orchestrator, so this plan fixes the sibling cascade and not the parent's retirement. | `runner_shared.SET_RETIREMENT_DONE_STATUS = "executed"`, whose own comment says "DELIBERATELY NOT `EXECUTION_SUCCESS_STATES`"; `runner_shared.decide_orchestrator_dispatch` collects such a child into its `stranded` list. Verified at review by symbol (the plan's original line offsets for both had drifted). Stated so nobody over-reads this fix; see "Deferred". |
| F-8 | The defect is host-agnostic in the CODE and agy-only in its TRIGGER, so the fix belongs in shared code. | The stale carriers are all in `runner_shared.execute_item_core`, which both hosts call. The trigger needs a first turn that writes no outcome and a re-ask that completes the work; on oc the first turn completes, so its re-ask is report-only. |
| F-9 | No existing code re-reconciles after a follow-up turn, so this is a new pattern and the ordering pins must be checked rather than assumed. | Full call-site census, RE-DERIVED BY AST at review: the `getattr` binding in `execute_item_core`, plus exactly three calls inside it - the scoring call (the only TUPLE-to-`disposition` assignment) and the two `except` stop handlers (`item["status"], _ = ...`). Nothing else in `agent_workflows/` calls it. |

## Proposed changes (ordered, validatable)

1. `runner_shared.py`: add `rescore_is_an_improvement(before, after)`, a pure ranked comparison with an explicit never-replaceable set and fail-closed handling of unknown statuses (E-01).
2. `runner_shared.execute_item_core`: after the defect record and its event, before `integration_gate_relevant`, re-score under three conditions (re-ask performed, `"outcome" in receipt["collected"]`, rescore is an improvement) using the ORIGINAL exit code (E-02, E-03).
3. `runner_shared.execute_item_core`: on acceptance, update the local `disposition`, `attempt["disposition"]`, `item["status"]`, `item["last_outcome"]`, relying on the existing downstream `save_state` rather than adding a call site (E-04).
4. `runner_shared.execute_item_core`: append an `ipd-rescored` event on acceptance only, to `events.jsonl` via the existing `append_jsonl` shape (E-05).
5. `tests/test_defect_report.py`: cases for improvement, equality, refused downgrade, deferral passthrough, and the THREE recollection negative controls (outcome `failed`, no receipt, and the absent-outcome `status: complete` / `collected: []` case), plus carrier agreement (V-01..V-05).
6. `tests/test_rununify_execute_item_gates.py`: correct the docstring's call count three -> four, re-anchor its two drifted `oc_runipd.py` offsets by symbol, add the new `integration_is_earned` ordering pin, and confirm the two existing pins still pass unweakened (E-06).

## Deferred / out of scope (with reason)

- THE ORCHESTRATOR STILL WILL NOT RETIRE ON `substantially-complete` (F-7). Retirement requires every child `executed` (`runner_shared.SET_RETIREMENT_DONE_STATUS`, and `evaluate_set_retirement` refuses with `RETIRE_REFUSED_UNFINISHED_CHILDREN` naming each child whose status differs), so a rescued item unblocks its SIBLINGS but leaves the parent stranded rather than retired. Widening the retirement bar is deliberately NOT done here: that bar is a separate, reasoned contract (its own comment says in terms that it is not `EXECUTION_SUCCESS_STATES`) governed by spec `77tr3o`, and changing it inside a defect fix would be an unreviewed contract change. What this plan removes is the sibling cascade and the false `partial`; the parent's retirement follows normally once the item reaches `executed` through the finalize path this fix re-opens.
  - Carrier-Declined: Nothing to carry: this is not deferred work but a statement of the fix's correct BOUNDARY. The retirement bar is spec `77tr3o`'s reasoned contract and is not defective, and a rescued item that reaches `executed` through the re-opened finalize path retires its parent normally, so no future act is pending.
- THE AGY HOST TRUNCATION that produces the empty first turn is `ty7w6o`'s subject, and the zero-work retry is `dy9ymn`'s. This plan deliberately fixes the SCORING independently of the trigger, so it holds for any future host or condition that ends a turn before its outcome is written.
  - Carrier: s0gnha
- NO DEPENDENCY, SUCCESS-BAR, OR RETIREMENT PREDICATE IS TOUCHED. The measured cascade was correct behavior on a wrong input (F-4). Loosening any of them would dispatch a dependent against a base lacking the commits it depends on, which is strictly worse than the defect.
  - Carrier-Declined: A rejected alternative, recorded so it is not re-proposed. The measured cascades were correct behavior on a wrong input, so there is no future state in which loosening them becomes right and no work to hand off.
- NOT CHANGING `reconcile_disposition` ON ANY HOST. It is already correct and pure; the bug is that its answer is never asked for a second time.
  - Carrier-Declined: Nothing to carry: the function is not defective, so declining to edit it leaves no outstanding obligation.

## Scope check

- Over-scope: none. One product file, two test files. No host driver is edited, no predicate is widened.
- Under-scope: the orchestrator retirement bar (F-7), the two sibling plans' concerns, and rendering driver events in the run report (OQ-03, a pre-existing gap affecting every event type), each excluded with a reason above. A reviewer should confirm those exclusions are right rather than assume them.
- Scope fence: the three declared `- Scope-Paths:` are the whole intended surface. Do not expand it casually; if the work genuinely requires a file outside the fence, MAKE the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path). Two specific temptations are named because review found the plan leaning toward each: `run_viewer.py` (E-05's corrected claim, deliberately excluded per OQ-03) and the three `reconcile_disposition` copies (excluded in Deferred; editing them makes the cross-host equality pins bite).

## Required tests / validation

`python3 -m pytest`, run BARE as the repository contract requires, with the actual summary line pasted
into each `V-*`. New and changed cases live in `tests/test_defect_report.py` (the re-ask's existing home)
and `tests/test_rununify_execute_item_gates.py` (the ordering pins). Every V-item below demands PASTED
output, not a claim.

Beyond the unit surface, the two measured runs are the falsification standard: a rescore that would not
have converted `zqs0px` from `partial` to `substantially-complete` given that run's on-disk outcome and
collection receipt has not fixed this defect. `V-02` reconstructs exactly that case in `tmp_path`
(never against the live, gitignored `.aw/records/runs/` tree, which CI does not have).

THE CITED RUN DIRECTORIES ARE NOT AVAILABLE TO AN EXECUTOR, confirmed at review: `.aw/records/runs/` is
gitignored and holds neither `run-20260918T193638Z-2963696` nor `run-20260918T190723Z-2697256` in a fresh
checkout or a lane worktree, so F-1, F-2 and F-5's on-disk artifacts CANNOT be re-verified from the tree.
What IS verifiable and was verified: both cited lane commits exist and their subjects match the plan's
description (`08416ebd` "docs(nobugship-01): record no-known-bugs rule ... (zqs0px)" and `8247a13c`
"zz5yxq: split reviewed out of the run success bar for execute action"), which independently corroborates
F-3's claim that the work was completed and committed. An executor must therefore build V-02's fixture
from the receipt and outcome SHAPES described in this plan, not by copying a live run directory.

## Spec / documentation sync

Spec `7ckptx` (worker lane containment) R2.1 requires collection BEFORE the disposition is computed,
and its rationale (`:136-144`) describes precisely this failure mode: "a fully successful turn silently
never finalizes". The measured defect is a SECOND instance of that same harm, arriving through a path
R2.1 does not cover, because the re-ask re-collects AFTER the disposition was computed and R2.1 speaks
only of the first collection. Whether R2.1 should be amended to state the invariant in its general form
("the disposition MUST be computed from the latest successfully collected submission") is `OQ-01`, and
this plan does NOT edit the spec: no `.spec.md` path is declared in `Scope-Paths`, so a spec edit here
would be an undeclared scope violation. The amendment, if the reviewer wants it, belongs to a plan that
declares it.

## Open questions

### OQ-01: Should spec `7ckptx` R2.1 be generalized from "collect before scoring" to "score from the latest collection"?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING because the code fix is correct and complete under the spec as it stands: R2.1's stated purpose is that a successful turn must not silently fail to finalize, and this change serves that purpose rather than contradicting it. Recorded rather than resolved because amending an approved spec is a contract change a reviewer should authorize deliberately, and because this plan's `Scope-Paths` deliberately declares no spec file (AGENTS.md requires a plan that amends a spec to declare it, so the honest options are "declare and amend" or "do not touch"; the smaller change was chosen for a release-blocking defect fix). If the reviewer wants the amendment, the recommended wording is that the disposition be computed from the latest SUCCESSFULLY COLLECTED submission for the attempt, which states the invariant this fix implements.
- Carrier: s0gnha

### OQ-02: Should an accepted rescore also re-run the verifier that the stale score skipped?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: NO, and deliberately, because the verifier block sits EARLIER in the body (the `verify_disp` assignments all precede the first scoring call) than the rescore point, so "re-running" it would mean either a backward jump or a duplicated verifier invocation, and a second paid verifier turn inside one attempt is a spend this defect fix has no mandate for. The consequence is stated plainly rather than hidden: a rescued item reaches the integration gate with `verify_disp` still `None`, so `integration_is_earned` (`oc_runipd.py:3912`, verified accurate at review) falls to its suite-check branch and the DRIVER runs the suite itself for the trust signal, which is the same posture `--no-verify` runs use today and is an existing, reviewed path (`novalnomerge-01` / `evgi9n`). CONFIRMED AT REVIEW by reading the predicate: with `validate=False` and `suite_result is None` it returns `INTEGRATION_REFUSED_NO_SIGNAL` ("refusing to integrate without any trust signal (fail-closed)"), and with a passing suite it returns `INTEGRATION_EARNED_BY_SUITE`. So the rescued item is integrated on a driver-observed suite result or not at all, never on an unverified agent claim. `V-06` pins that specific consequence so it cannot regress into "integrated on no signal at all".

### OQ-03: Should the run report render driver `events.jsonl` records, so an `ipd-rescored` event is visible without grepping?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING and OUT OF SCOPE HERE, recorded because this plan originally claimed the visibility it cannot deliver and the corrected claim leaves a real gap worth naming. MEASURED at review: `run_viewer.py` mentions `events.jsonl` exactly once, inside a tuple of filenames used to decide which files a run directory holds, and never parses a line of it; no driver event is rendered anywhere in it (`defect-report-recorded`, `dependency-blocked`, `ipd-stalled` and `turn-bound-expired` each appear zero times). So EVERY driver event, not just this plan's, is durable-but-unrendered today, which makes this a pre-existing reporting gap rather than a defect this plan introduces. E-05 is still worth doing as written: the record survives the run and is greppable, which is what makes a silent status rewrite auditable after the fact. Deliberately not fixed here because `run_viewer.py` is not in `- Scope-Paths:`, because rendering events is a reporting concern spanning every event type rather than this one, and because a defect-fix Set is the wrong place to add a display surface. If the reviewer wants it, it belongs to a plan that declares `run_viewer.py` and decides which events are worth showing.
- Carrier-Declined: A PRE-EXISTING, PLAN-INDEPENDENT REPORTING GAP, recorded for visibility rather than handed off: it affects every driver event equally, this plan neither creates nor worsens it, and E-05's auditability goal is met by the durable record alone. Nothing about this plan's completion is pending on it, so there is no future act for a carrier to own; should the reviewer want the display surface, that is a new plan declaring `run_viewer.py`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `pytest` output for the `rescore_is_an_improvement` cases showing ALL of: three improving pairs return True (`partial`->`substantially-complete`, `partial`->`executed`, `failed-safely`->`substantially-complete`); equal pairs return False; every downgrade returns False including `substantially-complete`->`partial` and `executed`->`partial`; `integration-deferred`, the stopped and the forced dispositions return False in BOTH directions; and an unrecognized status on either side returns False. Plus a demonstration that the function performs no I/O and mutates neither argument.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a test that RECONSTRUCTS THE MEASURED CASE in `tmp_path`: an attempt whose first score is `partial` with no outcome file, a re-ask that writes an outcome carrying `"disposition": "executed"` plus a collection receipt whose `collected` list CONTAINS `"outcome"`, and the assertion that the item ends `substantially-complete` and NOT `partial`.
    THREE NEGATIVE CONTROLS ARE REQUIRED, not one, and the third is the one that proves the gate reads the right field. (a) The receipt records the outcome collection as `failed` -> item stays `partial`. (b) NO receipt exists at all (`read_collection_receipt` returns `None`) -> item stays `partial`, proving the R2.5 fail-closed reading. (c) THE ABSENT-OUTCOME CASE: a receipt with `status: "complete"`, `collected: []` and `failed: []`, which is exactly what `collect_lane_submissions` writes for a lane that submitted nothing (measured at review) -> the item MUST stay `partial`. Control (c) is load-bearing because a gate written against `status` or against an empty `failed` list PASSES this fixture, so without (c) a decorative gate ships looking correct. Paste all three.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output showing an item whose status is `integration-deferred` at the rescore point still reads `integration-deferred` afterwards, with no `ipd-rescored` event emitted, AND pasted output of the negative control proving the test can fail: with the deferral refusal removed, the same test fails (name the assertion that fires).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted output showing that after an accepted rescore all four carriers agree: the local disposition, `attempt["disposition"]`, `item["status"]`, and `item["last_outcome"]` (non-`None`, equal to the re-collected outcome dict). Must explicitly assert `item["last_outcome"] is not None`, since a `None` there beside a collected outcome file is the measured symptom. Plus a statement of what `test_no_call_site_was_rewritten` required: either that no `save_state` call site was added, or the pin's updated count with the reason.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted output showing exactly one `ipd-rescored` event in `events.jsonl` for an accepted rescore, carrying `id6`, `attempt`, `before` and `after`; and ZERO such events for each of the FOUR non-acceptance paths (no re-ask performed; the recollection recorded the outcome `failed`; no receipt at all; the rescore is not an improvement). Read the event back FROM THE FILE, not from a mock of the appender. Do NOT require or assert any `aw runs` rendering: measured at review, `run_viewer.py` never parses `events.jsonl` and renders no driver event, so an assertion about the run report would fail for a reason this plan does not own.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted output of the full bare `python3 -m pytest` summary line, plus specifically: `tests/test_rununify_execute_item_gates.py` passing with both pre-existing ordering pins UNWEAKENED (quote the two test names and confirm no assertion in them was relaxed), the corrected call count in the docstring quoted, and the new ordering pin failing when the rescore is moved to after `integration_is_earned` (paste that deliberate-break output). Also paste evidence for OQ-02's stated consequence: a rescued item reaches the gate with `verify_disp is None` and is integrated on a DRIVER-RUN suite result, never on no signal.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is release-blocking (`Blocks-Release: next`, inherited from backlog `yxfw4k` per the
every-live-bug-gates-the-release rule) and must not be executed before explicit human approval, which
`- Status:` records and which no agent may write on the maintainer's behalf.

EXECUTION CONTRACT. Commit only the files this plan changed, path-scoped (`git commit -m msg -- <path>`),
never `git add -A`/`-a`/bare, and never push. Before every commit run `git diff --cached --name-only` and
`git restore --staged` anything not yours: this is a SHARED CHECKOUT with concurrent workers, and a
failed pre-commit hook can leave paths in the index you never staged, so re-verify after any failed
attempt. Prefer `aw commit <plan> -- <paths>`, which stages and commits only the intersection of your
explicit paths with what it staged itself.

When reporting tests passed, paste the ACTUAL bare `python3 -m pytest` output. Do not add `-n0`, a second
`-q`, or `-p no:randomly`: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal
-m 'not slow'`, and `-n0` measurably makes this suite several times slower here.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` reports conforming and every `V-*` above carries concrete pasted
evidence. A rescore is a SILENT STATUS REWRITE by nature, so a `V-*` marked from the matching execution
checkmark rather than from observed output would be exactly the unverified claim this gate exists to
refuse.
