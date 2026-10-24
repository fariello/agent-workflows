- Id: aaud70
- Status: done
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Investigate probe applicability for run_analytics_spa

## Workflow history
- 2026-10-24 done (aw backlog): closed by aw agy run: IPD di5puw executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261023-trimgap-26-di5puw-resolve-probe-applicability-for-run-analytics-spa-keys-and-l.ipd.md); evidence .aw/records/plans/executed/20261023-trimgap-26-di5puw-resolve-probe-applicability-for-run-analytics-spa-keys-and-l.ipd.md
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175032Z-1384916: di5puw
- 2026-10-18 created (aw backlog): Investigate probe applicability for run_analytics_spa

Carries 5 candidate production keys for agent_workflows/run_analytics_spa.py with remedy shape 'investigate probe'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- _render_findings (verdict: unprovable, operator: return-none, control: tests/test_run_analytics_e2e.py)
- _render_pricing (verdict: unprovable, operator: return-none, control: tests/test_run_analytics_e2e.py)
- _render_refusals (verdict: unprovable, operator: return-none, control: tests/test_run_analytics_packaging.py)
- refusal_from_result (verdict: unprovable, operator: return-none, control: tests/test_run_analytics_e2e.py)
- scan_for_network_references (verdict: unprovable, operator: return-none, control: tests/test_run_analytics_e2e.py)

Deleted test files to mine: the queue's control files (tests/test_run_analytics_e2e.py, tests/test_run_analytics_packaging.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: investigate probe.
Carried from lrnh5f via plan b83dpg.
