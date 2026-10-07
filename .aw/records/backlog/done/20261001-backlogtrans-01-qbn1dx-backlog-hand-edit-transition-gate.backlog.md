- Id: qbn1dx
- Status: done
- Graduated-To: backlogtrans
- Set: backlogtrans
- Priority: medium
- Work-Kind: chore
- Summary: Extend the hand-edit transition gate to backlog items once BACKLOG_TRANSITIONS exists, so an illegal backlog status move committed by hand is refused too

## Workflow history
- 2026-10-07 done (aw backlog): closed by aw agy run: IPD miimjb executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-backlogtrans-03-miimjb-refuse-a-staged-hand-edited-illegal-backlog-status-transitio.ipd.md); evidence .aw/records/plans/executed/20261002-backlogtrans-03-miimjb-refuse-a-staged-hand-edited-illegal-backlog-status-transitio.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: miimjb
- 2026-10-01 note (aw backlog): Split out of plan cc2m29 (Set backlogtrans), which closes the SETTER path only for backlog transitions. DEPENDS ON cc2m29: there is no BACKLOG_TRANSITIONS table to validate against until it lands, so this cannot be built first. DISTINCT FROM 4ynlcg, which extends the hand-edit gate for PLAN transitions; this is the backlog twin. The shipped backlog-blocking-close-gate hook is the nearest precedent but gates the release-gate done case ONLY and is blind to a hand-edited done -> open. Same honest limit applies: git hooks are local, not cloned, and skippable with --no-verify, so the portable authority is an aw check rule plus CI.
- 2026-10-01 created (aw backlog): Extend the hand-edit transition gate to backlog items once BACKLOG_TRANSITIONS exists, so an illegal backlog status move committed by hand is refused too
