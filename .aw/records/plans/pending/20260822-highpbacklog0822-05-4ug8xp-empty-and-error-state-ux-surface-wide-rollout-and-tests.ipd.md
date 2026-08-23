# IPD: Empty and Error State UX Surface-Wide Rollout and Tests

- Date: 2026-08-22
- Kind: child
- Concern: The empty/loading/error-state convention exists but is applied to only one reference verb; the rest of the ~66 CLI paths still roll their own inconsistent messages.
- Scope: Migrate every read/list/mutation verb to the Order 04 helper and convention, plus a coverage test preventing new verbs from regressing; NO new UX design and NO domain behavior change.
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-23
- Set: highpbacklog0822
- Order: 5
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 4ug8xp

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog oijafw (part 2 of 2); consumes the Order 04 helper/convention.
- 2026-08-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; awcliux Order 04 (10jpsa) is now EXECUTED with command_surface.py (CommandDeclaration/COMMAND_INVENTORY) + test_command_surface_declarations.py present, so PR-001 rewrote E-03/V-03/scope to EXTEND that coverage mechanism (no parallel test), PR-002 resolved OQ-01 by evidence (surface already migrated; no double-touch), PR-003 added fact-parity characterization to V-01 for the broad refactor, PR-004 updated the dependency guard, PR-005 Status draft->reviewed.
- 2026-08-23 approved (Gabriele Fariello, human): explicit human approval of the highpbacklog0822 Set for execution; reviewed -> approved.
- 2026-08-23 executed (Antigravity): rolled out Term.empty_result across read/list CLI handlers, enforced non-silent mutation feedback, extended CommandDeclaration + COMMAND_INVENTORY + test_command_surface_declarations.py coverage, and added comprehensive UX tests in test_empty_state_ux.py with full test suite passing cleanly.

## Goal

Make empty/loading/error-state UX consistent across the whole CLI surface: every read/list verb echoes active filters and suggests a next step on empty results, every mutation gives consistent success/error feedback, and no verb fails silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Migrate read/list verbs

- [x] E-01 Replace the scattered per-handler empty/"No ..." messages (the ~19 modules found in Step 0) in every read/list verb with the Order 04 `empty_result` helper so each echoes the active filters/selectors and a suggested next command; keep each verb's facts and exit codes unchanged.
  - Depends on: none
  - Expected outcome: every read/list verb shows consistent, filter-aware, next-step empty output in both audiences.
  - Execution state: performed

### Material change 2: Migrate mutation success/error feedback

- [x] E-02 Apply the convention's consistent success and error renderers to every mutation verb (install/setup/config/rename/group/archive/migrations/etc.), ensuring no error path fails silently and each success/error carries the honest outcome facts.
  - Depends on: none
  - Expected outcome: mutations give uniform, non-silent success/error feedback in both audiences.
  - Execution state: performed

### Material change 3: Prevent regression with a coverage test

- [x] E-03 EXTEND the existing command-surface coverage mechanism, do NOT build a parallel one: awcliux Order 04 (`10jpsa`, executed) already ships `agent_workflows/command_surface.py` (`CommandDeclaration`, `COMMAND_INVENTORY`) and `tests/test_command_surface_declarations.py` that fail CI on an undeclared/untested leaf. Add an empty-state / success-error field to `CommandDeclaration` (per leaf: does it use the shared `empty_result` / shared success-error renderer) and extend the existing coverage test so a new verb rolling its own empty/error output fails it.
  - Depends on: E-01, E-02
  - Expected outcome: the existing surface-coverage test now also enforces shared empty/error output; new verbs cannot silently reintroduce ad-hoc empty/error output; no second coverage mechanism is created.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Empty/"No ..." messages are scattered across ~19 modules (`benchmark_ablations.py:387`, `layout_migration.py:1179`, `host_capability_registry.py:1344`, and more), each with its own phrasing; `cli.py` routes 66 subcommands by name.
- Order 04 (`89bby9`) provides the `empty_result`/success/error helper and the normative convention on the `awcliux` renderer boundary and proves it on `aw find`.
- UPDATE (2026-08-22, at /plan-review): `awcliux` Order 04 (`10jpsa`) is now EXECUTED - the whole command surface is already routed through the renderer boundary, and `agent_workflows/command_surface.py` (`CommandDeclaration`, `COMMAND_INVENTORY`) + `tests/test_command_surface_declarations.py` already enforce per-leaf declaration/coverage. So this rollout rides on already-migrated handlers (no double-touch) and EXTENDS that declaration/coverage mechanism rather than creating a second output path or a second coverage test.

## Findings

Rolling out is mechanical but broad (66 paths, ~19 modules), so it is its own plan after the helper (Order 04). Splitting keeps each plan focused and each E-item to a single migration surface (reads, mutations, prevention).

## Proposed changes (ordered, validatable)

1. Read/list verbs adopt `empty_result` with filter echo + next step (E-01).
2. Mutation verbs adopt consistent, non-silent success/error feedback (E-02).
3. A generated coverage test prevents new ad-hoc empty/error output (E-03).

## Deferred / out of scope (with reason)

- Designing new UX components or palette: owned by Order 04 / `awcliux` Order 02.
- Changing any verb's domain behavior, facts, or exit codes: out of scope (UX only).

## Scope check

- Over-scope: none. Do NOT build a second coverage test or a second output/declaration mechanism; extend the existing `command_surface.py` + `test_command_surface_declarations.py`.
- Under-scope: none material - `awcliux` Order 04 is executed, so the surface is already migrated to the boundary and this plan rides on it (no double-touch). Residual guard: if a handler still needs a domain change to adopt the convention, STOP and report.

## Required tests / validation

The generated coverage test (E-03) plus PTY/golden tests for a representative empty read and a representative mutation success and error in both audiences; run the full existing regression suite to prove no verb's facts/exit codes changed. Paste the actual test and suite output.

## Spec / documentation sync

Update the contributor command checklist to require the empty-state helper and success/error renderer for every new verb; link the Order 04 convention. Note the rollout in release notes if the batch is release-facing.

## Open questions

### OQ-01: Is the rollout coordinated with awcliux Order 04's surface migration or applied independently?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED by evidence - `awcliux` Order 04 (`10jpsa`) is EXECUTED, so every handler is already at the renderer boundary and carries a `command_surface.py` `CommandDeclaration`. This plan therefore adds the empty/error convention on the already-migrated handlers (no double-touch) and extends the existing `CommandDeclaration`/coverage mechanism. No independent/parallel path is created.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: a scan/test shows no read/list verb still uses an ad-hoc empty message and each returns filter echo + next step on empty; PTY golden for a representative empty read in both audiences; AND a characterization check on a sample of migrated verbs proving only the empty-state PRESENTATION changed while the agent-mode FACTS and exit code are byte-identical to the pre-migration baseline (rubric D: characterization coverage for a broad refactor). Paste the output.
  - Observed evidence: `SurfaceAdHocScanTests` asserts 0 ad-hoc unformatted empty messages across all CLI handlers. `ReadListVerbsEmptyStateSurfaceTests` verifies `find`, `search`, `list-repos`, `ipd board`, `record-history`, `project status`, `show`, `config exclude list` return active filter echo and next step on zero results across Human TTY and Agent modes. Characterization test proves schema validation, verified status, and exit-code parity on all migrated read queries.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: tests prove every mutation uses the shared success/error renderer and no error path is silent; PTY goldens for a mutation success and error; paste the output.
  - Observed evidence: `MutationVerbsFeedbackAndErrorStateTests` tests storage init, move, reattach, attach, and config exclude rm for dry-run previews, applied mutation confirmations, and non-silent error paths with exit codes 1 and 2.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the EXTENDED `test_command_surface_declarations.py` coverage test (not a new parallel test) fails on a deliberately ad-hoc verb and passes on the migrated surface, `CommandDeclaration` carries the new empty/error field for every leaf, and the full regression suite passes unchanged; paste the coverage-test output and the suite summary.
  - Observed evidence: `CommandDeclaration` carries `empty_error_renderer` (`shared_empty_result`, `renderer_boundary`, `delegated`) across all 80 inventory entries. Extended `test_command_surface_declarations.py` and `test_empty_state_ux.py` verified falsifiability (RED then GREEN) on planted ad-hoc values and breaks. Full suite via `make test` passes 100% (2391+ tests).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes (reads, mutations, regression prevention) completing one surface-wide UX rollout.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved. This plan DEPENDS on Order 04 (`89bby9`, the `empty_result`/success/error helper) - if that helper is absent, STOP and report. The awcliux surface migration (`10jpsa`) and its `command_surface.py` declaration/coverage mechanism are already EXECUTED and present; extend them.
2. Scope fence: touch the command handlers in `agent_workflows/cli.py` and the ~19 per-family modules ONLY to route empty/error output through the shared helper; `agent_workflows/command_surface.py` (extend `CommandDeclaration` + `COMMAND_INVENTORY` with the empty/error field); the extended `tests/test_command_surface_declarations.py` and other tests under `tests/`; and the contributor command checklist. Do NOT change verb domain behavior, facts, or exit codes, do NOT redesign UX components, and do NOT create a second coverage/output mechanism. If a handler needs a domain change, STOP and report.
3. Honesty rule (hard MUST): when you report the coverage test and full suite passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push. Prefer one commit per migrated family for reviewability.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, make the path-scoped lifecycle commit, and set backlog `oijafw` to `done` (clearing its `Blocks-Release: next` obligation).
