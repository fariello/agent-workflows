# IPD: IPD Lifecycle History Tracking and Workflow Integration

- Date: 2026-08-07
- Kind: child
- Concern: ipd-lifecycle-history
- Scope: `agent_workflows/ipd_authoring.py`, `agent_workflows/ipd_schema.py`, `agent_workflows/ipd_lint.py`, `.agents/workflows/plan-review/`, `.agents/workflows/assess/templates/`
- Status: to-review
- Highest E allocated: 04
- Author: Antigravity Agent
- Id: wrt0wq
- Set: ipd-history
- Order: 1

## Workflow history

- 2026-08-07 draft (Antigravity Agent): created initial IPD structure.
- 2026-08-07 to-review (Antigravity Agent): populated implementation checklist, schema specification, and validation items for automated IPD history tracking across creation, update, review, approval, and execution.

## Goal

Enhance the Implementation Plan Document (IPD) framework, authoring tools (`aw ipd`), and workflow handlers (`/plan-review`, execution gates) to automatically record structured, audit-ready lifecycle history entries in every IPD's `## Workflow history` section. This ensures every IPD captures a complete, timestamped provenance log recording when a plan was Created, Updated, Reviewed, Approved, and Executed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: History Schema & Authoring Tooling Enhancement

- [ ] E-01 Define the canonical IPD history entry format in `agent_workflows/ipd_schema.py` (`- YYYY-MM-DD HH:MM:SS [Status: <from> -> <to>] (<actor>): <event_type> - <summary>`) and create the programmatic history manipulation API in `agent_workflows/ipd_authoring.py`.
  - Depends on: none
  - Expected outcome: Standardized history syntax and pure functions to append and validate history entries cleanly without corrupting other IPD sections.
  - Execution state: pending

- [ ] E-02 Update `aw ipd scaffold` to automatically generate the initial `created` history entry and expose an `aw ipd log-event` CLI helper command to append lifecycle events.
  - Depends on: E-01
  - Expected outcome: CLI commands automatically stamping timestamped history records upon plan creation or state changes.
  - Execution state: pending

### Task group 2: Review & Lifecycle Workflow Integration

- [ ] E-03 Update `/plan-review` (`.agents/workflows/plan-review/plan-review.md`) and `/plan-review-long` (`.agents/workflows/plan-review-long/plan-review-long.md`) instructions to mandate appending a `reviewed` history entry upon review completion.
  - Depends on: E-01
  - Expected outcome: Plan reviewers automatically stamp `## Workflow history` with review findings and status transition (`to-review` -> `reviewed`).
  - Execution state: pending

- [ ] E-04 Update the execution contract and terminal transition guidelines (`AGENTS.md`, `.agents/plans/README.md`, and IPD templates) to require recording `approved` and `executed` history entries prior to `git mv` into `.agents/plans/executed/`.
  - Depends on: E-01, E-02
  - Expected outcome: Every executed IPD carries a complete history trail from creation to terminal filing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- IPD schema requires `## Workflow history` as the very first H2 section immediately following metadata.
- Lifecycle readiness states defined in `agent_workflows/plans.py`: `draft` -> `to-review` -> `reviewed` -> `approved` / `auto-approved` -> `executed` / `superseded` / `not-executed`.
- Structural linting tool `agent_workflows/ipd_lint.py` enforces section ordering and schema invariants.
- Commits must remain path-scoped (`git commit -m msg -- <path>`); history updates modify only target plan files.

## Findings

| ID | Category | Finding | Impact | Proposed Fix |
|---|---|---|---|---|
| F-01 | Provenance Gap | IPDs currently record informal `## Workflow history` lines manually, leading to omitted transition logs for approval and execution events. | Missing audit trail showing when an IPD moved from `reviewed` to `approved` and who executed it. | Standardize history entry grammar and automate history logging across CLI tools and review runbooks. |
| F-02 | Tooling Support | `aw ipd scaffold` creates a basic history line, but no CLI tool exists for updating history during lifecycle transitions. | Agents must hand-edit markdown headers during `plan-review` or execution, risking format inconsistencies. | Add `aw ipd log-event` CLI command to programmatically append conformant history entries. |

## Proposed changes (ordered, validatable)

1. Update `agent_workflows/ipd_schema.py`:
   - Define regex pattern for structured history lines: `- YYYY-MM-DD( HH:MM:SS)? \[Status: (\w+) -> (\w+)\] \(([^)]+)\): (\w+) - (.+)`.
   - Define canonical event types: `created`, `updated`, `reviewed`, `approved`, `executed`, `retired`.

2. Update `agent_workflows/ipd_authoring.py`:
   - Add `append_history_entry(path, status_from, status_to, actor, event_type, summary)`.
   - Update `scaffold_ipd()` to use `append_history_entry()`.

3. Update `agent_workflows/cli.py`:
   - Add sub-command `aw ipd log-event --path <path> --event <event> --actor <actor> --summary <summary> [--from <status>] [--to <status>]`.

4. Update Workflow Documents:
   - Update `.agents/workflows/plan-review/plan-review.md` and `plan-review-long.md` to mandate appending `reviewed` entries.
   - Update `AGENTS.md` and `.agents/plans/README.md` documentation to explicitly list the mandatory history logging steps at each lifecycle stage.

5. Update `agent_workflows/ipd_lint.py`:
   - Add lint rule (`IPD-S405`) verifying that terminal plans (`executed`) contain corresponding `executed` history entries matching their `Status: executed` metadata.

## Deferred / out of scope (with reason)

- Modifying git log parser to auto-generate missing historical entries for legacy executed plans: Deferred. Legacy plans in `executed/` are frozen history; linting rules will apply to new plans going forward.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

1. Run `python3 -m agent_workflows ipd sync --apply .agents/plans/pending/20260807-ipd-history-01-wrt0wq-ipd-lifecycle-history-tracking.md` to ensure leaf synchronization.
2. Run `python3 -m agent_workflows ipd lint --phase author .agents/plans/pending/20260807-ipd-history-01-wrt0wq-ipd-lifecycle-history-tracking.md` to confirm structural compliance.
3. Validate markdown line formatting and ensure zero em/en dash rule compliance.

## Spec / documentation sync

- Update `.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` with the new history entry format specification.
- Update `.agents/plans/README.md` section on "Workflow history".

## Open questions

### OQ-01: Should timestamps in `## Workflow history` include seconds or remain date-and-time (YYYY-MM-DD HH:MM)?

- Blocking: no
- Status: resolved
- Owner: Antigravity Agent
- Resolution or deferral rationale: Resolved. Use `YYYY-MM-DD HH:MM` (local time) to match the plan filename timestamp convention while remaining human-readable.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `agent_workflows/ipd_schema.py` and `ipd_authoring.py` contain history format regex and `append_history_entry` function.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw ipd scaffold` and `aw ipd log-event` CLI commands produce structured history entries.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `.agents/workflows/plan-review/plan-review.md` updated to require appending `reviewed` history entries.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `AGENTS.md` and `.agents/plans/README.md` updated with lifecycle history logging rules.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: focused on IPD lifecycle history tracking across tools and workflows.

### Execution Contract

1. All open questions RESOLVED.
2. SCOPE FENCE: Touch ONLY `agent_workflows/ipd_authoring.py`, `agent_workflows/ipd_schema.py`, `agent_workflows/ipd_lint.py`, `agent_workflows/cli.py`, `.agents/workflows/plan-review/`, `.agents/plans/README.md`, `AGENTS.md`, and this IPD. Do not expand scope; if more files seem required, STOP and report.
3. HARD MUST honesty rule: When reporting test/validation success, paste actual runner output. Never claim success you did not run.
4. Commit ONLY changed files path-scoped (`git commit -m msg -- <path>`); never `git add -A` or bare commits; never push.
5. Lifecycle transition: Upon successful verification of all validation items, `git mv` this plan to `.agents/plans/executed/`, update `Status: executed`, and append a dated entry to `## Workflow history`.
