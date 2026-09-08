# IPD: Emit a refusal record when an orchestrator is deferred so a no-op run says why nothing ran

- Date: 2026-09-08
- Kind: child
- Concern: A run that does no work reports success and never says why. Naming an orchestrator whose children are not `approved` produces a run whose summary reads `Outcome: COMPLETED`, `Progress: 1/1 100% (1 reviewed)` and a table row with an empty `Verify` column, with no line anywhere stating that the orchestrator was DEFERRED, why, or what to do about it. The runner already computes the answer: `dispatch_orchestrator_item` picks a typed `ORCH_REASON_*` value for every refusal. But on the RECONSIDER path (the deferral) that reason is written ONLY to `events.jsonl`, and on the TERMINATE path it is written onto the item as `orchestrator_refusal_reason`, which no read surface consumes. So a precise, machine-readable diagnosis is produced and then discarded, and the operator is left to infer from a green summary that nothing happened.
- Scope: Close the last mile only. Write the refusal record on the RECONSIDER (deferred) path too, so the deferral reason and a remedy reach the queue item rather than only the event log, and make the existing typed reasons render. Reuses the refusal record and both render surfaces that reviewed plan `r2i1b1` builds; adds NO new refusal decision and changes NO gate's verdict.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_deferral_reporting.py
- Item-Dependencies: executed:r2i1b1
- Status: to-review
- Set: runghostid
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zyw4n3
- From-Backlog: i2fjf8
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `i2fjf8`, inheriting its `Blocks-Release: next` gate. THIS IS A HEAVY NARROWING: the item names TWO coupled defects and DEFECT 1 IS DEAD. Defect 1 was that the runner printed a Run ID, a State directory and a `resume` hint for a run it never persisted. I re-ran the item's own scenario at HEAD `8b4e1570` (`aw oc run 20260908-runanalytics-00-5lxvl3 --prepare-only`, a `reviewed` orchestrator whose children are `to-review`) and the announced directory EXISTS on disk with `state.json`, `events.jsonl`, `manifest.json`, `outcomes/`, `prompts/`, `sessions/`, and `aw runs <id>` renders it. TWO INDEPENDENT REASONS IT CANNOT RECUR, both verified in code: (a) `Run ID:` and `State directory:` are printed only AFTER `initialize_run` returns (`oc_runipd.py:8018-8020`), and `initialize_run` mkdirs the run directory at `:2927` before returning at `:3126`; (b) the empty-queue paths RAISE before that mkdir (`:2842-2860`, `EmptyStatusSelection` for a status selector and `DriverError` for `all`), with an inline comment stating the intent verbatim: "Freezing an empty queue instead would create a run directory, a report, and a ledger for zero work, which is durable state an operator then has to reconcile." That landed in `287874dd` (2026-09-05, "one shared needly-review predicate and the draft admission gate"), a week after the item was filed. I also confirmed the specific RESUME-hint symptom cannot appear for an empty queue even hypothetically: `render_continuation_hint` chooses the resume line only when NOT `all_success`, and `all(...)` over an empty queue is vacuously True, so an empty queue would take the INSPECT branch. Defect 1 is therefore not graduated. DEFECT 2 SURVIVES BUT IS MOSTLY COVERED, and I graduated only the residual. Reviewed plan `r2i1b1` (Set `orchprobe`, Order 01) builds the entire mechanism defect 2 needs: E-01 defines ONE shared refusal record (reason CODE, human REASON, REMEDY) stored on the queue item, E-02 makes the summary's diagnostics block render it for ANY status instead of the hardcoded allowlist, E-03/E-04 route `aw runs`' Issue predicate through one function and count a refusal as an issue across `--json`/`--agent`/`--issues`, and E-05 makes reason and remedy visible WITHOUT `--detail`. Its scope line explicitly excludes "adding any new refusal (child 03 does that)". So `r2i1b1` supplies the plumbing and the rendering; what remains is that the ORCHESTRATOR DEFERRAL never populates it. MEASURED THE RESIDUAL EXACTLY, which is what this plan is: I ran the item's scenario and dumped `state.json`, and the queue item's keys are `action, attempts, configured_file, dependencies, from_backlog, id6, initial_status, kind, order, position, setid, status` - NO refusal field, NO reason, NO remedy. Reading `dispatch_orchestrator_item` shows why: on TERMINATE it writes `item["orchestrator_refusal_reason"]` and `item["orchestrator_refusal_detail"]` (`runner_shared.py:3047-3048`), but on RECONSIDER it deliberately writes NO status and sends the reason only to `events.jsonl` (`:3017-3033`), and grepping `render_stream.py`/`run_viewer.py` for `orchestrator-deferred` and for `orchestrator_refusal_reason` returns NOTHING, so neither the event nor the item field reaches any read surface today.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a run that did nothing say so. The runner already knows the reason precisely; this plan puts it where the two read surfaces `r2i1b1` builds will display it, so an operator stops having to infer "nothing ran" from a green `COMPLETED` summary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: populate the refusal record on the deferral path

- [ ] E-01 Write `r2i1b1`'s refusal record on the RECONSIDER path in `dispatch_orchestrator_item` (`agent_workflows/runner_shared.py`, the RECONSIDER branch at `:3017-3033`), where today only an `orchestrator-deferred` event is appended and NO item field is written. Use `r2i1b1`'s shared constructor rather than inventing a second record shape; if it has not landed, STOP and report rather than forking one, because two refusal-record shapes on the same queue item is the exact divergence its E-01 exists to prevent. RESPECT THE ONE INVARIANT THIS PATH GUARDS: the RECONSIDER branch must still write NO `status`, because the item has to stay `queued` so a later iteration re-selects it when its children finish; the surrounding comment records that writing a terminal `dependency-blocked` here excluded such an orchestrator forever. Adding a refusal record is additive and must not disturb that.
  - Depends on: none
  - Expected outcome: after a deferred-orchestrator run, the queue item carries a refusal record naming the deferral, and its `status` is still `queued`.
  - Execution state: pending

- [ ] E-02 Map each existing `ORCH_REASON_*` value to a human REASON and an actionable REMEDY, reusing the typed vocabulary already defined rather than writing new prose per site. The constants are `ORCH_REASON_UNFINISHED_CHILDREN` (`:2692`), `ORCH_REASON_DEAD_CHILDREN` (`:2693`), `ORCH_REASON_CHILDREN_NOT_IN_RUN` (`:2699`), `ORCH_REASON_NO_CHILDREN` (`:2700`), `ORCH_REASON_UNAUTHORED_CHILD_ROWS` (`:2701`), `ORCH_REASON_FINALIZE_REFUSED` (`:2702`) and `ORCH_REASON_NO_ORCHESTRATOR` (`:2703`). THE REMEDY IS THE HALF THAT MATTERS and is what the item actually asked for: it wanted the run to say something like "children not executed; did you mean to include the children or pass --full-auto?" rather than a bare status. Each remedy must name a concrete next action. Follow `m7gvuz` E-06's discipline on wording: phrase the remedy as the CONSTRUCTIVE action, never as an instruction to delete or weaken the thing that refused.
  - Depends on: E-01
  - Expected outcome: every one of the seven reasons yields a specific human reason and a remedy naming an action; no reason falls through to a generic string.
  - Execution state: pending

- [ ] E-03 Make the TERMINATE path use the SAME record, so the two halves of one function stop reporting differently. Today TERMINATE writes bespoke fields `item["orchestrator_refusal_reason"]` and `item["orchestrator_refusal_detail"]` (`:3047-3048`) that grep shows NO surface reads. Populate `r2i1b1`'s record there too. KEEP THE EXISTING FIELDS as well rather than renaming them, at least initially: they are additive by design (their comment says so) and a consumer outside this grep may exist, so removing them is a separate, provable change. Also preserve `unsatisfied_dependencies` and `unsatisfied_dependency_reasons` (`:3038-3046`) exactly, since `write_report`'s `## Dependency blocks (why)` section reads them (`oc_runipd.py:3208-3222`) and is the one place a deferral reason surfaces today.
  - Depends on: E-02
  - Expected outcome: both dispatch outcomes populate the shared record; the existing bespoke fields and both dependency fields are unchanged; the existing dependency-blocks report section still renders.
  - Execution state: pending

### Task group 2: prove it, without depending on live run state

- [ ] E-04 Test the deferral reporting with a FIXTURE, never against `.aw/records/runs/`. That tree is gitignored with zero tracked files, and `tests/test_run_viewer.py:1-30` records that 23 tests reading it fail in a fresh checkout, so a test keyed to live runs would be unrunnable in CI and in every lane worktree the runner allocates. Drive `dispatch_orchestrator_item` directly with a constructed state, as the orchestrator-retirement tests already do. Cover, as separate cases: a RECONSIDER deferral populates the record AND leaves `status` unset/`queued`; a TERMINATE refusal populates the same record; each of the seven `ORCH_REASON_*` values produces a non-generic reason and remedy; and the `orchestrator-deferred` event is still appended with its existing fields. Assert the RECONSIDER case FAILS against HEAD `8b4e1570`, so the test is proven to bite.
  - Depends on: E-03
  - Expected outcome: fixture-driven tests passing in a bare worktree; the RECONSIDER case fails before the change and passes after.
  - Execution state: pending

- [ ] E-05 Verify END TO END that the reason now REACHES both surfaces, which is the only evidence that matters for the item's complaint, and confirm the no-op run no longer looks like a success. Re-run the item's exact scenario (name a `reviewed` orchestrator whose children are not `approved`) and show the summary and `aw runs` output carrying the reason and remedy. CHECK `r2i1b1` HAS LANDED FIRST: this plan declares `Item-Dependencies: executed:r2i1b1` precisely because rendering is its deliverable, not this plan's, and without it the record is written but invisible. ALSO confirm the ORDERING claim: the summary must still not misreport the item as failed, because a deferral is not a failure; the goal is an explained no-op, not a red run. If `r2i1b1` has landed and the rendering still does not show the record, report that as a finding against the rendering rather than adding a second render path here.
  - Depends on: E-04
  - Expected outcome: a pasted before/after of the same invocation showing the deferral reason and remedy in the summary and in `aw runs`, with the item still reported as deferred rather than failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The runner ALREADY computes a precise typed reason for every orchestrator refusal: seven `ORCH_REASON_*` constants (`runner_shared.py:2692-2703`) and a three-way outcome contract (RETIRE / RECONSIDER / TERMINATE). This plan is about delivery, not diagnosis.
- The three outcomes exist because a single write was measurably wrong twice: a terminal `dependency-blocked` excluded an orchestrator whose children finished later in the SAME run (from an event literally named `orchestrator-deferred`), while leaving everything reconsiderable would retry a structural refusal forever and SPIN. Do not collapse them.
- THE RECONSIDER PATH DELIBERATELY WRITES NO STATUS (`:3017-3021`), and the comment explains that recording the deferral is still required because "an unlabelled item with no event would be indistinguishable from one never reached". That is exactly this plan's argument, applied one layer further out: the EVENT is not enough either, because no read surface consumes it.
- The TERMINATE path already writes `orchestrator_refusal_reason`/`orchestrator_refusal_detail` onto the item, described in its own comment as "additive, so a consumer need not parse prose". Grep shows no consumer exists yet, which is what `r2i1b1` fixes on the rendering side.
- `write_report`'s `## Dependency blocks (why)` section (`oc_runipd.py:3208-3222`) is the ONE place a deferral surfaces today, and it reads `unsatisfied_dependencies`/`unsatisfied_dependency_reasons`, which only the TERMINATE path populates. So a RECONSIDER deferral appears in no report at all.
- Reviewed plan `r2i1b1` owns the refusal record and BOTH render surfaces, and explicitly excludes adding new refusals. Reviewed plan `m7gvuz` adds a different refusal (orchestrator carrying uncovered work) and E-06 there sets the remedy-wording discipline: name the constructive action, never suggest deleting the checklist.
- New tests on the run surface must use fixtures: `.aw/records/runs/` is gitignored with zero tracked files and 23 existing tests that read it fail in a fresh checkout.

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
| F-10 | THE RENDERING IS ALREADY OWNED, so this plan must not build it: `r2i1b1` defines the shared refusal record and renders it in the summary for ANY status and in `aw runs` across all payloads, and its scope excludes adding new refusals. | `r2i1b1` `- Status: reviewed`, Scope line, E-01 through E-05 |
| F-11 | The sibling that ADDS refusals is `m7gvuz`, and it adds a DIFFERENT one (an orchestrator carrying work no child covers), not the not-all-children-executed deferral. So the deferral has no owner but this plan. | `m7gvuz` E-06 and its Scope line |
| F-12 | The seven typed reasons already exist, so E-02 is a mapping exercise rather than a diagnosis one. | `runner_shared.py:2692-2703` |

## Proposed changes (ordered, validatable)

1. Write `r2i1b1`'s refusal record on the RECONSIDER path, preserving the no-status invariant (E-01).
2. Map all seven `ORCH_REASON_*` values to a human reason and an actionable remedy (E-02).
3. Populate the same record on the TERMINATE path, keeping the existing fields intact (E-03).
4. Test with fixtures, proving the RECONSIDER case fails before the change (E-04).
5. Verify end to end that both surfaces now show the reason, with `r2i1b1` landed (E-05).

## Deferred / out of scope (with reason)

- DEFECT 1 (the ghost Run ID / State directory / resume hint). DEAD, on three independent measurements (F-1 through F-4), fixed as a side effect of `287874dd` on 2026-09-05. Re-implementing it would be work against already-shipped behavior.
- THE REFUSAL RECORD ITSELF AND BOTH RENDER SURFACES. Owned by reviewed plan `r2i1b1` (F-10), which this plan declares as an `Item-Dependencies` edge rather than duplicating. Building a second record shape or a second render path is the precise divergence its E-01 exists to prevent.
- ADDING ANY NEW REFUSAL DECISION, including the uncovered-work probe. That is `m7gvuz`, and `r2i1b1`'s scope line explicitly assigns new refusals to it.
- CHANGING WHAT THE ORCHESTRATOR DISPATCH DECIDES. The three-way contract is correct and hard-won (a terminal write stranded an orchestrator forever; a fully reconsiderable one would spin). This plan adds reporting only.
- REMOVING the bespoke `orchestrator_refusal_reason`/`orchestrator_refusal_detail` fields once the shared record exists. Tempting, but they are documented as additive and a consumer outside this repository's grep may read them; deleting them is a separate, provable change.
- THE `aw runs` / summary WORDING for a deferral being reported as an ISSUE rather than a failure. `r2i1b1` E-04 decides how a refusal appears in the Issue column; this plan supplies the record and checks in E-05 that a deferral is not misreported as a failure, but does not re-litigate that presentation.

## Scope check

- Over-scope: none. One source module and one new test module. `run_viewer.py` and `render_stream.py` are deliberately NOT in `Scope-Paths` even though E-05 reads their output, because rendering is `r2i1b1`'s deliverable.
- Under-scope: defect 1 is dropped as already fixed; the record and rendering are inherited; no new refusal is added; the dispatch contract is untouched.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_orchestrator_deferral_reporting.py tests/test_orchestrator_retirement.py` for the focused surface. NOTE that `test_orchestrator_retirement.py` carries the KNOWN baseline failure (`test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`); it is pre-existing and unrelated, so judge that module on the delta and do NOT claim to have fixed or broken it.
- The end-to-end before/after from E-05 on the item's own scenario, with output pasted.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

Spec `77tr3o` (`runner orchestrator retirement`, `- Status: approved`) governs the orchestrator dispatch contract that `dispatch_orchestrator_item` implements. This plan changes only what is RECORDED for reporting, not what the dispatch DECIDES, so no spec text is contradicted and no `.spec.md` is declared in `Scope-Paths`. Two cautions for the executor. FIRST, if the spec enumerates the fields a dispatch outcome writes, adding a refusal record IS a contract addition: declare `.aw/records/specs/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md` in `Scope-Paths` and justify it here before editing. SECOND, `m7gvuz` E-07 is already amending that same spec, so check for contention before touching it and prefer reporting to a racing edit. The `ORCH_REASON_*` constants are the in-code documentation of the reason vocabulary and their comments must stay truthful if E-02 attaches remedies to them.

## Open questions

### OQ-01: Should the remedy for the not-all-children-executed deferral mention `--full-auto`?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: DEFERRED, leaning NO, recorded because the backlog item explicitly suggested that wording ("did you mean to include the children or pass `--full-auto`?"). The honest objection is that `--full-auto` promotes `reviewed -> approved` through the auto-approve predicate, so suggesting it as the remedy for "children are not approved" is suggesting that the operator bypass review, which is the failure class the `rdattest` Set exists to prevent. SAFER REMEDY: name the children and their statuses, and say they must reach `approved` first (or that the operator can name the children explicitly if they are already approved). A reviewer who wants `--full-auto` mentioned should say so deliberately, since it is a nudge toward automated approval embedded in an error message.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` of the RECONSIDER branch, and paste a fixture run's resulting queue item as JSON showing BOTH the refusal record present AND `status` still `queued` (or absent). Paste the `orchestrator-deferred` event too, showing its existing fields unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a table of all SEVEN `ORCH_REASON_*` values with the human reason and remedy each produces, generated by calling the mapping rather than transcribed by hand. Every remedy must name a concrete action; a generic fallback string for any reason fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a TERMINATE-path fixture run's queue item showing the shared record present AND `orchestrator_refusal_reason`/`orchestrator_refusal_detail` still present, AND `unsatisfied_dependencies`/`unsatisfied_dependency_reasons` unchanged. Paste the `## Dependency blocks (why)` section from the resulting `execution-report.md` proving it still renders.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new tests' names and the passing result, the RECONSIDER case's FAILING output against pre-change code, and proof the tests are fixture-based (paste the fixture setup) plus a run with `.aw/records/runs/` absent or from a clean temp dir.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: state whether `r2i1b1` has landed (paste evidence). Then paste the BEFORE and AFTER of the item's own invocation on a `reviewed` orchestrator with unapproved children: the run summary and `aw runs` output, showing the deferral reason and remedy present after and absent before. Confirm in the pasted output that the item is reported as DEFERRED, not as failed. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. A reviewer should note that this plan graduates only a NARROW RESIDUAL of backlog item `i2fjf8`: defect 1 is dead (F-1 through F-4) and defect 2's record and rendering are owned by `r2i1b1` (F-10), leaving only the deferral's failure to populate that record (F-6 through F-9).

It carries `Item-Dependencies: executed:r2i1b1` deliberately: without that plan the record this one writes is invisible, so executing this first would produce no observable improvement and E-05 could not pass.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE CONTENTION: `runner_shared.py` is declared by `r2i1b1`, `m7gvuz` and other in-flight plans, so re-locate every citation BY SYMBOL at execution time and never by the line numbers written above. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
