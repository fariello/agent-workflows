- Id: spvm3v
- Status: open
- Set: spvm3v
- Priority: medium
- Work-Kind: followup
- Summary: Two classes deleted from tests/test_docs.py remain unrestored: RunAnalyticsPrivacyDocTests (run_analytics_export detector blind spots vs docs/run-analytics.md) and LifecycleLegendAndDocsDriftGuardTests (no test asserts the lifecycle legend reaches aw --help output)

## Workflow history
- 2026-09-30 created (aw backlog): Filed by plan t9lcdu (gzmr54-01) as the durable carrier for its two deferred rows. t9lcdu restores only the docs_check and docs_render coverage; these two classes test neither module. Measured at HEAD 2e2ecce12: both PASS when recovered, so nothing is newly broken, but 'rg -n LIFECYCLE LEGEND tests/' and 'rg -n DETECTOR_BLIND_SPOTS tests/' both return zero, and no test asserts the legend reaches cli._build_parser().format_help() at all (tests/test_term.py covers only Term.format_lifecycle_legend).
