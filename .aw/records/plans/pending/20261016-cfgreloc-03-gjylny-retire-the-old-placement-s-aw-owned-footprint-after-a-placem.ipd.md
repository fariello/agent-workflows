# IPD: Retire the old placement's AW-owned footprint after a placement switch

- Date: 2026-10-16
- Kind: child
- Concern: After a placement switch the OLD side still holds AW-owned files: for `to-home` the target keeps `.aw/system/**`, `.aw/.gitignore`, `.aw/inbox/README.md`, `.aw/setup-repo-needed.md`, `.aw/workflow-artifacts/`, managed host adapters (`.claude/commands/*.md`, `.opencode/commands/*.md`, `.agents/skills/**`) and the managed `AGENTS.md` block, all tracked by a `private-target` install (Order 02 `xvlemm` F-02); for `to-target` the home dir `<AW_HOME>/projects/<id>/` keeps `system/`, `state/`, `config/`. Leaving them means a `completely-clean-target` repo is not clean (the preset's whole point) and, worse, `project_context.project_config_dir` and `project_system_dir` would still find in-tree material. `engine.uninstall_repo` already removes exactly this footprint, manifest-driven and drift-preserving, but it auto-selects its side through `engine._clean_delta_home_trees(repo_root)`, which after a `to-home` flip returns the NEW home trees, so calling it as-is would delete the freshly moved destination instead of the old target files.
- Scope: IN: `placement_switch.retire_footprint(repo_root, side, *, use_git=True, preserve=(), changed_out=None) -> list[str]` that retires ONE explicit side; for `side="target"` it calls `engine.uninstall_repo(repo_root, use_git, home_trees=None, ...)` through a new keyword `engine.uninstall_repo(..., side="target")` that forces the in-tree branch (skips the `_clean_delta_home_trees` auto-detect and the clean-delta lane teardown) while keeping every existing caller's default behavior; `preserve` is a set of repo-relative paths the retirement must not touch (the executor passes the already-handled config and records paths); for `side="home"` it removes only `<project_dir>/system`, `<project_dir>/state` and the remaining `<project_dir>/config` files, then prunes `<project_dir>` only when empty, refusing (raising) if `<project_dir>/records` still holds files. OUT: moving data (Order 04), CLI (Order 05).
- Scope-Paths: agent_workflows/placement_switch.py, agent_workflows/engine.py, tests/test_placement_switch_retire.py
- Item-Dependencies: executed:xvlemm
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 3
- Highest E allocated: 04
- Author: opencode
- Id: gjylny

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cfgreloc graduating backlog ui1aln.

## Goal

The only deletion code in the Set is one reviewable primitive that removes the old placement's AW-owned files on exactly the side it is told, reusing the existing manifest-driven uninstall rather than a second hand-written sweep, and never touching user content or the new side.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Side-explicit uninstall

- [ ] E-01 In `agent_workflows/engine.py` add keyword-only `side: Optional[str] = None` to `uninstall_repo`. `None` keeps today's behavior exactly. `side="target"` forces `home_trees = None` WITHOUT calling `_clean_delta_home_trees` (so the clean-delta lane teardown block and every `if home_trees is not None:` branch are skipped) and passes `home_trees=None` to `plan_uninstall`; any other value raises `ValueError`. Also accept keyword `preserve: frozenset[str] = frozenset()` and skip any repo-relative path in it (or under a preserved directory) in the step-4 `.aw/config` and `.aw/state` sweeps and the manifest-driven removal loop. Inside `side="target"`, `_system_member_destination` must resolve system members to `<repo>/.aw/system/...`: pass an explicit empty `home_trees={}` sentinel to it (its `if home_trees is None: home_trees = _clean_delta_home_trees(repo_root)` auto-detect would otherwise pick the new home system dir); `{}` has no `"system"` key so it falls through to `project_system_dir`, which must also be bypassed: compute `repo_root / AW_SYSTEM_DIR` directly when `side == "target"`.
  - Depends on: none
  - Expected outcome: default calls unchanged (the existing uninstall suites stay green); `side="target"` on a repo whose authoritative config is already home-placed removes only in-tree AW files.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/placement_switch.py` add `retire_footprint(repo_root, side, *, use_git=True, preserve=(), changed_out=None)`. `side="target"`: call `engine.uninstall_repo(repo_root, use_git, side="target", preserve=frozenset(preserve), changed_out=changed_out)` with `force=False` and no `drift_decider`, so user-edited managed files are PRESERVED and reported (existing uninstall contract), then return its actions. `side="home"`: resolve `<AW_HOME>/projects/<id>` with `project_context._resolve_effective_aw_home` and `_derive_project_id(_canonical_path(checkout_main_root(repo) or repo))` (the same derivation `engine._clean_delta_home_trees` case (b) uses), refuse with `PlacementSwitchError` if `records/` under it has any file, else remove `system/`, `state/`, `config/` and `worktrees/.owners` and prune empty dirs; it never runs `git` (home is not a repo). Return human-readable actions.
  - Depends on: E-01
  - Expected outcome: one call per side; neither side's call can reach the other side.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-03 Create `tests/test_placement_switch_retire.py` (`unittest.TestCase`, scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`, real install subprocess in `setUpClass`, per-test `copytree`). Cases: (1) target side on a `private-target` install after simulating the flip (write a valid home `project.json` for the repo and delete the in-tree config files): every manifest-owned in-tree file is gone, deletions are STAGED (`git diff --cached --name-status` shows `D`), nothing is committed (`git rev-list --count HEAD` unchanged), the home tree is byte-identical before and after (snapshot), a user file `notes/mine.md` and a user section in `AGENTS.md` outside the managed block survive; (2) a hand-edited `.claude/commands/aw.md` survives and is reported `PRESERVED`; (3) `preserve={".aw/records"}` leaves `.aw/records/**` untouched; (4) home side removes `system/`, `state/`, `config/`, prunes the project dir, and the target repo tree is unchanged; (5) home side with a file under `records/` raises and removes nothing; (6) `uninstall_repo` default (`side=None`) on a `completely-clean-target` install still removes the home trees (regression of the existing contract). Then run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_retire.py tests/test_uninstall_layout_artifacts.py -v` and every other module whose name contains `uninstall` (`ls tests | grep uninstall`).
  - Depends on: E-02
  - Expected outcome: all pass; the existing uninstall modules pass unchanged.
  - Execution state: pending

- [ ] E-04 Mutation proof: temporarily make `side="target"` fall through to the `_clean_delta_home_trees` auto-detect, run case (1), confirm it fails (home tree snapshot differs or in-tree files remain), restore, confirm with `git diff`, rerun green. Run bare `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: the mutant fails case (1); restored code passes; bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `engine.uninstall_repo` "Stages deletions (git rm -f when tracked/staged) and never commits. Never touches user content outside the framework namespace" (its docstring); a user-EDITED owned file is preserved unless `force` or `drift_decider` says remove.
- Managed `AGENTS.md` content is removed by `engine.remove_agents_pointer`, which strips only the managed block (`_strip_managed_block`) and leaves user prose.
- Tests drive real installs in scratch dirs (`tests/test_uninstall_layout_artifacts.py` `test_real_install_uninstall_deep_cleanup_removes_aw_directory` is the precedent).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `uninstall_repo` auto-selects the home side whenever the repo currently resolves as clean-delta. | `engine.uninstall_repo`: "if home_trees is None: home_trees = _clean_delta_home_trees(repo_root)"; `_clean_delta_home_trees` case (a) "if _is_clean_delta_install(repo)". After a to-home flip that predicate is true. |
| F-02 | `_system_member_destination` independently auto-detects the home system dir. | `engine._system_member_destination`: "if home_trees is None: home_trees = _clean_delta_home_trees(repo_root)" then `project_system_dir(repo_root)`, which reads the stored placement (`project_context.project_system_dir` -> `_stored_physical_classes`). |
| F-03 | The in-tree branch of step 4 already removes `.aw/config/**`, `.aw/state/**`, layout files and `.aw/.gitignore`, and step 7 prunes empty `.aw/` dirs. | `engine.uninstall_repo` comments "# 4. Deterministic framework-created lifecycle files" and "# 7. Prune now-empty directories under .aw". |

## Proposed changes (ordered, validatable)

1. `side`/`preserve` keywords on `uninstall_repo` (E-01).
2. `retire_footprint` for both sides (E-02).
3. Tests (E-03) and a mutation proof (E-04).

## Deferred / out of scope (with reason)

- Calling `retire_footprint` at the right moment of the transaction: Order 04.
  - Carrier: 6u755v
- A `--deep` style removal of user-created scaffolding (`engine.run_deep_cleanup`): the switch retires only framework-owned files, per spec Section 11.2 item 9's "never deletes without an explicit choice".
  - Carrier-Declined: deliberate non-goal; the operator can still run `aw uninstall --deep` on purpose.

## Scope check

- Over-scope: none; the `engine.py` change is two keyword parameters whose defaults preserve every current caller.
- Under-scope: none; both retire sides named in Order 02's `retire_side` are implemented.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_retire.py -v` passes.
- Every existing `tests/*uninstall*` module passes unchanged.
- Mutation proof (E-04) fails then passes.
- Bare `python3 -m pytest` passes.

## Spec / documentation sync

N/A: spec Section 8.1 (Order 01) already states that old-side tracked files are removed with `git rm` and left staged; this child implements that. No user-facing surface changes here.

## Open questions

### OQ-01: Reuse `uninstall_repo` or write a dedicated sweep?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Reuse. `uninstall_repo` already encodes the manifest ownership, drift preservation, managed-block stripping and stage-not-commit rules (F-03); a second sweep would duplicate them and drift. The only defect for this use is side auto-detection (F-01, F-02), fixed with an explicit keyword whose default is today's behavior.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- agent_workflows/engine.py` showing the `side`/`preserve` keywords and their defaults.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/placement_switch.py` for `retire_footprint`, and the returned action list from one target-side and one home-side scratch call.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `-v` output of `tests/test_placement_switch_retire.py` and of every `tests/*uninstall*` module, all passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted failing case (1) output under the mutant, `git diff --stat` after restore, the passing re-run, and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `xvlemm` is executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never run a retirement against this repository or the real home. Paste ACTUAL runner output. Mutation proofs are temporary and MUST NOT be committed. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit gjylny -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize gjylny` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
