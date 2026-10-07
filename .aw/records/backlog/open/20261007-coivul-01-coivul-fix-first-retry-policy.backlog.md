- Id: coivul
- Status: open
- Blocks-Release: f33nrj
- Set: coivul
- Priority: high
- Work-Kind: bug
- Summary: Fix first: send every agent-caused run failure back to the agent with what went wrong, instead of failing the item or the run

## Workflow history
- 2026-10-07 created (aw backlog): Maintainer ruling 2026-10-07 (session on plan p47qfu / spec 25kzda 5.5, 5.7)

USER-PERCEPTIBLE IMPACT (the bug test): the maintainer reports losing HOURS on unattended runs that stopped on a failure an agent fixes in one turn when told what went wrong ("99% of the time the intervention is telling an agent to investigate and fix"). That is a correct-but-blocking path a human waits on.

MEASURED 2026-10-07 (code read, runner_shared.py / oc_runipd.py):
- The turn retry can never fire: `TURN_RETRYABLE_DISPOSITIONS == {'failed-safely'}` and nothing reaching `handle_turn_failure_retry` carries that token unaccompanied. Nonzero exit with no outcome file is scored `fail-gate` by `reconcile_disposition` rung 5 and is refused.
- Spawn failure (`DriverError`), stall/turn-limit, hook refusal of the finalize commit, hook refusal of an integration commit (recorded `merge-conflict`), and a red combined suite after merge all fail the item with no fix-it turn.
- Spec `25kzda` 5.5/5.7 lists push, hook bypass, unauthorized status change and out-of-scope mutation as never-retry/abort-run, but the code DETECTS none of push, hook bypass or untooled status changes, and AUTO-JUSTIFIES out-of-scope edits.
- Correction turns start a FRESH session; the spec says resume.
- Agent proposals (gate/tool must change, different approach) have no durable channel: outcome-file fields sit in the gitignored run dir and nothing surfaces them.

MAINTAINER RULINGS 2026-10-07: every agent-caused failure gets a fix-it turn naming what failed; the message says fix the cause, not the gate, and allows a small, clearly-a-bug fix to a gate or tool with a stated reason, otherwise propose; proposals are filed as a plan (small, no behavior change) or a backlog item (everything else) and the item stops needs-human while the run continues; out-of-scope edits go back as revert-or-justify, with the agent (not the runner) writing the reason and the plan recording a `- Scope-Exceeded:` flag; detect untooled status changes and hook bypass now, leave push detection to Set `denypush`; resume the agent's session where possible; keep per-kind retry budgets (global caps are `38hwvk`). Supersedes plan `p47qfu` (backlog `vmrhj0`).
