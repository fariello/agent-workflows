# IPD: Retarget the untrack tool onto the run-scratch migration and restore the migration's deleted coverage

- Date: 2026-09-28
- Kind: child
- Concern: `tools/untrack-workflow-artifacts.py` STILL PERFORMS THE RETIRED LAYOUT'S MIGRATION, and running it today actively re-establishes the layout spec `20260817-2124-01` (`u7xtni`, Order 07) retired. Its module constant is `ARTIFACTS = "workflow-artifacts"`, the REPO-ROOT path, and `IGNORE_RULE = f"{ARTIFACTS}/"` is written into the user's ROOT `.gitignore` by `append_ignore_rule`. MEASURED on 2026-09-28 in a throwaway git repo carrying one tracked run record at `workflow-artifacts/assess/20260101-000000/report.md`: `python3 tools/untrack-workflow-artifacts.py --apply` prints `Local workflow-artifacts/ exists: yes` / `Tracked paths: 1` / `Removed 1 tracked path(s) from the Git index`, and afterwards `git ls-files` reports `.gitignore` plus `README.md` while the user's root `.gitignore` gained `workflow-artifacts/` under the comment `# agent-workflows working material (local-only; ...)`. THE RUN RECORD IS STILL AT THE REPO ROOT: nothing moved, so the double-home confusion Order 07 exists to end is preserved and freshly blessed with an ignore rule. Run the SAME repo through the replacement instead, `engine.migrate_root_workflow_artifacts`, and the outcome is strictly better on every axis: it reports `workflow-artifacts/assess/20260101-000000/report.md -> .aw/workflow-artifacts/assess/20260101-000000/report.md [migrated with git mv (history preserved, committed), then untracked so the .aw/.gitignore rule governs it; file kept on disk]` followed by `workflow-artifacts/ [removed: now empty; run scratch lives at .aw/workflow-artifacts/]`, and the user's root `.gitignore` is never created at all. So the tool is not merely stale prose: it is a WORSE, history-losing version of a migration the toolkit already performs correctly, and `tools/README.md` still advertises it as "Remediation Option A: Index-Only Stop Tracking (Recommended)". SECOND, AND NOT IN THE BACKLOG ITEM: the replacement has NO TEST COVERAGE LEFT. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_engine_install.py` entire, taking with it `RootRunScratchMigrationTests`, whose own docstring states "THE PROOF OBLIGATION IS UNUSUALLY HIGH" because this is "the only child that touches a user's committed history". `grep -rn "migrate_root_workflow_artifacts\|RETIRED_ROOT_ARTIFACTS_DIR" tests/` returns NOTHING today, and `ls tests/test_engine_install.py` reports no such file. Retargeting the tool onto that function while nothing tests the function is how a history-preserving migration decays silently.
- Scope: IN: (a) convert `tools/untrack-workflow-artifacts.py` into a thin delegating front end over `engine.migrate_root_workflow_artifacts`, on the `install-workflows.py` / `tools/agy_run.py` shim precedent, so the hand-run entry point performs the CORRECT migration and stops writing a root ignore rule for a retired path; (b) preserve the tool's one genuine safety property, DRY RUN BY DEFAULT, by routing it to the `dry_run=` parameter the engine function already exposes; (c) restore the deleted `RootRunScratchMigrationTests` as a focused new test file so the delegated-to function has outcome coverage again, keeping only tests that assert outcomes; (d) cover the delegation itself by driving the tool as a subprocess and asserting the relocation actually happened on disk and in the index; (e) rewrite the `tools/README.md` section, which currently recommends the wrong remediation. OUT: any change to `engine.migrate_root_workflow_artifacts` itself (it is `executed`, measured correct here, and this plan only gains it callers and tests); the `--commit` flag's removal versus retention beyond what OQ-01 decides; the separate root-doc path references owned by pending plan `fzueyy` (`ARCHITECTURE.md`, `CONTRIBUTING.md`), whose `- Scope-Paths:` already claims them and which explicitly declares `tools/README.md` and this tool OUT of its own scope; restoring any other class from the deleted `tests/test_engine_install.py` (`LayoutEmissionFreshInstallTests`, `AwGitignoreLaneTests`, `MachineLocalStatePremiseTests`, `InstallerCommitSetTests`), each its own decision; the `git-filter-repo` history-rewrite guidance in `tools/README.md`, which remains correct and stays; `DECISIONS.md` D119, a dated record of what was decided then.
- Scope-Paths: tools/untrack-workflow-artifacts.py, tools/README.md, tests/test_root_run_scratch_migration.py
- Item-Dependencies: none
- Status: to-review
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

- 2026-09-28 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `xtrwdb`. Reproduced the item's reported defect by running the tool against a throwaway repo and measured that it leaves the run record at the repo root while writing a root ignore rule for it; measured the replacement `engine.migrate_root_workflow_artifacts` against an identical repo and found it strictly better. Resolved the item's open "WHAT A FIX WOULD DECIDE" question (option b, delegate) from repository evidence rather than deferring it, and found a SECOND defect the item does not name: commit `19313eed` deleted the replacement's entire 13-test coverage class, so this plan restores it.

- 2026-09-28 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

A user who reaches for the hand-run untrack tool gets the migration the toolkit actually performs today, moving run scratch to `.aw/workflow-artifacts/` with its git history intact and without a root-`.gitignore` rule for a retired path, and the migration function that now backs both the installer and the tool regains the outcome coverage the suite trim deleted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the coverage the delegation will depend on

- [ ] E-01 RESTORE THE DELETED MIGRATION COVERAGE AS `tests/test_root_run_scratch_migration.py`. Recover the class with `git show 19313eed^:tests/test_engine_install.py` and take ONLY `RootRunScratchMigrationTests` (it begins at the line `class RootRunScratchMigrationTests(unittest.TestCase):` and is the last class in that file, 13 `def test` methods). Every other class in the recovered file is out of scope per the Scope statement. Restore the class docstring INTACT: it is the design rationale for the assertions, enumerating the five ways "a naive implementation passes while the feature is broken" (history via real `git log --follow` rather than mere file existence; whole path SETS compared so a partial move cannot pass; merge rather than move, since a populated destination is "the common case rather than an edge"; refusal rather than overwrite on a same-path/different-bytes conflict; and "IGNORED IN EFFECT, via real `git check-ignore` attributed to `.aw/.gitignore`"). Follow the `restorecov` precedent (`6vozur` E-01) for the shape of a restoration: prepend a module docstring stating that this is the coverage `19313eed` deleted, which plan restored it, and that it now guards a function with a SECOND caller (this plan's tool). AUDIT EACH RESTORED TEST AGAINST THE OUTCOME RULE before keeping it (`AGENTS.md`: no test may read production source with `inspect`/`ast`/regex, assert caller counts or symbol censuses, or pin docstrings); drop any that fails and RECORD which and why, since a silent omission is indistinguishable from a bug. Fix only what the move requires: the file's `REPO_ROOT`/`git`/`init_repo` helpers come from `tests.support`, which is importable unchanged from `tests/`.
  - Depends on: none
  - Expected outcome: the file exists, imports `engine.migrate_root_workflow_artifacts`, and its tests pass; the bare suite's test COUNT rises by exactly the number of restored methods.
  - Execution state: pending

### Task group 2: retarget the tool

- [ ] E-02 CONVERT THE TOOL INTO A DELEGATING FRONT END. Replace the body of `tools/untrack-workflow-artifacts.py` so it calls `engine.migrate_root_workflow_artifacts(repo_root, use_git=engine.git_available(repo_root), dry_run=not args.apply)` and prints the returned action lines, DELETING the module's own migration logic: the `ARTIFACTS` constant, `IGNORE_COMMENT`, `IGNORE_RULE`, `tracked_paths`, `ignore_is_present`, `append_ignore_rule`, `gitignore_is_clean`, and `acceptable_commit_paths`. Every one of those exists only to serve the retired repo-root path or the root-`.gitignore` write this plan removes. Use the established shim shape rather than inventing one: `install-workflows.py` inserts its own directory on `sys.path` "so the package resolves when this file is run directly from a checkout", prints a one-line `note:` to stderr naming the preferred surface, and delegates; `tools/agy_run.py` does the same from `tools/` with `Path(__file__).resolve().parent.parent`. PRESERVE DRY RUN AS THE DEFAULT, which is the tool's one genuine safety property and is why this is a retarget and not a deletion: `--apply` maps to `dry_run=False` and its absence to `dry_run=True`, a parameter the engine function already documents as "report what WOULD happen and touch nothing". Keep `repository_root()` and `MigrationError` (the CLI contract: exit 2 with `error: ` on stderr when not in a git work tree). Point the deprecation note at `aw install`, which reaches this same migration through `engine.install_into_repo`.
  - Depends on: E-01
  - Expected outcome: the tool relocates run scratch to `.aw/workflow-artifacts/` with history preserved, writes no root `.gitignore`, and still changes nothing without `--apply`.
  - Execution state: pending

- [ ] E-03 RESOLVE `--commit` AGAINST THE NEW BACKEND, per OQ-01's recorded decision. The flag cannot survive unchanged: `engine._commit_relocation` ALREADY COMMITS, making its own two path-scoped commits (the rename, then the untrack), so a post-hoc `--commit` would find nothing staged, and its guard `acceptable_commit_paths` is deleted by E-02 anyway. Implement OQ-01's resolution: keep the flag ACCEPTED but make it a no-op that prints a one-line note stating the migration now commits its own path-scoped relocation, so an existing hand-typed invocation or shell history does not start failing with an argparse error. Preserve the existing `--commit` requires `--apply` argparse check, since that relationship still reads correctly.
  - Depends on: E-02
  - Expected outcome: `--apply --commit` behaves exactly as `--apply` plus one explanatory line, and `--commit` alone still errors.
  - Execution state: pending

- [ ] E-04 COVER THE DELEGATION ITSELF, in the same file as E-01. Add one class that drives the TOOL as a subprocess with `tests.support.run_tool` (the helper that exists for exactly this: "Run one of the framework's Python tools with args") against a temp repo carrying a tracked repo-root run record. Assert OUTCOMES, not that a function was called: (1) without `--apply` the index and the working tree are BYTE-IDENTICAL afterwards and the retired path still holds the record; (2) with `--apply` the record is at `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` on disk, `git ls-files` no longer lists it at either path, and the retired directory is gone; (3) NO root `.gitignore` is created, which is the backlog item's specific complaint and the one assertion that fails against today's tool; (4) exit 0 in both cases. Include the FALSIFICATION the restorecov review demanded (PR-701): state in the class docstring how the suite was proven to COLLECT these tests, because a file pytest does not collect adds zero tests while the suite still reports green.
  - Depends on: E-03
  - Expected outcome: four outcome assertions that fail against the pre-E-02 tool and pass after it.
  - Execution state: pending

### Task group 3: stop recommending the wrong remediation

- [ ] E-05 REWRITE THE `tools/README.md` SECTION. Its heading `## \`untrack-workflow-artifacts.py\`` and its five occurrences of the bare retired path currently teach the retired layout, and its "Remediation Option A: Index-Only Stop Tracking (Recommended)" recommends the behavior this plan removes. State that the tool now delegates to the toolkit's run-scratch migration, that run scratch lives at `.aw/workflow-artifacts/` (ignored by the framework-owned `.aw/.gitignore`), that the dry run remains the default, and that `aw install` performs the same migration. KEEP the `git filter-repo` guidance and its destructive-action warning unchanged: that guidance is about purging already-committed history, is still correct, and D121/F4 deliberately hardened it into a consent absolute. NOTE FOR A REVIEWER: pending plan `fzueyy` declares this file OUT of its scope precisely because "the tool's SUBJECT is the retired path", which was true while the tool targeted it and stops being true here; that is why this plan, not that one, owns this section.
  - Depends on: E-02
  - Expected outcome: the section describes the delegating tool and the live path, with the history-rewrite warning intact.
  - Execution state: pending

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

## Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F-01 | MEDIUM | THE TOOL LEAVES THE RUN RECORD AT THE RETIRED PATH AND BLESSES IT. Run against a temp repo with one tracked record at `workflow-artifacts/assess/20260101-000000/report.md`, `--apply` prints `Removed 1 tracked path(s) from the Git index; local files were retained.` and `Added and staged the workflow-artifacts/ ignore rule.` Afterwards the record is STILL at the repo root, and the root `.gitignore` (newly created) contains `workflow-artifacts/`. This is the item's report, reproduced. | Measured 2026-09-28 in a throwaway repo; `git ls-files` afterwards returns `.gitignore` and `README.md`, and `cat .gitignore` shows the added rule |
| F-02 | MEDIUM | THE REPLACEMENT IS STRICTLY BETTER ON THE SAME INPUT, which is what makes delegation the right fix rather than retargeting the constant. `engine.migrate_root_workflow_artifacts` on an identical repo relocates the record to `.aw/workflow-artifacts/...` "[migrated with `git mv` (history preserved, committed), then untracked ...; file kept on disk]", removes the now-empty retired directory, and creates NO root `.gitignore`. | Measured 2026-09-28 by calling the function directly; both action lines captured, and `ls .gitignore` afterwards reports no such file |
| F-03 | MEDIUM | THE FUNCTION THIS PLAN DELEGATES TO HAS ZERO TESTS, and this is NOT in the backlog item. `19313eed` deleted `tests/test_engine_install.py` whole, including `RootRunScratchMigrationTests` (13 test methods) whose docstring calls its proof obligation "UNUSUALLY HIGH" because the function "is the only child that touches a user's committed history". | `grep -rn "migrate_root_workflow_artifacts\|RETIRED_ROOT_ARTIFACTS_DIR" tests/` returns nothing; `ls tests/test_engine_install.py` reports no such file; `git show 19313eed^:tests/test_engine_install.py` still yields the class |
| F-04 | LOW | THE ITEM'S "NO CALLER" CLAIM IS STILL TRUE, AND IT BOUNDS THE BLAST RADIUS. Nothing in `agent_workflows/` invokes the tool; the single package mention is the `engine.py` comment that keeps it "available for a user who wants only to untrack". The tool is also NOT SHIPPED: the wheel packages only `agent_workflows`, and the sdist include-list does not carry `tools/`, so no installed user can reach this script at all. Both facts are why this stays `low` priority. | Re-verified 2026-09-28: `grep -rn untrack_workflow_artifacts agent_workflows/ tools/ tests/` returns only that comment; `pyproject.toml` `[tool.hatch.build.targets.wheel] packages = ["agent_workflows"]` and the sdist `include` list omits `tools` |
| F-05 | LOW | `tools/README.md` ADVERTISES THE WRONG REMEDIATION AS RECOMMENDED, so the defect is reachable through documentation and not only by reading the script: "Remediation Option A: Index-Only Stop Tracking (Recommended): Use `python3 tools/untrack-workflow-artifacts.py --apply` to stop tracking future changes and keep local files." | `tools/README.md`, section `## \`untrack-workflow-artifacts.py\``; 5 bare occurrences of the retired path in that section |
| F-06 | LOW | A DELEGATING TOOL INHERITS ONE HONEST LIMIT, recorded so review does not mistake it for a regression this plan introduces: in a repo with NO `.aw/.gitignore`, the migration relocates and untracks correctly but the destination is not yet ignored, so the files show as `?? .aw/`. The installer does not hit this because `install_into_repo` runs the migration alongside `_ensure_aw_gitignore`; measured on the real installer, a first `aw install` reports `.aw/workflow-artifacts/ is NOT ignored (... re-run \`aw install\`)` and a second reports `is ignored by .aw/.gitignore (correct...)`. The relocated bytes are never lost or committed in either case, so this is a pre-existing property of the engine function (explicitly OUT of scope) and strictly better than today's tool, which leaves the record tracked-then-untracked at a retired path. | Measured 2026-09-28: direct call into a repo with no `.aw/.gitignore` leaves `?? .aw/` and `git check-ignore` exit 1; the real installer's two successive runs produce the two summary lines quoted |

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

- `python3 -m pytest` BARE, per `AGENTS.md`, with the `N passed` summary pasted. Record the pre-change baseline count first, because E-01 and E-04 must be shown to ADD tests (restorecov PR-701: a file pytest never collects adds zero tests while the suite still reports green).
- `python3 -m pytest tests/test_root_run_scratch_migration.py` for the focused file, with output pasted.
- THE FALSIFICATION E-04 EXISTS TO PROVIDE: run the new delegation test against the PRE-E-02 tool (e.g. `git stash` the tool change, or run the test at the parent commit) and paste the FAILURE, specifically the "no root `.gitignore`" assertion. A test that passes both before and after proves nothing about this fix.
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

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest tests/test_root_run_scratch_migration.py` output pasted showing every restored test passing, AND the bare-suite COUNT delta: the `N passed` line from before the change and after, whose difference equals the number of restored methods plus E-04's (restorecov PR-701, since an uncollected file adds zero tests while the suite still reports green). Paste the audit result required by E-01: the list of restored tests kept and, for any dropped, which and why under the outcome rule. Quote the restored class docstring's five-point rationale to show it survived, and show the new module docstring naming `19313eed` and this plan.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the tool run by hand in a throwaway repo holding a tracked `workflow-artifacts/<wf>/<RUN_ID>/report.md`. Paste: the `--apply` output showing the engine's `-> .aw/workflow-artifacts/...` action line; `git ls-files` proving the record is tracked at NEITHER path; `find .aw/workflow-artifacts -type f` proving the bytes are at the new path; `ls .gitignore` proving NO root ignore file was created (the backlog item's specific complaint); and `git log --follow -- .aw/workflow-artifacts/<wf>/<RUN_ID>/report.md` reaching the pre-migration commit. Also paste a `grep -n "ARTIFACTS\|IGNORE_RULE\|append_ignore_rule" tools/untrack-workflow-artifacts.py` returning nothing, proving the retired-path logic is gone rather than merely bypassed. Sanitize absolute paths before pasting.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `--apply --commit` output in a temp repo showing the same migration plus the explanatory note and exit 0, alongside `git log --oneline` showing the engine's own two relocation commits and NO third commit from the tool. Plus `--commit` without `--apply` still exiting nonzero with the argparse error, output pasted.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the delegation tests passing after the change, AND the FALSIFICATION: the same tests run against the pre-E-02 tool with the FAILURE pasted, naming the assertion that fired (expected: the root-`.gitignore` assertion, and the new-path assertion). Paste the dry-run case's proof that the index and working tree were unchanged. State in the evidence how collection was proven (the count delta from V-01), not merely that the file passes when named directly.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the rewritten `tools/README.md` section quoted, showing it names `.aw/workflow-artifacts/`, states the delegation and the dry-run default, and no longer recommends index-only untracking of the retired path. Paste a search of that section for the bare retired path showing only occurrences that are deliberately historical (a `.aw/`-prefixed path or the `git filter-repo` guidance), and quote the retained destructive-action warning to prove it was not dropped.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is a proposal and MUST be reviewed and approved by a human before execution. Child 01 of the `xtrwdb` Set; it has no `- Item-Dependencies:`, but its own E-items are ordered so the restored coverage (E-01) lands before the function acquires a second caller (E-02).

EXECUTION CONTRACT (`AGENTS.md`): commit ONLY the paths this plan declares, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim, and run the suite BARE as `python3 -m pytest` (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; a second `-q` would suppress the `N passed` line V-01 requires). This is a SHARED checkout: uncommitted changes you did not make are not yours, and `tools/README.md` in particular is a file other lanes touch, so verify the staged set before committing. Run `aw sanitize --agent` before pasting any evidence containing temp-repo absolute paths.

POST-GATE LIFECYCLE: do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and EVERY `V-*` item above carries concrete pasted evidence. V-04's falsification (the new tests failing against the old tool) is mandatory, not optional: without it the plan cannot show it fixed anything. If any item cannot be completed, STOP and report rather than marking it done.

BACKLOG HANDOFF: this plan carries `- From-Backlog: xtrwdb` and inherits that item's `- Blocks-Release: next`. The item stays `graduated` until this plan is `executed`, which is what preserves the release gate through the handoff.
