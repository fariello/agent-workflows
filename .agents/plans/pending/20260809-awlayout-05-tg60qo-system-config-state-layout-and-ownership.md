# IPD: System, config, state layout and ownership

- Date: 2026-08-09
- Kind: child
- Concern: Materialize the new logical layout and enforce ownership boundaries during install and update.
- Scope: `agent_workflows/project_layout.py`, layout integration in `agent_workflows/engine.py`, `agent_workflows/manifest.py`, `agent_workflows/_compat.py`, packaged layout assets, and `tests/test_project_layout.py`.
- Status: approved
- Approval: 2026-08-09, human maintainer (approved the awlayout Set for execution after /plan-review re-review; spec 20260809-2211-01 approved)
- Set: awlayout (AW project layout)
- Order: 5
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: tg60qo

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L5-01 [HIGH] (asserts a transactional installer with rollback that does NOT exist - only per-file backup + a separate `--undo`; restate the recovery mechanism or build staging+pivot). L5-02 [HIGH] (V-items for atomicity/ownership name outcomes but no concrete fixture/oracle; add per-root sentinel-byte assertions). L5-03 [HIGH] (human-owned `config/` no-clobber is asserted but not gated - a human value AW never wrote has no recorded hash; define the preserve/merge rule + test). L5-04 (state the manifest EXTENDS manifest.py, not a second ledger; bump SCHEMA_VERSION). L5-05 (manifest location vs the legacy DEFAULT_MANIFEST_RELPATH during transitional install). L5-06 (surface §17 drift-before-overwrite + provenance as a distinct behavior).
- 2026-08-09 author revision (Codex GPT-5): addressed L5-01 through L5-06 by choosing a journaled compensating transaction built on existing backups and undo primitives, defining preserve-or-explicit-replace config semantics, extending and versioning the existing manifest, specifying transitional manifest authority, and adding sentinel-byte and drift-provenance oracles.
- 2026-08-09 re-reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED (by the author). Verified against repo evidence that the author's revision RESOLVED every prior finding - H1-H7 and all L0/L1..L11 items - and introduced no new finding; the dependency DAG remains valid and the orchestrator/child dependency lines agree (Order 07 now correctly depends on 01,06). All 12 lint conforming at author + review-finalize. Readiness: GO - PENDING HUMAN APPROVAL, gated ONLY on the controlling spec 20260809-2211-01 being approved (still Status: to-review) before any child executes.
- 2026-08-09 approved (human maintainer): Status reviewed -> approved; controlling spec approved; cleared for execution via ipd-lifecycle (execute in dependency order, per-child gates).

## Goal

Create a small, predictable physical hierarchy for CLI-owned system files, user policy, operational state, and routed records. Ensure update behavior can replace owned files while preserving human-controlled configuration and durable state.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Layout and ownership

- [ ] E-01 Implement a layout materializer that maps the four logical roots to the selected physical policy, creates only required directories, records schema versions, and omits a target `.aw/records/` directory for external backends.
  - Depends on: none
  - Expected outcome: fresh installs have a minimal hierarchy whose physical paths exactly match the resolved context.
  - Execution state: pending
- [ ] E-02 Separate CLI-owned manifests and transaction data under `system/` from editable policy under `config/` and operational facts under `state/`; extend `agent_workflows/manifest.py` and bump `SCHEMA_VERSION` rather than creating a second ledger. For `config/`, create a missing file from confirmed policy, preserve every existing valid file and unknown human value, merge only schema-owned fields after showing provenance and an explicit confirmed diff, and refuse malformed or conflicting content without `--replace-config` plus confirmation.
  - Depends on: E-01
  - Expected outcome: updates can replace `system/` content but do not overwrite valid user configuration, actions, or history.
  - Execution state: pending
- [ ] E-03 Keep only required host adapters outside logical AW roots, document each adapter's host constraint in the manifest, and remove any redundant installed copy.
  - Depends on: E-02
  - Expected outcome: unavoidable host files remain thin entry points and the project repository is not polluted by duplicate AW content.
  - Execution state: pending

### Task group 2: Installer integration

- [ ] E-04 Wire validated wizard policy into install and update materialization as a journaled compensating transaction: preflight and stage the complete operation list, write a transaction journal and per-file backups, use atomic replacement for each file, update the new manifest and authoritative state last, and automatically run the existing undo primitives in reverse order on failure. Report compensation failure without claiming atomicity or success; do not describe this cross-root mechanism as a filesystem-wide atomic pivot.
  - Depends on: E-03
  - Expected outcome: the installer uses one context and one policy from confirmation through commit, with no partial hierarchy after failure.
  - Execution state: pending
- [ ] E-05 Add `tests/test_project_layout.py` and update affected engine, manifest, compatibility, package-data, install-footprint, and wheel tests for each delivery and records combination.
  - Depends on: E-04
  - Expected outcome: all supported layouts are packaged, installed, updated, and inspected consistently.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The current installer provides per-file backups and a separate `--undo`, not a transaction boundary. This Order composes those primitives into an automatic journaled compensating transaction with an explicit partial-compensation failure state.
- Package-data tests protect shipped workflow and support assets.
- Compatibility logic is centralized and must not become a second path resolver.
- Host adapter placement is constrained by the host, not by AW's preferred hierarchy.

## Findings

| Root | Owner | Update rule |
|---|---|---|
| `system` | `aw` command | replace managed content after drift checks |
| `config` | user or team policy | preserve valid values; migrate explicitly |
| `state` | AW runtime and user action commands | reconcile atomically; never blanket-replace |
| `records` | workflows and user | route through backend; never treat as installed payload |

During transition, the existing `DEFAULT_MANIFEST_RELPATH` remains the discovery bootstrap. A successful transaction writes the bumped manifest at the resolved new system location, records the legacy manifest as migrated, switches authority only after verification, and retains a compatibility reader until Order 09 removes it. There is never more than one authoritative writer.

## Proposed changes (ordered, validatable)

1. Materialize the selected physical layout.
2. Encode and enforce ownership.
3. Minimize host-required external adapters.
4. Integrate the policy with installer transactions.
5. Update focused and packaging coverage.

## Deferred / out of scope (with reason)

- Legacy data migration is Order 09; this plan handles fresh materialization and same-layout update only.
- Action semantics and history records are Order 06.
- Producer workflow routing is Order 08.

## Scope check

- Over-scope: no legacy relocation, record content generation, clean-delta host gates, or action reconciliation.
- Under-scope: hierarchy, ownership, host adapters, journaled compensation, dry run, drift provenance, idempotence, and packaging are covered.

## Required tests / validation

- `python3 -m unittest tests.test_project_layout -v`
- `python3 -m unittest tests.test_engine tests.test_manifest tests.test_install_footprint tests.test_package_data -v`
- `python3 -m unittest discover -s tests -v`

## Spec / documentation sync

- Keep physical mappings and ownership rules aligned with the canonical 2026-08-09 layout specification.
- Update compatibility fixtures in the same change; defer user-facing current-state docs to Order 11.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: fresh-install tree snapshots cover each backend; unique sentinel bytes placed outside every intended root remain byte-identical; external records do not create target `.aw/records/`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: fixtures place unique sentinel bytes in managed `system`, never-managed `config`, AW-managed `state`, and user `records`; update replaces only the eligible system sentinel, preserves the other three byte-for-byte, preserves unknown valid config fields, rejects malformed or conflicting config, and changes config only after an explicit field-level confirmation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: install-footprint tests list every target-external adapter, its host reason, and the absence of redundant copies.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: dry-run, second-install, drift, cancellation, and failure injection after every mutation step prove a complete journal, reverse-order compensation, byte-identical sentinel restoration, authoritative-state-last ordering, and an honest non-success result if compensation itself fails. Drift output identifies each value's Section 17 provenance before overwrite.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: focused, manifest-schema migration, legacy bootstrap, package-data, wheel, and full test suites pass from the built artifact; exactly one manifest is authoritative after successful transition.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: hierarchy creation and ownership enforcement must share the same transactional installer boundary.

STOP if Orders 01 through 04 are incomplete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
