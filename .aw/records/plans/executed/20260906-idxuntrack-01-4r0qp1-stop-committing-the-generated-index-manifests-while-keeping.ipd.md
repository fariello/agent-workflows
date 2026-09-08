# IPD: Stop committing the generated index manifests while keeping them refreshed

- Date: 2026-09-06
- Kind: child
- Concern: Multiple code sites put the generated `INDEX.json`/`INDEX.md` paths into a COMMIT path-set. Once child 02 gitignores those files, every one of them fails, and the failure is NOT a benign no-op: `git add -- <ignored-path>` exits 1 and stages NOTHING, so `git_commit_helper.offer_commit` returns `error` and commits NOTHING AT ALL, losing the real artifact's commit alongside the manifest's (measured, see F-7). This child removes the COMMIT half at every site while PRESERVING the REFRESH half, so the manifests stay current on disk and `check.stale-index` keeps working. It must land BEFORE untracking, because a `git commit -- <gitignored path>` in a journalled transaction is the sharpest failure mode in the whole change. REVIEW CORRECTION (2026-09-06, `/plan-review`): the authored scope named FOUR sites; a re-sweep at HEAD `7f80180e` found EIGHT contributors reaching FIVE distinct commit gateways (F-7..F-10). The four added ones are not new drift; all four existed at `7f80180e` and were missed. The `artifact_rename` site the plan named is additionally UNREACHABLE dead code (F-8).
- Scope: Every commit-path-set contributor for a generated manifest, plus one choke-point backstop, plus the tests that pin both halves. IN: dropping the manifest paths from `owned_paths` (`ipd_lifecycle.finalize`), from the `aw set` self-commit path list and `_index_paths_for_types`, from the TWO `cli.py` group/rename aggregation sites that actually perform the `MutationResult.index_paths` commit (which covers `plans_refs`, `research_refs` and `artifact_rename` at one place), from `artifact_rename`'s dead contribution, and from the two `*_archive` shard-move `touched` lists; correcting the `MutationResult` docstring that documents the removed contract; adding an ignored-path guard in `git_commit_helper.offer_commit` so a MISSED site degrades to "manifest not committed" instead of "nothing committed"; keeping every REGENERATION call untouched; retargeting the tests that actually assert a manifest was committed. OUT: `.gitignore`, `git rm --cached`, the `check.stale-index` semantics decision, the installer `.gitignore` TEMPLATE gap (child 02, see Deferred), and the three documents (all child 02); any change to WHEN a manifest is regenerated; the broader dead-code cleanup inside `artifact_rename`'s unreachable auto-index blocks.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/status_set.py, agent_workflows/artifact_rename.py, agent_workflows/cli.py, agent_workflows/plans_refs.py, agent_workflows/research_refs.py, agent_workflows/plans_archive.py, agent_workflows/research_archive.py, agent_workflows/git_commit_helper.py, tests/test_auto_index_on_mutation.py, tests/test_selfcommit_adoption.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: idxuntrack
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: ila6vl
- Id: 4r0qp1

## Workflow history
- 2026-09-08 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Lane recovered and merged during the stranded-lane recovery; integration had been refused by the binary whole-repo suite gate (root cause tracked by 32ij2j/xtklpd) [Scope reconciliation - out-of-scope agent_workflows/artifact_refs.py: Modified by THIS plan's own commits (674f2c68 739fc69c) but outside its declared Scope-Paths; the edit is part of the reviewed change and is recorded here rather than by widening the fence after the fact.; out-of-scope agent_workflows/attention.py: NOT THIS PLAN'S EDIT. Belongs to d099dc25 feat(att): add --id6-only, --active, --not-active, and --arci, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/attention_contract.py: NOT THIS PLAN'S EDIT. Belongs to 25390dec feat(attention): add --order-by runs and --run-status filter, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope agent_workflows/run_viewer.py: NOT THIS PLAN'S EDIT. Belongs to 9c589d2d runsverify 7wei1o: refuse an unresolvable `aw runs` target in, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_attention.py: NOT THIS PLAN'S EDIT. Belongs to d099dc25 feat(att): add --id6-only, --active, --not-active, and --arci, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_finalize_isolated_commit.py: NOT THIS PLAN'S EDIT. Belongs to 9db0ed81 fix(lifecycle): attribute finalize's committed scope audit by, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_finalize_scope_ownership.py: NOT THIS PLAN'S EDIT. Belongs to 9db0ed81 fix(lifecycle): attribute finalize's committed scope audit by, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_next_ordering.py: NOT THIS PLAN'S EDIT. Belongs to 25390dec feat(attention): add --order-by runs and --run-status filter, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_orchestrator_retirement.py: Modified by THIS plan's own commits (674f2c68 739fc69c) but outside its declared Scope-Paths; the edit is part of the reviewed change and is recorded here rather than by widening the fence after the fact.; out-of-scope tests/test_run_noun_split.py: NOT THIS PLAN'S EDIT. Belongs to 9c589d2d runsverify 7wei1o: refuse an unresolvable `aw runs` target in, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; out-of-scope tests/test_run_viewer.py: NOT THIS PLAN'S EDIT. Belongs to ca921309 merge lane 7wei1o: recover stranded validated work, a concurrent lane or agent; verified absent from this plan's own commits (674f2c68 739fc69c). Attributed here only because the finalize scope audit reads the WORKING TREE rather than this execution's commits, which is exactly the defect approved plan h9cn0y fixes.; in-scope-unmodified tests/test_auto_index_on_mutation.py: acknowledged]
- 2026-09-07 executed (opencode/its_direct/pt3-claude-opus-5-1m-us, run run-20260908T030809Z-1812970): E-01..E-08 performed, V-01..V-08 verified with pasted evidence. E-05/E-08 found a NINTH commit-path contributor the author and the review both missed (`artifact_refs.plan_reference_rewrites` rewrote the generated INDEX.md as a citing document, and the caller appended every rewritten file to its commit path-set, so `aw rename plans`/`aw group plans` committed the manifest anyway); fixed by honoring the module's existing `_SKIP_NAMES` when scanning. That fix touches `agent_workflows/artifact_refs.py`, which `- Scope-Paths:` does not declare: reported for human review in the decisions register (DECISION 1-4r0qp1-D1). Suite: 5621 passed, 32 failed, all 32 pre-existing lane-environment failures with node IDs IDENTICAL to the base measurement (zero regressions).
- 2026-09-07 approved (aw set): status set to approved
- 2026-09-06 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-011 (10 fixed, PR-008 deferred to child 02). Re-swept commit-path contributors backward from every commit gateway: 4 authored -> 8 real, one of the 4 dead code. Measured that git add of an ignored path stages NOTHING and loses the artifact's commit.
- 2026-09-06 to-review (aw set): Authored and ready for critique: aw ipd lint conforming, E-01..E-05 with a V-* bijection, every V-item demanding pasted evidence, no TODO placeholders, and OQ-01 resolved from repository evidence rather than deferred to the maintainer.

- 2026-09-06 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-06 authored (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `ila6vl` (maintainer decision 2026-08-31 to stop tracking the generated manifests; external-consumer check answered 2026-09-06: none). Every consumer line citation on the item was RE-VERIFIED at HEAD `7f80180e` rather than trusted, and two had drifted: `ipd_lifecycle` owned_paths moved from the item's `:1630` to `:2340`, and the `status_set` auto-refresh from `:823-894` to `:936-972`. Split from the item's single scope because the COMMIT-path removal must strictly precede untracking.

## Goal

Make every code path that currently COMMITS a generated index manifest stop doing so, while leaving every path that REGENERATES one untouched. After this child, the manifests are still written and still byte-comparable on disk, but no `aw` verb tries to include them in a commit. That is the precondition that makes child 02's `git rm --cached` safe.

Add ONE defensive backstop at the shared commit gateway, because the review's own re-sweep is the argument for it: the authored plan enumerated four sites and there were eight, so "we found them all" is a claim this Set has already falsified once. With the guard, a site missed by BOTH the author and this review degrades to a manifest silently not committed instead of the artifact commit vanishing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared backstop (do this FIRST)

- [x] E-06 In `git_commit_helper.offer_commit`, filter GITIGNORED paths out of the staging set instead of letting `git add` fail the whole commit. Locate by SYMBOL (`offer_commit`, its `rc, _out, err = _git(repo_root, ["add", "--", *rel_paths])` step at `:450`). Before staging, drop any `rel_paths` entry that `git check-ignore` reports as ignored; if that leaves the set EMPTY, return the existing `nothing-to-commit` outcome rather than `error`. Print a short note naming each dropped path so the drop is never silent. Do this FIRST so it is in place while E-01..E-05 land, and so a site anyone missed cannot take an artifact commit down with it. Do NOT add `-f`/`--force` anywhere: force-adding an ignored path is the exact behavior this Set exists to remove. Rationale, measured (F-7): with one ignored path in a two-path set, `offer_commit` returned `status=error`, `staged=()`, and created NO commit, so the real artifact went uncommitted too.
  - Depends on: none
  - Expected outcome: a path-set mixing a real artifact with a gitignored manifest commits the artifact and skips the manifest, with the skip reported; an all-ignored set is `nothing-to-commit`, not `error`.
  - Execution state: performed

### Task group 2: remove the commit half, preserve the refresh half

- [x] E-01 In `ipd_lifecycle._finalize_transaction`, stop putting the two plans-manifest paths into the transaction's `owned_paths`. Locate by SYMBOL (`owned_paths`, the `index_json_rel`/`index_md_rel` locals), not by the line number, which has already drifted once. Keep the manifest REGENERATION the MUTATING phase performs (`_refresh_plans_index_fail_loud`), which is a fail-loud gate and must stay. THREE journal consumers key on these entries and each needs a decision, so handle them explicitly rather than discovering them at runtime: (a) `git_index_entries` (`:2412`) captures `git ls-files --stage` for owned paths, which is harmless once untracked (it simply records nothing); (b) `_rollback_precommit` (`:1681-1688`) iterates `owned_paths` calling `git restore --staged -- <p>`, and that command exits 1 with "pathspec did not match any file(s) known to git" for an untracked path (measured), so leaving a manifest in `owned_paths` would make rollback emit a spurious error; (c) `index_json_before`/`index_md_before` (`:2410-2411`) snapshot the manifest CONTENT and are read by nothing (verified: no other reference in `agent_workflows/` or `tests/`), so leave them or drop them, but say which and why. Also note `stage` (`:2467`) filters on existence, so it does NOT protect against an ignored path, only a missing one.
  - Depends on: E-06
  - Expected outcome: `owned_paths` contains the plan's source and destination paths only; the finalize commit no longer names a manifest; the manifest is still refreshed on disk during the transaction; rollback no longer references an untracked path.
  - Execution state: performed

- [x] E-02 In `status_set.py`, stop contributing the manifest paths to the `aw set` self-commit. The ONE site that feeds the commit is `_index_paths_for_types` (`:1122-1138`), consumed at `_offer_self_commit:1165`. Delete the function and that call, having first confirmed by grep that nothing else consumes it (verified at review time: `_offer_self_commit` is its only caller). Do NOT touch `_auto_index_types` (`:912-988`): its `changes.append(Change(...))` entries at `:936-937,971-972` are the agent-mode CHANGES REPORT, not a commit path-set, and the plan's original citation of those lines as commit contributors was WRONG (F-11). They must keep reporting the refresh, and `tests/test_auto_index_on_mutation.py::test_aw_set_agent_output_includes_index_in_changes` must keep passing UNCHANGED as proof.
  - Depends on: E-06
  - Expected outcome: an `aw set` status change refreshes the manifests on disk, still REPORTS them in agent-mode changes, and commits only the artifact whose status changed.
  - Execution state: performed

- [x] E-03 Remove the `MutationResult.index_paths` commit contribution at the TWO aggregation sites that actually perform the commit: `cli.py:8557` (`index_all.extend(result.index_paths)`, committed at `:8560-8569` via `_offer_records_commit`) and `cli.py:11057-11062` (the `aw research set-assign`/`mv` branch). These two are the real gateway for `plans_refs` (`:451,499`), `research_refs` (`:347,367`) AND `artifact_rename` (`:658,804`), so fixing them here covers all three producers at the choke point instead of in three places. Then stop the producers contributing at all: make `artifact_rename._index_paths_for` (`:62-80`) unused and delete it with its two call sites, and do the same for `plans_refs._index_paths_for` (`:413-423`) and `research_refs._index_paths_for` (`:310-322`). Prefer removing the `index_paths` FIELD from `MutationResult` (`plans_refs.py:156`) entirely if no consumer remains; if you keep the field for compatibility, UPDATE its docstring (`plans_refs.py:148,150`), which currently states "The commit path-set is `touched_paths + index_paths`" and would otherwise document a contract the code no longer honors. Note `artifact_rename`'s contribution is DEAD at HEAD (F-8): its auto-index blocks are gated on `artifact_type in {"plans","research"}` but `artifact_types.TYPE_BACKENDS` routes plans/research to `plans_refs`/`research_refs`, never to `artifact_rename`. Remove it anyway, and record that it was dead so the next reader is not misled.
  - Depends on: E-06
  - Expected outcome: `aw rename <type>` / `aw group <type>` / `aw research mv` refresh the manifests and commit only the renamed artifact plus any files whose references were rewritten; no `MutationResult` docstring claims a contract the code no longer has.
  - Execution state: performed

- [x] E-07 Remove the manifest paths from the two ARCHIVE shard-move commit sets, which the authored plan missed entirely (F-9). `plans_archive.apply_shard_moves` (`:159-182`) appends both manifests to the `touched` list it RETURNS, and that list is committed verbatim by `_offer_archive_commit` (`:283-307`); `research_archive` has the identical shape at `:274-283` committed at `:387-411`. Note the research one appends UNCONDITIONALLY (no `p.exists()` guard), unlike its plans twin. Keep both `_refresh_index` / inline regeneration calls exactly as they are; remove only the append loops. Mind that `_offer_archive_commit` also calls `_gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *touched])` before committing, which is harmless for an untracked path (measured: exit 0), so no change is needed there.
  - Depends on: E-06
  - Expected outcome: `aw archive plans` / `aw archive research` commit exactly the moved artifact files, with the manifests refreshed on disk and absent from the commit.
  - Execution state: performed

### Task group 3: pin both halves in tests

- [x] E-04 Retarget the tests that actually assert a manifest was COMMITTED. Do NOT expect to find them in `tests/test_auto_index_on_mutation.py`: that module contains ZERO commit assertions (verified: `grep -c commit` returns 0), so the authored E-04 premise was wrong (F-12) and its 6 tests should pass UNCHANGED as the proof that the refresh half survived. The real commit assertions are in `tests/test_selfcommit_adoption.py`: `:265` (`assertTrue(any(f.endswith("INDEX.json") for f in files))`, on the archive commit) and `:348` (`assertTrue(any(p.endswith("INDEX.json") for p in mr.index_paths))`, on the plans backend). INVERT both to assert the manifest is ABSENT from the committed set, keeping their existing assertions that the real artifact IS committed. Add one case for E-06's guard: a path-set mixing a real file with a gitignored one commits the real file. Do not delete a test to make it pass.
  - Depends on: E-01, E-02, E-03, E-06, E-07
  - Expected outcome: the suite fails if a future change stops refreshing a manifest, fails if one starts committing a manifest again, and fails if the ignored-path guard regresses.
  - Execution state: performed

- [x] E-05 Re-sweep for any REMAINING commit-path contributor and classify every hit. Sweep `INDEX.json`/`INDEX.md`/`INDEX_JSON`/`INDEX_MD`/`index_paths` across `agent_workflows/` (exclude `__pycache__`) and classify each as writer, path constant, help text, reader, changes-report entry, or commit-path contributor. Cross-check from the OTHER direction too, which is how this review found the four missed sites: enumerate every `offer_commit` / `_offer_records_commit` / `_offer_archive_commit` / `_offer_self_commit` call and trace each one's path-set to its origin. The eight known contributors are E-01, E-02, E-03 (x2 gateway + 3 producers), and E-07 (x2); report any NINTH rather than silently expanding scope.
  - Depends on: E-01, E-02, E-03, E-07
  - Expected outcome: a pasted two-direction classification with zero unaccounted commit-path contributors, or a named new one reported for a scope decision.
  - Execution state: performed

- [x] E-08 Prove the end state against a REAL gitignore, which is the only check that can catch a ninth site. In a scratch clone or worktree, apply child 02's ignore locally (add the four paths to `.aw/.gitignore` and `git rm --cached` them) WITHOUT committing that change to this branch, then exercise `aw set`, `aw rename plans`, `aw group plans`, `aw archive plans`, `aw research mv` and `aw ipd finalize`, and confirm each still commits its artifact. This is a temporary local experiment to validate child 01; revert it and confirm the branch does not carry it. If any verb fails, that is a ninth site: report it.
  - Depends on: E-01, E-02, E-03, E-05, E-06, E-07
  - Expected outcome: every mutating verb commits its artifact successfully under a real gitignore, proving child 02 can land safely; the experimental ignore is reverted and provably absent from the branch.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The framework-owned `.aw/.gitignore` is the established mechanism for ignoring generated content, and it already carries a near-identical precedent: `system/layout.json` and `system/layout.schema.json` are gitignored with the comment "tracking generated output is exactly the git drift install-time emission exists to avoid." The maintainer chose that mechanism explicitly for `layout.json` on 2026-09-01, citing `ila6vl`. Child 02 follows it rather than the user's root `.gitignore`.
- `aw index plans --check` byte-compares an in-memory rebuild against the file ON DISK, never against git. Verified by running it at HEAD (`plans index --check: clean`, 490 plans). This is why untracking does not break the check, and it is the item's own point 6.
- The suite must be run bare (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.
- This is a shared checkout with concurrent agents and runs. Prefer an isolated worktree for execution; a measured lesson from 2026-09-06, when a co-worker's mid-run commit caused 56 unrelated failures to be misattributed to a local change.
- Every records self-commit funnels through ONE helper, `git_commit_helper.offer_commit`, reached via four thin wrappers (`_offer_records_commit` in `cli.py`, `_offer_archive_commit` in both `*_archive` modules, `_offer_self_commit` in `status_set.py`) plus direct calls from `specs.py`, `work_cmd.py` and `oc_runipd.py`. Enumerating those call sites and tracing each path-set BACKWARD is a more reliable way to find commit-path contributors than grepping for `INDEX`, and it is how this review found the four the author missed. `ipd_lifecycle.finalize` is the one exception: it stages and commits directly rather than through the helper, so it needs its own treatment (E-01) and is not covered by E-06's guard.
- `git add -- <ignored-path>` is NOT tolerant: it exits 1 and stages nothing, including the non-ignored paths in the same invocation. Any code that builds a mixed path-set must therefore filter ignored paths itself. Measured during this review; see F-7.

## Findings

| Id | Severity | Location (HEAD `7f80180e`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.py:2340-2343` | Both plans-manifest paths go into `owned_paths` for the finalize lifecycle commit. This is the sharpest edge: `finalize` is a journalled transaction with rollback and a committed-incomplete resume path, so a path that cannot be committed could wedge it. | source read; `owned_paths = [plan_rel, dest_rel, index_json_rel, index_md_rel]` |
| F-2 | MED | `status_set.py:936-937,971-972` | The `aw set` auto-refresh collects manifest paths for its self-commit, for plans and research separately. | source read |
| F-3 | MED | `status_set.py:1122-1138` | `_index_paths_for_types` exists solely to compute manifest self-commit paths (docstring names jgcm68 E-05). | docstring: "Repo-relative INDEX.json/INDEX.md paths for the indexed types just refreshed" |
| F-4 | MED | `artifact_rename.py:63-74` | Computes manifest paths for the rename self-commit. | docstring: "jgcm68 self-commit paths" |
| F-5 | LOW | item `ila6vl` body | Two of the item's line citations had drifted in 6 days (`:1630` -> `:2340`; `:823-894` -> `:936-972`). The consumers are all still real. | re-verified at HEAD `7f80180e` |
| F-6 | INFO | CI | No CI workflow references INDEX at all (`local-leaks.yml`, `secret-scan.yml`, `tests.yml`), so the item's scope point 8 ("confirm nothing in CI expects a committed baseline") is already satisfied. | `grep -rn INDEX .github/` returns nothing |
| F-7 | BLOCKER | `git_commit_helper.py:450-457` | The plan's premise that a missed site "silently no-ops" is FALSE, and the true behavior is worse. `git add -- <ignored>` exits 1 and stages NOTHING; `offer_commit` then resets its own paths and returns `error`, creating NO commit, so the REAL ARTIFACT goes uncommitted alongside the manifest. A single missed site therefore silently stops an artifact from being committed. Addressed by new E-06. | measured: `offer_commit(repo,['sub/plan.md','sub/INDEX.json'])` with `sub/INDEX.json` ignored returned `status=error`, `staged=()`, `git log` unchanged, `sub/plan.md` left dirty |
| F-8 | HIGH | `artifact_rename.py:62-80,658,804`; `artifact_types.py:75-118` | The `artifact_rename` site the plan scopes as one of its four is UNREACHABLE DEAD CODE. Both auto-index blocks gate on `artifact_type in {"plans","research"}`, but `TYPE_BACKENDS` routes `plans`->`plans_refs` and `research`->`research_refs`; `artifact_rename` only ever receives specs/prompts/backlog/walkthroughs/roadmaps/releases/other, for which `_index_paths_for` returns `()`. So E-03 as authored would have fixed nothing, while the two LIVE producers (`plans_refs`, `research_refs`) were unscoped. | `grep -n '"plans"\|"research"' artifact_types.py`; `_index_paths_for` returns `()` for every type actually routed there |
| F-9 | HIGH | `plans_archive.py:159-182,283-307`; `research_archive.py:274-283,387-411` | Two commit-path contributors the plan missed entirely: both `apply_shard_moves`-style functions append the manifests to the `touched` list that `_offer_archive_commit` commits verbatim. `aw archive plans`/`aw archive research` would hit F-7 and commit NOTHING. `research_archive` appends without an `exists()` guard. Added as E-07. | source read; `_offer_archive_commit(args, repo_root, touched)` at `plans_archive.py:239,279` |
| F-10 | HIGH | `plans_refs.py:413-423,451,499`; `research_refs.py:310-322,347,367`; `cli.py:8557,11057` | The two LIVE `MutationResult.index_paths` producers and the two aggregation sites that actually commit them were unscoped. `cli.py:8557`/`:11057` are the shared choke point for all three producers, so removing the contribution there covers `aw group`/`aw rename`/`aw research mv` at once. `MutationResult`'s docstring (`plans_refs.py:148,150`) documents the removed contract and would go stale. Folded into E-03. | source read; `_offer_records_commit(..., paths=[*touched_all, *index_all])` at `cli.py:8565` |
| F-11 | MED | `status_set.py:912-988` | The plan's citation of `status_set.py:936-937,971-972` as commit-path contributors is WRONG. Those lines append `Change(...)` records to the agent-mode CHANGES REPORT, not to any commit path-set; the only commit contributor in the module is `_index_paths_for_types` (`:1122-1138`) via `_offer_self_commit:1165`. Following the plan as authored would have deleted correct reporting behavior and broken `test_aw_set_agent_output_includes_index_in_changes`. Corrected in E-02. | source read; `_auto_index_types(..., changes=changes)` builds `Change`, never a commit list |
| F-12 | MED | `tests/test_auto_index_on_mutation.py` | E-04's premise ("for each case that currently asserts a manifest was committed, invert it") is false for the module it names: that file has ZERO commit assertions and only asserts on-disk refresh. The real commit assertions are in `tests/test_selfcommit_adoption.py:265,348`, which the plan never named. Corrected in E-04. | `grep -c commit tests/test_auto_index_on_mutation.py` -> `0`; both modules pass at HEAD (6 and 20 tests) |
| F-13 | MED | `ipd_lifecycle.py:1681-1688` | E-01 asked the executor to "confirm no rollback/journal step keys on those two entries" and to report if one does. THREE do, so the answer is pre-resolved rather than left as a runtime discovery: `_rollback_precommit` calls `git restore --staged -- <p>` over `owned_paths`, which exits 1 on an untracked path (measured: "pathspec did not match any file(s) known to git"); `git_index_entries` (`:2412`) captures stage lines; `index_json_before`/`index_md_before` (`:2410-2411`) snapshot content and are read by NOTHING. Enumerated in E-01. | measured `git restore --staged -- <untracked>` -> exit 1; `grep -rn index_json_before agent_workflows/ tests/` -> one definition, no reader |
| F-14 | MED | `engine.py:4274-4308,5323-5370` | The `.aw/.gitignore` the repo carries is byte-identical to `engine._AW_GITIGNORE_TEMPLATE` (verified), and `_ensure_aw_gitignore` back-fills patterns for already-installed repos. Child 02 edits the repo's FILE only, so unless the template and the back-fill list also gain the four paths, every fresh `aw install` and every existing managed repo will keep tracking the manifests, and this Set's fix would not generalize. Not in this child's scope; raised as an explicit dependency for child 02 (see Deferred). | `engine._AW_GITIGNORE_TEMPLATE == Path('.aw/.gitignore').read_text()` -> `True` |

## Proposed changes (ordered, validatable)

1. E-06 lands the shared `offer_commit` guard FIRST, so every later step is protected while it is being made and a ninth site cannot take an artifact commit down with it.
2. E-01 removes the manifest paths from the finalize transaction's commit set and settles its three journal consumers (highest-risk site next, so a problem surfaces before the cheaper edits).
3. E-02, E-03 and E-07 remove the contribution from the `aw set` self-commit, the group/rename `MutationResult` gateway (covering all three producers), and the two archive shard-move commits.
4. E-04 pins both halves in the tests that actually assert them.
5. E-05 re-sweeps from BOTH directions (manifest symbols, and every commit gateway's path-set) to prove no ninth site.
6. E-08 exercises every mutating verb under a REAL local gitignore, the only check that can catch a site all three passes missed.

## Deferred / out of scope (with reason)

- `.gitignore` entries and `git rm --cached`: child 02. Doing them here would mean this child's own validation runs against files that are simultaneously tracked and gitignored. E-08's temporary local experiment is deliberately NOT a commit of that change.
- The INSTALLER `.gitignore` template gap (F-14): child 02, which owns the `.gitignore` change and must extend `engine._AW_GITIGNORE_TEMPLATE` and the `_ensure_aw_gitignore` back-fill list alongside the repo's own file, or the fix will not reach a fresh install or any already-managed repo. Recorded here because this review found it; assigned there because that is where the gitignore work lives.
- The `check.stale-index` semantics decision: child 02, because it is only forced once the files are untracked.
- The three documents (`.aw/records/plans/README.md`, `.aw/records/research/README.md`, `CONTRIBUTING.md`): child 02, where the statements actually become wrong.
- Any change to regeneration TIMING or to `aw index` itself: not needed by this item and would widen the blast radius.
- The wider dead-code cleanup in `artifact_rename`'s two unreachable auto-index blocks (F-8): remove only the commit-path contribution here. Deleting the surrounding regeneration blocks is a separate refactor with its own risk, and leaving them costs nothing once they contribute no commit path.

## Scope check

- Over-scope: `git_commit_helper.py` (E-06) is a defensive change to a shared helper, not strictly required to make the four verbs work. Justified and kept: F-7 measured that a missed site loses the ARTIFACT's commit, and this review found four sites the author missed, so the residual risk of a ninth is demonstrated rather than hypothetical. It is additive (it only ever removes an unstageable path) and cannot change behavior while nothing is gitignored.
- Under-scope: none remaining. The authored scope was materially under-scoped (F-8/F-9/F-10 named four more contributors, one of the original four being dead code); corrected above.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, with the baseline measured in that worktree at execution time and pasted. Compare failing NODE IDS, not totals: ~35 environment-related failures are expected in any lane worktree (backlog `agrlvw`), and a concurrent co-worker commit can move the total under the executor's feet. Baseline measured at review time on the main checkout, for reference: `tests/test_auto_index_on_mutation.py` 6 passed, `tests/test_selfcommit_adoption.py` 20 passed, `tests/test_plans_refs.py tests/test_research_refs.py tests/test_plans_archive.py tests/test_research_archive.py` 44 passed.

Beyond the suite: E-01 requires an actual `aw ipd finalize` exercise (or the finalize test subset) proving the transaction still completes; E-08 requires every mutating verb exercised under a real local gitignore, which is the validation that would have caught F-8/F-9/F-10 and is therefore the one that must not be skipped.

## Spec / documentation sync

No user-facing document changes here; the three documents that assert the manifests are committed become wrong only once child 02 untracks them, and child 02 owns correcting them.

Two INTERNAL doc-in-code syncs ARE required and are part of the E-items rather than deferred: the `MutationResult` docstring (`plans_refs.py:148,150`), which states "The commit path-set is `touched_paths + index_paths`" and becomes false (E-03); and `offer_commit`'s docstring/`Parameters` block, which currently promises that "ONLY these are ever staged ... including deletions, renames, and any regenerated index" and must record the new ignored-path filtering and its `nothing-to-commit` outcome (E-06).

## Open questions

### OQ-01: Delete `_index_paths_for_types` or make it return empty?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW from repository evidence, so the executor no longer has to decide: DELETE it. `grep -n "_index_paths_for_types" agent_workflows/*.py` shows exactly one caller, `_offer_self_commit` (`status_set.py:1165`), and that call is itself being removed by E-02, leaving the function with no consumer at all. A dead function kept "returning empty" is a trap for the next reader, who cannot tell whether it is disabled or merely unused. Same ruling applied to the three `_index_paths_for` helpers in E-03. Not escalated to the maintainer: internal helper shape, no public contract.

### OQ-02: Is the shared `offer_commit` guard (E-06) wanted, or should the fix stay confined to the enumerated call sites?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW: include it. The evidence is this Set's own history, not a hypothetical. The authored plan named four contributors; a re-sweep found eight, and one of the four named was dead code, so the estimate was wrong in both directions. F-7 measures the cost of a single missed site as the LOSS OF THE ARTIFACT'S OWN COMMIT, silently, which is precisely the failure class that stranded lane `ueg5cf` and motivated the parent item. The guard is additive, is inert while nothing is gitignored, and turns that failure into a reported skip. REVERSIBLE: it is a local edit to one helper that a later maintainer can drop by deleting the filter. Alternative rejected: rely on E-05's sweep alone, which is the same kind of enumeration that already proved insufficient once here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the post-change `owned_paths` construction showing no manifest entries, AND pasted output of a finalize exercise (a real `aw ipd finalize` on a scratch plan, or the finalize test subset) completing successfully. Paste the resolution of all THREE journal consumers named in E-01: the current `_rollback_precommit` loop showing it no longer iterates a manifest path, the `git_index_entries` call, and the decision taken on `index_json_before`/`index_md_before` with the grep proving no reader.
  - Observed evidence: `owned_paths` is now `[plan_rel, dest_rel]`; a real begin+finalize under a genuinely gitignored manifest pair exits 0 and commits only the two plan paths; all three journal consumers resolved.
    (a) post-change `owned_paths` (`ipd_lifecycle.py:2402-2412`), no manifest entries:
    ```
        plans_dir = _plans_dir_of(repo_root, plan_path)
        dest_rel = _repo_relative(repo_root, plans_dir / "executed" / Path(plan_path).name)
        # The generated plans manifests (INDEX.json/INDEX.md) are deliberately ABSENT here. ...
        owned_paths = [plan_rel, dest_rel]
    ```
    (b) a REAL end-to-end `begin` + `finalize` (`ipd_lifecycle.begin`/`.finalize`, apply=True) in a
    scratch repo where BOTH manifests are genuinely gitignored AND `git rm --cached`ed first, which is
    the condition that would wedge the transaction if a manifest were still in `owned_paths`:
    ```
      IGNORED  .aw/records/plans/INDEX.json
      IGNORED  .aw/records/plans/INDEX.md
    manifests still tracked: (none)

    begin exit_code: 0 - begin receipt written for ff6666 at base c3b0df797fb7 (actor opencode/e08).
    plans index --check: clean

    finalize exit_code: 0
    finalize message: finalized ff6666 -> executed at de72bdf392b0 (actor opencode/e08).
    commit created: True de72bdf392b047c2f71c384f3f19922a00a6485b
    committed paths: ['.aw/records/plans/executed/20260101-demo-01-ff6666-demo.ipd.md', '.aw/records/plans/pending/20260101-demo-01-ff6666-demo.ipd.md']
    OK: no manifest in the commit
    plan now at: .aw/records/plans/executed/20260101-demo-01-ff6666-demo.ipd.md
    manifest refreshed on disk (mtime changed): True
    index --check: plans index --check: clean
    clean (fail-loud refresh converged)
    ```
    Note the last three lines: the manifest was still REGENERATED (mtime changed) and `--check`
    converged, so the refresh half provably survived while the commit half is gone.
    Also `python3 -m pytest tests/test_finalize_isolated_commit.py tests/test_finalize_scope_ownership.py
    tests/test_lifecycle_fixtures.py -o addopts="" -q` -> `164 passed`.
    (c) THREE journal consumers resolved:
      * `_rollback_precommit` (`:1743-1751`) iterates `journal["owned_paths"]`, which now holds only
        `[plan_rel, dest_rel]`, so no `git restore --staged` is issued for an untracked manifest and
        the spurious "pathspec did not match" error is structurally impossible. Loop unchanged:
        ```
            owned = journal.get("owned_paths", [])
            prior_index = journal.get("git_index_entries", {})
            for p in owned:
        ```
      * `git_index_entries` (`:2476`) unchanged, still `_git_index_entries(repo_root, owned_paths)`;
        it now simply captures stage lines for the two plan paths.
      * `index_json_before`/`index_md_before`: DROPPED, with the unused `_read_or_none` local helper
        (see DECISION 1-4r0qp1-D2 for the rationale: they described a content-restore that no code
        performs). Grep proving no reader existed and none remains:
        `grep -rn "index_json_before\|index_md_before" agent_workflows/ tests/ --include=*.py` ->
        one hit, the explanatory comment at `ipd_lifecycle.py:2463`; zero code references.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste an `aw set` status change on a scratch artifact showing (a) the manifest file's content updated on disk, and (b) `git show --stat` of the resulting commit containing no INDEX path. ALSO paste `python3 -m pytest tests/test_auto_index_on_mutation.py -o addopts="" -q` still at 6 passed, which is the proof the agent-mode changes report (F-11) was NOT damaged, and paste a grep showing `_index_paths_for_types` no longer exists.
  - Observed evidence: `aw set` commits only the artifact while the manifest content updates on disk; `test_auto_index_on_mutation.py` still 6 passed UNCHANGED (F-11 intact); `_index_paths_for_types` deleted.
    `aw set` on a scratch repo where both plans manifests are REALLY gitignored + `git rm --cached`ed:
    ```
    $ python3 -m agent_workflows set to-review aa1111 --commit -m "v02 evidence"
    -    plan        20260101-gamma-00-aa1111  reviewed → to-review
    committed 1 path(s): 09ebdb8aea70b55a38a0b7d1c779b484b71dc43f

    $ git show --stat --format="%H %s" HEAD
    09ebdb8aea70b55a38a0b7d1c779b484b71dc43f chore(records): set status to-review
     .aw/records/plans/pending/20260101-gamma-00-aa1111-first.ipd.md | 3 ++-
     1 file changed, 2 insertions(+), 1 deletion(-)
    ```
    (b) holds: the commit contains ONLY the plan file, no INDEX path.
    (a) holds: the manifest content ON DISK was updated by the same command, i.e. the refresh half ran:
    ```
    $ grep -o '"status": "[a-z-]*"' .aw/records/plans/INDEX.json | sort | uniq -c
          1 "status": "approved"
          1 "status": "executed"
          1 "status": "to-review"      <- the new status, written by the auto-refresh
    ```
    Agent-mode changes report intact (F-11 NOT damaged), UNCHANGED test module:
    ```
    $ python3 -m pytest tests/test_auto_index_on_mutation.py -o addopts="" -q
    ......                                                                   [100%]
    6 passed in 0.38s
    ```
    `_index_paths_for_types` is gone:
    ```
    $ grep -rn "_index_paths_for_types" agent_workflows/ tests/ --include=*.py
    (zero hits: deleted)
    ```
    Its now-unused `touched_types` parameter was also removed from `_offer_self_commit` (both call
    sites updated) rather than left as a dead argument for the next reader to puzzle over.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste an `aw rename plans` AND an `aw group plans` AND an `aw research mv` exercise (all three reach different call sites) each showing the manifest refreshed on disk and absent from the resulting commit's `--stat`. Paste the post-change `cli.py` aggregation sites showing no `index_paths` contribution, and the updated (or removed) `MutationResult` docstring proving it no longer claims `touched_paths + index_paths` is the commit set.
  - Observed evidence: all three run in the scratch repo with all four manifests REALLY gitignored.
    Each verb's own output says `wrote ... INDEX.json, INDEX.md` (the refresh half ran), while the
    commit `--stat` contains only the artifact:
    ```
    ############ aw rename plans bb2222 --slug v03-renamed --apply --commit
      renamed .../pending/20260101-alpha-02-bb2222-renamed-second.ipd.md -> .../20260101-alpha-02-bb2222-v03-renamed.ipd.md
      wrote        .aw/records/plans/INDEX.json, INDEX.md (3 plans)
      committed 1 path(s): 0b56d8709815ee52dbe90dac928734af8ce2c76b
        COMMIT refactor(plans): rename bb2222 and rewrite refs
       .../plans/pending/20260101-alpha-02-bb2222-v03-renamed.ipd.md     | 8 ++++++++
      OK: no manifest in commit
    ############ aw group plans aa1111 --set v03set --rename --apply --commit
      renamed .../pending/20260101-gamma-00-aa1111-first.ipd.md -> .../20260101-v03set-00-aa1111-first.ipd.md
      wrote        .aw/records/plans/INDEX.json, INDEX.md (3 plans)
      committed 1 path(s): 2f1e6e75e5c3af3092cfd33b7e3bae352e0ea4e7
        COMMIT refactor(plans): group aa1111 and rewrite refs
       .../plans/pending/20260101-v03set-00-aa1111-first.ipd.md      | 11 +++++++++++
      OK: no manifest in commit
    ############ aw research mv ee5555 --slug v03-other --apply --commit
      renamed .../20260101-beta-01-ee5555-renamed-other.notes.md -> .../20260101-beta-01-ee5555-v03-other.notes.md
      wrote        .agents/docs/research/INDEX.json, INDEX.md (2 docs)
      committed 2 path(s): 6839829f26298ca559f95c1effcc3ce85383973d
        COMMIT refactor(research): mv ee5555 and rewrite refs
       ...-renamed-other.notes.md => 20260101-beta-01-ee5555-v03-other.notes.md} | 0
      OK: no manifest in commit
    ```
    NOTE: the first two verbs needed a NINTH-site fix to reach this state. As authored, E-03 alone was
    NOT sufficient: `artifact_refs.plan_reference_rewrites` rewrote `INDEX.md` as a citing document and
    the caller appended it to `touched_paths`, so both verbs committed the manifest anyway. See
    DECISION 1-4r0qp1-D1 and the E-05 evidence below.
    Post-change `cli.py` aggregation sites, no `index_paths` contribution:
    ```
    cli.py:8560     if verb in ("group", "rename") and touched_all:
    cli.py:8565-8569        _offer_records_commit(args, repo_root, paths=touched_all, message=...)
    cli.py:11059    if mr.touched_paths:
    cli.py:11061-11064          _offer_records_commit(args, repo_root, paths=list(mr.touched_paths), ...)
    ```
    The FIELD itself is gone, so a caller cannot re-add the contribution by accident, and the
    docstring no longer documents the removed contract:
    ```
    $ python3 -c "from agent_workflows.plans_refs import MutationResult; print(MutationResult._fields)"
    ('rc', 'touched_paths')
    docstring now: "The commit path-set is ``touched_paths``, and that is the WHOLE of it. There is
    deliberately no ``index_paths`` companion: ..."
    $ grep -rn "_index_paths_for\b" agent_workflows/ --include=*.py
    (zero hits: all three producers deleted, including artifact_rename's DEAD one)
    ```
    `artifact_rename`'s contribution was confirmed DEAD before removal (F-8): `artifact_types.py:75-118`
    routes `plans`->`plans_refs.run_mv`/`run_set_assign` and `research`->`research_refs.*`, so the
    `artifact_type in {"plans","research"}` gate in `artifact_rename` is never true. The two
    unreachable regeneration blocks were LEFT in place per the plan's Deferred section, each now
    carrying a comment saying it is dead and why.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the full passing output of `python3 -m pytest tests/test_auto_index_on_mutation.py tests/test_selfcommit_adoption.py -o addopts="" -q`, plus a MUTATION CHECK on the INVERTED assertions: temporarily re-add a manifest path to one commit set, show `test_selfcommit_adoption` FAILS, then revert and show it passes. A test that cannot fail is not evidence. State the before/after counts (26 passed at review baseline for the two modules combined).
  - Observed evidence: 30 passed (26 baseline + 4 new guard tests); three independent mutations each made the inverted assertions FAIL, then were reverted.
    ```
    $ python3 -m pytest tests/test_auto_index_on_mutation.py tests/test_selfcommit_adoption.py -o addopts="" -q
    ..............................                                           [100%]
    30 passed in 2.79s
    ```
    COUNTS: baseline in THIS lane worktree was 26 for the two modules (6 + 20), matching the review
    baseline; now 30 (6 + 24). The +4 are the new `IgnoredPathsAreFilteredNotFatal` cases for E-06.
    The `test_auto_index_on_mutation.py` count is UNCHANGED at 6, which is the point: that module
    pins the REFRESH half and was correctly left alone (F-12 showed it has zero commit assertions).
    MUTATION CHECK, three independent mutations, each reverted afterwards:
    1. Re-added both manifests to `research_archive`'s returned `touched` list:
       ```
       FAILED tests/test_selfcommit_adoption.py::ArchiveCommitTests::test_commit_flag_commits_exactly_the_moved_doc_and_not_the_index
       E  - ['.agents/docs/research/INDEX.json', '.agents/docs/research/INDEX.md']
       E  + [] : generated manifests must not be committed; got [...INDEX.json, ...INDEX.md, ...notes.md]
       1 failed, 23 passed
       ```
    2. Re-added `.aw/records/plans/INDEX.json` to `plans_refs.run_set_assign`'s returned paths:
       ```
       FAILED tests/test_selfcommit_adoption.py::BackendReturnShapeTests::test_plans_backend_returns_touched_paths
       E  - ['.aw/records/plans/INDEX.json']
       E  + [] : generated manifests must not be in the commit path-set; got (...ipd.md, ...ipd.md, '.aw/records/plans/INDEX.json')
       1 failed, 23 passed
       ```
    3. Disabled E-06's filter (`ignored = []`):
       ```
       FAILED tests/test_selfcommit_adoption.py::IgnoredPathsAreFilteredNotFatal::test_an_all_ignored_set_is_nothing_to_commit_not_error
       FAILED tests/test_selfcommit_adoption.py::IgnoredPathsAreFilteredNotFatal::test_a_mixed_set_commits_the_real_path_and_skips_the_ignored_one
       2 failed, 2 passed
       ```
    All three reverted and re-verified clean (30 passed above; `grep -n MUTATION agent_workflows/*.py`
    shows only pre-existing unrelated prose). No test was deleted to make anything pass; both original
    commit assertions were INVERTED in place and each kept its "the real artifact IS committed" half.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste BOTH sweep directions. (a) every `INDEX*`/`index_paths` hit under `agent_workflows/` (excluding `__pycache__`) with its category; (b) every `offer_commit`/`_offer_records_commit`/`_offer_archive_commit`/`_offer_self_commit` call site with its path-set traced to origin. Both must show zero remaining commit-path contributors, or name the ninth.
  - Observed evidence: A NINTH SITE WAS FOUND AND FIXED. It is reported here rather than silently
    absorbed, per E-05's instruction; see DECISION 1-4r0qp1-D1 for the full rationale and the one
    scope caveat (the fix touches `agent_workflows/artifact_refs.py`, which `- Scope-Paths:` does not
    declare).
    NINTH SITE: `artifact_refs.plan_reference_rewrites` (`:121`) iterated `iter_scan_files`, which
    yields the generated `INDEX.md`, treated it as a CITING DOCUMENT and rewrote the old filename
    inside it; `plans_refs.apply_renames:367-369` then did `touched.append(_rel(e.file))` for every
    rewritten file, so the manifest entered the verb's COMMIT path-set. Measured live: the first E-08
    run committed `.aw/records/plans/INDEX.md` for BOTH `aw rename plans` and `aw group plans`. Fix:
    honor the module's OWN `_SKIP_NAMES` (`:54`, already `{README.md, INDEX.md, STATUS.md}`) when
    scanning, not only when collecting names. The rewrite was also pure dead work, since
    `plans_refs.py:371` regenerates the manifest from the renamed corpus immediately afterwards.
    DIRECTION (a), 75 hits under `agent_workflows/` (excluding `__pycache__`), by category:
      * WRITER / regeneration (kept, untouched): `plans_index.py` (18), `research_index.py` (18),
        `plans_archive.py:151,154`, `research_archive.py:268,271`, `research_cmd.py:499`.
      * PATH CONSTANT / name test (not a commit path): `runner_shared.py:299,308` (merge-conflict
        classifier `generated_manifest_paths`, currently no caller), `runner_shared.py:946`,
        `ipd_lint.py:1213,1246`, `artifact_refs.py:54`, `check_engine.py:380`, `selectors.py:46`,
        `record_history.py:341`, `review_findings.py:739`, `layout_migration.py:139`,
        `attention_contract.py:216`, `releases.py:560,603`, `research_archive.py:67`.
      * HELP TEXT / prose: `cli.py:198,2277,2291`, `selectors.py:12,24`.
      * SCOPE ALLOWANCE (not a commit path): `ipd_schema.py:477,487`
        (`SCOPE_PATHS_IMPLICIT_ALLOWANCES` lets a plan TOUCH the manifest without declaring it, which
        stays correct: the file is still written, just not committed).
      * CHANGES-REPORT entry (kept, by design, F-11): `status_set.py:936-937,971-972`.
      * EXPLANATORY COMMENT added by this plan: `ipd_lifecycle.py:2404`, `plans_refs.py:150`,
        `plans_archive.py:165`, `research_archive.py:274`, `status_set.py:1134`, `cli.py:8545,11057`.
      * COMMIT-PATH CONTRIBUTOR: **zero remaining.** Filtering the sweep for anything that feeds a
        commit path-set now matches only a comment:
        ```
        $ grep -rn "INDEX\.json\|INDEX\.md\|INDEX_JSON\|INDEX_MD\|index_paths" agent_workflows/ --include=*.py \
            | grep -v __pycache__ | grep -iE "touched|owned|paths=|commit"
        agent_workflows/research_archive.py:274:    # The regenerated INDEX.json/INDEX.md are deliberately NOT appended to `touched`: ...
        ```
    DIRECTION (b), every commit gateway traced BACKWARD to its path-set origin:
      * `plans_archive.py:236,276` -> `_offer_archive_commit(args, repo_root, touched)` -> `touched`
        from `apply_shard_moves` = moved files ONLY (E-07). CLEAN.
      * `research_archive.py:337,380` -> same shape, `touched` = moved files ONLY (E-07). CLEAN.
      * `status_set.py:1440,1479` -> `_offer_self_commit(...)` -> `paths = list(touched_paths)`, the
        rewritten artifacts ONLY (E-02). CLEAN.
      * `cli.py:8565` -> `_offer_records_commit(paths=touched_all)` <- `MutationResult.touched_paths`
        from `plans_refs`/`research_refs`/`artifact_rename`; the `index_paths` FIELD no longer exists
        (E-03), and `touched_paths` no longer picks up INDEX.md via the ref-rewriter (ninth-site fix).
        CLEAN.
      * `cli.py:11061` -> `_offer_records_commit(paths=list(mr.touched_paths))` (E-03). CLEAN.
      * `ipd_lifecycle.py` finalize: stages/commits `owned_paths` directly (not via the helper) =
        `[plan_rel, dest_rel]` (E-01). CLEAN.
      * `specs.py:697` -> `[str(path)]`, a single spec file. Never a manifest. CLEAN.
      * `work_cmd.py:470` -> operator-supplied `aw commit -- <paths>`; not a generated set. CLEAN.
      * `oc_runipd.py:1405` -> paths parsed from `git status --porcelain` and FILTERED to those whose
        FILENAME contains the item's id6 (`:1391-1396`), which a manifest never does. CLEAN.
      * `cli.py:4743` is `_offer_records_commit` itself (the shared wrapper), not an independent
        origin.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste a reproduction of F-7 BEFORE and AFTER. Before: a two-path `offer_commit` where one path is gitignored returning `status=error`, `staged=()`, no commit created. After: the same call committing the real path, reporting the skipped one by name, and creating a commit. Plus an all-ignored call returning `nothing-to-commit` rather than `error`, and a grep proving no `-f`/`--force` was introduced.
  - Observed evidence: same script run against the same scratch fixture, before and after the change.
    BEFORE (F-7 reproduced exactly as the review measured it):
    ```
    check-ignore sub/INDEX.json: .gitignore:1:sub/INDEX.json	sub/INDEX.json
    --- CASE A: mixed real + gitignored ---
    status='error' commit=None staged=()
    message: git add failed: The following paths are ignored by one of your .gitignore files: | sub/INDEX.json | hint: Use -f if you really want to add them. ...
    HEAD unchanged: True
    porcelain: ?? sub/                 <- sub/plan.md NEVER COMMITTED: the artifact's commit was lost
    --- CASE B: all paths gitignored ---
    status='error' commit=None staged=()
    ```
    AFTER:
    ```
    note: not committing gitignored path(s): sub/INDEX.json
    --- CASE A: mixed real + gitignored ---
    status='committed' commit='0e124dc541a7121f22c3e2da3d9ec8b4c12cfd55' staged=('sub/plan.md',)
    HEAD unchanged: False
    porcelain:                          <- clean: the real artifact IS committed
    --- CASE B: all paths gitignored ---
    status='nothing-to-commit' commit=None staged=()
    message: nothing to commit: every requested path is gitignored: sub/INDEX.json
    --- CASE C: TRACKED file that also matches an ignore pattern (must still commit) ---
    status='committed' staged=('sub/INDEX.json',)
    ```
    CASE C is the over-reach guard: git honors the index over `.gitignore` for a tracked file, and so
    does the filter, because `git check-ignore` was MEASURED to report ignored iff `git add` refuses
    (untracked+ignored -> rc 0 / add rc 1; tracked+matching -> rc 1 / add rc 0; tracked DELETION of a
    matching path -> rc 1 / add rc 0; nonexistent -> rc 1 / add rc 128, deliberately left in the set so
    git's own "pathspec did not match" still surfaces). See DECISION 1-4r0qp1-D3.
    No force-add introduced:
    ```
    $ grep -n '"-f"\|"--force"' agent_workflows/git_commit_helper.py
    no -f/--force anywhere in git_commit_helper.py
    ```
    A probe failure (`check-ignore` rc > 1) returns EMPTY, so a broken probe can never start dropping
    paths. `offer_commit`'s docstring/`Parameters`/`Returns` were updated to record the filtering, the
    stderr note, and the new all-ignored `nothing-to-commit` outcome (the doc-in-code sync the plan's
    "Spec / documentation sync" section requires). Pinned by four new tests, mutation-checked in V-04.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste an `aw archive plans --apply --commit` and an `aw archive research --apply --commit` exercise on scratch artifacts, each showing `git show --stat` with the moved files and NO INDEX path, and the manifests refreshed on disk. Plus `python3 -m pytest tests/test_plans_archive.py tests/test_research_archive.py -o addopts="" -q` passing.
  - Observed evidence: both run in the scratch repo with all four manifests REALLY gitignored.
    ```
    ############ aw archive plans --age 0d --apply --commit
      archived 20260101-v07-01-gg7777-seventh.ipd.md -> executed/202601/20260101-v07-01-gg7777-seventh.ipd.md
      committed 1 path(s): 76b4b53c7d07a72e55a6ccecb223ea5a6f063f7d
        COMMIT chore(plans): archive aged artifacts and regenerate index
       .../plans/executed/202601/20260101-v07-01-gg7777-seventh.ipd.md   | 8 ++++++++
      OK: no manifest in commit
      manifest on disk mentions the shard? 1        <- refresh half ran

    ############ aw archive research ee5555 --apply --commit
      archived ee5555 -> archive/202601/20260101-beta-01-ee5555-v03-other.notes.md
      committed 1 path(s): 849708709e089ce7f4fcbc41cc7096a1ad851b02
        COMMIT chore(research): archive aged artifacts and regenerate index
       .../202601/20260101-beta-01-ee5555-v03-other.notes.md      | 14 ++++++++++++++
      OK: no manifest in commit
      research manifest on disk mentions the archive path? 2      <- refresh half ran
    ```
    Note both commit messages still say "and regenerate index", which remains TRUE: the manifest is
    regenerated, it is simply not part of the commit.
    ```
    $ python3 -m pytest tests/test_plans_archive.py tests/test_research_archive.py -o addopts="" -q
    ........................                                                 [100%]
    24 passed in 0.57s
    ```
    The research appender had NO `exists()` guard (unlike its plans twin) and is now gone entirely, so
    the asymmetry the review flagged is resolved. `_offer_archive_commit`'s pre-commit
    `git reset --quiet HEAD -- *touched` needed no change (measured harmless for an untracked path);
    both `_offer_archive_commit` docstrings were corrected, since they claimed the INDEX is committed.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste, from the scratch clone/worktree with the four paths REALLY gitignored and `git rm --cached`ed, the successful commit evidence for each of `aw set`, `aw rename plans`, `aw group plans`, `aw archive plans`, `aw research mv`, and `aw ipd finalize`, each showing its artifact committed. Then paste `git check-ignore` and `git status --porcelain -- .aw/.gitignore` from THIS branch proving the experimental ignore was reverted and is not carried by the change.
  - Observed evidence: THIS IS THE CHECK THAT CAUGHT THE NINTH SITE (see V-05 / DECISION 1-4r0qp1-D1).
    A scratch repo (NOT this branch) was seeded with plans + research artifacts and their manifests
    TRACKED, then child 02's change was applied locally (`.aw/.gitignore` + root `.gitignore` +
    `git rm --cached` on all four), then every verb was run with `--commit`:
    ```
    ### after untracking, git check-ignore says:
        IGNORED  .aw/records/plans/INDEX.json
        IGNORED  .aw/records/plans/INDEX.md
        IGNORED  .agents/docs/research/INDEX.json
        IGNORED  .agents/docs/research/INDEX.md
    ### manifests still tracked (must be empty):
        (none)

    =========== 1. aw set                     committed 1 path(s): 5c21d69b...  OK: no manifest
    =========== 2. aw rename plans            committed 1 path(s): 67fa6c2d...  OK: no manifest
    =========== 3. aw group plans             committed 1 path(s): 0b259ddb...  OK: no manifest
    =========== 4. aw archive plans           committed 1 path(s): 0128f56a...  OK: no manifest
    =========== 5. aw research mv             committed 1 path(s): 28a9ec44...  OK: no manifest
    =========== 6. aw archive research        committed 1 path(s): f684803e...  OK: no manifest
    =========== 7. index --check still clean (byte-compare vs DISK)
        plans index --check: clean
        research index --check: clean
    ```
    Every verb exited 0 and committed its artifact; each `git show --stat` (full output in the
    execution report) contains the moved/rewritten artifact and NO INDEX path.
    `aw ipd finalize` is the sixth verb and is covered by V-01(b): it cannot be driven from a
    hand-built repo (it demands a begin receipt, pre-transition lint and a scope diff), so it was
    exercised through `ipd_lifecycle.begin` + `.finalize(apply=True)` in a fixture repo with the two
    plans manifests genuinely gitignored and `git rm --cached`ed: exit 0, plan moved to `executed/`,
    commit `de72bdf3` containing exactly the two plan paths, manifest mtime changed, `--check` clean.
    THE EXPERIMENT IS NOT CARRIED BY THIS BRANCH:
    ```
    $ git status --porcelain -- .aw/.gitignore
    (empty: untouched)
    $ git ls-files --error-unmatch .aw/records/plans/INDEX.json .aw/records/plans/INDEX.md
    .aw/records/plans/INDEX.json
    .aw/records/plans/INDEX.md          <- still TRACKED here; child 02 owns untracking
    $ git check-ignore -q .aw/records/plans/INDEX.json ; echo
    not-ignored .aw/records/plans/INDEX.json
    not-ignored .aw/records/plans/INDEX.md
    ```
    The scratch repos live under the gitignored `.aw/state/scratch-4r0qp1/`, so nothing leaked into the
    change set (`git status --porcelain` shows only the 13 intended files).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Size note: 8 E-leaves in 3 groups, within the count thresholds; grown from 5 by the review's re-sweep.
- Cohesion rationale: E-03 is the one item touching several files (`cli.py`, `plans_refs.py`, `research_refs.py`, `artifact_rename.py`) and it is deliberately NOT split, because those four are one data-flow path: the `MutationResult.index_paths` field, its three producers, and the two aggregation sites that commit it. Removing the producers while leaving the aggregation, or the reverse, leaves a half-wired contract whose docstring is false and whose behavior depends on which half landed, and no intermediate state is independently verifiable. Every other E-item is single-file and single-concern. E-06 is sequenced first on purpose: it is the only item that makes a MISS by any later item non-destructive.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, because pre-commit's stash/restore can leave a co-worker's paths in the index. When reporting tests passed, paste the ACTUAL runner output.

Post-gate lifecycle: this plan requires explicit human approval (`aw ipd set approved 4r0qp1 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: it is an output of `/plan-review` and writing one forges a review that did not happen (`IPD-M107`). On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence.
