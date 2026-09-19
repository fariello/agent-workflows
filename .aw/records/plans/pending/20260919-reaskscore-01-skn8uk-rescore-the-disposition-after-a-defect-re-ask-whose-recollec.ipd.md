# IPD: Rescore the disposition after a defect re-ask whose recollection changed the outcome

- Date: 2026-09-19
- Kind: child
- Concern: A DEFECT RE-ASK THAT COMPLETES THE WORK IS NEVER RESCORED, SO A FULLY SUCCESSFUL TURN IS RECORDED `partial` AND CASCADES `dependency-blocked` ACROSS ITS WHOLE SET. `execute_item_core` scores the turn ONCE (`runner_shared.py:13107`), before the defect re-ask block (`:13220`). When the first turn wrote no outcome file, that score is correctly the empty-outcome fallback `partial` (`oc_runipd.py:6135`, twin `agy_runipd.py:2988`). The re-ask then resumes the SAME session, the resumed turn does the entire job, and the injected `recollect` (`runner_shared.py:8943-8947`) re-collects the lane submissions, writing the agent's now-complete outcome to `<run_dir>/outcomes/<NN>-<id6>.json` - the EXACT path the scorer reads, as `lane_containment.py:607` states in as many words. NOTHING RESCORES IT. The block re-reads that file for the defect report ALONE (`:8949`) and mutates only the five `defect_*` keys, so the local `disposition`, `attempt["disposition"]`, `item["status"]` and `item["last_outcome"]` all keep their pre-re-ask values. `integration_gate_relevant` (`:13337`) then reads the stale local, so no verifier runs, no suite check runs, the lane is never integrated, `driver_finalize` is never called, and the item lands `partial`. Had it been rescored it would have returned `substantially-complete` (the deliberate downgrade of a self-claimed `executed`, `oc_runipd.py:6114-6117`), which IS inside that gate and inside `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:492`), and no sibling would have blocked.
- Scope: Rescore the disposition from the RE-COLLECTED outcome after a defect re-ask, in `runner_shared.execute_item_core` only, positioned after the defect record is persisted and before `integration_gate_relevant` is computed. Make the rescore MONOTONIC (it may only improve a disposition, never downgrade one), gate it on the recollection having actually reported success, and carry the improvement onto all four stale carriers plus a durable event. EXCLUDES changing `reconcile_disposition` itself on any host (it is already correct and pure). EXCLUDES the agy host-truncation trigger (`ty7w6o` owns it) and the zero-work retry (`dy9ymn` owns it). EXCLUDES loosening any dependency, orchestrator-retirement, or success-bar predicate: the cascade is correct and only its TRIGGER is wrong.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_defect_report.py, tests/test_rununify_execute_item_gates.py
- Item-Dependencies: none
- Status: to-review
- Set: reaskscore
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: yxfw4k
- Blocks-Release: next
- Work-Kind: bug
- Id: skn8uk

## Workflow history

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
  - Depends on: none
  - Expected outcome: `runner_shared.rescore_is_an_improvement` exists, is importable, has no I/O and no argument it can mutate, and returns True for exactly the improving pairs enumerated above.
  - Execution state: pending

- [ ] E-02 ADD THE RESCORE CALL TO `execute_item_core`, AT THE ONE POSITION WHERE IT HAS EFFECT AND CANNOT RACE A GATE: after the defect record is persisted onto `attempt`/`item` and its `defect-report-recorded` event is appended (currently ending at `runner_shared.py:13312`), and BEFORE `integration_gate_relevant` is computed (currently `:13337`). It MUST be gated on all three of: a re-ask actually having been performed this attempt; the recollection having reported success (read from the collection receipt via `lane_containment.read_collection_receipt`, never inferred from a file existing, which spec `7ckptx` R2.5 forbids in terms); and `rescore_is_an_improvement` returning True. The second call MUST pass the ORIGINAL executor `exit_code`, never the re-ask's `reask_rc`, because the fallback branch keys on it and the re-ask's exit code is a different fact already recorded separately at `:13287`. Pass `plan_repo` exactly as the first call does (`Path(work_dir) if work_dir else None`).
  - Depends on: E-01
  - Expected outcome: a second `disposition, outcome = reconcile_disposition(...)` tuple assignment exists in `execute_item_core`, positioned between the defect event append and `integration_gate_relevant`, reached only under those three conditions.
  - Execution state: pending

- [ ] E-03 PRESERVE THE `integration-deferred` PASSTHROUGH ACROSS THE SECOND CALL, WHICH IS THE ONE WAY THIS CHANGE COULD DESTROY DATA RATHER THAN MERELY MIS-SCORE. `reconcile_disposition` READS `item["status"]` for its deferral passthrough (`oc_runipd.py:6133`, twin `agy_runipd.py:2986`), and `execute_item_core` has ALREADY overwritten `item["status"]` with the first disposition by this point (currently `:13193`). So the second call runs with an input the first call did not have. E-01's refusal list already prevents replacing a deferral, and this item makes the property explicit and tested rather than emergent: assert that an item whose status is `integration-deferred` at the rescore point retains it, and that the rescore neither rewrites it nor emits an event. The comment at `oc_runipd.py:6120-6132` explains why relabelling a deferral `partial` destroys it; do not re-derive that reasoning, cite it.
  - Depends on: E-02
  - Expected outcome: a deferred item passes through the rescore unchanged, pinned by a test that fails if the refusal is removed.
  - Execution state: pending

- [ ] E-04 CARRY THE IMPROVED SCORE ONTO ALL FOUR STALE CARRIERS, not only the local. The measured defect leaves `item["last_outcome"] = null` beside a fully collected outcome file, which is the defect in one line and is itself a reporting bug: `run_viewer.py:920-926` reads `item["last_outcome"]` for the disposition and summary it displays, so a stale `None` there means the run report cannot describe a turn that succeeded. On an accepted rescore, update the local `disposition`, `attempt["disposition"]`, `item["status"]`, `item["last_outcome"]` (to the re-collected outcome dict) and `item["verification_status"]` handling, then `save_state`. Do NOT add a new `save_state` CALL SITE if an existing one is reachable without changing behavior: `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` counts call sites per runner, so check that pin before adding one and record what it required.
  - Depends on: E-02
  - Expected outcome: after an accepted rescore, all four carriers agree with each other and with the re-collected outcome file; `aw runs <id>` describes the item's real disposition and summary.
  - Execution state: pending

- [ ] E-05 EMIT A DURABLE `ipd-rescored` EVENT ON EVERY ACCEPTED RESCORE, naming `id6`, `attempt`, `before`, `after`, and the reason the rescore was permitted. A silent status rewrite is exactly the class of change a human must be able to audit afterwards, and scrollback is not a record: the events ledger is what `aw runs` reads. Emit NOTHING when the rescore is refused or is not an improvement, so the event's presence means "a re-ask changed this item's fate" and never "the code ran".
  - Depends on: E-02
  - Expected outcome: `events.jsonl` carries one `ipd-rescored` record per accepted rescore and none otherwise; `aw runs <run-id>` surfaces it.
  - Execution state: pending

### Task group 2: regression surface

- [ ] E-06 PIN THE ORDERING ON THE CALL GRAPH IN `tests/test_rununify_execute_item_gates.py` AND RE-BASE THE ONE DOCSTRING THIS CHANGE FALSIFIES. Two existing AST pins anchor on the LAST `disposition, ...` tuple assignment: `test_submissions_are_collected_before_the_disposition_is_reconciled` (`:207-259`) and `test_the_disposition_is_reconciled_before_integration` (`:261-291`). A new tuple assignment inside the rescore satisfies both (it sits after the collect and before integration), so neither should need weakening - VERIFY that rather than assuming it, and if either fails, report it as a finding rather than relaxing the assertion. The docstring at `:215` states `execute_item` "calls `reconcile_disposition` THREE times on each host"; that count becomes four and MUST be corrected, because a stale count in a characterization test is how the next reader is misled. Add one new pin: the rescore call is positioned AFTER the defect-report record and BEFORE `integration_is_earned`, asserted on the call graph (not on byte offsets), matching this file's stated convention at `:14-20`.
  - Depends on: E-02
  - Expected outcome: the two existing pins pass unweakened, the count in the docstring is corrected, and one new ordering pin exists that fails if the rescore is moved after the integration gate.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- THE LIVE `reconcile_disposition` IS THE PER-HOST COPY, NOT THE SHARED ONE. `execute_item_core` binds it with `getattr(driver_module, "reconcile_disposition", globals().get(...))` at `runner_shared.py:12483`, and both drivers define their own (`oc_runipd.py:6027`, `agy_runipd.py:2903`), so the shared body at `runner_shared.py:12337` is not what runs in production. This plan does NOT edit any of the three, which is what keeps it a one-file product change; an implementer who decides to edit them must expect the cross-host equality pins (`tests/test_rununify_run_queue.py:165`) to bite.
- CALLING `reconcile_disposition` TWICE IN ONE BODY IS AN ESTABLISHED SHAPE, not a novelty this plan introduces. The verifier's two stop handlers already do it (`runner_shared.py:13194`, `:13206`), with a hardcoded `exit_code=1`.
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
| F-7 | `substantially-complete` will NOT retire the orchestrator, so this plan fixes the sibling cascade and not the parent's retirement. | `SET_RETIREMENT_DONE_STATUS = "executed"` (`runner_shared.py:6443`), deliberately not `EXECUTION_SUCCESS_STATES`; `decide_orchestrator_dispatch` records such a child as STRANDED (`:7617-7622`). Stated so nobody over-reads this fix; see "Deferred". |
| F-8 | The defect is host-agnostic in the CODE and agy-only in its TRIGGER, so the fix belongs in shared code. | The stale carriers are all in `runner_shared.execute_item_core`, which both hosts call. The trigger needs a first turn that writes no outcome and a re-ask that completes the work; on oc the first turn completes, so its re-ask is report-only. |
| F-9 | No existing code re-reconciles after a follow-up turn, so this is a new pattern and the ordering pins must be checked rather than assumed. | Full call-site census: `runner_shared.py:12483` (binding), `:13107` (the scoring call), `:13194` and `:13206` (stop handlers). Nothing else in `agent_workflows/` calls it. |

## Proposed changes (ordered, validatable)

1. `runner_shared.py`: add `rescore_is_an_improvement(before, after)`, a pure ranked comparison with an explicit never-replaceable set and fail-closed handling of unknown statuses (E-01).
2. `runner_shared.execute_item_core`: after the defect record and its event, before `integration_gate_relevant`, re-score under three conditions (re-ask performed, recollection recorded successful, rescore is an improvement) using the ORIGINAL exit code (E-02, E-03).
3. `runner_shared.execute_item_core`: on acceptance, update the local `disposition`, `attempt["disposition"]`, `item["status"]`, `item["last_outcome"]`, and persist (E-04).
4. `runner_shared.execute_item_core`: append an `ipd-rescored` event on acceptance only (E-05).
5. `tests/test_defect_report.py`: cases for improvement, equality, refused downgrade, deferral passthrough, failed-recollection refusal, and carrier agreement (V-01..V-05).
6. `tests/test_rununify_execute_item_gates.py`: correct the falsified call count, add the new ordering pin, and confirm the two existing pins still pass unweakened (E-06).

## Deferred / out of scope (with reason)

- THE ORCHESTRATOR STILL WILL NOT RETIRE ON `substantially-complete` (F-7). Retirement requires every child `executed` (`runner_shared.py:6443`), so a rescued item unblocks its SIBLINGS but leaves the parent stranded rather than retired. Widening the retirement bar is deliberately NOT done here: that bar is a separate, reasoned contract (`runner_shared.py:6440-6442` says in terms that it is not `EXECUTION_SUCCESS_STATES`) governed by spec `77tr3o`, and changing it inside a defect fix would be an unreviewed contract change. What this plan removes is the sibling cascade and the false `partial`; the parent's retirement follows normally once the item reaches `executed` through the finalize path this fix re-opens.
  - Carrier-Declined: Nothing to carry: this is not deferred work but a statement of the fix's correct BOUNDARY. The retirement bar is spec `77tr3o`'s reasoned contract and is not defective, and a rescued item that reaches `executed` through the re-opened finalize path retires its parent normally, so no future act is pending.
- THE AGY HOST TRUNCATION that produces the empty first turn is `ty7w6o`'s subject, and the zero-work retry is `dy9ymn`'s. This plan deliberately fixes the SCORING independently of the trigger, so it holds for any future host or condition that ends a turn before its outcome is written.
  - Carrier: s0gnha
- NO DEPENDENCY, SUCCESS-BAR, OR RETIREMENT PREDICATE IS TOUCHED. The measured cascade was correct behavior on a wrong input (F-4). Loosening any of them would dispatch a dependent against a base lacking the commits it depends on, which is strictly worse than the defect.
  - Carrier-Declined: A rejected alternative, recorded so it is not re-proposed. The measured cascades were correct behavior on a wrong input, so there is no future state in which loosening them becomes right and no work to hand off.
- NOT CHANGING `reconcile_disposition` ON ANY HOST. It is already correct and pure; the bug is that its answer is never asked for a second time.
  - Carrier-Declined: Nothing to carry: the function is not defective, so declining to edit it leaves no outstanding obligation.

## Scope check

- Over-scope: none. One product file, two test files. No host driver is edited, no predicate is widened.
- Under-scope: the orchestrator retirement bar (F-7) and the two sibling plans' concerns, each excluded with a reason above. A reviewer should confirm those exclusions are right rather than assume them.

## Required tests / validation

`python3 -m pytest`, run BARE as the repository contract requires, with the actual summary line pasted
into each `V-*`. New and changed cases live in `tests/test_defect_report.py` (the re-ask's existing home)
and `tests/test_rununify_execute_item_gates.py` (the ordering pins). Every V-item below demands PASTED
output, not a claim.

Beyond the unit surface, the two measured runs are the falsification standard: a rescore that would not
have converted `zqs0px` from `partial` to `substantially-complete` given that run's on-disk outcome and
collection receipt has not fixed this defect. `V-02` reconstructs exactly that case in `tmp_path`
(never against the live, gitignored `.aw/records/runs/` tree, which CI does not have).

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
- Resolution or deferral rationale: RESOLVED: NO, and deliberately, because the verifier block sits EARLIER in the body (`runner_shared.py:13098-13188`) than the rescore point, so "re-running" it would mean either a backward jump or a duplicated verifier invocation, and a second paid verifier turn inside one attempt is a spend this defect fix has no mandate for. The consequence is stated plainly rather than hidden: a rescued item reaches the integration gate with `verify_disp` still `None`, so `integration_is_earned` (`oc_runipd.py:3912-3972`) falls to its suite-check branch and the DRIVER runs the suite itself for the trust signal, which is the same posture `--no-verify` runs use today and is an existing, reviewed path (`novalnomerge-01` / `evgi9n`). So the rescued item is integrated on a driver-observed suite result, never on an unverified agent claim. `V-06` pins that specific consequence so it cannot regress into "integrated on no signal at all".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `pytest` output for the `rescore_is_an_improvement` cases showing ALL of: three improving pairs return True (`partial`->`substantially-complete`, `partial`->`executed`, `failed-safely`->`substantially-complete`); equal pairs return False; every downgrade returns False including `substantially-complete`->`partial` and `executed`->`partial`; `integration-deferred`, the stopped and the forced dispositions return False in BOTH directions; and an unrecognized status on either side returns False. Plus a demonstration that the function performs no I/O and mutates neither argument.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a test that RECONSTRUCTS THE MEASURED CASE in `tmp_path`: an attempt whose first score is `partial` with no outcome file, a re-ask that writes an outcome carrying `"disposition": "executed"` plus a collection receipt recording `status: complete` and `outcome` collected, and the assertion that the item ends `substantially-complete` and NOT `partial`. Must also paste the negative control: the SAME fixture with the receipt recording the outcome collection as `failed` leaves the item `partial`, proving the recollection gate is real and not decorative.
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
  - Required evidence: pasted output showing exactly one `ipd-rescored` event in `events.jsonl` for an accepted rescore, carrying `id6`, `attempt`, `before` and `after`; and ZERO such events for each of the three non-acceptance paths (no re-ask performed, recollection failed, rescore not an improvement).
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
