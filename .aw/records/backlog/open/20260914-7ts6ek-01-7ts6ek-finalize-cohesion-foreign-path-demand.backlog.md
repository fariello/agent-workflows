- Id: 7ts6ek
- Status: open
- Set: 7ts6ek
- Priority: high
- Work-Kind: bug
- Summary: finalize's commit-cohesion scope audit demands reasons for other plans' paths when several lanes share a hot file

## Workflow history
- 2026-09-14 set (aw backlog): MEASURED KNOCK-ON, same root cause: 'aw check plans' findings rose 151 -> 623 across the ten recovery merges, and check.scope-drift now flags exactly the ten recovered plans (3i0aaz, b7xarm, zexed1, mm5p3v, ixis0c, 8tgg6g, r2i1b1, st5klo, fn2l1u) plus their dependents (9xycbh, d7qoxv). Bisected per merge: 151 at base, 184 after 3i0aaz, 336 after zexed1, 447 after 8tgg6g, 501 after st5klo, 623 at HEAD. Cause is the same as this item: the code landed while the plan is still 'approved' in pending/ because finalize cannot be run, so the scope audit sees declared paths changed with no terminal transition. These 472 extra findings are an ARTIFACT of the unfinalizable state, not independent defects, and they should clear when finalize is unblocked and the ten plans move to executed/. Do not chase them separately.

## What happens

`aw ipd finalize <id6>` refuses with a `--scope-reason` demand naming ~19 paths that belong to OTHER
plans, whenever several lanes are recovered into `main` before any of them is finalized. Measured
2026-09-14 while recovering ten lanes stranded by the binary suite gate: finalizing `8tgg6g`, whose
declared Scope-Paths are just its plan file plus `agent_workflows/runner_shared.py` plus
`tests/test_orchestrator_probe_cache.py`, demanded reasons for `artifact_audit.py`, `cli.py`,
`run_viewer.py`, `lane_containment.py`, `runner_shutdown.py`, `test_defect_report.py`,
`test_run_flag_surface.py` and a dozen more, none of which `8tgg6g` touched.

## Why (mechanism, not speculation)

`ipd_lifecycle.committed_attribution` attributes committed paths by COMMIT COHESION: a commit in
`base_head..HEAD` is "this execution's" if it touched at least one declared Scope-Path, and then EVERY
path in that commit becomes attributable. Its docstring states the accepted cost honestly, and this is
that cost firing at scale:

    A co-worker who touches one of this plan's declared paths in the same commit as unrelated files
    makes those files look like this plan's (a false DEMAND, which is fail-closed and merely annoying).

The multiplier nobody accounted for is a SHARED HOT FILE. `agent_workflows/runner_shared.py` is
declared by many plans and touched by nearly every runner lane, so `8tgg6g` anchors on five foreign
commits at once:

    $ git log --no-merges --oneline fea2c9f8..HEAD -- agent_workflows/runner_shared.py
    70792b53 feat(run_viewer): ... (zexed1)
    4e03ca49 feat(runners): guard the dirty-base cases ... (3i0aaz)
    11013cb1 feat(runner): add the integration deferral ladder (51vw4y)
    b816200c feat(orchprobe): cache an orchestrator probe verdict ... (8tgg6g)
    2062fc5b feat(defreport): require an affirmative or negative defect report (b7xarm)

Four of those five are other plans' work. Their full path sets are then demanded from `8tgg6g`.

The three escape hatches the docstring names are all still shut: git authorship cannot partition
(every agent commits as the maintainer), the run record is gitignored and unreachable from finalize,
and `AW-Run:`/`AW-Item:` trailers (backlog `a8eufb`) are not written yet.

## Why this is worse than "merely annoying"

The only way past it today is to pass ~19 `--scope-reason` strings asserting why each foreign path was
needed for THIS plan. That is a false attestation: it records in tracked history that `8tgg6g`
deliberately edited `cli.py` and `run_viewer.py` when it did not. The gate is fail-closed and correct
to refuse; what is missing is any HONEST way to answer it. So ten recovered plans cannot be finalized
at all, and `aw ipd board` / `aw attention` keep reporting shipped work as `approved` in `pending/`,
which is the same lie about lane state that `lanestrand-01 pr5b0t` and `integearn-04 ys1dor` exist to
remove.

## Repro

1. Integrate two or more lanes that each touch `agent_workflows/runner_shared.py` into `main`.
2. Run `aw ipd finalize <either id6> --actor X -m Y`.
3. Observe reasons demanded for the other lane's paths.

## Candidate fixes (not decided here)

1. WRITE THE TRAILERS. Make the driver stamp `AW-Item: <id6>` on every lane commit and have
   `committed_attribution` prefer trailers when present, falling back to cohesion. This is `a8eufb`
   and it settles attribution exactly rather than heuristically. Strongest fix; needs the driver.
2. INTERSECT COHESION WITH THE COMMIT'S OWN ANCHOR SET. If a commit anchors on a DIFFERENT plan's
   declared paths and that plan exists, do not attribute its paths here. Cheap, no new channel, and it
   would have fixed this case completely, since each foreign commit anchors on its own plan.
3. A `--scope-foreign <path>=<owning-id6>` answer that records the path as ANOTHER plan's work instead
   of forcing a false claim that it was this plan's.

Option 2 is the smallest change that removes the false demand without inventing a new attestation.
