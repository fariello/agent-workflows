# IPD: Fix metadata selectors self-commit routing companion locking and ipd finalize bugs

- Date: 2026-11-24
- Kind: child
- Concern: Nine verified bugs affect metadata setters, selectors, commit locking, and `ipd_lifecycle` in companion and `~/.aw/` modes: (1) `status_set._offer_self_commit` tries to `git add` unversioned `~/.aw/` records in `target_repo`, fails on unregistered custom companion dirs via `--dir`, and fails atomically on mixed-repo batches (while `offer_commit`/`commit_isolated` fail unsafely on out-of-repo absolute paths); (2) `commit_lock.writer_lock` and `ipd_lifecycle.acquire_finalize_lock` acquire different lock files in companion mode, breaking mutual exclusion; (3) `status_set._delegate_plan_executed_to_finalize` / `ipd_lifecycle.finalize` skips `_resolve_staged_companion_lane_plan`, bypassing lane isolation; (4) `ipd_lifecycle._finalize_transaction` passes companion worktree `coord.path` as `repo_root` (missing target leak allowlist and log-format detection) and reads commit identity from `target_repo` instead of `tx_git_root`; (5) `ipd_lifecycle._run_record_committed_paths` looks under `checkout_control_root / "records" / "runs"` instead of `project_records_dir / "runs"`; (6) `status_set.run_set_command` runs the orchestrator dirty-tree check against `target_repo`, failing open; (7) `status_set._prepare_status_change` and `apply_status_change` break `--rewrite-citations`, custom-companion staleness, and `read_at`/`read_path_at` `rel` paths; (8) `selectors.resolve` (`MATCH_PATH`) and `status_set.match_selector` reject records-relative paths (`plans/pending/...`, `records/plans/pending/...`); and (9) `artifact_meta.write_legacy`, `_git_target_root`, and `load_legacy_artifact` misresolve owner/git/collision roots for companion and `~/.aw/` records.
- Scope: Fix all nine bugs across `status_set.py`, `git_commit_helper.py`, `commit_lock.py`, `ipd_lifecycle.py`, `selectors.py`, and `artifact_meta.py`, with behavioral tests covering companion (sibling and custom `--dir`) and `~/.aw/` (`home`) modes.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/git_commit_helper.py, agent_workflows/commit_lock.py, agent_workflows/ipd_lifecycle.py, agent_workflows/selectors.py, agent_workflows/artifact_meta.py, tests/test_companion_ipd_lifecycle.py, tests/test_home_isolation.py, .aw/records/plans/pending/20261124-comphome-03-mmuv3v-fix-metadata-selectors-self-commit-routing-companion-locking.ipd.md
- Item-Dependencies: executed:ywl7uc
- Status: to-review
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: comphome
- Order: 3
- Highest E allocated: 5
- Id: mmuv3v
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 03 child IPD for `/assess-bugs` (Set `comphome`).

## Goal

Make `aw set`, `aw ipd finalize`, `selectors.resolve`, `commit_lock`, and `artifact_meta` writers behave safely, atomically, and consistently on companion (sibling and custom) and `~/.aw/` repositories.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Self-commit routing and commit containment

- [ ] E-01 Fix self-commit routing in `status_set._offer_self_commit`, `git_commit_helper.offer_commit`, and `commit_lock.commit_isolated`: partition touched paths by enclosing git root (consulting `resolve_project_context(target_repo=str(repo_root))` directly so custom non-sibling companions work under `--dir`), skip unversioned `~/.aw/` paths (`record_git_root(p) is None`) cleanly without prompting or running git against `target_repo`, commit each versioned repo's paths against its own root, and fail closed with a clean error on out-of-repo paths in `offer_commit` and `commit_isolated`.
  - Depends on: none
  - Expected outcome: `aw set --commit` / `--yes` succeeds cleanly on unversioned `~/.aw/`, custom companions via `--dir`, and mixed batches without `is outside repository` or `SameFileError`.
  - Execution state: pending

### Task group 2: Companion finalize locking, staged-lane delegation, worktree context, and runs attribution

- [ ] E-02 Fix `commit_lock.writer_lock` and `ipd_lifecycle` companion finalize bugs: acquire the shared companion writer lock in canonical order whenever `ipd_lifecycle.finalize` or `retire_orchestrator` commits to `tx_git_root != repo_root`; call `_resolve_staged_companion_lane_plan` inside `ipd_lifecycle.finalize` (covering `_delegate_plan_executed_to_finalize` / `aw ipd set executed`); in `_finalize_transaction`, pass `tx_git_root` to `agent_commit_identity` and thread target repo allowlist/config context with `records_root = coord.path / "records"` into `apply_status_change`; update `_run_record_committed_paths` to read `project_records_dir(repo_root) / "runs"` (falling back to `checkout_control_root / "records" / "runs"`).
  - Depends on: E-01
  - Expected outcome: concurrent `aw set --commit` and `aw ipd finalize` serialize on the same companion lock; `aw ipd set executed` inside an isolated companion lane edits the staged lane copy instead of live companion; companion finalize honors target leak allowlist, companion git identity, and exact run-record attribution.
  - Execution state: pending

### Task group 3: `status_set` guards and citation rewrites

- [ ] E-03 Fix companion and `~/.aw/` path handling in `status_set.py`: run the orchestrator dirty-tree check in `run_set_command` against `record_git_root(orch.path)` (skipping when unversioned); compute logical `.aw/records/<rel>` paths for `post_relocation_citation_rewrite` in `apply_status_change`; consult `resolve_project_context(target_repo=str(repo_root))` for `is_companion` and compute `rel` against `record_git_root(rec.path) or repo_root` in `_prepare_status_change`.
  - Depends on: E-01
  - Expected outcome: dirty companion orchestrators are refused rather than silently overwritten; `--rewrite-citations` rewrites `Scope-Paths` in companion and `~/.aw/` plans; stale-review and untooled-transition checks work on custom companions.
  - Execution state: pending

### Task group 4: `selectors` records-relative paths and `artifact_meta` owner/collision roots

- [ ] E-04 Fix `selectors.resolve` (`MATCH_PATH`), `status_set.match_selector`, and `artifact_meta.py`: resolve records-relative paths (`plans/pending/...`, `records/plans/pending/...`, `.aw/records/...`) against `project_records_dir(repo_root)` with path-containment validation; in `artifact_meta.write_legacy`, resolve `_core.repo_root_of(ltarget.path)` before `record_git_root`; in `artifact_meta._git_target_root`, consult `resolve_project_context(target_repo=str(repo_root))` before `record_owner_root`; in `artifact_meta.load_legacy_artifact`, pass `scan_repo` (or resolved target repo root) to `_core.global_id6s`.
  - Depends on: none
  - Expected outcome: `aw find plans plans/pending/<file>.ipd.md` and `aw ipd set reviewed records/plans/pending/<file>.ipd.md` resolve cleanly in companion and `~/.aw/` repos; `write_legacy`, `_git_target_root`, and `load_legacy_artifact` target the correct owner repo and non-empty id6 collision pool.
  - Execution state: pending

### Task group 5: Behavioral verification

- [ ] E-05 Add behavioral tests in `tests/test_companion_ipd_lifecycle.py` and `tests/test_home_isolation.py` covering all nine fixes, then run `python3 -m pytest`, `mypy`, and `aw sanitize`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: all targeted pytest suites pass, `mypy` reports zero errors on modified modules, and `aw sanitize` reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Never write code-pinning tests; assert on real CLI/function outcomes, git index state, lock contention, and file bytes.
- Commit path-scoped via `aw commit mmuv3v -- <paths>` inside an isolated worktree.

## Findings

Nine verified bugs from `/assess-bugs` run `20261124-213000`:
- High: `status_set._offer_self_commit` / `git_commit_helper.offer_commit` / `commit_lock.commit_isolated` fail on unversioned `~/.aw/`, custom companions, and mixed batches.
- High: `commit_lock.writer_lock` vs `ipd_lifecycle.acquire_finalize_lock` acquire distinct locks in companion mode.
- High: `status_set._delegate_plan_executed_to_finalize` / `ipd_lifecycle.finalize` skips `_resolve_staged_companion_lane_plan`.
- Medium: `status_set.run_set_command` orchestrator dirty-tree check fails open in companion mode.
- Medium: `status_set.apply_status_change` passes absolute external paths to `post_relocation_citation_rewrite`.
- Medium: `ipd_lifecycle._run_record_committed_paths` misses companion/`tracked`+`home` `records/runs/`.
- Medium: `artifact_meta.write_legacy` short-circuits on `record_git_root` before `repo_root_of`; `_git_target_root` and `_prepare_status_change` ignore `repo_root`; `load_legacy_artifact` passes wrong root to `global_id6s`.
- Medium: `ipd_lifecycle._finalize_transaction` passes `coord.path` as `repo_root` and reads target commit identity.
- Medium: `selectors.resolve` / `status_set.match_selector` fail on records-relative paths; `_prepare_status_change` passes absolute path as `rel` to `read_at`/`read_path_at`.

## Proposed changes (ordered, validatable)

1. Partition and guard self-commits (`E-01`).
2. Align companion finalize lock, staged-lane delegation, worktree context, and runs attribution (`E-02`).
3. Fix `status_set` dirty-tree guard, `--rewrite-citations`, and custom-companion staleness (`E-03`).
4. Fix `selectors` records-relative matching and `artifact_meta` owner/git/collision roots (`E-04`).
5. Add behavioral tests and validate (`E-05`).

## Deferred / out of scope (with reason)

- CLI archive/rename `_offer_*_commit` helpers are fixed alongside `aw rename`/`aw archive` in Order 04 (`7eivm2`).
  - Carrier: 7eivm2

## Scope check

- Over-scope: none.
- Under-scope: none; covers all metadata, selector, locking, and finalize bugs from `/assess-bugs`.

## Required tests / validation

- `python3 -m pytest tests/test_companion_ipd_lifecycle.py tests/test_home_isolation.py tests/test_companion_record_owner_root.py`
- `python3 -m mypy agent_workflows/status_set.py agent_workflows/git_commit_helper.py agent_workflows/commit_lock.py agent_workflows/ipd_lifecycle.py agent_workflows/selectors.py agent_workflows/artifact_meta.py`
- `aw sanitize`

## Spec / documentation sync

N/A: restores documented selector, setter, locking, and finalize guarantees across external backends.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste pytest output proving `aw set --commit`/`--yes` skips git cleanly on unversioned `~/.aw/`, commits custom non-sibling companions via `--dir`, handles mixed batches, and refuses out-of-repo paths cleanly in `offer_commit`/`commit_isolated`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_companion_ipd_lifecycle.py` output proving `commit_lock.writer_lock` vs `ipd_lifecycle.finalize` mutual exclusion, `_delegate_plan_executed_to_finalize` calling `_resolve_staged_companion_lane_plan`, `_finalize_transaction` honoring target allowlist and companion `agent_commit_identity`, and `_run_record_committed_paths` exact `run-record-exact` attribution.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_companion_ipd_lifecycle.py` output proving `status_set.run_set_command` refuses dirty companion orchestrators, `apply_status_change` rewrites `Scope-Paths` via `--rewrite-citations`, and `_prepare_status_change` resolves custom-companion staleness and `rel` paths.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_companion_ipd_lifecycle.py tests/test_home_isolation.py` output proving `selectors.resolve` resolves `plans/pending/...` and `records/plans/pending/...` in companion/`~/.aw/` repos, and `artifact_meta.write_legacy`, `_git_target_root`, and `load_legacy_artifact` resolve the owning repo and id6 collision set.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste full pytest summary for `test_companion_ipd_lifecycle.py`, `test_home_isolation.py`, and `test_companion_record_owner_root.py`, `mypy` zero-error output on `status_set.py`, `git_commit_helper.py`, `commit_lock.py`, `ipd_lifecycle.py`, `selectors.py`, and `artifact_meta.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute after human approval (`Status: approved`) and after `executed:ywl7uc`. Commit only path-scoped files via `aw commit mmuv3v -- <paths>`; never push.
