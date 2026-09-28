- Id: sj4zte
- Status: open
- Blocks-Release: next
- Set: reattclose
- Priority: medium
- Work-Kind: bug
- Summary: integrate_retired_lane closes its backlog item in the shared checkout after tearing its lane down, the same defect as a4em7s at a second call site

## Workflow history
- 2026-09-28 created (aw backlog): Filed while authoring pjuoyj (graduates a4em7s); measured, see body.

MEASURED 2026-09-28 at HEAD 0df0b094 while authoring plan pjuoyj (which graduates a4em7s and fixes the SIBLING site).

WHAT IS WRONG. `runner_shared.integrate_retired_lane` publishes a lane whose turn RETIRED its plan in-lane, and then closes the plan's backlog item by calling `process_backlog_close(run_dir, state, item)` with NO `lane_repo`/`lane_handle`, so the setter's move and its commit happen in the SHARED CHECKOUT. That is the same defect `a4em7s` records for `retry_deferred_integrations._finish`, at a different call site, and it has the same cause: the lane is already gone. MEASURED by locating both calls in the function's own source, the `lane_containment.teardown_lane_if_classified` call PRECEDES the `process_backlog_close` call in the same body (offsets 4567 and 4974 within the function source), so by the time the close runs there is no lane left to write in.

WHY IT MATTERS, with the harm measured on the shared helper rather than assumed. The success arm commits on main (one parent, and that parent is main's tip). The FAILURE arm is worse: with a rejecting pre-commit hook, `commit_backlog_close` returns None and main is left reading `D <graduated path>` plus `?? <done path>`, with the item on disk at `done/` while HEAD still records it at `graduated/`. `runner_shared.dirty_tree_overlap` returns that exact path when a later lane's incoming change names it, which is the mechanism `process_backlog_close`'s own docstring records as having refused 27 of 42, 23 of 41 and 18 of 43 remaining queue items across three consecutive runs on 2026-09-13.

HOW OFTEN. Only for a RETIRED-in-lane item that also carries a backlog item, which is rarer than the ordinary executed path. Note this site is NOT guarded on the `backlog_close.closed` predicate the way `_finish` and `finish_reintegrated_item` are, so it is reached unconditionally on the retired-and-integrated arm.

SUGGESTED FIX: the same one pjuoyj builds for a4em7s. Once that plan's coordinator-worktree close performer exists, route this call through it too, so the move and commit happen in a throwaway worktree and reach main as one fast-forward ref update. Deliberately NOT folded into pjuoyj: that plan is scoped to the site its own backlog item names, and widening it to every `process_backlog_close` caller would multiply the blast radius of a change to the runner's most load-bearing write path.

RELATED BUT DISTINCT, so this item is not the place for them. The no-lane self-finalize arm (`self_finalize and not work_dir`) writes to the shared checkout because that genuinely IS its execution tree, so it is correct rather than defective. `finish_reintegrated_item` runs on the out-of-band `--retry-incomplete` / `integrate` verb recovery path, not mid-run, so its write to main is an operator-initiated action rather than a run contaminating its own base.
