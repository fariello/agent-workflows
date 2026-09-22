- Id: a58s04
- Status: done
- Blocks-Release: next
- Set: a58s04
- Priority: high
- Work-Kind: bug
- Summary: Lane teardown never reclaims a merged lane: commits_ahead is measured against the lane's OWN base, so an integrated lane reports HOLDS-WORK forever and 28 of 38 worktrees accumulated to 4.7G

## Workflow history
- 2026-09-22 set (aw backlog): closed by aw oc run: IPD 65cuw0 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md); evidence .aw/records/plans/executed/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): Lane teardown never reclaims a merged lane: commits_ahead is measured against the lane's OWN base, so an integrated lane reports HOLDS-WORK forever and 28 of 38 worktrees accumulated to 4.7G

## Observed

Measured 2026-09-17 in the maintainer's checkout: `.aw/worktrees/` held **38 worktrees / 4.7G**, of
which **28 were fully merged into `main` and completely clean**. A successful, integrated lane is never
torn down, so every run permanently leaks its worktree.

`worktree_lease.inspect_lane` on six lanes whose work is provably IN `main`:

```
lane        state       commits_ahead(own base)  reclaimable
3dki3o      HOLDS-WORK        5                  False
51vw4y      HOLDS-WORK        4                  False
orziju      HOLDS-WORK        4                  False
s16omw      HOLDS-WORK        6                  False
ty3cj6      HOLDS-WORK        4                  False
yrqyxb      HOLDS-WORK        5                  False
```

Yet for every one of those:

```
merged_into_main=YES   ahead_of_main=0
```

## Root cause

`worktree_lease.py:308-314` computes `commits_ahead` as `rev-list --count <lane's own base>..<head>`,
i.e. against the commit the lane was CUT FROM, never against `main`:

```python
base_sha = _lane_base_sha(repo_root, branch, head or "") if head else None
commits_ahead = 0
if head and base_sha:
    rc, out, _err = _git(repo_root, ["rev-list", "--count", f"{base_sha}..{head}"])
```

Then `:321` sets `state = LANE_HOLDS_WORK` whenever `commits_ahead > 0`, and `reclaimable` (`:195`)
returns False for anything not `LANE_EMPTY`/`LANE_STALE`. So the lane's own commits, which are exactly
what integration merged, are counted as unrecovered work FOREVER. Integration moves the work into
`main` but nothing re-evaluates the lane afterwards, so the count never returns to zero.

That also explains the `aw attention` stranded-lane report: a merged lane is indistinguishable there
from a genuinely stranded one, which buries the ~12 lanes that DO hold unmerged commits under ~28 that
do not. The signal is real but drowned.

## Expected

A lane whose branch is an ANCESTOR of `main` (all its commits reachable from `main`) holds NO
unrecovered work and MUST be reclaimable, regardless of its distance from its own base. The
`commits_ahead`-from-own-base figure is still the right input for the "is this lane reusable for a
fresh execution" question (`LANE_EMPTY`/`LANE_STALE`/`LANE_FOREIGN`), so the fix is a SEPARATE
merged-ness predicate, not a change to that number's meaning.

## Fix sketch

1. Add an explicit `merged_into(ref)` reading to `LaneState` (`git merge-base --is-ancestor <branch>
   <ref>`), defaulting `ref` to the integration target (`main`).
2. Make `reclaimable` true when the lane is merged AND not dirty, independent of `commits_ahead`.
   Keep the never-reclaim-dirty rule exactly as it is; `wfamig` below shows why.
3. Tear the lane down at the END of a successful integration, rather than leaving it for a later
   reclamation pass that structurally cannot fire.
4. Teach the `aw attention` stranded-lane report to exclude a merged lane, so the ~12 genuinely
   stranded lanes stop being buried.
5. Regression test: a lane cut from an older base, committed, then merged to `main`, must report
   `reclaimable=True` and must NOT appear as stranded.

## Do NOT lose these when implementing

Untracked files are invisible to every merged-ness check, so step 2's dirty rule is load-bearing.
Measured in the same sweep: lane `wfamig` held an untracked plan
`.aw/records/plans/pending/20260917-revladder-01-i4ak5n-...ipd.md` (89 lines) that exists NOWHERE in
`main`. A teardown keyed on merged-ness alone would have destroyed it.

`git worktree remove` REFUSES a dirty worktree by default, which is the backstop that makes this safe;
never pass `--force` in an automated teardown.
