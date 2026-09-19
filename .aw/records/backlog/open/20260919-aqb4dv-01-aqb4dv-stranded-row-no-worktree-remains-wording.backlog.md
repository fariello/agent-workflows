- Id: aqb4dv
- Status: open
- Set: aqb4dv
- Priority: low
- Work-Kind: followup
- Summary: Decide whether a stranded-lane row should say 'no worktree remains' rather than silently omitting the worktree field

## Workflow history
- 2026-09-19 created (aw backlog): Decide whether a stranded-lane row should say 'no worktree remains' rather than silently omitting the worktree field

CARRIES OQ-03 of plan 0ta5vg (stranrep-01), which that plan left open and owned by the maintainer as a PRESENTATION choice rather than a correctness one.

BACKGROUND. Before 0ta5vg, every stranded-lane row printed a '.aw/worktrees/<id>' path whether or not the directory still existed (measured: 12 of 13 named an absent tree). 0ta5vg E-05 fixed the false assertion by OMITTING the segment when the path is absent, which is the minimum correct fix and matches the existing None-means-omit contract at attention.py:1277-1279.

THE OPEN QUESTION. Omission is silent: the reader cannot tell 'this row never had a worktree' from 'the worktree was reclaimed'. Saying 'no worktree remains' explicitly is genuinely useful, because it tells the reader that recovery is a BRANCH MERGE and not a tree inspection, which changes what they do next.

WHY IT IS NOT URGENT. Omission is already truthful and already shipped; this is an additive wording improvement, not a defect. Nothing is blocked on it.

DECISION OWNER: maintainer (presentation choice).

SCOPE IF ADOPTED: attention.stranded_lane_drift's detail assembly (the 'bits' list). Note F8a still forbids an absolute path in any surface, and spec F3a as amended by 0ta5vg now states that an absent worktree MUST NOT be rendered; adding an explicit 'no worktree remains' marker is compatible with both, since it names no path at all. Would also want a test asserting the marker appears only when the record HAD a worktree that is now absent, not when it never had one.
