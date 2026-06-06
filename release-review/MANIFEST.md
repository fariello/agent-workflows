# Release Review Runbook Manifest

This directory contains a modular, executable repository review runbook for use with OpenCode or another modern coding agent.

## How to use

From the repository root, tell the agent:

```text
Read and execute release-review/README.md
```

`README.md` is the controlling instruction. The agent should read `00-run-protocol.md`, then execute sections `01` through `08` in order.

## Files

| File | Purpose |
|---|---|
| `README.md` | Main orchestrator and single entry point for the full review. |
| `00-run-protocol.md` | Global operating protocol, safety rules, ID rules, artifacts, TodoWrite use, commit and push policy, and final reporting requirements. |
| `01-current-state.md` | Repository inventory, current-state assessment, public contract discovery, drift analysis, and early deprecation signals. |
| `02-quality-security-edge-cases.md` | Bugs, correctness, security, privacy, error handling, resource handling, reliability, and edge-case audit. |
| `03-tests-regression.md` | Test coverage, regression protection, fixtures, CI test behavior, and missing critical tests. |
| `04-docs-specs-examples.md` | Documentation, specification, examples, README, help text, and behavior-documentation alignment. |
| `05-feature-usability-maintainability.md` | Feature completeness, usability, developer experience, operator experience, maintainability, and stale-code impact. |
| `06-compatibility-packaging-release.md` | Compatibility, packaging, build, CI, deployment, versioning, changelog, migration, and release artifacts. |
| `07-implementation.md` | Consolidated implementation plan and safe, significant-value fixes. |
| `08-final-ship-review.md` | Final release readiness assessment, validation reconciliation, final report, push/no-push decision, and restart assessment. |
| `templates/execution-plan.md` | Template for the early run execution plan. |
| `templates/implementation-plan.md` | Template for the implementation plan created after audit sections and before fixes. |
| `templates/section-summary.md` | Generic template for per-section summaries saved under `repository-review/<RUN_ID>/section-summaries/`. |
| `templates/final-response.md` | Template for the saved final report and table-first final answer. |
| `templates/finding-register.csv` | CSV header template for durable finding tracking. |
| `templates/action-register.csv` | CSV header template for durable action tracking. |

## Expected run artifacts

The agent should create and maintain:

```text
repository-review/<RUN_ID>/
  00-run-metadata.md
  01-repository-inventory.md
  02-execution-plan.md
  03-findings-register.csv
  04-action-register.csv
  05-decisions.md
  06-commands.md
  07-commits.md
  08-checkpoints.md
  09-implementation-plan.md
  10-validation-results.md
  11-push-plan.md
  12-final-response.md
  deprecation-candidates.md
  ci-assessment.md
  section-summaries/
    01-current-state.md
    02-quality-security-edge-cases.md
    03-tests-regression.md
    04-docs-specs-examples.md
    05-feature-usability-maintainability.md
    06-compatibility-packaging-release.md
    07-implementation.md
    08-final-ship-review.md
```

`repository-review/` should be ignored by Git. The review artifacts are for local accountability and should not be committed unless the user explicitly asks.
