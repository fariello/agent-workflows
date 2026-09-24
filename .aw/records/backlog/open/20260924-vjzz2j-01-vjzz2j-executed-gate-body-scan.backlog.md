- Id: vjzz2j
- Status: open
- Blocks-Release: next
- Set: vjzz2j
- Priority: medium
- Work-Kind: bug
- Summary: executed_transition_gate._has_executed_status checks entire file rather than top metadata header, refusing commits with quoted status lines

## Workflow history
- 2026-09-24 created (aw backlog): executed_transition_gate._has_executed_status checks entire file rather than top metadata header, refusing commits with quoted status lines

In agent_workflows/hooks/executed_transition_gate.py, _has_executed_status(text) checks every line in text with line.strip().lower() == _STATUS_EXECUTED_LINE or _STATUS_DONE_LINE. When a plan contains quoted status lines or evidence blocks (e.g. in backticks or indented blocks) mentioning '- Status: done' or '- Status: executed', this predicate returns True even when the plan's metadata header at the top of the file has Status: approved. The hook ipd-executed-transition-gate then incorrectly refuses commits on pending plans containing such body text.
