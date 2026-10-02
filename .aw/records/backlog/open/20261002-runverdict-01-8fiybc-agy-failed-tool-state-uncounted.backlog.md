- Id: 8fiybc
- Status: open
- Set: runverdict
- Priority: low
- Work-Kind: chore
- Summary: An agy tool step in state FAILED is rendered to the operator but contributes to no analytics count, because the three readers accept different state tuples

## Workflow history
- 2026-10-02 created (aw backlog): An agy tool step in state FAILED is rendered to the operator but contributes to no analytics count, because the three readers accept different state tuples

FILED by plan `e08ssu` (Order 10, from backlog `2mjfo7`) as the durable carrier for a divergence that plan MEASURES and deliberately does NOT fix. It is NOT the duplication `2mjfo7` is about: the two analytics readers AGREE with each other here and both differ from the renderer, so unifying them preserves the gap rather than closing it.

WHAT DISAGREES. `run_dashboard._agy_line` and `verifier_corroboration.extract_session_commands` both accept only `state in ("DONE", "ERROR")`. `agy_runipd.render_agy_event` accepts `("DONE", "ERROR", "FAILED")` for both its `step_type == "tool"` and its `step_type == "subagent"` arms.

MEASURED CONSEQUENCE. An agy `step_update` of `step_type: "tool"`, `state: "FAILED"`, `tool_name: "run_command"` carrying `CommandLine: "python3 -m pytest"` yields `extract_session_commands` -> `commands=[]`, `missing_command_count=0`, and `session_stats` -> `tool_calls=0`, `commands={}`. The operator SEES the failed call in the stream; neither analytics surface counts it.

WHY `chore` AND NOT `bug`, stated so the classification can be disputed on its reasoning. The undercount is of FAILED calls only, and no measurement here shows a user waiting on or acting from the affected number: it understates `tool_calls`, `tool_errors` and the `commands` histogram in the dashboard rather than producing a wrong verdict. The repository's rule is explicit that an unmeasured hunch is not a bug, and no number was measured for a user-perceptible effect. NOTE THE ONE PATH THAT COULD RECLASSIFY IT: a verifier turn whose only test invocation FAILED would contribute zero observed commands, which can move `corroborate_verifier_turn` toward an `indeterminate` reason rather than a correct observation. That is fail-open and so not itself a wrong answer, but anyone who measures a verdict actually changing by it should re-file as `bug`.

SHAPE OF THE FIX. Reconcile the three accepted-state tuples deliberately, deciding whether a FAILED tool call is an observation (it ran and failed) or a non-event. Admitting it changes BOTH the dashboard's counts and the corroboration verdict's observed-command set, so it needs its own validation and must not ride along with a refactor. Plan `e08ssu`'s shared primitive `verifier_corroboration.tool_call_from_event` is the natural single place to make the decision once it lands.
