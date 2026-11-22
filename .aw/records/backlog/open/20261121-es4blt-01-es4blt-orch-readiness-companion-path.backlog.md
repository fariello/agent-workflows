- Id: es4blt
- Status: open
- Set: es4blt
- Work-Kind: bug
- Priority: high
- Summary: handle_review_orchestrator_readiness reads unintegrated companion plan before worktree copy
- Short-Description: handle_review_orchestrator_readiness reads unintegrated companion plan before worktree copy
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): handle_review_orchestrator_readiness reads unintegrated companion plan before worktree copy

## Symptom

In a repository configured with companion records storage (`public-target-private-companion`), reviewing an Order-0 orchestrator plan via `aw agy run reviews` (or `aw oc run`) ends in `fail-gate` (`IPD-REVIEW-ORCHESTRATOR-READY`: `Orchestrator <id6> is ready but status remains to-review (transition not executed)`) after exhausting the correction budget. This happens even when the review agent updated the isolated worktree copy to `Status: reviewed`, `Readiness: go-pending-approval`, and `Review-Depth: orchestrator`, and the worktree copy passes `aw ipd lint --phase review-finalize`.

## Root cause

In `agent_workflows/runner_shared.py::handle_review_orchestrator_readiness`, `plan_file` resolution tries `plan_path.relative_to(repo)`, which raises `ValueError` in companion storage because `plan_path` resides in the external companion repository rather than under `repo`. The fallback then executes `if plan_path.is_file(): plan_file = plan_path` **before** calling `queue_artifact_path(tree, item)`. Because the unintegrated companion-repo file exists on disk at `Status: to-review`, the gate inspects the stale companion copy on every attempt and correction turn instead of the edited worktree copy.

Note: `agent_workflows/cli.py::_run_plans` (`aw ipd board`) hits the same `relative_to(root)` assumption when `rec.path` resides in a companion records root.

## Expected fix

In `agent_workflows/runner_shared.py::handle_review_orchestrator_readiness`, resolve the worktree-local candidate via `queue_artifact_path(tree, item)` (and companion-relative `.aw/records/...` mapping into `tree`) **before** falling back to `plan_path`.

## Acceptance criteria

1. When `plan_path` lies outside `repo` (companion records backend) and an updated plan exists at `queue_artifact_path(tree, item)`, `handle_review_orchestrator_readiness` evaluates the worktree copy rather than the unintegrated companion copy.
2. An orchestrator plan marked `Status: reviewed` with valid coverage inside a review lane completes `handle_review_orchestrator_readiness` with `refused=False` and `disposition="reviewed"` without spending correction turns.
3. A regression unit test reproduces a companion `plan_path` outside `repo` still at `Status: to-review` while the worktree copy is at `Status: reviewed`, and verifies the gate reads the worktree copy and succeeds.
