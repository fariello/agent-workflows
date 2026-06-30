# 07 Implementation of Safe, Valuable Fixes

## Purpose

Create a consolidated implementation plan from Sections 1 through 6, then implement safe, meaningful, significant-value fixes.

This is the primary change-making section. It should favor useful release hardening over minimalism, but it must avoid churn, speculative work, broad refactors, and unsafe changes.

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

Read the findings register, action register, all section summaries from Sections 1 through 6, `deprecation-candidates.md`, `ci-assessment.md`, `schema-validation.md`, decisions, validation results, and current Git status.

## Required implementation plan

Before editing tracked project files, create `repository-review/<RUN_ID>/09-implementation-plan.md`.

The implementation plan must include scope summary, non-goals, change batches, unique implementation action IDs, source finding IDs, files likely to change, risk level, public behavior change assessment, required tests, required artifact updates, validation method, local commit grouping, deferred findings, blocked findings, deprecated-code decisions, and CI decisions.

Do not start implementation until the plan exists.

## Selection criteria

Implement findings when they are safe, well scoped, evidence-supported, likely to improve release readiness, validatable, and unlikely to break public behavior unless clearly justified.

Do not limit implementation to only high-priority items. Include lower-severity changes when they add significant value and are safe.

Defer or mark wont-do when a change is speculative, requires product judgment, needs unavailable credentials, risks public contract breakage without evidence, requires large refactoring, creates release/deployment side effects, cannot be validated, is cosmetic churn, or involves deprecation/removal without enough evidence.

### Non-deferral threshold for `LIVE`/High data-integrity findings (mandatory)

A finding tagged `LIVE` or rated **High** by the Section 2 live-interaction-surface or memory/resource review (can overwrite/destroy completed/verified/paid-for output or user data; spend real money/quota on skippable work; decide on incompletely-retrieved or truncated input; signal/stop/coordinate the wrong process; block forward progress through a backlog; or exhaust memory/handles in production) **must be fixed in this run, or explicitly escalated to the user - it may NOT be silently deferred to `TODO.md`.** The defer reasons "cannot be validated (hard to test)" and "requires large refactoring" do NOT apply to this class. For each such finding:

1. Implement the fix; extract a testable helper if needed so it CAN be validated ("hard to test" is a prompt to refactor for testability, not to defer).
2. If a fix is genuinely out of scope for the run, surface it to the user in the Section 7 per-phase report AND the final report's "identified but not addressed" table as an explicit **High/`LIVE`, not fixed** item requiring a decision - never only as a `TODO.md` entry.
3. Add a regression test for the fixed behavior.

#### Low-effort / low-risk Medium and Low findings: fix them too

A Medium- or Low-severity live-surface, memory, usability/self-documenting, or guiding-principles finding that is **low effort AND low risk** should also be fixed in this run, not deferred - this is exactly the class of cheap, safe correctness/usability fixes that tends to get dropped. Guardrails so this does not become scope-creep: apply only when ALL hold (low implementation effort, low risk, clear value, validatable); record a one-line effort+risk estimate on the finding (do not merely assert "low"); and if a fix turns out non-trivial, risky, or needs product judgment mid-way, stop and defer it normally with a reason rather than expanding scope.

### Self-documenting and guiding-principles fixes

Prefer fixes that make the product teach the user as they go - clearer command/flag/field names, better `--help`/usage output, helpful first-run guidance, actionable error messages, sensible defaults, inline hints - over adding documentation to compensate for an opaque interface. Implement `GP` (guiding-principles) fixes that move the project toward its stated principles; never implement a change that violates them.

### TODO.md update policy

As items from `TODO.md`/backlog are completed, become obsolete, or change status during this run, update `TODO.md` (and related backlog files) so they stay honest. Record the final disposition of every triaged item in `todo-reconciliation.md`. Do not use `TODO.md` as a place to silently park findings this review should have fixed or escalated.

## Allowed actions

Allowed: edit code, add/update tests, update docs/examples/specs/schemas/changelog/release notes, update packaging/build metadata when safe, add/update low-risk CI workflows when justified, mark code/docs deprecated when evidence is strong, remove obsolete code only when evidence is strong and risk is low, and create local commits.

Not allowed without explicit user permission: remote push, publish/deploy/release/upload, rotate credentials, delete user data, rewrite major architecture, change license terms, or remove public APIs/CLI commands/schemas/config fields without compatibility analysis and strong justification.

## Implementation order

Prefer safety/correctness fixes, `LIVE`/memory data-integrity fixes, tests protecting those fixes, edge-case/reliability fixes, self-documenting/usability and guiding-principles fixes, docs/spec/example corrections, packaging/build/release metadata fixes, low-risk CI additions, deprecation markers, then small maintainability fixes that reduce real risk.

Keep related code, tests, and docs synchronized in the same batch when practical.

## Local commits

After each coherent implementation batch, run relevant validation, update registers, update `07-commits.md`, commit only this run's tracked changes, and reference action IDs in the commit message.

If pre-existing user changes cannot be separated, do not commit. Record the blocker and continue carefully if safe.

## CI additions

If adding GitHub Actions or CI, keep workflows minimal, use repository-native commands, avoid publish/deploy/release/upload/secrets, avoid broad matrices unless justified, document rationale in `ci-assessment.md`, and validate syntax where practical.

## Schema validation actions

For each schema-related action selected for implementation:

1. Confirm the schema or data contract is actually part of the project contract or internal validation path.
2. Validate syntax and representative examples when practical.
3. Keep schemas, implementation, tests, docs, examples, generated artifacts, changelog, and release notes synchronized.
4. Preserve backward compatibility for public schemas and serialized outputs unless a breaking change is clearly justified and documented.
5. Add or update schema validation tests or CI checks only when low risk and repository-native commands are clear.
6. Record results in `schema-validation.md` and `10-validation-results.md`.

## Deprecated-code actions

For each selected deprecation candidate, confirm evidence, check references/exports/docs/tests/package metadata/CLI exposure/build scripts/workflows/changelog history, choose the safest action, prefer staged deprecation when public contract risk exists, and update docs/tests/release notes if behavior or public surface changes.

## Required outputs

Update the implementation plan, registers, decisions, commands, commits, checkpoints, validation results, deprecation candidates, CI assessment, `todo-reconciliation.md`, and `guiding-principles-assessment.md`.

Create the per-phase report `section-summaries/07-implementation.md` (what was done, why, what was considered but not done) covering implemented scope, intentionally unimplemented scope (including any `LIVE`/High finding escalated rather than fixed), change batches, source finding IDs addressed, self-documenting/usability and guiding-principles fixes made, `TODO.md` items completed or re-classified, tests and validations, artifacts updated, local commits, remaining risks, and follow-up work.

## TodoWrite guidance

If TodoWrite is available, create todos for each implementation batch, mark each in progress before editing, mark complete only after validation/register updates/local commit decision, track deferred/blocked items at a high level, and reconcile TodoWrite with the action register before leaving Section 7.

## Judgment guidance

Do the work that improves release readiness, not the work that merely increases diff size. Small precise fixes are preferred.

## Non-applicable guidance

If no safe implementation work is found, do not fabricate changes. Record the rationale and proceed to final review.

## Exit criteria

Before moving to Section 8, implementation plan is complete, safe selected fixes are implemented or explicitly deferred/blocked/wont-do, all `LIVE`/High data-integrity findings are fixed or explicitly escalated (never silently TODO'd), low-effort/low-risk Medium/Low fixes are made, self-documenting and guiding-principles fixes are applied where safe, `TODO.md` is updated to stay honest, relevant artifacts are synchronized, validation is run and recorded where possible, local commits are made or explained, actions are reconciled, the per-phase report is written, and the checkpoint is recorded.
