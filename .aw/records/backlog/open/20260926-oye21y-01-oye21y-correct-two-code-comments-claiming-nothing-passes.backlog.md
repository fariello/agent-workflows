- Id: oye21y
- Status: open
- Set: oye21y
- Priority: low
- Work-Kind: chore
- Summary: Correct two code comments claiming nothing passes AW-Run/AW-Item trailers

## Workflow history
- 2026-09-26 created (aw backlog): Correct two code comments claiming nothing passes AW-Run/AW-Item trailers

Two code comments repeat the false claim that nothing passes commit trailers, even though driver-side commit sites pass them:

1. agent_workflows/run_evidence.py (symbol RUN_FINDING_CODES['RUN-COMMIT-CONTENTS'].waiting_on): states that nothing in the tree passes trailers yet.
2. agent_workflows/ipd_lifecycle.py (attribution docstring in _scope_attributed_commits): states essentially no commit in history carries one yet, so nothing can be consumed today (backlog a8eufb).

The pointer to backlog a8eufb is dead because a8eufb is done (wired by executed plan wao266).
The correct statement for both locations is: driver-side sites pass them; nothing reads them back.
