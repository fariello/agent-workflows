# IPD: Name the real reason a review turn failed instead of blaming orchestrator readiness

- Date: 2026-10-07
- Kind: child
- Concern: A review turn that fails for any reason is reported as "review orchestrator readiness failed", even for a child plan. Measured 2026-10-07 in run `run-20261007T165351Z-456357`: the review of child `2j4pd0` ended because the model provider's content filter blocked a reply (`ContentFilterError`, last session record `reason: content-filter`), the host exited 1, and the run recorded `fail-gate` with the lane-preserved reason "review orchestrator readiness failed; lane preserved for inspection" and code `review-orchestrator-failed`. The cause is in `runner_shared.execute_item_core`: after `handle_review_orchestrator_readiness` returns the incoming disposition unchanged for a nonzero exit or a non-orchestrator, the caller tests `review_orch_disp == "fail-gate"`, which is true whenever the turn already failed, and writes the orchestrator reason. The real cause (a provider error in the session stream) is never surfaced anywhere in the summary or report.
- Scope: (1) Make the orchestrator-readiness branch fire only when `handle_review_orchestrator_readiness` itself refused (the item is an orchestrator, the turn exited 0, and its readiness check failed), and give every other failed review the preserved-lane reason of its actual cause; (2) read the host session stream's final error event (opencode `{"type":"error", ...}`, agy equivalent) and record it on the attempt as `host_error` with name and message; (3) show `host_error` in the run summary row and the execution report. EXCLUDES retrying the turn (that is `fixfirst` Order 04 `ytas91`), and EXCLUDES changing any disposition.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_review_failure_reason.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: lanegc
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ckxypc

## Workflow history
- 2026-10-07 to-review (aw set): authored review-ready at the maintainer's request 2026-10-07

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When a review fails, the summary says why ("provider content filter blocked the response", "host exited 1"), so the maintainer can act without reading session logs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the right reason

- [ ] E-01 In `runner_shared.execute_item_core`, record whether `handle_review_orchestrator_readiness` actually evaluated and refused (return a distinct marker, or compare against the incoming disposition and the item's `Kind`). Write the "review orchestrator readiness failed" reason and code only in that case. For any other failed review whose lane is preserved, write the reason from the turn's own outcome: the host error from E-02 when present, else "review turn exited <code> with no outcome file", else the disposition.
  - Depends on: none
  - Expected outcome: a child review whose host exits 1 records a preserved-lane reason naming the exit and no `review-orchestrator-failed` code; an orchestrator review whose readiness refuses still records the orchestrator reason.
  - Execution state: pending

### Task group 2: capture the host's error

- [ ] E-02 Add a pure parser that reads the last error event from a session stream file (opencode `{"type":"error","error":{"name":...,"data":{"message":...}}}`; the agy host's equivalent, or none if it has no such event) and returns `(name, message)` or nothing. Call it after every turn on both hosts and store `attempt["host_error"] = {"name":..., "message":...}` when found.
  - Depends on: none
  - Expected outcome: run against the real session file `09-2j4pd0-attempt-1.jsonl` content (copied into a fixture), it returns `("ContentFilterError", "The response was blocked by the provider's content filter")`; against a clean session it returns nothing.
  - Execution state: pending

- [ ] E-03 Show `host_error` in the end-of-run summary (a short line under the table for each item that has one) and in `execution-report.md`'s per-item section, and include it in the `--agent` run record.
  - Depends on: E-02
  - Expected outcome: a scripted run whose host emits a content-filter error shows "2j4pd0: provider ContentFilterError: The response was blocked by the provider's content filter" in the summary and report.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add `tests/test_review_failure_reason.py` driving the real runner with a scripted host that (a) emits a content-filter error and exits 1 on a child review, (b) exits 1 silently on a child review, (c) exits 0 on an orchestrator whose readiness fails; assert the preserved-lane reason, the absence or presence of `review-orchestrator-failed`, `host_error`, and the summary text. No source introspection.
  - Depends on: E-01, E-03
  - Expected outcome: the module passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `handle_review_orchestrator_readiness` returns the incoming `disposition` unchanged when `exit_code != 0` or the plan is not an orchestrator; only its own refusal path returns `"fail-gate"` by decision.
- Scripted hosts: `tests/test_silent_turn_observability.py` `fake_opencode`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The child review failed on a provider content filter. | `sessions/09-2j4pd0-attempt-1.jsonl` last records: `"reason":"content-filter"` then `{"type":"error",...,"error":{"name":"ContentFilterError","data":{"message":"The response was blocked by the provider's content filter"}}}`. |
| F-02 | The run blamed orchestrator readiness. | Event `worktree-preserved` for `2j4pd0`: `"reason": "review orchestrator readiness failed; lane preserved for inspection"`, `"retention_reasons": ["review-orchestrator-failed"]`; `2j4pd0` is `- Kind: child`. |
| F-03 | The caller's test conflates "already failed" with "readiness refused". | `execute_item_core`: `if review_orch_disp == "fail-gate":` after `handle_review_orchestrator_readiness(..., disposition=disposition, exit_code=exit_code)`, whose first lines are `if exit_code != 0: return disposition`. |

## Proposed changes (ordered, validatable)

1. Correct reason selection (E-01).
2. Capture the host's error (E-02).
3. Surface it (E-03).
4. Tests (E-04).

## Deferred / out of scope (with reason)

- Retrying a review that failed on a provider error.
  - Carrier: ytas91

## Scope check

- Over-scope: none. `runner_shared.py` E-01, E-02; both hosts E-02; `render_stream.py` E-03; the test module E-04.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_review_failure_reason.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

N/A: no spec text names the preserved-lane reason; this changes a message and adds a recorded field.

## Open questions

### OQ-01: Should a content-filter error get its own disposition?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: No. Dispositions are a closed vocabulary (`runner_shutdown.KNOWN_ITEM_STATUSES`); the error is recorded as `host_error` and `ytas91`'s `turn_failure_kind` decides retry.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the preserved-lane events for the child-exit-1 and orchestrator-refused cases.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the parser's output on the content-filter fixture and on a clean session.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the summary line and the execution-report excerpt naming the host error.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the passing module run with per-test counts and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
