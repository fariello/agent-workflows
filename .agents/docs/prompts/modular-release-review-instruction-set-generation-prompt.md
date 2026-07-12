# Instruction Set for Creating the Modular Release Review Runbook

## Objective

Create a modular `release-review/` runbook hierarchy that allows a modern coding agent, especially OpenCode using a strong reasoning model, to autonomously perform a robust repository and code review before a release or major run.

The resulting system should maximize the probability that the agent:

1. Understands the repository before changing it.
2. Performs a complete, structured audit.
3. Identifies meaningful bugs, risks, documentation gaps, test gaps, compatibility concerns, stale or deprecated code, and release blockers.
4. Implements safe, significant-value improvements.
5. Avoids unnecessary churn, speculative changes, broad rewrites, and risky behavior.
6. Tracks all findings and actions with unique run-specific IDs.
7. Produces durable review artifacts under `repository-review/<RUN_ID>/`.
8. Creates local commits at appropriate checkpoints.
9. Does not push to a remote until the end, and only if explicitly permitted.
10. Produces a final saved report and a table-first final response showing what was addressed and what was not addressed.

## Source Material

Use the existing final release validation Markdown file and the original 8-section sequence as the core source material. Preserve the review intent and rigor of the original sequence unless a change clearly improves autonomous execution, clarity, safety, or completeness.

Do not rewrite merely to rewrite. Make changes only when they materially improve the likelihood of a high-quality repository review.

## Desired Output

Generate a complete `release-review/` hierarchy as real Markdown and template files, packaged as a zip archive that can be downloaded and placed directly into a repository.

The zip archive should contain:

1. One main orchestrator file.
2. One shared run protocol file.
3. Eight numbered section files.
4. A small number of templates, if useful.
5. A `MANIFEST.md` file explaining the purpose of each generated file.
6. Clear instructions that the user can invoke with a single command such as:

   `Read and execute release-review/README.md`

The generated files should be ready to place into a repository without requiring manual reconstruction from prose.

The expected downloadable deliverable is:

```text
release-review.zip
```

The zip archive should expand to:

```text
release-review/
  MANIFEST.md
  README.md
  00-run-protocol.md
  01-current-state.md
  02-quality-security-edge-cases.md
  03-tests-regression.md
  04-docs-specs-examples.md
  05-feature-usability-maintainability.md
  06-compatibility-packaging-release.md
  07-implementation.md
  08-final-ship-review.md
  templates/
    execution-plan.md
    implementation-plan.md
    final-response.md
    finding-register.csv
    action-register.csv
```

## Recommended File Structure

Use this structure unless there is a strong reason to adjust it:

```text
release-review/
  README.md
  00-run-protocol.md
  01-current-state.md
  02-quality-security-edge-cases.md
  03-tests-regression.md
  04-docs-specs-examples.md
  05-feature-usability-maintainability.md
  06-compatibility-packaging-release.md
  07-implementation.md
  08-final-ship-review.md
  templates/
    execution-plan.md
    implementation-plan.md
    final-response.md
    finding-register.csv
    action-register.csv
```

Avoid creating more files unless they clearly improve execution quality.

## Authority Model

Make `release-review/README.md` the controlling instruction file.

The hierarchy should state clearly:

1. `README.md` controls the run.
2. `00-run-protocol.md` defines global rules.
3. `01` through `08` define phase-specific work.
4. Files under `repository-review/<RUN_ID>/` are the authoritative record of the run.
5. TodoWrite, if available, is only live progress tracking and is not the durable source of truth.

## Agent Invocation

The orchestrator should include this instruction directly:

> Treat this file as the controlling instruction for this repository review. Keep working until you have completed the required run artifacts, committed appropriate local changes, performed final validation, assessed whether to restart the review, made a push/no-push decision, and produced the final response in the required table-first format.

Use “local commits” where commits are intended during the review. Use “push” only for remote pushes.

## TodoWrite Guidance

Include TodoWrite instructions, but keep them bounded.

The runbook should instruct the agent:

1. Use TodoWrite if running in OpenCode and the tool is available.
2. Use TodoWrite for live progress visibility.
3. Do not treat TodoWrite as the authoritative record.
4. Mirror major section tasks and implementation batches in TodoWrite.
5. Do not create a TodoWrite item for every file inspected or every tiny edit.
6. Reconcile TodoWrite status against saved run artifacts before the final report.
7. If TodoWrite is unavailable, continue without it and record progress in the run directory.

This should improve transparency without creating excessive busywork.

## Run Directory Requirements

Require creation of:

```text
repository-review/<RUN_ID>/
```

Where `<RUN_ID>` is a timestamp such as:

```text
YYYYMMDD-HHMMSS
```

Require `repository-review/` to be added to `.gitignore` if not already ignored.

The run directory should include, at minimum:

```text
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
```

The exact numbering may be adjusted for clarity, but the artifacts above should exist unless explicitly marked not applicable.

## Unique ID Rules

Require every finding, candidate action, implemented change, deferred item, blocked item, deprecated-code candidate, CI candidate, decision, and final release concern to have a unique run-specific ID.

Use a run-specific prefix to reduce collision risk across restarts.

Recommended pattern:

```text
<RUN_ID>-S<section>-<TYPE><number>
```

Examples:

```text
20260606-142233-S2-B1
20260606-142233-S4-D3
20260606-142233-S7-X5
20260606-142233-S8-REL1
```

Restarts are new runs and must use new IDs. Restarted runs may reference earlier run IDs, but must not reuse them.

## Section Order

Preserve the 8-section sequence:

1. Current state and repository inventory
2. Quality, security, and edge cases
3. Tests and regression protection
4. Documentation, specifications, and examples
5. Feature completeness, usability, and maintainability
6. Compatibility, packaging, CI, deployment, and release artifacts
7. Implementation of safe, valuable fixes
8. Final ship review

Do not move implementation before the audit sections. The agent should understand the repository before making changes.

## Section File Design

Each section file should include:

1. Purpose
2. Required inputs
3. Allowed actions
4. Required review checks
5. Required outputs
6. TodoWrite guidance
7. Judgment guidance
8. Non-applicable guidance
9. Exit criteria

Each section should include a short standing-constraints block, but should not repeat the entire global protocol.

Recommended standing constraints:

```text
Standing constraints for this section:
- Preserve public behavior unless a change is clearly justified.
- Do not make speculative changes.
- Do not create broad refactors or formatting churn.
- Use run-specific unique IDs for every finding and action.
- Update the finding and action registers before leaving this section.
- Use TodoWrite if available, but treat repository-review/<RUN_ID>/ as authoritative.
- Mark non-applicable checks explicitly rather than forcing findings.
- Prefer meaningful fixes, not checklist compliance.
```

## Judgment Calls I Am Permitted to Make

I may make judgment calls to improve the final runbook when those judgments support the stated objective.

Permitted judgment calls include:

1. Renaming section files for clarity while preserving the 8-section flow.
2. Moving duplicated global instructions into `00-run-protocol.md`.
3. Adding short reinforcement language inside section files where it reduces drift.
4. Removing repetitive text that is likely to distract the agent.
5. Adding missing safeguards around commits, pushes, destructive changes, CI, deprecation, or validation.
6. Adjusting artifact names if doing so improves clarity.
7. Adding templates only when they reduce ambiguity or improve final reporting.
8. Making instructions more explicit where a modern LLM could otherwise interpret them incorrectly.
9. Marking some original prompts as section-level checks rather than preserving their exact phrasing.
10. Adding “not applicable” handling where a section may not fit a given repository.

## Judgment Calls I Should Avoid

Do not:

1. Add complexity for its own sake.
2. Create a large bureaucracy of artifacts that distracts from code quality.
3. Force every repository into every section.
4. Require a specific programming language, framework, package manager, or CI system.
5. Require branch creation unless the existing repository context clearly supports it.
6. Require remote pushes.
7. Encourage broad rewrites.
8. Encourage speculative features.
9. Encourage deleting code simply because it appears old.
10. Let section files contradict the main protocol.

## Implementation Philosophy

The runbook should instruct the coding agent to favor meaningful safe improvements over minimal review-only output, but not to change files merely to show activity.

Good changes include:

1. Bug fixes.
2. Security hardening.
3. Correctness fixes.
4. Edge-case handling.
5. Missing or weak tests for important behavior.
6. Documentation fixes that align docs with real behavior.
7. Packaging or release metadata fixes.
8. CI additions or improvements when clearly justified.
9. Deprecation markers or documentation for stale code when evidence is strong.
10. Small maintainability improvements that reduce real risk.

Bad changes include:

1. Cosmetic churn.
2. Large unrequested refactors.
3. Style-only rewrites.
4. Speculative feature work.
5. Reorganizing files without clear value.
6. Removing public behavior without compatibility analysis.
7. Creating CI workflows that publish, deploy, release, or upload artifacts without explicit permission.

## Deprecated-Code Analysis

Add explicit deprecated-code analysis across the runbook.

The runbook should require the agent to identify code, files, commands, examples, tests, configs, docs, workflows, or scripts that appear unused, obsolete, superseded, misleading, or harmful to maintainability.

However, the agent must distinguish among:

1. Safe to remove now.
2. Safe to mark deprecated now.
3. Candidate for future removal.
4. Probably still needed.
5. Unknown, requires human review.

The agent should not delete or deprecate code solely because it is old or not immediately referenced. It should look for evidence such as imports, references, tests, docs, package exports, CLI exposure, build scripts, workflows, external contract risk, and changelog history.

## CI and GitHub Actions

The runbook should require the agent to assess whether GitHub Actions or other CI should be added or updated.

The agent may add CI only when:

1. The repository has clear validation commands.
2. The workflow is low-risk.
3. It does not publish, deploy, release, upload secrets, or change remote state.
4. It is aligned with the repository’s language and package manager.
5. It materially improves release readiness.

The agent should consider, where applicable:

1. Linting.
2. Formatting checks.
3. Unit tests.
4. Type checks.
5. Build checks.
6. Security or dependency checks.
7. Documentation checks.
8. Matrix testing for supported versions.

If CI is not added, the agent should explain why in `ci-assessment.md`.

## Commit and Push Policy

The runbook should distinguish local commits from remote pushes.

Require local commits at appropriate checkpoints, especially:

1. After setting up the review artifacts and `.gitignore`.
2. After coherent implementation batches.
3. After documentation/test/CI updates where appropriate.
4. After final validation cleanup.

Do not require a local commit after every section if the section is review-only and does not change tracked repository files.

Remote pushes are prohibited until the final stage and only allowed if the user explicitly permitted pushing.

The final report must include a push/no-push recommendation and rationale.

## Implementation Plan

Require two planning artifacts:

1. `02-execution-plan.md`, created early after initial repository discovery.
2. `09-implementation-plan.md`, created after Sections 1 through 6 and before Section 7 implementation.

The early execution plan should be lightweight and provisional.

The implementation plan should map proposed changes to:

1. Unique IDs.
2. Source finding IDs.
3. Files likely to change.
4. Risk level.
5. Whether public behavior changes.
6. Required tests.
7. Required documentation updates.
8. Validation method.
9. Commit grouping.

The implementation plan should prevent the agent from prematurely fixing before it has completed the audit.

## Final Report Requirements

The final report must be saved as:

```text
repository-review/<RUN_ID>/12-final-response.md
```

The agent’s final user-facing response must present the same content.

The final response must begin with two tables.

First table:

```text
Completed actions
```

Columns:

1. Unique ID
2. Description of what was done
3. Files changed
4. Commit
5. Validation

Second table:

```text
Identified but not addressed
```

Columns:

1. Unique ID
2. Description of what was not done
3. Reason
4. Recommended next step

The second table must include audit findings that were identified but not implemented, not only action items that were started and left incomplete.

After the two tables, include:

1. Summary of changes.
2. Tests and validations run.
3. CI assessment summary.
4. Deprecated-code assessment summary.
5. Documentation and artifact updates.
6. Remaining risks.
7. Push/no-push decision.
8. Final release recommendation: GO, CONDITIONAL GO, or NO-GO.
9. Whether a restart is recommended.

## Restart Logic

The final section should require the agent to assess whether a new review run should be started.

Recommend a restart only when:

1. The implementation changed enough that earlier audit results may be stale.
2. The agent discovered substantial new architecture or behavior late in the run.
3. Validation exposed issues requiring another broad pass.
4. Major CI, packaging, public contract, or security changes were made.

Do not restart merely because minor fixes were made.

If a restart is recommended, the agent should explain why and whether it is urgent. A restarted run is a brand new run with a new run ID.

## Safety and Risk Controls

The runbook should tell the agent:

1. Do not run destructive commands unless clearly necessary and safe.
2. Do not delete user data, generated artifacts, databases, or untracked files without explicit justification.
3. Do not expose secrets in reports.
4. Do not commit secrets.
5. Do not install unnecessary dependencies.
6. Do not change license terms.
7. Do not alter public APIs without compatibility analysis.
8. Do not modify deployment or release automation to publish externally without explicit permission.
9. Stop and record a blocker if a change cannot be made safely.

## Quality Bar

The final hierarchy should feel like a practical operating manual for a strong coding agent, not a policy document.

It should be:

1. Clear.
2. Specific.
3. Complete.
4. Non-contradictory.
5. Modular.
6. Resistant to instruction drift.
7. Strong enough for autonomous execution.
8. Flexible enough to handle different repository types.
9. Conservative about risky changes.
10. Aggressive enough to improve meaningful release quality.

## Final Self-Review Before Delivering

Before presenting the generated `release-review/` hierarchy, review it for:

1. Contradictory instructions.
2. Missing artifact requirements.
3. Ambiguous commit versus push language.
4. Excessive repetition.
5. Missing final reporting requirements.
6. Missing TodoWrite fallback.
7. Missing deprecated-code analysis.
8. Missing CI assessment.
9. Missing non-applicable guidance.
10. Missing restart criteria.
11. Any language that encourages churn or unnecessary changes.
12. Whether the final output is a downloadable `release-review.zip` archive with the expected hierarchy and `MANIFEST.md`.

Only deliver the hierarchy after this self-review.
