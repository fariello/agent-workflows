# IPD: Canonical run-root analytics namespace and discovery isolation

- Date: 2026-09-08
- Kind: child
- Concern: Give analytics one canonical, disposable home without allowing its outputs to masquerade as execution runs.
- Scope: Centralize run-root resolution, reserve the analytics subtree, and make every discovery and target-resolution path reject that subtree.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_viewer.py, tests/test_runner_shared.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: to-review
- Set: runanalytics
- Order: 1
- Highest E allocated: 03
- Author: Codex
- Id: xbwq8n

## Workflow history

- 2026-09-08 draft (Codex): created from the run-analytics implementation prompt after inspecting current run-root and viewer behavior.
- 2026-09-08 to-review (Codex): specified the canonical namespace, exclusion invariants, compatibility behavior, and falsifiable tests.

## Goal

Make \`<repo>/.aw/records/runs/analytics/\` the visible but disposable analytics home while preserving all existing run lookup behavior. No analytics cache, report, snapshot, or export may be discovered, resumed, repaired, summarized, or targeted as an execution run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an \`E-*\` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item addresses one concern and is executable in one focused pass.

### Task group 1: Canonical paths and reservation

- [ ] E-01 Add shared path helpers and constants for the resolved runs root and its reserved analytics namespace.
  - Depends on: none
  - Expected outcome: callers obtain the canonical runs root from one helper; the helper exposes \`analytics/\`, \`analytics/cache/\`, \`analytics/snapshots/\`, and \`analytics/exports/\` without creating them during read-only discovery.
  - Execution state: pending
- [ ] E-02 Apply the reservation to run discovery and explicit target resolution while retaining documented legacy-root compatibility.
  - Depends on: E-01
  - Expected outcome: only real driver directories satisfying the existing run predicate are returned; any path within a reserved analytics tree is rejected with an actionable diagnostic, including a directory deliberately named \`run-*\`.
  - Execution state: pending
- [ ] E-03 Add path and routing regression coverage for canonical, legacy, missing, nested, symlinked, and adversarial analytics locations.
  - Depends on: E-02
  - Expected outcome: tests prove analytics is invisible to list, target, resume, liveness, and repair selection, while existing real-run ordering and target matching remain unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- \`runner_shared.state_root(repo)\` currently resolves \`.aw/records/runs\`; new code must reuse or deliberately supersede this authority rather than duplicate the path.
- \`run_viewer.discover_run_dirs\` currently probes the canonical root plus \`.aw/runs\` and \`.agents/runs\` for compatibility.
- \`run_viewer.resolve_target_runs\` accepts run directories and \`state.json\`, \`events.jsonl\`, or \`execution-report.md\` paths, so exclusion must cover explicit targets as well as directory scans.
- The entire \`.aw/records/runs\` tree is ignored and disposable. Analytics belongs there because reports describe that local corpus and do not need a second lifecycle or cleanup policy.
- \`aw runs\` has routing-sensitive fixed leaf names. This IPD changes discovery only; later IPDs own new leaf registration.

## Findings

| Finding | Implementation consequence |
|---|---|
| No real run corpus is present in this checkout | Implement against source contracts and checked-in fixtures; the integration IPD must also validate against an opt-in external corpus when available. |
| Current discovery recognizes children beginning with \`run-\` | Name shape alone is insufficient; reject by containment beneath the reserved analytics root before applying run predicates. |
| Reports and caches share the runs-root parent | Source run directories are read-only inputs, while the reserved analytics sibling is the only writable area. Document this boundary precisely. |
| Legacy roots are still supported | Preserve them for execution runs, but reserve an \`analytics\` child under every resolved source root to avoid accidental ingestion. |

## Proposed changes (ordered, validatable)

1. Introduce side-effect-free path and containment helpers with resolved-path safety.
2. Use those helpers in discovery and target resolution before run validation.
3. Pin compatibility and adversarial cases in unit tests.

## Deferred / out of scope (with reason)

- Cache formats, report generation, and retention are owned by Orders 02 and 07.
- CLI leaf registration is owned by Order 08.
- Deleting legacy roots is not part of analytics and would be a migration change.

## Scope check

- Over-scope: no storage writes, parsing, telemetry, UI, or command registration.
- Under-scope: covers every current entry point that turns filesystem paths into driver-run candidates; Order 10 performs a final repository-wide search for missed selectors.

## Required tests / validation

- Unit tests for canonical and legacy roots, absent directories, deterministic ordering, explicit file targets, nested \`run-*\` analytics output, symlink/relative-path containment, and ordinary real runs.
- Existing run viewer and shared-runner test modules remain green.
- Bare \`python3 -m pytest\` and \`git diff --check\` pass at execution closeout.

## Spec / documentation sync

No approved specification currently defines analytics storage. Order 10 documents the reserved namespace and disposable semantics in user-facing docs after the behavior is implemented. If execution discovers a controlling layout spec, amend it in that order before code relies on a conflicting rule.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a \`V-*\` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: focused tests show all analytics paths derive from the same resolved runs-root helper and read-only resolution creates no directories.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: focused tests show scan and explicit-target APIs reject every analytics descendant while accepting canonical and legacy execution runs.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: focused modules plus bare \`python3 -m pytest\` pass, and \`git diff --check\` is clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one boundary concern spans the shared path authority and the two existing run selectors.

Execute only after this IPD is approved through the repository lifecycle. After all E and V items pass with concrete evidence, move it through the normal executed lifecycle; do not write approval or observed evidence during authoring.
