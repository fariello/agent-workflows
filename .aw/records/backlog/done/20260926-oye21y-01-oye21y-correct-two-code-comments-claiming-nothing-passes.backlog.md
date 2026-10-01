- Id: oye21y
- Status: done
- Graduated-To: oye21y
- Set: oye21y
- Priority: low
- Work-Kind: chore
- Summary: Correct two code comments claiming nothing passes AW-Run/AW-Item trailers

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw agy run: IPD 2lxcwt executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-oye21y-01-2lxcwt-correct-the-stale-trailer-consumption-claims-in-run-evidence.ipd.md); evidence .aw/records/plans/executed/20260930-oye21y-01-2lxcwt-correct-the-stale-trailer-consumption-claims-in-run-evidence.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 2lxcwt
- 2026-09-26 created (aw backlog): Correct two code comments claiming nothing passes AW-Run/AW-Item trailers

Two code comments repeat the false claim that nothing passes commit trailers, even though driver-side commit sites pass them:

1. agent_workflows/run_evidence.py (symbol RUN_FINDING_CODES['RUN-COMMIT-CONTENTS'].waiting_on): states that nothing in the tree passes trailers yet.
2. agent_workflows/ipd_lifecycle.py (attribution docstring in _scope_attributed_commits): states essentially no commit in history carries one yet, so nothing can be consumed today (backlog a8eufb).

The pointer to backlog a8eufb is dead because a8eufb is done (wired by executed plan wao266).
The correct statement for both locations is: driver-side sites pass them; nothing reads them back.
