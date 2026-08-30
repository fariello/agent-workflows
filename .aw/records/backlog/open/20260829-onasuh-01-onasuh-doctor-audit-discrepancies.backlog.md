- Id: onasuh
- Status: open
- Set: onasuh
- Priority: medium
- Work-Kind: feature
- Summary: Surface artifact and status discrepancies in aw doctor via shared audit engine

## Workflow history
- 2026-08-29 created (aw backlog): Surface artifact and status discrepancies in aw doctor via shared audit engine

Surface artifact location and status discrepancies in `aw doctor` (and evaluate `aw check`) by extracting the audit logic in `run_viewer.py` (`audit_step_artifact` / `find_artifact_file`) into a shared reusable module. This ensures `aw runs`, `aw doctor`, and other diagnosis tooling share a single source of truth for artifact location/status drift, preventing inter-tool discrepancy divergence, while also accounting for active/live runner states.
