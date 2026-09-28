- Id: qkl8fs
- Status: open
- Set: qkl8fs
- Priority: medium
- Work-Kind: followup
- Summary: Allow runner in-lane backlog close to gate against main via carrier override or resolution bridge

## Summary
In an isolated lane worktree turn, `runner_shared.process_backlog_close` executes before the lane branch is merged into `main`. Consequently, the just-executed plan exists in `plans/executed/` only in the lane worktree, while `main` still has the plan in `plans/pending/`.
If `aw backlog set --dir <lane> --gate-dir <main>` is passed:
1. `check_engine.evaluate_blocking_close` evaluates the gate against `main`, where the carrier is still pending (so the HANDOFF arm fails).
2. The runner cites the lane's executed path as `--evidence`, but that path does not exist in `main` (so the SATISFIED arm fails).
3. Citing `main`'s pending path would falsely cite an unexecuted plan to satisfy a release gate.

As established by measurement under IPD `9vglxd` E-06, passing `--gate-dir <main>` from `close_backlog_item` would cause every ordinary single-carrier in-lane runner close to fail with `exit 1: carrier is not executed/implemented`. Per `9vglxd` E-06/V-06, E-05 was withdrawn and refiled as this item.

Resolving this requires either:
(a) providing `backlog set` with a carrier-override mechanism for the in-lane plan (analogous to `runner_shared.evaluate_backlog_close`'s `executed_overrides`),
(b) allowing `backlog set`'s evidence resolver to check the move tree when `--gate-dir` is passed and the move tree is a valid git worktree of `gate-dir`, or
(c) moving the runner's backlog close to post-merge.

## Workflow history
- 2026-09-28 created (aw backlog): Allow runner in-lane backlog close to gate against main via carrier override or resolution bridge
