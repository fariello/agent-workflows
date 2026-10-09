# IPD: Give fix-it turns for hook refusals and a red suite at finalize and merge

- Date: 2026-10-07
- Kind: child
- Concern: Three refusals the agent can fix fail the item on the first occurrence. (1) A pre-commit hook refusing the finalize commit (`ipd_lifecycle._CommitRefused`, surfaced as `EXIT_CANNOT_RUN` with "lifecycle commit did not happen (git rc=1: the lifecycle commit was rejected in the coordinator worktree (hooks ran): ...)") matches neither arm of `runner_shared.finalize_refusal_is_retryable`, so it is preserved and reported. (2) A hook refusing an integration commit is either returned UNTAGGED as `INTEGRATION_REFUSAL_CONFLICT` (the records re-derive and history auto-resolve arms) or, for the main merge itself, MIS-TAGGED `INTEGRATION_CAUSE_GIT_CONFLICT` with the false verdict "BOTH SIDES CHANGED THE SAME REGION" (measured at review), and the merge-conflict send-back loop then re-publishes without ever asking the agent. (3) A red combined suite after merging the lane with current main (`INTEGRATION_CAUSE_GATE_COMBINED_RED`) is terminal on the first attempt (`terminal_refusal_verdict`). The maintainer reports hours lost to exactly these: "this hook is not happy; fix the underlying issue and we'll try again" almost always works.
- Scope: Make each of the three a fix-it send-back under its own per-kind counter against the run's `--retry-budget`, carrying the hook's output or the newly failing tests (redacted) through Order 03's message, resuming the turn's session where one exists, and re-running the same gate afterwards. Tag a hook-refused integration commit with a new cause distinct from a git conflict, including the main-merge case. EXCLUDES transient integration refusals (already on the deferral ladder), conflict markers and lifecycle-duplicate placement (unchanged), a hook refusal diagnosed as a concurrent writer (`ipd_lifecycle.classify_commit_refusal`; unchanged), the pre-finalize gate-answer exchange and its `mine`/`needs-human`/`not-mine`/`fixed` vocabulary (unchanged), and any change to what the hooks check.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_hook_and_suite_fix_it.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:mcbph5
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 5
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: w9nvq4
- Approval: 2026-10-09, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-08 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010. Measured on scratch repos: the finalize hook refusal already carries the hook output (rc 2, plan left in pending, receipt kept, `finalize_refusal_is_retryable` False), so E-01 needs no `ipd_lifecycle` change and that path left Scope-Paths; a `pre-merge-commit` refusal of the main merge leaves MERGE_HEAD with no unmerged paths and is mis-tagged `git-merge-conflict` today, so E-02 now discriminates it structurally and E-06 gives it its own send-back (the conflict loop would re-publish without asking). E-03's premise was wrong: the gate-answer ask runs BEFORE finalize on the lane's own suite, not at the post-merge combined-red refusal, and `mine` is documented as "not being fixed now", so E-03 now sends combined-red back directly with the gate's `new_ids` and leaves the ask unchanged. Per-kind counters named; the exhausted reason names the kind; concurrent-writer diagnosis excluded; hook output must not reach the unredacted `record_refusal`; two shipped `tests/test_oc_runipd.py` combined-red tests would break and are now in scope; post-finalize fix commits recorded with an out-of-scope warning; `terminal_refusal_verdict` wording for combined-red updated. Gate contract added. Review record `.aw/records/reviews/20261007-fixfirst-05-w9nvq4-give-fix-it-turns-for-hook-refusals-and-a-red-suite-at-final.review.md`.
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When a hook refuses a commit or the merged suite goes red, the agent is shown exactly what the hook or the tests said and fixes it, and the runner tries again, instead of the item failing until a human notices.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: hook refusal at finalize

- [x] E-01 Add a third arm to `finalize_refusal_is_retryable` admitting a hook-refused finalize commit. Match on the text `ipd_lifecycle._finalize_transaction` already emits ("lifecycle commit did not happen" AND "the lifecycle commit was rejected in the coordinator worktree (hooks ran)"; measured at review, the driver receives it prefixed `error: ` because finalize exits `EXIT_CANNOT_RUN`), and REFUSE the arm when the message carries `DIAGNOSIS:` (the `classify_commit_refusal` concurrent-writer signature, which is not the agent's to fix). Define the two match strings as module constants beside `RETRYABLE_STALE_RECEIPT_SUMMARY`. Route it through `handle_finalize_refusal` with Order 03's `build_fix_it_notice` (kind `hook-refusal-finalize`), evidence = the hook output verbatim (bounded and path-redacted by the builder), plus one sentence: "the hook ran on your plan file and the lifecycle commit; a hook that rewrote a file did so in a discarded worktree, so apply the same fix to your lane and commit it with `aw commit`". No change to `ipd_lifecycle`.
  - Depends on: none
  - Expected outcome: a scratch repo whose `.git/hooks/pre-commit` rejects the finalize commit once yields one fix-it turn whose prompt contains the hook's output, then a successful finalize; a refusal carrying `DIAGNOSIS:` is not retried.
  - Execution state: performed

### Task group 2: hook refusal at integration

- [x] E-02 In `integrate_lane_branch`, tag every hook-refused integration commit with a new cause `INTEGRATION_CAUSE_HOOK_REFUSED = "hook-refused"` via `tag_integration_cause`, at three sites: (a) the records re-derive commit refusal ("records-only re-derivation was applied but its commit was REFUSED"); (b) the history auto-resolve commit refusal ("history-only conflict was resolved but its commit was REFUSED"); (c) the main `git merge --no-ff` when it returns rc 1 with this call owning the merge (`owns_merge_in_progress`) but `conflicted_paths(repo)` EMPTY, which is the structural signature of a `pre-merge-commit` refusal (measured at review: MERGE_HEAD present, no unmerged paths, git prints "Not committing merge"); abort the merge exactly as the conflict arm does. Keep the kind `INTEGRATION_REFUSAL_CONFLICT` so the deferral ladder is unchanged. Add a `terminal_refusal_verdict` sentence for the new cause that says a hook refused the commit and names no conflict. HOOK OUTPUT CAN CARRY AN ABSOLUTE PATH (the existing comment at sites (a)/(b) says so), so pass the reason through `render_stream._redact_absolute_paths` before tagging, and do NOT add this cause to the `record_refusal` call in `record_integration_refusal`, which does not redact.
  - Depends on: none
  - Expected outcome: in a scratch repo where main advanced and a `pre-merge-commit` hook refuses, `integrate_lane_branch` returns `(False, <reason>, INTEGRATION_REFUSAL_CONFLICT)` with `read_integration_cause(reason)[0] == "hook-refused"`, main has no MERGE_HEAD, and a genuine content conflict still reads `git-merge-conflict`.
  - Execution state: performed

- [x] E-06 Admit `INTEGRATION_CAUSE_HOOK_REFUSED` to a send-back beside the merge-conflict loop in `execute_item_core` (NOT inside it: that loop's `prepare_lane_for_conflict_resolution` merges main into the lane and, finding no conflict, re-publishes without asking, which would spin on the same refusal). Resume the turn's session (`attempt["session_id"]`, the same `resume_via_launcher` shape the conflict loop uses) with Order 03's `build_fix_it_notice` (kind `hook-refusal-integration`) carrying the hook output; after the turn, re-run `integrate_under_repository_lock` with the same `_publish`. Count against the counter E-04 names. Record each send-back on the attempt (`hook_refusal_sendback`) and as an event `integration-hook-refusal-sent-back`. With no session, do not ask; fall through to today's refusal.
  - Depends on: E-02
  - Expected outcome: an integration commit rejected once by a hook yields one send-back whose prompt contains the hook output, then a successful merge on the retry with `git log` on main showing the lane merge; a conflict-markers cause remains terminal.
  - Execution state: performed

### Task group 3: red suite after merge

- [x] E-03 For `INTEGRATION_CAUSE_GATE_COMBINED_RED` (the post-merge revalidation inside `integrate_lane_branch`, which runs AFTER finalize; it is NOT the pre-finalize gate-answer ask, which `gate_answer_is_warranted` runs on the lane's own suite before finalize and which this plan leaves unchanged), send the lane back in the same loop shape as E-06, resuming the session, with Order 03's message (kind `combined-red`) whose evidence is the gate's own record: `item["post_merge_revalidation"]["baseline_comparison"]["new_ids"]` when present (the failures the lane introduced), else `item["post_merge_revalidation"]["failures"]`, and the merged files. Do NOT send back when `revalidation_was_unmeasured(item)` (a harness fault, already reclassified by `record_integration_refusal`). After the turn, re-run integration; the gate re-measures because its cache is keyed by tree. Update the `INTEGRATION_CAUSE_GATE_COMBINED_RED` sentence in `terminal_refusal_verdict` so it no longer says "terminal on its first attempt" and instead says the fix-it budget was spent. Because the lane is already finalized, a fix commit escapes finalize's scope reconciliation (the merge-conflict send-back has the same property): record the paths each fix commit changed on the send-back record and add a warning line to it naming any path outside the plan's `- Scope-Paths:`.
  - Depends on: none
  - Expected outcome: a lane whose merged suite fails once yields a send-back listing the newly failing tests, then a green merge; an unmeasured revalidation is not sent back; a fix commit touching an undeclared path is named on the send-back record.
  - Execution state: performed

- [x] E-04 Give each kind its own counter on the item, compared against `frozen_retry_budget(state)`: `HOOK_FINALIZE_RETRY_COUNT_KEY` (E-01; `finalize_retry_decision` reads it instead of `FINALIZE_RETRY_COUNT_KEY` when the refusal matched E-01's arm), `HOOK_INTEGRATION_RETRY_COUNT_KEY` (E-06) and `COMBINED_RED_RETRY_COUNT_KEY` (E-03). Make the exhausted reason name the kind (today `finalize_retry_decision`'s exhausted text always says "refused this plan's pre-transition checkpoint"), and make the item's recorded refusal reason name it for the two integration kinds, so the run summary says which kind ran out.
  - Depends on: E-01, E-03, E-06
  - Expected outcome: with `--retry-budget 1`, a hook that always refuses yields exactly one fix-it turn and then the item fails with a reason naming the hook refusal; budget 0 yields no fix-it turn; spending the hook-finalize counter does not consume the pre-transition counter.
  - Execution state: performed

### Task group 4: tests

- [x] E-05 Add `tests/test_hook_and_suite_fix_it.py` driving the real runner through `execute_item` on BOTH hosts (`oc_runipd`, `agy_runipd`) with a scripted host in a scratch repo, using plain executable `.git/hooks/pre-commit` and `.git/hooks/pre-merge-commit` scripts that refuse a set number of times (a counter file), for each of E-01 to E-06, asserting on item status, attempt and counter values, the delivered prompt text, events, and git state on main and in the lane; include the `DIAGNOSIS:` and unmeasured-revalidation negatives and budget 0. Update the two shipped `tests/test_oc_runipd.py` combined-red tests (`test_non_passing_gate_defers_not_faked_executed`, `test_non_passing_gate_records_merge_conflict_main_pristine`), whose fake agent would now receive a send-back: set `"retry_budget": 0` in their state options so they keep asserting today's terminal outcome, and change nothing else. No source introspection.
  - Depends on: E-04
  - Expected outcome: the new module passes; the two updated tests pass with only the budget option added.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `terminal_refusal_verdict` changes words, never verdicts; a verdict change belongs at the classification sites, which is where this plan acts.
- `classify_integration_refusal` is fail-closed for unknown kinds; the new cause keeps the existing kind and is admitted explicitly.
- `record_refusal` does not redact; hook output must be redacted before it reaches any record (comment at the records re-derive arm in `integrate_lane_branch`).
- The merge-direction discriminator is structural (MERGE_HEAD, unmerged paths), never git's English (`merge_in_progress` docstring).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | A hook-refused finalize is not retryable, and finalize already surfaces the hook output. | Review demo: `rc 2 \| msg: lifecycle commit did not happen (git rc=1: the lifecycle commit was rejected in the coordinator worktree (hooks ran): HOOKSAYS: trailing whitespace in plan); rolled back to pre-finalize state.`; `receipt still present: True`; `retryable today: False`; `after hook fixed rc 0`. |
| F-02 | A hook-refused integration commit is either untagged or mis-tagged as a git conflict, and is never sent to the agent. | `integrate_lane_branch` arms "records-only re-derivation was applied but its commit was REFUSED" and "history-only conflict was resolved but its commit was REFUSED" return the bare kind; review demo on the main merge: `kind fail-merge \| cause git-merge-conflict`, reason "merge-back conflict; HOOKSAYS: refused ... Not committing merge". |
| F-03 | A red merged suite is terminal on the first attempt. The gate-answer ask is a different, earlier event. | `terminal_refusal_verdict` `INTEGRATION_CAUSE_GATE_COMBINED_RED` "terminal on its first attempt"; `gate_answer_is_warranted` is called once in `execute_item_core`, right after `integration_is_earned`, before finalize. |
| F-04 | Maintainer ruling 2026-10-07: send hook refusals back to the agent to fix the underlying issue. | Session 2026-10-07. |
| F-05 | (review) Two shipped tests drive combined-red through `execute_item` with the default budget and assert terminal `fail-merge`. | `tests/test_oc_runipd.py` `test_non_passing_gate_defers_not_faked_executed`, `test_non_passing_gate_records_merge_conflict_main_pristine`, both via `make_integration_validation_runner` returning False. |

## Proposed changes (ordered, validatable)

1. Finalize hook refusal retryable (E-01).
2. Tag integration hook refusals, including the main merge (E-02).
3. Integration hook refusal sent back (E-06).
4. Red merged suite sent back (E-03).
5. Per-kind counters and kind-naming exhaustion (E-04).
6. Tests (E-05).

## Deferred / out of scope (with reason)

None. The concurrent-writer diagnosis and the pre-finalize gate-answer vocabulary are excluded in Scope with their reasons; they are unchanged behavior, not deferred defects.

## Scope check

- Over-scope: none. `runner_shared.py` E-01 to E-04 and E-06; `tests/test_hook_and_suite_fix_it.py`, `tests/test_oc_runipd.py`, and `tests/test_agy_runipd_cli.py` E-05.
- Under-scope: a fix commit made after finalize is not re-reconciled by finalize; E-03 records and warns rather than re-running finalize, matching the shipped merge-conflict send-back.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_hook_and_suite_fix_it.py tests/test_oc_runipd.py tests/test_merge_conflict_sendback.py tests/test_finalize_sendback.py tests/test_production_correction_turn.py tests/test_runner_shared.py`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

N/A: spec `25kzda` 5.5/5.7 are amended by Order 01 (`tb6lw3` E-01 group (a) names "a hook refusal of any commit; a red combined suite after merge").

## Open questions

### OQ-01: Should a red suite skip the gate-answer ask and go straight to a send-back?

- Blocking: no
- Status: resolved
- Owner: plan-review
- Resolution or deferral rationale: The question rested on a wrong premise. The ask (`gate_answer_is_warranted`) runs before finalize on the lane's own suite, and its `fixed` answer already gives a bounded repair loop with a suite re-run (`perform_gate_answer`). The post-merge combined-red refusal is a later, separate event that has no ask, so E-03 sends it back directly with the gate's `new_ids`. The ask and its vocabulary are left unchanged (decision D-2 in the review record).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the delivered fix-it prompt containing the hook output, the item's final status, and `finalize_refusal_is_retryable` on a `DIAGNOSIS:`-bearing message returning False.
  - Observed evidence:
    `finalize_refusal_is_retryable` checks:
    ```
    DIAGNOSIS retryable: False
    HOOK retryable: True
    ```
    Delivered fix-it prompt and item execution in `test_v01_e01_hook_refusal_finalize_sendback_and_recovery`:
    ```
    item final status: executed
    item hook retry count: 1
    recovery prompt snippet:
      ## hook-refusal-finalize (attempt 1 of 2)
      HOOK_FAIL: trailing whitespace in plan.ipd.md
      the hook ran on your plan file and the lifecycle commit; a hook that rewrote a file did so in a discarded worktree, so apply the same fix to your lane and commit it with `aw commit`
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `integrate_lane_branch`'s return for the `pre-merge-commit` refusal (cause `hook-refused`, main without MERGE_HEAD) and for a real content conflict (cause `git-merge-conflict`); paste the reason showing no absolute path.
  - Observed evidence:
    `test_v02_tag_integration_hook_refusals_unit`:
    ```
    pre-merge-commit refusal:
      ok: False kind: fail-merge cause: hook-refused
      MERGE_HEAD exists: False
      reason: [aw-integration-cause=hook-refused] integration commit was refused by a git hook (pre-merge-commit), so the merge was aborted and main is untouched: HOOK_REFUSAL: rejecting merge from <path>
    real content conflict:
      ok: False kind: fail-merge cause: git-merge-conflict
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the send-back prompt listing the newly failing tests and the green re-run; the unmeasured case not sent back; the send-back record naming an undeclared path.
  - Observed evidence:
    `test_v03_e03_combined_red_sendback_and_warning_on_out_of_scope`:
    Send-back prompt containing newly failing test ID:
    ```
    ## combined-red (attempt 1 of 2)
    integration gate failed (combined-red):
    new failing tests:
      - tests/test_foo.py::test_failing_case
    ```
    Send-back record naming undeclared path and warning:
    ```
    paths_changed: ['clash.txt', 'extra.txt']
    warning: fix commit modified path(s) outside declared Scope-Paths: extra.txt
    ```
    Green re-run final status:
    ```
    item final status: executed
    combined_red_retry_count: 1
    ```
    Unmeasured case (`test_v03_e03_unmeasured_revalidation_negative_not_sent_back`):
    ```
    item final status: merge-retry
    combined_red_retry_count: 0
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the budget-1 run's counter values and the item's refusal reason naming the kind, the budget-0 run showing no fix-it turn, and the pre-transition counter unchanged after a hook-finalize retry.
  - Observed evidence:
    `test_v04_per_kind_counters_and_exhaustion_unit`:
    Pre-transition counter unchanged after hook finalize retry:
    ```
    dec1.retry: True, finalize_retry_count: 0
    dec2.exhausted: True, finalize_retry_count: 0, hook_finalize_retry_count: 1
    dec2.reason: "a git hook refused the finalize commit and the run's fix-it budget was spent (1 fix-it turn used)"
    ```
    `test_v04_e04_budget_zero_and_exhaustion_with_kind_naming`:
    Budget-1 run:
    ```
    item status: fail-merge
    hook_integration_retry_count: 1
    refusal reason: "the run's fix-it budget was spent (1 fix-it turn used) on integration hook refusals, and the commit was still refused"
    ```
    Budget-0 run:
    ```
    item status: fail-merge
    hook_integration_retry_count: 0
    turns used: 0
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the passing Required tests run with per-test counts, the `tests/test_oc_runipd.py` diff, and the bare-suite summary line.
  - Observed evidence:
    Diff in `tests/test_oc_runipd.py`:
    ```diff
    --- a/tests/test_oc_runipd.py
    +++ b/tests/test_oc_runipd.py
    @@ -3970,6 +3970,7 @@ class WorktreeIsolationTests(unittest.TestCase):
                 plan = _init_repo_with_conforming_plan(repo, "wir001")
                 run_dir = self._mk_run_dir(repo)
                 state, item = self._state_and_item(repo, plan)
    +            state["options"]["retry_budget"] = 0

                 # Force the gate's full revalidation to fail -> INTEGRATION_FAILED_COMBINED_RED.
                 def failing_runner_factory(*a, **k):
    @@ -4479,6 +4480,7 @@ class FailClosedIntegrationGuardTests(unittest.TestCase):
                 plan = _init_repo_with_conforming_plan(repo, "wir001")
                 run_dir = self._mk_run_dir(repo)
                 state, item = self._state_and_item(repo, plan)
    +            state["options"]["retry_budget"] = 0

                 main_head_before = subprocess.run(
                     ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True
    ```
    Bare-suite summary line for new test module:
    ```
    10 passed in 19.53s
    ```
    Passing Required test suite run with per-test counts:
    ```
    python3 -m pytest tests/test_hook_and_suite_fix_it.py tests/test_oc_runipd.py tests/test_merge_conflict_sendback.py tests/test_finalize_sendback.py tests/test_production_correction_turn.py tests/test_runner_shared.py
    409 passed in 60.23s (0:01:00)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `integration-hook-refusal-sent-back` event, the delivered prompt containing the hook output, and `git log --oneline -3` on main after the retry.
  - Observed evidence:
    `test_v06_e06_integration_hook_refusal_sendback`:
    Event:
    ```json
    {
      "at": "2026-10-09T09:14:19+00:00",
      "attempt": 1,
      "event": "integration-hook-refusal-sent-back",
      "id6": "wir001",
      "reason": "[aw-integration-cause=hook-refused] integration commit was refused by a git hook (pre-merge-commit), so the merge was aborted and main is untouched: HOOK_MERGE_FAIL: check failed on <path>\nNot committing merge; use 'git commit' to complete the merge.",
      "retry_attempt": 1,
      "retry_budget": 2
    }
    ```
    Delivered prompt snippet:
    ```
    ## hook-refusal-integration (attempt 1 of 2)
    integration commit was refused by a git hook (pre-merge-commit), so the merge was aborted and main is untouched: HOOK_MERGE_FAIL: check failed on <path>
    ```
    `git log --oneline -3` on main after retry:
    ```
    2135d49 integrate(aw oc run): merge verified lane wir001 to main
    50513a8 lane fix
    4b79e00 lifecycle(wir001): finalize wir001 -> executed
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Execute only after `mcbph5` has executed (`- Item-Dependencies:`), because every send-back uses its `build_fix_it_notice`.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
