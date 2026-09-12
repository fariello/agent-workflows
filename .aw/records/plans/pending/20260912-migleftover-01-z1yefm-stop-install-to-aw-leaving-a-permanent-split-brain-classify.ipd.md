# IPD: Stop install --to-aw leaving a permanent split-brain: let the install-time migration sweep its own empty legacy dirs

- Date: 2026-09-12
- Kind: child
- Concern: `aw install --to-aw` hardcodes the migration's leftover disposition to `defer`, so an install-driven migration can never clean up after itself. It leaves empty directories under `.agents/workflows/` plus `.agents/README.md`, which is enough to make the dual-layout detector report a permanent split-brain and make `aw doctor` advise a migration that has already run.
- Scope: Give the install-time migration path a way to reach a cleanup disposition, sweep the empty legacy directories it leaves, and stop the residue from being reported as a live split-brain layout. Includes a regression test built from the measured real-repo state.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/layout_migration.py, tests/test_layout_migration.py, tests/test_installer.py
- Item-Dependencies: none
- Status: to-review
- Set: migleftover
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: z1yefm
- From-Backlog: x15f0q
- Blocks-Release: f33nrj

## Workflow history

- 2026-09-12 to-review (opencode): authored from backlog item x15f0q; root cause verified in-tree, and the item's incorrect skills claim corrected before planning.
- 2026-09-12 draft (opencode): created.

## Goal

Make an install-driven `.agents/` to `.aw/` migration finish cleanly, so a migrated repo does not permanently report a split-brain layout and is not told to run a migration that already ran. This is the upgrade path all 27 legacy repos on the maintainer's server will take, and release 2.0.0 exists to gate exactly this migration.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Reachability of a cleanup disposition

- [ ] E-01 In `agent_workflows/cli.py`, stop hardcoding `leftover_disposition="defer"` on the install-time migration. Both call sites must be changed: the `--to-aw` path (cli.py:5241) and the interactive-confirm path (cli.py:5265-5267). Thread the value from a new `aw install` flag (`--leftovers {keep,remove,defer}`) whose DEFAULT preserves today's behavior (`defer`), so this item changes reachability only and no existing invocation changes meaning.
  - Depends on: none
  - Expected outcome: `aw install <repo> --to-aw --leftovers remove` reaches `MigrationManager.execute_migration(leftover_disposition="remove")`, while `aw install <repo> --to-aw` still passes `defer`.
  - Execution state: pending

- [ ] E-02 Declare the new `install --leftovers` flag in `command_surface.py`'s `COMMAND_INVENTORY` entry for `install` (the existing declaration is at command_surface.py:515) if the declaration enumerates flags. Verify against the conformance tests rather than assuming: `tests/test_command_surface_declarations.py` and `tests/test_cli_conformance_matrix.py` fail CI on an undeclared leaf.
  - Depends on: E-01
  - Expected outcome: both conformance tests report no NEW findings attributable to this change (see the pre-existing-baseline note in Required tests).
  - Execution state: pending

### Task group 2: Sweep the empty-directory residue

- [ ] E-03 Make the migration remove legacy directories it has emptied, under `remove`. `_handle_leftovers` already prunes only now-empty legacy directories and never `rmtree`s a root wholesale (layout_migration.py:527-541 documents this contract), so verify whether the empty-dir case is already covered by `remove` and, if it is, do NOT duplicate the logic: the defect may be purely that `remove` was unreachable (E-01). Only if a gap is proven should new pruning be added, and then modeled on the existing precedent in `engine.migrate_legacy_layout` (engine.py:2624-2636), which removes a now-empty legacy dir after moving its contents.
  - Depends on: E-01
  - Expected outcome: after a `--to-aw --leftovers remove` migration of a fixture seeded from the measured real-repo shape, zero empty directories remain under `.agents/workflows/`. If E-01 alone achieves this, record that finding explicitly and perform no code change here.
  - Execution state: pending

- [ ] E-04 Ensure `.agents/README.md` is disposed of consistently with the other leftovers under `remove`, and explicitly NOT under `defer`/`keep`. It is a tracked framework-authored file, so `_is_removable_leftover` (layout_migration.py:495-521) should already permit it on the tracked-path signal; confirm empirically rather than by reading, and record which branch decides it.
  - Depends on: E-03
  - Expected outcome: documented, tested behavior for `.agents/README.md` under each of the three dispositions.
  - Execution state: pending

### Task group 3: Regression test from the measured shape

- [ ] E-05 Add a test that seeds a fixture repo in the exact residue shape measured on the nine real repos (populated `.aw/system` plus `.agents/workflows/{assess,verify,benchmark,setup-repo}/tools` as EMPTY dirs, plus `.agents/README.md`, plus a populated `.agents/skills`), runs the install-time migration with `remove`, and asserts the repo is no longer classified as dual-layout. The test must assert `.agents/skills` SURVIVES, because it is the intended location for both layouts (engine.py:171, engine.py:174-183) and deleting it would be a real regression.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: a named test that fails against pre-fix code and passes after, and that would FAIL if a future change deleted `.agents/skills`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.agents/skills` is the INTENDED skills location for BOTH layouts, not legacy residue: `engine.SKILLS_DIR = ".agents/skills"` (engine.py:171) and `resolve_skills_dir()` returns it for the `aw` layout too (engine.py:174-183), because a skill package is discovered by a host tool scanning a fixed directory, exactly like the `.opencode/`/`.claude/` command shims. Verified: after `--to-aw`, all 92 skills files are CURRENT manifest rows, present on disk, with mtimes from the install that just ran. Any plan that "cleans up" `.agents/skills` is wrong.
- `remove` is deliberately conservative and must stay so: it deletes ONLY git-TRACKED orphans plus untracked stale-tool litter, and explicitly preserves the `untracked`/`local` quarantine lanes and anything gitignored (layout_migration.py:495-521). This plan must not weaken that predicate.
- Migration is transactional with a rollback journal (`_acquire_lock` layout_migration.py:647, `_save_transaction` :689, `rollback_migration` :1241). Any new deletion must happen inside that transaction so it is recoverable.
- The dual-layout detector keys off directory EXISTENCE, not live content, which is why empty dirs alone trip it. That detector is consumed by `aw doctor` and by `cli._split_brain_guard` (cli.py:5257-5260 region), so the residue can also affect later installs.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Reproduced on nine real 1.2.1 legacy repos; all exited 0 and all ended in the same residual state. | pysyslib, veraclavis, ansurv, cscie86-scratch, emo-train, Misc-Dev, zmm, grant-data, pubrun-benchmarks, each via `tools/aw_upgrade_test.py new <repo> -y -- --to-aw`. |
| F-02 | 4 to 9 EMPTY directories remain under `.agents/workflows/` after a successful migration. | Measured on pysyslib: 9 dirs, 0 files (`assess/tools`, `verify/tools`, `benchmark/tools`, `setup-repo/tools`, and parents). |
| F-03 | The residue makes a MIGRATED repo report a permanent split-brain, with unactionable advice. | On a migrated sandbox: `Layout: .aw + .agents (dual layout / split-brain)` and `Warning: Dual layouts detected (.aw/ and .agents/). Run 'aw migrate-layout' to consolidate.` The migration already ran; re-running clears nothing. |
| F-04 | ROOT CAUSE: the install path can never request cleanup. | `cli.py:5241` calls `mgr.execute_migration(target_backend="repository", leftover_disposition="defer")` with the value HARDCODED; the interactive path repeats it at cli.py:5265-5267. No install-time flag can reach `remove`. |
| F-05 | `defer` deletes nothing BY DESIGN, so the hardcoded value fully explains the residue. | `_handle_leftovers`: "`defer` records leftovers for a later cleanup; `keep` leaves them" (layout_migration.py:527-541); only the `disposition == "remove"` branch deletes (layout_migration.py:568+). |
| F-06 | CORRECTION to the originating backlog item: the 92 `.agents/skills` files are NOT a defect. | `engine.SKILLS_DIR = ".agents/skills"` (engine.py:171); `resolve_skills_dir()` returns it for both layouts with a documented rationale (engine.py:174-183). Verified after a fresh `--to-aw`: 92 CURRENT manifest rows, 0 missing on disk, mtimes matching the just-completed install. The item's "unreferenced duplicates" claim was wrong and has been corrected in the item. |
| F-07 | A precedent for self-cleaning migration already exists in-tree. | `engine.migrate_legacy_layout` removes the now-empty legacy dir after moving contents, guarded by "not any(p.is_file() ...)" (engine.py:2624-2636). |

## Proposed changes (ordered, validatable)

1. Make a cleanup disposition REACHABLE from `aw install --to-aw`, defaulting to today's `defer` so no existing invocation changes meaning (E-01, E-02).
2. Confirm empirically whether `remove` alone already clears the empty dirs; add pruning only if a gap is proven (E-03).
3. Pin `.agents/README.md` behavior per disposition (E-04).
4. Lock the whole outcome with a test seeded from the measured real-repo shape, which also guards `.agents/skills` against deletion (E-05).

## Deferred / out of scope (with reason)

- `.agents/skills` is explicitly NOT touched. F-06 proves it is the intended location for both layouts; deleting it would break host skill discovery.
- Changing the DEFAULT disposition to `remove` is deliberately deferred. It is a destructive-by-default change to a migration, and the maintainer should choose it knowingly once the cleanup path is proven reachable and tested. This plan makes the choice available and correct, not automatic.
- Making the dual-layout detector content-aware rather than existence-aware is a separate, larger change affecting `aw doctor`, `cli._split_brain_guard`, and `check_engine`. Once the residue is gone the false report is gone, so it is not needed to close this defect. (The upgrade-rehearsal harness already distinguishes the two cases via its `aw+litter` classification, which can inform that later work.)
- The stale-VERSION stamp seen alongside this residue is backlog `ygtykn`, planned separately; it is an installer-stamping bug, not a migration bug.

## Scope check

- Over-scope: none. The change is flag threading plus, if proven necessary, one pruning behavior, plus tests.
- Under-scope: E-03 is deliberately conditional, so this plan may end up changing only `cli.py` and the tests. That is an acceptable outcome and is stated as such rather than padding the plan with a change that may be unnecessary; V-03 requires the evidence that settles it either way.

## Required tests / validation

- `python3 -m pytest tests/test_layout_migration.py tests/test_installer.py -o addopts=""` must pass, including the new test.
- `python3 -m pytest tests/test_command_surface_declarations.py tests/test_cli_conformance_matrix.py -o addopts=""` must show no NEW findings from the added flag.
- An END-TO-END rehearsal on a real legacy repo, not only a synthetic fixture, since a synthetic fixture is what previously hid this class of defect: run `tools/aw_upgrade_test.py new <legacy-repo> -y -- --to-aw --leftovers remove` and paste the resulting probe output showing the layout is no longer `aw+litter`/dual and that `.agents/skills` survives.
- Full suite: `python3 -m pytest` must show no NEW failures against the pre-existing baseline. Four failures are already present on untouched HEAD (three `oc profile` undeclared-leaf failures in `tests/test_command_surface_declarations.py` and `tests/test_cli_conformance_matrix.py`, plus `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory`), verified on a pristine worktree of HEAD; they must not be counted as regressions or fixed here.

## Spec / documentation sync

No `.spec.md` file is amended, so none is declared in `Scope-Paths`. The `.aw` layout spec describes the target layout, not the leftover-disposition policy, and this plan does not change what a migrated repo's layout IS. A new user-facing `install` flag does need documenting: update the `install` help epilog (in `cli.py`, already in `Scope-Paths`), and note in `tools/README.md` only if the rehearsal harness's documented invocation changes.

## Open questions

### OQ-01: Should `--to-aw` default to `remove` rather than `defer`?

- Blocking: no
- Status: open
- Owner: human (maintainer)
- Resolution or deferral rationale: DELIBERATELY left to the maintainer, because it is a risk-appetite decision about making a migration destructive by default, which is exactly the class of question an agent should not settle alone. This plan does not depend on the answer: it makes `remove` reachable and tested while preserving `defer` as the default, so flipping the default later is a one-line change with the test already in place. Not blocking for that reason.

### OQ-02: Is the empty-dir residue already cleared by `remove`, or is new pruning required?

- Blocking: no
- Status: open
- Owner: opencode (settled during execution by E-03)
- Resolution or deferral rationale: Answerable only by running `remove` on a fixture in the measured shape, which is E-03's job; the docstring at layout_migration.py:527-541 says empty-dir pruning IS part of `remove`, which suggests the whole defect is unreachability (F-04), but that must be demonstrated rather than assumed. V-03 demands the evidence either way, so the plan cannot silently skip the question.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste output proving BOTH call sites are threaded, not just the flag added: a trace/print (or a test double capturing the call) showing `execute_migration` received `leftover_disposition="remove"` for `--to-aw --leftovers remove`, AND `"defer"` for a bare `--to-aw`. Also paste `aw install --help` showing the new flag with its default.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `python3 -m pytest tests/test_command_surface_declarations.py tests/test_cli_conformance_matrix.py -o addopts=""` summary, and state explicitly whether the `oc profile` failures present in the baseline are the ONLY failures. Any additional failure is a regression from this change and blocks the item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a before/after directory listing (e.g. `find .agents -type d -empty`) for a fixture in the measured shape, run through `--to-aw --leftovers remove`, showing a non-empty BEFORE list and an empty AFTER list. State plainly whether any code change was needed, and if none was, paste the evidence that `remove` alone sufficed (this resolves OQ-02).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the presence/absence of `.agents/README.md` after a run under EACH of `keep`, `defer`, and `remove` (three runs), plus a statement of which predicate branch decided it in the `remove` case.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the RED run (new test failing pre-fix) and the GREEN run post-fix with the `N passed` line. Separately paste an END-TO-END rehearsal against a REAL legacy repo (`tools/aw_upgrade_test.py new <repo> -y -- --to-aw --leftovers remove` followed by `probe`), showing the layout is no longer dual/`aw+litter` AND that `.agents/skills` still contains its 92 files. Also paste the source repo's `git status --porcelain` afterwards, proving the rehearsal did not mutate it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`Status: approved`) before any code change. The executor must: commit only the files listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`), never `git add -A` and never push; paste ACTUAL runner output for every `V-*` item; and treat the conservative `_is_removable_leftover` predicate (layout_migration.py:495-521) as a contract not to weaken. Any deletion added must run inside the existing migration transaction so `rollback_migration` can undo it. Post-gate lifecycle: once every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` reports conforming, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`, never a raw `git mv` plus commit. Backlog item `x15f0q` closes only after this plan is executed; it carries `Blocks-Release: f33nrj`, which this plan inherits.
