- Id: 2mjfo7
- Status: graduated
- Graduated-To: runverdict
- Set: runverdict
- Priority: low
- Work-Kind: chore
- Summary: Unify run_dashboard's two per-host session-log tool-call readers onto the shared verifier_corroboration extractor

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: e08ssu
- 2026-09-30 created (aw backlog): Filed as the durable carrier for a duplication plan bjx20r identifies and deliberately leaves in place

FILED as the durable carrier for a duplication plan `bjx20r` (Order 08, from backlog `5xgllt`) IDENTIFIES and deliberately does NOT fix, so the residue outlives that plan's execution.

WHAT IS DUPLICATED. `bjx20r` adds `agent_workflows/verifier_corroboration.py`, whose reader extracts per-host tool calls from a run's session JSONL: OpenCode's `tool_use` part (`part.tool`, `part.state.input.command` for `bash`, `part.state.status == "error"`) and Antigravity's `step_update` of `step_type == "tool"` (`tool_name`, `tool_info.parameters.CommandLine` for `run_command`, `state == "ERROR"`). `run_dashboard._oc_line` and `run_dashboard._agy_line` read EXACTLY those keys already, per host, discriminated the same way (`"event" in obj` -> agy, `"type" in obj and "part" in obj` -> oc, in `run_dashboard.session_stats`). So the per-host key knowledge exists twice after that plan lands.

WHY `bjx20r` DID NOT UNIFY THEM, recorded so this item is not re-argued from scratch. The two existing functions are PRIVATE, they MUTATE a stats dict in place rather than returning records, and they DISCARD the command text immediately (`run_dashboard._record_tool` stores only `command_kind(command)`), so there is nothing reusable without rewriting them. `run_dashboard` is also an analytics module that imports `run_analytics_spa`, and unifying would have put an analytics module plus `tests/test_run_dashboard.py` into a plan whose subject is a verification gate, for zero behavior change. The duplication is roughly twenty lines of key access per host.

WHY IT IS STILL WORTH FILING. The duplication is the kind `runner_shared`'s own module header warns about in general terms: two identical readers have no behavioral disagreement TODAY, which is exactly why nothing signals when one is updated for a new host event shape and the other is not. A host that changes where it records a command would then be read correctly by one consumer and silently wrongly by the other.

SHAPE OF THE FIX. Have `run_dashboard._oc_line` / `_agy_line` obtain their tool records from the shared extractor and keep their own aggregation, rather than moving aggregation into the shared module. Low priority and NOT release-gating: no user-visible defect exists today, which is why this is `chore` and not `bug`.
