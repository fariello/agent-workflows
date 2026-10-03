- Id: kw31r2
- Status: done
- Graduated-To: verremand
- Blocks-Release: next
- Set: verremand
- Priority: high
- Work-Kind: bug
- Summary: Remand verification evidence refusals and verification failures back to the agent under retry conventions

## Workflow history
- 2026-10-02 done (aw backlog): closed by aw agy run: IPD t18l64 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-verremand-01-t18l64-remand-verification-evidence-refusals-and-verification-failu.ipd.md); evidence .aw/records/plans/executed/20261001-verremand-01-t18l64-remand-verification-evidence-refusals-and-verification-failu.ipd.md
- 2026-10-01 graduated (aw set): Graduated to plan t18l64
- 2026-10-01 created (aw backlog): Remand verification evidence refusals and verification failures back to the agent under retry conventions

WHAT IS WRONG. When an execute-action child turn completes execution and reaches the independent verifier turn, any failure during verification (e.g. `verifier-no-test-evidence` from `has_verifier_test_evidence`, an unverified or failed verdict, or missing/unreadable outcome file) immediately sets `disposition = "fail-verify"`. In `agent_workflows/runner_shared.py`, `turn_failure_is_retryable` marks `fail-verify` as non-retryable (`"disposition 'fail-verify' is not retryable: verifier refused or turn fell short; not retryable as a host failure"`).

Consequently, the runner never remands the failure back to the agent under the run's `--retry-budget` (frozen retry budget). The turn retry is skipped (`turn_retry_skipped`), the lane worktree is preserved in `fail-verify`, the item is marked `fail-verify` on disk and `blocked` in active runner views, and the runner moves on to the next queued item.

WHY THIS VIOLATES SPEC 25kzda SECTION 5.5. Spec `25kzda` Section 5.5 explicitly lists `missing or stale validation evidence` as a retryable failure class eligible to spend retry budget alongside host spawn failures and deterministic check failures. Treating verification evidence defects as immediate terminal failures violates Section 5.5 and leaves work that an agent could trivially correct stranded.

MEASURED 2026-10-01 in run `run-20260930T233959Z-250047`, item `5poaqh` (Set `pftva5`):
Plan `5poaqh` was fully implemented, 90/90 tests passed, and pre-transition lint was conforming. The independent verifier ran all tests and reported `VERIFIED`, but formatted its outcome `tests_run` as test function nodeids (`tests/test_status_set.py::SetterRefusalRetryCommandTests::test_case_a...`) instead of CLI command strings (`python3 -m pytest ...`).
The runner flagged `verifier-no-test-evidence` and immediately refused integration without giving the agent an opportunity to fix the evidence or re-verify under the configured retry budget. The item was stranded `fail-verify` with 1 commit on `aw/lane/5poaqh` and 0 merge conflicts.

SUGGESTED FIX.
1. Introduce verification retry accounting (`VERIFICATION_RETRY_COUNT_KEY = "verification_retry_count"`) and a verification retry decision helper (`verification_retry_decision`) following the existing `finalize_retry_decision` pattern.
2. When verification fails with a retryable verification refusal (such as `verifier-no-test-evidence`, `unverified`, or `fail-verify` where bounded correction is safe):
   If `verification_retry_count < retry_budget`:
     - Increment retry counter.
     - Record `verification-sent-back` event in `events.jsonl`.
     - Set `item["status"] = "queued"`, `item["recovery_next"] = True`, `item["requeue_from_status"] = disposition`.
     - Ensure `build_prompt` passes the verification refusal code, reason, and remedy to the agent on the recovery turn.
   If budget is exhausted:
     - Record `fail-verify` (exhausted) and preserve lane.
3. Ensure symmetry across both OpenCode (`oc_runipd`) and Antigravity (`agy_runipd`) runners.
