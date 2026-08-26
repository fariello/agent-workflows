# IPD: Emit skill package + adapter bundle from install_all across hosts, with uninstall/idempotency/install-diff tests

- Date: 2026-08-25
- Kind: child
- Concern: `engine.install_all` (engine.py:1953) writes only `body_members` + `shim_members`; the generated skill packages (`host_adapters.build_skill_package(...).to_files()`, host_adapters.py:349/227) and per-host adapter bundle (`host_adapters.generate_adapter_bundle`, host_adapters.py:677) are never emitted by a real install. This child wires that emission in.
- Scope: Extend the installer run path to emit skill/adapter members: (1) in `install_into_repo` (engine.py:4893), build the skill/adapter member map via `generate_adapter_bundle`/`build_skill_package(...).to_files()` and merge it into the desired member set passed to `install_all` (engine.py:1953), writing them with the SAME idempotent write + skip-unchanged logic as `shim_members`; (2) include the skill/adapter members in the uninstall member set so `uninstall_repo` (engine.py:3836) removes them; (3) ensure the install-diff computation (the desired-set union at engine.py:2062) accounts for them so a re-install is a no-op. Extend install tests: a fresh install produces the skill package + adapter bundle for each generated host; a second install is idempotent (empty diff); uninstall removes them; no duplication.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/host_adapters.py, tests/
- Status: draft
- Set: installerskill
- Order: 1
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: kvfsak

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Wire skill-package + adapter-bundle emission into `install_all`/`install_into_repo`, writing them with the same idempotent path as shim members, removed on uninstall, and accounted for in install-diff, with tests across hosts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: emit + install

- [ ] E-01 In `install_into_repo` (engine.py:4893), build a skill/adapter member map via `host_adapters.generate_adapter_bundle` + `build_skill_package(...).to_files()` and merge it into the desired member set given to `install_all` (engine.py:1953), written with the SAME idempotent skip-unchanged logic as `shim_members`.
  - Depends on: none
  - Expected outcome: a fresh `aw install` writes the skill package + adapter bundle files for each generated host.
  - Execution state: pending

### Task group 2: uninstall + idempotency

- [ ] E-02 Include skill/adapter members in the uninstall member set (`uninstall_repo`, engine.py:3836) and in the desired-set union used for install-diff (engine.py:2062), so uninstall removes them and re-install is a no-op.
  - Depends on: E-01
  - Expected outcome: `uninstall` removes the emitted members; a second `install` produces an empty diff (idempotent).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `install_all` (engine.py:1953) writes `body_members` + `shim_members` with idempotent skip-unchanged; the desired set is `set(body_members) | set(shim_members)` (engine.py:2062). Skill/adapter members must join this set the same way.
- `host_adapters.generate_adapter_bundle` (host_adapters.py:677) + `build_skill_package(...).to_files()` (host_adapters.py:349/227) are the existing generators (execset proved digest parity); reuse, do not fork.
- execset deliberately deferred this wiring (D21-2h7777-D2); this child closes exactly that gap.

## Findings

The generators already exist and are verified; the work is purely wiring their output into the installer's member set + uninstall + diff, matching the shim-member pattern.

## Proposed changes (ordered, validatable)

1. `engine.py` `install_into_repo`: merge skill/adapter members into the desired set.
2. `engine.py` `uninstall_repo` + install-diff union: include them.
3. `tests/`: fresh-install emits (per host), re-install idempotent, uninstall removes.

## Deferred / out of scope (with reason)

- Skill/adapter CONTENT generation: already delivered by execset; not touched here.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- A fresh install into a temp repo emits the skill package + adapter bundle members for each generated host (assert files present).
- A second install yields an empty install-diff (idempotent, no duplication).
- `uninstall` removes exactly the emitted skill/adapter members and nothing else.

## Spec / documentation sync

- Update installer docs to note skill/adapter emission is part of `aw install`.

## Open questions

### OQ-01: Should skill/adapter members live under a distinct target subdir or alongside shims?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Follow whatever target layout `build_skill_package.to_files()` / `generate_adapter_bundle` already encode in their relative paths; do not invent a new layout here.

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
