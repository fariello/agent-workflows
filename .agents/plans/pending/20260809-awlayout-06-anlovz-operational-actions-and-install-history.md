# IPD: Operational actions and install history

- Date: 2026-08-09
- Kind: child
- Concern: Persist AW-specific actions as state, reconcile action generations across updates, and keep append-only install history separate from the current snapshot.
- Scope: `agent_workflows/actions.py`, the packaged action-definition catalog, action and history wiring in `agent_workflows/cli.py` and `agent_workflows/engine.py`, and `tests/test_actions.py`.
- Status: to-review
- Set: awlayout (AW project layout)
- Order: 6
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: anlovz

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): reconciled action ownership with D125's implemented attention projection and current plan lifecycle conventions.

## Goal

Represent AW operational follow-up as durable state rather than project records. Keep short human-facing IDs such as `setup-repo`, retain prior generations, and prevent repeated updates from creating a noisy sequence of duplicate tasks.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Action lifecycle

- [ ] E-01 Implement the versioned action document schema and atomic lifecycle moves among `state/actions/open`, `completed`, `dismissed`, and `superseded`, with immutable action ID and generation metadata.
  - Depends on: none
  - Expected outcome: action files are AW state, preserve resolution history, and never use an `aw-` filename prefix inside the AW-owned namespace.
  - Execution state: pending
- [ ] E-02 Implement `aw todo`, `aw show <id[@generation]>`, `aw complete <id>`, `aw dismiss <id>`, `aw reopen <id>`, and `aw history <id>` with confirmation, idempotence, stable machine output, and latest-open-generation resolution.
  - Depends on: E-01
  - Expected outcome: common commands stay short while explicit generation syntax remains available for inspection.
  - Execution state: pending
- [ ] E-03 Add a packaged action-definition catalog and update reconciliation rules: create only unmet actionable generations, preserve resolved history, supersede an obsolete open generation, and do nothing when an update needs no human attention.
  - Depends on: E-02
  - Expected outcome: the twelfth update does not recreate `setup-repo` or overwrite earlier resolution facts unless a new applicable generation is defined.
  - Execution state: pending

### Task group 2: Installation facts

- [ ] E-04 Persist an atomic current install snapshot and redacted append-only JSONL history under `state/`; fresh install opens `setup-repo`, and external records without observable durability may open `configure-durability`.
  - Depends on: E-03
  - Expected outcome: current facts, event history, and human actions remain separate, queryable concepts.
  - Execution state: pending
- [ ] E-05 Add `tests/test_actions.py` for lifecycle transitions, short and generation-qualified IDs, twelve sequential updates, catalog changes, interrupted writes, history append, redaction, fresh install, and no-op update.
  - Depends on: E-04
  - Expected outcome: action and install-history behavior is deterministic across repeated releases.
  - Execution state: pending

## Project conventions discovered (Step 0)

- State writes must be atomic and participate in installer rollback where they are part of installation.
- Human-readable Markdown actions may have front matter, but indexable facts must not depend on parsing prose.
- Machine output must remain stable and ANSI-free.
- Existing status commands should consume shared APIs instead of reading files ad hoc.
- `aw todo` owns action writes and direct queries; cross-tree consumers use the read-only `aw attention` projection defined by D125.

## Findings

| Concept | Storage | Mutation model |
|---|---|---|
| Current installation | `state/install.json` | atomic replacement |
| Install events | `state/history/installs.jsonl` | append-only, redacted |
| Open action | `state/actions/open/<id>-vN.md` | lifecycle move |
| Resolved action | terminal lifecycle directory | retained evidence |

## Proposed changes (ordered, validatable)

1. Implement action persistence and lifecycle.
2. Add short CLI commands and explicit generation lookup.
3. Reconcile catalog generations during updates.
4. Separate snapshot, history, and initial actions.
5. Test long-lived update behavior and failures.

## Deferred / out of scope (with reason)

- D125 attention-source, `/whatnext`, and `/setup-repo` integration is Order 07.
- General project task management is excluded; these actions exist only for AW operation.
- Notifications and scheduled reminders are excluded; workflows surface actions on demand.

## Scope check

- Over-scope: no project task tracker, workflow edits, external notification, or record artifact storage.
- Under-scope: lifecycle, generations, commands, catalog reconciliation, install facts, initial actions, redaction, and repeated updates are covered.

## Required tests / validation

- `python3 -m unittest tests.test_actions -v`
- `python3 -m unittest discover -s tests -v`
- `python3 -m agent_workflows todo --json`

## Spec / documentation sync

- Keep action names, lifecycle directories, generation rules, and history fields aligned with the canonical 2026-08-09 layout specification.
- Do not add `aw-` prefixes to action filenames or require them in normal CLI input.
- Keep direct action ownership separate from the read-only attention projection; this plan does not modify D125 mappings or `/whatnext`.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: lifecycle tests prove atomic moves, immutable ID and generation, retained terminal history, and correct filenames.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: command tests cover every required verb, short IDs, `id@generation`, ambiguity, confirmation rejection, idempotence, and ANSI-free machine output.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: catalog fixtures prove no duplicate open action, correct supersession, new applicable generation, and no-op update behavior.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: install tests prove snapshot replacement, ordered history append, secret redaction, fresh `setup-repo`, and conditional durability action.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the twelve-update scenario and focused and full suites pass with no lost or recreated resolved action.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: action reconciliation depends directly on install events and must use one atomic state contract.

STOP if Orders 01, 02, or 05 are incomplete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
