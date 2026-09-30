# IPD: Retarget the untrack tool onto the run-scratch migration and restore the migration's deleted coverage

- Date: 2026-09-28
- Kind: child
- Concern: `tools/untrack-workflow-artifacts.py` STILL PERFORMS THE RETIRED LAYOUT'S MIGRATION, and running it today actively re-establishes the layout spec `20260817-2124-01` (`u7xtni`, Order 07) retired. Its module constant is `ARTIFACTS = "workflow-artifacts"`, the REPO-ROOT path, and `IGNORE_RULE = f"{ARTIFACTS}/"` is written into the user's ROOT `.gitignore` by `append_ignore_rule`. MEASURED on 2026-09-28 in a throwaway git repo carrying one tracked run record at `workflow-artifacts/assess/20260101-000000/report.md`: `python3 tools/untrack-workflow-artifacts.py --apply` prints `Local workflow-artifacts/ exists: yes` / `Tracked paths: 1` / `Removed 1 tracked path(s) from the Git index`, and afterwards `git ls-files` reports `.gitignore` plus `README.md` while the user's root `.gitignore` gained `workflow-artifacts/` under the comment `# agent-workflows working material (local-only; ...)`. THE RUN RECORD IS STILL AT THE REPO ROOT: nothing moved, so the double-home confusion Order 07 exists to end is preserved and freshly blessed with an ignore rule. Run the SAME repo through the replacement instead, `engine.migrate_root_workflow_artifacts`, and the outcome is strictly better on every axis: it reports `workflow-artifacts/assess/20260101-000000/report.md -> .aw/workflow-artifacts/assess/20260101-000000/report.md [migrated with git mv (history preserved, committed), then untracked so the .aw/.gitignore rule governs it; file kept on disk]` followed by `workflow-artifacts/ [removed: now empty; run scratch lives at .aw/workflow-artifacts/]`, and the user's root `.gitignore` is never created at all. So the tool is not merely stale prose: it is a WORSE, history-losing version of a migration the toolkit already performs correctly, and `tools/README.md` still advertises it as "Remediation Option A: Index-Only Stop Tracking (Recommended)". SECOND, AND NOT IN THE BACKLOG ITEM: the replacement has NO TEST COVERAGE LEFT. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_engine_install.py` entire, taking with it `RootRunScratchMigrationTests`, whose own docstring states "THE PROOF OBLIGATION IS UNUSUALLY HIGH" because this is "the only child that touches a user's committed history". `grep -rn "migrate_root_workflow_artifacts\|RETIRED_ROOT_ARTIFACTS_DIR" tests/` returns NOTHING today, and `ls tests/test_engine_install.py` reports no such file. Retargeting the tool onto that function while nothing tests the function is how a history-preserving migration decays silently.
- Scope: IN: (a) convert `tools/untrack-workflow-artifacts.py` into a thin delegating front end over `engine.migrate_root_workflow_artifacts`, on the `install-workflows.py` / `tools/agy_run.py` shim precedent, so the hand-run entry point performs the CORRECT migration and stops writing a root ignore rule for a retired path; (b) preserve the tool's one genuine safety property, DRY RUN BY DEFAULT, by routing it to the `dry_run=` parameter the engine function already exposes; (c) restore the deleted `RootRunScratchMigrationTests` as a focused new test file so the delegated-to function has outcome coverage again, keeping only tests that assert outcomes; (d) cover the delegation itself by driving the tool as a subprocess and asserting the relocation actually happened on disk and in the index; (e) rewrite the `tools/README.md` section, which currently recommends the wrong remediation. OUT: any change to `engine.migrate_root_workflow_artifacts` itself (it is `executed`, measured correct here, and this plan only gains it callers and tests); the `--commit` flag's removal versus retention beyond what OQ-01 decides; the separate root-doc path references owned by pending plan `fzueyy` (`ARCHITECTURE.md`, `CONTRIBUTING.md`), whose `- Scope-Paths:` already claims them and which explicitly declares `tools/README.md` and this tool OUT of its own scope; restoring any other class from the deleted `tests/test_engine_install.py` (`LayoutEmissionFreshInstallTests`, `AwGitignoreLaneTests`, `MachineLocalStatePremiseTests`, `InstallerCommitSetTests`), each its own decision; the `git-filter-repo` history-rewrite guidance in `tools/README.md`, which remains correct and stays; `DECISIONS.md` D119, a dated record of what was decided then.
- Scope-Paths: tools/untrack-workflow-artifacts.py, tools/README.md, tests/test_root_run_scratch_migration.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: xtrwdb
- Blocks-Release: next
- Set: xtrwdb
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: cf7f8z

## Workflow history
- 2026-09-30 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: cf7f8z verified (set xtrwdb, attempt 1).
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-B01..PR-B05 all FIXED; Readiness go-pending-approval

- 2026-09-28 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-B01..PR-B05 all FIXED. Reviewed at HEAD `463e0f25`. THE PLAN'S DIAGNOSIS AND DESIGN ARE CORRECT AND WERE INDEPENDENTLY RE-MEASURED: F-01 reproduces verbatim (record left at the retired path, root `.gitignore` written), F-02 reproduces character-for-character on both action lines with `git log --follow` reaching the pre-migration commit, F-03's coverage gap is total, and F-04/F-05/F-06 all hold (F-10). PR-B01 (HIGH) is the consequential finding: E-01's "take ONLY the class" recipe produces 13 `NameError`s, because the class closes over two module-level helpers (`_install`, `_seed_committed_repo`) the plan never names; review assembled the restoration correctly and measured `13 passed`, and recorded the minimal sufficient import set. PR-B02: E-05 invalidates the premise pending plan `fzueyy` records in its test-exclusion constant, and both plans are unapproved, so the ordering dependency must be reported rather than assumed settled. PR-B03: E-04's falsification needs TWO assertions to fire, not one, and must not be staged by stashing a tracked file in a shared checkout. PR-B04: the gate had no scope fence or approval summary; both added with five negative constraints. PR-B05: the outcome-rule audit result and the dry-run feasibility were pre-measured so the executor is not guessing. Added F-07..F-10. No production code was modified by this review; every probe ran in a throwaway repo under `.aw/state/`, since removed, with `git status --short` empty throughout.
- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `xtrwdb`. Reproduced the item's reported defect by running the tool against a throwaway repo and measured that it leaves the run record at the repo root while writing a root ignore rule for it; measured the replacement `engine.migrate_root_workflow_artifacts` against an identical repo and found it strictly better. Resolved the item's open "WHAT A FIX WOULD DECIDE" question (option b, delegate) from repository evidence rather than deferring it, and found a SECOND defect the item does not name: commit `19313eed` deleted the replacement's entire 13-test coverage class, so this plan restores it.

- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

A user who reaches for the hand-run untrack tool gets the migration the toolkit actually performs today, moving run scratch to `.aw/workflow-artifacts/` with its git history intact and without a root-`.gitignore` rule for a retired path, and the migration function that now backs both the installer and the tool regains the outcome coverage the suite trim deleted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the coverage the delegation will depend on

- [x] E-01 RESTORE THE DELETED MIGRATION COVERAGE AS `tests/test_root_run_scratch_migration.py`. Recover the class with `git show 19313eed^:tests/test_engine_install.py` and take ONLY `RootRunScratchMigrationTests` (it begins at the line `class RootRunScratchMigrationTests(unittest.TestCase):` and is the last class in that file, 13 `def test` methods). Every other class in the recovered file is out of scope per the Scope statement. Restore the class docstring INTACT: it is the design rationale for the assertions, enumerating the five ways "a naive implementation passes while the feature is broken" (history via real `git log --follow` rather than mere file existence; whole path SETS compared so a partial move cannot pass; merge rather than move, since a populated destination is "the common case rather than an edge"; refusal rather than overwrite on a same-path/different-bytes conflict; and "IGNORED IN EFFECT, via real `git check-ignore` attributed to `.aw/.gitignore`"). Follow the `restorecov` precedent (`6vozur` E-01) for the shape of a restoration: prepend a module docstring stating that this is the coverage `19313eed` deleted, which plan restored it, and that it now guards a function with a SECOND caller (this plan's tool). AUDIT EACH RESTORED TEST AGAINST THE OUTCOME RULE before keeping it (`AGENTS.md`: no test may read production source with `inspect`/`ast`/regex, assert caller counts or symbol censuses, or pin docstrings); drop any that fails and RECORD which and why, since a silent omission is indistinguishable from a bug. Fix only what the move requires.

  THE CLASS ALONE DOES NOT RUN, AND THE TWO MISSING PIECES ARE NAMED HERE BECAUSE REVIEW MEASURED THEM (PR-B01, F-07). Taking ONLY the class, as this item originally said, yields 13 ERRORS, all `NameError`. An AST free-variable analysis of the class finds it closes over two MODULE-LEVEL HELPERS defined ABOVE it in the deleted file and mentioned nowhere in this plan: `_install(repo)`, which is a one-line wrapper returning `INS.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)`, and `_seed_committed_repo(base, name)`, which builds a temp repo via `init_repo`, writes a two-line user `.gitignore`, and makes one commit (its docstring explains both choices: the user line proves the installer preserved it, and the commit makes `git status --porcelain` meaningful against an unborn HEAD). CARRY BOTH OVER, docstrings included. THE EXACT WORKING IMPORT SET, measured by review as sufficient and minimal, is `from __future__ import annotations`, `tempfile`, `unittest`, `pathlib.Path`, `from tests.support import SOURCE_WORKFLOWS, git, init_repo`, and `from agent_workflows import engine as INS`. The deleted file also imported `cli as CLI`, `Term`, `mock`, `json`, `stat` and `argparse`; this class references NONE of them, so do not carry them (an unused import is lint noise and implies a dependency that does not exist).

  REVIEW PROVED THE RESTORATION PASSES BEFORE YOU START, so a failure is yours to explain rather than an unknown: assembled exactly as above, `python3 -m pytest <file> -o addopts=""` reports `13 passed` (measured twice, once with the full import set and once with the minimal one). The class also passes the outcome-rule audit E-01 requires: `rg -n "inspect\.|import ast|getsource|__doc__"` over the recovered class returns NOTHING, so all 13 are outcome tests and the expected audit result is "13 kept, 0 dropped". Record it as such; if you drop one, say which and why.
  - Depends on: none
  - Expected outcome: the file exists, imports `engine.migrate_root_workflow_artifacts` (as `INS.migrate_root_workflow_artifacts`), carries `_install` and `_seed_committed_repo`, and its 13 tests pass; the bare suite's test COUNT rises by exactly the number of restored methods plus E-04's.
  - Execution state: performed

### Task group 2: retarget the tool

- [x] E-02 CONVERT THE TOOL INTO A DELEGATING FRONT END. Replace the body of `tools/untrack-workflow-artifacts.py` so it calls `engine.migrate_root_workflow_artifacts(repo_root, use_git=engine.git_available(repo_root), dry_run=not args.apply)` and prints the returned action lines, DELETING the module's own migration logic: the `ARTIFACTS` constant, `IGNORE_COMMENT`, `IGNORE_RULE`, `tracked_paths`, `ignore_is_present`, `append_ignore_rule`, `gitignore_is_clean`, and `acceptable_commit_paths`. Every one of those exists only to serve the retired repo-root path or the root-`.gitignore` write this plan removes. Use the established shim shape rather than inventing one: `install-workflows.py` inserts its own directory on `sys.path` "so the package resolves when this file is run directly from a checkout", prints a one-line `note:` to stderr naming the preferred surface, and delegates; `tools/agy_run.py` does the same from `tools/` with `Path(__file__).resolve().parent.parent`. PRESERVE DRY RUN AS THE DEFAULT, which is the tool's one genuine safety property and is why this is a retarget and not a deletion: `--apply` maps to `dry_run=False` and its absence to `dry_run=True`, a parameter the engine function already documents as "report what WOULD happen and touch nothing". Keep `repository_root()` and `MigrationError` (the CLI contract: exit 2 with `error: ` on stderr when not in a git work tree). Point the deprecation note at `aw install`, which reaches this same migration through `engine.install_into_repo`.
  - Depends on: E-01
  - Expected outcome: the tool relocates run scratch to `.aw/workflow-artifacts/` with history preserved, writes no root `.gitignore`, and still changes nothing without `--apply`.
  - Execution state: performed

- [x] E-03 RESOLVE `--commit` AGAINST THE NEW BACKEND, per OQ-01's recorded decision. The flag cannot survive unchanged: `engine._commit_relocation` ALREADY COMMITS, making its own two path-scoped commits (the rename, then the untrack), so a post-hoc `--commit` would find nothing staged, and its guard `acceptable_commit_paths` is deleted by E-02 anyway. Implement OQ-01's resolution: keep the flag ACCEPTED but make it a no-op that prints a one-line note stating the migration now commits its own path-scoped relocation, so an existing hand-typed invocation or shell history does not start failing with an argparse error. Preserve the existing `--commit` requires `--apply` argparse check, since that relationship still reads correctly.
  - Depends on: E-02
  - Expected outcome: `--apply --commit` behaves exactly as `--apply` plus one explanatory line, and `--commit` alone still errors.
  - Execution state: performed

- [x] E-04 COVER THE DELEGATION ITSELF, in the same file as E-01. Add one class that drives the TOOL as a subprocess with `tests.support.run_tool` (the helper that exists for exactly this: "Run one of the framework's Python tools with args") against a temp repo carrying a tracked repo-root run record. Assert OUTCOMES, not that a function was called: (1) without `--apply` the index and the working tree are BYTE-IDENTICAL afterwards and the retired path still holds the record; (2) with `--apply` the record is at `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` on disk, `git ls-files` no longer lists it at either path, and the retired directory is gone; (3) NO root `.gitignore` is created, which is the backlog item's specific complaint and the one assertion that fails against today's tool; (4) exit 0 in both cases. Include the FALSIFICATION the restorecov review demanded (PR-701): state in the class docstring how the suite was proven to COLLECT these tests, because a file pytest does not collect adds zero tests while the suite still reports green.

  WHICH ASSERTIONS ACTUALLY DISCRIMINATE, measured at review so the falsification V-04 demands is not guesswork. Against TODAY's tool, run in a throwaway repo with one tracked record at `workflow-artifacts/assess/<RUN_ID>/report.md`, `--apply` leaves the record AT THE RETIRED PATH and creates a root `.gitignore` containing `workflow-artifacts/`. So assertions (2) and (3) BOTH fail against the old tool, which is what makes them the falsification, while (1) and (4) PASS against both tools and are regression guards rather than discriminators. Say which is which in the class docstring; a reviewer cannot otherwise tell a guard from a proof. NOTE for assertion (2): the `git ls-files` check must assert the record is tracked at NEITHER path, because the old tool also untracks it (at the retired path), so "not tracked at the retired path" alone passes against both.

  THE DRY-RUN CASE (1) IS VERIFIED PERFORMABLE: review measured that `dry_run=True` leaves HEAD unchanged, `git status --porcelain` empty, and the record still at the retired path, so a byte-identical index-and-worktree assertion is achievable rather than aspirational.
  - Depends on: E-03
  - Expected outcome: four outcome assertions, of which (2) and (3) fail against the pre-E-02 tool and all four pass after it.
  - Execution state: performed

### Task group 3: stop recommending the wrong remediation

- [x] E-05 REWRITE THE `tools/README.md` SECTION. Its heading `## \`untrack-workflow-artifacts.py\`` and its five occurrences of the bare retired path currently teach the retired layout, and its "Remediation Option A: Index-Only Stop Tracking (Recommended)" recommends the behavior this plan removes. State that the tool now delegates to the toolkit's run-scratch migration, that run scratch lives at `.aw/workflow-artifacts/` (ignored by the framework-owned `.aw/.gitignore`), that the dry run remains the default, and that `aw install` performs the same migration. KEEP the `git filter-repo` guidance and its destructive-action warning unchanged: that guidance is about purging already-committed history, is still correct, and D121/F4 deliberately hardened it into a consent absolute. CROSS-PLAN ORDERING OBLIGATION, WHICH IS NOT SETTLED AND MUST NOT BE ASSUMED (sharpened at review, PR-B02, F-08). Pending plan `fzueyy` declares this file OUT of its scope precisely because "the tool's SUBJECT is the retired path". That premise was true while the tool targeted the retired path and this E-item makes it FALSE. `fzueyy` is `- Status: to-review` (unapproved, reviewed in this same sweep), and its E-04 requires `tools/README.md` be excluded from its restored run-scratch path guard by a NAMED CONSTANT carrying that now-obsolete reason. So the two plans have a real ORDERING DEPENDENCY that neither declares, and WHICHEVER LANDS SECOND MUST RECONCILE. Concretely: if `fzueyy` executes first, its guard ships with an exclusion whose stated reason this E-item invalidates, and this E-item's executor must then either remove `tools/README.md` from that exclusion constant (making the rewritten section guard-clean, which after E-05 it should be) or record in this plan's workflow history why the exclusion still stands. If THIS plan executes first, `fzueyy`'s executor must not copy the stale reason forward. DO NOT edit `tests/test_run_scratch_path_guard.py` from here: it is not in `- Scope-Paths:` and does not exist yet. REPORT the reconciliation need to the human instead, since resolving a dependency between two unapproved plans is a scheduling decision and not an executor's to make.
  - Depends on: E-02
  - Expected outcome: the section describes the delegating tool and the live path, with the history-rewrite warning intact, and the cross-plan reconciliation with `fzueyy` is either performed (if that plan already landed) or REPORTED as outstanding.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE RUN-SCRATCH HOME IS SETTLED AND THIS PLAN DOES NOT RE-DECIDE IT. `engine.ARTIFACTS_DIR` is `".aw/workflow-artifacts/"`, and the comment above it instructs "Do NOT point it back at the repo root; the repo-root path is retired, and `tools/untrack-workflow-artifacts.py` remains available for a user who wants only to untrack an existing one." That sentence is the deferral this plan closes.
- `engine.RETIRED_ROOT_ARTIFACTS_DIR` is `"workflow-artifacts/"` and is "deliberately a separate constant from LEGACY_ARTIFACTS_DIR", so the retired path already has a single named home in the package. The tool's own `ARTIFACTS` constant is a duplicate of it.
- A REPO-ROOT `.gitignore` IS NOT THE FRAMEWORK'S TO WRITE FOR THIS TREE, which is why delegation removes a real violation rather than merely changing a path. `engine.py`'s module docstring states the installer "Does NOT silently edit user gitignores", and executed plan `vh14ku`'s OQ resolution records that `.aw/.gitignore` patterns are `.aw/`-relative so it "CANNOT express a repo-root path at all, and reaching outside `.aw/` would mean editing the user's own root `.gitignore`, which this installer explicitly does not do".
- THE PROTECTING RULE IS ANCHORED AND FRAMEWORK-OWNED. `_ensure_aw_gitignore` back-fills `/workflow-artifacts/` into `.aw/.gitignore`, "ANCHORED (`/workflow-artifacts/`), never a bare `workflow-artifacts/`", and measured live in this worktree: `git check-ignore -v --no-index -- .aw/workflow-artifacts/probe` prints `.aw/.gitignore:75:/workflow-artifacts/`.
- DELEGATING-SHIM PRECEDENT EXISTS TWICE, so E-02 copies a shape rather than inventing one: `install-workflows.py` ("DEPRECATED shim: use the `agent-workflows` / `aw` CLI instead", `sys.path.insert` then `return engine.main()`) and `tools/agy_run.py` ("It contains NO tool logic", same `sys.path` dodge). Six files under `tools/` already import the package.
- RESTORATION PRECEDENT AND ITS FALSIFICATION BAR: `restorecov` (`6vozur`, `dmxc5h`) restored classes deleted by this same commit `19313eed`. Its review (PR-701) established that "a filename pytest does not collect adds zero tests while the suite still reports green", so a restoration must prove a test COUNT delta, not merely that the file passes when named directly.
- RUN THE SUITE BARE as `python3 -m pytest` (`AGENTS.md`): `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, and a second `-q` would suppress the `N passed` summary this plan's validation requires.
- `tests/support.run_tool` exists for driving a `tools/` script as a subprocess, and `init_repo`/`git` cover temp-repo setup; the deleted test file used these same helpers.
- A RECOVERED TEST CLASS USUALLY CLOSES OVER MODULE-LEVEL HELPERS, so "take only the class" is never a complete recipe (added at review, F-07). Run an AST free-variable pass over the recovered class and carry every non-import free name it reports. For this restoration those are `_install` and `_seed_committed_repo`, and the plan's original recipe omitted both, which would have produced 13 `NameError`s. Carry only the imports the class actually uses; the deleted file's other six are unused here.

## Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | MEDIUM | THE TOOL LEAVES THE RUN RECORD AT THE RETIRED PATH AND BLESSES IT. Run against a temp repo with one tracked record at `workflow-artifacts/assess/20260101-000000/report.md`, `--apply` prints `Removed 1 tracked path(s) from the Git index; local files were retained.` and `Added and staged the workflow-artifacts/ ignore rule.` Afterwards the record is STILL at the repo root, and the root `.gitignore` (newly created) contains `workflow-artifacts/`. This is the item's report, reproduced. | Measured 2026-09-28 in a throwaway repo; `git ls-files` afterwards returns `.gitignore` and `README.md`, and `cat .gitignore` shows the added rule |
| F-02 | MEDIUM | THE REPLACEMENT IS STRICTLY BETTER ON THE SAME INPUT, which is what makes delegation the right fix rather than retargeting the constant. `engine.migrate_root_workflow_artifacts` on an identical repo relocates the record to `.aw/workflow-artifacts/...` "[migrated with `git mv` (history preserved, committed), then untracked ...; file kept on disk]", removes the now-empty retired directory, and creates NO root `.gitignore`. | Measured 2026-09-28 by calling the function directly; both action lines captured, and `ls .gitignore` afterwards reports no such file |
| F-03 | MEDIUM | THE FUNCTION THIS PLAN DELEGATES TO HAS ZERO TESTS, and this is NOT in the backlog item. `19313eed` deleted `tests/test_engine_install.py` whole, including `RootRunScratchMigrationTests` (13 test methods) whose docstring calls its proof obligation "UNUSUALLY HIGH" because the function "is the only child that touches a user's committed history". | `grep -rn "migrate_root_workflow_artifacts\|RETIRED_ROOT_ARTIFACTS_DIR" tests/` returns nothing; `ls tests/test_engine_install.py` reports no such file; `git show 19313eed^:tests/test_engine_install.py` still yields the class |
| F-04 | LOW | THE ITEM'S "NO CALLER" CLAIM IS STILL TRUE, AND IT BOUNDS THE BLAST RADIUS. Nothing in `agent_workflows/` invokes the tool; the single package mention is the `engine.py` comment that keeps it "available for a user who wants only to untrack". The tool is also NOT SHIPPED: the wheel packages only `agent_workflows`, and the sdist include-list does not carry `tools/`, so no installed user can reach this script at all. Both facts are why this stays `low` priority. | Re-verified 2026-09-28: `grep -rn untrack_workflow_artifacts agent_workflows/ tools/ tests/` returns only that comment; `pyproject.toml` `[tool.hatch.build.targets.wheel] packages = ["agent_workflows"]` and the sdist `include` list omits `tools` |
| F-05 | LOW | `tools/README.md` ADVERTISES THE WRONG REMEDIATION AS RECOMMENDED, so the defect is reachable through documentation and not only by reading the script: "Remediation Option A: Index-Only Stop Tracking (Recommended): Use `python3 tools/untrack-workflow-artifacts.py --apply` to stop tracking future changes and keep local files." | `tools/README.md`, section `## \`untrack-workflow-artifacts.py\``; 5 bare occurrences of the retired path in that section |
| F-06 | LOW | A DELEGATING TOOL INHERITS ONE HONEST LIMIT, recorded so review does not mistake it for a regression this plan introduces: in a repo with NO `.aw/.gitignore`, the migration relocates and untracks correctly but the destination is not yet ignored, so the files show as `?? .aw/`. The installer does not hit this because `install_into_repo` runs the migration alongside `_ensure_aw_gitignore`; measured on the real installer, a first `aw install` reports `.aw/workflow-artifacts/ is NOT ignored (... re-run \`aw install\`)` and a second reports `is ignored by .aw/.gitignore (correct...)`. The relocated bytes are never lost or committed in either case, so this is a pre-existing property of the engine function (explicitly OUT of scope) and strictly better than today's tool, which leaves the record tracked-then-untracked at a retired path. | Measured 2026-09-28: direct call into a repo with no `.aw/.gitignore` leaves `?? .aw/` and `git check-ignore` exit 1; the real installer's two successive runs produce the two summary lines quoted |

| F-07 | HIGH | **ADDED AT REVIEW (PR-B01). E-01's RESTORATION RECIPE IS INCOMPLETE AND PRODUCES 13 ERRORS AS WRITTEN.** Taking "ONLY `RootRunScratchMigrationTests`" and adding imports yields `NameError: name '_seed_committed_repo' is not defined` on every test. An AST free-variable analysis of the recovered class reports it closes over `['INS', 'Path', '_install', '_seed_committed_repo', 'git', 'tempfile', 'unittest']`: the last two of those non-import names are MODULE-LEVEL HELPERS defined above the class in the deleted file and named nowhere in this plan. With both carried over, the class passes `13 passed`. Review also determined the MINIMAL sufficient import set (six lines; the deleted file's `CLI`, `Term`, `mock`, `json`, `stat`, `argparse` imports are unused by this class). | An AST free-variable pass over the recovered class printing the seven names; a first assembly with the class plus imports alone giving `13 failed` all `NameError`; a second assembly adding `_install` and `_seed_committed_repo` giving `13 passed in 30.19s`; a third with only the six minimal imports giving `13 passed in 61.79s`; the two helper bodies read from `git show 19313eed^:tests/test_engine_install.py` |
| F-08 | MEDIUM | **ADDED AT REVIEW (PR-B02). E-05 WOULD INVALIDATE A PREMISE PENDING PLAN `fzueyy` RELIES ON, AND BOTH PLANS ARE UNREVIEWED IN THE SAME SWEEP.** `fzueyy` (`- Status: to-review`) excludes `tools/README.md` from its restored run-scratch path guard, and its E-04 requires that exclusion be "a named constant with a one-line reason each", the reason being that the README "documents `tools/untrack-workflow-artifacts.py`, a migration tool whose subject IS the retired path". E-05 of THIS plan removes exactly that property: after the rewrite the README documents a tool that targets `.aw/workflow-artifacts/`, so `fzueyy`'s recorded reason becomes false and its exclusion becomes an unjustified hole in a guard whose whole point is to catch bare retired-path references. This plan already notes the interaction in E-05's reviewer note, which is good, but states it as settled ("that is why this plan, not that one, owns this section") when the actual consequence is an ORDERING DEPENDENCY between two unapproved plans that neither declares: whichever lands second must reconcile. Neither may assume the other's outcome. | `.aw/records/plans/pending/20260928-wfartgrowth-01-fzueyy-...ipd.md` read: `- Status: to-review`, its `- Scope-Paths:` omitting `tools/README.md`, its OUT clause and E-04 exclusion reason quoted verbatim; this plan's E-05 reviewer note |
| F-09 | LOW | **ADDED AT REVIEW (PR-B03). THE SUITE BASELINE IS NOT STATED ANYWHERE IN THIS PLAN, WHICH IS THE RIGHT CHOICE AND IS WORTH CONFIRMING RATHER THAN LEAVING AMBIGUOUS.** Unlike its sibling plans in this sweep, this plan asks the executor to "Record the pre-change baseline count first" and transcribes NO number, so nothing here can go stale. Review measured the current figure for context only: `3217 passed, 2 skipped, 3 warnings in 53.42s` at HEAD `463e0f25`. Stated so the executor can sanity-check their own baseline against a same-week reading without the plan acquiring a bar that drifts. | review's clean-tree bare `python3 -m pytest` -> `3217 passed, 2 skipped, 3 warnings in 53.42s` at HEAD `463e0f25`; the plan's Required-tests wording containing no transcribed total |
| F-10 | LOW | **ADDED AT REVIEW. EVERY OTHER CLAIM IN THIS PLAN REPRODUCED AT HEAD `463e0f25`.** F-01 reproduces verbatim in a throwaway repo, including both quoted output lines, `git ls-files` returning `.gitignore` plus `README.md`, the record still present at the retired path, and the root `.gitignore` gaining the rule under the quoted comment. F-02 reproduces verbatim, including BOTH action lines character-for-character, no root `.gitignore` created, the bytes at the new path, and the retired directory removed; `git log --follow` on the new path reaches the pre-migration `init` commit through the engine's two relocation commits. F-03 reproduces (`rg` over `tests/` returns nothing, the file is absent, the class recovers from `19313eed^` with 13 `def test` methods and is the LAST class). F-04 reproduces (no caller in `agent_workflows/` beyond the one comment; the wheel packages only `agent_workflows` and the sdist `include` list omits `tools/`). F-05 reproduces (the heading, the "Recommended" line, and five bare occurrences). F-06 reproduces exactly (`?? .aw/` and `git check-ignore` exit 1 in a repo with no `.aw/.gitignore`). E-02's every named deletion target exists in the tool; E-02's exact call shape is valid against the shipped signature `migrate_root_workflow_artifacts(repo_root, *, use_git, dry_run=False)`; E-03's two-commit premise is verbatim in `_commit_relocation`'s docstring and observable in `git log --oneline`; the dry run touches nothing (HEAD unchanged, `git status --porcelain` empty, record still at the retired path); both shim precedents read as described; and `tests.support.run_tool` exists with the quoted docstring. | the probes named per finding, each in its own throwaway repo under `.aw/state/`, all removed afterwards; `git status --short` empty before and after |

## Proposed changes (ordered, validatable)

1. E-01 restores `RootRunScratchMigrationTests` as `tests/test_root_run_scratch_migration.py`, so the function E-02 delegates to is covered BEFORE it acquires a second caller.
2. E-02 replaces the tool's migration logic with a delegating call to `engine.migrate_root_workflow_artifacts`, deleting the retired-path constant and the root-`.gitignore` write, and preserving dry-run-by-default via `dry_run=`.
3. E-03 makes `--commit` an accepted no-op with an explanatory line, because the engine backend already makes its own path-scoped commits.
4. E-04 adds subprocess-level outcome coverage of the tool itself, including the "no root `.gitignore`" assertion that is the item's specific complaint.
5. E-05 rewrites the `tools/README.md` section, keeping the history-rewrite warning intact.

## Deferred / out of scope (with reason)

- `engine.migrate_root_workflow_artifacts` ITSELF. It is `executed` (plan `y4pptx`), was measured correct here on three inputs, and this plan only gains it a caller and tests. Changing it would put a user's committed history in scope for a `low` priority cleanup.
  - Carrier-Declined: Nothing is owed. This row records a PROHIBITION on this plan rather than outstanding work: the function is measured correct on all three inputs exercised here (tracked-with-ignore, tracked-without-ignore, and via the real installer), so naming a carrier would assert a defect that does not exist.
- THE `.aw/.gitignore`-ABSENT CASE (F-06). A caller-side back-fill would mean the hand-run tool writing framework files, which is `aw install`'s job; the engine function's contract is the migration alone. Recorded as a limit, not fixed.
  - Carrier-Declined: Nothing is owed, and this is a pre-existing property of an `executed` function rather than a defect this plan's fix leaves behind. No bytes are lost or committed in this case: the files are relocated and untracked, merely not yet ignored, and the very next `aw install` adds the rule (measured: first run reports NOT ignored, second reports ignored). A carrier would assert outstanding work where the correct remedy is already a shipped command.
- `ARCHITECTURE.md` AND `CONTRIBUTING.md` path references. Pending plan `fzueyy` (`wfartgrowth-01`) already declares both in its `- Scope-Paths:` and owns the run-scratch path guard. Touching them here would collide with a plan awaiting review.
  - Carrier: fzueyy
- EVERY OTHER CLASS IN THE DELETED `tests/test_engine_install.py` (`LayoutEmissionFreshInstallTests`, `LayoutEmissionSiteTests`, `AwGitignoreLaneTests`, `MachineLocalStatePremiseTests`, `InstallerCommitSetTests`). Each restoration is its own decision with its own audit, exactly as `restorecov` treated them one file per plan.
  - Carrier-Declined: DELIBERATELY UNCARRIED, and stated plainly rather than hidden behind a handoff this plan is not entitled to make. These classes cover installer surfaces this plan does not touch, and whether each is worth restoring is a judgement about the suite trim `19313eed` as a whole, not about this defect; `restorecov` set the precedent that each deleted file is its own plan with its own outcome audit. Filing a blanket carrier for four unexamined classes would assert a scope decision nobody has made. A maintainer who wants them restored should file the item against the trim, where the denominator is visible.
- THE `git filter-repo` REMEDIATION GUIDANCE in `tools/README.md`. It concerns purging already-committed history, is still correct after this change, and its destructive-action framing was deliberately hardened (D121 F4). Kept verbatim.
  - Carrier-Declined: There is nothing to carry. This row records a PROHIBITION (do not touch that guidance) rather than outstanding work; the guidance is correct as it stands, and V-05 asserts it survived the rewrite.
- `DECISIONS.md` D119 and `CHANGELOG.md`. Dated historical records where a past entry legitimately describes the tool as it then behaved; rewriting them would falsify the record.
  - Carrier-Declined: Nothing is owed. Leaving a dated record intact is the CORRECT terminal state, not deferred work: D119 accurately records what was decided on 2026-07-27, and editing it would falsify history rather than discharge an obligation.
- RETIRING THE TOOL OUTRIGHT (the item's option c). Rejected with a reason, see OQ-02: it would discard the dry-run-by-default preview, which has no equivalent on the `aw install` path.
  - Carrier-Declined: Nothing is owed, because this is a rejected design ALTERNATIVE rather than an outstanding defect. E-02 leaves the tool correct and the backlog item satisfied; OQ-02 records the maintainer's cheap override (delete the file and the README section) and states that E-01's restored coverage stands under either outcome, so no work is left unowned by this choice.

## Scope check

- Over-scope: none. Each of the three declared paths is required by an E-item: the tool (E-02, E-03), its README section (E-05), and the restored test file (E-01, E-04).
- Under-scope: the run-scratch path references in `ARCHITECTURE.md` and `CONTRIBUTING.md` are NOT fixed here (pending plan `fzueyy` owns them). The `.aw/.gitignore`-absent limit (F-06) is recorded and not remedied. No other deleted test class is restored. Nothing is changed in `agent_workflows/`, so no shipped behavior moves: this plan touches a hand-run script, its docs, and tests.

## Required tests / validation

- `python3 -m pytest` BARE, per `AGENTS.md`, with the `N passed` summary pasted. Record the pre-change baseline count first, because E-01 and E-04 must be shown to ADD tests (restorecov PR-701: a file pytest never collects adds zero tests while the suite still reports green). THIS PLAN DELIBERATELY TRANSCRIBES NO TOTAL, so nothing here can go stale; for a same-week sanity check only, review measured `3217 passed, 2 skipped, 3 warnings in 53.42s` at HEAD `463e0f25` (F-09). Compare against YOUR OWN baseline, not that figure.
- `python3 -m pytest tests/test_root_run_scratch_migration.py` for the focused file, with output pasted.
- THE FALSIFICATION E-04 EXISTS TO PROVIDE: run the new delegation test against the PRE-E-02 tool and paste the FAILURE. TWO assertions must fire, not one (measured at review): the "no root `.gitignore`" assertion AND the "record is at the new path / tracked at neither path" assertion, because today's tool both leaves the record at the retired path and writes the root ignore rule. Assertions (1) and (4) pass against both tools and are regression guards, not proofs; say so. DO NOT STAGE THIS BY `git stash`-ING A TRACKED FILE: this is a shared checkout and a stash-then-restore spanning a minute-long run can discard a co-worker's concurrent edit to `tools/untrack-workflow-artifacts.py`. Run the test at the parent commit in a separate worktree, or copy the pre-change tool to a scratch path and point `run_tool` at that copy. Paste `git status --short` before and after.
- MEASURE THE TOOL END-TO-END BY HAND in a throwaway repo carrying a tracked repo-root run record, and paste: the dry-run output plus proof nothing changed; the `--apply` output; `git ls-files` afterwards; `find .aw/workflow-artifacts -type f`; `ls .gitignore` showing no root ignore file was created; and `git log --follow -- <new path>` reaching the pre-migration commit.
- `aw sanitize --agent` clean, since the pasted evidence above involves absolute temp paths that must not enter a tracked artifact.
- `aw ipd lint` conforming for this plan.

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and that is measured rather than assumed. Spec `20260817-2124-01` (`u7xtni`, Order 07, `implemented`) already RULES that run scratch lives at `.aw/workflow-artifacts/`; this plan brings a hand-run tool into line with a contract that is already correct, so there is no contract to change. No `.spec.md` file appears in `- Scope-Paths:`, which is what the runners' spec-edit announcement and the finalize scope gate reconcile against.
- `tools/README.md` IS the documentation deliverable (E-05) and is declared in `- Scope-Paths:`.
- NO `DECISIONS.md` ENTRY IS ADDED. D119 recorded adopting the tool in its original form and remains an accurate record of that decision; this plan's rationale lives in the plan, and the `engine.py` comment that deferred this change is the thing being closed.

## Open questions

### OQ-01: What becomes of `--commit` once the engine backend makes its own commits?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence; E-03 implements it. The flag cannot survive unchanged, because `engine._commit_relocation` already performs TWO path-scoped commits (the rename, then the untrack) and its docstring records why the split is "load-bearing rather than fussy": a `git mv` and a `git rm --cached` against one index state leave the rename in NO commit, so `git log --follow` cannot reach the pre-migration history. A post-hoc `--commit` would therefore find nothing to commit, and its guard `acceptable_commit_paths` is deleted by E-02 in any case. Of the three options (remove the flag; keep it as a no-op with a note; keep it meaning "also commit anything left staged"), the third is REFUSED outright: committing whatever a shared checkout happens to have staged is exactly the `git add -A`-shaped hazard `AGENTS.md` forbids, and `_commit_paths` is already written to avoid it ("ALWAYS PATH-SCOPED, never `git add -A` and never a bare `git commit`, so a co-worker's ... unrelated STAGED work in this shared checkout is not swept in"). Between the first two, the no-op is chosen so an existing hand-typed invocation does not begin failing with an argparse error; this matches how `install-workflows.py` keeps parsing "the same historical flags" while delegating. NOT BLOCKING: nothing else in the plan depends on which of those two is picked.

### OQ-02: Should the tool be retired with a pointer to `aw install` instead of retargeted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as RETARGET (the item's option b), not retire (option c), on one measured property: the tool is DRY RUN BY DEFAULT and `aw install` has no equivalent. A user who wants to see what a migration WOULD do to their committed run records can run this script and get the engine function's `dry_run=True` action lines while touching nothing, whereas the `aw install` path performs the install. The engine function already exposes the parameter, so preserving that affordance costs one argument and no duplicated logic, and `engine.py`'s own comment anticipates exactly this user ("available for a user who wants only to untrack an existing one"). Retirement also has a cost the item does not weigh: the script is the only entry point that does the migration WITHOUT installing framework files into the repo. THE HONEST LIMIT, recorded so a maintainer can overrule cheaply: the tool is not shipped (F-04, the wheel packages only `agent_workflows` and the sdist omits `tools/`), so its audience is people working in a checkout of this repository. A maintainer who judges that audience too small to maintain a front end for can delete the file and the README section instead, which would satisfy the backlog item equally; that is a scope call for them, and it does not change E-01, whose restored coverage is needed either way. NOT BLOCKING: E-01 stands under either outcome.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `python3 -m pytest tests/test_root_run_scratch_migration.py` output pasted showing every restored test passing (expected: `13 passed`, which review measured on an assembled restoration), AND the bare-suite COUNT delta: the `N passed` line from before the change and after, whose difference equals the number of restored methods plus E-04's (restorecov PR-701, since an uncollected file adds zero tests while the suite still reports green). Paste the audit result required by E-01: the list of restored tests kept and, for any dropped, which and why under the outcome rule; review measured the expected result as 13 kept and 0 dropped, since `rg -n "inspect\.|import ast|getsource|__doc__"` over the recovered class returns nothing. CONFIRM THE TWO MODULE-LEVEL HELPERS WERE CARRIED (added at review, F-07) by quoting `_install` and `_seed_committed_repo` from the new file, and state that the class does not run without them; a restoration missing either FAILS V-01, because review measured that shape producing 13 `NameError`s. Quote the restored class docstring's five-point rationale to show it survived, and show the new module docstring naming `19313eed` and this plan.
  - Observed evidence: PASS. Restored test suite, count delta verification, and outcome audit details below:
    Restored test file run output (`python3 -m pytest tests/test_root_run_scratch_migration.py -o addopts=""`):
    ```
    ============================= 17 passed in 31.65s ==============================
    ```
    (13 restored `RootRunScratchMigrationTests` + 4 delegation tests all passing).

    Bare-suite test count delta:
    Pre-change baseline: `3291 passed, 2 skipped, 3 warnings in 139.16s (0:02:19)`
    Post-change suite:   `3308 passed, 2 skipped, 3 warnings in 59.20s`
    Delta: 3308 - 3291 = +17 passed, exactly matching the 13 restored test methods + 4 E-04 delegation methods.

    Outcome-rule audit result:
    `rg -n "inspect\.|import ast|getsource|__doc__"` returned 0 matches over `RootRunScratchMigrationTests`.
    13 kept, 0 dropped:
      1. test_every_destination_state_gets_the_right_disposition
      2. test_tracked_run_records_are_relocated_with_history_preserved
      3. test_nothing_is_lost_the_path_sets_are_equal_modulo_the_prefix
      4. test_an_already_populated_destination_is_MERGED_not_replaced
      5. test_untracked_content_is_moved_without_git
      6. test_the_readme_only_case_is_removed_not_relocated
      7. test_a_repo_with_no_retired_directory_is_a_silent_no_op
      8. test_dry_run_reports_and_touches_nothing
      9. test_the_migration_commit_does_not_sweep_in_unrelated_staged_work
      10. test_run_records_in_a_records_quarantine_lane_are_REPORTED_not_moved
      11. test_an_ordinary_wip_file_in_a_quarantine_lane_is_silent
      12. test_the_migration_runs_from_the_shared_install_chokepoint
      13. test_reinstall_is_idempotent

    Carried module-level helpers confirmed from `tests/test_root_run_scratch_migration.py`:
    ```python
    def _install(repo: Path) -> dict:
        """Run the shared install core the way every entry point does."""

        return INS.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)


    def _seed_committed_repo(base: Path, name: str) -> Path:
        """A temporary git repo with one commit and a pre-existing user line in the root `.gitignore`.

        The user line exists so a test can prove the installer PRESERVED it while adding its own managed
        block, and the commit exists so `git status --porcelain` is meaningful (an unborn HEAD reports
        everything as untracked regardless of the ignore rules).
        """

        repo = init_repo(base / name)
        (repo / ".gitignore").write_text(
            "# user's own line\n*.user-tmp\n", encoding="utf-8"
        )
        git(repo, "add", ".gitignore")
        git(repo, "commit", "-qm", "seed")
        return repo
    ```
    AST symbol table analysis verifies the class closes over `_install` and `_seed_committed_repo` and fails with 13 `NameError`s if either is omitted.

    Restored class docstring five-point rationale quoted intact:
    ```
    THE PROOF OBLIGATION IS UNUSUALLY HIGH, so each assertion below is chosen against a specific way
    a naive implementation passes while the feature is broken:

    1. HISTORY, not merely location. Asserting the file exists at the new path passes for a
       copy-and-delete that lost the history. So the tracked case asserts the ACTUAL
       `git log --follow` output reaches the pre-migration commit.
    2. NOTHING LOST, not one file checked. A test that checks a single file cannot catch a partial
       move, so the before/after run-record path SETS are compared for equality modulo the prefix.
    3. MERGE, not move (F-7). The destination is usually already populated, which is the common case
       rather than an edge, so a pre-existing destination run must SURVIVE alongside the relocated
       one.
    4. REFUSAL, not overwrite. A same-path/different-bytes conflict must leave BOTH files in place.
    5. IGNORED IN EFFECT, via real `git check-ignore` attributed to `.aw/.gitignore`.
    ```

    New module docstring naming `19313eed` and plan `cf7f8z`:
    ```python
    """Restored coverage for root workflow-artifacts run scratch migration.

    This is the outcome coverage deleted by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"),
    restored under plan `cf7f8z` (Set `xtrwdb`). It guards `engine.migrate_root_workflow_artifacts`,
    which is the only code in the framework touching a user's committed history.
    ...
    """
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the tool run by hand in a throwaway repo holding a tracked `workflow-artifacts/<wf>/<RUN_ID>/report.md`. Paste: the `--apply` output showing the engine's `-> .aw/workflow-artifacts/...` action line; `git ls-files` proving the record is tracked at NEITHER path; `find .aw/workflow-artifacts -type f` proving the bytes are at the new path; `ls .gitignore` proving NO root ignore file was created (the backlog item's specific complaint); and `git log --follow -- .aw/workflow-artifacts/<wf>/<RUN_ID>/report.md` reaching the pre-migration commit. Also paste a `grep -n "ARTIFACTS\|IGNORE_RULE\|append_ignore_rule" tools/untrack-workflow-artifacts.py` returning nothing, proving the retired-path logic is gone rather than merely bypassed. Sanitize absolute paths before pasting.
  - Observed evidence: PASS. Manual end-to-end relocation and untracking evidence:
    Manual end-to-end run in throwaway git repo holding tracked `workflow-artifacts/assess/20260101-000000/report.md`:
    Output of `tools/untrack-workflow-artifacts.py --apply`:
    ```
    workflow-artifacts/assess/20260101-000000/report.md -> .aw/workflow-artifacts/assess/20260101-000000/report.md [migrated with git mv (history preserved, committed), then untracked so the .aw/.gitignore rule governs it; file kept on disk]
    workflow-artifacts/ [removed: now empty; run scratch lives at .aw/workflow-artifacts/]
    ```
    `git ls-files` output:
    ```
    README.md
    ```
    (proves the run record is tracked at NEITHER path).

    `find .aw/workflow-artifacts -type f` output:
    ```
    .aw/workflow-artifacts/assess/20260101-000000/report.md
    ```

    `ls -la .gitignore` output:
    ```
    ls: cannot access '.gitignore': No such file or directory
    ```
    (exit code 2; proves NO root ignore file was created).

    `git log --follow --oneline -- .aw/workflow-artifacts/assess/20260101-000000/report.md` output:
    ```
    4ce789f agent-workflows: untrack 1 relocated run-scratch record (D92)
    c8ded0d agent-workflows: relocate 1 run-scratch record to .aw/workflow-artifacts/
    fc03d0f initial commit with tracked record
    ```
    (reaches pre-migration commit `fc03d0f`).

    Retired-path logic audit:
    `grep -n "ARTIFACTS\|IGNORE_RULE\|append_ignore_rule" tools/untrack-workflow-artifacts.py`
    returned nothing (exit code 1).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: `--apply --commit` output in a temp repo showing the same migration plus the explanatory note and exit 0, alongside `git log --oneline` showing the engine's own two relocation commits and NO third commit from the tool. Plus `--commit` without `--apply` still exiting nonzero with the argparse error, output pasted.
  - Observed evidence: PASS. Flag handling and commit verification evidence:
    `tools/untrack-workflow-artifacts.py --apply --commit` output:
    ```
    workflow-artifacts/assess/20260101-000000/report.md -> .aw/workflow-artifacts/assess/20260101-000000/report.md [migrated with git mv (history preserved, committed), then untracked so the .aw/.gitignore rule governs it; file kept on disk]
    workflow-artifacts/ [removed: now empty; run scratch lives at .aw/workflow-artifacts/]
    note: --commit is a no-op; the migration now commits its own path-scoped relocation.
    ```
    Exit code: 0.

    `git log --oneline` output:
    ```
    4ce789f agent-workflows: untrack 1 relocated run-scratch record (D92)
    c8ded0d agent-workflows: relocate 1 run-scratch record to .aw/workflow-artifacts/
    fc03d0f initial commit with tracked record
    ```
    (shows engine's two path-scoped relocation commits and NO third commit from the tool).

    `tools/untrack-workflow-artifacts.py --commit` (without `--apply`) output:
    ```
    usage: untrack-workflow-artifacts.py [-h] [--apply] [--commit]
    untrack-workflow-artifacts.py: error: --commit requires --apply
    ```
    Exit code: 2.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: the delegation tests passing after the change, AND the FALSIFICATION: the same tests run against the pre-E-02 tool with the FAILURE pasted, naming EACH assertion that fired. TWO must fire (measured at review): the root-`.gitignore` assertion and the new-path/tracked-at-neither-path assertion. State explicitly which assertions are DISCRIMINATORS and which are regression guards that pass against both tools (the dry-run and exit-code assertions are the latter), because presenting a guard as a proof would overstate the evidence. Paste the dry-run case's proof that the index and working tree were unchanged. STATE THE METHOD used to reach the pre-change tool and confirm it did not `git stash` a tracked file in this shared checkout, with `git status --short` pasted before and after. State in the evidence how collection was proven (the count delta from V-01), not merely that the file passes when named directly.
  - Observed evidence: PASS. Delegation suite execution and falsification evidence:
    (1) Delegation tests passing after change (`python3 -m pytest tests/test_root_run_scratch_migration.py -k UntrackWorkflowArtifactsDelegationTests`):
    ```
    tests/test_root_run_scratch_migration.py::UntrackWorkflowArtifactsDelegationTests::test_both_modes_exit_zero PASSED [ 25%]
    tests/test_root_run_scratch_migration.py::UntrackWorkflowArtifactsDelegationTests::test_apply_relocates_record_to_aw_and_untracks_both_paths PASSED [ 50%]
    tests/test_root_run_scratch_migration.py::UntrackWorkflowArtifactsDelegationTests::test_apply_creates_no_root_gitignore PASSED [ 75%]
    tests/test_root_run_scratch_migration.py::UntrackWorkflowArtifactsDelegationTests::test_dry_run_leaves_index_and_worktree_byte_identical PASSED [100%]
    ```

    (2) Falsification run against pre-E-02 tool:
    Executed before modifying `tools/untrack-workflow-artifacts.py`, driving the unmodified checked-out script directly.
    Method confirmation: No `git stash` or branch manipulation in this shared checkout.
    `git status --short` before falsification run:
    ```
    ?? tests/test_root_run_scratch_migration.py
    ```
    `git status --short` after falsification run:
    ```
    ?? tests/test_root_run_scratch_migration.py
    ```
    Pasted falsification failure output:
    ```
    =================================== FAILURES ===================================
    _ UntrackWorkflowArtifactsDelegationTests.test_apply_creates_no_root_gitignore _
        def test_apply_creates_no_root_gitignore(self) -> None:
            repo, _ = self._seed_repo_with_tracked_artifact("apply-no-gitignore-repo")
            proc = run_tool(self.TOOL, "--apply", cwd=repo)
            self.assertEqual(proc.returncode, 0, f"tool failed: {proc.stderr}")
    >       self.assertFalse((repo / ".gitignore").exists(), "root .gitignore was created")
    E       AssertionError: True is not false : root .gitignore was created

    _ UntrackWorkflowArtifactsDelegationTests.test_apply_relocates_record_to_aw_and_untracks_both_paths _
        def test_apply_relocates_record_to_aw_and_untracks_both_paths(self) -> None:
            repo, _ = self._seed_repo_with_tracked_artifact("apply-reloc-repo")
            proc = run_tool(self.TOOL, "--apply", cwd=repo)
            self.assertEqual(proc.returncode, 0, f"tool failed: {proc.stderr}")
            new_record = repo / self.REL_NEW_RECORD
    >       self.assertTrue(new_record.is_file(), f"relocated file missing: {new_record}")
    E       AssertionError: False is not true : relocated file missing: <temp-repo>/.aw/workflow-artifacts/assess/20260101-000000/report.md

    =========================== short test summary info ============================
    FAILED tests/test_root_run_scratch_migration.py::UntrackWorkflowArtifactsDelegationTests::test_apply_creates_no_root_gitignore
    FAILED tests/test_root_run_scratch_migration.py::UntrackWorkflowArtifactsDelegationTests::test_apply_relocates_record_to_aw_and_untracks_both_paths
    ======================== 2 failed, 15 passed in 29.88s =========================
    ```

    (3) Discriminators vs regression guards:
      - Discriminators (failed against pre-E-02 tool; prove the defect is resolved):
        * `test_apply_creates_no_root_gitignore`: Fails because pre-E-02 tool appends and stages root `.gitignore`.
        * `test_apply_relocates_record_to_aw_and_untracks_both_paths`: Fails because pre-E-02 tool leaves record at `workflow-artifacts/` and creates no `.aw/workflow-artifacts/` destination.
      - Regression guards (passed against both pre-E-02 and post-E-02 tools):
        * `test_dry_run_leaves_index_and_worktree_byte_identical`: Confirms dry-run non-mutation (HEAD matches, `git status --porcelain` empty, `git diff` empty, `git diff --cached` empty, file intact at retired path).
        * `test_both_modes_exit_zero`: Confirms exit code 0 on clean runs.

    (4) Collection proof:
    Bare pytest suite collected test count delta increased from 3291 to 3308 (+17 tests: 13 restored `RootRunScratchMigrationTests` + 4 `UntrackWorkflowArtifactsDelegationTests`).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: the rewritten `tools/README.md` section quoted, showing it names `.aw/workflow-artifacts/`, states the delegation and the dry-run default, and no longer recommends index-only untracking of the retired path. Paste a search of that section for the bare retired path showing only occurrences that are deliberately historical (a `.aw/`-prefixed path or the `git filter-repo` guidance), and quote the retained destructive-action warning to prove it was not dropped.
  - Observed evidence: PASS. Documentation rewrite and verification evidence:
    Rewritten `tools/README.md` section:
    ```markdown
    ## `untrack-workflow-artifacts.py`

    `tools/untrack-workflow-artifacts.py` is a backwards-compatible delegating shim that safely migrates a repository's run records from the retired repo-root `workflow-artifacts/` directory to the canonical `.aw/workflow-artifacts/` directory without deleting local files.

    The tool delegates to `engine.migrate_root_workflow_artifacts`, which preserves git history using `git mv` (so `git log --follow` reaches past the migration commit), commits the relocation in dedicated path-scoped commits, and untracks the destination files so the framework-owned `.aw/.gitignore` rule (`/workflow-artifacts/`) governs them going forward. Standard repository setup with `aw install` (or `agent-workflows install`) automatically runs this same migration.

    ### Usage

    1. **Dry run (default)**:
       ```bash
       python3 tools/untrack-workflow-artifacts.py
       ```
       Inspects the repository state and prints what would be relocated and untracked. Makes no changes to the repository or working tree.

    2. **Apply migration**:
       ```bash
       python3 tools/untrack-workflow-artifacts.py --apply
       ```
       Relocates run records from `workflow-artifacts/` to `.aw/workflow-artifacts/` with history preserved in Git, untracks the records at the new path, and removes the retired directory once empty. Does not create or modify any root `.gitignore`.

    3. **Compatibility flag `--commit`**:
       ```bash
       python3 tools/untrack-workflow-artifacts.py --apply --commit
       ```
       Accepted for backwards compatibility. Because the underlying migration already makes its own path-scoped commits for the relocation, `--commit` is a no-op that prints an explanatory note.

    ### Remediation Guidance for Already-Committed Artifacts

    If a repository has previously committed run records from the retired `workflow-artifacts/` path to Git history:

    1. **Size the Exposure First**:
       Run the local-leaks sanitizer to assess whether committed records contain sensitive local paths, usernames, or session IDs:
       ```bash
       aw sanitize . --agent
       ```

    2. **Remediation Option A: Relocate and Untrack (Recommended)**:
       Run `aw install` or `python3 tools/untrack-workflow-artifacts.py --apply` to migrate run records to `.aw/workflow-artifacts/` and stop tracking future changes. This preserves local files and commit history without rewriting Git history.

    3. **Remediation Option B: Git History Rewrite (Optional for Sensitive Exposure)**:
       If committed history contains sensitive credentials or private home paths that must be purged from Git history entirely, use `git-filter-repo` (or BFG Repo-Cleaner) to strip the directory from all commits:
       ```bash
       git filter-repo --path workflow-artifacts/ --invert-paths
       ```
       **WARNING (destructive; run ONLY with explicit human approval):** this REWRITES history, changes every subsequent commit SHA, and requires a coordinated force-push that invalidates all existing clones and open branches/PRs. It is NOT reversible by a normal pull. Do NOT run it automatically or as part of routine remediation; propose it, explain the blast radius, and wait for an explicit human decision before executing (consistent with the toolkit's never-rewrite-history-without-approval posture).
    ```

    Search of rewritten section for `workflow-artifacts`:
    All occurrences are either `.aw/workflow-artifacts/`, the tool script name, contextual description of the retired repo-root directory being migrated, or the historical `git filter-repo --path workflow-artifacts/ --invert-paths` guidance.

    Retained destructive-action warning quoted intact:
    ```
    **WARNING (destructive; run ONLY with explicit human approval):** this REWRITES history, changes every subsequent commit SHA, and requires a coordinated force-push that invalidates all existing clones and open branches/PRs. It is NOT reversible by a normal pull. Do NOT run it automatically or as part of routine remediation; propose it, explain the blast radius, and wait for an explicit human decision before executing (consistent with the toolkit's never-rewrite-history-without-approval posture).
    ```

    Cross-plan reconciliation:
    `fzueyy` has not yet landed (`tests/test_run_scratch_path_guard.py` does not exist). When `fzueyy` executes, its executor must reconcile its path-guard exclusion constant rather than copying the now-obsolete reason forward.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and has NOT been approved. `/plan-review` ran on 2026-09-28 and recorded `- Readiness: go-pending-approval`, which means it passed review and awaits human sign-off; it is not an approval. It must not be executed until a human approves it (`aw ipd set approved cf7f8z --by-human`). The executor must not self-approve and must not alter the `- Readiness:` field, which is an output of review rather than of authoring or execution. Child 01 of the `xtrwdb` Set; it has no `- Item-Dependencies:`, but its own E-items are ordered so the restored coverage (E-01) lands before the function acquires a second caller (E-02).

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. A hand-run script in `tools/` is rewritten as a thin delegating front end over a migration the toolkit already performs correctly, its README section is corrected, and 13 deleted tests plus 4 new ones are added. Review reproduced the defect end-to-end: today's tool leaves a tracked run record at the RETIRED repo-root path and writes `workflow-artifacts/` into the user's ROOT `.gitignore`, while the replacement relocates the record to `.aw/workflow-artifacts/` with `git log --follow` still reaching the pre-migration commit and creates no root ignore file at all. Nothing under `agent_workflows/` changes, so no shipped behavior moves, and the script is not even packaged (the wheel ships only `agent_workflows`), which is why the priority is `low`. THE ONE JUDGEMENT A HUMAN MAY WANT TO OVERRULE is retargeting rather than deleting the tool (OQ-02): the plan keeps it for its dry-run-by-default preview, which `aw install` has no equivalent for, and records that deleting the file and its README section would satisfy the backlog item equally. THE ONE THING A HUMAN SHOULD KNOW THAT THE PLAN DOES NOT DECIDE is the cross-plan ordering with pending plan `fzueyy` (F-08): both are unapproved, and E-05 invalidates a premise `fzueyy`'s test-exclusion constant records, so whichever executes second must reconcile.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Three paths, exactly the declared `- Scope-Paths:`: `tools/untrack-workflow-artifacts.py` (E-02, E-03), `tools/README.md` (E-05), and the new `tests/test_root_run_scratch_migration.py` (E-01, E-04). FIVE NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, do NOT change `agent_workflows/engine.py`: `migrate_root_workflow_artifacts` is `executed`, was measured correct here on four inputs, and it is the only code in the tree that touches a user's committed history. SECOND, do NOT restore any other class from the deleted `tests/test_engine_install.py`; each is its own decision and the Deferred section declines to carry them deliberately. THIRD, do NOT touch `ARCHITECTURE.md` or `CONTRIBUTING.md`, which pending plan `fzueyy` declares in its own `- Scope-Paths:`. FOURTH, do NOT edit `tests/test_run_scratch_path_guard.py` (it is `fzueyy`'s deliverable and does not exist yet); report the reconciliation instead. FIFTH, do NOT remove or soften the `git filter-repo` guidance or its destructive-action warning in `tools/README.md`; V-05 asserts it survived.

EXECUTION CONTRACT (`AGENTS.md`): commit ONLY the paths this plan declares, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim, and run the suite BARE as `python3 -m pytest` (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; a second `-q` would suppress the `N passed` line V-01 requires). This is a SHARED checkout: uncommitted changes you did not make are not yours, and `tools/README.md` in particular is a file other lanes touch, so verify the staged set before committing. Run `aw sanitize --agent` before pasting any evidence containing temp-repo absolute paths.

POST-GATE LIFECYCLE: do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and EVERY `V-*` item above carries concrete pasted evidence. V-04's falsification (the new tests failing against the old tool) is mandatory, not optional: without it the plan cannot show it fixed anything. If any item cannot be completed, STOP and report rather than marking it done.

BACKLOG HANDOFF: this plan carries `- From-Backlog: xtrwdb` and inherits that item's `- Blocks-Release: next`. The item stays `graduated` until this plan is `executed`, which is what preserves the release gate through the handoff.
