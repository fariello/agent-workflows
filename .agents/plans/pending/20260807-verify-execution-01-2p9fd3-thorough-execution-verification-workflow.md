# IPD: Thorough Execution & Intent Verification Workflow

- Date: 2026-08-07
- Kind: child
- Concern: verification-rigor
- Scope: `.agents/workflows/verify-execution/`, `.opencode/commands/`, `.claude/commands/`, `.agents/agent-workflows/`
- Status: to-review
- Highest E allocated: 04
- Author: Antigravity Agent
- Id: 2p9fd3
- Set: verify-execution
- Order: 1

## Workflow history

- 2026-08-07 draft (Antigravity Agent): created initial IPD structure.
- 2026-08-07 to-review (Antigravity Agent): populated complete implementation tasks, rubric, and validation gates for high-standard execution and intent verification.

## Goal

Establish a rigorous, high-standard execution verification process that audits executed Implementation Plan Documents (IPDs) and user prompts against both their explicit requirements and their underlying architectural intent. This workflow ensures that coding agents execute tasks fully, accurately, precisely, and without superficial symptom patching, missing assertions, un-run test claims, or dropped constraints.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Execution & Intent Verification Protocol Design

- [ ] E-01 Author the comprehensive Intent & Spirit Audit Harness (`.agents/workflows/verify-execution/intent-audit.md`) defining a 5-dimension verification process (Explicit Requirements, Implicit Intent & Spirit, Empirical Validation, Scope Discipline, and Repository Hygiene).
  - Depends on: none
  - Expected outcome: A reusable, tool-agnostic verification harness instructing auditing agents how to evaluate completed IPDs or prompts against actual git diffs and runtime logs.
  - Execution state: pending

- [ ] E-02 Define the Execution Fidelity Scoring Rubric & Failure Signature Catalog (`.agents/workflows/verify-execution/rubric.md`).
  - Depends on: E-01
  - Expected outcome: A deterministic rating framework (`FIDELITY_EXEMPLARY`, `FIDELITY_SURFACE_ONLY`, `FIDELITY_PARTIAL`, `FIDELITY_UNVERIFIED`, `FIDELITY_DIVERGED`) and a catalog of false-completion signatures (e.g. swallowed exceptions, silent try-excepts, empty mock returns, deleted failing assertions).
  - Execution state: pending

### Task group 2: Workflow Enhancement & Integration

- [ ] E-03 Upgrade the core `/verify-execution` workflow (`.agents/workflows/verify-execution/verify-execution.md`) to integrate the intent audit protocol and mandate empirical re-execution of test suites with log capture.
  - Depends on: E-01, E-02
  - Expected outcome: Updated `verify-execution.md` requiring strict proof of execution and automated corrective IPD emission when fidelity is below `FIDELITY_EXEMPLARY`.
  - Execution state: pending

- [ ] E-04 Wire command shims and manifest registries (`.opencode/commands/verify-execution.md`, `.claude/commands/verify-execution.md`, `.agents/workflows/index.md`) to expose the enhanced verification workflow across OpenCode, Claude Code, Antigravity, and other supported hosts.
  - Depends on: E-03
  - Expected outcome: Fully synchronized command shims and workflow index entries allowing cross-agent execution verification.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Repository follows IPD lifecycle: `pending/` -> `to-review` -> `reviewed` -> `approved` -> `executed/` (or `superseded/` / `not-executed/`).
- Tooling available for IPD lifecycle enforcement: `python3 -m agent_workflows ipd sync`, `python3 -m agent_workflows ipd lint`.
- Strict evidence discipline: Verification requires pasting actual runner output and inspecting raw git diffs at `path:line` rather than trusting commit messages or text claims.
- Concurrency and safety: Verification workflows must commit only their own created files (reports/corrective IPDs) path-scoped, never bare `git add -A`.

## Findings

| ID | Category | Finding | Impact | Proposed Fix |
|---|---|---|---|---|
| F-01 | Verification Gap | Existing `verify-execution.md` checks task items but lacks explicit checks for whether changes honor the *implicit spirit* of the prompt (e.g., detecting silent fallbacks or missing edge-case handling). | Agents can mark a task done by making superficial edits that technically touch a line but miss the core architectural goal. | Create explicit 5-dimension Intent Audit Harness with failure signature detection. |
| F-02 | Evidence Discipline | Past executions sometimes claimed "tests pass" without embedding raw, empirical test runner logs. | Unverified claims of success leading to undetected runtime regressions. | Enforce mandatory live test re-execution and empirical stdout/stderr log capture during verification. |

## Proposed changes (ordered, validatable)

1. Create `.agents/workflows/verify-execution/intent-audit.md`:
   - Define audit dimensions:
     1. **Explicit Checklist Audit**: 100% verification of every `E-*` item, acceptance criterion, and user prompt request.
     2. **Architectural Intent & Spirit Audit**: Deep check for completeness, edge cases, error handling, performance impacts, and anti-patterns (no superficial masking, no swallowing exceptions).
     3. **Empirical Runtime Validation**: Re-running test commands (`python -m pytest`, `aw ipd lint`, etc.) and capturing full terminal output.
     4. **Scope & Boundaries Audit**: Ensuring no unintended files were modified or committed.
     5. **Artifact & Convention Compliance**: Verifying that research docs, walkthroughs, and IPD metadata conform to repo standards.

2. Create `.agents/workflows/verify-execution/rubric.md`:
   - Categorize completion quality and define corrective actions for each verdict.

3. Update `.agents/workflows/verify-execution/verify-execution.md`:
   - Incorporate intent audit steps and corrective IPD emission logic.

4. Update Command Shims & Workflow Manifest:
   - Synchronize `.agents/workflows/index.md`, `.opencode/commands/verify-execution.md`, and `.claude/commands/verify-execution.md`.

## Deferred / out of scope (with reason)

- Automatic live auto-remediation of code gaps during verification: Deferred. The verification agent MUST NOT alter code in-place during audit to maintain concurrency safety; it must emit a corrective IPD into `pending/` for explicit execution.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

1. Run `python3 -m agent_workflows ipd sync --apply .agents/plans/pending/20260807-verify-execution-01-2p9fd3-thorough-execution-verification-workflow.md` to ensure `E-*` and `V-*` bijection and numbering.
2. Run `python3 -m agent_workflows ipd lint --phase author .agents/plans/pending/20260807-verify-execution-01-2p9fd3-thorough-execution-verification-workflow.md` to confirm structural validity.
3. Validate markdown formatting and ensure zero em/en dash rule compliance across authored text.

## Spec / documentation sync

- Update `.agents/workflows/index.md` manifest to describe the enhanced intent verification capabilities.
- Update `AGENTS.md` verification guidelines reference if needed.

## Open questions

### OQ-01: Should the verification workflow produce a standalone report file in `.agents/docs/walkthroughs/` or `.agents/docs/research/`?

- Blocking: no
- Status: resolved
- Owner: Antigravity Agent
- Resolution or deferral rationale: Resolved. The workflow will write a durable run record under `workflow-artifacts/verify-execution/<RUN_ID>/report.md` and emit a corrective IPD in `.agents/plans/pending/` if any gap is found.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: File `.agents/workflows/verify-execution/intent-audit.md` exists and contains 5-dimension verification rules.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: File `.agents/workflows/verify-execution/rubric.md` exists and defines fidelity levels and failure signatures.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `.agents/workflows/verify-execution/verify-execution.md` updated with intent audit steps and corrective IPD emission logic.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Workflow index `.agents/workflows/index.md` and command shims updated and synchronized.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: focused on verification rigor and intent auditing across agent workflows.

### Execution Contract

1. All open questions RESOLVED.
2. SCOPE FENCE: Touch ONLY `.agents/workflows/verify-execution/`, `.opencode/commands/verify-execution.md`, `.claude/commands/verify-execution.md`, `.agents/workflows/index.md`, and this IPD. Do not expand scope; if more files seem required, STOP and report.
3. HARD MUST honesty rule: When reporting test/validation success, paste actual runner output. Never claim success you did not run.
4. Commit ONLY changed files path-scoped (`git commit -m msg -- <path>`); never `git add -A` or bare commits; never push.
5. Lifecycle transition: Upon successful verification of all validation items, `git mv` this plan to `.agents/plans/executed/`, update `Status: executed`, and append a dated entry to `## Workflow history`.
