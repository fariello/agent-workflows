- Id: eh91an
- Status: open
- Set: eh91an
- Priority: medium
- Work-Kind: chore
- Summary: run_recovery.plan_retry and retry_budget_remaining remain dormant with zero production callers

## Workflow history
- 2026-09-20 created (aw backlog): Recorded as a finding from plan zzcrlo (finalback) OQ-03, which required the divergence be reported rather than quietly accepted for another cycle. `run_recovery.plan_retry` and `retry_budget_remaining` are complete and tested and document six guarantees (including evidence invalidation across the retry boundary and RetryLimitExceededError instead of looping), but they still have ZERO production callers. zzcrlo needed a bounded correction retry and COULD NOT use them: `plan_retry(engine, ...)` requires a `run_engine.RunEngine` over a hash-chained `ledger.jsonl`, and re-measured at HEAD a36dbc1e neither driver mentions run_engine or run_state at all (grep count 0 in both) and no run directory carries a ledger.jsonl. The step-state vocabularies are also disjoint: plan_retry raises NoRetryableStateError unless the step is in run_state.STATE_FAILED//STATE_BLOCKED, values a driver queue item never holds. Spec 25kzda:28 concedes the ledger is built but UNWIRED. So zzcrlo bounded its send-back directly against the item's own attempts list while reading the FROZEN options.retry_budget, introducing NO second budget knob. This item tracks the real fix: either wire the ledger substrate into the drivers so the shipped helpers are reachable, or retire them. Sibling: plan xipfy1 owns the general 'where is the budget spent' question. WHERE: agent_workflows/run_recovery.py plan_retry//retry_budget_remaining, agent_workflows/runner_shared.py finalize_retry_decision.
