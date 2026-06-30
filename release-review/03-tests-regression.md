# 03 Tests and Regression Protection

## Purpose

Review the project's tests and identify gaps that create risk for bugs, regressions, unsupported future changes, or unsafe release behavior.

This section is an audit pass. Do not add or change tests yet. Test implementation happens in Section 7.

## Standing constraints for this section

- Preserve public behavior unless a change is clearly justified.
- Do not make speculative changes.
- Do not create broad refactors or formatting churn.
- Use run-specific unique IDs for every finding and action.
- Update the finding and action registers before leaving this section.
- Use TodoWrite if available, but treat `repository-review/<RUN_ID>/` as authoritative.
- Mark non-applicable checks explicitly rather than forcing findings.
- Prefer meaningful fixes, not checklist compliance.


## Required inputs

Read the repository inventory, Section 2 findings, existing tests, CI configuration, package scripts, Makefiles, task runners, documented validation commands, public contracts, and examples.

## Allowed actions

Allowed: inspect tests and fixtures, run existing tests if safe, run existing coverage tools if already configured and safe, record test gaps and regression risks, update artifacts.

Not allowed: adding tests, rewriting tests, adding test dependencies, or changing CI workflows.

## Review checks

Examine test structure, unit tests, regression tests, contract tests, integration tests, end-to-end tests, fixtures, golden files, helpers, and CI automation.

Assess coverage for normal behavior, invalid inputs, edge cases, exceptions, configuration, CLI behavior, API contracts, serialization/file outputs, database/storage behavior, important workflows, backward compatibility, recent changes, security-relevant behavior, memory/resource and live-interaction-surface behavior (the `MEM`/`LIVE` findings from Section 2), failure/recovery, and deprecated or legacy behavior that must remain stable until removed.

Lead this section with the testing/regression-expert and QA/QC personas (see the persona-to-section map in `00-run-protocol.md`). For each High or `LIVE` finding from Section 2, note whether a regression test exists or must be added in Section 7; "hard to test" is a prompt to design a testable seam, not to skip coverage. Forcing function: append at least one observation per lead persona to `persona-review.md`, or note "no new finding from persona X in this section".

## Required outputs

Update the registers, decisions, commands, checkpoints, `persona-review.md`, and validation results if tests are run.

Create the per-phase report `section-summaries/03-tests-regression.md` (what was done, why, what was considered but not done) covering current test health, critical behavior well covered, critical behavior not well covered, missing regression tests (especially for `LIVE`/`MEM` findings), brittle/low-value/misleading tests, highest-value tests to add next, release-blocking test gaps, and test implications for deprecated-code candidates.

Use `T` for test gaps and `R` for regression or compatibility concerns.

## TodoWrite guidance

If TodoWrite is available, track test review and optional test execution as high-level todos.

## Judgment guidance

Do not equate quantity of tests with quality. Focus on critical behavior, public contracts, high-risk code, and recent changes.

If the repository lacks tests, record the absence and identify the smallest high-value tests that would improve release confidence.

## Non-applicable guidance

If the project is documentation-only or otherwise has no executable behavior, mark executable tests as not applicable and consider documentation checks or link checks if relevant.

## Exit criteria

Before moving to Section 4, existing tests and validation commands are understood, test gaps and regression risks are recorded, regression coverage for High/`LIVE`/`MEM` findings is planned, validation results are recorded if commands were run, candidate test actions are added, the per-phase report is written, and the checkpoint is recorded.
