- Id: yvmxs9
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Probe then restore behavioral test coverage for config

## Workflow history
- 2026-10-18 created (aw backlog): Probe then restore behavioral test coverage for config

Carries 2 candidate production keys for agent_workflows/config.py with remedy shape 'probe then restore'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- findings_gate_threshold (verdict: budget-exhausted, operator: return-none, control: tests/test_plan_readiness_recheck.py)
- read_review_findings_gate (verdict: budget-exhausted, operator: return-none, control: tests/test_plan_readiness_recheck.py)

Deleted test files to mine: the queue's control files (tests/test_plan_readiness_recheck.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: probe then restore.
Carried from lrnh5f via plan b83dpg.
