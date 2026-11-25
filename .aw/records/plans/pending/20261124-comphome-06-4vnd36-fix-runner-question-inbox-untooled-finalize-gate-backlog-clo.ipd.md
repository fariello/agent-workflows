# IPD: Fix runner question inbox untooled finalize gate backlog close companion review and AW_HOME lanes

- Date: 2026-11-24
- Kind: child
- Concern: Nine verified runner and lane-containment bugs break companion and `~/.aw/` (`home`) execution, review, and answer handling: (1) `runner_shared.consume_answers` fails to commit and rolls back every human preflight answer on companion and unversioned `~/.aw/` artifacts (and `question_inbox.write_question` / `consume_answers` parent-walk falls back to `<companion>` or `$HOME` instead of `record_owner_root`); (2) `check_status_untooled_range` + `finalize_outcome` / `ipd_lifecycle.plan_already_finalized` allow an untooled hand move into `executed/` to pass as exit 0 in companion and `~/.aw/` modes; (3) `process_backlog_close` fails in both modes (`lane_executed_carrier_override` misses staged `executed/` plans, and `commit_backlog_close` returns `None` for external records); (4) `read_zero_work_evidence` crashes with `TypeError: 'bool' object is not iterable` or overwrites `bool` `dirty` with `list[str]` in companion mode; (5) `review_findings.review_dirs` / `_cached_subject_review_files` ignore staged companion lane reviews, refusing `aw specs set reviewed`; (6) `handle_review_orchestrator_readiness`, `_promote_reviewed_plan`, `rereview` demote, `perform_carrier_verification`, `reconcile_disposition` retirement detection, `commit_review_shared_output`, and `check_review_lane_artifacts` (`evaluate_durable_carrier` for newly introduced lane carriers) read or mutate live `<companion>/records/` instead of staged lane copies; (7) `integrate_lane_branch` hardcodes `repo / ".aw" / "records" / "runs"` for `spec-anchor-check-unknown`; (8) `lane_containment` does not register staged `.aw/records/**` in the lane manifest for un-upgraded companion repos lacking `/records/` in `.aw/.gitignore`; and (9) `~/.aw/` (`records_backend == "home"`) lacks lane staging, projection, routing, and the fail-closed target-repo `.aw/records/**` merge guard.
- Scope: Fix all nine runner, question-inbox, review-findings, and lane-containment bugs in `runner_shared.py`, `question_inbox.py`, `review_findings.py`, `lane_containment.py`, and `ipd_lifecycle.py`, with behavioral tests covering companion and `~/.aw/` (`home`) runners.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/question_inbox.py, agent_workflows/review_findings.py, agent_workflows/lane_containment.py, agent_workflows/ipd_lifecycle.py, tests/test_companion_runner_integration.py, tests/test_companion_ipd_lifecycle.py, tests/test_question_inbox.py, tests/test_home_isolation.py, .aw/records/plans/pending/20261124-comphome-06-4vnd36-fix-runner-question-inbox-untooled-finalize-gate-backlog-clo.ipd.md
- Item-Dependencies: executed:7hfx7r, executed:mmuv3v, executed:ywl7uc
- Status: to-review
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: comphome
- Order: 6
- Highest E allocated: 5
- Id: 4vnd36
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 06 child IPD for `/assess-bugs` (Set `comphome`).

## Goal

Close every runner gate bypass, answer-rollback bug, backlog-close failure, companion review/carrier blind spot, and `~/.aw/` (`home`) isolated-lane gap across both `oc_runipd` and `agy_runipd`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Question inbox preflight answers and untooled `executed/` move gate

- [ ] E-01 Fix `runner_shared.consume_answers` and `question_inbox.write_question` for companion and `~/.aw/` artifacts: fall back to `project_context.record_owner_root(run_dir)` instead of walking up to `<companion>` or `$HOME`; preserve external paths instead of clearing `rel_art_path`; commit companion edits inside `record_git_root(art_full)` with repo-relative paths and accept non-git durability for unversioned `~/.aw/` records without reverting the human's answer.
  - Depends on: none
  - Expected outcome: answering a preflight question on a companion or `~/.aw/` artifact persists durably and commits in the companion repo (or stays saved without rollback on unversioned `~/.aw/`) instead of reverting and marking the answer `stale`.
  - Execution state: pending

- [ ] E-02 Close the untooled `executed/` move gate bypass in `ipd_lifecycle.plan_already_finalized` and `runner_shared.execute_item_core` / `finalize_already_done`: refuse to classify a move into `executed/` as `already_finalized` while the plan's begin receipt is still unconsumed on disk, and inspect staged companion lane / external `home` moves in `execute_item_core` so a hand `mv pending/ executed/` never bypasses pre-transition lint, begin-receipt validation, and scope audit.
  - Depends on: none
  - Expected outcome: a worker moving a companion or `~/.aw/` plan by hand into `executed/` is refused with an untooled-transition finding instead of silently passing as exit 0.
  - Execution state: pending

### Task group 2: Backlog close, zero-work evidence, companion review/carrier helpers, and `review_findings`

- [ ] E-03 Fix companion and `~/.aw/` execution/review helpers in `runner_shared.py` and `review_findings.py`: resolve staged companion lane plans in `lane_executed_carrier_override`, route isolated companion backlog closes through the lane (or commit in `record_git_root`, treating unversioned `~/.aw/` as succeeded) in `commit_backlog_close` / `process_backlog_close`; preserve `bool` `lane["dirty"] = True` and store companion paths in `lane["companion_dirty_paths"]` in `read_zero_work_evidence`; include `companion_staged_records_root / "reviews"` in `review_findings.review_dirs` and `_cached_subject_review_files`; fix `handle_review_orchestrator_readiness`, `_promote_reviewed_plan`, `rereview` demote, `perform_carrier_verification`, `reconcile_disposition` retirement detection, `commit_review_shared_output`, `check_review_lane_artifacts` durable-carrier overlay, and `integrate_lane_branch` `state_root(repo)` fallback.
  - Depends on: E-01, E-02
  - Expected outcome: `process_backlog_close`, zero-work recovery, companion spec/plan/orchestrator reviews, carrier verification, retirement detection, and non-isolated companion reviews all operate on the proper tree without mutating live companion prematurely or crashing.
  - Execution state: pending

### Task group 3: External `home` (`~/.aw/`) lane staging, routing, merge guard, and teardown manifest

- [ ] E-04 Extend isolated-lane external-records staging, prompt projection, routing, and the fail-closed target-repo `.aw/records/**` merge guard in `lane_containment.py` and `runner_shared.py` to cover `records_backend == "home"` (`~/.aw/`, routing writes/deletes back to `<AW_HOME>/projects/<pid>/records` without git commit when unversioned), and record staged `.aw/records/**` paths in the lane's driver-written manifest so un-upgraded companion repos lacking `/records/` in `.aw/.gitignore` still tear down cleanly.
  - Depends on: E-03
  - Expected outcome: `aw oc run` and `aw agy run` on a `records_backend == "home"` repo satisfy R1 prompt purity, work under OpenCode's `external_directory=deny`, route edits cleanly back to `~/.aw/projects/<pid>/records`, and block `.aw/records/**` from ever landing on target `main`.
  - Execution state: pending

### Task group 4: Behavioral verification

- [ ] E-05 Add end-to-end behavioral tests in `tests/test_companion_runner_integration.py`, `tests/test_companion_ipd_lifecycle.py`, `tests/test_question_inbox.py`, and `tests/test_home_isolation.py` covering all nine fixes, then run `python3 -m pytest`, `mypy`, and `aw sanitize`.
  - Depends on: E-04
  - Expected outcome: all targeted pytest suites pass, `mypy` reports zero errors on modified modules, and `aw sanitize` reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run bare `python3 -m pytest <targets>`; test observable behavior only (no code-pinning assertions).
- Commit path-scoped via `aw commit 4vnd36 -- <paths>` inside an isolated worktree.

## Findings

Nine verified bugs from `/assess-bugs` run `20261124-213000`:
- Blocker: `consume_answers` reverts and marks `stale` every human preflight answer on companion and `~/.aw/` artifacts (and parent-walk falls back to `<companion>` / `$HOME`).
- Blocker: untooled `executed/` move gate bypassed in companion and `~/.aw/` modes (`finalize_outcome` converts refusal to exit 0).
- Blocker: `~/.aw/` (`records_backend == "home"`) has no lane staging, projection, routing, or `.aw/records/**` merge guard.
- High: `process_backlog_close` fails in both companion and `~/.aw/` modes (`lane_executed_carrier_override` + `commit_backlog_close`).
- High: `read_zero_work_evidence` raises `TypeError` on `list(True)` or breaks `isinstance(dirty, bool)`.
- High: `review_findings` ignores staged companion lane reviews, breaking `aw specs set reviewed`.
- High: `handle_review_orchestrator_readiness`, `_promote_reviewed_plan`, `rereview` demote, `perform_carrier_verification`, and `check_review_lane_artifacts` durable-carrier check read/mutate live companion instead of staged lane copies.
- Medium: `reconcile_disposition` misses companion in-lane retirement; `commit_review_shared_output` ignores companion repo; un-upgraded companion repos block teardown.
- Low: `integrate_lane_branch` hardcodes `repo / ".aw" / "records" / "runs"` for `spec-anchor-check-unknown`.

## Proposed changes (ordered, validatable)

1. Fix `consume_answers` and `question_inbox.write_question` (`E-01`).
2. Close untooled `executed/` move bypass (`E-02`).
3. Fix backlog close, zero-work evidence, `review_findings`, and companion review/carrier/retirement helpers (`E-03`).
4. Extend lane staging, routing, and merge guard to `records_backend == "home"` and register staged records for teardown (`E-04`).
5. Add behavioral tests and validate (`E-05`).

## Deferred / out of scope (with reason)

- Companion `action=plan` backlog/spec production, `ipd_authoring.run_scaffold`, `backlog_graduate_legitimacy`, `route_companion_lane_records --no-renames`, `resolve_companion_lane_path` non-resurrection, and `artifact_meta.legacy_context` state-root fixes already landed in commit `c8a130148`.

## Scope check

- Over-scope: none.
- Under-scope: none; covers every open runner, question-inbox, review, and lane-containment bug from `/assess-bugs`.

## Required tests / validation

- `python3 -m pytest tests/test_companion_runner_integration.py tests/test_companion_ipd_lifecycle.py tests/test_question_inbox.py tests/test_home_isolation.py`
- `python3 -m mypy agent_workflows/runner_shared.py agent_workflows/question_inbox.py agent_workflows/review_findings.py agent_workflows/lane_containment.py agent_workflows/ipd_lifecycle.py`
- `aw sanitize`

## Spec / documentation sync

N/A: enforces existing specs `7ckptx` (lane containment), `6kwd2e` (question inbox), and `25kzda` (runner gates) on companion and `~/.aw/` backends.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest tests/test_question_inbox.py` output proving preflight answers commit cleanly in companion git repos and persist without rollback on unversioned `~/.aw/` records, and `record_owner_root` fallback resolves the owning target repo.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste pytest output proving a hand move into `executed/` in a companion or `~/.aw/` lane is refused instead of treated as `already_finalized` exit 0.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_companion_runner_integration.py` output proving `runner_shared.process_backlog_close`, `read_zero_work_evidence` (with dirty target + companion files), `review_findings.review_dirs`/`_cached_subject_review_files`, `handle_review_orchestrator_readiness`, `_promote_reviewed_plan`, `perform_carrier_verification`, `reconcile_disposition`, `commit_review_shared_output`, and `integrate_lane_branch` pass on companion and `~/.aw/` repos.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_companion_runner_integration.py tests/test_home_isolation.py` output proving `lane_containment` and `runner_shared` project lane-local paths for `records_backend == "home"`, route edits back to `~/.aw/projects/<pid>/records`, refuse `.aw/records/**` merges into target `main`, and tear down cleanly on un-upgraded companion repos.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste full pytest summary for `test_companion_runner_integration.py`, `test_companion_ipd_lifecycle.py`, `test_question_inbox.py`, and `test_home_isolation.py`, `mypy` zero-error output on `runner_shared.py`, `question_inbox.py`, `review_findings.py`, `lane_containment.py`, and `ipd_lifecycle.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: The 5 runner/lane modules (`runner_shared.py`, `question_inbox.py`, `review_findings.py`, `lane_containment.py`, `ipd_lifecycle.py`) and 4 existing test suites share one lane-staging/routing/gate contract for companion and `home` runs; landing them together prevents half-wired lane isolation.

Execute after human approval (`Status: approved`) and after `executed:ywl7uc`, `executed:mmuv3v`, and `executed:7hfx7r`. Commit only path-scoped files via `aw commit 4vnd36 -- <paths>`; never push.
