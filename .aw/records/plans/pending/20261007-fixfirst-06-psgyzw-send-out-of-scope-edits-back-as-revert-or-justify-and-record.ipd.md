# IPD: Send out-of-scope edits back as revert-or-justify and record kept ones as Scope-Exceeded

- Date: 2026-10-07
- Kind: child
- Concern: When an executing agent changes a path outside its plan's `- Scope-Paths:`, the RUNNER writes the justification for it: `runner_shared.compute_scope_reconciliation` builds "changed by the plan's approved execution (auto-reconciled by <host>)" for every out-of-scope path, and `driver_finalize` passes each as `--scope-reason`, so finalize accepts and the lane is merged. The reason on record is therefore the runner's boilerplate, not the agent's judgement, and nothing marks the plan as having gone outside its scope, so the maintainer cannot track or analyse how often it happens. The maintainer ruled on 2026-10-07: send it back, let the agent revert or justify with a real reason, and flag kept edits in the artifact's metadata.
- Scope: Stop auto-writing out-of-scope reasons; send an unjustified out-of-scope delta back to the agent as a fix-it turn ("revert X, or justify it"), accepting the agent's own `aw commit --scope-reason` reasons already recorded in the begin receipt; record every kept out-of-scope path and its reason in a new recognized plan field `- Scope-Exceeded:` written by finalize; amend the IPD structure spec to recognize the field. KEEP the additive-widening reasons and the declared-but-unmodified acks as they are (both describe declared paths, not out-of-scope edits). EXCLUDES review-turn out-of-scope warnings, and any absolute ban on editing gate code (Order 03's message carries the judgement rule).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_schema.py, tests/test_scope_exceeded.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: executed:mcbph5
- Status: draft
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 6
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: psgyzw

## Workflow history

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

An agent that edits outside its plan's scope is asked to revert or justify, writes its own reason, and the executed plan says plainly that it exceeded its scope, which paths, and why, so these cases can be found and analysed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: stop writing the agent's reasons for it

- [ ] E-01 In `compute_scope_reconciliation`, stop generating a reason for an out-of-scope path. Use only reasons the agent recorded (`ipd_lifecycle.read_scope_reasons`, populated by `aw commit --scope-reason`). Keep the widening reasons and the declared-but-unmodified acks unchanged. Return the unjustified out-of-scope paths separately.
  - Depends on: none
  - Expected outcome: for a lane with one justified and one unjustified out-of-scope path, the function returns the agent's reason for the first and lists the second as unjustified; widened and unmodified paths are handled exactly as before.
  - Execution state: pending

- [ ] E-02 When unjustified out-of-scope paths remain at finalize, send the item back with Order 03's message (kind `out-of-scope`), listing each path and the two ways to answer: revert it, or keep it and record why with `aw commit <plan> --scope-reason <path>=<why> -- <path>`. Admit this refusal in `finalize_refusal_is_retryable` as its own arm. On budget exhaustion the item fails as today.
  - Depends on: E-01
  - Expected outcome: a lane with an unjustified out-of-scope edit gets one fix-it turn naming the path; after the agent justifies it, finalize accepts.
  - Execution state: pending

### Task group 2: record what was kept

- [ ] E-03 Add `Scope-Exceeded` to `ipd_schema`'s recognized-but-optional fields (the same pattern as `META_FROM_SPEC`). Have finalize write `- Scope-Exceeded: <path> (<reason>); ...` into the plan's metadata block when one or more out-of-scope paths were kept, and nothing otherwise. Keep the existing "Scope reconciliation - out-of-scope ..." history note.
  - Depends on: E-01
  - Expected outcome: an executed plan that kept an out-of-scope path carries the field with the path and the agent's reason; one that did not carries no field; `aw ipd lint` accepts both.
  - Execution state: pending

- [ ] E-04 Amend spec `ipd-structure-and-linting` Section 4.4 to list `Scope-Exceeded` as recognized-but-optional, written only by finalize, never hand-written, with its value grammar. Add a dated amendment note in the spec's style.
  - Depends on: E-03
  - Expected outcome: Section 4.4 names the field; `aw check` reports no new finding on the spec.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_scope_exceeded.py` driving finalize and the runner on a scratch repo for: unjustified edit then fix-it then justified (field written with the agent's reason); edit reverted on the fix-it turn (no field); widened path (unchanged behavior, no field); `aw ipd lint` accepting the field and `aw find plans` locating a plan by it. No source introspection.
  - Depends on: E-02, E-04
  - Expected outcome: the module passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- A new recognized field goes in `ipd_schema` beside `META_FROM_SPEC`, so `IPD-M103` does not flag it, and value validation lives in `aw check`, not the schema.
- A spec edit is declared in `- Scope-Paths:` (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The runner writes the out-of-scope reasons itself. | `compute_scope_reconciliation`: `reasons = {p: f"changed by the plan's approved execution (auto-reconciled by {labels.command})" for p in out_of_scope}`; `driver_finalize` appends each as `--scope-reason`. |
| F-02 | Agents already have a way to record their own reason. | `aw commit --scope-reason PATH=WHY` "records it in the begin receipt for finalize to consume"; `ipd_lifecycle.record_scope_reasons` / `read_scope_reasons`. |
| F-03 | No metadata marks a plan that exceeded its scope; the only trace is a history note. | `ipd_lifecycle._reconciliation_history_note` renders "Scope reconciliation - out-of-scope ..." into workflow history. |
| F-04 | Maintainer ruling 2026-10-07: send it back, trust the agent's judgement with a good reason, and flag it in metadata for tracking. | Session 2026-10-07. |

## Proposed changes (ordered, validatable)

1. Use only the agent's reasons (E-01).
2. Send unjustified edits back (E-02).
3. `- Scope-Exceeded:` written by finalize (E-03).
4. Spec recognizes the field (E-04).
5. Tests (E-05).

## Deferred / out of scope (with reason)

- A report over all plans' `Scope-Exceeded` values. `aw find` / `aw attention` can already filter on metadata; a dedicated report can follow once there is data.
  - Carrier-Declined: no defect is deferred; the field is the deliverable and is queryable with existing verbs.

## Scope check

- Over-scope: none. `runner_shared.py` E-01, E-02; `ipd_lifecycle.py` E-02, E-03; `ipd_schema.py` E-03; the spec E-04; the test module E-05.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_scope_exceeded.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.
- `aw ipd lint` on a plan carrying the field.

## Spec / documentation sync

THIS PLAN AMENDS spec `ipd-structure-and-linting` (implemented, legacy-named, no `- Id:`), declared in `- Scope-Paths:`, because it adds a recognized metadata field and the spec's Section 4.4 is the list of recognized fields. The amendment adds one field and changes nothing else.

## Open questions

### OQ-01: Should the field be a list of paths or a yes/no flag?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: Paths with reasons. The maintainer wants to "track these things and analyze them", which needs what and why, not only whether.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a `python3 -c` session showing the function's output for the justified, unjustified, widened and unmodified cases.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the delivered fix-it prompt naming the path and the finalize result after the agent justified it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the executed plan's metadata block showing `- Scope-Exceeded:`, and `aw ipd lint` on it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the spec diff and `aw check` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing module run with per-test counts and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
