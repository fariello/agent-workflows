# IPD: Wire skill-package emission into the installer run() path across hosts

- Date: 2026-08-25
- Kind: orchestrator
- Concern: The execset Set (Order 05, 2h7777) proved skill/shim generation at the library level (`build_skill_package` digest parity + `generate_shim_members` drift-free) and exposed `/exec-set` via the existing shim path, but did NOT wire skill-package emission (`host_adapters.generate_adapter_bundle` / `build_skill_package(...).to_files()`) into `engine.install_all` (engine.py:1953), which today writes only `body_members` + `shim_members`. So a real `aw install` never emits the generated skill packages / per-host adapter bundles. Wiring it is a cross-cutting installer-output change (all hosts + uninstall + idempotency + install-diff), deliberately deferred out of the packaging Order (D21-2h7777-D2). Backlog item bplplj (medium).
- Scope: Wire skill-package + adapter-bundle emission into the installer run path so `aw install` writes the generated skill/adapter files alongside body + shim members, covering all hosts, uninstall, idempotency, and install-diff. Single coherent child (01) plus this orchestrator. Deliverable: `install_all`/`install_into_repo` (engine.py:1953/4893) collect skill/adapter members from `host_adapters.generate_adapter_bundle` + `build_skill_package(...).to_files()` and write them the same idempotent way as shim members; `uninstall_repo` (engine.py:3836) removes them; the install-diff/idempotency tests are extended so a fresh install emits the skill package and a re-install is a no-op.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/host_adapters.py, tests/
- Status: draft
- Set: installerskill
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: rldro6

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `aw install` actually emit the generated skill packages and per-host adapter bundles by wiring `generate_adapter_bundle`/`build_skill_package(...).to_files()` into the installer run path, idempotently and across uninstall + install-diff, closing the gap execset deferred.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; child 01 carries the work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [ ] E-01 After child 01 executes, confirm a fresh `aw install` emits the skill package + adapter bundle, a re-install is a no-op (idempotent), and `uninstall` removes them; full suite green.
  - Depends on: none
  - Expected outcome: install-diff test shows skill/adapter members on fresh install, empty diff on re-install, and clean removal on uninstall.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | emit skill/adapter (kvfsak) | wire `generate_adapter_bundle`/`build_skill_package.to_files()` into `install_all`/`install_into_repo`; uninstall + idempotency + install-diff tests | none |

Single child; orchestrator verifies.

## Completion criteria (the whole Set is done only when)

- `aw install` emits skill package + per-host adapter bundle members across all hosts.
- Re-install is idempotent (no duplicate writes / empty install-diff).
- `uninstall_repo` removes the emitted skill/adapter members.
- Install/install-diff tests assert all of the above and the suite is green.

## Cross-IPD validation

- Emission reuses the existing `generate_adapter_bundle`/`build_skill_package` library (no forked generator) and the same idempotent write path as shim members.

## Deferred / out of scope (with reason)

- Changing the CONTENT of skill/adapter generation (execset already proved digest parity): out of scope; this set only WIRES emission into install.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Aggregate of child 01: fresh-install emits skill/adapter members (all hosts); re-install idempotent; uninstall removes them; install-diff tests updated.

## Open questions

### OQ-01: Emit skill packages for all hosts, or only v1 live-capable hosts?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Follow `generate_adapter_bundle`'s existing v1-vs-deferred host distinction (host_adapters.py:62-66); emit for the hosts the bundle already generates, no new host policy here.

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
