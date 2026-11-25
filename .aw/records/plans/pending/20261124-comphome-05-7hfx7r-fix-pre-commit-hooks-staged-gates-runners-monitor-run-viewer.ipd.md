# IPD: Fix pre-commit hooks staged gates runners monitor run viewer checkup and clean-delta inbox

- Date: 2026-11-24
- Kind: child
- Concern: Eight verified bugs break pre-commit hooks, staged `check_engine` governance rules, run monitoring/viewing, checkup, and `clean-delta` inbox adoption in companion and `~/.aw/` repos: (1) `hooks/executed_transition_gate.py` hardcodes `.aw/records/plans/` (failing open on companion `records/plans/`), misses companion `records/meta/*.jsonl`, and looks for finalize journals in the companion repo instead of the owning target repo; (2) `hooks/meta_log_append_gate.py` and `check_engine._git_read_at_context` miss companion `records/meta/*.jsonl`; (3) `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_staged_backlog_done_items`, and `_lane_carrier_is_executed` run against `target_repo` with hardcoded `.aw/records/...` pathspecs, failing open in companion repos; (4) `hooks/ipd_dependency_statement_gate.py` falsely rejects every valid companion dependency as `dangling` because it passes `companion_dir` instead of `record_owner_root(companion_dir)` to `evaluate_ipd_dependencies`; (5) `runners_monitor.find_active_runners` hardcodes `.aw/records/runs` and reports zero active runners; (6) `run_viewer.discover_runs_in_directory` misses companion `records/runs` and external `state_root(p)`, and `_find_stem_for_id6` hardcodes `.aw/records/plans`; (7) `checkup.run_start_checkup` (when `run_dir` is omitted) and `set_records.run_artifacts_dir` hardcode target `.aw/` paths; and (8) `artifact_adopt` and `attention.inbox_waiting` hardcode `<repo_root>/.aw/inbox`, conflicting with `clean-delta`'s zero-footprint contract.
- Scope: Fix all eight bugs across `hooks/executed_transition_gate.py`, `hooks/meta_log_append_gate.py`, `hooks/ipd_dependency_statement_gate.py`, `check_engine.py`, `runners_monitor.py`, `run_viewer.py`, `checkup.py`, `artifact_adopt.py`, `attention.py`, and `set_records.py`, with behavioral tests covering companion and `~/.aw/` repos.
- Scope-Paths: agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/meta_log_append_gate.py, agent_workflows/hooks/ipd_dependency_statement_gate.py, agent_workflows/check_engine.py, agent_workflows/runners_monitor.py, agent_workflows/run_viewer.py, agent_workflows/checkup.py, agent_workflows/artifact_adopt.py, agent_workflows/attention.py, agent_workflows/set_records.py, tests/test_companion_doctor_and_carriers.py, tests/test_home_isolation.py, .aw/records/plans/pending/20261124-comphome-05-7hfx7r-fix-pre-commit-hooks-staged-gates-runners-monitor-run-viewer.ipd.md
- Item-Dependencies: executed:ywl7uc
- Status: to-review
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: comphome
- Order: 5
- Highest E allocated: 6
- Id: 7hfx7r
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 05 child IPD for `/assess-bugs` (Set `comphome`).

## Goal

Restore fail-closed pre-commit and staged governance hooks inside companion repos, make `aw runners` and `aw runs` discover companion and `~/.aw/` runs accurately, and eliminate remaining hardcoded `.aw/` writes in `checkup`, `set_records`, and `clean-delta` inbox adoption.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Companion pre-commit hooks and `_git_read_at_context`

- [ ] E-01 Fix `check_engine._git_read_at_context`, `hooks/executed_transition_gate.py`, `hooks/meta_log_append_gate.py`, and `hooks/ipd_dependency_statement_gate.py`: teach `_git_read_at_context` to detect a companion repo's `records/` layout (via `companion_identity.json` / `record_owner_root`) so `rel_records` resolves to `"records"` and `meta_dir` resolves to `"records/meta"`; update `executed_transition_gate.py` to detect both `.aw/records/plans/` and companion `records/plans/` and read finalize journals from `record_owner_root(root) or root`; update `ipd_dependency_statement_gate.py` to pass `record_owner_root(root) or root` into `evaluate_ipd_dependencies`.
  - Depends on: none
  - Expected outcome: companion pre-commit hooks catch raw `executed` transitions and non-append `records/meta/*.jsonl` edits, accept legitimate `aw ipd finalize` commits using the target repo's finalize journal, and accept valid cross-IPD dependencies inside companion repos.
  - Execution state: pending

### Task group 2: Staged and range governance rules in `check_engine.py`

- [ ] E-02 Route `check_engine.check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_staged_backlog_done_items`, and `_lane_carrier_is_executed` through the resolved records git root (`record_git_root(records_root)`) and records-relative prefix (`records/...` or `.aw/records/...`) instead of hardcoding `target_repo` and `.aw/records/...`.
  - Depends on: E-01
  - Expected outcome: staging an untooled plan status flip, illegal backlog transition, or ungated backlog close in a companion repo is caught by `aw check` and pre-commit gates, and `_lane_carrier_is_executed` resolves companion carriers cleanly.
  - Execution state: pending

### Task group 3: `runners_monitor`, `run_viewer`, `checkup`, `set_records`, and `clean-delta` inbox

- [ ] E-03 Fix run discovery and monitoring in `runners_monitor.py` and `run_viewer.py`: resolve `runs_dir` via `runner_shared.state_root(runner_shared.runs_repo_root(repo))` in `runners_monitor.find_active_runners`; probe `p / "records" / "runs"` and `runner_shared.state_root(p)` in `run_viewer.discover_runs_in_directory` and use `project_records_dir(repo_root) / "plans"` in `run_viewer._find_stem_for_id6`.
  - Depends on: none
  - Expected outcome: `aw runners` reports active runners on companion and `~/.aw/` repos, and `aw runs` discovers runs and resolves plan stems accurately in companion and `~/.aw/` layouts.
  - Execution state: pending

- [ ] E-04 Fix runtime-artifact and inbox directory placement in `checkup.py`, `set_records.py`, `artifact_adopt.py`, and `attention.py`: resolve `runs_dir` via `runner_shared.state_root` in `checkup.run_start_checkup`; route `set_records.run_artifacts_dir` away from target `.aw/` under `clean-delta`; resolve the inbox directory in `artifact_adopt.py` and `attention.inbox_waiting` through `project_context` (`<AW_HOME>/projects/<pid>/inbox` when `delivery_mode == "clean-delta"`, preserving `.aw/inbox` for tracked repos) while maintaining strict single-directory containment.
  - Depends on: none
  - Expected outcome: `checkup`, `set_records`, `aw adopt`, and `attention.inbox_waiting` work cleanly in `clean-delta` repos with zero target-repo footprint while still refusing paths outside the configured inbox directory.
  - Execution state: pending

### Task group 4: Behavioral verification

- [ ] E-05 Add behavioral tests for companion hooks, staged `check_engine` rules, `runners_monitor`, `run_viewer`, `checkup`, `set_records`, and `clean-delta` `aw adopt` in `tests/test_companion_doctor_and_carriers.py` and `tests/test_home_isolation.py`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: every new regression test fails without the fix and passes with it using real temporary git/companion/`clean-delta` repos.
  - Execution state: pending

- [ ] E-06 Run targeted `python3 -m pytest`, `mypy` on all 10 modified modules, and `aw sanitize`.
  - Depends on: E-05
  - Expected outcome: all targeted pytest suites pass, `mypy` reports zero errors on modified files, and `aw sanitize` reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Never write code-pinning tests; run real hook functions against real temporary git/companion repos and assert exit codes and refusal rules.
- Commit path-scoped via `aw commit 7hfx7r -- <paths>` inside an isolated worktree.

## Findings

Eight verified bugs from `/assess-bugs` run `20261124-213000`:
- High: `hooks/executed_transition_gate.py` misses companion `records/plans/` and `records/meta/*.jsonl`, and looks for finalize journals in companion instead of target repo.
- High: `hooks/meta_log_append_gate.py` and `check_engine._git_read_at_context` miss companion `records/meta/*.jsonl`.
- High: `status_untooled_gate`, `backlog_blocking_close_gate`, `precommit_scope_gate`, and staged `check_engine` checks fail open on companion repos.
- High: `hooks/ipd_dependency_statement_gate.py` falsely rejects every valid companion dependency as `dangling`.
- High: `runners_monitor.find_active_runners` hardcodes `.aw/records/runs` and reports zero active runners.
- Medium: `run_viewer.discover_runs_in_directory` and `_find_stem_for_id6` miss companion/`~/.aw/` layouts.
- Medium: `artifact_adopt` and `attention.inbox_waiting` hardcode `<repo_root>/.aw/inbox`, violating `clean-delta` zero-footprint.
- Low: `checkup.run_start_checkup` fallback and `set_records.run_artifacts_dir` hardcode target `.aw/` paths.

## Proposed changes (ordered, validatable)

1. Make companion pre-commit hooks and `_git_read_at_context` companion-aware (`E-01`).
2. Route staged/range `check_engine` checks through `record_git_root` and records-relative prefixes (`E-02`).
3. Fix `runners_monitor` and `run_viewer` companion and `~/.aw/` run discovery (`E-03`).
4. Fix `checkup`, `set_records`, `artifact_adopt`, and `attention.inbox_waiting` for `clean-delta` (`E-04`).
5. Add behavioral tests (`E-05`) and validate (`E-06`).

## Deferred / out of scope (with reason)

- Runner-side untooled `executed/` move gate bypass in isolated lanes is owned by Order 06 (`4vnd36`), which depends on `7hfx7r`.
  - Carrier: 4vnd36

## Scope check

- Over-scope: none.
- Under-scope: none; all hook, monitoring, viewer, checkup, and inbox bugs from `/assess-bugs` are covered.

## Required tests / validation

- `python3 -m pytest tests/test_companion_doctor_and_carriers.py tests/test_home_isolation.py`
- `python3 -m mypy agent_workflows/hooks/executed_transition_gate.py agent_workflows/hooks/meta_log_append_gate.py agent_workflows/hooks/ipd_dependency_statement_gate.py agent_workflows/check_engine.py agent_workflows/runners_monitor.py agent_workflows/run_viewer.py agent_workflows/checkup.py agent_workflows/artifact_adopt.py agent_workflows/attention.py agent_workflows/set_records.py`
- `aw sanitize`

## Spec / documentation sync

N/A: aligns hooks, monitors, and clean-delta inbox with existing documented containment contracts.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste pytest output proving `hooks/executed_transition_gate.py`, `hooks/meta_log_append_gate.py`, `hooks/ipd_dependency_statement_gate.py`, and `check_engine._git_read_at_context` reject raw transitions/log rewrites and accept valid companion finalize commits and dependencies.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste pytest output proving `check_engine.check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_staged_backlog_done_items`, and `_lane_carrier_is_executed` detect staged violations in companion repos.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste pytest output proving `runners_monitor.find_active_runners`, `run_viewer.discover_runs_in_directory`, and `run_viewer._find_stem_for_id6` discover companion and `~/.aw/` runs and resolve external plan stems cleanly.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste pytest output proving `checkup.run_start_checkup`, `set_records.run_artifacts_dir`, `artifact_adopt`, and `attention.inbox_waiting` use external `AW_HOME` paths in `clean-delta` mode without touching target `.aw/`, while rejecting outside inbox paths.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste pytest output for the new regression tests in `tests/test_companion_doctor_and_carriers.py` and `tests/test_home_isolation.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste full pytest summary for `test_companion_doctor_and_carriers.py` and `test_home_isolation.py`, `mypy` zero-error output on `executed_transition_gate.py`, `meta_log_append_gate.py`, `ipd_dependency_statement_gate.py`, `check_engine.py`, `runners_monitor.py`, `run_viewer.py`, `checkup.py`, `artifact_adopt.py`, `attention.py`, and `set_records.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: The pre-commit hooks directly invoke `check_engine`'s staged rules (`_git_read_at_context`, `check_status_untooled`, `_staged_backlog_done_items`), and the remaining four modules (`runners_monitor`, `run_viewer`, `checkup`, `artifact_adopt`) share the same companion/`clean-delta` runtime-directory resolution fix.

Execute after human approval (`Status: approved`) and after `executed:ywl7uc`. Commit only path-scoped files via `aw commit 7hfx7r -- <paths>`; never push.
