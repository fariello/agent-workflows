# IPD: Migrate existing on-disk research docs status intake -> todo and regenerate the index, with backward-compatible read

- Date: 2026-08-27
- Kind: child
- Concern: With the code token renamed to `todo` (child 01, backward-compat accepts legacy `intake`), the ~10 existing on-disk research docs still carry `status: intake` in frontmatter. They must be migrated to `status: todo` and the INDEX regenerated, so the corpus matches the new vocab and the board/index show `todo`.
- Scope: Migrate every on-disk research doc whose frontmatter `status:` is `intake` to `todo` (found ~10 via `grep -rl '^status: intake' .aw/records/research/`), preserving all other frontmatter, then regenerate `INDEX.json`/`INDEX.md` (`aw research index`). Use the naming/frontmatter tooling, not a blind sed, so it goes through the contract. Verify `aw research index --check` is clean and `aw attention` shows the migrated docs as READY `todo`. This depends on child 01 (the contract must ACCEPT `todo` first, and keep accepting `intake` during the window). Add a test that a doc created with legacy `intake` is migrated to `todo` and that `aw research index --check` passes post-migration.
- Scope-Paths: .aw/records/research/, agent_workflows/research_cmd.py, agent_workflows/research_index.py, tests/
- Status: draft
- Set: rstodo
- Order: 2
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: lpqy64

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Migrate the ~10 existing on-disk research docs from `status: intake` to `status: todo` (through the contract, not a blind sed), regenerate the INDEX, and verify the board/index show `todo` and `aw research index --check` is clean.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: migrate + reindex

- [ ] E-01 Identify every research doc with frontmatter `status: intake` (`grep -rl '^status: intake' .aw/records/research/`; ~10 today), rewrite each to `status: todo` preserving all other frontmatter (via the frontmatter tooling / a contract-aware helper, not a blind sed), then run `aw research index` to regenerate INDEX.json/INDEX.md. Confirm `aw research index --check` is clean and `aw attention` lists the migrated docs as READY.
  - Depends on: none
  - Expected outcome: zero `^status: intake` docs remain; all are `status: todo`; INDEX regenerated; `aw research index --check` clean; board shows them READY.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- ~10 docs currently carry `^status: intake` (verified). Includes this session's sk94i0/40g511/3nlmug/ud28vy and older intake docs.
- `aw research index` regenerates the manifest from frontmatter; `--check` fails on drift. Migrate through the contract so normalization/validation applies.
- Depends on child 01: the contract must accept `todo` (and still accept legacy `intake` during the window) before/at migration.

## Findings

Mechanical data migration; the only risk is doing it OUTSIDE the contract (blind sed could miss normalization or corrupt frontmatter), so route through the frontmatter tooling and re-validate with `index --check`.

## Proposed changes (ordered, validatable)

1. Rewrite the ~10 docs' `status: intake` -> `status: todo` via contract-aware tooling.
2. `aw research index` regenerate; confirm `--check` clean.
3. `tests/`: a doc with legacy `intake` migrates to `todo`; post-migration `index --check` passes.

## Deferred / out of scope (with reason)

- The code token rename + backward-compat read: child 01 (dependency).
- Dropping the `intake` compat alias: orchestrator OQ-01 (post-migration + one release).

## Scope check

- Over-scope: none.
- Under-scope: none (all on-disk docs + INDEX covered).

## Required tests / validation

- `grep -rl '^status: intake' .aw/records/research/` returns nothing after migration.
- Each migrated doc is `status: todo` with all other frontmatter intact.
- `aw research index --check` is clean; `aw attention` shows the migrated docs READY.

## Spec / documentation sync

- N/A (data migration; vocab docs updated in child 01).

## Open questions

### OQ-01: Migrate under a --dry-run/--apply gate (recommended) to preview the ~10 rewrites?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Yes - preview the exact set of files first, then apply, so the migration is auditable. Use the tooling's standard dry-run/apply pattern.

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
