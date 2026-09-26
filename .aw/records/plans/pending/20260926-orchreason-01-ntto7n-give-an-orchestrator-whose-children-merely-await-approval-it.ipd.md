# IPD: Give an orchestrator whose children merely await approval its own refusal code instead of children-terminally-failed

- Date: 2026-09-26
- Kind: child
- Concern: THE ORCHESTRATOR REFUSAL CODE SAYS A CHILD FAILED WHEN IT WAS ONLY NEVER APPROVED. `runner_shared.decide_orchestrator_dispatch` puts every child whose run status is `in terminal_states and not in success_states` into its `dead` list and returns `reason=ORCH_REASON_DEAD_CHILDREN` (`"children-terminally-failed"`). `reviewed` and `approved` are both in `runner_shared.TERMINAL_STATES` and neither is in `oc_runipd.EXECUTION_SUCCESS_STATES`, so a child that was frozen awaiting human approval and never dispatched gets the same machine code as a child that ran and failed. Measured at HEAD `61ef21d8` by calling the real function on a temp repo (orchestrator `par001` + child `kid001`): child run status `reviewed` -> `terminate children-terminally-failed`; `approved` -> `terminate children-terminally-failed`; `failed-safely` -> `terminate children-terminally-failed`; `queued` -> `reconsider children-unfinished`. The code is operator-visible: `dispatch_orchestrator_item` writes it as `Refusal.code` via `render_stream.record_refusal`, and `run_viewer` prints `! refused [<code>]: <reason>`. The human REMEDY text in `_ORCH_REASON_TEXT` already names the approval case first, so only the machine code (and the `detail` sentence "reached a non-success terminal state") misleads.
- Scope: IN: (a) a new constant `ORCH_REASON_CHILDREN_NOT_APPROVED = "children-not-approved"` beside the other `ORCH_REASON_*` values; (b) in `decide_orchestrator_dispatch`'s `if dead:` branch, return the new reason ONLY when EVERY dead child's run status is in `{"reviewed", "approved"}`, with a `detail` sentence saying the children await approval and were never dispatched; a mixed set keeps `ORCH_REASON_DEAD_CHILDREN` (a real failure is the stronger fact, and the remedy for it already mentions approval); outcome stays `ORCH_DISPATCH_TERMINATE` in both cases; (c) a new `_ORCH_REASON_TEXT` entry for the new code whose remedy names `aw ipd set approved <id6> --by-human --message ...` and does NOT name `--full-auto`; (d) narrowing the `ORCH_REASON_DEAD_CHILDREN` entry's prose to the failure case now that approval has its own code, while keeping the key so historical run records (`.aw/records/runs/*/state.json` carry `orchestrator_refusal_reason: children-terminally-failed`) still render their mapped text; (e) behavioral tests in a new test file. OUT: changing WHAT the dispatch decides (TERMINATE vs RECONSIDER) for any status; changing `TERMINAL_STATES` or either success set; rewriting historical run records; the `RETIRE_REFUSED_*` vocabulary of `evaluate_set_retirement`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_not_approved_reason.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: swk6r8
- Set: orchreason
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ntto7n

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog swk6r8. Authored review-ready; the misclassification was re-measured at HEAD 61ef21d8 by calling decide_orchestrator_dispatch on a temp repo for reviewed/approved/failed-safely/queued children.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the durable, operator-visible orchestrator refusal code distinguish "your child is waiting for approval" from "your child ran and failed", so an operator and any tooling keying on `refusal.code` are not told a crash happened when nothing ran.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE the misclassification at the executing HEAD. On a temp repo holding `.aw/records/plans/pending/20260908-finalback-00-par001-orch.ipd.md` (`- Kind: orchestrator`, `- Order: 0`) and `...-01-kid001-child.ipd.md` (`- Kind: child`, `- Order: 1`), the same fixture `tests/test_finalize_sendback.py::TheOrchestratorBarIsNotKilledWhileRetryBudgetRemains._repo_with_unfinished_child` builds, call `runner_shared.decide_orchestrator_dispatch(repo, "finalback", "par001", [{"id6": "kid001", "setid": "finalback", "status": S, "action": "execute"}], terminal_states=runner_shared.TERMINAL_STATES, success_states=oc_runipd.EXECUTION_SUCCESS_STATES)` for S in `reviewed`, `approved`, `failed-safely`, `queued`, and paste `(S, outcome, reason)`. If `reviewed`/`approved` already yield a non-failure code, STOP and report that the defect is fixed.
  - Depends on: none
  - Expected outcome: `reviewed`, `approved`, `failed-safely` all -> `terminate children-terminally-failed`; `queued` -> `reconsider children-unfinished`.
  - Execution state: pending

### Task group 2: split the reason

- [ ] E-02 ADD `ORCH_REASON_CHILDREN_NOT_APPROVED = "children-not-approved"` immediately after `ORCH_REASON_DEAD_CHILDREN` in `runner_shared`, with a `#:` comment citing `swk6r8` and stating that it is a SUBSET of the dead-children condition (terminal, not success, but never dispatched), and a module constant `_NOT_APPROVED_CHILD_STATUSES = frozenset({"reviewed", "approved"})`. Justify the set in the comment from repository evidence: `initial_queue_status` freezes any plan status outside `NON_TERMINAL_QUEUE_STATUSES` as `reviewed` (never dispatched), and an `approved` queue status is only ever a REVIEW item's disposition (`SUCCESS_STATES = {"executed", "reviewed", "approved"}` is the review bar), so for an `execute` child neither status means the child ran.
  - Depends on: E-01
  - Expected outcome: both names importable from `agent_workflows.runner_shared`; `ORCH_REASON_DEAD_CHILDREN` unchanged at `"children-terminally-failed"`.
  - Execution state: pending

- [ ] E-03 SPLIT THE `if dead:` BRANCH of `runner_shared.decide_orchestrator_dispatch`. Compute `unapproved = [(i, s) for i, s in dead if s in _NOT_APPROVED_CHILD_STATUSES]`. When `len(unapproved) == len(dead)`, return `ORCH_DISPATCH_TERMINATE` with `reason=ORCH_REASON_CHILDREN_NOT_APPROVED` and a `detail` of the shape `"Set {setid!r} can never complete in this run: child(ren) {listed} are awaiting human approval and were never dispatched, so they cannot become executed{also}"`. Otherwise keep the existing return byte-for-byte (`ORCH_REASON_DEAD_CHILDREN`, existing detail). The `unfinished` tuple and `eligibility` are populated identically in both arms. Carry a comment saying WHY a mixed set keeps the failure code: a child that actually failed is the stronger fact and needs investigation, and the failure remedy already covers approval.
  - Depends on: E-02
  - Expected outcome: E-01's probe now prints `reviewed`/`approved` -> `terminate children-not-approved`, `failed-safely` -> `terminate children-terminally-failed`, `queued` -> `reconsider children-unfinished`.
  - Execution state: pending

- [ ] E-04 ADD THE REMEDY ENTRY and NARROW THE OLD ONE in `runner_shared._ORCH_REASON_TEXT`. New key `ORCH_REASON_CHILDREN_NOT_APPROVED`: reason text saying the orchestrator can never be retired by this run because its children are frozen awaiting human approval and were never dispatched, and that nothing failed. Its remedy names `aw ipd set approved <id6> --by-human --message ...` for each child named in the reason, then re-running the Set, and repeating the existing "do NOT remove the child's row" warning. It MUST NOT contain `--full-auto` (the block comment above `_ORCH_REASON_TEXT`, "NO REMEDY NAMES `--full-auto`", states why). Then rewrite the `ORCH_REASON_DEAD_CHILDREN` entry's reason to lead with "a child ran and did not reach success" and keep a SHORT approval sentence for the mixed case. The key itself is KEPT, so `orchestrator_refusal_text("children-terminally-failed")` still returns mapped text for historical run records rather than the unknown-code fallback. Update the comment above that entry, which currently explains the name/condition mismatch this plan removes.
  - Depends on: E-03
  - Expected outcome: `orchestrator_refusal_text("children-not-approved")` returns a non-empty mapped pair whose remedy contains `aw ipd set approved` and not `--full-auto`; `orchestrator_refusal_text("children-terminally-failed")` still returns a mapped pair (not the "DOES NOT RECOGNIZE" fallback).
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 ADD `tests/test_orchestrator_not_approved_reason.py`, behavioral only (no source-text or structure pins, per the maintainer's 2026-09-26 test-policy ruling). Build the E-01 fixture in a `tempfile.TemporaryDirectory` and call the REAL `decide_orchestrator_dispatch`. Cases: (1) a single child `reviewed` -> TERMINATE + `children-not-approved`, and `detail` names `kid001`; (2) single child `approved` -> same; (3) single child `failed-safely` (also `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`) -> TERMINATE + `children-terminally-failed`; (4) MIXED: two children, one `reviewed` and one `failed-safely` -> `children-terminally-failed`, and `unfinished` names both; (5) `queued` -> RECONSIDER + `children-unfinished` (unchanged); (6) `orchestrator_refusal_text` for the new code is mapped, non-empty, contains `aw ipd set approved`, and does not contain `--full-auto`; (7) `orchestrator_refusal_text("children-terminally-failed")` is still mapped (its reason does not contain `DOES NOT RECOGNIZE`); (8) through `dispatch_orchestrator_item` on a minimal run dir (the `DispatchRunCase` helpers in `tests/test_orchestrator_retirement.py` show the shape), a `reviewed` child leaves the item's recorded refusal (`render_stream.refusal_of_item(item).code`) equal to `children-not-approved`, proving the new code reaches the read surface.
  - Depends on: E-04
  - Expected outcome: all cases pass; cases (1), (2), (6) and (8) FAIL against the pre-change code; (3), (4), (5), (7) pass both before and after (controls).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The `ORCH_REASON_*` vocabulary is the one `decide_orchestrator_dispatch` emits; `evaluate_set_retirement`'s `RETIRE_REFUSED_*` values are translated into it before any item field is written (block comment above `_ORCH_REASON_TEXT`, "KEYED ON `ORCH_REASON_*`, NEVER ON `RETIRE_REFUSED_*`").
- An unknown reason code is REPORTED, not raised: `orchestrator_refusal_text` returns a fallback naming the code verbatim. That is why the old key must stay mapped: historical `state.json` files (e.g. `.aw/records/runs/run-20260913T031350Z-1732436/state.json`, `orchestrator_refusal_reason: children-terminally-failed`) are rendered by `aw runs`.
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
| F-2 | INFO | `runner_shared.TERMINAL_STATES` | Both `reviewed` and `approved` are terminal and neither is an execution success, which is why they land in `dead`. | `sorted(TERMINAL_STATES)` includes `approved`, `reviewed`; `EXECUTION_SUCCESS_STATES` is `{executed, substantially-complete}` |
| F-3 | LOW | `run_viewer` refusal render | The code is shown to operators verbatim. | `run_viewer.py`: `f"  ! refused [{refusal.code}]: {refusal.reason}"` (line ~2119) |
| F-4 | INFO | `_ORCH_REASON_TEXT[ORCH_REASON_DEAD_CHILDREN]` | The human remedy already leads with approval, so the prose is honest; only the code misleads. | entry text: "The usual cause is a child that was never dispatched because it is not approved, NOT a child that crashed" |
| F-5 | INFO | tests | The only test naming `ORCH_REASON_DEAD_CHILDREN` uses `failed-safely`, a genuine failure. | `rg ORCH_REASON_DEAD_CHILDREN tests` -> `tests/test_finalize_sendback.py` lines 730, 741 only |

## Proposed changes (ordered, validatable)

1. E-01 re-measures.
2. E-02 adds the constant and the status set.
3. E-03 splits the branch (all-unapproved -> new code; any failure -> old code).
4. E-04 adds the new remedy and narrows the old one, keeping its key.
5. E-05 adds behavioral tests including a read-surface case and controls.

## Deferred / out of scope (with reason)

- Rewriting historical run records that carry `children-terminally-failed` for an unapproved child.
  - Carrier-Declined: run records are a historical observation of what the runner said at the time; rewriting them would falsify history, and the old key stays mapped so they still render.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/run_viewer.py` and `agent_workflows/render_stream.py` are deliberately NOT declared: they render `Refusal.code` generically and need no change. `tests/test_finalize_sendback.py` is not modified; it must stay green.
- Scope-Paths justification: `runner_shared.py` holds the constants, the decision, and the text map; the new test file holds E-05.

## Required tests / validation

- `tests/test_orchestrator_not_approved_reason.py` (new): eight behavioral cases, four shown failing before the fix.
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

- [ ] V-01 validates E-01
  - Required evidence: paste the four `(status, outcome, reason)` lines from the probe at the executing HEAD, and the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -c "from agent_workflows import runner_shared as r; print(r.ORCH_REASON_CHILDREN_NOT_APPROVED, r.ORCH_REASON_DEAD_CHILDREN, sorted(r._NOT_APPROVED_CHILD_STATUSES))"` output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the `if dead:` branch and the re-run of the E-01 probe showing `reviewed`/`approved` -> `children-not-approved`, `failed-safely` -> `children-terminally-failed`, `queued` -> `children-unfinished`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the output of calling `orchestrator_refusal_text` for `children-not-approved` and `children-terminally-failed`, showing both mapped, the first containing `aw ipd set approved` and neither containing `--full-auto`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_orchestrator_not_approved_reason.py` passing with its count; the same run with the E-03/E-04 hunks temporarily reverted showing cases (1), (2), (6), (8) FAILING and the controls passing; then `python3 -m pytest -o addopts="" -q tests/test_finalize_sendback.py tests/test_orchestrator_retirement.py` passing; then the bare `python3 -m pytest` summary line before and after with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. One new orchestrator refusal code, `children-not-approved`, emitted only when every child blocking a Set is frozen awaiting approval (never dispatched), with its own remedy telling the operator to approve the child via `aw ipd set approved`. A child that actually failed, alone or mixed with unapproved ones, keeps `children-terminally-failed`. What the runner DECIDES (terminate vs reconsider) does not change for any status, and the old code stays mapped so historical run records still render.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/runner_shared.py` (the `ORCH_REASON_*` constants, `_ORCH_REASON_TEXT`, and `decide_orchestrator_dispatch`'s dead branch) and the new `tests/test_orchestrator_not_approved_reason.py`. Any edit outside the declared paths is justified at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-05 must show the new cases FAILING before the fix.

GENUINE STOP CONDITION: if E-01 shows the approval case already carries a distinct code, retire this plan instead of executing it.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `swk6r8` `done` with `--evidence` citing the executed plan.
