- Id: gcpj15
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Probe then restore behavioral test coverage for ipd_lifecycle

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175005Z-1383890: 2qlg0w
- 2026-10-18 created (aw backlog): Probe then restore behavioral test coverage for ipd_lifecycle

Carries 4 candidate production keys for agent_workflows/ipd_lifecycle.py with remedy shape 'probe then restore'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- _baseline_ambiguity (verdict: budget-exhausted, operator: return-none, control: tests/test_begin_dirty_gate_scope.py)
- begin (verdict: budget-exhausted, operator: return-none, control: tests/test_begin_dirty_gate_scope.py)
- _execution_cohesive_committed_paths (verdict: budget-exhausted, operator: return-none, control: tests/test_finalize_scope_ownership.py)
- finalize_precheck (verdict: budget-exhausted, operator: return-none, control: tests/test_finalize_exact_attribution.py)

Deleted test files to mine: the queue's control files (tests/test_begin_dirty_gate_scope.py, tests/test_finalize_exact_attribution.py, tests/test_finalize_scope_ownership.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: probe then restore.
Carried from lrnh5f via plan b83dpg.
