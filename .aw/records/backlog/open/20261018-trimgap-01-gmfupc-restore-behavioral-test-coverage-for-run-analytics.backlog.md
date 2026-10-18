- Id: gmfupc
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for run_analytics_telemetry

## Workflow history
- 2026-10-18 created (aw backlog): Restore behavioral test coverage for run_analytics_telemetry

Carries 4 candidate production keys for agent_workflows/run_analytics_telemetry.py with remedy shape 'restore behavioral coverage'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- _validate_label_list (verdict: unguarded, operator: return-none, control: tests/test_run_analytics_telemetry.py)
- _validate_tool_versions (verdict: unguarded, operator: return-none, control: tests/test_run_analytics_telemetry.py)
- node_pseudonym (verdict: unguarded, operator: return-none, control: tests/test_run_analytics_telemetry.py)
- _validate_number_map (verdict: unguarded, operator: return-none, control: tests/test_run_analytics_telemetry.py)

Deleted test files to mine: the queue's control files (tests/test_run_analytics_telemetry.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: restore behavioral coverage.
Carried from lrnh5f via plan b83dpg.
