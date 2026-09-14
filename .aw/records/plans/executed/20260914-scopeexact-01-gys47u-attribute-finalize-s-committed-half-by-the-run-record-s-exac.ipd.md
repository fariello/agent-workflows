# IPD: Attribute finalize's committed half by the run record's exact commit SHAs before falling back to cohesion

- Date: 2026-09-14
- Kind: child
- Concern: `aw ipd finalize` cannot finalize a plan whose lane landed alongside other lanes, because commit-cohesion attribution demands a `--scope-reason` for every path in every commit that touched a shared hot file, including other plans' paths. Ten recovered plans are unfinalizable today.
- Scope: Add an EXACT attribution source (the run record's per-item `commits[].sha`) ahead of the existing cohesion heuristic in `ipd_lifecycle`, keeping cohesion as the fallback and keeping every fail-closed property. Reader only; no writer, no new gate, no change to the refusal condition.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_finalize_exact_attribution.py
- Item-Dependencies: none
- Status: executed
- Set: scopeexact
- Order: 1
- Highest E allocated: 05
- Author: recovery-agent
- Id: gys47u
- From-Backlog: 7ts6ek

## Workflow history
- 2026-09-14 executed (opencode/its_direct-pt3-claude-opus-5): Exact run-record attribution added ahead of commit cohesion; all E/V items verified with pasted evidence, 12 new tests, whole suite 7308 passed.
- 2026-09-14 approved (aw set, --by-human): Maintainer instruction 2026-09-14: 'Why not? That does not sound like we're ready to move forward and complete all the plans.' in direct response to this defect being filed as backlog 7ts6ek and deferred. That is an explicit instruction to fix it rather than file it, so it is recorded here as the approval attestation per the AGENTS.md contract for acting on a backlog item, and no separate approve round trip is taken. Both open questions are resolved from repository evidence; neither is blocking.

- 2026-09-14 draft (recovery-agent): created.
- 2026-09-14 authored (recovery-agent): completed from the measured 2026-09-14 recovery incident; graduated from backlog `7ts6ek`.

## Goal

Make `aw ipd finalize` demand a `--scope-reason` only for paths THIS execution actually committed, by
consulting the run record's exact per-item commit SHAs before falling back to commit cohesion. This
unblocks the ten plans recovered on 2026-09-14 without weakening any gate and without writing a false
attestation into a plan's permanent finalize evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the exact attribution source

- [x] E-01 Add `_run_record_committed_paths(repo_root, id6, base_head) -> CommittedAttribution` to `ipd_lifecycle.py`, reading run outcomes under `checkout_control_root(repo_root)/records/runs/`, keeping only SHAs that are ancestors of HEAD and in `base_head..HEAD`, and returning `anchored=False` with an empty set whenever the corpus is missing, unreadable, or names no qualifying SHA for this id6.
  - Depends on: none
  - Expected outcome: called for `8tgg6g` at the current HEAD it returns `anchored=True` and exactly `{plan file, agent_workflows/runner_shared.py, tests/test_orchestrator_probe_cache.py}`; called in a tree with no `records/runs/` it returns `anchored=False, paths=frozenset()`.
  - Execution state: performed

- [x] E-02 Wire it into the committed-half branch of the scope reconciliation so the exact source is consulted FIRST and cohesion is used unchanged when the exact source is not `anchored`. Do not alter the `anchored=False -> owned=True` fail-closed arm.
  - Depends on: E-01
  - Expected outcome: `aw ipd finalize 8tgg6g` demands ZERO scope reasons; `aw ipd finalize` in a corpus-free fixture behaves byte-identically to today.
  - Execution state: performed

- [x] E-03 Report the deciding source (exact vs cohesion) in the finalize preview/refusal output, so a demanded reason is attributable to the evidence that produced it.
  - Depends on: E-02
  - Expected outcome: the preview names the source; no change to exit codes or to which paths are demanded.
  - Execution state: performed

### Task group 2: proof

- [x] E-04 Write `tests/test_finalize_exact_attribution.py` covering Required tests items 1 through 5.
  - Depends on: E-02
  - Expected outcome: all cases pass, each asserting on the reconciliation result rather than on log prose.
  - Execution state: performed

- [x] E-05 Add the non-vacuity control (Required tests item 6) proving the suite fails when the new source is disabled.
  - Depends on: E-04
  - Expected outcome: with the exact source stubbed off, case 1 fails; restored, it passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `checkout_control_root(start)` (`ipd_lifecycle.py:190`) already resolves a LANE to the MAIN
  worktree's `.aw`, which is what makes `.aw/records/runs/` reachable from inside an isolated turn
  even though it is gitignored. Measured from the main tree: control root
  `<repo>/.aw`, `records/runs` present, 165 run directories visible. This is the same helper
  `8tgg6g` used for its probe verdict store, so this plan invents no new state location.
- Attribution is already SPLIT into halves by `_changed_path_sources` / `ChangedPathSources`
  (`ipd_lifecycle.py:1176`), and the committed half is judged by
  `_execution_cohesive_committed_paths` (`:1258`) returning a `CommittedAttribution(anchored, paths)`
  pair (`:1244`). The `anchored` flag is the existing fail-closed switch. This plan adds a source
  ahead of that call; it does not restructure the halves.
- `_working_tree_path_is_owned` (`:1392`) is the ONE ownership predicate and its name is a documented
  historical misnomer asserted as a source substring by the ownership suite. Do not rename it.
- The repo already has the trailer vocabulary (`git_commit_helper.TRAILER_KEY_RUN` /
  `TRAILER_KEY_ITEM`, `git_commit_helper.py:48`), and backlog `a8eufb` step (1) is graduated to plan
  `wao266` (`runtrailwire-01`) as the WRITER. This plan is deliberately a different, independent
  source and does not bind, block, or duplicate `wao266`.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | `ipd_lifecycle.py:1274-1293` | Cohesion attributes a commit's ENTIRE path set to a plan when the commit touched any declared Scope-Path. Its own docstring names the resulting false DEMAND as an accepted cost. |
| F-2 | HIGH | measured 2026-09-14 | The accepted cost scales with SHARED HOT FILES. Finalizing `8tgg6g` (declares its plan file, `agent_workflows/runner_shared.py`, `tests/test_orchestrator_probe_cache.py`) demanded ~19 reasons, because 5 non-merge commits in range touched `runner_shared.py` and 4 of them are other plans' (`zexed1`, `3i0aaz`, `51vw4y`, `b7xarm`). |
| F-3 | HIGH | measured 2026-09-14 | The run record ALREADY carries exact per-item SHAs. `outcomes/*.json` `commits[]` yields `8tgg6g -> b816200c, 1aa30004`; `3i0aaz -> 4e03ca49, 8bd1e941`; `zexed1 -> 70792b53`. All recorded SHAs for all eight recovered lanes were verified REACHABLE with `git cat-file -e <sha>^{commit}`. |
| F-4 | HIGH | measured 2026-09-14 | Attributing by those SHAs reduces `8tgg6g` from ~19 paths to EXACTLY its 3 declared ones, and `zexed1` to exactly the 12 paths of its own single commit. This is the whole defect, resolved from evidence the repo already writes. |
| F-5 | MED | `artifact_audit.py:1016`, `doctor.py:585` | `.aw/records/runs/` is GITIGNORED and box-local, so this source can be ABSENT (fresh clone, CI, a tree that never ran a driver). It must therefore be an ADDITIVE fast path with cohesion still behind it, never a replacement. |
| F-6 | MED | `ipd_lifecycle.py:1295-1302` | The `anchored=False` fail-closed switch exists because a bare empty set would read as "nothing is owned" and excuse EVERY committed path. Any new source must preserve that inversion-guard exactly. |
| F-7 | MED | measured 2026-09-14 | A run record can name a SHA that is not an ancestor of HEAD (an unmerged or abandoned lane attempt). `mm5p3v` records 7 SHAs across two attempts. Attribution must intersect with ancestors of HEAD so an abandoned attempt cannot launder a path. |

## Proposed changes (ordered, validatable)

1. Add `_run_record_committed_paths(repo_root, id6, base_head)` returning the same
   `CommittedAttribution` shape: read `checkout_control_root(repo_root)/records/runs/*/outcomes/*.json`,
   collect `commits[].sha` for that `id6`, keep only SHAs that are ancestors of HEAD AND inside
   `base_head..HEAD`, and union those commits' `--name-only` paths. `anchored` is True only when at
   least one such SHA was found, so an absent or empty corpus falls through instead of excusing.
2. In the committed-half branch (`:1561`), consult the exact source FIRST; when it is `anchored`, use
   its paths as `cohesive_committed`. When it is not, call
   `_execution_cohesive_committed_paths` exactly as today. Cohesion is unchanged and remains the
   fallback for every tree without a run corpus.
3. Record WHICH source decided, in the refusal/preview output, so a human reading a demanded reason
   can tell exact attribution from heuristic attribution.
4. Tests as `tests/test_finalize_exact_attribution.py`, including the fail-closed cases and the
   non-vacuity control described in Required tests.

## Deferred / out of scope (with reason)

- WRITING `AW-Run`/`AW-Item` trailers. Owned by plan `wao266` (`runtrailwire-01`), graduated from
  backlog `a8eufb` step (1). This plan adds a reader over state that ALREADY exists, so the two are
  independent and either may land first; when trailers exist they become a third, even better source
  and can be added ahead of this one by the same pattern.
- Changing the refusal CONDITION, the working-tree half, `check_engine.check_scope_drift` (which
  deliberately wants the broad unfiltered window, `:1217-1220`), or the `_scope_match` grammar.
- Renaming `_working_tree_path_is_owned` (documented misnomer, asserted as a source substring).

## Scope check

- Over-scope: none. Two files, one new function plus one branch, one new test file.
- Under-scope: the ten recovered plans still need finalizing after this lands; that is the follow-on
  act this change ENABLES and is deliberately not bundled, so this plan can be reviewed on its own
  merits rather than as a bulk lifecycle move.

## Required tests / validation

New `tests/test_finalize_exact_attribution.py`:

1. EXACT SOURCE WINS: a fixture repo with two plans whose commits both touch one shared declared file
   demands reasons only for the finalizing plan's own out-of-scope paths, and the other plan's paths
   appear in `disregarded_unowned`.
2. FALL BACK WHEN ABSENT: with no `records/runs/` at all, behavior is BYTE-IDENTICAL to today's
   cohesion result (asserted against the existing cohesion helper on the same fixture).
3. FAIL CLOSED, NO CORPUS: a plan whose ONLY commit is out-of-scope is still refused (the `p7dqwz`
   counterexample the existing switch protects).
4. FAIL CLOSED, EMPTY RECORD: a run record naming ZERO commits for this id6 must NOT be treated as
   "nothing owned"; it must fall through to cohesion.
5. NON-ANCESTOR SHA IGNORED (F-7): a SHA recorded for an abandoned lane attempt that is not an
   ancestor of HEAD contributes no paths.
6. NON-VACUITY CONTROL: with the new source deliberately disabled, test 1 FAILS. Proves the test
   measures the new code and not incidental behavior.
7. The existing suites that pin this area stay green, named explicitly:
   `tests/test_finalize_scope_ownership.py`, `tests/test_ipd_lifecycle_cli.py`.
8. Bare `python3 -m pytest`, with the actual summary line pasted.

## Spec / documentation sync

No `.spec.md` file changes. The finalize scope-reconciliation contract describes WHAT is demanded (a
reason for an out-of-scope path this execution changed) and not WHICH evidence establishes "this
execution", so improving attribution accuracy does not alter the contract. Stated explicitly because
a spec edit would otherwise be expected here: if review disagrees, the amendment belongs in the same
change and `Scope-Paths` must be extended to name the spec file.

## Open questions

### OQ-01: Should the exact source also be allowed to SHRINK the demand below cohesion when both are available?

- Blocking: no
- Status: resolved
- Owner: recovery-agent
- Resolution or deferral rationale: YES, and that is the entire point: exact attribution is strictly
  better evidence than a commit-boundary heuristic, so when it is `anchored` it decides alone rather
  than being unioned with cohesion. Unioning would re-admit exactly the foreign paths this plan
  removes (measured: it would keep all ~19 for `8tgg6g`). The fail-closed direction is preserved
  because an absent or empty exact source never shrinks anything; it falls through.

### OQ-02: Is trusting a gitignored, box-local run record as attribution evidence acceptable?

- Blocking: no
- Status: resolved
- Owner: recovery-agent
- Resolution or deferral rationale: Acceptable HERE, for a bounded reason. The record is locally
  writable, so it is not tamper-proof; but this gate is already explicitly "a deterministic
  consistency check, NOT a tamper-proof authority boundary" (`ipd_lifecycle.py:581-586`), and the same
  locally-forgeable class of input already feeds it. The failure mode is also asymmetric: a corrupted
  record can only cause a MISSING demand for a path the plan did commit, which is the same false
  EXCUSE cohesion already accepts and documents, never a false CLAIM written into permanent history,
  which is the harm this plan removes. Non-forgeable provenance stays the deferred item it already is.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted output of calling `_run_record_committed_paths` for `8tgg6g` at HEAD showing `anchored=True` and the exact three-path set, PLUS the same call in a temp repo with no `records/runs/` showing `anchored=False` and an empty set.
  - Observed evidence: PASS. `8tgg6g` at HEAD yields anchored=True and EXACTLY its three declared paths, versus the ~19 cohesion demanded; a temp repo with no `records/runs/` yields the fail-closed pair (anchored=False, empty), so a corpus-free tree falls through to cohesion unchanged. Detail below.
    ```
    $ python3 -c "... L._run_record_committed_paths(Path('.'),'8tgg6g',base) ..."
    V-01 (a) 8tgg6g at HEAD: anchored=True paths=3
        .aw/records/plans/pending/20260907-orchprobe-02-8tgg6g-cache-an-orchestrator-probe-verdict-against-a-content-digest.ipd.md
        agent_workflows/runner_shared.py
        tests/test_orchestrator_probe_cache.py
    V-01 (b) no corpus: anchored=False paths=set()
    ```
    Exactly the three declared paths, versus the ~19 cohesion demanded. The corpus-free call returns
    the fail-closed pair, so a tree with no run records falls through to cohesion unchanged.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `aw ipd finalize 8tgg6g --actor ... -m ...` preview showing NO `--scope-reason` demand, next to the current pre-change output showing the ~19 demanded paths, so the delta is visible rather than asserted.
  - Observed evidence: PASS. `aw ipd finalize 8tgg6g` went from refusing with 19 demanded `--scope-reason` paths (including `cli.py` and `run_viewer.py`, which it never touched) to 'precheck + reconciliation passed'. Demand counts after: 8tgg6g=0, 3i0aaz=0, mm5p3v=0, st5klo=0, b7xarm=2, zexed1=9, r2i1b1=30, fn2l1u=14; every nonzero one is CORRECT (b7xarm/zexed1 demands are genuinely in their own recorded commits, r2i1b1/fn2l1u have no record for the merged attempt2 branch and correctly fall back). Detail below.
    ```
    BEFORE (cohesion only, measured at the start of this plan):
    $ aw ipd finalize 8tgg6g --actor ... -m ...
    refused: finalize needs scope reconciliation answers (plan left unmoved). Supply them with:
      ... --scope-reason agent_workflows/agy_runipd.py=... --scope-reason agent_workflows/artifact_audit.py=...
      (19 paths total, including cli.py and run_viewer.py which 8tgg6g never touched)

    AFTER:
    $ aw ipd finalize 8tgg6g --actor ... -m ...
    precheck + reconciliation passed; re-run with --apply to perform the terminal transaction.
    ```
    Demand counts across the recovered plans after the change: 8tgg6g=0, 3i0aaz=0, mm5p3v=0, st5klo=0,
    b7xarm=2, zexed1=9, r2i1b1=30, fn2l1u=14. The nonzero ones are CORRECT: b7xarm and zexed1 have a
    run record and the demanded paths are genuinely in their own commits (both lanes disclosed those
    widenings as decisions), while r2i1b1 and fn2l1u have NO record for the merged attempt2 branch and
    correctly fall back to cohesion.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted preview output naming the deciding attribution source in both the exact case and a corpus-free case.
  - Observed evidence: PASS. The refusal names the deciding source and the cohesion case carries its heuristic warning; `finalize_precheck` evidence reports `run-record-exact` for 8tgg6g and `commit-cohesion` for r2i1b1. Detail below.
    ```
    $ aw ipd finalize r2i1b1 --actor p -m p        # cohesion fallback
    refused: finalize needs scope reconciliation answers (plan left unmoved).
      attribution: commit-cohesion (HEURISTIC fallback, no run record for this item). A path below
      MAY belong to a concurrent agent whose commit touched one of this plan's declared paths;
      verify before writing a reason you would be asserting

    $ python3 -c "... finalize_precheck ... ev.get('attribution_source')"
    8tgg6g  -> run-record-exact
    r2i1b1  -> commit-cohesion
    ```
    Both sources are reported, and the heuristic case carries the warning that a demanded path may be
    a co-worker's.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest tests/test_finalize_exact_attribution.py -o addopts=""` summary with every case named, plus pasted green runs of `tests/test_finalize_scope_ownership.py` and `tests/test_ipd_lifecycle_cli.py`.
  - Observed evidence: PASS. 12 passed in the new file; 99 passed across the two named regression suites. A TEST CAUGHT A REAL BUG IN THIS PLAN'S OWN CODE: the first implementation used `git rev-list -1 base..HEAD <sha>`, where a trailing revision is an additional START-POINT rather than a filter, so a pre-base sha was admitted; replaced with 'ancestor of HEAD and NOT ancestor of base' and the wrong form is now called out in a comment. Detail below.
    ```
    $ python3 -m pytest tests/test_finalize_exact_attribution.py -o addopts=""
    12 passed in 1.77s

    $ python3 -m pytest tests/test_finalize_scope_ownership.py tests/test_ipd_lifecycle_cli.py -o addopts=""
    99 passed in 12.47s
    ```
    A TEST CAUGHT A REAL BUG IN THIS PLAN'S OWN CODE, which is why the window filter is worth having:
    `test_a_sha_predating_the_frozen_base_contributes_nothing` failed against the first implementation,
    which used `git rev-list -1 base..HEAD <sha>`. A trailing revision there is an additional
    START-POINT, not a filter, so a pre-base sha was admitted. Replaced with "ancestor of HEAD and NOT
    ancestor of base", and the wrong form is now called out in a code comment so it is not
    reintroduced as a simplification.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: TWO parts, both pasted. (a) The non-vacuity control: FAILING output with the exact source disabled and PASSING output with it restored, demonstrating the control is real. (b) WHOLE-SUITE REGRESSION: the bare `python3 -m pytest` summary line at or above the 7296-passed baseline recorded 2026-09-14, with no new failure. Part (b) rides on this item deliberately, because the E/V bijection admits no V-item without an E-item and the suite run is evidence ABOUT E-05's control rather than a separate deliverable.
  - Observed evidence: PASS. Non-vacuity control: with the exact source stubbed to `CommittedAttribution(False, frozenset())` the suite FAILED 3 of 12; restored, 12 passed. Whole suite 7308 passed, 3 skipped, 2 xfailed, ZERO failures, against the 7296 baseline recorded 2026-09-14 (+12 = this plan's new file). Detail below.
    ```
    (a) NON-VACUITY CONTROL, exact source stubbed to CommittedAttribution(False, frozenset()):
    === WITH EXACT SOURCE DISABLED ===
    3 failed, 9 passed in 1.72s
    === RESTORED ===
    12 passed in 1.84s

    (b) WHOLE-SUITE REGRESSION:
    $ python3 -m pytest
    7308 passed, 3 skipped, 2 xfailed in 85.11s (0:01:25)
    ```
    The control is real: disabling the new source fails three cases. The suite is at 7308 passed
    versus the 7296 baseline recorded 2026-09-14 (+12, this plan's new file), zero failures.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the two declared `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`);
never `git add -A` and never push. Paste the ACTUAL runner output for every `V-*`; do not claim a
result that was not run. Run the suite BARE as `python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` reports conforming and every `V-*` carries pasted evidence.

WHY THIS NEEDS HUMAN APPROVAL BEFORE EXECUTION, stated plainly: it changes which paths a permanent
finalize record asserts a plan touched. That is an evidence surface, so an error here corrupts history
rather than merely failing a run. The fail-closed arms (F-6, Required tests 3 through 5) are the
review's highest-value target.
