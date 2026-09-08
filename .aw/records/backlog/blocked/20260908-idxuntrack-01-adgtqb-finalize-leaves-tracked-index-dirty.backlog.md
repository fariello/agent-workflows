- Id: adgtqb
- Status: blocked
- Set: idxuntrack
- Priority: high
- Work-Kind: bug
- Summary: Every aw ipd finalize leaves the tracked plans manifests dirty: idxuntrack child 4r0qp1 removed INDEX.json from every commit path-set but child yvvf98 never untracked it, so HEAD's index goes stale while aw index plans --check reads disk and reports clean
- Gate-Kind: artifact
- Gate-Ref: yvvf98

## Workflow history
- 2026-09-08 created (aw backlog): FILED from a measured incident during aw agy run 3m0urk (run-20260908T212520Z-3675719): the orchestrator retirement committed only the plan file and left .aw/records/plans/INDEX.json modified. Investigated rather than assumed: the runner and _finalize_transaction both behaved exactly as written and TESTED, so this is filed as a half-landed Set, not as a runner bug. BLOCKED on yvvf98 (idxuntrack Order 02, approved, pending, dependency satisfied) because that plan IS the fix; a typed gate refuses a graduation attempt that would otherwise re-add the manifests to owned_paths and break the three tests pinning their absence.

MEASURED 2026-09-08 during `aw agy run 3m0urk` (run `run-20260908T212520Z-3675719`). The runner
retired Order-0 orchestrator `3m0urk` (Set `runprofile`) in 9s with no agent turn, committed
`6d433620 lifecycle(3m0urk): finalize 3m0urk -> executed` containing EXACTLY ONE FILE (the plan), and
left `.aw/records/plans/INDEX.json` MODIFIED in the working tree. The run's own shutdown report listed
it under "dirty path(s) left exactly as found", which is the runner behaving correctly: R4 preserves
dirt rather than committing paths it does not own.

THE RUNNER IS NOT AT FAULT, AND NEITHER IS `_finalize_transaction`. Both did what they are written and
TESTED to do. The defect is a HALF-LANDED SET, and the honest framing matters because the obvious
"fix" is the wrong one.

WHAT IS ACTUALLY BROKEN: Set `idxuntrack` has two children, and only the first landed.

  * `4r0qp1` (Order 01) REMOVED the manifests from every commit path-set. EXECUTED (`59f7f19b`),
    landing as `674f2c68 refactor(records): stop committing the generated index manifests`. Verified
    via `git log -L 2591,2592:agent_workflows/ipd_lifecycle.py`, which shows the exact edit:
    `owned_paths = [plan_rel, dest_rel, index_json_rel, index_md_rel]` -> `[plan_rel, dest_rel]`.
  * `yvvf98` (Order 02) was to `git rm --cached` the manifests and add the gitignore entries. STILL
    `pending` with `- Status: approved`, and its E-01/E-04/E-05/E-06 are recorded `blocked`
    (`d003dbf2` records that honestly). It correctly declares `- Item-Dependencies: executed:4r0qp1`,
    so the ORDER was right; child 01 landing alone is precisely what opened the gap.

THE CONTRADICTION, MEASURED AT HEAD. `ipd_lifecycle.py:2583-2591` justifies the exclusion in its own
comment by asserting the manifests are gitignored: "naming them here would (a) put a gitignored path
in the `git add` set, which exits 1 and stages NOTHING, wedging the whole transaction". That premise is
FALSE in this repo today:

    git ls-files --error-unmatch .aw/records/plans/INDEX.json   -> rc=0  (TRACKED)
    git check-ignore -v .aw/records/plans/INDEX.json            -> rc=1  (NOT ignored)

`.aw/.gitignore` carries no INDEX entry. So a regenerated manifest is an ordinary MODIFICATION TO A
TRACKED FILE that no verb commits, which makes EVERY finalize a guaranteed dirty-tree producer.

REGENERATION IS INSIDE THE TRANSACTION, WHICH IS WHY THIS IS UNAVOIDABLE RATHER THAN INCIDENTAL.
`_refresh_plans_index_fail_loud` runs in the MUTATING phase at `ipd_lifecycle.py:2700`, BEFORE staging
at `:2710-2711` (`git add -- *stage`), and it is a FAIL-LOUD gate: it rebuilds, re-runs `--check`, and
raises if it did not converge. So the transaction is REQUIRED to rewrite the file and FORBIDDEN to
commit it.

NOT ORCHESTRATOR-SPECIFIC. `owned_paths` lives in `_finalize_transaction`, which serves BOTH
`retire_orchestrator` (`:2405`) and the ordinary `finalize` (`:2544`). Confirmed empirically: the ten
child finalizes on 2026-09-08 12:29-12:31 each committed one file, and `e148f82c` plus `69403678` are
the manual "regenerate the plans index" cleanup commits that followed. Every finalize on both hosts is
affected.

WHY `aw index plans --check` DOES NOT CATCH IT, which is the part that makes this silent. The check
byte-compares a rebuild against the file ON DISK, never against git (stated at `:2590`). So it reports
`clean` while HEAD's manifest is stale. Measured on `3m0urk`: `--check` said clean, yet HEAD still
listed the plan as `pending`/`approved` while it sat in `executed/`. A FRESH CLONE GETS THE WRONG
INDEX, and nothing in the repo says so.

DO NOT FIX THIS BY ADDING THE MANIFESTS BACK TO `owned_paths`. That is the tempting one-line change and
it is wrong: `tests/test_orchestrator_retirement.py:1789-1797` PINS the current behavior
(`assertNotIn(".aw/records/plans/INDEX.json", changed)`), with a comment naming `4r0qp1` E-01 and
calling a committed manifest "the regression". `tests/test_selfcommit_adoption.py:274,372` do the same.
Re-adding it would break three tests that deliberately assert the opposite and would revert a
consistent nine-site refactor (`status_set.py:1134`, `plans_archive.py:165`, `research_archive.py:274`,
`plans_refs.py:150`, `artifact_refs.py:126`, and the finalize path).

THE FIX THE DESIGN ALREADY ANTICIPATES: land `yvvf98` (untrack the manifests, add the gitignore
entries), which makes the `:2583` comment true and the dirt disappear by construction. It is `approved`
and its dependency is satisfied, so it is runnable now. The alternative coherent fix is to REVERT
`4r0qp1`, but that trades away the merge-conflict class `yvvf98` exists to kill (its own F-1/F-5 cite
the `ueg5cf` conflicts), so it should not be chosen by default.

SECOND-ORDER RISK WORTH RECORDING: `_assert_rollup_touched_only_owned_paths` (`:2155`) refuses a rollup
when the orchestrator's own plan file is dirty, and the surrounding design assumes generated manifests
are ignorable. A permanently-dirty TRACKED manifest erodes that assumption, so this is not merely
cosmetic untidiness.
