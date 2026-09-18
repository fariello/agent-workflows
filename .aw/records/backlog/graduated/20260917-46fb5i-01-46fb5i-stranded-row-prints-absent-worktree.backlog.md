- Id: 46fb5i
- Status: graduated
- Blocks-Release: next
- Set: 46fb5i
- Priority: medium
- Work-Kind: bug
- Summary: Every stranded-lane row prints a .aw/worktrees path that does not exist: lane_worktree_display reconstructs the string and never existence-checks it

## Workflow history
- 2026-09-18 graduated (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 graduated (aw set): Design handed off to plan 0ta5vg (stranrep-01), which fixes all four stranded-report defects as one cohesive change; that plan carries From-Backlog: kvf5xo and inherits Blocks-Release: next
- 2026-09-17 created (aw backlog): All 19 stranded rows print a .aw/worktrees/<id> path; zero of the 12 exist. lane_worktree_display reconstructs the string in its except branch without existence-checking it

MEASURED 2026-09-18 at HEAD `d188eaad`, in the maintainer's primary (non-lane) checkout:

    rows naming a worktree: 19, nonexistent: 19

Every one of the 19 stranded-lane rows prints `worktree .aw/worktrees/<id>`, and NOT ONE of those
directories exists on disk. Checked individually for all 12 distinct lanes (`03ie04`, `2c122z`,
`58ha43`, `7p9n2v`, `d7qoxv`, `fn2l1u`, `mm5p3v`, `nna8yz`, `qcqhj7`, `r2i1b1`, `rchpms`, `ybkmzp`):
all absent. `.aw/worktrees/` at the time held only `3v7wo6`, `fujm0y`, `perf-opt` and a review-sweep
lane, none of which appear in the report.

## Root cause

`runner_shared.lane_worktree_display` (`runner_shared.py:1324-1353`) takes the worktree path RECORDED
in the run's `state.json`. The recorded value is an absolute path under the operator's home directory,
so `relative_to(root)` raises, and the except branch RECONSTRUCTS a plausible-looking repo-relative
string from the path's last two components (`runner_shared.py:1345-1350`):

```python
except (ValueError, OSError, RuntimeError):
    name = Path(str(worktree)).name
    parent = Path(str(worktree)).parent.name
    if parent == "worktrees" and name:
        # The canonical lane shape, reconstructed WITHOUT the absolute prefix.
        return ".aw/worktrees/{0}".format(name)
```

Nothing existence-checks the result. The reconstruction is doing its ACTUAL job correctly, which is
satisfying spec F8a (never print an absolute path, prefer omission over leaking) rather than reporting
liveness; the bug is that a path derived purely from a historical string is then presented as if it
were a current fact.

## Expected

A worktree that does not exist is OMITTED from the row rather than asserted. An existing one still
renders repository-relative, exactly as now.

## Fix sketch

1. Existence-check the resolved path before returning it; return None when absent.
2. Preserve F8a in the same fail-safe direction as today: never return an absolute path, and omit
   rather than leak. Omitting an absent worktree strictly reduces what is printed, so it cannot
   introduce a leak.
3. Consider stating in the row that no worktree remains, since "no worktree" is itself useful (it means
   only the branch holds the work, so recovery is a merge and not a tree inspection). Optional; the
   minimum fix is omission.
4. Regression test: a record whose worktree is absent renders no worktree segment; a record whose
   worktree exists renders the repo-relative path; neither ever renders an absolute path.

## Why this matters

The worktree path is the operator's handle for inspecting a lane, so a row asserting a directory that
is not there sends the reader to a dead end and implies a recoverable tree that no longer exists. It
also contradicts the report's own remediation, which tells the reader to go look at the lane.

## Deliberately NOT proposed

Do NOT fix this by deriving the verdict from a filesystem walk of `.aw/worktrees/`. Spec F3a forbids it
("THE VERDICT COMES FROM THE RUN RECORD, NEVER FROM A FILESYSTEM WALK ... A verdict derived from a live
filesystem audit reports a RECOVERED run clean and so rewrites history") and `SCAN_ROOTS` must not be
extended. This item changes only whether ONE already-derived display field is rendered, not where the
stranded verdict comes from.

## Not a duplicate of

`a58s04` (lane teardown never reclaims a merged lane) is about worktrees that DO exist and should be
removed; this is about worktrees that do NOT exist and are printed anyway. Opposite direction, and
this one is read-only.
