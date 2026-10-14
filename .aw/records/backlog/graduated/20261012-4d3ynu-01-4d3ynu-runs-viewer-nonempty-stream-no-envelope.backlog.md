- Id: 4d3ynu
- Status: graduated
- Graduated-To: 4d3ynu
- Blocks-Release: next
- Set: 4d3ynu
- Priority: low
- Work-Kind: bug
- Summary: aw runs / aw runs list non-empty --agent stream and flag-conflict refusals emit bare JSON with no aw.agent/v1 envelope

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: 3jg79f
- 2026-10-12 created (aw backlog): aw runs / aw runs list non-empty --agent stream and flag-conflict refusals emit bare JSON with no aw.agent/v1 envelope

Found while graduating l5dq92 (plan t76qdk), which fixes ONLY the empty-state branch of run_viewer.run_viewer_cli and deliberately leaves these out of its scope. (1) The non-empty --agent path prints one bare json.dumps(asdict(RunSummary)) line per run (and bare StepSummary lines under --latest-only, a bare build_multi_run_summary_dict line under --summary-only, bare audit lines under --issues) followed by a bare {"kind": "excluded_runs"} line, with no schema/kind/outcome/exit fields and no terminating summary record, although command_surface declares runs list agent_record_kind=summary. (2) The flag-conflict and --since refusals in run_viewer_cli print bare {"error": ..., "exit_code": 2} under --agent/--json instead of a kind=error record. Measured at HEAD 4dc9b2f82 by reading run_viewer.run_viewer_cli. Deciding the item-record shape for a RunSummary (and whether --json keeps the bare runs dict) is a public machine-surface contract change for every aw runs consumer, so it needs its own plan.
