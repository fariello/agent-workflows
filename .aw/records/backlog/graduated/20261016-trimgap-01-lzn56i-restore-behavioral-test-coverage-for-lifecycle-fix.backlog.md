- Id: lzn56i
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for lifecycle_fixtures

## Workflow history
- 2026-10-17 graduated (aw backlog): graduated by run run-20261017T053744Z-500206: jy7439
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for lifecycle_fixtures

Carries 21 candidate production keys for agent_workflows/lifecycle_fixtures.py (244 exclusive lines): run_downgrade_warning, run_customized_file, run_multi_host_discovery, run_unsupported_host, run_interrupted_update, ... (21 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 21 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_lifecycle_fixtures.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for lifecycle_fixtures.
