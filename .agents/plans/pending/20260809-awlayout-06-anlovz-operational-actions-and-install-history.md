# IPD: Operational actions and install history

- Date: 2026-08-09
- Kind: child
- Concern: Persist AW-specific actions as state, reconcile action generations across updates, and keep append-only install history separate from the current snapshot.
- Scope: `agent_workflows/actions.py`, the packaged action-definition catalog, action and history wiring in `agent_workflows/cli.py` and `agent_workflows/engine.py`, and `tests/test_actions.py`.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 6
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: anlovz

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): reconciled action ownership with D125's implemented attention projection and current plan lifecycle conventions.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L6-01 [Med-High] (action `(id,generation)` must exist in exactly one lifecycle dir; validate id charset; a move is one atomic rename leaving no duplicate). L6-02 [HIGH] (lifecycle 'atomic moves' + fresh-install action creation share the non-atomic install of L5-01; define ordering so install.json/installs.jsonl/action stay consistent on partial failure). L6-03 (state that superseded/history growth is intentionally unbounded per §12.6, or bound it). L6-04 (define the installs.jsonl redaction set + reuse the existing leak sanitizer, do not reinvent). L6-05 (resolve the `state` root ONLY via the Order 01 resolver, never a hardcoded path). L6-06/L6-07 (atomic append for JSONL; align the `todo` flag with §18 `--agent`, not `--json`).
- 2026-08-09 author revision (Codex GPT-5): addressed L6-01 through L6-07 by specifying lifecycle uniqueness and ID validation, binding state paths to the resolver, ordering state publication within Order 05's compensating transaction, defining locked atomic JSONL append and leak-sanitizer reuse, documenting unbounded history, and correcting the machine command to `--agent`.
- 2026-08-09 re-reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED (by the author). Verified against repo evidence that the author's revision RESOLVED every prior finding - H1-H7 and all L0/L1..L11 items - and introduced no new finding; the dependency DAG remains valid and the orchestrator/child dependency lines agree (Order 07 now correctly depends on 01,06). All 12 lint conforming at author + review-finalize. Readiness: GO - PENDING HUMAN APPROVAL, gated ONLY on the controlling spec 20260809-2211-01 being approved (still Status: to-review) before any child executes.

## Goal

Represent AW operational follow-up as durable state rather than project records. Keep short human-facing IDs such as `setup-repo`, retain prior generations, and prevent repeated updates from creating a noisy sequence of duplicate tasks.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Action lifecycle

- [ ] E-01 Resolve the `state` root only through Order 01, then implement the versioned action document schema and lifecycle moves among `open`, `completed`, `dismissed`, and `superseded`. Accept IDs matching `[a-z][a-z0-9]*(?:-[a-z0-9]+)*` and positive integer generations; enforce that each `(id, generation)` exists in exactly one lifecycle directory; perform a transition as one same-filesystem atomic rename and verify the source disappeared and no duplicate destination exists.
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

- [ ] E-04 Persist the current install snapshot by atomic replacement and append each complete JSONL line under a state lock using one `O_APPEND` write plus `fsync`. Within Order 05's transaction, stage the snapshot and initial actions, publish system/config changes first, atomically publish actions, publish `install.json` as authoritative state last, then append the completed event; on failure compensate published state and append a redacted failed event with the same transaction ID. Fresh install opens `setup-repo`, and external records without observable durability may open `configure-durability`.
  - Depends on: E-03
  - Expected outcome: current facts, event history, and human actions remain separate, queryable concepts.
  - Execution state: pending
- [ ] E-05 Add `tests/test_actions.py` for lifecycle transitions, short and generation-qualified IDs, twelve sequential updates, catalog changes, interrupted writes, history append, redaction, fresh install, and no-op update.
  - Depends on: E-04
  - Expected outcome: action and install-history behavior is deterministic across repeated releases.
  - Execution state: pending

## Project conventions discovered (Step 0)

- State writes must be atomic and participate in installer rollback where they are part of installation.
- All paths in this plan come from the resolved Order 01 `state` root. No fallback or hard-coded `.aw/state` path is permitted.
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

Action generations and `state/history/installs.jsonl` are intentionally unbounded historical evidence under Section 12.6. Compaction, retention limits, or archival require a separate decision.

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
- `python3 -m agent_workflows todo --agent`

## Spec / documentation sync

- Keep action names, lifecycle directories, generation rules, and history fields aligned with the canonical 2026-08-09 layout specification.
- Do not add `aw-` prefixes to action filenames or require them in normal CLI input.
- Keep direct action ownership separate from the read-only attention projection; this plan does not modify D125 mappings or `/whatnext`.
- Reuse `agent_workflows.local_leaks` for event-field validation and redaction. The forbidden event set is credentials and tokens, URL userinfo/query/fragment values, secret-like environment values, conversation or action bodies, record contents, raw command arguments that may contain secrets, and public-output machine identifiers. Do not create a separate regex catalog.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: lifecycle tests prove ID regex and positive-generation validation, exactly-one-directory uniqueness before and after every transition, same-filesystem atomic rename, immutable ID and generation, retained terminal history, source disappearance, duplicate refusal, and correct filenames.
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
  - Required evidence: failure injection at every Order 05 transaction boundary proves no action or successful snapshot survives a compensated failure; completed and failed events share the transaction identity and match actual outcome; concurrent append tests produce complete parseable lines with no loss; the existing leak sanitizer verifies the forbidden set; fresh `setup-repo` and conditional durability actions appear only after authoritative state publication.
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
