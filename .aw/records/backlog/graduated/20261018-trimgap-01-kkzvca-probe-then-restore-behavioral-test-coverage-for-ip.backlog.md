- Id: kkzvca
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Probe then restore behavioral test coverage for ipd_lint

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175032Z-1384916: 3wkrng
- 2026-10-18 created (aw backlog): Probe then restore behavioral test coverage for ipd_lint

Carries 2 candidate production keys for agent_workflows/ipd_lint.py with remedy shape 'probe then restore'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- lint_file (verdict: budget-exhausted, operator: return-none, control: tests/test_ipd_dependency_check.py)
- check_item_dependencies (verdict: budget-exhausted, operator: return-none, control: tests/test_ipd_dependency_check.py)

Deleted test files to mine: the queue's control files (tests/test_ipd_dependency_check.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: probe then restore.
Carried from lrnh5f via plan b83dpg.
