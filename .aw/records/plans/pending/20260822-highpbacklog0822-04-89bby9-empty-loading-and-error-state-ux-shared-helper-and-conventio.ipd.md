# IPD: Empty Loading and Error State UX Shared Helper and Convention

- Date: 2026-08-22
- Kind: child
- Concern: Every CLI verb rolls its own empty/error output; there is no shared helper to echo active filters, suggest a next step on empty results, or give consistent success/error feedback.
- Scope: A shared empty/loading/error-state helper built on the `awcliux` human-TTY renderer boundary, plus the documented convention; NO per-verb rollout here (that is Order 05).
- Status: draft
- Set: highpbacklog0822
- Order: 4
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 89bby9

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created for backlog oijafw (part 1 of 2); built on the awcliux renderer boundary to avoid a second human-output path.

## Goal

Provide one reusable way for any verb to render an empty result (echoing the active filters and suggesting the next step), a loading/progress state, and consistent success/error feedback, so Order 05 can roll it out without each handler reinventing it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Define the empty/error-state helper

- [ ] E-01 Add an empty/loading/error-state component to the shared human renderer (the `awcliux` Order 02 `czw99i` `Term` component layer): an `empty_result(context)` that echoes the active filters/selectors and a suggested next command, a loading/progress cue, and consistent success and error renderers. Reuse the `awcliux` typed result/`Diagnostic`/`NextAction` facts; do not add a parallel output path.
  - Depends on: none
  - Expected outcome: one helper renders empty/loading/success/error states for both audiences via the existing renderer boundary.
  - Execution state: pending

### Material change 2: Document the convention

- [ ] E-02 Write the empty/loading/error-state convention: when a read/list verb returns nothing it MUST echo the active filters and suggest a next step; mutations MUST give consistent success/error feedback; errors MUST NOT fail silently. Include the agent-mode equivalent (the empty/error facts appear in the `aw.agent/v1` record, not just human prose).
  - Depends on: E-01
  - Expected outcome: a single normative convention Order 05 applies uniformly.
  - Execution state: pending

### Material change 3: Prove it on a reference verb

- [ ] E-03 Adopt the helper in ONE reference read verb that can return empty (e.g. `aw find`) so the empty-with-filters-and-next-step behavior is exercised end to end in both audiences; full rollout is Order 05.
  - Depends on: E-01, E-02
  - Expected outcome: the reference verb shows the new empty-state UX in TTY and agent modes; the pattern is proven for Order 05.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `cli.py` has 66 `add_parser(...)` subcommands, each routed by name to a handler that rolls its own output; there is NO shared empty-result helper.
- Empty/"No ..." messages are scattered across ~19 modules (e.g. `benchmark_ablations.py:387`, `layout_migration.py:1179`, `host_capability_registry.py:1344`), each phrasing its own.
- `agent_workflows/term.py` (217 lines) has only presentation primitives (`line`, `status`, `heading`, `kv`, `status_label`, `severity_label`, `color256`/`status_256`); no empty-state/next-step helper.
- The pending `awcliux` Set relocates human TTY rendering behind a renderer boundary (Order 01 `hd3kln`) and designs human output (Order 02 `czw99i`, `doctor` as reference). This UX work MUST build on that boundary, not duplicate it.

## Findings

The empty/error UX is genuinely cross-cutting and today inconsistent and scattered. Building the helper first (this plan) and rolling it out second (Order 05) keeps each plan at or under three material changes and avoids a monolithic change. Because `awcliux` owns the human renderer, the helper belongs in that layer.

## Proposed changes (ordered, validatable)

1. A shared empty/loading/error-state helper on the `awcliux` renderer layer (E-01).
2. A normative convention doc, human and agent modes (E-02).
3. A proven reference adoption on one read verb (E-03).

## Deferred / out of scope (with reason)

- Rolling the convention across every verb: Order 05.
- Redesigning the human palette/components themselves: owned by `awcliux` Order 02.

## Scope check

- Over-scope: none.
- Under-scope: if the `awcliux` renderer boundary is not yet executed, this plan cannot build on it; STOP and report (see execution contract) rather than creating a standalone helper.

## Required tests / validation

Unit tests for the helper: empty-result renders the active filters + a next-step suggestion; loading/success/error renderers produce the right facts in both human and agent modes; errors never render empty/silently. A PTY/golden test for the reference verb's empty state in TTY, plus an agent-mode record assertion. Paste the actual test output.

## Spec / documentation sync

Add the empty/loading/error-state convention to the `awcliux` human TTY guide / output contract (link, do not fork). Reference it from the contributor command checklist so new verbs adopt it.

## Open questions

### OQ-01: Does the helper live in term.py or the awcliux renderer module?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: it lives wherever `awcliux` Order 02 (`czw99i`) places the shared human `Term` components, so there is exactly one human-output path; if that module is not yet created when this plan runs, STOP and report (the dependency is unmet).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: unit tests prove `empty_result` echoes active filters + next step, and loading/success/error renderers produce correct facts in both audiences via the existing boundary (no parallel path); paste the test output.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the convention doc exists and specifies both human and agent-mode behavior and the no-silent-failure rule; quote the normative lines.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the reference verb (`aw find`) shows the empty-with-filters-and-next-step UX in a PTY golden and the agent record; paste the golden and the record.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes (helper, convention, reference adoption) establishing one empty/error-state pattern; rollout is deferred to Order 05.

Review and explicit approval required.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved. This plan DEPENDS on the `awcliux` human-TTY renderer boundary (Set `awcliux` Order 02 `czw99i`, itself gated on Order 01 `hd3kln`); if its shared human `Term` components are absent, STOP and report rather than building a standalone helper.
2. Scope fence: touch only the `awcliux` shared human renderer module + `agent_workflows/term.py` if that is where the components live, the reference `aw find` handler in `agent_workflows/cli.py`, the convention doc, and tests under `tests/`. Do NOT roll the convention across other verbs here (Order 05) and do NOT change verb domain behavior. If more than the reference verb needs touching, STOP and report.
3. Honesty rule (hard MUST): when you report the helper/golden tests passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. Do NOT set backlog `oijafw` to `done` here (that item closes only after Order 05 completes the rollout).
