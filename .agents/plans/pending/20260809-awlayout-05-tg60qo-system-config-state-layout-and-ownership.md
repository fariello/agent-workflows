# IPD: System, config, state layout and ownership

- Date: 2026-08-09
- Kind: child
- Concern: Materialize the new logical layout and enforce ownership boundaries during install and update.
- Scope: `agent_workflows/project_layout.py`, layout integration in `agent_workflows/engine.py`, `agent_workflows/manifest.py`, `agent_workflows/_compat.py`, packaged layout assets, and `tests/test_project_layout.py`.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 5
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: tg60qo

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L5-01 [HIGH] (asserts a transactional installer with rollback that does NOT exist - only per-file backup + a separate `--undo`; restate the recovery mechanism or build staging+pivot). L5-02 [HIGH] (V-items for atomicity/ownership name outcomes but no concrete fixture/oracle; add per-root sentinel-byte assertions). L5-03 [HIGH] (human-owned `config/` no-clobber is asserted but not gated - a human value AW never wrote has no recorded hash; define the preserve/merge rule + test). L5-04 (state the manifest EXTENDS manifest.py, not a second ledger; bump SCHEMA_VERSION). L5-05 (manifest location vs the legacy DEFAULT_MANIFEST_RELPATH during transitional install). L5-06 (surface §17 drift-before-overwrite + provenance as a distinct behavior).

## Goal

Create a small, predictable physical hierarchy for CLI-owned system files, user policy, operational state, and routed records. Ensure update behavior can replace owned files while preserving human-controlled configuration and durable state.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Layout and ownership

- [ ] E-01 Implement a layout materializer that maps the four logical roots to the selected physical policy, creates only required directories, records schema versions, and omits a target `.aw/records/` directory for external backends.
  - Depends on: none
  - Expected outcome: fresh installs have a minimal hierarchy whose physical paths exactly match the resolved context.
  - Execution state: pending
- [ ] E-02 Separate CLI-owned manifests and transaction data under `system/` from editable policy under `config/` and operational facts under `state/`; enforce write ownership in engine operations.
  - Depends on: E-01
  - Expected outcome: updates can replace `system/` content but do not overwrite valid user configuration, actions, or history.
  - Execution state: pending
- [ ] E-03 Keep only required host adapters outside logical AW roots, document each adapter's host constraint in the manifest, and remove any redundant installed copy.
  - Depends on: E-02
  - Expected outcome: unavoidable host files remain thin entry points and the project repository is not polluted by duplicate AW content.
  - Execution state: pending

### Task group 2: Installer integration

- [ ] E-04 Wire validated wizard policy into install and update materialization, including dry run, idempotent re-entry, ownership-aware drift reporting, and rollback on failure.
  - Depends on: E-03
  - Expected outcome: the installer uses one context and one policy from confirmation through commit, with no partial hierarchy after failure.
  - Execution state: pending
- [ ] E-05 Add `tests/test_project_layout.py` and update affected engine, manifest, compatibility, package-data, install-footprint, and wheel tests for each delivery and records combination.
  - Depends on: E-04
  - Expected outcome: all supported layouts are packaged, installed, updated, and inspected consistently.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Installer mutations use transactions and manifests; new writes must participate in rollback.
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
- Under-scope: hierarchy, ownership, host adapters, transactions, dry run, drift, idempotence, and packaging are covered.

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
  - Required evidence: fresh-install tree snapshots cover each backend and prove external records do not create target `.aw/records/`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: ownership tests modify one file in each root and prove update replaces only managed `system/` content.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: install-footprint tests list every target-external adapter, its host reason, and the absence of redundant copies.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: dry-run, second-install, drift, cancellation, and injected-failure tests prove stable output and transactional rollback.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: focused, package-data, wheel, and full test suites pass from the built artifact as required by existing packaging tests.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: hierarchy creation and ownership enforcement must share the same transactional installer boundary.

STOP if Orders 01 through 04 are incomplete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
