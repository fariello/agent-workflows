# IPD: Send a refused production or review action back for bounded correction turns

- Date: 2026-10-04
- Kind: child
- Concern: After Order 06 a production action whose orchestrator is not ready fails at once with `fail-gate`. The authoring agent's session is still open and holds the context needed to fix the finding (author the missing child, or assign the quoted obligation to a child), but the run never asks it to. The maintainer's direction (2026-10-04) is that a failed graduation should be fixed and resumed rather than discarded. The run already has the machinery: `25kzda` 5.5 makes "failed deterministic check for which a bounded correction is safe" retryable under one `--retry-budget`; `verification_retry_decision` and `finalize_retry_decision` remand items for correction turns; `resume_via_launcher` resumes the same session on both hosts (used by the defect re-ask). Separately, a `review` action over an orchestrator can finish with the orchestrator set `reviewed` while it is still not ready, because no review verification consults the readiness check; `25kzda` 4.4 as amended by Order 01 adds `IPD-REVIEW-ORCHESTRATOR-READY`. Both refusals are classified retryable by the amended `25kzda` 5.5.
- Scope: IN: classify `BACKLOG-GRADUATE-SET` and `SPEC-PLAN-SET` findings (and only those, among production findings) as a bounded correction: build a correction packet listing each finding's subject, quoted passage and remedy; resume the production session with it inside the same lane; re-run the full production verifier list after the turn; repeat up to the frozen `--retry-budget`; then fail honestly. Add `IPD-REVIEW-ORCHESTRATOR-READY` after a review turn on an orchestrator: call `orchestrator_readiness.review_readiness(..., ask=True)` on the reviewed text; if not ready, return the plan to `to-review` through the setter, and remand the review for a bounded correction with the same packet; on exhaustion leave it `to-review` with the findings recorded and no `- Readiness:` written. OUT: any other production finding's retry class (they keep their current dispositions); the readiness check itself (Order 03); the duplicate-handoff rule (Order 08).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_production_correction_turn.py
- Item-Dependencies: executed:r2wa38
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 7
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: nnsa2o

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 07 of Set `gradcover`. Implements `25kzda` 4.4 `IPD-REVIEW-ORCHESTRATOR-READY` and the 5.5 classification of the Set-level refusals as bounded corrections, both added by Order 01. Reuses the existing correction budget and session-resume path; adds no second retry knob.

## Goal

When the only thing wrong with a graduation or an orchestrator review is that the Set is not ready, hand the same agent session the exact quoted findings and let it fix them within the run's correction budget, so the common case ends in a handed-off Set rather than a failed item.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: production correction

- [ ] E-01 Add `production_set_retry_decision(item, state, findings, attempt_no)` mirroring `verification_retry_decision`: retryable only when EVERY finding's code is `BACKLOG-GRADUATE-SET` or `SPEC-PLAN-SET` (any other finding fails the item as today); budget is `frozen_retry_budget(state)`; a separate per-item counter and idempotency key so it does not consume the verification counter; returns retry, exhausted, reason, attempts, budget.
  - Depends on: none
  - Expected outcome: a findings list of only Set-level codes yields `retry=True` until the budget is spent, then `exhausted=True`; any mixed list yields `retry=False`.
  - Execution state: pending

- [ ] E-02 In both production branches of `execute_item_core`, when `production_set_retry_decision` says retry: write a correction prompt (through `write_prompt` with suffix `set-correction`) that lists, per not-ready orchestrator, each finding's subject, quoted passage and remedy, restates the rule that every whole-Set obligation names the child that performs it (a new child plan and table row for work no child performs, and never a deleted checklist), and instructs the agent to edit only plans in this Set; resume the production session in the SAME lane through `resume_via_launcher` (both host shapes, as the defect re-ask does); commit the turn's output through the existing production commit helper; and re-run the complete production verifier list. Loop until the verifiers pass or the decision is exhausted. On exhaustion, the existing `fail-gate` path applies with the last findings.
  - Depends on: E-01
  - Expected outcome: a scripted agent that fixes the finding on its first correction turn ends with the source `graduated`/`implementing`; one that never fixes it ends `fail-gate` after exactly `--retry-budget` correction turns, with every turn's findings recorded on its attempt.
  - Execution state: pending

### Task group 2: review correction

- [ ] E-03 After a `review` turn on an item whose plan is `- Kind: orchestrator` lands and the plan reads `reviewed`, call `orchestrator_readiness.review_readiness(repo, plan_path, ask=True, ...)`. If not ready, record `IPD-REVIEW-ORCHESTRATOR-READY` as the refusal code with the findings, return the plan to `to-review` with `aw ipd set to-review <id6> --message "<findings summary>"` (a legal backward edge), and remand the review through the same retry decision shape (its own counter) with a correction packet built the same way as E-02. On exhaustion, leave the plan `to-review`, record the findings, and do not write `- Readiness:` (spec `r07vma` R6).
  - Depends on: E-02
  - Expected outcome: a review whose scripted agent sets an unready orchestrator `reviewed` ends with the plan `to-review` and the refusal recorded; one that fixes the finding on correction ends `reviewed` with a pass verdict recorded.
  - Execution state: pending

- [ ] E-04 Record every correction turn durably: append to the item's `attempts[]` the correction key, the findings it was given, and the findings after it; emit `production-set-correction` / `review-orchestrator-correction` events with the counts; make the end-of-run summary name the item and the number of correction turns spent.
  - Depends on: E-03
  - Expected outcome: `aw runs` and the run summary show, for a corrected item, how many correction turns it took, and for an exhausted one, the last findings.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_production_correction_turn.py` using the fake-host production fixtures of `tests/test_backlog_production.py` with a scripted session that can be resumed: fixed on the first correction (source `graduated`, one correction turn recorded); never fixed with `--retry-budget 2` (two correction turns, then `fail-gate`, item `open`); budget 0 (no correction turn, immediate `fail-gate`); a mixed finding list (no correction turn); the spec twin of the first case; the review twin of the first and second cases; and a check that the correction prompt contains each quoted passage and the "never delete the checklist" sentence. Prove the tests can fail by making the retry decision always return `retry=False` and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation fails it; existing production and retry tests still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE RETRY BUDGET. `25kzda` 5.5 is "the single normative home" of the 0..10 bound and its three-tier precedence; `frozen_retry_budget(state)` reads the frozen value; no second flag may be added.
- SESSION RESUME IS SHARED. `resume_via_launcher` is how the defect re-ask resumes the same session on both hosts, with the oc shape (`resume_session=`) and the agy shape differing only in argument layout; reuse it.
- A CORRECTION PACKET CARRIES ONLY WHAT FAILED (`turn_correction_packet` docstring): no plan body, no full task re-send.
- `- Readiness:` IS AN OUTPUT OF `/plan-review` ONLY (`AGENTS.md`, "NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD"); on exhaustion it stays absent.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Production failure is terminal today. Both production branches' `if findings:` set `disposition = "fail-gate"` and preserve the lane; no retry decision is consulted. | the two `if findings:` blocks in `execute_item_core` |
| F-02 | The same-session resume exists and is host-neutral. The defect re-ask path calls `resume_via_launcher(raw_launcher, ..., {"resume_session": reask_session, ...})` for oc and the agy shape otherwise, gated on a recorded `session_id`. | the defect re-ask block in `execute_item_core` |
| F-03 | Review verification never consults readiness. After a review turn the runner commits the review output (`commit_review_shared_output` or the lane integration) and classifies writes (`classify_review_writes`); no step reads the orchestrator's child table or the verdict store. | the review branches in `execute_item_core` |
| F-04 | The correction budget default is 2 (`run_recovery.DEFAULT_RETRY_LIMIT`, recorded in `enforce_orchestrator_probe_gate`'s docstring), so with defaults a graduation gets at most two correction turns. | `resolve_retry_budget`; the docstring note |

## Proposed changes (ordered, validatable)

1. Add a production Set-level retry decision on the shared budget with its own counter (E-01).
2. Loop production correction turns in the same lane and session, re-verifying fully each time (E-02).
3. Add the post-review readiness check, the backward transition, and its correction loop (E-03).
4. Record and report correction turns (E-04).
5. Tests and mutation proof (E-05).

## Deferred / out of scope (with reason)

- RETRYING OTHER PRODUCTION FINDINGS (missing `From-Backlog`, lint failures). They may also be safe to correct, but no incident measured them failing; widening the class is a separate decision.
  - Carrier-Declined: no measured defect; this plan widens only the class the 2026-10-03 incident exercised
- CONTINUING A HANDOFF IN A LATER RUN after exhaustion. Order 08.
  - Carrier: 24qw39

## Scope check

- Over-scope: none. One production module and one test file.
- Under-scope: an exhausted graduation still leaves the work in a preserved lane; recovering it in a later run is Order 08.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_production_correction_turn.py tests/test_production_set_check.py tests/test_backlog_production.py tests/test_spec_production.py -q` pasted.
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements `25kzda` 4.4 (`IPD-REVIEW-ORCHESTRATOR-READY`) and 5.5 (classification) as amended by Order 01. The 5.5 class-to-surface table is extended by Order 01's prose; if the executor finds that table must also gain a row for consistency, that edit is a spec change NOT declared here and must be raised as a scope reason at finalize, not made silently.

## Open questions

### OQ-01: Should the correction turn resume the same session or start a fresh one?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: resume the same session when one was recorded, start a fresh turn in the same lane otherwise. The same session holds the agent's understanding of why it structured the Set as it did, which is exactly what is needed to decide whether a quoted obligation belongs to an existing child or a new one. The defect re-ask path already makes this choice and gates on a recorded `session_id`.

### OQ-02: On review exhaustion, should the orchestrator go back to `to-review` or stay `reviewed`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: `to-review`. Leaving it `reviewed` would record a readiness claim the check refused, which Order 05 now forbids anyway. `reviewed -> to-review` is a legal backward edge (`ipd_lifecycle._LEGAL_BACKWARD_EDGES`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the new function and test output for: Set-only findings under budget (retry), at budget (exhausted), mixed findings (no retry), repeated key (no spend).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of both production branches. Paste the fixed-on-first-correction case's final source status and attempt record (one correction), and the never-fixed case's correction count (equal to the budget) and final `fail-gate` with the item `open`. Paste one written correction prompt showing each quoted passage and the never-delete sentence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the review path. Paste the review case's final plan status (`to-review` on exhaustion, `reviewed` when fixed), the recorded `IPD-REVIEW-ORCHESTRATOR-READY` refusal, and a grep of the plan file showing no `- Readiness:` written on exhaustion.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the events emitted for a corrected item and the run summary line naming the correction count.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new file passing with its count and the existing production test files passing; the mutation failing and the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
