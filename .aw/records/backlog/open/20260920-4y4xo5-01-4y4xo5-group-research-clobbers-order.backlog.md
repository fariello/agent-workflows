- Id: 4y4xo5
- Status: open
- Blocks-Release: next
- Set: 4y4xo5
- Priority: medium
- Work-Kind: bug
- Summary: aw group research clobbers each record Order to 0 when --order is omitted (the e3hzyc defect in research_refs)

## Workflow history
- 2026-09-20 created (aw backlog): Filed while executing plan e3hzyc (F-12): the byte-identical defective line in the sibling backend, deliberately left out of that plan's fence.

MEASURED WHILE EXECUTING PLAN e3hzyc, whose fix covered agent_workflows/plans_refs.py ONLY.

research_refs.run_set_assign carries the byte-identical defective line that e3hzyc removed from plans_refs: it reads the flag with `start = getattr(args, "order", None)` and then collapses the absent case with `start_order=start if start is not None else 0` (agent_workflows/research_refs.py:326), against a planner whose signature default is also `start_order: int = 0` (:164) and which formats `order=f"{start_order + i:02d}"` (:181). So `aw group research <id6> --set X --apply` with NO --order renumbers every named research record from zero exactly as `aw group plans` did.

WHY IT WAS NOT FIXED THERE: e3hzyc's Scope-Paths fenced plans_refs.py, and its approval gate explicitly forbids both editing research_refs.py and extracting a shared helper across the two backends, because that would drag a second verb's behavior change inside a bug fix.

THE FIX SHAPE IS ALREADY PROVEN TWICE IN-REPO: plans_refs now resolves an absent flag per record (`_preserved_order`, front-matter Order then the filename NN), and artifact_rename.run_group_generic threads an Optional[int] so the name computer falls back to the filename's own NN. Either is a direct model.

ALSO IN SCOPE FOR THIS ITEM: the `aw research set-assign --order` help string documents the buggy default verbatim ("Starting NN (default 0).", agent_workflows/cli.py:2757). The shared rename/group string was updated by e3hzyc; this one was deliberately left alone.

SEVERITY NOTE: research records carry no orchestrator-reserved 00 slot the way plans do, so the user-visible harm is a silent renumber of a record set rather than a lint violation. It is still a repair verb corrupting what it repairs.
