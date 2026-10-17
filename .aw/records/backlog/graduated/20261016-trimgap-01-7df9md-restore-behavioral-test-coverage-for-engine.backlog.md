- Id: 7df9md
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for engine

## Workflow history
- 2026-10-17 graduated (aw backlog): graduated by run run-20261017T053744Z-500206: 33f8tn
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for engine

Carries 12 candidate production keys for agent_workflows/engine.py (264 exclusive lines): create_dependency_gate_hook, is_stale_shim_customized, _wire_optin_precommit_hook, _merge_tree, create_precommit_scope_gate_hook, ... (12 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 12 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_command_shims.py, test_comms.py, test_compat_migration_rollback.py, test_exec_set_workflow.py, test_host_adapters_skills.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for engine.
