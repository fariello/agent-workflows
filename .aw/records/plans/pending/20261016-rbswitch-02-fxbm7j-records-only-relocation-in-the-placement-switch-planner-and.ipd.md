# IPD: Records-only relocation in the placement-switch planner and executor

- Date: 2026-10-16
- Kind: child
- Concern: After Order 01 (`s07f73`) a records-backend change that would orphan records refuses, but nothing can perform it. Set `cfgreloc` builds a planner (`xvlemm` `placement_switch.plan_placement_switch`) and a journaled executor (`6u755v` `execute_placement_switch`, `resume_placement_switch`, `rollback_placement_switch`, `placement_switch_status`) for FULL placement switches, which also rewrite config, move durable state and retire a whole footprint. A records-only switch is a strict subset (one class moves, config stays where it is and is rewritten in place, nothing is retired), so the natural implementation reuses that module's census, blockers, journal, lock, copy-verify and recovery machinery rather than a second transaction, as the backlog item suggests ("the cfgreloc placement-switch planner (plan pl3f6e) is the natural place to reuse"; that Set's planner shipped as `xvlemm`).
- Scope: IN: in `agent_workflows/placement_switch.py`, `plan_records_root_switch(repo_path, new_policy, *, aw_home=None) -> SwitchPlan` (read-only, `direction` `records-to-home` or `records-to-target`, `retire_side=None`, items for the `records` class only plus one in-place `rewrite` of the config sources that carry `records_backend`); `execute_records_root_switch(repo_path, new_policy, *, aw_home=None, fault_injection=None) -> SwitchResult`; a `mode` field (`placement` or `records`) in the journal so the EXISTING `resume_placement_switch`, `rollback_placement_switch` and `placement_switch_status` dispatch on it; tests. OUT: CLI flags, preview rendering and messages (Order 03 `vv9ki4`); companion records (`n9vd2h`); config or durable-state movement (Set `cfgreloc`).
- Scope-Paths: agent_workflows/placement_switch.py, tests/test_records_root_switch_execute.py
- Item-Dependencies: executed:s07f73, executed:6u755v
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: wbz75c
- Blocks-Release: next
- Set: rbswitch
- Order: 2
- Highest E allocated: 05
- Author: opencode
- Id: fxbm7j

## Workflow history
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set rbswitch graduating backlog wbz75c.

## Goal

A records-backend change either completes with every record at the new records root, the config rewritten in place to name the new backend, and the resolver pointing there, or leaves the old root fully authoritative; a crash at any phase resumes or rolls back through the same recovery API `cfgreloc` ships.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Planner

- [ ] E-01 Re-measure the shipped `cfgreloc` surface at execution HEAD: `grep -n` in `agent_workflows/placement_switch.py` for `class SwitchItem`, `class SwitchPlan`, `def plan_placement_switch`, `def execute_placement_switch`, `def resume_placement_switch`, `def rollback_placement_switch`, `def placement_switch_status`, the journal phase names and the fault-injection set, and in `install_wizard.py` for `def records_root_switch` (Order 01). Record which helper functions the census, blocker and copy/verify code are factored into. If any of these is absent, the dependency chain is broken: stop and report. Then add `plan_records_root_switch`: detection is `install_wizard.records_root_switch(repo, new_policy, existing_policy=install_wizard.resolve_existing_policy(repo))`; `None` -> a plan with no items and `blockers=["not-a-records-switch"]`; `reason="companion"` -> no items, `blockers=["companion-unsupported"]`. Otherwise: `direction` is `records-to-home` when the target root is under `<AW_HOME>/projects/`, else `records-to-target`; items are the `xvlemm` records census applied to the old records root with destinations under the new one (every regular file and symlink `move`, git-ignored ones included with `tracked=False`, `INDEX.json`/`INDEX.md` `discard`), REUSING the census helper rather than copying it (extract a shared helper if `xvlemm` inlined it; the extraction must leave `plan_placement_switch` output unchanged, proven by its own test module passing); plus one `rewrite` item per config source that the authority flip edits (`project.json` always; `local.json` only when it carries a `records_backend` key, because `project_context.resolve_project_context` reads `merged_local_binding.get("records_backend")` BEFORE `project_policy_data.get("records_backend")`, so leaving it would make the flip a no-op), each with `source == destination`; `retire_side=None`. Blockers reuse the `xvlemm` predicates, scoped to records: `dirty-aw-tree` (porcelain non-empty under `.aw/records` or `.aw/config`), `unmerged`, `destination-not-empty` (a destination exists and is not hash-identical, EXCEPT a scaffold `.gitkeep`/`README.md` the installer already wrote there: such a source becomes a `discard` item, not a `move`, so the destination's copy is kept untouched, never overwritten, never journaled as copied and never deleted by rollback; a hash-identical pre-existing destination of any `move` item is likewise journaled `preexisting`, not `copied`, so rollback leaves it in place), `live-lane`, `unparseable-config`, `source-checkout`. Warnings: `records-become-untracked` (count) for `records-to-home` (`repository` -> `repository-untracked` resolves the same root, so Order 01's detector returns `None` and it never reaches this planner); `records-become-tracked-candidates` for `records-to-target` into `repository`. Every git subprocess runs with `GIT_OPTIONAL_LOCKS=0` and `-c core.fsmonitor=false` (the `xvlemm` purity rule).
  - Depends on: none
  - Expected outcome: on a committed `private-target` repo with one user record and a `records_backend=home` policy, the plan has `direction="records-to-home"`, one tracked `move` for the record, `move`s for scaffold files, a `project.json` `rewrite`, `retire_side=None`, no blockers; `plan_placement_switch` output unchanged.
  - Execution state: pending

### Task group 2: Executor

- [ ] E-02 Add `execute_records_root_switch`, reusing the `6u755v` control dir `<AW_HOME>/placement-switches/<project_id>/`, its sibling lock, `saved_config/`, atomic journal writes, and its copy and verify phase helpers; the journal gains `"mode": "records"` (an absent `mode` reads as `placement`, so a journal written by the shipped executor still resumes). Phases: `planned` -> `copied` -> `verified` (for `records-to-target` into `repository`, ensure `.aw/.gitignore` via `engine._ensure_aw_gitignore` and stage only non-ignored destinations with `git check-ignore --stdin -n -v --non-matching` then `git add --pathspec-from-file=-`, exactly as `6u755v` E-02) -> `switched` -> `sources-removed` -> `done`. There is no `retired` phase. In the copy phase a `move` item whose destination already exists hash-identical is journaled `preexisting` and not copied, and a `discard` item is never copied, so rollback (which deletes only `copied` destinations) can never delete a file this transaction did not write. Refuse when a journal of EITHER mode exists, or when the plan has any blocker, before writing anything.
  - Depends on: E-01
  - Expected outcome: a refused call writes nothing; a held lock refuses; copy and verify leave the old root authoritative; pre-existing destinations are never overwritten or journaled as copied.
  - Execution state: pending

- [ ] E-03 The switch phase is the authority flip, an in-place rewrite: save every config source into `saved_config/` (already done at `planned`), then rewrite `project.json` atomically (`tmp` + `os.replace` in the same directory) from the parsed old document (`project_schema.parse_portable_policy`, raw-dict fallback as `install_wizard.persist_project_policy` does), changing ONLY `records_backend`, `placements.records` and `git_policies.records` (mapping `repository` -> `target-tracked`/`target-git`, `repository-untracked` -> `target-ignored`/`ignored`, `home` -> `home-untracked`/`untracked`, the same values `install_wizard.get_preset_defaults` and `ProjectPolicy.__post_init__` use), carrying every other key including `preset`, `cutovers`, `setids` and unknown fields byte-for-byte in value; when `local.json` has a `records_backend` key, rewrite it to the new value in the same phase. If `project.json` is tracked, stage it (`git add -- .aw/config/project.json`). Journal `switched`, then assert `resolve_project_context(target_repo=repo).logical_roots["records"]` equals the plan's new root; if not, run the rollback procedure and raise. `sources-removed`: remove each `move` source (tracked ones with one batched `git rm -q -f --`, others `unlink`) and each `discard` source, journaling per item, then prune now-empty directories under the old records root. `done`: write the receipt to `<state_durable>/migrations/records_switch_receipt.json` (transaction id, from/to backend and roots, item counts, staged-path count, `unplanned_leftovers` for any file under the old root that was not a plan item, which is never deleted), then delete the control dir.
  - Depends on: E-02
  - Expected outcome: exactly one records root holds records; `project.json` differs from before only in the three records keys; the resolver agrees.
  - Execution state: pending

- [ ] E-04 Recovery dispatch. In `resume_placement_switch`, `rollback_placement_switch` and `placement_switch_status`, read the journal `mode` and route `records` journals to records-mode phase handlers: resume continues from the frozen plan (copy skips hash-identical destinations, the rewrite is idempotent, removal skips absent sources); rollback is allowed before `sources-removed` and restores `saved_config/` byte-for-byte (re-staging or unstaging `project.json` to its pre-switch index state), unstages and deletes every copied destination, deletes `.aw/.gitignore` if this transaction created it, prunes journaled created directories deepest-first, and deletes the control dir last; from `sources-removed` on it refuses with "the records move is past the point of no return; finish it with resume, then switch back with aw install --records-backend <old> --relocate". `placement_switch_status` reports `mode` alongside phase, direction and counts. `fault_injection` accepts `after-copy`, `mid-verify`, `after-switch`, `mid-source-removal`; any other value (including `before-retire`) raises `ValueError` in records mode.
  - Depends on: E-03
  - Expected outcome: every fault point resumes to the completed state; the three pre-`sources-removed` points roll back to a byte-identical old side; `placement`-mode behavior unchanged.
  - Execution state: pending

### Task group 3: Tests

- [ ] E-05 Create `tests/test_records_root_switch_execute.py` (`pytestmark = pytest.mark.slow`; scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`; a FRESH real `python3 -m agent_workflows install <repo> --preset private-target -y --no-interactive` subprocess per test after an `--allow-empty` initial commit, `GIT_AUTHOR_*`/`GIT_COMMITTER_*` in the env, never `copytree` an installed repo). Fixture: commit `.aw/records/backlog/open/x.backlog.md` and `project.json` keys `cutovers.spec_id6 = "2020-01-01"`, `setids = {"warn_length": 10}`, `run = {"retry_budget": 3}`; write an ignored `.aw/records/runs/r1/state.json`. Cases: (1) `records-to-home` happy path: `x.backlog.md` and `runs/r1/state.json` byte-identical under `<AW_HOME>/projects/<id>/records/`, none left under `<repo>/.aw/records/` except `unplanned_leftovers` named in the receipt, `project_config_dir` unchanged (still in-tree), `project.json` differs from the pre-switch copy only in `records_backend`, `placements.records`, `git_policies.records` (assert by dict comparison with those three keys popped), `git diff --cached --name-status` shows `D` for the tracked records and `M` for `project.json` and nothing else, `git rev-list --count HEAD` unchanged, receipt present, control dir gone; (2) `records-to-target` happy path from a repo installed `--preset private-target --records-backend home` with home records: in-tree records, tracked ones staged `A`, `runs/r1/state.json` present and `git check-ignore` reports it ignored, home `records/` holds no record files; (3) a `local.json` carrying `records_backend: repository` is rewritten and the resolver follows; (4) each fault point in each direction, then `resume_placement_switch` reaches the (1)/(2) end state and `placement_switch_status` reported `mode == "records"` in between; (5) each pre-`sources-removed` fault point rolls back to a byte-identical repo (paths, sha256, `git status --porcelain`, `git diff --cached`) and an `AW_HOME` with no new record files and no control dir; (6) rollback refused after `mid-source-removal` naming resume; (7) blockers: a dirty `.aw/records` file names `dirty-aw-tree` and writes nothing (snapshot), a non-identical file at a destination names `destination-not-empty`, `records_backend=companion` names `companion-unsupported`; (8) an existing `placement`-mode journal (written by calling `execute_placement_switch(..., fault_injection="after-copy")` for a `local-only` policy on the SAME repo, so both share `<AW_HOME>/placement-switches/<project_id>/`) blocks `execute_records_root_switch` and vice versa; (9) independent postcheck: re-derive the expected destination set from the pre-switch snapshot (every file under the old root except `INDEX.json`/`INDEX.md` and scaffold sources planned as `discard` because their destination pre-existed); and (10) pre-existing destination scaffold: pre-create `<AW_HOME>/projects/<id>/records/backlog/README.md` with DIFFERENT bytes, plan shows that source as `discard` with no blocker, and both a completed switch and an `after-copy` rollback leave that file byte-identical and compare sorted with sha256. Mutation proofs, each restored before the next: (M1) skip the `local.json` rewrite: case (3) fails on the resolver root; (M2) skip the config restore in rollback: the `after-switch` case of (5) fails. Restore, `git diff` clean. Run `python3 -m pytest -o addopts="" -m '' tests/test_records_root_switch_execute.py tests/test_placement_switch_plan.py tests/test_placement_switch_execute.py tests/test_placement_switch_retire.py -v` and bare `python3 -m pytest`.
  - Depends on: E-04
  - Expected outcome: all cases pass; M1 and M2 fail their named cases then pass after restore; the `cfgreloc` modules stay green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Spec `20260810-1447-01` Section 11.2: lock, per-item journal, verify before switch, switch last, resume from the transaction's own item list, independent postcheck, Git changes staged never committed. Section 8.2 (Order 01) applies it to the records class alone.
- Atomic JSON writes are `tmp` + `os.replace` (`install_wizard.persist_project_policy`); locks are `platform_lock.acquire` (non-blocking, `LockBusy`).
- `cfgreloc` plans `xvlemm` and `6u755v` define the census, blocker ids, journal location and fault-point names this plan extends; reuse, do not fork.
- Tests are behavioral in scratch dirs; never install into this repository.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The records root follows `records_backend` alone. | `project_context.resolve_project_context` `# records root` block: `repository`/`repository-untracked` -> `<repo>/.aw/records`, `companion` -> companion dir, else `project_aw_dir/records`. |
| F-02 | `local.json` outranks `project.json` for `records_backend`. | `resolve_project_context`: "elif merged_local_binding.get(\"records_backend\"):" precedes "elif project_policy_data.get(\"records_backend\"):". |
| F-03 | A records-only change leaves stale placement labels today. | `install_wizard.resolve_policy_noninteractive` keeps `placements = existing_policy.placements` when no preset is passed; authoring probe `project.json` after the bug still read `"records": "target-tracked"` with `records_backend: home`. |
| F-04 | `layout_migration.MigrationManager` is not reusable here. | Authoring probe: `aw migrate-layout apply --target-backend home -y` on a fresh `private-target` repo printed `FAIL Migration plan invalid: ... partial-aw:inbox has unknown owner/disposition` and moved nothing; its switch writes the legacy `config.json` (`cfgreloc` `xvlemm` F-01). |
| F-06 | The home records root may already hold installer scaffold before a `records-to-home` move. | Review probe: after the backlog bug state, `<AW_HOME>/projects/repo-793064/records` held 41 scaffold files byte-identical to the in-tree ones (only `backlog/mine.md` differed); `6u755v` E-03 copy "refuse if the destination exists and is not hash-identical" and rollback "delete every destination this transaction copied", so a scaffold whose bytes differ would refuse at copy despite the planner's exemption, and an identical pre-existing one could be deleted by rollback. E-01 makes such sources `discard` and journals pre-existing identical destinations `preexisting`. |
| F-05 | One control dir per project serializes both switch kinds. | `6u755v` E-01 places the journal at `<AW_HOME>/placement-switches/<project_id>/` and refuses when a journal exists; a shared location means a records move and a placement switch can never interleave. |

## Proposed changes (ordered, validatable)

1. Planner reusing the `xvlemm` census and blockers (E-01).
2. Executor reusing the `6u755v` journal, lock, copy and verify (E-02).
3. In-place authority flip, source removal, receipt (E-03).
4. Recovery dispatch by journal mode (E-04).
5. Tests with an independent postcheck and mutation proofs (E-05).

## Deferred / out of scope (with reason)

- CLI surface: Order 03.
  - Carrier: vv9ki4
- Companion records backends.
  - Carrier: n9vd2h
- Moving config or durable state: a records-only switch keeps both in place by definition; full placement switches are Set `cfgreloc`.
  - Carrier: c54a4z

## Scope check

- Over-scope: none; any helper extraction inside `placement_switch.py` is behavior-preserving and proven by the `cfgreloc` test modules.
- Under-scope: none; every Section 8.2 obligation (lock, journal, verify, single flip, staged changes, resume, rollback, independent check) has an E-item and a test case.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_records_root_switch_execute.py -v` passes, all fault points included.
- Mutations M1 and M2 fail their named cases, then pass after restore.
- `tests/test_placement_switch_plan.py`, `tests/test_placement_switch_execute.py`, `tests/test_placement_switch_retire.py` and bare `python3 -m pytest` pass.

## Spec / documentation sync

N/A: implements spec Section 8.2 as written by Order 01 (`s07f73`). If the contract proves unimplementable as written, STOP and record a blocking open question rather than diverging; a spec amendment would need its own declared scope.

## Open questions

### OQ-01: Rewrite `project.json` in place or reuse `persist_project_policy`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: In place, inside the transaction. `persist_project_policy` also rewrites `local.json` path fields and is guarded by Order 01 against exactly this change; the transaction needs a single journaled atomic write it can undo from `saved_config/`. Order 03 still calls `persist_project_policy` after a completed switch, which is then a same-root update the guard allows.

### OQ-02: Should the old records directory itself be removed?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Only emptied directories are pruned. Unplanned files (written after planning) are never deleted and are listed in the receipt, matching `6u755v` E-04's `unplanned_leftovers` rule; the following install re-scaffolds the new root.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `grep -n` re-measurement; pasted diff of `plan_records_root_switch` showing the call to `install_wizard.records_root_switch` and the shared census helper; pasted `json.dumps(plan.to_dict(), indent=2)` (first item of each kind) for a scratch `records-to-home` request; pasted `tests/test_placement_switch_plan.py` pass line after any extraction.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted scratch run showing a blocked request writes nothing (`find <AW_HOME>/placement-switches` empty before and after) and a held lock refusing with `another placement switch is running`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted scratch run of `execute_records_root_switch` (reachable by a direct call from a scratch driver script) printing the resolver records root before and after, the three-key `project.json` diff, `git diff --cached --name-status`, and the receipt JSON.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `placement_switch_status` output showing `mode: records` after an injected `after-switch` fault, then pasted `rollback_placement_switch` result and a byte-identical snapshot comparison.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `-v` runner output with every case PASSED; pasted case (10) PASSED line and the pre-existing scaffold sha256 before and after; pasted failure lines for M1 and M2 and the post-restore pass with `git diff --stat` empty; pasted bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `s07f73` and `6u755v` are executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never install into this repository or touch the real home. Paste ACTUAL runner output. Scope fence: `- Scope-Paths:`; justify any other edit at finalize with `--scope-reason`. Commit through `aw commit fxbm7j -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize fxbm7j` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
