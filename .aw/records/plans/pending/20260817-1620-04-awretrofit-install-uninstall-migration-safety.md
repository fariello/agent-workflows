# IPD: Install scaffolder + uninstall --deep + migration-engine cleanup/move safety

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 findings S2-B02, S2-B03, S2-M01, S2-L01: (B02) the install/setup scaffolder writes the records tree into legacy `.agents/` (engine.py constants 3699/3707/3725/3750) re-introducing split-brain on a fresh install; (B03) `aw uninstall --deep` cleans only `.agents/*` (engine.py:3423-3430) despite help promising `.aw/records/`; (M01) `cleanup_migration` can `rmtree`/`unlink` a re-created legacy source path and `_perform_move` clobbers a pre-existing destination unconditionally; (L01) leftover `remove` marks a path "removed" on `git rm` failure then force-unlinks, and rollback config write is non-atomic.
- Scope: Make the install scaffolder + `uninstall --deep` layout-aware and harden the migration engine's cleanup/move/rollback against destroying re-created or foreign content. OUT: the record-VERB cluster (Order 01, done) and shipped docs (Order 02).
- Status: to-review
- Set: awretrofit
- Order: 4
- Highest E allocated: 06
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: y5zxql

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from release-review run 20260817-153418 findings S2-B02/B03/M01/L01 (Set awretrofit Order 04).

## Goal

Stop a fresh/migrated `.aw/` repo from being pushed back into split-brain by the install/uninstall
paths, and close the migration-engine data-safety gaps that could delete re-created or foreign content.
Per D136, a fresh install materializes `.aw/` only; `uninstall --deep` must reach `.aw/records/`; and
the migration engine must never destroy content it did not itself create.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: install scaffolder targets .aw/records (B02, per D136)

- [ ] E-01 Make `create_setup_artifacts` (engine.py ~4190) scaffold the plans/docs/prompts/comms lifecycle under `.aw/records/` on a fresh/`aw`-layout install instead of the hardcoded `.agents/*` constants (engine.py:3699/3707/3725/3750), deriving the record roots from the resolved target layout (D136: fresh install = `.aw/` only). Route the creating writes through `guard_write` where practical so the "no legacy writes" contract actually covers scaffolding. Preserve the `--undo` manifest recording.
  - Depends on: none
  - Expected outcome: `aw setup`/install on a fresh repo creates `.aw/records/{plans,docs,prompts,comms}/...`, not `.agents/*`; a legacy-targeted install (if still supported) still works.
  - Execution state: pending

### Task group 2: uninstall --deep reaches .aw/records (B03)

- [ ] E-02 Extend `_DEEP_CLEANUP_ROOTS` (engine.py:3423-3430) / `plan_deep_cleanup` so `aw uninstall --deep` targets the `.aw/records/{plans,docs,prompts,comms}` roots (layout-aware) in addition to the legacy `.agents/*`, matching the cli.py:523 help promise. Keep the existing safety confirmations.
  - Depends on: none
  - Expected outcome: `aw uninstall --deep` (dry-run) on a migrated repo lists `.aw/records/*` for removal; help and behavior agree.
  - Execution state: pending

### Task group 3: migration-engine data-safety (M01, L01)

- [ ] E-03 Harden `cleanup_migration` (layout_migration.py ~1158-1165): before deleting a manifest `legacy_sources` path, re-verify git tracking/ignore state (reuse `_is_removable_leftover`'s logic) and NEVER `rmtree` a directory that now holds content not recorded in the manifest; refuse (and report) on unexpected content instead of `ignore_errors=True` deletion.
  - Depends on: none
  - Expected outcome: a re-created untracked file/dir at a former legacy source path SURVIVES `aw migrate-layout cleanup --confirm`; only manifest-recorded, still-matching content is removed.
  - Execution state: pending

- [ ] E-04 Harden `_perform_move` (layout_migration.py ~304-308): only clobber a destination that the CURRENT transaction's journal recorded as its own; if a foreign pre-existing destination is found, fail closed and surface a conflict rather than unconditional `rmtree`/`unlink`.
  - Depends on: none
  - Expected outcome: a move refuses to destroy a pre-existing destination it did not create; a normal (fresh-destination) move is unchanged.
  - Execution state: pending

- [ ] E-05 Fix leftover `remove` result honesty + atomic rollback (L01): on `git rm` failure distinguish a `degraded`/`unlinked-untracked` outcome from a clean `removed` in the result; and make `rollback_migration`'s config write use the temp-file + `os.replace` idiom used elsewhere.
  - Depends on: none
  - Expected outcome: the leftover result never labels a git-failed force-unlink as a clean `removed`; a crash mid-rollback cannot truncate `config.json`.
  - Execution state: pending

### Task group 4: tests

- [ ] E-06 Add regression tests: (a) fresh install scaffolds `.aw/records/*` not `.agents/*` (B02); (b) `uninstall --deep` dry-run targets `.aw/records/*` (B03); (c) cleanup preserves re-created untracked content (M01); (d) `_perform_move` refuses a foreign destination (M01); (e) leftover result distinguishes degraded removal + atomic rollback config (L01). Each falsifiable.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: new tests green; each fails against the pre-fix behavior (spot-check at least the M01 cleanup-preservation and B02 scaffold cases).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- D136: a fresh install materializes `.aw/` only (no legacy `.agents/` scaffolding); legacy is detected + offered migration. This resolves B02's "intended target" question - it is `.aw/records/`.
- `resolve_target_layout(repo_root)` governs the workflow BUNDLE path only; the record-scaffold constants (engine.py:3699/3707/3725/3750) were never wired to it - that is the B02 gap.
- `_is_removable_leftover` (layout_migration.py, from IPD wvlk84) is the proven tracked/ignored guard; reuse it for cleanup.
- Move-not-copy engine already journals per-item + hash-verifies; the M01/E-04 gap is only the unconditional destination clobber + the cleanup of re-created sources.

## Findings

| id | area | evidence | issue |
|---|---|---|---|
| B02 | install scaffolder | engine.py:3699/3707/3725/3750 + create_setup_artifacts ~4190 | fresh scaffold writes `.agents/*` (split-brain) |
| B03 | uninstall --deep | engine.py:3423-3430 vs cli.py:523 help | deep clean misses `.aw/records/*` |
| M01a | cleanup_migration | layout_migration.py ~1158-1165 | rmtree/unlink re-created legacy source (ignore_errors) |
| M01b | _perform_move | layout_migration.py ~304-308 | unconditional destination clobber |
| L01a | leftover remove | layout_migration.py ~414-417 | git-rm-fail force-unlink mislabeled `removed` |
| L01b | rollback config | layout_migration.py ~1042-1043 | non-atomic write vs the atomic idiom elsewhere |

## Proposed changes (ordered, validatable)

1. E-01 scaffolder -> `.aw/records/` (D136). 2. E-02 uninstall --deep -> `.aw/records/`.
3. E-03 cleanup re-verify guard. 4. E-04 move foreign-destination refusal.
5. E-05 leftover-result honesty + atomic rollback. 6. E-06 regression tests.

## Deferred / out of scope (with reason)

- Record VERBS (Order 01, done); shipped docs (Order 02); help/docstrings (Order 05).

## Scope check

- Over-scope: none - each item is a reproduced finding; E-03/E-04 are conservative guards, not a redesign.
- Under-scope: none - B02+B03+M01+L01 are the full install/uninstall/migration-safety set from the run.

## Required tests / validation

- New regression tests (E-06) fail-before/pass-after on the M01 cleanup-preservation + B02 scaffold cases.
- Fresh-install repro scaffolds `.aw/records/*`; `uninstall --deep` dry-run lists `.aw/records/*`.
- Full serial suite >= 982 passed / 1 skipped; `aw attention --check`/`sanitize --agent` clean; wheel unaffected.
- The existing migration test suite (test_layout_migration, test_awphysical_*) stays green (no regression to move/rollback/resume).

## Spec / documentation sync

- D136 already documents fresh-install=`.aw/`-only; this Order makes the install path CONFORM to it.
  Note completion in the orchestrator. cli.py:523 help already promises `.aw/records/` (E-02 makes it true).

## Open questions

### OQ-01: Should a fresh install still scaffold legacy `.agents/`?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: NO - D136 is explicit that a fresh install materializes `.aw/`
  only. B02 is a straight conformance fix to the documented decision, not a new design choice.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a fresh-install repro (or test) creates `.aw/records/{plans,docs,prompts,comms}` and NO `.agents/*`. Paste the created tree / test output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw uninstall --deep` dry-run on a migrated fixture lists `.aw/records/*` for removal (matching cli.py:523 help). Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: a test where a legacy source path is re-created (untracked) after migration shows `cleanup_migration` PRESERVES it (survives + reported refused), while a manifest-matching source is still removed. Paste test output.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: a test where a foreign file pre-exists at a move destination shows `_perform_move` refuses/raises rather than clobbering; a fresh-destination move is unchanged. Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: a test shows the leftover result labels a git-rm-failed force-unlink as degraded (not clean `removed`), and rollback config uses temp+os.replace (atomic). Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: all new regression tests pass; documented fail-before/pass-after on the M01 cleanup-preservation + B02 scaffold cases; full serial suite >= 982 passed / 1 skipped; existing migration suite green. Paste.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
implements E-01..E-06, pastes actual evidence (fresh-install tree, uninstall dry-run, the M01/L01
regression tests with fail-before/pass-after, full serial + migration suites), commits only the scoped
paths (`agent_workflows/engine.py`, `agent_workflows/layout_migration.py`, and the new/edited tests),
never pushes, runs `aw ipd lint --phase pre-transition` + the full suite before transition, and the
orchestrator owns the move to `executed/`. MEDIUM risk (core install + migration paths) - the guards
are conservative (fail-closed / preserve) and each is test-gated.
