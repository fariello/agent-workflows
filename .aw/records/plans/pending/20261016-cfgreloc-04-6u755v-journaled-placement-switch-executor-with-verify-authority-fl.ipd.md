# IPD: Journaled placement-switch executor with verify, authority flip, resume and rollback

- Date: 2026-10-16
- Kind: child
- Concern: Backlog `ui1aln` asks to "move config, policy keys and cutovers to the new placement, remove or retire the old one". With the planner (Order 02 `xvlemm`) and side-explicit retirement (Order 03 `gjylny`) in place, the missing piece is a crash-safe transaction: today a switch either refuses (Order 01 `ppu39q`) or, before that fix, half-happened (two `project.json` files, the stale one authoritative). Spec `20260810-1447-01` Section 8.1 (Order 01) requires lock, journal, copy-verify before switch, a single authority flip, source removal and retirement after it, resume and rollback. The existing `layout_migration.MigrationManager` journal and lock live under `<target>/.aw/state/runtime/` (`self.transaction_file`, `self.lock_file`), which a to-home switch retires, so the journal needs a location that survives both sides.
- Scope: IN: `placement_switch.execute_placement_switch(repo_path, new_policy, *, aw_home=None, fault_injection=None) -> SwitchResult`, `resume_placement_switch(repo_path, *, aw_home=None)`, `rollback_placement_switch(repo_path, *, aw_home=None)`, `placement_switch_status(repo_path, *, aw_home=None)`; a journal and lock under `<AW_HOME>/placement-switches/<project_id>/` (outside `<AW_HOME>/projects/<id>/`, so neither retirement side removes it); a final receipt under the NEW side's `state/durable/migrations/placement_switch_receipt.json`; `PlacementSwitchError`. OUT: CLI flags and messages (Order 05).
- Scope-Paths: agent_workflows/placement_switch.py, tests/test_placement_switch_execute.py
- Item-Dependencies: executed:xvlemm, executed:gjylny
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 4
- Highest E allocated: 06
- Author: opencode
- Id: 6u755v
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cfgreloc graduating backlog ui1aln.

## Goal

A placement switch either completes with exactly one authoritative `project.json` (carrying every policy key and cutover date), every record and the durable install history at the new side, and the old footprint retired, or leaves the old side fully authoritative; a crash at any phase resumes to the first outcome or rolls back to the second.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Transaction

- [ ] E-01 Journal and lock. Implement the control dir `<AW_HOME>/placement-switches/<project_id>/` (`project_id` from `project_context._derive_project_id(_canonical_path(checkout_main_root(repo) or repo))`, AW_HOME from `project_context._resolve_effective_aw_home(aw_home)`), a `journal.json` written atomically (`tmp` + `os.replace`) after every state change with fields `schema_version`, `transaction_id`, `plan` (the Order 02 `SwitchPlan.to_dict()`, frozen: resume never re-plans), `phase` (`planned`, `copied`, `verified`, `switched`, `sources-removed`, `retired`, `done`), per-item `copied`/`removed` flags, the list of directories and the `.aw/.gitignore` this transaction CREATED (for rollback, E-05), and `saved_config/` holding verbatim copies of every old config file (`project.json`, `local.json`, `config.json`, `policy.json` that exist), written and journaled BEFORE any other mutation. The lock is a SIBLING of the control dir, `<AW_HOME>/placement-switches/<project_id>.lock`, never inside it, because `done` and rollback delete the control dir while the lock is still held (on Windows an open locked file cannot be deleted, and on POSIX deleting it lets a second caller lock a fresh inode while the first still runs). Each of `execute_placement_switch`, `resume_placement_switch` and `rollback_placement_switch` holds `platform_lock.acquire(<lock>)` (non-blocking; `LockBusy` -> `PlacementSwitchError("another placement switch is running ...")`) for its whole call, releasing in `finally`; `placement_switch_status` takes no lock (read-only). `execute_placement_switch` computes `plan_placement_switch(repo, new_policy, aw_home=...)` AFTER acquiring the lock, and refuses when a journal exists (message names `resume`/`rollback`) and when the plan has any blocker (message lists every blocker id and text), in both cases before writing anything.
  - Depends on: none
  - Expected outcome: journal and lock created outside both retire targets; a second concurrent call (execute, resume or rollback) refuses; a refused call writes nothing.
  - Execution state: pending

- [ ] E-02 Copy and verify phases. For each `move` item: create missing destination parents (journal each directory this transaction creates, so rollback can prune exactly those), refuse if the destination exists and is not hash-identical (re-check of Order 02's `destination-not-empty`, since time passed), copy with `shutil.copy2(src, dst, follow_symlinks=False)` (a symlink is recreated as a link, never followed), journal the item `copied`. Then verify every destination against the plan: sha256, size and mode for regular files, `os.readlink` equality for symlinks; any mismatch -> phase stays `copied`, raise. `discard` items are not copied. For `to-target` only, after verify: first ensure `<repo>/.aw/.gitignore` with `engine._ensure_aw_gitignore(repo)` (journal `created_aw_gitignore` when it returns True), because a `local-only` target has no `.aw/` at all and without that file `git add -- .aw/records` stages the by-design-untracked `records/runs/**`, `records/history.jsonl` and `records/*/untracked/**` (review probe: `git add -n` listed all four kinds); then stage only the NON-ignored copied destinations, selected with `git check-ignore --stdin -n -v --non-matching` and staged with `git add --pathspec-from-file=-` (review probe: with the `.aw/.gitignore` written this staged only `x.backlog.md`; a plain `git add -- <paths>` naming an ignored path instead exits `1` with "The following paths are ignored", so naming every copied path is not an option). Journal the staged paths (spec Section 8.1 item 6; Order 02 OQ-01). Ignored destinations stay on disk, unstaged.
  - Depends on: E-01
  - Expected outcome: after `verified`, every moved file exists at both sides byte-identical, the old side is still authoritative (`project_config_dir` unchanged); for `to-target`, `git diff --cached --name-only` lists exactly the non-ignored moved records.
  - Execution state: pending

- [ ] E-03 Switch phase (the single authority flip). Build the new `project.json` by reading the old one with `project_schema.parse_portable_policy` (on `ValueError` fall back to the raw dict exactly as `install_wizard.persist_project_policy` does), override `preset`, `placements`, `git_policies`, `delivery_mode`, `records_backend` from `new_policy` (role, enabled hosts, consent, cutovers, setids and unknown fields carried). Journal the two new config paths as `new_config_paths` BEFORE writing them (for `to-target` the in-tree write flips authority immediately, F-03, so a crash between the write and the next journal entry must still be rollback-able), then write `project.json` atomically at the new config path and `local.json` per Order 02's `config_local` rule. Then remove the old config files: tracked ones with `git rm -q -f -- <rel>` (staged), untracked ones with `unlink`, home ones with `unlink`. Journal `switched`. Assert `project_context.project_config_dir(repo, aw_home)` now equals the new config dir; if not, run the E-05 rollback procedure and raise (this is the invariant the whole backlog item is about; restoring `saved_config/` alone would leave the new `project.json` beside it, which is the split brain itself). Re-running the switch phase (resume) is idempotent: it rewrites the new files and skips old files already absent.
  - Depends on: E-02
  - Expected outcome: exactly one `project.json` exists for the project; readers resolve it; every pre-switch key and cutover date is present and unchanged.
  - Execution state: pending

- [ ] E-04 Post-switch phases. `sources-removed`: delete each `move` item's source (tracked in-tree sources with one batched `git rm -q -f -- <rels>`, others with `unlink`), then remove `discard` sources that are not inside a directory Order 03 retires (in particular every `discard` under the old home `records/`, because Order 03's home side refuses while `records/` holds any file), journaling per item. `retired`: journal `retire_started: true`, then call `retire_footprint(repo, plan.retire_side, preserve=<the old records root, for side "target" ".aw/records">)` from Order 03, and record its returned actions in the journal. A file under the old records root that is NOT a plan item (written by another `aw` command after planning) is never deleted: on the target side `preserve` keeps it, on the home side `retire_footprint` refuses and the switch stays resumable; the receipt lists such files as `unplanned_leftovers`. `done`: write the receipt (transaction id, from/to preset and dirs, item counts, staged-path count, `unplanned_leftovers`, the `retire_footprint` actions including every `PRESERVED` one, timestamp) under the new side's `state_durable/migrations/placement_switch_receipt.json`, then delete the control dir.
  - Depends on: E-03
  - Expected outcome: a completed switch leaves no control dir, a receipt at the new side, and no tracked old footprint (anything Order 03 preserves is named in the receipt).
  - Execution state: pending

- [ ] E-05 Recovery API. `resume_placement_switch` loads the journal and continues from its phase using the journal's frozen `plan` (copy skips `copied` items whose destination hash matches; the switch phase is idempotent, E-03; removal skips absent sources; when `retire_started` is set it re-calls `retire_footprint`, which is safe because it only removes what is still present). `rollback_placement_switch` is allowed only while the phase is before `sources-removed`, in this order: (1) delete the NEW config files listed in `new_config_paths` (unstaging first with `git rm -q --cached --ignore-unmatch` if in-tree), because leaving the new `project.json` beside the restored old one recreates the two-config state the backlog item fixes; (2) restore every `saved_config/` file to its original path byte-for-byte and, for each that was tracked, `git reset -q -- <rel>` so the staged `git rm` is undone (no dirty-tree blocker means the saved bytes equal `HEAD`); (3) unstage every journaled staged destination (`git rm -q --cached -- <rels>`), delete every destination this transaction copied, delete `.aw/.gitignore` if `created_aw_gitignore`, and remove the journaled created directories deepest-first when empty; (4) delete the control dir. The control dir is deleted only after all four steps succeed, so a crash mid-rollback leaves a journal and a re-run of rollback continues it. From `sources-removed` onward it refuses with "the switch is past the point of no return; finish it with resume, then switch back with aw install --preset <old> --relocate". `placement_switch_status` returns the journal summary (phase, direction, counts) or `None` when no journal exists. `fault_injection` in `{"after-copy", "mid-verify", "after-switch", "mid-source-removal", "before-retire"}` raises `PlacementSwitchError("Fault injected: ...")` at that point after the journal write (`mid-verify`: after the first destination verified, phase still `copied`; `mid-source-removal`: after the first source removed and journaled); any other value raises `ValueError`.
  - Depends on: E-04
  - Expected outcome: every fault point resumes to the completed state; every pre-`sources-removed` fault point (`after-copy`, `mid-verify`, `after-switch`) rolls back to a byte-identical old side with exactly one `project.json`.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-06 Create `tests/test_placement_switch_execute.py` (`unittest.TestCase`; scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`; a FRESH real `python3 -m agent_workflows install <repo> --preset <p> -y --no-interactive` subprocess per test into its own temp dir, with `GIT_AUTHOR_*`/`GIT_COMMITTER_*` in the env and an `--allow-empty` initial commit so the installer's sync commit lands. Do NOT `copytree` an installed repo: a copied `private-target` repo's `local.json` keeps the original's `project_id`, which Order 02 turns into a `project-id-mismatch` blocker, and a copied `local-only` repo has no config at all (`xvlemm` review PR-004, `gjylny` review PR-005). For the target repos, `git commit` a user record `.aw/records/backlog/open/x.backlog.md` plus customized `project.json` keys `cutovers.spec_id6 = "2020-01-01"`, `run = {"retry_budget": 3}`, `setids = {"warn_length": 10}`, `enabled_hosts = ["opencode"]` and `non_secret_consent = {"telemetry_prompted": True}`; for the `local-only` repo write the same keys into the home `project.json` and a home `records/backlog/open/x.backlog.md` plus a home `records/runs/r1/state.json`; `role` stays `target` because Order 02 blocks `source-checkout`). Cases: (1) to-home happy path from `private-target`: exactly one `project.json` (home), `project_config_dir` is home, every customized key and the 2020 cutover preserved, `x.backlog.md` byte-identical at `<AW_HOME>/projects/<id>/records/backlog/open/`, `state/durable/history/installs.jsonl` moved, `git diff --cached --name-status` shows `D` for the record, `.aw/config/project.json` and `.aw/system/**`, `git rev-list --count HEAD` unchanged, no tracked path left under `.aw/` (`git ls-files .aw` empty) and any remaining `.aw/` file is named `PRESERVED` in the receipt, receipt present, control dir and lock-adjacent control dir gone. Do NOT assert that `git status` shows only `D` lines: the retirement also strips the managed blocks from the tracked `AGENTS.md` and `.gitignore`, which stage as `M` (review probe: `uninstall_repo` on a fresh `private-target` install staged 311 `D` and 2 `M`, `.gitignore` and `AGENTS.md`); assert instead that every staged entry is `D` except `M` on exactly those two files; (2) to-target happy path from `local-only`: in-tree `project.json` authoritative, home `config/`, `system/`, `state/` gone, `x.backlog.md` staged as `A`, `records/runs/r1/state.json` present in-tree but NOT staged and `git check-ignore` reports it ignored, `.aw/.gitignore` present; (3) for each fault point in each direction: run with the fault, assert `placement_switch_status` phase, then `resume_placement_switch` -> same end state as (1) or (2); (4) for each pre-`sources-removed` fault point (`after-copy`, `mid-verify`, `after-switch`) in each direction: `rollback_placement_switch` -> repo tree byte-identical to a pre-switch snapshot (paths, sha256, `git status --porcelain`, `git diff --cached`), `AW_HOME` tree identical to its pre-switch snapshot (paths and sha256, so no new file and no control dir remain), and exactly one `project.json` exists for the project (the `after-switch` to-target case is the one that fails if rollback forgets the new config); (5) rollback refused after `mid-source-removal` and `before-retire`, with the message naming resume, and a subsequent `resume_placement_switch` completes; (6) blocker refusal: dirty `.aw/records` file -> `PlacementSwitchError` naming `dirty-aw-tree`, nothing written in the repo or `AW_HOME` (snapshot, which also proves no control dir was created); (7) concurrent lock: hold `<AW_HOME>/placement-switches/<id>.lock` via `platform_lock.acquire` in the test and assert `execute_placement_switch`, `resume_placement_switch` and `rollback_placement_switch` each refuse with `another placement switch is running`; (8) independent check: after (1), re-derive the expected destination set from the PRE-switch snapshot (every file under the old records root except `INDEX.json`/`INDEX.md`, plus `state/durable/install.json` and `history/**`), not from the journal or the `SwitchPlan`, and compare to the destination filesystem in sorted order with sha256 (spec Section 11.2 independent postcheck); (9) an existing journal blocks a fresh `execute_placement_switch` with a message naming resume and rollback. Mark the module `pytestmark = pytest.mark.slow`. Mutation proofs, each restored before the next: (M1) remove the E-03 old-config removal, confirm (1) fails on the "exactly one project.json"/`project_config_dir` assertion; (M2) remove rollback step (1) (deleting the new config), confirm the to-target `after-switch` case of (4) fails. Restore, `git diff` clean. Run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_execute.py tests/test_placement_switch_plan.py tests/test_placement_switch_retire.py -v` and bare `python3 -m pytest`.
  - Depends on: E-05
  - Expected outcome: all cases pass; M1 fails (1) and M2 fails the to-target `after-switch` rollback case, then both pass after restore.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Locks use `platform_lock.acquire` (non-blocking by default, raises `LockBusy`; its docstring explains why a silent wait is wrong for a refusal path).
- Atomic JSON writes use `tmp` + `os.replace` (`install_wizard.persist_project_policy`, `layout_migration.MigrationManager._save_transaction`).
- Spec Section 11.2: switch last, journal per item, resume continues from the transaction's own item list (never a fresh inventory), an independent postcheck re-derives expectations from the frozen inventory, Git plans staged never committed.
- `install_wizard.persist_project_policy`'s read-modify-write (plan `on0keo`) is the precedent for carrying `cutovers`, `setids`, unknown fields and consent.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `MigrationManager` keeps its journal and lock under the target's `.aw/state/runtime/`. | `layout_migration.MigrationManager.__init__`: `self.transaction_file = (self.runtime_state_dir / "transactions" / "migration_transaction.json")`, `self.lock_file = self.runtime_state_dir / "locks" / "migration_writer.lock"`. A to-home retirement removes `.aw/state/**` (`engine.uninstall_repo` step 4). |
| F-02 | Writing the new `project.json` alone does not flip authority for to-home: the reader prefers the in-tree dir while ANY of four config files exists there. | `project_context.project_config_dir` rule 1 loop over `project.json`, `local.json`, `config.json`, `policy.json`. |
| F-03 | For to-target, writing `<repo>/.aw/config/project.json` flips authority immediately. | Same rule 1. |
| F-04 | Durable install history is what `install_history.record_install_history` appends to, under the durable state class. | `install_history.record_install_history` docstring "Atomic install snapshot update and JSONL append under durable state class"; authoring probe found `.aw/state/durable/install.json` and `history/installs.jsonl` after a `private-target` install. |
| F-05 | A `to-target` `git add` of the moved records would stage the by-design-untracked lanes unless `.aw/.gitignore` exists first, and naming an ignored path makes `git add` fail outright. | Review probe in a bare repo with no `.aw/.gitignore`: `git add -n -- .aw/records` listed `records/runs/**`, `records/history.jsonl` and `records/prompts/untracked/**`; with `engine._ensure_aw_gitignore` applied, `git check-ignore --stdin -n -v --non-matching` filtering then `git add --pathspec-from-file=-` staged only `x.backlog.md`; a plain `git add -- <ignored path>` exits `1` "The following paths are ignored". |
| F-06 | Retiring a `private-target` footprint stages `M` on `AGENTS.md` and `.gitignore`, not only `D`. | Review probe: `engine.uninstall_repo(Path(repo), True)` on a fresh `private-target` install staged 311 `D` and 2 `M` (`.gitignore`, `AGENTS.md`), and left untracked `.aw/workflow-artifacts/README.md` byte-identical to the shipped template. |
| F-07 | A lock file inside a directory the holder deletes is unsafe. | `platform_lock.LockHandle.release` comment on the Windows backend unlocking a byte range of an open file; this plan's `done` and rollback delete the control dir. |

## Proposed changes (ordered, validatable)

1. Journal and lock outside both retire targets (E-01).
2. Copy and verify (E-02).
3. Single authority flip with the reader invariant asserted (E-03).
4. Source removal, retirement and receipt (E-04).
5. Resume, rollback, status and fault injection (E-05).
6. Tests with an independent postcheck and a mutation proof (E-06).

## Deferred / out of scope (with reason)

- CLI surface, preview and messages: Order 05.
  - Carrier: ozr356
- Carrying live worktree lanes across a switch: Order 02 blocks on them (`live-lane`); spec Section 8.1 item 4 says lanes are not carried.
  - Carrier-Declined: deliberate non-goal; finish or tear down lanes, then switch.

## Scope check

- Over-scope: none.
- Under-scope: none; every Section 8.1 transaction obligation (lock, journal, verify-before-switch, single flip, staged deletions, resume, rollback window, independent check) has an E-item and a test case.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_execute.py -v` passes, all fault points included.
- Mutations M1 (case 1) and M2 (to-target `after-switch` rollback) fail, then pass after restore.
- The Order 02 and 03 modules still pass; bare `python3 -m pytest` passes.

## Spec / documentation sync

N/A: implements spec Section 8.1 as written by Order 01 (`ppu39q`). If execution finds the contract unimplementable as written (for example the rollback window), STOP and record it as a blocking open question rather than silently diverging; amending the spec would then need its own declared scope.

## Open questions

### OQ-01: Copy-then-remove or `git mv`/`os.rename`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Copy-verify-switch-remove. `AW_HOME` and the target are commonly different filesystems, so a rename is a copy anyway; more importantly the old side must stay fully authoritative and intact until the flip so that a pre-switch failure is a clean rollback (spec Section 11.2 "Failure before switch leaves legacy authoritative"). No permanent twin remains because sources are removed in `sources-removed`. Recorded in spec Section 8.1 item 4 by Order 01.

### OQ-02: Where do the journal and lock live?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `<AW_HOME>/placement-switches/<project_id>/`. Both candidate homes inside a side are removed by that side's retirement (F-01 for the target; Order 03 removes `<AW_HOME>/projects/<id>/state` for the home side), and the journal must outlive both. The `project_id` derivation is the same one `project_config_dir` uses, so `resume` and `status` find it from the repo path alone.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted diff of the journal/lock code and a pasted scratch run showing the control dir path and the concurrent-call refusal message.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted scratch run with `fault_injection="after-copy"` (produced by `execute_placement_switch`; the fault hook is E-05) showing both copies present with matching sha256 and `project_config_dir` unchanged, and for a to-target run `git diff --cached --name-only` listing the moved record but not `records/runs/**`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted scratch to-home run (produced by `execute_placement_switch`) printing the list of `project.json` files for the project (exactly one), `project_config_dir`, and the preserved `cutovers.spec_id6`, `run`, `setids`, `enabled_hosts`, `non_secret_consent` values; and the `retire_footprint` call with `side="target"` visible in the diff.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff` of the post-switch phases and a pasted scratch to-home run (produced by `execute_placement_switch`) showing the receipt JSON (including the `retire_footprint` actions), the absent control dir, and `git status --porcelain` in which every entry is `D` except `M` on `AGENTS.md` and `.gitignore`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted per-fault-point resume and rollback outcomes from the test run (produced by `resume_placement_switch`/`rollback_placement_switch`) including, for the to-target `after-switch` rollback, the count of `project.json` files for the project (exactly one); and the rollback refusal message after `mid-source-removal`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `-v` runner output of the three placement-switch modules passing; pasted M1 and M2 failure lines, `git diff --stat` after restore and the passing re-run; pasted bare-suite summary line; pasted `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `xvlemm` and `gjylny` are executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never run a switch against this repository or the real home. Paste ACTUAL runner output. Mutation proofs are temporary and MUST NOT be committed. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit 6u755v -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize 6u755v` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
