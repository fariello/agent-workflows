- Id: fdyjv6
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for migration_compact

## Workflow history
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for migration_compact

Carries 24 candidate production keys for agent_workflows/migration_compact.py (210 exclusive lines): evaluate_promotion_gate, build_metric_summary, TypedContract.validate, build_compact_package, generate_compact_projection, ... (24 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 24 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_exec_set_workflow.py, test_migration_compact_shims.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for migration_compact.
