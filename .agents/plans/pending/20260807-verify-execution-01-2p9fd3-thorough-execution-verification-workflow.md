# IPD: Thorough Execution & Intent Verification Workflow

- Date: 2026-08-07
- Kind: child
- Concern: verification-rigor
- Scope: `.agents/workflows/verify-execution/`, `.opencode/commands/`, `.claude/commands/`, `.agents/agent-workflows/`
- Status: reviewed
- Highest E allocated: 04
- Author: Antigravity Agent
- Id: 2p9fd3
- Set: verify-execution
- Order: 1

## Workflow history

- 2026-08-07 draft (Antigravity Agent): created initial IPD structure.
- 2026-08-07 to-review (Antigravity Agent): populated complete implementation tasks, rubric, and validation gates for high-standard execution and intent verification.
- 2026-08-10 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001/002/003/005 fixed in place (E-04 regenerate-not-hand-edit shims; V-* strengthened to concrete evidence; E-04 scoped to manifest update; E-03 preserves+maps to the existing MATCHES/DIVERGES/INCOMPLETE verdict and D65 corrective-IPD status). No open questions. Status to-review -> reviewed. GO - PENDING HUMAN APPROVAL.

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

- [ ] E-03 Upgrade the core `/verify-execution` workflow (`.agents/workflows/verify-execution/verify-execution.md`) to integrate the intent audit protocol and mandate empirical re-execution of test suites with log capture. PRESERVE, do not silently replace, the workflow's existing contracts: the current verdict vocabulary (MATCHES / DIVERGES / INCOMPLETE, verify-execution.md:107) and the D65 corrective-IPD status logic (born `auto-approved` vs `to-review` by COMPLEXITY, verify-execution.md:138-146). The new FIDELITY_* rubric (E-02) MUST be defined as an ADDITIONAL fidelity dimension that MAPS ONTO the existing verdict + D65 rule (state the mapping explicitly, e.g. which fidelity levels correspond to DIVERGES/INCOMPLETE and when a corrective IPD is born auto-approved vs to-review); it must not introduce a contradictory parallel scheme or weaken the "auto-approved is set by the checker, never by an executor" and "still must pass validation" guarantees (D64/D65). The existing run-record location `workflow-artifacts/verify-execution/<RUN_ID>/` (verify-execution.md:123) is retained.
  - Depends on: E-01, E-02
  - Expected outcome: Updated `verify-execution.md` requiring strict proof of execution (pasted real runner output, raw git-diff inspection at path:line) and corrective IPD emission, with the FIDELITY_* rubric explicitly reconciled to the existing MATCHES/DIVERGES/INCOMPLETE verdict and the D65 auto-approved/to-review status rule (no contradictory duplicate scheme).
  - Execution state: pending

- [ ] E-04 Update the workflow manifest row for `verify-execution` in `.agents/workflows/index.md` (the `description` column) to reflect the enhanced intent-audit capability, then REGENERATE the command shims via the installer (`aw install .`) rather than hand-editing them. IMPORTANT (repo architecture, engine.py:6-7,24): the `.opencode/commands/*` and `.claude/commands/*` shims are GENERATED from the index.md manifest and are "never hand-maintained"; the shim body is a static `Read and execute @.agents/workflows/verify-execution/verify-execution.md` pointer whose only content-bearing field is the `description` copied from the manifest row. Do NOT hand-edit the shim files (a hand-edit is flagged as customized and/or overwritten). Antigravity and other non-slash-command hosts use the universal fallback (read index.md), so they need no per-host shim. `verify-execution` is ALREADY registered in the index and both shims already exist; this task UPDATES the manifest description and regenerates, it does not create new shims.
  - Depends on: E-03
  - Expected outcome: the index.md manifest row for verify-execution reflects the enhanced capability, and `aw install .` (or the documented regeneration path) produces shims whose description matches the updated manifest row (verified by re-reading the generated shim, not by hand-editing it). No hand-edited shim files.
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

### Plan-review findings (2026-08-10 /plan-review, opencode its_direct/pt3-claude-opus-4.8-1m-us)

- PR-001 (HIGH, IN-SCOPE): E-04 originally mandated hand-editing the generated command shims. Repo architecture (engine.py:6-7,24) says shims are GENERATED from the index.md manifest and "never hand-maintained". FIXED: E-04 rewritten to update the manifest row description and REGENERATE via the installer; V-04 requires proof of regeneration (no hand-edit).
- PR-002 (MEDIUM, UNDER-SCOPE): V-01..V-04 were weak existence/"contains" checks that a stub could pass. FIXED: each V-* now demands concrete evidence (heading lists, quoted usable instruction bodies, all five fidelity levels + >=3 failure signatures, git diffs, regeneration proof).
- PR-003 (MEDIUM, IN-SCOPE): E-04 overstated the work ("expose across ... hosts") when verify-execution is already registered and shimmed, and non-slash hosts use the index fallback. FIXED: E-04 scoped to a manifest-row update + regeneration.
- PR-005 (MEDIUM, IN-SCOPE): E-01/E-03 introduced a FIDELITY_* scheme + "emit corrective IPD below FIDELITY_EXEMPLARY" alongside the existing MATCHES/DIVERGES/INCOMPLETE verdict and D65 auto-approved/to-review corrective-IPD status logic, without reconciling them (risk of an unexplained behavior change to a reviewed workflow). FIXED: E-03 now requires PRESERVING the existing verdict + D65 rule and explicitly MAPPING the FIDELITY_* levels onto them; V-02/V-03 verify the mapping.
- (PR-004 withdrawn: trailing-newline nit, not linter-flagged, not actionable.)

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
- Under-scope: two gaps found and FIXED in review: a weak verification checklist (PR-002, V-* strengthened) and unreconciled FIDELITY_* vs existing verdict/D65 logic (PR-005, E-03 now preserves+maps). No remaining under-scope.

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
  - Required evidence: `.agents/workflows/verify-execution/intent-audit.md` exists AND each of the 5 named dimensions (Explicit Requirements, Implicit Intent & Spirit, Empirical Validation, Scope Discipline, Repository Hygiene) is present as its own section with concrete, agent-followable instructions (not just headings). Paste the heading list (e.g. `grep -nE "^#" intent-audit.md`) and quote one dimension's instruction body to show it is usable, not a stub.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `.agents/workflows/verify-execution/rubric.md` exists AND defines all five fidelity levels (FIDELITY_EXEMPLARY, FIDELITY_SURFACE_ONLY, FIDELITY_PARTIAL, FIDELITY_UNVERIFIED, FIDELITY_DIVERGED) each with a decision/corrective action, AND a failure-signature catalog naming concrete signatures (swallowed exceptions, silent try/except, empty mock returns, deleted failing assertions). Paste the level list and at least three catalog entries. Confirm the file states how the fidelity levels MAP to the existing MATCHES/DIVERGES/INCOMPLETE verdict (PR-005).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff` of `.agents/workflows/verify-execution/verify-execution.md` showing the intent-audit integration and mandatory empirical re-execution (pasted real runner output requirement). Prove PRESERVATION: the MATCHES/DIVERGES/INCOMPLETE verdict and the D65 auto-approved/to-review corrective-IPD status logic are still present (quote the retained lines) and the new FIDELITY_* rubric is reconciled to them (quote the mapping). Confirm the run-record path `workflow-artifacts/verify-execution/<RUN_ID>/` is retained.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff` of `.agents/workflows/index.md` showing ONLY the verify-execution manifest-row `description` updated; then evidence that the shims were REGENERATED (not hand-edited): run `aw install . --dry-run` (or the documented regen path) and paste that it would refresh the verify-execution shim, and paste the regenerated `.opencode/commands/verify-execution.md` / `.claude/commands/verify-execution.md` description matching the manifest row. There must be NO hand-authored shim edit. Confirm `parse_manifest`/install still succeeds (no manifest breakage).
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
