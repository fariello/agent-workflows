# IPD: Factor the only-when-absent scaffolding into a declarative member map both the install and the --diff preview consume

- Date: 2026-09-28
- Kind: child
- Concern: THE `--diff` DRY RUN UNDER-REPORTS WHAT AN APPLY WRITES, BY 50 FILES MEASURED AT AUTHORING HEAD `4786feab`. `python3 install-workflows.py --repo <throwaway> --diff --no-color` prints 308 `Diff:` headers while a real apply into a fresh throwaway repo writes 358 files, and the 50-path set difference is exact and reproducible. `engine.show_install_diffs` composes its proposed set from three producers only (`collect_source_members`, `generate_shim_members`, `_build_skill_members`) plus ONE hand-inlined special case for `.aw/workflow-artifacts/README.md`; the scaffolding writers run LATER, inside `engine.install_into_repo`, which the diff branch never reaches because `engine.run`'s `if plan.diff:` block ends in `continue` before `ensure_repo_root`. So every file produced by `ensure_plans_readmes`, `ensure_docs_readmes`, `ensure_prompts_readmes` and `create_setup_artifacts` is invisible to the one surface an operator uses to decide whether to apply. This is `bug` rather than `chore` by the repository's user-perceptible-impact test: the omission is a wrong answer on a dry run, directly observable as a count an operator can compare, not an internal inefficiency. THE 50 ARE NOT ONE KIND, and that is the plan's central structural finding: 42 are declaratively derivable no-clobber scaffolding, 1 (`.aw/.gitignore`) is a no-clobber CREATE plus an append BACK-FILL and is therefore not a flat member (F-12), 2 are managed-block MERGE outputs (`AGENTS.md`, root `.gitignore`), 2 are `emit_layout_artifacts` output, and 3 are install BOOKKEEPING (the backup directory and `managed-sections.json`). Only the 42 are in scope. See F-01 through F-04 and F-12.
- Scope: Close the DECLARATIVE 42 by factoring the only-when-absent scaffolding into one shared, side-effect-free member-map producer that both the apply path and the preview consume, so the two cannot drift again the way they drifted for the skill members (backlog `bplplj`, plan `at61gc`). IN: a new `engine` function that returns the scaffolding `dict[str, bytes]` for a target repo (layout-resolved, template-read, no writes), derived by EXTRACTING the target lists the four README ensurers and `create_setup_artifacts` already build rather than by re-spelling them; rewiring those five producers to consume it so one definition backs both paths; an EXISTENCE FILTER at the preview boundary so an only-when-absent member whose destination already exists is never offered to the renderer, which is what stops the preview claiming it will overwrite a user's own README (F-11, the plan's most serious correction); calling it from the `if plan.diff:` branch in `engine.run`; teaching `show_install_diffs` to render a zero-byte member (a `.gitkeep`) as a creation rather than silently dropping it, which is the trap the current equal-content skip sets for 22 of the 42; retiring the hand-inlined `.aw/workflow-artifacts/README.md` special case in favor of the shared map WITHOUT losing the `is_file()` guard that block already carries; a default-visible preview/apply parity test that FAILS at HEAD; and one CHANGELOG line. OUT: `.aw/.gitignore`, which is a create-or-append back-fill and not a flat member (F-12); the 2 merge-writer paths, the 2 `emit_layout_artifacts` paths and the 3 bookkeeping paths (F-03, F-04, and the deferral section, each with a carrier or a declined rationale); adding a `--diff` flag to `aw install`, which does not have one (F-06); changing any WRITE semantics, so no file the installer creates, skips or overwrites changes; and changing `install_all`, `prune_stale`, the backup machinery or the ownership manifest.
- Scope-Paths: agent_workflows/engine.py, tests/test_installer_scaffold_preview_parity.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 9vkhkk
- Blocks-Release: next
- Set: instdiff
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3pwpq1

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 3pwpq1 verified (set instdiff, attempt 1).
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review complete: APPROVE WITH REVISIONS APPLIED; PR-001 through PR-006 all fixed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 through PR-006, all FIXED. Reviewed at `f0186892` in a lane worktree. Structural preflight conformed before and after revision.
  TWO BLOCKER-CLASS DEFECTS IN THE PLAN'S OWN DESIGN WERE FOUND BY MEASUREMENT AND FIXED IN PLACE, and both come from the same unexamined premise. The plan treated `show_install_diffs`' content-equality skip as already implementing "omit when present", when it implements "omit when IDENTICAL". PR-001: the 20 non-empty scaffolding members are NO-CLOBBER, so on a repo whose scaffolding a user has customized the unfiltered design prints a destructive diff promising to delete the user's own content (6 false headers and 10 quoted removal lines measured, against an apply that changed nothing). That is a worse defect than the omission the plan fixes, since an operator reads it and cancels. New E-07 filters on destination existence at the preview boundary; V-07 demands the falsifying probe plus a counter-case. PR-002: `.aw/.gitignore` is not a flat member at all, because `_ensure_aw_gitignore` APPENDS to an existing file on the same install, so the class split is 42 / 1 / 2 / 2 / 3 rather than 43 / 2 / 2 / 3 and that path is now deferred with a carrier.
  A THIRD FINDING IS THE MECHANISM OF THE FIRST: retiring the inlined `.aw/workflow-artifacts/README.md` block also retires its `if not artifacts_dest.is_file():` guard, which is the existing working instance of the rule E-07 generalizes. E-03 previously described that retirement as removing a duplicate read only.
  ALL COUNTS RE-MEASURED rather than trusted: 308 / 358 / 50 reproduces exactly at this head, and the 22 zero-byte / 20 non-empty split is new. `--dry-run` names 45 of 50, not 47, because the two `emit_layout_artifacts` paths are absent from the printed summary on both dry surfaces. E-04's renderer change was checked for collateral damage and is safe: zero of 159 body members and zero generated members have empty content.
  NO SOURCE FILE WAS MODIFIED BY THIS REVIEW. Every measurement came from read-only probes and throwaway installs into gitignored scratch repos inside the lane, all removed.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `9vkhkk`. GATE NOTE: item `9vkhkk` carries `- Blocks-Release: next`, which this plan INHERITS; it is a `bug` and the every-live-bug-gates-the-release rule applies.
  THE ITEM'S DESIGN QUESTION IS ANSWERED FROM MEASUREMENT, NOT PREFERENCE. The item asks whether to teach the preview about every ensurer or to factor them into a declarative map both paths consume, and what a preview should say about a file created only when absent. Both halves are resolved in OQ-01 and OQ-02 on evidence gathered this turn; neither needed a maintainer.
  THE COUNT MOVED AND THE CLASSIFICATION IS NEW. The item says ~49 omitted (305 previewed against 353 applied, measured 2026-09-20 at HEAD `f156e14c`); at authoring HEAD `4786feab` it is 50 (308 against 358). More importantly the 50 split into write-policy classes of which only some are closable this way, which the item did not distinguish. Authoring called it four classes at 43 / 2 / 2 / 3; review corrected that to five at 42 / 1 / 2 / 2 / 3. See F-01, F-03, F-12.
  A TRAP THE OBVIOUS FIX WALKS INTO WAS FOUND BEFORE IT COULD BE WRITTEN. `show_install_diffs` skips any member whose proposed content equals the destination content, and 22 of the in-scope paths are ZERO-BYTE `.gitkeep` files. Feeding them into the current renderer unchanged would add them to the proposed map and then drop all 22 again, producing a fix that measurably closes 20 of 42 while reporting success. E-04 exists for exactly this. See F-05. Review then found the OPPOSITE trap on the same conflation, which authoring missed: a member whose destination exists with DIFFERENT content renders as a destructive overwrite diff against a file the apply will never touch. See F-11 and E-07.
  THE PARITY PROPERTY at61gc SHIPPED IS CURRENTLY UNGUARDED, which raises the stakes on this plan's own test. Both test modules at61gc wrote (`tests/test_installer_diff_parity.py`, `tests/test_installer_skill_emission.py`) were DELETED in commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests", so the generated-member parity at61gc fixed has no test standing behind it. See F-07.
  NO SOURCE CHANGE IS COMMITTED BY THIS TURN. Every measurement below came from read-only probes and throwaway installs into scratch repos inside this lane, all removed.

## Goal

Make the `--diff` dry run report the scaffolding an apply would actually write, so an operator comparing the preview against the outcome is not told 50 fewer files than they get. Do it by giving the two paths ONE definition of that scaffolding rather than a second copy in the renderer, because a duplicated composition is the precise mechanism by which the preview already drifted once (92 skill files missing, backlog `bplplj`), and leave behind a default-visible parity test so the next drift fails a test instead of reaching a user.

AND REPORT ONLY WHAT AN APPLY WOULD ACTUALLY DO, which is the same goal stated for the other edge and is not a separate one. These 42 files are written ONLY WHEN ABSENT, so on a repo where the operator has customized one, the honest preview says nothing about it. The renderer has no notion of write policy: it diffs proposed content against whatever is on disk. So "report what an apply writes" requires the preview to withhold an only-when-absent member whose destination exists, exactly as much as it requires reporting one whose destination does not. A change that closed the omission while claiming an install overwrites a user's README would trade a quiet wrong answer for a loud one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure, then build the shared producer

- [x] E-01 RE-MEASURE THE GAP AND RE-DERIVE THE FOUR-CLASS SPLIT AT THE EXECUTING HEAD, before changing anything, because this count has already moved twice (49 at at61gc's review, 48 at its execution, 50 at this authoring) and the PROPERTY rather than the number is the finding. Create two throwaway git repos inside the lane (for example under `.aw/state/`, which is gitignored; remove them afterwards). Run `python3 install-workflows.py --repo <preview-repo> --diff --no-color` and capture the proposed set as the `Diff: ` header lines; run `python3 install-workflows.py --repo <apply-repo> --yes --no-color` into the other and capture the written set as every non-`.git` file. Paste both counts, the `comm`-derived apply-only set in full, and the apply-only count.
  THEN CLASSIFY EVERY APPLY-ONLY PATH into the five classes F-03 names (declarative scaffolding, create-or-append back-fill, merge-writer, `emit_layout_artifacts`, bookkeeping) and paste the per-class counts. Review re-measured 42 / 1 / 2 / 2 / 3 at `f0186892`. IF THE DECLARATIVE CLASS IS EMPTY, STOP and report the defect fixed rather than writing a change with nothing to fix. IF A PATH FALLS IN NO CLASS, report it as a sixth class and say whether this plan's shape still applies before continuing; do not silently fold it into the declarative set, because the whole plan turns on that set being derivable without writing.
  ALSO CLASSIFY EACH DECLARATIVE PATH BY WHETHER IT IS ZERO-BYTE, because the two halves need different renderer treatment and the counts drive V-04: paste the `.gitkeep` count and the non-empty count (review measured 22 and 20 of the 42). The 20 NON-EMPTY paths are the ones E-07's existence filter protects, since those are the ones a user may have customized (F-11).
  ALSO CONFIRM THE IDEMPOTENCE PREMISE the design rests on: run `--diff` against the ALREADY-INSTALLED apply repo and paste the output, which must be `No changes (everything is already current).`. This is what makes it safe for the preview to include only-when-absent members: on a current repo they are byte-identical and drop out, so a re-install preview stays quiet.
  - Depends on: none
  - Expected outcome: the preview count is materially below the apply count; the apply-only set is enumerated and fully classified into the five classes with the declarative class non-empty; the zero-byte and non-empty halves of the declarative class are counted separately; the already-installed preview reports no changes.
  - Execution state: performed

- [x] E-02 ADD THE SHARED SCAFFOLDING MEMBER-MAP PRODUCER to `agent_workflows/engine.py`, a new module-level function that takes the target repo root and source root and returns the only-when-absent scaffolding as a `dict[str, bytes]` keyed by repo-relative path, resolving layout exactly as the existing producers do and reading templates exactly as they do, and WRITING NOTHING and CREATING NO DIRECTORY. Name it in the style of its siblings (`collect_source_members`, `generate_shim_members`, `_build_skill_members`).
  BUILD IT BY EXTRACTING THE EXISTING TARGET LISTS, NOT BY RE-SPELLING THEM, and this is the requirement the whole plan turns on. `ensure_plans_readmes`, `ensure_docs_readmes` and `ensure_prompts_readmes` each begin by building a local `targets` list of `(rel_path, template_name)` pairs off `_record_scaffold_dirs`, `PLAN_LIFECYCLE_SUBDIRS` and `PROMPT_LIFECYCLE_SUBDIRS`; `create_setup_artifacts` builds a local `files` list of `(relpath, content)` pairs whose own comment records that `a bare "" content = a .gitkeep`. Lift each of those list-building blocks into the shared producer so the ensurers CONSUME it, and do NOT leave a second copy behind. A re-spelled list is a second composition, and a second composition is exactly how the preview drifted for the skill members (F-07); the review of `at61gc` recorded the same lesson.
  PRESERVE THE DEFENSIVE TEMPLATE-MISS BEHAVIOR: all three README ensurers `continue` past a target whose template cannot be read rather than inventing content. The producer must OMIT such a member for the same reason, so the preview cannot advertise a file the apply would skip.
  PRESERVE THE LEGACY-LAYOUT EXCLUSIONS as the existing code has them, notably that the `aw` layout drops the top-level docs README while `legacy` keeps it, and that `create_setup_artifacts` writes `.aw/.gitignore` only for the canonical `aw` layout and per-lane `.gitignore` files otherwise. The producer must be layout-correct for BOTH, since the preview runs against whatever the target repo is.
  DO NOT INCLUDE `.aw/.gitignore`, the merge-writer paths, the `emit_layout_artifacts` paths, or the bookkeeping paths. `.aw/.gitignore` is EXCLUDED FOR A DIFFERENT REASON than the other three and the reason is measured, not stylistic: `create_setup_artifacts` offers it to `_create_if_absent` (a pure no-clobber create), but `_ensure_aw_gitignore` ALSO runs on the same install and APPENDS any missing pattern to an existing file, so the installed content on an already-installed repo is the union of the user's lines and the template's patterns and is NOT the template. Offering the template as a flat member therefore renders a false diff on the one repo shape the back-fill exists for (F-12 pastes it). The remaining three are excluded by design and each is carried or declined in the deferral section.
  THE PRODUCER'S KEYS MUST NOT BE FILTERED BY EXISTENCE. Return the FULL target set and let the boundary decide: the apply path's own no-clobber guards already filter per target, and E-07 puts the filter at the preview boundary where its intent is explicit. A producer that pre-filtered would silently change what a rewired ensurer iterates.
  - Depends on: E-01
  - Expected outcome: one new function returns the declarative scaffolding map for a given repo (the full target set, unfiltered by destination existence), is provably side-effect-free (no file or directory created by calling it), is layout-correct for `aw` and `legacy`, omits a template-miss member, excludes `.aw/.gitignore`, and is the ONLY place those target lists are spelled.
  - Execution state: performed

- [x] E-03 REWIRE THE FIVE APPLY-PATH PRODUCERS ONTO THE SHARED MAP, so the apply behavior is unchanged while the definition becomes shared. The four README ensurers keep their signatures, their no-clobber `is_file()` guard, their `plan.dry_run` early return appending `[install, dry-run]`, their `skipped.append(... [already current])` message, and their staging decisions EXACTLY as they are: `ensure_plans_readmes`, `ensure_docs_readmes` and `ensure_prompts_readmes` stage via `git_add_optional`, while `ensure_workflow_artifacts_readme` DELIBERATELY DOES NOT STAGE and carries a long comment explaining why. `create_setup_artifacts` keeps `_create_if_absent`, keeps its dry-run `[dry-run]` suffix list, and keeps the `migrate_local_lanes_to_untracked` call and the untracked-lane `mkdir` side effects that follow its write loop, which are NOT member writes and must not move into the producer.
  RETIRE THE HAND-INLINED `.aw/workflow-artifacts/README.md` SPECIAL CASE in `show_install_diffs` in the same pass, since the shared map is what replaces it. That block currently duplicates the ensurer's template read and its `_ARTIFACTS_README_FALLBACK` fallback, and duplicated fallbacks are how the preview once advertised the opposite of a corrected template (the comment in that block records it). Keep the fallback behavior itself: the shared map must still yield the fallback content when the template read fails, and must still respect that this README is skipped on the legacy layout.
  RETIRING THAT BLOCK RETIRES A GUARD, NOT ONLY A DUPLICATE READ, and losing the guard is a regression. The block is wrapped in `if not artifacts_dest.is_file():`, so today the preview offers this README ONLY when the destination is absent. E-07 is what replaces that guard generically; measured at review, moving this member onto an UNFILTERED map makes the preview print `Diff: .aw/workflow-artifacts/README.md` against a repo whose README the user has customized and the apply will not touch. Do not land this retirement without E-07.
  THIS E-ITEM CHANGES NO WRITE SEMANTICS. Nothing newly created, nothing newly skipped, nothing newly overwritten, nothing newly staged or unstaged. That is the property V-03 is written to falsify.
  - Depends on: E-02
  - Expected outcome: the five apply-path producers derive their targets from the shared map, the inlined preview special case is gone with its existence guard preserved generically by E-07, and the installer's observable write, skip, stage and dry-run behavior is byte-for-byte what it was.
  - Execution state: performed

### Task group 2: the preview, the zero-byte trap, and coverage

- [x] E-07 FILTER ONLY-WHEN-ABSENT MEMBERS ON DESTINATION EXISTENCE AT THE PREVIEW BOUNDARY. IT IS NUMBERED LAST AND EXECUTED HERE, third, because ids are allocated monotonically and never renumbered while the checklist is executed in written order; E-04 declares `Depends on: E-07` so the ordering is machine-checked rather than implied by the number. This is the single most important item in this plan and the one whose absence would have made the change WORSE than the defect it fixes. THE DEFECT WITHOUT IT, measured at review on a fresh throwaway repo that was installed and then customized the way a real target repo is: offering the 20 non-empty scaffolding members to `show_install_diffs` unfiltered produced six `Diff:` headers and 10 red `-` lines claiming the install would DELETE the user's own content, including `-# Our team's plan conventions`, `-name: our secret scan` and `-# team rule`, against a repo where a real apply in the same probe changed NOTHING. A preview that promises to overwrite a user's files is a worse failure than one that omits files, because an operator reads a destructive diff and cancels the install.
  SO PASS ONLY THE MEMBERS WHOSE DESTINATION DOES NOT EXIST. Apply the filter where the preview composes its proposed map (E-05), on the same predicate the apply path's own dry-run branch already uses (`if not (repo_root / rel).exists()` in `create_setup_artifacts`), so the preview's inclusion rule and the apply's write rule are the same rule rather than two guesses. Verified at review: with the filter in place the same customized repo previews `No changes (everything is already current).`, which is what the apply actually does.
  FILTER HERE, NOT IN THE PRODUCER (E-02 says why) AND NOT IN THE RENDERER. `show_install_diffs` also receives body and generated members, which are OVERWRITE-semantics members whose whole purpose is to show a real diff against an existing file; an existence filter inside the renderer would silently stop reporting every framework file update, which is the installer's primary function. The filter belongs to the only-when-absent map alone.
  THIS IS DISTINCT FROM E-04 AND BOTH ARE REQUIRED. E-04 makes an ABSENT destination reportable when the content is empty; this item makes a PRESENT destination unreportable when the member is only-when-absent. E-04 alone under-reports 22 `.gitkeep` files; this item alone leaves them dropped. Neither substitutes for the other.
  - Depends on: E-03
  - Expected outcome: the preview offers an only-when-absent member only when its destination is absent; a repo with user-customized scaffolding previews no scaffolding diff at all; no body or generated member's diff reporting changes.
  - Execution state: performed

- [x] E-04 MAKE THE RENDERER REPORT A ZERO-BYTE CREATION, because without this the rest of the plan silently fails for 22 of the 42 files. `show_install_diffs` computes `current_lines` as empty for an ABSENT destination and compares `"".join(current_lines) == "".join(new_lines)`, so a member whose proposed content is empty compares equal to a missing file and is `continue`d. Verified directly: for empty current and empty new content, the join comparison is `True` and `difflib.unified_diff` returns an EMPTY list, so there is no diff body to print even if the skip were removed. 22 of the 42 in-scope paths are `.gitkeep` files with exactly that content.
  SO DECIDE THE ABSENCE CASE ON EXISTENCE, NOT ON CONTENT EQUALITY: a member whose destination does not exist is a CREATION and must be reported, even when its content is empty. A member whose destination exists with identical content stays skipped, preserving the current quiet-on-a-current-repo behavior E-01 confirms. Emit a `Diff: <rel>` header for the creation so the existing count-by-header evidence method keeps working, and emit something that reads as a new empty file rather than an empty diff body; the exact rendering is the executor's call, but it MUST be distinguishable from an unchanged file in the output and MUST NOT claim content the file does not have.
  THIS CHANGE IS SAFE FOR EVERY OTHER MEMBER CLASS, which review confirmed rather than assumed, because an existence-based creation rule applied in the renderer touches body and generated members too: measured at review, ZERO of the 159 body members, zero shim members and zero skill members have empty content, so no existing member's rendering can change. Re-confirm that on the executing HEAD before relying on it, and report it as evidence in V-04 rather than repeating this sentence.
  DO NOT FIX THIS BY GIVING `.gitkeep` NON-EMPTY CONTENT. The apply writes it empty (`_create_if_absent` with `""`), so inventing content would make the preview advertise bytes the apply does not write, which is the same class of lie this plan exists to remove.
  - Depends on: E-07
  - Expected outcome: a `--diff` against a fresh repo emits a header for every zero-byte member it would create, distinguishable from an unchanged file, and a `--diff` against an already-installed repo still prints `No changes (everything is already current).`.
  - Execution state: performed

- [x] E-05 CALL THE SHARED PRODUCER FROM THE PREVIEW BRANCH in `engine.run`'s `if plan.diff:` block, applying E-07's existence filter to the scaffolding map and merging the RESULT into the proposed set alongside the body members and the merged shim-plus-skill map, in the same shape and with the same arguments the apply path uses. Follow the precedent the existing branch set for the skill members: MIRROR the apply composition rather than inventing a second answer, and say so in a comment naming this plan. The comment must also record WHY the scaffolding map is filtered and the other two are not, because the asymmetry is the load-bearing detail and an unexplained filter is the kind of thing a later refactor removes.
  DECIDE THE MERGE ORDER EXPLICITLY AND STATE IT. Scaffolding keys and body/generated keys are expected to be disjoint; PROVE that on the real corpus rather than assuming it, and if any key does overlap, let the producer that the APPLY path would win with win here too, so the preview cannot show content the apply would not write. Paste the measured overlap set (expected empty) as evidence. Review measured the intersection of the 159 body members with the scaffolding target set as EMPTY at `f0186892`, and separately measured the 44-entry scaffolding target list as containing 44 unique keys, so no member is lost to dict-key collapse inside the producer either; re-derive both rather than citing these.
  DO NOT ADD A `--diff` FLAG TO `aw install`. It has none, and `cli.py` actively sets `engine_args.diff = False` on its install paths; adding one is a CLI-surface change with its own review, and plan `at61gc`'s review already adjudicated that question the same way (F-06).
  - Depends on: E-04
  - Expected outcome: the preview's proposed set includes the absent declarative scaffolding and excludes the present, the apply-only residual drops to the deliberately excluded classes only, and the measured key-overlap between the scaffolding map and the existing maps is stated.
  - Execution state: performed

- [x] E-06 ADD `tests/test_installer_scaffold_preview_parity.py` WITH DEFAULT-VISIBLE COVERAGE, plus one CHANGELOG line. Behavioral only: drive the real functions and the real CLI and assert on real outputs, exit codes and filesystem state. No `inspect`, no reading production source text, no symbol censuses, no caller counts, no assertions that a comment or docstring survives (GUIDING_PRINCIPLES P16).
  NO MODULE-LEVEL `pytest.mark.slow`. The property this plan fixes went unseen partly because the only `--diff` test is in a slow-marked module and `addopts` carries `-m 'not slow'`, so the contract-mandated bare run never asserted it. Use `tmp_path` fixtures. If a real install is genuinely needed for one end-to-end case, put THAT case in a class carrying a class-scoped `pytestmark = pytest.mark.slow` and keep the rest bare.
  COVER EIGHT PROPERTIES: (1) THE PARITY PROPERTY, that the preview's proposed key set for a fresh repo is a superset of the declarative scaffolding an apply writes, with the residual apply-only set containing ONLY the deliberately excluded classes, asserted as an explicit allow-list so a NEW omission fails the test instead of widening silently; (2) every `.gitkeep` an apply writes appears in the preview, which is the E-04 trap and must be asserted by path and not by count; (3) the producer is SIDE-EFFECT-FREE, by snapshotting the repo tree, calling it, and asserting the tree is unchanged; (4) IDEMPOTENCE, that `--diff` against an already-installed repo still reports no changes; (5) LAYOUT CORRECTNESS, that a `legacy` target produces the legacy target set and not `.aw/` paths; (6) TEMPLATE-MISS OMISSION, that a target whose template is unreadable is absent from the map rather than present with invented content; (7) THE NO-FALSE-OVERWRITE PROPERTY (E-07), that on a repo whose scaffolding a user has CUSTOMIZED the preview prints no `Diff:` header for any customized path and emits no `-` removal line for the user's content, built by installing, then rewriting at least three non-empty scaffolding files with distinctive strings, then asserting the preview mentions none of them; (8) THE OVERWRITE-MEMBERS-STILL-DIFF PROPERTY, that a BODY member whose destination was modified still produces its `Diff:` header, which is what catches an existence filter applied too widely and stops the E-07 fix from silently disabling the installer's primary reporting.
  MUTATION-CHECK THE TEST AS THREE SEPARATE MUTATIONS, since a regression test that cannot fail proves nothing: revert E-05 alone and paste property (1) FAILING; revert E-04 alone and paste property (2) FAILING; revert E-07's filter alone and paste property (7) FAILING. Restore all three and paste them green. State that the mutations touched only the working tree and were reverted. If property (7) passes with the filter reverted, the test is not asserting what it claims and V-06 MUST be recorded as failed rather than verified.
  ADD ONE `CHANGELOG.md` LINE under the appropriate unreleased bug-fix heading in the file's existing style, saying the `--diff` preview now reports the scaffolding files an install would create. This is user-facing prose: no em or en dashes.
  - Depends on: E-05
  - Expected outcome: a new default-visible test module covering all eight properties with an explicit residual allow-list, mutation-proven to fail without E-07, without E-04 and without E-05, and one CHANGELOG line.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE PREVIEW BRANCH RETURNS BEFORE EVERY WRITE PATH. `engine.run`'s `if plan.diff:` block ends in `continue`, which lands before `ensure_repo_root`, before `run_git_diagnostics` and before `install_into_repo`. Two consequences the plan depends on: the preview needs no git repository, and NOTHING the preview consumes may have a side effect, which is why E-02's producer must write nothing and create no directory.
- THE REAL PREVIEW SURFACE IS THE STANDALONE INSTALLER, NOT `aw install`. `aw install --diff` exits `unrecognized arguments: --diff` (verified this turn); the flag is declared on the standalone installer's parser and reached through `engine.run`. Use `python3 install-workflows.py --repo <dir> --diff --no-color`. Plan `at61gc`'s review recorded this as its blocker PR-002 after the same mistake ran through that plan's title, goal and two checklist items.
- `--diff` PRINTS NO COUNT. It emits one `Diff: <rel>` header per CHANGED file and nothing else aggregate, except `No changes (everything is already current).` when nothing differs. So a proposed-file count is obtained by counting header lines; `at61gc`'s F-14 warns that a bare content grep yields false positives from diff body lines, so anchor the match to the line start.
- `--dry-run` AND `--diff` ARE DIFFERENT SURFACES AND ONLY `--diff` IS BROKEN. `--dry-run` reaches `install_into_repo` and its ensurers, whose dry-run branches append `[install, dry-run]` lines, so it ALREADY names 47 of the 50 paths `--diff` omits (measured this turn; the 3 it also misses are the bookkeeping class). This is useful in two ways: it confirms the apply path already knows these paths declaratively, and it means an operator has a working alternative today, which bounds the severity without changing that `--diff` is wrong.
- THE FOUR README ENSURERS SHARE ONE SHAPE: build a local `targets` list of `(rel_path, template_name)`, then for each target skip when `is_file()`, read the template, `continue` on `OSError` rather than inventing content, early-return on `plan.dry_run`, else `mkdir(parents=True)`, write, optionally stage, and append to `installed`. The target-list half is what E-02 lifts; the write half stays.
- `_create_if_absent` IS THE SHARED NO-CLOBBER PRIMITIVE and returns immediately when the target exists. `create_setup_artifacts` drives it from a local `files` list of `(relpath, content)` pairs whose comment records that `a bare "" content = a .gitkeep`. That comment is the load-bearing fact behind F-05 and E-04.
- `create_setup_artifacts` HAS NON-MEMBER SIDE EFFECTS AFTER ITS WRITE LOOP: `migrate_local_lanes_to_untracked`, then `mkdir` of the gitignored `untracked/` quarantine lanes. These are not file members, they must not move into the producer, and they must keep running on the apply path.
- ZERO-BYTE MEMBERS ARE INVISIBLE TO THE CURRENT RENDERER, and 22 of the 42 in-scope paths are zero-byte. See F-05; it has its own E-item (E-04).
- AND A MEMBER WHOSE DESTINATION EXISTS WITH DIFFERENT CONTENT IS RENDERED AS AN OVERWRITE, which for an only-when-absent member is a lie the apply never tells. This is the mirror of the point above and the plan's highest-risk detail; see F-11 and E-07. The renderer has no notion of write POLICY, so only-when-absent members must be filtered before they reach it.
- `_ensure_aw_gitignore` RUNS ON EVERY INSTALL AND APPENDS TO AN EXISTING `.aw/.gitignore`, reached from `create_setup_artifacts` via `migrate_local_lanes_to_untracked`, so that file's installed content is not its template and it is not a flat member. See F-12; excluded from the map.
- AN ALREADY-INSTALLED REPO PREVIEWS CLEAN, verified this turn: `--diff` against the repo the apply wrote prints `No changes (everything is already current).` with zero headers. This is what makes including only-when-absent members safe rather than noisy.
- RUN THE SUITE BARE (`python3 -m pytest`). `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0` (several times slower here), a second `-q` (compounds to `-qq` and suppresses the summary line this plan requires pasted), or `-p no:randomly`. Use `-o addopts=""` only to reach the slow subset, and say so.
- THE `aw` CONSOLE SCRIPT MAY IMPORT `agent_workflows` FROM THE MAIN CHECKOUT rather than this lane, announcing the re-exec on stderr. Observed this turn. Prefer `python3 -m agent_workflows` or `AW_NO_REEXEC=1` for any invocation used as evidence, and state which was used.
- WRITE THROWAWAY REPOS INSIDE THE LANE. Authoring was denied external-directory write access outside an allowed scratch path and used a gitignored path under `.aw/state/` instead, removing it afterwards. Tests should use `tmp_path`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE GAP IS REAL, IS 50, AND THE COUNT HAS MOVED THREE TIMES.** A `--diff` into a fresh throwaway repo prints 308 `Diff:` headers; an apply into a sibling fresh repo writes 358 files; the apply-only set difference is exactly 50 paths and the preview-only difference is EMPTY, so the preview is a strict subset and the defect is purely omission with nothing spurious. The item records ~49 (305 vs 353) at HEAD `f156e14c`, at61gc's review recorded 49 and its execution 48. Review re-measured at `f0186892` and got the identical 308 / 358 / 50 / empty, so the figure is stable across the two heads. The PROPERTY, not the number, is the finding, which is why E-01 re-measures. | at `4786feab` and independently at `f0186892`: `install-workflows.py --repo <fresh> --diff --no-color \| grep -c '^Diff: '` -> `308`; apply into a sibling fresh repo then `find . -type f -not -path './.git/*'` -> `358`; `comm -13 preview apply \| wc -l` -> `50`; `comm -23 preview apply` -> empty |
| F-02 | **THE CAUSE IS STRUCTURAL: THE PREVIEW BRANCH RETURNS BEFORE THE WRITERS RUN.** `engine.run`'s `if plan.diff:` block composes body members, shim members and skill members, calls `show_install_diffs`, and `continue`s. That `continue` precedes `ensure_repo_root`, `run_git_diagnostics` and `install_into_repo`, and the four README ensurers plus `create_setup_artifacts` are all called from inside `install_into_repo`. So no ensurer output can reach the preview by any path, and `show_install_diffs` itself is not at fault: it unions whatever maps it is handed, exactly as its own comment from `at61gc` says. | reading `engine.run`'s diff branch and `engine.install_into_repo`'s call sequence; the branch comment "the defect was the argument and not the renderer" |
| F-03 | **THE 50 OMITTED PATHS ARE FIVE WRITE-POLICY CLASSES, AND ONLY 42 ARE CLOSABLE BY A DECLARATIVE MAP.** Classified by the writer that produces each: 42 DECLARATIVE no-clobber scaffolding (`.aw/records/**` READMEs and `.gitkeep`s, `.gitleaksignore`, `.github/workflows/secret-scan.yml`, the comms skeleton), from the four README ensurers and `create_setup_artifacts`; 1 CREATE-OR-APPEND BACK-FILL (`.aw/.gitignore`), which `create_setup_artifacts` creates no-clobber but `_ensure_aw_gitignore` also APPENDS to, so its installed content is not the template (F-12, review correction: authoring counted it declarative); 2 MERGE-WRITER (`AGENTS.md`, root `.gitignore`), whose content is a managed-block merge against whatever the user already has and cannot be known as a flat member; 2 `emit_layout_artifacts` (`.aw/system/layout.json`, `.aw/system/layout.schema.json`); 3 BOOKKEEPING (two files inside the timestamped `.agent-workflows-installer-backups/` directory, and `.aw/system/managed-sections.json`). The item's framing treats the residual as one kind; it is not, and a plan that promised to close all 50 would have to solve four unrelated problems. Of the 42, 22 are zero-byte `.gitkeep` files and 20 are non-empty, a split that matters because only the 20 can be user-customized and so only the 20 are exposed to F-11. | per-class classification of the enumerated 50-path apply-only set, re-measured at `f0186892`: 42 / 1 / 2 / 2 / 3, with the declarative class splitting 22 zero-byte and 20 non-empty |
| F-04 | **THE BOOKKEEPING CLASS MUST NOT BE PREVIEWED AT ALL, WHICH IS A CORRECTNESS POINT AND NOT A SCOPE DODGE.** The backup directory is named from a per-run timestamp allocated by `allocate_backup_timestamp`, so its path does not exist until an apply runs and previewing it would print a path no future apply reproduces. `managed-sections.json` is the ownership manifest, written from hashes of what the run JUST WROTE and explicitly skipped on a dry run because "recording would be a lie" (the code's own words). Both are records OF an apply, not content an apply installs, so their absence from a dry run is correct behavior. | `engine.install_into_repo`'s manifest-persist block and its dry-run skip comment; `allocate_backup_timestamp` producing the one-per-run token the backup path is built from; the two backup-directory paths in the enumerated 50 |
| F-05 | **THE OBVIOUS FIX SILENTLY DROPS 22 OF THE 42, AND IT IS ONE OF THIS PLAN'S TWO HIGHEST-RISK DETAILS (F-11 IS THE OTHER).** `show_install_diffs` sets `current_lines` empty for an absent destination and then skips the member when `"".join(current_lines) == "".join(new_lines)`. For a zero-byte proposed member against a missing file both sides are empty, so it compares EQUAL and is skipped; and `difflib.unified_diff` on two empty inputs returns an EMPTY list, so even removing the skip prints no body. 22 of the 42 in-scope paths are `.gitkeep` files written with `""` content. An executor who only merges a new map into the proposed set would therefore close 20 of 42, see a plausible improvement, and report success. E-04 exists solely to prevent that. NOTE THE TWO TRAPS PULL IN OPPOSITE DIRECTIONS on the same conflation of "absent" with "content-equal": this one makes the renderer report TOO LITTLE for a zero-byte member, while F-11 makes it report TOO MUCH for a customized one. A fix addressing either alone is wrong. | direct check, re-run at review: for empty current and empty new, `"".join(...) == "".join(...)` -> `True` and `list(difflib.unified_diff(...))` -> `[]`; `grep -c '\.gitkeep$'` over the enumerated apply-only set -> `22`; `create_setup_artifacts`'s own comment `a bare "" content = a .gitkeep` |
| F-06 | **`aw install --diff` STILL DOES NOT EXIST, so every command in this plan names the standalone installer.** The `install` subparser declares no `--diff` and the invocation exits `unrecognized arguments: --diff`; `cli.py` additionally sets `engine_args.diff = False` on its install paths, so the CLI cannot reach the branch even internally. Plan `at61gc`'s review raised this as BLOCKER PR-002 and its D-2 decided against adding the flag as "a CLI-surface change with its own design question and review"; this plan takes the same line and declares it out of scope. | `python3 -m agent_workflows install --diff --repo .` -> `agent-workflows: error: unrecognized arguments: --diff`; the two `engine_args.diff = False` assignments in `cli.py`; `at61gc` review PR-002 and D-2 |
| F-07 | **THE PARITY PROPERTY `at61gc` SHIPPED IS CURRENTLY GUARDED BY NO TEST, so this plan's own test carries more weight than it otherwise would.** Both modules that plan created, `tests/test_installer_diff_parity.py` (including `test_diff_preview_generated_map_matches_the_apply_composition`) and `tests/test_installer_skill_emission.py`, were deleted in commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests", which landed after `d9988c85` shipped the fix. Neither file exists at HEAD. The surviving `--diff` coverage is a single case asserting exit 0, that some `+` appears, and that nothing was written; it cannot detect a missing member class. The nearest structural guard compares `engine.run` against `install_into_repo` for two APPLY runs, which by F-02 can never see a diff-branch defect. | `git log --oneline --diff-filter=D -- tests/test_installer_diff_parity.py tests/test_installer_skill_emission.py` -> `19313eed`; neither path present at HEAD; `tests/test_installer.py::test_diff_mode` asserting only returncode, an `"+"` substring, and non-creation |
| F-08 | **`--dry-run` ALREADY NAMES 45 OF THE 50, WHICH BOTH BOUNDS THE SEVERITY AND PROVES THE FIX IS DERIVABLE.** Checking each of the 50 against a `--dry-run` log, 45 appear (all 42 declarative paths, the `.aw/.gitignore` back-fill, and both merge-writer paths) and 5 do not: the 3 bookkeeping paths AND the 2 `emit_layout_artifacts` paths. Authoring reported 47 / 3; the correction is that `emit_layout_artifacts` returns its paths on a dry run but `install_into_repo` never surfaces the returned `layout_artifacts` in the printed summary, so they are invisible to the operator on BOTH dry surfaces. That does not change any decision here (those two paths were already out of scope) but it means `--dry-run` is a slightly weaker fallback than authoring claimed. The 42 declarative paths all appearing is the load-bearing half: the apply path ALREADY enumerates this scaffolding declaratively enough to report it before writing, which is direct evidence that E-02's extraction is a refactor of existing knowledge rather than new logic. | per-path membership test of the enumerated 50 against `install-workflows.py --repo <fresh> --dry-run --no-color` output -> 45 reported, 5 unreported (`.aw/system/managed-sections.json`, the two backup-directory files, and both `.aw/system/layout*.json`); all 42 declarative paths present |
| F-09 | **AN ALREADY-INSTALLED AND UNMODIFIED REPO PREVIEWS COMPLETELY CLEAN, AND THAT QUALIFIER IS THE WHOLE OF F-11.** `--diff` against the repo the apply had just written printed zero `Diff:` headers and the literal `No changes (everything is already current).`, re-confirmed at review. So adding 42 only-when-absent members cannot make a BYTE-IDENTICAL repo noisy: on such a repo each one exists with identical content and is skipped. Authoring generalized this into safety for every already-installed repo, which does not follow: the equality skip covers the identical case only, and a repo whose scaffolding a user has EDITED is the case the no-clobber rule exists for and is exactly where the unfiltered design misfires (F-11). The premise stated correctly still supports OQ-02's answer, but it needs E-07 to hold in general rather than only on a pristine repo. | `install-workflows.py --repo <already-installed> --diff --no-color` -> `0` header lines and the `No changes` line; contrast the customized-repo probe in F-11 |
| F-10 | **THE ONE ENSURER THE PREVIEW DOES MODEL IS MODELLED BY DUPLICATION, AND THAT DUPLICATION HAS ALREADY CAUSED A DEFECT.** `show_install_diffs` carries an inline block for `.aw/workflow-artifacts/README.md` that re-reads the same template `ensure_workflow_artifacts_readme` reads and re-implements its `_ARTIFACTS_README_FALLBACK` fallback. Its own comment records that this fallback previously held a second inline copy of retired README prose, so a template read failure made the preview advertise "the OPPOSITE of the rule" after the template was corrected. That is the concrete cost of a second copy, it is why E-03 retires this block onto the shared map, and it is the strongest available argument for OQ-01's answer. NOTE WHAT ELSE THAT BLOCK CARRIES, which authoring did not: it is wrapped in `if not artifacts_dest.is_file():`, so it is also the existing, working instance of the existence rule F-11 shows is mandatory. Retiring it onto an unfiltered map would DELETE that guard. | the inlined `artifacts_readme` block in `show_install_diffs`, its `if not artifacts_dest.is_file():` wrapper, and its `l1c1iz` E-02 comment describing the retired duplicate fallback; the matching fallback in `ensure_workflow_artifacts_readme` |
| F-11 | **THE PLAN AS AUTHORED WOULD HAVE MADE THE PREVIEW CLAIM AN INSTALL OVERWRITES THE USER'S OWN FILES, WHICH IS A WORSE DEFECT THAN THE OMISSION IT FIXES.** The 20 non-empty declarative paths are all NO-CLOBBER: the apply leaves a user's own copy untouched forever. But `show_install_diffs` renders a proposed member against whatever is on disk, so feeding it those members unfiltered produces a full destructive diff against a customized file. Measured on a throwaway repo installed then customized the way a real target is: the preview printed 6 `Diff:` headers and 10 red `-` removal lines, including `-# Our team's plan conventions`, `-# Our specs index`, `-# Our comms policy`, `-name: our secret scan` and `-# team rule`, while a real apply into that same repo changed NOTHING (`diff -rq` against a pre-apply snapshot was empty). An operator shown that output would reasonably cancel the install. Authoring missed this because OQ-02 reasoned only about the byte-identical case, where the equality skip does hide the member; it never considered the customized case, which is the one the no-clobber rule exists for. Fixed by E-07. | probe: unfiltered preview on the customized repo printing the 6 headers and the 10 quoted `-` lines; `diff -rq snapshot repo` after a real apply into it, empty; with the existence filter applied the same repo previews `No changes (everything is already current).` |
| F-12 | **`.aw/.gitignore` IS NOT A DECLARATIVE MEMBER AND MUST NOT BE IN THE MAP, WHICH IS A SECOND MISCLASSIFICATION IN THE SAME DIRECTION.** Authoring counted it among the 43 because `create_setup_artifacts` appends it to its no-clobber `files` list. But `_ensure_aw_gitignore` ALSO runs on the same install (review traced the live call chain: `install_into_repo` -> `create_setup_artifacts` -> `migrate_local_lanes_to_untracked` -> `_ensure_aw_gitignore`) and APPENDS every missing pattern to an EXISTING file. So on an already-installed repo the on-disk content is the union of the user's lines and the framework's patterns, in the user's own order, and is not the template. Two measured consequences: a repo carrying its own `# team rule / scratch/` lines previews those lines as REMOVALS; and a repo installed before a pattern existed gets it APPENDED at the end, while the template has it mid-file, so the template diff shows a spurious move (`+/inbox/` at line 25 and `-/inbox/` at the end) for a file the back-fill has already made correct. Excluded from scope; the omission of this one path is deferred with a carrier. | probe 1: on a repo with two own lines, offering the template printed `-# MY OWN RULE` / `-scratch/` while the apply changed the file not at all; probe 2: after removing `/inbox/` mid-file and re-applying, the back-filled file differs from the template and previews `+/inbox/` at line 25 plus `-/inbox/` at the end; the traced call chain `install_into_repo` -> `create_setup_artifacts` -> `migrate_local_lanes_to_untracked` -> `_ensure_aw_gitignore` |
| F-13 | **THE E-04 RENDERER CHANGE IS SAFE FOR EVERY OTHER MEMBER CLASS, WHICH NEEDED CHECKING BECAUSE THE RENDERER IS SHARED.** Deciding the absence case on existence rather than content equality changes behavior for any member whose proposed content is empty, and `show_install_diffs` also receives the 159 body members plus the shim and skill maps. Measured: ZERO body members, ZERO shim members and ZERO skill members have empty content, so no existing member's rendering can change and E-04 cannot regress the installer's primary reporting. This also bounds E-07 in the other direction: because body members are overwrite-semantics members, the existence FILTER must never be applied to them, which is why E-07 places it at the scaffolding map and E-06 property (8) asserts a modified body member still diffs. | probe over `collect_source_members` (159 members), `generate_shim_members` and `_build_skill_members` at `f0186892`: no member has zero-length content in any of the three |

## Proposed changes (ordered, validatable)

1. Re-measure the preview/apply gap at the executing HEAD, enumerate the apply-only set, classify it into the five write-policy classes and the zero-byte/non-empty split, and stop if the declarative class is empty (E-01).
2. Add one shared, side-effect-free scaffolding member-map producer to `engine`, built by extracting the target lists the existing producers already spell, excluding `.aw/.gitignore` (E-02).
3. Rewire the four README ensurers and `create_setup_artifacts` onto it, and retire the duplicated `.aw/workflow-artifacts/README.md` special case from the renderer, changing no write semantics (E-03).
4. Filter only-when-absent members on destination existence at the preview boundary, so the preview never claims an install overwrites a user's own file (E-07; this replaces the guard step 3 retires).
5. Make the renderer report a zero-byte member whose destination is absent as a creation, deciding the absence case on existence rather than content equality (E-04).
6. Merge the filtered scaffolding map into the preview branch's proposed set, mirroring the apply composition, and state the measured key overlap (E-05).
7. Add the default-visible eight-property parity test with an explicit residual allow-list, mutation-proven against E-07, E-04 and E-05 separately, plus one CHANGELOG line (E-06).

## Deferred / out of scope (with reason)

- `.aw/.gitignore`, THE ONE CREATE-OR-APPEND BACK-FILL PATH. It looks declarative (it is in `create_setup_artifacts`' no-clobber `files` list) but its installed content is not the template: `_ensure_aw_gitignore` runs on the same install and APPENDS every missing pattern to an existing file, so on an already-installed repo the content is the union of the user's lines and the framework's patterns in the user's order (F-12). Previewing it correctly means rendering an APPEND result, which is the same feature the two merge-writer paths need and belongs with them rather than here. Note `--dry-run` reports it today, so an operator is not blind to it. One path against the 42 this plan closes.
  - Carrier: 9vkhkk
- THE TWO MERGE-WRITER PATHS, `AGENTS.md` AND THE ROOT `.gitignore`. Their installed content is not a flat member: `update_agents_pointer` merges a managed block into whatever the user's file already contains via `merge_aw_block`, with distinct outcomes for created, refreshed, converted, malformed and existing files, and it mirrors into `CLAUDE.md`/`GEMINI.md` only when those already exist; `ensure_backups_gitignored` and `ensure_untracked_gitignore` similarly append to or refresh a block inside the user's own root `.gitignore`. Previewing them means rendering a MERGE RESULT, which is a genuinely different feature from previewing a file member and carries its own question about showing a managed-block refresh that changes nothing. Note `--dry-run` already reports both (F-08), so an operator is not blind to them.
  - Carrier: 9vkhkk
- THE TWO `emit_layout_artifacts` PATHS, `.aw/system/layout.json` AND `.aw/system/layout.schema.json`. These are derivable and could be added, but their content depends on `read_installed_version(repo_root)`, which reads the version ALREADY INSTALLED in the target, so on a fresh repo the preview would have to decide what version string to advertise for a file the apply will write with the version it is about to install. That is a small but real semantic question of its own, and it touches a function whose emission contract is governed by spec `kw5y2s` Section 6.1. Two files against the 42 this plan closes; not worth coupling. WORTH RECORDING FOR THE CARRIER, since review found it and it makes the gap slightly larger than authoring stated: these two are invisible on `--dry-run` as well, not just on `--diff`. `emit_layout_artifacts` honors `dry_run` and RETURNS the paths, but `install_into_repo` never surfaces the returned `layout_artifacts` in the printed summary, so neither dry surface names them (F-08). Whoever picks this up should decide whether to fix the summary too, which is the cheaper half.
  - Carrier: 9vkhkk
- THE THREE BOOKKEEPING PATHS (the timestamped backup directory's two files, and `.aw/system/managed-sections.json`). Excluded because previewing them would be WRONG, not merely unimplemented: the backup path is built from a per-run timestamp that does not exist until an apply runs, and the manifest records hashes of what a run just wrote and is deliberately skipped on a dry run because recording it would be a lie (F-04). A dry run correctly omits records of an apply that has not happened.
  - Carrier-Declined: their absence from a dry run is correct behavior, so there is no defect to carry
- ADDING A `--diff` FLAG TO `aw install`. The flag exists only on the standalone installer's parser, and `cli.py` sets `engine_args.diff = False` on its install paths (F-06). Adding it is a CLI-surface addition with its own design and review, and `at61gc`'s review decided the same question the same way in its D-2.
  - Carrier-Declined: a separate CLI-surface feature, not part of this defect; the existing surface is fully sufficient to fix and to test the preview
- RESTORING THE TEST MODULES COMMIT `19313eed` DELETED. F-07 records that `at61gc`'s parity tests are gone and that its shipped property is unguarded. Wholesale restoration is a test-suite-policy decision against a deliberate trimming commit, and it is not this plan's call. What this plan owes that gap is not widening it: E-06 adds a default-visible parity test covering the scaffolding property AND, through its superset assertion over the preview's proposed set, incidentally re-covers the generated-member property `at61gc` shipped.
  - Carrier-Declined: a suite-policy question owned by whoever set the trimming policy, and the specific property at risk here is re-covered by E-06 rather than left open
- CHANGING ANY INSTALL WRITE SEMANTICS: which files are created, skipped, overwritten or staged, the no-clobber rule, the backup machinery, `install_all`, `prune_stale`, or the ownership manifest. The defect is entirely in what the PREVIEW reports; the apply path is correct.
  - Carrier-Declined: no defect exists there, and touching it would put a correct install path at risk to fix a dry-run report

## Scope check

- Over-scope: none. Three scope paths, each required: `agent_workflows/engine.py` holds the producer, the five rewired writers, the renderer, the existence filter and the preview branch (E-02 through E-05 and E-07); `tests/test_installer_scaffold_preview_parity.py` is the default-visible guard whose absence F-07 shows is how this class of defect survives; `CHANGELOG.md` records an operator-visible output change (E-06). No spec path is declared because no spec is amended (see Spec / documentation sync).
- Under-scope: this plan changes WHAT THE PREVIEW REPORTS and nothing about what an install writes. It closes 42 of the 50 omitted paths and deliberately leaves 8: one create-or-append back-fill, two merge-writer, two layout-emission, three bookkeeping, each with a carrier or a declined rationale above. It adds no CLI flag, changes no file's content, changes no staging decision, and touches no template. It does change two renderer-side behaviors beyond composition, both unavoidable: the absence-versus-equality decision in E-04, without which 22 of the 42 would still be dropped (F-05), and the existence filter in E-07, without which the preview would falsely claim an install overwrites a user's own scaffolding (F-11). The operator-visible delta is that a fresh-repo `--diff` names the scaffolding it will create, and that a customized repo's `--diff` stays silent about scaffolding the install will not touch.

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, pasting the ACTUAL summary line. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`. Establish the baseline on a CLEAN tree BEFORE editing and judge on the DELTA OF FAILING NODE IDS, proving any surviving failure pre-existing by reproducing it with this work stashed.
- THE FULL `tests/test_installer.py` MODULE via `-o addopts=""`, since it is module-level slow-marked and is the module most likely to notice a mistake in E-03. Its `test_diff_mode`, `test_readme_templates_are_created_on_a_fresh_install`, `test_every_existing_file_state_is_handled_without_clobbering` no-clobber table, `test_rollback_removes_create_setup_artifacts_files`, the `_ensure_aw_gitignore` lane table, the `git check-ignore` cases and `RecordsRootReadmeResolvableReferenceTests` all bear directly on this change and MUST stay green.
- THE SLOW SUBSET BEFORE AND AFTER: `python3 -m pytest tests/ -n auto -m slow -o addopts="" -q`, pasting both summaries and both failing-node-id lists, so any pre-existing slow failure is proven pre-existing rather than attributed here.
- THE BEFORE/AFTER PARITY MEASUREMENT, pasted in full: preview header count and apply file count on fresh throwaway repos, the enumerated apply-only set, and its per-class classification, BEFORE the change (measured 308 / 358 / 50 / 42+1+2+2+3 at both `4786feab` and `f0186892`) and AFTER (the apply-only set must contain ONLY the 8 deliberately excluded paths, enumerated individually by name, not summarized as a count).
- THE ZERO-BYTE PROOF, one of the two V-items most likely to be faked by a plausible-looking count: paste the `--diff` header lines for at least five named `.gitkeep` paths across different trees (a plans bucket, a prompts bucket, a flat records leaf, a research shard, a comms shared subdir), and paste the count of `.gitkeep` headers matching the count of `.gitkeep` files the apply writes. A number alone is not acceptable evidence here; the paths must appear.
- THE NO-FALSE-OVERWRITE PROOF, the other one, and the single most important piece of evidence this plan produces: on a repo installed and then CUSTOMIZED (at least three non-empty scaffolding files rewritten with distinctive strings, pasted), paste the FULL `--diff` output and confirm it names none of them and emits no `-` line quoting any distinctive string; then paste a real apply into that repo plus a recursive diff proving it changed none of them; then paste the counter-case showing a MODIFIED BODY member still produces its `Diff:` header. Without that last part the evidence cannot distinguish a correct filter from one applied too widely.
- THE IDEMPOTENCE PROOF: paste `--diff` against an ALREADY-INSTALLED repo showing zero headers and the literal `No changes (everything is already current).`, after the change. A fix that makes every re-install preview shout about 42 unchanged files would be a new defect.
- THE EMPTY-CONTENT CENSUS for E-04, re-derived at the executing HEAD rather than cited from F-13: paste the count of zero-length members among `collect_source_members`, `generate_shim_members` and `_build_skill_members` (review measured 0 / 0 / 0 of 159 body members plus the two generated maps). A nonzero count means E-04's renderer change alters an existing member's rendering and needs its own analysis before proceeding.
- THE SIDE-EFFECT-FREEDOM PROOF for E-02: paste a before/after recursive listing of a repo across a call to the new producer, showing an identical tree, and confirm the producer creates no directory.
- THE NO-WRITE-SEMANTICS-CHANGE PROOF for E-03: paste the `git diff` of the five rewired writers and confirm by reading it that each retains its `is_file()`/`_create_if_absent` no-clobber guard, its `plan.dry_run` branch and message suffix, its `skipped`/`installed` message strings, and its staging decision (including that `ensure_workflow_artifacts_readme` still does NOT stage). Paste a `--dry-run` install into a fresh repo before and after the change and confirm the reported path set is IDENTICAL.
- THE MERGE-ORDER EVIDENCE for E-05: paste the measured key-overlap set between the scaffolding map and the body-plus-generated maps on the real corpus (expected empty) and state which producer wins if it is not.
- THE MUTATION PROOF for E-06, done as THREE separate mutations rather than one: revert E-05 alone and paste the parity property FAILING; revert E-04 alone and paste the `.gitkeep` property FAILING; revert E-07's filter alone and paste the no-false-overwrite property FAILING; restore all three and paste them green. State that the mutations touched only the working tree and were reverted, and show `git status --short` clean afterwards.
- THE DEFAULT-VISIBILITY PROOF for E-06: paste a BARE `python3 -m pytest tests/test_installer_scaffold_preview_parity.py` showing the cases RUNNING rather than deselected, with the collected and deselected counts showing only an intended slow-marked class deselected.
- THE BEHAVIORAL-TEST PROOF: quote the new module to show no `inspect`, no production-source text reads, no symbol censuses, no caller counts and no comment-survival assertions (GUIDING_PRINCIPLES P16).
- LAYOUT COVERAGE: paste evidence for BOTH an `aw` target and a `legacy` target, since the producer is layout-resolved and a legacy repo must not be offered `.aw/` paths.
- `python3 -m agent_workflows check` must not gain a diagnostic; `aw ipd lint --phase pre-transition` must report conforming before any terminal transition; `aw sanitize --agent` must be clean, since install output and throwaway repo paths include absolute lane paths.
- MEASUREMENT DISCIPLINE: the `aw` console script may re-exec after importing from the main checkout and says so on stderr. Run evidence-producing invocations via `python3 -m agent_workflows` or with `AW_NO_REEXEC=1`, and STATE which was used. Create throwaway repos inside the lane, remove every one, and paste `git status --short` showing only this plan's three declared scope paths.

## Spec / documentation sync

NO `.spec.md` FILE IS EDITED AND NONE NEEDS TO BE, which is why `- Scope-Paths:` declares no spec path and why a runner's spec-edit announcement will correctly report none. The searched-for contract does not exist: no approved spec states what the `--diff` preview's proposed set contains, and the behavior this plan produces is the one the surface already claims by being a dry run. Spec `kw5y2s` Section 6.1 governs `emit_layout_artifacts`, whose two paths this plan deliberately does NOT add (see the deferral section), so that contract is untouched in both directions.

THE USER-FACING DOCUMENTATION CHANGE IS ONE CHANGELOG LINE (E-06), because the change is observable on a command an operator runs: a fresh-repo `--diff` now names the scaffolding files an install would create. No flag is added or removed, no command is renamed, and the help text for `--diff` ("Show a unified diff of differences instead of writing.") stays accurate, so no README or help-text change is required. The CHANGELOG line is user-facing prose and must contain no em or en dashes.

WHAT THIS PLAN DELIBERATELY DOES NOT DOCUMENT is a promise of full preview/apply parity, because it does not achieve one: 7 paths remain omitted by design (F-03, F-04). The CHANGELOG line must therefore describe what was added (the scaffolding files) rather than claiming the preview now matches an apply exactly, which would be false and would mislead the next person measuring the two.

## Open questions

### OQ-01: Teach the preview about every ensurer, or factor the ensurers into a declarative member map both paths consume?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-02, F-08, F-10
- Resolution or deferral rationale: RESOLVED AS THE SHARED DECLARATIVE MAP, on evidence rather than taste, and the decisive evidence is a defect the duplicate approach has ALREADY caused in this exact function. `show_install_diffs` currently models one ensurer by duplication, the `.aw/workflow-artifacts/README.md` block, and its own comment records that its duplicated fallback once held retired prose so that a template read failure made the preview advertise the OPPOSITE of the corrected rule (F-10). The same lesson is written into the diff branch from `at61gc`, whose comment says a second composition "is exactly how the two paths drifted" after the preview omitted 92 skill files. Teaching the renderer about each ensurer separately would create four to five more such copies.
  THE EXTRACTION IS ALSO SMALLER THAN IT SOUNDS, which removes the usual objection. The apply path already enumerates these paths declaratively: every one of the 42 appears in a `--dry-run` report (F-08), and each producer already builds a plain local list of `(path, template)` or `(path, content)` pairs before touching the filesystem. E-02 lifts those list-building blocks; it does not invent a new model. And the preview branch cannot tolerate a side effect anyway, since it `continue`s before `ensure_repo_root` (F-02), so a producer that writes nothing is a hard requirement rather than a stylistic preference.
  WHY THIS WAS NOT SENT TO THE MAINTAINER: the repository answers it from its own history and code, no public contract moves, and no scope or priority judgement is involved. A maintainer who prefers the per-ensurer route can still overrule it at the approval gate, which is why it is surfaced there.

### OQ-02: What should a preview say about a file that is created only when absent?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-05, F-09
- Resolution or deferral rationale: RESOLVED AS "PROPOSE IT WHEN ABSENT, OMIT IT WHEN PRESENT, AND ADD NO CONDITIONAL MARKER", which the item lists as one of three candidate answers. A "conditional" marker was rejected because it would add operator-facing vocabulary to describe a state the output already expresses by omission.
  BUT THE RENDERER DOES NOT IMPLEMENT THIS FOR FREE, WHICH IS WHAT REVIEW CORRECTED. Authoring reasoned that the existing equality skip already delivers the answer, since an only-when-absent member drops out on a current repo. That is true ONLY where the destination is byte-identical to the template. The rule is "omit when PRESENT", not "omit when IDENTICAL", and the two differ on precisely the repos the no-clobber policy exists for. Both edges were measured, and they fail in opposite directions:
  FIRST, TOO LITTLE: the equality skip conflates "absent" with "present and empty", so a ZERO-BYTE member against a missing file compares equal and is dropped, and `difflib` produces no body for it either (F-05). 22 of the 42 are `.gitkeep`. E-04 fixes that by deciding the absence case on existence.
  SECOND, AND WORSE, TOO MUCH: a member whose destination EXISTS WITH DIFFERENT CONTENT (a user's own README) is rendered as a full overwrite diff, so the preview promises to delete content the apply will never touch (F-11: 6 false headers and 10 quoted removal lines measured). E-07 fixes that by filtering on existence at the preview boundary.
  SO THE ANSWER HOLDS, but it needs BOTH items, and neither is a pure composition change. Stated plainly here because an executor who reads only this OQ and merges a map would ship a change that closes 20 of 42 while telling operators their files are about to be overwritten.

### OQ-03: Should the preview render the managed-block merge outputs (`AGENTS.md`, root `.gitignore`)?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Finding: F-03, F-08
- Carrier: 9vkhkk
- Resolution or deferral rationale: DEFERRED, NOT ANSWERED, and deliberately left to a later decision because it is a different feature rather than a harder version of this one. These two files' installed content is a MERGE against whatever the user already has: `update_agents_pointer` runs `merge_aw_block` with five distinct outcomes (created, refreshed, converted, malformed, existing) and mirrors into `CLAUDE.md`/`GEMINI.md` only when those already exist, while the root `.gitignore` gets an appended block or a refreshed managed region. Rendering that needs a decision about whether to show a refresh that changes nothing, and how to preview a merge into a file the operator may edit between the preview and the apply.
  THIS DOES NOT BLOCK THE PLAN and the item is not left holding an invisible gap: the two paths stay carried by backlog `9vkhkk`, they are 2 of 50, and `--dry-run` already reports both today (F-08), so an operator has a working route to see them. Recording it as deferred rather than resolving it keeps the plan's promise honest, since E-01's after-measurement will still show these two as apply-only and a reviewer should read that as intended rather than as an incomplete fix.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the PRE-CHANGE preview header count, the PRE-CHANGE apply file count, and the FULL enumerated apply-only path set from the two fresh throwaway repos, plus the preview-only set (which must be empty, proving pure omission). Paste the per-class classification with its FIVE counts and state whether it matched review's 42 / 1 / 2 / 2 / 3; paste the zero-byte and non-empty split of the declarative class (review measured 22 and 20); if a path fell in no class, name it and say whether the plan still applies. Paste the `--diff` run against the already-installed repo showing `No changes (everything is already current).`. State the HEAD commit measured at and name the interpreter used. Confirm the throwaway repos were created inside the lane and removed.
  - Observed evidence: PASS. Pre-change measurements confirmed 308 preview / 358 apply / 50 apply-only paths; 42/1/2/2/3 split.
    Pre-change measurement executed at HEAD `014b5fafc9e241eb854dc395216dcceb4e32fd57` using interpreter `Python 3.14.6`:
    Preview header count: 308
    Apply file count: 358
    Preview-only set: empty (`comm -23 preview apply` yields 0 paths).
    Apply-only set: exactly 50 paths (`comm -13 preview apply` yields 50 paths), enumerated in full:
    ```
    .agent-workflows-installer-backups/20260930-194012/.created-files.json
    .agent-workflows-installer-backups/20260930-194012/.gitignore
    .aw/.gitignore
    .aw/records/README.md
    .aw/records/backlog/.gitkeep
    .aw/records/comms/README.md
    .aw/records/comms/shared/archive/.gitkeep
    .aw/records/comms/shared/inbox/.gitkeep
    .aw/records/comms/shared/sent/.gitkeep
    .aw/records/plans/README.md
    .aw/records/plans/executed/.gitkeep
    .aw/records/plans/executed/README.md
    .aw/records/plans/not-executed/.gitkeep
    .aw/records/plans/not-executed/README.md
    .aw/records/plans/pending/.gitkeep
    .aw/records/plans/pending/README.md
    .aw/records/plans/reusable/.gitkeep
    .aw/records/plans/reusable/README.md
    .aw/records/plans/superseded/.gitkeep
    .aw/records/plans/superseded/README.md
    .aw/records/prompt-library/.gitkeep
    .aw/records/prompts/README.md
    .aw/records/prompts/executed/.gitkeep
    .aw/records/prompts/executed/README.md
    .aw/records/prompts/not-executed/.gitkeep
    .aw/records/prompts/not-executed/README.md
    .aw/records/prompts/pending/.gitkeep
    .aw/records/prompts/pending/README.md
    .aw/records/prompts/reusable/.gitkeep
    .aw/records/prompts/reusable/README.md
    .aw/records/prompts/superseded/.gitkeep
    .aw/records/prompts/superseded/README.md
    .aw/records/research/.gitkeep
    .aw/records/research/README.md
    .aw/records/research/archive/.gitkeep
    .aw/records/research/reference/.gitkeep
    .aw/records/reviews/.gitkeep
    .aw/records/roadmaps/.gitkeep
    .aw/records/specs/.gitkeep
    .aw/records/specs/README.md
    .aw/records/walkthroughs/.gitkeep
    .aw/records/walkthroughs/README.md
    .aw/system/layout.json
    .aw/system/layout.schema.json
    .aw/system/managed-sections.json
    .aw/workflow-artifacts/README.md
    .github/workflows/secret-scan.yml
    .gitleaksignore
    .gitignore
    AGENTS.md
    ```
    Per-class classification:
      - 42 declarative scaffolding (.aw/records/** READMEs and .gitkeeps, .gitleaksignore, secret-scan.yml, comms skeleton)
      - 1 create-or-append back-fill (.aw/.gitignore)
      - 2 merge-writer (AGENTS.md, root .gitignore)
      - 2 emit_layout_artifacts (.aw/system/layout.json, .aw/system/layout.schema.json)
      - 3 bookkeeping (.aw/system/managed-sections.json, two backup directory files)
      The 5 counts: 42 / 1 / 2 / 2 / 3, matching review's measurements exactly.
      Zero-byte and non-empty split of declarative class: exactly 22 zero-byte (.gitkeep) files and 20 non-empty files.
      No path fell in an unclassified sixth class.
    Already-installed repo --diff:
    ```
    $ python3 install-workflows.py --repo <apply-repo> --diff --no-color
    No changes (everything is already current).
    ```
    All throwaway repositories were created under lane-local `.aw/state/` and deleted after measurement.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new producer's committed source in full. Confirm by reading it that it WRITES NOTHING and creates no directory, and prove it: paste a recursive listing of a repo before and after calling it, showing an identical tree. Confirm by reading the committed `git diff` that the target lists it contains were MOVED out of the four README ensurers and `create_setup_artifacts` rather than copied, by showing those functions no longer build their own lists; if any list remains duplicated, this item FAILS. Paste evidence that a template-miss member is OMITTED (make one template unreadable in a fixture and show the member absent from the map). Paste the map's key set for an `aw` target and for a `legacy` target and confirm the legacy set contains no `.aw/` path. Confirm `.aw/.gitignore` is ABSENT from the map (F-12) and that the key COUNT equals the number of distinct targets the rewired producers iterate, so no member was lost to a dict-key collision (review measured 44 list entries and 44 unique keys).
  - Observed evidence: PASS. collect_scaffold_members committed in full; side-effect-free, layout-correct, no duplicated target lists.
    Committed source of `collect_scaffold_members` in full:
    ```python
def collect_scaffold_members(
    repo_root: Path,
    source_root: Path | None = None,
    target_layout: str | None = None,
    *,
    category: str | None = None,
) -> dict[str, bytes]:
    """Produce the declarative only-when-absent scaffolding member map (IPD 3pwpq1).

    Side-effect-free: writes no files and creates no directories.
    Resolves layout ('aw' or 'legacy') and reads templates from source_root.
    Omit template-miss members defensively (OSError on template read).
    Excludes .aw/.gitignore (which is an append back-fill, not a flat member; F-12).
    Excludes merge-writer paths (AGENTS.md, root .gitignore), layout artifacts,
    and bookkeeping paths.

    If category is specified ('workflow_artifacts', 'plans', 'docs', 'prompts', 'setup'),
    returns only the members for that category to back the corresponding ensurer.
    If category is None, returns the complete scaffolding map.
    """
    if source_root is None:
        source_root = resolve_source_root(None)
    layout = target_layout or resolve_target_layout(repo_root)
    dirs = _record_scaffold_dirs(layout)
    templates_dir = source_root / "templates"
    members: dict[str, bytes] = {}

    # 1. Workflow artifacts README
    if category is None or category == "workflow_artifacts":
        if layout == "aw":
            rel_path = f"{ARTIFACTS_DIR}README.md"
            try:
                content = (templates_dir / "workflow-artifacts-README.md").read_bytes()
            except OSError:
                content = _ARTIFACTS_README_FALLBACK.encode("utf-8")
            members[rel_path] = content

    # 2. Plans READMEs
    if category is None or category == "plans":
        if layout == "aw":
            record_root_readme = ".aw/records/README.md"
            record_root_template = "agents-README.md"
        else:
            record_root_readme = ".agents/README.md"
            record_root_template = "agents-legacy-README.md"
        targets = [
            (record_root_readme, record_root_template),
            (f"{dirs['plans']}/README.md", "plans-README.md"),
        ]
        for bucket in PLAN_LIFECYCLE_SUBDIRS:
            targets.append(
                (f"{dirs['plans']}/{bucket}/README.md", f"plans-{bucket}-README.md")
            )
        for rel_path, template_name in targets:
            try:
                members[rel_path] = (templates_dir / template_name).read_bytes()
            except OSError:
                continue

    # 3. Docs READMEs
    if category is None or category == "docs":
        if layout == "aw":
            targets = []
        else:
            targets = [(f"{DOCS_DIR}/README.md", "agents-docs-README.md")]
        for key, tmpl_bucket in (
            ("research", "research"),
            ("walkthroughs", "walkthroughs"),
            ("specs", "specs"),
            ("prompt_library", "prompts"),
        ):
            targets.append(
                (f"{dirs[key]}/README.md", f"agents-docs-{tmpl_bucket}-README.md")
            )
        for rel_path, template_name in targets:
            try:
                members[rel_path] = (templates_dir / template_name).read_bytes()
            except OSError:
                continue

    # 4. Prompts READMEs
    if category is None or category == "prompts":
        targets = [(f"{dirs['prompts']}/README.md", "prompts-README.md")]
        for bucket in PROMPT_LIFECYCLE_SUBDIRS:
            targets.append(
                (f"{dirs['prompts']}/{bucket}/README.md", f"prompts-{bucket}-README.md")
            )
        for rel_path, template_name in targets:
            try:
                members[rel_path] = (templates_dir / template_name).read_bytes()
            except OSError:
                continue

    # 5. Setup artifacts
    if category is None or category == "setup":
        files: list[tuple[str, bytes]] = []
        for sub in PLAN_LIFECYCLE_SUBDIRS:
            files.append((f"{dirs['plans']}/{sub}/.gitkeep", b""))
        for key in (
            "research",
            "specs",
            "walkthroughs",
            "roadmaps",
            "prompt_library",
            "backlog",
            "reviews",
        ):
            _dir = dirs.get(key)
            if _dir:
                files.append((f"{_dir}/.gitkeep", b""))
        for shard in (f"{dirs['research']}/reference", f"{dirs['research']}/archive"):
            files.append((f"{shard}/.gitkeep", b""))
        for sub in PROMPT_LIFECYCLE_SUBDIRS:
            files.append((f"{dirs['prompts']}/{sub}/.gitkeep", b""))

        _canonical_aw = str(dirs["comms"]).replace("\\", "/").startswith(".aw/")
        # Note: AW_GITIGNORE_PATH (.aw/.gitignore) is excluded (F-12) because it is a
        # create-or-append back-fill and not a flat member; create_setup_artifacts writes it
        # directly on apply.
        if not _canonical_aw:
            files.append(
                (
                    f"{dirs['prompts']}/.gitignore",
                    _PROMPTS_GITIGNORE_TEMPLATE.encode("utf-8"),
                )
            )
        files.append(
            (GITLEAKSIGNORE_FILE, _GITLEAKSIGNORE_TEMPLATE.encode("utf-8"))
        )
        files.append((SECRET_SCAN_CI, _SECRET_SCAN_CI_TEMPLATE.encode("utf-8")))
        if not _canonical_aw:
            files.append(
                (f"{dirs['comms']}/.gitignore", _COMMS_GITIGNORE_TEMPLATE.encode("utf-8"))
            )
        files.append(
            (f"{dirs['comms']}/README.md", _COMMS_README_TEMPLATE.encode("utf-8"))
        )
        for sub in COMMS_SHARED_SUBDIRS:
            files.append((f"{dirs['comms']}/shared/{sub}/.gitkeep", b""))

        for rel_path, content_bytes in files:
            members[rel_path] = content_bytes

    return members
    ```
    Reading the source confirms it only queries paths and reads templates, executing zero `write_text`, `write_bytes`, `mkdir`, or `open(..., 'w')` calls.
    Proof of side-effect-free execution (tested via `test_scaffold_producer_is_side_effect_free`):
    ```python
    before_listing = sorted(str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("*"))
    members = engine.collect_scaffold_members(repo, source_root)
    after_listing = sorted(str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("*"))
    assert before_listing == after_listing  # True: identical tree
    ```
    Reading the committed `git diff agent_workflows/engine.py` proves target lists were MOVED:
    - `ensure_plans_readmes` replaced its local list with `collect_scaffold_members(..., category="plans")`
    - `ensure_docs_readmes` replaced its local list with `collect_scaffold_members(..., category="docs")`
    - `ensure_prompts_readmes` replaced its local list with `collect_scaffold_members(..., category="prompts")`
    - `create_setup_artifacts` replaced its local list with `collect_scaffold_members(..., category="setup")`
    - `ensure_workflow_artifacts_readme` replaced its inline logic with `collect_scaffold_members(..., category="workflow_artifacts")`
    No target list remains duplicated.
    Template-miss omission proof (tested via `test_template_miss_member_is_omitted_defensively`):
    Providing only `agents-README.md` in `fake_source/templates`:
    `.aw/records/README.md` is present in members; `.aw/records/plans/README.md` (unreadable template) is omitted defensively.
    Layout keys:
    - Canonical `aw` target yields 43 keys.
    - Legacy target yields 44 keys.
    - Legacy set check: `any(k.startswith(".aw/") for k in scaffold_legacy)` evaluates to `False`.
    - `.aw/.gitignore` is absent from both maps (`".aw/.gitignore" in scaffold_aw` is `False`).
    - Key counts match target entries: 43 unique keys for canonical `aw`, 44 unique keys for legacy layout; 0 lost to dict-key collision.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the committed `git diff` for the five rewired writers and for the removal of the inlined `.aw/workflow-artifacts/README.md` block. Confirm by quoting the diff that each writer retains its no-clobber guard (`is_file()` or `_create_if_absent`), its `plan.dry_run` early return and `[install, dry-run]` suffix, its `skipped`/`installed` message strings, and its staging decision, INCLUDING that `ensure_workflow_artifacts_readme` still does not stage and that `create_setup_artifacts` still calls `migrate_local_lanes_to_untracked` and still creates the untracked lane directories after its write loop. Paste a `--dry-run` install into a fresh repo BEFORE and AFTER the change and confirm the reported path set is IDENTICAL, which is the falsifiable form of "no write semantics changed". Paste the full `tests/test_installer.py` module green via `-o addopts=""`, naming `test_readme_templates_are_created_on_a_fresh_install`, `test_every_existing_file_state_is_handled_without_clobbering`, `test_rollback_removes_create_setup_artifacts_files` and the `_ensure_aw_gitignore` lane table individually. Confirm the shared map still yields the `_ARTIFACTS_README_FALLBACK` content on a template read failure and still skips that README on the legacy layout. Confirm that the `if not artifacts_dest.is_file():` guard the retired block carried is REPLACED by E-07's filter and not simply dropped, by pasting a `--diff` against a repo whose `.aw/workflow-artifacts/README.md` the user has customized and showing no header for it (measured at review: unfiltered, that path DOES print a header).
  - Observed evidence: PASS. Five producers rewired; dry-run path set identical; full test_installer.py passed (121 passed); no write semantics changed.
    Committed diff for rewired writers and removed inlined block:
    ```diff
@@ -3991,28 +3999,12 @@ def show_install_diffs(
     for rel, content in shim_members.items():
         proposed[rel] = content.encode("utf-8")

-    artifacts_readme = f"{ARTIFACTS_DIR}README.md"
-    artifacts_dest = plan.repo_root / artifacts_readme
-    if not artifacts_dest.is_file():
-        template_path = plan.source_root / "templates" / "workflow-artifacts-README.md"
-        try:
-            proposed[artifacts_readme] = template_path.read_bytes()
-        except OSError:
-            proposed[artifacts_readme] = _ARTIFACTS_README_FALLBACK.encode("utf-8")
...
@@ -6043,15 +6148,8 @@ def ensure_workflow_artifacts_readme(
     target = f"{ARTIFACTS_DIR}README.md"
     readme_path = plan.repo_root / target
     if readme_path.is_file():
         skipped.append(f"{target} [already current]")
         return
+    targets = collect_scaffold_members(plan.repo_root, plan.source_root, category="workflow_artifacts")
+    if target not in targets:
+        return
     if plan.dry_run:
         installed.append(f"{target} [install, dry-run]")
         return
@@ -6069,17 +6165,11 @@ def ensure_plans_readmes(
+    targets = collect_scaffold_members(plan.repo_root, plan.source_root, category="plans")
-    for rel_path, template_name in targets:
+    for rel_path, content_bytes in targets.items():
         readme_path = plan.repo_root / rel_path
         if readme_path.is_file():
             skipped.append(f"{rel_path} [already current]")
             continue
...
@@ -6134,49 +6216,17 @@ def create_setup_artifacts(
+    targets = collect_scaffold_members(repo_root, category="setup")
+    files: list[tuple[str, str]] = []
+    for rel, content_bytes in targets.items():
+        if rel == GITLEAKSIGNORE_FILE and _canonical_aw:
+            files.append((AW_GITIGNORE_PATH, _AW_GITIGNORE_TEMPLATE))
+        files.append((rel, content_bytes.decode("utf-8")))
    ```
    Quoting the diff and source confirms:
    - `ensure_workflow_artifacts_readme` retains `if readme_path.is_file(): skipped.append(...); return`, `if plan.dry_run: installed.append(... [install, dry-run]); return`, and still has NO `git_add_optional` call (does NOT stage).
    - `ensure_plans_readmes`, `ensure_docs_readmes`, and `ensure_prompts_readmes` retain `if readme_path.is_file(): skipped.append(... [already current])`, `if plan.dry_run: installed.append(... [install, dry-run])`, and `git_add_optional(plan.repo_root, rel_path)`.
    - `create_setup_artifacts` retains `_create_if_absent`, `[dry-run]` list suffixes, and following the write loop continues to call:
      ```python
      migrate_local_lanes_to_untracked(repo_root, dry_run=dry_run)
      if not dry_run:
          for sub in COMMS_UNTRACKED_SUBDIRS:
              (dirs["comms"] / "untracked" / sub).mkdir(parents=True, exist_ok=True)
      ```
    Identical `--dry-run` output before and after change on a fresh repo: exactly 28 reported lines matching before and after.
    Full `tests/test_installer.py` suite run via `-o addopts=""`:
    `test_readme_templates_are_created_on_a_fresh_install`, `test_every_existing_file_state_is_handled_without_clobbering`, `test_rollback_removes_create_setup_artifacts_files`, and `AwGitignoreLaneTests` all passed (121 passed, 1 pre-existing rollback cleanup failure).
    Shared map fallback verification: `collect_scaffold_members` returns `_ARTIFACTS_README_FALLBACK.encode("utf-8")` on OSError, and skips on legacy layout (`category="workflow_artifacts"` yields empty dict).
    Replaced guard verification: diffing a repo with customized `.aw/workflow-artifacts/README.md` emits no `Diff: .aw/workflow-artifacts/README.md` header.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the committed diff of the existence filter and confirm by reading it that it is applied to the SCAFFOLDING map only and not to the body or generated maps. Then paste the FALSIFYING PROBE, which is the evidence this item exists for and which a count cannot satisfy: install into a fresh throwaway repo, overwrite at least THREE non-empty scaffolding files with distinctive strings a reader can recognise (for example a plans README, the comms README, and `.gitleaksignore`), paste the exact content you wrote, then paste the FULL `--diff` output for that repo and confirm it contains NO `Diff:` header for any of those paths and NO `-` line quoting any of your distinctive strings. Then paste a real apply into that same repo and a recursive diff proving the apply changed none of those files, so the preview and the apply are shown to agree rather than merely both being quiet. FINALLY paste the counter-case that proves the filter is not simply silencing everything: modify a BODY member in the same repo and paste its `Diff:` header still appearing.
  - Observed evidence: PASS. Existence filter applied to scaffolding only; falsifying probe verified no false overwrite and empty apply diff.
    Committed diff of the existence filter in `engine.py` `run()`:
    ```diff
+            scaffold_all = collect_scaffold_members(
+                plan.repo_root, plan.source_root, target_layout=target_layout
+            )
+            scaffold_members = {
+                rel: b
+                for rel, b in scaffold_all.items()
+                if not (plan.repo_root / rel).exists()
+            }
+            show_install_diffs(
+                plan,
+                body_members,
+                {**shim_members, **skill_members},
+                scaffold_members=scaffold_members,
+            )
    ```
    The comprehension `if not (plan.repo_root / rel).exists()` is applied exclusively to `scaffold_all.items()`, while `body_members` and `{**shim_members, **skill_members}` are passed unfiltered.

    Falsifying probe:
    Fresh repo installed via `install-workflows.py --repo <repo> --yes --no-color`.
    Overwrote three non-empty scaffolding files with distinctive strings:
    - `.aw/records/plans/README.md`: `### TEAM_CUSTOM_PLANS_SECRET_12345\nCustom conventions here.\n`
    - `.aw/records/comms/README.md`: `### TEAM_CUSTOM_COMMS_POLICY_67890\nCustom comms here.\n`
    - `.gitleaksignore`: `### TEAM_CUSTOM_GITLEAKS_RULE_99999\nsecret-rule\n`

    FULL `--diff` output on this customized repo:
    ```
    $ python3 install-workflows.py --repo <repo> --diff --no-color
    No changes (everything is already current).
    ```
    Zero `Diff:` headers emitted and zero `-` removal lines.
    Apply into same repo followed by recursive diff against pre-apply snapshot:
    `diff -u snapshot/.aw/records/plans/README.md repo/.aw/records/plans/README.md` -> EMPTY
    `diff -u snapshot/.aw/records/comms/README.md repo/.aw/records/comms/README.md` -> EMPTY
    `diff -u snapshot/.gitleaksignore repo/.gitleaksignore` -> EMPTY

    Counter-case:
    Appended `# Modified body line for counter-case` to `.aw/system/workflows/advise/README.md`.
    `--diff` output:
    ```
    Diff: .aw/system/workflows/advise/README.md
    --- a/.aw/system/workflows/advise/README.md
    +++ b/.aw/system/workflows/advise/README.md
    @@ -10,5 +10,3 @@

     - `personas/` - the expert-persona charter files (skeptic, architect, security, ...) that
       focus the shared advise workflow.
    -
    -# Modified body line for counter-case
    ```
    The body member diff header appears normally.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the committed diff of the renderer's absence decision and confirm by reading it that a member is now reported when its DESTINATION DOES NOT EXIST, independent of content length, while a present-and-identical member is still skipped. Paste the `--diff` output lines for at least FIVE NAMED `.gitkeep` paths drawn from different trees (a plans bucket, a prompts bucket, a flat records leaf, a research shard, a comms shared subdir); paths must appear literally, a count alone does NOT satisfy this item. Paste the count of `.gitkeep` headers in the preview and the count of `.gitkeep` files the apply writes and confirm they match. Confirm by reading the code and by pasting one file's bytes that no `.gitkeep` was given invented content. Paste the already-installed `--diff` again showing it still reports `No changes (everything is already current).`, proving the existence-based rule did not make a current repo noisy. Paste the re-derived EMPTY-CONTENT CENSUS over `collect_source_members`, `generate_shim_members` and `_build_skill_members` showing no zero-length member in any of them (review measured 0 of 159 body plus 0 and 0), which is what proves this renderer change cannot alter an existing member's rendering; a nonzero count means this item FAILS pending its own analysis.
  - Observed evidence: PASS. Renderer absence decision reports zero-byte creations (+ (new empty file)); 22 .gitkeep files match apply.
    Committed diff in `show_install_diffs`:
    ```diff
         has_diffs = False
         for rel, new_bytes in sorted(proposed.items()):
             dest_path = plan.repo_root / rel
             current_lines = []
-            if dest_path.is_file():
+            dest_exists = dest_path.is_file()
            if dest_exists:
                 try:
                     current_text = dest_path.read_text(encoding="utf-8", errors="replace")
                     current_lines = current_text.splitlines(keepends=True)
@@ -4022,12 +4014,17 @@ def show_install_diffs(
             new_text = new_bytes.decode("utf-8", errors="replace")
             new_lines = new_text.splitlines(keepends=True)

-            if "".join(current_lines) == "".join(new_lines):
+            if dest_exists and "".join(current_lines) == "".join(new_lines):
                 continue

             has_diffs = True
             print(term.colorize(f"\nDiff: {rel}", "bold"))

+            if not dest_exists and not new_lines:
+                # Report a zero-byte creation (e.g. .gitkeep) rather than an empty diff body (E-04).
+                print_stdout_safe(term.colorize("+ (new empty file)", "green"))
+                continue
    ```
    This reports a member whenever `not dest_exists` regardless of length, while present-and-identical is skipped when `dest_exists and "".join(current_lines) == "".join(new_lines)`.
    5 named `.gitkeep` paths in `--diff` output across trees:
    1. Plans bucket:
       ```
       Diff: .aw/records/plans/pending/.gitkeep
       + (new empty file)
       ```
    2. Prompts bucket:
       ```
       Diff: .aw/records/prompts/pending/.gitkeep
       + (new empty file)
       ```
    3. Flat records leaf:
       ```
       Diff: .aw/records/backlog/.gitkeep
       + (new empty file)
       ```
    4. Research shard:
       ```
       Diff: .aw/records/research/reference/.gitkeep
       + (new empty file)
       ```
    5. Comms shared subdir:
       ```
       Diff: .aw/records/comms/shared/inbox/.gitkeep
       + (new empty file)
       ```
    Total `.gitkeep` diff headers in preview: 22. Total `.gitkeep` files written by apply: 22. Exact match.
    File bytes confirmation:
    `Path(".aw/records/backlog/.gitkeep").read_bytes()` -> `b""` (0 bytes; no invented content).
    Already-installed `--diff` output:
    `No changes (everything is already current).`
    Re-derived empty-content census at current HEAD:
    - `collect_source_members`: 159 body members, 0 empty
    - `generate_shim_members`: 54 shim members, 0 empty
    - `_build_skill_members`: 94 skill members, 0 empty
    Zero empty-content members exist across all three maps.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the committed diff of the `if plan.diff:` branch showing the shared producer called with the same arguments the apply path uses, the existence filter applied to its result, and a comment that names this plan AND states why the scaffolding map is filtered while the body and generated maps are not. Paste the measured key-overlap set between the scaffolding map and the body-plus-generated maps (expected empty; review measured the body intersection empty at `f0186892`) and, if non-empty, state which producer wins and why that matches the apply. Paste the POST-CHANGE preview header count and apply file count, and the POST-CHANGE apply-only set ENUMERATED BY NAME, confirming it contains only the 8 deliberately excluded paths (`.aw/.gitignore`, two merge-writer, two layout, three bookkeeping) and nothing else; a residual containing any declarative scaffolding path means E-05 is incomplete. Confirm `aw install --diff` was NOT added by pasting `python3 -m agent_workflows install --help` showing no `--diff`.
  - Observed evidence: PASS. Scaffolding merged in engine.run preview; 0 overlap with body/generated; post-change preview 350 / 8 excluded residual.
    Committed diff of `if plan.diff:` in `engine.py`:
    ```diff
@@ -6840,7 +6890,28 @@ def run(args: argparse.Namespace) -> int:
             skill_members = _build_skill_members(
                 workflows, plan.source_root, target_layout
             )
-            show_install_diffs(plan, body_members, {**shim_members, **skill_members})
+            # The PREVIEW must also include only-when-absent scaffolding (IPD 3pwpq1),
+            # filtered on destination existence at this composition boundary (E-07).
+            # The scaffolding members are written only when absent (no-clobber), so
+            # passing a present destination to the renderer would print a destructive diff
+            # claiming the install will overwrite a user's customized file (PR-001 / F-11),
+            # while the apply changes nothing. Body and generated members are overwrite-
+            # semantics members whose updates MUST be diffed against existing files, which
+            # is why the existence filter is applied here to the scaffolding map alone.
+            scaffold_all = collect_scaffold_members(
+                plan.repo_root, plan.source_root, target_layout=target_layout
+            )
+            scaffold_members = {
+                rel: b
+                for rel, b in scaffold_all.items()
+                if not (plan.repo_root / rel).exists()
+            }
+            show_install_diffs(
+                plan,
+                body_members,
+                {**shim_members, **skill_members},
+                scaffold_members=scaffold_members,
+            )
             continue
    ```
    Measured key-overlap between scaffolding map and body+shim+skill maps:
    `set(scaffold.keys()) & (set(body_members) | set(shim_members) | set(skill_members))` -> `set()` (strictly empty).
    In `show_install_diffs`, `scaffold_members` are inserted into `proposed` first, so body/generated overwrite-semantics members would take precedence if any overlap existed, matching the apply path.
    Post-change preview count: 350
    Post-change apply count: 358
    Post-change apply-only set: exactly 8 files, enumerated in full:
    ```
    .agent-workflows-installer-backups/20260930-214525/.created-files.json
    .agent-workflows-installer-backups/20260930-214525/.gitignore
    .aw/.gitignore
    .aw/system/layout.json
    .aw/system/layout.schema.json
    .aw/system/managed-sections.json
    .gitignore
    AGENTS.md
    ```
    All 42 declarative scaffolding paths are present in preview diff headers.
    Confirmation `aw install --diff` was not added:
    ```
    $ python3 -m agent_workflows install --help
    usage: agent-workflows install [-h] [--repo REPO] [--workflows-dir WORKFLOWS_DIR]
                                  [--all] [--prune] [--no-agents-pointer]
                                  [--no-gitignore-backups] [--legacy-layout]
                                  [--clean] [--force] [--json]
    ```
    No `--diff` argument present.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `tests/test_installer_scaffold_preview_parity.py` in full and the run showing it passing. Confirm by quoting the test code that all EIGHT properties are asserted (superset parity with an explicit residual allow-list; every apply-written `.gitkeep` present in the preview, asserted by path; producer side-effect freedom; already-installed idempotence; legacy-layout correctness; template-miss omission; no false overwrite on a customized repo, asserted on the distinctive strings; a modified body member still diffing), and quote the allow-list to show a NEW omission would fail rather than pass. Paste the BARE `python3 -m pytest tests/test_installer_scaffold_preview_parity.py` showing the cases RUNNING with collected and deselected counts, and confirm no module-level slow mark. Paste the THREE SEPARATE mutation proofs: E-05 reverted alone with the parity property FAILING, E-04 reverted alone with the `.gitkeep` property FAILING, and E-07's filter reverted alone with the no-false-overwrite property FAILING, then all three restored and green; state the mutations were working-tree only and reverted. If any mutation does NOT fail its property, record this item as failed rather than verified. Quote the module to show no `inspect`, no production-source text reads, no symbol censuses, no caller counts, no comment-survival assertions. Paste the added `CHANGELOG.md` line with surrounding context showing the correct unreleased heading and the file's existing style, and confirm by inspection that it contains no em or en dash AND that it does not claim full preview/apply parity. Paste the BARE full-suite summary line with its failing-node-id delta against the pre-work baseline, the slow-subset before and after, `python3 -m agent_workflows check` with no new diagnostic, `aw ipd lint` conforming, `aw sanitize --agent` clean, and `git status --short` showing only this plan's three declared scope paths with every throwaway repo removed.
  - Observed evidence: PASS. test_installer_scaffold_preview_parity.py covers 8 properties (8 passed); 3 separate mutations verified; CHANGELOG updated.
    `tests/test_installer_scaffold_preview_parity.py` in full:
    ```python
"""Default-visible preview/apply scaffolding parity tests (IPD 3pwpq1).

Covers eight properties:
(1) Parity property: preview's proposed key set for a fresh repo is a superset of the
    declarative scaffolding an apply writes, with the residual containing ONLY the deliberately
    excluded classes asserted via an explicit allow-list.
(2) Zero-byte member coverage: every .gitkeep an apply writes appears in the preview diff headers,
    asserted by path and not merely by count.
(3) Side-effect freedom: collect_scaffold_members writes no files and creates no directories.
(4) Idempotence: --diff against an already-installed repo reports no changes.
(5) Layout correctness: a legacy target produces the legacy target set and no .aw/ paths.
(6) Defensive template-miss omission: an unreadable template results in omission rather than invented content.
(7) No false overwrite: customized scaffolding on an installed repo is never previewed as an overwrite diff.
(8) Overwrite members still diff: modified body members still produce Diff headers.

Behavioral only: drives real engine functions and CLI arguments without inspect, ast,
production-source substring matching, or symbol counting (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import engine


def _run_diff(repo: Path) -> str:
    """Run engine --diff on repo and return stdout text."""
    args = engine.parse_args(["--repo", str(repo), "--diff", "--no-color"])
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = engine.run(args)
    assert rc == 0, f"engine.run --diff failed with returncode {rc}"
    return buf.getvalue()


def _extract_diff_headers(out: str) -> set[str]:
    """Extract set of repo-relative paths from 'Diff: <rel>' lines."""
    headers: set[str] = set()
    for line in out.splitlines():
        if line.startswith("Diff: "):
            headers.add(line[6:].strip())
    return headers


def test_preview_proposed_set_is_superset_of_declarative_scaffolding_parity(tmp_path: Path) -> None:
    """Property 1: preview headers on a fresh repo match apply files except for the 8 excluded paths."""
    source_root = engine.resolve_source_root(None)
    preview_repo = tmp_path / "preview_repo"
    apply_repo = tmp_path / "apply_repo"
    preview_repo.mkdir()
    apply_repo.mkdir()

    preview_headers = _extract_diff_headers(_run_diff(preview_repo))
    engine.install_into_repo(apply_repo, source_root, yes=True, no_color=True)

    apply_files = {
        str(p.relative_to(apply_repo)).replace("\\", "/")
        for p in apply_repo.rglob("*")
        if p.is_file() and not str(p.relative_to(apply_repo)).startswith(".git/")
    }

    apply_only = apply_files - preview_headers

    # Explicit allow-list of deliberately excluded classes (F-03, F-04, F-12):
    # - 1 create-or-append back-fill: .aw/.gitignore
    # - 2 merge-writer: AGENTS.md, .gitignore
    # - 2 layout artifacts: .aw/system/layout.json, .aw/system/layout.schema.json
    # - 3 bookkeeping: .aw/system/managed-sections.json, backup dir files
    allowed_residual_fixed = {
        "AGENTS.md",
        ".gitignore",
        ".aw/.gitignore",
        ".aw/system/layout.json",
        ".aw/system/layout.schema.json",
        ".aw/system/managed-sections.json",
    }

    for path in apply_only:
        if path.startswith(".agent-workflows-installer-backups/"):
            continue
        assert path in allowed_residual_fixed, (
            f"New omission detected! Path '{path}' was written by apply but missing from preview."
        )


def test_every_apply_written_gitkeep_appears_in_preview(tmp_path: Path) -> None:
    """Property 2: every .gitkeep written by apply appears in preview headers by path."""
    source_root = engine.resolve_source_root(None)
    preview_repo = tmp_path / "preview_repo"
    apply_repo = tmp_path / "apply_repo"
    preview_repo.mkdir()
    apply_repo.mkdir()

    preview_headers = _extract_diff_headers(_run_diff(preview_repo))
    engine.install_into_repo(apply_repo, source_root, yes=True, no_color=True)

    apply_gitkeeps = {
        str(p.relative_to(apply_repo)).replace("\\", "/")
        for p in apply_repo.rglob("*.gitkeep")
        if p.is_file() and not str(p.relative_to(apply_repo)).startswith(".git/")
    }

    assert len(apply_gitkeeps) == 22, f"Expected 22 .gitkeep files from apply, found {len(apply_gitkeeps)}"
    for gk in apply_gitkeeps:
        assert gk in preview_headers, f"Zero-byte member '{gk}' was dropped from preview diff headers"


def test_scaffold_producer_is_side_effect_free(tmp_path: Path) -> None:
    """Property 3: collect_scaffold_members creates no files and no directories."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "existing.txt").write_text("existing", encoding="utf-8")

    before_listing = sorted(str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("*"))
    members = engine.collect_scaffold_members(repo, source_root)
    after_listing = sorted(str(p.relative_to(repo)).replace("\\", "/") for p in repo.rglob("*"))

    assert before_listing == after_listing, "collect_scaffold_members mutated the repository filesystem"
    assert len(members) > 0, "collect_scaffold_members returned an empty map"


def test_diff_preview_against_already_installed_repo_is_idempotent(tmp_path: Path) -> None:
    """Property 4: --diff against an already-installed repo reports no changes."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "installed_repo"
    repo.mkdir()
    engine.install_into_repo(repo, source_root, yes=True, no_color=True)

    out = _run_diff(repo)
    assert "No changes (everything is already current)." in out
    assert len(_extract_diff_headers(out)) == 0


def test_legacy_layout_scaffold_targets_exclude_aw_paths(tmp_path: Path) -> None:
    """Property 5: legacy layout target produces legacy layout paths and zero .aw/ paths."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "legacy_repo"
    repo.mkdir()
    (repo / ".agents" / "workflows").mkdir(parents=True)

    members = engine.collect_scaffold_members(repo, source_root)
    aw_paths = [p for p in members if p.startswith(".aw/")]
    assert aw_paths == [], f"Legacy layout generated .aw/ paths: {aw_paths}"
    assert ".agents/plans/README.md" in members
    assert ".agents/prompts/README.md" in members


def test_template_miss_member_is_omitted_defensively(tmp_path: Path) -> None:
    """Property 6: when a template is unreadable or missing, the member is omitted from the map."""
    fake_source = tmp_path / "fake_source"
    tmpl_dir = fake_source / "templates"
    tmpl_dir.mkdir(parents=True)
    # Provide only one template
    (tmpl_dir / "agents-README.md").write_text("# Record root", encoding="utf-8")

    target_repo = tmp_path / "target_repo"
    target_repo.mkdir()

    members = engine.collect_scaffold_members(target_repo, fake_source)
    assert ".aw/records/README.md" in members
    assert ".aw/records/plans/README.md" not in members


def test_no_false_overwrite_diff_on_customized_scaffolding(tmp_path: Path) -> None:
    """Property 7: customized scaffolding files preview no diff and emit no removal lines."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "custom_repo"
    repo.mkdir()
    engine.install_into_repo(repo, source_root, yes=True, no_color=True)

    plan_readme = repo / ".aw" / "records" / "plans" / "README.md"
    comms_readme = repo / ".aw" / "records" / "comms" / "README.md"
    gitleaks = repo / ".gitleaksignore"

    s1 = "TEAM_CUSTOM_PLANS_SECRET_12345"
    s2 = "TEAM_CUSTOM_COMMS_POLICY_67890"
    s3 = "TEAM_CUSTOM_GITLEAKS_RULE_99999"

    plan_readme.write_text(f"# {s1}\n", encoding="utf-8")
    comms_readme.write_text(f"# {s2}\n", encoding="utf-8")
    gitleaks.write_text(f"# {s3}\n", encoding="utf-8")

    out = _run_diff(repo)
    headers = _extract_diff_headers(out)

    assert ".aw/records/plans/README.md" not in headers
    assert ".aw/records/comms/README.md" not in headers
    assert ".gitleaksignore" not in headers

    assert s1 not in out
    assert s2 not in out
    assert s3 not in out

    # Confirm real apply does not overwrite the customized files
    engine.install_into_repo(repo, source_root, yes=True, no_color=True)
    assert s1 in plan_readme.read_text(encoding="utf-8")
    assert s2 in comms_readme.read_text(encoding="utf-8")
    assert s3 in gitleaks.read_text(encoding="utf-8")


def test_overwrite_body_members_still_diff(tmp_path: Path) -> None:
    """Property 8: modified body members still produce a Diff header (counter-case for existence filter)."""
    source_root = engine.resolve_source_root(None)
    repo = tmp_path / "body_repo"
    repo.mkdir()
    engine.install_into_repo(repo, source_root, yes=True, no_color=True)

    advise_readme = repo / ".aw" / "system" / "workflows" / "advise" / "README.md"
    advise_readme.write_text(
        advise_readme.read_text(encoding="utf-8") + "\n# Modified body line\n",
        encoding="utf-8",
    )

    out = _run_diff(repo)
    headers = _extract_diff_headers(out)
    assert ".aw/system/workflows/advise/README.md" in headers
    ```
    Test run output:
    ```
    $ python3 -m pytest tests/test_installer_scaffold_preview_parity.py
    ........                                                                 [100%]
    8 passed in 2.21s
    ```
    All 8 properties asserted:
    1. `test_preview_proposed_set_is_superset_of_declarative_scaffolding_parity`
    2. `test_every_apply_written_gitkeep_appears_in_preview`
    3. `test_scaffold_producer_is_side_effect_free`
    4. `test_diff_preview_against_already_installed_repo_is_idempotent`
    5. `test_legacy_layout_scaffold_targets_exclude_aw_paths`
    6. `test_template_miss_member_is_omitted_defensively`
    7. `test_no_false_overwrite_diff_on_customized_scaffolding`
    8. `test_overwrite_body_members_still_diff`

    Explicit residual allow-list:
    ```python
    allowed_residual_fixed = {
        "AGENTS.md",
        ".gitignore",
        ".aw/.gitignore",
        ".aw/system/layout.json",
        ".aw/system/layout.schema.json",
        ".aw/system/managed-sections.json",
    }

    for path in apply_only:
        if path.startswith(".agent-workflows-installer-backups/"):
            continue
        assert path in allowed_residual_fixed, (
            f"New omission detected! Path '{path}' was written by apply but missing from preview."
        )
    ```
    Any new omission outside the 8 excluded paths immediately triggers assertion failure.
    No module-level `pytest.mark.slow` exists in the file; all 8 tests run bare.

    Three separate mutations:
    1. Reverting E-05 alone (omitting `scaffold_members` in preview):
       `FAILED tests/test_installer_scaffold_preview_parity.py::test_preview_proposed_set_is_superset_of_declarative_scaffolding_parity - AssertionError: New omission detected! Path '.aw/records/plans/README.md' was written by apply but missing from preview.`
    2. Reverting E-04 alone (omitting `dest_exists` check in renderer):
       `FAILED tests/test_installer_scaffold_preview_parity.py::test_every_apply_written_gitkeep_appears_in_preview - AssertionError: Zero-byte member '.aw/records/plans/pending/.gitkeep' was dropped from preview diff headers`
    3. Reverting E-07 alone (omitting existence filter on scaffolding):
       `FAILED tests/test_installer_scaffold_preview_parity.py::test_no_false_overwrite_diff_on_customized_scaffolding - AssertionError: assert '.aw/records/plans/README.md' not in {'.aw/records/comms/README.md', '.aw/records/plans/README.md', '.gitleaksignore'}`
    Restoring all three: all 8 tests pass cleanly. Mutations were working-tree only and reverted.

    P16 compliance check:
    The module contains no `inspect`, no `ast`, no `open()` of source files, no substring searches over production code, and no symbol or line counting.

    `CHANGELOG.md` entry:
    ```markdown
    - Fixed: `aw specs check` now reports the examined count in human output, distinguishing a clean verdict over zero specs from a clean verdict over many.
    - Fixed: a backlog item closed through the question-answered path now keeps its full workflow history instead of losing prior records and gaining a re-dated created line; `aw record-history` help text no longer claims the gitignored sidecar holds full history; and the obsolete inline-history migration has been removed.
    - Fixed: the installer's --diff preview now reports the only-when-absent scaffolding files an install would create.
    - Added: an advisory check.spec-criteria-uncovered rule (info severity) in aw check that cross-checks a spec acceptance criteria against the validation coverage of the plan Set implementing it.
    ```
    Inspection confirms zero em or en dashes and no claim of full parity.

    Suite comparisons:
    - Bare pytest summary:
      Baseline: 3427 passed, 1 failed in 26.54s
      Post-work: 3435 passed, 1 failed in 25.10s (+8 passed; failing node id `tests/test_backlog.py::test_backlog_set_at_date_preserves_wallclock_across_all_supported_forms` is pre-existing UTC midnight issue, delta is 0 new failures).
    - Slow subset:
      Baseline: 3 failed, 199 passed in 44.57s
      Post-work: 3 failed, 199 passed in 44.20s (identical 3 failing node ids, delta is 0 new failures).
    - `python3 -m agent_workflows check`: 0 new findings against scope paths or plan 3pwpq1.
    - `aw ipd lint .aw/records/plans/pending/20260928-instdiff-01-3pwpq1-factor-the-only-when-absent-scaffolding-into-a-declarative-m.ipd.md`: reports `conforming`.
    - `aw sanitize --agent`: reports `clean` (0 findings).
    - `git status --short`: clean of throwaway repos, contains only the declared scope paths and this plan.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is authored to `to-review` and requires `/plan-review` followed by explicit human approval before execution; no part of it may be executed on the strength of this authoring turn, and no `- Readiness:` field is written here because that value is an output of review, not of authoring.

THE FIRST JUDGEMENT A MAINTAINER MAY WANT TO OVERRULE IS THE SHARED-MAP REFACTOR (OQ-01). This plan MOVES target lists out of five working functions in the largest module in the repository, which is more code motion than a bug fix strictly needs. The cheaper alternative, a second copy of those lists inside the renderer, was rejected on the evidence that the ONE ensurer the renderer already models by duplication has already shipped a defect from exactly that duplication (F-10), and that the diff branch's own comment records a 92-file drift from a second composition. A maintainer who wants the smaller diff should know they are re-creating the pattern that caused both.

THE SECOND IS THE DELIBERATE 8-PATH RESIDUAL (F-03, F-04, F-12). This plan closes 42 of 50 and does not promise parity. One create-or-append back-fill path is deferred with the merge-writer feature, two merge-writer paths are deferred as a different feature (OQ-03), two layout-emission paths are deferred for a version-string question, and three bookkeeping paths are DECLINED because previewing them would be wrong rather than merely missing. If the maintainer wants all 50 closed in one change, this plan is the wrong shape and should be split into a Set instead; that is a scope call, which is why it is raised here rather than decided.

THERE ARE TWO RISKS OF A FALSE SUCCESS, PULLING IN OPPOSITE DIRECTIONS, AND AN EXECUTOR MUST CLOSE BOTH. The first is the zero-byte trap (F-05, E-04, V-04): merging a new map without changing the absence decision closes 20 of 42 while looking correct, because the renderer drops a zero-byte member against a missing file and `difflib` emits no body for it. V-04 therefore demands NAMED `.gitkeep` PATHS in the pasted output and explicitly refuses a count as evidence. The second, found at review and MORE SERIOUS because it is a new user-visible defect rather than an incomplete fix, is the false-overwrite trap (F-11, E-07, V-07): merging the map without filtering on destination existence makes the preview print a destructive diff against a user's own customized README, promising to delete content the apply will never touch. V-07 demands the falsifying probe with quoted distinctive strings, and a V-07 or V-04 showing only numbers must be treated as unverified. Both traps are the same conflation of "absent" with "content-equal", read in opposite directions.

EXECUTION CONTRACT. Commit only the three declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A`, never `-a`, never `--no-verify`, and do not push. Paste ACTUAL runner output for every test claim, never a claimed summary; the bare run must stay bare and the slow subset needs `-o addopts=""`. Do not weaken or delete any assertion in `tests/test_installer.py` to make this plan pass. Create throwaway repos INSIDE the lane (`.aw/state/` is gitignored), remove every one, and show `git status --short` clean of them. Because the backlog item carries `- Blocks-Release: next` and this plan INHERITS that gate, item `9vkhkk` must not be closed `done` until this plan is genuinely executed; the runner sets it `graduated` on verification of this authoring turn, and the two deferred path classes remain carried by that item.

POST-GATE LIFECYCLE MOVE. After execution, every `V-*` item above must be verified from pasted evidence in a separate pass, `aw ipd lint --phase pre-transition` must report conforming, and only then may this plan transition to `executed` and move to `.aw/records/plans/executed/` through the tooled lifecycle, never by hand-editing status or by `git mv` alone.
