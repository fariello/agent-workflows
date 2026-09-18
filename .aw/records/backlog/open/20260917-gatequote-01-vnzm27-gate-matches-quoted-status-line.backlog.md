- Id: vnzm27
- Status: open
- Set: gatequote
- Priority: medium
- Work-Kind: bug
- Summary: executed_transition_gate reads a QUOTED status-executed line inside a fenced evidence block as the plan's own terminal status

## Workflow history
- 2026-09-17 created (aw backlog): executed_transition_gate reads a QUOTED status-executed line inside a fenced evidence block as the plan's own terminal status

MEASURED 2026-09-18 at HEAD 36129255 while executing integpath child 05 (3v7wo6).

A plan whose V-item evidence QUOTES another artifact's status line (which is exactly what a
verification plan's pasted evidence looks like) is refused by the pre-commit hook:

  no raw plan->executed commit (use aw ipd finalize)....Failed
  .../20260907-integpath-05-3v7wo6-....ipd.md (3v7wo6): raw plan->executed transition
  (gained '- Status: executed') with NO matching finalize evidence in .aw/state/.

The plan's OWN '- Status:' was 'approved' throughout. What tripped the gate was pasted evidence
inside a fenced code block, quoting the four child plans' real "grep -m1 '^- Status:'" output.

CAUSE: _has_executed_status (agent_workflows/hooks/executed_transition_gate.py:89-97) iterates
lines, applies line.strip().lower(), and compares the whole line to '- status: executed'. Stripping
indentation is what makes a quoted line indistinguishable from a real metadata line, and the function
has no notion of fenced blocks, so any indented or fenced quotation of that exact text matches.

WHY THIS MATTERS: it penalizes precisely the behavior the execution contract demands. Plans are told
to paste ACTUAL output rather than claim success, and a whole-Set verification plan's evidence is
mostly other artifacts' status lines. The workaround is to reformat the evidence (print id6 and
status on one line), which is lossy: the pasted output no longer matches the command a reader would
re-run.

The gate is otherwise correct and MUST NOT be relaxed or bypassed; --no-verify was not used.

Candidate fix: make the scan fence-aware (skip lines inside fenced blocks), or anchor the match to a
line with NO leading whitespace, which is what a real metadata line has. The second is the smaller
change and preserves the hand-edit detection the gate exists for, since a genuine status line is
never indented.
