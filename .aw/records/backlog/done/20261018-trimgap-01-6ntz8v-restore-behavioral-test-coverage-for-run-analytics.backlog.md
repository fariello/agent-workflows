- Id: 6ntz8v
- Status: done
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for run_analytics_findings

## Workflow history
- 2026-10-24 done (aw backlog): closed by aw agy run: IPD 92tzo6 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261023-trimgap-24-92tzo6-verify-and-lock-behavioral-coverage-for-run-analytics-findin.ipd.md); evidence .aw/records/plans/executed/20261023-trimgap-24-92tzo6-verify-and-lock-behavioral-coverage-for-run-analytics-findin.ipd.md
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175005Z-1383890: 92tzo6
- 2026-10-18 created (aw backlog): Restore behavioral test coverage for run_analytics_findings

Carries 3 candidate production keys for agent_workflows/run_analytics_findings.py with remedy shape 'restore behavioral coverage'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- assert_no_causal_language (verdict: unguarded, operator: raise, control: tests/test_run_analytics_findings.py)
- build_finding (verdict: unguarded, operator: return-none, control: tests/test_run_analytics_findings.py)
- findings_from_results (verdict: unguarded, operator: return-none, control: tests/test_run_analytics_findings.py)

Deleted test files to mine: the queue's control files (tests/test_run_analytics_findings.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: restore behavioral coverage.
Carried from lrnh5f via plan b83dpg.
