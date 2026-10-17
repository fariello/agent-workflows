- Id: ziuj5c
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for run_gates

## Workflow history
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for run_gates

Carries 3 candidate production keys for agent_workflows/run_gates.py (157 exclusive lines): execute_gated_action, GateDecision.is_approved, evaluate_gate.

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 3 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_migration_complex.py, test_run_packet_gates.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for run_gates.
