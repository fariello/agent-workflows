- Id: 1kebul
- Status: open
- Blocks-Release: next
- Set: runverdict
- Priority: medium
- Work-Kind: bug
- Summary: Three agy session-log readers use three different tool-name precedences, so one step can be a delegation to one reader and a shell command to another

## Workflow history
- 2026-10-02 created (aw backlog): Three agy session-log readers use three different tool-name precedences, so one step can be a delegation to one reader and a shell command to another

FILED by plan `e08ssu` (Order 10, from backlog `2mjfo7`) as the durable carrier for a divergence that plan MEASURES and deliberately does NOT fix, because resolving it changes a published verdict and is outside a de-duplication chore.

WHAT DISAGREES. Three readers answer 'which key names this agy tool call?' three different ways. `agy_runipd.render_agy_event` reads `tool_info.get("name") or step.get("tool_name")`. `agy_view` reads `update.get("tool_name") or info.get("name")`, the OPPOSITE precedence. Both analytics readers (`run_dashboard._agy_line` and `verifier_corroboration.extract_session_commands`) read `tool_name` ONLY and ignore `tool_info.name` entirely. `runner_stop.event_label` reads `info.get("name") or step.get("tool_name") or step.get("step_type")`.

MEASURED CONSEQUENCE. On a step carrying `tool_name="run_command"` and `tool_info.name="browser_subagent"`, both analytics readers report a shell command of kind `test` and `delegation_count=0`, while `agy_runipd`'s precedence would call the same step `browser_subagent`. So the SAME step is a test invocation to the corroboration verdict and a subagent delegation to the renderer.

WHY `bug` AND NOT `chore`. A delegation read as a shell command is exactly the input that turns `corroborate_verifier_turn`'s fail-open `indeterminate` (reason `delegation-present`) into an observed-command comparison that can reach `uncorroborated`. That verdict is published on the attempt and the item and is rendered by `run_viewer` as `corroboration: <verdict> (reason: <reason>)`, so a wrong answer is user-visible in `aw runs` and accuses a verifier of fabrication. The classification rests on that user-visible wrong answer, not on the redundancy.

THE SHAPE IS REAL, NOT HYPOTHETICAL. `tool_info.name` is the only name key used in `tests/test_runner_stop_triggers_e2e.py` (`"tool_info": {"name": "run_command"}`), so a live test already constructs the shape both analytics readers ignore.

SHAPE OF THE FIX. Pick ONE precedence, state why, and route all four readers through it; plan `e08ssu` adds the shared primitive `verifier_corroboration.tool_call_from_event` that is the natural home for the decision. Decide deliberately: changing the analytics readers to prefer `tool_info.name` CHANGES a published verdict for the measured shape, so the change needs its own validation rather than riding along with a refactor.
