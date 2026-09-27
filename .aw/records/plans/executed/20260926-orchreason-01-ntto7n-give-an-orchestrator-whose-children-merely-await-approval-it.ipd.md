# IPD: Give an orchestrator whose children merely await approval its own refusal code instead of children-terminally-failed

- Date: 2026-09-26
- Kind: child
- Concern: THE ORCHESTRATOR REFUSAL CODE SAYS A CHILD FAILED WHEN IT WAS ONLY NEVER APPROVED. `runner_shared.decide_orchestrator_dispatch` puts every child whose run status is `in terminal_states and not in success_states` into its `dead` list and returns `reason=ORCH_REASON_DEAD_CHILDREN` (`"children-terminally-failed"`). `reviewed` and `approved` are both in `runner_shared.TERMINAL_STATES` and neither is in `oc_runipd.EXECUTION_SUCCESS_STATES`, so a child that was frozen awaiting human approval and never dispatched gets the same machine code as a child that ran and failed. Measured at HEAD `61ef21d8` by calling the real function on a temp repo (orchestrator `par001` + child `kid001`): child run status `reviewed` -> `terminate children-terminally-failed`; `approved` -> `terminate children-terminally-failed`; `failed-safely` -> `terminate children-terminally-failed`; `queued` -> `reconsider children-unfinished`. The code is operator-visible: `dispatch_orchestrator_item` writes it as `Refusal.code` via `render_stream.record_refusal`, and `run_viewer` prints `! refused [<code>]: <reason>`. The human REMEDY text in `_ORCH_REASON_TEXT` already names the approval case first, so only the machine code (and the `detail` sentence "reached a non-success terminal state") misleads.
- Scope: IN: (a) a new constant `ORCH_REASON_CHILDREN_NOT_APPROVED = "children-not-approved"` beside the other `ORCH_REASON_*` values; (b) in `decide_orchestrator_dispatch`'s `if dead:` branch, return the new reason ONLY when EVERY dead child's run status is in `{"reviewed", "approved"}`, with a `detail` sentence saying the children await approval and were never dispatched; a mixed set keeps `ORCH_REASON_DEAD_CHILDREN` (a real failure is the stronger fact, and the remedy for it already mentions approval); outcome stays `ORCH_DISPATCH_TERMINATE` in both cases; (c) a new `_ORCH_REASON_TEXT` entry for the new code whose remedy names `aw ipd set approved <id6> --by-human --message ...` and does NOT name `--full-auto`; (d) narrowing the `ORCH_REASON_DEAD_CHILDREN` entry's prose to the failure case now that approval has its own code, while keeping the key so historical run records (`.aw/records/runs/*/state.json` carry `orchestrator_refusal_reason: children-terminally-failed`) still render their mapped text; (e) behavioral tests in a new test file. OUT: changing WHAT the dispatch decides (TERMINATE vs RECONSIDER) for any status; changing `TERMINAL_STATES` or either success set; rewriting historical run records; the `RETIRE_REFUSED_*` vocabulary of `evaluate_set_retirement`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_not_approved_reason.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: swk6r8
- Set: orchreason
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ntto7n

## Workflow history
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ntto7n verified (set orchreason, attempt 1).
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401..PR-405 all FIXED. Premise re-driven at HEAD 61ef21d8. Swept all 23 terminal statuses and found four other never-dispatched statuses keeping the failure code (declared as Deferred with the extension seam named); corrected F-2's false EXECUTION_SUCCESS_STATES claim; pinned the unasserted TERMINATE outcome and the no-Status overload as new test cases; re-grounded a gitignored run-record citation on the code.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog swk6r8. Authored review-ready; the misclassification was re-measured at HEAD 61ef21d8 by calling decide_orchestrator_dispatch on a temp repo for reviewed/approved/failed-safely/queued children.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the durable, operator-visible orchestrator refusal code distinguish "your child is waiting for approval" from "your child ran and failed", so an operator and any tooling keying on `refusal.code` are not told a crash happened when nothing ran.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [x] E-01 RE-MEASURE the misclassification at the executing HEAD. On a temp repo holding `.aw/records/plans/pending/20260908-finalback-00-par001-orch.ipd.md` (`- Kind: orchestrator`, `- Order: 0`) and `...-01-kid001-child.ipd.md` (`- Kind: child`, `- Order: 1`), the same fixture `tests/test_finalize_sendback.py::TheOrchestratorBarIsNotKilledWhileRetryBudgetRemains._repo_with_unfinished_child` builds, call `runner_shared.decide_orchestrator_dispatch(repo, "finalback", "par001", [{"id6": "kid001", "setid": "finalback", "status": S, "action": "execute"}], terminal_states=runner_shared.TERMINAL_STATES, success_states=oc_runipd.EXECUTION_SUCCESS_STATES)` for S in `reviewed`, `approved`, `failed-safely`, `queued`, and paste `(S, outcome, reason)`. ALSO sweep EVERY member of `runner_shared.TERMINAL_STATES` the same way and paste the table (added in review, F-7): that is what shows WHICH statuses this plan changes and which it deliberately leaves on the failure code, and it is nine lines of output. If `reviewed`/`approved` already yield a non-failure code, STOP and report that the defect is fixed.
  - Depends on: none
  - Expected outcome: `reviewed`, `approved`, `failed-safely` all -> `terminate children-terminally-failed`; `queued` -> `reconsider children-unfinished`. From the full sweep, measured in review at HEAD `61ef21d8`: `executed` -> `terminate children-not-in-this-run` (it is a terminal SUCCESS, so it is stranded, not dead), and every other terminal status -> `terminate children-terminally-failed`, INCLUDING the four that also never ran (`blocked`, `dependency-blocked`, `not-attempted`, `not-run`). Those four are OUT OF SCOPE here (see the Deferred section) and keeping them on the failure code is the authored, reviewed decision, not an oversight.
  - Execution state: performed

### Task group 2: split the reason

- [x] E-02 ADD `ORCH_REASON_CHILDREN_NOT_APPROVED = "children-not-approved"` immediately after `ORCH_REASON_DEAD_CHILDREN` in `runner_shared`, with a `#:` comment citing `swk6r8` and stating that it is a SUBSET of the dead-children condition (terminal, not success, but never dispatched), and a module constant `_NOT_APPROVED_CHILD_STATUSES = frozenset({"reviewed", "approved"})`. Justify the set in the comment from repository evidence: `initial_queue_status` freezes any plan status outside `NON_TERMINAL_QUEUE_STATUSES` as `reviewed` (never dispatched), and an `approved` queue status is only ever a REVIEW item's disposition (`SUCCESS_STATES = {"executed", "reviewed", "approved"}` is the review bar; verified in review that `reconcile_disposition` returns `status` for a review item when `status in ("reviewed", "approved")`), so for an `execute` child neither status means the child ran. ALSO record in that comment the ONE overload of `reviewed` that reaches this branch and why it is still correct (added in review, F-6): a plan carrying NO `- Status:` line also maps to `reviewed`, and "approve it" is right for that plan too. And record why the DANGEROUS-looking overload cannot reach here, so a later reader does not re-litigate it: `initial_queue_status` maps `superseded`/`not-executed` to `reviewed` as well, but a retired child is not UNFINISHED (`set_retirement_terminal_statuses()` is `{executed, not-executed, superseded}`), so `evaluate_set_retirement(...).unfinished` is empty and the dead branch is never reached. Measured in review: a child in `superseded/` yields `unfinished=()` and no dead-children reason at all.
  - Depends on: E-01
  - Expected outcome: both names importable from `agent_workflows.runner_shared`; `ORCH_REASON_DEAD_CHILDREN` unchanged at `"children-terminally-failed"`.
  - Execution state: performed

- [x] E-03 SPLIT THE `if dead:` BRANCH of `runner_shared.decide_orchestrator_dispatch`. Compute `unapproved = [(i, s) for i, s in dead if s in _NOT_APPROVED_CHILD_STATUSES]`. When `len(unapproved) == len(dead)`, return `ORCH_DISPATCH_TERMINATE` with `reason=ORCH_REASON_CHILDREN_NOT_APPROVED` and a `detail` of the shape `"Set {setid!r} can never complete in this run: child(ren) {listed} are awaiting human approval and were never dispatched, so they cannot become executed{also}"`. Otherwise keep the existing return byte-for-byte (`ORCH_REASON_DEAD_CHILDREN`, existing detail). The `unfinished` tuple and `eligibility` are populated identically in both arms. Carry a comment saying WHY a mixed set keeps the failure code: a child that actually failed is the stronger fact and needs investigation, and the failure remedy already covers approval.
  - Depends on: E-02
  - Expected outcome: E-01's probe now prints `reviewed`/`approved` -> `terminate children-not-approved`, `failed-safely` -> `terminate children-terminally-failed`, `queued` -> `reconsider children-unfinished`.
  - Execution state: performed

- [x] E-04 ADD THE REMEDY ENTRY and NARROW THE OLD ONE in `runner_shared._ORCH_REASON_TEXT`. New key `ORCH_REASON_CHILDREN_NOT_APPROVED`: reason text saying the orchestrator can never be retired by this run because its children are frozen awaiting human approval and were never dispatched, and that nothing failed. Its remedy names `aw ipd set approved <id6> --by-human --message ...` for each child named in the reason, then re-running the Set, and repeating the existing "do NOT remove the child's row" warning. It MUST NOT contain `--full-auto` (the block comment above `_ORCH_REASON_TEXT`, "NO REMEDY NAMES `--full-auto`", states why). Then rewrite the `ORCH_REASON_DEAD_CHILDREN` entry's reason to lead with "a child ran and did not reach success" and keep a SHORT approval sentence for the mixed case. The key itself is KEPT, so `orchestrator_refusal_text("children-terminally-failed")` still returns mapped text for historical run records rather than the unknown-code fallback. Update the comment above that entry, which currently explains the name/condition mismatch this plan removes.
  - Depends on: E-03
  - Expected outcome: `orchestrator_refusal_text("children-not-approved")` returns a non-empty mapped pair whose remedy contains `aw ipd set approved` and not `--full-auto`; `orchestrator_refusal_text("children-terminally-failed")` still returns a mapped pair (not the "DOES NOT RECOGNIZE" fallback).
  - Execution state: performed

### Task group 3: prove it

- [x] E-05 ADD `tests/test_orchestrator_not_approved_reason.py`, behavioral only (no source-text or structure pins, per the maintainer's 2026-09-26 test-policy ruling). Build the E-01 fixture in a `tempfile.TemporaryDirectory` and call the REAL `decide_orchestrator_dispatch`. Cases: (1) a single child `reviewed` -> TERMINATE + `children-not-approved`, and `detail` names `kid001`; (2) single child `approved` -> same; (3) single child `failed-safely` (also `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`) -> TERMINATE + `children-terminally-failed`; (4) MIXED: two children, one `reviewed` and one `failed-safely` -> `children-terminally-failed`, and `unfinished` names both; (5) `queued` -> RECONSIDER + `children-unfinished` (unchanged); (6) `orchestrator_refusal_text` for the new code is mapped, non-empty, contains `aw ipd set approved`, and does not contain `--full-auto`; (7) `orchestrator_refusal_text("children-terminally-failed")` is still mapped (its reason does not contain `DOES NOT RECOGNIZE`); (8) through `dispatch_orchestrator_item` on a minimal run dir (the `DispatchRunCase` helpers in `tests/test_orchestrator_retirement.py` show the shape, and its `write_plan`/`make_run`/`item` methods are the ones to mirror), a `reviewed` child leaves the item's recorded refusal (`render_stream.refusal_of_item(item).code`) equal to `children-not-approved`, proving the new code reaches the read surface. ADD TWO MORE CASES, both found in review: (9) the OUTCOME IS UNCHANGED for the new code, asserting `ORCH_DISPATCH_TERMINATE` explicitly in cases (1) and (2), because the Scope promises "outcome stays `ORCH_DISPATCH_TERMINATE` in both cases" and nothing else pins it, so a future edit could flip a terminate to a reconsider and reintroduce the 201-iteration spin the `if dead:` branch's own comment records; and (10) a child with NO `- Status:` line (queue status `reviewed` via `initial_queue_status(None)`, measured unfinished in review) -> `children-not-approved`, which pins the one legitimate `reviewed` overload that reaches this branch (F-6) so a later reader does not "fix" it by narrowing the status set.
  - Depends on: E-04
  - Expected outcome: all cases pass; cases (1), (2), (6), (8) and (10) FAIL against the pre-change code; (3), (4), (5), (7), (9) pass both before and after (controls; note (9) is a control for the OUTCOME while (1)/(2) change the REASON, which is why it passes both ways).
  - Execution state: performed

## Project conventions discovered (Step 0)

- The `ORCH_REASON_*` vocabulary is the one `decide_orchestrator_dispatch` emits; `evaluate_set_retirement`'s `RETIRE_REFUSED_*` values are translated into it before any item field is written (block comment above `_ORCH_REASON_TEXT`, "KEYED ON `ORCH_REASON_*`, NEVER ON `RETIRE_REFUSED_*`").
- An unknown reason code is REPORTED, not raised: `orchestrator_refusal_text` returns a fallback naming the code verbatim (verified in review: calling it for `children-not-approved` today returns a reason containing "THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE"). That is why the old key must stay mapped: historical run `state.json` files carry `orchestrator_refusal_reason: children-terminally-failed` and are rendered by `aw runs`. NOTE ON THAT CITATION (corrected in review, F-9): the authored plan cited a specific path, `.aw/records/runs/run-20260913T031350Z-1732436/state.json`, which does NOT exist in a fresh checkout. It is not a false claim, it is an UNVERIFIABLE one: `.aw/.gitignore` ignores `records/runs/`, so run records are box-local and never committed. The keep-the-key requirement stands on the CODE (the fallback path in `orchestrator_refusal_text`) rather than on any one run directory, so do not treat the missing path as a failed precondition, and do not go looking for it.
- No remedy names `--full-auto` or a host command (`aw oc run` / `aw agy run`); the one command allowed is `aw ipd set approved`, host-neutral (same block comment).
- Spec `77tr3o` R-9 requires the refusal reasons to be DISTINGUISHABLE in the record; it does not enumerate the code strings (grep of `.aw/records/specs/` for `children-terminally-failed` returns nothing). Adding a finer code strengthens R-9 and amends no spec.
- `tests/test_finalize_sendback.py::TheOrchestratorBarIsNotKilledWhileRetryBudgetRemains::test_an_EXHAUSTED_child_DOES_terminate_the_set` asserts `ORCH_REASON_DEAD_CHILDREN` for `FINALIZE_RETRY_EXHAUSTED_STATUS` (= `failed-safely`), which is a real failure and keeps that code under this plan.
- Tests run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`. Tests are behavioral only (maintainer ruling 2026-09-26).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `runner_shared.decide_orchestrator_dispatch`, `if dead:` branch | A never-dispatched child (`reviewed`/`approved`) yields the same code as a failed one. | probe: `reviewed terminate children-terminally-failed`, `approved terminate children-terminally-failed`, `failed-safely terminate children-terminally-failed` |
| F-2 | INFO | `runner_shared.TERMINAL_STATES` | Both `reviewed` and `approved` are terminal and neither is an execution success, which is why they land in `dead`. | `sorted(TERMINAL_STATES)` includes `approved`, `reviewed`; `EXECUTION_SUCCESS_STATES` is `{"executed"}` (CORRECTED in review, F-8: the authored cell said `{executed, substantially-complete}`, which is false; `substantially-complete` is in `TERMINAL_STATES` and is NOT a success, so it lands in `dead` and correctly keeps the failure code) |
| F-6 | LOW | `runner_shared.initial_queue_status` | **`reviewed` IS AN OVERLOADED QUEUE STATUS, BUT THE DANGEROUS OVERLOAD IS UNREACHABLE HERE, AND THE REMAINING ONE IS BENIGN.** Raised in review as a suspected MEDIUM (a `superseded`/`not-executed` plan also gets queue status `reviewed`, per `initial_queue_status`'s own docstring, so "approve it" could be aimed at a deliberately retired plan) and then DISPROVED by driving it: a retired child is not UNFINISHED, so it never reaches the dead branch at all. Measured: child in `superseded/` (or `not-executed/`) -> `evaluate_set_retirement(...).unfinished == ()` and the dispatch never returns a dead-children reason; a `- Status: superseded` plan sitting wrongly in `pending/` likewise yields `unfinished=()`. The overload that DOES reach the branch is a plan with NO `- Status:` line (an older hand-written manifest), which also maps to `reviewed` and is unfinished. For that case "approve it" is the RIGHT advice, so the new code is still correct. Recorded because the reasoning, not just the conclusion, is what a later reader needs. | `initial_queue_status('superseded'\|'not-executed'\|None) == 'reviewed'`; child in `superseded/` -> `unfinished=()`, no dead reason; `pending/` with no Status -> `unfinished=(('kid001','reviewed'),)` -> `children-terminally-failed` |
| F-7 | LOW | `decide_orchestrator_dispatch` dead branch | **FOUR OTHER NEVER-DISPATCHED STATUSES KEEP THE FAILURE CODE, WHICH THE PLAN DOES NOT SAY.** Swept all 23 `TERMINAL_STATES` in review: besides `reviewed`/`approved`, the statuses `blocked`, `dependency-blocked`, `not-attempted` and `not-run` all yield `children-terminally-failed`, and none of them means "ran and failed" either (`dependency-blocked` is written at dispatch when an edge is unmet, and `not-attempted`/`not-run` are by name un-run). The plan's fix is still correct and strictly better, but its Concern frames the defect as binary (approval vs failure) when the real space has a third class the plan deliberately leaves alone. | sweep output: `blocked`, `dependency-blocked`, `not-attempted`, `not-run` -> `terminate children-terminally-failed`; `executed` -> `children-not-in-this-run` |
| F-3 | LOW | `run_viewer` refusal render | The code is shown to operators verbatim. | `run_viewer.py`: `f"  ! refused [{refusal.code}]: {refusal.reason}"` (line ~2119) |
| F-4 | INFO | `_ORCH_REASON_TEXT[ORCH_REASON_DEAD_CHILDREN]` | The human remedy already leads with approval, so the prose is honest; only the code misleads. | entry text: "The usual cause is a child that was never dispatched because it is not approved, NOT a child that crashed" |
| F-5 | INFO | tests | The only test naming `ORCH_REASON_DEAD_CHILDREN` uses `failed-safely`, a genuine failure. | `rg ORCH_REASON_DEAD_CHILDREN tests` -> `tests/test_finalize_sendback.py` only, at `test_a_queued_retrying_child_is_NOT_declared_dead` (assertNotEqual) and `test_an_EXHAUSTED_child_DOES_terminate_the_set` (assertEqual). Confirmed in review. |
| F-8 | LOW | F-2's own evidence cell | **A FINDING'S EVIDENCE MISSTATED A SET THIS PLAN'S CORRECTNESS DEPENDS ON.** F-2 asserted `EXECUTION_SUCCESS_STATES` is `{executed, substantially-complete}`. It is `{"executed"}` (driven in review). The distinction matters rather than being pedantic: `substantially-complete` IS in `TERMINAL_STATES` and is NOT a success, so it lands in `dead` and must keep the FAILURE code (it means a turn ran and under-delivered). Had the executor believed the wrong set, `substantially-complete` would have looked like a success that never reaches the branch, and a plausible "while I am here" widening of `_NOT_APPROVED_CHILD_STATUSES` would have mislabeled a real under-delivery as an approval wait. | `sorted(runner_shared.EXECUTION_SUCCESS_STATES) == ['executed']`; `sorted(SUCCESS_STATES) == ['approved','executed','reviewed']`; sweep: `substantially-complete` -> `terminate children-terminally-failed` |
| F-9 | LOW | Project-conventions bullet citing a run record | **A CITED EVIDENCE PATH DOES NOT EXIST IN A CHECKOUT, BY DESIGN.** The plan cited `.aw/records/runs/run-20260913T031350Z-1732436/state.json` as the historical record proving the old key must stay mapped. No `.aw/records/runs/` directory exists here: `.aw/.gitignore` ignores `records/runs/`, so run records are box-local. The requirement is sound and rests on the CODE (the unknown-code fallback in `orchestrator_refusal_text`, driven in review), so the fix is to stop leaning on an uncommittable path, not to drop the requirement. Left unfixed it would read to an executor as a failed precondition and invite a hunt outside the workspace. | `ls .aw/records/runs/` -> does not exist; `git check-ignore -v` -> `.aw/.gitignore:14:records/runs/`; `orchestrator_refusal_text('children-not-approved')` -> "THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE" |

## Proposed changes (ordered, validatable)

1. E-01 re-measures.
2. E-02 adds the constant and the status set.
3. E-03 splits the branch (all-unapproved -> new code; any failure -> old code).
4. E-04 adds the new remedy and narrows the old one, keeping its key.
5. E-05 adds behavioral tests including a read-surface case and controls.

## Deferred / out of scope (with reason)

- Rewriting historical run records that carry `children-terminally-failed` for an unapproved child.
  - Carrier-Declined: run records are a historical observation of what the runner said at the time; rewriting them would falsify history, and the old key stays mapped so they still render.
- Giving the four OTHER never-dispatched terminal statuses (`blocked`, `dependency-blocked`, `not-attempted`, `not-run`) a non-failure code (added in review, F-7).
  - Carrier-Declined: measured in review that all four currently yield `children-terminally-failed` and none of them means "ran and failed" either, so the same naming complaint applies to them. They are NOT folded in here because each needs a DIFFERENT remedy sentence and the remedies are the deliverable: `dependency-blocked` tells the operator to run the prerequisite, `blocked` points at a gate, and `not-attempted`/`not-run` mean the run ended before reaching the child. Bundling four remedies into one plan would produce one vague message instead of two precise ones, which is the defect this plan exists to fix. The approval case is also the one with a MEASURED operator cost in backlog `swk6r8`. A follow-up may extend the same split; this plan's `_NOT_APPROVED_CHILD_STATUSES` is the seam to extend, and `orchestrator_refusal_text`'s unknown-code fallback means a future code degrades gracefully rather than crashing.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/run_viewer.py` and `agent_workflows/render_stream.py` are deliberately NOT declared: they render `Refusal.code` generically and need no change. `tests/test_finalize_sendback.py` is not modified; it must stay green.
- Scope-Paths justification: `runner_shared.py` holds the constants, the decision, and the text map; the new test file holds E-05.

## Required tests / validation

- `tests/test_orchestrator_not_approved_reason.py` (new): TEN behavioral cases (eight authored plus (9) and (10) added in review), FIVE shown failing before the fix.
- `python3 -m pytest -o addopts="" tests/test_finalize_sendback.py tests/test_orchestrator_retirement.py` stays green.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: spec `77tr3o` R-9 requires distinguishable reasons and enumerates no code strings, so a finer code satisfies it more strictly without amending it. No `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs enumerate these codes (grep of `docs/` and `README.md` for `children-terminally-failed` finds nothing).

## Open questions

### OQ-01: For a mixed set of unapproved and failed children, which code wins?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: The FAILURE code, from repository evidence: the existing `ORCH_REASON_DEAD_CHILDREN` remedy already tells the operator to check each child's status and names approval, so it is correct for the mixed case, whereas `children-not-approved` would hide a real failure behind an "approve it" instruction. This was also the brief's stated design.

### OQ-02: Does changing the code for the approval case require a spec amendment (backlog `swk6r8` says the vocabulary is governed by spec `77tr3o`)?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No. `77tr3o` R-9 ("THE TWO REFUSAL REASONS MUST BE DISTINGUISHABLE IN THE RECORD") names facts, not strings, and a grep of `.aw/records/specs/` for the code strings returns nothing. The change adds distinguishability, which is the direction R-9 demands.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the four `(status, outcome, reason)` lines from the probe at the executing HEAD, and the HEAD hash.
  - Observed evidence: PASS. Measured at executing HEAD dd25636f4e90eea0a75fd14b557f46a71b4f3cb9:
    Executing HEAD: dd25636f4e90eea0a75fd14b557f46a71b4f3cb9
    Probe output:
    ('reviewed', 'terminate', 'children-terminally-failed')
    ('approved', 'terminate', 'children-terminally-failed')
    ('failed-safely', 'terminate', 'children-terminally-failed')
    ('queued', 'reconsider', 'children-unfinished')

    Full TERMINAL_STATES sweep at HEAD dd25636f4e90eea0a75fd14b557f46a71b4f3cb9:
    already-landed         -> ('terminate', 'children-terminally-failed')
    approved               -> ('terminate', 'children-terminally-failed')
    blocked                -> ('terminate', 'children-terminally-failed')
    dependency-blocked     -> ('terminate', 'children-terminally-failed')
    executed               -> ('terminate', 'children-not-in-this-run')
    fail-begin             -> ('terminate', 'children-terminally-failed')
    fail-depend            -> ('terminate', 'children-terminally-failed')
    fail-gate              -> ('terminate', 'children-terminally-failed')
    fail-lane              -> ('terminate', 'children-terminally-failed')
    fail-merge             -> ('terminate', 'children-terminally-failed')
    fail-verify            -> ('terminate', 'children-terminally-failed')
    failed                 -> ('terminate', 'children-terminally-failed')
    failed-safely          -> ('terminate', 'children-terminally-failed')
    integration-blocked    -> ('terminate', 'children-terminally-failed')
    interrupted            -> ('terminate', 'children-terminally-failed')
    merge-conflict         -> ('terminate', 'children-terminally-failed')
    merge-needs-human      -> ('terminate', 'children-terminally-failed')
    merge-refused          -> ('terminate', 'children-terminally-failed')
    not-attempted          -> ('terminate', 'children-terminally-failed')
    not-run                -> ('terminate', 'children-terminally-failed')
    partial                -> ('terminate', 'children-terminally-failed')
    reviewed               -> ('terminate', 'children-terminally-failed')
    substantially-complete -> ('terminate', 'children-terminally-failed')
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `python3 -c "from agent_workflows import runner_shared as r; print(r.ORCH_REASON_CHILDREN_NOT_APPROVED, r.ORCH_REASON_DEAD_CHILDREN, sorted(r._NOT_APPROVED_CHILD_STATUSES))"` output.
  - Observed evidence: PASS. Output confirms ORCH_REASON_CHILDREN_NOT_APPROVED, ORCH_REASON_DEAD_CHILDREN, and _NOT_APPROVED_CHILD_STATUSES:
    $ python3 -c "from agent_workflows import runner_shared as r; print(r.ORCH_REASON_CHILDREN_NOT_APPROVED, r.ORCH_REASON_DEAD_CHILDREN, sorted(r._NOT_APPROVED_CHILD_STATUSES))"
    children-not-approved children-terminally-failed ['approved', 'reviewed']
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff of the `if dead:` branch and the re-run of the E-01 probe showing `reviewed`/`approved` -> `children-not-approved`, `failed-safely` -> `children-terminally-failed`, `queued` -> `children-unfinished`.
  - Observed evidence: PASS. Diff of dead branch and probe rerun confirm reviewed/approved -> children-not-approved:
    Diff of if dead: branch in agent_workflows/runner_shared.py:
    ```diff
    @@ -18002,6 +18002,22 @@ def decide_orchestrator_dispatch(
             listed = ", ".join(f"{i} ({s})" for i, s in dead)
             rest = actionable + stranded
             also = f"; {len(rest)} other child(ren) are also unfinished" if rest else ""
    +        unapproved = [(i, s) for i, s in dead if s in _NOT_APPROVED_CHILD_STATUSES]
    +        if len(unapproved) == len(dead):
    +            return OrchestratorDispatch(
    +                outcome=ORCH_DISPATCH_TERMINATE,
    +                reason=ORCH_REASON_CHILDREN_NOT_APPROVED,
    +                detail=(
    +                    f"Set {decision.setid!r} can never complete in this run: child(ren) {listed} "
    +                    f"are awaiting human approval and were never dispatched, so they cannot become "
    +                    f"{SET_RETIREMENT_DONE_STATUS}{also}"
    +                ),
    +                unfinished=tuple(dead) + tuple(rest),
    +                eligibility=decision,
    +            )
    +        # A mixed set of unapproved and failed children keeps ORCH_REASON_DEAD_CHILDREN:
    +        # a child that actually failed is the stronger fact and needs investigation,
    +        # and the failure remedy already covers approval.
             return OrchestratorDispatch(
                 outcome=ORCH_DISPATCH_TERMINATE,
                 reason=ORCH_REASON_DEAD_CHILDREN,
    ```
    Re-run of E-01 probe:
    ('reviewed', 'terminate', 'children-not-approved')
    ('approved', 'terminate', 'children-not-approved')
    ('failed-safely', 'terminate', 'children-terminally-failed')
    ('queued', 'reconsider', 'children-unfinished')
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the output of calling `orchestrator_refusal_text` for `children-not-approved` and `children-terminally-failed`, showing both mapped, the first containing `aw ipd set approved` and neither containing `--full-auto`.
  - Observed evidence: PASS. Refusal text mapped for both codes, contains aw ipd set approved, no --full-auto:
    === children-not-approved ===
    Reason: this orchestrator can NEVER be retired by this run: its child plans are frozen awaiting human approval and were never dispatched, so they cannot become `executed`. Nothing failed
    Remedy: approve each unapproved child named in the reason above with `aw ipd set approved <id6> --by-human --message ...` and run the Set again. Do NOT remove the child's row from the orchestrator's table to clear this, which would retire the parent over work that never completed
    Has aw ipd set approved: True
    Contains --full-auto: False

    === children-terminally-failed ===
    Reason: this orchestrator can NEVER be retired by this run: a child ran and did not reach success, so the Set cannot complete however long the run waits. If unapproved children are also present, they cannot complete either
    Remedy: look at each child's status named in the reason above. For any child that ran and did not finish: read that child's own outcome record, fix what it reports, then re-run it. For a child awaiting approval: approve it with `aw ipd set approved <id6> --by-human --message ...`. Either way do NOT remove the child's row from the orchestrator's table to clear this, which would retire the parent over work that never completed
    Has aw ipd set approved: True
    Contains --full-auto: False
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_orchestrator_not_approved_reason.py` passing with its count; the same run with the E-03/E-04 hunks temporarily reverted showing cases (1), (2), (6), (8), (10) FAILING and the controls passing; then `python3 -m pytest -o addopts="" -q tests/test_finalize_sendback.py tests/test_orchestrator_retirement.py` passing; then the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty). The before-and-after bare run is REQUIRED and not optional here: `decide_orchestrator_dispatch` is shared by both hosts and `tests/test_finalize_sendback.py` asserts `ORCH_REASON_DEAD_CHILDREN` for `failed-safely`, so a too-wide status set breaks an existing test rather than merely under-delivering.
  - Observed evidence: PASS. All 10 cases pass, 5 fail pre-fix, related tests pass, and full suite is clean:
    1) python3 -m pytest -o addopts="" -q tests/test_orchestrator_not_approved_reason.py:
    ..........                                                               [100%]
    10 passed in 0.74s

    2) Same run before E-03/E-04 hunks (cases 1, 2, 6, 8, 10 failing, controls passing):
    FAILED tests/test_orchestrator_not_approved_reason.py::TestOrchestratorNotApprovedReason::test_case_10_child_with_no_status_line
    FAILED tests/test_orchestrator_not_approved_reason.py::TestOrchestratorNotApprovedReason::test_case_06_orchestrator_refusal_text_new_code
    FAILED tests/test_orchestrator_not_approved_reason.py::TestOrchestratorNotApprovedReason::test_case_08_read_surface_via_dispatch_orchestrator_item
    FAILED tests/test_orchestrator_not_approved_reason.py::TestOrchestratorNotApprovedReason::test_case_02_single_child_approved
    FAILED tests/test_orchestrator_not_approved_reason.py::TestOrchestratorNotApprovedReason::test_case_01_single_child_reviewed
    5 failed, 5 passed in 0.26s

    3) python3 -m pytest -o addopts="" -q tests/test_finalize_sendback.py tests/test_orchestrator_retirement.py:
    ........................................................................ [ 76%]
    ......................                                                   [100%]
    94 passed in 68.15s (0:01:08)

    4) Bare pytest before and after summary lines:
    Before: 2689 passed, 2 skipped, 3 warnings in 123.15s (0:02:03)
    After:  2699 passed, 2 skipped, 3 warnings in 77.87s (0:01:17)
    After-minus-before failing node-ID set: set() (0 failing before, 0 failing after).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. One new orchestrator refusal code, `children-not-approved`, emitted only when every child blocking a Set is frozen awaiting approval (never dispatched), with its own remedy telling the operator to approve the child via `aw ipd set approved`. A child that actually failed, alone or mixed with unapproved ones, keeps `children-terminally-failed`. What the runner DECIDES (terminate vs reconsider) does not change for any status, and the old code stays mapped so historical run records still render.

WHAT THIS DELIBERATELY DOES NOT FIX, so the approver is not surprised later (added in review, F-7). Sweeping all 23 terminal statuses showed that FOUR others also carry `children-terminally-failed` without having run: `blocked`, `dependency-blocked`, `not-attempted` and `not-run`. The same naming complaint applies to them and this plan leaves them alone on purpose, because each needs its own remedy sentence (run the prerequisite / clear the gate / the run ended early) and bundling four remedies would produce one vague message instead of two precise ones. `_NOT_APPROVED_CHILD_STATUSES` is the seam a follow-up extends. So after this plan the code is right about the approval case and still coarse about four others, which is a tracked stopping point rather than an oversight.

WHAT IS PROVEN VERSUS ASSERTED. The defect was re-driven in review at HEAD `61ef21d8` on the real function (`reviewed`/`approved`/`failed-safely` -> `children-terminally-failed`; `queued` -> `children-unfinished`; `executed` -> `children-not-in-this-run`), so the premise is measured rather than inferred. The read-surface claim is also checked in code: `dispatch_orchestrator_item` passes `code=decision.reason` into `record_refusal`, which is why E-05 case (8) is a genuine end-to-end assertion and not a restatement of case (1).

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/runner_shared.py` (the `ORCH_REASON_*` constants, `_ORCH_REASON_TEXT`, and `decide_orchestrator_dispatch`'s dead branch) and the new `tests/test_orchestrator_not_approved_reason.py`. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-05 must show the new cases FAILING before the fix.

GENUINE STOP CONDITION: if E-01 shows the approval case already carries a distinct code, retire this plan instead of executing it. NOT a stop condition (clarified in review, F-9): the Project-conventions bullet cites a run `state.json` path that does NOT exist in a checkout, because `.aw/.gitignore` ignores `records/runs/`. That is expected, the keep-the-old-key requirement rests on the code's unknown-code fallback rather than on that file, and it is not a missing input to hunt for.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `swk6r8` `done` with `--evidence` citing the executed plan.
