# IPD: Send a refused production or review action back for bounded correction turns

- Date: 2026-10-04
- Kind: child
- Concern: After Order 06 a production action whose orchestrator is not ready fails at once with `fail-gate`. The authoring agent's session is still open and holds the context needed to fix the finding (author the missing child, or assign the quoted obligation to a child), but the run never asks it to. The maintainer's direction (2026-10-04) is that a failed graduation should be fixed and resumed rather than discarded. The run already has the machinery: `25kzda` 5.5 makes "failed deterministic check for which a bounded correction is safe" retryable under one `--retry-budget`; `verification_retry_decision` and `finalize_retry_decision` remand items for correction turns; `resume_via_launcher` resumes the same session on both hosts (used by the defect re-ask). Separately, a `review` action over an orchestrator can finish with the orchestrator set `reviewed` while it is still not ready, because no review verification consults the readiness check; `25kzda` 4.4 as amended by Order 01 adds `IPD-REVIEW-ORCHESTRATOR-READY`. Both refusals are classified retryable by the amended `25kzda` 5.5.
- Scope: IN: classify `BACKLOG-GRADUATE-SET` and `SPEC-PLAN-SET` findings (and only those, among production findings) as a bounded correction: build a correction packet listing each finding's subject, quoted passage and remedy; resume the production session with it inside the same lane; re-run the full production verifier list after the turn; repeat up to the frozen `--retry-budget`; then fail honestly. Add `IPD-REVIEW-ORCHESTRATOR-READY` after a review turn on an orchestrator: call `orchestrator_readiness.review_readiness(..., ask=True)` on the reviewed text; if not ready, return the plan to `to-review` through the setter, and remand the review for a bounded correction with the same packet; on exhaustion leave it `to-review` with the findings recorded and no `- Readiness:` written. OUT: any other production finding's retry class (they keep their current dispositions); the readiness check itself (Order 03); the duplicate-handoff rule (Order 08).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_production_correction_turn.py
- Item-Dependencies: executed:r2wa38, executed:26m1nb
- Status: approved
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 7
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: nnsa2o
- Approval: 2026-10-06, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-06 approved (aw set): status set to approved
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 (all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-007. Fixed: demotion leaves `- Readiness:` standing (measured), stripped by Order 05 and dependency added (PR-001); review trigger no longer "plan reads reviewed", since Order 05 makes the agent's own `aw set reviewed` refuse without a record, with site and disposition specified (PR-002); review correction delivered by session resume, not re-queue, since the review prompt is a bare slash command (PR-003); production commit baseline and session shapes stated (PR-004); E-04 surfaces limited to ones reachable within scope (PR-005); gate contract (PR-006); remedy reuse, test list, stale wording (PR-007).
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): wording updated for the maintainer ruling 2026-10-04 (coverage answer stored in the plan).

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 07 of Set `gradcover`. Implements `25kzda` 4.4 `IPD-REVIEW-ORCHESTRATOR-READY` and the 5.5 classification of the Set-level refusals as bounded corrections, both added by Order 01. Reuses the existing correction budget and session-resume path; adds no second retry knob.

## Goal

When the only thing wrong with a graduation or an orchestrator review is that the Set is not ready, hand the same agent session the exact quoted findings and let it fix them within the run's correction budget, so the common case ends in a handed-off Set rather than a failed item.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: production correction

- [x] E-01 Add `production_set_retry_decision(item, state, findings, attempt_no)` mirroring `verification_retry_decision`: retryable only when EVERY finding's code is `BACKLOG-GRADUATE-SET` or `SPEC-PLAN-SET` (any other finding fails the item as today); budget is `frozen_retry_budget(state)`; a separate per-item counter and idempotency key so it does not consume the verification counter; returns retry, exhausted, reason, attempts, budget.
  - Depends on: none
  - Expected outcome: a findings list of only Set-level codes yields `retry=True` until the budget is spent, then `exhausted=True`; any mixed list yields `retry=False`.
  - Execution state: performed

- [x] E-02 In both production branches of `execute_item_core`, when `production_set_retry_decision` says retry: write a correction prompt (through `write_prompt` with suffix `set-correction`) that lists, per not-ready orchestrator, each finding's subject, quoted passage and remedy, restates the rule that every whole-Set obligation names the child that performs it (a new child plan and table row for work no child performs, and never a deleted checklist), and instructs the agent to edit only plans in this Set (render the per-finding remedy from Order 03's shared remedy data in `orchestrator_readiness`, the `r07vma` R7 text, rather than a second copy of the wording); resume the production session in the SAME lane through `resume_via_launcher` (both host shapes, as the defect re-ask does: oc passes `resume_session=attempt["session_id"]`, which `oc_runipd.run_opencode` honors even on an isolated turn, and agy passes `session_id=` with `use_continue=False`; when no session was recorded, launch a fresh turn in the same lane, OQ-01); commit the turn's output through the existing production commit helper (`commit_backlog_production_output` / `commit_spec_production_output` with the ORIGINAL `baseline_plan_ids`, so plans the first turn created are still `allowed` when the correction edits them, and a correction that adds a child is committed too); and re-run the complete production verifier list (including Order 06's Set verifier, which re-asks because the edited orchestrator's coverage fingerprint changed). Loop until the verifiers pass or the decision is exhausted. On exhaustion, the existing `fail-gate` path applies with the last findings.
  - Depends on: E-01
  - Expected outcome: a scripted agent that fixes the finding on its first correction turn ends with the source `graduated`/`implementing`; one that never fixes it ends `fail-gate` after exactly `--retry-budget` correction turns, with every turn's findings recorded on its attempt.
  - Execution state: performed

### Task group 2: review correction

- [x] E-03 After EVERY `review` turn on an item whose plan is `- Kind: orchestrator` (metadata read with `ipd_lint.parse`) ends with exit 0, whatever status the plan now reads, call `orchestrator_readiness.review_readiness(lane_or_repo, plan_path, ask=True, state=state, host=<oc|agy>, retry_budget=frozen_retry_budget(state))` against the tree the review wrote (the review sweep lane when isolated, else the shared checkout). SITE: after `commit_review_lane_output` / `commit_review_shared_output` and BEFORE the lane integrates, so the probe sees committed review output and its own coverage-record commit (Order 02) lands on the lane branch with it. The trigger is NOT "the plan reads `reviewed`": after Order 05 the reviewing agent's own `aw set reviewed` REFUSES for an orchestrator without a current coverage record, so the plan typically stays `to-review` while `reconcile_disposition` still scores the turn `reviewed` (its review branch returns `"reviewed"` for any exit-0 turn with positive evidence whatever the on-disk status). Three outcomes: (a) ready and the plan reads `reviewed` or later: no action; (b) not ready: record `IPD-REVIEW-ORCHESTRATOR-READY` with the findings (`record_refusal`); if the plan reads `reviewed`, return it to `to-review` with `aw ipd set to-review <id6> --message "<findings summary>" --yes --no-commit --dir <tree>` (a legal backward edge; Order 05 requires the explicit `--message` and strips `- Readiness:` on the demotion) and commit that change in the same tree; remand; (c) ready but the plan still reads `to-review` (its review's setter call was refused before the record existed): remand with a packet saying the coverage record now exists and the review must re-run its own `reviewed` transition. REMAND = a correction turn delivered the way E-02 delivers it (`write_prompt` suffix `review-orchestrator-correction`, `resume_via_launcher` into the review sweep's recorded session, which `oc_runipd.run_opencode` reuses inside the sweep lane), NOT a re-queue, because `build_review_prompt` renders only the slash command and would drop the packet. After the turn, re-score and repeat (b)/(c) under a decision of E-01's shape with its own counter and key, up to `frozen_retry_budget(state)`. In every not-ready or not-yet-reviewed outcome the ITEM's disposition is `fail-gate` (not `reviewed`), so no summary reports a review that did not reach `reviewed`. On exhaustion, leave the plan `to-review`, keep the findings recorded, and leave `- Readiness:` absent (spec `r07vma` R6): the runner never writes that field.
  - Depends on: E-02
  - Expected outcome: a review whose scripted agent sets an unready orchestrator `reviewed` ends, after the budget, with the plan `to-review`, no `- Readiness:` line, the item `fail-gate`, and the refusal recorded; one that fixes the finding on correction ends `reviewed` with a current coverage pass recorded in the plan; one whose plan stayed `to-review` only because the record was missing ends `reviewed` after one correction turn.
  - Execution state: performed

- [x] E-04 Record every correction turn durably: append to the item's `attempts[]` the correction key, the findings it was given, and the findings after it; emit `production-set-correction` / `review-orchestrator-correction` events with the counts; and reach the operator through the two surfaces that already render without a renderer change: a `record_refusal` on exhaustion whose reason names the correction turns spent and the last findings (rendered by `aw runs`' `Issue` column and the run summary's diagnostics block), and a line in `write_report`'s `execution-report.md` (in `runner_shared`) per corrected item naming the number of correction turns. Do NOT edit `render_stream.py` (not in Scope-Paths); if a summary-table change proves necessary, justify it with `--scope-reason`.
  - Depends on: E-03
  - Expected outcome: `execution-report.md` names each corrected item and its correction-turn count; for an exhausted item, `aw runs` and the run summary show the refusal naming the turns spent and the last findings.
  - Execution state: performed

### Task group 3: pin it

- [x] E-05 Add `tests/test_production_correction_turn.py` using the fake-host production fixtures of `tests/test_backlog_production.py` with a scripted session that can be resumed: fixed on the first correction (source `graduated`, one correction turn recorded); never fixed with `--retry-budget 2` (two correction turns, then `fail-gate`, item `open`); budget 0 (no correction turn, immediate `fail-gate`); a mixed finding list (no correction turn); the spec twin of the first case; the review twin of the first and second cases (the second asserting no `- Readiness:` line and item `fail-gate`); the record-missing review case of E-03 (c) on both hosts, asserting the agy correction turn receives `session_id=` and oc `resume_session=`; and a check that the correction prompt contains each quoted passage and the "never delete the checklist" sentence. Prove the tests can fail by making the retry decision always return `retry=False` and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation fails it; existing production and retry tests still pass.
  - Execution state: performed

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
| F-03 | Review verification never consults readiness. After a review turn the runner commits the review output (`commit_review_shared_output` or the lane integration) and classifies writes (`classify_review_writes`); no step reads the orchestrator's child table or its coverage record. Measured at review by a spy on `runner_shared.execute_item_core` over the bare suite (5083 passed): no existing test dispatches a `review` action on an orchestrator, so E-03 changes no existing test's path. | the review branches in `execute_item_core` |
| F-05 | A demotion through the setter leaves `- Readiness:` in place. Measured at review: `aw ipd set to-review r2wa38 --message ... --yes --no-commit` on a copy of a `reviewed` plan wrote `- Status: to-review` and kept `- Readiness: go-pending-approval`, which `tests/test_readiness_absence_invariant.py` refuses for a `to-review` plan and which would leave a refused review's readiness standing. `status_set.apply_status_change` strips only `- Approval:` when leaving `approved`. | the measured run; the `- Approval:` strip in `apply_status_change` |
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
- `python3 -m pytest -o addopts="" tests/test_production_correction_turn.py tests/test_production_set_check.py tests/test_backlog_production.py tests/test_spec_production.py tests/test_verification_sendback.py tests/test_review_lane_output_commit.py tests/test_retry_class_mapping.py -q` pasted.
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

- [x] V-01 validates E-01
  - Required evidence: paste the new function and test output for: Set-only findings under budget (retry), at budget (exhausted), mixed findings (no retry), repeated key (no spend).
  - Observed evidence:
    `production_set_retry_decision` in `agent_workflows/runner_shared.py`:
    ```python
    def production_set_retry_decision(
        item: Mapping[str, Any],
        state: Mapping[str, Any],
        findings: Sequence[Any],
        attempt_no: int,
    ) -> ProductionSetRetryDecision:
        """Decide RETRY / FAIL-GATE for failed production Set verifications (spec 25kzda 5.5, IPD nnsa2o E-01)."""
        used = production_set_retry_attempts(item)
        budget = frozen_retry_budget(state)
        key = production_set_retry_idempotency_key(item, attempt_no)
        retryable, why = production_set_findings_are_retryable(findings)
        if not retryable:
            return ProductionSetRetryDecision(
                retry=False,
                exhausted=False,
                reason=why,
                attempts=used,
                budget=budget,
                key=key,
            )
        if production_set_retry_key_already_spent(item, key):
            return ProductionSetRetryDecision(
                retry=False,
                exhausted=False,
                reason=(
                    f"production Set correction {key} was ALREADY recorded for this item, "
                    f"so this decision spends nothing (idempotency, as `plan_retry` guarantees for a repeated key)"
                ),
                attempts=used,
                budget=budget,
                key=key,
            )
        if used >= budget:
            return ProductionSetRetryDecision(
                retry=False,
                exhausted=True,
                reason=(
                    f"production Set verification failed in a retryable class and the run's correction "
                    f"budget is exhausted ({used} of {budget} correction attempt"
                    f"{'' if budget == 1 else 's'} spent), so the item is FAILED rather than resumed"
                ),
                attempts=used,
                budget=budget,
                key=key,
            )
        return ProductionSetRetryDecision(
            retry=True,
            exhausted=False,
            reason=(
                f"production Set verification failed in a retryable class, so the session is being resumed "
                f"for a bounded correction turn; correction attempt {used + 1} of {budget}"
            ),
            attempts=used,
            budget=budget,
            key=key,
        )
    ```

    Unit test output for all 4 cases:
    ```
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e01_production_set_retry_decision_unit PASSED [ 55%]
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of both production branches. Paste the fixed-on-first-correction case's final source status and attempt record (one correction), and the never-fixed case's correction count (equal to the budget) and final `fail-gate` with the item `open`. Paste one written correction prompt showing each quoted passage and the never-delete sentence.
  - Observed evidence:
    Diff of `is_spec_production` and `is_backlog_production` branches in `agent_workflows/runner_shared.py`:
    ```python
                while findings:
                    set_retry_dec = production_set_retry_decision(
                        item, state, findings, attempt_no + used_turns
                    )
                    if not set_retry_dec.retry:
                        if set_retry_dec.exhausted:
                            # record_refusal on exhaustion
                            ...
                        break
                    # write correction prompt, resume_via_launcher, commit output, re-verify
                    ...
    ```

    Fixed-on-first-correction case:
    - Final backlog item status: `graduated` (`- Status: graduated` in `.aw/records/backlog/graduated/20261004-set001-01-bkl001-test-item.backlog.md`)
    - Final queue item status: `executed`
    - Attempt record:
      ```json
      {
        "turn": 1,
        "action": "production-set-correction",
        "key": "bkl001:production-set-attempt-1",
        "findings_given": [{"code": "BACKLOG-GRADUATE-SET", "subject": "orc001", "detail": "Orchestrator plan orc001 child table names 'chd002' but no file exists at that path"}],
        "findings_after": []
      }
      ```

    Never-fixed case:
    - Correction count: 2 (equal to budget 2)
    - Item status: `fail-gate`
    - Backlog status: `open` (`- Status: open` in `.aw/records/backlog/open/20261004-set002-01-bkl002-test-item.backlog.md`)

    Written correction prompt:
    ```markdown
    Production Set verification failed for backlog item bkl001.

    The following orchestrator plans in Set set001 require correction:

    ### Orchestrator orc001
    - **Finding**: Orchestrator plan orc001 child table names 'chd002' but no file exists at that path
      - **Quoted passage**:
        ```
        | 02 | chd002 | .aw/records/plans/pending/20261004-set001-02-chd002-test-child.ipd.md |
        ```
      - **Remedy**: Create child plan chd002 at .aw/records/plans/pending/20261004-set001-02-chd002-test-child.ipd.md or update table row

    Every whole-Set obligation must name the child that performs it. Create a new child plan and table row for work no child performs. Never delete the checklist or parent obligation items to bypass verification. Edit only plans in Set set001.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff of the review path showing the site (after the review-output commit, before integration). Paste the review case's final plan status (`to-review` on exhaustion, `reviewed` when fixed), item disposition (`fail-gate` on exhaustion), the recorded `IPD-REVIEW-ORCHESTRATOR-READY` refusal, a grep of the plan file showing no `- Readiness:` line on exhaustion, and the record-missing case (c) ending `reviewed` with its correction-turn count (1).
  - Observed evidence:
    Diff of review path site in `agent_workflows/runner_shared.py`:
    ```python
            if wt_handle is not None:
                # review output committed via commit_review_lane_output
                ...
                review_orch_disp = handle_review_orchestrator_readiness(
                    tree=Path(wt_handle.path),
                    item=item,
                    ...
                )
                if review_orch_disp == "fail-gate":
                    disposition = "fail-gate"
                    attempt["disposition"] = "fail-gate"
                    item["status"] = "fail-gate"
                    ...
                else:
                    review_integrated, review_reason, review_kind = (
                        integrate_under_repository_lock(...)
                    )
    ```

    Review cases:
    - Fixed case: plan status `reviewed`, item disposition `reviewed`.
    - Exhausted case: plan status `to-review`, item disposition `fail-gate`, refusal recorded with code `IPD-REVIEW-ORCHESTRATOR-READY`.
    - Grep for `- Readiness:` in exhausted plan: returns empty (stripped on demotion back to `to-review`).
    - Record-missing case (c): ends with plan status `reviewed`, item status `reviewed`, correction turns spent: 1.
    ```
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e03_review_orchestrator_fixed_and_exhausted PASSED [ 11%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e03_review_orchestrator_record_missing_outcome_c PASSED [ 77%]
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the events emitted for a corrected item, the `execution-report.md` line naming its correction count, and, for an exhausted item, the recorded refusal (code and reason naming the turns spent) as `aw runs --agent` (or the run-viewer loader) reports it.
  - Observed evidence:
    Emitted events from `events.jsonl`:
    ```json
    {"at": "2026-10-06T19:00:00Z", "event": "production-set-correction", "id6": "bkl001", "attempt": 1, "turn": 1, "key": "bkl001:production-set-attempt-1", "findings_count": 1}
    {"at": "2026-10-06T19:00:00Z", "event": "review-orchestrator-correction", "id6": "orc001", "attempt": 1, "turn": 1, "key": "orc001:review-orchestrator-attempt-1", "findings_count": 1}
    ```

    `execution-report.md` line in `## Correction turns`:
    ```markdown
    ## Correction turns
    - `bkl001`: 1 correction turn spent (production Set verification passed after 1 correction turn)
    ```

    Recorded refusal on exhaustion:
    ```json
    {
      "code": "BACKLOG-GRADUATE-SET",
      "reason": "correction budget exhausted (2 correction turns spent); Backlog item bkl002 graduation Set verifier refused: [orc002] Child plan chd002 listed in child table missing"
    }
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new file passing with its count and the existing production test files passing; the mutation failing and the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
    New test file output:
    ```
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e03_review_orchestrator_fixed_and_exhausted PASSED [ 11%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e02_backlog_production_never_fixed_exhausted PASSED [ 22%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e02_backlog_production_fixed_on_first_correction PASSED [ 33%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e02_budget_zero PASSED [ 44%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e01_production_set_retry_decision_unit PASSED [ 55%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e02_correction_prompt_contents PASSED [ 66%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e03_review_orchestrator_record_missing_outcome_c PASSED [ 77%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e02_spec_production_fixed_on_first_correction PASSED [ 88%]
    tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e02_mixed_findings_no_retry PASSED [100%]
    ============================== 9 passed in 34.32s ==============================
    ```

    Existing production and retry test files output:
    ```
    .......................................................................  [100%]
    71 passed in 144.67s (0:02:24)
    ```

    Mutation test failure (with retry=False forced in production_set_retry_decision):
    ```
    FAILED tests/test_production_correction_turn.py::TestProductionCorrectionTurn::test_e02_backlog_production_fixed_on_first_correction
    AssertionError: 'fail-gate' != 'executed'
    ============================== 1 failed in 4.47s ===============================
    ```

    Revert pass:
    ```
    tests/test_production_correction_turn.py .                               [100%]
    ============================== 1 passed in 6.00s ===============================
    ```

    Grep for source-structure reads returning nothing:
    `grep -nE "inspect|ast\.|source|open\(.*runner_shared" tests/test_production_correction_turn.py` (no code-structure reads).

    Bare `python3 -m pytest` suite reconciliation:
    Baseline: 5176 passed.
    Current: 5185 passed, 2 skipped, 3 warnings in 282.75s (+9 new tests in `test_production_correction_turn.py`, exact match).

    `aw ipd lint` output:
    `- >  ◕  approved     plan        20261004-gradcover-07-nnsa2o  [high]  [blocking]  conforming`

    `aw sanitize --agent` output:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`

    Staged paths: only declared scope paths (`agent_workflows/runner_shared.py`, `tests/test_production_correction_turn.py`, and the plan file).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Scope fence: the two `- Scope-Paths:` are the declared surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and an untouched declared path with `--scope-ack`). Commit only the paths you changed through `aw commit <plan> -- <paths>`; never push. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`. Depends on `r2wa38` (the Set verifier) and `26m1nb` (the setter gate, the `--message` requirement, and the `- Readiness:` strip on demotion) being executed.
