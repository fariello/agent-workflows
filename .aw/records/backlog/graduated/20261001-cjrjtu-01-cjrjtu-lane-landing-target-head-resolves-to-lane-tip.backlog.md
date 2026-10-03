- Id: cjrjtu
- Status: graduated
- Graduated-To: cjrjtu
- Blocks-Release: next
- Set: cjrjtu
- Priority: high
- Work-Kind: bug
- Summary: lane_work_has_landed defaults target to the symbolic HEAD, so run from inside a lane it resolves to the lane's own tip and reports UNMERGED work as merged, making inspect_lane report reclaimable=True on work that reached nothing

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: 3mv7li
- 2026-10-01 created (aw backlog): Filed while authoring the plan graduating backlog voxbcx: verifying that item's anchoring claims surfaced a second, independent and more dangerous anchoring defect in the landing predicate's default target.

MEASURED 2026-10-01 at HEAD `faf47d81a` (git 2.43.0) while authoring the plan that graduates backlog `voxbcx`.

THIS IS A SECOND, INDEPENDENT ANCHORING DEFECT, found while verifying `voxbcx`'s claims, and it is
strictly WORSE than `voxbcx`: where `voxbcx` makes a lane look UNCLAIMED, this makes UNMERGED WORK look
RECOVERED, which is the one false positive `LaneState.reclaimable`'s own docstring says must never occur
("a false True there is what would authorize destroying unproven work").

THE MECHANISM. `runner_shared.lane_work_has_landed(repo, branch, target=...)` defaults `target` to
`LANE_INTEGRATION_TARGET_FALLBACK`, which is the literal string `"HEAD"`, and runs
`git merge-base --is-ancestor <branch> <target>` with `cwd=repo`. When `repo` IS the lane worktree,
`HEAD` resolves to the LANE'S OWN TIP, so the lane is trivially its own ancestor and the predicate
answers True for work that has reached nothing.

MEASURED, both directions, on a purpose-built checkout with one unmerged lane commit:

    git rev-parse HEAD in main = 1bb9b96bac
    git rev-parse HEAD in lane = 1987047f77
    lane branch tip            = 1987047f77

    merge-base --is-ancestor <branch> HEAD, run in lane -> rc 0   (ancestor)
    merge-base --is-ancestor <branch> HEAD, run in main -> rc 1   (NOT ancestor)

    lane_work_has_landed(main, branch) -> False     (correct)
    lane_work_has_landed(lane, branch) -> True      (WRONG)
    lane_merged_into_target(main, branch) -> False
    lane_merged_into_target(lane, branch) -> True

    inspect_lane(main): merged_into_target=False reclaimable=False   (correct)
    inspect_lane(lane): merged_into_target=True  reclaimable=True    (WRONG)

So from inside a lane, a lane holding one UNMERGED commit reports `reclaimable=True`.
`teardown_worktree`'s own docstring records what that authorizes: it deletes the branch AND its reflog,
leaving the commit reachable from no ref, "garbage-collectable with no ref and no reflog to recover it
from".

THE FIX IS NOT THE SAME AS `voxbcx`'s. `voxbcx` is about WHERE a file is composed, and anchoring it on
`checkout_control_root` is a provable no-op for a main-checkout caller. This defect is about which
COMMIT a relative revision names, and `checkout_control_root` does not help: `HEAD` is resolved by git
against the invoking worktree, not by path composition. Candidate directions (none asserted): (1) resolve
the target against the CHECKOUT (e.g. `git rev-parse` in the main worktree rather than in the lane)
before passing it to `--is-ancestor`; (2) make the default target explicit rather than `HEAD` (the
symbolic default is what makes it cwd-sensitive), noting the fallback's docstring argues `HEAD` is the
honest default precisely BECAUSE a fork may use `master`/`trunk`, so a literal `"main"` is the one wrong
answer; (3) refuse/return `None` when the predicate is invoked from a linked worktree, so an unanswerable
landing question fails toward PRESERVATION as `lane_merged_into_target` already documents.

WHY IT IS FILED `bug` AND GATED. Unlike `voxbcx` (a latent inconsistency with no measured user-visible
symptom, correctly filed `chore`), this one has a measured wrong ANSWER from a reachable caller, and the
wrong answer is in the destroy-authorizing direction. Per AGENTS.md "Every live bug gates the next
release", it carries `- Blocks-Release:`.

HONEST LIMIT ON REACHABILITY, stated so the claim is not trusted further than it holds. The drivers'
reclamation and liveness paths run from the MAIN checkout, where the two anchorings agree, so no
in-tree caller is PROVEN affected today; this was established by reading call sites, not by exhaustive
execution. What makes it more than theory is that the repository already ships two bespoke workarounds
for exactly this class of cwd sensitivity (`ipd_lifecycle.checkout_control_root`, fixed under `dh0uno`,
and `attention._resolve_runs_repo_root`, which climbs out of `.aw/worktrees/` by hand), and that `aw`
verbs resolve their repo root from cwd (`project_context.resolve_verb_repo_root` climbs to the LANE, and
`runner_shared.add_integrate_parser` defaults `--repo` to `.`), so an operator running a verb from inside
a lane supplies the lane as `repo`.
