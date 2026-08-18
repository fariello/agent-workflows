# IPD: Install scaffolder + uninstall --deep + README-stub placement: layout-aware and flat

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 findings S2-B02, S2-B03 + the README-stub placement handed over from Order 07 (split out of Order 04, 2026-08-17). (B02) `create_setup_artifacts` scaffolds the records tree from hardcoded legacy `.agents/*` constants (engine.py:3701 PLANS_DIR / 3709 DOCS_DIR / 3727 PROMPTS_DIR / 3752 COMMS_DIR) - a fresh install re-introduces split-brain; (README) the README-stub placement tables `_PLANS_README_TARGETS`/`_DOCS_README_TARGETS`/`_PROMPTS_README_TARGETS` (engine.py:4061/4105/4147) + `ensure_*_readmes` are legacy-hardcoded and `_DOCS_README_TARGETS` targets the Order-07-obsoleted `.agents/docs/README.md`; (B03) `aw uninstall --deep` `_DEEP_CLEANUP_ROOTS` (engine.py:3425) cleans only `.agents/*` despite cli.py:523 help promising `.aw/records/`.
- Scope: Make the install scaffolder, its README-stub placement, and `uninstall --deep` layout-aware and FLAT, DERIVING the record roots from the canonical resolver (`record_producers.resolve_record_path`/RecordClass) so they cannot drift from the layout again. Per D136 a fresh install materializes `.aw/` only; the FINAL layout is flat `.aw/records/{plans,prompts,comms,backlog,research,specs,walkthroughs,roadmaps,prompt-library}` (Order 07, no `docs/`). OUT: migration-engine safety (Order 04, done); record verbs (Order 01); shipped docs (Order 02).
- Status: executed
- Set: awretrofit
- Order: 8
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ksim8l

## Workflow history

- 2026-08-17 authored (opencode Opus 4.8): split out of Order 04; carries findings B02, B03, and the README-stub placement (PR-001/PR-002/PR-003 from the Order-04 dual /plan-review). Ready for /plan-review.
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. PR-001 (MEDIUM): E-01 said "derive from RecordClass" but RecordClass OMITS backlog/roadmaps/prompt-library; hardened E-01 to enumerate the authoritative flat set explicitly. GO - PENDING HUMAN APPROVAL.
- 2026-08-17 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): human approved. Implemented E-01/E-02/E-03/E-04 in commit 6f10f94: `_record_scaffold_dirs` layout-aware helper; `create_setup_artifacts` + the 3 README ensurers derive the FLAT `.aw/records/*` set (incl. backlog/roadmaps/prompt-library, no docs/; PR-001 fix) with dry-run/real parity; `_DEEP_CLEANUP_ROOTS` gains the 9 flat roots; legacy `.agents/workflows` repo still scaffolds `.agents/*`. Removed dead `_PLANS_README_TARGETS`. V-01..V-04 verified (fresh+legacy repro, README placement, deep-cleanup flat on this repo, mutation RED->GREEN); updated 10 legacy-asserting tests (count 24->26); full serial suite 1009 passed / 1 skipped; sanitize+attention clean. pre-transition lint conforming; moved pending -> executed/.

## Goal

Stop a fresh install from re-introducing split-brain and make `uninstall --deep` honor its promise, by
making the install scaffolder + its README-stub placement + deep-cleanup roots layout-aware and FLAT,
derived from the canonical resolver so they cannot drift from the `.aw/records/` layout again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: install scaffolder -> flat .aw/records/ (B02, D136)

- [x] E-01 Make `create_setup_artifacts` (engine.py ~4192) scaffold the records lifecycle under the FLAT `.aw/records/*` on a fresh/`aw`-layout install instead of the hardcoded legacy `.agents/*` constants (PLANS_DIR/DOCS_DIR/PROMPTS_DIR/COMMS_DIR) and the stale `DOCS_SUBDIRS`. Resolve the records BASE via `resolve_record_path`/the layout, then scaffold the AUTHORITATIVE FLAT set (NO `docs/` level): `plans/` + `prompts/` + `prompt-library/` (the library, was docs/prompts) + `comms/` + `backlog/` + `research/` (+ its reference/archive shards) + `specs/` + `walkthroughs/` + `roadmaps/`, each with its lifecycle subdirs + `.gitkeep`; plus the prompts/comms nested `.gitignore` + `local/` lanes. **plan-review PR-001 (verified):** do NOT derive the set from `RecordClass` alone - it is INCOMPLETE (`{plans,specs,research,records,prompts,comms,walkthroughs}`: it OMITS `backlog`, `roadmaps`, and the `prompt-library`); and the current `DOCS_SUBDIRS=(research,walkthroughs,specs,prompts)` is the OLD nested docs shape (and its `prompts` = the library). Enumerate the flat set explicitly from the Order-07 canonical layout (or first extend RecordClass to cover backlog/roadmaps and add a library class, then derive) so nothing is silently missed. Update BOTH the dry-run mirror and the real writes. Route creating writes through `guard_write` where practical. Preserve `--undo` manifest recording. Keep a legacy-targeted install (`resolve_target_layout` -> legacy) scaffolding `.agents/*`.
  - Depends on: none
  - Expected outcome: a fresh `aw`-layout install creates the FULL FLAT `.aw/records/*` set (incl. backlog + roadmaps + prompt-library, no `docs/`), not `.agents/*`; a legacy install still scaffolds `.agents/*`.
  - Execution state: performed

### Task group 2: README-stub placement -> flat .aw/records/ (Order-07 handoff)

- [x] E-02 Repoint the README-stub placement to the flat `.aw/records/*` dirs on an `aw`-layout install: `_PLANS_README_TARGETS` (4061), `_DOCS_README_TARGETS` (4105), `_PROMPTS_README_TARGETS` (4147) + `ensure_plans_readmes`/`ensure_docs_readmes`/`ensure_prompts_readmes` (called ~4395-4398), derived from the same resolver as E-01. DROP the obsolete top-level `docs/` README target (there is no `.aw/records/docs/`); place per-type stubs at `.aw/records/{research,specs,walkthroughs,roadmaps,prompt-library}` (the Order-02 templates were retitled to these flat paths). No-clobber preserved.
  - Depends on: E-01
  - Expected outcome: a fresh `aw`-layout install drops README stubs into the flat `.aw/records/*` dirs; no `.agents/*`, no `.aw/records/docs/README.md`; legacy install unchanged.
  - Execution state: performed

### Task group 3: uninstall --deep -> flat .aw/records/ (B03)

- [x] E-03 Extend `_DEEP_CLEANUP_ROOTS` (engine.py:3425) / `plan_deep_cleanup` so `aw uninstall --deep` targets the FLAT `.aw/records/*` roots (resolver-derived, no `docs/`) in addition to legacy `.agents/*`, matching the cli.py:523 help promise. Keep the existing safety confirmations.
  - Depends on: none
  - Expected outcome: `aw uninstall --deep` (dry-run) on a migrated repo lists the flat `.aw/records/*` roots; help and behavior agree.
  - Execution state: performed

### Task group 4: tests

- [x] E-04 Add falsifiable regression tests: (a) a fresh `aw`-layout install scaffolds the FLAT `.aw/records/*` (no `.agents/*`, no `.aw/records/docs/`); (b) it drops README stubs into the flat dirs (no `.aw/records/docs/README.md`); (c) a legacy install still scaffolds `.agents/*`; (d) `uninstall --deep` dry-run lists the flat `.aw/records/*`. Each fails against the pre-fix hardcoded-legacy behavior.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: new tests green; spot-check the B02 flat-scaffold case fails against the pre-fix code; full serial suite >= 1004 passed / 1 skipped.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- D136: a fresh install materializes `.aw/` only. `resolve_target_layout(repo_root)` governs only the workflow BUNDLE path; the record-scaffold constants + README-target tables were never wired to it - the B02/README gap.
- Post-Order-07 the `.aw/records/` layout is FLAT (no `docs/`); derive roots from `record_producers.resolve_record_path`/RecordClass so the installer cannot drift again (that drift is the root cause of the whole Set).
- Order 01 established the `resolve_record_path` idiom; Order 07 flattened the layout + renamed the library to `prompt-library/`.

## Findings

| id | area | evidence | issue |
|---|---|---|---|
| B02 | install scaffolder | engine.py:3701/3709/3727/3752 + create_setup_artifacts ~4192 | fresh scaffold writes legacy `.agents/*` (split-brain) |
| README | README-stub placement | engine.py:4061/4105/4147 + ensure_*_readmes; `_DOCS_README_TARGETS` -> Order-07-obsoleted `.agents/docs/README.md` | stubs dropped into legacy/obsolete paths |
| B03 | uninstall --deep | engine.py:3425 vs cli.py:523 help | deep clean misses `.aw/records/*` |

## Proposed changes (ordered, validatable)

1. E-01 scaffolder -> flat `.aw/records/` (resolver-derived). 2. E-02 README-stub placement -> flat.
3. E-03 uninstall --deep -> flat roots. 4. E-04 regression tests.

## Deferred / out of scope (with reason)

- Migration-engine safety (Order 04, executed); record verbs (Order 01); shipped docs (Order 02); help/docstrings (Order 05).

## Scope check

- Over-scope: none - each item is a reproduced B02/B03/README finding; resolver-derived, not a redesign.
- Under-scope: none - the full install-side of the run's findings, split cleanly from Order 04's migration-engine half.

## Required tests / validation

- New regression tests (E-04) fail-before/pass-after on the B02 flat-scaffold case.
- Fresh `aw` install repro scaffolds the flat `.aw/records/*` + README stubs there; legacy install unchanged; `uninstall --deep` dry-run lists the flat roots.
- Full serial suite >= 1004 passed / 1 skipped; `aw attention --check`/`sanitize --agent` clean.

## Spec / documentation sync

- D136 already documents fresh-install=`.aw/`-only; this Order makes the install path CONFORM. cli.py:523 help already promises `.aw/records/` (E-03 makes it true). No spec status change.

## Open questions

### OQ-01: Should a fresh install still scaffold legacy `.agents/`?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: NO - D136: a fresh install materializes `.aw/` only. A legacy
  install (resolve_target_layout -> legacy, i.e. an existing `.agents/workflows` repo not yet migrated)
  still scaffolds `.agents/*` for compatibility. This is conformance to the documented decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: a fresh `aw`-layout install (test/repro) creates the FLAT `.aw/records/*` (no `.agents/*`, no `.aw/records/docs/`), derived from the resolver; a legacy install still scaffolds `.agents/*`. Paste the created tree / test output.
  - Observed evidence: Added `engine._record_scaffold_dirs(target_layout)` (flat aw set / legacy nested) + rewrote `create_setup_artifacts` to build one shared file-list from it (dry-run + real share it, no drift). Repro on a fresh repo -> `.aw/records/{plans/*,prompts/*,prompt-library,comms/shared/*,backlog,research/{reference,archive},specs,walkthroughs,roadmaps}`; `.aw/records/docs` absent; `.agents/` absent. Legacy repo (.agents/workflows present) -> `.agents/plans/pending` + `.agents/docs/research` created, `.aw/records` absent. `FreshInstallScaffoldTests` (4 tests) + `test_legacy_repo_still_scaffolds_agents` pass.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: a fresh `aw` install drops README stubs into the flat `.aw/records/*` dirs; no `.aw/records/docs/README.md`; no `.agents/*` stub. Paste the created README paths.
  - Observed evidence: Rewrote `ensure_plans_readmes`/`ensure_docs_readmes`/`ensure_prompts_readmes` to derive targets from `_record_scaffold_dirs` (record-root README at `.aw/records/README.md`; per-type stubs at the flat dirs; the obsolete top-level `docs/README.md` dropped for the aw layout). `test_readme_stubs_land_flat`: `.aw/records/{README.md,plans/README.md,comms/README.md}` present; `.aw/records/docs/README.md` + `.agents/README.md` absent. Removed the dead `_PLANS_README_TARGETS` constant.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `aw uninstall --deep` dry-run on a migrated fixture lists the flat `.aw/records/*` roots (matching cli.py:523 help). Paste.
  - Observed evidence: `_DEEP_CLEANUP_ROOTS` extended with the 9 flat `.aw/records/*` roots (legacy `.agents/*` retained; per-root is_dir() skips the absent set). On THIS migrated repo `plan_deep_cleanup(.)` lists 9 flat roots: `.aw/records/{plans,prompts,prompt-library,comms,backlog,research,specs,walkthroughs,roadmaps}`. `DeepCleanupFlatTests::test_deep_cleanup_targets_flat_records` + the updated test_cli uninstall tests pass.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: all new tests pass; documented fail-before/pass-after on the B02 flat-scaffold case; full serial suite >= 1004 passed / 1 skipped; `aw attention --check`/`sanitize --agent` clean. Paste.
  - Observed evidence: `tests/test_awretrofit_install_scaffolder.py` -> 5 passed. Mutation: forcing `_record_scaffold_dirs` to the legacy branch -> `test_scaffold_is_flat_aw_records` `1 failed`; restored -> 5 passed. Full serial suite: `1009 passed, 1 skipped` (was 1004; +5 new, and 10 legacy-asserting tests in test_setup_artifacts/test_installer/test_dir_readmes/test_cli updated to the flat layout incl. created-count 24->26). `aw attention --check` valid; `aw sanitize --agent` clean.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
implements E-01..E-04, pastes actual evidence (the fresh-install FLAT tree + README stubs, the legacy
install unchanged, the uninstall dry-run, the full serial suite), commits only the scoped paths
(`agent_workflows/engine.py` + the new/edited tests), never pushes, runs `aw ipd lint --phase
pre-transition` + the full suite before transition, and the orchestrator owns the move to `executed/`.
MEDIUM risk (core install path) - mitigated by resolver-derivation (no hardcoded list), the legacy
branch preserved, no-clobber, and per-case tests.
