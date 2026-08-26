# IPD: Extract runipd render_event/Palette/Heartbeat into a shared agent_workflows rendering utility

- Date: 2026-08-25
- Kind: child
- Concern: runipd's interactive streaming layer (`render_event`, oc_runipd.py:142; `Palette`, oc_runipd.py:108; `Heartbeat`, oc_runipd.py:196) is inline in `oc_runipd.py`, so any other consumer that wants normalized progress/streaming output must duplicate it. It should be a shared `agent_workflows` rendering utility.
- Scope: Extract `render_event`/`Palette`/`Heartbeat` (and any tightly-coupled helpers) into a new shared module (e.g. `agent_workflows/render_stream.py`), then refactor `oc_runipd.py` to import and use it, behavior-preserving (identical rendered output for the same event stream). No UX/behavior change; pure extraction + de-duplication. Add unit tests for the shared renderer (event -> rendered line, palette application, heartbeat lifecycle) and confirm runipd output is unchanged.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, tests/
- Status: draft
- Set: runnernorm
- Order: 1
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: dg28i9

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Extract runipd's `render_event`/`Palette`/`Heartbeat` streaming layer into a shared `agent_workflows` rendering utility and refactor runipd to consume it, behavior-preserving, so interactive output is normalized and reusable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: extract + refactor

- [ ] E-01 Move `render_event` (oc_runipd.py:142), `Palette` (oc_runipd.py:108), `Heartbeat` (oc_runipd.py:196), and tightly-coupled helpers into a new `agent_workflows/render_stream.py`; refactor `oc_runipd.py` to import them. Behavior-preserving (identical rendered output for the same event stream).
  - Depends on: none
  - Expected outcome: `render_stream` holds the single definitions; `oc_runipd` imports them; runipd output is byte-identical for a fixed event stream.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The render layer lives at oc_runipd.py:108 (`Palette`), :142 (`render_event`), :196 (`Heartbeat`); it is used at the runipd streaming call sites (e.g. oc_runipd.py:1430 `Heartbeat(pal, ...)`).
- awocrunner reduced `tools/ipdrunner/runipd.py` to a thin shim after packaging the core; the same packaged-core discipline applies to shared internals.

## Findings

Pure refactor: the risk is behavior drift, mitigated by a golden-output test over a fixed event stream before and after extraction.

## Proposed changes (ordered, validatable)

1. `render_stream.py`: new module holding `render_event`/`Palette`/`Heartbeat`.
2. `oc_runipd.py`: import from `render_stream`; delete inline definitions.
3. `tests/`: renderer unit tests + a golden runipd-output test proving no behavior change.

## Deferred / out of scope (with reason)

- Adopting the shared renderer in other tools: those tools are graduated in child 02; broad adoption can follow once they are packaged.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Unit tests: `render_event` maps sample events to expected lines; `Palette` applies/omits color per settings; `Heartbeat` lifecycle (enter/exit/interval).
- Golden test: runipd rendered output for a fixed event stream is identical before/after extraction.

## Spec / documentation sync

- N/A (internal refactor; no user-facing surface change).

## Open questions

### OQ-01: Should the shared renderer subsume the `should_color` TTY logic (attention.py:901) too?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Keep scope to the runipd render layer; unifying with `should_color` is a possible later consolidation, not required here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
