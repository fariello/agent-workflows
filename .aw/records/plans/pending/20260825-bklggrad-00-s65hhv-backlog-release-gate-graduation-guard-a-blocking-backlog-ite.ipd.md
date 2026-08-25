# IPD: Backlog release-gate graduation guard: a blocking backlog item cannot be closed unless the gate is handed off, satisfied with evidence, or explicitly released

- Date: 2026-08-25
- Kind: orchestrator
- Concern: When a backlog item is translated into an IPD/IPD set (or otherwise satisfied), it should leave the backlog by being marked `done` (it served its purpose; no bespoke `promoted`/`superseded` state is warranted). But a backlog item carrying `- Blocks-Release: <R>` must not silently lose its release gate when it exits the active-blocker set. Today `aw backlog set done` on a blocking item drops it from the release-blocker view with no check, and the only backlog<->plan link is informal prose (no machine-readable `From-Backlog`), so nothing can deterministically confirm the gate was handed off or satisfied. This is the exact "move an invariant out of prose into a deterministic boundary" pattern from the agentadhere findings, applied to one concrete rule. Origin: design discussion 2026-08-25 (backlog->IPD handoff policy + release-gate preservation).
- Scope: Introduce a machine-readable `From-Backlog` link and a shared close-legitimacy predicate, then enforce it at two layers (setter/check + optional opt-in pre-commit hook) all calling ONE predicate so they cannot diverge. The predicate answers "does this transition silently drop a release gate?" with per-transition severity on a `Blocks-Release` item: (1) `-> done` FAIL-CLOSED unless one of {handoff: a blocking plan with `From-Backlog: <id6>` and the same `Blocks-Release: <R>`; satisfied: a resolvable `--evidence` citation, reusing the spec-`implemented` `_evidence_resolvable` pattern for non-IPD work like README/research/prompt/check items; de-gated: `Blocks-Release` cleared first}; (2) blocking `-> parked` WARN (allowed; gate hidden from active view, hint to de-gate); (3) priority-demote of a blocker WARN (allowed; possible contradiction). Everything else flows freely with NO check: priority promote, open<->parked (non-blocking), block/unblock (the existing typed Gate-Kind/Gate-Ref requirement stays), reopen. Sibling consistency checks fold in: dangling `From-Backlog`, gate mismatch (`From-Backlog` plan's `Blocks-Release` != item's), and orphaned-live-blocker (a blocking item already graduated to a blocking plan but still `open`). Children: 01 `From-Backlog` field (schema + `aw ipd set --from-backlog` + dangling-ref check); 02 shared predicate + `aw backlog set done` fail-closed gate + the two WARN transitions + `aw check` consistency rules + tests; 03 optional opt-in pre-commit hook wired by `aw install` covering the fail-closed `done` case + adversarial/bypass tests. Then dogfood: close `3gr7fk` through the new guard.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/ipd_schema.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/releases.py, agent_workflows/attention.py, agent_workflows/engine.py, agent_workflows/hooks/, tests/
- Status: draft
- Set: bklggrad
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: s65hhv

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make the backlog->plan graduation honest and deterministic: a release-blocking backlog item can only leave the active-blocker set when its gate is handed off, satisfied with evidence, or explicitly released. Deliver the `From-Backlog` link, the shared close-legitimacy predicate enforced at setter + check + an opt-in hook, then dogfood it by closing `3gr7fk`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; each child carries its own executable checklist. The orchestrator's only execution step is the post-children dogfood transition.

### Task group 1: dogfood the guard

- [ ] E-02 After children 01-03 are executed and green, close backlog item `3gr7fk` THROUGH the new guard: add `From-Backlog: 3gr7fk` to the agentadhere orchestrator (3b4f8u, which already carries `Blocks-Release: next`), then `aw backlog set done 3gr7fk` and confirm it succeeds via the HANDOFF path (not by clearing the gate), leaving the release gate solely on the agentadhere orchestrator.
  - Depends on: none
  - Expected outcome: `aw backlog set done 3gr7fk` succeeds because the agentadhere orchestrator is a `From-Backlog: 3gr7fk` + `Blocks-Release: next` plan; `aw attention` shows the gate once (on 3b4f8u), no double-count; `aw check` clean. (Cross-IPD: runs only after children 01/02/03 are executed; ordering tracked in the dependency table below.)
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | `From-Backlog` field (ku93tn) | Schema recognition + `aw ipd set --from-backlog` + dangling check | none |
| 02 | Shared predicate + gate (orb9zb) | `evaluate_blocking_close`, `aw backlog set done` fail-closed + `--evidence`, warn transitions, `aw check` rules | 01 |
| 03 | Opt-in pre-commit hook (f1dhht) | Installer-wired hook delegating to the predicate; bypass-catcher | 02 |

Sequence is strictly 01 -> 02 -> 03; the orchestrator dogfood step runs after all three.

## Completion criteria (the whole Set is done only when)

- An IPD may legally carry `From-Backlog` and lints clean; the setter writes/clears it and the dangling check works (01).
- `aw backlog set done` on a blocking item fails closed unless handoff/evidence/de-gate; park/demote warn but never block; the three `aw check` consistency rules work (02).
- An opt-in installer-wired pre-commit hook catches the hand-edit bypass and is idempotent/off-by-default (03).
- `3gr7fk` is closed `done` through the HANDOFF path and the release gate lives solely on the agentadhere orchestrator (dogfood).
- Full test suite green.

## Cross-IPD validation

- One shared predicate: the setter (02), the `aw check` rules (02), and the hook (03) all call `evaluate_blocking_close` - no duplicated legitimacy logic (grep confirms a single definition).
- `From-Backlog` field (01) is consumed by the predicate (02) and the hook (03); no child re-implements the resolver.

## Deferred / out of scope (with reason)

- Wiring the `aw check` rule into required CI: belongs to the agentadhere Phase-5 child (CI/protected-branch), not this set.
- A commit-hash evidence form and a first-class `promoted` backlog status: explicitly decided against / deferred (design discussion 2026-08-25; `done` + evidence/handoff is sufficient and avoids valueless paperwork).

## Scope check

- Over-scope: none.
- Under-scope: none (field + predicate + two enforcement layers + dogfood is the complete guard).

## Required tests / validation

Aggregate of the children's tests (schema/lint, setter fail-closed + three paths, check rules, warn-only transitions, hook bypass + install opt-in/idempotency) plus the dogfood assertion that `3gr7fk` closes via handoff and the gate is single-sourced on the orchestrator.

## Open questions

### OQ-01: Should the same guard eventually extend to specs (a blocking spec closed without a plan)?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: This set targets backlog items (the concrete gap). The predicate is written record-type-agnostically so a spec extension is cheap later; not required for the 2.0.0 blocker close.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
