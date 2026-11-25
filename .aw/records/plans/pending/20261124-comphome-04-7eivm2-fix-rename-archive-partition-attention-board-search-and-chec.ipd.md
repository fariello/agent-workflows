# IPD: Fix rename archive partition attention board search and check_engine external-record bugs

- Date: 2026-11-24
- Kind: child
- Concern: Nine verified CLI, attention-board, and `check_engine` bugs crash or emit false errors whenever records live in a companion repo or `~/.aw/` (`AW_HOME`): (1) `aw rename`, `aw group`, `aw research mv`, and `aw research set-assign` crash with `ValueError` on unguarded `relative_to(repo_root)`; (2) `aw archive plans` and `aw archive research` crash with `ValueError` (and `research_archive.apply_archive` mutates status on disk before crashing); (3) `_offer_records_commit` and `_offer_archive_commit` run git against `target_repo` instead of `record_git_root`; (4) `aw partition` fails on every explicit selector and silently breaks `classify_sets`, `expand_candidates_with_dependencies`, and `_is_orchestrator_plan`; (5) `aw ipd board` (human mode) crashes with `ValueError` and `aw search --short`/`-s` misses `item_map`; (6) `attention.scan` passes `repo_root` instead of `records_root / "research"` to `companion_owner_stem`, invalidating the board (`valid: false`) on `.data/` files, and joins `repo_root / it.path` in staleness, `-o mtime|ctime`, `filter_items_by_selectors`, and warning filters; (7) `plan_readiness.review_staleness_index` and `_resolve_recheck_review_binding` fail on external companion/`~/.aw/` paths; (8) `check_engine.stale_record_scope_paths`, `resolve_gate_ref`, and `graduated_closable_warnings` fail on logical `.aw/records/...` paths; and (9) `artifact_refs.filter_in_flight_plan_edits` and `_is_pending_plan_file` bypass in-flight receipt protection and disable `Scope-Paths` citation rewriting (plus `ipd_authoring._run_bulk_id_backfill` preferring stale local `.aw/records/plans`).
- Scope: Fix all nine bugs across `artifact_rename.py`, `research_refs.py`, `plans_archive.py`, `research_archive.py`, `partition.py`, `attention.py`, `plan_readiness.py`, `check_engine.py`, `artifact_refs.py`, `ipd_authoring.py`, and `cli.py`, with behavioral tests covering companion and `~/.aw/` modes.
- Scope-Paths: agent_workflows/artifact_rename.py, agent_workflows/research_refs.py, agent_workflows/plans_archive.py, agent_workflows/research_archive.py, agent_workflows/partition.py, agent_workflows/attention.py, agent_workflows/plan_readiness.py, agent_workflows/check_engine.py, agent_workflows/artifact_refs.py, agent_workflows/ipd_authoring.py, agent_workflows/cli.py, tests/test_companion_doctor_and_carriers.py, tests/test_research_companion.py, .aw/records/plans/pending/20261124-comphome-04-7eivm2-fix-rename-archive-partition-attention-board-search-and-chec.ipd.md
- Item-Dependencies: executed:ywl7uc
- Status: to-review
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: comphome
- Order: 4
- Highest E allocated: 6
- Id: 7eivm2
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 04 child IPD for `/assess-bugs` (Set `comphome`).

## Goal

Eliminate every `relative_to(repo_root)` crash, logical-vs-physical path mismatch, false-positive check error, and broken self-commit across CLI record verbs, `aw attention`, `aw partition`, `plan_readiness`, `artifact_refs`, and `check_engine` in companion and `~/.aw/` repositories.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: `aw rename`, `aw group`, `aw archive`, `aw ipd board`, and `aw search`

- [ ] E-01 Fix external-record path rendering and moves in `artifact_rename.py`, `research_refs.py`, `plans_archive.py`, and `research_archive.py`: replace unguarded `relative_to(repo_root)` calls with `artifact_core.repo_relative_posix` for display and full/`record_git_root`-relative paths for `_core.git_mv`, and ensure `research_archive.apply_archive` verifies move paths before mutating status on disk.
  - Depends on: none
  - Expected outcome: `aw rename`, `aw group`, `aw research mv`/`set-assign`, and `aw archive plans`/`research` succeed cleanly on companion and `~/.aw/` repos without `ValueError` or partial mutation.
  - Execution state: pending

- [ ] E-02 Fix CLI self-commits, human-mode `aw ipd board`, and `aw search` in `cli.py`, `plans_archive.py`, and `research_archive.py`: partition touched paths by enclosing git root in `_offer_records_commit` and `_offer_archive_commit` (skipping unversioned `~/.aw/` records); fix human-mode `aw ipd board` (`cli._run_plans`) `relative_to(repo_root)` crash and `aw search --short`/`-s` `item_map` physical-path lookup (`cli._run_search`).
  - Depends on: E-01
  - Expected outcome: self-commits commit against `record_git_root` in companion repos and skip cleanly on unversioned `~/.aw/`; `aw ipd board` and `aw search --short` render external records cleanly.
  - Execution state: pending

### Task group 2: `aw partition` and `aw attention` + `plan_readiness`

- [ ] E-03 Fix logical-to-physical external record path mapping in `partition.py`, `attention.py`, and `plan_readiness.py`: resolve logical `.aw/records/...` `Item.path` through `project_records_dir(repo_root)` in `partition.py` (`collect`, `classify_sets`, `expand_candidates_with_dependencies`, `_is_orchestrator_plan`) and `attention.py` (`scan`, `_order_primary` mtime/ctime, `filter_items_by_selectors`, `_filter_drift_by_selection`, `run_attention` warning filters); pass `records_root / "research"` to `_rc.companion_owner_stem` in `attention.scan`; run `plan_readiness.review_staleness_index` against `record_git_root` and allow external `project_records_dir(repo_root) / "reviews"` in `_resolve_recheck_review_binding`.
  - Depends on: none
  - Expected outcome: `aw partition <selector>`, `aw attention --check` (with research `.data/` files), `aw attention -o mtime`, `aw attention <selector>`, and `aw ipd recheck` all work identically in companion and `~/.aw/` repos as in repository mode.
  - Execution state: pending

### Task group 3: `check_engine` logical-path rules, `artifact_refs`, and `ipd_authoring`

- [ ] E-04 Fix logical `.aw/records/...` resolution in `check_engine.py`, `artifact_refs.py`, and `ipd_authoring.py`: resolve `.aw/records/<rest>` through `project_records_dir(repo_root)` and normalize `hit_rels` back to logical `.aw/records/...` in `check_engine.stale_record_scope_paths` and `resolve_gate_ref`; emit logical `.aw/records/...` `--evidence` paths in `check_engine.graduated_closable_warnings`; recognize external pending plans in `artifact_refs.filter_in_flight_plan_edits` and `_is_pending_plan_file`; check `has_stored_records_placement(repo_root)` before target `.aw/records/plans` in `ipd_authoring._run_bulk_id_backfill`.
  - Depends on: none
  - Expected outcome: `check.scope-path-target-stale` and `check.gate-ref-dangling` stop emitting false positives on valid `.aw/records/...` references; `graduated_closable_warnings` produces valid `--evidence` commands; in-flight begin-receipt protection and `Scope-Paths` citation rewriting work on external plans.
  - Execution state: pending

### Task group 4: Behavioral verification

- [ ] E-05 Add behavioral tests covering rename, group, archive, partition, board, search, attention `.data/` + mtime + selectors, `plan_readiness`, `stale_record_scope_paths`, `resolve_gate_ref`, and `artifact_refs` under both companion and `~/.aw/` backends in `tests/test_companion_doctor_and_carriers.py` and `tests/test_research_companion.py`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: every new regression test fails without the fix and passes with it using real CLI/function calls (no source-reading assertions).
  - Execution state: pending

- [ ] E-06 Run targeted `python3 -m pytest`, `mypy` on all 11 modified modules, and `aw sanitize`.
  - Depends on: E-05
  - Expected outcome: all pytest cases pass, `mypy` reports zero errors on modified modules, and `aw sanitize` reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run pytest bare (`python3 -m pytest <targets>`); no code-pinning assertions.
- Commit path-scoped via `aw commit 7eivm2 -- <paths>` inside an isolated worktree.

## Findings

Nine verified bug clusters from `/assess-bugs` run `20261124-213000`:
- Blocker: `aw rename` / `aw group` / `aw research mv|set-assign` crash with `ValueError`.
- Blocker: `aw archive plans` and `aw archive research` crash with `ValueError` (research archive partially mutates first).
- Blocker: `aw partition` rejects every explicit selector and skips Set classification, dependency expansion, and orchestrator guard.
- Blocker: false-positive `check.scope-path-target-stale` on every pending plan declaring `.aw/records/...` in `Scope-Paths`.
- High: `aw ipd board` human mode crashes; `aw search --short` misses `item_map`; `_offer_records_commit` / `_offer_archive_commit` target `repo_root`.
- High: false-positive `check.gate-ref-dangling` on logical `.aw/records/...` `Gate-Ref`.
- High: `artifact_refs` bypasses in-flight receipt guard and disables `Scope-Paths` citation rewriting.
- High: `attention.scan` marks research `.data/` files as invalid records (`valid: false`), and `repo_root / it.path` breaks staleness, `-o mtime|ctime`, selectors, and warning filters (`graduated_closable_warnings` emits rejected absolute `--evidence`).
- Medium: `plan_readiness._resolve_recheck_review_binding` skips external review records; `ipd_authoring._run_bulk_id_backfill` checks target `.aw/records/plans` before stored placement.

## Proposed changes (ordered, validatable)

1. Fix external-record path rendering and moves in `artifact_rename`, `research_refs`, `plans_archive`, and `research_archive` (`E-01`).
2. Fix CLI self-commits, human-mode `aw ipd board`, and `aw search --short` (`E-02`).
3. Fix `partition`, `attention`, and `plan_readiness` external path mapping (`E-03`).
4. Fix `check_engine` logical-path rules, `artifact_refs`, and `ipd_authoring` (`E-04`).
5. Add behavioral tests (`E-05`) and validate (`E-06`).

## Deferred / out of scope (with reason)

- Staged git-diff checks (`check_status_untooled`, `check_staged_illegal_backlog_transition`, `_staged_backlog_done_items`, `_lane_carrier_is_executed`) are owned by Order 05 (`7hfx7r`) together with the pre-commit hooks that invoke them.
  - Carrier: 7hfx7r

## Scope check

- Over-scope: none.
- Under-scope: none; all CLI, attention, partition, and non-staged check_engine findings from `/assess-bugs` are covered.

## Required tests / validation

- `python3 -m pytest tests/test_companion_doctor_and_carriers.py tests/test_research_companion.py`
- `python3 -m mypy agent_workflows/artifact_rename.py agent_workflows/research_refs.py agent_workflows/plans_archive.py agent_workflows/research_archive.py agent_workflows/partition.py agent_workflows/attention.py agent_workflows/plan_readiness.py agent_workflows/check_engine.py agent_workflows/artifact_refs.py agent_workflows/ipd_authoring.py agent_workflows/cli.py`
- `aw sanitize`

## Spec / documentation sync

N/A: restores documented CLI, attention, and check_engine behavior on external backends.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste pytest output proving `artifact_rename`, `research_refs`, `plans_archive`, and `research_archive` succeed on companion and `~/.aw/` repos with zero `ValueError` crashes and no partial mutation.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste pytest output proving `cli._offer_records_commit`, `plans_archive._offer_archive_commit`, `research_archive._offer_archive_commit`, `cli._run_plans` (`aw ipd board`), and `cli._run_search` (`aw search --short`) work cleanly on companion and `~/.aw/` repos.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste pytest output proving `partition.collect`/`classify_sets`/`expand_candidates_with_dependencies`, `attention.scan` (with `.data/` files), `attention._order_primary` (`-o mtime`), `filter_items_by_selectors`, and `plan_readiness.review_staleness_index`/`_resolve_recheck_review_binding` pass on companion and `~/.aw/` repos.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste pytest output proving `check_engine.stale_record_scope_paths`, `check_engine.resolve_gate_ref`, `check_engine.graduated_closable_warnings`, `artifact_refs.filter_in_flight_plan_edits`/`_is_pending_plan_file`, and `ipd_authoring._run_bulk_id_backfill` pass on companion and `~/.aw/` repos.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste pytest output for the new regression tests in `tests/test_companion_doctor_and_carriers.py` and `tests/test_research_companion.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste full pytest summary for `test_companion_doctor_and_carriers.py` and `test_research_companion.py`, `mypy` zero-error output on `artifact_rename.py`, `research_refs.py`, `plans_archive.py`, `research_archive.py`, `partition.py`, `attention.py`, `plan_readiness.py`, `check_engine.py`, `artifact_refs.py`, `ipd_authoring.py`, and `cli.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: All 11 modules share one root defect (joining `repo_root / logical_path` or calling unguarded `path.relative_to(repo_root)` on external companion/`AW_HOME` records) and reuse the same logical-to-physical path resolution helpers; keeping them in one child plan prevents partial cross-module inconsistencies across `attention`, `partition`, `check_engine`, and CLI record verbs.

Execute after human approval (`Status: approved`) and after `executed:ywl7uc`. Commit only path-scoped files via `aw commit 7eivm2 -- <paths>`; never push.
