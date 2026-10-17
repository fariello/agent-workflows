- Id: igefrj
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for migration_inventory

## Workflow history
- 2026-10-17 graduated (aw backlog): graduated by run run-20261017T053805Z-509296: 94wi2f
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for migration_inventory

Carries 25 candidate production keys for agent_workflows/migration_inventory.py (189 exclusive lines): _harness_ir, HarnessRegistry.catalog_rows, plan_rollup, build_assess_harness, plan_review_parity, ... (25 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 25 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_migration_inventory_shared.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for migration_inventory.
