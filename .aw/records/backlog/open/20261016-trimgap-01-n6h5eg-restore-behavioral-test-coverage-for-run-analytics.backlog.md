- Id: n6h5eg
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for run_analytics_cli

## Workflow history
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for run_analytics_cli

Carries 76 gaps for agent_workflows/run_analytics_cli.py (449 exclusive lines): 1 production key (agent_workflows/run_analytics_cli.py::run_analyze, verdict unguarded-unreached, 4 exclusive lines) and 75 missing test names from tests/test_run_analytics_cli.py classified as gap (445 exclusive lines).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Recreated missing names.
Reach class and verdict: run_analyze is unreached at baseline HEAD (unguarded-unreached); 75 missing tests replayed passed in detached worktree but leave 445 exclusive lines uncovered by surviving suite.
Deleted test files to mine: tests/test_run_analytics_cli.py at 19313eed^.
Remedy: restore the 75 named behavioral tests in tests/test_run_analytics_cli.py and behavioral coverage for run_analyze, updating fixtures and schemas where analytics contracts evolved.
