- Id: fkmjoy
- Status: open
- Blocks-Release: next
- Set: fkmjoy
- Priority: low
- Work-Kind: bug
- Summary: check.scope-drift cannot audit a lane whose base diverged from its receipt's frozen base_head, so such an execution gets no scope advisory at all

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan wmnmei (rcptstale-01): measured on lc4unl, whose lane HEAD does not descend from its receipt's base.

MEASURED 2026-09-22 at HEAD 132e8333 while implementing rcptstale wmnmei.

check.scope-drift now measures the plan's ISOLATED LANE (maintainer ruling 2026-09-10, OQ-01 of plan wmnmei) and reports nothing when there is no usable lane. One shape of 'no usable lane' is a lane that EXISTS and holds real work but whose HEAD does not descend from the receipt's frozen base_head, so a base..HEAD diff across the fork would attribute main's own intervening commits to the plan. check_engine._plan_execution_tree therefore returns None and the plan is silent.

OBSERVED: of six plans holding a live begin receipt, lc4unl was exactly this shape. Its receipt froze base c49c9027; its lane aw/lane/lc4unl was created from 5421fc10 and its HEAD b1223b4f does not contain the frozen base (git merge-base --is-ancestor c49c9027 aw/lane/lc4unl exits 1). Its lane is classified HOLDS-WORK, so this is an execution in flight, not debris.

WHY THE DIVERGENCE IS LEGITIMATE AND NOT ITSELF THE BUG: worktree_lease.allocate_worktree deliberately does NOT adopt a STALE or HOLDS-WORK lane, it attempt-scopes a new one alongside, and its own docstring explains that adopting a lane cut from an older base 'makes main's own intervening commits appear in that delta and be attributed to this execution'. So lane and receipt can honestly disagree, and refusing to diff across the fork is correct.

THE GAP: nothing reconciles the two afterwards. The advisory's silence is the safe answer to an unanswerable question, but the consequence is that an in-flight execution of this shape has NO declared-scope check between begin and finalize. Finalize still reconciles scope, so this is a loss of EARLY feedback rather than of the authority boundary.

NOT A REGRESSION INTRODUCED BY wmnmei: before that change the same plan produced 18 findings, all of which named other agents' commits rather than its own work, so the pre-existing behavior was wrong in a different and louder way. This item records what is still missing after the correct fix.

CANDIDATE DIRECTIONS (design needed, none asserted here): (1) prefer the LANE's own recorded base (worktree_lease._lane_base_sha reads the branch creation reflog) over the receipt's base when the two diverge, so the diff is taken against the tree the lane was actually cut from; (2) have the runner re-issue the receipt when it attempt-scopes a lane, so receipt and lane never disagree; or (3) report a distinct advisory saying scope could not be audited for this execution, which the maintainer explicitly declined for the no-lane case (OQ-01) but which may read differently for a lane that demonstrably exists.
