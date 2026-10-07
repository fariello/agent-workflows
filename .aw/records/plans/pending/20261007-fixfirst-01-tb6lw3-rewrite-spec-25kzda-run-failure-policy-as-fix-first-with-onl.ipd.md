# IPD: Rewrite spec 25kzda run failure policy as fix first, with only a corrupt ledger aborting a run

- Date: 2026-10-07
- Kind: child
- Concern: Spec `25kzda` tells the runner to give up on exactly the failures an agent fixes best. Section 5.5 lists push, hook bypass, unauthorized status change and out-of-scope mutation as "must never retry"; Section 5.7 says a hook refusal fails the item, a host failure retries "only when no ambiguous side effect exists", and push and hook bypass abort the run; Section 4.1 enumerates six run-abort classes. The maintainer ruled on 2026-10-07 that this is backwards for an isolated-worktree runner: aborting cannot undo a push, a hook bypass or a hand status edit lives only in the lane and is caught again at merge, and "ambiguous side effect" is not testable. The code already disagrees with the spec in both directions (F-03).
- Scope: Amend spec `25kzda` Sections 4.1, 5.5 and 5.7 to a fix-first policy, and update the `run_evidence` finding-code transcription the spec pins (`run_evidence.ABORT_CLASSES` and the affected `RunFindingCode.action` cells) so the byte-equality tests stay green. EXCLUDES all runner behavior changes (Orders 02 to 07), and EXCLUDES changing the retry budget's bound, default or precedence.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/run_evidence.py, tests/test_run_finding_abort_partition.py, tests/test_run_finding_spec_transcription.py, tests/test_retry_class_mapping.py
- Item-Dependencies: none
- Status: draft
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tb6lw3

## Workflow history

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The spec says what the maintainer wants: when the agent caused the failure, tell it what went wrong and let it fix it; stop one item only when a human or the runner itself must act; abort a run only when the runner cannot trust its own ledger.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: amend the spec

- [ ] E-01 Rewrite Section 5.5's two retry lists as three groups, in this order and with these members:
  (a) FIX-IT (agent-caused; a bounded correction turn naming what failed): host spawn failure; nonzero exit or no outcome file; stall or turn-limit expiry; missing expected artifact or failed deterministic check; missing or stale validation evidence; verifier transport failure; a hook refusal of any commit; a red combined suite after merge; an out-of-scope change (revert or justify); an unauthorized status change or plan move (undo, use the setter); a hook-bypass commit (undo, recommit through the hooks); a push (recorded, the agent is told, the run continues).
  (b) STOP THIS ITEM, NO FIX-IT TURN (a human or the runner must act; independent items continue): missing human approval; an agent proposal that a gate, tool or approach must change (Order 02); ownership or lease conflict; unknown or non-idempotent external outcome; identity or type ambiguity; fix-it budget exhausted.
  (c) ABORT THE RUN: corrupt run ledger only.
  DELETE the phrase "that did not create an ambiguous side effect" and do not replace it with another untestable qualifier.
  STATE THE ONE RULE FOR (a): the fix-it message tells the agent to fix the cause and not the gate, and that a gate or tool change is acceptable only when it is small and clearly a bug, with the reason recorded; otherwise the agent proposes it (Order 02, Order 03).
  - Depends on: none
  - Expected outcome: Section 5.5 carries the three groups with exactly these members, no "ambiguous side effect" wording remains anywhere in the spec, and the retry budget paragraph (bound 0 to 10, default 2, three-tier precedence) is byte-identical.
  - Execution state: pending

- [ ] E-02 Rewrite the Section 5.5 disposition mapping table so each fix-it class names the evidence the runner keys on (a disposition plus a marker, a finalize finding, an integration refusal kind) rather than the single token `failed-safely`, and so no row says a class is retryable through a path that cannot reach it (F-02). Mark each row with the Order in this Set that implements it.
  - Depends on: E-01
  - Expected outcome: every fix-it row names its evidence and its implementing Order; the never-retry rows for push, hook bypass, unauthorized status change and out-of-scope mutation are gone.
  - Execution state: pending

- [ ] E-03 Rewrite Section 5.7's response column to match E-01: hook refusal, out-of-scope mutation, unauthorized status change, hook-bypass attempt, push attempt and host/transport failure become "Fix-it turn naming what failed" (push: "Record, tell the agent, continue"); concurrent overlap and unknown external outcome become "Stop item; continue independent items"; corrupt ledger stays "Abort run". Rewrite Section 4.1's "Exhaustive `ABORT RUN` set" to the single class "Corrupt run ledger", and move the other five classes' rationale into a "Stop this item" paragraph, keeping the "reclassified" sentence only where it still holds.
  - Depends on: E-01
  - Expected outcome: Section 5.7 and 4.1 agree with 5.5 group (c): the abort set has one member.
  - Execution state: pending

- [ ] E-04 Record the amendment with `aw specs note` on the same file, naming the maintainer ruling of 2026-10-07 and this plan's id6. Do NOT run `aw specs set`; the spec stays `approved`.
  - Depends on: E-02, E-03
  - Expected outcome: one new dated workflow-history line; `- Status: approved` unchanged; `aw specs check` conforms.
  - Execution state: pending

### Task group 2: keep the pinned transcription true

- [ ] E-05 Update `agent_workflows/run_evidence.py` so `ABORT_CLASSES` holds only "Corrupt run ledger" and every `RunFindingCode.action` cell that names a removed abort class (at least `RUN-COMMIT-GATEWAY`'s "ABORT RUN for a hook-bypass attempt", and the "ABORT RUN only for identity/type ambiguity or ownership conflict" cells) matches the amended Section 4.2 table byte for byte. Update the transcription and partition tests only where they enumerate the old set, keeping them as behavior tests over the shipped table. Update `tests/test_retry_class_mapping.py` only where it asserts the old mapping table text.
  - Depends on: E-03
  - Expected outcome: `python3 -m pytest tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py tests/test_retry_class_mapping.py -o addopts=""` passes; no runner behavior changed (`git diff` touches no file outside Scope-Paths).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Spec 5.5 declares itself "the single normative home" for the retry budget; this plan changes the CLASSES, not the budget.
- `tests/test_run_finding_spec_transcription.py` asserts byte equality between spec Section 4.2 cells and `run_evidence.RUN_FINDING_CODES`, so editing a cell is a code change and both must move together.
- A spec edit is declared in `- Scope-Paths:` so both runners announce it before the run (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Section 5.5 lists out-of-scope mutation, unauthorized status change, hook bypass and push on the never-retry list; Section 5.7 says push and hook bypass abort the run, hook refusal fails the item, and host failure retries only "when no ambiguous side effect exists". | Spec `25kzda` Section 5.5 "It must never retry these classes regardless of budget"; Section 5.7 rows `hook_refused`, `hook_bypass_attempt`, `push_attempt`, `host_failure`. |
| F-02 | The 5.5 mapping table says host spawn failure and host nonzero exit are retryable through `turn_failure_is_retryable` on `failed-safely`, but no production path delivers that token to the predicate. | `runner_shared.TURN_RETRY_CLASSIFICATION`; `reconcile_disposition` rung 5 returns `fail-gate`; `oc_runipd` `except DriverError` sets `failed-safely` after `execute_item_core` has already returned (plan `p47qfu` F-12). |
| F-03 | The code disagrees with the spec in both directions: none of the six abort classes aborts a run; push, hook bypass and untooled status changes are not detected; out-of-scope edits are auto-justified and integrated. | `run_evidence.ABORT_CLASSES` is read only to validate the finding table; `runner_shared.compute_scope_reconciliation` writes "changed by the plan's approved execution (auto-reconciled by ...)" for every out-of-scope path; `RUN-COMMIT-GATEWAY` is `UNBOUND_BY_DEPENDENCY`. |
| F-04 | Section 4.1 makes the six classes "exhaustive" for aborting the whole queue, and `run_evidence.ABORT_CLASSES` transcribes them verbatim. | Spec Section 4.1 "Exhaustive `ABORT RUN` set"; `run_evidence.ABORT_CLASSES` docstring "Spec 4.1's EXHAUSTIVE abort-class set, verbatim". |
| F-05 | Maintainer ruling 2026-10-07: a push cannot be undone by aborting; a hook bypass or a hand status edit should be undone by the agent and redone with the proper tool; a hook refusal should go back to the agent; retrying only an unchanged worktree is the least useful case; "ambiguous side effect" is not reliably testable. | Session 2026-10-07; backlog `coivul`. |

## Proposed changes (ordered, validatable)

1. Three-group retry policy in 5.5 (E-01).
2. Evidence-keyed mapping table (E-02).
3. Matching 5.7 responses and a one-member 4.1 abort set (E-03).
4. Record the amendment (E-04).
5. Keep `run_evidence` and its tests byte-true to the spec (E-05).

## Deferred / out of scope (with reason)

- Implementing any of it. Orders 02 to 07 implement the classes; this plan changes only the contract and its pinned transcription, so code children are reviewed against the new contract.
  - Carrier: lxb1ew

## Scope check

- Over-scope: none. Each path is written by one E-item: the spec by E-01 to E-04, `run_evidence.py` and the three tests by E-05.
- Under-scope: Section 4.2 rows that only name a removed abort class in their action cell are covered by E-05; rows whose behavior changes are left to the implementing child.

## Required tests / validation

- `python3 -m pytest tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py tests/test_retry_class_mapping.py -o addopts=""`.
- Bare `python3 -m pytest`, with the baseline re-derived in the lane before any edit.
- `aw specs check` and `aw check` on the amended spec.

## Spec / documentation sync

THIS PLAN AMENDS AN APPROVED SPEC, declared in `- Scope-Paths:`. Why: the maintainer ruled the current never-retry and abort lists wrong for an isolated-worktree runner (F-05), and every other child in this Set implements the amended contract, so the contract must change first. The amendment widens what is retried and narrows what aborts; it does not change the budget.

## Open questions

### OQ-01: Should a push still stop the item rather than continue?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Resolved 2026-10-07: record it, tell the agent, continue. Aborting cannot recall a pushed commit, and detection is out of this Set (`denypush`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the amended Section 5.5 group lists; paste `grep -c "ambiguous side effect"` on the spec showing 0; paste a diff of the budget paragraph showing it unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the amended mapping table, showing each fix-it row's evidence and implementing Order.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the amended 5.7 rows for every changed class and the amended 4.1 abort set showing one member.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new workflow-history line, the spec's `- Status:` line, and `aw specs check` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing run of the three named test modules with per-test counts, `python3 -c "from agent_workflows import run_evidence; print(run_evidence.ABORT_CLASSES)"`, and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
