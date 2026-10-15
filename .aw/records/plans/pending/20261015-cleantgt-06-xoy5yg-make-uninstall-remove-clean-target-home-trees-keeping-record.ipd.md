# IPD: Make uninstall remove clean-target home trees, keeping records unless deep

- Date: 2026-10-15
- Kind: child
- Concern: After Set children 01..05 a clean-delta install puts `system/`, `records/`, `config/`, `state/` (including run state, receipts, locks, journals, installer backups and the setup marker) and isolated lane worktrees (`worktrees/<id6>/`) under `<AW_HOME>/projects/<project_id>/`, but `engine.uninstall_repo` only removes home `config/` (`project.json`, `local.json`) and `state/`, `engine.plan_uninstall` resolves manifest entries as `repo_root / rel`, `engine.plan_deep_cleanup`/`engine.run_deep_cleanup` walk only `repo_root / root` for `_DEEP_CLEANUP_ROOTS`, and `cli._uninstall_dry_run_report` lists only home config/state. So `aw uninstall` on a clean target would orphan home `system/` and `worktrees/`, never offer home `records/`, and could delete a worktree a live run is using.
- Scope: Teach `engine.plan_uninstall`, `engine.uninstall_repo`, `engine.plan_deep_cleanup`, `engine.run_deep_cleanup`, `cli._run_uninstall`, `cli._uninstall_dry_run_report` and `cli._offer_deep_cleanup` the clean-delta home layout: remove home `system/`, `config/`, `state/` and `worktrees/` on a normal uninstall, keep home `records/` unless `--deep` (or the interactive records prompt says remove), tear lanes down through `worktree_lease.teardown_worktree` so git's `.git/worktrees/<name>` admin entries and lane branches go too, and REFUSE (exit 1, nothing removed) while any lane under home `worktrees/` is owned by another live process or holds unlanded work, with `--force` overriding only the holds-work case. Tests in `tests/test_clean_target_config_home.py`.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/cli.py, tests/test_clean_target_config_home.py
- Item-Dependencies: executed:3m8aix
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleantgt
- Order: 6
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xoy5yg

## Workflow history
- 2026-10-15 to-review (aw set): authored review-ready child of Set cleantgt (orchestrator ucr3h8) from backlog kvwwt0

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw uninstall <target> --yes` on a `completely-clean-target` or `local-only` install remove every agent-workflows tree under `<AW_HOME>/projects/<project_id>/` except `records/`, make `aw uninstall <target> --deep --yes` remove `records/` too and prune the project directory, leave the target with `git status --porcelain --ignored` empty, HEAD unchanged and no `.git/worktrees/` admin entry or `aw/lane/*` branch of ours, and never delete a lane a live run is using.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline and the home-tree inventory

- [ ] E-01 Re-measure at execution HEAD `engine.plan_uninstall`, `engine.uninstall_repo`, `engine.plan_deep_cleanup`, `engine.run_deep_cleanup`, `engine._DEEP_CLEANUP_ROOTS`, `cli._run_uninstall`, `cli._uninstall_dry_run_report`, `cli._offer_deep_cleanup`, `worktree_lease.teardown_worktree`, `worktree_lease.inspect_lane`, `worktree_lease.lane_owned_by_other_live_process`, `lanes_cli.collect_lane_rows`, and the accessors Set children 01, 02 and 04 delivered (records root, system root, home state root, home worktrees root, all in `agent_workflows/project_context.py` or `worktree_lease`). Reproduce the baseline: temp repo, temp `HOME`/`AW_HOME`, clean-target install, `aw work begin <plan>` to create one lane, then `aw uninstall <t> --yes`, and list what remains under `<AW_HOME>/projects/<id>/`, `git worktree list`, and `git branch --list 'aw/lane/*'`.
  - Depends on: none
  - Expected outcome: Accessor names and the baseline residue recorded in V-01 (expected: `system/`, `records/`, `worktrees/<id6>/` remain; the lane is still registered).
  - Execution state: pending

- [ ] E-02 Add `engine._clean_delta_home_trees(repo_root) -> Optional[dict]` returning, only when the stored policy is clean-delta (`engine._is_clean_delta_install` from `3m8aix`), the resolved home paths `{"project_dir", "system", "config", "state", "worktrees", "records"}` taken from `resolve_project_context(target_repo=...).physical_classes` plus the child-04 worktrees accessor (never composed from a preset name), and `None` otherwise. `records` is included only when it resolves under `project_dir` (`records_backend == "home"`); a companion records root is never touched by uninstall.
  - Depends on: E-01
  - Expected outcome: Returns the six paths for both clean presets, `None` for private-target and companion presets and for a repo with no stored config.
  - Execution state: pending

### Task group 2: Lanes first, refusing while a lane is live

- [ ] E-03 Add `engine._home_lane_preflight(repo_root, worktrees_root) -> tuple[list, list, list]` that enumerates registered worktrees from `git worktree list --porcelain` (the discovery surface `worktree_lease._registered_worktrees` and `lanes_cli.collect_lane_rows` use) whose path is under `worktrees_root`, plus any directory under `worktrees_root` git does not register, and classifies each into `live` (`worktree_lease.lane_owned_by_other_live_process` is True), `holds_work` (`worktree_lease.inspect_lane(...).state == LANE_HOLDS_WORK`), or `removable`. In `cli._run_uninstall`, before `_confirm`, call it for a clean-delta target: any `live` lane REFUSES with exit 1 and a message naming each lane id and path and telling the user to stop the run or run `aw lanes prune`; any `holds_work` lane refuses unless `--force`, and with `--force` prints a warning naming the work being discarded. `--dry-run` reports the same classification without refusing.
  - Depends on: E-02
  - Expected outcome: With a lane whose owner record names a different live pid, `aw uninstall <t> --yes` and `--yes --force` both exit 1 and nothing under `<AW_HOME>/projects/<id>/` is removed; with a dirty non-live lane, `--yes` exits 1 and `--yes --force` proceeds with a warning.
  - Execution state: pending

- [ ] E-04 In `engine.uninstall_repo`, for a clean-delta target, tear down every `removable` (and, under `force`, `holds_work`) lane through `worktree_lease.teardown_worktree` so the worktree directory, the git admin entry under `.git/worktrees/` and the `aw/lane/<id>` branch are removed, run `git worktree prune` in the target, clear owner records, then remove the remaining contents of the home `worktrees/` tree (including `.owners/`) and the directory itself. Record each action in the returned list. Never call `git rm`/`git add` in the target for these paths.
  - Depends on: E-03
  - Expected outcome: After uninstall, `git -C <t> worktree list` shows only the main worktree, `git -C <t> branch --list 'aw/lane/*'` is empty, and `<AW_HOME>/projects/<id>/worktrees` does not exist.
  - Execution state: pending

### Task group 3: Home system, config, state, and records

- [ ] E-05 In `engine.plan_uninstall` and `engine.uninstall_repo`, resolve each manifest `file`/`shim` entry's on-disk path through the child-02 system-root accessor (so a `.aw/system/...` entry is checked and removed at `<home>/system/...` with plain unlink, not `_uninstall_remove`'s `git rm`), then remove the whole home `system/` tree (workflows, `VERSION`, `managed-sections.json`, `layout.json`, `layout.schema.json`) and prune empty directories, preserving the drift rule (an edited owned file is kept unless `force` or the drift decider says remove). Extend the existing home `config/` + `state/` branch so `state/` removal covers `state/runtime/backups/` and `state/runtime/setup-repo-needed.md` from `3m8aix`, and prune `project_dir` only when empty.
  - Depends on: E-04
  - Expected outcome: `aw uninstall <t> --yes` removes home `system/`, `config/`, `state/` and leaves home `records/` byte-identical (same file list and hashes before and after).
  - Execution state: pending

- [ ] E-06 In `engine.plan_deep_cleanup` and `engine.run_deep_cleanup`, add the home `records/` tree for a clean-delta target as records files (absolute paths reported, `is_records` classification, at-risk because home records are never in git), and in `cli._offer_deep_cleanup` and `cli._uninstall_dry_run_report` show it under the existing records prompt and dry-run listing; `--deep` removes it and prunes `project_dir`. Make `cli._run_uninstall`'s `has_footprint` also true when any home tree from E-02 exists, and make `cli._uninstall_dry_run_report` list home `system/`, `config/`, `state/`, `worktrees/` (with the E-03 lane classification) and `records/` counts. For a clean-delta target pass `use_git=False` so `_offer_commit_uninstall` has nothing to stage or commit.
  - Depends on: E-05
  - Expected outcome: `--dry-run` lists every home tree and changes nothing; `--deep --yes` removes home `records/` and `<AW_HOME>/projects/<id>/`; a normal `--yes` non-interactive run prints the existing "pass --deep" notice and keeps records.
  - Execution state: pending

### Task group 4: Tests

- [ ] E-07 Add subprocess tests to `tests/test_clean_target_config_home.py` (P16, outcomes only): `test_case_m_uninstall_keeps_home_records` (both presets: install, create a backlog item so records hold user content, uninstall `--yes`; assert home `system/`, `config/`, `state/`, `worktrees/` absent, `records/` present with the item, target porcelain-ignored empty and HEAD unchanged), `test_case_n_uninstall_deep_removes_project_dir`, `test_case_o_uninstall_tears_down_idle_lane` (lane created with `aw work begin`; after uninstall no `.git/worktrees` entry and no `aw/lane/*` branch), `test_case_p_uninstall_refuses_live_lane` (owner record written by the test process via `worktree_lease.write_lane_owner`, so the owner is a live process other than the `aw uninstall` subprocess; assert exit 1, and every home tree still present, with and without `--force`), and `test_case_q_uninstall_dry_run_lists_home_trees`.
  - Depends on: E-06
  - Expected outcome: All new cases pass in a narrowed run.
  - Execution state: pending

- [ ] E-08 Perform the mutation proofs and the bare suite: (a) make `_home_lane_preflight` return no live lanes and observe `test_case_p_uninstall_refuses_live_lane` fail; (b) skip the home `system/` removal and observe `test_case_m_uninstall_keeps_home_records` fail; restore both and re-run; then run bare `python3 -m pytest`.
  - Depends on: E-07
  - Expected outcome: Each mutation turns its test red and restoring turns it green; bare suite shows no failure that does not also fail on the base commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `engine.uninstall_repo` docstring: "Stages deletions (git rm -f when tracked/staged) and never commits. Never touches user content outside the framework namespace." Home trees are framework namespace; home records are user content and are kept by default, matching `cli._offer_deep_cleanup`'s "Keep your authored records ... [Y/n]" default.
- `worktree_lease.teardown_worktree` docstring: "this deletes the per-lane BRANCH as well as the worktree, and `--force` also destroys UNCOMMITTED files in the lane." That is why a holds-work lane needs `--force` and a live lane is refused outright.
- `worktree_lease.lane_owned_by_other_live_process`: "Undeterminable liveness counts as owned (fail safe)." Uninstall inherits that fail-safe.
- `worktree_lease` stays stdlib-only at module level (pinned by `tests/test_worktree_lease_stdlib_only.py`); this plan only calls it and does not edit it.
- Every routing decision reads the stored policy and `resolve_project_context(...).physical_classes`; `project_context.py` stays pure.
- Suite: bare `python3 -m pytest`; narrowed runs `python3 -m pytest -o addopts="" <file> -v`. Test fixtures use temp `HOME`/`AW_HOME` and a git identity; `tests/test_clean_target_config_home.py` `TestCleanTargetConfigHome.setUp` already builds that environment and `_run_aw` drives the CLI by subprocess.

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `engine.uninstall_repo` step 4 | The home branch (entered when `repo_root/.aw/config` is absent) removes only `project.json`/`local.json` from `project_config_dir(repo_root)` and everything under `project_dir / "state"`, then `project_dir.rmdir()`, which silently fails while `system/`, `records/` or `worktrees/` exist. Home system and worktrees are orphaned. |
| F-02 | High | `engine.plan_uninstall` | `dest = repo_root / rel` for every manifest entry; with system under home every `.aw/system/...` entry is classified `missing` ("manifest entry stale") and nothing is removed. |
| F-03 | High | uninstall has no lane awareness | No uninstall symbol consults `worktree_lease` or `git worktree list`; removing `<home>/worktrees/<id6>/` by directory deletion would leave a registered-but-missing worktree and an `aw/lane/*` branch in the target `.git`, and would destroy a live run's working tree. |
| F-04 | Medium | `engine.plan_deep_cleanup` / `engine.run_deep_cleanup` | Iterate `repo_root / root` for `_DEEP_CLEANUP_ROOTS` only; home `records/` is never offered or removed by `--deep`. |
| F-05 | Medium | `cli._uninstall_dry_run_report` and `cli._run_uninstall` | Dry run lists only home `config`/`state` files; `has_footprint` keys on `has_home_cfg` and in-repo dirs, so after a partial uninstall (config gone, system left) `aw uninstall` reports "framework not installed" and cannot clean the rest. |

## Proposed changes (ordered, validatable)

1. E-01 baseline (no code).
2. E-02 `engine._clean_delta_home_trees`.
3. E-03 `engine._home_lane_preflight` and the refusal in `cli._run_uninstall`.
4. E-04 lane teardown and home `worktrees/` removal in `engine.uninstall_repo`.
5. E-05 home `system/` via the system-root accessor; extend `config/` + `state/` removal.
6. E-06 home `records/` in deep cleanup; dry run, footprint, no-commit for clean-delta.
7. E-07 tests; E-08 mutation proofs and bare suite.

## Deferred / out of scope (with reason)

- Removing user-scope host adapters for clean-delta (`~/.config/opencode/`, `~/.claude/`), since this Set never installs them; that delivery is a separate feature in deferred spec `or061f`.
  - Carrier: or061f
- Uninstalling a companion records root (`public-target-private-companion`): companion records are a separate repository the user owns and are not a clean-delta home tree; unchanged behavior, no new obligation.
  - Carrier-Declined: not a clean-delta tree and not part of backlog kvwwt0's defect; E-02 deliberately excludes a records root outside `project_dir`.
- Spec amendment and CHANGELOG line describing uninstall behavior: owned once for the whole Set by the final child.
  - Carrier: nwporz

## Scope check

- Over-scope: none. Each item serves "uninstall leaves no clean-target residue and never destroys live or unlanded work".
- Under-scope: none known. The home trees are exactly those Set children 01..05 create (`system`, `records`, `config`, `state`, `worktrees`); E-01 lists the actual residue after a baseline uninstall so a tree created by a sibling and missed here is caught before editing, and is then in scope.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -v` with the five new cases passing.
- Subprocess proof that after `--yes` the target is porcelain-ignored empty, HEAD unchanged, no lane admin entry or branch, and home `records/` unchanged; after `--deep --yes` the project directory is gone.
- Live-lane refusal proof: exit 1 and all home trees still present.
- Two mutation proofs (E-08) and the bare `python3 -m pytest` summary.

## Spec / documentation sync

N/A here: the spec `20260810-1447-01` amendment, `aw specs note` and the CHANGELOG line for the whole Set are owned by child `nwporz` (Order 07). This plan edits no spec, so no `.spec.md` is in `- Scope-Paths:`.

## Open questions

### OQ-01: Should `--force` override the live-lane refusal?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `--force` in `cli._run_uninstall` means "remove files you edited" (`uninstall_repo` drift rule) and skip the prompt; it was never consent to kill another process's working tree. A live owner is a running driver or agent whose lane would be destroyed mid-write, and `worktree_lease.lane_owned_by_other_live_process` already treats undeterminable liveness as owned. The user's remedy is explicit: stop the run, or `aw lanes prune`. `--force` does override the holds-work (non-live) case, with a warning, consistent with `teardown_worktree`'s own `force` semantics.

### OQ-02: Must uninstall remove the `aw/lane/*` branches in the target `.git`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes for lanes it tears down. The maintainer's 2026-10-15 accepted residual is git's `.git/worktrees/<name>` entry "while a lane exists"; after uninstall no lane exists, so neither that entry nor the lane branch should remain. `worktree_lease.teardown_worktree` removes both, so reusing it is the single path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `grep -n` output locating each E-01 symbol and accessor at execution HEAD, and the pasted baseline residue (`find <AW_HOME>/projects/<id> -maxdepth 2`, `git -C <t> worktree list`, `git -C <t> branch --list 'aw/lane/*'`) after a pre-change `aw uninstall --yes`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `git diff` hunk adding `engine._clean_delta_home_trees` and pasted probe output showing the six paths for both clean presets and `None` for private-target, companion and unconfigured repos.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted subprocess output (path: `cli._run_uninstall` -> `engine._home_lane_preflight`) of `aw uninstall <t> --yes` and `--yes --force` with a live-owned lane, each exiting 1 and naming the lane, plus pasted `find <AW_HOME>/projects/<id> -maxdepth 1` before and after showing nothing removed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted subprocess output (path: `engine.uninstall_repo` -> `worktree_lease.teardown_worktree`) of uninstall on a target with one idle lane, followed by pasted `git -C <t> worktree list`, `git -C <t> branch --list 'aw/lane/*'`, `ls <t>/.git/worktrees` and `ls <AW_HOME>/projects/<id>/worktrees` showing no lane residue.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `git diff -- agent_workflows/engine.py` for `plan_uninstall`/`uninstall_repo` and pasted output showing home `system/`, `config/`, `state/` absent after `--yes` and a pasted sorted `sha256sum` listing of home `records/` identical before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted `aw uninstall <t> --dry-run` output listing every home tree with counts, and pasted `aw uninstall <t> --deep --yes` output followed by `ls <AW_HOME>/projects/` showing the project directory gone, and target `git status --porcelain --ignored` empty with HEAD unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Pasted `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -v` output showing `test_case_m` through `test_case_q` PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Pasted failing output for each of the two mutations, pasted passing output after restore, and the pasted bare `python3 -m pytest` summary line, with any failure shown to fail identically on the base commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Do not execute until `- Status: approved` and `3m8aix` is executed (Item-Dependencies). Execute in an isolated worktree via `aw work begin xoy5yg` (or under `aw oc run`, which isolates by default), in order E-01..E-08. Mark an `E-*` performed only after doing it and a `V-*` pass only with concrete pasted evidence; paste the ACTUAL runner output and never claim a pass you did not run. Every probe and test uses a temp git repo with temp `HOME`/`AW_HOME`; never uninstall from this repository or touch the real home. Mutation proofs are temporary and MUST NOT be committed. Commit only the paths you changed plus this IPD through `aw commit xoy5yg -- <paths>`; never `git add -A`, never push, never `--no-verify`.

SCOPE FENCE. `- Scope-Paths:` is the expected edit set. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize xoy5yg`. Never `git mv` the plan by hand. This plan inherits `- Blocks-Release: next` from `kvwwt0`.
