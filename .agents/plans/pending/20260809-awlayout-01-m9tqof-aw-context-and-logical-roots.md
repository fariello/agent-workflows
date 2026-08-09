# IPD: AW context and logical-root resolver

- Date: 2026-08-09
- Kind: child
- Concern: Define the shared project-context contract and resolve every logical AW root through one fail-closed API.
- Scope: `agent_workflows/project_schema.py`, `agent_workflows/project_context.py`, context-related CLI wiring in `agent_workflows/cli.py`, and `tests/test_project_context.py`.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 1
- Highest E allocated: 04
- Author: Codex (GPT-5, high reasoning)
- Id: m9tqof

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L1-01 (§9 resolver: `aw context` needs `--repo` + must return all ~11 §9 fields incl. permitted commit destinations + root accessibility; E-03/V-02 do not enumerate them). L1-02 (§17: bind to the 6-level precedence, conflicting authoritative sources are ERRORS not last-write-wins, and `--json` must report per-value provenance; V-02 tests only generic failure). L1-03 (test resolver PURITY/determinism + no Git mutation, not just 'no writes'). L1-04 (add path-traversal/symlink-escape fail-closed tests at the resolver boundary). L1-05/L1-06 (pin the coverage guard + `rg` audit to concrete patterns/canonical enum symbol).

## Goal

Create the typed vocabulary and single resolver that later IPDs use for `system`, `config`, `state`, and `records`. Prevent callers from guessing paths or silently falling back when project identity or policy is ambiguous.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Schema and resolution

- [ ] E-01 Add canonical enums and immutable data structures for delivery mode, records backend, durability state, logical roots, project identity, and resolved project context in `agent_workflows/project_schema.py`.
  - Depends on: none
  - Expected outcome: all later storage and installer code imports one vocabulary with stable serialized values.
  - Execution state: pending
- [ ] E-02 Implement `agent_workflows/project_context.py` with explicit policy precedence, target-root discovery, logical-root resolution, and fail-closed errors for missing or conflicting inputs.
  - Depends on: E-01
  - Expected outcome: one pure resolver returns all physical paths and their ownership without creating directories or mutating Git state.
  - Execution state: pending

### Task group 2: Inspection surface and tests

- [ ] E-03 Add `aw context` and `aw path <system|config|state|records>` CLI inspection commands, including stable JSON output and ANSI-free `--agent` output.
  - Depends on: E-02
  - Expected outcome: people, workflows, and tests can inspect the same resolved context used by the implementation.
  - Execution state: pending
- [ ] E-04 Add `tests/test_project_context.py` for precedence, all logical roots, ambiguity, missing context, JSON output, and side-effect-free inspection; audit this IPD set so later plans reference this resolver instead of constructing paths.
  - Depends on: E-03
  - Expected outcome: the resolver contract is regression-tested and every dependent IPD has an explicit integration point.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Python package code is under `agent_workflows/`; CLI entry points are routed through `agent_workflows/cli.py`.
- Tests use `unittest`, and the repository expects the complete suite to remain green.
- Human output may use `Term`; JSON and agent-facing output must not contain ANSI sequences.
- Existing install behavior is compatibility input, not the new path authority.

## Findings

| Finding | Consequence |
|---|---|
| Path knowledge is currently distributed across installer and workflow behavior. | Later changes need one resolver before any data is moved. |
| Delivery mode and records location answer different questions. | They must be separate enum fields, not one combined mode. |
| A resolver that creates paths makes inspection unsafe. | Resolution remains pure; materialization belongs to Order 05. |

## Proposed changes (ordered, validatable)

1. Establish the shared serialized schema.
2. Resolve context without side effects.
3. Expose the resolution through stable CLI output.
4. Lock the contract with focused tests and a dependent-plan audit.

## Deferred / out of scope (with reason)

- Project registry matching is Order 02 because it requires its own ambiguity and relocation rules.
- Backend initialization is Order 03 because path resolution must be testable first.
- Directory creation and migration are Orders 05 and 09.

## Scope check

- Over-scope: no installer writes, registry persistence, action state, or migration.
- Under-scope: all four roots, policy axes, output modes, and error behavior are covered.

## Required tests / validation

- `python3 -m unittest tests.test_project_context -v`
- `python3 -m unittest discover -s tests -v`
- `python3 -m agent_workflows context --json`
- `python3 -m agent_workflows path records --agent`

## Spec / documentation sync

- Keep field names and precedence aligned with `.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md`.
- Do not update user-facing current-state documentation until Order 11.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: focused tests round-trip every enum and serialized context field with no duplicate literal vocabulary elsewhere in new modules.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: focused tests prove precedence, all four resolved roots, no filesystem writes, and explicit failure for conflicts.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: captured CLI output is stable JSON or plain agent text and contains no ANSI escapes.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the focused and full suites pass, and `rg` finds no new path construction required to be replaced by the resolver.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: schema, pure resolution, and inspection form one contract that must land before storage implementations.

Do not execute this plan until it and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
