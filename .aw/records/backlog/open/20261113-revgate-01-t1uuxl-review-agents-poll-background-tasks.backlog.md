- Id: t1uuxl
- Status: open
- Set: revgate
- Priority: medium
- Work-Kind: chore
- Summary: Review agents push long commands to the background and poll them, costing cached tokens; the review prompt should require foreground commands and no polling

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-14 created (aw backlog): Review agents push long commands to the background and poll them, costing cached tokens; the review prompt should require foreground commands and no polling

## Observed

run-20261114T011406Z-590956 (review sweep): 42 manage_task calls (32 status, 8 list, 2 kill) and 4 five-second schedule timers, mostly while waiting on `aw check plans` (over 2 minutes) or pytest. Each poll replays the whole context, so the maintainer measured about 34.8M cached tokens across 268 checks in the sweeps.

## Cause

The execute prompt already tells the agent to run every command it needs the result of in the FOREGROUND (runner_shared.py, execute prompt), but build_review_prompt carries no such rule.

## Fix

Add the same foreground rule to the review prompt, plus: do not poll a background task with status or timer calls. Timeouts are unaffected: the 30-minute stall watchdog counts command output and the aw suite heartbeat as progress.
