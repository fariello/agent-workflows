# IPD: Pure placement-switch planner with blockers and per-item moves

- Date: 2026-10-16
- Kind: child
- Concern: Relocating config between the target and `AW_HOME` (backlog `ui1aln`) touches four physical classes with different rules (spec `20260810-1447-01` Section 8.1, added by Order 01 `ppu39q`), and the existing `layout_migration.MigrationManager` cannot be reused for it: its switch phase writes `cfg_data["records_backend"] = target_backend` into the LEGACY `self.config_dir / "config.json"`, its `config_dir`, `durable_state_dir` and `records_dir` are hard-wired to `<target>/.aw/`, and its inventory roots (`layout_inventory.DEFAULT_ROOTS`) are legacy `.agents/`-era roots. A dedicated, read-only planner is needed before anything moves, so the transaction (Order 04) and the CLI preview (Order 05) both consume one computed plan.
- Scope: IN: new module `agent_workflows/placement_switch.py` with dataclasses `SwitchItem` (class, source, destination, kind `move`/`discard`/`rewrite`, `tracked`, sha256, size, mode) and `SwitchPlan` (repo, project_id, from/to preset, from/to config dirs, `direction` `to-home`/`to-target`, items, `retire_side`, blockers, warnings, `to_dict()`), and `plan_placement_switch(repo_path, new_policy, *, aw_home=None) -> SwitchPlan`; read-only (no writes, no `mkdir`; subprocess only `git status --porcelain`, `git ls-files` and `git worktree list --porcelain`, each with `GIT_OPTIONAL_LOCKS=0`). OUT: executing, retiring, CLI.
- Scope-Paths: agent_workflows/placement_switch.py, tests/test_placement_switch_plan.py
- Item-Dependencies: executed:ppu39q
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 2
- Highest E allocated: 03
- Author: opencode
- Id: xvlemm

## Workflow history
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cfgreloc graduating backlog ui1aln.

## Goal

One pure function answers "what exactly would switching this repo to that preset move, drop and delete, and is it safe to do now?", with no side effects, so a preview, a refusal and the transaction never disagree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Planner

- [ ] E-01 Create `agent_workflows/placement_switch.py` with `SwitchItem`, `SwitchPlan` and `plan_placement_switch`. Detection reuses `install_wizard.config_placement_switch(repo, new_policy, existing_policy=install_wizard.resolve_existing_policy(repo))` (Order 01; since the `ppu39q` review it returns a `PlacementSwitch(current_dir, target_dir, reason)` and detects companion pairs ONLY through its `label` branch, which needs `existing_policy`, because the companion preset's config writer resolves to the same in-tree dir as `private-target`'s). When it returns `None`, return a plan with no items and `blockers=["not-a-placement-switch"]`. When either side is `public-target-private-companion`, return a plan with no items and `blockers=["companion-unsupported"]` (E-02) instead of building a census whose `current_dir == target_dir`. Resolve the OLD side with `project_context.resolve_project_context(target_repo=repo)` (stored policy) and the NEW side with the same call passing `new_policy`'s `delivery_mode`, `records_backend`, `preset`, `role`, `companion_dir`, `aw_home`. Items per class (spec Section 8.1 item 4): `config_project` -> one `rewrite` item (old `project.json` to new path; the executor writes the merged document, it does not copy bytes); `config_local` -> `rewrite` (re-derived: only `human_slug`, `runtime_overrides`, `local_aliases` and unknown fields carry; path fields `common_dir`/`worktree_path`/`companion_dir` are dropped as machine-local to the old layout; `project_id` is NOT carried but set to the destination's id, see the `project-id-mismatch` blocker in E-02); every regular file and symlink under the old `records` root -> `move`, INCLUDING the git-ignored ones (`records/runs/`, `records/history.jsonl`, `records/*/untracked/` are user data and move with `tracked=False`), with the single exception of the generated `records/*/INDEX.json`/`INDEX.md` files, which are `discard` because `aw index` regenerates them; old `state_durable` -> `move` for `history/` and `install.json` only, `discard` for everything else; `state_runtime` -> `discard`; `system`, `.aw/.gitignore`, `.aw/setup-repo-needed.md`, `.aw/inbox/README.md`, `.aw/workflow-artifacts/` and the managed host adapters -> not items (Order 03 retires them; the following install re-materializes them). Set `retire_side` to `target` for `to-home` and `home` for `to-target`. Include `tracked` from one `git ls-files -z` call over the repo, and sha256/size/mode per moved file. EVERY git subprocess runs with `GIT_OPTIONAL_LOCKS=0` in its `env` (and `-c core.fsmonitor=false`): a plain `git status --porcelain` refreshes and rewrites `.git/index` when a tracked file's stat data changed (review probe: `touch AGENTS.md` then `git status` changed the index mtime, `GIT_OPTIONAL_LOCKS=0` left it unchanged), which would make the "read-only" planner write and fail the E-03 purity snapshot.
  - Depends on: none
  - Expected outcome: module imports with no side effects; `plan_placement_switch` on a scratch `private-target` repo with a `local-only` policy returns `direction="to-home"`, a `config_project` rewrite, one `move` per record file, `retire_side="target"`.
  - Execution state: pending

- [ ] E-02 Add blocker detection to `plan_placement_switch` (spec Section 8.1 item 7), each a stable string id plus a human message: `dirty-aw-tree` (`git status --porcelain -- .aw` non-empty, ignoring paths `.aw/.gitignore` ignores, i.e. use plain `git status --porcelain`, which already omits ignored files); `unmerged` (any `U` status in `git status --porcelain`); `destination-not-empty` (any item destination exists and is not hash-identical to its source; and for `to-home`, the new `<AW_HOME>/projects/<id>/` directory contains a `records/` or `config/` child not explained by an existing journal); `live-lane` (`git worktree list --porcelain` reports a worktree under the old worktrees root, `worktree_lease.worktrees_root(repo)`); `unparseable-config` (the planner itself `json.load`s every present old config file (`project.json`, `local.json`, legacy `config.json`/`policy.json`) and any that fails to parse or is not a JSON object blocks; it MUST NOT rely on `resolve_project_context` or `resolve_existing_policy`, which both silently tolerate a malformed `project.json` (review probe: `[1,2` in `project.json`, both returned `private-target` with no error)); `project-id-mismatch` (`to-home` only: the destination home project dir the new-side `resolve_project_context` resolves, which honors a `project_id` stored in the old `local.json` ("if isinstance(local_pid, str) and local_pid.strip()"), differs from `<aw_home>/projects/<_derive_project_id(_canonical_path(checkout_main_root(repo) or repo))>`, the dir `project_config_dir` will read after the flip because it derives the id from the path and never reads `local.json`; switching in that state recreates the split brain, e.g. a moved or copied checkout whose `local.json` still names the old path's id: review probe on a `cp -a` copy `rc` printed derived id `rc-af4372` while the new writer resolved `.../projects/r-2598b2/config/project.json`); `to-target` has the mirror check (the old home dir must be the derived one, else the planner is reading a config the reader does not use); `companion-unsupported` (either side is `public-target-private-companion`, message names backlog `n9vd2h`); `source-checkout` (`project_role == "source-checkout"`; never relocate the framework's own repo). Add warnings (not blockers): `records-become-untracked` for `to-home` with a count of tracked record files; `records-become-tracked-candidates` for `to-target`.
  - Depends on: E-01
  - Expected outcome: each blocker is produced by exactly its condition and the plan with any blocker is still fully populated (so a preview can show everything), except the two short-circuit blockers `not-a-placement-switch` and `companion-unsupported`, which return an empty item list.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-03 Create `tests/test_placement_switch_plan.py` (`unittest.TestCase`, scratch dirs with patched `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`; set up repos with a real `python3 -m agent_workflows install <repo> --preset <p> -y --no-interactive` subprocess in `setUp`, one fresh repo per test (see the copy note below); a git repo whose install is committed needs `GIT_AUTHOR_*`/`GIT_COMMITTER_*` in the subprocess env, and an `--allow-empty` initial commit so the installer's sync commit lands (review probe: on a repo with no commits the 357 files stay staged `A`, which would trip `dirty-aw-tree`)). Cases: to-home item census (a committed `.aw/records/backlog/open/x.backlog.md` appears as a tracked `move` with the right destination under `<AW_HOME>/projects/<id>/records/`); to-target census from a `local-only` repo; `not-a-placement-switch` for a same-placement policy; `companion-unsupported` (not `not-a-placement-switch`) for a `private-target` repo given a `public-target-private-companion` policy; `project-id-mismatch` on a `cp -a` copy of a `private-target` repo given a `local-only` policy; every blocker in E-02 triggered by its minimal condition and absent otherwise; warnings counts; purity: after `touch`ing one tracked file, snapshot `(path, mtime_ns, size)` for every file under the repo INCLUDING `.git/` and under `AW_HOME` before and after `plan_placement_switch` and assert equality, plus `git status --porcelain` unchanged. Do NOT share one installed tree across tests by copying it: the project id is path-derived but a `private-target` install's `local.json` stores `project_id`, so a `shutil.copytree` copy resolves its home destination to the ORIGINAL's dir (review probe: copy `rc` wrote to `r-2598b2`) and the copies collide in `AW_HOME`, and a copied `local-only` repo has no config at all (its config is keyed by the original path; probe: `resolve_existing_policy` on the copy returned `None`). Install fresh per test into its own temp dir (one install measured `real 0m3.038s`); the copy case is instead the deliberate fixture for the `project-id-mismatch` blocker. Mark the class that runs the install subprocess `@pytest.mark.slow`. Run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_plan.py -v` and bare `python3 -m pytest`.
  - Depends on: E-02
  - Expected outcome: all cases pass; purity snapshot identical.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `project_context.project_config_dir` returns `<repo>/.aw/config` when ANY of `project.json`, `local.json`, `config.json`, `policy.json` exists there (its docstring rule 1), so the old side is authoritative until all four are gone; the planner records all present ones.
- The project id is derived from the canonical path (`project_context._derive_project_id`: slug plus sha256 prefix of the path), so the home destination is per checkout path.
- Linked worktree lanes resolve config through `checkout_main_root` (`project_config_dir` docstring, IPD `fnnwj3`), so a live lane is a real hazard during a flip.
- Tests run behaviorally in scratch dirs (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE").

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `MigrationManager` cannot express this switch. | `layout_migration.MigrationManager.__init__` sets `self.config_dir = self.aw_dir / "config"` etc.; its switch phase writes `cfg_data["records_backend"] = target_backend` into `config.json`; `layout_inventory.DEFAULT_ROOTS` lists `.agents`, `workflow-artifacts`, installer backups, `.aw`, adapters and pointer files. |
| F-02 | A `private-target` install tracks `.aw/config/project.json`, `.aw/.gitignore`, `.aw/inbox/README.md`, `.aw/records/**`, `.aw/system/**`, `.agents/skills/**`, `.claude/commands/**`, `.opencode/commands/**`, `AGENTS.md` and leaves `.aw/state/**`, `.aw/config/local.json`, `.aw/workflow-artifacts/` ignored. | Authoring probe: `git ls-files` after `install --preset private-target -y` (357 files committed by the installer's own "agent-workflows: sync via installer" commit) and `.aw/.gitignore` content (`/state/`, `/config/local.json`, `/workflow-artifacts/`, `/worktrees/`). |
| F-03 | A `local-only` / `completely-clean-target` install leaves the target with only `.git`; everything lives under `<AW_HOME>/projects/<id>/{config,records,state,system}`. | Authoring probe: `ls -a` of the repo after `install --preset local-only -y` printed only `.`, `..`, `.git`; home tree listing shows the four children. |
| F-05 | `git status` writes `.git/index` unless `GIT_OPTIONAL_LOCKS=0`. | Review probe: index mtime changed after `touch AGENTS.md; git status --porcelain`; unchanged with `GIT_OPTIONAL_LOCKS=0`. |
| F-06 | A `private-target` `local.json` stores `project_id`, which `resolve_project_context` prefers over the path-derived id, while `project_config_dir` only derives. | `project_context.resolve_project_context` "if isinstance(local_pid, str) and local_pid.strip():"; `project_config_dir` "project_id = _derive_project_id(anchor_abs)"; review probe on a copied checkout. |
| F-04 | Both home presets resolve the same config dir, so a switch between them is not a placement switch. | `resolve_project_context` `config root` block keys only on `delivery_mode` (`clean-delta` for both, `install_wizard.get_preset_defaults`); authoring probe `install --preset completely-clean-target` over a `local-only` repo exited `0`. |

## Proposed changes (ordered, validatable)

1. Module, dataclasses and the census (E-01).
2. Blockers and warnings (E-02).
3. Tests including a purity snapshot (E-03).

## Deferred / out of scope (with reason)

- Executing the plan: Order 04.
  - Carrier: 6u755v
- Retiring system, adapters and the old config footprint: Order 03.
  - Carrier: gjylny
- Companion pairs: refused with `companion-unsupported`.
  - Carrier: n9vd2h

## Scope check

- Over-scope: none.
- Under-scope: none; every class in spec Section 4 is assigned a disposition (moved, rewritten, discarded, or retired by Order 03 and re-materialized by the install).

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_plan.py -v` passes, including the purity snapshot.
- Bare `python3 -m pytest` passes.

## Spec / documentation sync

N/A: the contract this implements is written by Order 01 (`ppu39q`, spec Section 8.1); this child adds an internal module with no user-facing surface.

## Open questions

### OQ-01: Should records moved into the target be staged automatically?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The planner only reports them (`records-become-tracked-candidates`). Spec Section 11.2 item 10 says migration generates Git plans "without committing or pushing", and the normal install's `engine.prompt_and_run_commit` already offers to commit installer paths; Order 04 stages moved records (`git add`) and leaves them uncommitted; Order 05 (`ozr356` E-03) keeps them OUT of `engine.prompt_and_run_commit`'s `files_to_commit`, so the operator commits them deliberately. (Amended at review: the earlier text said the commit offer "includes them", which contradicted `ozr356` E-03.)

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted new-file diff of `agent_workflows/placement_switch.py` showing the call to `install_wizard.config_placement_switch`; pasted `json.dumps(plan.to_dict(), indent=2)` (truncated to the first item of each kind) for a scratch to-home switch; pasted proof of purity on that run: `stat -c %y .git/index` before and after `plan_placement_switch` after a `touch` of a tracked file, identical.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted per-blocker probe output (blocker id list for each minimal condition, including `companion-unsupported` for a `private-target` -> `public-target-private-companion` request and `project-id-mismatch` for a copied checkout, and for the clean case, which must be empty).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `-v` runner output of `tests/test_placement_switch_plan.py` with every case PASSED, and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `ppu39q` is executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never install into this repository or touch the real home. Paste ACTUAL runner output. Scope fence: `- Scope-Paths:`; justify any other edit at finalize with `--scope-reason`. Commit through `aw commit xvlemm -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize xvlemm` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
