# IPD: Install and update policy wizard

- Date: 2026-08-09
- Kind: child
- Concern: Collect complete layout and storage policy through an accessible first-install wizard and a safe update checkpoint.
- Scope: `agent_workflows/install_wizard.py`, policy-related wiring in `agent_workflows/cli.py` and `agent_workflows/engine.py`, terminal presentation in `agent_workflows/term.py`, and `tests/test_install_wizard.py`.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 4
- Highest E allocated: 05
- Author: Codex (GPT-5, high reasoning)
- Id: q0wpk4

## Workflow history

- 2026-08-09 draft (Codex (GPT-5, high reasoning)): created an execution-ready child plan from the approved architecture direction.
- 2026-08-09 revision (Codex (GPT-5, high reasoning)): adopted stable plan identity, clustered naming, and the current lifecycle execution contract after the upstream rebase.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO (controlling spec 20260809-2211-01 is unapproved; foundational HIGH findings need the author/maintainer). Findings recorded, NOT rewritten (another author's plan). L4-01 [HIGH/blocking] (required-test `python3 -m agent_workflows update` targets a NON-EXISTENT verb - cli.py has no `update`, install is idempotent; use `install . --dry-run` or add `update` to scope). L4-02 (add an explicit negative test: `--yes` on an UNCONFIGURED first install does NOT silently select the recommended `home`/`tracked` default and exits nonzero - §11.3). L4-03 (reconcile with the existing `_run_setup`/`_confirm` wizard in cli.py; state supersede/delegate/coexist to avoid two divergent setup surfaces). L4-04 (add `--no-color` + screen-reader linear-output to the 11.4 matrix).

## Goal

Make storage and delivery choices understandable at initial install and reviewable at every interactive update. Preserve automation safety by requiring a complete explicit policy or saved profile before a noninteractive first install writes anything.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Policy collection

- [ ] E-01 Implement pure wizard models for current policy, proposed policy, option metadata, decision transcript, cancellation, and validation; keep prompt rendering separate from selection logic.
  - Depends on: none
  - Expected outcome: interactive and noninteractive paths produce the same validated policy object and auditable transcript.
  - Execution state: pending
- [ ] E-02 Implement the first-install wizard with clear explanations and pros and cons for delivery and records choices, recommending `tracked` delivery and `home` records without silently selecting them.
  - Depends on: E-01
  - Expected outcome: an interactive first install reviews every required decision before presenting a final no-write summary and confirmation.
  - Execution state: pending
- [ ] E-03 Implement the interactive update checkpoint with `keep current policy` as the default, a concise change and warning summary, and an explicit route into the full wizard.
  - Depends on: E-02
  - Expected outcome: every interactive update exposes policy status without forcing users through unchanged questions.
  - Execution state: pending

### Task group 2: Automation and accessibility

- [ ] E-04 Enforce noninteractive rules: an existing saved policy may be reused; first install requires every policy field or a named saved profile; `--yes` alone fails before writes and identifies missing fields.
  - Depends on: E-03
  - Expected outcome: unattended execution is deterministic and cannot accept privacy-sensitive defaults implicitly.
  - Execution state: pending
- [ ] E-05 Add color as redundant emphasis using existing `Term` behavior, named labels and symbols in plain text, plus transcript tests for TTY, piped output, `NO_COLOR`, `FORCE_COLOR`, `TERM=dumb`, cancellation, and invalid input.
  - Depends on: E-04
  - Expected outcome: the wizard is colorful when appropriate and fully understandable without color or interactivity.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `Term` already owns terminal color policy and uses the standard 16-color vocabulary.
- `NO_COLOR`, `FORCE_COLOR`, TTY detection, and `TERM=dumb` must remain authoritative.
- Agent and JSON output must never contain prompts or ANSI escapes.
- Install transactions must not begin until policy validation and final confirmation succeed.

## Findings

| Situation | Required behavior |
|---|---|
| Interactive first install | Full wizard, explicit review, then confirmation |
| Interactive update | Concise checkpoint, keep-current default, optional full review |
| Noninteractive first install | Complete flags or saved profile; otherwise fail before writes |
| Noninteractive update | Reuse valid saved policy unless explicit complete overrides are supplied |

## Proposed changes (ordered, validatable)

1. Separate choice logic from terminal rendering.
2. Build the complete first-install flow.
3. Build the concise update flow.
4. Fail closed in automation.
5. Verify accessible color and complete transcripts.

## Deferred / out of scope (with reason)

- Physical directory creation is Order 05.
- Migrating from a legacy or different policy is Order 09.
- A graphical installer is excluded; the CLI is the canonical setup surface.

## Scope check

- Over-scope: no backend creation, target-layout migration, remote setup, or workflow edits.
- Under-scope: first install, update, noninteractive execution, saved profiles, confirmation, cancellation, and color accessibility are covered.

## Required tests / validation

- `python3 -m unittest tests.test_install_wizard -v`
- `python3 -m unittest discover -s tests -v`
- `NO_COLOR=1 python3 -m agent_workflows install --dry-run`
- `TERM=dumb python3 -m agent_workflows update --dry-run`

## Spec / documentation sync

- Keep option order, defaults, warnings, and automation rules aligned with the canonical 2026-08-09 layout specification.
- Save transcript fixtures only if assertions need them; avoid duplicating full user documentation before Order 11.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pure tests prove equivalent validated policies from interactive selections, explicit flags, and saved profiles.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: golden transcripts contain each choice, balanced pros and cons, visible recommendation, final summary, and no write before confirmation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: update transcripts default to keeping policy and enter the full flow only after an explicit selection.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: automated first install with only `--yes` exits nonzero, lists missing policy fields, and leaves filesystem and Git state unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: terminal-mode matrix tests pass; stripped colored output matches no-color semantic content; JSON and agent output contain no ANSI bytes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the same policy contract must drive interactive setup, update review, and unattended safety.

STOP if Orders 01 through 03 are incomplete. Do not execute until this plan and the parent orchestrator are approved.

Execution contract: touch only the files and areas named in Scope; do not expand scope, and STOP and report if more is required. Paste actual validation output before claiming a pass. Commit only this plan's changed files, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. After every E-item is performed and matching V-item passes, append the lifecycle history, set `Status: executed`, move this file from `pending/` to `executed/` with `git mv`, regenerate the plans index, and make the path-scoped lifecycle commit.
