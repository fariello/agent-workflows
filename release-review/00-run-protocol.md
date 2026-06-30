# 00 Run Protocol

This file defines the global rules for the release review. These rules apply to all sections.

## Authority model

1. `README.md` is the controlling instruction.
2. This file defines shared rules.
3. Section files `01` through `09` define phase-specific tasks (`09` runs only after a GO/CONDITIONAL GO and explicit user approval to release).
4. `repository-review/<RUN_ID>/` is the authoritative run record.
5. TodoWrite, if available, is live progress tracking only.

If a section file appears to conflict with this protocol, follow this protocol and record the conflict in `05-decisions.md`.

## Review mindset: the eight reviewer personas

This review is not a checklist pass. Every audit section (Sections 1 through 6) and the final review (Section 8) must be conducted while deliberately adopting, in turn, each of the following eight expert personas. The goal is breadth of perspective: a finding obvious to one persona is often invisible to another. Do not merely name the personas; actually reason from each viewpoint and let each surface findings the others would miss.

| # | Persona | Looks for |
|---|---|---|
| 1 | **QA / QC engineer** | Defects, broken behavior, incorrect output, flaky paths, things that "work on the happy path only", missing validation, anything that would fail acceptance. |
| 2 | **Testing & regression-testing expert** | Missing/weak tests, untested critical paths, regression exposure, brittle or misleading tests, missing fixtures/golden files, no protection for recently changed behavior. |
| 3 | **UI / UX expert engineer** | Confusing flows, poor defaults, unclear errors, inconsistent terminology, accessibility gaps, friction, anything that needs a manual to understand, anything that violates "learn as you go". |
| 4 | **Systems & software architect** | Abstraction quality, extensibility, separation of concerns, elegant vs. accidental complexity, future-proofing without bloat, the general case vs. hardcoded special cases, coupling, configurability. |
| 5 | **Software engineer** | Code correctness, readability, maintainability, memory/resource handling, error propagation, dead code, dependency hygiene, idiomatic use of the language/framework. |
| 6 | **Sophisticated power user** | Missing advanced capabilities, ergonomics, scriptability/automation, escape hatches, performance at scale, whether the tool respects expert expectations. |
| 7 | **Complete novice / naive user** | First-run confusion, undefined jargon, missing onboarding, unclear next step, anything that assumes domain knowledge the user does not have, anything requiring "reading the manual" or a course. |
| 8 | **Stakeholder** | Whether the project actually achieves its intended goals/outcomes, fitness for purpose, risk to the mission, reputational/compliance/business risk, value delivered vs. promised. |

When recording a finding, note which persona(s) surfaced it when it adds clarity. A finding raised by the novice or stakeholder persona is as legitimate as one from the QA or security perspective.

## Guiding principles adherence

If the repository contains a guiding-principles document (`GUIDING_PRINCIPLES.md`, `PRINCIPLES.md`, `.agents/GUIDING_PRINCIPLES.md`, a "Principles" section in `README.md`/`CONTRIBUTING.md`, or an equivalent named in `AGENTS.md`), treat it as a binding contract for this review:

1. Discover and read it during Section 1; record its location and a summary in `01-repository-inventory.md`.
2. In every audit section, check the project against each stated principle and file findings for violations (type `GP`).
3. In Section 7, prefer fixes that move the project toward its principles; do not implement changes that violate them.
4. In Section 8, include a per-principle adherence assessment.

If no such document exists, fall back to these universal release principles and record that you did so:

- **Intuitive and self-documenting.** A user should be able to "learn as they go" without reading a manual or taking a course. Naming, defaults, help text, error messages, and first-run behavior should teach the user what to do next.
- **Solve for the general case, configurable over hardcoded.** Avoid special-casing and magic constants where configuration or abstraction is the cleaner answer, without adding speculative features.
- **KISS.** Prefer the simplest design that meets the need; avoid bloat and accidental complexity.
- **Honest documentation.** Docs describe what the software actually does today, not what is hoped for.

## Self-documenting / learn-as-you-go bar

A core release goal of this review is that the released project is **as intuitive and self-documenting as reasonably possible**, so users can learn it as they go. Throughout the review, actively hunt for and record (type `U`) anything that forces a user to read external documentation, attend training, or already possess domain knowledge in order to accomplish a basic task: unclear command/flag/field names, silent or cryptic errors, missing `--help`/usage output, missing first-run guidance, undefined jargon in the UI or CLI, non-obvious required steps, and confusing defaults. Where the fix is safe and in scope, implement it in Section 7 (clearer help text, better error messages, sensible defaults, inline hints), not merely document it.

## TODO.md and tracked-backlog reconciliation

Many repositories carry a `TODO.md` (or equivalent: `TODO`, `TODOS.md`, `BACKLOG.md`, `ROADMAP.md`, `KNOWN_ISSUES.md`, `.agents/TODO.md`, issue-tracker exports, or `TODO`/`FIXME`/`HACK`/`XXX` markers in code). These often contain items that should - or might need to - be addressed before a release. This review must not ignore them.

1. **Discover** all such backlog sources in Section 1 and inventory them in `01-repository-inventory.md`.
2. **Triage** every TODO-like item against this release. For each, classify it as:
   - `must-before-release` - a release blocker or a known defect/risk that should not ship.
   - `should-before-release` - worth doing now if safe and in scope.
   - `out-of-scope-for-release` - legitimately deferred; leave it tracked.
   - `stale/obsolete` - already done, no longer relevant, or contradicted by current code (deprecation candidate).
3. **File findings** (type `TODO`) for any `must-` or `should-` items and feed them into Section 7 selection like any other finding.
4. **Update `TODO.md` itself** in Section 7 when items are completed, become obsolete, or change status - keep it honest. Do **not** use `TODO.md` as a dumping ground to silently defer High-severity findings discovered in this review (see Section 7 non-deferral rule).
5. Record the full triage in `todo-reconciliation.md` and summarize it in the Section 8 report.

## Mandatory per-phase reports

Each section (Sections 1 through 9) must produce a per-phase report saved under:

```text
repository-review/<RUN_ID>/section-summaries/<NN>-<short-name>.md
```

Use `templates/per-phase-report.md`. Every per-phase report must explicitly cover three things:

1. **What I did** in this phase (concrete inspections, commands, edits, decisions).
2. **Why** I did it (the reasoning, the risk being mitigated, the principle/persona driving it).
3. **What I considered but did NOT do**, and the explicit reason (out of scope, too risky, no evidence, deferred, needs human decision). This third part is mandatory and is as important as the first two.

These reports are part of the deliverable. They give the user a readable, auditable narrative of the review independent of the CSV registers.

## Commit-between-phases policy

In addition to committing meaningful tracked product changes (see Commit policy below), commit at every section boundary so the run is recoverable and the per-phase narrative is preserved:

1. After completing each section, commit that section's tracked product changes (if any) as a coherent unit referencing the section's action IDs.
2. If the user has asked for run artifacts to be committed (or `repository-review/` is intentionally tracked for this project), commit the section's per-phase report and updated registers at the boundary too. Otherwise keep them local per the artifact policy.
3. Never bundle changes from two different sections into one commit unless they are genuinely one logical change.
4. Record each commit in `07-commits.md` and at the section checkpoint in `08-checkpoints.md`.

## Core behavior

Proceed autonomously through the full review unless invoked through a planning-only command. In planning-only mode, complete Sections 1 through 6, create `09-implementation-plan.md`, and stop before Section 7 implementation.

Section 9 (release execution: pushing, tagging, publishing, deploying) is performed only after Section 8 produces a GO or CONDITIONAL GO and the user has explicitly approved release execution. Do not run Section 9 automatically.

Proceed autonomously through the full review. Use judgment. Do not stop for minor uncertainty. Record assumptions and proceed conservatively.

Stop or pause only for a true safety blocker, such as risk of deleting user data, exposing or committing secrets, running ambiguous destructive commands, needing unavailable credentials, being unable to separate this run's changes from pre-existing user changes, or needing to alter public behavior without enough evidence or validation.

## Required run directory

Create:

```text
repository-review/<RUN_ID>/
```

Use a timestamp run ID:

```text
YYYYMMDD-HHMMSS
```

Add `repository-review/` to `.gitignore` if not already ignored.

Required artifacts:

| Artifact | Purpose |
|---|---|
| `00-run-metadata.md` | Run ID, timestamp, agent/model if known, repository path, Git metadata, initial status, environment summary. |
| `01-repository-inventory.md` | Project type, structure, languages, frameworks, public contracts, tests, docs, build/release artifacts. |
| `02-execution-plan.md` | Lightweight plan for the full review and audit, updated when material facts change. |
| `03-findings-register.csv` | Durable register of all findings, including addressed and unaddressed findings. |
| `04-action-register.csv` | Durable register of all candidate actions, implemented changes, deferred items, and blockers. |
| `05-decisions.md` | Decisions, assumptions, non-applicable judgments, scope choices, and rationale. |
| `06-commands.md` | Commands run, purpose, result summary, and whether output was clean or had errors. |
| `07-commits.md` | Local commits made, files included, source action IDs, and validation. |
| `08-checkpoints.md` | Section boundary checkpoints and reconciliation notes. |
| `09-implementation-plan.md` | Consolidated implementation plan created after Sections 1 through 6 and before Section 7. |
| `10-validation-results.md` | Tests, builds, linters, type checks, security checks, documentation checks, and manual validation. |
| `11-push-plan.md` | Push/no-push decision, rationale, branch/remotes, and recommended next action. |
| `12-final-response.md` | Final saved report matching the user-facing final response. |
| `deprecation-candidates.md` | Deprecated, obsolete, stale, unused, superseded, or misleading code and artifact candidates. |
| `ci-assessment.md` | CI and GitHub Actions assessment, recommendations, changes made, or reasons no change was made. |
| `schema-validation.md` | Discovered schemas, schema validation commands, sample payload/config/example validation, compatibility risks, and schema drift findings. |
| `final-bug-security-audit.md` | Final post-implementation bug, correctness, security, privacy, and unsafe-change sanity audit before completion. |
| `todo-reconciliation.md` | Triage of every discovered `TODO.md`/backlog/`TODO`-marker item against this release, with per-item classification and disposition. |
| `guiding-principles-assessment.md` | Per-principle adherence assessment against the repository's guiding-principles document, or the universal fallback principles if none exists. |
| `persona-review.md` | Per-persona notes capturing what each of the eight reviewer personas surfaced, including the novice and stakeholder views. |
| `section-summaries/` | Mandatory per-phase reports for Sections 1 through 9, each covering what was done, why, and what was considered but not done. |
| `audit-lanes/` | Optional reports from controlled parallel read-only audit lanes used after Section 1. |

If any artifact is not applicable, create it anyway and mark it as not applicable with rationale.

## Unique ID system

Every finding, candidate action, implemented change, deferred item, blocked item, deprecated-code candidate, CI candidate, decision, release concern, and final recommendation must have a unique run-specific ID.

Use this pattern:

```text
<RUN_ID>-S<section>-<TYPE><number>
```

Examples:

```text
20260606-142233-S1-A1
20260606-142233-S2-B1
20260606-142233-S2-S1
20260606-142233-S3-T1
20260606-142233-S4-D1
20260606-142233-S5-M1
20260606-142233-S6-CI1
20260606-142233-S7-X1
20260606-142233-S8-REL1
```

Recommended type codes:

| Type | Meaning |
|---|---|
| `A` | General action or artifact concern |
| `B` | Bug or correctness issue |
| `S` | Security or privacy issue |
| `E` | Edge case, error handling, cleanup, recovery, or resource issue |
| `T` | Test gap or test concern |
| `D` | Documentation, specification, example, or help-text issue |
| `F` | Feature completeness issue |
| `U` | Usability, developer experience, or operator experience issue |
| `M` | Maintainability issue |
| `R` | Regression, compatibility, migration, or public contract risk |
| `P` | Packaging, build, release artifact, or versioning issue |
| `O` | Operations or deployment issue |
| `CI` | CI or GitHub Actions issue or recommendation |
| `SCH` | Schema, data contract, serialized format, migration, payload, or config validation issue |
| `DEP` | Deprecated, obsolete, stale, or unused code/artifact candidate |
| `TODO` | Item discovered in `TODO.md`/backlog/roadmap or a `TODO`/`FIXME` code marker that bears on this release |
| `GP` | Guiding-principles violation (against the repo's principles doc or the universal fallback principles) |
| `MEM` | Memory, resource, lifetime, leak, unbounded-growth, or concurrency/state-safety issue |
| `X` | Concrete implemented change |
| `REL` | Final release decision, blocker, or release readiness finding |
| `Q` | Question or ambiguity |
| `DEC` | Decision or judgment call |

Restarts are new runs with new IDs. A restarted run may reference earlier run IDs but must not reuse them.

## Register requirements

Maintain `03-findings-register.csv` and `04-action-register.csv` throughout the run. Use these statuses: `identified`, `planned`, `completed`, `deferred`, `blocked`, `not_applicable`, `superseded`, and `wont_do`.

Findings must include ID, section, type, severity, title, status, affected area, evidence, impact, recommended action, public behavior change, required artifact updates, source files, validation, and next step.

Actions must include ID, source finding IDs, section, status, description, files changed, commit, validation, reason not done, and recommended next step.

## TodoWrite protocol

If running in OpenCode and TodoWrite is available, use TodoWrite for live progress visibility. Create one todo per major section and one per implementation batch. Keep todo statuses aligned with the run artifacts. Reconcile TodoWrite against the registers before the final report.

Do not use TodoWrite as the official record. If TodoWrite is unavailable, continue without it and record progress in the run directory.

## Optional controlled parallel audit mode

After Section 1 completes the repository baseline, the main agent may use controlled parallel read-only audit lanes for Sections 2 through 6 when doing so is likely to improve review breadth, reduce missed findings, or manage a large repository more effectively.

Parallel audit mode is optional. Do not force it for small or simple repositories.

Allowed lane scopes include:

1. Code quality, correctness, security, privacy, and edge cases.
2. Tests, fixtures, coverage, and regression protection.
3. Documentation, specifications, examples, and help text.
4. Compatibility, packaging, build, CI, deployment, versioning, and release artifacts.
5. Schemas, data contracts, migrations, examples, fixtures, and serialized outputs.
6. Deprecated, obsolete, stale, unused, duplicated, or superseded code and artifacts.

Rules for parallel audit lanes:

1. The main agent must complete Section 1 before starting parallel lanes.
2. Lanes must be read-only.
3. Lanes must not edit tracked files.
4. Lanes must not update official registers directly.
5. Lanes must not create commits.
6. Lanes must not push to a remote.
7. Lanes must not make final release decisions.
8. Lanes must not assign official run-specific IDs.
9. Lanes should use temporary candidate IDs only.
10. Lanes must produce compact reports under `repository-review/<RUN_ID>/audit-lanes/` using `templates/audit-lane-report.md`.
11. The main agent must synthesize all lane reports before creating `09-implementation-plan.md`.
12. The main agent must deduplicate findings, assign official IDs, decide severity, update registers, and record decisions.
13. Section 7 implementation must remain serial.
14. Section 8 final review must remain serial.
15. Section 9 release execution must remain serial.

If parallel lanes are not used, record that decision in `05-decisions.md` and continue serially.


## Live-interaction-surface and data-integrity rule (shared)

A recurring source of production incidents is **live-interaction surfaces** that hermetic unit tests do not exercise: resume/skip/idempotency logic, multi-process or multi-run coordination (start guards, pidfiles, stop/signal targeting, shared ledgers), work-selection/limit/pagination advancement, spend/cap/budget accounting, external-IO/fetch completeness, and any place where incomplete data drives an automated decision or where a re-run can overwrite completed/verified/paid-for output.

Green tests are NOT evidence these are correct. When such surfaces exist, trace the actual runtime behavior by reading the code paths, not by inferring from passing tests.

A defect on a live-interaction surface that can (a) overwrite or destroy completed/verified/paid-for output or user data, (b) spend real money or quota on work that should have been skipped, (c) make an automated decision on incompletely-retrieved or truncated input, (d) signal/stop/coordinate the wrong process, or (e) prevent forward progress through a backlog, is **at least High severity**, is tagged `LIVE` in the finding title, and the difficulty of writing an automated test for it does **not** lower its severity. Section 7 defines the mandatory non-deferral handling for these findings.

## Memory, resource, and lifetime rule (shared)

Treat memory and resource correctness as first-class (`MEM`). Hunt for leaks and unbounded growth (caches/maps/lists/log buffers that never evict), unclosed files/sockets/handles/db connections, missing cleanup on error paths, use-after-free / use-after-close, double-free / double-close, dangling references, retained large buffers, recursion without bounds, and concurrency/state hazards (races, missing synchronization, non-idempotent retries, TOCTOU). Apply this to whatever the language exposes: manual memory, GC pressure and retention, RAII/ownership, context managers, `defer`/`finally`, and connection pools. A confirmed leak or unbounded-growth path that affects long-running or production use is at least Medium and often High.

## Command logging

For every meaningful command, append to `06-commands.md` the command, purpose, working directory, relevant assumptions, result, short output summary, and follow-up action if any.

Do not paste secrets or excessive logs. Summarize long outputs and save only relevant excerpts when needed.

## Commit policy

Use local commits for meaningful tracked repository changes when safe. Do not commit `repository-review/` artifacts unless the user explicitly asks for them to be committed.

Before any commit, run `git status --short`, confirm the files to commit were changed by this run, avoid committing unrelated pre-existing changes, and run appropriate validation first or state why validation could not be run.

Commit at logical checkpoints: after adding `repository-review/` to `.gitignore`, after coherent implementation batches, after test/docs/CI updates when they form a reviewable unit, and after final validation cleanup if tracked files changed.

Use commit messages that reference action IDs. If changes cannot be separated from pre-existing user changes, do not commit. Record the blocker.

## Remote push policy

Do not push to a remote during the review. At the end, create `11-push-plan.md` with branch, local commits, permission status, push recommendation, risks, suggested command if permitted, and no-push rationale if permission is absent. Only push if explicitly permitted by the user.

## Implementation philosophy

Favor meaningful, safe improvements. Do not restrict fixes to only high-priority issues. Implement lower-severity changes when they add significant release value and are safe, well scoped, and validated.

Good changes include bug fixes, security hardening, correctness fixes, edge-case handling, cleanup fixes, important tests, accurate docs, packaging fixes, low-risk CI checks, clear deprecation markers, and small maintainability improvements that reduce real risk.

Avoid cosmetic churn, broad refactors, style-only rewrites, speculative features, file reorganization without clear value, public behavior changes without compatibility analysis, unnecessary dependencies, and workflows that publish, deploy, release, or upload artifacts without explicit permission.

## Deprecated-code analysis

Throughout the review, identify code, files, commands, examples, tests, configs, docs, workflows, or scripts that appear unused, obsolete, superseded, misleading, or harmful to maintainability. Record candidates in `deprecation-candidates.md`.

Classify each candidate as safe to remove now, safe to mark deprecated now, candidate for future removal, probably still needed, or unknown requiring human review.

Do not delete or deprecate something solely because it is old or not immediately referenced. Look for imports, references, tests, docs, package exports, CLI exposure, build scripts, CI workflows, changelog history, external contract risk, and usage patterns.

## CI and GitHub Actions

Assess whether CI should be added or updated. Record findings in `ci-assessment.md`.

You may add or update CI only when validation commands are clear, the workflow is low risk, it does not publish, deploy, release, upload artifacts, or change remote state, it does not require unknown secrets, it aligns with the repository language and package manager, and it materially improves release readiness.

Consider linting, formatting checks, unit tests, type checks, build checks, security or dependency checks, documentation checks, and matrix testing for supported versions. If CI is not added, explain why.

## Schema validation

Throughout the review, identify and validate schemas and data contracts when applicable.

Schemas may include:

1. JSON Schema.
2. OpenAPI or Swagger specifications.
3. GraphQL schemas.
4. XML Schema.
5. Database schemas or migrations.
6. Protocol buffers.
7. Avro, Parquet, or other data serialization contracts.
8. Configuration schemas.
9. Custom file format schemas.
10. Message, event, API payload, import, export, or serialized output contracts.

Record schema findings in `schema-validation.md` and the finding/action registers.

When repository-native validation commands exist, use them. When examples, fixtures, golden files, sample configs, documented payloads, or test data exist, validate representative samples against the relevant schemas when practical and safe.

Check for:

1. Schema syntax validity.
2. Drift between schemas, implementation, docs, examples, tests, and generated artifacts.
3. Backward compatibility risks for public schemas and serialized outputs.
4. Missing validation for user-provided or external data.
5. Migration or versioning concerns.
6. Generated schema artifacts that are stale or not reproducible.
7. CI opportunities for schema validation.

Do not introduce new schema tooling unless it is low risk, aligned with the repository, and clearly justified. If validation is not possible, explain why and record the residual risk.

## Validation expectations

Use repository-native commands when available. Prefer commands documented in README, package scripts, Makefiles, task runners, CI files, or contribution docs. Do not invent unsafe commands or install heavy new tooling just to validate unless the repository clearly requires it.

## Non-applicable handling

Some repositories will not have APIs, CLIs, UIs, packaging, deployment, docs, tests, or CI. Do not force findings. Mark non-applicable checks explicitly, explain why, and continue.

## Final report requirements

Save the final report to `repository-review/<RUN_ID>/12-final-response.md`, then present the same content to the user.

The final report must begin with two tables:

### Completed actions

| Unique ID | Description of what was done | Files changed | Commit | Validation |
|---|---|---|---|---|

### Identified but not addressed

| Unique ID | Description of what was not done | Reason | Recommended next step |
|---|---|---|---|

The second table must include audit findings that were identified but not implemented, not only actions that were started and left incomplete.

After the two tables, include summary of changes, validations run, CI assessment summary, schema validation summary, deprecated-code summary, final bug/security/memory sanity audit summary, TODO.md/backlog reconciliation summary, guiding-principles adherence summary, eight-persona sign-off (one line per persona, including the novice and stakeholder views), self-documenting/learn-as-you-go assessment, documentation and artifact updates, remaining risks, push/no-push decision, GO/CONDITIONAL GO/NO-GO recommendation, and restart recommendation.

The "identified but not addressed" table must include any `LIVE`/High live-interaction-surface finding that was not fixed, flagged `LIVE - needs user decision`. Such a finding must never be silently moved into `TODO.md` in place of being reported here.

## Restart assessment

At the end, decide whether a new review run should be started. Recommend a restart only when implementation changed enough that earlier audit results may be stale, substantial architecture or behavior was discovered late, validation exposed issues requiring another broad pass, or major CI, packaging, public contract, or security changes were made. Do not restart merely because minor fixes were made.

## Safety rules

Do not run destructive commands unless clearly necessary and safe. Do not delete user data, generated artifacts, databases, or untracked files without explicit justification. Do not expose or commit secrets. Do not install unnecessary dependencies. Do not change license terms. Do not alter public APIs without compatibility analysis. Do not modify deployment or release automation to publish externally without explicit permission. Stop and record a blocker if a change cannot be made safely.
