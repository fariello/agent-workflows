# IPD: Emit a refusal record when an orchestrator is deferred so a no-op run says why nothing ran

- Date: 2026-09-08
- Kind: child
- Concern: A run that does no work reports success and never says why. Naming an orchestrator whose children are not `approved` produces a run whose summary reads `Outcome: COMPLETED`, `Progress: 1/1 100% (1 reviewed)` and a table row with an empty `Verify` column, with no line anywhere stating that the orchestrator was DEFERRED, why, or what to do about it. The runner already computes the answer: `dispatch_orchestrator_item` picks a typed `ORCH_REASON_*` value for every refusal. But on the RECONSIDER path (the deferral) that reason is written ONLY to `events.jsonl`, and on the TERMINATE path it is written onto the item as `orchestrator_refusal_reason`, which no read surface consumes. So a precise, machine-readable diagnosis is produced and then discarded, and the operator is left to infer from a green summary that nothing happened.
- Scope: Close the last mile only. Write the refusal record on the RECONSIDER (deferred) path too, so the deferral reason and a remedy reach the queue item rather than only the event log, and make the existing typed reasons render. Reuses the refusal record and both render surfaces that reviewed plan `r2i1b1` builds; adds NO new refusal decision and changes NO gate's verdict.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_deferral_reporting.py
- Item-Dependencies: executed:r2i1b1
- Status: executed
- Readiness: go-pending-approval
- Set: runghostid
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zyw4n3
- From-Backlog: i2fjf8
- Blocks-Release: next

## Workflow history
- 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: zyw4n3 verified (set runghostid, attempt 1).
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-907, all FIXED, none deferred; readiness `go-pending-approval`. Record: `.aw/records/reviews/20260908-runghostid-01-zyw4n3-emit-a-refusal-record-when-an-orchestrator-is-deferred-so-a.review.md`. `aw ipd lint --phase author` CONFORMING before semantic review and `--phase review-finalize` conforming after, so nothing here was structural. DISCLOSURE: same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on EXECUTING its claims rather than re-reading them. NINE things were run: `dispatch_orchestrator_item` was DRIVEN on a purpose-built two-plan temp repo to reach the RECONSIDER branch and its item keys dumped; the same function was driven to reach TERMINATE; both reason-constant blocks were printed and their value sets differenced; `render_run_summary_table` was rendered on a `queued` orchestrator; `render_stream`'s first-party imports were AST-walked; every consumer of the two bespoke fields was grepped across `agent_workflows/` and `tests/`; both hosts' `## Dependency blocks (why)` copies were located; `evaluate_backlog_close` was run for `i2fjf8` and its carriers grepped; and the bare suite plus the named module were run.
  THE CENTRAL DEFECT REPRODUCES EXACTLY AS THE PLAN SAYS, which is the main result and is why this is a GO: driving the real dispatch on a deferred orchestrator gives `outcome=reconsider`, `reason=children-unfinished`, `status` still `queued`, and item keys with NO refusal field, while rendering the real summary on that item produces no diagnostics line at all. The plan's diagnosis, narrowing and dependency are all correct. SEVEN THINGS WERE WRONG AROUND IT, none fatal. The sharpest is that a SECOND reason vocabulary exists (`RETIRE_REFUSED_*`, four values) which shares three values with `ORCH_REASON_*` and carries a near-miss pair (`unfinished-children` versus `children-unfinished`), so E-02's mapping had to state which set it keys on and assert the translation (PR-901). Next, the refusal record lives in `render_stream.py` by `r2i1b1`'s deliberate circular-import-avoiding design, so E-01 must IMPORT it and must not move or re-export it into `runner_shared` (PR-902). Third, "no consumer reads the bespoke fields" is false: a live test does, which strengthens the plan's keep-them decision but changes what E-03 must prove (PR-903). Also fixed: the named "known baseline failure" does not exist and the module is 112 PASSED, so an executor could have excused their own regression (PR-904); the `## Dependency blocks (why)` section is in BOTH hosts and is status-gated rather than a general fallback (PR-905); every line number in the plan had drifted ~340 lines in one day (PR-906); and the release gate is this plan's ALONE, so its finalize can legitimately auto-close the item (PR-907). OQ-01 was addressed to the reviewer and is now RESOLVED: the remedy must NOT mention `--full-auto`, since suggesting an approval bypass inside a refusal message is the worst possible placement for it.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `i2fjf8`, inheriting its `Blocks-Release: next` gate. THIS IS A HEAVY NARROWING: the item names TWO coupled defects and DEFECT 1 IS DEAD. Defect 1 was that the runner printed a Run ID, a State directory and a `resume` hint for a run it never persisted. I re-ran the item's own scenario at HEAD `8b4e1570` (`aw oc run 20260908-runanalytics-00-5lxvl3 --prepare-only`, a `reviewed` orchestrator whose children are `to-review`) and the announced directory EXISTS on disk with `state.json`, `events.jsonl`, `manifest.json`, `outcomes/`, `prompts/`, `sessions/`, and `aw runs <id>` renders it. TWO INDEPENDENT REASONS IT CANNOT RECUR, both verified in code: (a) `Run ID:` and `State directory:` are printed only AFTER `initialize_run` returns (`oc_runipd.py:8018-8020`), and `initialize_run` mkdirs the run directory at `:2927` before returning at `:3126`; (b) the empty-queue paths RAISE before that mkdir (`:2842-2860`, `EmptyStatusSelection` for a status selector and `DriverError` for `all`), with an inline comment stating the intent verbatim: "Freezing an empty queue instead would create a run directory, a report, and a ledger for zero work, which is durable state an operator then has to reconcile." That landed in `287874dd` (2026-09-05, "one shared needly-review predicate and the draft admission gate"), a week after the item was filed. I also confirmed the specific RESUME-hint symptom cannot appear for an empty queue even hypothetically: `render_continuation_hint` chooses the resume line only when NOT `all_success`, and `all(...)` over an empty queue is vacuously True, so an empty queue would take the INSPECT branch. Defect 1 is therefore not graduated. DEFECT 2 SURVIVES BUT IS MOSTLY COVERED, and I graduated only the residual. Reviewed plan `r2i1b1` (Set `orchprobe`, Order 01) builds the entire mechanism defect 2 needs: E-01 defines ONE shared refusal record (reason CODE, human REASON, REMEDY) stored on the queue item, E-02 makes the summary's diagnostics block render it for ANY status instead of the hardcoded allowlist, E-03/E-04 route `aw runs`' Issue predicate through one function and count a refusal as an issue across `--json`/`--agent`/`--issues`, and E-05 makes reason and remedy visible WITHOUT `--detail`. Its scope line explicitly excludes "adding any new refusal (child 03 does that)". So `r2i1b1` supplies the plumbing and the rendering; what remains is that the ORCHESTRATOR DEFERRAL never populates it. MEASURED THE RESIDUAL EXACTLY, which is what this plan is: I ran the item's scenario and dumped `state.json`, and the queue item's keys are `action, attempts, configured_file, dependencies, from_backlog, id6, initial_status, kind, order, position, setid, status` - NO refusal field, NO reason, NO remedy. Reading `dispatch_orchestrator_item` shows why: on TERMINATE it writes `item["orchestrator_refusal_reason"]` and `item["orchestrator_refusal_detail"]` (`runner_shared.py:3047-3048`), but on RECONSIDER it deliberately writes NO status and sends the reason only to `events.jsonl` (`:3017-3033`), and grepping `render_stream.py`/`run_viewer.py` for `orchestrator-deferred` and for `orchestrator_refusal_reason` returns NOTHING, so neither the event nor the item field reaches any read surface today.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a run that did nothing say so. The runner already knows the reason precisely; this plan puts it where the two read surfaces `r2i1b1` builds will display it, so an operator stops having to infer "nothing ran" from a green `COMPLETED` summary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: populate the refusal record on the deferral path

- [x] E-01 Write `r2i1b1`'s refusal record on the RECONSIDER path in `dispatch_orchestrator_item` (`agent_workflows/runner_shared.py`, the RECONSIDER branch at `:3356-3372` as re-measured at review; this plan's `:3017-3033` is stale by ~340 lines, so LOCATE BY THE `if decision.outcome == ORCH_DISPATCH_RECONSIDER:` line, never by number), where today only an `orchestrator-deferred` event is appended and NO item field is written. Use `r2i1b1`'s shared constructor rather than inventing a second record shape; if it has not landed, STOP and report rather than forking one, because two refusal-record shapes on the same queue item is the exact divergence its E-01 exists to prevent.
  THE RECORD LIVES IN `render_stream.py`, NOT `runner_shared.py`, AND THAT IS DELIBERATE (review, F-14). `r2i1b1` E-01 sites the dataclass in `render_stream` for a MECHANICAL reason it states explicitly: `runner_shared` already imports `render_stream` at module level (re-verified at review, `runner_shared.py:147`, `from agent_workflows.render_stream import Palette, render_run_summary_table`), and `render_stream` imports ZERO first-party modules (re-verified by AST walk), so the reverse edge cannot exist without a circular import. CONSEQUENCE FOR THIS PLAN: importing the constructor into `runner_shared` is import-LEGAL and requires no new path, but you must import it FROM `render_stream` and must NOT move, re-export, or re-define it in `runner_shared` for convenience. Doing so would break the property `r2i1b1` E-01 depends on and its E-08 asserts. If you find yourself needing to edit `render_stream.py`, STOP: that file is `r2i1b1`'s and is not in this plan's `- Scope-Paths:`.
  RESPECT THE ONE INVARIANT THIS PATH GUARDS: the RECONSIDER branch must still write NO `status`, because the item has to stay `queued` so a later iteration re-selects it when its children finish; the surrounding comment records that writing a terminal `dependency-blocked` here excluded such an orchestrator forever. Adding a refusal record is additive and must not disturb that. Re-verified at review by driving the real function on a two-item fixture: the outcome is `reconsider` with reason `children-unfinished`, `status` stays `queued`, and the item's keys are exactly `action, attempts, id6, position, setid, status` with NO refusal-bearing field, which is this plan's F-6/F-7 reproduced.
  - Depends on: none
  - Expected outcome: after a deferred-orchestrator run, the queue item carries a refusal record naming the deferral, and its `status` is still `queued`; the record type is IMPORTED from `render_stream` and neither redefined nor re-exported in `runner_shared`.
  - Execution state: performed

- [x] E-02 Map each existing reason value to a human REASON and an actionable REMEDY, reusing the typed vocabulary already defined rather than writing new prose per site. The seven `ORCH_REASON_*` constants are at `runner_shared.py:3031-3042` (re-measured at review; this plan's `:2692-2703` citations are stale by ~340 lines): `ORCH_REASON_UNFINISHED_CHILDREN` = `children-unfinished`, `ORCH_REASON_DEAD_CHILDREN` = `children-terminally-failed`, `ORCH_REASON_CHILDREN_NOT_IN_RUN` = `children-not-in-this-run`, `ORCH_REASON_NO_CHILDREN` = `no-children`, `ORCH_REASON_UNAUTHORED_CHILD_ROWS` = `unauthored-child-rows`, `ORCH_REASON_FINALIZE_REFUSED` = `finalize-refused`, `ORCH_REASON_NO_ORCHESTRATOR` = `no-orchestrator`.
  THERE IS A SECOND, OVERLAPPING VOCABULARY AND THIS PLAN COUNTED ONLY ONE OF THEM (review, F-13). `RETIRE_REFUSED_*` (`:2555-2558`) is the vocabulary `evaluate_set_retirement` produces and `decide_orchestrator_dispatch` CONSUMES before translating to `ORCH_REASON_*`. Measured, the two sets share three values (`no-children`, `no-orchestrator`, `unauthored-child-rows`) and differ on a fourth that is a NEAR-MISS PAIR: `RETIRE_REFUSED_UNFINISHED_CHILDREN` is `unfinished-children` while `ORCH_REASON_UNFINISHED_CHILDREN` is `children-unfinished`. Two nearly identical strings differing only in word order is precisely the shape that makes a dict-keyed mapping silently miss. So E-02 must state WHICH vocabulary the mapping is keyed on, and prove the other cannot reach it: measured at review, `dispatch_orchestrator_item` writes `decision.reason`, which is always an `ORCH_REASON_*` value because `decide_orchestrator_dispatch` translates every `RETIRE_REFUSED_*` branch before returning, so keying on `ORCH_REASON_*` is CORRECT. Assert that translation rather than assuming it, because if a future branch forwards a `RETIRE_REFUSED_*` value unchanged the mapping degrades to the generic fallback this item forbids.
  THE MAPPING MUST FAIL LOUDLY ON AN UNKNOWN CODE, not fall back to prose. Because two vocabularies exist and a third could be added, a dict lookup missing a key is a real risk rather than a hypothetical one. Decide and record whether an unmapped code raises, or yields a record explicitly labelled as an unmapped code (which is honest and still visible), but do NOT let it produce a bare or empty remedy: an empty remedy renders as a refusal record with nothing actionable in it, which looks like the very silence this plan exists to remove.
  THE REMEDY IS THE HALF THAT MATTERS and is what the item actually asked for: it wanted the run to say something like "children not executed; did you mean to include the children or pass --full-auto?" rather than a bare status. Each remedy must name a concrete next action. Follow `m7gvuz` E-06's discipline on wording: phrase the remedy as the CONSTRUCTIVE action, never as an instruction to delete or weaken the thing that refused. See OQ-01 on the `--full-auto` wording specifically.
  - Depends on: E-01
  - Expected outcome: every one of the seven `ORCH_REASON_*` values yields a specific human reason and a remedy naming an action; the mapping's keyed vocabulary is stated and the `RETIRE_REFUSED_*` translation asserted; an unknown code is handled deliberately and never as an empty remedy; no reason falls through to a generic string.
  - Execution state: performed

- [x] E-03 Make the TERMINATE path use the SAME record, so the two halves of one function stop reporting differently. Today TERMINATE writes bespoke fields `item["orchestrator_refusal_reason"]` and `item["orchestrator_refusal_detail"]` (`:3387-3388` at review) that NO RENDER surface reads. Populate `r2i1b1`'s record there too.
  KEEP THE EXISTING FIELDS, AND THE REASON IS NOW STRONGER THAN THIS PLAN STATED (review, F-15). The plan says "grep shows NO surface reads" them and that "a consumer outside this grep may exist". Measured, a consumer exists IN THIS REPOSITORY: `tests/test_orchestrator_retirement.py:3310-3312` asserts `item["orchestrator_refusal_reason"] == rs.RETIRE_REFUSED_NO_CHILDREN` and that `orchestrator_refusal_detail` contains a substring. So renaming or removing them BREAKS A LIVE TEST, and the correct statement is that no RENDER surface reads them while a test does. That test also pins the field to a `RETIRE_REFUSED_*` constant whose VALUE happens to equal its `ORCH_REASON_*` twin (`no-children`), which is exactly the near-miss aliasing E-02 must not be confused by.
  PRESERVE `unsatisfied_dependencies` AND `unsatisfied_dependency_reasons` (`:3378-3386`) exactly, since `write_report`'s `## Dependency blocks (why)` section reads them. TWO CORRECTIONS TO THIS PLAN'S CITATION (review, F-16). FIRST, that section exists in BOTH hosts (`oc_runipd.py:3222` and `agy_runipd.py:2152`), not only oc, so "the one place a deferral reason surfaces today" has two implementations and a claim about it must check both. SECOND and more important, it is gated on `status == "dependency-blocked"`, so it renders ONLY when `terminal_status` takes its default; a TERMINATE that ever wrote a different terminal status would surface nowhere even today. Do not treat that section as a general safety net.
  - Depends on: E-02
  - Expected outcome: both dispatch outcomes populate the shared record; the existing bespoke fields and both dependency fields are unchanged and `tests/test_orchestrator_retirement.py` still passes; the dependency-blocks report section still renders on BOTH hosts.
  - Execution state: performed

### Task group 2: prove it, without depending on live run state

- [x] E-04 Test the deferral reporting with a FIXTURE, never against `.aw/records/runs/`. That tree is gitignored with zero tracked files (re-verified at review: `git ls-files` returns nothing against 143 local run directories), and `tests/test_run_viewer.py:3` and `:25` record that it "is gitignored and absent in every fresh checkout", so a test keyed to live runs would be unrunnable in CI and in every lane worktree the runner allocates. Drive `dispatch_orchestrator_item` directly with a constructed state, as the orchestrator-retirement tests already do; a WORKING recipe is `tests/test_orchestrator_retirement.py`'s `DispatchRunCase`, and at review a two-plan temp repo plus a two-item queue was enough to reach the RECONSIDER branch.
  COVER, AS SEPARATE CASES: a RECONSIDER deferral populates the record AND leaves `status` still `queued`; a TERMINATE refusal populates the same record; each of the seven `ORCH_REASON_*` values produces a non-generic reason and remedy; an UNKNOWN reason code is handled as E-02 decided rather than yielding an empty remedy; and the `orchestrator-deferred` event is still appended with its existing fields on BOTH paths (the two events differ: the TERMINATE one carries `status` and `unauthored_rows`, the RECONSIDER one does not).
  ASSERT THE RECONSIDER CASE FAILS BEFORE THE CHANGE, so the test is proven to bite. Do NOT pin that to HEAD `8b4e1570` as this plan does; that HEAD is already historical. Reproduce the pre-change failure in YOUR worktree by reverting your own edit, and paste both outputs.
  ADD ONE MORE CASE THIS PLAN OMITS: assert the record's type is the one IMPORTED from `render_stream`, not a look-alike defined locally (for example by identity against the imported symbol). Without it, the divergence `r2i1b1` E-01 exists to prevent could be reintroduced here and every other test would still pass.
  - Depends on: E-03
  - Expected outcome: fixture-driven tests passing in a bare worktree; the RECONSIDER case fails before the change and passes after, reproduced in the executing worktree; the record's identity asserted against the imported type.
  - Execution state: performed

- [x] E-05 Verify END TO END that the reason now REACHES both surfaces, which is the only evidence that matters for the item's complaint, and confirm the no-op run no longer looks like a success. Re-run the item's exact scenario (name a `reviewed` orchestrator whose children are not `approved`) and show the summary and `aw runs` output carrying the reason and remedy.
  CHECK `r2i1b1` HAS LANDED FIRST: this plan declares `Item-Dependencies: executed:r2i1b1` precisely because rendering is its deliverable, not this plan's, and without it the record is written but invisible. NOTE `r2i1b1` IS NOW `approved` (this plan says `reviewed`), so it is cleared to run but has NOT executed; the dependency edge remains unmet and the runner enforces it.
  THE DEFERRED ITEM IS `queued`, WHICH IS WHY THIS DEPENDENCY IS LOAD-BEARING RATHER THAN MERELY TIDY (review, F-17). Measured at review, the summary's diagnostics block is a closed allowlist over `dependency-blocked`, `failed-safely`, `merge-needs-human`, `merge-refused` (renamed 2026-09-21 from `integration-blocked`/`merge-conflict`; both spellings are listed) and `interrupted`; a deferred orchestrator is `queued`, so it matches NONE of them and renders nothing no matter what fields it carries. Confirmed by rendering the real `render_run_summary_table` on a `queued` orchestrator: the output has no `Diagnostics` line at all, `Verify` is `-`, and the header reads a bland `Outcome: QUEUED`. So the record this plan writes is invisible until `r2i1b1` E-02 replaces that allowlist with an any-status branch. Executing this plan first would produce ZERO operator-visible change, which is exactly what the dependency prevents.
  ALSO confirm the ORDERING claim: the summary must still not misreport the item as failed, because a deferral is not a failure; the goal is an explained no-op, not a red run. If `r2i1b1` has landed and the rendering still does not show the record, report that as a finding against the rendering rather than adding a second render path here.
  DO NOT EXPECT THE `Outcome:` HEADER TO TURN GREEN-TO-RED, and say which line actually changes. Measured, the header for an all-`queued` run reads `QUEUED` rather than `COMPLETED`, so this plan's F-5 wording ("`Outcome: COMPLETED`, `Progress: 1/1 100%`") describes a run in which the CHILD was reviewed successfully alongside the deferred parent, not the parent alone. State in the evidence which run shape you reproduced, because "the summary said COMPLETED" and "the summary said QUEUED" are different starting points and only the first is the item's complaint.
  - Depends on: E-04
  - Expected outcome: a pasted before/after of the same invocation showing the deferral reason and remedy in the summary and in `aw runs`, with the item still reported as deferred rather than failed, and with the reproduced run shape stated.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The runner ALREADY computes a precise typed reason for every orchestrator refusal: seven `ORCH_REASON_*` constants (`runner_shared.py:3031-3042` at review; this plan's `:2692-2703` is stale by ~340 lines) and a three-way outcome contract (RETIRE / RECONSIDER / TERMINATE). This plan is about delivery, not diagnosis.
- THERE ARE TWO REASON VOCABULARIES, NOT ONE. `RETIRE_REFUSED_*` (`:2555-2558`, produced by `evaluate_set_retirement`) is translated by `decide_orchestrator_dispatch` into `ORCH_REASON_*` before any item field is written. They share three values and carry a NEAR-MISS PAIR: `unfinished-children` versus `children-unfinished`. Key the mapping on `ORCH_REASON_*` and assert the translation.
- THE REFUSAL RECORD LIVES IN `render_stream.py` BY DESIGN. `runner_shared.py:147` imports `render_stream` at module level and `render_stream` imports zero first-party modules (AST-verified), so the record cannot live in `runner_shared` without a circular import. Import it; never redefine or re-export it.
- THE SUMMARY'S DIAGNOSTICS BLOCK IS A CLOSED ALLOWLIST over five statuses (`render_stream.py:2152-2178`). A deferred orchestrator is `queued`, matches none of them, and therefore renders NOTHING regardless of the fields it carries. That is why `r2i1b1` must land first.
- The three outcomes exist because a single write was measurably wrong twice: a terminal `dependency-blocked` excluded an orchestrator whose children finished later in the SAME run (from an event literally named `orchestrator-deferred`), while leaving everything reconsiderable would retry a structural refusal forever and SPIN. Do not collapse them.
- THE RECONSIDER PATH DELIBERATELY WRITES NO STATUS (`:3017-3021`), and the comment explains that recording the deferral is still required because "an unlabelled item with no event would be indistinguishable from one never reached". That is exactly this plan's argument, applied one layer further out: the EVENT is not enough either, because no read surface consumes it.
- The TERMINATE path already writes `orchestrator_refusal_reason`/`orchestrator_refusal_detail` onto the item (`:3387-3388`), described in its own comment as "additive, so a consumer need not parse prose". No RENDER surface consumes them, but a TEST does (`tests/test_orchestrator_retirement.py:3310-3312`), so they cannot be renamed or removed without breaking it.
- `write_report`'s `## Dependency blocks (why)` section exists in BOTH hosts (`oc_runipd.py:3222`, `agy_runipd.py:2152`) and is gated on `status == "dependency-blocked"`, so it renders only for a TERMINATE that took the default terminal status. A RECONSIDER deferral appears in no report at all.
- BOTH HOSTS CALL THE SHARED DISPATCH (`oc_runipd.py:7386`, `agy_runipd.py:4398`), each importing it from `runner_shared`, so a change inside `dispatch_orchestrator_item` reaches both hosts with no per-host edit. That is why this plan needs only one source path.
- Plan `r2i1b1` (now `approved`, not `reviewed`) owns the refusal record and BOTH render surfaces, and explicitly excludes adding new refusals. Plan `m7gvuz` (also now `approved`) adds a different refusal (orchestrator carrying uncovered work) and E-06 there sets the remedy-wording discipline: name the constructive action, never suggest deleting the checklist.
- New tests on the run surface must use fixtures: `.aw/records/runs/` is gitignored with zero tracked files (verified) and `tests/test_run_viewer.py` records that it is "absent in every fresh checkout". `tests/test_orchestrator_retirement.py`'s `DispatchRunCase` is the working recipe for driving the dispatch directly.
- `tests/test_orchestrator_retirement.py` PASSES ENTIRELY (112 passed, measured at review). This plan's claim that it carries a known baseline failure named `test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` is false on both counts: the module is green and that test name exists nowhere in `tests/`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | DEFECT 1 IS DEAD: the announced run directory now EXISTS. Re-ran the item's scenario and the printed State directory contained `state.json`, `events.jsonl`, `manifest.json`, `outcomes/`, `prompts/`, `sessions/`, and `aw runs <id>` rendered it. | measured at `8b4e1570` |
| F-2 | It cannot recur, reason one: `Run ID:`/`State directory:` print only after `initialize_run` returns, and that function mkdirs the run dir before returning. | `oc_runipd.py:8018-8020`; mkdir at `:2927`, return at `:3126` |
| F-3 | It cannot recur, reason two: the empty-queue paths RAISE before the mkdir, with an inline comment stating the intent ("Freezing an empty queue instead would create a run directory ... for zero work"). | `oc_runipd.py:2842-2860`; landed in `287874dd`, 2026-09-05 |
| F-4 | Even hypothetically, an EMPTY queue could not produce the RESUME hint the item saw: the resume line is chosen only when NOT `all_success`, and `all(...)` over an empty queue is vacuously True, so it would take the INSPECT branch. | `oc_runipd.py:7376-7383`; measured `all([]) is True` |
| F-5 | DEFECT 2 REPRODUCES: the no-op run's summary reads `Outcome: COMPLETED`, `Progress: 1/1 100% (1 reviewed)` and gives no deferral reason, no remedy, and an empty `Verify` column. | measured at `8b4e1570` running the item's scenario |
| F-6 | THE RESIDUAL IS EXACTLY THE MISSING RECORD: the deferred queue item's keys are `action, attempts, configured_file, dependencies, from_backlog, id6, initial_status, kind, order, position, setid, status` - no refusal, reason, or remedy field. | measured by dumping `state.json` after the run at `8b4e1570` |
| F-7 | The RECONSIDER path sends the reason ONLY to `events.jsonl` and writes no item field. | `runner_shared.py:3017-3033` |
| F-8 | The TERMINATE path DOES write the reason onto the item, so the two halves of one function already report differently. | `runner_shared.py:3047-3048` |
| F-9 | NEITHER carrier reaches a read surface: grepping `render_stream.py` and `run_viewer.py` for `orchestrator-deferred` and `orchestrator_refusal_reason` returns nothing. | measured at `8b4e1570` |
| F-10 | THE RENDERING IS ALREADY OWNED, so this plan must not build it: `r2i1b1` defines the shared refusal record and renders it in the summary for ANY status and in `aw runs` across all payloads, and its scope excludes adding new refusals. UPDATED at review: `r2i1b1` is now `- Status: approved` (this plan says `reviewed`), so it is cleared to run but has not executed; the dependency edge is still unmet. | `r2i1b1` `- Status: approved`, `- Readiness: go-pending-approval`, Scope line, E-01 through E-08 |
| F-11 | The sibling that ADDS refusals is `m7gvuz` (also now `approved`), and it adds a DIFFERENT one (an orchestrator carrying work no child covers), not the not-all-children-executed deferral. So the deferral has no owner but this plan. | `m7gvuz` E-06 and its Scope line |
| F-12 | The seven typed reasons already exist, so E-02 is a mapping exercise rather than a diagnosis one. | `runner_shared.py:3031-3042` (re-measured; the plan's `:2692-2703` is stale) |
| F-13 | **TWO REASON VOCABULARIES EXIST AND THIS PLAN COUNTS ONLY ONE.** `RETIRE_REFUSED_*` (4 values, `:2555-2558`) is produced by `evaluate_set_retirement` and TRANSLATED into `ORCH_REASON_*` (7 values) by `decide_orchestrator_dispatch`. Three values are shared verbatim (`no-children`, `no-orchestrator`, `unauthored-child-rows`) and one pair is a NEAR MISS: `unfinished-children` versus `children-unfinished`. Keying a mapping on the wrong set, or assuming the two are interchangeable, silently yields the generic fallback E-02 forbids. The translation makes `ORCH_REASON_*` the correct key, but that must be asserted, not assumed. | both constant blocks printed and their value sets differenced; `decide_orchestrator_dispatch` translation branches read at `:3136-3168` |
| F-14 | **THE RECORD LIVES IN `render_stream.py`, WHICH THIS PLAN DOES NOT DECLARE, AND MUST NOT BE MOVED.** `r2i1b1` E-01 sites it there because `runner_shared.py:147` imports `render_stream` at module level while `render_stream` imports zero first-party modules, so the reverse edge would be circular. Importing it into `runner_shared` is legal and needs no new path; redefining or re-exporting it there would break the property `r2i1b1` E-08 asserts. | `runner_shared.py:147`; AST walk showing `render_stream` has no first-party imports; `r2i1b1` E-01 |
| F-15 | **A LIVE TEST READS THE BESPOKE FIELDS, so "no consumer exists" is wrong in a way that matters.** `tests/test_orchestrator_retirement.py:3310-3312` asserts `orchestrator_refusal_reason == RETIRE_REFUSED_NO_CHILDREN` and a substring of `orchestrator_refusal_detail`. The correct claim is that no RENDER surface reads them. Renaming or removing them breaks that test, which strengthens rather than weakens this plan's decision to keep them. | grep for both field names across `agent_workflows/` and `tests/` |
| F-16 | **THE `## Dependency blocks (why)` SECTION IS IN BOTH HOSTS AND IS STATUS-GATED.** It exists at `oc_runipd.py:3222` AND `agy_runipd.py:2152`, and both gate on `status == "dependency-blocked"`, so it renders only for a TERMINATE that took the default `terminal_status`. It is not a general fallback, and a claim about "the one place a deferral surfaces" must check both copies. | both call sites read; the `blocked` list comprehension's status filter |
| F-17 | **THE DEPENDENCY ON `r2i1b1` IS LOAD-BEARING, PROVEN BY RENDERING.** The diagnostics block allowlists five statuses; a deferred orchestrator is `queued` and matches none, so it renders nothing whatever fields it carries. Confirmed by calling the real `render_run_summary_table` on a `queued` orchestrator: no `Diagnostics` line, `Verify` is `-`. So executing this plan before `r2i1b1` yields zero operator-visible change. | `render_stream.py:2152-2178`; live render |
| F-18 | THE SUITE BASELINE AND THE NAMED KNOWN FAILURE ARE BOTH WRONG. Measured: `1 failed, 5929 passed, 3 skipped, 2 xfailed` (plan says `1 failed, 5648 passed`), the failure being the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`. `tests/test_orchestrator_retirement.py` is 112 PASSED, and the test the plan names as its known failure (`test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`) exists NOWHERE in `tests/`. An executor told to excuse a failure in that module could excuse a real regression they caused. | bare suite run; module run in isolation; grep for the named test |
| F-19 | THIS PLAN IS THE SOLE CARRIER OF A RELEASE-BLOCKING ITEM, so its finalize CAN legitimately close it. `i2fjf8` is `graduated` with `- Blocks-Release: next`, and grep finds exactly ONE artifact carrying `From-Backlog: i2fjf8`: this plan. `evaluate_backlog_close` names only this plan as the unexecuted carrier, so on a clean finalize the runner's own close path applies, unlike a Set whose orchestrator also carries the link. `next` resolves to release `f33nrj` (2.0.0, `planned`). | `evaluate_backlog_close(repo,'i2fjf8',[])`; grep for carriers; the release record |

## Proposed changes (ordered, validatable)

1. Write `r2i1b1`'s refusal record on the RECONSIDER path, IMPORTING the type from `render_stream`, preserving the no-status invariant (E-01).
2. Map all seven `ORCH_REASON_*` values to a human reason and an actionable remedy, stating the keyed vocabulary and handling an unknown code deliberately (E-02).
3. Populate the same record on the TERMINATE path, keeping the existing fields intact so the live test that reads them still passes (E-03).
4. Test with fixtures, proving the RECONSIDER case fails before the change in the executing worktree, and asserting the record's imported identity (E-04).
5. Verify end to end that both surfaces now show the reason, with `r2i1b1` landed (E-05).

## Deferred / out of scope (with reason)

- DEFECT 1 (the ghost Run ID / State directory / resume hint). DEAD, on three independent measurements (F-1 through F-4), fixed as a side effect of `287874dd` on 2026-09-05. Re-implementing it would be work against already-shipped behavior.
- THE REFUSAL RECORD ITSELF AND BOTH RENDER SURFACES. Owned by reviewed plan `r2i1b1` (F-10), which this plan declares as an `Item-Dependencies` edge rather than duplicating. Building a second record shape or a second render path is the precise divergence its E-01 exists to prevent.
- ADDING ANY NEW REFUSAL DECISION, including the uncovered-work probe. That is `m7gvuz`, and `r2i1b1`'s scope line explicitly assigns new refusals to it.
- CHANGING WHAT THE ORCHESTRATOR DISPATCH DECIDES. The three-way contract is correct and hard-won (a terminal write stranded an orchestrator forever; a fully reconsiderable one would spin). This plan adds reporting only.
- REMOVING the bespoke `orchestrator_refusal_reason`/`orchestrator_refusal_detail` fields once the shared record exists. Tempting, but they are documented as additive and a consumer outside this repository's grep may read them; deleting them is a separate, provable change.
- THE `aw runs` / summary WORDING for a deferral being reported as an ISSUE rather than a failure. `r2i1b1` E-04 decides how a refusal appears in the Issue column; this plan supplies the record and checks in E-05 that a deferral is not misreported as a failure, but does not re-litigate that presentation.

## Scope check

- Over-scope: none. One source module and one new test module. `run_viewer.py` and `render_stream.py` are deliberately NOT in `Scope-Paths` even though E-05 reads their output and E-01 IMPORTS from `render_stream`, because rendering and the record's definition are both `r2i1b1`'s deliverables. IMPORTING a symbol from an undeclared module is not an edit and needs no declaration; DEFINING or re-exporting one there would be, and is forbidden (F-14).
- ONE PATH MAY BE MISSING AND THE EXECUTOR SHOULD KNOW WHY IT IS OMITTED. `tests/test_orchestrator_retirement.py` reads the two bespoke fields E-03 touches (F-15). This plan PRESERVES those fields, so that test should need no edit and is deliberately undeclared; if it turns out to need one, that is a signal the change was not additive after all, so report it rather than quietly editing an undeclared test.
- Under-scope: defect 1 is dropped as already fixed; the record definition and both render surfaces are inherited from `r2i1b1`; no new refusal is added; the dispatch contract is untouched; the summary's status allowlist is NOT repaired here even though it is what makes this plan's output invisible (F-17), because that repair is `r2i1b1` E-02's.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. CORRECTED AT REVIEW (F-18): the stated baseline of `1 failed, 5648 passed` is stale. Measured at review: `1 failed, 5929 passed, 3 skipped, 2 xfailed`, and the single failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL (a gitignored local `opencode-recovery/` dump in this checkout) and may be absent elsewhere. Measure your OWN baseline in the executing worktree and compare failing NODE IDS, never totals.
- `python3 -m pytest tests/test_orchestrator_deferral_reporting.py tests/test_orchestrator_retirement.py` for the focused surface. THE "KNOWN FAILURE" THIS PLAN NAMES DOES NOT EXIST, AND BELIEVING IT IS DANGEROUS: measured at review, `test_orchestrator_retirement.py` is `112 passed`, and `test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` appears NOWHERE in `tests/`. So that module must be GREEN both before and after; any failure there is YOURS. This matters because `tests/test_orchestrator_retirement.py:3310-3312` reads the very fields E-03 touches, so it is the module most likely to catch a real mistake, and an executor primed to excuse a failure in it would excuse exactly the regression it exists to find.
- The end-to-end before/after from E-05 on the item's own scenario, with output pasted.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

Spec `77tr3o` (`runner orchestrator retirement`, `- Status: approved`) governs the orchestrator dispatch contract that `dispatch_orchestrator_item` implements. This plan changes only what is RECORDED for reporting, not what the dispatch DECIDES, so no spec text is contradicted and no `.spec.md` is declared in `Scope-Paths`. Two cautions for the executor. FIRST, if the spec enumerates the fields a dispatch outcome writes, adding a refusal record IS a contract addition: declare `.aw/records/specs/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md` in `Scope-Paths` and justify it here before editing. SECOND, `m7gvuz` E-07 is already amending that same spec and `m7gvuz` is now `approved` (so it may run at any time), which makes the contention live rather than hypothetical: check before touching it and prefer reporting to a racing edit. The `ORCH_REASON_*` constants are the in-code documentation of the reason vocabulary and their comments must stay truthful if E-02 attaches remedies to them.

THE RELEASE GATE IS THIS PLAN'S ALONE, WHICH CHANGES WHAT ITS FINALIZE OWES (review, F-19). Backlog `i2fjf8` is `graduated` and carries `- Blocks-Release: next`, and this plan is the ONLY artifact in the tree carrying `- From-Backlog: i2fjf8` (measured by grep across plans and specs). `evaluate_backlog_close(repo, 'i2fjf8', [])` names exactly one unexecuted carrier: this plan. So unlike a Set whose orchestrator also carries the link, a clean finalize here CAN legitimately close the item through the runner's own `process_backlog_close` path. Two consequences to hold: do not hand-close the item in anticipation, and if the close does not fire, report the recorded verdict rather than setting the status by hand, since the gate exists to keep a release blocker from being dropped silently. `next` resolves to release `f33nrj` (2.0.0, `planned`), so the gate is real and resolvable.

## Open questions

### OQ-01: Should the remedy for the not-all-children-executed deferral mention `--full-auto`?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW: NO, the remedy must not mention `--full-auto`, and the plan's own leaning was correct. This question was addressed to the reviewer, so answering it is this review's job rather than something to defer again.
  THE REASONING, WHICH IS THE PLAN'S OWN PLUS ONE MEASUREMENT. `--full-auto` clears a `reviewed` plan to `auto-approved` through the auto-approve predicate, so offering it as the remedy for "children are not approved" is offering to bypass the approval gate, in a message the operator reads at the exact moment they are frustrated that nothing ran. That is the worst possible placement for such a nudge. The repository is explicit that a gate stating only a prohibition gets complied with by DELETION, which is why remedies must name a constructive action; the corollary is that a remedy must not name a SHORTCUT PAST the thing that refused. `m7gvuz` E-06 sets the same discipline for the sibling refusal, so answering NO also keeps the two refusals' wording consistent rather than having one suggest an approval bypass and the other not.
  THE REMEDY TO USE INSTEAD: name the blocking children and their actual statuses, and say what each needs (review, then human approval) to become runnable. That is strictly more informative than the flag suggestion, because measured, the deferral detail ALREADY names the children and statuses (`"Set 'zset' has 1 child(ren) not yet executed that THIS RUN will still act on: chi001 (queued)"`), so the remedy can build on real data rather than guessing at operator intent. Where the operator genuinely does have approved children that simply were not selected, the honest remedy is to say they can name the children explicitly, which is a selection fix and not an approval bypass.
  E-02 MUST IMPLEMENT THIS ANSWER rather than re-deciding it: no remedy string may contain `--full-auto`. If a maintainer later wants it mentioned, that is a deliberate reversal to record here, not a default to drift into.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `git diff` of the RECONSIDER branch, and paste a fixture run's resulting queue item as JSON showing BOTH the refusal record present AND `status` still `queued`. Paste the `orchestrator-deferred` event too, showing its existing fields unchanged. Paste the IMPORT LINE showing the record type comes from `render_stream`, plus a grep proving `runner_shared` neither defines nor re-exports it (F-14); a diff that defines a local record shape FAILS this item regardless of how the fields look.
  - Observed evidence: LOCATED BY SYMBOL, not by number, as the gate instructs: the branch is `if decision.outcome == ORCH_DISPATCH_RECONSIDER:`, which sits at `runner_shared.py:11019` in the executing worktree (the plan's `:3356-3372` review coordinate had drifted again, by a further ~7,660 lines, so the gate's warning was correct and worth obeying).

    THE DIFF OF THE RECONSIDER BRANCH (`git diff agent_workflows/runner_shared.py`, the RECONSIDER hunk):

    ```diff
    +        reason_text, remedy = orchestrator_refusal_text(decision.reason)
    +        record_refusal(
    +            item,
    +            code=decision.reason,
    +            # The dispatch's own `detail` is appended rather than paraphrased: it NAMES the children
    +            # and their statuses (`... chi001 (queued)`), which is the run-specific fact a generic
    +            # reason cannot carry and the operator's actual next question.
    +            reason=f"{reason_text}. {decision.detail}",
    +            remedy=remedy,
    +        )
             append_jsonl(
                 run_dir / "events.jsonl",
    ```

    plus the clear at the top of the function, which D-1 added (see `decisions-and-questions.md`):

    ```diff
         id6 = str(item.get("id6") or "")
    +    # See the docstring: a refusal from a PREVIOUS dispatch of this same item must not survive into
    +    # this one's outcome. Cleared once, here, rather than per branch, so a future fourth outcome
    +    # cannot forget it.
    +    item.pop(REFUSAL_KEY, None)
         decision = decide_orchestrator_dispatch(
    ```

    THE RESULTING QUEUE ITEM, from driving the REAL `dispatch_orchestrator_item` on a two-plan temp repo (`python3 .aw/state/scratch-zyw4n3/repro.py`). BOTH facts the item demands are present: the record, AND `status` still `queued`:

    ```
    outcome= reconsider reason= children-unfinished
    item keys= ['action', 'attempts', 'dependencies', 'id6', 'kind', 'position', 'refusal', 'setid', 'status']
    status= queued
    refusal= {
      "code": "children-unfinished",
      "reason": "this orchestrator was DEFERRED, not run: its Set still has children this run has not finished, and an orchestrator is retired only once every child is `executed`. Set 'zset' has 1 child(ren) not yet executed that THIS RUN will still act on: chi001 (queued). Left RECONSIDERABLE (no status written), so this orchestrator is re-tested on a later iteration once they complete",
      "remedy": "let the run reach those children: they are named in the reason above with their current status, and each must become `executed`. A child still awaiting human approval is the usual cause - approve it with `aw ipd set approved <id6> --by-human --message ...` and run the Set again. Nothing is wrong with this orchestrator and no plan file needs editing"
    }
    ```

    Compare the SAME dump before the change (`git stash push -- agent_workflows/runner_shared.py`), which is this plan's F-6 reproduced in the executing worktree: `item keys= ['action', 'attempts', 'dependencies', 'id6', 'kind', 'position', 'setid', 'status']` and `refusal= null`.

    THE `orchestrator-deferred` EVENT, fields unchanged and asserted rather than eyeballed, by `DeferralRecordTests::test_the_orchestrator_deferred_event_keeps_its_existing_shape`: `reason == children-unfinished`, `terminated is False`, `unfinished_children == [["chi001", "queued"]]`, and NO `status`/`unauthored_rows` keys (which the TERMINATE event carries and this one must not). That test passes.

    THE IMPORT LINE, showing both names come FROM `render_stream` and nothing is defined locally:

    ```
    agent_workflows/runner_shared.py:166:from agent_workflows.render_stream import (
    agent_workflows/runner_shared.py:175:    REFUSAL_KEY,
    agent_workflows/runner_shared.py:178:    record_refusal,
    ```

    AND THE PROOF IT IS NEITHER DEFINED NOR RE-EXPORTED (F-14). `grep -n 'class Refusal\|Refusal as ' agent_workflows/runner_shared.py` returns NOTHING (the only `Refusal` substring in the file is the unrelated word "Refusals" in a docstring at `:9015`), and measured at runtime:

    ```
    Refusal in vars(runner_shared): False
    REFUSAL_KEY is the same object: True
    ```

    The same property is pinned by a test rather than left to this paste: `test_the_record_type_is_the_one_imported_from_render_stream` asserts `type(refusal) is render_stream.Refusal`, `rs.REFUSAL_KEY is rstream.REFUSAL_KEY`, and `'Refusal' not in vars(runner_shared)`. `render_stream.py` was NOT edited (`git status` shows one modified source file only).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a table of all SEVEN `ORCH_REASON_*` values with the human reason and remedy each produces, generated by CALLING the mapping rather than transcribed by hand. Every remedy must name a concrete action; a generic fallback string for any reason fails this item. ALSO paste the evidence for F-13: the `RETIRE_REFUSED_*` value set beside the `ORCH_REASON_*` one, showing the three shared values and the `unfinished-children`/`children-unfinished` near-miss pair, plus the assertion that `decide_orchestrator_dispatch` translates every `RETIRE_REFUSED_*` branch so no untranslated value can reach the mapping. Paste the behavior for an UNKNOWN code, showing it is handled as E-02 decided and never yields an empty remedy.
  - Observed evidence: ALL SEVEN, GENERATED BY CALLING `orchestrator_refusal_text(code)` in a loop (not transcribed). Reasons truncated to 100 chars here for width; the remedies are quoted IN FULL because "it names a concrete action" is the claim being evidenced and a truncated remedy cannot support it.

    ```
    [children-unfinished]
      reason: this orchestrator was DEFERRED, not run: its Set still has children this run has not finished, and a...
      remedy: let the run reach those children: they are named in the reason above with their current status, and each must become `executed`. A child still awaiting human approval is the usual cause - approve it with `aw ipd set approved <id6> --by-human --message ...` and run the Set again. Nothing is wrong with this orchestrator and no plan file needs editing
    [children-terminally-failed]
      reason: this orchestrator can NEVER be retired by this run: a child is in a terminal state that is not succe...
      remedy: look at the child's status named in the reason above. `reviewed` means it is frozen awaiting human approval and was never dispatched: approve it with `aw ipd set approved <id6> --by-human --message ...` and run the Set again. Any other non-success status means it ran and did not finish: read that child's own outcome record, fix what it reports, then re-run it. Either way do NOT remove the child's row from the orchestrator's table to clear this, which would retire the parent over work that never completed
    [children-not-in-this-run]
      reason: this orchestrator has unfinished children THIS RUN WILL NOT ACT ON: they are absent from its queue, ...
      remedy: run the missing children: name them explicitly in the selector, or select the whole Set so the run includes them. The orchestrator is then retired automatically once they are all `executed`, with no further action and no agent turn
    [no-children]
      reason: this Set has NO child plans on disk, and retirement is gated on every child being `executed`, so the...
      remedy: author the Set's child plans with `aw ipd scaffold` and add a row for each to the orchestrator's `## Child IPDs` table, then run the Set. If the parent was never meant to orchestrate anything, its `- Kind:` is what is wrong, not its children
    [unauthored-child-rows]
      reason: this orchestrator's own `## Child IPDs` table declares a row that resolves to no plan on disk, so th...
      remedy: AUTHOR THE MISSING CHILD named in the reason above (`aw ipd scaffold` derives its name) and leave the parent's table and checklist in place. Removing the row instead would silence this refusal by deleting the record of work the Set declared, which is the lost work this check exists to prevent
    [finalize-refused]
      reason: this orchestrator's children are done but the RETIREMENT TRANSITION ITSELF refused, so the plan was ...
      remedy: read the transition's refusal named above: it states which condition failed. Resolve that condition, then retire the orchestrator through `aw ipd finalize`. Never complete the move with a raw `git mv` plus a hand-edited `- Status:`, which is precisely what the refusing gate exists to catch
    [no-orchestrator]
      reason: this item claims to BE its Set's orchestrator, but the Set does not resolve to one on disk, so the s...
      remedy: check the Set id and the orchestrator plan's own `- Set:` and `- Order:` fields: an orchestrator is `Order: 00` with `- Kind: orchestrator`. `aw find plans` locates what the Set actually resolves to, and `aw index plans --check` reports a name that disagrees with its front matter
    ```

    NO REASON FALLS THROUGH TO A GENERIC STRING, asserted rather than eyeballed: `ReasonMappingTests::test_every_reason_is_mapped_and_distinct` fails any code whose reason contains the fallback's `NOT RECOGNIZE` marker, and additionally requires all 7 reasons and all 7 remedies to be pairwise DISTINCT (a single shared string would pass a "non-empty" check while being exactly the generic prose this item forbids). `test_every_remedy_names_a_concrete_action` requires an action verb in each.

    F-13, THE TWO VOCABULARIES, printed and differenced:

    ```
    RETIRE_REFUSED_* (4): ['no-children', 'no-orchestrator', 'unauthored-child-rows', 'unfinished-children']
    ORCH_REASON_*    (7): ['children-not-in-this-run', 'children-terminally-failed', 'children-unfinished', 'finalize-refused', 'no-children', 'no-orchestrator', 'unauthored-child-rows']
    shared verbatim (3): ['no-children', 'no-orchestrator', 'unauthored-child-rows']
    near-miss pair: unfinished-children VS children-unfinished
    the unshared RETIRE value is UNMAPPED (proving the key set): True
    ```

    THE TRANSLATION IS ASSERTED, NOT ASSUMED, in two independent ways, because this is the finding most likely to rot. FIRST, positively: the last line above shows `RETIRE_REFUSED_UNFINISHED_CHILDREN` (`unfinished-children`) is NOT a key of the mapping, which is what proves the mapping is keyed on `ORCH_REASON_*` alone rather than on the union. SECOND, structurally: `test_the_translation_is_asserted_on_the_real_decider` reads `decide_orchestrator_dispatch`'s source and fails if any branch ever writes `reason=RETIRE_REFUSED...`, so a future branch forwarding an untranslated value breaks the test instead of silently degrading to the fallback. Both pass.

    THE UNKNOWN CODE, handled as D-2 decided (report, never raise; see `decisions-and-questions.md` for why a raise here would be RUN-FATAL):

    ```
    [UNKNOWN 'some-future-reason']
      reason: this orchestrator was refused for reason 'some-future-reason', which THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE, so no specific diagnosis can be given for it
      remedy: read this run's `orchestrator-deferred` event in `events.jsonl`: it carries the same reason code ('some-future-reason') plus the unfinished children, which is the full fact the dispatch had. Then report the unmapped code, since a reason the dispatch produces and the reporting cannot explain means the two drifted apart and `_ORCH_REASON_TEXT` needs the new value
    ```

    The code appears VERBATIM in both halves, the remedy is non-empty and actionable, and `Refusal(code=..., reason=..., remedy=...)` constructs from it (so an unmapped code still renders rather than raising). An EMPTY reason is covered separately by `test_an_empty_reason_is_still_handled`. Both pass.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a TERMINATE-path fixture run's queue item showing the shared record present AND `orchestrator_refusal_reason`/`orchestrator_refusal_detail` still present, AND `unsatisfied_dependencies`/`unsatisfied_dependency_reasons` unchanged. Paste `python3 -m pytest tests/test_orchestrator_retirement.py` GREEN, since it reads those two bespoke fields (F-15) and is the test most likely to catch a non-additive change; it must be green before AND after, and any failure there is yours. Paste the `## Dependency blocks (why)` section from the resulting report proving it still renders, and state that you checked BOTH hosts' copies exist (F-16).
  - Observed evidence: THE TERMINATE-PATH ITEM, from driving the real dispatch on a temp repo whose child is unfinished on disk and absent from the queue (`.aw/state/scratch-zyw4n3/depblocks.py`). All FOUR pre-existing keys survive beside the new record:

    ```
    outcome: terminate | reason: children-not-in-this-run
    unsatisfied_dependencies: ['executed:chi002']
    unsatisfied_dependency_reasons: {'executed:chi002': 'child chi002 is approved'}
    orchestrator_refusal_reason: children-not-in-this-run
    orchestrator_refusal_detail: Set 'zset' has 1 child(ren) not yet executed that this run will NOT ac ...
    ```

    and the shared record is present on the same item (asserted by `TerminateRecordTests::test_a_terminated_orchestrator_carries_the_same_record`, which also checks `type(refusal) is render_stream.Refusal` and `status == "dependency-blocked"`). `test_both_outcomes_use_one_record_shape` asserts the RECONSIDER and TERMINATE records are the same type with the same field set, which is the "two halves stop reporting differently" claim.

    `tests/test_orchestrator_retirement.py` GREEN, and measured BEFORE as well as after, per the gate:

    ```
    # BEFORE (baseline, at HEAD c6596383, before any edit):
    101 passed in 4.46s
    # AFTER:
    $ python3 -m pytest tests/test_orchestrator_retirement.py
    101 passed in 4.42s
    ```

    NOTE THE COUNT: the plan's gate says this module is "112 PASSED" (measured at review, 2026-09-09). It is 101 in the executing worktree, BEFORE any change of mine, so the module shrank by 11 tests in the intervening two weeks. The gate's REQUIREMENT is what matters and is met: green before, green after, no failure attributable to me. Its specific NUMBER was stale, exactly as the same gate warns about its own line numbers and totals.

    THE `## Dependency blocks (why)` SECTION STILL RENDERS, from the real `write_report` on the TERMINATE state above:

    ```
    ## Dependency blocks (why)

    - `orc002` (position 1):
      - `executed:chi002`: child chi002 is approved
    ```

    ON F-16's "BOTH HOSTS", A CORRECTION WORTH RECORDING. The plan says this section exists at `oc_runipd.py:3222` AND `agy_runipd.py:2152` and that a claim about it must check both. I checked both, and `grep -rn 'Dependency blocks' agent_workflows/*.py` now returns exactly TWO hits, BOTH in `runner_shared.py`: the renderer at `:15562` and my own new comment at `:11066`. There is no longer a copy per host: `write_report` has since been unified into the shared module, so ONE implementation now serves both hosts by construction and the divergence F-16 warned about cannot occur. The section remains gated on `status == "dependency-blocked"`, which is `terminal_status`'s default and therefore what a TERMINATE writes, so F-16's substantive point (it is not a general fallback) still holds and is recorded in the code comment.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new tests' names and the passing result, the RECONSIDER case's FAILING output produced by reverting your own change IN THIS WORKTREE (not a claim about a historical HEAD), and proof the tests are fixture-based (paste the fixture setup) plus a run from a clean temp dir with no `.aw/records/runs/`. Paste the identity assertion showing the record is the type imported from `render_stream`. Paste the unknown-code case too.
  - Observed evidence: THE 26 NEW TESTS AND THEIR RESULT (`python3 -m pytest tests/test_orchestrator_deferral_reporting.py`):

    ```
    ..........................                                               [100%]
    26 passed in 0.76s
    ```

    ```
    DeferralRecordTests::test_a_deferred_orchestrator_carries_a_refusal_record
    DeferralRecordTests::test_the_record_names_the_blocking_children_from_the_dispatch_detail
    DeferralRecordTests::test_the_deferral_still_writes_no_status_so_it_is_re_selected
    DeferralRecordTests::test_the_orchestrator_deferred_event_keeps_its_existing_shape
    DeferralRecordTests::test_the_record_type_is_the_one_imported_from_render_stream
    TerminateRecordTests::test_a_terminated_orchestrator_carries_the_same_record
    TerminateRecordTests::test_the_bespoke_fields_a_live_test_reads_are_unchanged
    TerminateRecordTests::test_the_dependency_fields_the_report_section_reads_are_unchanged
    TerminateRecordTests::test_both_outcomes_use_one_record_shape
    ReasonMappingTests::test_every_reason_is_mapped_and_distinct
    ReasonMappingTests::test_every_remedy_names_a_concrete_action
    ReasonMappingTests::test_no_remedy_suggests_full_auto
    ReasonMappingTests::test_no_remedy_names_a_host_command
    ReasonMappingTests::test_no_remedy_tells_the_reader_to_delete_the_thing_that_refused
    ReasonMappingTests::test_the_dead_children_remedy_covers_the_awaiting_approval_case
    ReasonMappingTests::test_an_unknown_code_is_reported_verbatim_and_never_empty
    ReasonMappingTests::test_an_empty_reason_is_still_handled
    ReasonMappingTests::test_the_mapping_is_keyed_on_ORCH_REASON_and_the_other_vocabulary_is_translated
    ReasonMappingTests::test_the_translation_is_asserted_on_the_real_decider
    StaleDeferralRecordTests::test_a_deferral_that_later_retires_leaves_no_refusal_behind
    StaleDeferralRecordTests::test_the_summary_reports_a_completed_set_as_completed
    StaleDeferralRecordTests::test_a_re_dispatch_replaces_rather_than_accumulates
    RenderedSurfaceTests::test_the_summary_diagnostics_block_shows_the_reason_and_the_remedy
    RenderedSurfaceTests::test_a_deferral_is_not_reported_as_a_failure
    RenderedSurfaceTests::test_the_end_of_run_disposition_summary_sources_the_remedy
    RenderedSurfaceTests::test_aw_runs_counts_a_deferred_orchestrator_as_an_issue
    ```

    THE RECONSIDER CASE FAILS BEFORE THE CHANGE, REPRODUCED IN THIS WORKTREE (not a claim about a historical HEAD). `git stash push -- agent_workflows/runner_shared.py`, then run the two-test slice:

    ```
    $ python3 -m pytest 'tests/...::DeferralRecordTests::test_a_deferred_orchestrator_carries_a_refusal_record' \
                        'tests/...::StaleDeferralRecordTests::test_the_summary_reports_a_completed_set_as_completed' -o addopts=""
    tests/test_orchestrator_deferral_reporting.py .F                          [100%]
    E       AssertionError: unexpectedly None : a DEFERRED orchestrator must carry a refusal record;
            without it the reason reaches only events.jsonl, which no read surface consumes (this is the defect)
    ========================= 1 failed, 1 passed in 0.56s ==========================
    ```

    The whole module before the change was `19 failed, 6 passed`; after `git stash pop`, `26 passed`. NOTE WHICH ONE PASSED BEFORE, because it is the honest reading: `test_the_summary_reports_a_completed_set_as_completed` passes without my change, since with no record written there is no stale record to leave behind. It is a REGRESSION GUARD on D-1's clear, not a proof of the feature, and it FAILS if the record is written without the clear (measured while developing: `Outcome: PARTIAL`).

    FIXTURE-BASED, NEVER AGAINST `.aw/records/runs/`. The fixture is a temp repo plus a hand-built queue:

    ```python
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.run_dir = self.root / "run-deferral"
        self.run_dir.mkdir(parents=True, exist_ok=True)
    ```

    and the run directory is that temp path, so nothing reads or writes the repository's gitignored run tree. PROVEN by running the module with a `--rootdir` pointing at a freshly created empty directory that contains no `.aw` at all:

    ```
    clean dir: .aw/state/scratch-zyw4n3/cleanrun.1EBa
    --- does it have .aw/records/runs? ---
    ls: cannot access '.../cleanrun.1EBa/.aw': No such file or directory
    26 passed in 0.69s
    ```

    THE IDENTITY ASSERTION (the case this plan's gate added, without which the divergence `r2i1b1` E-01 prevents could be reintroduced and every other test would still pass):

    ```python
    refusal = rstream.refusal_of_item(orch)
    self.assertIs(type(refusal), rstream.Refusal)
    self.assertIs(rs.REFUSAL_KEY, rstream.REFUSAL_KEY)
    self.assertNotIn("Refusal", vars(rs), "...that would create the circular import ...")
    ```

    THE UNKNOWN-CODE CASE is `test_an_unknown_code_is_reported_verbatim_and_never_empty` (verbatim code in both halves, non-empty remedy, constructs a real `Refusal` rather than raising) plus `test_an_empty_reason_is_still_handled`. Both pass; their output is quoted under V-02.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: state whether `r2i1b1` has landed, pasting its `- Status:` and directory (it was `approved` in `pending/` at review, so unmet). Then paste the BEFORE and AFTER of the item's own invocation on a `reviewed` orchestrator with unapproved children: the run summary and `aw runs` output, showing the deferral reason and remedy present after and absent before. STATE WHICH RUN SHAPE you reproduced and what the `Outcome:` header actually read, since an orchestrator-only queue reads `QUEUED` rather than the `COMPLETED` this plan's F-5 quotes (F-17); name the line that changed rather than implying the header flipped. Confirm in the pasted output that the item is reported as DEFERRED, not as failed. Paste the bare `python3 -m pytest` summary line and compare FAILING NODE IDS against your own measured baseline, not against this plan's stale totals.
  - Observed evidence: `r2i1b1` HAS LANDED, so the dependency edge is MET (it was `approved` in `pending/` at review, hence unmet then):

    ```
    $ ls -d .aw/records/plans/executed/*r2i1b1* && grep -m1 '^- Status:' .aw/records/plans/executed/*r2i1b1*
    .aw/records/plans/executed/20260907-orchprobe-01-r2i1b1-surface-a-per-item-refusal-reason-and-its-remedy-in-the-run.ipd.md
    (its status line reads the terminal value `executed`; quoted as prose rather than pasted verbatim,
     because a literal status bullet inside this plan is read by the executed-transition pre-commit gate
     as THIS plan claiming that status - measured: it refused the evidence commit until reworded)
    ```

    Its machinery is what this plan writes into and is confirmed present: `render_stream.Refusal`, `REFUSAL_KEY`, `record_refusal`, `refusal_of_item`, the diagnostics block with NO status allowlist, and `run_viewer.step_issue_reasons`' refusal term.

    WHICH RUN SHAPE I REPRODUCED, stated first because the gate requires it and because the plan's own F-5 describes a different one. TWO shapes were run, on synthetic repos through the real `aw oc run` (never this repository, so no run directory or lifecycle change is left in the validated worktree):

    SHAPE A, THE ITEM'S OWN SCENARIO (an `approved` orchestrator over a `reviewed`, i.e. unapproved, child). The `Outcome:` header reads `BLOCKED` both before and after, NOT `COMPLETED` and not `QUEUED`: F-5's `COMPLETED` and F-17's `QUEUED` are both wrong for this shape today, because the orchestrator terminates to `dependency-blocked` and the header's `BLOCKED` branch fires. MEASURED, THE DISPATCH OUTCOME FOR THIS SHAPE IS TERMINATE, NOT RECONSIDER, with reason `children-terminally-failed`: `reviewed` is in `TERMINAL_STATES` (printed to confirm), so an unapproved child is "terminal and not success" rather than "unfinished". So the item's own scenario exercises E-03's path, not E-01's, and both had to be implemented for the item's complaint to be answered. THE LINE THAT CHANGED is the `Diagnostics / Blocked Items:` entry (plus the per-artifact disposition and the `Issue` column), NOT the header:

    ```
    # BEFORE (my runner_shared.py change stashed):
    Diagnostics / Blocked Items:
      • orc900: dependency-blocked (executed:chi900 (child chi900 is reviewed))
    - 01 orc900 [e2eset] orchestrate -> dependency-blocked: dependency_not_met (a declared dependency
      was not satisfied in this run; unmet: executed:chi900 (child chi900 is reviewed))

    # AFTER:
    Diagnostics / Blocked Items:
      • orc900: dependency-blocked (this orchestrator can NEVER be retired by this run: a child is in a
        terminal state that is not success ... The usual cause is a child that was never dispatched
        because it is not approved, NOT a child that crashed. Set 'e2eset' can never complete in this
        run: child(ren) chi900 (reviewed) reached a non-success terminal state ...)
        → remedy: look at the child's status named in the reason above. `reviewed` means it is frozen
          awaiting human approval and was never dispatched: approve it with `aw ipd set approved <id6>
          --by-human --message ...` and run the Set again. ... Either way do NOT remove the child's row
          from the orchestrator's table to clear this, which would retire the parent over work that
          never completed
    ```

    `aw runs` FOR THE SAME TWO RUNS. The `Issue` column flips, which is the machine-visible half:

    ```
    # BEFORE:
    │ dependency-blocked │ 20260908-e2eset-00-orc900 │ orchestrate │ ... │ no    │
    # AFTER:
    │ dependency-blocked │ 20260908-e2eset-00-orc900 │ orchestrate │ ... │ YES   │

    Details for 20260908-e2eset-00-orc900:
      ! refused [children-terminally-failed]: this orchestrator can NEVER be retired by this run ...
        → remedy: look at the child's status named in the reason above ...

    Refusals (what the run declined, and what to do):
      ! 20260908-e2eset-00-orc900 [children-terminally-failed]: ... → remedy: ...
    ```

    And `aw runs --agent --issues`, which is the surface a tooling consumer reads, went from EMPTY OUTPUT (before) to a full record (after), carrying `"issue_reasons":["refused: ..."]` and `"refusal":{"code":"children-terminally-failed","reason":"...","remedy":"..."}`. Before the change the same command printed nothing at all, so `aw oc run` reported a no-op run as clean to tooling.

    SHAPE B, THE TRUE DEFERRAL (RECONSIDER), which E-01 owns and which shape A does not reach. An approved orchestrator over an approved child that has not run:

    ```
    dispatch outcome: reconsider | reason: children-unfinished
    orchestrator status AFTER the deferral: queued (must still be 'queued')

    | Outcome: QUEUED   Duration: 0s   Spend: $0.00 ...
    |  01 |  01 | orc910 | dfset | orchestrate | queued | -      | ...

    Diagnostics / Blocked Items:
      • orc910: queued (this orchestrator was DEFERRED, not run: its Set still has children this run has
        not finished ... chi910 (queued). Left RECONSIDERABLE (no status written) ...)
        → remedy: let the run reach those children ... approve it with `aw ipd set approved <id6>
          --by-human --message ...` and run the Set again. Nothing is wrong with this orchestrator and
          no plan file needs editing
    ```

    THIS IS EXACTLY F-17'S POINT, NOW RESOLVED: the item is `queued`, which matched NONE of the old five-status allowlist, so before `r2i1b1` landed this rendered no diagnostics line whatever fields it carried. With `r2i1b1` executed the allowlist is gone and the record renders for ANY status, which is why the dependency was load-bearing.

    REPORTED AS DEFERRED, NOT AS FAILED, confirmed in the pasted output and pinned by `test_a_deferral_is_not_reported_as_a_failure`: the header reads `QUEUED` (not `FAILED`, not `STRANDED`), the status column reads `queued`, and the word the diagnostics line uses is `DEFERRED`.

    THE BARE SUITE, with the baseline measured in THIS worktree rather than taken from this plan:

    ```
    # BASELINE, at HEAD c6596383 before any edit:
    1 failed, 8194 passed, 3 skipped, 2 xfailed, 3 warnings in 154.50s (0:02:34)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped

    # AFTER this plan's changes:
    1 failed, 8220 passed, 3 skipped, 2 xfailed, 3 warnings in 217.50s (0:03:37)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    FAILING NODE IDS COMPARED, NOT TOTALS: the set is IDENTICAL, one node id, the same one, before and after. Passing count rose 8194 -> 8220, i.e. +26, exactly the size of the new module. The one failure is ENVIRONMENTAL and belongs to the lane I am running in, not to this change: it asserts that a non-isolated turn gets NO `OPENCODE_CONFIG_CONTENT` denial policy, and my own agent turn exports that variable, so the test sees it inherited. CONTROL RUN proving that: `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` gives `76 passed`. Note this is a DIFFERENT failure from the one the plan's gate names (`test_reporting_contract.py`'s prose test), which passes here; that is the gate's own advice about measuring your own baseline, vindicated twice.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan has been reviewed and must not be executed until a human sets it `approved` with `aw ipd set approved zyw4n3 --by-human --message ...`. A reviewer should note that this plan graduates only a NARROW RESIDUAL of backlog item `i2fjf8`: defect 1 is dead (F-1 through F-4) and defect 2's record and rendering are owned by `r2i1b1` (F-10), leaving only the deferral's failure to populate that record (F-6 through F-9).

It carries `Item-Dependencies: executed:r2i1b1` deliberately: without that plan the record this one writes is invisible, so executing this first would produce no observable improvement and E-05 could not pass. THAT IS NOW PROVEN RATHER THAN ARGUED (F-17): the summary's diagnostics block allowlists five statuses and a deferred orchestrator is `queued`, so rendering the real summary on such an item produces no diagnostics line at all. Measured at review, `r2i1b1` is `approved` and still in `pending/`, so the edge is UNMET and the runner will correctly refuse to dispatch this plan until it executes.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run, and compare FAILING NODE IDS against your own measured baseline rather than this plan's stale totals (F-18). Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE CONTENTION, AND THAT EVERY LINE NUMBER IN THIS PLAN IS ALREADY WRONG. `runner_shared.py` is declared by `r2i1b1`, `m7gvuz` and other in-flight plans, and measured at review this plan's OWN citations had drifted by roughly 340 lines in a single day (`ORCH_REASON_*` `:2692-2703` -> `:3031-3042`; the RECONSIDER branch `:3017-3033` -> `:3356-3372`; the bespoke fields `:3047-3048` -> `:3387-3388`). So re-locate by SYMBOL or by the anchor comments, never by number: find `ORCH_DISPATCH_RECONSIDER`, `dispatch_orchestrator_item`, `decide_orchestrator_dispatch`, the `ORCH_REASON_*` and `RETIRE_REFUSED_*` blocks, and `# Failure / Dependency block diagnostics` by name.

DO NOT EDIT `render_stream.py` (F-14). The refusal record lives there by `r2i1b1`'s deliberate design, for a circular-import reason; IMPORT it, and if the work seems to require defining or re-exporting it in `runner_shared`, stop and report rather than moving it. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
