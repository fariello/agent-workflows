- Id: l9ssp6
- Status: done
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Investigate probe applicability for benchmark_runners

## Workflow history
- 2026-10-24 done (aw backlog): closed by aw agy run: IPD rempo8 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261023-trimgap-37-rempo8-lock-trialresult-to-dict-and-runneradapter-adapter-digest-be.ipd.md); evidence .aw/records/plans/executed/20261023-trimgap-37-rempo8-lock-trialresult-to-dict-and-runneradapter-adapter-digest-be.ipd.md
- 2026-10-24 graduated (aw backlog): graduated by run run-20261023T221924Z-2698768: rempo8
- 2026-10-18 created (aw backlog): Investigate probe applicability for benchmark_runners

Carries 2 candidate production keys for agent_workflows/benchmark_runners.py with remedy shape 'investigate probe'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- TrialResult.to_dict (verdict: unprovable, operator: return-none, control: tests/test_benchmark_runners_reports.py)
- RunnerAdapter.adapter_digest (verdict: unprovable, operator: return-none, control: tests/test_benchmark_runners_reports.py)

Deleted test files to mine: the queue's control files (tests/test_benchmark_runners_reports.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: investigate probe.
Carried from lrnh5f via plan b83dpg.
