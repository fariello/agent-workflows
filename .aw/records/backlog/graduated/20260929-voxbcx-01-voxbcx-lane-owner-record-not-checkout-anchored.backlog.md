- Id: voxbcx
- Status: graduated
- Graduated-To: voxbcx
- Set: voxbcx
- Priority: low
- Work-Kind: chore
- Summary: worktree_lease._owner_record_path composes from the passed root while ipd_lifecycle.receipt_dir anchors on the checkout, so read_lane_owner returns None when called from inside a lane

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053024Z-3198670: tjags7
- 2026-09-29 created (aw backlog): Filed as the durable carrier for a deferred obligation in plan iqtt8d (Set fkmjoy), which measured the asymmetry while fixing check.scope-drift lane resolution.

MEASURED 2026-09-29 while authoring plan `iqtt8d` (backlog `fkmjoy`).

THE ASYMMETRY. Two neighbouring state stores under `.aw/` anchor DIFFERENTLY:

* `ipd_lifecycle.receipt_dir` anchors on the CHECKOUT via `checkout_control_root` (`git rev-parse --git-common-dir`), so a begin receipt written from a lane worktree lands in the one shared store. That was deliberate, fixed under backlog `dh0uno`, whose docstring records the measured defect: an inner `aw` running inside a lane wrote to `<lane>/.aw/state/...`, 'a second control store the driver could not see and lane teardown then deleted'.
* `worktree_lease._owner_record_path` composes `repo_root / OWNERS_SUBDIR / <lane>.json` from the PASSED root, with no such anchoring.

MEASURED, both directions, on the live checkout:

    read_lane_owner(<main>,  'om3rzi:attempt2') -> record present (True)
    read_lane_owner(<lane>,  'om3rzi:attempt2') -> None
    _owner_record_path(<lane>, 'om3rzi:attempt2')
      = <lane>/.aw/worktrees/.owners/om3rzi_attempt2.json   (does not exist)

while `receipt_dir(<main>)` and `receipt_dir(<lane>)` both return the single checkout-anchored `.aw/state/ipd-lifecycle`.

WHY THIS IS FILED AS A CHORE AND NOT A BUG. No in-tree caller reached at authoring is believed to be affected: `read_lane_owner`, `write_lane_owner`, `clear_lane_owner`, `lane_is_safe_to_adopt` and `lane_owned_by_other_live_process` are called from allocation, reclamation and the liveness guard, all of which run from the main checkout, where the two anchorings agree. So this is a LATENT inconsistency with no measured user-visible symptom, which is why it is not gated. That claim is the part most worth re-checking before acting: it was established by reading call sites, not by exhaustive execution, and an in-lane `aw` invocation that grows an ownership query would silently read an empty store.

WHAT MAKES IT MORE THAN A STYLE POINT. The failure mode is the dangerous kind rather than a loud one. `read_lane_owner` returns `None` on an unreadable or absent record, and `lane_is_safe_to_adopt` maps a MISSING record to 'adoptable' ('no owner record; unclaimed'), because records are only ever written by an allocating driver. So a caller asking from the wrong anchor does not get an error; it gets 'this lane is unclaimed', which is precisely the answer the E-08 liveness gate exists to prevent when a LIVE process owns the lane. The distinction between 'no record' and 'record I cannot see' is real and is currently unrepresentable.

WHY IT IS NOT FIXED IN `iqtt8d`. Changing the anchoring MOVES where every owner record lives, so it needs a migration story covering existing records, plus the teardown and reclamation paths that consume them (`clear_lane_owner` on teardown, `reclaim_lanes_on_interrupt`). That is well outside an advisory-resolution plan's concern. It constrained that plan's design only negatively: its new lane resolver enumerates GIT REFS rather than reading owner records, precisely so it cannot depend on this.

CONSTRAINT ON ANY FIX. `worktree_lease` is deliberately STDLIB-ONLY with no package-level import (see the module header note and the function-local import in `lane_merged_into_target`), and `inspect_lane` is pinned RUN-CONTEXT-FREE. `checkout_control_root` currently lives in `ipd_lifecycle`, which imports nothing from `worktree_lease` at module level but is a package module; a naive fix that imports it at module level in `worktree_lease` would violate that constraint. Either use a function-local import or lift the helper somewhere both can reach.

CANDIDATE DIRECTIONS (none asserted): (1) anchor `_owner_record_path` on the checkout the way `receipt_dir` does, with a read-time fallback to the legacy lane-local path so existing records stay visible; (2) leave the anchoring alone and document the constraint at each owner function, on the ground that every caller is a driver running from the main tree; (3) distinguish 'absent' from 'unreachable' in `lane_is_safe_to_adopt` so a wrong-anchor read fails safe instead of reporting the lane unclaimed.
