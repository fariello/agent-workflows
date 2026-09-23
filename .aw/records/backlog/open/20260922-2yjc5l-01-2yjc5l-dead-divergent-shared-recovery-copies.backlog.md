- Id: 2yjc5l
- Status: open
- Blocks-Release: next
- Set: 2yjc5l
- Priority: medium
- Work-Kind: bug
- Summary: Three runner symbols keep a DEAD and DIVERGENT runner_shared copy the hosts never reach, one of which changes which commits count as snapshots

## Workflow history
- 2026-09-22 created (aw backlog): Three runner symbols keep a DEAD and DIVERGENT runner_shared copy the hosts never reach, one of which changes which commits count as snapshots

MEASURED 2026-09-23 at HEAD 2d04ef8b while executing IPD gqo6if (runresidue 01). Reported rather than fixed, per that plan's OQ-02.

`python3 tools/runner_fork_scan.py --triples` reports SIX three-way forks, where a symbol is
defined in BOTH hosts AND in `runner_shared` while the hosts ignore the shared copy. Three of them
are the recovery-routing trio, and they are the concerning ones because `agy_runipd` delegates to
`oc_runipd` (a PEER HOST, not the shared library) while a shared copy sits unused:

    route_recovery_turn                shared copy identical to the hosts': True
    classify_recovery_disposition      shared copy identical to the hosts': False
    build_verify_and_continue_notice   shared copy identical to the hosts': False

THE DIVERGENCE THAT MATTERS is `classify_recovery_disposition`. The copy the drivers actually run
classifies a preserved mid-edit commit with
`worktree_lease.commit_subject_is_interrupted_snapshot(subject)`; the dead shared copy uses
`subj.startswith('wip(snapshot):')`. Those are not the same predicate, so the two bodies disagree
about which commits are snapshots, and therefore about whether a recovery turn is dispatched as
VERIFY-AND-CONTINUE or as a FRESH EXECUTION. A later 'tidy-up' that simply points the hosts at the
shared copy (the obvious reading of the unification directive) would silently change recovery
routing on BOTH hosts. The shared copy also builds its `RecoveryDisposition` with different fields
(`st.path` against `st.worktree_path`, no `_lane_commit_subjects` empty-list guard).

WHY THIS IS NOT JUST DEDUPLICATION WORK: `tests/test_runner_layering.py` classifies all three
NEUTRAL/LAZY_WRAPPER (host-agnostic, movable) and lists `build_verify_and_continue_notice` in
`MOVE_UNSETTLED` with its DESTINATION CONTESTED between `runner_shared` and `render_stream`,
assigned to `runnerlayer` Order 02 (`1f7xno`). So the MOVE has an owner. What has no owner is the
dead divergent copy sitting in `runner_shared` in the meantime, which is a live trap for whoever
performs that move.

SUGGESTED FIX, in this order: (1) decide which snapshot predicate is correct (a product question,
maintainer's call); (2) reconcile the shared body to it; (3) then let `1f7xno` make the hosts
delegate. Doing (3) first is the hazard. Note `dispatch_turn` already binds `route_recovery_turn`
with `getattr(driver_module, ..., globals().get(...))`, so the shared copy is reachable as a
FALLBACK, which is how a future host with no copy of its own would silently get the divergent
logic.
