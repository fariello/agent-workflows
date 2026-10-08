- Id: rayd4c
- Status: done
- Graduated-To: rayd4c
- Set: rayd4c
- Priority: low
- Work-Kind: chore
- Summary: Remove the dead cli._completion_configured, which has had zero production callers since 4y95tp replaced it with _completion_state

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD yi24m0 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-rayd4c-01-yi24m0-delete-the-dead-cli-completion-configured-and-prove-no-calle.ipd.md); evidence .aw/records/plans/executed/20261001-rayd4c-01-yi24m0-delete-the-dead-cli-completion-configured-and-prove-no-calle.ipd.md
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: yi24m0
- 2026-09-29 created (aw backlog): Remove the dead cli._completion_configured, which has had zero production callers since 4y95tp replaced it with _completion_state

FOUND while authoring plan s2yf26 (Set lz16f3), whose F-08 measured it and whose Deferred section declines to delete it in scope.

MEASURED: `grep -rn "_completion_configured" --include="*.py" .` returns exactly three hits and NONE is a call: the definition in `agent_workflows/cli.py`, a docstring reference inside its successor `cli._completion_state`, and a docstring line in `tests/test_completion.py`. Plan 4y95tp superseded it by widening the PRESENCE question into the three-state `absent`/`current`/`stale` classification, so `_completion_state` is the live predicate and this one is unreachable.

WHY IT WAS NOT DONE IN s2yf26: deleting a function is a different concern from adding a reporting surface, and AGENTS.md forbids broadening scope opportunistically. That plan's E-06 corrects the actively MISLEADING part (the test docstring still describing `_completion_configured` as the composing predicate) and deliberately leaves the code alone.

SCOPE OF THE FIX: delete `cli._completion_configured`, drop the now-pointless back-reference from `cli._completion_state`'s docstring, and confirm the suite still passes. Low value, near-zero risk, and it should follow s2yf26 rather than race it, since both touch the same neighborhood of `cli.py`.
