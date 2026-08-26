# IPD: Graduate agy run/sessions/view and pwatch under the packaged host-subcommand + compat-shim pattern

- Date: 2026-08-25
- Kind: child
- Concern: Several source-checkout tools remain outside the packaged host-subcommand pattern that awocrunner established for runipd (`aw oc runipd` + packaged core + thin `tools/` compat shim, cli.py:2153): `tools/agy_run.py`, `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`, `tools/pwatch.py`. They should be graduated so they are invocable via `aw` and covered by the package.
- Scope: Graduate the four tools under the awocrunner packaged-core + host-subcommand + compat-shim pattern: (1) move each tool's logic into a packaged `agent_workflows` core module (e.g. `agy_run.py`, `agy_sessions.py`, `agy_view.py`, `pwatch.py`); (2) expose `aw agy run` (renamed from runagy), `aw agy sessions`, `aw agy view`, and `aw pwatch` via cli.py (an `aw agy` group mirroring `aw oc`, plus a top-level `aw pwatch`); (3) reduce each `tools/*.py` to a thin compat shim that forwards to the packaged entry (as `tools/ipdrunner/runipd.py` was reduced). Add invocation tests (each `aw` subcommand runs the packaged core) and shim-forwarding tests. If child 01's shared renderer has landed, the graduated tools may consume it; if not, leave their output as-is (adoption is optional, not required for graduation).
- Scope-Paths: agent_workflows/agy_run.py, agent_workflows/agy_sessions.py, agent_workflows/agy_view.py, agent_workflows/pwatch.py, agent_workflows/cli.py, tools/agy_run.py, tools/agy_sessions.py, tools/view-antigravity-jsonl.py, tools/pwatch.py, tests/
- Status: draft
- Set: runnernorm
- Order: 2
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: puot79

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Graduate `agy_run`/`agy_sessions`/`view-antigravity-jsonl`/`pwatch` into packaged cores exposed as `aw agy run/sessions/view` and `aw pwatch`, with thin `tools/` compat shims, following the awocrunner pattern.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: agy tools

- [ ] E-01 Move `tools/agy_run.py`, `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py` logic into packaged cores (`agent_workflows/agy_run.py`, `agy_sessions.py`, `agy_view.py`) and expose an `aw agy` group in cli.py with `run`/`sessions`/`view` subcommands (mirroring `aw oc`, cli.py:2153).
  - Depends on: none
  - Expected outcome: `aw agy run/sessions/view` invoke the packaged cores.
  - Execution state: pending

### Task group 2: pwatch + compat shims

- [ ] E-02 Move `tools/pwatch.py` into a packaged `agent_workflows/pwatch.py` and expose `aw pwatch`; then reduce all four `tools/*.py` to thin compat shims that forward to the packaged entries (as `tools/ipdrunner/runipd.py` was reduced).
  - Depends on: E-01
  - Expected outcome: `aw pwatch` runs the packaged core; each `tools/*.py` shim forwards and still works.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- awocrunner pattern: packaged core in `agent_workflows/`, host-subcommand group in cli.py (`aw oc`, cli.py:2153/6719), thin `tools/` compat shim (`tools/ipdrunner/runipd.py`).
- Tools to graduate: `tools/agy_run.py`, `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`, `tools/pwatch.py` (there is also an existing `tools/test_agy_run.py` to migrate/adapt).

## Findings

Graduation is mechanical and precedented; the risk is preserving each tool's CLI surface behind the shim. Tests assert both the new `aw` invocation and the shim forwarding.

## Proposed changes (ordered, validatable)

1. `agent_workflows/agy_run.py`/`agy_sessions.py`/`agy_view.py`/`pwatch.py`: packaged cores.
2. `cli.py`: `aw agy run/sessions/view` group + `aw pwatch`.
3. `tools/*.py`: thin compat shims forwarding to packaged entries.
4. `tests/`: `aw` invocation tests + shim-forwarding tests (migrate `tools/test_agy_run.py`).

## Deferred / out of scope (with reason)

- The shared renderer extraction: child 01 (independent); graduated tools MAY consume it once landed, but adoption is not required for graduation.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `aw agy run/sessions/view` and `aw pwatch` each run the packaged core (invocation tests).
- Each `tools/*.py` compat shim forwards to the packaged entry and preserves prior behavior.
- Migrated `tools/test_agy_run.py` passes against the packaged core.

## Spec / documentation sync

- Update docs/READMEs to list `aw agy run/sessions/view` and `aw pwatch`; note the compat shims.

## Open questions

### OQ-01: Should `aw agy view` keep the `view-antigravity-jsonl` name as an alias?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Provide a compat shim under the old name; the canonical surface is `aw agy view`. Finalize alias handling in implementation.

## Validation and cross-check (verify before reporting done)

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
