# Agent Workflows

Reusable, tool-agnostic agent workflows for this repository. Each workflow is a
capability with its own subdirectory here. To run one, read and execute its body
file (the path below), or use the matching slash command in a tool that supports them
(`/<command>`).

These workflows are invoked on demand; they are not always-loaded context. `AGENTS.md`
carries only a one-line pointer to this index, not the workflow contents.

## Workflows

The table below is the manifest. The installer reads it to generate per-tool command
shims. Keep the columns stable: `command | body | description`.

<!-- WORKFLOWS-MANIFEST:BEGIN -->
| command | body | description |
|---|---|---|
| release-review | .agents/workflows/release-review/README.md | Full pre-release repository review and hardening: deep audit through eight personas, the Fix Bar, fix/validate/report, push and release decisions. |
| release-review-plan | .agents/workflows/release-review/README.md | Release review in planning-only mode: audit and consolidated implementation plan, stopping before implementation. |
| plan-review | .agents/workflows/plan-review/plan-review.md | Pre-execution plan reviewer: review and improve a proposed implementation plan before any code is written (edits planning documents only). |
<!-- WORKFLOWS-MANIFEST:END -->

## Running a workflow

- **OpenCode / Claude Code (native):** type `/release-review`, `/release-review-plan`,
  or `/plan-review`. Pass an optional target or flags as arguments, e.g.
  `/plan-review .agents/plans/pending/my-feature.md`.
- **Any other agent (universal fallback):** tell it to "read and execute" the body
  path, e.g. "Read and execute .agents/workflows/release-review/README.md".

## Notes

- `release-review-plan` shares the `release-review` body; it runs that runbook in
  planning-only mode (see the runbook's planning-only instructions).
- `release-review/` also contains the shared policy (`fix-decision-policy.md`,
  `00-run-protocol.md`) that `plan-review` references as a sibling.
- The installer copies these workflows into a target repository, generates the
  per-tool command shims from this manifest, and adds a one-line pointer to
  `AGENTS.md`. See `release-review/install-workflows.py`.
