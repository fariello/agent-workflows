- Id: dwe3jk
- Status: done
- Set: specaudit
- Priority: low
- Work-Kind: bug
- Summary: Runaway-escalation stderr warning ignores NO_COLOR and non-TTY streams

## Workflow history
- 2026-10-26 done (aw set): Fixed in the commit that filed this item; test_runaway_warning_honors_no_color fails on the old code and passes now; full core suite 1834 passed.
- 2026-10-26 created (aw backlog): Filed and fixed 2026-10-25 from the spec audit.

check_runaway_escalation (agent_workflows/runner_shared.py ~25365) printed a hardcoded \033[31m...\033[0m warning to stderr without calling should_color, so NO_COLOR, --no-color and piped stderr still received raw ANSI escapes (spec uonrjg color precedence). Found by the 2026-10-25 spec audit. Fixed in the same change: the message is wrapped in red only when should_color(stream) is true; tests test_runaway_warning_honors_no_color (fails on the old code) and test_runaway_warning_is_red_on_a_color_terminal in tests/test_question_drain.py.
