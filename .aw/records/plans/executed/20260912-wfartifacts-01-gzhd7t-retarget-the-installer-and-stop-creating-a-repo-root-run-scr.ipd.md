# IPD: Retarget the installer and stop creating a repo-root run-scratch directory

- Date: 2026-09-12
- Kind: child
- Concern: THE INSTALLER STILL CREATES THE DIRECTORY THE DECISION RETIRED, AND ADVERTISES IT AS TRACKED. `engine.ARTIFACTS_DIR` is `"workflow-artifacts/"` (`engine.py:237`), `_ensure_artifacts_readme` (`:5139`) does `artifacts_dir.mkdir(parents=True, exist_ok=True)` at the REPO ROOT and writes a README there, and `:3292` adds the same path to the proposed-file set. So every fresh install materializes a repo-root directory whose README says "DO NOT gitignore this folder", which is the opposite of Order 07's ruling and the reason the maintainer noticed on 2026-09-12.
  `check_gitignore` COMPOUNDS IT BY REPORTING THE WRONG THING. At `:2664-2676` it inspects only the repo-root path and prints either "workflow-artifacts/ is ignored (correct, recommended for local working material)" or "workflow-artifacts/ is not ignored (advisory: working material will be tracked in git)". Both sentences are now wrong: the correct state is that the repo-root directory does not exist and `.aw/workflow-artifacts/` is ignored by the framework-owned file. An installer that keeps reporting on a retired path teaches the user the retired layout.
  THE FALLBACK LITERAL IS A SECOND COPY OF THE BAD PROSE. `_ensure_artifacts_readme` carries an inline `readme_content` fallback (`:5153-5162`) duplicating the "DO NOT gitignore this folder" text for when the template cannot be read, so fixing only the template file would leave a live copy that still ships on any OSError.
- Scope: Stop creating a repo-root run-scratch directory on install, retarget `ARTIFACTS_DIR` and the README emission to `.aw/workflow-artifacts/`, and make `check_gitignore` report the path that now matters. EXCLUDES the gitignore pattern itself (Order 02, which must land first), the README's CONTENT (Order 04), the shipped body references (Order 03), and migrating existing content (Order 05).
- Scope-Paths: agent_workflows/engine.py, tests/test_installer.py, tests/test_engine_install.py
- Item-Dependencies: none
- Status: executed
- Priority: high
- Work-Kind: bug
- Readiness: go-pending-approval
- Blocks-Release: next
- From-Backlog: o9inwt
- Set: wfartifacts
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: gzhd7t

## Workflow history
- 2026-09-18 executed (aw oc run): aw oc run self-finalize: gzhd7t verified (set wfartifacts, attempt 1). [Scope reconciliation - out-of-scope tests/test_awretrofit_install_selfheal.py: changed by the plan's approved execution (auto-reconciled by aw oc run); in-scope-unmodified tests/test_engine_install.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-12 approved (aw set): status set to approved
- 2026-09-12 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 all FIXED in place, none deferred, none REPLAN. aw ipd lint conformed at --phase author before semantic review and at --phase review-finalize after every revision. THE REVIEW RE-MEASURED EVERY NUMERIC CLAIM RATHER THAN TRUSTING IT, which is what produced the findings: the 86 occurrences, the 0 prefixed, the 29 repos, the 11-file and 3-file affected repos, the 170 reviews, the 42/10 test refs and all four engine.py citations re-verified EXACTLY, but the file count was 27 and is 25 (grep -rl without --include matched three __pycache__ binaries) and two per-file figures mixed grep -c lines with grep -o occurrences (18/11 vs the true 20/12). PR-002 found the riskiest gap: Order 05 described a MOVE where both trees are populated and three workflow names collide, so it is a MERGE; no RUN_ID collides because run ids are timestamps, but that is the data's property not the design's, so a merge test is now mandatory. PR-004 NARROWED Order 04 after finding the shipped agents-README.md template is already CORRECT and a fresh install receives it, so the wrong .aw/records/README.md is local drift from the Order 11 migration and the template must NOT be edited. PR-003 named the five tests that assert the defect. Also added, per the maintainer's instruction: an isolated-worktree clause to all six execution contracts, recording that aw oc run / aw agy run default isolate_worktree True and that a hand run must allocate its own lane. Typed review records written for all six. No product code was modified by this review. HUMAN APPROVAL IS STILL REQUIRED.
- 2026-09-12 to-review (aw set): Authored as Order 07 delivery (Set wfartifacts) from backlog o9inwt: the spec's run-scratch relocation was implemented in this repo but never delivered to the shipped surface (86 stale references, installer still creating a repo-root dir with a 'DO NOT gitignore' README, 29 repos affected). Review-ready: no TODO placeholders, E/V bijection complete, every V-item demands pasted evidence.

- 2026-09-12 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a fresh install produce the layout Order 07 chose, and stop advertising the retired one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: retarget the code, then prove a fresh install is clean

- [x] E-01 RETARGET `ARTIFACTS_DIR` AND EVERY WRITE SITE TO `.aw/workflow-artifacts/`, and REMOVE the repo-root `mkdir`.
  THE THREE SITES, located by name rather than by the line numbers cited here: the `ARTIFACTS_DIR` constant (`engine.py:237`), the proposed-file entry (`:3292`), and `_ensure_artifacts_readme` (`:5139`), which is the one that actually creates the directory.
  DO NOT LEAVE A REPO-ROOT `mkdir` BEHIND. The maintainer's report is specifically that the directory APPEARS; a run that merely stops writing the README but still creates an empty directory has not fixed the reported defect.
  KEEP `LEGACY_ARTIFACTS_DIR` AND THE PRE-D19 MIGRATION INTACT (`:238`, `:2608-2613`). That code moves `repository-review/` into the artifacts tree and is a DIFFERENT, older migration; retargeting its destination is correct, deleting it is not.
  - Depends on: none
  - Expected outcome: `ARTIFACTS_DIR` is the `.aw/` path, no repo-root directory is created by any install path, and the pre-D19 migration still runs with its destination retargeted.
  - Execution state: performed
  - Execution note: `ARTIFACTS_DIR = ".aw/workflow-artifacts/"`. All three named sites retargeted: the constant; the proposed-file entry in `show_install_diffs`, now DERIVED as `f"{ARTIFACTS_DIR}README.md"` so the diff preview cannot drift from the write path; and `ensure_workflow_artifacts_readme`, whose repo-root `mkdir` is GONE (it now builds `plan.repo_root / ARTIFACTS_DIR`). The pre-D19 migration and `LEGACY_ARTIFACTS_DIR` are INTACT with the destination retargeted via `ARTIFACTS_DIR`; its follow-up `git add` had to move to the tolerant `git_add_optional` because the retargeted destination is ignored and a raw add aborted the install (measured; decision D-03). Two additions beyond the literal three sites, both consequences of the move: the ensurer now SKIPS a `legacy` layout target (which has no `.aw/` tree, so writing there would half-migrate it and land an unignored file), and `.aw/workflow-artifacts` was added to `_DEEP_CLEANUP_ROOTS` classified as OTHER, since relocating the tree inside `.aw/` brought it into `aw uninstall --deep`'s "no `.aw/` remains" promise (decision D-04).

- [x] E-02 FIX `check_gitignore` TO REPORT THE PATH THAT MATTERS, or remove the advisory if it no longer says anything true.
  WHAT IT SAYS TODAY IS MISLEADING IN BOTH BRANCHES: "workflow-artifacts/ is ignored (correct, recommended...)" and "...is not ignored (advisory: working material will be tracked in git)". After Order 02 the framework-owned `.aw/.gitignore` ignores the real path unconditionally, so an advisory about the user's ROOT gitignore and a retired path is noise that contradicts the installer's own behavior.
  DECIDE EXPLICITLY AND SAY WHY IN THE CODE: either report on `.aw/workflow-artifacts/` (and then it should essentially always read "ignored"), or drop the line and its `gitignore_status` plumbing. Do NOT leave a branch that can print advice about a directory the installer no longer creates.
  NOTE THE PLUMBING REACHES THE SUMMARY at `:3729` (`print(f"Gitignore (workflow-artifacts): {gitignore_status}")`) and through `install_into_repo`'s returned dict, so removing it is a small API change to check for callers, not a one-line delete.
  - Depends on: E-01
  - Expected outcome: no installer output describes the retired repo-root path, and whatever remains is true of a repo installed after Order 02.
  - Execution state: performed
  - Execution note: OQ-01 RESOLVED AS "RETARGET, NOT REMOVE", with the reason recorded in the function docstring as E-02 required (decision D-01). The decision is not merely a path swap: retargeting the old LINE-SCAN alone could not have made the line true, because it inspected the repo-ROOT `.gitignore` while the rule that protects run scratch ships in the framework-owned `.aw/.gitignore`, so it would have reported "not ignored" about a path that IS ignored. The predicate is now `git check-ignore -v --no-index`, the same authority the sibling `_already_tracked_untracked_matches` and `git_commit_helper` use, and it ATTRIBUTES the rule to the source file providing it. No branch can now describe the retired directory: a `legacy` target returns an explicit `n/a`, and non-git degrades to "could not be checked" rather than a false claim. The `gitignore_status` key and the function signature are UNCHANGED, so no caller was touched. `print_summary`'s label was also changed, because it hard-coded `Gitignore (workflow-artifacts)` and so named the retired path even when the status string did not; it now reads `Gitignore (run scratch)`.

- [x] E-03 PROVE A FRESH INSTALL PRODUCES NO REPO-ROOT DIRECTORY AND UPDATE THE TESTS THAT PIN THE OLD BEHAVIOR.
  EXPECT EXISTING TESTS TO FAIL, and treat that as the signal rather than a nuisance: 42 references to `workflow-artifacts`/`ARTIFACTS_DIR` exist across 10 test files (`test_installer.py`, `test_awretrofit_install_selfheal.py`, `test_acceptance_matrix.py`, `test_packaging.py` and others). Each must be re-pointed or deliberately re-scoped, and any that asserts the repo-root README is INSTALLED is asserting the defect and must be inverted.
  THE DEFECT-ASSERTING SITES ARE NAMED IN F-7 so you do not have to hunt: `test_installer.py:394` (`is_file()` on the repo-root README), `:406` (its "Git Guidelines" content), `:409-410` (a re-run preserves a customized copy), and `test_awretrofit_install_selfheal.py:69`/`:78` (`git_add_optional` on the same path). The `test_installer.py:409` case is the subtle one: PRESERVING a user's customized README is correct behavior that should survive at the NEW path, so re-point it rather than delete it.
  THE NEW ASSERTION THAT MATTERS: after `install_into_repo` on a fresh repo, `(repo / "workflow-artifacts").exists()` is FALSE. That single line is the maintainer's report turned into a test.
  RUN THE SUITE BARE and compare the FAILURE SET, not counts.
  - Depends on: E-02
  - Expected outcome: a test asserting no repo-root directory after a fresh install, every pre-existing reference re-pointed or re-scoped with a stated reason, and an empty bare-suite failure-set delta.
  - Execution state: performed
  - Execution note: Two NEW tests in `tests/test_installer.py`: `test_fresh_install_creates_no_repo_root_workflow_artifacts_dir` (the maintainer's report as a test: `(repo / "workflow-artifacts").exists()` is False, the README landed at the new path, and it is NOT in the index) and `test_installer_summary_names_no_repo_root_run_scratch_path` (E-02's guard, a regex sweep of real installer output). All five F-7 defect-asserting sites were RE-POINTED, none deleted: `test_installer.py`'s README-creation list, its "Git Guidelines" content check, and its customized-copy-preserved re-run case (that one is CORRECT behavior that should survive at the new path, exactly as F-7 warned); and both `test_awretrofit_install_selfheal.py` cases, whose module docstring now records that the "not staged" guarantee is henceforth by CONSTRUCTION rather than by the ignore rule matching. The F-5 count was re-measured rather than trusted: of the 42 references across 10 files, only those 5 asserted the defect; the rest are legacy-migration and inventory/scan fixtures that legitimately still name the OLD path (they test pre-Order-07 repos), so they were left alone deliberately - 131 passed across those 8 suites unchanged. NOTE the E-01 deep-cleanup addition was DISCOVERED by a failing test rather than by inspection, which is what F-5's "treat failures as the signal" instruction is for.

## Project conventions discovered (Step 0)

- ORDER 07 IS THE AUTHORITY AND IT IS ALREADY `implemented`: spec `20260817-2124-01-records-taxonomy-cleanup` (`u7xtni`), history line "run-artifacts -> `.aw/workflow-artifacts/`". This Set DELIVERS that decision; it does not revisit it.
- RUN SCRATCH IS UNTRACKED BECAUSE OF D92: run records carry local context, absolute home paths and session detail, so committing them publishes machine identity into permanent history. That is the reason, and it is why "just track it" is not an option.
- THIS REPO'S ROOT `.gitignore:62-68` ALREADY ENCODES THE TARGET STATE and is the best statement of intent in the tree, but it is NOT shipped: a target repo receives the framework-owned `.aw/.gitignore` instead. Never cite the root file as evidence that a target repo is protected.
- PATTERNS IN `.aw/.gitignore` ARE `.aw/`-RELATIVE AND MUST BE ANCHORED. The template's own `/inbox/` comment records the measured reason: a bare `inbox/` matched at any depth and silently swallowed the TRACKED `records/comms/shared/inbox/` lane, breaking `aw install`.
- `_ensure_aw_gitignore` IS THE ONLY PATH THAT REACHES AN ALREADY-INSTALLED REPO, because a repo that already has a `.aw/.gitignore` never re-reads the template. Every prior addition in that function carries a comment saying exactly this.
- `install_into_repo` IS THE SHARED CHOKEPOINT for every entry point (`aw install` via `engine.run()`, `aw setup` via `cli._run_setup` -> `cli._install_one`, and library callers). Wiring into `run()` reaches only one of them.
- `.aw/records/` IS TRACKED DURABLE RECORDS, NOT SCRATCH: `records/reviews/` alone holds 170 typed `.review.md` files. An agent already mistook it for the scratch home and moved run records into `.aw/records/reviews/untracked/`.
- Shared checkout, concurrent edits; the suite runs BARE (`python3 -m pytest`). Re-locate every symbol by NAME, not by the line numbers cited in these plans.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the installer creates the retired directory | `_ensure_artifacts_readme` calls `artifacts_dir.mkdir(parents=True, exist_ok=True)` on a REPO-ROOT path and writes a README into it. | `engine.py:5141`, `:5168` |
| F-2 | HIGH | the constant still points at the repo root | `ARTIFACTS_DIR = "workflow-artifacts/"`. | `engine.py:237` |
| F-3 | MEDIUM | the advisory is wrong in both branches | `check_gitignore` reports either "is ignored (correct...)" or "is not ignored (advisory...)" about a path that should not exist. | `engine.py:2664-2676`, printed at `:3729` |
| F-4 | MEDIUM | a third copy of the bad prose is inline | `_ensure_artifacts_readme`'s OSError fallback duplicates the README text, so fixing the template alone leaves live bad prose. | `engine.py:5153-5162` |
| F-5 | MEDIUM | 42 test references pin the old behavior | across 10 files (both figures re-verified at review); some assert the repo-root README IS installed, i.e. they assert the defect. | grep over `tests/` |
| F-7 | MEDIUM | THE DEFECT-ASSERTING TESTS ARE NAMED, so the executor does not have to hunt for them | `tests/test_installer.py:394` asserts `workflow-artifacts/README.md` `is_file()` and `:406` asserts its content contains "Git Guidelines"; `:409-410` then asserts a re-run PRESERVES a customized copy. `tests/test_awretrofit_install_selfheal.py:69`/`:78` exercise `git_add_optional` on that same path and its module docstring already cites "Order 07 gitignores workflow-artifacts", so that file half-knew. Each needs re-pointing to `.aw/workflow-artifacts/README.md` or re-scoping, not deletion. | read at review |
| F-6 | LOW | the pre-D19 migration must survive | `LEGACY_ARTIFACTS_DIR` moves `repository-review/` into the artifacts tree; it needs retargeting, not deletion. | `engine.py:238`, `:2608-2613` |

## Proposed changes (ordered, validatable)

1. Retarget `ARTIFACTS_DIR`, the proposed-file entry, and `_ensure_artifacts_readme`; remove the repo-root `mkdir` (E-01).
2. Make `check_gitignore` true or remove it with its plumbing (E-02).
3. Re-point or re-scope the 42 pinning test references and add the no-repo-root-directory assertion (E-03).

## Deferred / out of scope (with reason)

- WHERE RUN SCRATCH BELONGS. Settled by Order 07 and out of scope here; this Set delivers that ruling rather than re-opening it.
- `tools/untrack-workflow-artifacts.py`'s IN-PLACE BEHAVIOR. It untracks the repo-root path without moving anything and is not wired into install. It stays available for a user who wants only to untrack; changing it is a separate concern.
- THE PRESET/PLACEMENT DIVERGENCE recorded in backlog `2812t3` (presets still emit `state_durable: target-tracked` for a gitignored tree). Adjacent, separately carried, and not touched here.
- ANY DELETION OF A USER'S COMMITTED RUN RECORDS. Explicitly forbidden Set-wide; Order 05 relocates and never deletes.

## Scope check

- Over-scope: none.
- Under-scope, stated rather than left as `none`: this plan does not add the gitignore pattern (Order 02), does not change README CONTENT (Order 04), does not touch the shipped bodies (Order 03), and does not move existing content (Order 05). It also does not delete the pre-D19 `repository-review/` migration.

## Required tests / validation

- A FRESH `install_into_repo` INTO A SCRATCH REPO: assert `(repo / "workflow-artifacts").exists()` is FALSE. This single assertion is the maintainer's report turned into a test.
- THE INSTALLER SUMMARY names no repo-root `workflow-artifacts/` path.
- EVERY PRE-EXISTING TEST re-pointed or re-scoped, each named with a one-line reason; a DELETED test must be justified.
- `python3 -m pytest` BARE, failure-SET delta empty.
- `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change: Order 07's spec already specifies the target layout and is `implemented`. This plan makes the code match it.

`engine.py`'s module docstring (`:39`, `:42`, `:47`) describes `workflow-artifacts/` run records and D17/D19 behavior; update those lines so the file's own front matter does not contradict its code. That is documentation inside a declared Scope-Path, not a spec amendment.

## Open questions

### OQ-01: Should `check_gitignore` be retargeted or removed outright?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us (executor, 2026-09-18)
- Resolution: RETARGETED, NOT REMOVED, and additionally rewritten to ASK GIT rather than line-scan a file. Recorded in the `check_gitignore` docstring as E-02 required, and in decision `02-gzhd7t-D1`. The deciding evidence is that retargeting the old line-scan ALONE could not have made the advisory true: it inspected the repo-ROOT `.gitignore`, but after Order 02 the rule that protects run scratch lives in the framework-owned `.aw/.gitignore`, which a root-file scan structurally cannot see, so it would have printed "not ignored" about a path that IS ignored. The predicate is now `git check-ignore -v --no-index` (the same authority the sibling `_already_tracked_untracked_matches` and `git_commit_helper` already use), which also attributes the rule to its source file. Kept rather than dropped because, asked this way, the line is a genuine post-install check of the D92 containment that can report a real gap (a `legacy` target has no `.aw/` tree; a repo whose `.aw/.gitignore` predates Order 02 gains the rule only on an install that runs the back-fill), and removal would have cost an API change across two callers plus a test double for no gain. No branch can now describe the retired repo-root directory, which is the constraint E-02 said actually matters.
- Resolution or deferral rationale: EXECUTOR'S CHOICE, WITH THE REASON RECORDED IN CODE, and E-02 requires the decision be explicit either way. Resolved rather than asked because both options are defensible and neither is risky: after Order 02 the framework-owned gitignore ignores the real path unconditionally, so a retargeted advisory would essentially always print "ignored" and carries little information, while removing it is a small API change (`gitignore_status` appears in `install_into_repo`'s returned dict and the summary at `:3729`) that needs a caller check. What is NOT acceptable is leaving a branch that can advise about a directory the installer no longer creates. NOT BLOCKING: E-02 states the constraint that actually matters, and V-02 demands evidence for whichever path is taken.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `engine.py` diff for all three sites and quote the new `ARTIFACTS_DIR` value. Then paste, from a REAL fresh install into a scratch repo, the output of `ls -d <repo>/workflow-artifacts` showing it does NOT exist, and `ls -d <repo>/.aw/workflow-artifacts` if the README now lands there. An existing repo-root directory, even an empty one, is a FAILED validation: the reported defect is that the directory appears.
  - Observed evidence: `ARTIFACTS_DIR = ".aw/workflow-artifacts/"`; all three sites retargeted and the repo-root `mkdir` removed; on a REAL fresh install `ls -d <repo>/workflow-artifacts` reports "No such file or directory" (the directory does not exist AT ALL, not merely empty) while `ls -d <repo>/.aw/workflow-artifacts` lists `README.md`, and `git ls-files -- .aw/workflow-artifacts` is EMPTY. The pre-D19 migration survived with its destination retargeted. Full pasted evidence below and in the run submission's execution-report.md (V-01).

    THE NEW CONSTANT VALUE, quoted exactly:

    ```python
    ARTIFACTS_DIR = ".aw/workflow-artifacts/"
    ```

    SITE 1, the constant (`engine.py:237` at authoring time):

    ```diff
    -ARTIFACTS_DIR = "workflow-artifacts/"
    +ARTIFACTS_DIR = ".aw/workflow-artifacts/"
    ```

    SITE 2, the proposed-file entry in `show_install_diffs` (`:3292`), now DERIVED so it cannot drift:

    ```diff
    -    artifacts_readme = "workflow-artifacts/README.md"
    +    artifacts_readme = f"{ARTIFACTS_DIR}README.md"
    ```

    SITE 3, `ensure_workflow_artifacts_readme` (`:5139`), the one that actually created the directory. The repo-root `mkdir` is gone, because the path it builds is now the `.aw/` one:

    ```diff
    -    artifacts_dir = plan.repo_root / "workflow-artifacts"
    +    artifacts_dir = plan.repo_root / ARTIFACTS_DIR
         readme_path = artifacts_dir / "README.md"
    -    rel_path = "workflow-artifacts/README.md"
    +    rel_path = f"{ARTIFACTS_DIR}README.md"
    ```

    THE PRE-D19 MIGRATION SURVIVED (F-6), destination retargeted through the constant, with its `git add` made tolerant because the new destination is ignored:

    ```diff
    -                git_run(repo, ["add", "--", rel_dst])
    +                git_add_optional(repo, rel_dst)
    ```

    REAL FRESH INSTALL into a scratch git repo (`install_into_repo`, backup off, prune on):

    ```text
    === ls -d <repo>/workflow-artifacts (MUST NOT EXIST) ===
    ls: cannot access '<repo>/workflow-artifacts': No such file or directory
    === ls -d <repo>/.aw/workflow-artifacts ===
    <repo>/.aw/workflow-artifacts
    README.md
    ```

    The repo-root directory does not exist AT ALL (not merely empty), which is the criterion this item sets. The README landed at the new path.

    NOT STAGED, which decision D-02 makes deliberate (`git ls-files -- .aw/workflow-artifacts` on that install):

    ```text
    (empty output)
    ```

    AND the ignore state of the new path on this pre-Order-02 tree, which is exactly why the README is no longer staged:

    ```text
    $ git -C <repo> check-ignore -v --no-index -- .aw/workflow-artifacts/probe
    check-ignore-rc=1 (1 = not ignored; Order 02 has not landed)
    ```

  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the full installer summary block from a fresh install and show that NO line mentions a repo-root `workflow-artifacts/`. If the advisory was kept, quote the exact new sentence and show it is true for that repo by pasting `git check-ignore -v` on the path it names; if it was removed, paste the diff showing the `gitignore_status` plumbing removed from both the summary and `install_into_repo`'s returned dict, plus a grep proving no caller still reads that key.
  - Observed evidence: the advisory was KEPT and retargeted (OQ-01). The real fresh-install summary line reads `Gitignore (run scratch): .aw/workflow-artifacts/ is NOT ignored (run scratch carries local paths and session detail (D92); ...)`; a regex sweep of the WHOLE 351-line summary for a repo-root `workflow-artifacts/` returns NO match (rc=1), and `git check-ignore -v --no-index -- .aw/workflow-artifacts/probe` exits 1 on that repo, confirming the sentence is TRUE for it (Order 02 has not landed). Full pasted evidence below, summary saved as installer-summary.txt (V-02).

    THE ADVISORY WAS KEPT (OQ-01 resolved as retarget-not-remove; decision D-01), so this item's "if kept" branch applies. The full summary from a real fresh install is saved at the run submission as `installer-summary.txt` (351 lines); its status block reads:

    ```text
    AGENTS.md: created AGENTS.md with pointer
    CLAUDE.md: not present (skipped)
    GEMINI.md: not present (skipped)
    Gitignore (run scratch): .aw/workflow-artifacts/ is NOT ignored (run scratch carries local paths and session detail (D92); re-run `aw install` to add the framework-owned .aw/.gitignore rule)
    Gitignore (installer backups): added .agent-workflows-installer-backups/ to .gitignore
    ```

    NO LINE MENTIONS A REPO-ROOT `workflow-artifacts/`. Swept the WHOLE summary with a regex that matches the bare path but not the `.aw/`-prefixed one and not the shipped template filename:

    ```text
    $ grep -nE "(^|[^./[:alnum:]-])workflow-artifacts/" installer-summary.txt
    grep-rc=1 (1 = no match, correct)
    ```

    The only two remaining occurrences of the string anywhere in the summary are both legitimate and neither is the repo-root path:

    ```text
    164:[added    ] .aw/system/workflows/templates/workflow-artifacts-README.md
    320:[added    ] .aw/workflow-artifacts/README.md
    ```

    THE NEW SENTENCE IS TRUE FOR THAT REPO, shown with `git check-ignore` on the exact path it names. The summary says NOT ignored, and git agrees, because Order 02 (which carries the ignore rule) has not landed:

    ```text
    $ git -C <repo> check-ignore -v --no-index -- .aw/workflow-artifacts/probe
    check-ignore-rc=1 (1 = not ignored)
    ```

    This is the reporting behavior the item asks for: the line now reports the REAL state of the REAL path rather than asserting a fixed sentence, so it correctly shows a GAP today and will report the rule and its source file once Order 02 lands. Verifying the ignored branch names its source is covered by the `check-ignore -v` attribution in the code path (`source = result.stdout.split(":", 1)[0]`).

  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the new assertion and its passing output, then paste the BARE `python3 -m pytest` summary lines BEFORE and AFTER and state the failure-SET delta explicitly (criterion: empty). For every pre-existing test you changed, name it and say in one line whether it was re-pointed or re-scoped and why; a test deleted rather than re-pointed must be justified, since deleting a test that asserted the old path is how the guarantee silently disappears.
  - Observed evidence: new `test_fresh_install_creates_no_repo_root_workflow_artifacts_dir` + `test_installer_summary_names_no_repo_root_run_scratch_path` pass (`3 passed, 153 deselected`). BARE suite BEFORE `31 failed, 7962 passed, 3 skipped, 2 xfailed`, AFTER `31 failed, 7962 passed, 3 skipped, 2 xfailed`; FAILURE-SET DELTA IS EMPTY compared as SETS of test ids (`diff` of the sorted lists is identical), all 31 pre-existing runner/lifecycle failures this plan does not touch. Slow suites run explicitly too: `194 passed` + `131 passed` with one failure PROVEN pre-existing by re-running it at HEAD with my files stashed (`2 failed in 8.01s`), filed as backlog `57dwkc`. All five F-7 defect-asserting sites RE-POINTED, none deleted. Full pasted evidence and the per-test table below (V-03).

    THE NEW ASSERTION, the maintainer's report turned into a test:

    ```python
    self.assertFalse(
        (self.repo / "workflow-artifacts").exists(),
        "a fresh install must not create a repo-root workflow-artifacts/ directory "
        "(Order 07 relocated run scratch to .aw/workflow-artifacts/)",
    )
    ```

    ITS PASSING OUTPUT, together with the E-02 summary guard and the re-pointed README test:

    ```text
    $ python3 -m pytest tests/test_installer.py -o addopts="" -q -k "repo_root_workflow_artifacts or summary_names_no_repo_root or readme_creation"
    ...                                                                      [100%]
    3 passed, 153 deselected in 6.64s
    ```

    BARE SUITE BEFORE (at HEAD 6ff7a7ba, before any edit):

    ```text
    31 failed, 7962 passed, 3 skipped, 2 xfailed in 118.31s (0:01:58)
    ```

    BARE SUITE AFTER:

    ```text
    31 failed, 7962 passed, 3 skipped, 2 xfailed in 105.44s (0:01:45)
    ```

    FAILURE-SET DELTA IS EMPTY. Compared as SETS of test ids, not counts, per the execution contract:

    ```text
    baseline count: 31  after count: 31
    === DELTA ===
    FAILURE-SET DELTA IS EMPTY (identical sets)
    ```

    All 31 are pre-existing failures in runner/lifecycle suites (`test_oc_runipd.py`, `test_agy_runipd_cli.py`, `test_runner_backlog_close_in_lane.py`, `test_ipd_lifecycle_cli.py`, `test_novalnomerge_integration.py`, `test_worker_role_refusal.py`), none of which this plan touches. The two sorted lists are saved at the run submission as `base.clean` and `after.clean`.

    THE SLOW SUITES TOO, since `addopts` excludes `-m slow` from a bare run and `test_installer.py` IS slow-marked. Ran the installer + every path-referencing suite explicitly:

    ```text
    $ python3 -m pytest tests/test_installer.py tests/test_awretrofit_install_selfheal.py tests/test_engine_install.py -o addopts="" -q
    1 failed, 194 passed in 210.48s (0:03:30)
    FAILED tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory

    $ python3 -m pytest tests/test_acceptance_matrix.py tests/test_packaging.py tests/test_record_producers.py tests/test_layout_inventory_gitignore.py tests/test_scan_secrets.py tests/test_untrack_workflow_artifacts.py tests/test_untracked_lane_migration.py tests/test_awphysical_migration.py -o addopts="" -q
    131 passed in 11.44s
    ```

    THAT ONE FAILURE IS PRE-EXISTING AND NOT MINE, and I verified it rather than asserting it: with all three of my files stashed, at HEAD, it and its `test_cli.py` twin BOTH still fail:

    ```text
    $ git stash push -- agent_workflows/engine.py tests/test_installer.py tests/test_awretrofit_install_selfheal.py
    $ python3 -m pytest <the two tests> -o addopts="" -q
    2 failed in 8.01s
    ```

    The cause is unrelated: deep cleanup orphans `.aw/system/layout.json` + `layout.schema.json` (enumerated the remaining tree to confirm). Filed as backlog `57dwkc`. My `.aw/workflow-artifacts` deep-cleanup root works correctly on its own terms, verified directly: enumerated by `plan_deep_cleanup` = True, classified as OTHER not records = True, tree gone after `run_deep_cleanup` = True.

    EVERY PRE-EXISTING TEST I CHANGED, each RE-POINTED (none deleted, none re-scoped away):

    | Test | Action | Why |
    |---|---|---|
    | `test_installer.py::test_readme_creation_and_preservation` README list (`:394`) | re-pointed to `.aw/workflow-artifacts/README.md` | the "a fresh install creates it" guarantee is still real; only the path moved |
    | same test, "Git Guidelines" content check (`:406`) | re-pointed | asserts the template landed; its CONTENT is Order 04's scope, so the assertion is unchanged apart from the path |
    | same test, customized-copy-preserved re-run (`:409-410`) | re-pointed | F-7 flagged this as the subtle one: preserving a user's customized README is CORRECT behavior that must survive at the new path, so deleting it would drop a real guarantee |
    | `test_awretrofit_install_selfheal.py::test_ensure_workflow_artifacts_readme_survives_gitignored_dir` (`:69`) | re-pointed, plus a new assertion that no repo-root dir is created | the Order-10 no-abort guarantee is still live; the module docstring now records that "not staged" is henceforth guaranteed by CONSTRUCTION rather than by the ignore rule matching |
    | `test_awretrofit_install_selfheal.py::test_git_add_optional_returns_false_on_ignored` (`:78`) | re-pointed | `git_add_optional` is still used by the sibling README ensurers, so the helper's skip-on-ignored contract still needs direct coverage even though the run-scratch ensurer no longer calls it |

    NO TEST WAS DELETED. The other 37 of the 42 F-5 references were re-measured and deliberately LEFT naming the old path: they are legacy-migration and inventory/scan fixtures that model PRE-Order-07 repos (`test_acceptance_matrix.py`'s legacy artifact, `test_awphysical_migration.py`, `test_untrack_workflow_artifacts.py`, `test_record_producers.py`'s legacy-write rejection, `test_packaging.py`'s forbidden-top list), so re-pointing them would destroy what they test. All 131 pass unchanged.

  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since `pre-commit`'s stash/restore can leave a co-worker's paths in the index in this shared checkout. Paste ACTUAL command output for every validation item; never claim a result you did not run. Re-locate every symbol by NAME rather than by the line numbers cited here, which are accurate at authoring time only. Run the suite BARE (`python3 -m pytest`) and judge on the FAILURE-SET delta, not counts. Run `aw sanitize --agent` before treating any output as shareable.

DO NOT DELETE A USER'S COMMITTED RUN RECORDS, anywhere in this Set. Relocation preserves history; deletion is unrecoverable and is the one outcome worse than leaving the retired directory in place.

ISOLATE THE WORKTREE (maintainer instruction 2026-09-12). If you run this plan through `aw oc run` / `aw agy run` you already have this: `isolate_worktree` DEFAULTS TRUE (`oc_runipd.py:3048`, `:6106`; `agy_runipd.py:2055`, `:3254`), so the agent turn, verifier and finalize happen on an `aw/lane/<id6>` branch in a fresh worktree while the main tree stays untouched, and changes return through the merge-and-revalidate gate. Do NOT pass `--no-isolate-worktree`.
IF YOU EXECUTE BY HAND, ALLOCATE ONE YOURSELF rather than editing the main checkout: `git worktree add ../aw-lane-<id6> -b aw/lane/<id6>`, work and commit there, then merge back. THIS SET MAKES THAT PARTICULARLY IMPORTANT for two measured reasons. FIRST, Order 03 rewrites 25 shipped files and Orders 01/02/05 all edit `engine.py`, so a half-finished hand run leaves the installer and the shipped bodies DISAGREEING, which is the exact defect state this Set exists to end. SECOND, this is a SHARED CHECKOUT with concurrent agents and humans, and an isolated lane is what keeps a partial rewrite of `.aw/system/workflows/` from being visible to (or swept into a commit by) someone else mid-run.
NOTE THE ONE THING ISOLATION DOES NOT COVER: Order 05 must be TESTED against scratch clones, never against a user's real repository. A worktree isolates THIS repo's tree; it does nothing to protect the OTHER repositories on the machine whose committed run records that plan is designed to move (the two counted in Order 05's findings).

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence.
