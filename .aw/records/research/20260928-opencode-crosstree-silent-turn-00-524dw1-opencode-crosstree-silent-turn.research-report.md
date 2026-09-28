---
id: 524dw1
created: 20260928
set: opencode-crosstree-silent-turn
order: 00
topic: [opencode, sessions]
model:
kind: research-report
status: reference
outcome: informational
summary: Upstream defect report: opencode run cross-tree session produces silent exit-0
consumed-by: [r0iob3]
priority: medium
---

# Upstream Defect Report: opencode run cross-tree session produces silent exit-0

- Status: NOT FILED UPSTREAM (created as durable artifact in execution environment; awaiting maintainer submission)
- Component: opencode CLI / core runner
- Measured Versions: 1.18.30 (initial report), 1.18.32 (IPD authoring), 1.18.33 (lane execution)
- Severity: High (silent exit 0 creates false-positive success signal)

## Summary

When `opencode run --session <session-id> --dir <worktree-path>` is invoked where `<session-id>` was originally bound to a different directory (such as a parent git repository or a different git worktree), the command immediately exits with exit code 0 having produced ZERO output:
- No stdout / JSON event stream
- No stderr messages or diagnostic logs
- No tool execution
- No modification of files

## Contract Violation

Exit 0 is an affirmative claim of success in UNIX conventions and CLI tool design.
A caller running an automated agent turn cannot distinguish "the turn completed successfully with nothing to say" from "the turn never executed". In an automated driver or CI environment, this silent exit 0 leads callers to falsely conclude that the task completed or passed review.

The expected contract for cross-tree session reuse is:
1. Either: cleanly rebind the existing session to the new directory (if supported);
2. Or: fail loudly with a non-zero exit code and an explicit error message naming both directories (e.g., `Error: session <id> is bound to /path/A, cannot run in /path/B`).

Silence with exit 0 is the one failure mode that no automated caller can handle safely.

## Candidate Causes

Root cause diagnosis was constrained by sandboxed execution environments, but two primary candidate causes have been identified:

### Candidate 1: Swallowed Refusal
The session manager or runtime detects that `session.directory != args.dir` (or that the session's workspace scope does not match), aborts or skips execution, but fails to set a non-zero exit code or surface the refusal message to stdout/stderr. The process completes its event loop with no items processed and exits 0.

### Candidate 2: No-op Delivery / Directory Mismatch Delivery
The prompt is accepted and dispatched to a session context whose internal cwd or listener binding does not match the active invocation, causing the turn to be dropped or delivered into a non-observable scope without generating events on the current stream.

## Store Schema Observations (opencode.db)

Analysis of opencode's SQLite store schema (`opencode.db`) provides relevant context:
- The `session` table records both `project_id` and `directory`.
- The `project` table records `worktree`.
- The `project_directory` table records distinct directory mappings for the same project (`type='git_worktree'`).
- A git worktree and its main checkout share a single `project_id` while having distinct `directory` paths in `project_directory`.

This demonstrates that opencode recognizes multiple worktrees under the same project identity, making the directory mismatch a common multi-worktree workflow occurrence rather than an esoteric edge case.

## Local Workaround in agent-workflows

In this repository, plan `r0iob3` introduces two independent defenses:
1. **Refusal of cross-tree carry**: The runner detects when an operator `--session` or previous lane session would be carried into an isolated worktree, logs a `cross-tree-session-refused` refusal naming both directories, and falls back to a fresh session.
2. **Silent turn detector**: `turn_attempted_nothing` verifies attempt artifacts (outcome files, git commits, dirty files, and event logs) and marks zero-output turns as `turn-silent-refused` (`fail-gate` / `fail-verify`), preventing silent turns from being recorded as completed or advancing review lifecycles.
