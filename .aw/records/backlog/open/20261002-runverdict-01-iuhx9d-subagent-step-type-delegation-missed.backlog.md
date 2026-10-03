- Id: iuhx9d
- Status: open
- Blocks-Release: next
- Set: runverdict
- Priority: medium
- Work-Kind: bug
- Summary: verifier_corroboration misses the agy step_type subagent delegation shape, so a delegating agy verifier turn can be reported uncorroborated instead of indeterminate

## Workflow history
- 2026-10-02 created (aw backlog): verifier_corroboration misses the agy step_type subagent delegation shape, so a delegating agy verifier turn can be reported uncorroborated instead of indeterminate

FILED by plan `e08ssu` (Order 10, from backlog `2mjfo7`) as the durable carrier for a correctness gap that plan MEASURES and deliberately does NOT fix, because the fix changes a published verdict and a de-duplication chore has no authority to do that.

WHAT IS MISSED. `verifier_corroboration.extract_session_commands` detects delegation ONLY by matching a tool NAME against `SUBAGENT_TOOLS` inside a `step_update` whose `step_type == "tool"`. Antigravity also reports delegation as its OWN step type: `agy_runipd.render_agy_event` carries a dedicated `step_type == "subagent"` arm reading `subagent_info.subagents`, and `agy_runipd`'s module header states that "agy's stdout stream ALREADY carries `step_type == 'subagent'` events" (which is why its watchdog needs no separate progress observer). That shape never reaches the name check, so it is invisible.

MEASURED CONSEQUENCE. A `step_update` of `step_type: "subagent"`, `state: "DONE"` yields `extract_session_commands` -> `delegation_count=0`. `run_dashboard._agy_line` misses it identically (`tool_calls=0`, `categories={}`), so the dashboard also undercounts its own `subagent` category on agy.

WHY THIS IS A CORRECTNESS GAP IN THE MODULE'S OWN STATED CONTRACT, which is what makes it `bug`. `verifier_corroboration`'s docstring commits to a fail-open design in which a delegated turn resolves to `indeterminate` with reason `delegation-present`, because "Subagent tool calls do not appear in the parent session log, making commands unobservable". When the delegation is not DETECTED, that arm never fires: the turn reads its log fine, observes whatever non-delegated commands it ran, and can fall through to `uncorroborated`, i.e. a confident false accusation of fabrication against a verifier that genuinely delegated its test run. That is precisely the outcome plan `bjx20r` F-5(a) was designed to prevent, and the verdict is published on the attempt and the item and rendered by `run_viewer` as `corroboration: <verdict> (reason: <reason>)`, so the wrong answer is user-visible in `aw runs`.

SHAPE OF THE FIX. Treat an agy `step_type == "subagent"` step as a delegation in the shared reader, reading the same `subagent_info` `agy_runipd` already reads, and add a fixture for the shape (the existing `agy_session_*` fixtures do not contain it). Validate against the verdict, not only the count: the point is that such a turn reaches `indeterminate`/`delegation-present` rather than `uncorroborated`. Plan `e08ssu`'s shared primitive `verifier_corroboration.tool_call_from_event` is the natural home once it lands, and that plan's E-01 deliberately returns `None` for this shape today so the gap is preserved rather than silently changed.
