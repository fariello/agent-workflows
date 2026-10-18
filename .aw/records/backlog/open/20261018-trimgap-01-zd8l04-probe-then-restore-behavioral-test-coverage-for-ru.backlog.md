- Id: zd8l04
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Probe then restore behavioral test coverage for run_analytics_telemetry

## Workflow history
- 2026-10-18 created (aw backlog): Probe then restore behavioral test coverage for run_analytics_telemetry

Carries 8 candidate production keys for agent_workflows/run_analytics_telemetry.py with remedy shape 'probe then restore'.

Details in Set findings doc wo21z5 ## Probe queue, ## Budget probe results, and ## Filing plan.

Keys covered:
- ResourceSampler.__init__ (verdict: budget-exhausted, operator: raise, control: tests/test_run_analytics_telemetry.py)
- ResourceSampler.start (verdict: budget-exhausted, operator: raise, control: tests/test_run_analytics_telemetry.py)
- ResourceSampler.stop (verdict: budget-exhausted, operator: raise, control: tests/test_run_analytics_telemetry.py)
- SystemResourceProbeAdapter.accelerators (verdict: budget-exhausted, operator: return-none, control: tests/test_run_analytics_telemetry.py)
- SystemResourceProbeAdapter.disk (verdict: budget-exhausted, operator: return-none, control: tests/test_run_analytics_telemetry.py)
- TelemetryCollector.__init__ (verdict: budget-exhausted, operator: raise, control: tests/test_run_analytics_telemetry.py)
- TelemetryCollector._emit (verdict: budget-exhausted, operator: return-none, control: tests/test_run_analytics_telemetry.py)
- TelemetryCollector._observe_accelerators (verdict: budget-exhausted, operator: return-none, control: tests/test_run_analytics_telemetry.py)

Deleted test files to mine: the queue's control files (tests/test_run_analytics_telemetry.py) plus hpjj44 ## Derived properties; source 19313eed^.
Remedy: probe then restore.
Carried from lrnh5f via plan b83dpg.
