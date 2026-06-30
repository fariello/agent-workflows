# 08 Final Ship Review

## Purpose

Assess whether the current project is ready to ship as a robust, well-written, well-documented, stable, secure, maintainable, feature-complete project for its intended scope.

Be practical but conservative. The goal is not to claim perfection. The goal is to determine whether the project is as close to release-ready as reasonably possible for its intended scope.

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

Read all run artifacts, current Git status, local commits made during the run, validation results, CI assessment, schema validation assessment, deprecation candidates, findings and action registers, implementation plan, and Section 7 results.

## Allowed actions

Allowed: run final validation commands, inspect final diffs, update final artifacts, make final small cleanup edits if necessary and safe, create a final local commit if tracked files changed, prepare push/no-push plan, and write final report.

Not allowed unless explicitly permitted: remote push, publish/deploy/release/upload/change remote state, start a new review run automatically, or make broad new implementation changes that should have gone through Section 7 planning.

## Final review checks

Review project purpose/scope, feature completeness, correctness, stability, security/privacy, memory/resource safety, edge cases, performance, test coverage, regression protection, docs/specs/examples, API/CLI/UI/config/schema/storage/integration consistency, packaging/build, deployment/operations, installation/first-run, versioning/changelog/release notes, backward compatibility/migration, developer and operator experience, user-facing rough edges, documented limitations, deprecation candidates, CI readiness, and release blockers.

Conduct the final review through all eight personas (`00-run-protocol.md`) and produce an eight-persona sign-off (one line per persona, including the novice and stakeholder views) in the final report and in `persona-review.md`.

## Eight-persona sign-off, TODO, principles, and self-documenting reconciliation (mandatory)

Before writing the final report:

1. **Persona sign-off.** For each of the eight personas, state whether the project is acceptable from that viewpoint and list any blocking concerns with IDs.
2. **TODO/backlog reconciliation.** Finalize `todo-reconciliation.md`: confirm every `must-before-release` item is fixed or escalated as a release blocker, every `should-` item is fixed or consciously deferred, stale items are removed/marked, and `TODO.md` itself is honest. Summarize in the report.
3. **Guiding-principles adherence.** Finalize `guiding-principles-assessment.md` with a per-principle verdict and any unresolved `GP` findings.
4. **Self-documenting / learn-as-you-go.** State whether a novice could learn the project as they go without a manual or course, and list any remaining `U` blockers.

## Final bug/security sanity audit

Before writing the final report, create or update:

```text
repository-review/<RUN_ID>/final-bug-security-audit.md
```

This is not a full repeat of Section 2. It is a final post-implementation sanity audit focused on whether changes made during the run introduced or left unresolved material issues.

Review:

1. New or modified code paths.
2. New or modified tests.
3. New or modified configuration, CI, packaging, scripts, schemas, examples, and documentation.
4. Changed file handling, path handling, subprocess use, network behavior, serialization, deserialization, authentication, authorization, logging, error handling, and secret handling.
5. Any unresolved HIGH or CRITICAL findings.
6. Whether final validation failures indicate latent bugs or release blockers.
7. Whether any implemented change created a new compatibility, security, privacy, or reliability risk.

Record:

1. New findings, if any, with run-specific IDs.
2. Previously identified issues still unresolved.
3. Issues confirmed resolved.
4. Residual risk.
5. Whether the final release recommendation changes.

If a new material issue is found, update the finding and action registers and decide whether it must be fixed before final completion. Do not hide or minimize late-discovered issues.

## Final validation

Run the most appropriate repository-native validation commands available and safe. Record all results in `10-validation-results.md`. If validation cannot be run, explain why and assess release risk.

## Final schema validation check

Before the final report, update `schema-validation.md` with final status.

Confirm, where applicable:

1. Schemas and data contracts were discovered and assessed.
2. Repository-native schema validation commands were run, or inability to run them was explained.
3. Representative examples, fixtures, golden files, sample configs, documented payloads, imports, exports, migrations, or serialized outputs were validated when practical.
4. Schema, implementation, documentation, tests, examples, and generated artifacts are synchronized or remaining drift is recorded.
5. Public schema or serialized-output compatibility risks are identified and reflected in the final recommendation.

Use `SCH` IDs for unresolved schema issues.

## Final finding categories

Categorize remaining findings as must fix before release, should fix before release if time allows, acceptable known limitation if documented, or nice to have after release.

For each final finding, include ID, title, severity, affected area, why it matters, recommended fix, affected audiences, public behavior change assessment, required artifact updates, and whether it blocks release.

Use `REL` IDs for final release decisions and blockers. Preserve earlier IDs when referring to unresolved items.

## Push/no-push plan

Create or update `repository-review/<RUN_ID>/11-push-plan.md` with current branch, local commits, Git status, whether the user explicitly permitted pushing, push recommendation, risks, suggested command if permitted, and no-push rationale if permission is absent.

Do not push unless explicitly permitted.

## Restart assessment

Decide whether a new review run should be started. Recommend restart only when implementation changed enough that earlier audit results may be stale, substantial architecture or behavior was discovered late, validation exposed issues requiring another broad pass, or major CI/packaging/public contract/security changes were made. Do not restart merely because minor fixes were made. Do not start a new run automatically.

## Final report

Save the final report to `repository-review/<RUN_ID>/12-final-response.md`, then present the same content to the user.

Create or update `section-summaries/08-final-ship-review.md` with the Section 8 final ship review summary.

The final response must begin with these two tables.

### Completed actions

| Unique ID | Description of what was done | Files changed | Commit | Validation |
|---|---|---|---|---|

### Identified but not addressed

| Unique ID | Description of what was not done | Reason | Recommended next step |
|---|---|---|---|

The second table must include audit findings identified but not implemented, not only actions that were attempted and left incomplete. Any `LIVE`/High data-integrity finding that was not fixed MUST appear here, flagged `LIVE - needs user decision`, never silently moved to `TODO.md`.

After the tables, include summary of changes, tests and validations run, CI assessment summary, schema validation summary, deprecated-code assessment summary, final bug/security/memory sanity audit summary, TODO.md/backlog reconciliation summary, guiding-principles adherence summary, eight-persona sign-off, self-documenting / learn-as-you-go assessment, documentation and artifact updates, remaining risks, push/no-push decision, final GO/CONDITIONAL GO/NO-GO recommendation, restart recommendation, and (if applicable) readiness to proceed to Section 9 release execution upon explicit user approval.

**Live-surface / data-integrity gate.** If any `LIVE`/High data-integrity finding (Section 2) is unaddressed, the recommendation may not be a clean GO: it is at most CONDITIONAL GO with that finding listed as an explicit prerequisite, or NO-GO if it can overwrite/destroy verified data, spend uncontrolled money, corrupt shared state, or exhaust production resources. Hermetic tests passing does not satisfy this gate.

## TodoWrite guidance

If TodoWrite is available, reconcile all todos against the findings and action registers, mark statuses accurately, and do not leave stale in-progress todos.

## Judgment guidance

Be honest. Do not claim release readiness if validation failed, critical tests are missing, security blockers remain, or public contract risk is unresolved.

A CONDITIONAL GO is appropriate when the project is mostly ready but has limited, clearly documented prerequisites. A NO-GO is appropriate when unresolved blockers would likely harm users, operators, developers, integrations, maintainers, security, or release reliability.

## Non-applicable guidance

If release concepts do not apply to the repository, provide a readiness assessment for the nearest equivalent, such as major run readiness, internal adoption readiness, or handoff readiness.

## Section 9 handoff

If the recommendation is GO or CONDITIONAL GO and the user explicitly approves performing the release, proceed to `09-release-execution.md`. Do not begin release execution automatically or without that approval. If the recommendation is NO-GO, do not proceed to Section 9.

## Exit criteria

The run is complete only when final validation, the eight-persona sign-off, the TODO/backlog reconciliation, the guiding-principles assessment, the self-documenting assessment, push/no-push plan, restart assessment, release recommendation, completed and unaddressed tables, final response file, and user-facing final response are complete.
