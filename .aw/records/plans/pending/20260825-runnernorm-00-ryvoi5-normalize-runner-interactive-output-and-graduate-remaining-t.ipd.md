# IPD: Normalize runner interactive output and graduate remaining tools under aw

- Date: 2026-08-25
- Kind: orchestrator
- Concern: Follow-on work deferred by the awocrunner Set (which graduated runipd to `aw oc runipd`). Two gaps: (a) runipd's interactive render layer (`render_event`/`Palette`/`Heartbeat`, oc_runipd.py:142/108/196) is inline and unshared, so progress/streaming output is duplicated per tool rather than normalized; (b) several source-checkout tools remain outside the packaged host-subcommand pattern: `tools/agy_run.py`, `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`, `tools/pwatch.py`. Backlog item 1sdkvd (medium, non-blocking); the item itself notes it can be split renderer-vs-tool-graduation.
- Scope: (a) Extract runipd's `render_event`/`Palette`/`Heartbeat` streaming layer into a shared `agent_workflows` rendering utility so interactive/progress output is normalized across consumers, with runipd refactored to consume it (behavior-preserving). (b) Graduate the remaining source-checkout tools under the packaged host-subcommand + compat-shim pattern established by awocrunner (packaged core + `aw <host>` group + thin `tools/` shim): `agy_run.py -> aw agy run` (renamed runagy), `agy_sessions.py -> aw agy sessions`, `view-antigravity-jsonl.py -> aw agy view`, `pwatch.py -> aw pwatch`. Two children: 01 shared renderer + runipd refactor; 02 tool graduation (packaged cores + `aw agy`/`aw pwatch` groups + compat shims). Non-blocking; children are independent and may execute in either order.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_run.py, agent_workflows/agy_sessions.py, agent_workflows/agy_view.py, agent_workflows/pwatch.py, agent_workflows/cli.py, tools/, tests/
- Status: draft
- Set: runnernorm
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ryvoi5

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Normalize the runner's interactive output into a shared renderer (consumed by runipd) and graduate the remaining source-checkout tools (agy run/sessions/view, pwatch) under the packaged `aw <host>` + compat-shim pattern, per backlog 1sdkvd.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [ ] E-01 After children 01-02 execute, confirm runipd uses the shared renderer (no inline duplicate) and each graduated tool runs via `aw agy ...`/`aw pwatch` with a working compat shim; full suite green.
  - Depends on: none
  - Expected outcome: shared renderer has a single definition consumed by runipd; `aw agy run/sessions/view` and `aw pwatch` invoke the packaged cores; shims forward; suite green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | shared renderer (dg28i9) | extract `render_event`/`Palette`/`Heartbeat` into a shared utility; refactor runipd to consume it | none |
| 02 | graduate tools (puot79) | package agy run/sessions/view + pwatch cores; add `aw agy`/`aw pwatch`; thin `tools/` compat shims | none |

Children are independent (may execute in either order); orchestrator verifies.

## Completion criteria (the whole Set is done only when)

- A shared rendering utility exists and runipd consumes it with unchanged behavior (01).
- `agy_run`/`agy_sessions`/`view-antigravity-jsonl`/`pwatch` are packaged and invocable as `aw agy run/sessions/view` and `aw pwatch`, with thin `tools/` compat shims (02).
- Full test suite green.

## Cross-IPD validation

- Single renderer definition (no duplicated `render_event`/`Palette`/`Heartbeat`).
- Graduated tools follow the awocrunner packaged-core + host-subcommand + compat-shim pattern (consistency with `aw oc runipd`).

## Deferred / out of scope (with reason)

- Changing runner behavior/UX beyond normalization: out of scope (behavior-preserving extraction only).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Aggregate of children: renderer unit tests + runipd behavior-preserved; graduated-tool invocation tests via `aw agy`/`aw pwatch` + shim-forwarding tests.

## Open questions

### OQ-01: Rename `runagy` to `aw agy run` - keep a `runagy` alias?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Provide a thin compat shim (as awocrunner did for runipd) so existing `runagy`/`tools/*.py` invocations keep working; finalize alias names in child 02.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
