# IPD: Installer rollback: unique per-run backup directory (same-second collision fix)

- Date: 2026-08-15
- Kind: child
- Concern: The installer keys each backup directory on a seconds-granularity timestamp, so two install runs within the same wall-clock second collide into one backup directory, corrupting `--undo` rollback fidelity (backlog qver7w; `test_rollback_undo` ~50% flake).
- Scope: The installer backup-directory naming/selection in `agent_workflows/engine.py` and a deterministic regression test. Rollback semantics for the normal (distinct-second) case are unchanged.
- Status: executed
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 4o5lt9

## Workflow history

- 2026-08-15 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created as a corrective IPD for backlog qver7w, discovered while capturing the plan-11 self-migration baseline (test_rollback_undo ~50% flake).
- 2026-08-15 approved (human maintainer via chat, recorded by opencode Opus 4.8): Status draft -> approved; cleared to execute.
- 2026-08-15 executed (opencode Opus 4.8 orchestrator, its_direct/pt3-claude-opus-4.8-1m-us): implemented E-01/E-02 in commit e25eacc (agent_workflows/engine.py + tests/test_installer.py); V-01/V-02 verified with concrete evidence incl. mutation probes RED against both halves of the fix and the full serial suite Ran 937 tests OK (skipped=1). Pre-transition lint conforming. Status approved -> executed; moved to executed/.

## Goal

Guarantee that each installer run writes its backups and its `.created-files.json` record into a distinct backup directory even when multiple runs happen within the same wall-clock second, so `--undo` always rolls back exactly the most recent run. This removes the ~50% non-determinism in `test_rollback_undo` and closes a real rollback-fidelity bug that undermines the plan-11 self-migration rehearsal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Fix the backup-directory collision

- [x] E-01 Introduce a single per-run backup-directory token in `agent_workflows/engine.py` that is unique against any already-existing backup directory (append a monotonic `-NN` suffix when the seconds-granularity name is already taken), compute it once at the start of an install run, and thread that one token through every same-run backup site (`install_all`, orphan prune, `.gitignore` safety, layout migrate, and the `.created-files.json` record write) so a run never reuses a prior run's directory; keep `run_rollback` selecting the lexically-latest directory that carries a `.created-files.json` record.
  - Depends on: none
  - Expected outcome: Two installer runs in the same second write to two distinct backup directories; `--undo` restores exactly the state captured before the most recent run.
  - Execution state: performed

### Task group 2: Lock it with a deterministic regression test

- [x] E-02 Add a deterministic regression test that forces two install runs to share the same seconds-granularity timestamp (patch the timestamp clock) and asserts `--undo` restores the pre-most-recent-run content, plus a same-second collision assertion on the backup directory set; prove the test fails against the pre-fix behavior (mutation probe) and passes against the fix.
  - Depends on: E-01
  - Expected outcome: A test that is RED on the old same-second-collision behavior and GREEN on the fix, and is order-independent (no flake).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Backups live under `.agent-workflows-installer-backups/<timestamp>/` (`engine.py` `BACKUPS_DIR`, `create_backup_path`).
- A single install run already issues several independent `datetime.now()` calls (install_all :1620, orphan prune :1712, layout migrate :1997, gitignore :2227, record write :2591); `2f261ec` made `run_rollback` prefer the latest dir that carries a `.created-files.json` so an intra-run cross-second split does not lose the created-files list.
- `write_file` (:1554) backs up an existing, differing destination with `shutil.copy2` into `BACKUPS_DIR/<timestamp>/<rel>`, overwriting any file already at that backup path.
- Tests are stdlib `unittest`; the end-to-end installer tests run `install-workflows.py` as a subprocess (`tests/support.py:run_installer`).

## Findings

- `test_installer.InstallerEndToEndTests.test_rollback_undo` fails ~6/12 runs under both plain `unittest` and `pytest -n auto`; it passes when the two installs cross a 1-second boundary.
- Root cause: the two install runs in the test can share one `%Y%m%d-%H%M%S` directory. Run 1 (fresh install) writes a `.created-files.json` listing every file as created; run 2 (overwrite of a user-modified `index.md`) backs up the modified content and rewrites the record in the SAME directory. On `--undo`, the merged directory does not represent a single run, so the restored `index.md` is wrong.
- This is distinct from the `2f261ec` fix (which addressed record-less latest-dir selection WITHIN one run); this is a cross-run directory collision.
- Blast radius: the fix touches backup-directory naming used by the install/update/undo path; it must not change rollback behavior for the normal distinct-second case.

## Proposed changes (ordered, validatable)

1. Add a helper (e.g. `allocate_backup_timestamp(repo_root)`) that returns `datetime.now().strftime("%Y%m%d-%H%M%S")`, and if `BACKUPS_DIR/<name>` already exists, appends the smallest `-NN` (2-digit) suffix that does not yet exist; the returned token is the run's single backup directory name.
2. Compute the token once per install invocation and pass it to all same-run backup sites so they share one directory; a new run computes a new (guaranteed-distinct) token.
3. Leave `run_rollback`'s "latest dir with a `.created-files.json`" selection intact (it now selects the correct single-run directory because runs no longer merge).
4. Add the deterministic regression test (E-02).

## Deferred / out of scope (with reason)

- Redesigning the backup/undo model or retention/pruning policy: out of scope; this is a targeted collision fix.
- Changing rollback selection heuristics beyond what is needed for uniqueness: out of scope (the `2f261ec` behavior stays).

## Scope check

- Over-scope: none. The change is confined to backup-directory naming/threading plus one test.
- Under-scope: The fix must cover every same-run backup site (install_all, orphan prune, gitignore safety, layout migrate, record write) so no site can still mint a colliding directory.

## Required tests / validation

- `python3 -m unittest tests.test_installer.InstallerEndToEndTests.test_rollback_undo` run repeatedly (>=12x) with zero failures.
- The new deterministic same-second regression test: RED against pre-fix behavior (mutation probe), GREEN against the fix.
- `python3 -m unittest discover -s tests -t .` (full serial suite) green, with no regression in installer/backup/undo tests.
- `python3 -m agent_workflows check-local-leaks . --agent`.

## Spec / documentation sync

- N/A: no user-facing behavior or documented contract changes; backup directory naming is an internal implementation detail. A DECISIONS.md note is optional and not required for this fix.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The fix approach (unique per-run backup directory) is unambiguous and low-risk; no open design question blocks execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the actual output of running `test_rollback_undo` at least 12 times with zero failures, and show that two same-second install runs produce two distinct `.agent-workflows-installer-backups/<name>` directories. Failure condition: any run restores the wrong content, or two same-second runs share one backup directory.
  - Observed evidence: Before the fix, `for i in $(seq 1 16); do python3 -m unittest tests.test_installer.InstallerEndToEndTests.test_rollback_undo; done` gave `PASS=6 FAIL=6 out of 12` (~50% flake). After the fix, the 12x loop gave `test_rollback_undo: PASS=12 FAIL=0 / 12` (exit 0 each). A frozen-clock probe of two same-second install runs produced two distinct backup directories `['20260815-120000', '20260815-120000-01']` (dir `120000` carried the created-files record; dir `120000-01` carried the index.md backup), confirming same-second runs no longer collide into one directory. Full serial suite: `python3 -m unittest discover -s tests -t .` -> `Ran 937 tests in 173.725s / OK (skipped=1)`; parallel `pytest -n auto` -> `936 passed, 1 skipped` (previously 1 failed on the flake).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Paste the new regression test passing, AND the mutation-probe output showing it FAILS when the fix is reverted (same-second collision reintroduced). Failure condition: the test passes against the pre-fix behavior (i.e. it cannot catch the collision).
  - Observed evidence: New tests `tests.test_installer.SameSecondBackupCollisionTests` (`test_same_second_runs_use_distinct_backup_dirs_and_undo_restores_latest`, `test_allocate_backup_timestamp_is_unique_against_existing_dirs`) GREEN: `Ran 2 tests in 1.492s / OK`. Mutation probe 1 (revert `allocate_backup_timestamp` uniqueness to always return the naive same-second base): `FAILED (failures=1, errors=1)` - `FAIL: test_same_second_runs_...` and `ERROR: test_allocate_backup_timestamp_...`. Mutation probe 2 (revert `save_created_files_record` to skip writing an empty record): `AssertionError: False is not true : rollback removed index.md (older run's created-list won over newer backups)` -> `FAILED (failures=1)`. Fix restored (engine.py byte-identical to the fixed version: `diff ... && echo IDENTICAL` -> `IDENTICAL`) and both tests GREEN again. The test catches both halves of the fix.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: One targeted bug fix plus its regression test; a single cohesive change.

Execution requires human approval recorded as `Status: approved` with an attributed `- Approval:` line. The executor implements E-01/E-02, pastes actual command output (including the deliberate red-then-green mutation probe), commits only the explicitly scoped paths (`agent_workflows/engine.py`, `tests/test_installer.py`) with path-scoped Git commands, never pushes without confirmation, runs `aw ipd lint --phase pre-transition --agent` and the full serial suite before any transition, and the orchestrator owns the terminal move to `executed/`.
