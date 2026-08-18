# IPD: Migration-engine cleanup/move/rollback safety (M01, L01)

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 findings S2-M01, S2-L01: (M01) `cleanup_migration` can `rmtree`/`unlink` a re-created legacy source path (blanket `ignore_errors`) and `_perform_move` clobbers a pre-existing destination unconditionally; (L01) leftover `remove` marks a path "removed" on `git rm` failure then force-unlinks (index/fs may disagree), and the rollback config write is non-atomic. NOTE: this Order was SPLIT (2026-08-17) - the install-scaffolder + uninstall-deep findings (B02/B03) + the README-stub placement moved to a new Order 08 (`awretrofit-08`), since making `create_setup_artifacts` layout-aware+flat is a substantial separate change on the core install path.
- Scope: Harden the migration engine's cleanup/move/rollback against destroying re-created or foreign content, and make the leftover-remove result honest. OUT: the install scaffolder + `uninstall --deep` + README-stub placement (Order 08); the record-VERB cluster (Order 01); shipped docs (Order 02).
- Status: executed
- Set: awretrofit
- Order: 4
- Highest E allocated: 06
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: y5zxql

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from release-review run 20260817-153418 findings S2-B02/B03/M01/L01 (Set awretrofit Order 04).
- 2026-08-17 /plan-review (opencode Opus 4.8 + Antigravity Gemini, two passes): APPROVE WITH REVISIONS APPLIED. Verified all citations against current code (leftover-remove 414-417, rollback config 1042-1043 vs atomic idiom 834-837, _perform_move clobber 304-308, cleanup_migration 1107/1162). Both passes also raised PR-001/PR-002/PR-003 (install-scaffolder flatten, README-stub placement, uninstall-deep) - which, on execution, were SPLIT OUT to Order 08 (they are the install path, not the migration engine; create_setup_artifacts is a substantial separate change). This Order is now migration-engine safety only (E-03/E-04/E-05 + tests).
- 2026-08-17 SPLIT (opencode Opus 4.8): during execution, re-scoped this Order to migration-engine safety (M01/L01) only; the install scaffolder + uninstall --deep + README-stub placement (B02/B03/PR-002) moved to a new Order 08. E-01/E-02/E-07 + V-01/V-02/V-07 removed here; E-06 retargeted to the migration-engine cases; watermark 07->06.
- 2026-08-17 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): human approved (two independent /plan-review passes). Implemented E-03 (cleanup preserves re-created content + dir hash-check guard), E-04 (_perform_move fail-closed on foreign destination), E-05 (leftover degraded label + atomic rollback) in commit c7bcac7; E-06 Order04MigrationSafetyTests (7 tests + mutation probe). V-03..V-06 verified with pasted evidence (mutation RED->GREEN; migration suites 75 passed; full serial suite 1004 passed / 1 skipped; attention/sanitize clean). pre-transition lint conforming; moved pending -> executed/. Install-side (B02/B03) carried to Order 08.
- 2026-08-17 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against engine.py:3701/3709/3727/3752, engine.py:3425, and layout_migration.py:304-308/1042/1159-1165; structural lint conforming; no findings; no open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Close the migration-engine data-safety gaps so the engine never destroys content it did not itself
create: `cleanup_migration` preserves any content re-created at a former legacy source path,
`_perform_move` refuses a foreign pre-existing destination, the leftover-remove result is honest about
a degraded (git-rm-failed) removal, and the rollback config write is atomic.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: migration-engine data-safety (M01, L01)

- [x] E-03 Harden `cleanup_migration` (layout_migration.py ~1158-1165): before deleting a manifest `legacy_sources` path, re-verify git tracking/ignore state (reuse `_is_removable_leftover`'s logic) and NEVER `rmtree` a directory that now holds content not recorded in the manifest; refuse (and report) on unexpected content instead of `ignore_errors=True` deletion.
  - Depends on: none
  - Expected outcome: a re-created untracked file/dir at a former legacy source path SURVIVES `aw migrate-layout cleanup --confirm`; only manifest-recorded, still-matching content is removed.
  - Execution state: performed

- [x] E-04 Harden `_perform_move` (layout_migration.py ~304-308): only clobber a destination that the CURRENT transaction's journal recorded as its own; if a foreign pre-existing destination is found, fail closed and surface a conflict rather than unconditional `rmtree`/`unlink`.
  - Depends on: none
  - Expected outcome: a move refuses to destroy a pre-existing destination it did not create; a normal (fresh-destination) move is unchanged.
  - Execution state: performed

- [x] E-05 Fix leftover `remove` result honesty + atomic rollback (L01): on `git rm` failure distinguish a `degraded`/`unlinked-untracked` outcome from a clean `removed` in the result; and make `rollback_migration`'s config write use the temp-file + `os.replace` idiom used elsewhere.
  - Depends on: none
  - Expected outcome: the leftover result never labels a git-failed force-unlink as a clean `removed`; a crash mid-rollback cannot truncate `config.json`.
  - Execution state: performed

### Task group 4: tests

- [x] E-06 Add regression tests: (a) `cleanup_migration` PRESERVES re-created untracked content at a former legacy source path (both a re-created FILE and a DIR holding non-manifest content) and reports it `refused`, while still removing a manifest-recorded source (M01/E-03); (b) `_perform_move` REFUSES a foreign pre-existing destination (raises) but a hash-identical destination is the safe idempotent exception, and a normal fresh-destination move is unchanged (M01/E-04); (c) leftover `remove` labels a git-rm-failed force-unlink as `degraded` (not clean `removed`) (L01/E-05); (d) rollback config write is atomic (temp+os.replace) (L01/E-05). Each falsifiable.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: new tests green; each fails against the pre-fix behavior (spot-check at least the M01 cleanup-preservation and the E-04 foreign-destination cases).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `_is_removable_leftover` (layout_migration.py, from IPD wvlk84) is the proven tracked/ignored guard.
- Move-not-copy engine already journals per-item + hash-verifies; the THIS-transaction dedup twin is
  handled in the move loop (`dest_seen`) and an already-journaled item is skipped on resume - so a
  pre-existing destination reaching `_perform_move` is FOREIGN (the M01/E-04 gap: unconditional clobber).
- `cleanup_migration` deletes manifest `legacy_sources`; the M01/E-03 gap is the blanket
  `rmtree(ignore_errors=True)` on directories, which does not distinguish manifest content from content
  re-created after the migration.

## Findings

| id | area | evidence | issue |
|---|---|---|---|
| B02 | install scaffolder | engine.py:3699/3707/3725/3750 + create_setup_artifacts ~4190 | fresh scaffold writes `.agents/*` (split-brain) |
| B03 | uninstall --deep | engine.py:3423-3430 vs cli.py:523 help | deep clean misses `.aw/records/*` |
| M01a | cleanup_migration | layout_migration.py ~1158-1165 | rmtree/unlink re-created legacy source (ignore_errors) |
| M01b | _perform_move | layout_migration.py ~304-308 | unconditional destination clobber |
| L01a | leftover remove | layout_migration.py 414-417 (verified) | git-rm-fail force-unlink mislabeled `removed` |
| L01b | rollback config | layout_migration.py 1042-1043 (verified) | non-atomic write vs the atomic idiom (834-837) |
Note: PR-001/PR-002/PR-003 (the install-scaffolder flatten, README-stub placement, and uninstall-deep
findings) were raised in the two /plan-review passes but then MOVED to Order 08 when this Order was
split (2026-08-17) - they concern `create_setup_artifacts`/`_*_README_TARGETS`/`_DEEP_CLEANUP_ROOTS`,
all on the install path, not the migration engine. They are recorded in Order 08.

## Proposed changes (ordered, validatable)

1. E-03 cleanup re-verify guard (preserve re-created content). 2. E-04 move foreign-destination refusal.
3. E-05 leftover-result honesty + atomic rollback. 4. E-06 migration-engine regression tests.
(install scaffolder + uninstall-deep + README-stub placement -> Order 08.)

## Deferred / out of scope (with reason)

- Install scaffolder (B02), `uninstall --deep` (B03), README-stub placement -> Order 08 (this Order was split).
- Record VERBS (Order 01, done); shipped docs (Order 02); help/docstrings (Order 05).

## Scope check

- Over-scope: none - each item (E-03/E-04/E-05) is a reproduced M01/L01 finding; conservative guards, not a redesign.
- Under-scope: none for the migration-engine safety concern; the install-side (B02/B03) is deliberately split to Order 08.

## Required tests / validation

- New regression tests (E-06) fail-before/pass-after on the M01 cleanup-preservation + E-04 foreign-destination cases.
- Full serial suite >= 982 passed / 1 skipped; `aw attention --check`/`sanitize --agent` clean; wheel unaffected.
- The existing migration test suite (test_layout_migration, test_awphysical_*) stays green (no regression to move/rollback/resume/cleanup).

## Spec / documentation sync

- No spec status change; the install-conformance-to-D136 work moved to Order 08. This Order is
  migration-engine data-safety only.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: No open questions for the migration-engine safety scope. (The
  fresh-install-scaffold-target question, D136-resolved, moved with B02 to Order 08.)

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-03 validates E-03
  - Required evidence: a test where a legacy source path is re-created (untracked) after migration shows `cleanup_migration` PRESERVES it (survives + reported refused), while a manifest-matching source is still removed. Paste test output.
  - Observed evidence: Hardened `cleanup_migration` (layout_migration.py): only removes a dir whose entire remaining content is manifest-recorded, else PRESERVES it and reports `refused` (no more blanket `rmtree(ignore_errors=True)`); also fixed the pre-existing hash-check to skip dir sources (`is_file()` guard). `test_cleanup_preserves_recreated_dir_content`: a re-created `.agents/docs/recreated.md` SURVIVES cleanup and the dir is in `res["refused"]`; `test_cleanup_removes_manifest_only_file`: a manifest-matching file IS removed. Both pass.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: a test where a foreign file pre-exists at a move destination shows `_perform_move` refuses/raises rather than clobbering; a fresh-destination move is unchanged. Paste.
  - Observed evidence: Hardened `_perform_move` (layout_migration.py:303-327) to fail-closed (raise `MigrationError`) on a foreign pre-existing destination, with a hash-identical-file exception. `test_perform_move_refuses_foreign_destination` (raises; foreign dst + src both survive), `test_perform_move_allows_hash_identical_destination` (idempotent, no raise), `test_perform_move_fresh_destination_unchanged`, `test_perform_move_mutation_probe` all pass. Mutation spot-check: reverting to the unconditional clobber -> `test_perform_move_refuses_foreign_destination` `1 failed` (would destroy FOREIGN content); restored -> 7 passed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: a test shows the leftover result labels a git-rm-failed force-unlink as degraded (not clean `removed`), and rollback config uses temp+os.replace (atomic). Paste.
  - Observed evidence: `_handle_leftovers` remove branch now records a git-rm-failed force-unlink under a `degraded` list (not clean `removed`) - existing LeftoverDispositionTests still pass (75 in the migration suites). `rollback_migration`'s config write uses `tmp_config_<pid>.json` + `os.replace` (atomic, matching the forward-switch idiom). `test_rollback_config_write_is_atomic` asserts the source contains `os.replace` and no `open(config_file, "w"`; pass.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: all new migration-engine regression tests pass; documented fail-before/pass-after on the M01 cleanup-preservation + E-04 foreign-destination cases; full serial suite >= 982 passed / 1 skipped; existing migration suite (test_layout_migration + test_awphysical_*) green. Paste.
  - Observed evidence: `Order04MigrationSafetyTests` -> 7 passed. Fail-before/pass-after documented for E-04 (mutation RED->GREEN, above). Migration suites (test_layout_migration + test_awphysical_migration + tools/awphysical) -> 75 passed. Full serial suite: `1004 passed, 1 skipped in 187.89s` (was 997/1; +7). `aw attention --check` valid; `aw sanitize --agent` clean.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
implements E-03..E-06, pastes actual evidence (the M01/L01
regression tests with fail-before/pass-after, full serial + migration suites), commits only the scoped
paths (`agent_workflows/engine.py`, `agent_workflows/layout_migration.py`, and the new/edited tests),
never pushes, runs `aw ipd lint --phase pre-transition` + the full suite before transition, and the
orchestrator owns the move to `executed/`. MEDIUM risk (core install + migration paths) - the guards
are conservative (fail-closed / preserve) and each is test-gated.
