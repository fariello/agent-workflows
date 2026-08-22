# IPD: Compatibility Contract Migration Rollback and Deprecation

- Date: 2026-08-21
- Kind: child
- Concern: Ship the architecture without breaking existing invocations or losing recoverability.
- Scope: Compatibility contract for existing commands/shims/pointers/IPD locations + idempotent previewable migration/update + rollback + interrupted-recovery + opt-in privacy-preserving deprecation diagnostics. No docs/security/release-readiness (Order 18).
- Status: reviewed
- Set: awoptimize
- Order: 17
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: gnfkh8

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-08 E-01..E-04 into 5 right-sized E-items (compatibility contract, previewable idempotent migration, rollback+interrupted-recovery, opt-in deprecation diagnostics, tests); carries the compatibility-gates table + deprecation-window OQ.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Deps on 14-16 + 01-13 justified; never-remove-a-surface + never-push invariants airtight; migration MOVES/backs-up (D135). PR-001 (LOW, rubric C): the gate said "reuse the installer/engine.py migration primitives" but the migration/rollback engine is MigrationManager in layout_migration.py (engine.py holds install/layout resolution) - FIXED by naming layout_migration.py:MigrationManager (execute_migration/rollback_migration) for migration/rollback and engine.py for install, in both the conventions note and the scope fence. V-01..V-05 map 1:1 with falsifiable evidence. OQ-01 (deprecation window) non-blocking, two-release default.

## Goal

Move users from the manually maintained prose workflows to the canonical compiled packages WITHOUT
breaking existing invocations, and make every transition observable and reversible: freeze the public
compatibility contract, implement previewable idempotent migration/update, implement rollback +
interrupted-recovery, and add opt-in privacy-preserving deprecation diagnostics. Docs, security, and
the GO/NO-GO release-readiness gate are Order 18; this Order does not tag, publish, or remove any
compatibility surface.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: compatibility contract

- [ ] E-01 Define the compatibility contract for existing manifest commands, arguments, `.opencode/commands/`, `.claude/commands/`, AGENTS/CLAUDE/GEMINI pointers, IPD locations, `agy_run.py` entry points, exit codes, and machine output, as a machine-readable table (one row per surface) with owner, version boundary, migration, and test per entry.
  - Depends on: none
  - Expected outcome: the compatibility table has one row + a passing golden test for every named surface, with NO unspecified breaking change; each preserved/changed/deprecated/unsupported behavior is explicit.
  - Execution state: pending

### Task group 2: migration and rollback

- [ ] E-02 Implement idempotent, previewable migration/update logic that detects legacy, partial, current, drifted, and locally-customized states; previews changes, preserves user files, backs up replaced generated files, and records the exact compiler/adapter version.
  - Depends on: E-01
  - Expected outcome: legacy/current/partial/drift/customized fixtures preview exact changes, preserve human files, back up generated replacements, record versions, and rerun idempotently (a no-op when current); human-owned content is never silently overwritten.
  - Execution state: pending
- [ ] E-03 Implement rollback to the last compatible generated set + runtime state, including interrupted-migration recovery and an explicit warning when new-run data cannot be read by an older version (distinguish adapter rollback from data-schema downgrade).
  - Depends on: E-02
  - Expected outcome: rollback + interrupted-migration fixtures restore prior command discovery and runtime adapters without record loss, and warn rather than corrupt on unreadable future data.
  - Execution state: pending

### Task group 3: deprecation diagnostics

- [ ] E-04 Add deprecation diagnostics and LOCAL, privacy-preserving usage counters ONLY if approved; keep aliases until parity + adoption gates are met; telemetry is never required for operation and can be disabled/avoided completely.
  - Depends on: E-03
  - Expected outcome: diagnostics are local, opt-in if they count usage, disable cleanly, and CANNOT remove an alias before its parity/adoption/version gate; operation never depends on telemetry.
  - Execution state: pending

### Task group 4: tests

- [ ] E-05 Add `tests/test_compat_migration_rollback.py` (stdlib unittest): the compatibility-contract golden tests (one per surface, no unspecified break); the migration fixtures (legacy/current/partial/drift/customized: preview, preserve, backup, version-record, idempotent rerun); the rollback + interrupted-recovery + downgrade-warning fixtures; the deprecation-diagnostic opt-in/disable + no-early-alias-removal fixtures. Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: contract + migration + rollback + deprecation fixtures pass; the full serial suite is green (pasted).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Compatibility gates

| Surface | Preserve until | Removal authority |
|---|---|---|
| OpenCode command shims | generated parity plus two release cycles | separately approved release IPD |
| Claude command shims | skill/command parity plus two release cycles | separately approved release IPD |
| plan-review-long name | canonical alias usage and benchmark parity | maintainer approval |
| same-session agy audit | fresh verifier available and documented | may remain diagnostic indefinitely |
| static host matrix reader | all consumers migrated to evidence registry | schema migration review |
| legacy workflow bodies | canonical package parity and rollback bundle | per-family cutover gate |

This Order OWNS the compatibility contract + migration/rollback/deprecation MECHANICS; it never REMOVES a surface (removal is a separately approved release action, per the "Removal authority" column).

## Project conventions discovered (Step 0)

- Setup is designed to be idempotent, drift-aware, and ask before changes; existing host shims + user instruction pointers are part of the public repository interface.
- Migration MOVES/backs-up, never silently overwrites human-owned content (consistent with the repo's D135 move-not-copy migration posture).
- New runtime records (Orders 02/03/07 JSONL) may not be backward-readable by an older version; rollback must distinguish adapter rollback from data-schema downgrade and warn rather than corrupt.
- Pure/generation + install-engine module shape (stdlib-only, D138); reuse the existing migration/rollback primitives in `agent_workflows/layout_migration.py` (`MigrationManager.execute_migration`/`rollback_migration`, the journaled move-not-copy engine) and the install/layout resolution in `agent_workflows/engine.py` (`install_into_repo`/`resolve_target_layout`), rather than forking a new migration engine.

## Findings

| Finding | Consequence |
|---|---|
| Generated files may contain local edits despite ownership conventions. | Migration must detect drift and preserve/back-up or explicitly resolve it, never overwrite silently. |
| New runtime records may not be backward readable. | Rollback distinguishes adapter rollback from data-schema downgrade and warns on unreadable future data. |
| A compatibility surface could be removed prematurely. | Removal is gated by the compatibility-gates table's authority column; this Order never removes a surface. |

## Proposed changes (ordered, validatable)

1. Freeze the public compatibility contract (E-01).
2. Implement previewable idempotent migration/update (E-02).
3. Implement rollback + interrupted-state recovery + downgrade warning (E-03).
4. Add opt-in, privacy-preserving deprecation diagnostics (E-04).
5. Contract + migration + rollback + deprecation tests + full suite (E-05).

## Deferred / out of scope (with reason)

- Operator/author/security DOCUMENTATION, security hardening, lifecycle matrix fixtures, and the GO/NO-GO release-readiness review: Order 18.
- Actual tag/release/publish/deploy/push: a separately approved release action (never here).
- REMOVING any compatibility surface: deferred to the named adoption boundary + its removal authority.
- Central telemetry collection: out unless separately specified + privacy-reviewed.

## Scope check

- Over-scope: no release mutation, external publishing, forced deletion, docs/security/release-readiness (Order 18).
- Under-scope: none - the compatibility contract, previewable idempotent migration, rollback + recovery, and opt-in deprecation diagnostics are covered; Order 18 owns docs + validation + the release gate.

## Required tests / validation

- `tests/test_compat_migration_rollback.py`: compatibility-contract golden tests (one per surface, no unspecified break); migration fixtures (legacy/current/partial/drift/customized -> preview, preserve, backup, version-record, idempotent rerun); rollback + interrupted-recovery + downgrade-warning; deprecation opt-in/disable + no-early-alias-removal.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Publish the compatibility contract table + the migration/rollback/deprecation behavior. (The full operator/architecture/security docs are Order 18.)

## Open questions

### OQ-01: Deprecation duration and supported version window?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Adopt a MINIMUM two-release compatibility window (matching the compatibility-gates table's "plus two release cycles") unless release cadence or usage evidence justifies longer; record the decision before publishing any deprecation dates. Non-blocking: this Order builds the deprecation-diagnostic mechanism and keeps aliases; the exact window is a maintainer policy set before deprecation dates are published, and does not change this Order's interfaces.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted golden-test output showing the machine-readable compatibility table has one row + passing test for every named surface, with no unspecified breaking change.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted fixtures for legacy/current/partial/drift/customized states previewing exact changes, preserving human files, backing up generated replacements, recording versions, and rerunning idempotently (no-op when current).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted rollback + interrupted-migration fixtures restoring prior command discovery + runtime adapters without record loss, and warning (not corrupting) on unreadable future data.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted test output showing deprecation diagnostics are local + opt-in + cleanly disable-able, operation never requires telemetry, and an alias cannot be removed before its parity/adoption/version gate.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `tests/test_compat_migration_rollback.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Orders 14-16 (the migration this compatibility layer preserves/rolls back) plus Orders 01-13 upstream. Scope fence: touch only the compatibility-contract + migration/update + rollback + deprecation-diagnostic modules (reuse `agent_workflows/layout_migration.py`'s `MigrationManager` for migration/rollback and `agent_workflows/engine.py` for install/layout resolution; do not fork a new engine) and `tests/test_compat_migration_rollback.py`; do NOT write the operator/security docs or run the release-readiness review (Order 18), REMOVE any compatibility surface, or tag/publish/push - if it seems to need more, STOP and report. Never silently overwrite human-owned content; rollback must not lose records; a surface is removed only via its documented removal authority (a separate approved release action). Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
