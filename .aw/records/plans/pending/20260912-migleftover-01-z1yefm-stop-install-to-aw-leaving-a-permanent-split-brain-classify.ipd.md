# IPD: Stop install --to-aw leaving a permanent split-brain: let the install-time migration sweep its own empty legacy dirs

- Date: 2026-09-12
- Kind: child
- Concern: `aw install --to-aw` hardcodes the migration's leftover disposition to `defer`, so an install-driven migration can never clean up after itself. It leaves empty directories under `.agents/workflows/` plus `.agents/README.md`, which is enough to make the dual-layout detector report a permanent split-brain and make `aw doctor` advise a migration that has already run.
- Scope: Give the install-time migration path a way to reach a cleanup disposition, sweep the empty legacy directories it leaves, and stop the residue from being reported as a live split-brain layout. Includes a regression test built from the measured real-repo state.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/layout_migration.py, agent_workflows/doctor.py, tests/test_layout_migration.py, tests/test_installer.py, tests/test_doctor.py
- Item-Dependencies: executed:h90ij1
- Status: reviewed
- Readiness: go-pending-approval
- Set: migleftover
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: z1yefm
- From-Backlog: x15f0q
- Blocks-Release: f33nrj

## Workflow history
- 2026-09-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-09-12 to-review (opencode): authored from backlog item x15f0q; root cause verified in-tree, and the item's incorrect skills claim corrected before planning.
- 2026-09-12 draft (opencode): created.

## Goal

Make an install-driven `.agents/` to `.aw/` migration finish cleanly, so a migrated repo does not permanently report a split-brain layout and is not told to run a migration that already ran. This is the upgrade path all 27 legacy repos on the maintainer's server will take, and release 2.0.0 exists to gate exactly this migration.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Reachability of a cleanup disposition

- [ ] E-01 In `agent_workflows/cli.py`, stop hardcoding `leftover_disposition="defer"` on the install-time migration. THREE call sites must be changed, not two: the `--to-aw` path (cli.py:5240), the interactive-confirm path in `_handle_legacy_migration` (cli.py:5265-5267), and the migrate-now branch inside `_split_brain_guard` (cli.py:4998), which was missed when this plan was authored and which is the path a split-brain repo actually takes. Thread the value from a new `aw install` flag (`--leftovers {keep,remove,defer}`) whose DEFAULT preserves today's behavior (`defer`), so this item changes reachability only and no existing invocation changes meaning. Verify by grep that no hardcoded `leftover_disposition=` literal remains in `cli.py` before marking this done.
  - Depends on: none
  - Expected outcome: `aw install <repo> --to-aw --leftovers remove` reaches `MigrationManager.execute_migration(leftover_disposition="remove")`; a bare `--to-aw` still passes `defer`; and `grep -n 'leftover_disposition="' agent_workflows/cli.py` returns no hardcoded literal.
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

### Task group 3: Make doctor's layout report content-aware

- [ ] E-06 Repoint `doctor.probe_environment`'s layout classification at the shared content-aware detector instead of its own existence test. It currently computes `has_aw`/`has_agents` from bare `.is_dir()` (doctor.py:323-326); `engine.detect_split_brain_layout` (engine.py:119-142) already implements the correct predicate and is what `cli._split_brain_guard` consumes (cli.py:4977). Reuse it rather than writing a second content walk. A repo that has completed migration must report a plain `.aw` layout even though `.agents/skills` still exists.
  - Depends on: none
  - Expected outcome: on a fixture holding only the residue shape (empty `.agents/workflows/*/tools` plus `.agents/README.md` plus a populated `.agents/skills`), `probe_environment(repo).layout` no longer contains "split-brain", and `engine.detect_split_brain_layout` and doctor AGREE. A genuine split-brain (a non-empty file under `.agents/workflows`) must still be reported.
  - Execution state: pending

### Task group 4: Regression test from the measured shape

- [ ] E-05 Add a test that seeds a fixture repo in the exact residue shape measured on the nine real repos (populated `.aw/system` plus `.agents/workflows/{assess,verify,benchmark,setup-repo}/tools` as EMPTY dirs, plus `.agents/README.md`, plus a populated `.agents/skills`), runs the install-time migration with `remove`, and asserts the repo is no longer classified as dual-layout. The test must assert `.agents/skills` SURVIVES, because it is the intended location for both layouts (engine.py:171, engine.py:174-183) and deleting it would be a real regression.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: a named test that fails against pre-fix code and passes after, and that would FAIL if a future change deleted `.agents/skills`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.agents/skills` is the INTENDED skills location for BOTH layouts, not legacy residue: `engine.SKILLS_DIR = ".agents/skills"` (engine.py:171) and `resolve_skills_dir()` returns it for the `aw` layout too (engine.py:174-183), because a skill package is discovered by a host tool scanning a fixed directory, exactly like the `.opencode/`/`.claude/` command shims. Verified: after `--to-aw`, all 92 skills files are CURRENT manifest rows, present on disk, with mtimes from the install that just ran. Any plan that "cleans up" `.agents/skills` is wrong.
- `remove` is deliberately conservative and must stay so: it deletes ONLY git-TRACKED orphans plus untracked stale-tool litter, and explicitly preserves the `untracked`/`local` quarantine lanes and anything gitignored (layout_migration.py:495-521). This plan must not weaken that predicate.
- Migration is transactional with a rollback journal (`_acquire_lock` layout_migration.py:647, `_save_transaction` :689, `rollback_migration` :1241). Any new deletion must happen inside that transaction so it is recoverable.
- THERE ARE TWO DIFFERENT DETECTORS AND THEY DISAGREE on the measured residue; an earlier draft of this plan wrongly described them as one. `engine.detect_split_brain_layout` (engine.py:119-142) is already CONTENT-AWARE: it walks `.agents/workflows` and returns True only for a non-empty, non-cruft FILE, so it correctly returns False for empty directories. `doctor.probe_environment` instead tests bare directory existence, `has_aw = (repo_root/".aw").is_dir()` and `has_agents = (repo_root/".agents").is_dir()` (doctor.py:323-326), and so reports split-brain on any `.agents/` that exists at all. Measured on a fixture holding ONLY the residue shape (empty `.agents/workflows/*/tools` dirs plus `.agents/README.md`): `engine.detect_split_brain_layout` -> `False`, doctor layout string -> `.aw + .agents (dual layout / split-brain)`.
- CONSEQUENCE for this plan's scope: `cli._split_brain_guard` consumes the ENGINE detector (cli.py:4977), so the residue does NOT block later installs and this plan must not claim it does. The false user-facing report comes from DOCTOR alone. Note `.agents/skills` is a legitimate permanent resident of `.agents/` (see the first convention above), so doctor's existence test can NEVER be correct on a migrated repo: `.agents/` is expected to exist forever.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Reproduced on nine real 1.2.1 legacy repos; all exited 0 and all ended in the same residual state. | pysyslib, veraclavis, ansurv, cscie86-scratch, emo-train, Misc-Dev, zmm, grant-data, pubrun-benchmarks, each via `tools/aw_upgrade_test.py new <repo> -y -- --to-aw`. |
| F-02 | 4 to 9 EMPTY directories remain under `.agents/workflows/` after a successful migration. | Measured on pysyslib: 9 dirs, 0 files (`assess/tools`, `verify/tools`, `benchmark/tools`, `setup-repo/tools`, and parents). |
| F-03 | The residue makes a MIGRATED repo report a permanent split-brain, with unactionable advice. | On a migrated sandbox: `Layout: .aw + .agents (dual layout / split-brain)` and `Warning: Dual layouts detected (.aw/ and .agents/). Run 'aw migrate-layout' to consolidate.` The migration already ran; re-running clears nothing. |
| F-08 | The false report comes from DOCTOR's existence test, not from the shared engine detector, which is already content-aware (found in review, PR-002). | `engine.detect_split_brain_layout` walks for a non-empty file (engine.py:119-142) and returns False on the residue; `doctor.py:323-326` tests bare `.is_dir()` and returns split-brain. Measured side by side on a residue-only fixture: engine `False`, doctor `.aw + .agents (dual layout / split-brain)`. |
| F-09 | A THIRD hardcoded `defer` exists that the original plan did not name (found in review, PR-003). | `_split_brain_guard`'s migrate-now branch calls `execute_migration(target_backend="repository", leftover_disposition="defer")` at cli.py:4998, in addition to cli.py:5240 and cli.py:5265-5267. Fixing only the two named sites would leave the split-brain consolidation path unable to clean up. |
| F-10 | `.agents/` must be expected to exist PERMANENTLY on a migrated repo, so doctor's existence test can never be made correct by cleanup alone. | `.agents/skills` is the intended skills location for both layouts (engine.py:171, engine.py:174-183), so even a perfect cleanup leaves `.agents/` present. |
| F-11 | The interactive migrate prompt currently defaults to NO, which contradicts the 2.0.0 intent of encouraging the new layout (surfaced in review; owned by `kapm7y`, not fixed here). | `_confirm(term, "Migrate ... to canonical .aw/ now?", False)` at cli.py:5256-5259, rendering `[y/N]` (cli.py:4799). By contrast `_confirm_install` already supports a yes-default and documents it (cli.py:4875-4878), so a yes-defaulting prompt is an established pattern. |
| F-12 | Non-interactively and under `--yes`, an old repo is NOT migrated at all; it is kept on the deprecated layout with a warning (surfaced in review; owned by `kapm7y`). | cli.py:5277-5282. Consequence: an automated fleet update with `--yes` silently leaves every repo on the layout 2.0.0 is trying to retire. |
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
- (REVISED IN REVIEW, PR-002.) An earlier draft DEFERRED the detector fix on the premise that "once the residue is gone the false report is gone". That premise is FALSE: `.agents/skills` is a permanent legitimate resident of `.agents/` (F-10), so `.agents/` exists forever on a migrated repo and doctor's bare-existence test (doctor.py:323-326) reports split-brain forever no matter how complete the cleanup. Cleanup alone therefore cannot close this defect, and the detector fix is now IN scope as E-06. What remains genuinely deferred is auditing `check_engine`'s own layout rules, which are a separate surface with their own tests and are not what the user sees in `aw doctor`.
- The stale-VERSION stamp seen alongside this residue is backlog `ygtykn`, planned separately; it is an installer-stamping bug, not a migration bug.
- PROMPTING for the disposition, defaulting that prompt to the encouraged action, and remembering the answer are all OUT of scope here and belong to blocking backlog item `kapm7y`. Two related defects found during this review are recorded as F-11 and F-12 and are `kapm7y`'s to fix, not this plan's: the interactive migrate prompt defaults to NO, and `--yes` keeps the deprecated layout rather than migrating. They are deliberately NOT fixed here because changing what `--yes` does to a fleet is a policy change that needs the persistence mechanism first, and bundling it would make this plan's blast radius far larger than the residue bug it exists to fix.

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
- Status: resolved
- Owner: human (maintainer)
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-12, and the answer is neither of the two options originally offered. The ruling: for 2.0.0 the goal is to strongly encourage everyone onto the new layout, and behavior we WANT must not be hidden behind a flag a user has to read `--help` to discover. So a policy question like this should ASK, and the prompt should DEFAULT TO THE ENCOURAGED ACTION, rather than silently defaulting either way. The maintainer also required that the user be able to SAVE that choice for future installs so they are not prompted repeatedly; that persistence mechanism does not exist yet and is filed as blocking backlog item `kapm7y` (`Blocks-Release: next`).
  WHAT THIS PLAN DOES, given the ruling: it keeps `defer` as the non-interactive default (so nothing becomes destructive without an explicit choice) and makes `remove` reachable and tested. It does NOT add the prompt, because a prompt without the save-my-answer mechanism would nag on every install of every repo, which the maintainer explicitly rejected. The prompt-and-remember behavior is `kapm7y`'s job, and this plan is its prerequisite: `kapm7y` needs a reachable non-default disposition to prompt FOR. Sequencing is therefore this plan first, then `kapm7y`, and the eventual default flip is a one-line change with E-05's test already in place.

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

- [ ] V-06 validates E-06
  - Required evidence: paste, for TWO fixtures, both `engine.detect_split_brain_layout(repo)` and `probe_environment(repo).layout`: (a) the residue-only shape, where both must agree that it is NOT split-brain; and (b) a genuine split-brain with a non-empty file under `.agents/workflows`, where both must still report split-brain. Pre-fix, (a) returned `False` from engine and `.aw + .agents (dual layout / split-brain)` from doctor; show that disagreement is gone without losing true-positive detection.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

DEPENDENCY: this plan declares `- Item-Dependencies: executed:h90ij1` and MUST NOT run before plan `h90ij1` is executed. Both plans edit `agent_workflows/doctor.py` and `agent_workflows/cli.py`: `h90ij1` owns the environment probe's version and config READS, while this plan's E-06 changes the LAYOUT classification a few lines above them (doctor.py:323-326). Sequencing them makes the second edit apply to a file whose surrounding function has already settled. The runner re-checks dependencies at dispatch and isolates each item in its own worktree, so a queued-together Set is safe and no concurrency warning is warranted; a hand-run of this plan BEFORE `h90ij1`, however, is not.

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`Status: approved`) before any code change. The executor must: commit only the files listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`), never `git add -A` and never push; paste ACTUAL runner output for every `V-*` item; and treat the conservative `_is_removable_leftover` predicate (layout_migration.py:495-521) as a contract not to weaken. Any deletion added must run inside the existing migration transaction so `rollback_migration` can undo it. Post-gate lifecycle: once every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` reports conforming, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`, never a raw `git mv` plus commit. Backlog item `x15f0q` closes only after this plan is executed; it carries `Blocks-Release: f33nrj`, which this plan inherits.
