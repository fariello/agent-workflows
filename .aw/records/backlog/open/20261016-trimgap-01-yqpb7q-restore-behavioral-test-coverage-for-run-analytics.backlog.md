- Id: yqpb7q
- Status: open
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for run_analytics_telemetry

## Workflow history
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for run_analytics_telemetry

Carries 24 candidate production keys for agent_workflows/run_analytics_telemetry.py (151 exclusive lines): _parse_accelerator_csv, SystemResourceProbeAdapter._run_bounded, build_event, ResourceSampler.tick, _validate_accelerators, ... (24 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 24 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_run_analytics_packaging.py, test_run_analytics_telemetry.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for run_analytics_telemetry.
