# IPD: Install scaffolder + uninstall --deep + migration-engine cleanup/move safety

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 findings S2-B02, S2-B03, S2-M01, S2-L01: (B02) the install/setup scaffolder writes the records tree into legacy `.agents/` (engine.py constants 3699/3707/3725/3750) re-introducing split-brain on a fresh install; (B03) `aw uninstall --deep` cleans only `.agents/*` (engine.py:3423-3430) despite help promising `.aw/records/`; (M01) `cleanup_migration` can `rmtree`/`unlink` a re-created legacy source path and `_perform_move` clobbers a pre-existing destination unconditionally; (L01) leftover `remove` marks a path "removed" on `git rm` failure then force-unlinks, and rollback config write is non-atomic.
- Scope: Make the install scaffolder + `uninstall --deep` layout-aware and harden the migration engine's cleanup/move/rollback against destroying re-created or foreign content. OUT: the record-VERB cluster (Order 01, done) and shipped docs (Order 02).
- Status: reviewed
- Set: awretrofit
- Order: 4
- Highest E allocated: 07
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: y5zxql

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from release-review run 20260817-153418 findings S2-B02/B03/M01/L01 (Set awretrofit Order 04).
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Structural preflight conforming. Re-verified ALL citations against current code (post Orders 01/02/07): scaffolder constants engine.py:3701/3709/3727/3752; README targets 4061/4105/4147; _DEEP_CLEANUP_ROOTS:3425; _perform_move clobber 304-308; cleanup_migration 1107/1162; leftover-remove 414-417; rollback config 1042-1043 (non-atomic) vs atomic idiom 834-837 - all accurate. Findings: PR-001 (HIGH) E-01/E-02 target set was stale - Order 07 flattened `.aw/records/docs/` away, so DERIVE roots from the resolver + use the FLAT layout (no `docs/`); PR-002 (HIGH) added E-07 for the README-stub PLACEMENT (`_*_README_TARGETS`/ensure_*_readmes, legacy-hardcoded + the Order-07-obsoleted `.agents/docs/README.md`) that Order 07 explicitly handed to this Order; PR-003 (MED) E-02 deep-cleanup roots likewise flat/resolver-derived. All FIXED in plan (E-07 added, E-06/V-07 extended). OQ-01 resolved (D136 fresh=.aw/-only). No open questions. GO - PENDING HUMAN APPROVAL.
- 2026-08-17 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against engine.py:3701/3709/3727/3752, engine.py:3425, and layout_migration.py:304-308/1042/1159-1165; structural lint conforming; no findings; no open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Stop a fresh/migrated `.aw/` repo from being pushed back into split-brain by the install/uninstall
paths, and close the migration-engine data-safety gaps that could delete re-created or foreign content.
Per D136, a fresh install materializes `.aw/` only; `uninstall --deep` must reach `.aw/records/`; and
the migration engine must never destroy content it did not itself create.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: install scaffolder targets .aw/records (B02, per D136)

- [ ] E-01 Make `create_setup_artifacts` (engine.py ~4192) scaffold the records lifecycle under `.aw/records/` on a fresh/`aw`-layout install instead of the hardcoded legacy `.agents/*` constants (engine.py:3701 PLANS_DIR, 3709 DOCS_DIR, 3727 PROMPTS_DIR, 3752 COMMS_DIR). **plan-review PR-001 (post-Order-07 layout):** the FINAL layout is FLAT `.aw/records/{plans,prompts,comms,backlog,research,specs,walkthroughs,roadmaps,prompt-library}` - there is NO `.aw/records/docs/` level anymore (Order 07 flattened it). Do NOT hardcode a new `.aw/records/{plans,docs,...}` list; DERIVE the record roots from the canonical resolver (`record_producers.resolve_record_path(<class>)` / the RecordClass set) so the scaffolder cannot drift from the real layout again (that drift is the root cause of this whole Set). Route the creating writes through `guard_write` where practical. Preserve the `--undo` manifest recording. Keep a legacy-targeted install working (if `resolve_target_layout` -> legacy).
  - Depends on: none
  - Expected outcome: `aw setup`/install on a fresh repo creates the FLAT `.aw/records/*` tree (derived from the resolver, no `docs/` level), not `.agents/*`; a legacy install still scaffolds `.agents/*`.
  - Execution state: pending

- [ ] E-07 **plan-review PR-002 (README-stub placement, folded from Order 07):** the installer README-stub placement is ALSO legacy-hardcoded and post-Order-07-stale: `_PLANS_README_TARGETS` (engine.py:4061 -> `.agents/README.md`), `_DOCS_README_TARGETS` (engine.py:4105 -> `.agents/docs/README.md` + the `agents-docs-README.md` stub that Order 07 obsoleted when it removed the `docs/` level), `_PROMPTS_README_TARGETS` (engine.py:4147 -> `PROMPTS_DIR/README.md`), and `ensure_plans_readmes`/`ensure_docs_readmes`/`ensure_prompts_readmes` (called at ~4395-4398). Repoint these to drop the README stubs into the FLAT `.aw/records/*` dirs on an `aw`-layout install, derived from the same resolver as E-01. Drop the obsolete top-level `docs/` README target (there is no `.aw/records/docs/`); if per-type README stubs are wanted, place them at `.aw/records/{research,specs,walkthroughs,roadmaps}` (the Order-02 templates were already retitled to these flat paths).
  - Depends on: E-01
  - Expected outcome: a fresh `aw`-layout install drops README stubs into the flat `.aw/records/*` dirs (not `.agents/*`, no `.aw/records/docs/README.md`); legacy install unchanged.
  - Execution state: pending

### Task group 2: uninstall --deep reaches .aw/records (B03)

- [ ] E-02 Extend `_DEEP_CLEANUP_ROOTS` (engine.py:3425) / `plan_deep_cleanup` so `aw uninstall --deep` targets the FLAT `.aw/records/*` roots (layout-aware, derived from the resolver like E-01 - NOT a hardcoded `.aw/records/{plans,docs,...}` list; note post-Order-07 there is no `docs/` level) in addition to the legacy `.agents/*`, matching the cli.py:523 help promise. Keep the existing safety confirmations.
  - Depends on: none
  - Expected outcome: `aw uninstall --deep` (dry-run) on a migrated repo lists the flat `.aw/records/*` roots for removal; help and behavior agree.
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

- [ ] E-06 Add regression tests: (a) fresh install scaffolds the FLAT `.aw/records/*` not `.agents/*` and NO `.aw/records/docs/` (B02); (b) fresh install drops README stubs into the flat `.aw/records/*` dirs, no `.aw/records/docs/README.md` (E-07); (c) `uninstall --deep` dry-run targets the flat `.aw/records/*` (B03); (d) cleanup preserves re-created untracked content (M01); (e) `_perform_move` refuses a foreign destination (M01); (f) leftover result distinguishes degraded removal + atomic rollback config (L01). Each falsifiable.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-07
  - Expected outcome: new tests green; each fails against the pre-fix behavior (spot-check at least the M01 cleanup-preservation and the B02 flat-scaffold cases).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- D136: a fresh install materializes `.aw/` only (no legacy `.agents/` scaffolding); legacy is detected + offered migration. This resolves B02's "intended target" question - it is `.aw/records/`.
- `resolve_target_layout(repo_root)` governs the workflow BUNDLE path only; the record-scaffold constants (engine.py:3701/3709/3727/3752) + the README-stub target tables (4061/4105/4147) were never wired to it - that is the B02/PR-002 gap.
- POST-ORDER-07: the final `.aw/records/` layout is FLAT (no `docs/`): plans, prompts, comms, backlog, research, specs, walkthroughs, roadmaps, prompt-library. Derive scaffold/cleanup roots from `record_producers.resolve_record_path`/the RecordClass set, NOT a hardcoded list, so the installer cannot drift from the layout again.
- `_is_removable_leftover` (layout_migration.py, from IPD wvlk84) is the proven tracked/ignored guard; reuse it for cleanup.
- Move-not-copy engine already journals per-item + hash-verifies; the M01/E-04 gap is only the unconditional destination clobber + the cleanup of re-created sources.

## Findings

| id | area | evidence | issue |
|---|---|---|---|
| B02 | install scaffolder | engine.py:3699/3707/3725/3750 + create_setup_artifacts ~4190 | fresh scaffold writes `.agents/*` (split-brain) |
| B03 | uninstall --deep | engine.py:3423-3430 vs cli.py:523 help | deep clean misses `.aw/records/*` |
| M01a | cleanup_migration | layout_migration.py ~1158-1165 | rmtree/unlink re-created legacy source (ignore_errors) |
| M01b | _perform_move | layout_migration.py ~304-308 | unconditional destination clobber |
| L01a | leftover remove | layout_migration.py 414-417 (verified) | git-rm-fail force-unlink mislabeled `removed` |
| L01b | rollback config | layout_migration.py 1042-1043 (verified) | non-atomic write vs the atomic idiom (834-837) |
| PR-001 | plan-review (post-Order-07) | Order 07 flattened `.aw/records/docs/` away | E-01/E-02 target set stale (`{plans,docs,prompts,comms}`); DERIVE from the resolver, use the FLAT layout, no `docs/`. FIXED |
| PR-002 | plan-review (Order-07 handoff) | engine.py:4061/4105/4147 `_*_README_TARGETS` + ensure_*_readmes legacy-hardcoded; `_DOCS_README_TARGETS` references the Order-07-obsoleted `.agents/docs/README.md` | README-stub PLACEMENT was flagged in Order 07 as belonging here; added as E-07. FIXED |
| PR-003 | plan-review | cli.py:523 help + `_DEEP_CLEANUP_ROOTS` | E-02 target set also stale/flat; derive from resolver. FIXED |

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

- [ ] V-07 validates E-07
  - Required evidence: a fresh `aw`-layout install drops README stubs into the flat `.aw/records/*` dirs (not `.agents/*`); no `.aw/records/docs/README.md` is created; the `_*_README_TARGETS` / `ensure_*_readmes` derive from the resolver. Paste the created README paths / test output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
implements E-01..E-07, pastes actual evidence (fresh-install FLAT tree + README stubs, uninstall dry-run, the M01/L01
regression tests with fail-before/pass-after, full serial + migration suites), commits only the scoped
paths (`agent_workflows/engine.py`, `agent_workflows/layout_migration.py`, and the new/edited tests),
never pushes, runs `aw ipd lint --phase pre-transition` + the full suite before transition, and the
orchestrator owns the move to `executed/`. MEDIUM risk (core install + migration paths) - the guards
are conservative (fail-closed / preserve) and each is test-gated.
