# IPD: Full Command-Surface Migration and Compatibility

- Date: 2026-08-22
- Kind: child
- Concern: Apply the dual-audience contract to every current and future command.
- Scope: Read, check, preview, mutation, interactive, family, bare, and alias paths.
- Status: draft
- Set: awcliux
- Order: 4
- Highest E allocated: 03
- Author: OpenAI
- Id: 10jpsa

## Workflow history

- 2026-08-22 draft (OpenAI): created from `_build_parser()` inventory.

## Goal

Migrate the parser surface in three bounded families so no print path or alias bypasses the shared renderers.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Reads and checks

- [ ] E-01 Migrate status/context/path/project/storage reads; attention/todo/IPD board; workflow/research reads; show/find/search/index/check; doctor; specs/backlog checks; and sanitizer.
  - Depends on: none
  - Expected outcome: consistent modes, facts, errors, empty states, and limits.
  - Execution state: pending

### Material change 2: Previews and mutations

- [ ] E-02 Migrate install/setup/uninstall, include/exclude/config, normalization, artifact writes, project/storage changes, rename/group/archive, migrations, and sanitizer fixes to previews, confirmations, receipts, and verification states.
  - Depends on: none
  - Expected outcome: agents get safe structured failure or explicit receipts; humans retain decision-ready prompts.
  - Execution state: pending

### Material change 3: Entrypoints and prevention

- [ ] E-03 Route bare `aw`, empty families, `help`, aliases, and module entrypoints through the boundary; fail CI when a parser leaf lacks a contract declaration.
  - Depends on: E-01, E-02
  - Expected outcome: aliases are agent-byte-equivalent and new commands cannot land uncovered.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The audited parser has 69 paths including families/aliases; 29 expose `--agent`, 18 expose `--json`, and many writes expose neither.
- `--agent` never implies `--yes` or mutation permission. Non-TTY confirmation failures need structured next actions.
- Preserve dry-run defaults.

## Findings

Risk is concentrated in direct printing, divergent flags, and mixed domain/cannot-run errors. Use a generated inventory and family adapters, not a monolithic rewrite.

## Proposed changes (ordered, validatable)

Inventory fields: command, class, human recipe, agent record kind, mutation gate, legacy flags, exit contract, migrated, tested.

```json
{"schema":"aw.agent/v1","kind":"result","cmd":"backlog set","outcome":"changed","exit":0,"applied":true,"complete":true,"changed":["records/backlog/done/..."],"verified":true,"evidence":["backlog-check"],"next":null}
```

Do not infer audience from stdin: piped stdin may answer a prompt, but piped stdout still selects agent output and explicit safety policy still governs mutation.

## Deferred / out of scope (with reason)

- Command renames belong to `awcmdsurf`; domain refactors require separate corrective IPDs.

## Scope check

- Over-scope: none.
- Under-scope: inventory standalone installer scripts and explicitly include or exclude them.

## Required tests / validation

Run generated inventory, family, alias, bare/family dispatch, safety, direct-print scan, and existing regression tests; compare typed facts across renderers.

## Spec / documentation sync

Replace divergent per-command agent prose with links to the canonical contract.

## Open questions

### OQ-01: Do `--json` and `--format json` remain?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: retain as explicit full-detail formats; `--agent` is compact and conflicting flags are usage errors.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: generated read/check inventory has no unmigrated row and all scenario tests pass.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: exactly three migrations cover read, write, and entrypoint/prevention surfaces.

Review and explicit approval required. Preserve semantics and safety; split any domain change.
