# IPD: Install scaffolder + uninstall --deep + README-stub placement: layout-aware and flat

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 findings S2-B02, S2-B03 + the README-stub placement handed over from Order 07 (split out of Order 04, 2026-08-17). (B02) `create_setup_artifacts` scaffolds the records tree from hardcoded legacy `.agents/*` constants (engine.py:3701 PLANS_DIR / 3709 DOCS_DIR / 3727 PROMPTS_DIR / 3752 COMMS_DIR) - a fresh install re-introduces split-brain; (README) the README-stub placement tables `_PLANS_README_TARGETS`/`_DOCS_README_TARGETS`/`_PROMPTS_README_TARGETS` (engine.py:4061/4105/4147) + `ensure_*_readmes` are legacy-hardcoded and `_DOCS_README_TARGETS` targets the Order-07-obsoleted `.agents/docs/README.md`; (B03) `aw uninstall --deep` `_DEEP_CLEANUP_ROOTS` (engine.py:3425) cleans only `.agents/*` despite cli.py:523 help promising `.aw/records/`.
- Scope: Make the install scaffolder, its README-stub placement, and `uninstall --deep` layout-aware and FLAT, DERIVING the record roots from the canonical resolver (`record_producers.resolve_record_path`/RecordClass) so they cannot drift from the layout again. Per D136 a fresh install materializes `.aw/` only; the FINAL layout is flat `.aw/records/{plans,prompts,comms,backlog,research,specs,walkthroughs,roadmaps,prompt-library}` (Order 07, no `docs/`). OUT: migration-engine safety (Order 04, done); record verbs (Order 01); shipped docs (Order 02).
- Status: to-review
- Set: awretrofit
- Order: 8
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ksim8l

## Workflow history

- 2026-08-17 authored (opencode Opus 4.8): split out of Order 04; carries findings B02, B03, and the README-stub placement (PR-001/PR-002/PR-003 from the Order-04 dual /plan-review). Ready for /plan-review.

## Goal

Stop a fresh install from re-introducing split-brain and make `uninstall --deep` honor its promise, by
making the install scaffolder + its README-stub placement + deep-cleanup roots layout-aware and FLAT,
derived from the canonical resolver so they cannot drift from the `.aw/records/` layout again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: install scaffolder -> flat .aw/records/ (B02, D136)

- [ ] E-01 Make `create_setup_artifacts` (engine.py ~4192) scaffold the records lifecycle under the FLAT `.aw/records/*` on a fresh/`aw`-layout install instead of the hardcoded legacy `.agents/*` constants (PLANS_DIR/DOCS_DIR/PROMPTS_DIR/COMMS_DIR). DERIVE the record roots from `record_producers.resolve_record_path`/the RecordClass set - NOT a hardcoded list, and NO `docs/` level (Order 07 flattened it: research/specs/walkthroughs/roadmaps sit directly under `.aw/records/`; the prompt LIBRARY is `prompt-library/`, distinct from the `prompts/` staging tree). Update BOTH the dry-run mirror and the real writes, and the prompts/comms nested `.gitignore` + `local/` lane placement. Route creating writes through `guard_write` where practical. Preserve `--undo` manifest recording. Keep a legacy-targeted install (`resolve_target_layout` -> legacy) scaffolding `.agents/*`.
  - Depends on: none
  - Expected outcome: a fresh `aw`-layout install creates the FLAT `.aw/records/*` tree (resolver-derived, no `docs/`), not `.agents/*`; a legacy install still scaffolds `.agents/*`.
  - Execution state: pending

### Task group 2: README-stub placement -> flat .aw/records/ (Order-07 handoff)

- [ ] E-02 Repoint the README-stub placement to the flat `.aw/records/*` dirs on an `aw`-layout install: `_PLANS_README_TARGETS` (4061), `_DOCS_README_TARGETS` (4105), `_PROMPTS_README_TARGETS` (4147) + `ensure_plans_readmes`/`ensure_docs_readmes`/`ensure_prompts_readmes` (called ~4395-4398), derived from the same resolver as E-01. DROP the obsolete top-level `docs/` README target (there is no `.aw/records/docs/`); place per-type stubs at `.aw/records/{research,specs,walkthroughs,roadmaps,prompt-library}` (the Order-02 templates were retitled to these flat paths). No-clobber preserved.
  - Depends on: E-01
  - Expected outcome: a fresh `aw`-layout install drops README stubs into the flat `.aw/records/*` dirs; no `.agents/*`, no `.aw/records/docs/README.md`; legacy install unchanged.
  - Execution state: pending

### Task group 3: uninstall --deep -> flat .aw/records/ (B03)

- [ ] E-03 Extend `_DEEP_CLEANUP_ROOTS` (engine.py:3425) / `plan_deep_cleanup` so `aw uninstall --deep` targets the FLAT `.aw/records/*` roots (resolver-derived, no `docs/`) in addition to legacy `.agents/*`, matching the cli.py:523 help promise. Keep the existing safety confirmations.
  - Depends on: none
  - Expected outcome: `aw uninstall --deep` (dry-run) on a migrated repo lists the flat `.aw/records/*` roots; help and behavior agree.
  - Execution state: pending

### Task group 4: tests

- [ ] E-04 Add falsifiable regression tests: (a) a fresh `aw`-layout install scaffolds the FLAT `.aw/records/*` (no `.agents/*`, no `.aw/records/docs/`); (b) it drops README stubs into the flat dirs (no `.aw/records/docs/README.md`); (c) a legacy install still scaffolds `.agents/*`; (d) `uninstall --deep` dry-run lists the flat `.aw/records/*`. Each fails against the pre-fix hardcoded-legacy behavior.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: new tests green; spot-check the B02 flat-scaffold case fails against the pre-fix code; full serial suite >= 1004 passed / 1 skipped.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: a fresh `aw`-layout install (test/repro) creates the FLAT `.aw/records/*` (no `.agents/*`, no `.aw/records/docs/`), derived from the resolver; a legacy install still scaffolds `.agents/*`. Paste the created tree / test output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a fresh `aw` install drops README stubs into the flat `.aw/records/*` dirs; no `.aw/records/docs/README.md`; no `.agents/*` stub. Paste the created README paths.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `aw uninstall --deep` dry-run on a migrated fixture lists the flat `.aw/records/*` roots (matching cli.py:523 help). Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: all new tests pass; documented fail-before/pass-after on the B02 flat-scaffold case; full serial suite >= 1004 passed / 1 skipped; `aw attention --check`/`sanitize --agent` clean. Paste.
  - Observed evidence:
  - Result: pending

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
