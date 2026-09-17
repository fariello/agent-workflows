# IPD: Fix lane reclaim so a merged lane is reclaimable and torn down

- Date: 2026-09-17
- Kind: child
- Concern: A lane whose work is fully merged into `main` is NEVER reclaimed, so every successful run permanently leaks its worktree. `worktree_lease.inspect_lane` computes `commits_ahead` as `rev-list --count <the lane's OWN base>..<head>` (`worktree_lease.py:308-314`), then sets `LANE_HOLDS_WORK` whenever that is non-zero (`:321`), and `reclaimable` returns False for any state other than `LANE_EMPTY`/`LANE_STALE` (`:193-199`). Integration moves the lane's commits into `main` but nothing re-evaluates the lane afterwards, so the exact commits integration merged keep the lane at HOLDS-WORK forever. MEASURED 2026-09-17 in the maintainer's checkout: 38 worktrees / 4.7G, of which 28 were provably merged into `main` AND clean; six sampled lanes (`3dki3o`, `51vw4y`, `orziju`, `s16omw`, `ty3cj6`, `yrqyxb`) each reported `HOLDS-WORK` with 4-6 `commits_ahead` while `merge-base --is-ancestor <branch> main` returned 0 and `rev-list --count main..<branch>` returned 0 for all six.
- Scope: Add an explicit merged-ness reading to `LaneState`, make `reclaimable` honor it, tear a lane down at the end of a successful integration, and stop `aw attention` reporting a merged lane as stranded. Does NOT change what `commits_ahead` MEANS: that figure is still the correct input to the lane-REUSE question (`LANE_EMPTY`/`LANE_STALE`/`LANE_FOREIGN` decide whether a lane can be adopted for a fresh execution), so this adds a separate predicate rather than redefining an existing one.
- Scope-Paths: agent_workflows/worktree_lease.py, agent_workflows/runner_shared.py, agent_workflows/attention.py, tests/test_worktree_lease_merged_reclaim.py
- Item-Dependencies: none
- Status: to-review
- From-Backlog: a58s04
- Set: laneorph
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 65cuw0

## Workflow history
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from a measured sweep of .aw/worktrees/ (38 worktrees/4.7G, 28 provably merged and clean) and of the 13 lane branches holding 76 unmerged commits; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make a merged lane reclaimable, and reclaim it at the moment its work lands, so `.aw/worktrees/` stops
growing without bound. The user-visible symptom was 4.7G of worktrees, but the load-bearing harm is to
the STRANDED-LANE SIGNAL: `aw attention` currently cannot distinguish a merged lane from a genuinely
stranded one, so roughly 28 merged lanes buried the roughly 12 that really do hold unmerged work. A
report that cries wolf on two thirds of its rows is a report an operator learns to ignore, which is
exactly how the seven branch-only stranded lanes (`2c122z` at 26 commits, `58ha43` at 22, `7p9n2v` at
16, `rchpms` at 10) went unnoticed for weeks.

NON-GOAL, stated because it is the tempting shortcut and it destroys work: teardown must NOT be keyed
on merged-ness alone. UNTRACKED files are invisible to every merged-ness test. Measured in the same
sweep, lane `wfamig` was fully merged and held an untracked 89-line plan
(`.aw/records/plans/pending/20260917-revladder-01-i4ak5n-...ipd.md`) that existed NOWHERE in `main`; a
merged-ness-only teardown would have deleted the only copy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Make merged-ness a first-class reading

- [ ] E-01 Add a `merged_into_target` boolean to `worktree_lease.LaneState`, computed as `git merge-base --is-ancestor <branch> <target>` where the target defaults to the integration branch the drivers merge into (`main`). Record it ALONGSIDE `commits_ahead`; do not alter how `commits_ahead` is computed, since `LANE_STALE`/`LANE_FOREIGN` adoption logic reads it and changing its meaning would silently change which lanes are reused.
  - Depends on: none
  - Expected outcome: `inspect_lane` on a merged lane returns `merged_into_target=True` while still reporting its real `commits_ahead`; on an unmerged lane it returns False. No existing field changes value.
  - Execution state: pending

- [ ] E-02 Make `LaneState.reclaimable` return True when the lane is merged into the target AND not dirty, in addition to today's `LANE_EMPTY`/`LANE_STALE` cases. KEEP the dirty exclusion exactly as it is; it is the only thing standing between an automated teardown and the `wfamig` untracked-plan loss described in the Goal.
  - Depends on: E-01
  - Expected outcome: a merged clean lane is `reclaimable=True`; a merged DIRTY lane stays `reclaimable=False`; an unmerged lane is unaffected.
  - Execution state: pending

### Task group 2: Reclaim at the moment work lands

- [ ] E-03 Tear the lane down at the END of a successful integration, in the shared integration path both hosts call, rather than leaving it to a later reclamation pass that structurally never fires for a merged lane. Use `git worktree remove` WITHOUT `--force`, so git's own refusal on a dirty tree is a second independent backstop; on refusal, leave the lane in place and record why.
  - Depends on: E-02
  - Expected outcome: a run that integrates a lane leaves no worktree for it, and a lane that git refuses to remove is preserved with a recorded reason rather than force-deleted.
  - Execution state: pending

- [ ] E-04 Stop `aw attention` reporting a MERGED lane as stranded, consuming E-01's reading rather than re-deriving merged-ness locally. A stranded lane must remain reported when it holds commits not reachable from the target.
  - Depends on: E-01
  - Expected outcome: the stranded-lane report lists only lanes with unmerged commits; a merged lane no longer appears.
  - Execution state: pending

### Task group 3: Guard the invariant

- [ ] E-05 Add `tests/test_worktree_lease_merged_reclaim.py`: build a real lane in a temp repo, cut from an OLDER base, commit on it, merge it to the target, and assert `merged_into_target=True`, `reclaimable=True`, that it is NOT reported stranded, and that `commits_ahead` is still non-zero (proving the fix did not achieve its result by corrupting that figure). Add the negative cases: an unmerged lane stays non-reclaimable and stranded, and a merged lane with an UNTRACKED file stays non-reclaimable.
  - Depends on: E-03, E-04
  - Expected outcome: a test file that fails against today's code for the merged case and passes after E-01..E-04, with the untracked case pinned so a later change cannot reintroduce the `wfamig` hazard.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease.py` owns lane state as a NON-MUTATING reading (`inspect_lane`'s docstring); a fix
  belongs in that reading plus its consumers, not in a new parallel notion of lane health.
- `LaneState.reclaimable`'s docstring already states the safety rule this plan must preserve verbatim:
  "Provably empty: safe to tear down. NEVER true for a lane holding commits or dirty files." E-02
  widens "provably empty" to "provably recovered", and must not weaken the dirty half.
- Two drivers consume `lane["reclaimable"]` (`oc_runipd.py:2337`, `agy_runipd.py:1292`) through the
  shared `runner_shared` lane dict, so fixing the reading fixes both hosts at once. Do not add a
  per-host reclaim rule.
- `git worktree remove` refuses a dirty worktree unless `--force` is passed; the 2026-09-17 manual
  sweep relied on exactly that refusal, and it is why `--force` must not appear in an automated path.
- Lane branches are cheap and are the durable record of a lane's work: the manual sweep removed 28
  WORKTREES and deleted ZERO branches. Teardown means the directory, never the ref.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | `commits_ahead` is measured against the lane's OWN base, never the integration target | `worktree_lease.py:308-314`, `rev-list --count {base_sha}..{head}` where `base_sha` comes from `_lane_base_sha` (the branch-creation reflog entry) |
| F-2 | Any non-zero `commits_ahead` forces `LANE_HOLDS_WORK`, and `reclaimable` is False for that state | `worktree_lease.py:321` (`if commits_ahead > 0 or dirty`), `:193-199` (`reclaimable`) |
| F-3 | The defect is systematic, not incidental: 28 of 38 worktrees were merged AND clean | measured 2026-09-17; 4.7G total, 1.1G after removing exactly those 28 |
| F-4 | Six sampled merged lanes each reported HOLDS-WORK with a non-zero count | `3dki3o` 5, `s16omw` 6, `yrqyxb` 5, `51vw4y` 4, `orziju` 4, `ty3cj6` 4; all with `ahead_of_main=0` and `--is-ancestor` exit 0 |
| F-5 | The real cost is signal loss, not disk: merged lanes are indistinguishable from stranded ones in `aw attention` | the same sweep found 7 branch-only stranded lanes holding 26/22/16/10/3/3/2 unmerged commits, buried among ~28 false rows |
| F-6 | An untracked file makes a merged lane unsafe to remove, so merged-ness alone must never authorize teardown | lane `wfamig` was merged and held the ONLY copy of an 89-line plan `i4ak5n`; `git worktree remove` without `--force` is what refused it |
| F-7 | Both hosts already share the reclaim decision through one dict key, so one fix covers both | `oc_runipd.py:2337` and `agy_runipd.py:1292` both read `lane["reclaimable"]` from `runner_shared`'s lane dict (`runner_shared.py:825`) |

## Proposed changes (ordered, validatable)

1. `worktree_lease.py`: add `merged_into_target` to `LaneState` and compute it in `inspect_lane` via
   `merge-base --is-ancestor`. Additive; every existing field keeps its current value.
2. `worktree_lease.py`: widen `reclaimable` to accept a merged, non-dirty lane. The dirty exclusion is
   unchanged.
3. Shared integration path: on a successful integration, remove the lane worktree with
   `git worktree remove` (no `--force`), keeping the branch; on refusal, preserve and record.
4. `attention.py`: exclude a merged lane from the stranded-lane set, consuming the E-01 reading.
5. `tests/test_worktree_lease_merged_reclaim.py`: the merged, unmerged, and merged-plus-untracked
   cases, plus an assertion that `commits_ahead` is still non-zero for a merged lane.

## Deferred / out of scope (with reason)

- TRIAGING the lanes that genuinely hold unmerged work is Order 02 (`ut0vzr`), not this plan. This plan
  makes the report trustworthy; deciding the fate of 14 unmerged branches is a judgement call needing
  the maintainer.
- Deleting merged lane BRANCHES is out of scope. A ref is a few bytes and is the durable record of what
  a lane did; the disk was consumed by worktrees, and no evidence says the refs are a problem.
- A general `aw lane` operator verb (list/reclaim/recover) is a plausible follow-on but is not needed to
  stop the leak, and bundling a new public surface into a defect fix would widen the blast radius.
- The seven branch-only stranded lanes have NO worktree, so nothing this plan does affects them.

## Scope check

- Over-scope: none. Every change is on the path from "a lane is merged" to "its worktree is gone and it
  is not reported stranded".
- Under-scope: this plan does not reclaim the 9 worktrees currently on disk, because each holds
  something not in `main` (6 unmerged, 2 staged deletions, 1 maintainer's own). Those are Order 02's.

## Required tests / validation

- `python3 -m pytest tests/test_worktree_lease_merged_reclaim.py` passes, and each new assertion is
  shown to FAIL against pre-fix code (a test that passes both before and after proves nothing here).
- `python3 -m pytest` bare, green, with the actual summary line pasted.
- A REAL end-to-end check, since this defect survived unit-level correctness for weeks: run a driver
  execution that integrates a lane, then show `git worktree list` no longer contains it and its branch
  still exists.
- `aw attention --check` on this repo reports only genuinely unmerged lanes as stranded.

## Spec / documentation sync

No `.spec.md` governs lane reclamation, so no spec amendment is declared and no `.spec.md` appears in
`Scope-Paths`. If E-03 changes the operator-visible end-of-run lane reporting, note it in the lane
section of the runner docs; otherwise N/A.

## Open questions

### OQ-01: Which ref is the merge target on a repo that does not use `main`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE CODE, not by asking. The drivers already record
  the branch they integrate into per run (`ending_branch` was `main` for every attempt in the runs
  inspected), and the integration path merges into the checkout's current branch rather than a hardcoded
  name. E-01 therefore takes the target as a PARAMETER defaulting to the repo's integration branch, so a
  fork using `master` or `trunk` is correct without configuration. Hardcoding `"main"` would be the one
  wrong answer.

### OQ-02: Should teardown also delete the merged lane's branch?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and this is deliberate rather than unexamined. The 2026-09-17
  manual sweep removed 28 worktrees and kept all 28 branches, which reclaimed 3.6G, so the disk problem
  is entirely worktrees. A branch is the durable record of what a lane did and is nearly free; deleting
  refs automatically would destroy audit history to save bytes. Recorded as a resolved question rather
  than omitted, so a later reader does not assume it was forgotten.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `inspect_lane` for a MERGED lane and an UNMERGED lane in a temp
    repo, showing `merged_into_target` True and False respectively, AND showing `commits_ahead` retains
    its pre-fix value for both (proving the field was added, not substituted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `reclaimable` for three lanes: merged+clean (True), merged+dirty (False),
    merged+UNTRACKED-file-only (False). The third is the `wfamig` hazard and must be shown explicitly,
    not argued.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git worktree list` before and after a real driver run that integrates a lane,
    showing the lane's worktree gone; plus `git rev-parse --verify <lane branch>` succeeding after, so
    the branch is provably kept. Plus the refusal path: a dirty lane's worktree still present with the
    recorded reason pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `aw attention --check` output on a repo containing BOTH a merged lane and an
    unmerged one, showing only the unmerged lane reported stranded.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_worktree_lease_merged_reclaim.py` summary line,
    PLUS evidence the merged-case assertion fails against pre-fix code (stash the fix or check out the
    prior revision and paste the failure).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. The executor MUST follow the repository
execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, and never push. Paste ACTUAL runner output for every V-item; a claim of success
without pasted evidence does not satisfy this gate.

Post-gate lifecycle: on completion, `aw ipd finalize` moves this plan to `.aw/records/plans/executed/`
only after `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries observed
evidence. Do NOT mark this executed on the strength of the unit tests alone: V-03 requires a real
integration to have reclaimed a real worktree, because unit-level correctness is exactly what this
defect already passed while leaking 4.7G.
