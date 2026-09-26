# IPD: Default the unattended install-time leftover disposition to remove when nothing is saved

- Date: 2026-09-26
- Kind: child
- Concern: AN UNATTENDED INSTALL-TIME MIGRATION LEAVES STALE LEGACY FILES BEHIND BY DEFAULT. Every install-time migration call site (`cli._handle_legacy_migration`'s `--to-aw` and interactive-confirm branches, and `cli._split_brain_guard`'s migrate-now branch) reads `cli._install_leftover_disposition`, which returns `defer` when `--leftovers` is absent. Measured at HEAD `f46b6775` on a scratch legacy repo carrying a tracked `.agents/README.md` leftover: a real `MigrationManager.execute_migration(leftover_disposition="defer")` leaves `.agents/README.md` in place, `remove` deletes it. The maintainer ruled on 2026-09-26 that with nothing saved the default is `remove` (OQ-01). THE RULING RESTS ON A PREMISE THE CODE DOES NOT FULLY HONOR, measured on the same scratch shape: `layout_migration.MigrationManager._is_removable_leftover` treats "tracked" as `git ls-files --error-unmatch` (in the INDEX), so `remove` (a) deletes a leftover that was `git add`ed but never committed, which then exists nowhere in history, and (b) runs `git rm -f` on a tracked leftover carrying UNCOMMITTED edits, discarding them (HEAD keeps only the old content). Flipping the default makes both losses happen without anyone choosing `remove`, so this plan makes the premise true before flipping.
- Scope: IN: (a) tighten `_is_removable_leftover` so `remove` deletes a path only if it exists in `HEAD` and is unmodified against `HEAD` (index and worktree), which is exactly "recoverable from history"; everything else is preserved; (b) change the built-in default in `cli._install_leftover_disposition` from `defer` to `remove`, keeping precedence explicit `--leftovers` > saved `defaults.leftovers` (added by `je74a0`) > built-in, and keeping an unrecognized explicit value fail-safe at `defer` (OQ-03); (c) update the install `--leftovers` help (it promises "Never deletes without an explicit 'remove'") and the resolver's docstring; (d) a CHANGELOG entry; (e) amend the migration spec's non-interactive-default sentences for the install-driven case, declared; (f) behavioral tests and the existing tests that pin the old default. OUT: `aw migrate-layout`'s own default (its `_run_migrate_layout` resolution stays `defer`, OQ-02); any prompt for the disposition; the classifier (`vv6y7e`).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/layout_migration.py, CHANGELOG.md, tests/test_installer.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: executed:je74a0
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: 6kczjg
- Set: setprompt
- Order: 3
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: o7k6lt

## Workflow history

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

- [ ] E-03 ADD BEHAVIORAL TESTS to `tests/test_installer.py` in a new class (for example `InstallLeftoverDefaultRemoveTests`), driving the REAL `MigrationManager` and real `cli._handle_legacy_migration` on `git init` repos (NO mocking of `MigrationManager`; behavior only, no source-text or AST pins, per the 2026-09-26 test-policy ruling), reusing `InstallLeftoverDispositionThreadingTests`' `_legacy_repo` shape extended with `.agents/skills/assess/SKILL.md` (every real legacy repo has it, per je74a0 E-06). Safety cases, written BEFORE E-02 and shown failing: (a) a staged-never-committed leftover SURVIVES `remove`; (b) a committed leftover with an uncommitted edit SURVIVES `remove` with its edit intact. Controls passing before and after: (c) a clean committed leftover is removed by `remove`; (d) an untracked file under `.agents/` survives (an untracked leftover that the classifier accepts, for example under `.agents/plans/untracked/`, which migrates or is preserved, never deleted); (e) `.agents/skills/assess/SKILL.md` survives byte-identical.
  - Depends on: E-01
  - Expected outcome: (a) and (b) FAIL before E-02 and pass after; (c), (d), (e) pass throughout.
  - Execution state: pending

### Task group 3: flip the default

- [ ] E-04 CHANGE THE BUILT-IN DEFAULT in `cli._install_leftover_disposition` from `defer` to `remove`. Precedence after the change: an explicit `--leftovers` value in `("keep", "remove", "defer")` wins; else the saved `defaults.leftovers` from `je74a0` wins; else, when the value is ABSENT (attribute missing or `None`), return `remove`; an explicitly present but UNRECOGNIZED value returns `defer` (OQ-03). Rewrite the docstring, which today says "It DEFAULTS to `defer` ... nothing becomes destructive without an explicit `--leftovers remove`", to state the new default, the maintainer ruling of 2026-09-26, and why it is safe (E-02). Update the `z1yefm` comment above the install `--leftovers` argument that says "The DEFAULT stays `defer`".
  - Depends on: E-02
  - Expected outcome: `_install_leftover_disposition(Namespace(leftovers=None))` and `(Namespace())` return `remove` with nothing saved; saved `defer` returns `defer`; `--leftovers keep` returns `keep`; `leftovers="rm -rf"` returns `defer`.
  - Execution state: pending

- [ ] E-05 TEST THE NEW DEFAULT END TO END and repair the tests that pin the old one. In the E-03 class, with `XDG_CONFIG_HOME` isolated: (f) `aw install <legacy repo> --to-aw --yes` with NOTHING saved removes a clean tracked leftover; (g) after `aw config set defaults.leftovers defer`, the same install KEEPS it; (h) `--leftovers defer` on the command line keeps it even with `remove` saved; (i) the untracked file and `.agents/skills` survive in (f). Then update, without weakening, the existing assertions that encode the old built-in default: in `InstallLeftoverDispositionThreadingTests`, the resolver assertions `_install_leftover_disposition(self._args())` and `(argparse.Namespace())` expecting `defer`, and the `(None, "defer")` rows in `test_migration_paths_thread_requested_disposition`; re-read them after `je74a0` E-06/E-07 (which also edits this class) and change only the absent-value expectations to `remove`. The split-brain test that passes a `MagicMock` `args` and asserts `leftover_disposition="defer"` exercises the present-but-unrecognized branch, so it should still pass unchanged; confirm rather than edit it.
  - Depends on: E-04
  - Expected outcome: (f) to (i) pass; (f) FAILS against the pre-E-04 resolver; the repaired assertions pass and name `remove`.
  - Execution state: pending

### Task group 4: contract and user-facing text

- [ ] E-06 UPDATE THE CONTRACT AND USER TEXT. (a) Install `--leftovers` help in `cli._build_parser`: replace "or defer (record for a later cleanup; the default). Never deletes without an explicit 'remove'." with text saying `remove` is the default when nothing is saved, that it deletes only leftovers git can restore unchanged, and how to opt out (`--leftovers defer`, or `aw config set defaults.leftovers defer`). Leave `aw migrate-layout`'s `--leftovers` and `--yes` help unchanged (OQ-02). (b) `CHANGELOG.md`, `## 2.0.0 (pending)` list: one `- Changed:` bullet announcing that an install-time layout migration now removes leftover legacy files by default when you have not saved a preference, that only files git can restore unchanged are removed, that untracked files, private lanes and `.agents/skills` are never touched, and the two opt-outs. USER-FACING PROSE: no em or en dashes. (c) AMEND the migration spec (declared): in `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`, the Section 3 bullet "with a non-interactive default of `defer` that never deletes without an explicit choice" and step 9 "non-interactive default `defer`, which never deletes without an explicit choice": keep `defer` for `aw migrate-layout`, and state that an install-driven migration's default is the saved answer, else `remove` restricted to leftovers recoverable unchanged from `HEAD` (maintainer ruling 2026-09-26). Record it with `aw specs note <spec path> --message "..."` naming `o7k6lt`; if that verb refuses on an `implemented` spec, paste the refusal and add no history line.
  - Depends on: E-04
  - Expected outcome: `aw install --help` shows the new text; the CHANGELOG bullet exists with no dashes; the spec sentences match the shipped behavior.
  - Execution state: pending

- [ ] E-07 RUN THE BARE SUITE `python3 -m pytest` before (at E-01) and after E-06 and compare failing node IDs; also `python3 -m pytest tests/test_installer.py tests/test_doctor.py tests/test_layout_inventory.py -o addopts="" -q`, since `_is_removable_leftover` also backs the doctor residue view's expectations.
  - Depends on: E-06
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

## Proposed changes (ordered, validatable)

1. E-01 re-measures on the post-`je74a0` tree, including both loss cases.
2. E-02 restricts `remove` to leftovers recoverable unchanged from `HEAD`.
3. E-03 tests the safety cases (failing first) and the controls.
4. E-04 flips the built-in default to `remove`, fail-safe on junk.
5. E-05 tests the default end to end and repairs the old-default assertions.
6. E-06 help text, CHANGELOG, and the declared spec amendment.
7. E-07 bare suite before and after.

## Deferred / out of scope (with reason)

- Changing `aw migrate-layout`'s non-interactive default.
  - Carrier-Declined: the ruling covers the install-driven migration only (OQ-02); the migrate-layout wizard has its own interactive leftover step.

## Scope check

- Over-scope: E-02 (`layout_migration.py`) is beyond the item's literal "one-line change", and is required: the ruling authorizes a destructive default on the stated premise that `remove` deletes only what history can restore, and F-3/F-4 show that premise is false today. Shipping the flip without E-02 would delete unrecoverable content by default.
- Under-scope: `agent_workflows/config.py` is NOT declared: `je74a0` owns the `defaults.leftovers` key.
- Scope-Paths justification: `cli.py` (resolver, help, comment), `layout_migration.py` (E-02), `CHANGELOG.md`, `tests/test_installer.py` (the file `rg -l _install_leftover_disposition tests` returns), and the migration spec (E-06c).

## Required tests / validation

- `tests/test_installer.py`: new class with safety cases (a), (b) FAILING before E-02, controls (c) to (e), and end-to-end default cases (f) to (i) with (f) FAILING before E-04; repaired old-default assertions.
- `python3 -m pytest tests/test_installer.py tests/test_doctor.py tests/test_layout_inventory.py -o addopts="" -q`.
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

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `aw migrate-layout`: NO; the ruling names the install migration, and that verb resolves its disposition separately (`_run_migrate_layout`) with its own interactive leftover step. Interactive install paths (confirm-to-migrate and split-brain migrate-now): YES, because they share the one resolver by design (`z1yefm`: "so they cannot drift apart") and install offers no leftover prompt, so there is no interactive answer to prefer.

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
  - Required evidence: paste the `_is_removable_leftover` diff and re-run E-01 cases (2) to (4), showing (2) still removes and (3), (4) now preserve with the file listed under `preserved`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_installer.py -o addopts="" -q -k LeftoverDefault` BEFORE E-02 showing (a), (b) FAILING and (c) to (e) passing, then after E-02 all passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the resolver diff and a `python3 -c` run showing the five expected results (absent attr, `None`, saved `defer`, `keep`, junk).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the E-03 class passing with (f) to (i), (f) failing against the pre-E-04 resolver, and the diff of the repaired `InstallLeftoverDispositionThreadingTests` assertions showing only absent-value expectations changed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new `aw install --help` `--leftovers` text, the CHANGELOG diff, a dash grep over both showing no em or en dash, the spec diff, and the `aw specs note` output (or refusal).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and the narrowed installer/doctor/inventory run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Two coupled changes. FIRST, a safety tightening: `remove` now deletes a legacy leftover only if git can give it back unchanged (it exists in `HEAD` and has no staged or unstaged edits). Today it also deletes never-committed files and discards local edits (measured). SECOND, the ruled default flip: with nothing saved, an install-time migration uses `remove` instead of `defer`; a saved `defaults.leftovers` or an explicit `--leftovers` still wins, and an invalid value falls back to `defer`. `aw migrate-layout` is unchanged. The install help, the CHANGELOG and the migration spec (a declared amendment) are updated to match. The first change is DELIBERATELY broader than the item: it also makes an explicit `--leftovers remove` safer, and without it the ruled default would destroy unrecoverable content. Graduates backlog `6kczjg` (a decision chore; no release gate) and runs after `je74a0`, which adds the saved answer to the same resolver.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `cli._install_leftover_disposition`, the install `--leftovers` help and its comment; `layout_migration.MigrationManager._is_removable_leftover`; one CHANGELOG bullet; `tests/test_installer.py`; the migration spec's two default sentences. An edit outside the declared paths, if one proves necessary, is made and then justified at finalize with `--scope-reason` per out-of-scope path; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-03 and V-05 must show the new tests FAILING before their fixes.

GENUINE STOP CONDITION: if E-01 shows `je74a0` did not land the saved-answer read in `_install_leftover_disposition`, do not flip the default (the opt-out the ruling promises would not exist); report instead.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `6kczjg` `done` with `--evidence` citing the executed plan.
