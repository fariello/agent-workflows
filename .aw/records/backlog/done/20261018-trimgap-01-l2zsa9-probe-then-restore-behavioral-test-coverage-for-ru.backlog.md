- Id: l2zsa9
- Status: done
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Probe then restore behavioral test coverage for runner_shared

## Workflow history
- 2026-10-24 done (aw backlog): closed by aw agy run: IPD wfm5iv executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261023-trimgap-29-wfm5iv-probe-then-restore-core-tier-behavioral-coverage-for-runner.ipd.md); evidence .aw/records/plans/executed/20261023-trimgap-29-wfm5iv-probe-then-restore-core-tier-behavioral-coverage-for-runner.ipd.md
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175028Z-1384849: wfm5iv
- 2026-10-18 created (aw backlog): Probe then restore behavioral test coverage for runner_shared

Carries 3 candidate production keys for agent_workflows/runner_shared.py with remedy shape 'probe then restore'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- spec_impacts_for_queue (verdict: budget-exhausted, operator: return-none, control: tests/test_spec_visibility.py)
- expand_selectors (verdict: budget-exhausted, operator: return-none, control: tests/test_runipd_selector_admission.py)
- route_recovery_turn (verdict: budget-exhausted, operator: return-none, control: tests/test_resumedupe.py)

Deleted test files to mine: the queue's control files (tests/test_resumedupe.py, tests/test_runipd_selector_admission.py, tests/test_spec_visibility.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: probe then restore.
Carried from lrnh5f via plan b83dpg.
