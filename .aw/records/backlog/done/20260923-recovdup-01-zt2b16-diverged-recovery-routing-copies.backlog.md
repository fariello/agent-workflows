- Id: zt2b16
- Status: done
- Graduated-To: recovone
- Blocks-Release: next
- Set: recovdup
- Priority: high
- Work-Kind: bug
- Summary: runner_shared carries its own diverged copy of classify_recovery_disposition and build_verify_and_continue_notice, so recovery routing has two disagreeing implementations

## Workflow history
- 2026-09-25 set (aw backlog): closed by aw oc run: IPD cdxcbh executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260924-recovone-01-cdxcbh-give-classify-recovery-disposition-build-verify-and-continue.ipd.md); evidence .aw/records/plans/executed/20260924-recovone-01-cdxcbh-give-classify-recovery-disposition-build-verify-and-continue.ipd.md
- 2026-09-25 graduated (aw set): graduated into recovone plan cdxcbh (to-review); plan also covers 2t4v1j
- 2026-09-23 set (aw backlog): status -> open
- 2026-09-23 created (aw backlog): Found while executing runnerlayer 02 (1f7xno). runner_shared defines classify_recovery_disposition (:22052) and build_verify_and_continue_notice (:20437) while oc_runipd defines its own (:4893, :5025) and agy_runipd delegates to OC's by a lazy import. Measured: the docstring-stripped AST bodies DIFFER. The shared classify_recovery_disposition calls lane_branch_tip and matches snapshots by subj.startswith('wip(snapshot):') while oc's calls worktree_lease.commit_subject_is_interrupted_snapshot; it also reads st.path/st.base_commit where oc reads st.worktree_path/lane_base, and it drops oc's not-st.exists and not-st.head guards entirely. So which routing verdict a recovery turn gets depends on which copy the call site resolved. runner_shared.execute_item_core rebinds route_recovery_turn off driver_module (so a host override wins there), but nothing rebinds the two names above. This is the class (d) reconciliation 818uru deferred behind lanectn, and it is why 1f7xno deferred these three names rather than moving them.

## Measured harder while executing 1f7xno: the shared copy is DEAD ON ARRIVAL, not merely diverged

`runner_shared.classify_recovery_disposition` cannot run at all against a live lane. It reads
`st.path` and `st.base_commit` off the `worktree_lease.LaneState` returned by `inspect_lane`, and
that NamedTuple has neither field:

    LaneState._fields == ('lane_id', 'state', 'branch', 'branch_exists', 'worktree_path',
                          'worktree_registered', 'head', 'base_sha', 'requested_base',
                          'commits_ahead', 'dirty', 'owner', 'owner_live', 'merged_into_target')

So every call reaching a lane that exists raises `AttributeError: 'LaneState' object has no
attribute 'path'`. The host copy in `oc_runipd` reads `st.worktree_path` and the caller's
`lane_base`, which are the real fields.

WHY NOBODY NOTICED: nothing called the shared copy. `oc_runipd` defined its own,
`agy_runipd` delegated to oc's, and `execute_item_core` rebinds `route_recovery_turn` off
`driver_module`, so the shared pair was unreachable in every shipped path. It is dead code that
LOOKS like a shared implementation, which is worse than an absent one because a later plan
consolidating onto it (as `1f7xno` attempted for `route_recovery_turn`) silently adopts a body
that cannot work. Measured live 2026-09-23 by calling it through the consolidated
`route_recovery_turn`: four tests in `tests/test_resumedupe.py` failed with that AttributeError.

CONSEQUENCE FOR `1f7xno`: `route_recovery_turn` is NOT consolidated after all. Its two copies are
AST-identical, so the consolidation looked safe, but the shared one resolves
`classify_recovery_disposition` in `runner_shared`'s namespace and therefore reaches the broken
sibling. The three recovery-routing names are all deferred together, which is the correct unit.

THE FIX IS A RECONCILIATION, not a move: decide which body is authoritative (the host's, on this
evidence), delete the other, and have both hosts bind the survivor. That is out of a pure-move
plan's scope, which is why this item exists.
