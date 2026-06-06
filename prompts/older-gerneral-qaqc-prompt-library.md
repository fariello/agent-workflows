# Project Audit, Sync, Validation, and Release Readiness Prompt Library

Use this document as a reusable prompt library for periodically checking, auditing, synchronizing, validating, hardening, and preparing a project for release.

Each section is intended to be copied and pasted independently. Use the lighter sections for routine maintenance. Use the final release sequence, in order, when preparing to ship a robust, well-written, well-documented, stable, secure, and feature-complete project.

# General Use Guidance

1. Use **Periodic Maintenance Audit** when you want a quick but useful health check.
2. Use **Periodic Project Sync Check** after recent code, documentation, packaging, or release work.
3. Use **Focused Approved Fix Execution Prompt** only after a review identifies specific fixes you want implemented.
4. Use **Final Release Validation Sequence** in order when preparing a serious release.
5. Unless a prompt explicitly asks for implementation, reviews should identify issues first and avoid making changes.
6. When using modern LLMs, avoid redundant review passes. Prefer one clear pass per purpose, then an approved implementation pass.
7. Preserve existing behavior and public contracts unless a change is necessary to fix a bug, security issue, correctness issue, or clear inconsistency.
8. If a breaking change appears necessary, flag it explicitly before recommending or making it.

# Finding Labeling Convention

Use this convention in every review, audit, validation, sync, and execution prompt in this document.

Label every item for consideration, remediation, follow-up, or decision with a stable, easy-to-reference ID. The goal is to make follow-up discussion precise, so later recommendations should say `S4: Add a limitations note...` rather than referring to an unlabeled bullet that the user must search for.

For standalone prompts, use simple labels such as `S1`, `D2`, or `T3`.

For the **Final Release Validation Sequence**, prefix every generated label with the part number so IDs remain unique across separate prompt runs. Use this form:

```text
P<part number>-<category><number>
```

Examples:

1. `P1-A1` for the first artifact or synchronization issue found in Part 1
2. `P2-S1` for the first security issue found in Part 2
3. `P3-T4` for the fourth test issue found in Part 3
4. `P4-D2` for the second documentation issue found in Part 4
5. `P5-U3` for the third usability issue found in Part 5
6. `P6-R1` for the first regression or compatibility issue found in Part 6
7. `P7-X2` for the second approved implementation action made in Part 7
8. `P8-REL1` for the first final release decision, blocker, or checklist item in Part 8

Use the most specific applicable category prefix:

1. `B#` for bugs, correctness issues, broken assumptions, or behavior defects
2. `S#` for security, privacy, secrets, permissions, authentication, authorization, unsafe execution, unsafe file handling, unsafe serialization, dependency, or supply-chain issues
3. `E#` for edge cases, invalid inputs, error handling, recovery, cleanup, resource leaks, idempotency, reentrancy, or concurrency issues
4. `R#` for regressions, backward compatibility, public contract, migration, or integration risks
5. `T#` for tests, fixtures, test utilities, coverage gaps, brittle tests, or CI test issues
6. `D#` for documentation, examples, specifications, README, help text, user guidance, or terminology issues
7. `A#` for artifact synchronization, build files, packaging metadata, version metadata, changelog, release notes, schemas, sample configs, golden files, or generated files
8. `F#` for feature completeness, missing workflows, incomplete implementation, out-of-scope behavior, or product fit issues
9. `U#` for usability, onboarding, developer experience, operator experience, confusing behavior, naming, defaults, or error message quality
10. `P#` for performance, resource usage, scaling, caching, or efficiency issues
11. `O#` for operations, deployment, observability, logging, monitoring, diagnostics, supportability, or runtime environment issues
12. `M#` for maintainability, architecture, duplication, internal clarity, code organization, or long-term support concerns
13. `Q#` for open questions, ambiguities, assumptions to verify, or decisions needed from the user
14. `X#` for approved implementation actions or concrete changes made during an execution prompt
15. `REL#` for release blockers, release-readiness decisions, go/no-go concerns, or final release checklist items

Number items sequentially within each category prefix across the response. Do not restart `S#`, `D#`, `T#`, or other labels in each subsection of the same response. If an item has subitems, use suffixes such as `S4.a` and `S4.b` for standalone prompts, or `P2-S4.a` and `P2-S4.b` for release-sequence prompts.

When summarizing, prioritizing, asking for approval, implementing fixes, or revisiting unresolved issues, preserve the original IDs exactly. If a later prompt repeats, confirms, refines, or supersedes an earlier issue, reference the earlier ID rather than creating an unrelated duplicate. For example:

1. Fix now: `P2-S1`, `P2-B2`, `P2-E3`
2. Document now, fix later: `P2-S4: Add a limitations note about key-name-only redaction.`
3. Defer: `P5-U2`, `P5-M1`
4. Implemented action: `P7-X2 resolves P4-D3 and P6-A1`

# Periodic Maintenance Audit

Please perform a focused periodic maintenance audit of the current project.

This is a cursory review, not a full release readiness review, redesign, large refactor, or broad implementation pass. Keep the scope narrow, practical, and behavior-preserving unless you identify a clear bug, security issue, correctness issue, or documentation drift.

Finding labeling requirement: Label every item for consideration, remediation, follow-up, or decision using the Finding Labeling Convention. Preserve those IDs in the final summary, next-action list, and any approval questions.

Please review the current project for:

1. Obvious bugs, correctness issues, or broken assumptions
2. Security, privacy, dependency, file handling, path handling, authentication, authorization, serialization, subprocess, network, secret management, or supply-chain concerns
3. Edge cases, invalid inputs, error handling gaps, cleanup issues, recovery paths, or resource leaks
4. Regression or backward compatibility risks in public APIs, CLI behavior, configuration, schemas, file formats, outputs, or user-facing behavior
5. Missing, weak, outdated, or stale tests for important behavior
6. Documentation drift between the implementation and README, user docs, API docs, CLI docs, examples, specifications, schemas, or operational notes
7. Stale build, packaging, deployment, version, changelog, release note, fixture, sample config, or golden file artifacts
8. Inconsistent naming, terminology, help text, UI copy, developer experience, or maintainability concerns
9. Any obvious opportunities for small, safe improvements that reduce risk or future maintenance burden

Do not make changes yet. First provide a concise audit summary with:

1. Overall project health
2. High-priority issues found, using item IDs
3. Medium- or low-priority issues found, using item IDs
4. Documentation or artifact drift found, using item IDs
5. Tests that should be added or updated, using item IDs
6. Security or compatibility concerns, using item IDs
7. Recommended next actions, clearly separated into:

   1. Fix now
   2. Consider soon
   3. Defer

For each issue, include:

1. ID
2. Title
3. Severity: LOW, MEDIUM, HIGH, or CRITICAL
4. Affected area
5. Why it matters
6. Recommended fix
7. Whether the fix appears safe for a patch release, minor release, or should wait

Preserve existing behavior and public contracts unless a change is necessary to fix a bug, security issue, correctness issue, or clear inconsistency. If any breaking change appears necessary, explicitly flag it before recommending it.

# Periodic Project Sync Check

Please perform a focused synchronization check of the current project.

This is not a broad audit or redesign. The purpose is to determine whether recent work has created drift between implementation, tests, documentation, examples, configuration, packaging, deployment files, and release artifacts.

Finding labeling requirement: Label every stale artifact, missing update, synchronization risk, question, or recommended action using the Finding Labeling Convention. Preserve those IDs in the final summary and next-action list.

Please check whether recent changes require updates to:

1. Unit tests
2. Regression or contract tests
3. README.md
4. User documentation
5. API documentation
6. CLI documentation
7. Operational or deployment documentation
8. Architecture documentation
9. Functional specification
10. Examples or sample usage
11. Schemas, sample configs, fixtures, or golden files
12. Build files
13. Packaging metadata
14. Deployment configuration
15. Version metadata
16. CHANGELOG.md or release notes
17. CLI help text, UI copy, API descriptions, or entry points
18. Markdown navigation bars at the top and bottom of relevant Markdown files

Requirements:

1. Keep the pass narrow and practical.
2. Focus on synchronization, completeness, and obvious omissions.
3. If something is already correct, say so.
4. If something appears stale, inconsistent, or missing, call it out clearly with an ID.
5. Do not broaden this into unrelated cleanup.
6. Do not make changes unless explicitly asked.

At the end, provide:

1. Artifacts reviewed with no change needed
2. Artifacts that appear stale or incomplete, using item IDs
3. Artifacts likely needing updates, using item IDs
4. Any drift risks that remain, using item IDs
5. Recommended next actions, using item IDs

# Focused Approved Fix Execution Prompt

Use this only after a review has identified specific issues and you want the assistant to make changes.

Please implement the approved fixes from the prior review.

Before making changes, briefly restate the exact scope in 3 to 6 bullets, including what must not change.

Finding labeling requirement: Reference the approved source IDs from the prior review. Label each concrete change made as `X#`, and include the source issue ID it addresses, such as `X2 resolves S4`. Preserve both the source IDs and change IDs in the final summary.

Execution rules:

1. Make small, targeted, reviewable changes.
2. Preserve existing behavior and public contracts unless a change is explicitly approved or required to fix a bug, security issue, correctness issue, or clear inconsistency.
3. Do not introduce unnecessary dependencies, tools, frameworks, or services.
4. Keep code, tests, documentation, examples, specifications, schemas, build files, packaging files, deployment files, and release artifacts synchronized.
5. Do not remove comments, docstrings, examples, or tests unless they are incorrect, obsolete, duplicated, or actively harmful.
6. If a breaking change is unavoidable, clearly flag it and explain:

   1. What changed
   2. Why it is necessary
   3. What users or downstream systems must do to adapt
7. Preserve or restore Markdown navigation bars at the top and bottom of every relevant Markdown file, adapting links as needed for the file location.
8. Do not broaden the work into unrelated cleanup.
9. Prefer the smallest safe change that fixes the issue.

After implementation, provide:

1. Summary of changes made, using `P7-X#` IDs and source review IDs
2. Tests run and results
3. Artifacts updated, using `P7-X#` IDs where applicable
4. Artifacts reviewed with no change needed
5. Remaining risks or open concerns, using item IDs
6. Follow-up work to consider, using item IDs
7. Final artifact sync checklist

# Final Release Validation Sequence

Run the following prompts in order when preparing a project for a serious release. These prompts are intentionally more rigorous than the periodic checks. They are designed to reduce bugs, close documentation gaps, validate feature completeness, catch security and compatibility issues, and ensure the project is ready to ship.

Each part should be copied and run separately. Preserve the item IDs generated by each part so later prompts can refer back to them. In this sequence, every newly generated ID must include the part prefix, such as `P2-S1` or `P4-D3`. When a later part repeats, confirms, refines, or supersedes an earlier issue, reference the earlier ID rather than creating an unrelated duplicate.

## 1 of 8 Reconcile Current State

Please examine the current project as it exists now and reconcile its real current state before recommending or making changes.

Assume relevant work may already have happened through prior conversation, manual edits, tool runs, local experimentation, build runs, or test runs.

Finding labeling requirement: Because this is Part 1 of 8, label every drift item, ambiguity, artifact concern, release concern, question, and recommended next action with a `P1-` prefix using the Finding Labeling Convention, such as `P1-A1`, `P1-Q1`, or `P1-REL1`. Preserve those IDs in the final summary and recommended next actions.

Do not make changes yet. First provide a concise current-state assessment.

Please determine:

1. What the project currently does
2. The likely public contract, including APIs, CLIs, schemas, file formats, configuration, outputs, or user-facing behavior
3. What tests exist now
4. What docs and specs exist now
5. What build, packaging, deployment, and release artifacts exist now
6. What appears to have changed recently
7. Any obvious drift between implementation, tests, docs, examples, schemas, build files, packaging files, deployment files, changelog, or release notes

Please provide:

1. Current project state summary
2. Likely project type and scope
3. Public contract summary
4. Existing artifact summary
5. Drift or inconsistencies found, using item IDs
6. Key ambiguities to resolve, using item IDs
7. Release-quality concerns already visible, using item IDs
8. Recommended next actions, using item IDs

## 2 of 8 Quality, Security, and Edge Case Audit

Please review the current project for bugs, correctness issues, security concerns, edge cases, reliability risks, maintainability risks, and resource handling problems.

This is a review pass. Do not make changes yet. First produce a prioritized assessment.

Finding labeling requirement: Because this is Part 2 of 8, label every issue, remediation candidate, test need, question, and recommended next action with a `P2-` prefix using the Finding Labeling Convention. Security items must use IDs such as `P2-S1`; edge case, error handling, cleanup, or recovery items must use IDs such as `P2-E1`; bugs and correctness issues must use IDs such as `P2-B1`. Preserve all IDs in summaries and approval questions.

Please review for:

1. Bugs or correctness issues
2. Security issues
3. Privacy or data handling issues
4. Unsafe file handling or path handling
5. Unsafe serialization or deserialization
6. Unsafe subprocess, shell, or network behavior
7. Authentication or authorization gaps
8. Secret management issues
9. Dependency or supply-chain concerns
10. Input validation gaps
11. Edge cases and boundary conditions
12. Error handling and recovery gaps
13. Cleanup issues or resource leaks
14. Concurrency, state, caching, race condition, reentrancy, or idempotency risks
15. Performance or resource usage issues that can be improved without changing intended behavior
16. Logging, observability, and diagnosability gaps that materially affect supportability
17. Missing or weak tests for important behavior

For each issue found, provide:

1. ID
2. Title
3. Severity: LOW, MEDIUM, HIGH, or CRITICAL
4. Affected area
5. Explanation of the issue
6. Likely user, operator, developer, or business impact
7. Recommended fix
8. Whether the fix is safe for a patch release, minor release, or should wait

At the end, provide:

1. Highest-priority fixes, using item IDs
2. Security concerns, using item IDs
3. Edge cases that need test coverage, using item IDs
4. Reliability or maintainability concerns, using item IDs
5. Recommended next actions, using item IDs

## 3 of 8 Test Coverage and Regression Protection Review

Please review the current project's tests and identify gaps that create risk for bugs, regressions, or unsupported future changes.

This is a review pass. Do not add or change tests yet unless explicitly asked.

Finding labeling requirement: Because this is Part 3 of 8, label every test gap, brittle test, missing fixture, CI concern, regression concern, question, and recommended next action with a `P3-` prefix using the Finding Labeling Convention. Test items must use IDs such as `P3-T1`; compatibility and regression items must use IDs such as `P3-R1`. Preserve all IDs in summaries and approval questions.

Please examine:

1. Existing test structure
2. Unit tests
3. Regression tests
4. Contract tests for public behavior
5. Integration tests
6. End-to-end tests, if applicable
7. Fixtures and sample inputs
8. Golden files or expected outputs
9. Test helpers and utilities
10. CI or automated test configuration

Please assess whether the tests cover:

1. Normal behavior
2. Invalid inputs
3. Edge cases
4. Exceptions and error handling
5. Configuration behavior
6. Command-line behavior and exit semantics
7. API behavior and contract expectations
8. Serialization, deserialization, or file output behavior
9. Database or storage behavior
10. Important user workflows
11. Backward compatibility
12. Recently changed behavior
13. Security-relevant behavior
14. Failure and recovery behavior

Please provide:

1. Current test health summary
2. Critical behavior that is well covered
3. Critical behavior that is not well covered, using item IDs
4. Missing regression tests, using item IDs
5. Brittle, low-value, or misleading tests, using item IDs
6. Highest-value tests to add next, using item IDs
7. Whether any missing tests should block release, using item IDs

## 4 of 8 Documentation, Specification, and Example Review

Please review the current project documentation, specifications, and examples for accuracy, completeness, consistency, and usefulness.

The documentation and specifications must reflect actual current behavior, not hoped-for or planned behavior.

Finding labeling requirement: Because this is Part 4 of 8, label every documentation issue, example issue, specification issue, terminology issue, help text issue, question, and recommended next action with a `P4-` prefix using the Finding Labeling Convention. Documentation, example, and specification items should generally use IDs such as `P4-D1`; artifact sync items should use IDs such as `P4-A1`. Preserve all IDs in summaries and approval questions.

Please review, where applicable:

1. README.md
2. User guides
3. API documentation
4. CLI documentation
5. Architecture documentation
6. Configuration documentation
7. Schema or data contract documentation
8. Functional specification
9. Operational or deployment documentation
10. Examples or sample usage
11. Installation instructions
12. Build instructions
13. Packaging or release notes
14. Known limitations
15. Migration or compatibility notes
16. Markdown navigation bars at the top and bottom of relevant Markdown files

Please check for:

1. Outdated claims
2. Missing setup or usage steps
3. Broken or stale examples
4. Terminology inconsistencies
5. Missing limitations or assumptions
6. Missing configuration details
7. Missing security, privacy, or operational notes
8. Mismatch between documented behavior and implemented behavior
9. Mismatch between specification and implementation
10. Areas where a new user, developer, or operator would likely get stuck
11. Implemented behavior that is undocumented
12. Documented behavior that is not implemented
13. Partially implemented behavior that is not clearly labeled as partial or future work

Please provide:

1. Documentation health summary
2. Specification health summary
3. Major inaccuracies, using item IDs
4. Missing or weak documentation, using item IDs
5. Examples that need correction, using item IDs
6. Documentation that appears accurate as-is
7. Documentation or specification updates required before release, using item IDs
8. Recommended updates, grouped by priority and using item IDs

## 5 of 8 Feature Completeness, Usability, and Maintainability Review

Please review the project for feature completeness, usability, developer experience, operator experience, maintainability, onboarding quality, and practical future improvements.

The goal is not to invent unnecessary features. The goal is to determine whether the project feels complete, coherent, useful, maintainable, and ready for its intended audience.

Finding labeling requirement: Because this is Part 5 of 8, label every feature gap, usability issue, onboarding concern, maintainability concern, question, and recommended next action with a `P5-` prefix using the Finding Labeling Convention. Feature items must use IDs such as `P5-F1`; usability and operator/developer experience items should use IDs such as `P5-U1`; maintainability items should use IDs such as `P5-M1`. Preserve all IDs in summaries and approval questions.

Please assess:

1. What the project appears intended to do
2. What core workflows are implemented
3. What core workflows appear incomplete
4. What documented features are missing or only partially implemented
5. What implemented features are undocumented
6. What user needs appear implied but unsupported
7. What operational or developer needs appear implied but unsupported
8. API ergonomics and discoverability
9. Naming clarity and consistency
10. CLI, UI, or workflow usability
11. Defaults, help text, and error messages
12. Installation and setup clarity
13. Build and packaging clarity
14. Onboarding clarity for new users, developers, or operators
15. README usefulness for first-time users
16. Configuration clarity
17. Error handling from the user or operator perspective
18. Maintainability from the contributor perspective
19. Places where current behavior may be technically correct but awkward, confusing, or fragile
20. Features or refinements likely required before a robust release
21. Features that would be useful but should not block release

Please categorize findings as:

1. Required for release
2. Strongly recommended soon
3. Nice to have later
4. Should be explicitly out of scope

For each item, include:

1. ID
2. Title
3. Affected area
4. Why it matters
5. Recommended action
6. Whether it changes public behavior
7. Whether it needs documentation, tests, examples, specs, schemas, changelog, release notes, packaging, deployment updates, or none

At the end, provide recommended next actions using item IDs.

## 6 of 8 Compatibility, Packaging, and Release Artifact Review

Please review the current project for compatibility, packaging, build, deployment, versioning, changelog, and release artifact readiness.

Focus on whether the project can be safely shipped without breaking existing users, integrations, automation, documentation, workflows, or assumptions.

Finding labeling requirement: Because this is Part 6 of 8, label every compatibility risk, regression risk, packaging issue, build issue, deployment issue, versioning issue, changelog issue, migration concern, question, and recommended next action with a `P6-` prefix using the Finding Labeling Convention. Compatibility and regression items should use IDs such as `P6-R1`; artifact items should use IDs such as `P6-A1`; operations and deployment items should use IDs such as `P6-O1`. Preserve all IDs in summaries and approval questions.

Please review:

1. Public API behavior
2. CLI commands, flags, outputs, and exit behavior
3. UI behavior, if relevant
4. Configuration files
5. Environment variables
6. Defaults and precedence rules
7. Schemas
8. Serialized outputs
9. Messages or file formats
10. Logging behavior
11. Error handling behavior
12. Existing callers, scripts, integrations, or workflows
13. Platform compatibility
14. Dependency assumptions
15. Database, storage, or migration compatibility
16. Build files
17. Packaging metadata
18. Deployment configuration
19. Installation or first-run behavior
20. Version metadata
21. CHANGELOG.md or release notes
22. Migration guidance, if relevant
23. Documentation accuracy after recent changes
24. Tests that should be added or updated

Please provide:

1. Confirmed regressions, using item IDs
2. Plausible regression risks, using item IDs
3. Backward compatibility risks, using item IDs
4. Packaging or build risks, using item IDs
5. Deployment or operational risks, using item IDs
6. Missing regression tests, using item IDs
7. Versioning, changelog, or migration concerns, using item IDs
8. Recommended mitigations, using item IDs
9. Any breaking changes that need explicit release notes or migration guidance, using item IDs

Do not make changes yet. If fixes are later approved, make only the smallest safe adjustments required to reduce release risk.

## 7 of 8 Approved Release Hardening Fixes

Use this only after the prior release validation reviews identify specific fixes and you want the assistant to implement them.

Please implement the approved release hardening fixes from the prior reviews.

Before making changes, briefly restate the exact scope in 3 to 6 bullets, including what must not change.

Finding labeling requirement: Because this is Part 7 of 8, reference the approved source IDs from the prior release validation parts. Label each concrete change made with a `P7-X#` ID, and include the source issue ID it addresses, such as `P7-X3 resolves P4-D7`. Preserve both source IDs and change IDs in the final summary.

Execution rules:

1. Make small, targeted, reviewable changes.
2. Preserve existing behavior and public contracts unless a change is explicitly approved or required to fix a bug, security issue, correctness issue, or clear inconsistency.
3. Do not introduce unnecessary dependencies, tools, frameworks, or services.
4. Keep code, tests, documentation, examples, specifications, schemas, build files, packaging files, deployment files, and release artifacts synchronized.
5. Do not remove comments, docstrings, examples, or tests unless they are incorrect, obsolete, duplicated, or actively harmful.
6. If a breaking change is unavoidable, clearly flag it and explain:

   1. What changed
   2. Why it is necessary
   3. What users or downstream systems must do to adapt
7. Preserve or restore Markdown navigation bars at the top and bottom of every relevant Markdown file, adapting links as needed for the file location.
8. Do not broaden the work into unrelated cleanup.
9. Prefer the smallest safe change that fixes the issue.

After implementation, provide:

1. Summary of changes made, using `P7-X#` IDs and source review IDs
2. Tests run and results
3. Artifacts updated, using `P7-X#` IDs where applicable
4. Artifacts reviewed with no change needed
5. Remaining risks or open concerns, using item IDs
6. Follow-up work to consider, using item IDs
7. Final artifact sync checklist

## 8 of 8 Final Ship Review

Please assess whether the current project is ready to ship as a robust, well-written, well-documented, stable, secure, maintainable, feature-complete project for its intended scope.

Be practical but conservative. The goal is not to claim perfection. The goal is to determine whether the project is as close to bug-free as reasonably possible, has the right features for its intended release, and is documented and tested well enough to support real users.

Finding labeling requirement: Because this is Part 8 of 8, label every remaining blocker, risk, limitation, release decision, checklist item, question, and post-release follow-up with a `P8-` prefix using the Finding Labeling Convention. Release blockers and final release decisions should use IDs such as `P8-REL1`. Preserve all earlier IDs when referring to unresolved items from prior parts.

Please perform a thorough final release readiness review covering:

1. Project purpose and scope
2. Feature completeness for the intended release
3. Correctness of core behavior
4. Stability and reliability
5. Security and privacy posture
6. Edge cases and error handling
7. Performance and resource usage
8. Test coverage for critical paths
9. Regression protection for public behavior
10. Documentation accuracy and completeness
11. Functional specification accuracy and completeness
12. Examples and sample usage
13. API, CLI, UI, configuration, schema, storage, and integration consistency
14. Packaging and build readiness
15. Deployment and operational readiness
16. Installation and first-run experience
17. Versioning, changelog, and release note readiness
18. Backward compatibility and migration concerns
19. Developer experience and maintainability
20. Operator experience and diagnosability
21. User-facing rough edges
22. Known limitations and whether they are documented
23. Any missing work that should block release

Please categorize all findings as:

1. Must fix before release
2. Should fix before release if time allows
3. Acceptable known limitation if documented
4. Nice to have after release

For each finding, include:

1. ID
2. Title
3. Severity: LOW, MEDIUM, HIGH, or CRITICAL
4. Affected area
5. Why it matters
6. Recommended fix
7. Whether it affects users, operators, developers, integrations, or maintainers
8. Whether it changes public behavior
9. Required artifact updates
10. Whether it blocks release

Please also provide:

1. Summary of what appears release-ready
2. Summary of what is not release-ready, using item IDs
3. Feature completeness assessment, using item IDs where applicable
4. Documentation readiness assessment, using item IDs where applicable
5. Test readiness assessment, using item IDs where applicable
6. Security readiness assessment, using item IDs where applicable
7. Packaging and deployment readiness assessment, using item IDs where applicable
8. GO, CONDITIONAL GO, or NO-GO recommendation, labeled as `P8-REL#`
9. Concrete release checklist, using item IDs
10. Concrete post-release follow-up list, using item IDs

Do not make changes yet. First provide the release readiness assessment.

