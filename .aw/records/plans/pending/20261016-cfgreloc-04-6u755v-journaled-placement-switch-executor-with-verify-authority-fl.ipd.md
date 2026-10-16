# IPD: Journaled placement-switch executor with verify, authority flip, resume and rollback

- Date: 2026-10-16
- Kind: child
- Concern: Backlog `ui1aln` asks to "move config, policy keys and cutovers to the new placement, remove or retire the old one". With the planner (Order 02 `xvlemm`) and side-explicit retirement (Order 03 `gjylny`) in place, the missing piece is a crash-safe transaction: today a switch either refuses (Order 01 `ppu39q`) or, before that fix, half-happened (two `project.json` files, the stale one authoritative). Spec `20260810-1447-01` Section 8.1 (Order 01) requires lock, journal, copy-verify before switch, a single authority flip, source removal and retirement after it, resume and rollback. The existing `layout_migration.MigrationManager` journal and lock live under `<target>/.aw/state/runtime/` (`self.transaction_file`, `self.lock_file`), which a to-home switch retires, so the journal needs a location that survives both sides.
- Scope: IN: `placement_switch.execute_placement_switch(repo_path, new_policy, *, aw_home=None, fault_injection=None) -> SwitchResult`, `resume_placement_switch(repo_path, *, aw_home=None)`, `rollback_placement_switch(repo_path, *, aw_home=None)`, `placement_switch_status(repo_path, *, aw_home=None)`; a journal and lock under `<AW_HOME>/placement-switches/<project_id>/` (outside `<AW_HOME>/projects/<id>/`, so neither retirement side removes it); a final receipt under the NEW side's `state/durable/migrations/placement_switch_receipt.json`; `PlacementSwitchError`. OUT: CLI flags and messages (Order 05).
- Scope-Paths: agent_workflows/placement_switch.py, tests/test_placement_switch_execute.py
- Item-Dependencies: executed:xvlemm, executed:gjylny
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 4
- Highest E allocated: 06
- Author: opencode
- Id: 6u755v

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cfgreloc graduating backlog ui1aln.

## Goal

A placement switch either completes with exactly one authoritative `project.json` (carrying every policy key and cutover date), every record and the durable install history at the new side, and the old footprint retired, or leaves the old side fully authoritative; a crash at any phase resumes to the first outcome or rolls back to the second.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Transaction

- [ ] E-01 Journal and lock. Implement the control dir `<AW_HOME>/placement-switches/<project_id>/` (`project_id` from `project_context._derive_project_id(_canonical_path(checkout_main_root(repo) or repo))`), a `journal.json` written atomically (`tmp` + `os.replace`) after every state change with fields `schema_version`, `transaction_id`, `plan` (the Order 02 `SwitchPlan.to_dict()`), `phase` (`planned`, `copied`, `verified`, `switched`, `sources-removed`, `retired`, `done`, `rolled-back`), per-item `copied`/`removed` flags, and `saved_config/` holding verbatim copies of every old config file (`project.json`, `local.json`, `config.json`, `policy.json` that exist). Hold `platform_lock.acquire(<control>/switch.lock)` (non-blocking; `LockBusy` -> `PlacementSwitchError("another placement switch is running ...")`) for the whole call. `execute_placement_switch` refuses when a journal exists in a non-terminal phase (message names `resume`/`rollback`) and when the plan has any blocker (message lists every blocker id and text).
  - Depends on: none
  - Expected outcome: journal and lock created outside both retire targets; a second concurrent call refuses.
  - Execution state: pending

- [ ] E-02 Copy and verify phases. For each `move` item: `mkdir -p` the destination parent, refuse if the destination exists and is not hash-identical (re-check of Order 02's `destination-not-empty`, since time passed), copy with `shutil.copy2` (symlinks recreated as links, never followed), journal `copied`. Then verify every destination's sha256, size and mode against the plan; any mismatch -> phase stays `copied`, raise. `discard` items are not copied. For `to-target`, `git add -- <dest>` each copied record so the moved records are staged (spec Section 8.1 item 6; Order 02 OQ-01).
  - Depends on: E-01
  - Expected outcome: after `verified`, every moved file exists at both sides byte-identical, the old side is still authoritative (`project_config_dir` unchanged).
  - Execution state: pending

- [ ] E-03 Switch phase (the single authority flip). Build the new `project.json` by reading the old one with `project_schema.parse_portable_policy` (on `ValueError` fall back to the raw dict exactly as `install_wizard.persist_project_policy` does), override `preset`, `placements`, `git_policies`, `delivery_mode`, `records_backend` from `new_policy` (role, enabled hosts, consent, cutovers, setids and unknown fields carried), write it atomically at the new config path; build `local.json` per Order 02's `config_local` rule and write it. Then remove the old config files: tracked ones with `git rm -q -f -- <rel>` (staged), untracked ones with `unlink`, home ones with `unlink`. Journal `switched`. Assert `project_context.project_config_dir(repo)` now equals the new config dir; if not, restore `saved_config/` and raise (this is the invariant the whole backlog item is about).
  - Depends on: E-02
  - Expected outcome: exactly one `project.json` exists for the project; readers resolve it; every pre-switch key and cutover date is present and unchanged.
  - Execution state: pending

- [ ] E-04 Post-switch phases. `sources-removed`: delete each `move` item's source (tracked in-tree sources with one batched `git rm -q -f -- <rels>`, others with `unlink`), then remove `discard` sources that are not inside a directory Order 03 retires, journaling per item. `retired`: call `retire_footprint(repo, plan.retire_side, preserve=<config and records paths already handled>)` from Order 03. `done`: write the receipt (transaction id, from/to preset and dirs, item counts, staged-path count, timestamp) under the new side's `state_durable/migrations/placement_switch_receipt.json`, then delete the control dir.
  - Depends on: E-03
  - Expected outcome: a completed switch leaves no control dir, a receipt at the new side, and no old footprint.
  - Execution state: pending

- [ ] E-05 Recovery API. `resume_placement_switch` loads the journal and continues from its phase (copy skips `copied` items whose destination hash matches; removal skips absent sources). `rollback_placement_switch` is allowed only before `sources-removed`: restore `saved_config/` files to their original paths (re-`git add` any that were tracked, undoing the staged `git rm`), delete destinations this transaction created (`git rm --cached` any it staged), write phase `rolled-back`, delete the control dir. From `sources-removed` onward it refuses with "the switch is past the point of no return; switch back with aw install --preset <old> --relocate". `placement_switch_status` returns the journal summary or `None`. `fault_injection` in `{"after-copy", "mid-verify", "after-switch", "mid-source-removal", "before-retire"}` raises `PlacementSwitchError("Fault injected: ...")` at that point after the journal write.
  - Depends on: E-04
  - Expected outcome: every fault point resumes to the completed state; every pre-`sources-removed` fault point rolls back to a byte-identical old side.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-06 Create `tests/test_placement_switch_execute.py` (`unittest.TestCase`; scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`; real `install` subprocess in `setUpClass`, then per-test `copytree` and, for the target repos, a `git commit` of a user record `.aw/records/backlog/open/x.backlog.md` plus customized `project.json` keys `cutovers.spec_id6 = "2020-01-01"`, `run = {"retry_budget": 3}`, `setids = {"warn_length": 10}`, `enabled_hosts = ["opencode"]` and `non_secret_consent = {"telemetry_prompted": True}`; `role` stays `target` because Order 02 blocks `source-checkout`). Cases: (1) to-home happy path: exactly one `project.json` (home), `project_config_dir` is home, every customized key and the 2020 cutover preserved, `x.backlog.md` byte-identical at `<AW_HOME>/projects/<id>/records/backlog/open/`, `state/durable/history/installs.jsonl` moved, `git diff --cached --name-status` shows `D` for the record, `.aw/config/project.json` and `.aw/system/**`, nothing committed, no `.aw/` directory left (or only user files), receipt present, control dir gone; (2) to-target happy path from `local-only`: in-tree `project.json` authoritative, home config gone, records staged as `A`, home `system/`, `state/`, `config/` gone; (3) for each fault point: run with the fault, assert `placement_switch_status` phase, then `resume_placement_switch` -> same end state as (1); (4) for each pre-`sources-removed` fault point: `rollback_placement_switch` -> old tree byte-identical to a pre-switch snapshot (paths, sha256, `git status --porcelain`, `git diff --cached`) and home has no new files except none; (5) rollback refused after `mid-source-removal`; (6) blocker refusal: dirty `.aw/records` file -> `PlacementSwitchError` naming `dirty-aw-tree`, nothing written anywhere (snapshot); (7) concurrent lock: hold the lock via `platform_lock.acquire` in the test and assert refusal; (8) independent check: after (1), re-derive the expected destination set from the PRE-switch snapshot (not from the journal) and compare to the filesystem in sorted order (spec Section 11.2 independent postcheck). Mark the module `pytestmark = pytest.mark.slow`. Mutation proof: remove the E-03 old-config removal, confirm (1) fails on the "exactly one project.json"/`project_config_dir` assertion, restore, `git diff` clean. Run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_execute.py tests/test_placement_switch_plan.py tests/test_placement_switch_retire.py -v` and bare `python3 -m pytest`.
  - Depends on: E-05
  - Expected outcome: all cases pass; mutation fails (1) then passes.
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
- Mutation proof fails case (1) and passes after restore.
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
  - Required evidence: pasted scratch run with `fault_injection="after-copy"` (produced by `execute_placement_switch`, E-04) showing both copies present with matching sha256 and `project_config_dir` unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted scratch to-home run (produced by `execute_placement_switch`) printing the list of `project.json` files for the project (exactly one), `project_config_dir`, and the preserved `cutovers.spec_id6`, `run`, `setids`, `enabled_hosts`, `non_secret_consent` values; and the `retire_footprint` call with `side="target"` visible in the diff.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff` of the post-switch phases and a pasted scratch to-home run (produced by `execute_placement_switch`) showing the receipt JSON, the absent control dir, and `git status --porcelain` with only `D` lines.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted per-fault-point resume and rollback outcomes from the test run (produced by `resume_placement_switch`/`rollback_placement_switch`) and the rollback refusal message after `mid-source-removal`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `-v` runner output of the three placement-switch modules passing; pasted mutation failure line, `git diff --stat` after restore and the passing re-run; pasted bare-suite summary line; pasted `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `xvlemm` and `gjylny` are executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never run a switch against this repository or the real home. Paste ACTUAL runner output. Mutation proofs are temporary and MUST NOT be committed. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit 6u755v -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize 6u755v` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
