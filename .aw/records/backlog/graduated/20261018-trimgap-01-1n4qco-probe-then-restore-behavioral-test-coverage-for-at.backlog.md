- Id: 1n4qco
- Status: graduated
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Probe then restore behavioral test coverage for attention

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T175032Z-1384916: a5drqh
- 2026-10-18 created (aw backlog): Probe then restore behavioral test coverage for attention

Carries 3 candidate production keys for agent_workflows/attention.py with remedy shape 'probe then restore'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- _shared_gate_ref (verdict: budget-exhausted, operator: return-none, control: tests/test_attention_priority_blocker.py)
- render_table (verdict: budget-exhausted, operator: return-none, control: tests/test_attention_priority_blocker.py)
- _render_table_row (verdict: budget-exhausted, operator: return-none, control: tests/test_attention_priority_blocker.py)

Deleted test files to mine: the queue's control files (tests/test_attention_priority_blocker.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: probe then restore.
Carried from lrnh5f via plan b83dpg.
