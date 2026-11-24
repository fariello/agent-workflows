- Id: f3geta
- Status: open
- Set: f3geta
- Work-Kind: chore
- Priority: low
- Summary: artifact_core.aggregate_index_results has no caller after the INDEX writers were deleted (snin8q E-18)
- Short-Description: artifact_core.aggregate_index_results has no caller after the INDEX writers were deleted (snin8q E-18)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): artifact_core.aggregate_index_results has no caller after the INDEX writers were deleted (snin8q E-18)

Observed 2026-11-24 during snin8q (metastore Order 42) at lane HEAD 6a8b09f28: after deleting artifact_core.emit_index_check_result, emit_index_write_result and emit_index_missing_dir_refusal, rg -n 'aggregate_index_results' agent_workflows tests tools prints only its own definition in agent_workflows/artifact_core.py. It aggregated per-type index CommandResults for 'aw index all', whose producers no longer exist. snin8q E-18 names only the three emit_index_* helpers, so it was left in place. Candidate owner: 9o83cr residual inventory or cxxmyv.
