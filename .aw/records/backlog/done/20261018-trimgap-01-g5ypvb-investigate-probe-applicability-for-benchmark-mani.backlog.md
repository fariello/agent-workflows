- Id: g5ypvb
- Status: done
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Investigate probe applicability for benchmark_manifest

## Workflow history
- 2026-10-24 done (aw backlog): closed by aw agy run: IPD ya0h23 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261023-trimgap-25-ya0h23-restore-behavioral-test-coverage-for-benchmark-manifest-dige.ipd.md); evidence .aw/records/plans/executed/20261023-trimgap-25-ya0h23-restore-behavioral-test-coverage-for-benchmark-manifest-dige.ipd.md
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175028Z-1384849: ya0h23
- 2026-10-18 created (aw backlog): Investigate probe applicability for benchmark_manifest

Carries 3 candidate production keys for agent_workflows/benchmark_manifest.py with remedy shape 'investigate probe'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- BenchmarkManifest.digest (verdict: unprovable, operator: return-none, control: tests/test_benchmark_corpus.py)
- Ceilings.digest (verdict: unprovable, operator: return-none, control: tests/test_benchmark_corpus.py)
- _digest (verdict: unprovable, operator: return-none, control: tests/test_benchmark_corpus.py)

Deleted test files to mine: the queue's control files (tests/test_benchmark_corpus.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: investigate probe.
Carried from lrnh5f via plan b83dpg.
