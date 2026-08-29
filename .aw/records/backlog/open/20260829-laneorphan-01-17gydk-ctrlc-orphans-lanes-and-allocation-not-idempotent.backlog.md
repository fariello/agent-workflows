- Id: 17gydk
- Status: open
- Blocks-Release: next
- Set: laneorphan
- Priority: high
- Kind: bug
- Summary: CTRL-C orphans lane worktrees/branches and lane allocation is not idempotent, so every later aw oc run of that Set dies on 'a branch named aw/lane/<id6> already exists' until someone clears them by hand

## Workflow history
- 2026-08-29 created (aw backlog): CTRL-C orphans lane worktrees/branches and lane allocation is not idempotent, so every later aw oc run of that Set dies on 'a branch named aw/lane/<id6> already exists' until someone clears them by hand

OBSERVED 2026-08-29 (twice today): a CTRL-C during 'aw oc run wtiso' left five lane branches + worktrees behind (aw/lane/{8zgybk,qcqhj7,rchpms,7p9n2v,58ha43}). The next 'aw oc run wtiso' then failed EVERY lane at allocation:
  worktree allocation failed; not launching. git worktree add failed for lane '8zgybk': fatal: a branch named 'aw/lane/8zgybk' already exists
The run is permanently wedged until a human removes the worktrees and branches. Recovery required inspecting each lane by hand (four were empty; 8zgybk held ~1180 lines of real Phase-0 work that had to be merged before cleanup).

TWO DEFECTS, both needed:

(a) NO INTERRUPT CLEANUP. The driver allocates the lane (worktree_lease.allocate_worktree -> 'git worktree add -b aw/lane/<id6> .aw/worktrees/<id6>') but SIGINT/SIGTERM does not run teardown or reconciliation, so the lane leaks. Note the correct behavior is NOT blind teardown: a lane may hold unmerged work (8zgybk did), so interrupt handling must PRESERVE-AND-RECORD (leave the branch, register it in the ledger as recoverable, report it) rather than force-remove. This is the graceful-quit invariant from backlog kjzlgw ('every stop leaves the system COHERENT... partial worktree edits quarantined/restored'); if kjzlgw is implemented first, this item is its lane-specific acceptance test.

(b) ALLOCATION IS NOT IDEMPOTENT. Even with perfect cleanup, hitting an existing lane for the SAME id6 must not be a hard failure. allocate_worktree should ADOPT/REUSE an existing lane whose branch+worktree already match that id6 (verifying its base and that it is not another live run's), or allocate a fresh attempt-scoped name, instead of aborting the step. A resumable run especially must tolerate its own leftover lane - today 'aw oc run resume' cannot get past its own debris.

FIX SKETCH: (1) install an interrupt handler that, per allocated lane, records a ledger event, leaves any lane with commits or dirty files intact and clearly reported as recoverable, and tears down only provably-empty lanes; (2) make allocation adopt-or-attempt-scope rather than fail (attempt-scoped names are already recommended by research x03wgn: 'branch: aw/lane/<run-id>/<lane-id>/<attempt-id>'); (3) add 'aw doctor --lanes' / 'aw recover' surfacing so orphans are discoverable without git spelunking. Apply to BOTH oc_runipd and agy_runipd.

TEST: (1) start a run, send SIGINT mid-lane, assert the ledger records each allocated lane, empty lanes are gone, a lane with work is PRESERVED and reported, and a subsequent run of the same Set allocates successfully (no 'already exists'); (2) with a pre-existing lane branch for the same id6, allocation adopts or attempt-scopes rather than failing the step; (3) assert a lane holding commits is NEVER force-removed by cleanup.

RELATED: kjzlgw (graceful-quit protocol, the general case), x03wgn Section 4/7 (attempt-scoped lane naming, orphaned-worktree recovery invariants).
