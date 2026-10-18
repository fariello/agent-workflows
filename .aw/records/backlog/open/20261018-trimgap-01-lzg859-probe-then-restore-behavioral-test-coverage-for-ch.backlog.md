- Id: lzg859
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Probe then restore behavioral test coverage for check_engine

## Workflow history
- 2026-10-18 created (aw backlog): Probe then restore behavioral test coverage for check_engine

Carries 10 candidate production keys for agent_workflows/check_engine.py with remedy shape 'probe then restore'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- check_ipd_draft_ready (verdict: budget-exhausted, operator: return-none, control: tests/test_doctor_and_marker.py)
- check_plan_priority_required (verdict: budget-exhausted, operator: return-none, control: tests/test_work_commit.py)
- check_review_decision_unescalated (verdict: budget-exhausted, operator: return-none, control: tests/test_doctor_and_marker.py)
- check_review_finding_unescalated (verdict: budget-exhausted, operator: return-none, control: tests/test_doctor_and_marker.py)
- check_spec_criteria_uncovered (verdict: budget-exhausted, operator: return-none, control: tests/test_doctor_and_marker.py)
- _plan_disposition (verdict: budget-exhausted, operator: return-none, control: tests/test_check_engine_receipt_liveness.py)
- check_names (verdict: budget-exhausted, operator: return-none, control: tests/test_prompt_id6_filenames.py)
- check_release_gate_consistency (verdict: budget-exhausted, operator: return-none, control: tests/test_bug_gate_default.py)
- evaluate_review_finding_escalation (verdict: budget-exhausted, operator: return-none, control: tests/test_doctor_and_marker.py)
- _iter_type_files (verdict: budget-exhausted, operator: raise, control: tests/test_doctor_and_marker.py)

Deleted test files to mine: the queue's control files (tests/test_bug_gate_default.py, tests/test_check_engine_receipt_liveness.py, tests/test_doctor_and_marker.py, tests/test_prompt_id6_filenames.py, tests/test_work_commit.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: probe then restore.
Carried from lrnh5f via plan b83dpg.
