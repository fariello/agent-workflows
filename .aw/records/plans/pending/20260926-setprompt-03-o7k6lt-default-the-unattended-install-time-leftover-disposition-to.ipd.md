# IPD: Default the unattended install-time leftover disposition to remove when nothing is saved

- Date: 2026-09-26
- Kind: child
- Concern: AN UNATTENDED INSTALL-TIME MIGRATION LEAVES STALE LEGACY FILES BEHIND BY DEFAULT. Every install-time migration call site (`cli._handle_legacy_migration`'s `--to-aw` and interactive-confirm branches, and `cli._split_brain_guard`'s migrate-now branch) reads `cli._install_leftover_disposition`, which returns `defer` when `--leftovers` is absent. Measured at HEAD `f46b6775` on a scratch legacy repo carrying a tracked `.agents/README.md` leftover: a real `MigrationManager.execute_migration(leftover_disposition="defer")` leaves `.agents/README.md` in place, `remove` deletes it. The maintainer ruled on 2026-09-26 that with nothing saved the default is `remove` (OQ-01). THE RULING RESTS ON A PREMISE THE CODE DOES NOT FULLY HONOR, measured on the same scratch shape: `layout_migration.MigrationManager._is_removable_leftover` treats "tracked" as `git ls-files --error-unmatch` (in the INDEX), so `remove` (a) deletes a leftover that was `git add`ed but never committed, which then exists nowhere in history, and (b) runs `git rm -f` on a tracked leftover carrying UNCOMMITTED edits, discarding them (HEAD keeps only the old content). Flipping the default makes both losses happen without anyone choosing `remove`, so this plan makes the premise true before flipping. BOTH LOSSES RE-MEASURED AT REVIEW on HEAD `1d013100` (where `je74a0` and `vv6y7e` are already executed) through a REAL end-to-end `execute_migration`, not the predicate alone: the staged-never-committed leftover ended up existing nowhere in history, and the locally-edited one was deleted leaving only the pre-edit content in `HEAD`. Review also found the operation is ENTIRELY SILENT about what it deleted (F-9), and that the ruling this plan cites is scoped to an UNATTENDED run while the resolver it changes is shared with two INTERACTIVE paths (BLOCKING OQ-02).
- Scope: IN: (a) tighten `_is_removable_leftover` so `remove` deletes a path only if it exists in `HEAD` and is unmodified against `HEAD` (index and worktree), which is exactly "recoverable from history"; everything else is preserved; (b) change the built-in default in `cli._install_leftover_disposition` from `defer` to `remove`, keeping precedence explicit `--leftovers` > saved `defaults.leftovers` (added by `je74a0`) > built-in, and keeping an unrecognized explicit value fail-safe at `defer` (OQ-03); (c) update the install `--leftovers` help (it promises "Never deletes without an explicit 'remove'") and the resolver's docstring; (d) a CHANGELOG entry; (e) amend the migration spec's non-interactive-default sentences for the install-driven case, declared; (f) behavioral tests and the existing tests that pin the old default; (g) ONE user-visible report line naming what `remove` deleted and how to restore it, because the operation is currently silent (added at review, E-08/E-09). OUT: `aw migrate-layout`'s own default (its `_run_migrate_layout` resolution stays `defer`, OQ-02); any prompt for the disposition (OQ-02 option iii, which would re-scope this plan); the classifier (`vv6y7e`).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/layout_migration.py, CHANGELOG.md, tests/test_installer.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: executed:je74a0
- Status: reviewed
- Readiness: no-go
- Work-Kind: chore
- Priority: medium
- From-Backlog: 6kczjg
- Set: setprompt
- Order: 3
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: o7k6lt

## Workflow history
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: REVIEWED - OPEN QUESTIONS; PR-002..PR-007 fixed, PR-001 escalated to blocking OQ-02

- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS. Re-measured every premise at HEAD `1d013100` (both dependencies already executed) and both data-loss claims reproduced end to end through a real `execute_migration`; E-02's proposed predicate verified correct on seven cases and shown NOT to become a no-op inside a live migration. PR-001 escalated: the plan widens the maintainer's UNATTENDED ruling to the two INTERACTIVE install paths on its own authority, so OQ-02 is reopened `Blocking: yes` / `Owner: maintainer` with three options and E-04 onward is gated behind it (`IPD-Q501` now fails lint by design). Added E-08/E-09 (the deletion is currently SILENT: a real install that deleted a tracked file never printed "leftover", "remove" or "delete"), required the test fixture to COMMIT (`init_repo` never does, so the removal controls would have passed vacuously), added safety case (b2) for a STAGED edit, named the old-default assertion E-05 missed, and corrected E-07's false doctor-coupling claim. Findings F-8..F-13 added. Watermark 07 -> 09. Readiness `no-go` on the unresolved blocking question.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 6kczjg on the maintainer's 2026-09-26 ruling that an unattended install-time migration with nothing saved defaults --leftovers to remove (OQ-01). Re-measured at HEAD f46b6775: defer keeps a tracked leftover, remove deletes it; ALSO measured that remove deletes a staged-never-committed leftover and discards uncommitted edits to a tracked one, so E-02 makes the ruling's recoverable-from-history premise true before E-04 flips the default. Ordered after je74a0 (saved defaults.leftovers, same resolver).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

An unattended `aw install` migration with no saved answer cleans up its git-recoverable legacy leftovers by default, while anything that is not recoverable from git history (untracked, ignored, private lanes, skills, never-committed, or locally modified) is always preserved.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE AT THE EXECUTING HEAD, after `je74a0` (and therefore `vv6y7e`) has executed. Read `cli._install_leftover_disposition` fresh (je74a0 E-05 adds the saved-answer read) and paste it. On scratch git repos (committed BASE = `.agents/workflows/VERSION`, `.agents/workflows/index.md`, `.agents/plans/README.md`, `.agents/skills/assess/SKILL.md`, plus a tracked leftover `.agents/README.md`; `AW_HOME` and `XDG_CONFIG_HOME` isolated), drive the real `MigrationManager(str(repo)).execute_migration(target_backend="repository", leftover_disposition=D)` and paste which `.agents/` files survive, for: (1) D=`defer`; (2) D=`remove`; (3) D=`remove` with `.agents/README.md` untracked-then-`git add`ed but never committed, plus `git log --all -- .agents/README.md`; (4) D=`remove` with an uncommitted edit to the committed `.agents/README.md`, plus `git show HEAD:.agents/README.md`. Then run `aw install <repo> --to-aw --yes` with nothing saved and paste the leftover disposition it used.
  - Depends on: none
  - Expected outcome: (1) keeps the leftover; (2) removes it and keeps skills; (3) removes a file that has no history; (4) removes the file and the edit is gone; the install uses `defer`.
  - Execution state: pending

### Task group 2: make the premise true

- [ ] E-02 TIGHTEN `layout_migration.MigrationManager._is_removable_leftover` so its PRIMARY signal is "recoverable from HEAD": keep every existing guard (local lanes, `untracked`, the `_skills_prefix` guard, `check-ignore`), then require BOTH that the path exists in `HEAD` (`git cat-file -e HEAD:<rel>` exits 0) AND that it is unmodified against `HEAD` in index and worktree (`git diff --quiet HEAD -- <rel>` exits 0). A repo with no `HEAD` commit therefore removes nothing. Update the docstring: `remove` deletes only leftovers that git can give back unchanged. Do NOT change `is_stale_tool_litter` (untracked `__pycache__`/`.pyc` litter is regenerable by definition) or `_handle_leftovers`' pruning of now-empty dirs. This also makes an EXPLICIT `--leftovers remove` and `aw migrate-layout --leftovers remove` safer, which is intended.
  - Depends on: E-01
  - Expected outcome: E-01 cases (3) and (4) now preserve `.agents/README.md` and report it under `preserved`; case (2) still removes it.
  - Execution state: pending

- [ ] E-03 ADD BEHAVIORAL TESTS to `tests/test_installer.py` in a new class (for example `InstallLeftoverDefaultRemoveTests`), driving the REAL `MigrationManager` and real `cli._handle_legacy_migration` on `git init` repos (NO mocking of `MigrationManager`; behavior only, no source-text or AST pins, per the 2026-09-26 test-policy ruling), reusing `InstallLeftoverDispositionThreadingTests`' `_legacy_repo` shape (which ALREADY carries `.agents/skills/assess/SKILL.md`, verified at review: `je74a0` E-06 added it, so no extension is needed). Safety cases, written BEFORE E-02 and shown failing: (a) a staged-never-committed leftover SURVIVES `remove`; (b) a committed leftover with an uncommitted edit SURVIVES `remove` with its edit intact. Controls passing before and after: (c) a clean committed leftover is removed by `remove`; (d) an untracked file under `.agents/` survives (an untracked leftover that the classifier accepts, for example under `.agents/plans/untracked/`, which migrates or is preserved, never deleted); (e) `.agents/skills/assess/SKILL.md` survives byte-identical.
  - THE FIXTURE MUST COMMIT, AND `_legacy_repo` DOES NOT (review PR-002, measured F-8). `tests/support.py:init_repo` runs `git init` plus three `git config` calls and NEVER commits, so a `_legacy_repo` has NO resolvable `HEAD` (`git rev-parse HEAD` -> "unknown revision", measured). Under E-02 a HEAD-less repo removes NOTHING, so if (c) and (f) are built on the fixture as-is they PASS VACUOUSLY: the leftover survives because there is no HEAD, not because the code is right, and a later regression that deleted everything would still pass them. So every case that asserts a REMOVAL ((c), and (f) in E-05) MUST `git add -A` and `git commit` the base state first, exactly as `tests/test_layout_inventory.py::_make_git_repo` already does. Case (a) deliberately does the opposite (commit a seed file, then `git add` the leftover WITHOUT committing it), which is the only shape that distinguishes "not in HEAD" from "no HEAD at all".
  - ADD ONE MORE SAFETY CASE (b2): a leftover whose edit is STAGED (`git add`ed after being committed) also survives. Measured at review that `git diff --quiet HEAD -- <rel>` returns 1 for a staged-modified path as well as a worktree-modified one, so E-02 covers it; without the case nothing pins the index half of the claim, which is the half `git rm -f` would silently discard.
  - Depends on: E-01
  - Expected outcome: (a), (b), (b2) FAIL before E-02 and pass after; (c), (d), (e) pass throughout; (c) demonstrably NON-vacuous (it removes a file, so it cannot pass in a HEAD-less repo).
  - Execution state: pending

### Task group 3: flip the default

- [ ] E-04 CHANGE THE BUILT-IN DEFAULT in `cli._install_leftover_disposition` from `defer` to `remove`. Precedence after the change: an explicit `--leftovers` value in `("keep", "remove", "defer")` wins; else the saved `defaults.leftovers` from `je74a0` wins; else, when the value is ABSENT (attribute missing or `None`), return `remove`; an explicitly present but UNRECOGNIZED value returns `defer` (OQ-03). Rewrite the docstring, which today says "It DEFAULTS to `defer` ... nothing becomes destructive without an explicit `--leftovers remove`", to state the new default, the maintainer ruling of 2026-09-26, and why it is safe (E-02). Update the `z1yefm` comment above the install `--leftovers` argument that says "The DEFAULT stays `defer`".
  - Depends on: E-02
  - Expected outcome: `_install_leftover_disposition(Namespace(leftovers=None))` and `(Namespace())` return `remove` with nothing saved; saved `defer` returns `defer`; `--leftovers keep` returns `keep`; `leftovers="rm -rf"` returns `defer`.
  - Execution state: pending

- [ ] E-05 TEST THE NEW DEFAULT END TO END and repair the tests that pin the old one. In the E-03 class, with `XDG_CONFIG_HOME` isolated: (f) `aw install <legacy repo> --to-aw --yes` with NOTHING saved removes a clean tracked leftover (the fixture MUST commit first, per E-03's fixture rule, or this case is vacuous); (g) after `aw config set defaults.leftovers defer`, the same install KEEPS it; (h) `--leftovers defer` on the command line keeps it even with `remove` saved; (i) the untracked file and `.agents/skills` survive in (f). Then update, without weakening, the existing assertions that encode the old built-in default: in `InstallLeftoverDispositionThreadingTests`, the resolver assertions `_install_leftover_disposition(self._args())` and `(argparse.Namespace())` expecting `defer`, and the `(None, "defer")` rows in `test_migration_paths_thread_requested_disposition`; re-read them after `je74a0` E-06/E-07 (which also edits this class) and change only the absent-value expectations to `remove`. NOTE `test_leftover_flag_parsing_and_resolver` ALSO ends with a "Clear restores built-in default" assertion (`CFG.unset_config_value("defaults.leftovers")` then expecting `defer`) that the plan did not enumerate; it must become `remove` too (review PR-004, located at review). The split-brain test that passes a `MagicMock` `args` and asserts `leftover_disposition="defer"` exercises the present-but-unrecognized branch, so it should still pass unchanged (VERIFIED at review: `getattr(MagicMock(), "leftovers")` is a `MagicMock`, not in the enum, so the resolver returns `defer`); confirm rather than edit it.
  - ALSO CONFIRM the docstring of `test_leftover_flag_parsing_and_resolver` ("safe fallback to defer") and the `aw install --yes` help are not left asserting or promising the old default; the `--yes` help string is `"Skip preflight confirmations."` and needs no change, but `aw migrate-layout`'s `--yes` help DOES say "leftovers defaults to defer" and stays correct because OQ-02 keeps that verb at `defer` (verified at review).
  - Depends on: E-04
  - Expected outcome: (f) to (i) pass; (f) FAILS against the pre-E-04 resolver; the repaired assertions pass and name `remove`.
  - Execution state: pending

### Task group 4: contract and user-facing text

- [ ] E-06 UPDATE THE CONTRACT AND USER TEXT. (a) Install `--leftovers` help in `cli._build_parser`: replace "or defer (record for a later cleanup; the default). Never deletes without an explicit 'remove'." with text saying `remove` is the default when nothing is saved, that it deletes only leftovers git can restore unchanged, and how to opt out (`--leftovers defer`, or `aw config set defaults.leftovers defer`). Leave `aw migrate-layout`'s `--leftovers` and `--yes` help unchanged (OQ-02). (b) `CHANGELOG.md`, `## 2.0.0 (pending)` list: one `- Changed:` bullet announcing that an install-time layout migration now removes leftover legacy files by default when you have not saved a preference, that only files git can restore unchanged are removed, that untracked files, private lanes and `.agents/skills` are never touched, and the two opt-outs. USER-FACING PROSE: no em or en dashes. (c) AMEND the migration spec (declared): in `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`, the Section 3 bullet "with a non-interactive default of `defer` that never deletes without an explicit choice" and step 9 "non-interactive default `defer`, which never deletes without an explicit choice": keep `defer` for `aw migrate-layout`, and state that an install-driven migration's default is the saved answer, else `remove` restricted to leftovers recoverable unchanged from `HEAD` (maintainer ruling 2026-09-26). Record it with `aw specs note <spec path> --message "..."` naming `o7k6lt`; if that verb refuses on an `implemented` spec, paste the refusal and add no history line.
  - Depends on: E-04
  - Expected outcome: `aw install --help` shows the new text; the CHANGELOG bullet exists with no dashes; the spec sentences match the shipped behavior.
  - Execution state: pending

- [ ] E-08 REPORT WHAT WAS DELETED. A destructive default that prints nothing is the part of this change a user cannot consent to after the fact, and measured at review the install path is COMPLETELY SILENT about it: a full `aw install <repo> --to-aw --yes` that deleted `.agents/README.md` emitted hundreds of `[added ]` lines and the word "leftover", "remove", "delete" appeared NOWHERE in stdout or stderr (F-9). `_handle_leftovers` already RETURNS the classified lists and `execute_migration` already stores them on the transaction as `tx["leftover_disposition"] = {"disposition","leftovers","removed","preserved","stale_tool_litter"}` (verified at review by reading the transaction back: `removed: ['.agents/README.md']`), so the data needs no new plumbing. In BOTH `cli._handle_legacy_migration` migration branches and the `cli._split_brain_guard` migrate-now branch, after a successful `execute_migration`, when the disposition used was `remove` and the recorded `removed` list is non-empty, emit ONE `term.status("info", ...)` line naming the count and how to recover (the paths are in git history, so `git checkout HEAD -- <path>` restores them), and name `--leftovers defer` / `aw config set defaults.leftovers defer` as the opt-out. Read the list from the manager's own recorded transaction rather than re-deriving it; do NOT print an unbounded file list (name the count, and list at most a few paths).
  - WHY THIS IS IN SCOPE rather than a follow-up: the plan's own approval paragraph tells the human that only git-recoverable files are deleted, and a user can only ACT on that (recover a file they wanted) if they are told a deletion happened. Flipping a default to destructive while keeping the operation silent is the combination that produces an unrecoverable-in-practice loss even when it is recoverable in principle.
  - Depends on: E-04
  - Expected outcome: an unattended install that removes a leftover prints one line naming the count and the recovery command; an install that removes nothing, or that ran `keep`/`defer`, prints no such line.
  - Execution state: pending

- [ ] E-09 TEST THE REPORT (E-08). In the E-03 class: (j) the (f) install's captured output contains the count and the recovery hint; (k) the (g) install (saved `defer`) output contains NO such line; (l) an install over a legacy repo with NO leftovers to remove prints no such line. Assert on the USER-VISIBLE output, not on an internal call.
  - Depends on: E-08
  - Expected outcome: (j) to (l) pass; (j) fails before E-08.
  - Execution state: pending

- [ ] E-07 RUN THE BARE SUITE `python3 -m pytest` before (at E-01) and after E-06 and compare failing node IDs; also `python3 -m pytest tests/test_installer.py tests/test_layout_inventory.py tests/test_layout_migration.py -o addopts="" -q`. THE FILE LIST IS CORRECTED (review PR-006): the plan named `tests/test_doctor.py` on the rationale that `_is_removable_leftover` "backs the doctor residue view's expectations", and that is FALSE as measured. `_is_removable_leftover` has exactly ONE caller in the package (`_handle_leftovers`), `agent_workflows/doctor.py` never imports `layout_migration` at all, and `grep` for `removable` in `tests/test_doctor.py` finds nothing. `tests/test_layout_inventory.py` IS genuinely affected (it calls `execute_migration(..., leftover_disposition="remove")` five times) and `tests/test_layout_migration.py` holds the `InstallMigrationResidueSweepTests` that the backlog item says already pins the whole `remove` outcome, so those two are the real neighbours. Running `test_doctor.py` is harmless and may stay, but do not cite a coupling that does not exist.
  - Depends on: E-06, E-09
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `cli._install_leftover_disposition` is the single resolver for all three install-time migration call sites (plan `z1yefm` E-01); `je74a0` E-05 adds the saved `defaults.leftovers` read to it with the built-in default left at `defer`, and E-06/E-07 of that plan edit `tests/test_installer.py`'s `InstallLeftoverDispositionThreadingTests`.
- `remove` safety lives in `layout_migration.MigrationManager._is_removable_leftover` (local lanes, `untracked`, `.agents/skills` via `_skills_prefix`, `check-ignore`, then git tracking) plus `is_stale_tool_litter` for untracked `.pyc`/`__pycache__` under `.agents/workflows/`; `_handle_leftovers` scans only `_LEGACY_LEFTOVER_ROOTS = (".agents", "workflow-artifacts")`.
- `aw migrate-layout` resolves its own disposition in `cli._run_migrate_layout` (`cli_leftovers or config_leftovers or "defer"`) and does not call `_install_leftover_disposition`.
- The migration spec (`implemented`) states the non-interactive default is `defer`; changing a behavior a spec describes requires a declared spec amendment (AGENTS.md "A PLAN MAY AMEND A SPEC").
- Tests are run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`; config is isolated with `XDG_CONFIG_HOME`, the toolkit home with `AW_HOME`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `f46b6775` on 2026-09-26 with a real `MigrationManager` on scratch repos (`.agents/workflows/{VERSION,index.md}`, `.agents/plans/README.md`, `.agents/README.md`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | INFO | `_install_leftover_disposition` | Built-in default is `defer`. | `return "defer"` fall-through; spy on `_handle_legacy_migration(to_aw=True, leftovers=None)` -> `leftover_disposition='defer'` |
| F-2 | INFO | `_handle_leftovers` | `defer` leaves the tracked leftover; `remove` deletes it. | `defer ['.agents/README.md']`, `remove []` |
| F-3 | HIGH | `_is_removable_leftover` | `remove` deletes a staged-never-committed leftover, which then exists nowhere in history. | after `git add` of an uncommitted `.agents/README.md`: `remove []`; `git log --all -- .agents/README.md` -> none |
| F-4 | HIGH | `_is_removable_leftover` + `git rm -f` | `remove` discards uncommitted edits to a tracked leftover. | committed `r`, worktree `UNCOMMITTED EDIT`: `remove []`; `git show HEAD:.agents/README.md` -> `r` |
| F-5 | INFO | `_is_removable_leftover` | Untracked content is preserved. | a `git rm --cached` leftover survives `remove`: `remove ['.agents/README.md']` |
| F-6 | MEDIUM | migration spec Section 3 and step 9 | The implemented spec pins the non-interactive default to `defer` ("never deletes without an explicit choice"), which the ruling changes for install-driven migrations. | the two quoted sentences |
| F-7 | INFO | `vv6y7e` dependency | Until the classifier fix lands, any repo with `.agents/skills` refuses to migrate at all, so the flip is only observable after `vv6y7e` (reached transitively through `je74a0`). | `PreflightGateError ... 'agents:skills has unknown owner/disposition'` on the skills fixture |

Added at review (2026-09-26) at HEAD `1d013100`, on which BOTH `je74a0` and `vv6y7e` are already `executed`, so the post-dependency tree F-1..F-7 anticipated is the tree these were measured on. A real `MigrationManager.execute_migration` completed end to end on the skills-bearing fixture (F-7's gate is gone), and `_install_leftover_disposition` already contains the saved-answer read `je74a0` promised, so the gate's stop condition is satisfied.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-8 | HIGH | `tests/support.py:init_repo`, used by `InstallLeftoverDispositionThreadingTests._legacy_repo` | THE PLANNED FIXTURE HAS NO `HEAD`, WHICH WOULD MAKE THE REMOVAL CASES PASS VACUOUSLY UNDER E-02. `init_repo` runs `git init` and three `git config` calls and never commits. Under E-02 a HEAD-less repo removes nothing, so a control asserting "a clean tracked leftover IS removed" would pass because there is no HEAD, not because the code is correct. | `git rev-parse HEAD` on a `_legacy_repo`-shaped repo -> `fatal: ambiguous argument 'HEAD': unknown revision`; on that repo the CURRENT predicate says removable=False and the E-02 predicate says removable=False (`cat-file`=128, `diff`=128), so both agree for the WRONG reason |
| F-9 | HIGH | `cli._handle_legacy_migration` / `cli._split_brain_guard` success branches | THE DELETION IS ENTIRELY SILENT. A full `aw install <repo> --to-aw --yes` that deleted a tracked `.agents/README.md` printed hundreds of `[added ]` lines and the success line `migrated legacy layout to .aw/`; the strings "leftover", "remove", "delete" appeared NOWHERE in captured stdout+stderr. `execute_migration` itself printed the empty string. | captured output searched for each keyword: all three `NOT MENTIONED`; leftover file gone = True |
| F-10 | INFO | `_handle_leftovers` return value and `execute_migration`'s transaction | THE REPORT E-08 NEEDS COSTS NO NEW PLUMBING. The classified lists are already returned and already persisted. | transaction read back after a real migration: `{"disposition": "remove", "leftovers": [...], "preserved": [".agents/skills/assess/SKILL.md"], "removed": [".agents/README.md"], "stale_tool_litter": []}` |
| F-11 | INFO | `agent_workflows/doctor.py` | E-07's DOCTOR COUPLING CLAIM IS FALSE. `_is_removable_leftover` has exactly one caller in the package (`_handle_leftovers`); `doctor.py` never imports `layout_migration`, and `tests/test_doctor.py` contains no `removable` reference. The genuinely coupled files are `tests/test_layout_inventory.py` (five `leftover_disposition="remove"` calls) and `tests/test_layout_migration.py`. | `grep -rn "_is_removable_leftover" agent_workflows/` -> 4 hits, all in `layout_migration.py`; `grep -rn "MigrationManager\|layout_migration" agent_workflows/doctor.py` -> no output |
| F-12 | INFO | E-02's proposed predicate, all five cases | E-02'S EXACT COMMAND PAIR IS CORRECT AS SPECIFIED. Probed directly: clean tracked -> removable; worktree-modified -> preserved; STAGED-modified -> preserved; staged-never-committed -> preserved; HEAD-less repo -> preserved. It also survives the real migration context: instrumented at the moment `_handle_leftovers` calls the predicate DURING a live `execute_migration`, the clean leftover still measured `cat-file=0 diff=0`, so the migration's own staged renames do not dirty the leftover's own diff and the flip is not a silent no-op. A mode-only change and a clean symlink both behave sensibly (mode change -> preserved; clean symlink -> removable). | the five-case probe plus the in-migration instrumentation, both re-run at review |
| F-13 | INFO | `aw specs note` on an `implemented` spec | E-06(c)'s CONTINGENCY IS UNNECESSARY BUT HARMLESS. On a scratch COPY of the target spec the verb exited 0 and prepended the record; the spec also already carries a `2026-09-25 note (aw specs)` amendment record, so there is precedent. | `rc = 0` and the new record visible at the head of `## Workflow history` on the copy (the tracked spec was NOT touched) |

## Proposed changes (ordered, validatable)

1. E-01 re-measures on the post-`je74a0` tree, including both loss cases.
2. E-02 restricts `remove` to leftovers recoverable unchanged from `HEAD`.
3. E-03 tests the safety cases (failing first) and the controls, on a fixture that COMMITS.
4. E-04 flips the built-in default to `remove`, fail-safe on junk. GATED ON OQ-02 (blocking).
5. E-05 tests the default end to end and repairs the old-default assertions.
6. E-08 reports what was deleted; E-09 tests that report.
7. E-06 help text, CHANGELOG, and the declared spec amendment.
8. E-07 bare suite before and after.

STEPS 1 to 3 ARE INDEPENDENT OF OQ-02 AND ARE THE SAFETY HALF OF THIS PLAN. E-02's tightening is a strict improvement to an EXISTING explicit `--leftovers remove` and to `aw migrate-layout --leftovers remove`, both of which can destroy unrecoverable content today (F-3, F-4). It needs no ruling and could ship alone. Only steps 4 onward turn a default destructive, and those are what OQ-02 gates.

## Deferred / out of scope (with reason)

- Changing `aw migrate-layout`'s non-interactive default.
  - Carrier-Declined: the ruling covers the install-driven migration only (OQ-02); the migrate-layout wizard has its own interactive leftover step listing "[3] remove: Permanently delete leftover legacy files after move", so a user of that verb is shown the choice. Note E-02 still makes that verb's EXPLICIT `--leftovers remove` safer, which is a benefit and not a scope change.
- Adding the interactive leftover PROMPT that install lacks (OQ-02 option iii, and backlog `kapm7y`'s territory).
  - Carrier-Declined: this needs no separate carrier because it is not an obligation this plan defers past its own execution; it is one of the three OPTIONS of BLOCKING open question OQ-02, which gates E-04 and therefore gates this plan reaching `executed` at all. The obligation lives in the question, which the lint gate refuses (`IPD-Q501`) until the maintainer answers. If they choose option (iii), this plan is the wrong vehicle (a prompt is a new interaction surface with its own remember-the-answer behavior, which is `je74a0`'s pattern, not a default flip) and the plan should be re-scoped or superseded rather than grown. Recorded here so the choice has a visible home beside the other two.

## Scope check

- Over-scope: E-02 (`layout_migration.py`) is beyond the item's literal "one-line change", and is required: the ruling authorizes a destructive default on the stated premise that `remove` deletes only what history can restore, and F-3/F-4 show that premise is false today. Shipping the flip without E-02 would delete unrecoverable content by default. E-08/E-09 (the deletion report) are likewise beyond the literal item and are justified in E-08: a destructive default the user is never told about cannot be acted on, and F-9 measured the operation as entirely silent.
- Under-scope: `agent_workflows/config.py` is NOT declared: `je74a0` owns the `defaults.leftovers` key.
- Scope-Paths justification: `cli.py` (resolver, help, comment, and the three success branches E-08 touches), `layout_migration.py` (E-02), `CHANGELOG.md`, `tests/test_installer.py` (the file `rg -l _install_leftover_disposition tests` returns), and the migration spec (E-06c). NOTE `tests/test_layout_inventory.py` and `tests/test_layout_migration.py` are RUN by E-07 but are NOT expected to need edits (their fixtures commit, so E-02 preserves their behavior: verified at review); if either does need an edit, take the `--scope-reason` at finalize.

## Required tests / validation

- `tests/test_installer.py`: new class with safety cases (a), (b), (b2) FAILING before E-02, controls (c) to (e), end-to-end default cases (f) to (i) with (f) FAILING before E-04, and report cases (j) to (l) with (j) failing before E-08; repaired old-default assertions (including the "Clear restores built-in default" one the plan originally missed). Every case that asserts a REMOVAL must use a fixture that COMMITS, or it is vacuous (F-8).
- `python3 -m pytest tests/test_installer.py tests/test_layout_inventory.py tests/test_layout_migration.py -o addopts="" -q`.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- SPEC AMENDMENT, DECLARED: `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` is in `- Scope-Paths:`. WHY: its Section 3 bullet and step 9 state a non-interactive default of `defer` that "never deletes without an explicit choice"; after this plan an install-driven migration removes recoverable leftovers by default, so leaving the spec unamended would make every later plan reviewed against a contract the code contradicts. The amendment is narrow: `aw migrate-layout` keeps `defer`, and the install-driven default is scoped to leftovers recoverable unchanged from `HEAD`, which is the maintainer's 2026-09-26 ruling and its stated premise.
- `CHANGELOG.md` and the install `--help` text (E-06).
- `README.md` needs no change: its only `--leftovers` mentions are `aw migrate-layout` examples.

## Open questions

### OQ-01: With nothing saved, what should an unattended install-time migration do with leftovers?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: `remove`. Maintainer ruling 2026-09-26 (recorded on backlog `6kczjg`): "with nothing saved, an unattended aw install --to-aw migration defaults --leftovers to REMOVE (git-tracked leftovers only, recoverable from history; untracked content, private lanes and skills are preserved). Ordered after je74a0, which adds the saved defaults.leftovers answer." E-02 exists so the parenthetical premise is actually true (F-3, F-4).

### OQ-02: Does the new default also apply to `aw migrate-layout` and to the interactive install paths?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Carrier-Declined: this question cannot outlive the plan, so there is nothing for a carrier to catch. It is `Blocking: yes`, which makes `aw ipd lint` refuse at EVERY checkpoint (`IPD-Q501`, verified at review: `review-finalize` exits 1 naming it), so the plan cannot reach `executed` while it is open and the obligation cannot silently class `done` in `aw attention`. Either the maintainer answers it, and it becomes `resolved` with a rationale, or the plan does not execute. Should the answer instead be "do something other than flip the default" (option ii or iii), the correct response is to re-scope or supersede this plan, and THAT successor is the durable record, not a carrier filed now against a decision nobody has made yet.
- Resolution or deferral rationale: OPEN, REOPENED AT REVIEW, and BLOCKING because only the maintainer can widen their own ruling. `aw migrate-layout`: NO, and that half is settled (the ruling names the install migration, that verb resolves its disposition separately in `cli._run_migrate_layout` as `cli_leftovers or config_leftovers or "defer"`, and it has its own interactive leftover step listing "[3] remove: Permanently delete leftover legacy files after move"). THE INTERACTIVE INSTALL HALF IS NOT SETTLED. The maintainer's ruling, quoted verbatim on backlog `6kczjg`, is scoped to an UNATTENDED install: "with nothing saved, an unattended aw install --to-aw migration defaults --leftovers to REMOVE". This plan's own title and `- Concern:` say "unattended" too. But `cli._install_leftover_disposition` is consulted by all three call sites including the INTERACTIVE confirm-to-migrate branch (`_handle_legacy_migration` after `_ask_policy` returns True on a TTY) and the interactive split-brain migrate-now branch, so flipping the built-in default silently makes an INTERACTIVE, ATTENDED install destructive by default as well. The author's reasoning (they share one resolver by design, and install has no leftover prompt) is sound ENGINEERING but it is an extension of the ruling's stated scope, and it is exactly the kind of decision AGENTS.md reserves for the human (risk appetite on a destructive default). WHAT THE MAINTAINER MUST CHOOSE: (i) ACCEPT the widening, so any install-driven migration with nothing saved removes recoverable leftovers, interactive or not (simplest, one resolver, no drift, and what this plan currently implements); or (ii) SCOPE IT to unattended only, which means the resolver must learn whether the run is attended (an `assume_yes`/`isatty` signal, as `_ask_policy` already computes) and return `defer` when a human is present to be asked; or (iii) ASK in the interactive case, adding the leftover prompt install currently lacks, which is the shape the maintainer's earlier OQ-01 ruling on `6kczjg` favored for policy questions ("a policy question like this should ASK, with the prompt DEFAULTING TO THE ENCOURAGED ACTION"). Note (iii) is close to what backlog `kapm7y` was for. Until this is answered, E-04 must not be executed: the GENUINE STOP CONDITION in the gate now names it.

### OQ-03: What should an explicitly present but unrecognized value resolve to?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `defer`, from repository precedent: the resolver's current junk case (`leftovers="rm -rf"`) returns the non-destructive value, and `je74a0`'s `normalize` drops an out-of-enum saved value "rather than kept or raised". A value nobody validly chose must never select the destructive disposition; only ABSENCE selects the ruled default.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the resolver as read, the surviving `.agents/` files for cases (1) to (4), the `git log`/`git show` outputs for (3) and (4), and the disposition the unattended install used.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `_is_removable_leftover` diff and re-run E-01 cases (2) to (4), showing (2) still removes and (3), (4) now preserve with the file listed under `preserved`. ALSO paste the STAGED-MODIFIED case (commit the leftover, edit it, `git add` it) preserving, and one run proving the tightening is NOT a silent no-op inside a real migration: instrument the predicate (or print the two git exit codes) at the moment `_handle_leftovers` calls it DURING a live `execute_migration` on the clean-leftover fixture, showing `cat-file=0 diff=0` so a clean leftover is still removable in context (review F-12 measured exactly this at HEAD `1d013100`; reproduce it after the change).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_installer.py -o addopts="" -q -k LeftoverDefault` BEFORE E-02 showing (a), (b), (b2) FAILING and (c) to (e) passing, then after E-02 all passing. ALSO prove the removal controls are NOT vacuous: paste `git rev-parse HEAD` inside the (c) fixture showing a real commit sha (a HEAD-less fixture would pass (c) for the wrong reason, F-8).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the resolver diff and a `python3 -c` run showing the five expected results (absent attr, `None`, saved `defer`, `keep`, junk).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the E-03 class passing with (f) to (i), (f) failing against the pre-E-04 resolver, and the diff of the repaired `InstallLeftoverDispositionThreadingTests` assertions showing only absent-value expectations changed (the diff MUST include the "Clear restores built-in default" assertion). Paste the split-brain `MagicMock` test passing UNEDITED, and `git diff --stat` for that test showing no change to it.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new `aw install --help` `--leftovers` text, the CHANGELOG diff, a dash grep over both showing no em or en dash, the spec diff, and the `aw specs note` output (or refusal).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and the narrowed `tests/test_installer.py tests/test_layout_inventory.py tests/test_layout_migration.py` run.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the captured stdout+stderr of an unattended `aw install <legacy repo> --to-aw --yes` that removed a leftover, showing the one report line with the count and the recovery hint; grep that same output for the leftover's path or the word "removed" showing a HIT (the pre-change run showed all of "leftover", "remove", "delete" as NOT MENTIONED, F-9, so paste that contrast). Also paste a `keep`/`defer` run showing NO report line.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the (j) to (l) tests passing, and (j) failing before E-08 with its assertion message.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Three changes, and ONE DECISION THE PLAN CANNOT MAKE FOR YOU.

FIRST, a safety tightening (E-02, needs no ruling): `remove` deletes a legacy leftover only if git can give it back unchanged (it exists in `HEAD` and has no staged or unstaged edits). Today it also deletes never-committed files and DISCARDS UNCOMMITTED EDITS, measured end to end through a real migration at review: a staged-never-committed leftover was deleted and then existed nowhere in history, and a committed leftover with a local edit was deleted leaving only the old content in `HEAD`. This improves an EXISTING explicit `--leftovers remove` (and `aw migrate-layout --leftovers remove`) whether or not you approve the default flip.

SECOND, the ruled default flip (E-04): with nothing saved, an install-time migration uses `remove` instead of `defer`; a saved `defaults.leftovers` or an explicit `--leftovers` still wins, and an invalid value falls back to `defer`. `aw migrate-layout` is unchanged.

THIRD, a deletion REPORT (E-08, added at review): the operation is currently SILENT. A real unattended install that deleted a tracked file printed hundreds of `[added ]` lines and never once said "leftover", "remove", or "delete". A default that destroys files without telling you cannot be acted on, even when the files are technically recoverable, so the flip now comes with one line naming what was removed and how to restore it. The data is already recorded on the migration transaction, so this is a report, not new bookkeeping.

THE DECISION (OQ-02, BLOCKING, needs your answer before E-04 runs): your ruling says "an UNATTENDED aw install --to-aw migration", and this plan's title says unattended too, but the resolver being changed is shared by all three install-time call sites INCLUDING the interactive confirm-to-migrate and interactive split-brain branches. So flipping the built-in default also makes an ATTENDED, interactive install destructive by default. That may be exactly what you want (one resolver, no drift), but it is wider than what you ruled, so the plan does not assume it. The three options are laid out in OQ-02: accept the widening, restrict it to unattended runs (the resolver would learn the attended signal `_ask_policy` already computes), or add the leftover prompt install currently lacks (closest to your earlier "a policy question should ASK, defaulting to the encouraged action" ruling, and near backlog `kapm7y`'s territory).

The install help, the CHANGELOG and the migration spec (a declared amendment) are updated to match. Graduates backlog `6kczjg` (a decision chore; no release gate) and runs after `je74a0`, which adds the saved answer to the same resolver (VERIFIED at review: the saved-answer read is present, and both `je74a0` and `vv6y7e` are already executed).

Scope fence (a DECLARATION for reconciliation, not a stop directive): `cli._install_leftover_disposition`, the install `--leftovers` help and its comment, and the three post-migration success branches E-08 reports from (`_handle_legacy_migration` x2, `_split_brain_guard` x1); `layout_migration.MigrationManager._is_removable_leftover`; one CHANGELOG bullet; `tests/test_installer.py`; the migration spec's two default sentences. An edit outside the declared paths, if one proves necessary, is made and then justified at finalize with `--scope-reason` per out-of-scope path; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-03, V-05 and V-09 must show the new tests FAILING before their fixes, and V-03 must additionally show its removal fixture has a real `HEAD` so the control is not vacuous.

DO NOT MUTATE THE TRACKED SPEC WHILE PROBING. E-06(c) edits the spec deliberately, which is correct; any exploratory `aw specs note` run to see whether the verb refuses must be done on a COPY in a scratch repo (review did exactly that and left the tracked file untouched, F-13).

GENUINE STOP CONDITIONS, both of which leave the plan unexecuted and reported rather than partially applied:
1. OQ-02 IS UNANSWERED (blocking). Do NOT execute E-04 or anything downstream of it (E-05, E-06, E-08, E-09) until the maintainer picks one of its three options. E-01, E-02 and E-03 are independent of it and MAY proceed: they only make an already-available destructive option safer. If you stop here, say so plainly and name OQ-02.
2. If E-01 shows `je74a0` did not land the saved-answer read in `_install_leftover_disposition`, do not flip the default (the opt-out the ruling promises would not exist); report instead. VERIFIED SATISFIED at review on HEAD `1d013100`, so this is a re-check, not an expected blocker.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `6kczjg` `done` with `--evidence` citing the executed plan.
