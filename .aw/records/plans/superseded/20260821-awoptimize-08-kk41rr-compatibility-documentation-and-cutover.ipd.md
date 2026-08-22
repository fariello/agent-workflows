RETIRED 2026-08-21: superseded by the awoptimize re-scope (right-sizing into smaller child IPDs; see the re-scope proposal and DECISIONS). This old Order is resplit into new Orders 17, 18.

# IPD: Compatibility Documentation and Cutover

- Date: 2026-08-21
- Kind: child
- Concern: Ship the architecture safely with truthful documentation, reversible migration, validated compatibility, and explicit release gates.
- Scope: Compatibility contract, migration tooling, operator/user docs, security and failure runbooks, deprecation telemetry, clean-install/update/rollback tests, release notes, and cutover. No release, tag, push, or deployment.
- Status: superseded
- Set: awoptimize
- Order: 8
- Highest E allocated: 09
- Author: Codex GPT-5.6 Sol
- Id: kk41rr

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created as the final rollout and truthfulness gate for the architecture Set.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Compatibility contract, idempotent/previewable migration, rollback + interrupted-recovery, opt-in privacy-preserving deprecation telemetry, and an explicit GO/NO-GO release-readiness review that does NOT tag/publish/push are all present and honest. The compatibility-gates table (preserve-until / removal-authority per surface) is a strong safety fence. Canonical full-suite evidence command pinned to `make test`. Size assessment standard (correct). OQ-01 (deprecation window) is non-blocking with a sensible two-release default. This Order sequences last, after Orders 01-07.

## Goal

Move users from manually maintained prose workflows to canonical compiled packages without breaking existing invocations or overstating host/model support. Every transition must be observable, reversible, documented, and blocked by clean-install, update, rollback, security, and behavioral evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Compatibility and migration

- [ ] E-01 Define the compatibility contract for existing manifest commands, arguments, `.opencode/commands/`, `.claude/commands/`, AGENTS/CLAUDE/GEMINI pointers, IPD locations, `agy_run.py` entry points, exit codes, and machine output.
  - Depends on: none
  - Expected outcome: each preserved, changed, deprecated, or unsupported behavior has an owner, version boundary, migration, and test.
  - Execution state: pending
- [ ] E-02 Implement idempotent migration and update logic that detects legacy, partial, current, drifted, and locally customized states; preview changes, preserve user files, back up replaced generated files, and record the exact compiler/adaptor version.
  - Depends on: E-01
  - Expected outcome: reruns are no-ops when current and never silently overwrite human-owned content.
  - Execution state: pending
- [ ] E-03 Implement rollback to the last compatible generated set and runtime state, including interrupted-migration recovery and an explicit warning when new-run data cannot be read by an older version.
  - Depends on: E-02
  - Expected outcome: failed cutover can return command discovery and workflow execution to the prior known-good state without losing records.
  - Execution state: pending
- [ ] E-04 Add deprecation diagnostics and local, privacy-preserving usage counters only if approved; keep aliases until parity and adoption gates are met and never require telemetry for operation.
  - Depends on: E-03
  - Expected outcome: removal decisions use evidence while users can disable or avoid telemetry completely.
  - Execution state: pending

### Documentation, security, and release gate

- [ ] E-05 Write architecture, authoring, skill-selection, orchestration, evidence, verification, benchmark, host-adapter, troubleshooting, recovery, and security documentation with exact commands, outputs, limitations, and responsibility boundaries.
  - Depends on: E-04
  - Expected outcome: operators can explain why a run is incomplete, reproduce evidence, rerun probes, and recover without reading implementation internals.
  - Execution state: pending
- [ ] E-06 Document model profiles as evidence-backed defaults, not universal personality claims; distinguish model ID from reasoning configuration and list benchmark date, task corpus, host, version, thresholds, and pending combinations.
  - Depends on: E-05
  - Expected outcome: no documentation turns vendor marketing or one observed rollout into a general quality guarantee.
  - Execution state: pending
- [ ] E-07 Harden security boundaries: local servers loopback/authenticated, external files consented and contained, skills least-privilege, evidence redacted, real HOME excluded from probes, untrusted repository text isolated, and destructive tools human-gated.
  - Depends on: E-06
  - Expected outcome: threat-model tests and runbooks cover the new execution and host-integration attack surface.
  - Execution state: pending
- [ ] E-08 Execute clean-install, legacy-update, partial-state, customized-file, interrupted-update, rollback, downgrade-warning, no-network, no-credential, multi-host discovery, and unsupported-host fixtures.
  - Depends on: E-07
  - Expected outcome: setup is repeatable, drift-aware, and fail-closed across supported layouts.
  - Execution state: pending
- [ ] E-09 Perform final release-readiness review: full suite, leak scan, IPD lint, generated drift, docs checks, complete workflow disposition, capability evidence freshness, benchmark thresholds, changelog, versioning, artifact manifest, and residual-risk sign-off.
  - Depends on: E-08
  - Expected outcome: produces a GO/NO-GO report but does not tag, publish, deploy, or push.
  - Execution state: pending

## Compatibility gates

| Surface | Preserve until | Removal authority |
|---|---|---|
| OpenCode command shims | generated parity plus two release cycles | separately approved release IPD |
| Claude command shims | skill/command parity plus two release cycles | separately approved release IPD |
| plan-review-long name | canonical alias usage and benchmark parity | maintainer approval |
| same-session agy audit | fresh verifier available and documented | may remain diagnostic indefinitely |
| static host matrix reader | all consumers migrated to evidence registry | schema migration review |
| legacy workflow bodies | canonical package parity and rollback bundle | per-family cutover gate |

## Project conventions discovered (Step 0)

- Setup is designed to be idempotent, drift-aware, and ask before changes.
- Clean-delta and skills support are already evidence-gated in project decisions.
- Existing host shims and user instruction pointers are part of the public repository interface.
- Release actions are distinct from release-note preparation and require separate authority.

## Findings

| Finding | Consequence |
|---|---|
| Generated files may contain local edits despite ownership conventions. | Migration must classify and preserve or explicitly resolve drift. |
| New runtime records may not be backward readable. | Rollback must distinguish adapter rollback from data-schema downgrade. |
| Host/model support becomes stale quickly. | Documentation must render from capability and benchmark registries with dates. |
| A green implementation suite does not prove clean update or rollback. | Matrix fixtures must cover lifecycle paths from real legacy states. |

## Proposed changes (ordered, validatable)

1. Freeze public compatibility promises.
2. Implement previewable idempotent migration.
3. Add rollback and interrupted-state recovery.
4. Add opt-in deprecation diagnostics.
5. Publish complete operator, author, security, and recovery guidance.
6. Validate clean and legacy lifecycle matrices.
7. Produce a release-readiness decision without releasing.

## Deferred / out of scope (with reason)

- Actual tag, release, package publish, deployment, or push requires a separately approved release action.
- Removing compatibility surfaces is deferred to the named adoption boundary.
- Central telemetry collection is out unless separately specified and privacy-reviewed.
- Unsupported host/model combinations remain documented as pending.

## Scope check

- Over-scope: no release mutation, external publishing, or forced deletion.
- Under-scope: compatibility, migration, rollback, documentation, security, lifecycle fixtures, and release-readiness are covered.

## Required tests / validation

- Compatibility contract golden tests for every listed surface.
- Fresh, update, partial, customized, interrupt, rollback, and downgrade fixtures.
- Documentation command/option/link validation and generated-table drift.
- Security tests for containment, symlink escape, untrusted instructions, permissions, authentication, and redaction.
- Full suite (canonical `make test`, i.e. parallel `pytest -n auto`; `make test-serial` only for isolation debugging), leak scan, IPD lint, workflow compiler drift, host probe freshness, benchmark gates, and residual audit.

## Spec / documentation sync

- This Order owns current-state architecture, migration, rollback, troubleshooting, security, support matrix, benchmark summary, changelog, and release-note consistency.
- All support and performance tables must be generated from their evidence registries.

## Open questions

### OQ-01: Deprecation duration and supported version window?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: adopt a minimum two-release compatibility window unless release cadence or usage evidence justifies longer; record the decision before publishing deprecation dates.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: machine-readable compatibility table has one row and passing golden test for every named surface, with no unspecified breaking change.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: legacy/current/partial/drift/customized fixtures preview exact changes, preserve human files, back up generated replacements, record versions, and rerun idempotently.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: rollback and interrupted-migration fixtures restore prior command discovery and runtime adapters without record loss and warn rather than corrupt on unreadable future data.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: diagnostics are local, opt-in if counting usage, privacy-reviewed, disable cleanly, and cannot remove an alias before its parity/adoption/version gate.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: documentation link/command/option checks pass and operator walkthroughs reproduce incomplete diagnosis, evidence inspection, host probe, recovery, and rollback from a clean fixture.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: model tables render exact IDs/configurations, task corpus, host/version, dates, thresholds, uncertainty, and pending cells from benchmark records with no unsupported generalization.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: threat-model tests prove loopback/auth, containment, consent, least privilege, redaction, real-HOME refusal, untrusted-text isolation, and human destructive gates.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: every named lifecycle fixture passes from a clean isolated environment, unsupported/no-credential cases fail before mutation, and reruns show no unmanaged drift.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: retained outputs show full suite, leak scan, all IPD lint phases, compiler drift, docs, disposition, claim freshness, benchmark and residual-risk gates pass; git evidence shows no tag, release, deploy, or push.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: compatibility, migration, rollback, docs, security, and cutover jointly determine whether the architecture can ship safely.

Requires executed Orders 01 through 07. This plan may produce a release-readiness decision but may not tag, publish, deploy, or push. Any destructive compatibility removal requires a new approved plan.

Execution contract: path-scoped commits, no broad staging or push, raw lifecycle evidence retained. Stop on user-owned drift, unreadable future data, stale capability proof, unmet benchmark gate, or unresolved critical security finding.
