- Id: 3hurk1
- Status: done
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for benchmark_corpus

## Workflow history
- 2026-10-24 done (aw backlog): closed by aw agy run: IPD btubm6 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261023-trimgap-24-btubm6-restore-behavioral-test-coverage-for-benchmark-corpus-load-c.ipd.md); evidence .aw/records/plans/executed/20261023-trimgap-24-btubm6-restore-behavioral-test-coverage-for-benchmark-corpus-load-c.ipd.md
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175028Z-1384849: btubm6
- 2026-10-18 created (aw backlog): Restore behavioral test coverage for benchmark_corpus

Carries 2 candidate production keys for agent_workflows/benchmark_corpus.py with remedy shape 'restore behavioral coverage'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- SeededTask.workspace_seed_path (verdict: unguarded, operator: return-none, control: tests/test_benchmark_corpus.py)
- load_corpus (verdict: unguarded, operator: return-none, control: tests/test_benchmark_corpus.py)

Deleted test files to mine: the queue's control files (tests/test_benchmark_corpus.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: restore behavioral coverage.
Carried from lrnh5f via plan b83dpg.
