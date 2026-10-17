- Id: gjmiuw
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for run_analytics_submit

## Workflow history
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for run_analytics_submit

Carries 14 candidate production keys for agent_workflows/run_analytics_submit.py (311 exclusive lines): open_url, _redact_url, _refusal_result, url_policy_refusal, attestation_refusal, ... (14 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 14 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_run_analytics_privacy_boundary.py, test_run_analytics_submit.py, test_run_analytics_wizard.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for run_analytics_submit.
