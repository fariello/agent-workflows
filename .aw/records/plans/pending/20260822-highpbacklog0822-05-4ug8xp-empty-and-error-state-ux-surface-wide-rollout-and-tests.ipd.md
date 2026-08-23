# IPD: Empty and Error State UX Surface-Wide Rollout and Tests

- Date: 2026-08-22
- Kind: child
- Concern: The empty/loading/error-state convention exists but is applied to only one reference verb; the rest of the ~66 CLI paths still roll their own inconsistent messages.
- Scope: Migrate every read/list/mutation verb to the Order 04 helper and convention, plus a coverage test preventing new verbs from regressing; NO new UX design and NO domain behavior change.
- Status: draft
- Set: highpbacklog0822
- Order: 5
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 4ug8xp

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog oijafw (part 2 of 2); consumes the Order 04 helper/convention.

## Goal

Make empty/loading/error-state UX consistent across the whole CLI surface: every read/list verb echoes active filters and suggests a next step on empty results, every mutation gives consistent success/error feedback, and no verb fails silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Migrate read/list verbs

- [ ] E-01 Replace the scattered per-handler empty/"No ..." messages (the ~19 modules found in Step 0) in every read/list verb with the Order 04 `empty_result` helper so each echoes the active filters/selectors and a suggested next command; keep each verb's facts and exit codes unchanged.
  - Depends on: none
  - Expected outcome: every read/list verb shows consistent, filter-aware, next-step empty output in both audiences.
  - Execution state: pending

### Material change 2: Migrate mutation success/error feedback

- [ ] E-02 Apply the convention's consistent success and error renderers to every mutation verb (install/setup/config/rename/group/archive/migrations/etc.), ensuring no error path fails silently and each success/error carries the honest outcome facts.
  - Depends on: none
  - Expected outcome: mutations give uniform, non-silent success/error feedback in both audiences.
  - Execution state: pending

### Material change 3: Prevent regression with a coverage test

- [ ] E-03 Add a generated coverage test over the parser surface asserting each read/list verb uses the shared empty-state helper and each mutation uses the shared success/error renderer, so a new verb that rolls its own empty/error output fails the test.
  - Depends on: E-01, E-02
  - Expected outcome: new verbs cannot silently reintroduce ad-hoc empty/error output.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Empty/"No ..." messages are scattered across ~19 modules (`benchmark_ablations.py:387`, `layout_migration.py:1179`, `host_capability_registry.py:1344`, and more), each with its own phrasing; `cli.py` routes 66 subcommands by name.
- Order 04 (`89bby9`) provides the `empty_result`/loading/success/error helper and the normative convention on the `awcliux` renderer boundary and proves it on `aw find`.
- `awcliux` Order 04 (`10jpsa`) migrates the whole surface to the renderer boundary; this UX rollout must ride on that migration where it overlaps and must not create a second output path.

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

- Over-scope: none.
- Under-scope: reconcile overlap with `awcliux` Order 04's surface migration so a verb is migrated once, not twice; if both would touch the same handler, coordinate/sequence rather than double-edit.

## Required tests / validation

The generated coverage test (E-03) plus PTY/golden tests for a representative empty read and a representative mutation success and error in both audiences; run the full existing regression suite to prove no verb's facts/exit codes changed. Paste the actual test and suite output.

## Spec / documentation sync

Update the contributor command checklist to require the empty-state helper and success/error renderer for every new verb; link the Order 04 convention. Note the rollout in release notes if the batch is release-facing.

## Open questions

### OQ-01: Is the rollout coordinated with awcliux Order 04's surface migration or applied independently?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: coordinate. Where `awcliux` Order 04 (`10jpsa`) migrates a handler to the renderer boundary, this plan adds the empty/error convention in the same pass or immediately after, so each handler is touched once. If `awcliux` Order 04 is still pending when this runs, apply the convention through the same boundary Order 04 (`89bby9`) established and avoid a second output path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a scan/test shows no read/list verb still uses an ad-hoc empty message and each returns filter echo + next step on empty; PTY golden for a representative empty read in both audiences; paste the output.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: tests prove every mutation uses the shared success/error renderer and no error path is silent; PTY goldens for a mutation success and error; paste the output.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the generated coverage test fails on a deliberately ad-hoc verb and passes on the migrated surface, and the full regression suite passes unchanged; paste the coverage-test output and the suite summary.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes (reads, mutations, regression prevention) completing one surface-wide UX rollout.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved. This plan DEPENDS on Order 04 (`89bby9`); if the `empty_result`/success/error helper and convention are absent, STOP and report.
2. Scope fence: touch the command handlers in `agent_workflows/cli.py` and the ~19 per-family modules ONLY to route empty/error output through the shared helper, plus tests under `tests/` and the contributor command checklist. Do NOT change verb domain behavior, facts, or exit codes, and do NOT redesign UX components. If a handler needs a domain change, STOP and report.
3. Honesty rule (hard MUST): when you report the coverage test and full suite passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push. Prefer one commit per migrated family for reviewability.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, make the path-scoped lifecycle commit, and set backlog `oijafw` to `done` (clearing its `Blocks-Release: next` obligation).
